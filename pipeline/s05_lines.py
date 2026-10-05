"""Stage 5 — the straight "compass" lines (the two big triangles and chords).

1. Mask out everything that is not a long straight line: the three rings, the tick rows, the sun rays and the
   printed text zones (they are short or curved) so Hough only sees the long chords.
2. Standard Hough transform (rho 0.25 px, theta 0.05 deg) on the thresholded ink -> candidate lines, non-max suppressed.
3. Refine each candidate by total least squares on the ink pixels within 3 px of it (sub-pixel position and angle).
4. Walk along every refined line and record where ink actually exists -> visible segments (the rest is hidden by the
   hands / numerals / date window, or simply not drawn).
5. Intersect the lines pairwise: the vertices tell us how the figure was constructed (equilateral triangles, etc.).
"""
from __future__ import annotations

import cv2
import numpy as np

from lib import *
import s04_dial_primitives as s4


def candidate_mask(ink, fr, prim):
    h, w = ink.shape
    yy, xx = np.mgrid[:h, :w]
    rad = np.hypot(xx - fr.cx, yy - fr.cy)
    ang = np.degrees(np.arctan2(xx - fr.cx, -(yy - fr.cy))) % 360
    m = (ink > 0.5) & (rad > 20) & (rad < 243)
    for ring in prim["rings"]:
        m &= np.abs(rad - ring["r_px"]) > ring["stroke_px"] / 2 + 3.5
    # sun rays: 12 spikes between the inner ring and r=116
    d30 = np.abs(((ang + 15) % 30) - 15)
    m &= ~((rad > 70) & (rad < 118) & (d30 < 3.5))
    return m


def hough(mask8, rho=1.0, theta_deg=0.1, thresh=100, max_lines=60):
    lines = cv2.HoughLines(mask8, rho, np.radians(theta_deg), thresh)
    return [] if lines is None else [tuple(l[0]) for l in lines]


def suppress(lines, d_rho=6.0, d_theta=np.radians(1.2)):
    kept = []
    for rho, th in lines:
        dup = False
        for r2, t2 in kept:
            dt = abs(((th - t2) + np.pi / 2) % np.pi - np.pi / 2)
            dr = abs(rho - r2) if abs(th - t2) < np.pi / 2 else abs(rho + r2)
            if dt < d_theta and dr < d_rho:
                dup = True
                break
        if not dup:
            kept.append((rho, th))
    return kept


def refine(ink, mask, rho, th, fr, band=3.0):
    h, w = ink.shape
    ys, xs = np.nonzero(mask)
    n = np.array([np.cos(th), np.sin(th)])
    d = xs * n[0] + ys * n[1] - rho
    sel = np.abs(d) < band
    P = np.c_[xs[sel], ys[sel]].astype(float)
    wgt = ink[ys[sel], xs[sel]]
    if len(P) < 40:
        return None
    for _ in range(4):
        mu = (P * wgt[:, None]).sum(0) / wgt.sum()
        C = np.cov((P - mu).T, aweights=wgt)
        evals, evecs = np.linalg.eigh(C)
        dirv = evecs[:, 1]
        nrm = np.array([-dirv[1], dirv[0]])
        dist = (P - mu) @ nrm
        keep = np.abs(dist) < max(1.8, 2.5 * np.median(np.abs(dist)) * 1.48)
        P, wgt = P[keep], wgt[keep]
        if len(P) < 40:
            return None
    rms = float(np.sqrt(np.average(dist[keep] ** 2, weights=wgt)))
    return mu, dirv, rms, len(P)


def segments_on_line(ink_hard, mu, dirv, fr, rmax=246, step=0.5, min_len=6):
    """Walk along the line and report [t0, t1] (px along dirv from mu) where ink is present."""
    ts = np.arange(-rmax * 1.2, rmax * 1.2, step)
    pts = mu[None, :] + ts[:, None] * dirv[None, :]
    inside = np.hypot(pts[:, 0] - fr.cx, pts[:, 1] - fr.cy) < rmax
    vals = np.zeros(len(ts))
    h, w = ink_hard.shape
    xi, yi = np.round(pts[:, 0]).astype(int), np.round(pts[:, 1]).astype(int)
    ok = inside & (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
    # ink within +-1 px across the line
    nrm = np.array([-dirv[1], dirv[0]])
    for off in (-1, 0, 1):
        q = pts[ok] + off * nrm
        v = ink_hard[np.clip(np.round(q[:, 1]).astype(int), 0, h - 1), np.clip(np.round(q[:, 0]).astype(int), 0, w - 1)]
        vals[ok] = np.maximum(vals[ok], v)
    m = vals > 0.5
    segs, i = [], 0
    while i < len(m):
        if m[i]:
            j = i
            while j < len(m) and (m[j] or (j + 1 < len(m) and m[min(j + 14, len(m) - 1)] and not ok[j] is False and False)):
                j += 1
            segs.append((ts[i], ts[min(j, len(ts) - 1)]))
            i = j
        else:
            i += 1
    # merge gaps shorter than 12 px (a ring or a text stroke crossing the line)
    merged = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < 40:
            merged[-1] = (merged[-1][0], s[1])
        else:
            merged.append(s)
    return [s for s in merged if s[1] - s[0] >= min_len]


def dedupe(lines, d_ang=0.8, d_dist=3.0, max_rms=1.2):
    """Hough peaks of one physical line refine to (almost) the same line -> keep one per cluster (best rms)."""
    good = [l for l in lines if l["rms_px"] <= max_rms]
    out = []
    for l in sorted(good, key=lambda l: (l["rms_px"], -l["visible_len_px"])):
        # signed distance depends on the direction convention, so compare the oriented normal (angle, dist) pairs
        dup = False
        for o in out:
            da = abs(((l["angle_deg"] - o["angle_deg"]) + 90) % 180 - 90)
            if da < d_ang and abs(l["dist_from_centre_px"] - o["dist_from_centre_px"]) < d_dist:
                dup = True
                break
        if not dup:
            out.append(l)
    return out


def cross_section(ink, mu, dirv, segs, half=6, step=1.0):
    """Average perpendicular ink profile along the visible parts of a line -> stroke width (FWHM, px) and centre shift."""
    nrm = np.array([-dirv[1], dirv[0]])
    offs = np.arange(-half, half + 1e-6, 0.25)
    acc = np.zeros(len(offs)); n = 0
    h, w = ink.shape
    for a, b in segs:
        for t in np.arange(a + 8, b - 8, step):
            p0 = mu + t * dirv
            q = p0[None, :] + offs[:, None] * nrm[None, :]
            if (q[:, 0] < 1).any() or (q[:, 0] > w - 2).any() or (q[:, 1] < 1).any() or (q[:, 1] > h - 2).any():
                continue
            v = cv2.remap(ink, q[:, 0].astype(np.float32).reshape(1, -1), q[:, 1].astype(np.float32).reshape(1, -1), cv2.INTER_LINEAR).ravel()
            acc += v; n += 1
    if n == 0:
        return None, None
    prof = acc / n
    i = int(np.argmax(prof))
    wd, c = fwhm(prof, i, base=0.0)
    return float(wd * 0.25), float((c - (len(offs) - 1) / 2) * 0.25)


def sequential_lines(ink, mask, fr, thresh=55, min_inliers=90, max_rms=1.0, max_lines=40):
    """Detect-strongest-erase-repeat. Robust where many lines cross (a one-shot Hough peak list blurs there)."""
    work = (mask * 255).astype(np.uint8)
    found = []
    for _ in range(max_lines):
        cands = hough(work, thresh=thresh)
        if not cands:
            break
        accepted = False
        for rho, th in cands[:12]:
            r = refine(ink, work > 0, rho, th, fr)
            if r is None:
                continue
            mu, dirv, rms, n = r
            if rms > max_rms or n < min_inliers:
                continue
            segs = segments_on_line(ink, mu, dirv, fr)
            total = sum(b - a for a, b in segs)
            if total < 70:
                continue
            nrm = np.array([-dirv[1], dirv[0]])
            sw, shift = cross_section(ink, mu, dirv, segs)
            mu = mu + (shift or 0) * nrm                       # re-centre on the stroke
            dist = float((np.array([fr.cx, fr.cy]) - mu) @ nrm)
            ang = float(np.degrees(np.arctan2(dirv[0], -dirv[1])) % 180)
            ends = [mu + segs[0][0] * dirv, mu + segs[-1][1] * dirv]
            ends_r = [float(np.hypot(*(e - [fr.cx, fr.cy]))) for e in ends]
            found.append({"stroke_px": round(sw, 3) if sw else None, "ends_px": [e.tolist() for e in ends], "ends_r_px": [round(r, 2) for r in ends_r],"mu_px": mu.tolist(), "dir": dirv.tolist(), "dist_from_centre_px": round(dist, 3), "angle_deg": round(ang, 3),
                          "rms_px": round(rms, 3), "ink_px": n, "segments_px": [[round(a_, 1), round(b_, 1)] for a_, b_ in segs],
                          "visible_len_px": round(total, 1)})
            # erase the pixels of this line from the working mask
            cv2.line(work, tuple(np.round(mu - 700 * dirv).astype(int)), tuple(np.round(mu + 700 * dirv).astype(int)), 0, 6)
            accepted = True
            break
        if not accepted:
            break
    return found


def circle_hits(mu, d, c, r):
    """Both intersections of the infinite line mu + t*d with the circle (c, r), as t values."""
    f = np.asarray(mu) - np.asarray(c)
    b = f @ d
    disc = b * b - (f @ f - r * r)
    s = np.sqrt(max(disc, 0))
    return -b - s, -b + s


def finalize(lines, fr, prim):
    """Give every line its two end points: the chord ends on the outer ring, except the two lines that meet at the apex (12 o'clock)."""
    c = np.array([fr.cx, fr.cy])
    r_out = max(r["r_px"] for r in prim["rings"])
    for l in lines:
        mu, d = np.array(l["mu_px"]), np.array(l["dir"])
        t0, t1 = circle_hits(mu, d, c, r_out)
        l["end_a_px"] = (mu + t0 * d).tolist()
        l["end_b_px"] = (mu + t1 * d).tolist()
    apex = [l for l in lines if min(l["ends_r_px"]) > 0 and abs(l["dist_from_centre_px"]) < 125 and abs(l["angle_deg"] % 180 - 90) > 40 and abs(abs(l["dist_from_centre_px"]) - 120.5) < 3]
    if len(apex) == 2:
        a, b = apex
        A = np.array([[a["dir"][1], -a["dir"][0]], [b["dir"][1], -b["dir"][0]]])
        rhs = np.array([np.dot([a["dir"][1], -a["dir"][0]], a["mu_px"]), np.dot([b["dir"][1], -b["dir"][0]], b["mu_px"])])
        P = np.linalg.solve(A, rhs)
        for l in apex:
            # replace the end that is nearer to 12 o'clock by the apex point
            ea, eb = np.array(l["end_a_px"]), np.array(l["end_b_px"])
            if ea[1] < eb[1]:
                l["end_a_px"] = P.tolist()
            else:
                l["end_b_px"] = P.tolist()
        print("apex point (px):", P.round(2).tolist(), " r =", round(float(np.hypot(*(P - c))), 2), "from centre")


def run(name="front_a"):
    cal = load_json("calibration.json")["photos"][name]
    fr = Frame(cal["centre_px"][0], cal["centre_px"][1], cal["dial_edge_radius_px"])
    prim = load_json("dial_primitives_px.json")
    im = load_rgba(name)
    ink, hmask = s4.build_ink(name, fr, im)
    mask = candidate_mask(ink, fr, prim)
    save_img(f"lines_{name}_candidate_mask.png", (mask * 255).astype(np.uint8))
    lines = sequential_lines(ink, mask, fr)
    lines.sort(key=lambda l: (l["angle_deg"], l["dist_from_centre_px"]))
    finalize(lines, fr, prim)
    for i, l in enumerate(lines):
        print(i, "ang", l["angle_deg"], "dist", l["dist_from_centre_px"], "stroke", l["stroke_px"], "end r", l["ends_r_px"], "rms", l["rms_px"], "nseg", len(l["segments_px"]))
    save_json("lines_px.json", {"lines": lines})
    return lines


if __name__ == "__main__":
    run("front_a")
