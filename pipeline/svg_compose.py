"""Compose the extracted watch into one static SVG (used for QA, the README image and the verification renders).
The website composes the same data live in JavaScript; this file is the reference implementation of the layer order."""
from __future__ import annotations

import math

import numpy as np

from lib import *


def f(v, nd=2):
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def pol(r, a_deg):
    a = math.radians(a_deg)
    return r * math.sin(a), -r * math.cos(a)


def hex_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def mix_hex(a, b, t):
    A, B = hex_rgb(a), hex_rgb(b)
    return "#%02X%02X%02X" % tuple(int(round(A[i] + (B[i] - A[i]) * t)) for i in range(3))


def wedge(r0, r1, a0, a1):
    x0, y0 = pol(r0, a0); x1, y1 = pol(r1, a0); x2, y2 = pol(r1, a1); x3, y3 = pol(r0, a1)
    big = 1 if (a1 - a0) % 360 > 180 else 0
    if r0 <= 0.01:
        return f"M0 0L{f(x1)} {f(y1)}A{f(r1)} {f(r1)} 0 {big} 1 {f(x2)} {f(y2)}Z"
    return f"M{f(x0)} {f(y0)}L{f(x1)} {f(y1)}A{f(r1)} {f(r1)} 0 {big} 1 {f(x2)} {f(y2)}L{f(x3)} {f(y3)}A{f(r0)} {f(r0)} 0 {big} 0 {f(x0)} {f(y0)}Z"


def fan(profile, step, r0, r1, sub=5, pad=0.15):
    """Smooth angular colour fan: `profile` colours at `step` degrees, interpolated into `sub` wedges per step."""
    n = len(profile)
    out = []
    for i in range(n):
        for j in range(sub):
            t = j / sub
            a0 = i * step + j * step / sub
            c = mix_hex(profile[i], profile[(i + 1) % n], (t + 0.5 / sub))
            out.append(f'<path d="{wedge(r0, r1, a0 - pad, a0 + step / sub + pad)}" fill="{c}"/>')
    return "".join(out)


def hand_svg(h, ang, uid, model, which):
    """Hour/minute hand: two facets (left/right of the axis) with measured lengthwise colour ramps, brightness from the facet model."""
    poly = h["polygon"]                                       # tip-left, tip-right, base-right, base-left (units, y up = negative)
    (xl_t, yt), (xr_t, _), (xr_b, yb), (xl_b, _) = poly
    st = h["stations"]
    y1, y2 = -h["length"], h["tail"]
    def ramp(cols, factor):
        out = []
        for s, c in zip(st, cols):
            off = (-s - y1) / (y2 - y1)
            rgb = [max(0, min(255, int(v * factor))) for v in hex_rgb(c)]
            out.append(f'<stop offset="{f(off, 4)}" stop-color="#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"/>')
        return "".join(out)
    t = math.radians(ang)
    F = lambda a: model["m"] + model["a"] * math.cos(math.radians(a - model["theta0"]))
    meas = h["angle_photo"]
    fl = F(ang) / F(meas)
    fr = F(-ang) / F(-meas)
    fl, fr = max(.55, min(1.4, fl)), max(.55, min(1.4, fr))
    defs = (f'<linearGradient id="hl{uid}{which}" gradientUnits="userSpaceOnUse" x1="0" y1="{f(y1)}" x2="0" y2="{f(y2)}">{ramp(h["left"], fl)}</linearGradient>'
            f'<linearGradient id="hr{uid}{which}" gradientUnits="userSpaceOnUse" x1="0" y1="{f(y1)}" x2="0" y2="{f(y2)}">{ramp(h["right"], fr)}</linearGradient>')
    left = f'M{f(xl_t)} {f(yt)}L0 {f(yt)}L0 {f(yb)}L{f(xl_b)} {f(yb)}Z'
    right = f'M0 {f(yt)}L{f(xr_t)} {f(yt)}L{f(xr_b)} {f(yb)}L0 {f(yb)}Z'
    body = f'<path d="{left}" fill="url(#hl{uid}{which})"/><path d="{right}" fill="url(#hr{uid}{which})"/>'
    return defs, f'<g transform="rotate({f(ang, 2)})">{body}</g>'


def compose(core, body, pose=None, size=1200, bg=None, parts=("body", "bezel", "dial", "hands"), date_day=28, uid="p", frame_px=None):
    pose = pose or {"hour": 303.45, "minute": 60.18, "second": 0.23}
    D = core["dial"]
    k = core["unit"]["px_per_unit"]
    ub = body["unit_bbox"]
    pad = 6
    vb = (ub[0] - pad, ub[1] - pad, ub[2] - ub[0] + 2 * pad, ub[3] - ub[1] + 2 * pad)
    if frame_px:                       # render exactly onto the photo's pixel grid: (width_px, height_px)
        cxp, cyp = core["unit"]["centre_px"]
        kk = 1.0 / core["unit"]["px_per_unit"]
        vb = (-cxp * kk, -cyp * kk, frame_px[0] * kk, frame_px[1] * kk)
    defs, g = [], []
    # ---- body
    if "body" in parts:
        s = (1.0 / k) / body["grid_per_px"]
        paths = "".join(f'<path d="{L["d"]}" fill="{L["fill"]}"/>' for L in body["levels"])
        g.append(f'<g id="body" transform="scale({f(s, 6)})" fill-rule="evenodd">{paths}</g>')
        ir = body["inner_radius_units"]
        g.append(f'<circle r="{f(ir + 0.5)}" fill="#1E1E1F"/>')
    # ---- bezel
    B = core["bezel"]
    if "bezel" in parts:
        n_in = len(B["inner_ring_colours"])
        r_a, r_b = B["inner_ring"]
        g.append(fan(B["inner_ring_colours"], 360 / n_in, r_a, r_b, sub=3))
        r_gap_out = B["r_out"] + 2.4
        g.append(f'<circle r="{f(B["r_out"] + 1.0)}" fill="{B["groove_colour"]}"/>')
        cnt = B["count"]; pitch = 360 / cnt
        half_groove = math.degrees((B["groove_w"] / 2) / ((B["r_in"] + B["r_out"]) / 2))
        c = B["corner"]
        for i in range(cnt):
            a0 = B["first_groove_deg"] + pitch * i + half_groove + math.degrees(c / B["r_out"])
            a1 = B["first_groove_deg"] + pitch * (i + 1) - half_groove - math.degrees(c / B["r_out"])
            d = wedge(B["r_in"] + c, B["r_out"] - c, a0, a1)
            col = B["tooth_colours"][(i) % cnt]
            g.append(f'<path d="{d}" fill="{col}" stroke="{col}" stroke-width="{f(2 * c)}" stroke-linejoin="round"/>')
    # ---- dial
    if "dial" in parts:
        S = core["shading"]
        g.append(f'<circle r="{f(B["inner_ring"][0] + 0.2)}" fill="{S["median"]}"/>')
        g.append(fan(S["main"], S["step_deg"], 0, 200, sub=5))
        band_in = D["chapter_band_inner"]
        g.append(fan(S["outer"], S["step_deg"], band_in, 200, sub=3).replace('fill="', 'fill-opacity="0.9" fill="'))
        g.append(f'<circle r="{f((band_in + 200) / 2)}" fill="none" stroke="#02103D" stroke-opacity=".0" stroke-width="{f(200 - band_in)}"/>')
        ink = D["ink"]
        # rings
        for r in D["rings"]:
            g.append(f'<circle r="{r["r"]}" fill="none" stroke="{ink}" stroke-width="{r["w"]}"/>')
        # ticks
        for name, row in D["tick_rows"].items():
            for kk in range(60):
                cls = row["five"] if kk % 5 == 0 else row["one"]
                col = row["colour"] if kk % 5 == 0 else row["colour_one"]
                a = 6 * kk + row["offset_deg"]
                x0, y0 = pol(cls["r0"], a); x1, y1 = pol(cls["r1"], a)
                g.append(f'<path d="M{f(x0)} {f(y0)}L{f(x1)} {f(y1)}" stroke="{col}" stroke-width="{cls["w"]}"/>')
        # rays
        R_ = D["rays"]
        for a in R_["angles"]:
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            def Q(r, w, side):
                x, y = pol(r, a); return x + side * w / 2 * ca, y + side * w / 2 * sa
            pts = [Q(R_["r0"], R_["w0"], -1), Q(R_["r1"], R_["w1"], -1), Q(R_["r1"], R_["w1"], 1), Q(R_["r0"], R_["w0"], 1)]
            g.append(f'<path d="M{" L".join(f(x) + " " + f(y) for x, y in pts)}Z" fill="{ink}"/>')
        # chords + apex
        for c_ in D["chords"]:
            g.append(f'<path d="M{f(c_["a"][0])} {f(c_["a"][1])}L{f(c_["b"][0])} {f(c_["b"][1])}" stroke="{ink}" stroke-width="{c_["w"]}"/>')
        if D["apex"]:
            pts = D["apex"]["points"]
            g.append(f'<path d="M{" L".join(f(x) + " " + f(y) for x, y in pts)}Z" fill="{ink}"/>')
        # text
        for t in D["text"]:
            g.append(f'<path d="{t["d"]}" fill="{t["fill"]}" fill-rule="evenodd" transform="translate({f(t["x"])} {f(t["y"])}) rotate({t["rot"]})"/>')
        # date window
        W = D["date"]
        x, y, w, h = W["x"], W["y"], W["w"], W["h"]
        rim = W["rim"]
        defs.append(f'<radialGradient id="dp{uid}" cx=".5" cy=".5" r=".75"><stop offset="0" stop-color="{W["plate_centre"]}"/><stop offset="1" stop-color="{W["plate_edge"]}"/></radialGradient>')
        g.append(f'<rect x="{f(x + rim / 2)}" y="{f(y + rim / 2)}" width="{f(w - rim)}" height="{f(h - rim)}" rx="{W["radius"]}" fill="url(#dp{uid})" stroke="{W["rim_colour"]}" stroke-width="{rim}"/>')
        g.append(f'<rect x="{f(x + rim)}" y="{f(y + rim)}" width="{f(w - 2 * rim)}" height="{f(h - 2 * rim)}" rx="{f(W["radius"] * .55)}" fill="none" stroke="{W["edge_colour"]}" stroke-width=".7" stroke-opacity=".8"/>')
        txt = str(date_day)
        tl = len(txt) * W["digit_w"] + (len(txt) - 1) * W["digit_gap"]
        g.append(f'<text x="{f(W["digit_cx"] - tl / 2)}" y="{f(W["digit_cy"] + W["digit_h"] / 2)}" textLength="{f(tl)}" lengthAdjust="spacingAndGlyphs" '
                 f'font-family="Poppins,Arial,sans-serif" font-weight="600" font-size="{f(W["digit_h"] / .71)}" fill="{W["digit_colour"]}" stroke="none">{txt}</text>')
    # ---- hands
    if "hands" in parts:
        Hn = core["hands"]
        for which in ("hour", "minute"):
            d_, g_ = hand_svg(Hn[which], pose[which], uid, Hn["facet_model"], which)
            defs.append(d_); g.append(g_)
        sec = Hn["second"]; hub = Hn["hub"]
        g.append(f'<circle r="{hub["pad_r"]}" fill="{hub["pad_colour"]}" fill-opacity=".9"/>')
        pad = sec["pad"]
        g.append(f'<g transform="rotate({f(pose["second"], 2)})"><path d="M0 {f(pad["y"] - pad["r"])}A{pad["r"]} {pad["r"]} 0 0 0 0 {f(pad["y"] + pad["r"])}Z" fill="{pad["left"]}"/><path d="M0 {f(pad["y"] - pad["r"])}A{pad["r"]} {pad["r"]} 0 0 1 0 {f(pad["y"] + pad["r"])}Z" fill="{pad["right"]}"/><path d="M{f(-sec["w"] / 2)} {f(-sec["tip"])}H{f(sec["w"] / 2)}V{f(sec["tail"])}H{f(-sec["w"] / 2)}Z" fill="{sec["colour"]}"/></g>')
        g.append(f'<circle r="{f((hub["ring_r"][0] + hub["ring_r"][1]) / 2)}" fill="none" stroke="{hub["ring_colour"]}" stroke-width="{f(hub["ring_r"][1] - hub["ring_r"][0])}"/>')
        g.append(f'<circle r="{hub["screw_r"]}" fill="{hub["screw_colour"]}"/><circle r="1.1" fill="#3a2a2c"/>')
    bgrect = f'<rect x="{f(vb[0])}" y="{f(vb[1])}" width="{f(vb[2])}" height="{f(vb[3])}" fill="{bg}"/>' if bg else ""
    h_px = int(size * vb[3] / vb[2])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(vb[0])} {f(vb[1])} {f(vb[2])} {f(vb[3])}" width="{size}" height="{h_px}">'
            f'<defs>{"".join(defs)}</defs>{bgrect}{"".join(g)}</svg>')
