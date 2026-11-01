"""Inventory of the team deliveries in _khg/from_team: one row per dataset (layer, raster, table, archive).

    python tools/inventory_from_team.py [FOLDER]     # FOLDER defaults to $REPEAT_KHG/from_team, then ../../_khg/from_team

Metadata only: vector layers (CRS, geometry, features, extent, columns), rasters (CRS, size, cell, dtype,
nodata, extent), CSV (rows, columns), archive entries and run reports. Nothing is extracted or changed.
Writes reports/investigations/from_team_inventory.csv (one row per dataset) and from_team_entries.csv
(archive entries). Needs geopandas, pyogrio, rasterio, pandas.
"""
import os
import sys
import zipfile
from pathlib import Path

import pandas as pd
import pyogrio
import rasterio

HUB = Path(__file__).resolve().parents[1]
OUT = HUB / "reports" / "investigations"
SKIP = {".cpg", ".dbf", ".prj", ".qmd", ".shx", ".sbn", ".sbx", ".xml", ".qpj", ".ovr", ".lock", ".atx", ".cpg"}
ROOT = Path(os.environ.get("REPEAT_KHG", HUB.parent / "_khg")) / "from_team"


def vector_rows(p):
    rows = []
    for name, geom in pyogrio.list_layers(p):
        info = pyogrio.read_info(p, layer=name)
        b = info["total_bounds"]
        rows.append(dict(layer=name, kind="vector", geometry=geom, features=info["features"],
                         crs=info["crs"], bounds=None if b is None else ",".join(f"{v:.4f}" for v in b),
                         fields=";".join(info["fields"])))
    return rows


def raster_row(p):
    with rasterio.open(p) as r:
        b = r.bounds
        return [dict(layer="", kind="raster", geometry=f"{r.count} band {r.dtypes[0]}",
                     features=f"{r.width}x{r.height}", crs=r.crs.to_string() if r.crs else "none",
                     cell=f"{abs(r.res[0]):.6g} x {abs(r.res[1]):.6g}", nodata=r.nodata,
                     bounds=",".join(f"{v:.4f}" for v in (b.left, b.bottom, b.right, b.top)))]


def table_row(p):
    df = pd.read_csv(p, nrows=None, low_memory=False)
    return [dict(layer="", kind="table", features=len(df), fields=";".join(map(str, df.columns)))]


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    rows, entries = [], []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() in SKIP:
            continue
        rel = p.relative_to(root)
        base = dict(delivery=rel.parts[0], file=str(Path(*rel.parts[1:])), size_mb=round(p.stat().st_size / 2**20, 2))
        ext = p.suffix.lower()
        try:
            if ext in {".shp", ".gpkg"}:
                got = vector_rows(p)
            elif ext in {".tif", ".tiff"}:
                got = raster_row(p)
            elif ext == ".csv":
                got = table_row(p)
            elif ext == ".zip":
                with zipfile.ZipFile(p) as z:
                    infos = [i for i in z.infolist() if not i.is_dir()]
                for i in infos:
                    entries.append(dict(delivery=base["delivery"], archive=base["file"], entry=i.filename,
                                        size_mb=round(i.file_size / 2**20, 2)))
                got = [dict(kind="archive", features=len(infos))]
            else:
                got = [dict(kind=ext.lstrip(".") or "file")]
        except Exception as e:
            got = [dict(kind="error", fields=str(e)[:200])]
        rows += [{**base, **g} for g in got]
    cols = ["delivery", "file", "layer", "kind", "geometry", "features", "crs", "cell", "nodata", "bounds", "fields", "size_mb"]
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=cols).to_csv(OUT / "from_team_inventory.csv", index=False)
    pd.DataFrame(entries).to_csv(OUT / "from_team_entries.csv", index=False)
    print(len(rows), "datasets,", len(entries), "archive entries ->", OUT)


if __name__ == "__main__":
    main()
