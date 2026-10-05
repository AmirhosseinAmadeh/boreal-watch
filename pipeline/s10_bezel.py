"""Stage 10 — fluted bezel (120 teeth) and the thin ring between dial and teeth.

Teeth are periodic, so we measure one tooth precisely (median of 120 aligned polar patches), then place it 120 times.
Per-tooth colours capture the photo's specular pattern: the site can rotate that pattern when the light moves.
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import uniform_filter1d

from lib import *

NA = 14400


def run(name="front_a"):
    cal = load_json("calibration.json")["photos"][name]
    fr = Frame(cal["centre_px"][0], cal["centre_px"][1], cal["dial_edge_radius_px"])
    im = load_rgba(name)
    bgr = im[..., :3]
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    per = NA / 360
    P = polar_clock(g, fr.cx, fr.cy, 470, NA, cv2.INTER_CUBIC)

    # groove positions -> regular 3 deg grid
    sig = P[:, 356:392].mean(axis=1)
    hp = sig - uniform_filter1d(sig, NA // 40, mode="wrap")
    pk, _ = find_peaks(-hp, distance=NA // 200, prominence=2)
    ang = []
    for p in pk:
        y0, y1, y2 = hp[(p - 1) % NA], hp[p], hp[(p + 1) % NA]
        ang.append(((p + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-9)) % NA) * 360 / NA)
    ang = np.array(ang)
    k = np.arange(len(ang))
    a0 = float(np.median(((ang - 3 * k) + 180) % 360 - 180))
    rms = float(np.sqrt(((((ang - (a0 + 3 * k)) + 180) % 360 - 180) ** 2).mean()))

    # one tooth (aligned on tooth centre)
    half = int(1.5 * per)
    pat = []
    for kk in range(120):
        c = int(round(((a0 + 1.5 + 3 * kk) % 360) * per))
        pat.append(P[(np.arange(c - half, c + half + 1)) % NA, 330:440])
    T = np.median(np.array(pat), axis=0)                 # [angle, radius]
    mid = T[half]
    # radial extent of the tooth: where the centre-line luminance is within the "tooth plateau"
    plateau = np.median(mid[352 - 330:372 - 330])
    r = np.arange(330, 440)
    inside = np.abs(mid - plateau) < 0.22 * plateau
    runs = []
    i = 0
    while i < len(inside):
        if inside[i]:
            j = i
            while j < len(inside) and inside[j]:
                j += 1
            runs.append((r[i], r[j - 1] + 1))
            i = j
        else:
            i += 1
    tooth_run = max([x for x in runs if 340 < x[0] < 360], key=lambda x: x[1] - x[0])
    # groove width across the tooth at the mid radius
    prof = T[:, 365 - 330]
    gl = prof < (plateau * 0.8)
    edge_l = np.nonzero(~gl)[0].min(); edge_r = np.nonzero(~gl)[0].max()
    groove_deg = (3.0 - (edge_r - edge_l + 1) / per)
    # tooth colours
    def tooth_colour(kk, r0=357, r1=372):
        A = a0 + 1.5 + 3 * kk
        pts = []
        for rr in np.arange(r0, r1, 1.0):
            for da in np.linspace(-0.45, 0.45, 5):
                a = np.radians(A + da)
                x, y = fr.cx + rr * np.sin(a), fr.cy - rr * np.cos(a)
                pts.append(bgr[int(round(y)), int(round(x))])
        return [int(v) for v in np.median(np.array(pts), axis=0)[::-1]]
    teeth = [tooth_colour(kk) for kk in range(120)]
    # groove colour
    gc = []
    for kk in range(120):
        A = a0 + 3 * kk
        a = np.radians(A)
        for rr in np.arange(357, 372, 2.0):
            x, y = fr.cx + rr * np.sin(a), fr.cy - rr * np.cos(a)
            gc.append(bgr[int(round(y)), int(round(x))])
    groove_col = [int(v) for v in np.median(np.array(gc), axis=0)[::-1]]

    # ring between dial edge and teeth: colour per 5 deg
    ring_in = []
    for A in range(0, 360, 5):
        pts = []
        for rr in np.arange(344.5, 350.0, 0.5):
            for da in np.linspace(-2, 2, 9):
                a = np.radians(A + da)
                x, y = fr.cx + rr * np.sin(a), fr.cy - rr * np.cos(a)
                pts.append(bgr[int(round(y)), int(round(x))])
        ring_in.append([int(v) for v in np.median(np.array(pts), axis=0)[::-1]])
    # tooth bevel: luminance profile across the tooth at its centre radius (left edge highlight)
    ang_prof = [round(float(v), 1) for v in T[:, 365 - 330][::5]]
    out = {
        "count": 120, "pitch_deg": 3.0, "first_groove_deg": round(a0, 3), "grid_rms_deg": round(rms, 3),
        "tooth_r_in_px": float(tooth_run[0]), "tooth_r_out_px": float(tooth_run[1]),
        "groove_deg": round(float(groove_deg), 3), "groove_px_at_mid": round(float(groove_deg * np.pi / 180 * 364), 2),
        "tooth_colours": teeth, "groove_colour": groove_col, "inner_ring_colours_5deg": ring_in,
        "tooth_angular_profile_at_365": ang_prof, "plateau_luminance": float(plateau),
    }
    print({k_: v for k_, v in out.items() if k_ not in ("tooth_colours", "inner_ring_colours_5deg", "tooth_angular_profile_at_365")})
    save_json("bezel_px.json", out)
    return out


if __name__ == "__main__":
    run()
