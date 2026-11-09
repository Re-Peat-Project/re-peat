# RE-PEAT full chain (tools/khg_pipeline.py) in one image: the re-peat hub, the six module repositories and the four Python
# environments of pipeline.yaml (main, dem, delineation, pump), installed from the lock files in env/.
#
# Build from the re-peat folder (the build context is the re-peat repository; Docker reads docker/Dockerfile.dockerignore):
#   docker build -f docker/Dockerfile -t repeat-chain .
# Data, work folders and credentials are mounted at run time, never copied in: see docker/README.md.
#
# REPOS=lock (default) checks out the commits of env/repos.lock.txt; REPOS=main takes the head of each repository's main branch
# (for testing only: the run is then not reproducible from the lock).

FROM ubuntu:24.04

ARG REPOS=lock
ARG UID=1000
ARG GID=1000
# Python of each environment, as on the reference machine (pyvenv.cfg, 2026-11-08): main and pump 3.13, dem and delineation 3.12
ARG PY_MAIN=3.13
ARG PY_DEM=3.12
ARG PY_DELINEATION=3.12
ARG PY_PUMP=3.13

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

# git for the repositories; rasterio, pyogrio and pyproj bring GDAL and PROJ in their wheels, so no system GDAL is needed
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git tini \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /usr/local/bin/
RUN uv python install ${PY_MAIN} ${PY_DEM} ${PY_DELINEATION} ${PY_PUMP}

WORKDIR /opt/repeat

# the hub first (small: tools, settings, sites, env locks), then the module repositories at the locked commits
COPY . re-peat/
RUN set -eu; \
    while read -r repo commit; do \
      case "$repo" in ''|\#*) continue ;; esac; \
      git clone --quiet "https://github.com/Re-Peat-Project/${repo}.git" "$repo"; \
      if [ "$REPOS" = "lock" ]; then git -C "$repo" checkout --quiet "$commit"; fi; \
      echo "$repo $(git -C "$repo" rev-parse HEAD)" >> /opt/repeat/repos.installed.txt; \
    done < re-peat/env/repos.lock.txt; \
    cat /opt/repeat/repos.installed.txt

# Lock files as written on the reference machine (Windows): editable paths made absolute, and the lines that pip freeze adds
# for the editable packages and for pip itself dropped (uv installs those from the -e lines). The report and test tools of
# docker/exclude.txt are dropped too; the lock files themselves stay complete.
RUN set -eu; mkdir -p /opt/repeat/locks; \
    names=$(sed -e 's/\r$//' -e 's/#.*//' -e 's/[[:space:]]//g' re-peat/docker/exclude.txt | grep . | paste -sd'|'); \
    for env in main dem delineation pump; do \
      sed -e 's/\r$//' -e 's#^-e \./#-e /opt/repeat/#' re-peat/env/${env}.lock.txt \
        | grep -v -E '^(repeat-[a-z]+|pip)==' \
        | grep -v -i -E "^(${names})==" > /opt/repeat/locks/${env}.txt; \
      echo "${env}: $(grep -c . /opt/repeat/locks/${env}.txt) lines"; \
    done

# main: repeat-common, repeat-neraca, repeat-prioritisation, earthengine-api, sliderule (workspace .venv, as in pipeline.yaml)
RUN uv venv --python ${PY_MAIN} /opt/repeat/.venv \
 && uv pip install --python /opt/repeat/.venv/bin/python -r /opt/repeat/locks/main.txt
# dem: repeat-dem's own environment (its scripts run by path)
RUN uv venv --python ${PY_DEM} /opt/repeat/repeat-dem/.venv \
 && uv pip install --python /opt/repeat/repeat-dem/.venv/bin/python -r /opt/repeat/locks/dem.txt
# delineation: repeat-delineation and repeat-common
RUN uv venv --python ${PY_DELINEATION} /opt/repeat/repeat-delineation/.venv \
 && uv pip install --python /opt/repeat/repeat-delineation/.venv/bin/python -r /opt/repeat/locks/delineation.txt
# pump: repeat-pump pulls repeat-neraca v0.2.0 as a GitHub archive; the workspace copy then replaces it (README of repeat-pump,
# docs/19-running-the-pipeline.md: the two installs must be separate)
RUN uv venv --python ${PY_PUMP} /opt/repeat/repeat-pump/.venv \
 && uv pip install --python /opt/repeat/repeat-pump/.venv/bin/python -r /opt/repeat/locks/pump.txt \
 && uv pip install --python /opt/repeat/repeat-pump/.venv/bin/python --no-deps -e /opt/repeat/repeat-neraca

# interpreters and mount points of the container (pipeline.local.yaml overrides pipeline.yaml)
COPY docker/pipeline.local.yaml re-peat/pipeline.local.yaml

RUN groupadd -g ${GID} repeat && useradd -m -u ${UID} -g ${GID} repeat \
 && mkdir -p /data /khg /sitmat /work /secrets \
 && chown -R repeat:repeat /opt/repeat/re-peat /khg /work
USER repeat

ENV REPEAT_DATA=/data \
    REPEAT_KHG=/khg \
    PATH=/opt/repeat/.venv/bin:$PATH
WORKDIR /opt/repeat/re-peat
VOLUME ["/data", "/khg", "/sitmat", "/work"]

ENTRYPOINT ["/usr/bin/tini", "--", "/opt/repeat/.venv/bin/python", "tools/khg_pipeline.py"]
CMD ["setup"]
