# Validated Lab Data — Round 2 (ABP)

Drop the chemist's validated deliverables here:

- Validated Round 2 EDDs (.xlsx / .csv)
- Validation report PDFs
- Any per-analyte notes from the project chemist
- Updated Hg / As / Sb / Tl results, with lab qualifier flags (J, U, UJ, etc.)
- COC / sampling-date references if available

How it gets used
----------------
Once files are in this folder, the visualizer's embedded `DATA` (and the
`abp_samples.geojson` source + the master `.xlsx`) are refreshed from the
validated numbers. The "UNVALIDATED DATA" badge in the top bar gets dropped
for Round 2 once all four analytes are reconciled. Lab qualifier flags are
carried through to the sample popups and CSV export.

Notes
-----
- Original / unvalidated source files live in their existing locations and
  are not modified here.
- Anything dropped in this folder is published with the GitHub Pages site
  (the repo is public). If a deliverable shouldn't be public, push it to a
  feature branch instead and tell Mo which branch to pull from.
