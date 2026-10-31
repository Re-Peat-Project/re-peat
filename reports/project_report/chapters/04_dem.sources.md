# Sources for chapter 4 (Terrain: DEM investigation)

Paths are relative to the workspace root. "Benchmark report" = `re-peat/reports/dem_benchmark/report.md`.

## Why terrain matters

- 0.4 m water-table limit, 0.3 m head drop between canal blocks: `re-peat/docs/02-dtm.md` line 7. The 0.4 m criterion itself was seen in P.10/2019 Gambar 1 and in the 2021 Kahayan-Sebangau report, not in the PP 57/2016 text (`re-peat/docs/17-subkhg-delineation-background.md` line 136).
- Dome slope 1-2 m/km near rivers, under 0.5 m/km in the centre, Block C: `re-peat/docs/17-subkhg-delineation-background.md` line 45 (Ritzema et al. 2014).
- Real 1 km height difference 0.46 m (Mendahara), 0.38 m (Sugihan-Lumpur): benchmark report lines 11, 19-20.

## Candidate sources

- LiDAR from KLHK Direktorat Gambut archive 2015-2024, 25 m, flight dates and datum not recorded: benchmark report lines 22, 35. 20 m Sugihan-Saleh LiDAR: `re-peat/sites/khg_dem_inputs.csv` (row 16.02-07.01 lidar, res_m 20.0).
- DEMNAS 8 m surface model; KLHK modelled DTM 12 m, method unknown; GLO-30 30 m DSM; FABDEM v1.2 30 m (Hawker et al. 2022); DeltaDTM v1.1 30 m, land below ~10 m +MSL, CC BY 4.0, Pronk et al. 2024: benchmark report lines 30-34.
- DeltaDTM built from CopernicusDEM (TanDEM-X 2012-2015) corrected with ICESat-2 and GEDI, non-terrain cells removed, defined for land below 10 m +MSL: `re-peat/docs/14-data-catalog.md` line 54.
- GLO-30 from TanDEM-X data of 2011 to 2015: benchmark report line 149.
- FABDEM = machine-learning forest correction of GLO-30: `repeat-dem/docs/test-run-sebangau.md` line 277. FABDEM licence CC BY-NC-SA 4.0 (Bristol), Non-Commercial Government Licence v2.0 (mirror), KLH status unclarified: `repeat-dem/AGENTS.md` line 27; `repeat-dem/docs/test-run-sebangau.md` line 294.

## What DEMNAS is

- Inputs IFSAR 5 m, TerraSAR-X 5 m, ALOS PALSAR 11.25 m, mass points; 0.27 arc-second (about 8 m), EGM2008: `repeat-dem/docs/demnas-literature.md` lines 9-10.
- Mass points 20-50 m apart, denser on craggy terrain, sparser on flat ground (2018 prototype): same file line 12.
- Flat forested domes lowest mass-point density (inference stated in the review): same file line 15.
- Julzarika & Harintaka "dominated by DSM" (S. Kalimantan), "neither DSM nor DTM" (C. Java), about 20 points, profile comparison: same file line 27.
- Accuracy table (2.237/3.679 m, 142 GCPs; 2.79 m BIG portal; 4.968/8.172 m, 60 GPS pre-marks, Bogor 30-2000 m): same file lines 22-24.
- Published figures are best case for forest (open-ground references): same file line 33.
- 8.17 m is LE90, LE90 = 1.645 × RMSE, RMSE 4.97 m: same file line 29.
- No sub-metre accuracy published anywhere: same file line 34.

## Earlier tests

- Three sites, ICESat-2 ATL08 2019-2025, 2 km block split: `repeat-dem/docs/test-run-sebangau.md` lines 60-62, 187.
- Median DEM minus ground -3.4 (Sebangau), -0.03 (Mendahara), +2.16 m (Bengkalis): same file lines 201-203.
- Sebangau open land about 4 m below ground, unexplained: `repeat-dem/AGENTS.md` line 20; `repeat-dem/docs/demnas-literature.md` line 44.
- Fitted tree-cover k 0.10, 0.21, about 0.05; prior 0.8 would give Mendahara RMSE 5.9 m vs 2.6 m raw: test-run-sebangau.md line 207.
- Smoothed RMSE 1.24, 2.32, 2.78 m: same file lines 191-193. 0.25 m target not met: line 210.
- Height-difference error at 1-2 km 1.16, 1.88, 2.55 m RMS, growing to 8 km: same file lines 236-247.
- GEDI vs LiDAR NMAD 4.061 m (Mendahara), 5.016 m (Sugihan-Lumpur); ICESat-2 0.673, 0.625 m: `repeat-dem/runs/checks/demnas_ground_filter.md` lines 26-31. "Too noisy under peat forest to calibrate with": `repeat-dem/AGENTS.md` line 74.
- Pulau Padang 2 m LiDAR flown November 2016; dtm_smooth height-difference error 1.20/1.67/2.08 m at 0.5/1/2 km; 0.3 m head drop cannot be resolved: test-run-sebangau.md lines 362, 394, 398.
- Loader fault, 0.25 m NMAD against exact interpolation, earlier results including the first Pulau Padang comparison made with old loader: benchmark report line 142.
- Kahayan-Sebangau KHG-wide: 22,422 usable points; 2.14 vs 2.19 m; non-forest 1.02 vs 0.91 m; mangrove 3.79 vs 2.39 m; DEMNAS tile covers a diagonal strip, FABDEM and GLO-30 complete: test-run-sebangau.md lines 300-309.

## Correction method (described from the code and templates)

- Steps 1-7: `repeat-dem/demnas_dtm.py` (correct(), masking and despike lines 678-699, coarse_median lines 448-460), `repeat-dem/ground_truth.py` `fit_k_bias` lines 424-470; parameter values from `re-peat/tools/pipeline/templates/dem_correction_deltadtm.yaml` and `dem_correction_demnas.yaml` (aoi_buffer_m 500, chm_min_m 2, chm_max_m 60, min_ground_photons 10, len/res 100 m, t0/t1 2019-2025, exclude classes 80/50, edge_buffer_m 50, max_abs_residual_m 30, validation_fraction 0.3, block_size_m 2000, min_points_per_class 30, bias_from_chm_below_m 2, joint_intercept true, k_bounds 0-1, despike 400 m / 2.5 m, median 300 m, gaussian 150 m, datum pyproj EPSG:4326+3855).
- Strips with at least 2 km overlap; identical result on test grid: benchmark report line 55.
- DeltaDTM 30 m, prior k 0 for all classes; DEMNAS 8 m, prior k 0.8 (10, 95), 0.5 (20), 0.4 (90), 0.2 (30, 40): the two templates.
- Fitted k DeltaDTM: Mendahara tree cover 0.0 (clipped), mangrove 0.003; Kampar-Gaung 0.0 to 0.007: `_khg/15.05-07-10.01_mendahara_batanghari/01_dem/benchmark/04_processed/deltadtm/calibration.json`, `_khg/14.02-04-05.01_kampar_gaung/01_dem/processed/deltadtm/calibration.json`.
- Fitted k DEMNAS Mendahara: tree cover 0.087, mangrove 0.304; shrubland, grassland, cropland, wetland kept prior: `_khg/15.05-07-10.01_mendahara_batanghari/01_dem/benchmark/04_processed/demnas/calibration.json`.

### Docs differ from code (rule 5)

- `re-peat/pipeline.yaml` line 63 and `repeat-dem/README.md` line 72 say DeltaDTM runs "without canopy factor" / "no canopy factor". The code (`ground_truth.py` lines 447-455 with `joint_intercept: true`) still fits k and a per-class intercept for every class with at least 30 vegetated points; the prior of 0 only applies to classes below that. Fitted values were 0 to 0.007, so the practical effect is offsets only. The chapter describes the code.
- `repeat-dem/README.md` line 120 and `re-peat/docs/02-dtm.md` line 28 describe one global bias plus k per class. With the chain templates (`joint_intercept: true`) the code fits an intercept per class; classes without enough vegetated points use the global low-canopy bias. The chapter describes the code.
- The joint fit also requires the canopy height of the vegetated points to span more than 1 m (`np.ptp(chm[veg]) > 1.0`, `ground_truth.py` line 449); no document states this. Not mentioned in the chapter text (detail).
- `repeat-dem/README.md` line 104 says ground points come from SlideRule by default. The chain templates set `ground.source: local` and read the cached ICESat-2 ATL08 file (`{ground_points}`). The chapter does not name the fetch route.
- `repeat-dem/README.md` line 5 says the smoothed results of 1.2 to 2.8 m are "at lidar points in vegetation". `repeat-dem/AGENTS.md` line 18 and `test-run-sebangau.md` lines 187-193 show they were measured at ICESat-2 validation points. The chapter uses ICESat-2.
- The DEMNAS template keeps the prior k 0.8/0.5/0.4/0.2 for classes with fewer than 30 vegetated points, which `repeat-dem/docs/demnas-literature.md` line 51 and `re-peat/docs/02-dtm.md` line 75 call unsupported. Stated in the chapter.

## Benchmark design

- Two KHG, areas 2,012 and 6,347 km², LiDAR cells 3,219,296 and 10,151,210, ICESat-2 points 68,979 and 266,462: benchmark report lines 19-20.
- LiDAR only as reference: benchmark report line 9.
- Comparison at every LiDAR cell, no resampling of the candidate; metrics NMAD, height-difference error at 0.5, 1, 2 km over all cell pairs: benchmark report lines 47-49; `repeat-dem/docs/test-run-sebangau.md` not used here.
- Criterion written before the run, Tier A 0.30 m, Tier B half the real 1 km difference: benchmark report line 53; `repeat-dem/benchmark/sugihan_lumpur.yaml` lines 21-24 ("written before any result (2026-10-25)").
- Processed candidates +0.6 to +1.0 m above the LiDAR: benchmark report line 22.
- Pulau Padang 24 m blocks: median within-block SD 0.0531 m, 5.04% of blocks with range > 1 m, block height difference 1.3541 m RMS at 1 km: `repeat-dem/runs/checks/reference_resolution_padang.csv` rows 4, 9, 12; benchmark report line 24.
- Workflow diagram: `re-peat/reports/dem_benchmark/dem_benchmark_workflow.drawio`.

## Results

- Main results table: benchmark report lines 63-84.
- Figures: `re-peat/reports/dem_benchmark/figures/height_difference_error.png`, `error_maps_mendahara.png`, `error_maps_sugihan_lumpur.png`, `subkhg_units_sugihan_lumpur.png`.
- DEMNAS 2.94 to 1.66 m and 3.46 to 2.19 m; DeltaDTM and KLHK gained little: benchmark report line 88. Error grows with distance, regional tilt: line 90.
- Heavy smoothing 1200/600: DeltaDTM 0.450 m (Mendahara), 0.319 m (Sugihan-Lumpur); flat surface 0.457 and 0.379 m: `repeat-dem/runs/checks/demnas_ground_filter.md` lines 6-20.
- Land-cover table: benchmark report lines 92-104.

## Sub-KHG comparison

- Units and IoU table (LiDAR 30, KLHK as used 28/0.40/0.36/66%, processed 29/0.45/0.41/66%, DeltaDTM 30/0.48/0.47/70%, DEMNAS 30/0.38/0.34/58%): benchmark report lines 116-122.
- Flat surface 30 units, mean IoU 0.399, median 0.367, overlap 0.578: `_khg/16.02.01_sugihan_lumpur/01_dem/benchmark/05_pipeline/delineation_compare.csv`.
- Outlets in this test were primary canals only: `params.outlet_canal_classes` = ["Kanal Primer"] in every `_khg/16.02.01_sugihan_lumpur/01_dem/benchmark/05_pipeline/*/delineate/delineation_report.json`. The benchmark report does not say so.
- Rivers and primary canals always boundaries: benchmark report line 128.
- Groundwater model: 19,433 of 25,391 cells (77%) fixed heads, no skill even on LiDAR: benchmark report lines 13, 138. Model status "in development": workspace `AGENTS.md`.

## Limits

- Benchmark report lines 148-151.

## Decision and coverage

- Chain once per DEM, decided 2026-10-27; variants lidar, deltadtm, demnas; min cover 90%: `re-peat/pipeline.yaml` lines 45-47; `repeat-dem/AGENTS.md` line 13.
- LiDAR used as delivered: `repeat-dem/README.md` line 72.
- Pulau Padang LiDAR left out, 2 m DTM, decision 2026-10-27: `re-peat/tools/pipeline/khgconf.py` line 19.
- Coverage per KHG: `re-peat/sites/khg_dem_inputs.csv` (cover_pct: Kampar-Gaung LiDAR 99.8, AHL Muba25 100, Mendahara 100, Saleh-Sugihan 98.3, Sugihan-Lumpur OKI25 100 and Sugihan-Saleh 1.6; DeltaDTM 97.9-99.9; DEMNAS 99.4-100). 14 KHG in the file.
- Saleh-Sugihan LiDAR valid area inside the KHG polygon: about 1,174 km² of 1,896.5 km² (62%). Computed in this task by masking `_khg/16.02-07.01_saleh_sugihan/01_dem/inputs/lidar_sugihan_saleh_2020_20m.tif` with `_khg/16.02-07.01_saleh_sugihan/00_inputs/khg.gpkg`; agrees with the units area 1,173.4 km² in `_khg/16.02-07.01_saleh_sugihan/02_delineation/lidar/delineation_report.json` and "lidar on 62% of the KHG" in `repeat-dem/docs/test-run-sebangau.md` line 422.
- Recommendations (DeltaDTM interim, carry 0.47-0.64 m error, regression-kriging trend correction, KLHK test away from LiDAR, revisit fixed-head grid): benchmark report lines 156-159. GNSS or levelling for decimetre heights: `repeat-dem/docs/demnas-literature.md` line 54.

### Code discrepancy found (rule 5)

- `repeat-dem/script/prepare_khg_dem.py` line 117 computes `cover_pct` as valid cells over KHG cells inside the clipped raster window, not over the whole KHG. For Saleh-Sugihan this gives 98.3% where the true share is about 62%, so the 90% gate in `re-peat/tools/pipeline/khgconf.py` lines 70-71 let the LiDAR variant run. The coverage table placeholder asks for coverage against the KHG polygon.

## Contradictions between sources

- `re-peat/sites/khg_dem_inputs.csv` (98.3%) against `repeat-dem/docs/test-run-sebangau.md` line 422 (62%) for Saleh-Sugihan LiDAR coverage; see above.
- `re-peat/docs/02-dtm.md` line 60 and line 153 suggest a coarser `--res` for tests; `repeat-dem/AGENTS.md` line 5 forbids it. Not used in the chapter.
- The 2026-10-08 runs at Mendahara and Bengkalis were made on DEMs averaged 4x to 30 m (`test-run-sebangau.md` line 177); the Mendahara 8 m rerun gave the same smoothed RMSE (2.32 m, line 354). The chapter quotes the 30 m figures as in the summary table.

## References cited

- Hawker, L. et al. (2022). A 30 m global map of elevation with forests and buildings removed (FABDEM). Environmental Research Letters 17, 024016. doi:10.1088/1748-9326/ac4d4f. Listed in `re-peat/docs/Peatland Rewetting Water-Sharing Model — Methodology.md` line 614; DOI from the benchmark report line 33.
- Julzarika, A. and Harintaka (2019). Indonesian DEMNAS: DSM or DTM? 2019 IEEE AGERS, 31-36. doi:10.1109/AGERS48446.2019.9034351. Cited in `repeat-dem/docs/demnas-literature.md` lines 9, 27; the full reference is given only in `repeat-dem/docs/test-run-sebangau.md` line 222 (outside the allowed list; flag for the reference check).
- Pronk et al. (2024). DeltaDTM v1.1. doi:10.1038/s41597-024-03091-9; data doi:10.4121/21997565 (4TU, CC BY 4.0). Cited in `re-peat/docs/14-data-catalog.md` line 54 (read through Europe PMC, PMC10917791); DOI from the benchmark report line 30. The workspace gives no title or journal, so none is stated here.
- Ritzema, H., Limin, S., Kusin, K., Jauhiainen, J., Wösten, H. (2014). Canal blocking strategies for hydrological restoration of degraded tropical peatlands in Central Kalimantan, Indonesia. Catena 114, 11-20. https://luk.tsipil.ugm.ac.id/rawa/PLG/1-s2.0-S0341816213002531-main.pdf. From `re-peat/docs/17-subkhg-delineation-background.md` line 128.
- Susetyo, D.B., Lumban-Gaol, Y.A. and Sofian, I. (2018). Prototype of national digital elevation model in Indonesia. ISPRS Archives XLII-4, 609-613. doi:10.5194/isprs-archives-XLII-4-609-2018. From `repeat-dem/docs/demnas-literature.md` line 58.
- Susetyo, D.B. (2023). Vertical accuracy assessment of various open-source DEM data: DEMNAS, SRTM-1, and ASTER GDEM. Geodesy and Cartography 49(4), 209-215. doi:10.3846/gac.2023.18168. From `repeat-dem/docs/demnas-literature.md` line 59.

- Diagram: the report embeds a reader version drawn in draw.io, re-peat/reports/project_report/diagrams/*_report.drawio (plain labels; same boxes and edges as the module original).
