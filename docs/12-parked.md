# 12 Parked items and future improvements

Things we decided not to do yet, or found and left. Started 2026-10-20 during the split into repositories. Each line says what, why it was parked, and where it would go. When one is picked up, move it to the repository's own issues or docs.

## Data contracts ([11](11-data-contracts.md))

| Item | Why parked | Where |
|---|---|---|
| `dtm_smooth.json` sidecar (source DEM, vertical datum, correction settings, validation RMSE, date), so consumers can warn or refuse when the RMSE is missing | Decided 2026-10-20 to keep for later improvement | `repeat-dem` writes it; delineation, neraca, prioritisation and pump read it |
| `repeat_common.contracts`: one `validate_<file>()` per section of the contracts, called by the reader of that file | Same | `repeat-common` |

## Neraca air

| Item | Why parked | Where |
|---|---|---|
| Tropical peat table as the default for the physical model, with a measured Sy shape and transmissivity from conductivity profiles | Research done, see `repeat-neraca/docs/tropical-peat-hydraulic-parameters.md`; the Urzainki 2023 sets are site-calibrated, so adopting one needs a decision | `repeat-neraca` |
| KHG deficit: higher-resolution evaporation and rain, more dry seasons when station or other water table data cover them, a per-sub-KHG deficit once there is spatial skill | Data coverage limits us to 2026 and 25 km forcing today | `repeat-neraca` (`deficit.py`) |
| Stations read directly from SiTMAT (only forcing is read directly now) | Not asked for; the export step still writes the station files | `repeat-neraca` with `repeat_common.tma` |
| Canal level that is not "surface minus 1.2 m" (observed water tables sit at 35-55 cm) | The physical model cannot hold the dry-season level without a managed canal level and an outside water term | `repeat-neraca` |
| `registry` entries for the tropical sets, once one is adopted | Adding parameters changes the registry snapshot hash of every run | `repeat-neraca/repeat-neraca/src/repeat_neraca/parameters.yaml` |

## Housekeeping

| Item | Why parked | Where |
|---|---|---|
| Config key `units.subkhg` to `delineation:` | Kept so existing site configs work; change when the site configs are next edited | `repeat-delineation`, `sites/*/delineate.yaml` |
| Prioritisation reads `units.subkhg.canal_class_field` as a fallback for the canal class column | Left from the combined program | `repeat-prioritisation` (`subkhg/check_inputs.py`, `dashboard.py`) |
| Logger names `prioritas.*` | Cosmetic | `repeat-prioritisation`, `repeat-neraca` experiments |
| Two files called `neraca_unit.csv` (physical model: water table per sub-KHG with `neraca_skill_ok`; experiments: bucket indicators, in their own output folder) | The folder tells which; a rename would break `extra_indicators` paths of the site configs | `repeat-neraca` |
| `Registry` finds `repeat-neraca/src/repeat_neraca/parameters.yaml` through the source tree, so only an editable install works | Fine while everyone installs with `pip install -e` | `repeat-neraca` packaging |
| Some doc tables in this folder (`README.md` status table, `03-prioritisation.md`) still use pre-split names | Cosmetic; the banners at the top say where the code lives now | `re-peat/docs` |
| `--peat-depth` (mineral surface elevation, peat volume) exists in `demnas_dtm.py` but not in the QGIS plugin port | Plugin is a separate port | `repeat-dem/qgis_plugin` |
| Folder names `khg-prioritisation-module`, `rewetting-algorithm`, `demnas-corrections`, `apps/sitmat-extract` differ from the repository names | Renamed when the repositories are created in the organisation | each |
| Sugihan-Lumpur delineation and sub-KHG scoring were not re-run from the hub configs (Kampar-Gaung and the neraca runs were) | Cost; configs are parsed and use the same paths as before | `sites/sugihan_lumpur` |
