# Build Spec — SBMM ABP Soil Contamination Visualizer & Figure Tool

## 0. How to use this document

This is a build specification to hand to Claude Code. Build a **single-file, self-contained HTML web app** (no server, no build step) that visualizes the Round 1 + Round 2 surface-soil sampling data for the Area Between Piles (ABP) at the Sulphur Bank Mercury Mine (SBMM) Superfund Site, and lets the user draw, measure, and export publication-style figures.

The data file `abp_samples.geojson` ships alongside this spec in the same folder. The app must load it (with a fetch + a hard-coded fallback copy embedded in the file so it still works when opened via `file://`).

**Hard constraints**
- Single `index.html` file, all CSS/JS inline. External libraries from CDN only (listed below).
- Must run by double-clicking the file (no local server required). Because `fetch()` of a local file fails under `file://`, embed the GeoJSON as a `const DATA = {...}` JS object as the primary source, and optionally allow a file-picker to load an updated GeoJSON.
- No backend, no API keys that aren't free/keyless. Use Esri World Imagery (keyless) as the satellite base layer; Google tiles require no key via the standard XYZ URL but Esri is safer for redistribution.
- Mapping stack: **Leaflet 1.9.4** (matches the existing SBMM planner tool the user already uses).

---

## 1. Project context (so design decisions make sense)

The ABP is the strip of land between the North Waste Rock Pile (NWP) and the Waste Rock Dam (WRD) at an inactive mercury mine. Soil is contaminated primarily with **mercury (Hg)** and secondarily **arsenic (As)**; **antimony (Sb)** and **thallium (Tl)** are also analyzed. The team is writing a tech memo and needs to (a) see where contamination is, (b) delineate the footprint that exceeds cleanup levels, and (c) explore whether portions of the area could meet a more stringent "background" target.

Two comparison thresholds matter, and the tool must support toggling between them:

| Analyte | ROD Remediation Goal (On-Mine, "unauthorized tribal user") | PMB / On-Mine Background |
|---|---|---|
| Mercury (Hg) | 204 mg/kg | 58 mg/kg |
| Arsenic (As) | 6.1 mg/kg | 6.1 mg/kg |
| Antimony (Sb) | 51 mg/kg | 0.52 mg/kg |
| Thallium (Tl) | 1.3 mg/kg | 0.47 mg/kg |

(These values are also embedded in the GeoJSON `metadata.criteria`. Read them from there so they stay in sync; don't hard-code a second copy.)

**Important caveat to surface in the UI:** Round 2 analytical data is UNVALIDATED. Show a small persistent "UNVALIDATED DATA" badge somewhere unobtrusive.

---

## 2. Data model

`abp_samples.geojson` is a standard FeatureCollection. Each feature is a `Point` (`coordinates: [lon, lat]`, WGS84). Properties:

**Common**
- `id` — sample/location ID (e.g. `SS-18`, `W01`, `E09`, `OS3`)
- `round` — `1` or `2`
- `sampled` — boolean (false = planned but not collected)
- `Hg`, `As`, `Sb`, `Tl` — shallow (0–0.5 ft) result in mg/kg, or `null`
- `rod_exceed` — `"YES"` / `"NO"` / `"NOT SAMPLED"`
- `rod_drivers` — comma list of analytes that exceeded ROD (e.g. `"Hg, As"`)
- `pmb_exceed`, `pmb_drivers` — same against PMB
- `depth` — `"Shallow"`, `"Shallow + Deep"`, or `""`
- `notes` / `field_note` — free text

**Round 2 only**
- `coord_source` — `"Relocated"`, `"Planned"`, `"Field (FM)"`, `"Manual (provided)"`
- `Hg_deep`, `As_deep`, `Sb_deep`, `Tl_deep` — 2–3 ft results where collected, else `null`
- `Hg_OM`, `OM_effect` — mercury in the co-located organic-matter (humus) sample, and whether OM is `"OM higher"`/`"OM lower"`/`"~equal"` vs the shallow soil
- `has_fd` — `"Yes"` if a field duplicate exists
- `not_sampled_reason` — populated for the 4 not-sampled R2 points

There are **94 features**: 41 Round 1 (32 sampled + 9 not sampled) and 53 Round 2 (49 sampled + 4 not sampled). Hg ranges 1.8–2,700 mg/kg. Map should auto-fit to data bounds; approximate center is `39.006336, -122.668003`.

---

## 3. Map & base layers

- Leaflet map, default zoom fit to feature bounds, max zoom 22.
- Base layer switcher with at least:
  - **Esri World Imagery** (satellite) — default
  - **Esri World Topo / OSM** (street/topo)
  - Optional: a blank/white background for clean figure export
- Scale bar (feet + meters). Live cursor lat/long readout. North arrow overlay (for figures).

---

## 4. Sample-point rendering

Render each feature as a marker whose **shape encodes round**, **fill color encodes the active "color-by" mode**, and **border encodes sampled vs not-sampled**:

- **Round 1** → circle
- **Round 2** → square
- **Opportunistic (id starts with `OS`)** → triangle
- **Not sampled** (`sampled=false`) → hollow/gray with dashed border, regardless of round
- Round-2 locations with **deep samples** (`depth` contains "Deep") → add a small dot/ring accent so surface+deep points are distinguishable.

**Color-by modes (dropdown, this is the core interaction):**
1. **ROD exceedance** — RED if `rod_exceed=="YES"`, GREEN if `"NO"`, GRAY if `"NOT SAMPLED"`.
2. **PMB exceedance** — same logic on `pmb_exceed`.
3. **By analyte concentration** — choose analyte (Hg/As/Sb/Tl) from a second dropdown; apply a graduated color ramp (see §6) with the chosen threshold (ROD or PMB) marking the breakpoint. Use a perceptually-uniform ramp (e.g. viridis or a white→yellow→orange→red ramp for contamination).
4. **By round** — Round 1 vs Round 2 distinct colors (for the combined-figure story).
5. **By driver** — color by which COC drives the exceedance (Hg / As / both / none).

A **dynamic legend** must update to match the active mode (show threshold value, color bins, and shape key).

**Popups** on click: show id, round, coord source, sampled status, all four analytes (shallow + deep where present), OM Hg + effect, ROD & PMB exceedance + drivers, depth, FD flag, field note, and not-sampled reason. Make popup copy-friendly.

**Labels:** toggle to show/hide `id` labels next to each point (needed for figure export). Labels should auto-declutter or at least be draggable.

---

## 5. Heat map (contamination intensity)

- Use **Leaflet.heat** (`leaflet-heat`) or a Turf.js-based interpolation.
- Heat intensity weighted by the **selected analyte's concentration** (default Hg), normalized.
- Provide controls: analyte selector, radius, blur, max-intensity, and an opacity slider.
- Toggle on/off independently of the point layer.
- **Bonus / SOTA:** offer a true **IDW (inverse-distance-weighted) interpolation surface** as an alternative to the kernel-density heatmap, clipped to the convex hull (or a user-drawn boundary) of the sample points, rendered as a colored raster/canvas overlay with the same ramp as §6. This is the more defensible "contamination surface" for a figure. Use Turf.js (`@turf/turf`) for hull + interpolation, or implement a simple IDW on a canvas grid.

---

## 6. Color ramps & thresholds

- Use a single shared color scale utility. Suggested ramp for concentration: `#2c7bb6 → #ffffbf → #fdae61 → #d7191c` (blue-low to red-high) or viridis.
- For exceedance modes use solid semantic colors: RED `#d7191c`, GREEN `#1a9641`, GRAY `#9e9e9e`.
- Threshold lines/bins must reference the active criterion set (ROD vs PMB) pulled from `metadata.criteria`.
- Provide a "Color by ratio to threshold" option (concentration ÷ threshold) so 1× = at the line, >1× = exceedance — this normalizes across analytes and is great for the multi-COC figure.

---

## 7. Drawing, measurement & figure creation (key requirement)

Use **Leaflet-Geoman** (`@geoman-io/leaflet-geoman-free`) — it's the modern, actively-maintained successor to Leaflet.draw and supports polylines, polygons, rectangles, circles, text markers, editing, dragging, and snapping.

Required tools:
- **Polyline** drawing — for delineation boundaries, transects, cross-section lines, haul-road alignments. Show running length (ft + m).
- **Polygon** drawing — for excavation/remediation footprints. On completion, compute and display **area (ft², acres, m²)** using Turf.js.
- **Rectangle & circle** — quick AOIs.
- **Text/label annotations** placeable on the map (figure captions, callouts).
- **Edit / drag / delete** any drawn shape; **snap** vertices to sample points.
- **Style controls** for drawn shapes: line color, weight, dash, fill color, fill opacity — so the user can match figure conventions.
- Each drawn shape gets an editable label and optional note.

**Volume estimate helper (SOTA):** when a polygon is drawn, let the user enter an assumed excavation depth (ft) and report an estimated soil **volume (cubic yards)** = area × depth. This supports the memo's remedy/volume discussion. Also report how many sample points fall inside the polygon and the min/mean/max Hg (and other analytes) within it.

---

## 8. Filtering & analysis panel

A collapsible side panel with:
- **Round filter:** R1 only / R2 only / both.
- **Sampled filter:** show/hide not-sampled (planned) points.
- **Exceedance filter:** show only ROD exceedances / only PMB exceedances / only "clean" (passes both) / all.
- **Analyte threshold slider:** show only points where selected analyte > X mg/kg (live).
- **Depth filter:** surface only / has-deep.
- **Search box:** zoom to a sample by id.
- **Stats readout (live, reflects current filter):** count by category, # ROD exceedances, # PMB exceedances, min/mean/median/max per analyte, % exceeding each threshold. This mirrors the kind of summary stats the memo needs.
- **OM vs Shallow mini-view:** for Round 2, a small toggle/table or scatter (OM Hg vs shallow Hg) with a 1:1 reference line, since the team is comparing humus-layer Hg to soil Hg. Color points by `OM_effect`.

---

## 9. Data-gap analysis (carry over from the existing planner tool)

- Adjustable grid overlay (25/50/75/100 ft cells). Color each cell by sample density within a radius: red = 0 samples (gap), yellow = 1–2, green = 3+. This helps justify where Round 2 filled gaps and where residual gaps remain (e.g. the vegetation-blocked not-sampled points).

---

## 10. Export / import (figure output is the point of the tool)

- **Export current map view as a high-resolution PNG** (use `leaflet-easyPrint` or `dom-to-image`/`html2canvas`) including legend, scale bar, north arrow, and a title block the user can edit. This is how they'll generate draft figures for the memo.
- **Export to PDF** (letter/11×17 landscape) — optional but desirable; can be "print to PDF" via a print-optimized CSS layout.
- **Export drawn shapes as GeoJSON** (so Greg/GIS can pull boundaries into ArcGIS).
- **Export filtered sample set as CSV** (id, lat, lon, analytes, flags).
- **Import GeoJSON** — both to (a) reload an updated `abp_samples.geojson` when validated data arrives, and (b) load previously drawn shapes.
- **Save/restore session** to `localStorage` (drawn shapes, active layers, filters) so work isn't lost on reload. Provide an explicit "Save" and "Load" plus auto-save.

---

## 11. UI / layout

- Left collapsible control panel (layers, color-by, filters, draw tools, export). Map fills the rest.
- Top bar: title "SBMM ABP Soil Contamination Visualizer", base-layer switch, UNVALIDATED badge, project tag "OU1 · D3913200 · Task 2.1.5".
- Floating legend (bottom-right), collapsible.
- Responsive enough for a laptop screen; this is an internal desktop tool, not mobile-first.
- Clean, professional, low-chrome aesthetic suitable for environmental consulting. Avoid playful styling.

---

## 12. Recommended libraries (all CDN, keyless)

- Leaflet 1.9.4 — `https://unpkg.com/leaflet@1.9.4/dist/leaflet.{css,js}`
- Leaflet-Geoman free — `https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.css` + `.js`
- Leaflet.heat — `https://unpkg.com/leaflet.heat/dist/leaflet-heat.js`
- Turf.js — `https://unpkg.com/@turf/turf@6/turf.min.js`
- Esri World Imagery tiles (XYZ, keyless): `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`
- For PNG export: `html2canvas` or `leaflet-easyPrint`.
- (Optional charts for the OM scatter / stats: Chart.js.)

---

## 13. Acceptance criteria (definition of done)

1. Opens by double-click (file://), loads all 94 points from embedded data, fits bounds.
2. Color-by dropdown switches cleanly between ROD, PMB, analyte-concentration, round, and driver modes, with a matching dynamic legend each time.
3. Shapes encode round (circle/square/triangle) and not-sampled points are visually distinct (hollow/gray).
4. Heat map toggles on/off and re-weights by selected analyte; IDW surface option works and is clipped to the data hull.
5. User can draw a polyline (shows length), draw a polygon (shows area + acres + in-polygon sample stats + optional volume), edit/drag/delete shapes, and style them.
6. Filtering by round / sampled / exceedance / analyte-threshold / depth updates both the map and the live stats readout.
7. Clicking a point shows a full, copy-friendly popup including not-sampled reason and OM data.
8. Export PNG produces a figure with legend, scale bar, north arrow, and editable title; export drawn shapes as GeoJSON; export filtered points as CSV.
9. Session (shapes/filters/layers) persists across reload via localStorage.
10. "UNVALIDATED DATA" badge is visible; criteria values come from `metadata.criteria`, not hard-coded twice.

---

## 14. Nice-to-have (SOTA) if time allows

- **Split-screen / swipe** comparing ROD vs PMB coloring side by side (leaflet-side-by-side).
- **Time/round slider** animating Round 1 → Round 2 appearance.
- **Cluster toggle** (Leaflet.markercluster) for dense areas.
- **Cross-section profile:** draw a polyline, get a profile chart of nearest-sample Hg vs distance along the line.
- **Auto-delineation:** draw a contour at the active threshold from the IDW surface (marching squares) and output it as a polygon the user can edit — this is essentially the "extent of contamination" line the memo needs.
- **Print layout templates** sized for figures referenced in the memo (Site Location, Sample Locations, Hg Results, As Results).

---

## 15. Deliverable

A single `index.html` (plus the `abp_samples.geojson` for reference/reload). Keep all logic in that one file. Comment the code by section so the team can tweak thresholds, colors, and labels later without a build step.
