# Design notes — what was measured, and from where

Source of truth: the official Swatch product page
https://www.swatch.com/en-en/sistem-boreal-yis401gc/YIS401GC.html and its product photos (front 1920² and 1600², transparent PNG).
The watch in this site is rebuilt by the edge-detection pipeline (see `PIPELINE.md`); no Swatch image file is stored or served.

R = dial radius = 342.87 px = 200 site units. Photo centre (931.40, 962.84) px.

## Corrections to the first version of these notes
| first version said | measured |
|---|---|
| 8 rays at 45° | **12 rays every 30°** (r 0.213–0.333 R, tapering 6.0 → 2.3 px) |
| six-point star, vertices at 0.77 R | **6 chords** of the outer ring: four at ±26.6° (120.6 and 185.6 px from the centre) and two at ±45° (51.4 px); the two apex chords end in a solid triangle at r = 269 px |
| rings 0.22 / 0.53 / 0.73 R | **0.2194 / 0.5178 / 0.7156 R** (stroke 3.7 px) |
| minute ticks 0.94–0.98 R | two rows: inner 243.5–268 px (0.71–0.78 R), outer chapter band 322–338 px (0.94–0.99 R); 1-min 2.3 px, 5-min 7.5 px wide |
| printed lines `#D3D9E4` | core ink **`#ECEBEB`** (the old value was diluted by anti-aliased edge pixels); outer ticks `#D9E8F4` / `#C9D9EB` |
| seconds hand `#C81A35` | **`#D5051F`**, 6.2 px wide, tip 281 px, tail 97 px |
| fluted bezel “≈1.0–1.15 R” | **120 teeth**, pitch 3.000°, r 353–378 px (1.03–1.10 R), groove ≈ 2.4–3.8 px |

## Dial print (units: px of the 1920 photo)
* rings r = 75.2 / 177.5 / 245.4
* chords: angles 26.61°, 26.63°, 45.06°, 134.98°, 153.44°, 153.45°; distance from centre 51.4 (diagonals), 120.6 and 185.6 px; stroke 2.1 px; ends on the outer ring except the apex pair
* apex triangle: apex (931.5, 693.4), base on the outer ring's top edge
* minute labels at r = 284.5 px, hour numerals at r ≈ 212 px, “swatch / SWISS” and “AUTOMATIC” on the vertical axis
* label / numeral rotation rule: clock angle A for upper and side items; A−180 (flipped to stay readable) for labels 20–40 and numerals 4–8 (3 is the date)
* date window: x 1127.4–1199.3, y 936.5–991.2 px (72 × 55 px), rim 3.6 px pale blue `#D9E8F4`, plate `#CDCFD9`→`#AAB3C7`, digits `#232235`, digit block 22 × 35 px each, gap 4 px
* hub: red ring r 4.6–13 px, steel pad r 24 px

## Colours (median pixel of each region)
| Role | HEX | Note |
|---|---|---|
| Dial, darkest | `#011542` | at ≈0° (12 o'clock side) |
| Dial, median | `#032253` | |
| Dial, lit lobes | `#0A4B8A` / `#074583` | peaks at ≈105° and ≈257° |
| Chapter band | `#04376C` | band from r = 318.5 px outwards, about 1.4× brighter than the dial, darkening towards the bezel |
| Printed lines | `#ECEBEB` | core of the strokes |
| Hands | two facets sampled at 16 stations along the length (stored in the data file); typical light facet ≈ `#DCDBDB`, shaded facet ≈ `#7A797D` | brightness follows `F(t)=193.5+53.4·cos(t−120°)` |
| Fluted bezel | teeth `#7C7B7E`–`#A09E9F` (per tooth), groove `#59595B` | |
| Case / bracelet | 8 tonal levels `#1E1E1F` … `#F1F1F1` | k-means on luminance |

Shading of the dial: 72 colour samples (one per 5°) are stored in `assets/boreal-data.js`; brush texture amplitude ≈ 4 / 255 luminance, correlation ≈ 0.55°.

## Facts used
Official page: SISTEM51 automatic (mechanical, self-winding), 51 parts, 90-hour power reserve,
exceptional anti-magnetic qualities, Swiss made, polished stainless steel case and bracelet,
openwork caseback, sun-brushed blue dial with maritime compass-inspired design, 3 bar, clasp material
stainless steel, collection "Core".
Retailer listings (found via search, not on the official page): 42.00 mm diameter, 13.80 mm thickness,
50.60 mm lug-to-lug, butterfly clasp.

## Not measured / reconstructed
See “Limitations” in `PIPELINE.md`: hidden glyph parts (hour “10” zero, hour “2”, minute label “10”, logo “a”, SWISS “I”), hand parallax,
static lighting of the metal, typeset date digits, and the caseback (still the earlier illustration).
