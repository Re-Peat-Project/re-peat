# 11 Data contracts between modules

Status: **draft 2026-10-20; D1 to D3 settled the same day**, written before splitting the code into separate repositories. The modules exchange files only; this page says which files, with which columns, CRS and sign conventions. A module may change anything inside itself as long as it keeps writing and reading these files. When a contract changes, change this page first.

Lines marked **Decision** are not settled in the code today. They are listed again at the end.

## The modules and what they hand over

```
repeat-sitmat ──► tma/ ─────────────────────────────┐
repeat-dem ─────► dtm_smooth.tif ─┬─► repeat-delineation ─► subkhg_units.gpkg ─┬─► repeat-neraca ─► neraca_unit.csv ─┐
repeat-common (open data, read in-process: ERA5, Sentinel, WorldCover, ...)    │                                      │
                                                                               └─► repeat-prioritisation ◄────────────┘
                                                                                        │
                                                          unit_prioritas.gpkg/csv, subkhg_priority.csv
                                                                                        ▼
                                                                                  repeat-pump
```

`repeat-common` is a library, not a stage: modules import it, they do not exchange files with it.

## Conventions for every file

| Item | Rule |
|---|---|
| Unit identifier | `unit_id`, text, unique across all KHG of a run, form `<khg_id>_S<nn>` (e.g. `KHG01_S03`). Always together with `khg_id`. **Decision D1:** `repeat-pump` still reads `subkhg_id`; it should read `unit_id` and accept `subkhg_id` as an alias. |
| Vector CRS | Files handed between modules are EPSG:4326, as the delineation writes them today. A module projects internally. |
| Raster CRS | The KHG's UTM zone, metres. |
| Vertical datum | The DEM's datum (DEMNAS: check the metadata, commonly EGM2008). Stated in the sidecar of `dtm_smooth.tif`. |
| Water table depth | Metres or centimetres **below** the surface, positive down, in every file of ours. SiTMAT's raw `water_level_cm` is negative below the surface; only `repeat-common` (`tma`) converts it. |
| Units | SI. Rain and evaporation in mm/day. Areas in km2 in tables, m2 inside code. |
| Indicator columns | Prefix says the role: `u_` need, `i_` stakes, `f_` feasibility, `v_` validation only. Anything else is metadata and is never scored. |
| Missing | Empty cell or NaN. Never 0, never -9999. A module that needs a value stops with a message naming the key. |

## C1. Water table observations (`repeat-sitmat` to everyone)

Folder `sitmat_out/processed/` as written by the extractor.

| File | Columns |
|---|---|
| `stations.csv` | `kind` (concession or community), `station_id`, `name`, `company_code`, `company_name`, `lon`, `lat`, `provinsi`, `kabupaten`, `kecamatan` |
| `daily_long.csv` | `kind`, `station_id`, `date`, `water_level_cm`, `water_level_min_cm`, `water_level_max_cm`, `soil_moisture_pct`, `rain_fall_mm`, `status`, `source`, `flag` |
| `stations_geo.csv` | optional, adds the spatial join to KHG and administrative areas |

`water_level_cm` is negative below the surface. `flag` marks range and spike readings. Readers use `kind = concession`, drop flagged readings and keep stations with at least 50% coverage of the period (`common/tma.py` today). The canonical in-memory table is `station_id, date, depth_m, lon, lat` with depth positive down.

## C2. Ground surface (`repeat-dem` to delineation, neraca, prioritisation, pump)

| File | Content |
|---|---|
| `dtm_smooth.tif` | Smoothed ground surface, UTM, metres, float32, nodata set in the file |
| `dtm_smooth.json` | Sidecar: source DEM, vertical datum, correction settings, validation RMSE at held-out ground points, date |

The sidecar is **new**: today the RMSE and datum are only in the run report. Consumers use it to refuse or warn (the pump module refuses a DSM). Lidar or an alternative open DEM replaces the file with the same name and sidecar; nothing downstream changes.

## C3. Sub-KHG units (`repeat-delineation` to neraca, prioritisation, pump)

`subkhg_units.gpkg`, EPSG:4326, columns `khg_id`, `unit_id`, `geometry`. Written together with `delineation_report.json` (settings, inputs, pieces before and after merging, areas). Edited polygons keep `khg_id` and `unit_id`. Area is not stored; consumers compute it in an equal-area or UTM projection.

## C4. Rain and evaporation forcing (`repeat-common` to `repeat-neraca`)

Two routes, same table. **Direct (default, D2):** `repeat-neraca` reads ERA5 and WaPOR through `repeat_common.forcing` (`khg_table`), using the cache folder of the window first (`forcing_direct:` block in the site config, `run_neraca.py --forcing direct`). **File (offline fallback):** `run_neraca.py --forcing file` reads `forcing_daily.csv`, written by the bucket experiments before they were retired (2026-10-26); the files on disk still serve. Both gave identical numbers (checked byte for byte on both sites). The station files (`stations.csv`, `stations_daily.csv`) are written by `python -m repeat_neraca.stations` from the SiTMAT extract (checked byte-identical to the earlier files on both sites, 2026-10-26).

Per sub-KHG rain and evapotranspiration for the climatic balance come from Earth Engine through `python -m repeat_common.fetch_gee_balance` (CHIRPS daily, WaPOR v3 AETI dekadal, MOD16A2GF; reduced on each product's own grid): `03_neraca/inputs/balance_<product>_dekad.csv` with `unit_id, start, end, days, mm, n_px, time_cov`, and `units_landcover.csv` (ESA WorldCover v200 class shares).

| File | Columns |
|---|---|
| `forcing_daily.csv` | `date`, `window`, `P_era5_mm`, `E_era5_mm`, `E_wapor_mm` (KHG mean, local days UTC+7, mm/day) |
| `stations.csv`, `stations_daily.csv` | `station_id, lon, lat, concession` and `date, station_id, depth_cm` (positive down) for the calibration window |

## C5. Neraca air results (`repeat-neraca` to prioritisation and pump)

Two outputs with different spatial meaning, and the contract must not blur them.

| File | Level | Columns |
|---|---|---|
| `neraca_khg.csv` | KHG, one row | `khg_id`, `period_start`, `period_end`, `n_days`, `valid_day_share`, `n_stations`, `area_km2`, `sy`, `net_balance_mm`, `obs_depth_start_cm`, `obs_depth_end_cm`, `obs_change_cm`, `storage_change_mm`, `deficit_mm`, `deficit_mm_low`, `deficit_mm_high`, `deficit_m3`, `deficit_months` (months of the window with negative P - E; a partial last month counts), `evaporation_source`, `e_wapor_covers_period`, `method` |
| `neraca_balance_unit.csv` (`03_neraca/runs/balance/`) | sub-KHG | `unit_id`, `u_wb_mean` (mm/month), `u_deficit_months` (per year), `wb_year_sd_mm`, `p_minus_et_mean_mm`, `interception_share`, `n_px_<product>`, `wb_mean_<et>`, `deficit_months_<et>`, `n_years`, `balance_stable_ok` |
| `neraca_unit.csv` (physical model, tier 2) | sub-KHG | `unit_id`, `u_wt_mean_cm`, `u_wt_peak_cm`, `u_wt_days_gt40`, `neraca_skill_ok` |

The sub-KHG output is the climatic balance of `repeat_neraca.balance` (method: `repeat-neraca/docs/neraca-air-method.md`). The prioritisation merges `neraca_balance_unit.csv` through `extra_indicators`: `u_wb_mean` and `u_deficit_months` replace its own TerraClimate columns and fill the water-balance slots of the rank-sum (`ranksum_columns: {u_wb_daily_mean: u_wb_mean}`). `common.pipeline.gate_balance` leaves them empty where `balance_stable_ok` is 0 (the order of sub-KHG changes between years or between ET sources). In the need score they keep weight 0 until the team sets one. The physical model's `neraca_unit.csv` carries no ranking information (every sub-KHG follows the same curve) and is not merged. The KHG-level `deficit_mm` is the useful number: it sizes the water the system must supply, and is what the pump module needs. It is a mass balance over a dry-season window with a constant Sy of 0.15 (band 0.10 to 0.20) and ERA5 evaporation as the central value (`deficit_mm_low` and `deficit_mm_high` give the band); the definition and the agreed choices are in `repeat-neraca/docs/neraca-air.md`. There is no skill flag in `neraca_khg.csv`: `n_stations`, `valid_day_share` and `e_wapor_covers_period` are the evidence.

## C6. Prioritisation results (`repeat-prioritisation` to pump and the dashboard)

| File | Content |
|---|---|
| `unit_prioritas.gpkg` / `.csv` | one row per unit: `khg_id`, `unit_id`, indicator columns, group scores, `peringkat` (rank, 1 = most need), `kelas` (tertile class), `cakupan_*` coverage |
| `laporan.json` | settings, indicator coverage, sensitivity and validation |
| `subkhg_priority.csv` | **new**, what `repeat-pump` reads: `unit_id`, `priority_rank` (= `peringkat`), `deficit_mm`, `design_period_days` |

`repeat-prioritisation` writes `subkhg_priority.csv` next to the ranking. `priority_rank` comes straight from `peringkat`. `deficit_mm` comes from `neraca_khg.csv` (the same value for every unit of a KHG until neraca has spatial skill) and `design_period_days` from the run config. Any column may be empty: the pump module then falls back to equal priority and specific-yield demand, and says so.

## C7. Inputs the pump module needs from outside the chain

Not produced by any module here: canals with `canal_class` (and optional `depth_m`, `width_m`), existing structures (`sekat_id`, `has_gate`), rivers, burnt area, peat depth, moisture rasters. Their schema is in `repeat-pump`'s README and is not repeated here. Where the same layer (canals, peat depth) is also used by delineation, neraca or prioritisation, all of them read the same file; the per-site registry (below) holds the path once.

## Per-site registry

Each study KHG has a folder in the hub, `sites/<khg_slug>/`: a README (runbook, decisions, results), one config per module (`delineate.yaml`, `subkhg.yaml`, `neraca.yaml` for neraca air) and `reports/`. The configs name every path through three environment variables: `REPEAT_WORK` (derived data: clipped vectors, caches, outputs), `REPEAT_DATA` (the raw REPEAT-LH data) and `SITMAT_PROCESSED`. The module repositories keep only an example config. Done 2026-10-20 for Kampar-Gaung and Sugihan-Lumpur; the outputs were checked to be identical to those of the configs before the move.

## Decisions to settle before code moves

| # | Question | Proposal |
|---|---|---|
| D1 | `unit_id` or `subkhg_id` | **Settled and done:** `unit_id` everywhere; the pump module accepts `unit_id` for its `subkhg_id` (layer and table) |
| D2 | Forcing as file hand-over or direct read | **Settled and done for forcing:** `repeat-neraca` imports the readers from `repeat-common`; the export remains the offline route. Stations are still file-only |
| D3 | Who writes `subkhg_priority.csv` | **Settled and done:** `repeat-prioritisation` (`subkhg/priority_export.py`, config `priority_export:`), reading `neraca_khg.csv` |
| D4 | `dtm_smooth.json` sidecar | add it in `repeat-dem`; consumers warn when RMSE is missing |
| D5 | Where the contract checks live | `repeat-common.contracts`: one `validate_<file>()` per section above, called by the reader of that file |
