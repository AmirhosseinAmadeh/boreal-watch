"""Shared helpers for the edge-detection pipeline.

Conventions
-----------
* Pixel space: x right, y down, origin top-left, units = photo pixels of the 1920px source.
* Dial space ("units"): origin at the dial centre, y down, 1 unit = DIAL_R / 200, so the outer
  edge of the dial is 200 units. This is the space `main.js` already uses (viewBox -200..200).
* Clock angle: 0 = 12 o'clock, increasing clockwise, in degrees.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source"
OUT = ROOT / "pipeline" / "out"
OUT.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- io
def load_rgba(name: str = "front_a") -> np.ndarray:
    im = cv2.imread(str(SRC / f"{name}.png"), cv2.IMREAD_UNCHANGED)
    if im is None:
        raise FileNotFoundError(f"{name}.png missing in source/ — see PIPELINE.md, stage 0")
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im


def save_json(name: str, data) -> Path:
    p = OUT / name
    p.write_text(json.dumps(data, indent=1), encoding="utf-8")
    return p


def load_json(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def save_img(name: str, img: np.ndarray) -> Path:
    p = OUT / name
    cv2.imwrite(str(p), img)
    return p


# --------------------------------------------------------------------------- geometry
def clock_to_xy(r, a_deg, cx=0.0, cy=0.0):
    """Clock angle (0 = up, clockwise) + radius -> x, y (y down)."""
    a = np.radians(a_deg)
    return cx + r * np.sin(a), cy - r * np.cos(a)


def xy_to_clock(x, y, cx=0.0, cy=0.0):
    """x, y -> (radius, clock angle in [0, 360))."""
    dx, dy = np.asarray(x) - cx, np.asarray(y) - cy
    return np.hypot(dx, dy), np.degrees(np.arctan2(dx, -dy)) % 360.0


def wrap180(a):
    return (np.asarray(a) + 180.0) % 360.0 - 180.0


class Frame:
    """Maps between photo pixels and dial units for one photo."""

    def __init__(self, cx: float, cy: float, dial_r_px: float):
        self.cx, self.cy, self.R = cx, cy, dial_r_px
        self.k = 200.0 / dial_r_px  # px -> units

    def to_units(self, x, y):
        return (np.asarray(x) - self.cx) * self.k, (np.asarray(y) - self.cy) * self.k

    def to_px(self, u, v):
        return np.asarray(u) / self.k + self.cx, np.asarray(v) / self.k + self.cy

    def len_units(self, px):
        return np.asarray(px) * self.k


# --------------------------------------------------------------------------- polar
def to_polar(img: np.ndarray, cx: float, cy: float, rmax: int, n_angles: int = 3600,
             interp=cv2.INTER_CUBIC) -> np.ndarray:
    """Unwrap around (cx, cy): returns array [angle, radius] (rows = clock angle 0..360 cw from 3 o'clock)
    NOTE: cv2.warpPolar starts at +x (3 o'clock); `polar_clock` re-bases it to 12 o'clock."""
    return cv2.warpPolar(img, (rmax, n_angles), (cx, cy), rmax, cv2.WARP_POLAR_LINEAR | interp)


def polar_clock(img: np.ndarray, cx: float, cy: float, rmax: int, n_angles: int = 3600,
                interp=cv2.INTER_CUBIC) -> np.ndarray:
    """Polar view with row index = clock angle (0 = 12 o'clock, cw), col index = radius px."""
    p = to_polar(img, cx, cy, rmax, n_angles, interp)
    return np.roll(p, n_angles // 4, axis=0)  # row 0 (3 o'clock) -> 90deg ; shift so row0 = 12 o'clock


def polar_view(p: np.ndarray) -> np.ndarray:
    """Make a human-friendly picture of a polar array: radius on y (outer at top), angle on x."""
    return cv2.rotate(p, cv2.ROTATE_90_COUNTERCLOCKWISE)


def sample(img: np.ndarray, x, y, order=1):
    """Bilinear sample of a single-channel image at float coordinates."""
    return cv2.remap(img, np.asarray(x, np.float32), np.asarray(y, np.float32), cv2.INTER_LINEAR if order == 1 else cv2.INTER_CUBIC,
                     borderMode=cv2.BORDER_REPLICATE)


# --------------------------------------------------------------------------- small numerics
def fwhm(profile: np.ndarray, peak_idx: int, base: float | None = None):
    """Full width at half maximum around a peak in a 1-D profile (in samples, sub-sample precision)."""
    p = np.asarray(profile, float)
    base = np.min(p) if base is None else base
    half = base + (p[peak_idx] - base) / 2
    lo = peak_idx
    while lo > 0 and p[lo] > half:
        lo -= 1
    hi = peak_idx
    while hi < len(p) - 1 and p[hi] > half:
        hi += 1
    # linear interpolation of the crossings
    def cross(i0, i1):
        y0, y1 = p[i0], p[i1]
        return i0 if y1 == y0 else i0 + (half - y0) / (y1 - y0) * (i1 - i0)
    a = cross(lo, lo + 1)
    b = cross(hi - 1, hi)
    return b - a, (a + b) / 2


def circle_fit(xs, ys):
    """Algebraic (Kasa) least-squares circle fit. Returns cx, cy, r, rms residual."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    A = np.c_[2 * xs, 2 * ys, np.ones_like(xs)]
    b = xs ** 2 + ys ** 2
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = sol[0], sol[1]
    r = math.sqrt(sol[2] + cx * cx + cy * cy)
    res = np.hypot(xs - cx, ys - cy) - r
    return cx, cy, r, float(np.sqrt(np.mean(res ** 2)))


def robust_circle_fit(xs, ys, iters=6, k=2.5):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    keep = np.ones(len(xs), bool)
    for _ in range(iters):
        cx, cy, r, rms = circle_fit(xs[keep], ys[keep])
        res = np.abs(np.hypot(xs - cx, ys - cy) - r)
        thr = max(k * np.median(res[keep]) * 1.4826, 0.2)
        nk = res < thr
        if nk.sum() < 10 or (nk == keep).all():
            break
        keep = nk
    return cx, cy, r, rms, keep
