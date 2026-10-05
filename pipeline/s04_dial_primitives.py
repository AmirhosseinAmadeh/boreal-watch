"""Stage 4 — regular dial primitives: rings, minute ticks, hour spikes ("rays").

Works in polar space where all of these become axis-aligned and can be measured by simple statistics:
  * a concentric ring is a horizontal line  -> radius = centroid, stroke = FWHM, coverage = fraction of angles inked
  * a radial tick is a vertical bar         -> angle = centroid, width = FWHM, extent = radial run of the stacked profile
  * a ray is a vertical tapered bar         -> stack the clean ones, read half-width as a function of radius
All numbers are first measured in photo pixels and converted to dial units (R = 200) at the end.
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy.signal import find_peaks

from lib import *
import s03_hands as hands

NA = 7200
PER = NA / 360


def build_ink(name, fr, im):
    red8, opened = hands.masks(im, fr)
    hmask = cv2.dilate(cv2.bitwise_or(red8, opened), np.ones((7, 7), np.uint8)) > 0
    R = im[..., 2].astype(np.float32)
    ink = np.clip((R - 25) / (190 - 25), 0, 1)
    ink[hmask] = 0
    return ink, hmask


def runs(profile, thr, scale):
    m = profile > thr
    out, i = [], 0
    while i < len(m):
        if m[i]:
            j = i
            while j < len(m) and m[j]:
                j += 1
            out.append((i / scale, j / scale))
            i = j
        else:
            i += 1
    return out


def ring_stats(Pu, scale):
    """Pu = ink polar upsampled radially by `scale`. Returns a dict per ring."""
    prof = np.median(Pu, axis=0)
    pk, _ = find_peaks(prof, height=0.6, distance=3 * scale)
    rings = []
    for i in pk:
        r = i / scale
        if not (40 < r < 300):
            continue
        w, centre = fwhm(prof, i, base=0.0)
        lo, hi = int((r - 6) * scale), int((r + 6) * scale)
        seg = prof[lo:hi]
        cen = (seg * np.arange(lo, hi)).sum() / seg.sum() / scale
        # coverage: share of angles where the ring is inked at its centre radius
        col = Pu[:, int(round(cen * scale))]
        coverage = float((col > 0.5).mean())
        rings.append({"r_px": round(float(cen), 3), "stroke_px": round(float(w / scale), 3), "coverage": round(coverage, 3)})
    return rings


def tick_row(P, r_lo, r_hi, per=PER):
    """Angular profile of a row of ticks -> list of (index, centre_deg_offset, width_px)."""
    prof = P[:, int(r_lo):int(r_hi)].mean(axis=1)
    rmid = (r_lo + r_hi) / 2
    out = []
    for k in range(60):
        c = int(round(6 * k * per)); w = int(1.6 * per)
        seg = prof[(np.arange(c - w, c + w)) % NA]
        pk = seg.max()
        if pk < 0.3:
            out.append(None)
            continue
        half = seg.min() + (pk - seg.min()) / 2
        ii = np.nonzero(seg > half)[0]
        lo, hi = ii.min(), ii.max()
        cen = ((seg[lo:hi + 1] * np.arange(lo, hi + 1)).sum() / seg[lo:hi + 1].sum() - w) / per
        out.append({"k": k, "centre_deg": float(cen), "width_px": float((hi - lo + 1) / per * np.pi / 180 * rmid)})
    return out


def tick_extent(P4, k_list, r_lo, r_hi, per=PER, scale=4, thr=0.5):
    """Radial extent of the ticks in `k_list`: stack their (angle-maxed) radial profiles, take the median run."""
    starts, ends = [], []
    for k in k_list:
        c = int(round(6 * k * per)); w = int(0.8 * per)
        prof = P4[(np.arange(c - w, c + w)) % NA].max(axis=0)
        rr = [r for r in runs(prof, thr, scale) if r[1] > r_lo and r[0] < r_hi]
        if rr:
            a = min(rr, key=lambda t: abs((t[0] + t[1]) / 2 - (r_lo + r_hi) / 2))
            starts.append(a[0]); ends.append(a[1])
    return (float(np.median(starts)), float(np.median(ends)), len(starts))


def ink_colour(im, mask):
    return [int(v) for v in np.median(im[..., :3][mask], axis=0)[::-1]]


def run(name="front_a"):
    cal = load_json("calibration.json")["photos"][name]
    fr = Frame(cal["centre_px"][0], cal["centre_px"][1], cal["dial_edge_radius_px"])
    im = load_rgba(name)
    ink, hmask = build_ink(name, fr, im)
    RM = 360
    P = polar_clock(ink, fr.cx, fr.cy, RM, NA, cv2.INTER_LINEAR)
    np.save(OUT / "ink_polar.npy", P.astype(np.float32))
    SC = 4
    P4 = cv2.resize(P, (RM * SC, NA), interpolation=cv2.INTER_CUBIC)

    # ---- rings
    rings = ring_stats(P4, SC)
    print("rings:", rings)

    # ---- minute ticks, two rows
    res = {"frame": {"cx": fr.cx, "cy": fr.cy, "R_px": fr.R, "k_units_per_px": fr.k}, "rings": rings}
    rows = {}
    for label, (rlo, rhi) in {"inner": (250, 265), "outer": (324, 334)}.items():
        stats = tick_row(P, rlo, rhi)
        ok = [s for s in stats if s]
        w5 = [s["width_px"] for s in ok if s["k"] % 5 == 0]
        w1 = [s["width_px"] for s in ok if s["k"] % 5]
        off = float(np.median([s["centre_deg"] for s in ok]))
        k1 = [s["k"] for s in ok if s["k"] % 5 and 0.7 * np.median(w1) < s["width_px"] < 1.4 * np.median(w1)]
        k5 = [s["k"] for s in ok if s["k"] % 5 == 0 and 0.7 * np.median(w5) < s["width_px"] < 1.4 * np.median(w5)]
        e1 = tick_extent(P4, k1, rlo - 20, rhi + 20)
        e5 = tick_extent(P4, k5, rlo - 20, rhi + 20)
        # colour: pixels of ticks of this class
        yy, xx = np.mgrid[:im.shape[0], :im.shape[1]]
        rad = np.hypot(xx - fr.cx, yy - fr.cy)
        ang = np.degrees(np.arctan2(xx - fr.cx, -(yy - fr.cy))) % 360
        near5 = np.abs(((ang + 3) % 6) - 3) < 0.3
        sel = (rad > e1[0] + 2) & (rad < e1[1] - 2) & near5 & (ink > 0.95)
        c1 = ink_colour(im, sel & (np.abs(((ang / 6 + 0.5) % 5) - 0.5) > 0.2)) if sel.any() else None
        rows[label] = {
            "offset_deg": round(off, 3),
            "one_min": {"width_px": round(float(np.median(w1)), 2), "r0_px": round(e1[0], 2), "r1_px": round(e1[1], 2), "n": e1[2]},
            "five_min": {"width_px": round(float(np.median(w5)), 2), "r0_px": round(e5[0], 2), "r1_px": round(e5[1], 2), "n": e5[2]},
        }
        print(label, rows[label])
    res["tick_rows"] = rows

    # ---- rays: stack the unobstructed ones, 12 slots at 30 deg
    ray_angles = [a for a in range(0, 360, 30)]
    r0, r1 = 70, 150
    patches, used = [], []
    for a in ray_angles:
        c = int(round(a * PER)); w = int(4 * PER)
        patch = P[(np.arange(c - w, c + w)) % NA, r0:r1]
        # a ray is "clean" if its centre line is fully inked from 80..108
        mid = patch[len(patch) // 2 - 3:len(patch) // 2 + 3].max(axis=0)
        if mid[82 - r0:108 - r0].min() > 0.6:
            patches.append(patch); used.append(a)
    stack = np.median(np.array(patches), axis=0)
    prof_w = []
    for r in range(78, 120):
        col = stack[:, r - r0]
        if col.max() < 0.3:
            continue
        ii = np.nonzero(col > col.max() / 2)[0]
        prof_w.append((r, float((ii.max() - ii.min() + 1) / PER * np.pi / 180 * r)))
    mid = stack[len(stack) // 2 - 3:len(stack) // 2 + 3].max(axis=0)
    rr = runs(mid, 0.5, 1)
    res["rays"] = {"angles_deg": ray_angles, "clean_used": used, "radial_run_px": [round(rr[0][0] + r0, 2), round(rr[0][1] + r0, 2)],
                   "width_vs_r_px": [[r, round(w, 2)] for r, w in prof_w[::2]]}
    print("rays used", used, "run", res["rays"]["radial_run_px"], "width", prof_w[0], prof_w[-1])
    save_json("dial_primitives_px.json", res)
    return res


if __name__ == "__main__":
    run("front_a")
