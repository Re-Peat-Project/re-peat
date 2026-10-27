# 18 Full run: every selected KHG, once per DEM

Plan of 2026-10-27 for running the whole RE-PEAT chain (DEM, delineation, neraca air, prioritisation, interventions) on the
selected KHG. Readiness is checked by `python tools/khg_pipeline.py status`, which writes `$REPEAT_KHG/pipeline_status.csv`.

## Decisions

| Question | Decision |
|---|---|
| Where the DEM varies | The whole chain, once per DEM: each DEM gets its own sub-KHG units, neraca, prioritisation and sekat. |
| DeltaDTM and DEMNAS | After the repeat-dem correction (ICESat-2 class offsets + smoothing, the parameters of the benchmark runs), not the raw clips. |
| KHG | All 14 KHG folders: the 12 selected (Cawang-Lalang still unresolved) plus Sugihan-Lumpur and Kampar-Gaung. |
| Pulau Padang | No LiDAR variant (its LiDAR is a 2 m DTM). |
| Older outputs | The single-DEM outputs of Sugihan-Lumpur and Kampar-Gaung directly in `<step>/` stay where they are. |
| A DEM variant runs | when its DEM covers at least 90 % of the KHG (the pump's stage 1 threshold). |

Folders: `repeat_common.khg.step_dir(khg, step, dem)` gives `<khg>/<step>/<dem>/` for 02_delineation, 03_neraca, 04_prioritisation
and 05_pump; `<dem>` is `lidar`, `deltadtm` or `demnas`. Corrected DEMs go to `01_dem/processed/<dem>/` (the benchmark's
`01_dem/benchmark/04_processed/<dem>/` is used where it exists, same method).

## What runs (33 variants)

| KHG | LiDAR (cover) | DeltaDTM | DEMNAS | Peat depth |
|---|---|---|---|---|
| 14.02-04-05.01 Kampar-Gaung | RIAU25m (99.8 %) | yes | yes | yes |
| 14.03.02 Pulau Bengkalis | none | yes | yes | yes |
| 14.10.01 Pulau Padang | left out (2 m) | yes | yes | yes |
| 14.10.03 Pulau Tebing Tinggi | none | yes | yes | to check (Siak-Kampar raster by footprint) |
| 15-16.01 Air Hitam Laut-Buntu Kecil | Muba25 (100 %) | yes | yes | yes |
| 15.05-07-10.01 Mendahara-Batanghari | Jambi25m (100 %) | yes (processed) | yes (processed) | yes |
| 16.02-07.01 Saleh-Sugihan | Sugihan-Saleh 20 m, UTM 48S copy (98.3 %) | yes | yes | yes |
| 16.02.01 Sugihan-Lumpur | OKI25 (100 %) | yes (processed) | yes (processed) | yes |
| 61.02-08.01 Mempawah-Peniti | none | yes | yes | yes |
| 61.12-71.01 Pungurbesar-Kapuas | none | yes | yes | yes |
| 62.03-04.01 Kapuas-Barito | none | yes | yes | none (weight 0) |
| 62.11-14.02 Kahayan-Sebangau | none | yes | yes | none (weight 0) |
| 63.07-08-11.01 Balangan-Batangalai | none | yes (97.9 %) | yes | yes |
| 91.18-17.01 Buru Mappi-Buru Obaa | none | yes | yes | none (weight 0) |

## Steps

Once per KHG:

1. **Inputs** (`00_inputs/`): `repeat-subkhg-prepare` with the KHG boundary from `batas_khg_indonesia.gpkg` by registry code,
   the national canals, RBI rivers and lakes, and existing sekat (REALISASI). Missing at 12 KHG.
2. **ICESat-2** (`_data/icesat2/`): `python -m repeat_common.fetch_icesat2 --khg <name>`, one KHG at a time (SlideRule limits).
   Present at 2 KHG.
3. **WorldCover and canopy tiles** for the DEM correction: present only for the two benchmark KHG (8 canopy tiles).
4. **KHG deficit** (`03_neraca/runs/deficit/`): SiTMAT stations and ERA5; does not use the DEM.
5. **Sentinel-2, WorldCover, JRC** rasters of the prioritisation (`cache/`), and the NDMI raster the pump reads.

Once per KHG and DEM:

6. **DEM correction** (DeltaDTM, DEMNAS): `tiled_dtm.py` with the benchmark parameters into `01_dem/processed/<dem>/`.
7. **Delineation** (`02_delineation/<dem>/`): config generated from the Sugihan-Lumpur one (primary and secondary canals as
   outlets, merge adjacent, minimum area auto), canal class field detected per KHG.
8. **Neraca air** (`03_neraca/<dem>/`): `fetch_gee_balance --khg <code> --dem <dem>` (cache keyed by the unit set), balance,
   `neraca_map`.
9. **Prioritisation** (`04_prioritisation/<dem>/`): config generated per variant (units, DEM, peat depth when found).
10. **Interventions** (`05_pump/<dem>/`): run config from the KHG folder with `inputs.dtm.source` = the variant, stages 1-12,
    HTML report and layouts.

Last: a comparison table over every KHG and DEM (sekat kept, water held against the deficit, interventions, budget).

## Built (2026-10-27)

- The runner: `tools/khg_pipeline.py` (setup, init, status, plan, run) with `pipeline.yaml` and one `sites/<folder>/khg.yaml` per KHG;
  how to use it, here or on another machine: [19-running-the-pipeline.md](19-running-the-pipeline.md).
- `repeat_common.khg.DEMS`, `step_dir` (the variant folders).
- `fetch_gee_balance`: cache files carry a fingerprint of the unit set, `--dem` selects a variant. Before this, two unit sets of
  one KHG would have shared cached years.
- `repeat_neraca.batch --dem`, `maps.write_map(kf, dem)`; the pump's `khgsetup.setup_from_khg(dem=, dtm=)` and
  `khg_run_config.py --dem --dtm`.
- DEM correction templates per product (`tools/pipeline/templates/`), copied from the benchmark runs; land cover and canopy
  height streamed.
- Pilot: Mendahara-Batanghari, every step and DEM (times in `$REPEAT_KHG/pipeline_runs.csv`).

## Pilot: Mendahara-Batanghari (2026-10-27)

Every step and DEM, from `python tools/khg_pipeline.py run --khg 15.05-07-10.01`; the DEM corrections and ICESat-2 points already
existed from the benchmark. Results from `python tools/khg_pipeline.py compare` (`$REPEAT_KHG/pipeline_compare.csv`):

| | LiDAR (Jambi 25 m) | DeltaDTM (corrected) | DEMNAS (corrected) |
|---|---|---|---|
| Sub-KHG units | 29 | 29 | 29 |
| Sekat, head rule / kept at 90 % | 134 / 73 | 139 / 62 | 385 / 120 |
| Water held / deficit of the 3 selected sub-KHG | 12.0 % | 13.7 % | 19.2 % |
| Interventions: close canals, revegetation, sekat + water, sekat + wells, sekat | 17, 1, 8, 2, 1 | 15, 6, 7, 0, 1 | 16, 4, 8, 0, 1 |
| Budget, billion Rp (low / central / high) | 9.0 / 14.1 / 14.2 | 50.0 / 76.8 / 89.9 | 85.6 / 130.7 / 146.7 |

The units differ between DEMs (each variant delineates its own), so the selected sub-KHG, their deficit and their classes differ;
most of the budget difference is revegetation (1 unit with LiDAR, 6 with DeltaDTM). DEMNAS again places far more head-rule sekat.

Time per step at Mendahara-Batanghari (2,014 km2), from `$REPEAT_KHG/pipeline_runs.csv`:

| Step | Time |
|---|---|
| inputs | 7 s |
| delineation | 75-90 s per DEM |
| deficit | 17 min (most of it the first ERA5 download; cached afterwards) |
| neraca | 10-11 min per DEM (Earth Engine, 4 workers) |
| prioritisation | 26 min for the first DEM (Sentinel-2, 9 years), about 1 min for the others (cache) |
| pump | 2-2.5 min per DEM |
| layouts | 10-20 s per DEM |

About 1.5 hours for this KHG without the DEM correction and ICESat-2 fetch, which the other 12 KHG still need (not timed yet).
Larger KHG take longer (Kapuas-Barito and Kahayan-Sebangau are 2.2-2.8 times this area). The first pass failed at the
prioritisation because `REPEAT_WORK` was not set; it is now in `pipeline.yaml` (`environment`), and the rerun resumed from there.

## Status (2026-10-28)

Full chain, all DEMs: Mendahara-Batanghari, Saleh-Sugihan, Kampar-Gaung. The run was stopped there; the other 11 KHG are left
for the team to run (`python tools/khg_pipeline.py run --khg <code>`). Sugihan-Lumpur has its deficit and both DEM corrections,
and its earlier single-DEM outputs in `<step>/`, but no per-DEM delineation onwards yet.

Every one of the 14 KHG folders has `inputs`, `dem_inputs`, `icesat2` and `local_inputs` done, so each folder runs without `_data`
([19-running-the-pipeline.md](19-running-the-pipeline.md)). `00_inputs/` is 16 to 182 MB per KHG. No peat-depth model exists for
Kapuas-Barito, Kahayan-Sebangau and Buru Mappi-Buru Obaa (`peat_depth: null`); no SiTMAT station lies within 5 km of
Mempawah-Peniti, Balangan-Batangalai and Buru Mappi-Buru Obaa, so their deficit step will write `NOT_AVAILABLE.txt`.

From `python tools/khg_pipeline.py compare`:

| KHG, DEM | Units | Sekat kept / head rule | Held / deficit | Budget, bn Rp (central) |
|---|---|---|---|---|
| Kampar-Gaung, LiDAR (Riau 25 m) | 28 | 27 / 60 | 47.8 % | 1.5 |
| Kampar-Gaung, DeltaDTM | 27 | 63 / 138 | 105.1 % | 6.6 |
| Kampar-Gaung, DEMNAS | 29 | 48 / 401 | 144.1 % | 38.5 |
| Saleh-Sugihan, LiDAR (20 m) | 29 | 31 / 84 | no deficit (0 SiTMAT stations) | 23.3 |
| Saleh-Sugihan, DeltaDTM | 26 | 12 / 34 | no deficit | 24.6 |
| Saleh-Sugihan, DEMNAS | 27 | 40 / 137 | no deficit | 31.1 |

At Kampar-Gaung the water held by the kept sekat exceeds the deficit of the selected sub-KHG with DeltaDTM and DEMNAS; the deficit
(5.0 to 7.5 million m3) is far smaller than Mendahara-Batanghari's (26 to 38 million m3). Kampar-Gaung step times: ICESat-2 14 min,
DEM correction 31 min (DeltaDTM) and 39 min (DEMNAS), delineation under 3 min, neraca 17 to 27 min, prioritisation 3 to 4 min,
pump 3 to 7 min per DEM.

Fixed during this run: the ICESat-2 file of a KHG with a two-word name (`atl08_PulauBengkalis_...`) was not matched by the runner,
and `fetch_icesat2` and `repeat_common.gee` did not find names written with a double space in the boundary file
("KHG Sungai Pungurbesar -  Sungai Kapuas").

## Notes

- Kampar-Gaung's earlier neraca and sub-KHG used the id `71`; new runs use the registry code.
- Peat depth is found by the raster footprint covering the KHG; a match is checked for valid pixels inside the KHG before use.
- DeltaDTM covers land below about 10 m only; every KHG here is at least 97.9 % covered.
