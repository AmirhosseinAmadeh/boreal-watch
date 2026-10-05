"""Stage 11 — build: turn every measured number into the site's data file and a standalone preview SVG.

Inputs  : pipeline/out/*.json from stages 1-10
Outputs : assets/boreal-data.js   (window.BOREAL = {...}, everything except the heavy body paths)
          assets/boreal-body.js   (window.BOREAL.body = {...}, ~the traced case / lugs / crown / bracelet tonal layers)
          assets/boreal-preview.svg (the whole watch as one static SVG - used for QA and the README)
Units   : the site's dial space - origin = dial centre, 200 = dial radius, y down, clock angle 0 = 12 o'clock, clockwise.
"""
from __future__ import annotations

import json
import re

import numpy as np

from lib import *
import vec

ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def r1(v, nd=2):
    return round(float(v), nd)


def scale_path(d: str, k: float, nd=2) -> str:
    """Scale every number of an absolute M/L/C/Z path by k (px -> dial units)."""
    def rep(m):
        v = float(m.group(0)) * k
        s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
        return "0" if s in ("", "-0") else s
    return re.sub(r"-?\d+(?:\.\d+)?", rep, d)


def rdp(points, eps):
    pts = np.asarray(points, float)
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a
    n = np.hypot(*ab)
    q = pts - a
    d = np.abs(ab[0] * q[:, 1] - ab[1] * q[:, 0]) / (n if n else 1)
    i = int(np.argmax(d))
    if d[i] > eps:
        return np.vstack([rdp(pts[:i + 1], eps)[:-1], rdp(pts[i:], eps)])
    return np.vstack([a, b])


def hex_(rgb):
    return "#%02X%02X%02X" % tuple(int(v) for v in rgb)


def build():
    cal = load_json("calibration.json")["photos"]["front_a"]
    cal_b = load_json("calibration.json")["photos"]["front_b"]
    cx, cy, R = cal["centre_px"][0], cal["centre_px"][1], cal["dial_edge_radius_px"]
    k = 200.0 / R
    prim = load_json("dial_primitives_px.json")
    lines = load_json("lines_px.json")["lines"]
    text = load_json("text_items.json")["items"]
    hands = load_json("hands_raw.json")["hands"]
    bez = load_json("bezel_px.json")
    shade = load_json("dial_shading.json")
    colours = load_json("colours.json")

    U = lambda px: r1(px * k)                         # length px -> units
    P = lambda x, y: [r1((x - cx) * k), r1((y - cy) * k)]  # point px -> units
    inkc = hex_(colours["ring2"])

    out = {"unit": {"dial_radius": 200, "px_per_unit": r1(1 / k, 4), "source_px": 1920, "centre_px": [r1(cx, 3), r1(cy, 3)]}}

    # --- rings, ticks, rays, chords
    rings = [{"r": U(r["r_px"]), "w": U(r["stroke_px"]), "coverage": r["coverage"]} for r in prim["rings"]]
    tick_rows = {}
    for name, row in prim["tick_rows"].items():
        one, five = row["one_min"], row["five_min"]
        tick_rows[name] = {
            "offset_deg": row["offset_deg"],
            "one": {"r0": U(one["r0_px"]), "r1": U(one["r1_px"]), "w": U(one["width_px"])},
            "five": {"r0": U(five["r0_px"]), "r1": U(five["r1_px"]), "w": U(five["width_px"])},
        }
    tick_rows["inner"]["colour"] = hex_(colours["tick_inner_5min"]); tick_rows["inner"]["colour_one"] = hex_(colours["tick_inner_1min"])
    tick_rows["outer"]["colour"] = hex_(colours["tick_outer_5min"]); tick_rows["outer"]["colour_one"] = hex_(colours["tick_outer_1min"])
    ry = prim["rays"]
    pw = np.array(ry["width_vs_r_px"], float)
    slope, icpt = np.polyfit(pw[:, 0], pw[:, 1], 1)
    rays = {"angles": ry["angles_deg"], "r0": U(ry["radial_run_px"][0]), "r1": U(ry["radial_run_px"][1]),
            "w0": U(slope * ry["radial_run_px"][0] + icpt), "w1": U(slope * ry["radial_run_px"][1] + icpt)}
    chords = [{"a": P(*l["end_a_px"]), "b": P(*l["end_b_px"]), "w": U(l["stroke_px"]), "angle_deg": l["angle_deg"], "dist": U(abs(l["dist_from_centre_px"]))} for l in lines]
    # apex triangle: filled between the two apex chords from the apex down to the outer edge of the outer ring
    apex_chords = [c for c in chords if abs(c["dist"] - U(120.55)) < 1.5]
    apex_pt = None
    if len(apex_chords) == 2:
        top = [min((c["a"], c["b"]), key=lambda p: p[1]) for c in apex_chords]
        apex_pt = [r1((top[0][0] + top[1][0]) / 2), r1(min(top[0][1], top[1][1]))]
        r_ring_out = rings[2]["r"] + rings[2]["w"] / 2
        base = []
        for c in apex_chords:
            a, b = np.array(c["a"]), np.array(c["b"])
            d = (b - a) / np.hypot(*(b - a))
            f = a
            # intersect with circle of radius r_ring_out
            bb = f @ d
            disc = bb * bb - (f @ f - r_ring_out ** 2)
            t = [-bb - np.sqrt(disc), -bb + np.sqrt(disc)]
            pts = [a + tt * d for tt in t]
            base.append(min(pts, key=lambda p: p[1]).tolist())
        apex = {"points": [apex_pt, [r1(base[0][0]), r1(base[0][1])], [r1(base[1][0]), r1(base[1][1])]]}
    else:
        apex = None

    out["dial"] = {"rings": rings, "tick_rows": tick_rows, "rays": rays, "chords": chords, "apex": apex,
                   "ink": inkc, "radius": 200, "chapter_band_inner": U(318.5)}

    # --- text items
    items = []
    for t in text:
        cxu, cyu = P(*t["centre_px"])
        items.append({"kind": t["kind"], "label": t["label"], "x": cxu, "y": cyu, "rot": round(t["rot"], 2),
                      "d": scale_path(t["d"], k, 2), "reconstructed": t.get("reconstructed"), "occluded": t["occluded"],
                      "fill": hex_(colours["minute_labels"]) if t["kind"] != "logo" else hex_(colours["logo"])})
    out["dial"]["text"] = items

    # --- date window (measured by hand from the edge profiles, see PIPELINE.md stage 8)
    wx0, wx1, wy0, wy1 = 1127.4, 1199.3, 936.5, 991.2
    out["dial"]["date"] = {"x": r1((wx0 - cx) * k), "y": r1((wy0 - cy) * k), "w": U(wx1 - wx0), "h": U(wy1 - wy0), "rim": U(3.6), "radius": U(5.2),
                           "rim_colour": "#D9E8F4", "edge_colour": "#59595B", "plate_centre": "#CDCFD9", "plate_edge": "#AAB3C7", "digit_colour": "#232235",
                           "digit_h": U(35), "digit_w": U(22), "digit_gap": U(4), "digit_cx": r1((1161.0 - cx) * k), "digit_cy": r1((964.5 - cy) * k),
                           "sample_day": 28}

    # --- dial shading (two lobes): 72 samples at 5 deg, plus the chapter band
    out["shading"] = {"step_deg": shade["step_deg"], "main": [hex_(c) for c in shade["main_rgb"]], "outer": [hex_(c) for c in shade["outer_rgb"]],
                      "median": "#032253", "brush": {"amplitude": 4.2, "corr_deg": 0.55}}

    # --- bezel
    out["bezel"] = {"count": bez["count"], "first_groove_deg": bez["first_groove_deg"], "r_in": U(bez["tooth_r_in_px"]), "r_out": U(bez["tooth_r_out_px"]),
                    "groove_deg": bez["groove_deg"], "groove_w": U(3.2), "groove_colour": hex_(bez["groove_colour"]),
                    "tooth_colours": [hex_(c) for c in bez["tooth_colours"]], "inner_ring_colours": [hex_(c) for c in bez["inner_ring_colours_5deg"]],
                    "inner_ring": [U(343.0), U(352.5)], "corner": U(3.0)}

    # --- hands (canonical pose pointing up; x = lateral, y = -length)
    hs = {}
    for h in hands:
        L = np.array(h["left_edge_px"]); Rr = np.array(h["right_edge_px"]); Ls = h["length_px"]
        fits = []
        for E in (L, Rr):
            sel = (E[:, 1] > 45) & (E[:, 1] < Ls - 35)
            x, s_ = E[sel, 0], E[sel, 1]
            keep = np.ones(len(x), bool)
            for _ in range(6):
                b_, a_ = np.polyfit(s_[keep], x[keep], 1)
                res = x - (a_ + b_ * s_)
                keep = np.abs(res) < max(0.35, 2.5 * np.median(np.abs(res[keep])) * 1.48)
            fits.append((a_, b_, float(np.sqrt((res[keep] ** 2).mean()))))
        (aL, bL, eL), (aR, bR, eR) = fits
        delta = np.arctan((bL + bR) / 2)                     # the symmetry axis is tilted by delta from the straightened frame
        cd, sd = np.cos(delta), np.sin(delta)
        def rot(x, s_):                                      # rotate the hand's own frame so that its symmetry axis is vertical
            return x * cd - s_ * sd, x * sd + s_ * cd
        s_tail, s_tip = -22.0, Ls
        corners = [(aL + bL * s_tip, s_tip), (aR + bR * s_tip, s_tip), (aR + bR * s_tail, s_tail), (aL + bL * s_tail, s_tail)]
        rc = [rot(x, s_) for x, s_ in corners]
        ax0 = (rc[0][0] + rc[1][0]) / 2 - (rc[0][1] - 0) * 0  # lateral centre at the tip (before pivot alignment)
        # axis x at s'=0 (pivot) from the two edge lines
        xl0, xr0 = rot(aL, 0)[0], rot(aR, 0)[0]
        shift = (xl0 + xr0) / 2
        poly = [[r1((x - shift) * k), r1(-s_ * k)] for x, s_ in rc]
        st = np.array(h["stations_px"])
        hs[h["label"]] = {"angle_photo": r1(h["angle_deg"] + np.degrees(delta), 2), "length": U(Ls), "tail": U(-s_tail),
                          "axis_offset": r1(shift * k), "polygon": poly, "fit_rms_px": [r1(eL, 3), r1(eR, 3)],
                          "stations": [r1(s_ * k) for s_ in st], "left": [hex_(c) for c in h["left_rgb"]], "right": [hex_(c) for c in h["right_rgb"]]}
    out["hands"] = {"hour": hs.get("hour"), "minute": hs.get("minute"),
                    "second": {"colour": "#D5051F", "w": U(6.2), "tip": U(281.5), "tail": U(97.0),
                               "pad": {"y": 44.5, "r": 5.5, "left": "#E5E4E5", "right": "#BDBCBD", "note": "steel disc under the red stripe, measured on both photos (stage 5 residual)"}},
                    "hub": {"pad_r": U(24), "ring_r": [U(4.6), U(13)], "screw_r": U(4.2), "pad_colour": "#6E6A6D", "ring_colour": "#D5051F", "screw_colour": "#CE8787"},
                    "facet_model": {"m": 193.5, "a": 53.4, "theta0": 120.0, "note": "left facet brightness F(t)=m+a*cos(t-theta0); right facet F(-t); fitted from the two measured poses"}}

    save_json("build_core.json", out)
    return out, k


def write_assets():
    out, k = build()
    js = "/* generated by pipeline/s11_build.py - do not edit by hand */\nwindow.BOREAL = " + json.dumps(out, separators=(",", ":")) + ";\n"
    (ASSETS / "boreal-data.js").write_text(js, encoding="utf-8")
    print("assets/boreal-data.js", len(js) // 1024, "KB")
    body = load_json("body.json")
    bjs = "/* generated by pipeline/s09_body.py + s11_build.py */\nwindow.BOREAL.body = " + json.dumps(body, separators=(",", ":")) + ";\n"
    (ASSETS / "boreal-body.js").write_text(bjs, encoding="utf-8")
    print("assets/boreal-body.js", len(bjs) // 1024, "KB")
    if (OUT / "caseback.json").exists():
        back = load_json("caseback.json")
        kjs = "/* generated by pipeline/s13_caseback.py + s11_build.py (lazy-loaded by main.js) */" + chr(10) + "window.BOREAL.back = " + json.dumps(back, separators=(",", ":")) + ";" + chr(10)
        (ASSETS / "boreal-back.js").write_text(kjs, encoding="utf-8")
        print("assets/boreal-back.js", len(kjs) // 1024, "KB")
    import stages
    pjs = "/* generated by pipeline/s11_build.py from the stage outputs */\nwindow.BOREAL.pipeline = " + json.dumps({"stages": stages.stages()}, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (ASSETS / "boreal-pipeline.js").write_text(pjs, encoding="utf-8")
    print("assets/boreal-pipeline.js", len(pjs) // 1024, "KB")
    import svg_compose
    svg = svg_compose.compose(out, body, size=1100)
    (ASSETS / "boreal-preview.svg").write_text(svg, encoding="utf-8")
    print("assets/boreal-preview.svg", len(svg) // 1024, "KB")
    try:
        import resvg_py
        png = resvg_py.svg_to_bytes(svg_string=svg, background="#ffffff")
        (OUT / "preview.png").write_bytes(bytes(png))
    except Exception as e:  # rasteriser is optional
        print("resvg render skipped:", e)
    return out, body


if __name__ == "__main__":
    write_assets()
