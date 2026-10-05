"""Renders the parametric dial model (what stages 1-5 measured) back to a pixel image, so we can
(a) subtract it from the photo's ink map -> the *residual* is exactly what is not yet explained
    (numerals, text, logo, date window, apex triangle, hub ...), and
(b) score how well the vector model reproduces the photo (see s11_verify.py).
Everything is drawn at 4x supersampling with 3 fractional bits (sub-pixel exact), then box-downsampled.
"""
from __future__ import annotations

import cv2
import numpy as np

from lib import *

SS = 4
FB = 3  # fractional bits for cv2 fixed-point drawing


class Canvas:
    def __init__(self, shape):
        self.h, self.w = shape
        self.img = np.zeros((self.h * SS, self.w * SS), np.float32)

    def _fx(self, pts):
        """photo px (float) -> cv2 fixed-point ints on the supersampled grid. Pixel centres are at +0.5."""
        a = (np.asarray(pts, float) + 0.5) * SS - 0.5
        return np.round(a * (1 << FB)).astype(np.int32)

    def poly(self, pts, value=1.0):
        cv2.fillPoly(self.img, [self._fx(pts)], value, cv2.LINE_AA, FB)

    def ring(self, c, r, stroke):
        cx, cy = self._fx([c])[0]
        cv2.circle(self.img, (int(cx), int(cy)), int(round(r * SS * (1 << FB))), 1.0, max(1, int(round(stroke * SS))), cv2.LINE_AA, FB)

    def segment(self, p0, p1, width):
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        d = p1 - p0; n = np.hypot(*d)
        if n == 0:
            return
        u = d / n; v = np.array([-u[1], u[0]]) * width / 2
        self.poly([p0 + v, p1 + v, p1 - v, p0 - v])

    def result(self):
        return np.clip(cv2.resize(self.img, (self.w, self.h), interpolation=cv2.INTER_AREA), 0, 1)


def clock_pt(c, r, a_deg):
    a = np.radians(a_deg)
    return np.array([c[0] + r * np.sin(a), c[1] - r * np.cos(a)])


def draw_dial_model(cv: Canvas, c, prim, lines):
    for ring in prim["rings"]:
        cv.ring(c, ring["r_px"], ring["stroke_px"])
    for row in prim["tick_rows"].values():
        for k in range(60):
            cls = row["five_min"] if k % 5 == 0 else row["one_min"]
            a = 6 * k + row["offset_deg"]
            p0, p1 = clock_pt(c, cls["r0_px"], a), clock_pt(c, cls["r1_px"], a)
            cv.segment(p0, p1, cls["width_px"])
    ry = prim["rays"]
    pw = np.array(ry["width_vs_r_px"], float)
    slope, icpt = np.polyfit(pw[:, 0], pw[:, 1], 1)
    r0, r1 = ry["radial_run_px"]
    for a in ry["angles_deg"]:
        aa = np.radians(a)
        t = np.array([np.sin(aa), -np.cos(aa)]); nrm = np.array([np.cos(aa), np.sin(aa)])
        pts = [np.array(c) + r * t + s * (slope * r + icpt) / 2 * nrm for r, s in ((r0, -1), (r1, -1), (r1, 1), (r0, 1))]
        cv.poly(pts)
    for l in lines:
        cv.segment(l["end_a_px"], l["end_b_px"], l["stroke_px"])


def render(shape, c, prim, lines):
    cv = Canvas(shape)
    draw_dial_model(cv, c, prim, lines)
    return cv.result()
