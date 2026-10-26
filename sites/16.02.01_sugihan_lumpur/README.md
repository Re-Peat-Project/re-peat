# Runbook: Sungai Sugihan - Sungai Lumpur (KHG.16.02.01), second real-data test

Run on 2026-10-16 with the same chain as [Kampar-Gaung](../14.02-04-05.01_kampar_gaung/README.md); only the KHG, the rasters and the output folders differ. Everything
is a command or a tracked config in `sites/16.02.01_sugihan_lumpur/`; numbers are generated into `../re-peat/sites/16.02.01_sugihan_lumpur/reports/`. As there, this is a test of the chain, not a
validated ranking: no held-out outcome, default weights, and neraca air fails its own skill check.

KHG: South Sumatra (OKI), 6,347 km2, a flat tidal peat lowland (median DTM height 2.8 m) with a dense canal network. The DTM and peat depth rasters are
valid on only about 54% of their grid.

## Steps

Setup (installs): see [Kampar-Gaung](../14.02-04-05.01_kampar_gaung/README.md#setup). Environment: `REPEAT_DATA` = the workspace `_data`, `REPEAT_KHG` = the workspace `_khg`, `SITMAT_PROCESSED` as there. All inputs, caches and outputs of this KHG are in `$REPEAT_KHG/16.02.01_sugihan_lumpur/` (see its `README.md`); the DEM benchmark of this KHG is in its `01_dem/benchmark/`.

| # | Repo | What | Command | Time |
|---|---|---|---|---|
| 1 | repeat-prioritisation | Clip the national vectors | below | seconds |
| 2 | repeat-prioritisation | Look at the inputs | `python -m subkhg.check_inputs --config ../re-peat/sites/16.02.01_sugihan_lumpur/subkhg.yaml --out ../re-peat/sites/16.02.01_sugihan_lumpur/reports/sugihan_lumpur_inputs.md` | 1 min |
| 3 | repeat-delineation | Delineate sub-KHG, with the sweep | `python -m repeat_delineation --config ../re-peat/sites/16.02.01_sugihan_lumpur/delineate.yaml --sweep 5,20,35,50,70,100,150,200,300` | 3 min |
| 4a | repeat-common | Rain (CHIRPS) and evapotranspiration (WaPOR v3, MOD16) per sub-KHG per dekad from Earth Engine, and WorldCover shares | `python -m repeat_common.fetch_gee_balance --khg 16.02.01 --products chirps,wapor,mod16 --start 2018-01-01 --end 2026-10-01` (needs `EE_PROJECT`; `--workers 9` for parallel years) | about 15 min with 4 workers for 30 sub-KHG (measured, Sugihan-Lumpur); years are cached, a rerun takes about a minute |
| 4b | repeat-neraca | Climatic balance per sub-KHG: `u_wb_mean`, `u_deficit_months`, stability check | `python -m repeat_neraca.balance --inputs $REPEAT_KHG/16.02.01_sugihan_lumpur/03_neraca/inputs --out $REPEAT_KHG/16.02.01_sugihan_lumpur/03_neraca/runs/balance` | seconds |
| 4c | repeat-neraca | SiTMAT station files for the deficit | `python -m repeat_neraca.stations --config ../re-peat/sites/16.02.01_sugihan_lumpur/neraca.yaml` | 1 min |
| 4d | repeat-neraca | KHG deficit `neraca_khg.csv` and the physical model (diagnostic) | `python scripts/run_neraca.py --config ../re-peat/sites/16.02.01_sugihan_lumpur/neraca.yaml --tier 1 --classes primary,secondary,tertiary` | 1 min |
| 5 | repeat-prioritisation | Cloud layers for the ranking (once) | `python -m subkhg.run --config ../re-peat/sites/16.02.01_sugihan_lumpur/subkhg.yaml --fetch-only` | 15 min |
| 6 | repeat-prioritisation | Score and rank | `python -m subkhg.run --config ../re-peat/sites/16.02.01_sugihan_lumpur/subkhg.yaml --skip-fetch` | 3 min |
| 6b | repeat-prioritisation | `subkhg_priority.csv` for repeat-pump is written next to the ranking; to fill `deficit_mm`, set `priority_export.neraca_khg` in `subkhg.yaml` to the `neraca_khg.csv` of step 4d | (step 6 again) | seconds |
| 7 | repeat-neraca | Report and pages | `python -m subkhg.report ...`, `python -m subkhg.dashboard ...` (arguments as in the Kampar-Gaung runbook, with `sugihan_lumpur` configs; outputs `../re-peat/sites/16.02.01_sugihan_lumpur/reports/sugihan_lumpur.md`, `docs/sugihan_lumpur_subkhg_process.html`) | seconds |

Step 1:

```bash
python -m subkhg.prepare_inputs \
  --khg-shp "$REPEAT_DATA/Peat depth and DTM/BatasKHG/KHG_SungaiSugihan_SungaiLumpur/BatasKHG_SungaiSugihan_SungaiLumpur.shp" \
  --khg-id 16.02.01 --out $REPEAT_KHG/16.02.01_sugihan_lumpur/00_inputs \
  --canals "$REPEAT_DATA/kanal_osgm_khg_existing_Indonesia.gpkg" \
  --rivers "$REPEAT_DATA/RBI_sungai.gpkg" --lakes "$REPEAT_DATA/RBI_wadukdanau.gpkg" \
  --blocks "$REPEAT_DATA/infrastruktur_hidrologis_existing_BRGM_Indonesia.gpkg" \
  --blocks-where "Jenis == 'Sekat Kanal' and KETERANGAN == 'REALISASI'"
```

It gave 14,928 canal segments (623 primary, 3,764 secondary, 10,541 tertiary), 2 river segments, 2,861 existing blocks and no lakes.

## Decisions (same as Kampar-Gaung unless noted)

| Setting | Value | Note |
|---|---|---|
| Outlets | primary canals plus rivers; all canals burned | only 2 river segments here, so the 623 primary canals are nearly all of the outlet network |
| `min_area_km2` | `auto`, `merge: adjacent` | chose **96 km2, 28 sub-KHG** (101-1,358 km2, median 161) from 6,219 pieces |
| Peat depth scale | 0.01 (cm) | |
| Sentinel-2 | 60 m, baseline 2019-2021 | |
| Rasters | `DTM_Sungai_Sugihan_Sungai_Lumpur.tif` (100% of the KHG), `Peat_depth_model_KHG_Sungai_Sugihan_Sungai_Lumpur.img` (**75%**, see index) | from `../re-peat/sites/16.02.01_sugihan_lumpur/reports/repeat_data_index.csv` |

Sweep (sub-KHG for minimum area 5 / 20 / 35 / 50 / 70 / 100 / 150 / 200 / 300 km2): adjacent merge 182 / 107 / 93 / 59 / 37 / 27 / 18 / 12 / 6; nearest-unit
merge 161 / 94 / 74 / 34 / 5 / 2 / 1 / 1 / 1. The adjacent merge again gives a smooth count; the largest unit (1,358 km2) is a coastal piece that stays large.

## Results

**Neraca air does not pass** (51 stations in 3 concessions, 2026-04-01 to 2026-10-09). Scored with blocks left out, the model's error (11.3 cm) is worse than the
no-skill baseline (5.7 cm) and the spatial Spearman is 0.23 (peak depth) and -0.07 (days deeper than 40 cm). Things that differ from Kampar-Gaung:
- **The stations are almost identical.** Observed peak depth runs from 51 cm (10th percentile) to 55 cm (90th). Water tables are held near 50 cm across the KHG, so a
  spatial test has nothing to rank. The mean observed curve falls from about 40 to 52 cm over the season; the simulated one stays near 40 cm.
- **A rule dropped a useful term.** With the drainage term the daily error was 6.4 cm (baseline 5.7) and the per-station correlation 0.90; without it 11.3 cm and 0.77.
  The drainage term was dropped because its spatial skill (0.01) was lower than without (0.23), a comparison between two numbers that are both noise at a 4 cm spread. The
  rule (`keep drainage only if RMSE gain >= 2% and spatial skill not worse`) was designed for Kampar-Gaung and should be revisited for KHG with little spatial spread.
- **Covariates:** the strongest is distance to the nearest river (Spearman -0.59 with peak depth; only 2 river segments, so this is mostly distance from the coast and the
  main channels); canal density -0.30, the rest 0.23 or less.
- Unit outputs are again covariates in disguise: storage decline vs mean peat depth -0.98 (table in `../re-peat/sites/16.02.01_sugihan_lumpur/reports/sugihan_lumpur.md`); peak depth and days > 40 cm have no relation to canal proximity (-0.08, -0.04).

**Sentinel-1** ([report](reports/sugihan_lumpur_sentinel1.md)): within a station, a brighter-than-usual VV scene falls on a shallower-than-usual water table (median Spearman -0.62,
98% of stations negative; Kampar-Gaung -0.38, 84%). Across stations there is no signal (0.17 or less), which is expected when the stations differ by 4 cm. Concession explains only
16% of the variance here (64% in Kampar-Gaung). So radar tracks day-to-day wetness change in both KHG and ranks locations in neither beyond the concession.

**Ranking.** 28 sub-KHG; the need score and the rank-sum agree weakly (Spearman 0.15, 2 of the top 6 shared). Sub-KHG 16.02.01_S21 (423 km2) is first by both. Only 12 of
28 units contain a station, so the water-table indicators are reported but not scored. Treat it as a demonstration that the pipeline runs, not as a finding.

**Things found in the inputs:**
1. 20% of the peat depth raster's valid pixels equal 50 cm (a floor); 4 of 26 sub-KHG with peat data have a mean at the floor. Peat depth covers 75% of the KHG.
2. Block spacing sits at the 2,000 m cap for 4 of 28 sub-KHG: the DTM is so flat that canal slope is below the 0.0002 where the spacing rule saturates.
3. Peat depth is strongly correlated with the water-distance and lift feasibility indicators (rho 0.82 and -0.83), and canal density with reach (0.89).
4. WorldCover tree cover has a median of 0.42 here (0.70 in Kampar-Gaung), with many crop pixels; the "intact forest" indicator is more usable here but still cannot tell plantation from forest.

## Not done

Same list as Kampar-Gaung: no outcome check of the ranking, weights and the 0.8 weight on need are defaults, concession polygons and water-level targets are not available.
