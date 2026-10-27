# RE-PEAT

Peatland rewetting toolkit of the RE-PEAT project (World Bank, KLH), GIS workstream, Departemen Teknik Geodesi UGM. GitHub organisation: Re-Peat-Project.

This repository is the hub. It holds no analysis code; that lives in the modules. It holds what ties them together: the runner of the full chain, the documentation, the data contracts between modules, and the per-KHG configs, runbooks and reports.

## Run the chain

```bash
python tools/khg_pipeline.py setup     # repositories, interpreters, folders
python tools/khg_pipeline.py init      # sites/<folder>/khg.yaml per KHG
python tools/khg_pipeline.py status    # what is done and what can run, per KHG and DEM
python tools/khg_pipeline.py run --khg 15.05-07-10.01
```

Shared settings in [pipeline.yaml](pipeline.yaml) (machine overrides in an untracked `pipeline.local.yaml`), one `sites/<folder>/khg.yaml` per KHG. Setup on another machine, steps and outputs: [docs/19-running-the-pipeline.md](docs/19-running-the-pipeline.md); the plan for the selected KHG: [docs/18-full-run-plan.md](docs/18-full-run-plan.md).

### Setting up Google Earth Engine

Neraca air (rain and evapotranspiration per sub-KHG) and DeltaDTM are read from Google Earth Engine. Each person needs their own
Earth Engine access through a Google Cloud project; the steps below follow the official pages
([Earth Engine access](https://developers.google.com/earth-engine/cloud/earthengine_cloud_project_setup),
[Python installation](https://developers.google.com/earth-engine/guides/python_install),
[Authentication](https://developers.google.com/earth-engine/guides/auth)), read on 2026-10-27.

1. **Register a Cloud project for Earth Engine.** Open the registration page, https://console.cloud.google.com/earth-engine, and
   create a new project or register an existing one. Choose **noncommercial** use for research and education: no billing account
   is needed, but you fill in the eligibility questionnaire in the Cloud console
   (https://console.cloud.google.com/earth-engine/configuration). Access starts as soon as the project is registered.
   Noncommercial projects must reverify periodically.
   - The manual route does the same: create a project (https://console.cloud.google.com/projectcreate), enable the Earth Engine
     API (https://console.cloud.google.com/apis/library/earthengine.googleapis.com), then register it at
     `https://code.earthengine.google.com/register?project=<your-project-id>`.
2. **Install the client** in the `main` environment (it is in `env/main.lock.txt`): `pip install earthengine-api`.
3. **Authenticate** once per machine, in a terminal: `earthengine authenticate` (or `python -c "import ee; ee.Authenticate()"`).
   The credentials go to `~/.config/earthengine/credentials` (on Windows under your user folder). If they stop working:
   `earthengine authenticate --force`.
4. **Tell the pipeline your project.** Put it in `pipeline.local.yaml` (not tracked), so it overrides the project of
   `pipeline.yaml`:

   ```yaml
   environment:
     EE_PROJECT: <your-project-id>
   ```

   Optionally also `earthengine set_project <your-project-id>`, the default of the `earthengine` command and of `ee.Initialize()`.
5. **Check:**

   ```bash
   python -c "import ee; ee.Initialize(project='<your-project-id>'); print(ee.String('Hello from the Earth Engine servers!').getInfo())"
   ```

   The error "Earth Engine API has not been used in project ... or it is disabled" means the project is not registered or the API
   is not enabled for it (step 1).

Noncommercial projects use the Community quota tier by default
([noncommercial tiers](https://developers.google.com/earth-engine/guides/noncommercial_tiers)). The runner sends at most
`neraca.workers` requests at a time (8 in `pipeline.yaml`); lower it in `pipeline.local.yaml` if requests are refused.

![Workflow](docs/img/workflow.png)

## The modules

Each module is its own repository. They exchange files, never imports; the files are defined in [docs/11-data-contracts.md](docs/11-data-contracts.md).

| Module | Does | Folder today |
|---|---|---|
| `repeat-sitmat` | Downloads water-table (TMA) data from SiTMAT; dashboard | `apps/sitmat-extract` |
| `repeat-common` | Library: open-data readers (Sentinel, ERA5, CHIRPS, WaPOR, ...), grid helpers, SiTMAT reader, config helpers | `repeat-common` |
| `repeat-dem` | DEMNAS correction and smoothing to a ground surface; the open-DEM investigation | `demnas-corrections` |
| `repeat-delineation` | Sub-KHG delineation from a DTM, rivers and canals | `repeat-delineation` |
| `repeat-neraca` | Neraca air (water balance): climatic balance per sub-KHG, KHG deficit, physical model | `repeat-neraca` |
| `repeat-prioritisation` | National (which KHG) and sub-KHG (which area inside a KHG) prioritisation | `khg-prioritisation-module` |
| `repeat-pump` | Rewetting with pompanisasi: canal blocks, water sources, routes, pump sizing; QGIS plugin | `rewetting-algorithm` |

The folder names of four modules still differ from the repository names; they are renamed when the repositories are created in the organisation.

## Set up a workstation

Clone every repository next to this one. Then, in one Python 3.11+ environment:

```bash
pip install -e ../repeat-common ../repeat-delineation "../repeat-neraca[neraca,experiments]"
pip install -r ../khg-prioritisation-module/requirements.txt
```

Environment variables used by the site configs (a missing one stops the run with a message):

| Variable | Points to |
|---|---|
| `REPEAT_DATA` | the REPEAT-LH `_data` folder: `Peat depth and DTM`, `_converted`, ... |
| `REPEAT_WORK` | a folder for derived data: clipped vectors, caches, outputs. For the national profile it is this repository's `reports/` folder, so the report is pushed with it (its `.gpkg` files are git-ignored; rebuild them with the profile run). Other modules still use `repeat-prioritisation/data_local`. |
| `SITMAT_PROCESSED` | `sitmat-extract/sitmat_out/processed` |

## Sites

The team selected 12 main KHG (plus reserves): see [docs/13-selected-khg.md](docs/13-selected-khg.md) and [sites/selected_khg.csv](sites/selected_khg.csv). One name (cawang-lalang) is still to be confirmed.

[sites/](sites/) has one folder per KHG that has been run:

| Site | KHG id | What is there |
|---|---|---|
| [kampar_gaung](sites/14.02-04-05.01_kampar_gaung/README.md) | 71 | Sungai Kampar - Sungai Gaung (Riau), 7,115 km2 |
| [16.02.01_sugihan_lumpur](sites/16.02.01_sugihan_lumpur/README.md) | 16.02.01 | Sungai Sugihan - Sungai Lumpur (South Sumatra), 6,348 km2 |

Each site folder has a README (the runbook: steps with the repository each runs in, decisions and reasons, results), one config per module (`delineate.yaml`, `subkhg.yaml`, `neraca.yaml` for neraca air) and `reports/`. These are test runs of the whole chain, not validated rankings.

## Data catalogue

[docs/14-data-catalog.md](docs/14-data-catalog.md) lists every file in `_data` (format, CRS, resolution, features, remarks). It is generated: run `python tools/catalog_data.py` after adding data; new files are appended and hand-written remarks in [sites/data_catalog.csv](sites/data_catalog.csv) are kept. [docs/16-khg-data-recap.md](docs/16-khg-data-recap.md) is the same per selected KHG (resolution, coverage, gaps per module): run `python tools/khg_data_recap.py`; the datasets it checks are listed in [sites/khg_recap_sources.csv](sites/khg_recap_sources.csv). `python tools/check_contour_source.py` tests which raster a contour set was traced from (default: the LiDAR contour sets; `--contour`, `--rasters` and `--zones` for others, per KHG; results in `reports/investigations/`); `python tools/contour_grid_spacing.py` detects the grid of contours whose source raster is not on disk.

The DEM benchmark (five elevation sources against LiDAR at KHG Mendahara - Batanghari and Sugihan - Lumpur, and the pipeline test) is reported in [reports/dem_benchmark/report.md](reports/dem_benchmark/report.md), built by `python tools/dem_benchmark_report.py` from the outputs of `repeat-dem/script/dem_benchmark*.py`; the workflow diagram is `reports/dem_benchmark/dem_benchmark_workflow.drawio` (`python tools/dem_benchmark_diagram.py`).

## National profile

[docs/15-national-profile.md](docs/15-national-profile.md) profiles and ranks all 865 KHG from the local layers (fire history, hotspots, canals by class) and builds an interactive dashboard (`reports/national_profile/dashboard.html`) where the weights can be changed live; the registry of official KHG codes is [sites/khg_registry.csv](sites/khg_registry.csv). Tools: `tools/fetch_firms.py` and `tools/fetch_peat_extent.py` (wrappers: the code is `repeat_common.fetch_firms` and `repeat_common.fetch_peat_extent` in repeat-common), `tools/parse_kepmen_khg.py` (needs pdfplumber), `tools/catalog_data.py`.

## Documentation

[docs/README.md](docs/README.md) is the index: background and terms, parameter register, pitfalls, DEMNAS literature, the build plan, neraca air, and the data contracts. Method pages written before the split name the old code layout; each has a note at the top saying where the code lives now.

## Rules

- Data never goes into a repository. Paths come from the environment variables above.
- A module changes what it likes inside; what it reads and writes between modules changes only after [docs/11-data-contracts.md](docs/11-data-contracts.md) does.
- A change to `repeat-common` changes every module: re-run the site checks of the modules that use it.
