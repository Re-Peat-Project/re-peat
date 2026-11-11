# RE-PEAT chain in Docker

One image holds the re-peat hub, the six module repositories and the four Python environments that `pipeline.yaml` names
(main, dem, delineation, pump), installed from `env/*.lock.txt` at the commits of `env/repos.lock.txt`. Data, work folders
and credentials stay outside the image and are mounted at run time.

For team members running the chain on their own machine, start with docs/22-running-on-your-machine.md (docker/compose.yaml,
Earth Engine login with `ee-auth`, check with `ee-check`). This file covers the image itself and the server.

## Before building

The image takes whatever is in `env/` at build time. Refresh the locks on the reference machine after committing and pushing
every module repository, otherwise the image checks out older commits:

    python tools/khg_pipeline.py setup --lock

`env/repos.lock.txt` was last written on 2026-10-28; the DEM checks, the national availability scan and the per-KHG
config layers came later.

## Build

From the re-peat folder:

    docker build -f docker/Dockerfile -t repeat-chain .

Build arguments:

| Argument | Default | Meaning |
|---|---|---|
| `REPOS` | `lock` | `lock`: commits of `env/repos.lock.txt`; `main`: head of each repository (testing only) |
| `UID`, `GID` | 1000 | owner of the files the container writes in `/khg` and `/work`; set to the server user's (`id -u`, `id -g`) |
| `PY_MAIN`, `PY_DEM`, `PY_DELINEATION`, `PY_PUMP` | 3.13, 3.12, 3.12, 3.13 | Python of each environment, as on the reference machine |

The lock files were written on Windows. If a pinned version has no Linux wheel the build stops at that environment; pin the
nearest version that has one and note it in the lock file's header.

## Mounts

| In the container | What | Mode |
|---|---|---|
| `/data` | the data folder (`_data`, `REPEAT_DATA`) | read only |
| `/khg` | the per-KHG work folders (`_khg`, `REPEAT_KHG`) | read-write |
| `/sitmat` | processed SiTMAT (`repeat-sitmat/sitmat_out/processed`) | read only |
| `/work` | the national profile outputs (`re-peat/reports` on the reference machine; read by the prioritisation) | read-write |
| `/secrets` | the Earth Engine service-account key | read only |

## Earth Engine

The neraca air step and the DeltaDTM fetch call `ee.Initialize(project=EE_PROJECT)` (`repeat_common.gee.init`). In the container
use a service account of the Earth Engine cloud project, registered for Earth Engine, and pass its key:

    -e EE_PROJECT=<project> -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/ee-key.json -v /path/to/keys:/secrets:ro

Not yet tested in the container. Another route is to mount a personal login (`~/.config/earthengine`) read only at
`/home/repeat/.config/earthengine`. Keep keys out of the repositories and the image.

## Run

    docker run --rm \
      -v /srv/repeat/_data:/data:ro -v /srv/repeat/_khg:/khg -v /srv/repeat/sitmat:/sitmat:ro -v /srv/repeat/work:/work \
      -v /srv/repeat/keys:/secrets:ro -e EE_PROJECT=<project> -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/ee-key.json \
      repeat-chain <command>

`<command>` is any `tools/khg_pipeline.py` command (docs/19-running-the-pipeline.md); without one the container runs `setup`, which
lists repositories, interpreters, folders and package versions against the locks. Then `data` (checks `/data` against
`sites/data_manifest.csv`), `status`, `plan`, `run --khg <code>`.

`sites/` is baked into the image. To use per-KHG configs changed after the build, mount them:
`-v /srv/repeat/re-peat/sites:/opt/repeat/re-peat/sites`.

## Not in the image

- report, screenshot and test packages of the reference machine (playwright, pymupdf, python-docx, onnxruntime, pytest and
  their dependencies): `docker/exclude.txt` lists them, and the build drops them from the lock files it installs. A package
  that a chain step starts to import must come off that list.
- QGIS (print layouts are skipped: `python.qgis: ""`)
- tippecanoe for the dashboard tiles (its own image: `repeat-prioritisation/tiles/Dockerfile`)
- the report tools (draw.io, Chrome)
- running several KHG at once: `run` executes one command at a time; parallel runs on the server are the next piece of work
