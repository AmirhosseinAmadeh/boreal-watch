"""Stage 3 — hands.

Printed dial ink is thin (3-8 px at 1920 px) while the hands are thick (>= 25 px) and silver, so a morphological
opening with a disc larger than the biggest ink stroke keeps only the hands. The red seconds hand is picked by hue.

For every hand we then
  1. refine its angle by symmetry (a hand is mirror-symmetric about its own axis),
  2. rotate the photo so the hand points up (canonical pose) at 4x supersampling,
  3. read the outline row by row (sub-pixel crossing of the half-way luminance between hand and dial),
  4. sample the light / shaded half colours along the length (two facets),
so the SAME outline can be re-rotated by the site's clock.
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy.signal import medfilt

from lib import *

SS = 4  # supersampling factor of the straightened views


def masks(im, fr: Frame):
    bgr = im[..., :3]
    b, g, r = [bgr[..., i].astype(np.int32) for i in range(3)]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    yy, xx = np.mgrid[:im.shape[0], :im.shape[1]]
    inside = np.hypot(xx - fr.cx, yy - fr.cy) < fr.R * 1.0

    red = ((r - g) > 70) & ((r - b) > 60) & inside
    red8 = cv2.morphologyEx((red * 255).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    sat = bgr.max(axis=2).astype(int) - bgr.min(axis=2).astype(int)
    silver = (gray > 70) & (sat < 60) & inside
    s8 = (silver * 255).astype(np.uint8)
    opened = cv2.morphologyEx(s8, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
    return red8, opened


def components(mask8, min_area):
    n, lab, stats, cent = cv2.connectedComponentsWithStats(mask8, 8)
    return [(lab == i, stats[i]) for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= min_area]


def rough_angle(mask, pivot):
    """Principal axis of the hand mask (ignoring the hub and the very tip), pointing away from the pivot.
    A hand is a long thin symmetric shape, so PCA gives its direction to ~0.05 deg."""
    ys, xs = np.nonzero(mask)
    P = np.c_[xs, ys].astype(float)
    d = np.hypot(*(P - np.asarray(pivot)).T)
    Q = P[(d > 45) & (d < d.max() - 8)]
    mu = Q.mean(0)
    w, v = np.linalg.eigh(np.cov((Q - mu).T))
    ax = v[:, 1]
    if ax @ (mu - np.asarray(pivot)) < 0:
        ax = -ax
    return float(np.degrees(np.arctan2(ax[0], -ax[1])) % 360), float(d.max())


def straighten(img, pivot, ang_deg, w, h, piv_out, ss=SS):
    """Rotate `img` about `pivot` by -ang so the hand points up, output (w*ss, h*ss) with pivot at piv_out*ss."""
    M = cv2.getRotationMatrix2D(pivot, ang_deg, ss)          # cv2 angle>0 = counter-clockwise => cancels cw clock angle
    M[0, 2] += piv_out[0] * ss - pivot[0]      # the pivot is the fixed point of the rotation+scale
    M[1, 2] += piv_out[1] * ss - pivot[1]
    return cv2.warpAffine(img, M, (w * ss, h * ss), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)


def row_extents(L, x0, y_top, y_bot, thr_out=45.0, search=40 * SS):
    """For each row between y_top..y_bot return (xl, xr) sub-pixel, scanning outward from x0 for the half-way crossing."""
    xl = np.full(y_bot - y_top, np.nan)
    xr = np.full(y_bot - y_top, np.nan)
    for i, y in enumerate(range(y_top, y_bot)):
        row = L[y]
        for side, arr in ((-1, xl), (1, xr)):
            # inner luminance = median of the 6 px nearest the axis on that side
            lo = int(x0 + side * 2 * SS)
            seg = row[min(lo, lo + side * 6 * SS):max(lo, lo + side * 6 * SS)]
            if seg.size == 0:
                continue
            Lin = float(np.median(seg))
            if Lin < 90:
                continue
            half = 0.5 * (Lin + thr_out)
            x = lo
            for k in range(search):
                xn = lo + side * k
                if xn < 1 or xn >= len(row) - 1:
                    break
                if row[xn] < half:
                    # linear interpolation between xn-side and xn
                    xp = xn - side
                    a, b = row[xp], row[xn]
                    t = 0 if a == b else (a - half) / (a - b)
                    x = xp + side * t
                    arr[i] = x
                    break
    return xl, xr


def hampel(a, k=9, n=3.0):
    a = a.copy()
    med = medfilt(np.nan_to_num(a, nan=np.nanmedian(a)), k)
    dev = np.abs(a - med)
    mad = np.nanmedian(dev) + 1e-6
    bad = ~np.isfinite(a) | (dev > n * 1.4826 * mad + 2 * SS)
    a[bad] = med[bad]
    return a


def rdp(points, eps):
    pts = np.asarray(points, float)
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a
    n = np.hypot(*ab)
    q = pts - a
    d = np.abs(ab[0] * q[:, 1] - ab[1] * q[:, 0]) / (n if n else 1)
    i = int(np.argmax(d))
    if d[i] > eps:
        return np.vstack([rdp(pts[:i + 1], eps)[:-1], rdp(pts[i:], eps)])
    return np.vstack([a, b])


def analyse_silver(name, im, fr, mask, pivot, label):
    ang0, length = rough_angle(mask, pivot)
    gray = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
    W, H, py = 160, 440, 380
    ang = ang0
    x0 = W / 2 * SS
    st = straighten(gray, pivot, ang, W, H, (W / 2, py))
    y_a, y_b = int((py - 0.80 * length) * SS), int((py - 0.18 * length) * SS)
    xl, xr = row_extents(st, x0, y_a, y_b)
    ok = np.isfinite(xl) & np.isfinite(xr)
    mid = (xl[ok] + xr[ok]) / 2
    axis_offset_px = float(np.median(mid - x0) / SS)      # lateral offset of the hand's mid-line from the pivot (px)
    st = straighten(gray, pivot, ang, W, H, (W / 2, py))
    stc = straighten(im[..., :3], pivot, ang, W, H, (W / 2, py))
    x0 = W / 2 * SS
    y_top, y_bot = int((py - length - 6) * SS), int((py + 26) * SS)
    xl, xr = row_extents(st, x0, y_top, y_bot)
    xl, xr = hampel(xl), hampel(xr)
    ys = np.arange(y_top, y_bot)
    ok = (xr - xl) > 2 * SS
    # tip: first row where width collapses
    top = ys[ok][0] if ok.any() else y_top
    sel = ok & (ys >= top)
    s_px = (py * SS - ys) / SS                              # length along the hand from the pivot (px of the photo)
    half_l = (x0 - xl) / SS                                 # distances from axis, photo px
    half_r = (xr - x0) / SS
    # facet colours along the length: sample the middle of each half, 40 stations from just past the hub to the tip
    stations = np.linspace(34.0, s_px[sel].max() - 4.0, 16)
    left_c, right_c = [], []
    for s_ in stations:
        i = int(np.argmin(np.abs(ys - int(round(py * SS - s_ * SS)))))
        y = int(ys[i]); c = (xl[i] + xr[i]) / 2; w = xr[i] - xl[i]
        for arr, off in ((left_c, -0.25), (right_c, 0.25)):
            xx = int(c + off * w)
            patch = stc[y - 2 * SS:y + 2 * SS, xx - 2 * SS:xx + 2 * SS].reshape(-1, 3)
            arr.append([int(v) for v in np.median(patch, axis=0)[::-1]])
    outline_l = np.c_[-half_l[sel], s_px[sel]]
    outline_r = np.c_[half_r[sel], s_px[sel]]
    save_img(f"hand_{name}_{label}_straight.png", cv2.resize(stc[: , :], None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
    return {
        "label": label, "angle_deg": round(float(ang), 3), "axis_offset_px": round(axis_offset_px, 2), "length_px": round(float(s_px[sel].max()), 2),
        "tail_px": round(float(-s_px[sel].min()), 2),
        "left_edge_px": [[round(float(x), 2), round(float(y), 2)] for x, y in outline_l[::2]],
        "right_edge_px": [[round(float(x), 2), round(float(y), 2)] for x, y in outline_r[::2]],
        "stations_px": [round(float(s), 2) for s in stations],
        "left_rgb": left_c, "right_rgb": right_c,
    }


def run(name="front_a"):
    cal = load_json("calibration.json")["photos"][name]
    fr = Frame(cal["centre_px"][0], cal["centre_px"][1], cal["dial_edge_radius_px"])
    pivot = (fr.cx, fr.cy)
    im = load_rgba(name)
    red8, opened = masks(im, fr)
    save_img(f"hands_{name}_mask.png", np.dstack([opened, opened, red8]))

    hands = []
    comps = components(opened, 4000)
    comps.sort(key=lambda c: -np.hypot(*(np.argwhere(c[0]).max(0) - np.argwhere(c[0]).min(0))))
    for k, (m, st) in enumerate(comps[:2]):
        # grow the opened mask back by 3 px to restore the rounded ends, then analyse
        mm = cv2.dilate(m.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) > 0
        _, length = rough_angle(mm, pivot)
        label = "minute" if length > 260 else "hour"
        h = analyse_silver(name, im, fr, mm, pivot, label)
        print(label, {k_: h[k_] for k_ in ("angle_deg", "axis_offset_px", "length_px", "tail_px")})
        hands.append(h)
    return {"photo": name, "hands": hands}


if __name__ == "__main__":
    res = run("front_a")
    save_json("hands_raw.json", res)
