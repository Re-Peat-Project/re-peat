# Sources for chapter 5 (Sub-KHG delineation)

Paths are relative to the workspace root. "Doc 17" = `re-peat/docs/17-subkhg-delineation-background.md`. "Report <KHG>/<dem>" = `_khg/<folder>/02_delineation/<dem>/delineation_report.json`, read with the workspace Python in this task (unit counts and areas also checked against `subkhg_units.gpkg` in the same folder, areas in a local UTM projection; identical to 0.1 km²).

## What a sub-KHG is

- KHG areas: Saleh-Sugihan 1,896.6 km² (Report Saleh-Sugihan/deltadtm, area_km2.total), Kampar-Gaung 7,111 km² (`re-peat/sites/14.02-04-05.01_kampar_gaung/README.md` line 7), Mendahara-Batanghari 2,012 km² and Sugihan-Lumpur 6,347 km² (`re-peat/reports/dem_benchmark/report.md` lines 19-20).
- SK.129/2017 defines no level below the KHG; the only regulated sub-unit is the P.15/2017 water management zone defined by 1 m elevation bands: Doc 17 lines 35, 41.
- Sub-KHG is the unit of the neraca, prioritisation and canal-block planning: Doc 17 line 3; `repeat-delineation/README.md` line 3.
- 2021 Kahayan-Sebangau study (purpose, outlet concept, D8, Strahler order 7, LiDAR plus WorldDEM, 16 units of 35.0-1,491.2 km², KHG 4,508 km², field check, wide outlet canals): Doc 17 lines 11-20 (report pages 25-28, 45-48, 64-66).
- Cahyono et al. 2022 abstract wording: Doc 17 line 29.
- Pulau Padang 2018 study, same chain, 11 units: Doc 17 line 27.
- Jaenicke et al. 2010, two sub-catchments named after outlet rivers, 30 m DTM: Doc 17 line 44.
- Cobb et al. 2017 "within a network of rivers or canals": Doc 17 line 47 (abstract only).

## Method (described from the code)

- Steps 1-7: `repeat-delineation/src/repeat_delineation/delineate.py` (`SUBKHG_DEFAULTS` lines 35-48; `_prepare` lines 274-334: burn, pysheds fill_pits, fill_depressions, resolve_flats, flowdir, accumulation, stream_order, threshold in km²; `_units_auto` lines 256-271: start 5 km², × 1.1 per step until count ≤ target_count[1]; `_merge_small` lines 175-205: smallest first, longest divide border, channel border only without a divide neighbour; `delineate` lines 358-418: outlet set order, channel cells to nearest unit, clip, numbering north to south).
- 30 m grid: `repeat-delineation/src/repeat_delineation/config.py` line 12 (`grid_res_m: 30`); no override in the generated configs `re-peat/sites/<folder>/<dem>/delineate.yaml`. Bilinear warp: `repeat-common/src/repeat_common/grid.py` line 135. Grid over the KHG plus 1 km: `repeat-delineation/docs/delineation_flow.drawio` (box "1. Grid").
- Chain settings (Kanal Primer, Kanal Sekunder; min_area auto; merge adjacent): `re-peat/pipeline.yaml` lines 66-69; `params` block of every chain delineation report.
- Tertiary canals are the plantation drainage grid: `re-peat/sites/14.02-04-05.01_kampar_gaung/README.md` line 65. All canals burned, only outlet classes are outlets: `delineate.py` lines 296-307.
- Coastal catchments split at 50 km²: `delineate.py` lines 43, 87-125.
- Mapped outlets alone in all 12 runs (`outlet_order` null, `tried` = [["mapped channels", n]]): all 12 chain reports.
- No external basis for count or minimum area: Doc 17 line 104.
- Secondary canals added 2026-10-26 after stability test (ARI 0.47 to 0.63): `re-peat/sites/16.02.01_sugihan_lumpur/delineate.yaml` (comment on outlet_canal_classes). First runs 2026-10-16 primary only: `re-peat/sites/14.02-04-05.01_kampar_gaung/README.md` lines 3, 65; `re-peat/sites/16.02.01_sugihan_lumpur/README.md` lines 3, 46.
- 2021 study counted primary and secondary canals for IPG, ignored tertiary: Doc 17 line 24.
- Method diagram: `repeat-delineation/docs/delineation_flow.drawio` (generated from the code by `repeat-delineation/docs/delineation_diagram.py`).

### Docs differ from code (rule 5)

- `repeat-delineation/README.md` line 46 lists the outlet channels as "mapped rivers + outlet canals + DEM streams of order >= k". The code (`delineate.py` lines 372-392) first tries the mapped outlets alone and adds DEM streams only when the count is outside `target_count`. Doc 17 line 56 and the drawio describe the code correctly. The chapter follows the code.
- Default outlet classes in the code are `primer`, `primary` (`delineate.py` line 46; README line 40); the chain overrides them with Kanal Primer and Kanal Sekunder (`re-peat/pipeline.yaml` line 67). The chapter states the chain setting.

## Results

All numbers from the 12 chain reports (Report <KHG>/<dem>): n_subkhg, pieces_before_merge, min_area_km2, area_km2 (min, median, max, total), inputs.outlet_canal_segments, inputs.rivers_segments.

| KHG | DEM | Units | Pieces | Min area (km²) | Min / median / max (km²) | Total (km²) | Outlet canal segments | River segments |
|---|---|---|---|---|---|---|---|---|
| Kampar-Gaung | lidar | 28 | 18,534 | 105.6 | 109.2 / 215.7 / 621.0 | 7,096.3 | 977 | 16 |
| Kampar-Gaung | deltadtm | 27 | 17,504 | 116.1 | 128.4 / 224.9 / 538.8 | 7,110.5 | 977 | 16 |
| Kampar-Gaung | demnas | 29 | 15,435 | 116.1 | 127.5 / 214.8 / 510.6 | 7,110.5 | 977 | 16 |
| Mendahara-Batanghari | lidar | 29 | 16,881 | 30.6 | 35.5 / 63.5 / 139.8 | 2,011.2 | 2,190 | 5 |
| Mendahara-Batanghari | deltadtm | 29 | 15,500 | 33.6 | 39.3 / 54.8 / 202.9 | 2,012.3 | 2,190 | 5 |
| Mendahara-Batanghari | demnas | 29 | 14,877 | 30.6 | 35.5 / 56.5 / 151.0 | 2,012.3 | 2,190 | 5 |
| Saleh-Sugihan | lidar | 29 | 5,885 | 17.3 | 20.3 / 38.7 / 76.5 | 1,173.4 | 3,080 | 4 |
| Saleh-Sugihan | deltadtm | 26 | 13,911 | 27.8 | 31.7 / 74.5 / 137.3 | 1,896.6 | 3,080 | 4 |
| Saleh-Sugihan | demnas | 27 | 13,868 | 30.6 | 37.3 / 66.8 / 137.8 | 1,896.6 | 3,080 | 4 |
| Sugihan-Lumpur | lidar | 29 | 21,137 | 116.1 | 126.2 / 220.8 / 373.0 | 6,345.6 | 4,387 | 2 |
| Sugihan-Lumpur | deltadtm | 29 | 19,140 | 105.6 | 117.6 / 189.4 / 413.0 | 6,347.2 | 4,387 | 2 |
| Sugihan-Lumpur | demnas | 27 | 18,920 | 105.6 | 121.1 / 223.0 / 481.0 | 6,347.2 | 4,387 | 2 |

- Saleh-Sugihan LiDAR coverage about 1,174 km² (62%): see `04_dem.sources.md` (computed in this task) and `repeat-dem/docs/test-run-sebangau.md` line 422.
- Surface provenance: Mendahara and Sugihan-Lumpur DeltaDTM/DEMNAS delineations read `01_dem/benchmark/04_processed/<dem>/dtm_smooth.tif` (`re-peat/sites/15.05-07-10.01_mendahara_batanghari/<dem>/delineate.yaml`, `re-peat/sites/16.02.01_sugihan_lumpur/<dem>/delineate.yaml`); Kampar-Gaung and Saleh-Sugihan read `01_dem/processed/<dem>/dtm_smooth.tif`. Fallback order: `re-peat/tools/pipeline/steps.py` lines 49-50. Benchmark used curated tiles, chain streams them, same parameters: header comments of `re-peat/tools/pipeline/templates/dem_correction_*.yaml`.
- Chain completed for these four KHG: `_khg/pipeline_status.csv`.
- Map placeholder layers: `_khg/16.02.01_sugihan_lumpur/02_delineation/lidar/subkhg_units.gpkg` (fields khg_id, unit_id), `_khg/16.02.01_sugihan_lumpur/00_inputs/canals.gpkg` (field KET_KANAL; class field named in `re-peat/sites/16.02.01_sugihan_lumpur/delineate.yaml`).

## Sensitivity and stability

- Stability set-up (7 DTMs, flat, 5 noise members, sigma 0.25 m, correlation 500 m, written before any run; reference LiDAR): `re-peat/sites/16.02.01_sugihan_lumpur/delineation_stability.yaml`.
- ARI table: `_khg/16.02.01_sugihan_lumpur/02_delineation/stability/summary.csv`.
- Per-member units, IoU, ARI, largest unit 1,353.2 km² (primary) and 373.0 km² (primary+secondary): `_khg/16.02.01_sugihan_lumpur/02_delineation/stability/members.csv`.
- The "DeltaDTM" members are `deltadtm_base_m300_g150` and `deltadtm_base_m1200_g600`, made from the processed DeltaDTM `dtm_corrected.tif` (ICESat-2 class offsets, not smoothed) and smoothed by `repeat-dem/script/demnas_ground_filter.py` (`repeat-dem/benchmark/demnas_ground_filter.yaml` lines 5-7).
- Flow merge agrees less, adjacent stays: Doc 17 line 108; summary.csv.
- Boundary-frequency figure: `_khg/16.02.01_sugihan_lumpur/02_delineation/stability/boundary_frequency.png`.
- Sweeps: Kampar-Gaung 5,581 pieces, 247/129/107/73/42/35/21/13/9, nearest 186/99/79/42/5/2/2/1/1: `re-peat/sites/14.02-04-05.01_kampar_gaung/README.md` line 66. Sugihan-Lumpur 6,219 pieces, 182/107/93/59/37/27/18/12/6, nearest 161/94/74/34/5/2/1/1/1: `_khg/16.02.01_sugihan_lumpur/02_delineation/delineation_sweep.json`; `re-peat/sites/16.02.01_sugihan_lumpur/README.md` line 52.
- Same LiDAR, two reads: 30 units, min area 105.6 km², 113.0-373.0 km² from the source file `lidar_klhk/dem_25m/DEM25M/OKI25.tif` (`_khg/16.02.01_sugihan_lumpur/02_delineation/delineation_report.json`, dated 2026-10-26, config `re-peat/sites/16.02.01_sugihan_lumpur/delineate.yaml`), against 29 units, 116.1 km² from the chain clip `01_dem/inputs/lidar_oki25.tif` (Report Sugihan-Lumpur/lidar, 2026-10-28). Cause not investigated.

## Limits

- No official sub-KHG layout for these KHG: `re-peat/sites/14.02-04-05.01_kampar_gaung/README.md` line 123; Kahayan-Sebangau chain status "to do": `_khg/pipeline_status.csv`.
- Canal layer has class and length only, no flow direction or dimensions; units carry no outlet or topology: Doc 17 lines 82-84, 100.
- No dome-crest layer: Doc 17 lines 59, 87.
- Concessions not used; plantations may change boundaries: Doc 17 lines 14, 63.
- TerraClimate cell about 21 km²; smallest 2021 unit spans about 1.6 cells; Sugihan-Lumpur smallest units about 6 cells: Doc 17 line 90. The chapter's 118-126 km² are the smallest chain units at Sugihan-Lumpur (Reports Sugihan-Lumpur/*).

## Contradictions between sources

- Sugihan-Lumpur unit numbers differ by source: runbook `re-peat/sites/16.02.01_sugihan_lumpur/README.md` line 47 gives 28 units, 96 km², 101-1,358 km² (2026-10-16, KLHK modelled DTM, primary canals only); Doc 17 line 60 says the last run on file was made with the KLHK modelled DTM, 116.1 km², 27 units of 131.7-463.4 km²; the top-level `_khg/16.02.01_sugihan_lumpur/02_delineation/delineation_report.json` now holds 30 units, 105.6 km², 113.0-373.0 km² (LiDAR, primary+secondary); the chain LiDAR run gives 29 units, 116.1 km², 126.2-373.0 km². The chapter reports the chain run and notes the 30/29 difference. Doc 17 is out of date on this point.
- `re-peat/sites/16.02.01_sugihan_lumpur/README.md` line 40 counts 14,928 canal segments (623 primary, 3,764 secondary, 10,541 tertiary), Doc 17 line 81 counts 14,156 (549, 3,494, 10,113) from `khg_data_recap.csv`. The chapter uses the 4,387 outlet segments of the chain report, which match the first count (623 + 3,764).
- Saleh-Sugihan LiDAR coverage 98.3% (`re-peat/sites/khg_dem_inputs.csv`, `re-peat/sites/16.02-07.01_saleh_sugihan/khg.yaml`) against 62% (`repeat-dem/docs/test-run-sebangau.md` line 422 and the units area); code cause in `04_dem.sources.md`.
- The DEM benchmark's sub-KHG comparison (`re-peat/reports/dem_benchmark/report.md` lines 116-122) does not state that it used primary canals only; the reports under `01_dem/benchmark/05_pipeline/` show it did.

## References cited

- Cahyono, B. K., Aditya, T., Istarno (2022). The Determination of Priority Areas for the Restoration of Degraded Tropical Peatland Using Hydrological, Topographical, and Remote Sensing Approaches. Land 11(7), 1094. https://doi.org/10.3390/land11071094 (abstract only). From Doc 17 line 126.
- Cobb, A. R., Hoyt, A. M., Gandois, L., et al. (2017). How temporal patterns in rainfall determine the geomorphology and carbon fluxes of tropical peatlands. PNAS. https://doi.org/10.1073/pnas.1701090114 (abstract only). From Doc 17 line 130.
- Jaenicke, J., Wösten, H., Budiman, A., Siegert, F. (2010). Planning hydrological restoration of peatlands in Indonesia to mitigate carbon dioxide emissions. Mitigation and Adaptation Strategies for Global Change 15, 223-239. https://doi.org/10.1007/s11027-010-9214-5. From Doc 17 line 127.
- Laporan Akhir, Penyusunan Neraca Air KHG Sungai Kahayan - Sungai Sebangau (2021). Local file `re-peat/docs/Laporan Akhir KHG SK SS _.pdf`, as summarised in Doc 17 lines 7-25, 113. Cited in the text as "Laporan Akhir KHG Kahayan-Sebangau 2021".

- Diagram: the report embeds a reader version drawn in draw.io, re-peat/reports/project_report/diagrams/*_report.drawio (plain labels; same boxes and edges as the module original).
