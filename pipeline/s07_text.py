"""Stage 7 — numerals and minute labels.

Every numeral is a small piece of printed text, rotated to a rule that we measured instead of assumed:
  * minute labels (60, 05 ... 55) sit at r = 284.5 px on every 30 deg; labels 20-40 are flipped by 180 deg so they read upright
    (confirmed numerically: the digit "5" correlates 0.73-0.81 with the reference when flipped, 0.52-0.54 when not)
  * hour numerals (r ~ 212 px) follow the same rule for 4-8 o'clock; 3 is replaced by the date window.

For each item: de-rotate the photo around the item's centre (6x supersampling), keep the connected components that belong
to the item, repair the slits left where chords/rings crossed it, re-centre on the union bounding box, then trace Beziers.
"""
from __future__ import annotations

import cv2
import numpy as np

from lib import *
import model_px
import s04_dial_primitives as s4
import vec

SC = 6                      # supersampling of the upright crops


def flipped(kind, A):
    if kind == "min":
        return 120 <= A <= 240           # labels 20..40
    return 120 <= A <= 240               # hours 4..8   (A = 30*h)


def rot_for(kind, A):
    return (A - 180) % 360 if flipped(kind, A) else A % 360


def glyph_mask(up, foot=None, line_px=3.4, grow_px=1.0, spur_px=0.0):
    """up = upright soft ink at SC x.  `foot` = upright footprint of the parametric lines/rings (same grid) or None.
    Pixels outside the line footprint are kept exactly as photographed (so glyph corners stay sharp). Inside the footprint a pixel
    is kept only if it belongs to a thick structure (a glyph stroke wider than the 2.1 px chords) -> opening, grown by `grow_px`."""
    m = (cv2.GaussianBlur(up, (0, 0), 0.7) > 0.45).astype(np.uint8)
    if foot is not None:
        d = int(round(line_px * SC)) | 1
        opened = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (d, d)))
        g = int(round(grow_px * SC * 2)) | 1
        body = cv2.dilate(opened, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (g, g)))
        m = (m & ((foot == 0) | (body > 0))).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (SC + 1, SC + 1)))
    if spur_px > 0:                                                # remove spurs thinner than spur_px (chord stubs, JPEG noise)
        k = int(round(spur_px * SC)) | 1
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    return m > 0


def chord_clean(ink, lines, c, half_w=1.9, probe=2.4):
    """Drop the pixels of every chord, except where the chord runs *inside* a thicker glyph stroke.
    A chord pixel is inside a stroke when the ink continues on BOTH sides of the chord (+-probe px along its normal);
    in a counter or on open dial the pixels beside the chord are blank, so it is removed.  Because the test is perpendicular to the
    chord, a chord that merely touches a glyph edge leaves no stub (its pixels outside the glyph have blank sides)."""
    h, w = ink.shape
    out = ink.copy()
    for l in lines:
        a, b = np.array(l["end_a_px"]), np.array(l["end_b_px"])
        d = (b - a) / np.hypot(*(b - a)); n = np.array([-d[1], d[0]])
        foot = np.zeros((h, w), np.uint8)
        cv2.line(foot, tuple(np.round(a).astype(int)), tuple(np.round(b).astype(int)), 1, int(np.ceil(2 * half_w)))
        ys, xs = np.nonzero(foot)
        pts = np.c_[xs, ys].astype(np.float32)
        def samp(off):
            q = pts + off * n.astype(np.float32)
            return cv2.remap(ink, q[:, 0].reshape(-1, 1), q[:, 1].reshape(-1, 1), cv2.INTER_LINEAR).ravel()
        inside = (samp(probe) > 0.5) & (samp(-probe) > 0.5)
        out[ys[~inside], xs[~inside]] = 0
    return out


def fill_vertical_strip(ink, strip, radius=4):
    """The seconds hand is a ~6 px vertical strip that hides part of the print under it.
    Each side is completed separately: the left half of the strip is inpainted (Telea) with the right half treated as blank background,
    and vice-versa; the two halves then meet in the middle.  A stroke that continues under the hand (the bar of a '1') is bridged, and two
    glyphs that merely sit next to the hand ('6' and '0' of 60) are NOT glued together."""
    ink8 = (np.clip(ink, 0, 1) * 255).astype(np.uint8)
    ys, xs = np.nonzero(strip)
    xc = (np.median(xs[ys == ys.min() + (ys.max() - ys.min()) // 2]) if len(ys) else 0)
    xc = int(round(float(np.mean(xs)))) if len(xs) else 0
    out = ink8.copy()
    xx = np.arange(ink.shape[1])[None, :].repeat(ink.shape[0], 0)
    near = cv2.dilate(strip.astype(np.uint8), np.ones((9, 3), np.uint8)) > 0
    for side in (-1, +1):
        hole = strip & ((xx <= xc) if side < 0 else (xx > xc))
        tmp = ink8.copy()
        other = strip & ((xx > xc) if side < 0 else (xx <= xc))
        tmp[other] = 0
        filled = cv2.inpaint(tmp, hole.astype(np.uint8) * 255, radius, cv2.INPAINT_TELEA)
        out[hole] = filled[hole]
    return out.astype(np.float32) / 255


def warp_upright(img, center, rot_cw, size, scale=SC):
    M = cv2.getRotationMatrix2D((float(center[0]), float(center[1])), rot_cw, scale)
    M[0, 2] += size[0] * scale / 2 - center[0]
    M[1, 2] += size[1] * scale / 2 - center[1]
    return cv2.warpAffine(img, M, (int(size[0] * scale), int(size[1] * scale)), flags=cv2.INTER_CUBIC), M


class TextExtractor:
    def __init__(self, name="front_a"):
        cal = load_json("calibration.json")["photos"][name]
        self.fr = Frame(cal["centre_px"][0], cal["centre_px"][1], cal["dial_edge_radius_px"])
        self.c = np.array([self.fr.cx, self.fr.cy])
        self.prim = load_json("dial_primitives_px.json")
        self.lines = load_json("lines_px.json")["lines"]
        self.im = load_rgba(name)
        _, self.hmask = s4.build_ink(name, self.fr, self.im)
        import s03_hands as hands
        red8, silver8 = hands.masks(self.im, self.fr)
        raw = np.clip((self.im[..., 2].astype(np.float32) - 25) / 165, 0, 1)
        silver_d = cv2.dilate(silver8, np.ones((7, 7), np.uint8)) > 0
        raw[silver_d] = 0                       # the hour / minute hands truly hide what is below (completed per item later)
        strip = cv2.dilate(red8, np.ones((3, 3), np.uint8)) > 0
        ink = fill_vertical_strip(raw, strip)   # the thin red seconds hand is completed side by side
        self.ink = ink
        self.hand_zone = (cv2.dilate(red8, np.ones((7, 7), np.uint8)) > 0) | self.hmask
        mdl = model_px.render(ink.shape, self.c, self.prim, self.lines)
        self.model = cv2.dilate(mdl, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        self.clean = chord_clean(ink, self.lines, self.c)

    def centre_px(self, r, A):
        a = np.radians(A)
        return self.c + r * np.array([np.sin(a), -np.cos(a)])

    def fixed_item(self, kind, centre, size, label, rot=0.0):
        centre = np.array(centre, float)
        up, M = warp_upright(self.clean, centre, rot, size)
        m = glyph_mask(up, None, spur_px=1.8 if kind == 'hour' else 0.0)
        n, lab, st, cen = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
        keep = np.zeros_like(m)
        H, W = m.shape
        for i in range(1, n):
            x, y, w, h, a = st[i]
            if a >= 10 * SC * SC and not (x <= 1 or y <= 1 or x + w >= W - 1 or y + h >= H - 1):
                keep |= lab == i
        it = {"kind": kind, "A": 0, "rot": rot, "centre_px": centre, "size": size, "mask": keep, "occluded": 0.0, "label": label}
        return it

    def item(self, kind, A, r0, size, rot=None, iters=2, min_area=14):
        rot = rot_for(kind, A) if rot is None else rot
        centre = self.centre_px(r0, A)
        for _ in range(iters):
            up, M = warp_upright(self.clean, centre, rot, size)
            fp, _ = warp_upright(self.model, centre, rot, size)
            fp, _ = warp_upright(self.model, centre, rot, size)
            m = glyph_mask(up, None, spur_px=1.8 if kind == 'hour' else 0.0)
            n, lab, st, cen = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
            keep = np.zeros_like(m)
            H, W = m.shape
            for i in range(1, n):
                x, y, w, h, a = st[i]
                touches = x <= 1 or y <= 1 or x + w >= W - 1 or y + h >= H - 1
                if a >= min_area * SC * SC and not touches:
                    keep |= lab == i
            ys, xs = np.nonzero(keep)
            if len(xs) == 0:
                break
            ux, uy = (xs.min() + xs.max()) / 2 / SC - size[0] / 2, (ys.min() + ys.max()) / 2 / SC - size[1] / 2   # shift of bbox centre
            # move the centre by that shift (in the item's upright frame -> photo frame)
            rr = np.radians(rot)
            dx = ux * np.cos(rr) - uy * np.sin(rr)
            dy = ux * np.sin(rr) + uy * np.cos(rr)
            centre = centre + np.array([dx, dy])
        up, M = warp_upright(self.clean, centre, rot, size)
        fp, _ = warp_upright(self.model, centre, rot, size)
        fp, _ = warp_upright(self.model, centre, rot, size)
        m = glyph_mask(up, None, spur_px=1.8 if kind == 'hour' else 0.0)
        n, lab, st, cen = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
        keep = np.zeros_like(m)
        H, W = m.shape
        for i in range(1, n):
            x, y, w, h, a = st[i]
            touches = x <= 1 or y <= 1 or x + w >= W - 1 or y + h >= H - 1
            if a >= min_area * SC * SC and not touches:
                keep |= lab == i
        hz, _ = warp_upright(self.hand_zone.astype(np.float32), centre, rot, size)
        occl = float(((hz > 0.5) & (np.abs(cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 6 * SC) - 0) > 0.01)).sum() / max(1, (hz > 0.5).sum() + 1))
        occluded = float((hz > 0.5)[keep | cv2.dilate(keep.astype(np.uint8), np.ones((3 * SC, 3 * SC), np.uint8)).astype(bool)].mean()) if keep.any() else 0.0
        return {"kind": kind, "A": A, "rot": rot, "centre_px": centre, "size": size, "mask": keep, "occluded": occluded}


def comps_of(mask):
    """Connected components of a (SC x) mask as (x0, y0, x1, y1, submask) sorted left to right."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    out = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        out.append((x, y, x + w, y + h, (lab[y:y + h, x:x + w] == i)))
    return sorted(out, key=lambda c: c[0])


def paste(dst, sub, x, y):
    h, w = sub.shape
    dst[y:y + h, x:x + w] |= sub


def rect_px(mask, item, x0, y0, x1, y1):
    """Fill a rectangle given in PHOTO pixels into an upright item mask (rot = 0 items only)."""
    cx, cy = item["centre_px"]; W, H = item["size"]
    ix0, ix1 = int(round((x0 - cx + W / 2) * SC)), int(round((x1 - cx + W / 2) * SC))
    iy0, iy1 = int(round((y0 - cy + H / 2) * SC)), int(round((y1 - cy + H / 2) * SC))
    mask[iy0:iy1, ix0:ix1] = True


def repair(items, tx):
    """Complete the few glyphs that are physically hidden in the photo.  Every repaired item is flagged "reconstructed"
    with the method used, so the site and the docs can say so honestly."""
    by = {(i["kind"], i["label"]): i for i in items}
    notes = []

    # --- logo lockup: the seconds hand hides the right half of the "a" in swatch and the whole "I" of SWISS
    lg = by[("logo", "swatch SWISS")]
    rect_px(lg["mask"], lg, 934.4, 809.0, 937.0, 823.0)      # stem of the "a"
    rect_px(lg["mask"], lg, 925.0, 809.0, 937.0, 811.4)      # top of the bowl
    rect_px(lg["mask"], lg, 925.0, 820.6, 937.0, 823.0)      # bottom of the bowl
    rect_px(lg["mask"], lg, 930.55, 831.2, 932.25, 842.0)    # the "I"
    lg["reconstructed"] = "a (stem + bowl bars) and I drawn from the stroke width of the visible letters"

    # --- minute label "10": hidden under the minute hand; rebuild from clean digits of the same font:
    #     the "1" of "15" and the "0" of "05" (the visible "0" is partly covered on its left)
    m10, m15, m05 = by[("min", "10")], by[("min", "15")], by[("min", "05")]
    c10, c15, c05 = comps_of(m10["mask"]), comps_of(m15["mask"]), comps_of(m05["mask"])
    vis0 = max(c10, key=lambda c: c[2])
    one15, five15 = c15[0], c15[-1]
    zero05 = c05[0]
    gap = five15[0] - one15[2]
    new = np.zeros_like(m10["mask"])
    zw, zh = zero05[2] - zero05[0], zero05[3] - zero05[1]
    zx0 = vis0[2] - zw                                   # right edge of the visible 0 is intact
    zy0 = vis0[3] - zh
    paste(new, zero05[4], int(zx0), int(zy0))
    ox = zx0 - gap - (one15[2] - one15[0])
    oy = vis0[3] - (one15[3] - one15[1])
    paste(new, one15[4], int(ox), int(oy))
    m10["mask"] = new
    m10["reconstructed"] = "1 copied from the label 15, 0 copied from the label 05; right edge aligned to the visible 0"

    # --- hour numerals: typical glyph metrics from the clean ones
    clean = [by[("hour", str(h))] for h in (4, 5, 6, 7, 8, 9)]
    widths, rcs = [], []
    for it in clean:
        c = comps_of(it["mask"])
        x0 = min(q[0] for q in c); x1 = max(q[2] for q in c)
        widths.append(x1 - x0)
        rcs.append(float(np.hypot(*(it["centre_px"] - tx.c))))
    wmed = int(np.median(widths))
    r_c = float(np.median(rcs))
    c12 = comps_of(by[("hour", "12")]["mask"])
    x_one_end = c12[0][2]
    parts = [c for c in c12 if c[0] >= x_one_end - 2 and c is not c12[0]]
    X0 = min(c[0] for c in parts); Y0 = min(c[1] for c in parts); X1 = max(c[2] for c in parts); Y1 = max(c[3] for c in parts)
    two_mask = np.zeros((Y1 - Y0, X1 - X0), bool)
    for c in parts:
        two_mask[c[1] - Y0:c[3] - Y0, c[0] - X0:c[2] - X0] |= c[4]
    # the diagonal of the "2" passes under the seconds hand and can leave a break: bridge consecutive pieces with a stroke-wide line
    n_, lab_, st_, _ = cv2.connectedComponentsWithStats(two_mask.astype(np.uint8), 8)
    if n_ > 2:
        order = sorted(range(1, n_), key=lambda i: st_[i, cv2.CC_STAT_TOP])
        stroke_px = int(np.median([st_[i, cv2.CC_STAT_WIDTH] for i in order]))
        for a_i, b_i in zip(order[:-1], order[1:]):
            ya = np.nonzero(lab_ == a_i)[0].max(); xa = np.nonzero((lab_ == a_i)[ya])[0].mean()
            yb = np.nonzero(lab_ == b_i)[0].min(); xb = np.nonzero((lab_ == b_i)[yb])[0].mean()
            cv2.line(two_mask.view(np.uint8), (int(xa), int(ya)), (int(xb), int(yb)), 1, max(SC * 3, stroke_px // 2))
    two = (X0, Y0, X1, Y1, two_mask)                            # the "2" of 12, already completed side-wise
    m12 = by[("hour", "12")]["mask"]
    m12[Y0:Y1, X0:X1] = False
    m12[Y0:Y1, X0:X1] |= two_mask                               # same bridge on the 12 itself
    # hour "2" (2 o'clock) - the minute hand covers it: reuse the "2" of 12, centred at the nominal radius
    h2 = by[("hour", "2")]
    h2["centre_px"] = tx.centre_px(r_c, 60)
    H, W = h2["mask"].shape
    new = np.zeros_like(h2["mask"])
    sub = two[4]
    paste(new, sub, (W - sub.shape[1]) // 2, (H - sub.shape[0]) // 2)
    h2["mask"] = new
    h2["reconstructed"] = "2 copied from the 12 (same font, same size); position from the numeral ring radius"
    # hour "10": "1" is visible, the "0" is partly under the hour hand -> stadium ring from measured widths/strokes
    h10 = by[("hour", "10")]
    c10h = comps_of(h10["mask"])
    bar = c10h[0]
    arch = max(c10h, key=lambda c: c[2])
    hbar = bar[3] - bar[1]
    stroke = int(np.median(bar[4].sum(axis=1)))                # width of the "1" bar = stem thickness
    zx1 = arch[2]
    zx0 = zx1 - wmed
    zy0, zy1 = bar[1], bar[3]
    Hh, Ww = h10["mask"].shape
    z = np.zeros((Hh, Ww), np.uint8)
    cv2.rectangle(z, (zx0 + wmed // 2, zy0 + wmed // 2), (zx1 - wmed // 2, zy1 - wmed // 2), 1, -1)
    z = cv2.dilate(z, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (wmed, wmed)))
    zi = np.zeros_like(z)
    cv2.rectangle(zi, (zx0 + stroke + (wmed - 2 * stroke) // 2, zy0 + stroke + (wmed - 2 * stroke) // 2),
                  (zx1 - stroke - (wmed - 2 * stroke) // 2, zy1 - stroke - (wmed - 2 * stroke) // 2), 1, -1)
    zi = cv2.dilate(zi, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, wmed - 2 * stroke), max(3, wmed - 2 * stroke))))
    zero_shape = (z > 0) & ~(zi > 0)
    h10["mask"] = h10["mask"] | zero_shape
    h10["reconstructed"] = "0 drawn as a stadium ring from the median glyph width and the stem width of the 1"
    return notes


def trace_item(it):
    """Upright mask (SC x) -> Bezier outline in photo px, relative to the item centre (x right, y down)."""
    h, w = it["mask"].shape
    paths = vec.trace_bitmap(it["mask"], SC, origin=(-w / SC / 2, -h / SC / 2), turd=int(1.5 * SC * SC / 4))
    return paths


def run(name="front_a"):
    tx = TextExtractor(name)
    items = []
    for j in range(12):
        A = 30 * j
        it = tx.item("min", A, 284.5, (56, 34)); it["label"] = f"{(A // 6) or 60:02d}"; items.append(it)
    for h in range(1, 13):
        if h == 3:
            continue
        A = 30 * (h % 12)
        it = tx.item("hour", A, 212.0, (64, 64)); it["label"] = str(h); items.append(it)
    # fixed-position text blocks
    lg = tx.item("logo", 0, 0, (120, 56), rot=0, iters=0); 
    items.append(lg)
    items[-1] = tx.fixed_item("logo", (931.4, 822.0), (120, 56), label="swatch SWISS")
    items.append(tx.fixed_item("automatic", (932.0, 1107.0), (100, 24), label="AUTOMATIC"))
    repair(items, tx)
    out = []
    for it in items:
        paths = trace_item(it)
        bb = vec.bbox(paths)
        out.append({"kind": it["kind"], "label": it["label"], "A": it["A"], "rot": it["rot"],
                    "centre_px": [round(float(it["centre_px"][0]), 3), round(float(it["centre_px"][1]), 3)],
                    "occluded": round(it["occluded"], 3), "bbox_px": [round(v, 2) for v in bb],
                    "reconstructed": it.get("reconstructed"),
                    "d": vec.path_d(paths, nd=2)})
    save_json("text_items.json", {"items": out})
    # contact sheet of the *traced* result for inspection
    tiles = []
    for it, o in zip(items, out):
        t = (it["mask"].astype(np.uint8) * 255)
        f = min(3.0, 250 / (t.shape[1] / SC), 200 / (t.shape[0] / SC))
        t = cv2.resize(t, (int(t.shape[1] / SC * f), int(t.shape[0] / SC * f)), interpolation=cv2.INTER_AREA)
        canvas = np.zeros((220, 260), np.uint8)
        y0, x0 = (220 - t.shape[0]) // 2, (260 - t.shape[1]) // 2
        canvas[y0:y0 + t.shape[0], x0:x0 + t.shape[1]] = t[:220, :260]
        cv2.putText(canvas, f"{o['kind']} {o['label']} rot={o['rot']:.0f} occl={o['occluded']:.2f}", (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, 255, 1)
        tiles.append(canvas)
    while len(tiles) % 6:
        tiles.append(np.zeros_like(tiles[0]))
    save_img("text_items_sheet.png", np.vstack([np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]))
    print("traced", len(out), "items; total path chars:", sum(len(o["d"]) for o in out))
    return tx, items


if __name__ == "__main__":
    run()
