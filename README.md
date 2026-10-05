# SISTEM BOREAL YIS401GC — visual study

A one-page site that rebuilds the Swatch SISTEM BOREAL YIS401GC in code, using colours and geometry
measured from the official product photos (see `DESIGN-NOTES.md`).

Unofficial fan study, not affiliated with Swatch. The watch is redrawn in SVG/CSS; no Swatch image files are used.

## Run
Open `index.html`, or serve the folder:

    python -m http.server 8765

No build step. Fonts (Poppins, Barlow Condensed, IBM Plex Mono, Vazirmatn) load from Google Fonts with fallbacks.

## What is on the page
- Live watch: sun-brushed dial lit by the pointer, fluted bezel, polished case and bracelet, draggable hands, real date.
- Light lab: slider turns the light; shows the perceived blue.
- Geometry lab: toggle the compass rings, six-point star, rays, numerals, minute track.
- Palette: measured HEX values, click to copy.
- Anatomy: scroll-driven exploded view (case, fluted bezel, dial, hands, crystal).
- Movement: scroll flips the watch to the openwork caseback.
- Compass, specs table (official vs retailer-listing vs photo), FA (RTL) / EN toggle, reduced-motion support.
