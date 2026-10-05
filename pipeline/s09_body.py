"""Stage 9 — body: case, lugs, crown and bracelet.

Polished steel is made of flat facets, each with an almost constant tone in the photo, so it can be reproduced exactly as
nested tonal regions ("stacked thresholds"):

  base      = the alpha silhouette (sub-pixel iso-line of the alpha channel), filled with the darkest tone
  level k   = every pixel at least as bright as threshold k, filled with the mean colour of its tone band

Painting the levels from dark to bright rebuilds the photo's tonal map as pure vector shapes, and the region boundaries ARE the
edges of the facets / link gaps (the edge-detection result, in closed form). Thresholds come from 1-D k-means on the metal luminance.
Anything inside the fluted bezel (r < 379 px) is excluded: the dial, flutes and hands are separate layers.
"""
from __future__ import annotations

import cv2
import numpy as np

from lib import *
import vec

K_LEVELS = 8
UP = 2                    # potrace grid supersampling
R_INNER_PX = 379.0        # metal begins outside the fluted ring
GRID = 2.0                # path coordinates are integers on a grid of 1/2 photo pixel


def run(name="front_a", K=K_LEVELS):
    cal = load_json("calibration.json")["photos"][name]
    fr = Frame(cal["centre_px"][0], cal["centre_px"][1], cal["dial_edge_radius_px"])
    im = load_rgba(name)
    bgr, alpha = im[..., :3], im[..., 3]
    h, w = alpha.shape
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    yy, xx = np.mgrid[:h, :w]
    rad = np.hypot(xx - fr.cx, yy - fr.cy)
    inside = alpha > 127
    metal = inside & (rad > R_INNER_PX)

    # tone thresholds (k-means on luminance of the metal)
    gs = cv2.bilateralFilter(gray, 7, 25, 5)
    vals = gs[metal].reshape(-1, 1).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.3)
    _, _, cent = cv2.kmeans(vals[::5], K, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    cent = np.sort(cent.ravel())
    thr = (cent[1:] + cent[:-1]) / 2
    band = np.digitize(gs, thr)
    colours = []
    for k in range(K):
        sel = metal & (band == k)
        c = np.median(bgr[sel], axis=0)[::-1] if sel.sum() else np.array([cent[k]] * 3)
        colours.append([int(v) for v in c])
    print("tone colours (dark->light):", colours)

    scale = UP
    def up(m):
        return cv2.resize(m.astype(np.uint8), (w * scale, h * scale), interpolation=cv2.INTER_NEAREST) > 0

    def smooth_mask(m):
        """light smoothing at the potrace grid: removes 1-px speckle but keeps facet corners"""
        u = cv2.resize(m.astype(np.float32), (w * scale, h * scale), interpolation=cv2.INTER_LINEAR)
        u = cv2.GaussianBlur(u, (0, 0), 0.9 * scale / 2)
        return u > 0.5

    layers = []
    # base silhouette from the alpha channel at 2x (sub-pixel)
    a_up = cv2.resize(alpha.astype(np.float32), (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
    base_mask = (a_up > 127) & ~(cv2.resize(rad.astype(np.float32), (w * scale, h * scale)) <= R_INNER_PX * 1.0 - 0)  # ring-shaped metal
    full_mask = a_up > 127
    layers.append({"name": "silhouette", "colour": colours[0], "mask": full_mask})
    sizes = []
    for k in range(1, K):
        m = metal & (gs >= thr[k - 1])
        # drop specks
        n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
        keep = np.zeros_like(m)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] >= 6:
                keep |= lab == i
        # fill tiny holes
        inv = ~keep
        n, lab, st, _ = cv2.connectedComponentsWithStats(inv.astype(np.uint8), 4)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < 6:
                keep |= lab == i
        layers.append({"name": f"tone{k}", "colour": colours[k], "mask": smooth_mask(keep) & full_mask})

    out = []
    total = 0
    for L in layers:
        paths = vec.trace_bitmap(L["mask"], scale, origin=(0, 0), turd=10, alphamax=1.15, opttol=1.0)
        # integer grid = 2 x photo pixels, origin at the dial centre; relative commands -> compact
        tx = lambda p: ((p[0] - fr.cx) * GRID, (p[1] - fr.cy) * GRID)
        d = vec.path_d_rel(paths, tx=tx)
        out.append({"name": L["name"], "fill": "#%02X%02X%02X" % tuple(L["colour"]), "d": d})
        total += len(d)
        print(f'{L["name"]:10s} fill {out[-1]["fill"]}  paths {len(paths):5d}  chars {len(d):8d}')
    print("total path chars:", total)
    bb = [int(np.nonzero(inside)[1].min()), int(np.nonzero(inside)[0].min()), int(np.nonzero(inside)[1].max()), int(np.nonzero(inside)[0].max())]
    ub = [round(float((bb[0] - fr.cx) * fr.k), 1), round(float((bb[1] - fr.cy) * fr.k), 1), round(float((bb[2] - fr.cx) * fr.k), 1), round(float((bb[3] - fr.cy) * fr.k), 1)]
    save_json("body.json", {"grid_per_px": GRID, "unit_bbox": ub, "levels": out, "inner_radius_units": round(R_INNER_PX * fr.k, 2), "thresholds": [float(t) for t in thr]})
    return out


if __name__ == "__main__":
    run()
