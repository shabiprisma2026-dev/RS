# RS – remote sensing / mining survey work

The user writes in Persian. Reply in Persian. Do not guess coordinates: say when something is approximate.

## Contents
- `Abadan_Pt_report_*` – earlier report (Word/PDF).
- `gcp/` – GCP / check-point layout for a 186 ha drone survey area (`make_gcp.py`, KML, CSV).
- `cadastre/` – **active project**: the "orange strip" (محدوده نارنجی) on cadastre.mimt.gov.ir and its mineral prospectivity.
  - `orange_area.kml`, `orange_area.md` – strip geometry, **v2** (top section of the .md is authoritative; the v1 tables below it are kept only as history).
  - `make_orange_kml.py` – builds the KML from `CENTRE_UTM` (UTM 40N, EPSG:32640), width 42 m.
  - `screenshots/` – the two cadastre screenshots everything is derived from.
  - `prospect/` – Sentinel-2 / DEM analysis and `prospectivity_report.md` (current findings + next steps).

## Key facts (cadastre project)
- Location: Shotori Range, ~37 km E of Tabas, South Khorasan; strip centre ≈ 57.320E 33.616N.
- Strip: ~819 m long, 42 m wide, on a dry valley floor (1535–1565 m), inside a dark rock body flanked by bright carbonate ridges.
- Georeferencing: screenshots matched to Sentinel-2 2024-08-15 (tile 40SEC), ±~50 m. Not yet checked against official cadastre vertex coordinates.
- Sentinel-2: no gossan / clay-OH anomaly in the strip. Targets: dark-body/carbonate contacts (MVT Pb-Zn-F-Ba, Shotori Fm), possible coal-bearing clastics.
- Exploration licence (yellow) ≈ 5.6 km SE at ~57.378E 33.601N – commodity unknown.

## Open tasks (needs Iranian internet / user's browser)
1. ngdir.ir: 1:100k geology sheet, stream-sediment geochemistry (Pb, Zn, Ba, F, Cu, As, Sb), mineral occurrences near the strip.
2. cadastre.mimt.gov.ir: commodity/status of the yellow licence and neighbouring purple blocks; official vertex coordinates of the strip if shown.
3. Google Earth: high-res check for old workings, gossans, veins, coal seams.
4. ASTER (Earthdata login) for carbonate/silica/Al-OH/Mg-OH mapping.
5. Update `cadastre/prospect/prospectivity_report.md` with the results.

## Running the analysis
```
pip install -r requirements.txt
cd cadastre/prospect
python download_data.py      # Sentinel-2 COGs + Copernicus DEM from AWS (no login)
python match_screenshot.py   # screenshot ↔ Sentinel-2 matching
python spectral_indices.py   # indices, stats inside the strip, maps
cd .. && python make_orange_kml.py
```

## Git
Work branch: `claude/clever-galileo-reel2u`.
