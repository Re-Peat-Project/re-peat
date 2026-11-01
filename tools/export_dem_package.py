#!/usr/bin/env python3
"""Zip everything one DEM variant produced, per KHG, to hand to peers.

  python re-peat/tools/export_dem_package.py --dem deltadtm [--khg 16.02.01 ...] [--out <zip>] [--dry-run]

For each KHG folder in $REPEAT_KHG (all of them, or the codes given) it takes, from input to output:
  00_inputs   KHG boundary, canals, rivers, lakes, blocks, peat depth, ICESat-2, protected-area clip, SiTMAT stations
  01_dem      the variant's DEM clip and manifest, its correction run (inputs, intermediates, corrected DTM, validation), and
              where LiDAR exists the benchmark error maps, metrics and processed run
  02_delineation, 03_neraca, 04_prioritisation, 05_pump   the variant's folder, plus the shared KHG deficit in 03_neraca/runs
  cache       the variant's delineation intermediates
  logs        pipeline logs of the variant
  sites       the tracked configs of the KHG (re-peat/sites/<folder>)
Left out: copies of inputs made inside pump runs (inputs_clipped), parameter-sweep variants (05_demnas_ground_filter,
05_pump/variants, stability/cache), .vrt files (relative links break), lock files. Other variants' folders are not touched.
The zip holds README.md and MANIFEST.csv (path, bytes, stage). Nothing is written into the KHG folders.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import os
import sys
import zipfile
from pathlib import Path

HUB = Path(os.environ.get("REPEAT_HUB") or Path(__file__).resolve().parents[1])
KHG_ROOT = Path(os.environ.get("REPEAT_KHG") or HUB.parent / "_khg")

CORE_INPUTS = ["khg.gpkg", "canals.gpkg", "rivers.gpkg", "lakes.gpkg", "blocks.gpkg", "peat_depth.tif", "icesat2_atl08.gpkg",
               "feg_protected.gpkg", "local_manifest.csv", "sitmat"]
SKIP_PARTS = {"inputs_clipped", "05_demnas_ground_filter", "variants", "cache_stability"}
SKIP_SUFFIX = (".vrt", ".lock")


def stage(rel: str) -> str:
    return rel.split("/", 1)[0]


def wanted(rel: str, dem: str) -> bool:
    p = rel.split("/")
    if any(x in SKIP_PARTS for x in p) or rel.endswith(SKIP_SUFFIX) or (len(p) > 2 and p[0] == "02_delineation" and p[1] == "stability"):
        return False
    s = p[0]
    if s == "00_inputs":
        return p[1] in CORE_INPUTS
    if s == "01_dem":
        if p[1] == "inputs":
            return p[-1] == "manifest.csv" or dem in p[-1]
        if p[1] == "benchmark":
            return p[-1] in ("README.md",) or p[2] == "03_metrics" or any(dem in x for x in p[2:])
        return any(dem in x for x in p[1:])
    if s == "03_neraca" and len(p) > 2 and p[1] == "runs" and p[2] in ("deficit", "balance_khg_level"):
        return True
    if s == "logs":
        return dem in p[-1]
    return any(dem in x for x in p[1:]) or (s == "cache" and any(dem in x for x in p[1:2]))


def collect(folder: Path, dem: str):
    out = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_PARTS]
        for f in files:
            full = Path(root) / f
            rel = full.relative_to(folder).as_posix()
            if wanted(rel, dem):
                out.append((full, rel))
    return out


def site_files(khg_name: str):
    d = HUB / "sites" / khg_name
    return [(f, f"sites/{f.relative_to(d).as_posix()}") for f in sorted(d.rglob("*")) if f.is_file() and f.suffix in (".yaml", ".md")
            and not any(x in f.parts for x in ("reports",))] if d.is_dir() else []


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dem", default="deltadtm")
    ap.add_argument("--khg", nargs="*", help="KHG codes (without the KHG. prefix); default all folders")
    ap.add_argument("--out")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    folders = sorted(d for d in KHG_ROOT.iterdir() if d.is_dir() and d.name[:1].isdigit())
    if a.khg:
        folders = [d for d in folders if any(d.name.startswith(c.replace("KHG.", "") + "_") for c in a.khg)]
    plan = []
    for d in folders:
        files = collect(d, a.dem)
        if not any(r.startswith("01_dem/") and a.dem in r for _, r in files):
            print(f"skip {d.name}: no {a.dem} files")
            continue
        sites = site_files(d.name)
        plan.append((d, files, sites))
        tot = sum(f.stat().st_size for f, _ in files) + sum(f.stat().st_size for f, _ in sites)
        print(f"{d.name:45s} {len(files) + len(sites):5d} files {tot / 1e6:8.1f} MB")
    grand = sum(f.stat().st_size for _, fs, ss in plan for f, _ in fs + ss)
    print(f"{'total':45s} {sum(len(fs) + len(ss) for _, fs, ss in plan):5d} files {grand / 1e6:8.1f} MB (before compression)")
    if a.dry_run:
        return
    today = dt.date.today().isoformat()
    out = Path(a.out) if a.out else KHG_ROOT / "_export" / f"repeat_{a.dem}_package_{today}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = io.StringIO()
    mw = csv.writer(manifest, lineterminator="\n")
    mw.writerow(["khg_folder", "path_in_zip", "bytes", "stage"])
    root_name = f"repeat_{a.dem}_package"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as z:
        for d, files, sites in plan:
            for f, rel in files + sites:
                arc = f"{root_name}/{d.name}/{rel}"
                z.write(f, arc)
                mw.writerow([d.name, arc, f.stat().st_size, stage(rel)])
            print("zipped", d.name, flush=True)
        for extra in ("pipeline.yaml",):
            if (HUB / extra).is_file():
                z.write(HUB / extra, f"{root_name}/{extra}")
        z.writestr(f"{root_name}/MANIFEST.csv", manifest.getvalue())
        z.writestr(f"{root_name}/README.md", readme(a.dem, plan, today))
    print(f"{out}: {out.stat().st_size / 1e6:.0f} MB")


def readme(dem: str, plan, today: str) -> str:
    rows = "\n".join(f"| {d.name} | {len(fs) + len(ss)} |" for d, fs, ss in plan)
    return f"""# RE-PEAT, {dem} package ({today})

One folder per KHG, each laid out as in the project's per-KHG work folder:

| Folder | Holds |
|---|---|
| `00_inputs/` | KHG boundary, canals, rivers, lakes, canal blocks, peat depth, ICESat-2 ground heights, protected-area clip, SiTMAT stations |
| `01_dem/inputs/` | {dem} clipped to the KHG, with `manifest.csv` |
| `01_dem/processed/{dem}/` | DTM correction: canopy and land-cover inputs, ground points, calibration, `dtm_corrected.tif`, `dtm_smooth.tif`, validation |
| `01_dem/benchmark/` | only where airborne LiDAR covers the KHG: error maps against LiDAR, metrics, the processed run |
| `02_delineation/{dem}/` | sub-KHG units and report |
| `03_neraca/{dem}/` | rain and evapotranspiration per sub-KHG, water balance; `03_neraca/runs/` holds the station-based KHG deficit |
| `04_prioritisation/{dem}/` | sub-KHG ranking, maps |
| `05_pump/{dem}/` | canal blocks and pumping, conditioned DTM, flow accumulation, report |
| `cache/` | delineation intermediates |
| `logs/` | pipeline logs |
| `sites/` | the configs that produced the runs |

`MANIFEST.csv` lists every file with its size and stage. `pipeline.yaml` is the chain definition.
Left out to keep the size down: input copies inside pump runs, parameter sweeps, `.vrt` files, other DEM variants.
Rasters are GeoTIFF, vectors GeoPackage; open them in QGIS. The {dem} product is DeltaDTM v1.1 (land below about 10 m +MSL).

| KHG folder | Files |
|---|---|
{rows}
"""


if __name__ == "__main__":
    sys.exit(main())
