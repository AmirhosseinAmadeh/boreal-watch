"""Stage 8 — appearance measurements that are not geometry: ink colours per feature class, and the dial's two-lobe shading.

* colours   : median RGB of the *core* of each printed feature (ink > 0.97), so anti-aliased edge pixels do not dilute the colour
* shading   : with print, ticks and hands masked, the median dial colour in 5-degree wedges (72 samples) for the main dial and for the
              pale chapter band. The two bright lobes sit at ~105 and ~257 deg.
The date window geometry (72.5 x 55 px, pale-blue rim 3.6 px, plate gradient, digit block 22 x 35 px) was read from edge profiles through
its centre row/column; the numbers are in s11_build.py.
"""
from __future__ import annotations

import cv2
import numpy as np

from lib import *
import s04_dial_primitives as s4


def run(name="front_a"):
    cal = load_json("calibration.json")["photos"][name]
    fr = Frame(cal["centre_px"][0], cal["centre_px"][1], cal["dial_edge_radius_px"])
    im = load_rgba(name)
    bgr = im[..., :3]
    ink, h = s4.build_ink(name, fr, im)
    prim = load_json("dial_primitives_px.json")
    yy, xx = np.mgrid[:bgr.shape[0], :bgr.shape[1]]
    rad = np.hypot(xx - fr.cx, yy - fr.cy)
    ang = np.degrees(np.arctan2(xx - fr.cx, -(yy - fr.cy))) % 360
    core = ink > 0.97
    med = lambda m: [int(v) for v in np.median(bgr[m], axis=0)[::-1]] if m.sum() else None
    out = {}
    for i, r in enumerate(prim["rings"]):
        out[f"ring{i}"] = med(core & (np.abs(rad - r["r_px"]) < 1.0) & ~h)
    for row, (rlo, rhi) in {"inner": (250, 264), "outer": (324, 336)}.items():
        for cls, f in (("1min", lambda k: k % 5 != 0), ("5min", lambda k: k % 5 == 0)):
            sel = np.zeros_like(core)
            for k in range(60):
                if f(k):
                    a = 6 * k + prim["tick_rows"][row]["offset_deg"]
                    sel |= (np.abs(((ang - a) + 180) % 360 - 180) < 0.18) & (rad > rlo) & (rad < rhi)
            out[f"tick_{row}_{cls}"] = med(sel & core & ~h)
    rays = np.zeros_like(core)
    for a in range(0, 360, 30):
        rays |= (np.abs(((ang - a) + 180) % 360 - 180) < 0.3) & (rad > 82) & (rad < 108)
    out["rays"] = med(rays & core & ~h)
    out["minute_labels"] = med(core & (rad > 276) & (rad < 293) & ~h)
    out["hour_numerals"] = med(core & (rad > 195) & (rad < 228) & (ang > 170) & (ang < 190) & ~h)
    out["logo"] = med(core & (yy > 800) & (yy < 826) & (xx > 880) & (xx < 985) & ~h)
    save_json("colours.json", out)

    # two-lobe shading
    raw = bgr.astype(np.float32)
    valid = (cv2.dilate((ink > 0.08).astype(np.uint8), np.ones((5, 5), np.uint8)) == 0) & (~h)
    NA, RM = 720, 345
    pol = lambda a: polar_clock(a, fr.cx, fr.cy, RM, NA, cv2.INTER_LINEAR)
    V = pol(valid.astype(np.float32)) > 0.99
    ch = [pol(raw[..., i]) for i in range(3)]

    def profile(lo, hi, step=5):
        res = []
        for a in range(0, 360, step):
            rows = np.arange(int((a - step / 2) * NA / 360), int((a + step / 2) * NA / 360)) % NA
            sel = V[rows][:, lo:hi]
            res.append(None if sel.sum() < 40 else [int(np.median(ch[i][rows][:, lo:hi][sel])) for i in (2, 1, 0)])
        return res

    def fill(p):
        p = [None if x is None else np.array(x, float) for x in p]
        n = len(p)
        for i in range(n):
            if p[i] is None:
                j = k = 1
                while p[(i - j) % n] is None: j += 1
                while p[(i + k) % n] is None: k += 1
                p[i] = (p[(i - j) % n] * k + p[(i + k) % n] * j) / (j + k)
        return [[int(round(v)) for v in x] for x in p]

    save_json("dial_shading.json", {"step_deg": 5, "main_rgb": fill(profile(60, 320)), "outer_rgb": fill(profile(326, 341))})
    print("colours and shading written")


if __name__ == "__main__":
    run()
