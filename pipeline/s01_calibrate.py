"""Stage 1 — calibrate: find the exact dial centre and every concentric ring.

Idea: the dial is a stack of concentric circles. If the centre is right, the *median over all angles* of the
radial luminance profile is razor sharp (hands, numerals and ticks are sparse in angle, so the median ignores
them). We therefore search for the centre that maximises the sharpness of that profile, then read every ring
radius off the profile and confirm each ring individually by fitting a circle to its per-angle edge points.
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy.optimize import minimize
from scipy.signal import find_peaks

from lib import *

PHOTOS = ["front_a", "front_b"]


def refine_center(gray, c0, lo, hi, rmax, n_angles=1440):
    def score(c):
        p = to_polar(gray, c[0], c[1], rmax, n_angles, cv2.INTER_LINEAR)
        d = np.diff(np.median(p[:, lo:hi], axis=0))
        return -float(np.sum(d * d))

    res = minimize(score, c0, method="Nelder-Mead", options={"xatol": 0.005, "fatol": 1e-3})
    return res.x


def blue_mask(im):
    b, g, r = [im[..., i].astype(int) for i in range(3)]
    return ((b - r) > 35) & (im[..., 3] > 128)


def edge_points(gray, cx, cy, r_lo, r_hi, n_angles=1800, polarity=0, upsample=8):
    """Per-angle sub-pixel position of the strongest radial edge in [r_lo, r_hi] (px).
    polarity: +1 rising (dark->light outward), -1 falling, 0 either."""
    rmax = int(r_hi + 8)
    p = to_polar(gray, cx, cy, rmax, n_angles, cv2.INTER_CUBIC)
    p = cv2.GaussianBlur(p, (0, 0), 0.8)
    big = cv2.resize(p[:, r_lo - 4:r_hi + 4], None, fx=upsample, fy=1, interpolation=cv2.INTER_CUBIC)
    g = np.gradient(big, axis=1)
    g = g if polarity == 0 else (g if polarity > 0 else -g)
    idx = np.argmax(np.abs(g) if polarity == 0 else g, axis=1)
    r = (idx / upsample) + r_lo - 4
    ang = np.arange(n_angles) * 2 * np.pi / n_angles
    return cx + r * np.cos(ang), cy + r * np.sin(ang), r


def run():
    out = {"photos": {}}
    for name in PHOTOS:
        im = load_rgba(name)
        gray = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
        m = blue_mask(im)
        m8 = cv2.morphologyEx((m * 255).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        cnts, _ = cv2.findContours(m8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cnts, key=cv2.contourArea)
        (x0, y0), r0 = cv2.minEnclosingCircle(c)
        s = r0 / 346.36                      # scale vs front_a, used to pick radial windows
        rmax = int(560 * s)
        lo, hi = int(60 * s), int(350 * s)
        cx, cy = refine_center(gray, (x0, y0), lo, hi, rmax)

        # 1-D profile (4x radial oversampling) and its ring peaks
        S = 4
        p = to_polar(gray, cx, cy, rmax, 1440, cv2.INTER_CUBIC)
        p4 = cv2.resize(p, (rmax * S, p.shape[0]), interpolation=cv2.INTER_CUBIC)
        prof = np.median(p4, axis=0)
        sm = cv2.GaussianBlur(prof.reshape(1, -1), (0, 0), sigmaX=10).ravel()
        pk, _ = find_peaks(prof - sm, prominence=40, distance=3 * S)
        rings = [float(i / S) for i in pk if i / S < 345 * s]

        # dial edge = sharpest blue->metal transition, circle-fitted per angle
        xs, ys, rr = edge_points(gray, cx, cy, int(330 * s), int(356 * s), polarity=+1)
        ex, ey, er, erms, keep = robust_circle_fit(xs, ys)
        out["photos"][name] = {
            "size": list(im.shape[:2]),
            "centre_px": [round(float(cx), 3), round(float(cy), 3)],
            "centre_from_dial_edge_px": [round(float(ex), 3), round(float(ey), 3)],
            "dial_edge_radius_px": round(float(er), 3),
            "dial_edge_rms_px": round(float(erms), 3),
            "ring_peaks_px": [round(r, 2) for r in rings],
            "ring_peaks_ratio": [round(r / er, 4) for r in rings],
        }
        print(name, out["photos"][name])
    save_json("calibration.json", out)
    return out


if __name__ == "__main__":
    run()
