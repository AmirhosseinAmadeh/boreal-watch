"""Stage 12 — verification: render the extracted vector model onto the photo's pixel grid and measure the difference.

Metrics (all on the 1920 px photo, hands excluded where noted):
  silhouette IoU     alpha>0.5 of the photo vs the rendered body
  metal luminance    mean abs error on the case / bracelet
  dial ink IoU       white print (R channel) vs rendered print, away from the hands
  dial edge chamfer  mean distance (px) from photo ink edges to the nearest rendered ink edge, and back
  hands IoU          photo hand mask vs rendered hands
Writes pipeline/out/verify.json and pipeline/out/verify_diff.png (git-ignored).
"""
from __future__ import annotations

import cv2
import numpy as np
import resvg_py

from lib import *
import svg_compose
import s03_hands as hands
import s04_dial_primitives as s4


def render(parts, size=(1920, 1920), pose=None, **kw):
    core = load_json("build_core.json")
    body = load_json("body.json")
    svg = svg_compose.compose(core, body, pose=pose, size=size[0], parts=parts, frame_px=size, **kw)
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg))
    im = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED)
    return im


def chamfer(a, b):
    """mean distance from edge pixels of a to the nearest edge pixel of b"""
    dt = cv2.distanceTransform((b == 0).astype(np.uint8), cv2.DIST_L2, 5)
    return float(dt[a > 0].mean()) if (a > 0).any() else 0.0


def run():
    cal = load_json("calibration.json")["photos"]["front_a"]
    fr = Frame(cal["centre_px"][0], cal["centre_px"][1], cal["dial_edge_radius_px"])
    photo = load_rgba("front_a")
    alpha = photo[..., 3] > 127
    res = {}
    full = render(("body", "bezel", "dial", "hands"), pose={"hour": 303.45, "minute": 60.18, "second": 0.23})
    save_img("verify_render.png", full)
    ra = full[..., 3] > 127
    res["silhouette_iou"] = round(float((alpha & ra).sum() / (alpha | ra).sum()), 4)

    yy, xx = np.mgrid[:1920, :1920]
    rad = np.hypot(xx - fr.cx, yy - fr.cy)
    metal = alpha & (rad > 380)
    g_ph = cv2.cvtColor(photo[..., :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
    g_rd = cv2.cvtColor(full[..., :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
    res["metal_luminance_mae"] = round(float(np.abs(g_ph - g_rd)[metal].mean()), 2)

    # dial print: compare the red channel (white print on blue)
    dial = render(("dial",))
    ink_ph, hm = s4.build_ink("front_a", fr, photo)
    ink_rd = np.clip((dial[..., 2].astype(np.float32) - 25) / 165, 0, 1)
    ok = (rad < fr.R * 0.985) & ~hm & ~(cv2.dilate(hm.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0)
    a, b = ink_ph > 0.5, ink_rd > 0.5
    res["dial_ink_iou"] = round(float((a & b & ok).sum() / (((a | b) & ok).sum())), 4)
    res["dial_ink_precision"] = round(float((a & b & ok).sum() / (b & ok).sum()), 4)
    res["dial_ink_recall"] = round(float((a & b & ok).sum() / (a & ok).sum()), 4)
    ea = cv2.Canny((np.clip(ink_ph, 0, 1) * 255).astype(np.uint8), 80, 160) * ok
    eb = cv2.Canny((np.clip(ink_rd, 0, 1) * 255).astype(np.uint8), 80, 160) * ok
    res["dial_edge_chamfer_px"] = {"photo_to_model": round(chamfer(ea, eb), 3), "model_to_photo": round(chamfer(eb, ea), 3)}

    # hands
    red8, silver = hands.masks(photo, fr)
    hp = silver > 0
    hd = render(("hands",), pose={"hour": 303.45, "minute": 60.18, "second": 0.23})
    hr = hd[..., 3] > 127
    hr_s = hr & ~(cv2.dilate(red8, np.ones((9, 9), np.uint8)) > 0)
    comp = hp & (rad < fr.R)
    res["hands_iou"] = round(float((comp & hr_s).sum() / ((comp | hr_s).sum())), 4)

    # diff picture: photo | render | |diff|
    d = np.abs(photo[..., :3].astype(int) - full[..., :3].astype(int)).sum(axis=2) / 3
    d = np.clip(d * 3, 0, 255).astype(np.uint8)
    both = np.hstack([photo[500:1450, 420:1500, :3], full[500:1450, 420:1500, :3], cv2.cvtColor(d[500:1450, 420:1500], cv2.COLOR_GRAY2BGR)])
    save_img("verify_diff.png", cv2.resize(both, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA))
    print(res)
    save_json("verify.json", res)
    return res


if __name__ == "__main__":
    run()
