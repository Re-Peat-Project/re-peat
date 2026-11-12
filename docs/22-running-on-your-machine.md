# Running the chain on your own machine

For team members who want to run the RE-PEAT chain (DEM preparation to canal-block plan) for one or more KHG on their own
computer, with Docker. Everything runs inside one image; your machine only needs Docker and a folder for data and results.
Status (2026-11-11): the container ran a KHG end to end on the reference machine (Mandiangin-Siak, 33 min); the compose setup
below and the `ee-auth` / `ee-check` commands are new and not yet tried by a second person. The image is published at
`ghcr.io/re-peat-project/repeat-chain` (built by the repository's GitHub workflow), so nobody has to build it.

## 1. What you need

| | |
|---|---|
| Docker | Docker Desktop (Windows, macOS) or Docker Engine (Linux). In Docker Desktop, give it at least 8 GB of memory (Settings, Resources) |
| Disk | about 9 GB for the image, 2 GB for the national data, and from about 0.1 GB per KHG you run (83 MB for Mandiangin-Siak, 17,644 ha; more for large KHG) |
| Internet | the chain downloads DeltaDTM, rain and evapotranspiration (Earth Engine), ICESat-2 (SlideRule), ERA5 and Sentinel-2 (Planetary Computer) while it runs |
| Earth Engine | your own Google account with a Cloud project registered for Earth Engine (section 3) |
| Two files of the re-peat repository | `docker/compose.yaml` and `docker/peer.example.env` (download them, or clone the repository) |

## 2. Folders

Pick one folder (`REPEAT_DIR`), for example `D:/repeat`. The chain uses these folders inside it; Docker creates the empty ones.

| Folder | What goes in | Needed |
|---|---|---|
| `data/` | the national data (section 4) | yes |
| `khg/` | one work folder per KHG: inputs, DEMs, units, water balance, priorities, canal-block plan and its HTML report | made by the chain |
| `config/settings.yaml` | your national choices: any key of `pipeline.yaml` (docs/21-configuration.md) | optional |
| `config/overrides/<code>.yaml` | your choices for one KHG, e.g. `14.08.04.yaml` | optional |
| `earthengine/` | your Earth Engine login, written by `ee-auth` | yes |
| `sitmat/` | processed SiTMAT water tables (`stations.csv`, `stations_geo.csv`, `daily_long.csv`), from the team's shared drive | needed when the KHG has SiTMAT stations (`facts.stations_*` in its `sites/<folder>/khg.yaml`); without them the KHG deficit step is skipped |
| `work/` | national profile outputs | can stay empty |

Then, next to `compose.yaml`:

    cp peer.example.env .env       # set REPEAT_DIR and EE_PROJECT in it

The commands below assume `compose.yaml` and `.env` are in the current folder (in a clone of re-peat: `cd docker`).

## 3. Earth Engine, once

1. Register at https://code.earthengine.google.com/register with your Google account: choose non-commercial use (research or
   education) and create or pick a Cloud project. Its id (e.g. `ee-yourname`) goes into `EE_PROJECT` in `docker/.env`.
2. Log in from the container (it prints a link: open it, sign in, paste the code back):

       docker compose run --rm chain ee-auth

3. Check:

       docker compose run --rm chain ee-check

   It should print `Earth Engine ok: project <yours>, DeltaDTM readable`.

The login stays in `REPEAT_DIR/earthengine/`; keep it private (it gives access to your Google account's Earth Engine).

## 4. Data

Put these files in `REPEAT_DIR/data/`, same names and subfolders (1.92 GB in total). They will be on the team's shared drive as a data pack (`data/`, `sitmat/`, `MANIFEST.csv` with the size and sha256 of every file, `README.md`): copy its `data/` and `sitmat/` into `REPEAT_DIR`. The GIS team makes the pack with `python tools/peer_data_pack.py --out <folder>` (`--khg <codes>` adds the modelled peat-depth rasters of those KHG, `--sitmat khg` keeps only their SiTMAT stations, `--zip` writes one zip file).

| File | Size |
|---|---|
| `batas_khg_indonesia.gpkg` (KHG boundaries) | 37 MB |
| `kanal_osgm_khg_existing_Indonesia.gpkg` (canals) | 212 MB |
| `RBI_sungai.gpkg`, `RBI_wadukdanau.gpkg` (rivers, lakes) | 16 MB |
| `infrastruktur_hidrologis_existing_BRGM_Indonesia.gpkg` (existing canal blocks) | 16 MB |
| `burnt_area_2015_2026_Indonesia.gpkg` | 722 MB |
| `hotspot_viirs_snpp_2012_2025.gpkg`, `hotspots_modis_2026.gpkg` | 722 MB |
| `landstatus/FEG__Indonesia__2017__Rev_Tipologi.gpkg` (peat ecosystem function) | 90 MB |
| `klhk_khg_feg_50k.gpkg`, `kedalaman_gambut_bbsdlp.gpkg` (peat thickness classes) | 63 MB |
| `desa_target_pemulihan_ekosistem_gambut.gpkg`, `dpg/dmpg_villages_sitmat.gpkg` (villages) | 27 MB |
| `peat_extent_gfw_v20230315_z11.tif`, `peat_extent_gpm2022_1km.tif` (peat extent) | 14 MB |

Optional, per KHG:
- the modelled peat-depth raster the KHG's `sites/<folder>/khg.yaml` names under `peat_depth.path` (50 KHG have one). Without
  it the chain falls back to the KLHK 1:50k classes, then BBSDLP classes, then PEATGRIDS (1 km, low confidence), in that
  order, and `config validate` notes which it uses.
- your own LiDAR DTM: put the GeoTIFF(s) in `REPEAT_DIR/data/lidar_own/` (heights in metres, CRS set). The DEM step clips every
  file there that covers the KHG; if one covers at least 90 % of it, the chain runs a LiDAR variant on it next to DeltaDTM.
  The team's own LiDAR is not shared.
- DeltaDTM needs nothing: the chain downloads it from Earth Engine.

Check what is missing for a KHG before running: `docker compose run --rm chain config validate --khg <code>`.

## 5. Run

    docker compose pull                                   # the image, once and after updates (about 2 GB download)
    docker compose run --rm chain plan --khg 14.08.04     # what would run
    docker compose run --rm chain run --khg 14.08.04      # run it
    docker compose run --rm chain status --khg 14.08.04

(`docker compose build` builds the image yourself instead, from a clone of re-peat, in about 7 minutes.)

`<code>` is the KHG code of `sites/khg_registry.csv` (e.g. `14.08.04`) or its name. Results are in `REPEAT_DIR/khg/<folder>/`:
the canal-block plan and its report in `05_pump/<dem>/` (`report.html`, the map layers in `<name>.gpkg`). A stopped run resumes
where it stopped: run the same command again. `run --force --steps pump` redoes one step.

By default the chain runs DeltaDTM and, where it covers the KHG, LiDAR. Your choices go in `config/`, never in the image:

    # REPEAT_DIR/config/settings.yaml: for every KHG you run
    dems:
      default: [deltadtm]
    pump:
      set:
        optimise.n_blocks: 15

    # REPEAT_DIR/config/overrides/14.08.04.yaml: for one KHG
    steps:
      delineation: {min_area_km2: 10}

`config show --khg <code>` lists every setting with the file it comes from; `config validate --khg <code>` catches typos and
wrong values. All settings: docs/21-configuration.md.

## 6. Time and size

Mandiangin-Siak (17,644 ha, two DEMs) took 33 minutes in the container: most of it the deficit step (11 min, the first ERA5
download) and the prioritisation (7 min, Sentinel-2). Large KHG take hours. Its work folder is 83 MB; large KHG and DEMNAS make it bigger.

## 7. When something fails

- The step's log is in `REPEAT_DIR/khg/<folder>/logs/pipeline_<step>[_<dem>].log`; the last lines say why.
- `Earth Engine init failed`: run `ee-check`; log in again with `ee-auth` if the login expired.
- A timeout from a download service: run the same command again (the chain resumes).
- Out of memory (the container stops without a message): give Docker Desktop more memory.
