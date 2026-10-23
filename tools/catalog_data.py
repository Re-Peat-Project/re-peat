"""Catalogue every file in the _data folder: one row per vector layer, raster or other file.

    python tools/catalog_data.py [DATA_DIR]      # DATA_DIR defaults to $REPEAT_DATA, then ../_data

Writes sites/data_catalog.csv (the table) and docs/14-data-catalog.md (the same, readable).
Rerunning refreshes the technical columns and keeps the hand-written ones
(description, source, year, remarks), keyed on (path, layer). New files get empty
hand-written cells; files that disappeared are kept and marked status=missing.
Needs pyogrio, rasterio, pandas.
"""
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pyogrio
import rasterio

HUB = Path(__file__).resolve().parents[1]
CSV = HUB / "sites" / "data_catalog.csv"
MD = HUB / "docs" / "14-data-catalog.md"

AUTO = ["path", "layer", "kind", "format", "geometry", "features", "crs", "resolution", "bands_dtype",
        "extent_xmin_ymin_xmax_ymax", "fields", "size_mb", "modified", "status"]
MANUAL = ["description", "source", "year", "remarks"]
VECTOR_EXT = {".gpkg", ".shp", ".geojson", ".fgb", ".gdb", ".kml"}
RASTER_EXT = {".tif", ".tiff", ".img", ".vrt", ".nc", ".asc"}
SKIP_EXT = {".tfw", ".shx", ".dbf", ".prj", ".cpg", ".sbn", ".sbx", ".xml", ".ovr", ".aux", ".qix", ".done"}  # shapefile sidecars


def crs_label(crs):
    if not crs:
        return ""
    try:
        return rasterio.crs.CRS.from_user_input(crs).to_string()
    except Exception:
        return str(crs)[:40]


def vector_rows(f, base):
    rows = []
    for name, geom in pyogrio.list_layers(f):
        try:
            info = pyogrio.read_info(f, layer=name, force_total_bounds=False)
            bounds = info.get("total_bounds")
            rows.append({
                "layer": name, "kind": "vector", "format": info.get("driver", ""),
                "geometry": info.get("geometry_type") or geom or "", "features": info.get("features"),
                "crs": crs_label(info.get("crs")),
                "extent_xmin_ymin_xmax_ymax": " ".join(f"{b:.5g}" for b in bounds) if bounds is not None else "",
                "fields": ", ".join(info.get("fields", [])),
            })
        except Exception as e:
            rows.append({"layer": name, "kind": "vector", "remarks_auto": f"unreadable: {e}"[:100]})
    return rows


def raster_rows(f):
    with rasterio.open(f) as r:
        res = f"{abs(r.res[0]):.6g} x {abs(r.res[1]):.6g} " + ("deg" if r.crs and r.crs.is_geographic else "m")
        b = r.bounds
        return [{"layer": "", "kind": "raster", "format": r.driver, "geometry": f"{r.width}x{r.height} px",
                 "crs": crs_label(r.crs), "resolution": res,
                 "bands_dtype": f"{r.count} x {r.dtypes[0]}" + (f", nodata={r.nodata}" if r.nodata is not None else ""),
                 "extent_xmin_ymin_xmax_ymax": f"{b.left:.5g} {b.bottom:.5g} {b.right:.5g} {b.top:.5g}"}]


def scan(data):
    out = []
    for f in sorted(p for p in data.rglob("*") if p.is_file()):
        ext = f.suffix.lower()
        rel = f.relative_to(data).as_posix()
        if ext in SKIP_EXT or rel.startswith("raw/"):   # raw/ holds downloads kept for provenance; the products are listed
            continue
        st = f.stat()
        common = {"path": rel, "size_mb": round(st.st_size / 1e6, 1),
                  "modified": date.fromtimestamp(st.st_mtime).isoformat(), "status": "ok"}
        try:
            if ext in VECTOR_EXT:
                rows = vector_rows(f, data)
            elif ext in RASTER_EXT:
                rows = raster_rows(f)
            else:
                rows = [{"layer": "", "kind": "other", "format": ext.lstrip(".")}]
        except Exception as e:
            rows = [{"layer": "", "kind": "unreadable", "format": ext.lstrip("."), "geometry": str(e)[:100]}]
        out += [{**common, **r} for r in rows]
    return pd.DataFrame(out).reindex(columns=AUTO)


def main():
    data = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("REPEAT_DATA") or HUB.parent / "_data")
    new = scan(data).fillna("")
    key = ["path", "layer"]
    if CSV.exists():
        old = pd.read_csv(CSV, dtype=str).fillna("")
        merged = new.merge(old[key + MANUAL], on=key, how="left").fillna("")
        gone = old.merge(new[key], on=key, how="left", indicator=True)
        gone = gone[gone["_merge"] == "left_only"].drop(columns="_merge")
        gone["status"] = np.where(gone["kind"].isin(["cloud", "external"]), gone["status"], "missing")   # cloud datasets are catalogued by hand and are not files in _data
        merged = pd.concat([merged, gone], ignore_index=True)
    else:
        merged = new.assign(**{c: "" for c in MANUAL})
    merged = merged[AUTO + MANUAL].sort_values(key, kind="stable")
    merged.to_csv(CSV, index=False, encoding="utf-8")

    cols = ["path", "layer", "kind", "format", "geometry", "features", "crs", "resolution", "size_mb", "description", "remarks"]
    md = ["# 14 Data catalogue", "",
          f"Generated by `tools/catalog_data.py` from the `_data` folder ({date.today().isoformat()}). Do not edit this page; "
          "edit the hand-written columns (description, source, year, remarks) in [sites/data_catalog.csv](../sites/data_catalog.csv) "
          "and rerun the script. New files are added on rerun and existing remarks are kept. The CSV also has extent, fields, "
          "band type and modification date.", "",
          "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in merged.iterrows():
        md.append("| " + " | ".join(str(r[c]).replace("|", "/") for c in cols) + " |")
    MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(merged)} rows from {data} -> {CSV}, {MD}")


if __name__ == "__main__":
    main()
