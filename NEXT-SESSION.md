# Next session — open items

Context: PR #1 (`edge-detection-pipeline`) rebuilt the watch from the official photo; the Edge lab (section 07) is liked as is. Pipeline docs: `PIPELINE.md`; data: `assets/boreal-*.js`; scripts: `pipeline/`. Photos live in the git-ignored `source/` (front_a, front_b, back).

## Done since the last notes (uncommitted)
- Compass section removed; specs is 06, Edge lab 07.
- Hands follow the light: two-lobe steel facet model in `main.js` (`FM`, `facetF`, `facetFactor`), driven by hand angle and light angle, near-white to ~#15151A; hub pad has a light overlay. Only two measured poses exist; the dark floor is a physical assumption.
- Seconds hand has the steel disc seen at 6 o'clock in the photo (data: `hands.second.pad`, also in the static SVG).
- Caseback traced from the back photo: `pipeline/s13_caseback.py` -> `assets/boreal-back.js` (~1.1 MB, lazy-loaded), Edge lab stage "Caseback" with a layer slider.

## Ideas / known gaps
- Caseback: plate grain is flattened, the engraved rim text (AUTOMATIC, MAXIMUM ...) is only partly legible, wheels do not turn (the old animated wheels are gone). Could shrink the file (plate classes ~400 KB, body ~330 KB) with a coarser grid or fewer classes, or split the gold wheels into a separate layer that can rotate.
- Hands: more evidence (other official angles, e.g. li1/li2 lifestyle shots) would let the facet model be fitted with real extremes; consider 3-4 facets (ridge + bevels).
- The seconds-hand disc: confirm whether it belongs to the hand (rotates) or is fixed on the dial; needs a photo with the seconds hand elsewhere.

## Already known (from PIPELINE.md, lower priority)
- Hands IoU 0.53 because of photo parallax (removed on purpose).
- Reconstructed glyphs: hour 10 zero, hour 2, minute 10, logo "a", SWISS "I".
- Numerals 4 and 5 slightly ragged; date digits typeset (Poppins) instead of traced.
- Metal is one static lighting (gloss overlay + rotating bezel colours only).
