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
| MODFLOW 6 (through flopy) as the groundwater engine: peat as 8-10 layers (thin at the top) to follow T(z) and Sy(z), Newton solver, canals as RIV/DRN with a stage per reach (SFR if canal flow must be routed), pumps as WEL, sea edge as CHD/GHB, a water budget per boundary | Decided 2026-10-28 to defer: the open questions (canal boundary in managed land, specific yield, the gate) are the same in either code. flopy 3.11.0 (CC0) and MODFLOW 6.8.1 (win64 binary) checked 2026-10-28; layering thin unconfined peat and the binary dependency of the QGIS plugin are the costs | `repeat-neraca` (`groundwater/`), after the canal boundary is settled; `docs/groundwater-model-report.md` section 8 |
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
| `--peat-depth` (mineral surface elevation, peat volume) exists in `demnas_dtm.py` but not in the QGIS plugin port | Plugin is a separate port | `repeat-dem/qgis_plugin` |
