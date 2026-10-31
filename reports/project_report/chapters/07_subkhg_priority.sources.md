# Sources for chapter 7 (sub-KHG prioritisation)

Abbreviations: SL = `_khg/16.02.01_sugihan_lumpur/04_prioritisation/`, PR = `repeat-prioritisation/src/repeat_prioritisation/`, SITE = `re-peat/sites/16.02.01_sugihan_lumpur/`.

## Numbers and claims

- Purpose, need score, rank, tertile classes, hand-over to the interventions module: `repeat-prioritisation/docs/subkhg-method.md` sections 1-2; `PR/subkhg/prioritise.py` docstring.
- Diagram: existing `repeat-prioritisation/docs/figures/subkhg_method.drawio` (reused; it names module "repeat-pump" and output paths, which the brief keeps out of prose; the coordinator may want to relabel it).
- One chain per DEM (LiDAR where it covers, corrected DeltaDTM and DEMNAS): AGENTS.md "DEM variants"; SITE `khg.yaml` (`dems`); SITE `lidar/subkhg.yaml`, `deltadtm/subkhg.yaml`, `demnas/subkhg.yaml` (units, DTM and neraca table differ per DEM).
- LiDAR variant uses the KLHK 25 m DEM `lidar_klhk/dem_25m/DEM25M/OKI25.tif`: SITE `khg.yaml` `dems.lidar.sources`; DeltaDTM and DEMNAS use `01_dem/benchmark/04_processed/<dem>/dtm_smooth.tif`: SITE `deltadtm/subkhg.yaml`, `demnas/subkhg.yaml` `rasters.dtm`.
- Unit IDs not shared between variants: each variant reads its own `02_delineation/<dem>/subkhg_units.gpkg` (SITE `<dem>/subkhg.yaml` `units.path`); unit counts differ (29/29/27).
- Fire and canals with the national code, per km² of peat: `PR/subkhg/national_layers.py` docstring and `fire_and_canals`.
- 30 m grid: `PR/subkhg/run.py` PRESET `grid_res_m`.
- Inputs table: `repeat-prioritisation/docs/subkhg-method.md` section 3; SITE `lidar/subkhg.yaml` (vectors, rasters, tma period 2026-04-01 to 2026-10-15, `sources.ndmi.res_m` 20); `re-peat/sites/data_catalog.csv` rows for burnt area, VIIRS, KLH hotspots, canal layer.
- Baseline 2015-2022, validation 2023 (El Niño): SITE `lidar/subkhg.yaml` `years`; comment in SITE `subkhg.yaml`.
- Weights (2, 1, 1, 1, 1, 0.5/0.3/0.2, 1.5, 1.5, 1, 1, 1/1, stakes 2 and 1; lift 1 in feasibility): SL `lidar/laporan.json` `weights`; groups from `PR/subkhg/prioritise.py` `NEED_INDICATORS` (f_reach, f_water_dist, i_forest moved to group u; i_forest direction -1) and `PR/common/scoring.py` `INDICATOR_DEFAULTS` (i_peat_depth, i_protected group i).
- Single canal density weight 0 when classes exist: `PR/subkhg/prioritise.py` `score_need` lines 131-134.
- Reach 200 m, 60 m on burned land; permanent water >= 10 months; forest = WorldCover 10 and 95: `PR/common/pipeline.py` DEFAULTS `params` (`l_inf_m`, `l_inf_burnt_m`, `water_min_months`, `forest_classes`); `PR/common/indicators.py` lines 192-215.
- Block metric: spacing = 0.4 / median slope along primary+secondary canals, clip 50-2,000 m, needed = ceil(L / spacing), existing = blocks inside unit, additional = max(0, needed - existing), gap = 1 - min(1, existing/needed): `PR/common/indicators.py` lines 234-270; `PR/common/pipeline.py` `ipg_dA_m` 0.4, `ipg_js_min_m` 50, `ipg_js_max_m` 2000; SITE `lidar/subkhg.yaml` `ipg_canal_classes` (Kanal Primer, Kanal Sekunder). Origin in the 2021 Kahayan-Sebangau study: `re-peat/docs/03-prioritisation.md` "Metrik IPG".
- 0.4 m from PP 57/2016: `re-peat/docs/05-parameters.md` (target water-table depth row).
- Rain indicators weight 0, 4-25 km constant inside a KHG: `PR/subkhg/prioritise.py` comment in `NEED_INDICATORS`.
- Neraca balance only when stable, rank-sum slot only, never in need score: `PR/common/pipeline.py` `gate_balance`; SITE `lidar/subkhg.yaml` `extra_indicators` comment and `scoring.ranksum_columns`.
- SiTMAT minimum units min(20, max(3, n/2)): `PR/common/scoring.py` `normalise_scoped`.
- Scaling within the KHG, need = 0.8 U + 0.2 S, tertile classes, rank-sum alongside: `PR/subkhg/run.py` PRESET (`alpha_urgency` 0.8, `normalise_scope` khg); `PR/subkhg/prioritise.py` `score_need`, `ranksum`.
- Earlier rank-sum indicators: `repeat-prioritisation/docs/prior_method.md`; `PR/subkhg/prioritise.py` `RANKSUM_INDICATORS`.
- Rank-sum indicators used (4 for LiDAR and DeltaDTM, 5 for DEMNAS): SL `<dem>/laporan.json` `ranksum.used`.
- Deficit months off because order follows land cover: SITE `subkhg.yaml` comment on `scoring`.
- Correlation flag 0.8, 300 draws, Dirichlet concentration 20, stable = share >= 0.8 or <= 0.2: `PR/common/pipeline.py` DEFAULTS `scoring`; `PR/common/scoring.py` `sensitivity`.
- KHG area about 6,347 km²: SL `deltadtm/unit_prioritas.csv` and `demnas/unit_prioritas.csv` sum of `area_km2` (6,347.2); LiDAR 6,345.6.
- National rank 31: `re-peat/reports/national_profile/operational/profile.csv` KHG.16.02.01 `peringkat`.
- Run date 28 October 2026: file times of SL `<dem>/laporan.json` (2026-10-28 15:38 to 15:45).
- Units per DEM 29/29/27: SL `<dem>/laporan.json` `n_units`.
- Unit area min, max, median: SL `<dem>/unit_prioritas.csv` `area_km2`.
- Class units and areas: SL `<dem>/ringkasan_kelas.csv` (`unit`, `luas_km2`).
- Units with a SiTMAT station 11/10/12: SL `<dem>/unit_prioritas.csv` `n_tma_stations` > 0.
- Balance stable 0/0/27: SL `<dem>/unit_prioritas.csv` `balance_stable_ok`; SL `<dem>/laporan.json` `indicator_coverage.u_wb_mean` (0, 0, 1).
- Spearman need vs rank-sum 0.76/0.68/0.69, top overlap 0.667 of 6, 0.833 of 6, 0.6 of 5: SL `<dem>/laporan.json` `ranking_agreement`.
- Stable class 62%/62%/74%, median rank SD 4.16/4.23/3.97: SL `<dem>/laporan.json` `sensitivity`.
- 14 scored indicators (15 in `indicators_used` minus `f_lift`, which is feasibility): SL `<dem>/laporan.json` `indicators_used`.
- Correlated pairs (0.848, 0.879, 0.868; peat depth-lift -0.804 LiDAR only): SL `<dem>/laporan.json` `correlated_pairs`.
- Median canal slope 0.000277/0.000596/0.00229; units at 2,000 m cap 4/0/0: SL `<dem>/unit_prioritas.csv` `kemiringan_kanal` (median; count of 0.4/slope >= 2000). Spacing 1,446/671/175 m = 0.4 / median slope (arithmetic).
- Blocks needed/existing/additional 3,634/2,847/1,335; 6,237/2,847/3,631; 25,580/2,847/22,733: SL `<dem>/kebutuhan_sekat.csv` summed over classes (same totals from `unit_prioritas.csv` `n_sekat_perlu`, `n_sekat_ada`, `sekat_tambahan`).
- Additional blocks in high-need units 526/1,514/4,988: SL `<dem>/kebutuhan_sekat.csv`, row "Kebutuhan intervensi: tinggi".
- Ratios 7 times (25,580/3,634) and 8 times (0.00229/0.000277): arithmetic on the above.
- 787 = 3,634 - 2,847: arithmetic.
- KHG deficit 290 mm, 1 June to 9 October 2026, 51 stations, ERA5, Sy 0.15, range 284.7-295.7 for Sy 0.10-0.20: `_khg/16.02.01_sugihan_lumpur/03_neraca/runs/deficit/neraca_khg.csv`; same value in SL `<dem>/subkhg_priority.csv` `deficit_mm` 290.238.
- Four KHG with the full chain on three DEMs: `_khg/pipeline_status.csv`; AGENTS.md (2026-10-28 status).
- Validation 2023 per DEM (positives 3/3/3 and 17/17/15; AUC values): SL `<dem>/laporan.json` `validation.v_burned_frac` and `v_hotspot`, keys `skor_risiko` (need score), `skor_urgensi` (need part), `hanya_riwayat_kebakaran` (fire history alone).
- Validation design (indicators to 2022, this year's hotspots out, positive = burned share >= 0.05): `PR/common/scoring.py` `validate`; `re-peat/reports/subkhg_validation.md` header.
- Earlier unit set (30 units) bootstrap values: `re-peat/reports/subkhg_validation.md` (Sugihan-Lumpur 2019: need 0.37 (0.06 to 0.62), fire history 0.64 (0.39 to 0.82); Kampar-Gaung 2019: need 0.61 (0.35 to 0.80), fire history 0.38 (0.02 to 0.68)).
- Weights need team judgement (AHP), validation as check: `repeat-prioritisation/docs/subkhg-method.md` section 8.
- Peat depth valid on 74.7% of the KHG: SITE `khg.yaml` `peat_depth.valid_share` 0.747.
- Partial-coverage peat depth must not drive the ranking: AGENTS.md data rules.
- 30-unit cap, no hydrological basis: `repeat-prioritisation/docs/reports/Sub KHG prioritisation improvements.md` first section.
- Burnt-area source not recorded: `re-peat/sites/data_catalog.csv` row `burnt_area_2015_2026_Indonesia.gpkg` (source column empty).
- SiTMAT concession bias, one season: `repeat-prioritisation/docs/subkhg-method.md` section 9; `Sub KHG prioritisation improvements.md` (1,159 of 1,284 stations concession).
- Canal layer OSM-derived, no flow direction: `re-peat/sites/data_catalog.csv` row `kanal_osgm_khg_existing_Indonesia.gpkg`.
- Forest share counts plantations: `re-peat/sites/16.02.01_sugihan_lumpur/README.md` finding 4.
- Classes cut over the whole run: `PR/subkhg/prioritise.py` line `q1, q2 = out["skor_risiko"].quantile(...)` (not grouped by KHG).

## Discrepancies between docs and code, and between sources (code followed)

1. `re-peat/docs/03-prioritisation.md` (written for the earlier `prioritas_khg`) gives risk = 0.6 urgency + 0.4 impact, feasibility tertile classes, reach in feasibility with weight 2, forest in impact, MODIS burned area, baseline 2016-2022. The sub-KHG code ranks by need = 0.8 U + 0.2 S (`subkhg/run.py`), puts reach (1.5), distance to water (1) and forest (reversed) in need (`prioritise.py`), takes fire from the burnt-area polygons on peat (`national_layers.py`), baseline 2015-2022 (site configs). Chapter follows the code.
2. Peat depth: the improvements report recommends weight 0 and AGENTS.md says partial-coverage depth must not drive the ranking; the code (`INDICATOR_DEFAULTS`) and the runs (`laporan.json` `weights`) give it weight 2 in stakes. The national-layers config of the site sets `i_peat_depth` 0, but that config only feeds the fire and canal columns. Chapter reports weight 2 and flags the conflict in the limits.
3. `subkhg-method.md` names the sensitivity column `p_prioritas1`; the sub-KHG code writes `p_kebutuhan_tinggi` (`prioritise.py`).
4. `subkhg-method.md` section 8 (30 units, classes 10/10/10, Spearman 0.58, 73% stable) and the site runbook (28 units, Spearman 0.15, 2,861 existing blocks) describe older runs (`04_prioritisation/national_layers/` and 2026-10-16). The per-DEM runs of 2026-10-28 give 29/29/27 units and 2,847 existing blocks. Chapter uses the per-DEM runs; `subkhg_validation.md` is cited only as "an earlier unit set".
5. `subkhg-method.md` says Kampar-Gaung 2019 need-score Spearman 0.61 (0.34 to 0.80); `subkhg_validation.md` gives (0.35 to 0.80). Chapter uses the validation report.
6. `subkhg-method.md` section 9 says only Sugihan-Lumpur among the selected KHG has units; `pipeline_status.csv` now shows Saleh-Sugihan and Mendahara-Batanghari done as well.
7. README of `subkhg/` (cited in the improvements report) says tertiles are within each KHG; the code cuts them over the whole run. Same result for one-KHG runs.
8. Existing blocks counted are all realised blocks inside a unit (`indicators.py` lines 258-262), while blocks needed counts only primary and secondary canals; the docs do not state this asymmetry.
9. `kebutuhan_sekat.csv` "sekat_tambahan" is the sum of per-unit max(0, needed - existing), not needed minus existing (code, `indicators.py` line 269).
10. The improvements report says Sentinel-2 runs at 60 m and validation is empty; the current configs set 20 m and validation 2023. That report describes an older state.

## References cited

- Urzainki, I., Palviainen, M., Hökkä, H., Persch, S., Chatellier, J., et al. (2023). A process-based model for quantifying the effects of canal blocking on water table and CO2 emissions in tropical peatlands. Biogeosciences 20, 2099-2116. https://doi.org/10.5194/bg-20-2099-2023. Cited for: block effects on the water table reach about 600 m. As listed in `repeat-pump/docs/references.md` ("Used for the ~600 m reach of block effects") and `re-peat/docs/17-subkhg-delineation-background.md` (references).

Regulations named (not cited as works): PP 57/2016, 0.4 m water-table criterion, as given in `re-peat/docs/05-parameters.md`.

## Added after review

- 30-unit cap and automatic minimum area 116.1 km² (LiDAR variant): `_khg/16.02.01_sugihan_lumpur/02_delineation/lidar/delineation_report.json` (`target_count` [6, 30], `min_area_km2` 116.1, `min_area_setting` auto); `repeat-delineation/src/repeat_delineation/delineate.py` line 39-40.
- Existing blocks counted on all canal classes, needed on primary and secondary only: `PR/common/indicators.py` lines 241-262.
- Validation wording (five of six comparisons fire history >= need score; DeltaDTM burned share 0.885 vs 0.872): SL `<dem>/laporan.json` `validation`.

- Diagram: the report embeds a reader version drawn in draw.io, re-peat/reports/project_report/diagrams/*_report.drawio (plain labels; same boxes and edges as the module original).
