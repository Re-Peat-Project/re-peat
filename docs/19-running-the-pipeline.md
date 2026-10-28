# 19 Running the full chain

How to run the whole RE-PEAT chain (DEM, sub-KHG delineation, neraca air, prioritisation, interventions) for one or many KHG, on
this machine or another one, with the project data or your own. The plan behind it (which KHG, which DEMs, why) is in
[18-full-run-plan.md](18-full-run-plan.md).

## What runs where

`re-peat` is the runner. It holds:

| File | Holds |
|---|---|
| `pipeline.yaml` | Settings shared by every KHG: folders, the interpreter of each module, the national input files, the steps and their parameters |
| `pipeline.local.yaml` | Your machine's overrides of `pipeline.yaml` (interpreters, folders, QGIS). Not tracked; create it when a default does not fit |
| `sites/<folder>/khg.yaml` | One KHG: its DEM variants (with the clip and its coverage, or the reason a variant is skipped), peat depth, canal class field, overrides |
| `sites/<folder>/<dem>/*.yaml` | The module configs of one KHG and DEM, generated from the two files above (delineation, prioritisation, DEM correction) |
| `tools/khg_pipeline.py` | The runner: `setup`, `init`, `status`, `plan`, `run` |

The modules stay in their own repositories (`repeat-common`, `repeat-dem`, `repeat-delineation`, `repeat-neraca`,
`repeat-prioritisation`, `repeat-pump`); the runner calls their command-line tools, each with its own interpreter.

Every path in the tracked files is written with `${REPEAT_DATA}` (the data folder) or `${REPEAT_KHG}` (the work folders), so the same
files work on any machine.

## Setting up a machine

1. **Workspace.** One folder holding `re-peat` and the module repositories side by side (`python tools/khg_pipeline.py setup --clone`
   clones the missing ones from the Re-Peat-Project organisation, at the commits in `env/repos.lock.txt`).
2. **Environments.** As set in `pipeline.yaml` under `python:`. Defaults (Windows):
   - `main`: `<workspace>/.venv` with `pip install -e repeat-common repeat-neraca repeat-prioritisation` and `earthengine-api`,
     `sliderule` (for ICESat-2).
   - `dem`: `repeat-dem/.venv` (its `requirements.txt`).
   - `delineation`: `repeat-delineation/.venv` (`pip install -e repeat-delineation repeat-common`).
   - `pump`: `repeat-pump/.venv` (`pip install -e repeat-pump`, then `pip install -e repeat-neraca`: repeat-pump takes the
     groundwater solver from repeat-neraca, pinned to a GitHub archive; the second command swaps in the workspace copy and must
     come after the first, since pip refuses both in one command).
   - `qgis` (optional, print layouts): OSGeo4W's `python-qgis.bat`.

   On Linux or macOS, set the paths in `pipeline.local.yaml` (`.venv/bin/python`).
3. **Data.** The `_data` folder with the layout described in the workspace `AGENTS.md`. Point the runner at another copy with
   `REPEAT_DATA` (environment variable) or `data:` in `pipeline.local.yaml`. The work folders default to `<workspace>/_khg`
   (`REPEAT_KHG` or `khg_root:` to change).
4. **Accounts.**
   - Google Earth Engine (neraca air, DeltaDTM): `earthengine authenticate`, and your cloud project in `environment.EE_PROJECT`
     (in `pipeline.local.yaml`).
   - SiTMAT water tables: `environment.SITMAT_PROCESSED` → the processed SiTMAT folder (repeat-sitmat).
   - ICESat-2 comes from SlideRule and Sentinel-2 from Microsoft Planetary Computer; neither needs an account.
5. **Same package versions.** `env/<env>.lock.txt` holds the exact packages of each environment of the reference machine
   (`python tools/khg_pipeline.py setup --lock` writes them). From the workspace folder:
   `python -m venv .venv` then `.venv/Scripts/python -m pip install -r re-peat/env/main.lock.txt` (and the same for `dem`,
   `delineation`, `pump` in their repositories' `.venv`). The module repositories are installed in editable mode (`-e ./<repo>`).
   `env/repos.lock.txt` holds the commit of each module repository (`setup --lock` writes it too, and warns about uncommitted or
   unpushed work, which the lock cannot carry). `setup` reports a repository on another commit and the command to check out the
   locked one.
6. **Same data.** `python tools/khg_pipeline.py data` checks every file of the data folder the chain reads (national files, DEM
   sources, peat-depth rasters) against `sites/data_manifest.csv` (size and sha256) and lists what is missing or different.
7. **Check.** `python tools/khg_pipeline.py setup` lists the repositories, interpreters, folders and whether the installed packages
   match the lock files, and says what is missing. Earth Engine: see the README, "Setting up Google Earth Engine".

### What a run records

Every `run` writes `$REPEAT_KHG/pipeline_provenance/<id>.json`:
- the commit of each repository and how many files had uncommitted changes;
- the sha256 of each lock file, and whether the installed packages matched it;
- the sha256 of the data manifest and of the settings;
- the date.

Every step's log line and its row in `pipeline_runs.csv` carry that id. Earth Engine, Planetary Computer, SlideRule and the S3 tiles
(WorldCover, Meta canopy height) are read live: their archives can change after the recorded date, so a later rerun can differ
slightly. Results are exactly repeatable only from committed code, the locked packages and a data folder that matches the manifest.

## Running

```bash
cd re-peat
python tools/khg_pipeline.py init                      # sites/<folder>/khg.yaml for the selected KHG (kept if present; --overwrite)
python tools/khg_pipeline.py status                    # done / to do / does not apply, per KHG and DEM -> $REPEAT_KHG/pipeline_status.csv
python tools/khg_pipeline.py plan --khg 15.05-07-10.01 # the commands `run` would execute; writes the module configs, runs nothing
python tools/khg_pipeline.py run --khg 15.05-07-10.01  # one KHG, every step and DEM
python tools/khg_pipeline.py run                       # every KHG with a khg.yaml
python tools/khg_pipeline.py run --steps neraca prioritisation --dem deltadtm   # part of the chain
python tools/khg_pipeline.py compare                   # every KHG and DEM side by side -> $REPEAT_KHG/pipeline_compare.csv
```

- **One at a time.** Commands run one after the other: heavy steps in parallel ran this machine out of memory.
- **Resumable.** A step whose output is there is skipped, so an interrupted run continues where it stopped; `--force` reruns.
- **Failures.** A failed step is recorded and the run goes on with the next KHG or DEM. The steps after it are skipped for that
  KHG or DEM.
- **Logs.** Each step logs to `$REPEAT_KHG/<folder>/logs/pipeline_<step>[_<dem>].log`. Every run appends to
  `$REPEAT_KHG/pipeline_runs.csv` (step, status, seconds).

## The steps

| Step | Per | Module (environment) | Output |
|---|---|---|---|
| inputs | KHG | repeat-prioritisation `subkhg.prepare_inputs` (main) | `00_inputs/` khg, canals, rivers, lakes, existing sekat |
| dem_inputs | KHG | repeat-dem `script/prepare_khg_dem.py` (dem) | `01_dem/inputs/` clips and `manifest.csv` |
| icesat2 | KHG | repeat-common `fetch_icesat2` (main) | `_data/icesat2/atl08_<khg>_<years>.gpkg` |
| local_inputs | KHG | `tools/pipeline/localize.py` (main) | `00_inputs/national/`, `feg_protected.gpkg`, `peat_depth.tif`, `sitmat/`, `icesat2_atl08.gpkg`, `local_manifest.csv` |
| dem_correction | DeltaDTM, DEMNAS | repeat-dem `script/tiled_dtm.py` (dem) | `01_dem/processed/<dem>/dtm_smooth.tif` |
| delineation | DEM | repeat-delineation (delineation) | `02_delineation/<dem>/subkhg_units.gpkg` |
| deficit | KHG | repeat-neraca `stations`, `run --tier 1` (main) | `03_neraca/runs/deficit/neraca_khg.csv` |
| neraca | DEM | repeat-neraca `batch --dem` (main; Earth Engine) | `03_neraca/<dem>/inputs/`, `runs/balance/` with `neraca_map.gpkg` |
| prioritisation | DEM | repeat-prioritisation `subkhg.run` (main; Sentinel-2) | `04_prioritisation/<dem>/` |
| pump | DEM | repeat-pump `khg_run_config`, `run`, `report-html` (pump) | `05_pump/<dem>/` GeoPackage, `run_report.md`, `report.html`, `budget.csv` |
| layouts | DEM | repeat-pump `make_layouts.py` (qgis) | `05_pump/<dem>/layouts/` PNG and PDF |

The DEM variants are `lidar` (when a LiDAR covers at least 90 % of the KHG), `deltadtm` and `demnas` (after the correction).

## Running from a KHG folder, without the data folder

The `_data` folder is too large to pass around. After `inputs`, `dem_inputs`, `icesat2` and `local_inputs`, a KHG work folder holds
every file the later steps read, clipped from the national data to the KHG plus 5 km:

| In `00_inputs/` | From `_data` | Read by |
|---|---|---|
| `khg.gpkg`, `canals.gpkg`, `rivers.gpkg`, `lakes.gpkg`, `blocks.gpkg` | KHG boundaries, canal and river network, existing sekat | every step |
| `national/` (same file names as in `_data`) | burnt area, VIIRS hotspots, this year's KLH hotspots, canals, existing infrastructure, target villages, national peat depth, DPG village list; GFW and Global Peatland Map peat extent (raster windows) | prioritisation (national layers), pump (burnt area) |
| `feg_protected.gpkg` | peat ecosystem function 2017 | prioritisation (protected share) |
| `peat_depth.tif` | the KHG's peat-depth model (window on its own grid) | deficit, prioritisation, pump |
| `sitmat/` | SiTMAT stations within the area and their daily readings | deficit, prioritisation |
| `icesat2_atl08.gpkg` | ICESat-2 ground points | DEM correction |

`01_dem/inputs/` already holds the DEM clips. `local_manifest.csv` lists each file with its source, feature count or raster size,
and sha256. The generated configs read these copies when they exist, and `_data` otherwise. With a fresh copy of a KHG folder
(say from a shared drive) a peer only needs the repositories, the environments and the online accounts (Earth Engine; SlideRule,
Planetary Computer and the S3 tiles need none):

```bash
# REPEAT_KHG: the folder holding the copied <code>_<name>/ folders; the data folder may be missing or empty
python tools/khg_pipeline.py status --khg 15.05-07-10.01
python tools/khg_pipeline.py run --khg 15.05-07-10.01      # the steps already done are skipped
```

Checked on Mendahara-Batanghari (LiDAR units): the fire, hotspot, canal and peat-share indicators computed with an empty data
folder equal those computed from `_data` (largest difference 4e-16).

## Your own data or settings

- **Another data folder with the same layout:** set `REPEAT_DATA`; nothing else changes.
- **Different national files** (canals, rivers, boundary): change `national:` in `pipeline.local.yaml`.
- **One KHG differently:** edit its `sites/<folder>/khg.yaml`:
  - point a DEM variant at another clip;
  - skip a variant with `skip: <reason>`;
  - set the peat depth (or `null`);
  - add `overrides`, e.g. `{delineation: {min_area_km2: 50}}`.

  `init` never overwrites an existing `khg.yaml` without `--overwrite`.
- **A KHG not in the list:** `python tools/khg_pipeline.py init --khg <code or name>`, then `run --khg <code>`. Any of the 865 KHG
  in `sites/khg_registry.csv` works once its DEM clips exist (the `dem_inputs` step).
