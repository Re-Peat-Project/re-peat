"""Catalogue every file in the _data folder: one row per vector layer, raster or other file.

    python tools/catalog_data.py [DATA_DIR]      # DATA_DIR defaults to $REPEAT_DATA, then ../_data

Writes sites/data_catalog.csv (the table) and docs/14-data-catalog.md (the same, readable).
Rerunning refreshes the technical columns and keeps the hand-written ones
(description, source, year, remarks), keyed on (path, layer). New files get empty
hand-written cells; files that disappeared are kept and marked status=missing.
Folders listed in sites/catalog_collapse.csv (columns prefix, depth) are summarised instead of listed file by file:
one row per sub-folder (depth 1) or one row for the whole prefix (depth 0), per kind and format, with the file count,
the CRS and resolutions found, the union of the extents and the file names. Use it for deliveries made of dozens of
near-identical per-KHG files.
Needs pyogrio, rasterio, pandas.
"""
import contextlib
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
RASTER_EXT = {".tif", ".tiff", ".img", ".vrt", ".nc", ".asc", ".sdat"}
COLLAPSE = HUB / "sites" / "catalog_collapse.csv"
SKIP_EXT = {".lock", ".rrd", ".sprj", ".sgrd", ".mgrd", ".tfw", ".shx", ".dbf", ".prj", ".cpg", ".sbn", ".sbx", ".xml", ".ovr", ".aux", ".qix", ".done"}  # shapefile sidecars


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


@contextlib.contextmanager
def opened(f):
    """GDAL reads a path containing '!' as an archive separator; open such files from their own folder."""
    if "!" in str(f):
        cwd = os.getcwd()
        os.chdir(f.parent)
        try:
            yield Path(f.name)
        finally:
            os.chdir(cwd)
    else:
        yield f


def collapse(df, rules):
    """Replace the per-file rows under each rule's prefix by summary rows (kind 'collection')."""
    drop, out = pd.Series(False, index=df.index), []
    for prefix, depth in rules:
        pre = prefix.strip("/") + "/"
        sel = df["path"].str.startswith(pre)
        if not sel.any():
            continue
        sub = df[sel]
        rel = sub["path"].str[len(pre):]
        base = (pre + rel.str.split("/").str[0]) if depth >= 1 else pd.Series(pre.rstrip("/"), index=sub.index)
        for (b, kind, fmt), g in sub.groupby([base, sub["kind"], sub["format"]]):
            ext = [list(map(float, e.split())) for e in g["extent_xmin_ymin_xmax_ymax"] if isinstance(e, str) and len(e.split()) == 4]
            u = lambda c: sorted({str(v) for v in g[c] if isinstance(v, str) and v})
            res = u("resolution")
            out.append({"path": f"{b}/*", "layer": f"[{kind}: {fmt}]", "kind": "collection", "format": fmt,
                        "geometry": f"{len(g)} {kind} files", "features": len(g), "crs": ", ".join(u("crs")[:4]),
                        "resolution": (res[0] if len(res) == 1 else f"{len(res)} values, e.g. " + "; ".join(res[:3])) if res else "",
                        "bands_dtype": "; ".join(u("bands_dtype")[:3]),
                        "extent_xmin_ymin_xmax_ymax": " ".join(f"{v:.5g}" for v in (min(e[0] for e in ext), min(e[1] for e in ext), max(e[2] for e in ext), max(e[3] for e in ext))) if ext else "",
                        "fields": "files: " + "; ".join(Path(p).stem for p in g["path"])[:300],
                        "size_mb": round(float(g["size_mb"].sum()), 1), "modified": g["modified"].max(), "status": "ok"})
        drop |= sel
    return pd.concat([df[~drop], pd.DataFrame(out)], ignore_index=True).reindex(columns=AUTO)


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
                with opened(f) as g:
                    rows = vector_rows(g, data)
            elif ext in RASTER_EXT:
                with opened(f) as g:
                    rows = raster_rows(g)
            else:
                rows = [{"layer": "", "kind": "other", "format": ext.lstrip(".")}]
        except Exception as e:
            rows = [{"layer": "", "kind": "unreadable", "format": ext.lstrip("."), "geometry": str(e)[:100]}]
        out += [{**common, **r} for r in rows]
    df = pd.DataFrame(out).reindex(columns=AUTO)
    if COLLAPSE.exists():
        rules = [(r.prefix, int(r.depth)) for r in pd.read_csv(COLLAPSE).itertuples()]
        df = collapse(df, rules)
    return df


def main():
    data = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("REPEAT_DATA") or HUB.parent / "_data")
    new = scan(data).fillna("")
    key = ["path", "layer"]
    if CSV.exists():
        old = pd.read_csv(CSV, dtype=str).fillna("")
        merged = new.merge(old[key + MANUAL], on=key, how="left").fillna("")
        gone = old.merge(new[key], on=key, how="left", indicator=True)
        gone = gone[gone["_merge"] == "left_only"].drop(columns="_merge")
        pre = tuple(r.prefix.strip("/") + "/" for r in pd.read_csv(COLLAPSE).itertuples()) if COLLAPSE.exists() else ()
        gone = gone[~gone["path"].str.startswith(pre) | gone["path"].str.endswith("/*")] if pre else gone
        gone = gone[~gone["path"].str.lower().str.endswith(tuple(SKIP_EXT))]
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
          "band type and modification date. Folders listed in [sites/catalog_collapse.csv](../sites/catalog_collapse.csv) are summarised as `collection` rows (file count, CRS and resolutions found, file names) instead of file by file.", "",
          "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in merged.iterrows():
        md.append("| " + " | ".join(str(r[c]).replace("|", "/") for c in cols) + " |")
    MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(merged)} rows from {data} -> {CSV}, {MD}")


if __name__ == "__main__":
    main()
