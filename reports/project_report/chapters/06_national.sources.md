# Sources for chapter 6 (national prioritisation)

Abbreviations: OP = `re-peat/reports/national_profile/operational/`, VA = `re-peat/reports/national_profile/validate/`, S3 = `re-peat/reports/national_profile/stage3/`, PR = `repeat-prioritisation/src/repeat_prioritisation/`.

## Numbers and claims

- 865 KHG profiled, 476 ranked: OP `report.json` keys `n_profiled`, `n_ranked`; also `_slides/build/facts.json` `nat_profiled`, `nat_ranked`.
- 389 not ranked: OP `profile.csv`, `kelas` = "Tidak diperingkat (KHG kecil)" count.
- Ranking test: area >= 50 km² and peat >= 25 km²: OP `report.json` `config.min_area_km2` = 50, `config.peat.min_peat_km2` = 25; code `PR/national/profile.py` `rank()` line 496.
- Peat on 180,004 km² (ranked) of 185,920 km² (all): OP `profile.csv`, sum of `peat_km2` over rows with `peringkat` not empty / all rows.
- Fire counted on peat (representative point of burned patch, cell under hotspot): `PR/national/profile.py` `burned_by_year` (line 225-227), `hotspots_by_year` (264); `re-peat/docs/15-national-profile.md` "Peat basis".
- GFW extent about 76 m, union of Miettinen et al. 2016 and Gumbricht et al. 2017: `re-peat/sites/data_catalog.csv` row `peat_extent_gfw_v20230315_z11.tif`; `re-peat/docs/15-national-profile.md`.
- Global Peatland Map as cross-check (non-commercial licence): `re-peat/docs/15-national-profile.md`; AGENTS.md analysis conventions.
- Median peat share per island (0.66/0.93/190 etc.): `re-peat/reports/national_profile/dashboard_data.json` `data.meta.peat_by_island` (median `peat_frac`, median `peat_frac_gpm1km`, n), computed in `PR/national/dashboard.py` lines 233-235.
- Indicators and weights (2, 1, 1, 1, 0.5, 0.3, 0.2): OP `report.json` `indicators_used` and `config.indicators`; `_slides/build/facts.json` `nat_weights`.
- Fire period 2015-2025 in operational mode: OP `report.json` `config.years.baseline`; code `PR/national/profile.py` `main()` line 554-555.
- VIIRS S-NPP 375 m, NASA FIRMS, type 0, confidence n and h: OP `report.json` `config.hotspots`; `re-peat/sites/data_catalog.csv` row `hotspot_viirs_snpp_2012_2025.gpkg`.
- KLH hotspots MODIS, 1 Jan to 15 Sep 2026, medium and high kept, two schemas harmonised: OP `report.json` `now.last_date` = 2026-09-15, `now.months` 1-9; `PR/national/profile.py` `hotspots_now`, `LEVEL`; `re-peat/docs/15-national-profile.md` "This year's hotspots"; data_catalog row `_data_hotspot_Januari_September_2026.gpkg`.
- 167,718 points, 160,207 medium or high: OP `report.json` `now.n_points`, `now.n_kept`.
- 37,657 on peat inside KHG: OP `profile.csv` sum of `hs_now_kept`.
- High-only switch on the dashboard: `re-peat/docs/15-national-profile.md` "Hotspot confidence".
- Separate indicator because MODIS and VIIRS counts not comparable: `re-peat/docs/15-national-profile.md`; data_catalog row VIIRS (notes).
- Tolak-Siduk top by density (3.93 per km², 604): OP `profile.csv` row KHG.61.04.06, `peringkat_now` = 1, `u_hotspot_now` = 3.928, `hs_now_kept` = 604.
- Kahayan-Sebangau top by count (2,538): OP `profile.csv` row KHG.62.11-14.02, `peringkat_now_n` = 1, `hs_now_kept` = 2538; `_slides/build/facts.json` `nat_now_top`.
- Canal weights add to 1, split of single weight: `repeat-prioritisation/configs/examples/national_profile.yaml` comment on `u_canal_primary`.
- 517 KHG with no canal segment: OP `profile.csv`, `u_canal_density` empty (count 517), code `profile.py` line 466-469 (`canal_segments > 0`).
- 213 of the ranked KHG without canals: OP `profile.csv`, rows with `peringkat` and empty `u_canal_primary`.
- Weight 0 columns (burned now, FRP rho 0.99, peat depth, structures, villages, SiTMAT): OP `report.json` `config.indicators`; `re-peat/docs/15-national-profile.md` table.
- Peat depth map covers 100 KHG: OP `profile.csv` non-empty `i_peat_depth` = 100.
- SiTMAT in 164 KHG, threshold 0.4 m, min 30 days, concession stations: OP `profile.csv` `tma_deep_share` non-empty count 164; OP `report.json` `config.tma` (kinds concession, threshold_m 0.4, min_days 30).
- Scaling 5th-95th percentile, clip, weighted mean of available indicators: `PR/common/scoring.py` `normalise`, `group_score`; OP `report.json` `config.scoring.normalise_quantiles`.
- Score = urgency (no impact indicators scored): `PR/common/scoring.py` `score()` line `skor_risiko = a*u + (1-a)*impact.fillna(u)`; all scored indicators are `u_`.
- Tertiles by rank, score 0 = low: `PR/national/profile.py` `rank()` lines 528-532; class counts 158/159/159: OP `report.json` `class_counts`.
- Correlated pairs 0.891, 0.867, 0.83: OP `report.json` `correlated_pairs`.
- Sensitivity 300 runs, Dirichlet concentration 20, 89.3% stable, median rank SD 13.1: OP `report.json` `sensitivity`, `config.scoring.sensitivity_concentration`; stable = `p_fokus_tinggi` >= 0.8 or <= 0.2, `PR/common/scoring.py` `sensitivity()`, high_fn in `profile.py` line 513.
- Validation numbers (AUC 0.973/0.970, capture 0.846/0.886, Spearman 0.735/0.771; hotspots 0.956/0.882, 0.771/0.815, 0.829/0.784; positives 10 and 282): VA `report.json` `validation`; same in `_slides/build/facts.json` `nat_validation`.
- Validation design (baseline 2015-2022, test 2023-2025, this year's hotspots excluded; positive = burned share >= 0.05; capture weighted by KHG area): VA `report.json` `config.years`, `config.scoring.validation_burn_threshold`; `PR/national/profile.py` `rank()` line 499-501; `PR/common/scoring.py` `validate()`, `_capture()` (uses `area_km2`).
- Top 20 by island (11/8/1) and province (6/6): OP `profile.csv`, rows `peringkat` 1-20, columns `island`, `province`.
- 14 of top 20 kept on area basis: OP `profile.csv`, rows `peringkat` 1-20 with `peringkat_area` <= 20.
- Yearly sums (burned peat 2015 11,346; 2019 4,547; 2023 2,861; other years 68-1,532 km²; hotspots on peat 2015 345,772, 2019 166,389): OP `yearly.csv`, metric `burned_peat_km2` and `n_hotspot_peat`, summed over `khg_id` per `year`.
- Selected KHG list and roles; Cawang-Lalang unresolved: `re-peat/sites/selected_khg.csv`; `re-peat/docs/13-selected-khg.md`.
- Ranks, classes and `p_fokus_tinggi` of team KHG: OP `profile.csv` columns `peringkat`, `kelas`, `p_fokus_tinggi` for khg_id KHG.61.12-71.01, KHG.63.07-08-11.01, KHG.62.11-14.02, KHG.61.02-08.01, KHG.16.02-07.01, KHG.16.02.01, KHG.14.03.02, KHG.15.05-07-10.01, KHG.15-16.01, KHG.62.03-04.01, KHG.91.18-17.01, KHG.14.10.01, KHG.14.10.03. Same ranks in `_slides/build/facts.json` `team`.
- Padang and Tebing Tinggi burned share below 0.4%: OP `profile.csv` `u_fire_freq` 0.00399 and 0.00307.
- Buru Mappi burned share 0.7%, 920 hotspots, 12th by count: OP `profile.csv` KHG.91.18-17.01 `u_fire_freq` 0.0069, `hs_now_kept` 920, `peringkat_now_n` 12.
- Stage 3 for 34 KHG (top 25 + team): S3 `stage3_profile.csv` (34 rows); `PR/national/stage3.py` `select()`.
- Stage 3 layers, TerraClimate 2015-2021 dry months June-October, 250 m sampling, permanent water >= 10 months: `repeat-prioritisation/configs/examples/national_stage3.yaml` (`years.baseline`, `dry_months`, `grid_res_m`); `PR/national/stage3.py` `water_season()` (v >= 10).
- Deficit 5 mm (KHG.11.05-14.01) to 120 mm (KHG.62.11-14.02); tree cover 0.25 (KHG.62.03.03) to 0.95 (KHG.11.05-14.01): S3 `stage3_profile.csv` columns `deficit_mean_mm`, `lc_tree`.
- ERA5 dropped (70 s per month per KHG, 25 km): `re-peat/docs/15-national-profile.md` Stage 3.
- Overlay layers, grid of points, licences not summed, burns 2015-2025: `PR/national/overlay.py` docstring, line 127 (cell size), line 210 (`BA_2015`-`BA_2025`); `re-peat/docs/15-national-profile.md` "Land status overlays".
- Sugihan-Lumpur licence peat 4,313 km² (0.796), burned 1,748 km², hotspots 193: S3 `overlay/overlay_summary.csv` khg_id KHG.16.02.01, layer `licence_any`; total 213 from OP `profile.csv` `hs_now_kept`.
- Kahayan-Sebangau licence share 0.035, 98 of 2,538: same file, KHG.62.11-14.02.
- Mempawah 0 of 691, Buru Mappi 0 of 920 inside licences: same file, KHG.61.02-08.01 and KHG.91.18-17.01, `hs_now_peat`; totals OP `hs_now_kept`.
- Protected function: Saleh-Sugihan 128 of 146, share 0.918; Pungurbesar 1,636 of 1,825: `overlay_summary.csv` layer `feg`, class `lindung`; totals OP `hs_now_kept`.
- 5 km ring from BlueBook "Buffer 5 Kilometer"; no regulation found: `re-peat/docs/15-national-profile.md`; `PR/national/overlay.py` docstring.
- Dashboard (bilingual, eight sliders in three groups, filters, confidence switch, parity check, views, link state, CSV): `re-peat/docs/15-national-profile.md` "The dashboard"; `PR/national/dashboard.py` `PARAMS` (8 parameters).
- Not scored yet list: `re-peat/docs/15-national-profile.md` "Not in the score yet".

- KLH target about 3.3 million ha in 337 priority KHG, selected with SKEG (burned land, land affected by canals): KLH/BPLH 2026, TOR of the 2 November 2026 FGD, as relayed by the coordinator (document supplied by the user; not read in the workspace by this author). The 337-KHG list is not in the workspace; no comparison made.

## Discrepancies between docs and code (code followed)

1. Confidence size test: `15-national-profile.md` says "area of 50 km2 or more"; `profile.py` line 476 uses peat area >= `min_peat_km2` (25 km²) when the peat basis is on. Confidence is not quoted in the chapter.
2. Peat depth coverage: config comment (`national_profile.yaml`) says 89 of 865 KHG; `15-national-profile.md` says about 100; the data (OP `profile.csv`) has 100. Chapter uses 100.
3. KHG without canals: `_slides/build/facts.json` `nat_no_canal` = 518 (KHG with zero canal km); code leaves `u_canal_*` empty where `canal_segments == 0`, which is 517 KHG, matching `15-national-profile.md`. Chapter uses 517.
4. Overlay grid: doc says 100 m, or 200 m for the largest KHG; `overlay.py` line 127 uses max(100, round(sqrt(area/60000)/50)*50) m. Chapter describes the code.
5. Stage 3 and SiTMAT: the task brief lists SiTMAT as a stage 3 layer; `stage3.py` writes no SiTMAT columns. SiTMAT is in the national profile (`tma_by_khg` in `profile.py`), reported, weight 0. Chapter describes it there.
6. Stage 3 is described in `15-national-profile.md` and code as shown, not scored; there is no score refinement in stage 3. Chapter says so.
7. `profile.py` module docstring says "Everything normalised by KHG area (the peat area is not available yet)"; the code uses the peat basis (`use_peat`). Chapter follows the code.
8. Code default `min_area_km2` is 10 (`profile.py` DEFAULTS); the config and the run use 50 (OP `report.json`).
9. OP `report.json` lists input `dmpg` as `dpg/dpg_atlas_villages.csv`, the code default is `dpg/dpg_villages_boundaries.gpkg`; the run predates the current default. The validate run (22 Oct) is older than the operational run (26 Oct) and lists the older village file `desa_target_pemulihan_ekosistem.gpkg` (removed 2026-10-24, identical to the `_gambut` file per AGENTS.md). Neither affects scored indicators.
10. The `0.6` urgency/impact mix (`alpha_urgency`) has no effect nationally because no impact indicator is scored.
11. Dashboard parity: `15-national-profile.md` gives `150:0` as an example only; no parity result was read, so none is quoted.

## References cited

- KLH/BPLH (2026). Terms of reference, FGD of 2 November 2026 on fire prevention through KHG water governance. Supplied by the user to the coordinator; no file path or URL known to this author.

- Miettinen, J., et al. (2016) and Gumbricht, T., et al. (2017): named as the two sources of the GFW composite peat extent for Indonesia in `re-peat/docs/15-national-profile.md` ("Peat basis") and `re-peat/docs/14-data-catalog.md` (row `peat_extent_gfw_v20230315_z11.tif`). No full reference or DOI is given there. Source layer URL as given in the catalogue: tiles.globalforestwatch.org/gfw_peatlands/v20230315 (CC BY 4.0).

## Added after review

- Overlay cell size rule (about 60,000 points per KHG, from 100 m in 50 m steps): `PR/national/overlay.py` line 127.
- Buru Mappi has no licence area in the 2025 layer: `stage3/overlay/overlay_summary.csv` KHG.91.18-17.01, layer `licence_any`, `area_km2` 0.
- Burnt-area source not recorded: `re-peat/sites/data_catalog.csv` row `burnt_area_2015_2026_Indonesia.gpkg` (source column empty).
- `hs_now_high_share` added to placeholders: OP `profile.csv` column `hs_now_high_share` (high-confidence share of this year's hotspots on peat, `profile.py` line 460).

# Section 6.9 (reading the ranking), rewritten 2026-10-29

Numbers printed by `project_report_dashboards.py numbers`.

### Methods reproduced

- SiTMAT: `derive()` reproduces `deriveStations()` and `selectPop()` of repeat-sitmat/assets/js/data.js at the explorer defaults: flagged readings dropped (`noFlag`), weekly bins of 7 days from 1 April with at least 3 readings (`MIN_WEEK_DAYS`), start level = median of the first 4 weekly medians with at least 2 valid (`BASE_WEEKS`), panel = coverage of weeks at least 0.6 (`minCov`) and a start level, Theil-Sen slope with tie-corrected Mann-Kendall z, significant at |z| >= 1.96, trends need 8 weekly values. National series need 5 stations per week (overview.js), regional ones 2 (`minN`). Duration curves: insights.js `renderDuration` (thirds of the window, pooled daily readings). Dry spells: insights.js `longestSpell` (`DRY_GAP` 2). Concessions: insights.js `concessionStats` (stations with 20 or more valid days, mean of station shares; at least 3 stations, the `PAT.min` default). Sharing: regions.js `renderSharing` (mean of station means per kind and KHG).
- Check of the reproduction: the explorer page at default settings shows 525 panel stations of 1,132 with data, -2.7 cm, -0.22 cm/wk significant, 33 % -> 35 % below -40 cm, 49 % drying and 12 % wetting (figures/screen_sitmat_overview.png, shot 2026-10-29); the Python output gives the same six values (lines "concession 2026-04-01..2026-10-22").
- National: `score()` reproduces `compute()` of repeat-prioritisation/src/repeat_prioritisation/national/assets/dashboard.js (eligibility area >= 50 km2 and peat >= 25 km2, `minUnits`, parameters with weight 0 skipped, 5th-95th percentile scaling over eligible KHG with a value, weighted mean of the values a KHG has, ties ordered by the unclipped score then index). Presets: `buildControls()` of the same file. Data: re-peat/reports/national_profile/dashboard_data.json.
- Parity (line "parity"): max |score - skor_risiko| = 2.09e-05 against re-peat/reports/national_profile/operational/profile.csv; ranks identical to `peringkat` for ranks 1-211; below that, 7 swaps between KHG whose Python scores differ by less than 1e-4 (dashboard data hold indicator values to 4 decimals) and differences in the order of the 134 KHG with a score of 0; no other difference. The page itself checks only the top 150. Not quoted in the draft text; it only says the figures use the dashboard's own scoring.
- Team KHG: `F.team()` (re-peat/sites/selected_khg.csv) equals the `team` flags of dashboard_data.json (asserted in `team_codes()`).

### national_dashboard_section.md

- Fire history gives 79 %, this year 12 %, canals 9 % of the summed top-25 score: line "top 25: share of summed score by group".
- Fire history maximum 0.67 (weights 2 + 1 + 1 of a total of 6, meta.weights in dashboard_data.json); 11 KHG at the maximum, all in the top 25: lines "top 25: KHG with fire history at its maximum" (11) and "ranked KHG with fire history at its maximum" (11).
- Canals add most at Barito-Taping (0.167, text 0.17); two of the top 25 without canal contribution: lines "top 25: canal contribution max", "top 25: KHG with no canal contribution".
- Presets, 263 KHG scoreable under Canals; default top 25 kept: History 21, Equal 18, This year 9, Canals 7: table `nat_presets_top25` printed by `numbers()`.
- Team ranks under presets (Pungurbesar-Kapuas 1/3/6/19/1, Balangan-Batangalai 4 and 54 under This year, Kahayan-Sebangau 7 and 75 under Canals, Mempawah-Peniti 21, 10, 6, 3, Saleh-Sugihan 30 -> 23 and 151, Sugihan-Lumpur 31 -> 24 and 193, Buru Mappi-Buru Obaa 138 and 49, Pulau Padang and Pulau Tebing Tinggi between 171 and 269): rank table printed by `numbers()` and line "team KHG best / worst rank across presets".
- Seven of 11 main KHG within the top 158 under every preset (158 = size of the default "high" class, chapter 6.3); the four that are not: Mendahara-Batanghari, Air Hitam Laut-Buntu Kecil, Buru Mappi-Buru Obaa, Pulau Padang: line "team main KHG / within the size of the 'high' class".
- Ranked KHG with a value: 476 for burned share, hotspots, this year's indicators; 287 for repeat burns; 263 for each canal class; 217 ranked KHG with burned share 0; 331 below Pulau Padang (70th percentile): lines "ranked KHG with a value per parameter" and "ranked KHG with burned share 0".
- Percentiles (Saleh-Sugihan 99 burned share and repeat burns, 68 this year; Sugihan-Lumpur 96 burned share, 59 this year; Mempawah-Peniti 98 secondary, tertiary and this year; Pulau Padang 70, Pulau Tebing Tinggi 68 burned share): `nat_team_percentiles()` (values printed in the figure cells; percentile = share of the 476 ranked KHG with a lower value, as the strip plots of dashboard.js `renderStrips`).
- Burned shares (Saleh-Sugihan 42.6 % 2015, 28.3 % 2019, 11.9 % 2023; Kahayan-Sebangau 38.9 % 2015, 17.6 % 2019; Sugihan-Lumpur 37.0 % 2015, at most 5.5 % after; Pungurbesar-Kapuas 16.6 % 2018, 11.0 % 2023, 8.0 % 2026; Mempawah-Peniti and Pulau Bengkalis 6.0 % in 2026, previous maxima 4.3 %): lines "burned series ...", from dashboard_data.json profiles.<id>.burned.
- Monthly hotspots 2026 on peat (Pungurbesar-Kapuas 710 of 1,825 in March; Pulau Bengkalis 389 of 674 in February; Buru Mappi-Buru Obaa 703 of 920 in July; Kahayan-Sebangau 1,333 of 2,538 in September): per-KHG lines, profiles.<id>.now_m (second value = on peat). Totals agree with chapter 6 (2,538 Kahayan-Sebangau, 920 Buru Mappi).
- Deficit: peak in 2015 for 9 of 13 KHG (2019 for Mempawah-Peniti, Pulau Bengkalis, Pulau Padang, Pulau Tebing Tinggi), 403 mm at Sugihan-Lumpur: per-KHG lines "deficit peak", profiles.<id>.deficit (TerraClimate June-October, 2015-2021).
- Dashboard features (bilingual page, eight sliders, presets, filters, 34 profiles, CSV download, address stores the state): dashboard.js (`buildControls`, `hashState`, `renderProfile`) and the current section 6.9.
- Validation tests fire, not the canal weights: chapter 6.4 and 6.10.
