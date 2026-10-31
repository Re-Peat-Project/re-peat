# Sources for chapter 9 (RE-PEAT Interventions)

Abbreviations: PM = repeat-pump/docs/pump-method.md; PD = repeat-pump/docs/proposed_defaults.md; PY = repeat-pump/configs/proposed_defaults.yaml; QP = repeat-pump/docs/qgis_plugin.md; RM = repeat-pump/README.md; RD = re-peat/docs/04-rewetting-design.md; KLH = repeat-pump/docs/Panduan Teknis GIS Rewetting KLH.docx (text read with python-docx, Appendix A table "Ringkasan Parameter" and Appendix D table); WF = repeat-pump/docs/Workflow GIS Rewetting KLH.docx; code = repeat-pump/repeat_pump/core/<file>.py; SL = _khg/16.02.01_sugihan_lumpur/05_pump/<dem>/ (runs of 2026-10-28 15:45-15:51). The undated files directly in SL's parent folder (run_report.json of 2026-10-27) are an older run and were not used.

## Purpose, position in the chain, inputs

- Deliverables (blocks on primary/secondary canals, reach, interventions per sub-KHG, budget, optional pumping): PM lines 7-13.
- Chain position and what each upstream module supplies: PM lines 15-24 (table).
- Inputs table: PM lines 26-39; RM input table; DSM refused: RM "dtm | Bare-earth DTM. surface_type: DSM is refused".
- Run config written from the KHG folder, nothing typed by hand: PM line 41.
- Policy values start empty; stage stops until filled; preset values listed as warnings and in run report: RM section 2; PD lines 3-6; code config.py line 172-180 (None defaults).

## Twelve stages

- Method figure: repeat-pump/docs/figures/pump_method.drawio (existing draw.io diagram, dated 2026-10-27; its boxes contain file paths and option names, which the build or the team may want to simplify).

- Stage list, names, review flags (2, 6, 9), 11 optional, 12 always last: code pipeline.py lines 15-28.
- Fingerprint and rerun of later stages: PM line 45.
- Stage 1 clip margin 600 m: PY run.clip_margin_m; SL lidar run_report.json config.run.clip_margin_m = 600. Accuracy warning when dA < 2 x RMSE: code io.py lines 349-350; PD line 111 ("above 0.2 m").
- Stage 2 snap 1 m, QA layers, nothing deleted silently: PY topology.snap_tolerance_m; KLH Appendix C row 3.1-3.2.
- Stage 3 burn depth 2 m default: PD line 73; SL run_config.yaml hydro.burn_depth_default_m = 2.0.
- Stage 4 500 m segments, <25 m flagged not scored: PD lines 71-72; SL lidar run_report.json notes[0].
- Stage 5 sample step 5 m: SL lidar run_config.yaml profiles.sample_step_m = 5; direction fallback order and 1.5 times rule: PM line 47.
- Stage 6 ring 15-100 m: SL run_config.yaml prioritise.ring_buffer_m [15, 100]; KLH Appendix C row 6.1-6.3. Min-max, direct/AHP, sensitivity: code prioritise.py lines 1-10. Top 20 %: run_config.yaml prioritise.top_fraction 0.2 and code prioritise.py line 361. Sensitivity steps ±10/±20 %: SL lidar run_report.json sensitivity[].delta_pct.
- Stages 8-10 description: PM line 57; code routing.py lines 1-8, pumps.py lines 1-8.
- Stage 11 algorithms and objectives: PM line 59; off by default: PD line 92.
- Stage 12: code report.py line 1 and lines 66-68.
- Block-only when no river qualifies: RM "Sekat only" paragraph; SL warnings "rivers: no features inside the analysis extent" (all three runs).

## Head rule, KLH minimum distance, merge

- dA 0.40 m from PP 57/2016: PM line 53 and table line 96; code sekat.py lines 1-9.
- Walk upstream, block at dA rise, existing resets baseline: code sekat.py place_sekat lines 24-58.
- n_req = ceil(dz/dA), IPG = n_existing / n_req, js = dA/i capped at max_spacing, ts formula: code sekat.py lines 3-9 and 316-334.
- Reinforced at slope >= 5 %, marks type only: code sekat.py line 339; PD line 81.
- Min distance 500 m between new blocks and merge 100 m adopted 2026-10-28 at users' request; guide used 50 m: PD lines 23-24; PY lines 28-31. Implementation: code sekat.py place_sekat line 57 (min_new) and dedup_proposed lines 61-77; used by the runs: SL lidar run_report.json config.sekat.min_new_spacing_m = 500, dedup_tol_m = 100.
- "On land steeper than 0.40 m in 500 m (0.08 %)": PD line 22 and 23 (dA/500 = 0.08 %).
- Min 100 m from existing on the same canal: code sekat.py line 52 (min_spacing, only against existing positions on that canal); value 100 m from PY sekat.min_spacing_m.
- Snap tolerance 30 m for existing blocks: PY sekat.snap_tolerance_m; code sekat.py lines 281-304.
- max_spacing caps only the reported required spacing: code sekat.py lines 151, 334 (js_req) and no other use (grep of core/*.py; requirements.py line 76 only lists it as required).

## Balance and reach

- Canal-rise objective, held at land minus dA, raise upstream stations from drawdown level, capped at surface, rank by extra rise, keep fewest giving share, max_blocks override: code sekat.py balance() lines 172-223; PM line 54.
- Reach layer content: PM line 55; code sekat.py reach_lines; layer columns rise_m, depth_m, burnt_frac read from SL gpkg layer sekat_reach.
- 90 % evidence (2.4-5 times; 1.9-2.5 times more water per block): PM line 82. Tertiary 2.8-3.3 times: PM line 84. Primary/secondary per KLH guide: KLH step 1.2.
- Drawdown 0.8-1.2 m ranking barely moved: PD line 27; PY line 36-37.
- Groundwater model uses same 1.0 m unblocked canal level: AGENTS.md line 115 ("A block scenario needs the same unblocked canal level as repeat-pump (sekat.balance_drawdown_m, 1.0 m)"); PD line 98 (optimise.canal_drawdown_m 1.0 m).

## Prioritisation

- Top 3 sub-KHG by rank: SL run_config.yaml run.subkhg_selection (mode top_n, n 3); code prioritise.py lines 383-386. Rank from _khg/16.02.01_sugihan_lumpur/04_prioritisation/lidar/subkhg_priority.csv (priority_rank).
- Equal weights 0.25 (legacy KLH equal weighting), sign-off still open: PY lines 41-45; PD line 28. AHP CR <= 0.10: code prioritise.py line 9; QP line 49. KLH scoring 1-3, threshold 10: code prioritise.py lines 12-17; KLH 7.1-7.2. Concession flag: PY line 49.
- Sensitivity minima: SL <dem>/run_report.md "Weights and sensitivity": lidar 0.988 / 0.93; deltadtm 0.983 / 0.92; demnas 0.977 / 0.82.

## Routing and pumps

- 30 m river buffer: PY line 18; code network.py lines 15-22. Target highest node of each cluster: code routing.py lines 150-162. Cost = length + lambda x uphill; Steiner default, per-target option; ungated existing blocks dead ends; proposed blocks gated: code routing.py lines 1-8, 30-40; lambda 1000 (1 m = 1 km): PY line 58.
- Demand modes, Q = V / period, influence 600 m: code pumps.py lines 1-8, 129-138; PY lines 59-62. 120 days July-October (Ritzema 2014): PY line 62. Manning 0.035 (Chow 1959): PY line 53. Max head 5 m, capacity 0.10 m3/s, efficiency 0.65 (Haman 2017): PY lines 55-57. Station at intake and when cumulative head exceeds max, snapped to latest block: code pumps.py site_stations lines 42-80. P = rho g Q H / eta (Karassik 2008): code pumps.py lines 25-27. Shortfalls reported: code pumps.py line 208. Pump values low/medium confidence: PD lines 33-42. Pumping not run on a real KHG: PM line 150.

## Interventions

- Rules and thresholds: code interventions.py classify() lines 96-112; thresholds PY lines 75-85; SL run_report.json interventions.thresholds. "Otherwise" class: code interventions.py lines 114-118.
- Held water = rise x Sy 0.15 x 600 m (Urzainki et al. 2023): code interventions.py line 173; PY lines 84-85. Deficit = KHG deficit mm x unit area: code interventions.py lines 160-163. Units not analysed use KHG deficit >= 50 mm: code interventions.py line 107.

## Budget

- Items and quantity rules: code budget.py lines 1-17 and quantities() lines 62-93 (reinforced = sekat_type not standard; IPG estimate from sekat_tambahan; canal density primary+secondary x area x peat fraction; burnt ha; wells burnt ha / pi r^2; pumps and fuel = kW x hours x period x L/kWh).
- Prices: PY lines 87-98; PD lines 50-61. Search date 2026-10-27, not inflation-adjusted, not verified, P.4/2019 not found: PD line 46; PM line 149. Sources kinds (news, ULM journal, Tokopedia, solardistro diesel): PD lines 52-59.
- Register 19 rows, statuses 15 to verify, 2 unconfirmed, 1 assumption, 1 obtain from KLH: repeat-pump/repeat_pump/data/budget_sources.csv, column status (counted with pandas).
- Canal closure unpriced: PY line 91; SL run_report.md "Not priced".

## Outputs, layouts, plugin

- Output list: PM lines 108-119; RM "HTML report" and "Map layouts" paragraphs; QP line 66 (symbols, budget table, locator, templates A0-A4).
- Layout figure: _khg/16.02.01_sugihan_lumpur/05_pump/lidar/layouts/layout_A3_landscape.png (viewed: all text renders as solid bars; same in deltadtm A3 and demnas A0). Production defect reported to the coordinator, not in the chapter text.
- Plugin external runner, private env, internet once: QP lines 3-14. Wizard features: QP lines 24-66; RM section 4. Tested headless in QGIS 4.2.2, not by a person on desktop: QP line 81.

## KLH guide comparison

- Ten steps, values: KLH text lines "Alur kerja terdiri atas sepuluh tahap" and Appendix A table (segment 500 m, sliver 25 m, burn 2 m, buffer 50 m, MCDA max 12, breaks, threshold >= 10 temporary, muara buffer 30 m, contour 0.5 m, SNAP/NODE_TOL, JARAK_MIN 500 m, DEDUP_TOL 50 m, SLOPE_MIN_PCT 5 % mode tandai).
- Deliberate differences: KLH Appendix D table (attribute dominance, min-max vs fixed breaks, ring buffer vs 50 m, BURN_FREQ, concessions, centroid vs highest pool, contour vs dA, threshold vs top fraction, weighting); PD lines 65-88.
- Guide places blocks on the route: KLH step 10.3 (input "hasil routing (Tahap 9)"; check "Titik lokasi sekat kanal tampil di sepanjang jalur rute"). Module places on every analysed canal: code sekat.py run loop lines 307-340 over all cleaned canals.
- Workflow document is an earlier draft with open decisions ("Perlu keputusan"), including the sekat design method still under trial: WF. Not cited for values.

## Sugihan-Lumpur results (all from SL, 2026-10-28)

- Selected sub-KHG: run_report.json validation.selected_subkhg (lidar S21, S03, S02; deltadtm S23, S03, S08; demnas S20, S06, S04).
- DTM: lidar run_config.yaml inputs.dtm.path = 01_dem/inputs/lidar_oki25.tif, validation.dtm_resolution_m 25.0; deltadtm and demnas path 01_dem/benchmark/04_processed/<dem>/dtm_smooth.tif, resolution 30.0 and 8.0. "KLHK 25 m LiDAR DEM": AGENTS.md _data table (lidar_klhk/dem_25m, 25 m DEMs incl. OKI).
- Vertical error: run_report.json config.inputs.dtm.vertical_rmse_m (0.3, 0.49, 4.97); PY suggested_facts.
- Canals clean: counts.2.canals_clean (596, 408, 476). Oriented by flow accumulation / unresolved: run_report.md Stage 5 warnings (191/302, 165/182, 294/178).
- Existing in extent / snapped: counts.7.existing (173, 273, 380) and gpkg layer sekat_existing_assessed column snapped sum (76, 127, 131) = existing minus counts.7.unsnapped (97, 146, 249).
- Dropped as duplicates: run_report.md Stage 7 warnings (3, 4, 12).
- Head-rule / kept: sekat_balance.head_rule (86, 117, 226), sekat_balance.kept (43, 39, 62). 226/86 = 2.63. LiDAR share kept 0.902: sekat_balance.share_kept.
- Tertiary canals 3-4 times more sekat at Sugihan-Lumpur: PY lines 16-17 (comment on topology.canal_classes).
- Unit codes per variant: each DEM has its own 02_delineation/<dem>/subkhg_units.gpkg (unit counts 29, 29, 27 in interventions.units); a check of S03 overlap between lidar and deltadtm could not match ids (id column khg_id holds the KHG code), so no claim is made.
- Well area 12.6 ha: PY line 94.
- Reach km and burnt km: sum of length_m and length_m x burnt_frac of gpkg layer sekat_reach (68.7/26.9, 110.1/65.0, 128.9/58.9) (computed in this task with geopandas).
- Water held / deficit: interventions.held_m3_selected and deficit_m3_selected (2,193,873 / 196,886,024; 5,063,346 / 175,921,233; 5,015,239 / 227,084,736). Shares per unit: interventions.held_share_selected.
- KHG deficit 290 mm: interventions.csv column deficit_mm = 290.238.
- Interventions counts: interventions.counts; units: interventions.units (29, 29, 27).
- Budget: run_report.json budget.by_item and totals; run_report.md budget table; cost per m3: budget.idr_per_m3_held (352.8, 138.6, 222.5). Revegetation share 564.81 / 619.79 = 91 %.

## Discrepancies (docs vs code; code taken as right) and contradictions

1. max_spacing_m: PM line 53 and PY line 25 describe "spacing js = dA / slope, at most 500 m" as a placement rule. In code (sekat.py lines 151, 334) max_spacing_m only caps the reported js_req_m; place_sekat never adds a block for distance. Chapter describes the code.
2. min_new_spacing_m: PD line 79 says "opt-in, not in the preset" and code docstring sekat.py line 31 says "off by default", while PD line 23 and PY line 28 put 500 m in the preset (adopted 2026-10-28). Engine default is None (config.py line 176); the preset sets 500 and the 2026-10-28 runs used it. Chapter says adopted via the proposed defaults.
3. min_spacing_m (100 m): PY line 26-27 says it "keeps proposals from clustering"; code applies it only between a new block and existing blocks on the same canal (sekat.py line 52).
4. Interventions and budget docstrings (interventions.py line 1, budget.py line 1) say "part of stage 11"; pipeline.py runs them in stage 12 (report). Chapter follows the pipeline.
5. PM section 8 results (124 head-rule, 54 kept, 109 of 232 existing, 3.27 / 230.7 million m3, budget 406.1/636.3/769.8) and PD line 26 ("54 of 123") are from 2026-10-27, before the 500 m / 100 m defaults. The 2026-10-28 runs give 86 / 43 on LiDAR. Chapter uses the 28 October runs. The PM evidence for the 90 % share (decision 1) predates the 500 m minimum distance.
6. RD (hub method page) proposes a pool rule of 0.3 m (0.4 m minus freeboard), anchors at outlets and junctions, a 100 m anchor merge and Monte Carlo DEM noise; none of these is in the module code. Chapter describes the module only.
7. QP line 81 says the wizard was driven through "all 11 stages"; pipeline.py has 12 stages (stage 11 optional). RM says 12.
8. The DEMNAS error of 4.97 m (PY suggested_facts) is from a field comparison of raw DEMNAS, but the DEMNAS run used the corrected surface (dtm_smooth.tif); the error of the corrected surface at this KHG is not stated in these sources. Noted as a limit.
9. The "lidar" variant at Sugihan-Lumpur is a 25 m LiDAR-derived DEM, not 1 m LiDAR; PD line 20 assumes 1 m LiDAR cells for breach distance 100 cells (about 2.5 km at 25 m).
10. Layout PNGs from the batch export show all text as solid bars (viewed lidar A3 and demnas A0); they need re-export before use in the report.
11. sekat_new summed over selected units in interventions.csv (34, 33, 41) is lower than kept blocks (43, 39, 62); some kept blocks fall in the 600 m clip margin outside the selected units. The budget prices all kept blocks (budget.csv sekat_standard 43, 39, 62). Chapter reports kept blocks.

## References cited (as listed in repeat-pump/docs/references.md)

- Urzainki et al. (2020). Biogeosciences 17, 4769-4784, doi:10.5194/bg-17-4769-2020. Used for: canal-rise objective (PM line 54, line 170).
- Urzainki et al. (2023). A process-based model for quantifying the effects of canal blocking on water table and CO2 emissions in tropical peatlands. Biogeosciences 20, 2099-2116, doi:10.5194/bg-20-2099-2023. Used for: about 600 m reach of block effects.
- Ritzema et al. (2014). Catena 114, 11-20. Used for: dry season July to October (PD line 42).
- Chow (1959). Open-Channel Hydraulics. McGraw-Hill. Used for: Manning n 0.030-0.040, Table 5-6 (read via drainagecalculators.com per references.md).
- Haman (2017). Pumps for Florida Irrigation and Drainage Systems, UF/IFAS CIR832 (WI001). Used for: pump efficiency 65-80 %.
- Karassik et al. (2008). Pump Handbook, 4th ed. McGraw-Hill. Used for: P = rho g Q H / eta (code pumps.py line 26).
- PP 57/2016 (regulation, listed as PP57-2016 "see the spec"; no further detail in references.md). Used for: 0.40 m water-table limit.
- Panduan Teknis GIS Rewetting KLH (repeat-pump/docs/, PanduanKLH). Used for: guide steps and values.

- Diagram: the report embeds a reader version drawn in draw.io, re-peat/reports/project_report/diagrams/*_report.drawio (plain labels; same boxes and edges as the module original).
