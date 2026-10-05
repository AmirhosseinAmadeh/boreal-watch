# Design notes — what was measured, and from where

Source of truth: the official Swatch product page
https://www.swatch.com/en-en/sistem-boreal-yis401gc/YIS401GC.html and its product photos.
The watch in this site is redrawn from scratch in SVG/CSS; no Swatch image file is stored or served.

## Colours (median pixel of each region of the official front/back photos)
| Role | HEX | Note |
|---|---|---|
| Dial, dark brushed wedge | #02103D | 5th percentile of dial luminance |
| Dial, median | #05255A | |
| Dial, lit lobe | #094782 | 75th percentile / bright sector |
| Dial, outer chapter band | #063A6E | band just inside the bezel |
| Printed lines | #D3D9E4 | thin white-blue lines and numerals |
| Hands | #BBBABC | shadow #87878B, highlight #E7E6EA |
| Fluted bezel | #807E7F | groove #595758, ridge #999798 |
| Case, polished | #C4C5C1 | highlight #EDEDEB |
| Bracelet | #B8B8B8 | |
| Seconds hand | #C81A35 | |
| Caseback plate | #A7AEB4 | |
| Caseback gold | #D9B866 | few pixels, JPEG-lightened; gradient goes darker |
| Caseback dark parts | #3B3D3D | |

Surface composition of the front photo: steel ≈ 64%, blue ≈ 35%, red ≈ 0.2%.
(The earlier brief had a 65/25/5/5 split and #D42632 for red; the measured values replace it.)

## Dial geometry (R = dial radius = 1.0)
- inner ring 0.22R · mid ring 0.53R · outer ring 0.73R
- eight rays at 45° steps, 0.24R – 0.36R
- six-point star (two triangles), vertices at 0.77R; one apex at 12
- hour numerals centred at 0.63R, cap height ≈ 0.17R, 3 replaced by the date window
- minute numerals at ≈ 0.80R; minute ticks 0.94 – 0.98R; 5-minute batons 0.89 – 0.98R
- date window at 3: x 0.61R – 0.79R, height ≈ 0.14R
- seconds hand: red, tail to ≈ 0.33R, ring hub; silver faceted hour/minute hands
- dial is sun-brushed (fine radial lines) with two opposite bright lobes
- fluted (coin-edge) bezel ≈ 1.0R – 1.15R; polished case with integrated lugs; three-column steel bracelet

## Facts used
Official page: SISTEM51 automatic (mechanical, self-winding), 51 parts, 90-hour power reserve,
exceptional anti-magnetic qualities, Swiss made, polished stainless steel case and bracelet,
openwork caseback, sun-brushed blue dial with maritime compass-inspired design, 3 bar, clasp material
stainless steel, collection "Core".
Retailer listings (found via search, not on the official page): 42.00 mm diameter, 13.80 mm thickness,
50.60 mm lug-to-lug, butterfly clasp.

## Not verified / approximated
- Hour-numeral rotation rule and exact numeral font (Barlow Condensed is a stand-in).
- Hand outlines, bracelet link pattern, and caseback layout are redrawn by eye from the photos.
- The dial wordmark is set as plain text in Poppins, not the official logo artwork.
