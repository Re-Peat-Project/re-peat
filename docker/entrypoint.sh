#!/bin/sh
# Entry point of the repeat-chain image.
#   ee-auth     log in to Earth Engine once (prints a link; paste the code back). Needs `docker run -it` and the login folder
#               mounted writable at /home/repeat/.config/earthengine
#   ee-check    check the login and EE_PROJECT with one small Earth Engine request
#   shell       a shell inside the container
#   anything else: tools/khg_pipeline.py <command> (setup, data, init, status, plan, run, config, compare)
set -e
case "$1" in
  ee-auth)
    shift
    exec /opt/repeat/.venv/bin/earthengine authenticate --auth_mode=notebook "$@" ;;
  ee-check)
    exec /opt/repeat/.venv/bin/python -c "
import os, sys, ee
p = os.environ.get('EE_PROJECT')
if not p or p.startswith('\$'):
    sys.exit('EE_PROJECT is not set: your Google Cloud project registered for Earth Engine')
try:
    ee.Initialize(project=p)
    n = ee.Image('projects/sat-io/open-datasets/DELTARES/deltadtm_v1-1').bandNames().size().getInfo()
except Exception as e:
    sys.exit(f'Earth Engine not ready: {e}')
print(f'Earth Engine ok: project {p}, DeltaDTM readable ({n} band)')
" ;;
  shell)
    exec /bin/bash ;;
  *)
    exec /opt/repeat/.venv/bin/python /opt/repeat/re-peat/tools/khg_pipeline.py "$@" ;;
esac
