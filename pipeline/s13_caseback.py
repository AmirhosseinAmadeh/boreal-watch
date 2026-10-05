"""Stage 13 — the caseback (second official photo, `source/back.png`, the 3rd product image `..._sa300_er003.png`).

The back view needs its own trace; mirroring the front body (what the first version did) loses every back-side tone.

  1. Registration. The back photo is the front body seen from behind at a different zoom. Mirror the front alpha channel and
     fit scale + translation to the back alpha (IoU ~0.99), which gives the case centre and the px/unit factor of the back
     photo in the *same units* the front uses (dial radius = 200).
  2. Body (case, lugs, bracelet, crown, glass ring): same recipe as stage 9 — the alpha silhouette plus stacked tonal regions of
     the polished metal, traced with potrace.
  3. Movement window (r < R_WIN, the blue-grey openwork plate with gold wheels, jewels, engraved text and the guilloche):
     mean-shift flattening removes the plate's grain, k-means in Lab gives K colour classes, and every class is traced as its
     own region, painted from the largest to the smallest. Thin guilloche lines, gold teeth and engraved letters survive as
     small classes on top of the plate.

Output: pipeline/out/caseback.json  ->  assets/boreal-back.js (via s11_build.py).
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy import optimize

from lib import *
import vec

R_WIN_PX = 468.0     # inside: the movement (blue-grey plate); outside: glass ring + case metal
K_BODY = 8
K_WIN = 12           # plate bands + gold + dark parts; the guilloche is a separate line layer
UP_BODY = 1.5        # potrace grid supersampling
UP_WIN = 2.0
GRID = 1.0           # path coordinates are integers on a grid of 1 photo pixel, origin = case centre


def register(back_alpha: np.ndarray):
    """Scale + translation that maps the mirrored front photo onto the back photo. Returns (scale, centre_back_px)."""
    cal = load_json("calibration.json")["photos"]["front_a"]
    fa = load_rgba("front_a")[..., 3] > 127
    fm = fa[:, ::-1]
    fcx, fcy = fm.shape[1] - 1 - cal["centre_px"][0], cal["centre_px"][1]
    B = back_alpha > 127
    H, W = B.shape

    def cost(p):
        s, tx, ty = p
        M = np.array([[s, 0, tx], [0, s, ty]], np.float32)
        Wm = cv2.warpAffine(fm.astype(np.uint8), M, (W, H), flags=cv2.INTER_NEAREST) > 0
        a, b = Wm[300:H - 300], B[300:H - 300]       # the bracelet is cropped by the photo edge, compare the middle only
        return -(a & b).sum() / max(1, (a | b).sum())

    s0 = 1.368
    p0 = [s0, W / 2 - s0 * fcx, H / 2 - s0 * fcy]
    sim = [p0, [p0[0] + .01, p0[1], p0[2]], [p0[0], p0[1] + 8, p0[2]], [p0[0], p0[1], p0[2] + 8]]
    r = optimize.minimize(cost, p0, method="Nelder-Mead", options={"xatol": .05, "fatol": 1e-6, "maxiter": 400, "initial_simplex": sim})
    s, tx, ty = r.x
    return float(s), (float(s * fcx + tx), float(s * fcy + ty)), float(-r.fun)


def trace_layers(layers, origin, cx, cy, up, label):
    out = []
    for L in layers:
        paths = vec.trace_bitmap(L["mask"], up, origin=origin, turd=L.get("turd", 10), alphamax=1.2, opttol=1.4)
        tx = lambda p: ((p[0] - cx) * GRID, (p[1] - cy) * GRID)
        d = vec.path_d_rel(paths, tx=tx)
        out.append({"name": L["name"], "fill": "#%02X%02X%02X" % tuple(L["colour"]), "d": d, **({"opacity": L["opacity"]} if "opacity" in L else {})})
        print(f'  {label} {L["name"]:8s} {out[-1]["fill"]}  paths {len(paths):5d}  chars {len(d):8d}')
    return out


def up_smooth(m, w, h, up, sigma=0.9):
    u = cv2.resize(m.astype(np.float32), (int(w * up), int(h * up)), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(u, (0, 0), sigma * up / 2 + .01) > 0.5


def drop_specks(m, min_area):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
    keep = np.zeros_like(m, bool)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= min_area:
            keep |= lab == i
    return keep


def run(name="back"):
    im = load_rgba(name)
    bgr, alpha = im[..., :3], im[..., 3]
    h, w = alpha.shape
    s, (cx, cy), iou = register(alpha)
    front = load_json("calibration.json")["photos"]["front_a"]
    ppu = (front["dial_edge_radius_px"] / 200.0) * s                       # back-photo px per unit
    print(f"registration: scale {s:.4f} vs front, centre ({cx:.2f}, {cy:.2f}), IoU {iou:.4f}, {ppu:.4f} px/unit")

    yy, xx = np.mgrid[:h, :w]
    rad = np.hypot(xx - cx, yy - cy)
    inside = alpha > 127

    # ---------------------------------------------------------------- body: tonal regions of the metal
    metal = inside & (rad > R_WIN_PX - 3)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gs = cv2.bilateralFilter(gray, 7, 25, 5)
    vals = gs[metal].reshape(-1, 1).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.3)
    _, _, cent = cv2.kmeans(vals[::5], K_BODY, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    cent = np.sort(cent.ravel())
    thr = (cent[1:] + cent[:-1]) / 2
    band = np.digitize(gs, thr)
    colours = []
    for k in range(K_BODY):
        sel = metal & (band == k)
        c = np.median(bgr[sel], axis=0)[::-1] if sel.sum() else np.array([cent[k]] * 3)
        colours.append([int(v) for v in c])
    a_up = cv2.resize(alpha.astype(np.float32), (int(w * UP_BODY), int(h * UP_BODY)), interpolation=cv2.INTER_CUBIC) > 127
    layers = [{"name": "silhouette", "colour": colours[0], "mask": a_up}]
    for k in range(1, K_BODY):
        m = drop_specks(metal & (gs >= thr[k - 1]), 12)
        inv = ~m
        n, lab, st, _ = cv2.connectedComponentsWithStats(inv.astype(np.uint8), 4)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < 10:
                m |= lab == i
        layers.append({"name": f"tone{k}", "colour": colours[k], "mask": up_smooth(m, w, h, UP_BODY, 1.2) & a_up, "turd": 14})
    print("body:")
    body = trace_layers(layers, (0, 0), cx, cy, UP_BODY, "body")

    # ---------------------------------------------------------------- movement window: colour classes + line layer
    n_ = int(2 * R_WIN_PX + 10)
    x0, y0 = int(round(cx - n_ / 2)), int(round(cy - n_ / 2))
    crop = bgr[y0:y0 + n_, x0:x0 + n_].copy()
    cy_, cx_ = np.mgrid[:n_, :n_]
    r_ = np.hypot(cx_ - (cx - x0), cy_ - (cy - y0))
    win = r_ <= R_WIN_PX + 1.5
    # (a) flat classes: strong mean-shift removes the plate's grain and the hair-thin guilloche, keeps facets, gold, holes, text blocks
    big = cv2.pyrMeanShiftFiltering(crop, 8, 26)
    lab_ = cv2.cvtColor(big, cv2.COLOR_BGR2LAB).astype(np.float32)
    v = lab_[win]
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.4)
    _, _, cen = cv2.kmeans(v[::5], K_WIN, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    d2 = ((lab_.reshape(-1, 1, 3) - cen[None]) ** 2).sum(2)
    idx = d2.argmin(1).reshape(n_, n_)
    # majority filter: blur each class indicator, take the argmax -> no pixel-sized speckle left
    sm = np.stack([cv2.GaussianBlur((idx == k).astype(np.float32), (0, 0), 1.3) for k in range(K_WIN)], -1)
    idx = sm.argmax(-1)
    cen_bgr = cv2.cvtColor(cen.reshape(1, -1, 3).astype(np.uint8), cv2.COLOR_LAB2BGR)[0]
    area = np.array([((idx == k) & win).sum() for k in range(K_WIN)])
    order = np.argsort(-area)
    disc = up_smooth(win, n_, n_, UP_WIN, 0.2)
    wl = []
    for rank, k in enumerate(order):
        m = (idx == k) & win
        if rank == 0:
            mask = disc
        else:
            m = drop_specks(m, 14)
            mask = up_smooth(m, n_, n_, UP_WIN, 1.0) & disc
            mask = (cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & disc      # 0.5 px bleed: no seams between classes
        sel = (idx == k) & win
        col = np.median(crop[sel], axis=0)[::-1] if sel.any() else cen_bgr[k][::-1]       # true photo colour of the class, not the filtered centroid
        wl.append({"name": f"c{rank}", "colour": [int(t) for t in col], "mask": mask, "turd": 12})
    # (b) gold detail: engraved/printed gold letters, gear teeth, jewel settings are thinner than the mean-shift scale -> own layers
    lab_s = cv2.cvtColor(cv2.GaussianBlur(crop, (0, 0), 0.8), cv2.COLOR_BGR2LAB).astype(np.float32)
    gold = (lab_s[..., 2] > 139) & (lab_s[..., 0] > 95) & win
    gold = drop_specks(gold, 6)
    Lg = lab_s[..., 0]
    for nm, sel in (("gold_d", gold & (Lg <= 168)), ("gold_l", gold & (Lg > 168))):
        sel = drop_specks(sel, 5)
        if sel.any():
            col = np.median(crop[sel], axis=0)[::-1]
            wl.append({"name": nm, "colour": [int(t) for t in col], "mask": up_smooth(sel, n_, n_, UP_WIN, 0.8) & disc, "turd": 6})
    # (c) guilloche + engraved text: dark ridges (Sato filter, scale 1.2-1.8 px) with hysteresis -> only long connected curves, no grain
    from skimage.filters import sato, apply_hysteresis_threshold
    g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    rid = sato(g, sigmas=[1.2, 1.8], black_ridges=True)
    plate = np.isin(idx, order[:7]) & win & ~gold
    hi, lo = np.percentile(rid[plate], 94), np.percentile(rid[plate], 84)
    lines = apply_hysteresis_threshold(rid, lo, hi) & plate
    lines = drop_specks(lines, 30)
    lcol = np.median(crop[lines], axis=0)[::-1] if lines.any() else np.array([90, 100, 110])     # colour of the ridge core, before any thickening
    lines = cv2.dilate(lines.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0
    wl.append({"name": "lines", "colour": [int(t) for t in lcol], "mask": up_smooth(lines, n_, n_, UP_WIN, 0.7) & disc, "turd": 8, "opacity": 0.85})
    print("window:")
    out_win = trace_layers(wl, (x0, y0), cx, cy, UP_WIN, "win")

    bb = [int(np.nonzero(inside)[1].min()), int(np.nonzero(inside)[0].min()), int(np.nonzero(inside)[1].max()), int(np.nonzero(inside)[0].max())]
    ub = [round(float((bb[0] - cx) / ppu), 1), round(float((bb[1] - cy) / ppu), 1), round(float((bb[2] - cx) / ppu), 1), round(float((bb[3] - cy) / ppu), 1)]
    tot = sum(len(L["d"]) for L in body) + sum(len(L["d"]) for L in out_win)
    print("total path chars:", tot)
    data = {"grid_per_px": GRID, "px_per_unit": round(ppu, 4), "centre_px": [round(cx, 2), round(cy, 2)], "scale_vs_front": round(s, 4), "iou": round(iou, 4),
            "unit_bbox": ub, "window_radius_units": round(R_WIN_PX / ppu, 2), "body": body, "window": out_win,
            "k_body": K_BODY, "k_window": K_WIN, "path_chars": tot}
    data["verify"] = verify(data, bgr, alpha, cx, cy)
    save_json("caseback.json", data)
    return data


def verify(data, bgr, alpha, cx, cy):
    """Render the traced layers on the photo's pixel grid (resvg) and compare with the photo."""
    try:
        import resvg_py
    except ImportError:
        return {}
    h, w = alpha.shape
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-cx} {-cy} {w} {h}" width="{w}" height="{h}" fill-rule="evenodd">'
    for L in data["body"] + data["window"]:
        o = f' fill-opacity="{L["opacity"]}"' if "opacity" in L else ""
        svg += f'<path d="{L["d"]}" fill="{L["fill"]}"{o}/>'
    png = resvg_py.svg_to_bytes(svg_string=svg + "</svg>", background="#000000")
    r = cv2.imdecode(np.frombuffer(bytes(png), np.uint8), cv2.IMREAD_COLOR)
    save_img("back_render.png", r)
    yy, xx = np.mgrid[:h, :w]
    rad = np.hypot(xx - cx, yy - cy)
    ins = alpha > 127
    pb, rb = cv2.GaussianBlur(bgr, (0, 0), 3).astype(float), cv2.GaussianBlur(r, (0, 0), 3).astype(float)
    res = {}
    for nm, m in (("window", (rad < R_WIN_PX) & ins), ("case", (rad >= R_WIN_PX) & ins & (rad < 1000))):
        res[nm + "_mae_px"] = round(float(np.abs(r.astype(float) - bgr.astype(float))[m].mean()), 2)
        res[nm + "_mae_blur3"] = round(float(np.abs(pb - rb)[m].mean()), 2)
    print("verify:", res)
    return res


if __name__ == "__main__":
    run()
