#!/usr/bin/env bash
# Rebuild every national output after an input that all of them share changes (the peat basis, the KHG boundaries).
# Steps whose per-KHG or per-tile caches hold that input run with --force. Order and commands follow docs/15-national-profile.md.
#   bash re-peat/tools/national_rebuild.sh [step ...]     # no argument = all steps; steps: peat fire report profile stage3 dashboard
# Needs: the workspace .venv, Docker (map tiles), node (charts and slides). Log: re-peat/reports/national_profile/rebuild.log
set -euo pipefail
WS="$(cd "$(dirname "$0")/../.." && pwd)"
m() { cygpath -m "$1" 2>/dev/null || echo "$1"; }
export REPEAT_DATA="$(m "$WS/_data")" REPEAT_WORK="$(m "$WS/re-peat/reports")" REPEAT_HUB="$(m "$WS/re-peat")"
export SITMAT_PROCESSED="$(m "$WS/repeat-sitmat/sitmat_out/processed")" PYTHONIOENCODING=utf-8
PY="$WS/.venv/Scripts/python.exe"; [ -x "$PY" ] || PY="$WS/.venv/bin/python"
CFG=configs/examples/national_profile.yaml S3=configs/examples/national_stage3.yaml
STEPS="${*:-peat fire report profile stage3 dashboard}"
run() { echo "== $(date +%H:%M:%S) $*"; "$@"; }
cd "$WS/repeat-prioritisation"
for s in $STEPS; do case $s in
  peat)      # KLH peat: dissolved extent (with the other PPEG layers) and its 30 m raster on the fire tally grid
             run "$PY" -m repeat_prioritisation.national.ppeg --layers
             run "$PY" -m repeat_prioritisation.national.ppeg --peat-raster "$CFG" ;;
  fire)      run "$PY" -m repeat_prioritisation.national.fire_landstatus --config "$CFG" --force --workers 4
             run "$PY" -m repeat_prioritisation.national.fire_tables --config "$CFG" ;;
  report)    run "$PY" -m repeat_prioritisation.national.ppeg
             run "$PY" "$WS/re-peat/tools/ppeg_roles.py"          # priority area and roles: read by the report and the deck
             run "$PY" "$WS/re-peat/tools/fire_landstatus_report.py"
             run powershell -NoProfile -File "$(m "$WS/re-peat/tools/docx_render.ps1")" "$(m "$WS/re-peat/reports/fire_landstatus/RE-PEAT_fire_land_status.docx")"
             run "$PY" "$WS/re-peat/tools/fire_landstatus_figs.py" --style slides
             (cd "$WS/_slides" && run node build_fire.js)
             (cd "$WS/repeat-dashboard" && run "$PY" pipeline/build_fire_summary.py) ;;
  profile)   run "$PY" -m repeat_prioritisation.national.profile --config "$CFG" --mode validate
             run "$PY" -m repeat_prioritisation.national.profile --config "$CFG" --mode operational
             run "$PY" -m repeat_prioritisation.national.monthly --config "$CFG" --force
             run "$PY" -m repeat_prioritisation.national.land --config "$CFG" --force
             run "$PY" -m repeat_prioritisation.national.tenure --config "$CFG" --force ;;
  stage3)    run "$PY" -m repeat_prioritisation.national.stage3 select --config "$S3"
             run "$PY" -m repeat_prioritisation.national.run --config "$S3" --fetch-only
             run "$PY" -m repeat_prioritisation.national.stage3 summarize --config "$S3"
             run "$PY" -m repeat_prioritisation.national.overlay --config "$S3" ;;
  dashboard) run "$PY" -m repeat_prioritisation.national.dashboard --config "$CFG" --top all
             run "$PY" -m tests.test_national_profile ;;
  *) echo "unknown step $s"; exit 2 ;;
esac; done
echo "== $(date +%H:%M:%S) done"
