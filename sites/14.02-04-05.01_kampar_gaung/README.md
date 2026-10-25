# Runbook: Sungai Kampar - Sungai Gaung (KHG 71), first real-data test

Run on 2026-10-16. Everything below is reproducible from the repo: each step is a command, each setting is in a tracked
config in `sites/14.02-04-05.01_kampar_gaung/`, and the numbers are generated into `../re-peat/sites/14.02-04-05.01_kampar_gaung/reports/`. Nothing depends on files outside
the repo except your data folders (see "Setup").

**What this run is:** a test of the whole chain (inputs, delineation, neraca air, ranking) on one large KHG (7,111 km2),
with coarse settings to keep it cheap (Sentinel-2 at 60 m, baseline 2019-2021). **What it is not:** a validated ranking.
There is no outcome to test the ranking against (no held-out year was set), the indicator weights are defaults nobody
has agreed, and the neraca air module failed its own skill check (below).

## Setup

All repositories are cloned side by side (`re-peat`, `repeat-common`, `repeat-delineation`, `repeat-neraca`, `repeat-prioritisation` = the `khg-prioritisation-module` checkout until it is renamed, ...). Each command runs from the repository named in the `Repo` column, and the configs here are referenced as `../re-peat/sites/14.02-04-05.01_kampar_gaung/...`.

```bash
pip install -e ../repeat-common ../repeat-delineation "../repeat-neraca[neraca,experiments]" -r requirements.txt   # once, in one environment
export REPEAT_DATA="C:/.../_repeat-project/_data"                   # the workspace data folder
export REPEAT_KHG="C:/.../_repeat-project/_khg"                     # per-KHG work folders: inputs, caches, outputs (not tracked)
export SITMAT_PROCESSED="C:/.../sitmat-extract/sitmat_out/processed"
python -m tests.test_ranksum                                        # in repeat-prioritisation
```

The cache (`$REPEAT_KHG/14.02-04-05.01_kampar_gaung/cache/71/`) is keyed by file name, not by the settings that made a layer. If you change a setting that changes a
layer (for example `sources.ndmi.res_m`), delete the old layer files first, or they are reused.

Configs read `${REPEAT_KHG}`, `${REPEAT_DATA}` and `${SITMAT_PROCESSED}`; a missing variable stops with a message. All inputs, caches and outputs of this KHG are in `$REPEAT_KHG/14.02-04-05.01_kampar_gaung/` (see its `README.md`). Generated reports are in `reports/` next to this file.

## Steps

| # | Repo | What | Command | Time |
|---|---|---|---|---|
| 0 | repeat-prioritisation | Which DTM and peat depth rasters cover which KHG (names do not match) | `python scripts/index_repeat_data.py --root "$REPEAT_DATA/Peat depth and DTM" --out ../re-peat/sites/14.02-04-05.01_kampar_gaung/reports/repeat_data_index.csv` | 1 min |
| 1 | repeat-prioritisation | Clip the national vectors to the KHG | see below | seconds |
| 2 | repeat-prioritisation | Look at the inputs | `python -m subkhg.check_inputs --config ../re-peat/sites/14.02-04-05.01_kampar_gaung/subkhg.yaml --out ../re-peat/sites/14.02-04-05.01_kampar_gaung/reports/kampar_gaung_inputs.md` | 1 min |
| 3 | repeat-delineation | Delineate sub-KHG | `python -m repeat_delineation --config ../re-peat/sites/14.02-04-05.01_kampar_gaung/delineate.yaml` | 1.5 min |
| 4a | repeat-neraca | ERA5 forcing, every window (once) | `python -m repeat_neraca.bucket.run --config ../re-peat/sites/14.02-04-05.01_kampar_gaung/neraca_experiments.yaml --forcing-only` | 11-33 min per window, 4 windows |
| 4b | repeat-neraca | Neraca air skill on SiTMAT stations | `python -m repeat_neraca.bucket.run --config ../re-peat/sites/14.02-04-05.01_kampar_gaung/neraca_experiments.yaml --calibrate-only` | 30 s |
| 4c | repeat-neraca | Neraca air indicators per sub-KHG | `python -m repeat_neraca.bucket.run --config ../re-peat/sites/14.02-04-05.01_kampar_gaung/neraca_experiments.yaml` | 30 s |
| 4d | repeat-neraca | What explains the station water tables | `python -m repeat_neraca.bucket.covariates --config ../re-peat/sites/14.02-04-05.01_kampar_gaung/neraca_experiments.yaml --ndvi-year 2019` | 1 min |
| 4e | repeat-neraca | Sentinel-1 radar against the stations | `python -m repeat_neraca.bucket.sentinel1 --config ../re-peat/sites/14.02-04-05.01_kampar_gaung/neraca_experiments.yaml` | 5 min |
| 4f | repeat-neraca | Physical neraca air (the model that replaces the bucket) and the KHG deficit `neraca_khg.csv` | `python scripts/run_neraca.py --config ../re-peat/sites/14.02-04-05.01_kampar_gaung/neraca.yaml --tier 1 --classes primary,secondary,tertiary` | 1 min |
| 5 | repeat-prioritisation | Cloud layers for the ranking (once) | `python -m subkhg.run --config ../re-peat/sites/14.02-04-05.01_kampar_gaung/subkhg.yaml --fetch-only` | 37 min |
| 6 | repeat-prioritisation | Score and rank | `python -m subkhg.run --config ../re-peat/sites/14.02-04-05.01_kampar_gaung/subkhg.yaml --skip-fetch` | 3 min |
| 6b | repeat-prioritisation | `subkhg_priority.csv` for repeat-pump is written next to the ranking; to fill `deficit_mm`, set `priority_export.neraca_khg` in `subkhg.yaml` to the `neraca_khg.csv` of step 4f | (step 6 again) | seconds |
| 7 | repeat-prioritisation | Report | `python -m subkhg.report --subkhg-config ../re-peat/sites/14.02-04-05.01_kampar_gaung/subkhg.yaml --neraca-config ../re-peat/sites/14.02-04-05.01_kampar_gaung/neraca_experiments.yaml --out ../re-peat/sites/14.02-04-05.01_kampar_gaung/reports/kampar_gaung.md` | seconds |

Step 1:

```bash
python -m subkhg.prepare_inputs \
  --khg-shp "$REPEAT_DATA/Peat depth and DTM/BatasKHG/KHG_SungaiKampar-SungaiGaung/KHG_SungaiKampar-SungaiGaung.shp" \
  --khg-id 71 --out $REPEAT_KHG/14.02-04-05.01_kampar_gaung/00_inputs \
  --canals "$REPEAT_DATA/kanal_osgm_khg_existing_Indonesia.gpkg" \
  --rivers "$REPEAT_DATA/RBI_sungai.gpkg" --lakes "$REPEAT_DATA/RBI_wadukdanau.gpkg" \
  --blocks "$REPEAT_DATA/infrastruktur_hidrologis_existing_BRGM_Indonesia.gpkg" \
  --blocks-where "Jenis == 'Sekat Kanal' and KETERANGAN == 'REALISASI'"
```

It gave 11,733 canal segments, 16 river segments, 2,884 existing blocks and no lakes (inside the KHG plus a 2 km buffer).
The lakes file is not used by the configs.

## Decisions and why

| # | Decision | Reason and evidence | Set in |
|---|---|---|---|
| 1 | Only **primary** canals (plus rivers) are sub-KHG outlets; all canals are burned into the DTM | The canal file has three classes in `KET_KANAL` (primary 118, secondary 859, tertiary 10,756 segments in the clipped file). Tertiary canals are the plantation drainage grid; as outlets they would cut every block into its own unit (not run). The class names are compared in lower case, so the value is `Kanal Primer`. | `delineate.yaml` |
| 2 | `min_area_km2: auto`, `merge: adjacent` | The catchments of the primary canals and rivers give **5,581 pieces** at 30 m. Small pieces are merged, smallest first, into the neighbour they share the longest divide with, so the count falls smoothly with the minimum area: 5 / 20 / 35 / 50 / 70 / 100 / 150 / 200 / 300 km2 give **247 / 129 / 107 / 73 / 42 / 35 / 21 / 13 / 9** sub-KHG. The earlier merge into the nearest unit collapsed it (186 / 99 / 79 / 42 / 5 / 2 / 2 / 1 / 1). `auto` steps the minimum up 10% from 5 km2 until at most `target_count[1]` = 30 units remain: **127.7 km2, 26 sub-KHG** (132-885 km2, median 202). Reproduce: `python -m repeat_delineation --config ../re-peat/sites/14.02-04-05.01_kampar_gaung/delineate.yaml --sweep 5,20,35,50,70,100,150,200,300` (writes `delineation_report.json` and `delineation_sweep.json`). | `delineate.yaml` |
| 3 | `peat_depth_scale: 0.01` | The data owner confirmed the raster is in centimetres (values 35-1,393, median 193). | `neraca.yaml`, `subkhg.yaml` |
| 4 | Canal blocks for metrik IPG: primary and secondary canals only | Tertiary canals are not part of the block-spacing rule in the Kahayan-Sebangau parameters used here. Assumption, not checked with the team. | `subkhg.yaml` |
| 5 | Existing blocks = `Sekat Kanal` and `REALISASI` | The BRGM file also holds spillways, water gates and planned (`RENCANA`) blocks. Only built canal blocks count as existing. | step 1 |
| 6 | Baseline 2019-2021 | Three years that include a dry year (2019, El Nino) and two wetter ones. `years.baseline` is a range, so 2019-2021 includes 2020. A test choice, not a recommendation. | `subkhg.yaml`, `neraca.yaml` |
| 7 | Sentinel-2 at 60 m | At 20 m a year over 7,111 km2 is heavy. The units are 130+ km2, so 60 m is enough for a test. | `subkhg.yaml` |
| 8 | Water-table stations are a **current-state** indicator (2026-04-01 to 2026-10-15) | SiTMAT only holds 2026; baseline years cannot use it. 17 of the 26 sub-KHG have at least one station. | `subkhg.yaml` |
| 9 | ERA5 rain and dry-spell fetch is off in the ranking run | Those indicators have weight 0 in the need score (they are constant inside a KHG), and the fetch costs about 4 minutes per KHG-year. | sub-KHG preset |
| 10 | Neraca air outputs get **no weight** in the need score | They failed the skill check (below). They stay available to the rank-sum method, with `neraca_skill_ok = 0` in the table. | not listed in `indicators:` |
| 11 | `ranksum_columns: {u_deficit_months: u_deficit_months_dry}` | The neraca air module counts 5 dry months, not 12; it must not replace the 12-month column. | `subkhg.yaml` |
| 12 | `scoring.method: need` | The default. The rank-sum is computed alongside; both ranks are in every output. | default |

### The neraca air model (details in `repeat-neraca/docs/bucket_experiments_README.md`; run with `pip install -e ../repeat-neraca[experiments]`)

| Choice | Value | Reason |
|---|---|---|
| Simulated months | April to October; indicators over June to October | April is spin-up; SiTMAT starts on 1 April. |
| Days | local days (WIB, UTC+7) | Hourly ERA5 is summed to local days. |
| Calibration window | 2026-04-01 to 2026-10-09 | ERA5 is complete only to about 2026-10-09 (checked with `scripts/probe_cloud_sources.py coverage`). |
| Stations | concession kind, flagged readings dropped, 50% coverage: 86 inside the KHG | `common/tma.py` defaults. |
| Fit | grid search of Sy, drainage k and starting depth z0, leave-one-spatial-block-out (4 blocks) | Parameters are fitted on some stations and scored on others. |
| Sy grid up to 3.0 | wider than physical on purpose | To see whether the fit hits the edge: it did, on all three parameters. |
| No peat-depth cap on the water table | the table can fall into the mineral soil | Stations on 50 cm of peat reach 100+ cm. |
| Drainage term kept only if RMSE improves by 2% **and** spatial skill does not drop | | A constant offset can cut RMSE without telling places apart. |
| Verdict: usable only with spatial Spearman of at least 0.3 and RMSE below the no-skill baseline | `neraca.min_spatial_skill` | Written to `neraca_report.json`, to the log and to `neraca_skill_ok`. |

## Results

Full numbers: [reports/kampar_gaung.md](reports/kampar_gaung.md), inputs: [reports/kampar_gaung_inputs.md](reports/kampar_gaung_inputs.md).

**Neraca air does not pass.** On the 86 stations, scored on blocks left out of the fit:
the daily series correlate moderately (median r 0.63 with the drainage term), but across stations the spatial skill is nil
(Spearman -0.03 for peak depth, -0.02 for days deeper than 40 cm) and the out-of-fold RMSE (16.5 cm) is worse than the
no-skill baseline (15.3 cm). The fit ends on the edge of every grid (Sy 3.0, k 4.0, z0 40): the best bucket is nearly a flat
line near 40 cm. The observed mean water table sits at about 40 cm (the regulatory limit) from April to August, then
falls to 60-70 cm in September: these concession water tables look managed (weirs), not driven by rain minus evaporation.
No simple covariate explains which stations are deepest: every Spearman is 0.34 or less (best: distance to the KHG edge,
distance to a canal, elevation, peat depth). Consequence: the outputs are rescaled covariates. `u_storage_decline_pct`
has a Spearman of -0.91 with mean peat depth across the 26 sub-KHG, and `u_wt_peak_cm` / `u_wt_days_gt40` have 0.82 / 0.68 with canal
proximity (the drainage term). They were given no weight.

**Ranking.** 26 sub-KHG; the need score and the rank-sum agree moderately (Spearman 0.67, 3 of the top 5 shared).
Sub-KHG 71_S26 (281 km2) is first by both. Take this as a demonstration that the pipeline runs on real inputs, not as a
finding about where to intervene.

**Things found in the inputs** (each affects how far the numbers can be trusted):

1. **The peat depth raster has a floor at 50 cm.** 37% of its valid pixels are exactly 50.0 cm. 13 of the 25 sub-KHG with peat data
   have a mean depth at that floor, and 37 of the 86 stations sit on it. Thin peat is therefore not resolved.
2. **Block spacing for 11 of 25 sub-KHG sits at the 2,000 m cap.** The median canal slope from the DTM is 0.00031; below 0.0002
   the rule dA / slope is cut at the maximum spacing, so "blocks needed" there is canal length divided by 2,000 m, not a
   terrain result. Existing blocks (2,754 counted) exceed those needed (1,759) in total.
3. **`i_forest` is high (median 0.70) because WorldCover "tree cover" includes plantations.** In a concession landscape the
   indicator "intact forest needs less" cannot tell natural forest from acacia. Not tested against another land cover.
4. **`f_water_dist` is 2-28 km (median 13 km)** because dry-season water is only the 16 river segments and the JRC layer; canals
   are not counted as water. `f_lift` is strongly correlated with peat depth (-0.91) and `f_reach` with canal density (0.94).
5. **SiTMAT covers one season and sits mostly in concessions:** 17 of the 26 sub-KHG have a station.
6. Sub-KHG of 132-885 km2 are large; the merge is by longest shared divide, not by a hydrological hierarchy (sub-basin levels). Not compared with an official sub-KHG layout (none exists for this KHG).

## Not done

- No outcome check of the ranking (no held-out burned area or hotspots; `years.validation` is empty).
- Weights and the 0.8 weight on need are defaults.
- Sentinel-2 only at 60 m, and only 2019-2021; the user's burned-area and hotspot files (`_converted`) were not used (cloud MODIS and FIRMS were).
- Neraca air needs rainfall and evaporation finer than 25 km, and information on water management (weirs, canal blocks, concession practice), before it can say which sub-KHG dry out more.
- The measure recommendation (sekat kanal, sumur bor, pompa) is not built.
