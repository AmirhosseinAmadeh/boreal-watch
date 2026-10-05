# Edge-detection pipeline — from the official photo to the vector watch

This document explains how `assets/boreal-data.js`, `assets/boreal-body.js` and `assets/boreal-preview.svg` are produced.
Everything runs from `pipeline/` and every number the site draws comes out of these stages. The same walk-through is on the site
(section **08 — Edge lab**), where each stage is drawn from its own output.

> **Legal / scope.** The official product photos are *not* in this repository (`source/` is git-ignored) and are never served.
> What is stored is code plus numeric / vector output. The wordmark and the dial artwork are Swatch's; this is an unofficial fan study.

## Run it

```bash
pip install -r pipeline/requirements.txt
# stage 0: put the photos in source/ (see below), then
python pipeline/run_all.py
```

Stage 0 — photos. From the official page `https://www.swatch.com/en-en/sistem-boreal-yis401gc/YIS401GC.html` the product images are
`static.swatch.com/images/product/YIS401GC/sa200/YIS401GC_sa200_er003.png` (1920², front, used as **front_a.png**) and `..._er004.png`
(1600², front, used only for cross-checks, **front_b.png**). They are transparent PNGs, so the **alpha channel is a perfect case/bracelet mask**.
A third image (`sa300/..._er003.png`, caseback) exists but is not used yet.

## Why it works: three ideas

1. **Polar unwrapping.** The dial is a stack of concentric circles. Resampling the photo around the dial centre turns rings into horizontal
   lines, ticks and rays into vertical bars, chords into arches — and makes the numerals' rotation rule visible. Most measurements are
   then one-dimensional statistics (median, centroid, FWHM).
2. **The red channel is a drawing.** The print is white (R≈235) on a blue dial (R≈5–30), so `R` is an almost binary ink map. Hands are separated by *size*
   (print strokes are 2–8 px thick, hands ≥ 25 px) rather than by colour.
3. **Explain, subtract, repeat.** Measure what is regular (rings, ticks, rays, chords) as parametric primitives, render them back onto the photo's grid,
   and subtract. The residual is exactly what is left to trace (numerals, logo, date window). The same renderer later scores the whole model.

## Stages

| # | script | what it does | key result |
|---|---|---|---|
| 1 | `s01_calibrate.py` | Centre found by maximising the sharpness of the angle-median radial profile (Nelder–Mead). Dial edge fitted per-angle (robust circle). | centre (931.40, 962.84) px, dial R = 342.87 px (rms 0.54 px) |
| 2 | `s02_edges.py` | Edge atlas: Canny on luminance (2 scales, consensus), Canny on the red channel, Scharr gradient. | the edge maps the later stages read |
| 3 | `s03_hands.py` | Morphological opening isolates hands; PCA angle; photo straightened at 4×; row-by-row sub-pixel edges; straight-edge fits; facet colours. | edges are straight to ≈0.05 px; light model `F(t)=193.5+53.4·cos(t−120°)` fitted from the two poses |
| 4 | `s04_dial_primitives.py` | Rings, two tick rows, sun rays in polar space. | rings at 0.219R / 0.518R / 0.716R; **12 rays every 30°** (the old notes said 8); ticks 2.3 px / 7.5 px wide |
| 5 | `s05_lines.py` | Hough + sequential detect-erase + total least squares; chord ends on the outer ring. | **6 chords**: 4 at 26.6° and 2 diagonals at 45°; two meet in a solid apex triangle at 12 |
| 6 | `s06_residual.py` | Render the model, subtract from the ink. | model precision 0.907 (it is not inventing ink); 70 residual pieces |
| 7 | `s07_text.py` | Rotation rule measured (labels 20–40 and numerals 4–8 flipped), items straightened at 6×, chords removed by a “ink on both sides” test, traced with potrace; hidden glyphs reconstructed and flagged. | 25 items; typeface is custom (best system font IoU 0.76) |
| 8 | `s08_measure.py` | Core-ink colours per feature; the dial's two-lobe shading in 5° wedges. | print `#ECEBEB`, outer ticks `#D9E8F4`, lobes at ≈105° and ≈257° |
| 9 | `s09_body.py` | Case, lugs, crown, bracelet as stacked tonal regions (k-means thresholds on luminance, alpha silhouette). | 8 levels, ~170 KB of path data |
| 10 | `s10_bezel.py` | Teeth via angular FFT + median of 120 aligned patches. | **120 teeth**, pitch 3.000°, r 353–378 px |
| 11 | `s11_build.py` | Convert to dial units (200 = R), write the site data and a static SVG. | `assets/boreal-*.js`, `assets/boreal-preview.svg` |
| 12 | `s12_verify.py` | Render the vector model on the photo's grid and compare. | see below |

### Verification (front_a, 1920 px)

| metric | value |
|---|---|
| silhouette IoU (body) | 0.9988 |
| metal luminance error | 6.8 / 255 |
| dial print ink IoU / precision / recall | 0.754 / 0.851 / 0.868 (strokes are 2–4 px wide, so IoU is harsh) |
| dial print edge chamfer | 1.02 px (photo→model), 0.45 px (model→photo) |
| hands IoU | 0.53 (see limitations: parallax) |

The second photo gives an independent check: its ring radii divided by its dial radius agree with the first photo within 0.003.

## Things I tried that did not work (and why)

* **Hough circles** for the rings: fine for radii, but ±1 px centre error smears every ring; the sharpness optimisation is far better.
* **Subtracting the chord model from numerals**: cut strokes where chords cross glyphs (4, 5, 7, 8 were ragged). The “ink on both sides of the chord” test removes only the chord pixels that are *outside* a glyph.
* **Identifying the numeral font** against Bahnschrift, Arial Narrow, Impact, Segoe, Tahoma, Barlow Condensed…: best mean IoU 0.76, so the face is custom and the glyphs are traced instead of typeset.
* **A single Telea inpaint across the seconds hand**: it glued 6 and 0 of “60” together. Each side of the strip is now completed separately.
* **Fitting hands by their width profile**: the minute-label “10” sits under the minute hand's tip and contaminates the last rows, so each edge is fitted as a straight line on the clean middle section instead.

## Limitations (honest list)

* **Reconstructed, not measured**: the hour hand hides part of the “10” (the zero is drawn as a stadium ring from median metrics), the minute hand hides the label “10” and the “2” at 2 o'clock (copied from the “12”/“05”/“15” glyphs), and the seconds hand hides the right of the logo's “a” and all of SWISS's “I” (drawn from stroke widths). They are marked `reconstructed` in the data and orange in the lab.
* **Hands have photo parallax**: in the photo the hands' axes are 3–4 px off the dial centre (the camera is not exactly overhead). The model removes that so the hands rotate about the pivot, which is why hands IoU is only 0.53.
* **Metal is a static posterisation** of one lighting. The light slider adds a soft-light gloss and rotates the bezel's tooth colours; it cannot re-light the case.
* **Date digits** are typeset (Poppins, forced to the measured box with `textLength`); the photo only contains “2” and “8”.
* **Numerals 4 and 5** keep a slightly ragged edge where chords touch them.
* **Caseback** is still the earlier hand-drawn illustration; the back photo has not been extracted yet.
* Colours are from one photo; JPEG-like noise in the brush texture is modelled statistically (seeded noise with the measured amplitude), not copied.
