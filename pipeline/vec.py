"""Bitmap -> vector helpers (potrace via `potracer`).

All shapes are traced from an upsampled, thresholded bitmap, so a 20 px tall glyph in the photo is traced on a
120 px tall grid: smooth Bezier outlines instead of staircase polygons.
"""
from __future__ import annotations

import numpy as np
import potrace


def trace_bitmap(mask: np.ndarray, scale: float, origin=(0.0, 0.0), turd=6, alphamax=1.1, opttol=0.25):
    """Trace a boolean mask (True = ink). Returns a list of closed paths in *source units*:
    each path = {"start": (x, y), "segs": [("L", (x, y)) | ("C", (x1, y1), (x2, y2), (x, y)) ...]}.
    `scale` = pixels of the mask per source unit; `origin` = source coordinate of the mask's top-left corner."""
    bm = potrace.Bitmap(~np.asarray(mask, bool))   # potracer traces the False pixels
    plist = bm.trace(turdsize=turd, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY, alphamax=alphamax,
                     opticurve=True, opttolerance=opttol)
    ox, oy = origin

    def P(pt):
        return (ox + pt.x / scale, oy + pt.y / scale)

    paths = []
    for curve in plist:
        segs = []
        for s in curve.segments:
            if s.is_corner:
                segs.append(("L", P(s.c)))
                segs.append(("L", P(s.end_point)))
            else:
                segs.append(("C", P(s.c1), P(s.c2), P(s.end_point)))
        paths.append({"start": P(curve.start_point), "segs": segs})
    return paths


def path_d(paths, nd=2, tx=lambda p: p):
    """SVG path data (closed subpaths; use fill-rule=evenodd for glyphs with counters)."""
    f = lambda v: f"{v:.{nd}f}".rstrip("0").rstrip(".") if nd else str(int(round(v)))
    out = []
    for p in paths:
        x, y = tx(p["start"])
        out.append(f"M{f(x)} {f(y)}")
        for s in p["segs"]:
            if s[0] == "L":
                x, y = tx(s[1])
                out.append(f"L{f(x)} {f(y)}")
            else:
                (a, b), (c, d), (e, g) = tx(s[1]), tx(s[2]), tx(s[3])
                out.append(f"C{f(a)} {f(b)} {f(c)} {f(d)} {f(e)} {f(g)}")
        out.append("Z")
    return "".join(out)


def bbox(paths):
    xs, ys = [], []
    for p in paths:
        xs.append(p["start"][0]); ys.append(p["start"][1])
        for s in p["segs"]:
            for q in s[1:]:
                xs.append(q[0]); ys.append(q[1])
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0)


def path_d_rel(paths, tx=lambda p: p):
    """Compact SVG path: integer coordinates (the caller picks the grid through `tx`), relative commands, subpath-closed.
    Absolute coordinates are rounded FIRST and differenced afterwards, so rounding errors never accumulate."""
    out = []
    for p in paths:
        pts = [tx(p["start"])]
        cmds = []
        for sgm in p["segs"]:
            if sgm[0] == "L":
                pts.append(tx(sgm[1])); cmds.append("l")
            else:
                pts.extend([tx(sgm[1]), tx(sgm[2]), tx(sgm[3])]); cmds.append("c")
        q = [(int(round(x)), int(round(y))) for x, y in pts]
        out.append(f"M{q[0][0]} {q[0][1]}")
        i = 1
        last = q[0]
        prev_cmd = None
        for c in cmds:
            n = 1 if c == "l" else 3
            vals = []
            base = last
            for j in range(n):
                vals.extend([q[i + j][0] - base[0], q[i + j][1] - base[1]])
            last = q[i + n - 1]
            i += n
            body = " ".join(map(str, vals))
            out.append((c if c != prev_cmd else " ") + body if c != prev_cmd else " " + body)
            prev_cmd = c
        out.append("z")
    return "".join(out).replace(" -", "-")
