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

## Post FGD-1 to-do (Miro board "Re-peat", mind map "TODO Post FGD-1"; status 2026-11-05)

Parked on 2026-11-05 to prepare the national KHG run first. Status as of that date.

| Item | Status 2026-11-05 | Where |
|---|---|---|
| Prioritisation: fix the supporting data for the national priority (land use? village boundaries?) | Not started | `repeat-prioritisation` |
| DEM: find comparison LiDAR | Done for the LiDAR already held: Saleh-Sugihan (2020) and Pulau Padang (2016) are benchmark sites 3 and 4; no new LiDAR sourced | `repeat-dem/benchmark/dated_lidar.yaml` |
| DEM: test the DeltaDTM calibration | Largely done: canal mask, ICESat-2 trend, forest-type offsets, dome fits, none adopted; processed DeltaDTM stays (1 km error on peat 0.45-0.71 m), and the error is DeltaDTM's own | `repeat-dem/runs/checks/`, root `AGENTS.md` DEM section |
| Neraca: integrate the groundwater model with the dashboard for simulation | Discussed only: serve published run results first, scenario jobs later; run parameters listed | `repeat-neraca` |
| Neraca: groundwater model method: peat capillarity and a hydrotopographic model | Not started; capillarity is not in the model. Validation tiers (D26) are the method change so far | `repeat-neraca/docs/groundwater-model-report.md` |
| Neraca: find historic SIPALAGA records | Open; D26 sets how they would be used for validation; needs a data request | `repeat-neraca` D26 |
| Neraca: integrate ForTy for land cover, find land-use data | ForTy and TMF fetched (2 KHG; `repeat_common.fetch_forest_type` works for any KHG); unlicensed tree crops reported (43.7% at Mendahara-Batanghari), not yet in model runs. Next: one run treating them as managed, scored on community stations. Land use not started | `repeat-neraca/docs/reports/forest_type_managed.md`, report section 8 item 6 |
| Neraca: find canal data or test Dadap (2021) | Sources noted (Dadap, licence CC BY-ND 3.0; Haidar and Takeuchi 2022); canals not visible in raw DEMNAS. Next: Dadap against the national canal layer per KHG | `repeat-pump/docs/canal_mapping_sources.md`, `repeat-dem/runs/checks/canal_visibility.md` |
| Interventions: edit canal data | Not started | `repeat-pump` |
| Interventions: fix cost estimates | Not started | `repeat-pump` (budget) |
| Interventions: fix intervention types | Not started | `repeat-pump` |

## Research ideas: Earth observation embeddings (discussed 2026-11-05)

Foundation-model embeddings (Google AlphaEarth Foundations, published as annual 10 m embeddings on Earth Engine; Ai2 OlmoEarth, open models to fine-tune) as a side layer of the chain, not as the water model: an embedding describes the surface, while the water table depends on canal levels and management, and SiTMAT labels mostly show the 40 cm compliance level. Product versions, years and licences not yet checked.

| Item | Why parked | Where |
|---|---|---|
| Peat depth from embeddings: train on the 159 KHG with modelled, KLHK FEG 1:50k or BBSDLP depth (plus DeltaDTM height and distance to rivers), validate on held-out KHG, predict the 706 KHG that now fall back to PEATGRIDS; pass rule written first, compared with PEATGRIDS | National run preparation first; needs the per-KHG peat-depth order settled (`docs/20-khg-availability.md`) | `repeat-common` (fetch), new check in `repeat-neraca` or `repeat-dem` |
| Managed land and drainage intensity beyond licences (43.7% unlicensed tree crops at Mendahara-Batanghari): embeddings with ForTy as a map of managed land for the model | Same; follows `repeat-neraca/docs/reports/forest_type_managed.md` | `repeat-neraca` |
| Canal density or a drained / not drained flag per sub-KHG for the 522 KHG without mapped canals (10 m is too coarse for single tertiary canals) | Same | `repeat-pump`, `docs/canal_mapping_sources.md` |
| KHG analogues: an embedding per KHG or sub-KHG (landscape, climate, model outputs) to carry settings validated at the 35 KHG with community stations to similar KHG, and to flag the least trustworthy results | Needs validated set-ups first (D26 tiers) | `re-peat` (national run), `repeat-neraca` |
| Embeddings as inputs of a fast emulator of the groundwater model for scenario screening | Needs the model to pass tier 2 first | `repeat-neraca` |

Start with the ready-made AlphaEarth embeddings on Earth Engine (nothing to train); fine-tune OlmoEarth on the DTI server only if they fall short.

## Housekeeping

| Item | Why parked | Where |
|---|---|---|
| Config key `units.subkhg` to `delineation:` | Kept so existing site configs work; change when the site configs are next edited | `repeat-delineation`, `sites/*/delineate.yaml` |
| Prioritisation reads `units.subkhg.canal_class_field` as a fallback for the canal class column | Left from the combined program | `repeat-prioritisation` (`subkhg/check_inputs.py`, `dashboard.py`) |
| Logger names `prioritas.*` | Cosmetic | `repeat-prioritisation`, `repeat-neraca` experiments |
| Two files called `neraca_unit.csv` (physical model: water table per sub-KHG with `neraca_skill_ok`; experiments: bucket indicators, in their own output folder) | The folder tells which; a rename would break `extra_indicators` paths of the site configs | `repeat-neraca` |
| `Registry` finds `repeat-neraca/src/repeat_neraca/parameters.yaml` through the source tree, so only an editable install works | Fine while everyone installs with `pip install -e` | `repeat-neraca` packaging |
| `--peat-depth` (mineral surface elevation, peat volume) exists in `demnas_dtm.py` but not in the QGIS plugin port | Plugin is a separate port | `repeat-dem/qgis_plugin` |
