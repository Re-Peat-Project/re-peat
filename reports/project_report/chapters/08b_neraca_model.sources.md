# Sources for 08b_neraca_model.md (sections 8.6-8.14)

Abbreviations used below:
- GMR = `repeat-neraca/docs/groundwater-model-report.md`
- REV = `repeat-neraca/research_notes/groundwater_models_review.md`
- PAR = `repeat-neraca/research_notes/peat_parameters_sumatra_kalimantan.md`
- BURN = `repeat-neraca/research_notes/burned_peat_hydrology.md`
- TPH = `repeat-neraca/docs/tropical-peat-hydraulic-parameters.md`
- REFS = `repeat-neraca/docs/references.md`
- MSR = `repeat-neraca/docs/reports/model_station_runs.md`
- SWEEP = `repeat-neraca/docs/reports/model_sweep_14.10.03_200m.md`
- FIN = `repeat-neraca/docs/reports/field_inputs_14.10.03.md`
- SITES = `repeat-neraca/docs/reports/station_sites.md`
- SC12 = `repeat-neraca/docs/reports/scenarios_15.05-07-10.01_canals1.2.md`
- SC06 = `repeat-neraca/docs/reports/scenarios_15.05-07-10.01.md`
- PARK = `re-peat/docs/12-parked.md`
- SL = `_khg/16.02.01_sugihan_lumpur/03_neraca/lidar/runs/model/`
- KG = `_khg/14.02-04-05.01_kampar_gaung/03_neraca/lidar/runs/model/`
- MB = `_khg/15.05-07-10.01_mendahara_batanghari/03_neraca/lidar/runs/model/`
- Code: `repeat-neraca/src/repeat_neraca/model.py` (MODEL), `groundwater/simulate.py` (SIM), `groundwater/solver.py` (SOLVER), `groundwater/fieldcheck.py` (FC), `repeat-neraca/scripts/compare_scenarios.py` (CMP), `repeat-neraca/scripts/summarise_model_runs.py` (SUM), `repeat-neraca/src/repeat_neraca/parameters.yaml` (REG)

Numbers from run files were read with `.venv/Scripts/python.exe` on 2026-10-28.

## 8.6 Why a groundwater model

- The adopted method has two outputs (climatic balance per sub-KHG, station deficit per KHG); neither answers a what-if; the balance has no storage, canal level or blocks; the deficit has no spatial form: GMR section 1.1 (lines 49-56).
- What a what-if needs (state, canal mechanism, intervention); the 2D groundwater-flow equation provides all three; every model that simulated blocking has this structure: GMR section 1.2 (lines 58-60).
- Status: in development; runs for any KHG from its code; has passed the supply check where it can be made, not the level and dynamics checks outside managed land: GMR line 3.

## 8.7 Review

- Table rows (form, canal and block, pump, skill, licence): GMR table section 2.1 (lines 80-92) and REV section 1 table.
- Urzainki 2023 needs canal bed and width: REV section 5, option B ("the network needs canal bed and width").
- MIKE SHE data (3 peat layers, tide boundary, ~113,000 cells), 15 wells RMSE 0.05-0.09 m, NSE 0.36-0.87: GMR line 85; REV section 1.
- SIMGRO R² 0.74: GMR line 86. Suryadi NSE 0.73-0.95, 30-day calibration, block heights 0.2-0.6 m, spacing 200-400 m: GMR line 87.
- DigiBog 2.5D, 1 m, 0.2 km², GPL-3.0: GMR line 88. PEATCLSM-Trop ditch 0.68 m, spacing 31.4 m, R 0.68: GMR line 89. DRAINMOD: GMR line 90; REV row ("licence not confirmed"). MPeat2D: GMR line 92.
- SWAP (Taufik et al. 2019): canal level 130 cm below ground in the dry season, 50 cm wet; drainage resistance; water table deeper than 85 cm 1.9% natural, 34% canal drainage: REFS section 2, Taufik row. SWAP is not in the GMR table; it is listed in REV section 2 point 1 ("SWAP in Taufik 2019") and in REFS.
- MONALAGA: GMR line 94; REV text below table (product page lists BRGM Tebing Tinggi 2020; report not online).
- "Equation not the fault", the two inputs: GMR section 2.2 lines 98-100.
- Boreal T 0.59 m²/day at the surface: GMR line 99; TPH table (0.59). Urzainki 2023 surface T 50 or 500: GMR line 99. Jaenicke T 30 m²/d top metre: GMR line 99. "100 to 1,000 times": GMR line 11.
- 100 m grid, 500 m too coarse: GMR line 101. No tropical study models a pump: GMR line 106.
- Block effect sizes (9 cm at 100 m, under 5 cm by ~300 m; 1.44 / 1.57 cm; 100-400 m upstream): GMR lines 102-105; REV section 2 point 3 (Sutikno et al. 2023 as source of the Tebing Tinggi field reports).
- MODFLOW deferred 2026-10-28, reasons (layers 8-10, binary for the plugin, same open questions), fallback role: GMR line 465; PARK "Neraca air" table row 1; GMR D5 alternatives (line 145, "fallback if a canal network is too much to write").

## 8.8 The model

- Equation and scheme (implicit Euler, Picard, ponded water removed): SOLVER docstring lines 1-10; SIM docstring. Code checked: matches the docs.
- Runoff saturation-excess (Katimon et al. 2013): BURN evidence table and "What this means" point 1.
- Grid 100 m or 200 m: GMR FAQ line 26; run names. Code default grid is 100 m (MODEL `--res` default 100.0).
- Shared solver with the interventions module: GMR D3 (line 143); SOLVER docstring line 2.
- Start saturated at a wet-season start; 2026 runs start 2025-11-01: MODEL `--h0` default 0.0 and `--start` help text; GMR line 324.
- Tropical sets: SOLVER `TROPICAL_SETS` (s1 0.6, s2 0.5, t1 50 or 500, t2 2.5). "factor e every 0.4 m" = 1/t2, our arithmetic; also GMR line 465 ("falling by a factor e every 0.4 m").
- Sy 0.6 fits intact forest; drained 0.1-0.3; Ismail 0.3 surface, 0.1 at -1.5 m; Kurnianto 0.10-0.15: GMR line 124; PAR "What this means" point 1. Cobb and Harvey 0.29: TPH first table; GMR D6 line 146.
- Drained set: `Sy = 0.3 exp(0.73 z)`, the team's fit through Ismail's two values, not the authors' equation: SOLVER comment above `drained-ismail-*`; PAR "Use in the model". T as Urzainki large: SOLVER `drained-ismail-large` (0.3, 0.73, 500, 2.5).
- Boreal table kept as the known failure; nothing fitted: GMR D6.
- Peat-depth fallback order and 8 m for the deepest class: GMR D15 (line 155); MODEL `BBSDLP_DEPTH_M` (D6 = 8.0) and `depth_fallback`.
- T below 2 m small whatever the depth (exp(-2.5 d) < 0.007 for d > 2 m): GMR D10 (line 150).
- Edge held 0.3 m below surface: REG `river_stage_below_edge` default 0.3; GMR limitations line 452 ("a river rule").
- Canals per class, 1.2 m base (REG `canal_drawdown` default 1.2), alternatives 0.6 and 0.4 in runs; a class can be left unfixed: MODEL `parse_drawdown` ("none"), SIM `Boundary.heads`.
- Managed land: licences PBPH and oil palm (MODEL `MANAGED_LICENCES = ("PBPH", "Perkebunan Kelapa Sawit")`), 2025 licence layer (MODEL `LICENCES`); canals fixed at the target and managed cells topped up daily; supply = storage difference: SIM docstring and `run` (held cells). Target 0.4 m PP 57/2016: MODEL `REGULATORY_TARGET_M`. Station-median alternative: MODEL `managed_targets` (`stations-loo`).
- Blocks: reach depth below the land fixed on canal cells; higher level kept where a managed and a block level meet; overlapping reaches, shallower wins: SIM `Boundary.heads` (`canal_override`), MODEL `block_levels`. GMR D17.
- Pumped land held at 0.4 m: MODEL `--supply-target` default `REGULATORY_TARGET_M`; MODEL `supply_areas` keeps interventions whose `intervention` contains "water"; where both, shallower target (`np.fmin`) in MODEL main.
- No ET below the peat base: SIM `run` (`peat_base`); GMR D16.
- Burned peat (no infiltration cap; Setiawan 2020; Konecny 2016 lower surface; Hirano 2015 lower ET): BURN short answer, evidence table and "What this means".
- Forcing: CHIRPS and MOD16 KHG means per dekad, spread evenly, fetched from Earth Engine: MODEL `forcing` and docstring; GMR D8. MOD16 without gap filling for 2026 (gap-filled ends Dec 2025): GMR line 273.
- DTM choice: MODEL docstring; GMR D9. Input table per run: MODEL writes `inputs.csv`; GMR D15.
- Outputs: MODEL lines 386-402 (series, season tifs, unit table) and `unit_table`; season default 06-01 to 09-30 (MODEL `--season`), 122 days (SC12 header). Season days map covers open cells only: MODEL line 398.
- "Still needs rewetting" (more than 50% of open land deeper than 40 cm for more than half the season): CMP `STILL_DRY_SHARE = 0.5` and docstring; SC12 header.

## 8.9 Design decisions

- D1-D17: GMR section 3 table (lines 139-157). Evidence column: D4 "74 of 74": GMR section 4.4; D9 DEMNAS 1.86 m: FIN DTM table; D14 Kampar deficit 7 mm: MSR; D16 642 cm and peat ~1.3 m: GMR section 7 point 6 and MSR.

## 8.10 How the model is judged

- Constant and distance predictions, distance fitted in-sample: FC docstring; GMR line 171.
- Field check: Spearman >= 0.3 (FC `MIN_SPEARMAN`), above distance prediction, RMSE below constant: FC `score`.
- Station timing check: median per-station r >= 0.5 (FC `MIN_TEMPORAL_R`); station needs >= 30 days (FC `score_stations`); level checks need >= 8 points (FC `score`, `testable = n >= 8`).
- Supply check: factor 2 (FC `SUPPLY_RATIO = (0.5, 2.0)`), plus 50 mm (FC `SUPPLY_ABS_MM`, comment "added 2026-10-28 after Kampar-Gaung"); GMR D14 (amended after the Kampar-Gaung runs at the owner's request). Applied only in runs with a managed target: MODEL lines 471-480.
- Kampar-Gaung tropical-large 0.4 supply 42 mm vs 7 mm: passes only through the 50 mm floor (ratio 6): MSR; arithmetic ours.
- "Not testable" and the pass rule: FC `gate_pass`; AGENTS.md "Neraca air: two methods".
- Stations on canal/edge cells and in held land excluded: MODEL lines 455-458 (flags `on_fixed_cell`, `in_managed_land`); FC `score_stations`.

## 8.11 Test sites and evidence

- Tebing Tinggi: 1,385 points, 1,132 on peat, 329 zeros, 91% (team joperi) and 91% mangrove, ponding column 0: FIN "Zero water tables". 528 scored at 200 m, 584 at 100 m: SWEEP; GMR section 6.3. DeltaDTM r 0.91, median -0.37 m: FIN DTM table.
- Six configurations, Spearman 0.01-0.05, bias -48 to -71 cm, RMSE 67-81, constant RMSE 40 cm: SWEEP runs table. 100 m Spearman -0.01: GMR section 6.3 table.
- Field data: distance 0.00, thickness 0.02, 76% (258 points), 25 teams, 0.13: SWEEP "The field data"; GMR section 6.5. Interpretation: GMR section 7 point 1.
- Station ranking: 1,181 stations, 178 KHG, good thresholds 120 / 45 days; table values (78/0/11.0/7.0; 51/0/3.1/11.0; 12/9/12.7/1.0); only Mendahara meets 5 + 3: SITES.
- Sugihan-Lumpur 1.2 m: 18 flagged, 33 scored: SL `tropical-large_p1.2_s1.2_t1.2_e0.3_200m/station_scores.csv` (flag counts) and `station_scores.json` (median r 0.87, KHG mean r 0.94). Drawdown 12 / 126 cm, KHG mean at end September 122 cm: GMR section 6.4; MSR. Stations about 42 cm: station_scores.json `obs_khg_mean_cm` 42.3. P - ET June to September -376 mm: GMR section 7 point 4.
- Sugihan-Lumpur 0.4 m: simulated 36.5 cm, observed 42.3 cm: SL `tropical-large_p0.4_s0.4_t0.4_e0.3_200m/station_scores.json`; drawdown 72 cm: MSR. Canal supply 14 mm August, 25 mm September: GMR line 311.
- Station runs table: MSR rows (Spearman, distance, bias, RMSE, constant, median r, drawdown); confirmed for the Sugihan, Kampar and Mendahara runs against each run's `station_scores.json`.
- 642 cm below the peat (~1.3 m): MSR; peat median 1.3 m in SL `tropical-large_p1.2_s1.2_t1.2_e0.3_200m/model_report.md` line 3; GMR section 7 point 6.
- ET stress at Sugihan with canals 0.4 m changed nothing; threshold -0.70 m reached at end of September: GMR line 348; SL `..._etnatural/station_scores.json` (median r 0.84, sim mean 37.6 cm vs 36.5 cm without).
- Mendahara by kind (concession 9, 8 in licences, 37/28 cm, 6/52 cm; community 6, 29/95, 63/38): MB `tropical-large_p1.2_s1.2_t1.2_mp0.4_s0.4_t0.4_e0.3_100m/station_scores.json` `by_kind` (community: 28.7 / 94.6 cm, drawdown 63.4 / 37.5 cm; concession: 37.4 / 27.8 cm, 5.6 / 51.8 cm, in_managed_land 8); GMR section 6.6 table.
- Managed runs table: MSR rows with a managed target; GMR section 6.7 table. Managed shares 77%, 44%, 22%: GMR section 6.7 table; Mendahara 22.1% in MB `tropical-large_p1.2_s1.2_t1.2_mt0.4_e0.3_100m_pb_dbbsdlp/inputs.csv`. Supply values confirmed in each run's `station_scores.json` (`model_managed_supply_mm`: 244, 233, 324, 42, 41, 104, 194, 209, 250, 181).
- Targets 0.43-0.44 m at Sugihan: GMR section 6.7. Every station off a canal cell at Sugihan and Kampar lies in a licence: GMR section 7 point 7.
- Community stations under the managed runs: 95 / 38 cm (tropical large), 165 / 99 cm (Ismail Sy), median r 0.38: MB `..._mt0.4_e0.3_100m_pb_dbbsdlp/station_scores.json` and `drained-ismail-large_p1.2_..._mt0.4_e0.3_100m_pb_dbbsdlp/station_scores.json` (165.4 / 98.5). 0.6 m canals: 66 / 23 cm; 7 stations 37 vs 36 cm: MB `tropical-large_p0.6_..._mt0.4_e0.3_100m_pb_dbbsdlp/station_scores.json` (66.3 / 22.6; obs 36.1, sim 37.5). Stations start late July 2026: GMR line 367.
- Season ranges table: each run's `model_units.csv` (Sugihan `SL/tropical-large_p1.2_s1.2_t1.2_mt0.4_e0.3_200m_pb_dbbsdlp`, Kampar `KG/...same`, Mendahara `MB/tropical-large_p0.6_s0.6_t0.6_mt0.4_e0.3_100m_pb_dbbsdlp`), columns `open_mean_depth_cm`, `open_days_deeper_40cm`, `managed_supply_mm`; units 30, 28, 29.
- Dry and wet year: SL `year2019_dry` and `year2022_wet`, `model_series.csv` June-September (P - ET -285 / +602 mm; managed supply 163 mm, 480 million m³ / 1 mm; unmanaged depth end of September 79 cm, share 0.995 / 9 cm, 0.07); S02 `open_days_deeper_40cm` 95.75 / 48.3 in `model_units.csv`; years chosen from the balance calendar, 6 and 0 deficit months: GMR section 6.8.

## 8.12 Scenarios

- 160 reaches, 29% of the KHG held at 0.4 m: SC12 scenario headers. 8 units marked for water: the `interventions` layer of `_khg/15.05-07-10.01_mendahara_batanghari/05_pump/lidar/mendahara_batanghari.gpkg` has 8 rows with `intervention = block_water`, the only value containing "water" (MODEL `supply_areas` filter); SC12 second table shows 8 units with 0 km² open land (S01, S02, S03, S04, S09, S26, S27, S28).
- Interventions module assumes unblocked canals 1.0 m below the land: `_khg/15.05-07-10.01_mendahara_batanghari/05_pump/lidar/proposed_defaults.yaml` line 32 (`balance_drawdown_m: 1.0`); GMR line 405. Reach median 0.59 m: `depth_m` of layer `sekat_reach` (median 0.587, 160 reaches), read from the same GeoPackage.
- Scenario table: area-weighted days 60.9 / 60.2 / 58.0 and open land 1,207.1 / 1,207.1 / 822.9 km² recomputed from the three MB `model_units.csv` files (`open_km2` × `open_days_deeper_40cm`, units with open land); supply 58.5 / 58.3 / 108.7 million m³ and units 12 / 12 / 9: SC12. The 58.0 covers less open land than the other two.
- Mean change -0.7 days over open cells: SC12 first scenario.
- Distance-band table: SC12 and SC06, first scenario tables.
- Literature comparison: GMR line 424; REV section 2 point 3.
- Units still needing rewetting: baseline "yes" S01, S02, S07, S08, S09, S10, S14, S16, S19, S21, S24, S25; pump scenario "yes" S07, S08, S10, S14, S16, S19, S21, S24, S25: SC12 unit tables. 0.6 m baseline: 8 to 7, S09 held: SC06 unit tables and header. Pumping 105.1 vs 54.6 million m³, blocks -13.6 days within 150 m: SC06.

## 8.13 Limitations

- Canal levels unknown and controlling: GMR FAQ point 2. Community land too deep (95 vs 29 cm, our difference 66 cm): MSR. Sy limitation: GMR section 8 item 2. Fixed canal per class, no network, no tides, edge river rule: GMR Limitations (lines 448-453). KHG-mean forcing: GMR Limitations.
- Mendahara peat depth 36.4% from KHG median 3.9 m: MB `tropical-large_p1.2_s1.2_t1.2_mt0.4_e0.3_100m_pb_dbbsdlp/inputs.csv`. Tebing Tinggi depth r 0.10: FIN. Open DEM errors of dome relief: GMR D2 and FAQ point 4.
- No before/after measurements: GMR section 7 point 9.
- Decisions needed: GMR section 8 items 0-3. Tebing Tinggi stations 5 concession at about 20 cm, 3 community at about 150 cm: GMR section 8 item 1; FIN station table.

## 8.14 FAQ

- Adapted from GMR "Questions and answers" (lines 25-45). Run time 6 to 35 minutes: GMR line 38. Median fall 1 to 12 cm: GMR summary line 16. 233-324 vs 290 mm: GMR line 17. Distance bands and 50 million m³: SC12. Setiawan 2020: BURN.

## Discrepancies between docs, code and run files (rule 5)

1. Managed target default. AGENTS.md says `--managed-target` has a default of 0.4 m. In MODEL the option defaults to None (no managed land held); 0.4 m (`REGULATORY_TARGET_M`) is the value given in every reported run, the default of `--supply-target`, and the fallback of the station-median mode. The chapter describes the runs.
2. Default peat table and DEM. MODEL defaults are `tropical-small` and `deltadtm`; every 2026 station run in the chapter uses `tropical-large` (or `drained-ismail-large`) and LiDAR. The chapter describes the runs, not the defaults.
3. Stale gate results in run files. `station_scores.json` of `SL/tropical-large_p1.2_s1.2_t1.2_mtloo_e0.3_200m_pb_dbbsdlp`, `SL/drained-ismail-large_p1.2_s1.2_t1.2_mt0.4_e0.3_200m_pb_dbbsdlp`, `KG/tropical-large_p1.2_s1.2_t1.2_mtloo_e0.3_200m_pb_dbbsdlp` and `KG/drained-ismail-large_p1.2_s1.2_t1.2_mt0.4_e0.3_200m_pb_dbbsdlp` show level checks as False with 0 stations scored and a supply check labelled "within x2" without the 50 mm floor (gate False). They were written by older gate code. MSR (from SUM, which re-gates with `FC.supply_ok` and treats checks without stations as not testable) and GMR give pass (supply only) for the Sugihan runs and for Kampar tropical-large; the chapter follows the current code.
4. Sugihan 0.4 m bias. GMR section 6.4 table and MSR give -6 cm; GMR section 7 point 4 says -4 cm. The run file gives 36.5 vs 42.3 cm (about -6). The chapter uses the file.
5. Season ranges. GMR section 6.8 gives Sugihan days 51-120 and Kampar 1-69; the run files give 50.46-120.06 and 1.22-68.48. The chapter uses 50 to 120 and 1 to 68.
6. Sugihan run time. GMR section 6.4 gives 6.2 min for the 1.2 m run; the run's own `model_report.md` (rerun 2026-10-28) gives 9.4 min. The chapter gives no single run time; the FAQ quotes the GMR range of 6 to 35 minutes.
7. "Widest spread" at Kampar-Gaung. GMR section 6.6 says Kampar-Gaung has the widest spread of station levels (11 cm against 3 cm at Sugihan). SITES gives Mendahara-Batanghari 12.7 cm. The chapter compares Kampar with Sugihan only.
8. "Consistent" scenario baseline. GMR section 6.9 calls the 1.2 m baseline the consistent comparison; the interventions module assumes 1.0 m. The chapter says 1.2 m is closer but not equal.
9. Physical-model doc. `repeat-neraca/docs/physical-model.md` describes the frozen tiers 1 and 2 (500 m default grid, initial water table -0.20 m); the groundwater model command uses its own defaults (100 m grid, start saturated, `--h0` 0). Not a conflict for this chapter, noted because the two documents describe different programs that share the solver.

## Placeholders

- Figure model_station_fit_sugihan_lumpur (lines): `_khg/16.02.01_sugihan_lumpur/03_neraca/inputs/stations_daily.csv` (date, station_id, depth_cm); `station_sim_daily.csv` and `station_scores.csv` (column `flag`) in `SL/tropical-large_p1.2_s1.2_t1.2_e0.3_200m/` and `SL/tropical-large_p0.4_s0.4_t0.4_e0.3_200m/`; optional `model_series.csv` (P_mm, ET_mm).
- Figure model_days_map_mendahara (maps): `MB/tropical-large_p1.2_s1.2_t1.2_mt0.4_e0.3_100m_pb_dbbsdlp/model_season_days_deeper_40cm.tif`; `MB/tropical-large_p1.2_s1.2_t1.2_mt0.4_blk_e0.3_100m_pb_dbbsdlp/days_deeper_40cm_change.tif`; `_khg/15.05-07-10.01_mendahara_batanghari/05_pump/lidar/mendahara_batanghari.gpkg` layer `sekat_reach`; `_khg/15.05-07-10.01_mendahara_batanghari/00_inputs/khg.gpkg`; `_khg/15.05-07-10.01_mendahara_batanghari/02_delineation/lidar/subkhg_units.gpkg`.
- Figure model_days_by_distance (distance bands): SC12 and SC06, first-scenario tables "By distance from the block reaches".
- Diagram neraca_model_boundaries (re-peat/reports/project_report/diagrams/neraca_model_boundaries.drawio) (draw.io): boundaries and scenario inputs, from GMR D13, D17 and SIM `Boundary`.

## References cited

- Apers, S., De Lannoy, G. J. M., Baird, A. J., Cobb, A. R., et al. (2022). Tropical peatland hydrology simulated with a global land surface model. Journal of Advances in Modeling Earth Systems, 14(3), e2021MS002784. https://doi.org/10.1029/2021MS002784 (TPH references; GMR references). Used for: PEATCLSM-Trop form, ditch 0.68 m, spacing 31.4 m, R 0.68; ET thresholds.
- Cobb, A. R., and Harvey, C. F. (2019). Scalar simulation and parameterization of water table dynamics in tropical peatlands. Water Resources Research, 55(11), 9351-9377. https://doi.org/10.1029/2019WR025411 (TPH). Used for: Sy 0.29 near the surface.
- Hirano, T., et al. (2015). Global Change Biology. https://doi.org/10.1111/gcb.12653 (PAR, BURN). Used for: lower ET on burned, drained forest.
- Imanudin et al. (2018). Journal of Wetlands Environmental Management 6(1), 12-26. https://www.tropicalpeatlands.org/knowledge/publication/11463-19717 (REV sources). Used for: DRAINMOD on oil palm peat.
- Ismail, I., Torabi Haghighi, A., Marttila, H., Kurniawan, U., Karyanto, O., and Kløve, B. (2021). Water table variations on different land use units in a drained tropical peatland island of Indonesia. Hydrology Research, 52(6), 1372-1388. https://doi.org/10.2166/nh.2021.062 (TPH, PAR). Used for: Sy up to 0.3 near the surface and 0.1 at -1.5 m (the exponential is the team's fit).
- Jaenicke, J., Wösten, H., Budiman, A., Siegert, F. (2010). Mitigation and Adaptation Strategies for Global Change 15, 223. Thesis chapter: https://edoc.ub.uni-muenchen.de/11761/2/Jaenicke_Julia.pdf (GMR, REV). Used for: SIMGRO at Sebangau, R² 0.74; T 30 m²/d in the top metre.
- Katimon, A., et al. (2013). https://doi.org/10.1080/02626667.2013.815759 (BURN). Used for: saturation-excess runoff in tropical peat.
- Konecny, K., et al. (2016). Global Change Biology. https://doi.org/10.1111/gcb.13186 (BURN). Used for: surface lowering by fire.
- Kurnianto et al. (2026). Journal of Hydrology: Regional Studies 64, 103185. https://doi.org/10.1016/j.ejrh.2026.103185 (GMR, REV, PAR). Used for: MIKE SHE at Pulau Padang, 15-well validation, block effect 9 cm at 100 m and under 5 cm by ~300 m, calibrated Sy 0.10-0.15.
- Mahdiyasa et al. (2024). Earth Surface Dynamics 12, 929. https://esurf.copernicus.org/articles/12/929/2024/ (REV). Used for: MPeat2D.
- Putra, Baird and Holden (2022). Hydrological Processes. https://doi.org/10.1002/hyp.14470 (GMR, REV). Used for: DigiBog_Hydro (cited as Putra et al. 2022).
- Setiawan et al. (2020). IOP Conference Series: Earth and Environmental Science 504, 012020. https://doi.org/10.1088/1755-1315/504/1/012020 (BURN). Used for: no significant change in permeability after fire.
- Suryadi et al. (2021). Journal of Engineering and Technological Sciences 53(2). https://doi.org/10.5614/j.eng.technol.sci.2021.53.2.5 (GMR, REV). Used for: MODFLOW/FREEWAT at Kahayan-Sebangau.
- Sutikno et al. (2023). Water Management for Integrated Peatland Restoration in Pulau Tebing Tinggi PHU. Springer. https://doi.org/10.1007/978-981-99-0906-3_9 (GMR, REV; labelled *abstract* there). Used for: rewetting about 100 to 400 m from blocks at Tebing Tinggi.
- Taufik, M., Setiawan, B. I., and Van Lanen, H. A. J. (2019). Ambio 48, 363. https://doi.org/10.1007/s13280-018-1082-3 (REFS, *full text*). Used for: SWAP, seasonal canal levels and water-table exceedance.
- Urzainki, I., Laurén, A., Palviainen, M., Haahti, K., Budiman, A., Basuki, I., Netzer, M., and Hökkä, H. (2020). Canal blocking optimization in restoration of drained peatlands. Biogeosciences 17, 4769-4784. https://doi.org/10.5194/bg-17-4769-2020 (GMR, TPH). Used for: 2D Boussinesq model, fixed canal rule, no quantitative validation.
- Urzainki, I., Palviainen, M., Hökkä, H., Persch, S., Chatellier, J., Wang, O., Mahardhitama, P., Yudhista, R., and Laurén, A. (2023). A process-based model for quantifying the effects of canal blocking on water table and CO2 emissions in tropical peatlands. Biogeosciences 20(11), 2099-2116. https://doi.org/10.5194/bg-20-2099-2023 (TPH, GMR). Used for: tropical peat sets, canal network with weirs, 141 dipwells, KHG-wide rise 1.44 / 1.57 cm.

Not cited as a reference but named: MONALAGA, PUI Gambut dan Kebencanaan, Universitas Riau, product page https://puigk.unri.ac.id/id/produk-unggulan (GMR, REV); PP 57/2016 (0.4 m compliance level, MODEL comment on `REGULATORY_TARGET_M`).

## Added after review

- Block never lowers a canal (higher level kept on any already fixed canal cell): SIM `Boundary.heads`, `canal_override` branch (`np.maximum(head, level)` where `fixed & label == 2`).
- Interventions canal level 1.0 m: the Mendahara run used `balance_drawdown_m` 1.0 (`_khg/15.05-07-10.01_mendahara_batanghari/05_pump/lidar/run_report.json`); `repeat-pump/repeat_pump/core/sekat.py` lines 176-187: a block raises the canal upstream from a dry-season level `balance_drawdown_m` below the land. The run's `proposed_defaults.yaml` comment says the value is "only used to rank the sekat", while `sekat.py` also uses it to compute each reach's raise. Discrepancy 10: GMR line 405 says repeat-pump "places blocks assuming" 1.0 m; the code uses it to compute the raise and rank blocks. The chapter says "computes the water each block holds".
- Diagram: `repeat-neraca/docs/figures/neraca_method.drawio` shows only the adopted climatic balance and station deficit (no groundwater model), so a new draw.io placeholder is used.

- Scenario plan: the block runs record 160 reaches (`run_config.json` notes.block_reaches, runs of 28 October 2026 14:04) from the interventions plan of 27 October 2026; `05_pump/lidar/mendahara_batanghari.gpkg` layer sekat_reach now has 150 reaches after the rerun with the KLH spacing (min_new_spacing_m 500, dedup_tol_m 100). The owner chose to keep the scenarios and state the plan used.

## Added 2026-10-29: target, canal levels, canal modes, station outliers

Abbreviations: BAND = `repeat-neraca/docs/reports/managed_target_band.md`; MODES = `repeat-neraca/docs/reports/canal_modes.md`; SUB = `repeat-neraca/docs/reports/subcell_canal_check.md`; OUTL = `repeat-neraca/docs/reports/station_outliers.md`; CONC = `repeat-neraca/docs/reports/concession_levels.md`; LID = `repeat-neraca/docs/reports/lidar_canal_levels_14.10.01.md`; CANAL = `repeat-neraca/research_notes/canal_levels_evidence.md`.

- Boundaries, LiDAR levels 0.8 / 0.3 / 0.3 m: LID (medians 0.80, 0.32, 0.24 m); shallow bound for narrow drains: CANAL section 1; GMR section 6.10. D18, D19, D20: GMR section 3 table; SIM `Boundary.leak`, `CanalStore`; FC `screen`.
- D18 numbers: SUB (fixed bias +1.6 to +18.5 cm, leak factor 12 within 0.7 cm); 40% fixed canal cells at 200 m: Sugihan-Lumpur `model_report.md` of `SL/tropical-large_p0.8_s0.3_t0.3_mt0.4_e0.3_200m_pb_dbbsdlp` ("canals 39.9%").
- D20 numbers: OUTL national table (22,656 of 132,109 concession = 17%; 732 of 3,167 community = 23%).
- Concession step 2.5 to 1, 1,157 stations: CONC. Published water tables: CANAL section 4 (Evans 2019 70 ± 17 cm; Hooijer 2012 0.70-0.73 m; Vernimmen and Hooijer 2026 -0.6 / -0.85 m at 5-9 m elevation).
- Band table: BAND (open-land days and supply per run).
- Canal modes, same cells 0 to 2 days for D18; store canal depth 0.41-0.55 m at Mendahara-Batanghari and Sugihan-Lumpur: MODES; GMR section 6.12.
- Mendahara community record: 3 July days, three-week gap, restart above the ground: `_khg/15.05-07-10.01_mendahara_batanghari/03_neraca/inputs/model/stations_daily.csv`; figure model_community_mendahara (daily mean on days with at least 5 of 6 stations: about -50 cm in the restart week). Screened 44 / 11 cm and model values: MODES community table (screened columns). Raw 29 / 63 cm: same table.
- FAQ factor 2 to 5: BAND (Sugihan 243 to 103, Kampar 40 to 8, Mendahara 172 to 92 mm).
- Figure model_community_mendahara: `re-peat/tools/project_report_figures.py`, function of the same name.

References added:
- Evans, C. D., Williamson, J. M., Kacaribu, F., et al. (2019). Rates and spatial variability of peat subsidence in Acacia plantation and forest landscapes in Sumatra, Indonesia. Geoderma, 338, 410-421. https://doi.org/10.1016/j.geoderma.2018.12.028 (CANAL, *full text*). Used for: Acacia water table 70 ± 17 cm.
- Hooijer, A., Page, S., Jauhiainen, J., et al. (2012). Subsidence and carbon loss in drained tropical peatlands. Biogeosciences, 9, 1053-1071. https://doi.org/10.5194/bg-9-1053-2012 (CANAL, *full text*). Used for: plantation water tables 0.70-0.73 m.
- Vernimmen, R., and Hooijer, A. (2026). Satellite LiDAR reveals patterns in water table depth and flood risk in SE Asia coastal lowland and peatland plantations. Frontiers in Environmental Science, 14, 1869652. https://doi.org/10.3389/fenvs.2026.1869652 (CANAL, *full text*). Used for: canal water about -0.6 m (oil palm) and -0.85 m (Acacia) at 5-9 m elevation.
