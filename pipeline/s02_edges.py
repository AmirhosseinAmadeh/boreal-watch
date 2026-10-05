"""Stage 2 — edge atlas.

Three complementary detectors, because no single one fits every material on this watch:

* Canny on luminance (two scales, consensus)  -> case facets, bracelet links, bezel flutes, hand outlines
* Canny on the RED channel                    -> printed dial ink. The dial is blue (R ~ 5-30) and every
                                                 print is white (R ~ 200+), so R is a near-binary drawing
* Scharr gradient magnitude + non-max suppression on R, then sub-pixel iso-contours at 50 % ink level
                                              -> sub-pixel outlines for numerals, text and logo

Writes pipeline/out/edges_*.png (git-ignored: these are derived from Swatch's photo).
"""
from __future__ import annotations

import cv2
import numpy as np

from lib import *


def auto_canny(img8, sigma=0.33, lo_k=None):
    v = np.median(img8[img8 > 0]) if (img8 > 0).any() else np.median(img8)
    lo = int(max(0, (1.0 - sigma) * v))
    hi = int(min(255, (1.0 + sigma) * v))
    return cv2.Canny(img8, lo, hi, L2gradient=True)


def run(name="front_a"):
    im = load_rgba(name)
    bgr, alpha = im[..., :3], im[..., 3]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    red = bgr[..., 2]
    inside = alpha > 128

    # 1. luminance Canny, two scales; keep edges present at both (consensus) + the stronger fine ones
    e1 = cv2.Canny(cv2.GaussianBlur(gray, (0, 0), 1.0), 40, 110, L2gradient=True)
    e2 = cv2.Canny(cv2.GaussianBlur(gray, (0, 0), 2.0), 25, 70, L2gradient=True)
    near2 = cv2.dilate(e2, np.ones((5, 5), np.uint8))
    edges_L = cv2.bitwise_and(e1, near2)
    edges_L[~inside] = 0

    # 2. red-channel Canny for the printed ink
    r_blur = cv2.GaussianBlur(red, (0, 0), 0.9)
    edges_R = cv2.Canny(r_blur, 50, 140, L2gradient=True)

    # 3. Scharr magnitude of R (for visual inspection and for the Hough weights)
    gx = cv2.Scharr(red.astype(np.float32), cv2.CV_32F, 1, 0)
    gy = cv2.Scharr(red.astype(np.float32), cv2.CV_32F, 0, 1)
    mag = np.hypot(gx, gy)
    mag8 = np.clip(mag / np.percentile(mag, 99.5) * 255, 0, 255).astype(np.uint8)

    # 4. visualisation: edges over a dimmed photo (alpha composited on mid-grey)
    bg = np.full_like(bgr, 48)
    a = (alpha[..., None] / 255.0)
    photo = (bgr * a + bg * (1 - a)).astype(np.uint8)
    dim = (photo * 0.35).astype(np.uint8)
    vis = dim.copy()
    vis[edges_L > 0] = (0, 200, 255)       # amber: luminance edges
    vis[edges_R > 0] = (255, 255, 255)     # white: ink edges
    save_img(f"edges_{name}_overlay.png", vis)
    save_img(f"edges_{name}_L.png", edges_L)
    save_img(f"edges_{name}_R.png", edges_R)
    save_img(f"edges_{name}_scharrR.png", mag8)
    print(name, "edge pixels  L:", int((edges_L > 0).sum()), " R:", int((edges_R > 0).sum()))


if __name__ == "__main__":
    run("front_a")
    run("front_b")
