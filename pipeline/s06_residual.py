"""Stage 6 — residual.

residual = photo ink  -  (parametric model, slightly dilated)
Whatever remains was not explained by rings / ticks / rays / chords: numerals, text, the logo, the date window,
the apex triangle, and the hub. We label the connected components so the next stages can classify and trace them.
"""
from __future__ import annotations

import cv2
import numpy as np

from lib import *
import model_px
import s04_dial_primitives as s4


def run(name="front_a"):
    cal = load_json("calibration.json")["photos"][name]
    fr = Frame(cal["centre_px"][0], cal["centre_px"][1], cal["dial_edge_radius_px"])
    prim = load_json("dial_primitives_px.json")
    lines = load_json("lines_px.json")["lines"]
    im = load_rgba(name)
    ink, hmask = s4.build_ink(name, fr, im)
    mdl = model_px.render(ink.shape, (fr.cx, fr.cy), prim, lines)
    save_img(f"model_{name}.png", (mdl * 255).astype(np.uint8))

    grown = cv2.dilate(mdl, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    resid = np.clip(ink - grown, 0, 1)
    yy, xx = np.mgrid[:ink.shape[0], :ink.shape[1]]
    rad = np.hypot(xx - fr.cx, yy - fr.cy)
    resid[rad > fr.R * 0.985] = 0
    resid[hmask] = 0
    save_img(f"residual_{name}.png", (resid * 255).astype(np.uint8))

    # model quality: IoU of binarised ink vs model inside the dial, away from hands and residual-explained stuff
    inside = (rad < fr.R * 0.985) & ~hmask
    a, b = ink[inside] > 0.5, mdl[inside] > 0.5
    print(f"model vs ink  precision {(a & b).sum() / b.sum():.3f}  recall-of-model-region {(a & b).sum() / (a | b).sum():.3f}")
    # of the model pixels, what share is truly ink? (precision = model is not hallucinating)
    # components of the residual
    r8 = (resid > 0.5).astype(np.uint8) * 255
    r8 = cv2.morphologyEx(r8, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, lab, stats, cent = cv2.connectedComponentsWithStats(r8, 8)
    comps = []
    for i in range(1, n):
        x, y, w, h, a_ = stats[i]
        if a_ < 12:
            continue
        cxm, cym = cent[i]
        r = float(np.hypot(cxm - fr.cx, cym - fr.cy))
        ang = float(np.degrees(np.arctan2(cxm - fr.cx, -(cym - fr.cy))) % 360)
        comps.append({"id": i, "bbox": [int(x), int(y), int(w), int(h)], "area": int(a_), "r_px": round(r, 1), "clock_deg": round(ang, 1)})
    comps.sort(key=lambda c: (c["r_px"] // 40, c["clock_deg"]))
    print(len(comps), "residual components")
    save_json("residual_components.json", {"components": comps})
    np.save(OUT / "residual_labels.npy", lab.astype(np.int32))
    vis = cv2.cvtColor((np.clip(ink, 0, 1) * 90).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    vis[..., 1] = np.maximum(vis[..., 1], (mdl * 160).astype(np.uint8))          # model = green
    vis[..., 2] = np.maximum(vis[..., 2], (resid * 255).astype(np.uint8))        # residual = red
    save_img(f"residual_{name}_overlay.png", vis)
    return comps


if __name__ == "__main__":
    run("front_a")
