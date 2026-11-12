"""Data pack for a team member running the chain on their own machine (docs/22-running-on-your-machine.md).

    python tools/peer_data_pack.py --out ../_peer_data_pack                       # national core files and all SiTMAT stations
    python tools/peer_data_pack.py --out ../_peer_data_pack --khg 14.08.04 16.02.01
    python tools/peer_data_pack.py --out ../_peer_data_pack --khg 14.08.04 --sitmat khg   # SiTMAT of those KHG only
    python tools/peer_data_pack.py --out ../_peer_data_pack --zip                 # also one zip file, for a single download

Writes <out>/data/ and <out>/sitmat/, laid out as the peer's REPEAT_DIR/data and REPEAT_DIR/sitmat, plus
  MANIFEST.csv   every file with its size, sha256, source and licence note (from sites/data_catalog.csv)
  README.md      what is in the pack, where it goes, and how it may be used
Contents:
  national core  the files every KHG run reads (pipeline.yaml `national`, tools/pipeline/localize.py), 1.92 GB on 2026-11-11
  peat depth     with --khg: the modelled peat-depth raster of each listed KHG that has one (khg.yaml peat_depth.path)
  SiTMAT         the processed SiTMAT folder (stations.csv, stations_geo.csv, daily_long.csv): all stations, those of the
                 --khg KHG plus 5 km (--sitmat khg), or none (--sitmat none)
Not included: LiDAR (restricted; a peer puts their own in data/lidar_own), DEMNAS (optional, the peer's Tanahair login),
DeltaDTM and ICESat-2 (the chain downloads them). Files are copied unchanged; nothing is sent anywhere.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import os
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pipeline import config, khgconf, localize  # noqa: E402


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(1 << 22):
            h.update(b)
    return h.hexdigest()


def core_files(s) -> list[str]:
    """Data-folder paths every KHG run reads."""
    files = {v["path"] for v in s["national"].values() if isinstance(v, dict) and v.get("path")}
    files |= set(localize.NATIONAL.values()) | set(localize.NATIONAL_COPY.values()) | set(localize.NATIONAL_RASTERS.values())
    files |= {localize.FEG, "klhk_khg_feg_50k.gpkg"}
    return sorted(files)


def catalogue() -> dict:
    f = config.HUB / "sites" / "data_catalog.csv"
    with open(f, encoding="utf-8") as fh:
        return {r["path"]: r for r in csv.DictReader(fh)}


def licence_note(row: dict) -> str:
    text = " ".join(row.get(k, "") for k in ("source", "remarks"))
    for key in ("CC BY-NC-SA", "CC BY-ND", "CC BY 4.0", "CC BY", "non-commercial"):
        if key.lower() in text.lower():
            return key
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--khg", nargs="*", default=[], help="add the modelled peat-depth rasters of these KHG")
    ap.add_argument("--sitmat", choices=["all", "khg", "none"], default="all")
    ap.add_argument("--zip", action="store_true", help="also write <out>.zip")
    a = ap.parse_args()
    s = config.load()
    data, out = s.data, a.out.resolve()
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} is not empty; choose a new folder")
    cat = catalogue()
    rows, missing = [], []

    def add(src: Path, rel: str, what: str):
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        c = cat.get(rel.removeprefix("data/"), {})
        rows.append({"file": rel, "what": what, "bytes": dst.stat().st_size, "sha256": sha256(dst),
                     "source": c.get("source", ""), "licence": licence_note(c)})
        print(f"{rel:<70} {dst.stat().st_size / 1e6:8.1f} MB", flush=True)

    for rel in core_files(s):
        (add(data / rel, f"data/{rel}", "national core") if (data / rel).is_file() else missing.append(rel))
    codes = khgconf.khg_codes(s, a.khg) if a.khg else []
    for code in codes:
        c = khgconf.load(s, code)
        pd_ = c.get("peat_depth") or {}
        if pd_.get("source") == "modelled raster" and pd_.get("path") and Path(pd_["path"]).is_file():
            p = Path(pd_["path"])
            rel = p.relative_to(data).as_posix()
            add(p, f"data/{rel}", f"modelled peat depth of KHG.{code}")
            for side in p.parent.glob(p.stem + ".*"):          # sidecars of .img rasters (.ige, .rrd, .aux.xml)
                if side != p and side.is_file():
                    add(side, f"data/{side.relative_to(data).as_posix()}", f"sidecar of the peat depth of KHG.{code}")
        else:
            print(f"KHG.{code}: no modelled peat-depth raster here ({pd_.get('source')}); the chain uses that source", flush=True)
    sit = Path(os.environ.get("SITMAT_PROCESSED", ""))
    if a.sitmat != "none":
        if not (sit / "stations.csv").is_file():
            missing.append(f"SiTMAT ({sit})")
        elif a.sitmat == "all":
            for name in ("stations.csv", "stations_geo.csv", "daily_long.csv"):
                if (sit / name).is_file():
                    add(sit / name, f"sitmat/{name}", "SiTMAT processed, all stations")
        else:
            import geopandas as gpd
            from shapely.ops import unary_union
            if not codes:
                sys.exit("--sitmat khg needs --khg")
            areas = []
            for code in codes:
                g = gpd.GeoSeries([khgconf._khg_geometry(s, code)], crs=4326)
                areas.append(g.to_crs(g.estimate_utm_crs()).buffer(localize.BUFFER_M).to_crs(4326).iloc[0])
            tmp = out / "_sitmat_tmp"
            n = localize.clip_sitmat(sit, tmp, unary_union(areas))
            for f in sorted(tmp.iterdir()):
                add(f, f"sitmat/{f.name}", f"SiTMAT processed, {n} stations of KHG {', '.join(codes)} plus 5 km")
            shutil.rmtree(tmp)
    with open(out / "MANIFEST.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "what", "bytes", "sha256", "source", "licence"])
        w.writeheader()
        w.writerows(rows)
    total = sum(r["bytes"] for r in rows)
    (out / "README.md").write_text(README.format(date=dt.date.today(), n=len(rows), gb=total / 1e9,
                                                 khg=", ".join(codes) or "none", sitmat=a.sitmat), encoding="utf-8")
    print(f"{len(rows)} files, {total / 1e9:.2f} GB -> {out}" + (f"; missing here: {', '.join(missing)}" if missing else ""))
    if a.zip:
        z = out.with_suffix(".zip")
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for p in sorted(out.rglob("*")):
                if p.is_file():
                    zf.write(p, p.relative_to(out).as_posix())
        print(f"zip: {z} ({z.stat().st_size / 1e9:.2f} GB)")


README = """# RE-PEAT data pack for running the chain on your machine

Made {date} by `re-peat/tools/peer_data_pack.py`: {n} files, {gb:.2f} GB. Modelled peat depth for KHG: {khg}. SiTMAT: {sitmat}.

## Where it goes

Copy `data/` and `sitmat/` into your `REPEAT_DIR` (the folder named in `.env` next to `compose.yaml`), so you have
`REPEAT_DIR/data/...` and `REPEAT_DIR/sitmat/...`. Then follow docs/22-running-on-your-machine.md of the re-peat repository:
`docker compose run --rm chain config validate --khg <code>` tells you if anything a KHG needs is still missing.

`MANIFEST.csv` lists every file with its size and sha256, to check a download.

## Not in the pack

- LiDAR: restricted. If you have your own LiDAR DTM, put it in `REPEAT_DIR/data/lidar_own/` (GeoTIFF, metres).
- DEMNAS: optional; downloaded with your own Tanahair link (`TANAHAIR_LINK`).
- DeltaDTM and ICESat-2: the chain downloads them.
- Modelled peat depth of other KHG: the chain uses the KLHK 1:50k or BBSDLP classes, or PEATGRIDS.

## Use

For RE-PEAT work only. Most files are government data (KLHK/KLH, BRGM, BIG, SiTMAT) shared within the project team: do not
publish them or pass them on. SiTMAT water tables are restricted. `peat_extent_gpm2022_1km.tif` is CC BY-NC-SA 4.0
(non-commercial). The `source` and `licence` columns of MANIFEST.csv say more per file.
"""

if __name__ == "__main__":
    main()
