"""Per-KHG data recap: what is on disk for each selected KHG, at what resolution, and what is missing.

    python tools/khg_data_recap.py [DATA_DIR] [--workers N]   # DATA_DIR defaults to $REPEAT_DATA, then ../_data

Reads the KHG list from sites/selected_khg.csv (plus Air Banyuasin - Air Lalang, the candidate for
cawang-lalang), the datasets from sites/khg_recap_sources.csv (theme, glob relative to DATA_DIR or an
absolute path) and SiTMAT stations from $SITMAT_PROCESSED (default ../repeat-sitmat/sitmat_out/processed).
Raster coverage is the share of the KHG area with valid pixels, counted at native resolution in blocks;
raster x KHG jobs run in parallel. Vectors report features, length or area share inside the KHG.

Writes sites/khg_data_recap.csv (long table) and docs/16-khg-data-recap.md.
Needs geopandas, pyogrio, rasterio, pandas.
"""
import argparse
import os
import re
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import transform_bounds, transform_geom
from rasterio.windows import Window, from_bounds
from shapely.geometry import box, mapping, shape

HUB = Path(__file__).resolve().parents[1]
SOURCES = HUB / "sites" / "khg_recap_sources.csv"
CSV = HUB / "sites" / "khg_data_recap.csv"
MD = HUB / "docs" / "16-khg-data-recap.md"
BOUNDARY = ("batas_khg_indonesia.gpkg", "nama__khg__indonesia__2017__rev_tipologi")
EXTRA_KHG = [("Sumatera Selatan", "candidate for cawang-lalang", "KHG Air Banyuasin - Air Lalang")]
BLOCK = 4096
MIN_COVER = 1.0  # % of the KHG; smaller overlaps are edge slivers of a neighbouring KHG's file
THEMES = ["lidar_dtm", "modelled_dtm", "demnas", "contour", "peat_depth", "canals", "rivers", "infrastructure", "canal_blocks", "tmat"]


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"^KHG ", "", str(s))).strip().lower()


def res_m(d):
    r = abs(d.res[0])
    return round(r * 111320, 1) if d.crs.is_geographic else round(r, 2)


def raster_cover(job):
    """Share of the KHG with valid pixels, read block by block at native resolution."""
    path, khg, geom_wgs = job
    with rasterio.open(path) as d:
        if d.crs is None:
            return None
        geom = transform_geom("EPSG:4326", d.crs, geom_wgs)
        gb = box(*rasterio.features.bounds(geom))
        if not gb.intersects(box(*d.bounds)):
            return None
        w = from_bounds(*gb.intersection(box(*d.bounds)).bounds, d.transform).round_offsets().round_lengths()
        w = w.intersection(Window(0, 0, d.width, d.height))
        inside = valid = 0
        vals = []
        for r0 in range(int(w.row_off), int(w.row_off + w.height), BLOCK):
            for c0 in range(int(w.col_off), int(w.col_off + w.width), BLOCK):
                b = Window(c0, r0, min(BLOCK, w.col_off + w.width - c0), min(BLOCK, w.row_off + w.height - r0))
                m = geometry_mask([geom], (int(b.height), int(b.width)), d.window_transform(b), invert=True)
                if not m.any():
                    continue
                a = d.read(1, window=b).astype("float64")
                ok = np.isfinite(a) & (a > -100) & (a < 1e5)
                if d.nodata is not None:
                    ok &= a != d.nodata
                inside += m.sum()
                valid += (ok & m).sum()
                if (ok & m).any():
                    vals.append(a[ok & m][:: max(1, (ok & m).sum() // 20000)])
        # the KHG may extend past the raster, so divide by the whole KHG area (raster CRS units)
        cover = 100 * valid * abs(d.res[0] * d.res[1]) / shape(geom).area
        v = np.concatenate(vals) if vals else np.array([])
        return {
            "khg": khg, "path": path, "res_m": res_m(d), "crs": d.crs.to_string(),
            "coverage_pct": round(min(cover, 100.0), 1),
            "summary": f"p2-p98 {np.percentile(v, 2):.1f}..{np.percentile(v, 98):.1f}" if v.size else "",
        }


def vector_stats(path, layer, field, khg, geom_wgs):
    info = pyogrio.read_info(path, layer=layer)
    crs = info["crs"] or "EPSG:4326"
    geom = gpd.GeoSeries([geom_wgs], crs=4326).to_crs(crs).iloc[0]
    df = pyogrio.read_dataframe(path, layer=layer, bbox=tuple(geom.bounds), columns=[field] if field else [])
    if df.empty:
        return None
    df = df.set_crs(crs, allow_override=True)
    df = df[df.intersects(geom)]
    if df.empty:
        return None
    utm = gpd.GeoSeries([geom_wgs], crs=4326).estimate_utm_crs()
    clip = df.geometry.intersection(geom).to_crs(utm)
    gt = info["geometry_type"].replace(" Z", "").replace("Multi", "")
    out = {"khg": khg, "path": path, "features": len(df), "crs": str(crs)}
    if gt == "LineString":
        out["length_km"] = round(clip.length.sum() / 1000, 1)
    elif gt == "Polygon":
        out["coverage_pct"] = round(100 * clip.union_all().area / gpd.GeoSeries([geom_wgs], crs=4326).to_crs(utm).area.iloc[0], 1)
    if field:
        s = df[field]
        if pd.api.types.is_numeric_dtype(s):
            out["summary"] = f"{field} {s.min():g}..{s.max():g}"
        else:
            vc = s.astype(str).value_counts()
            out["summary"] = "; ".join(f"{k} {v}" for k, v in vc.head(4).items()) + (f"; +{len(vc) - 4} more" if len(vc) > 4 else "")
    return out


def tmat_rows(khgs, sitmat):
    st = pd.read_csv(sitmat / "stations_geo.csv")
    wl = pd.read_csv(sitmat / "daily_long.csv", usecols=["station_id", "date", "water_level_cm"]).dropna(subset=["water_level_cm"])
    per = wl.groupby("station_id").agg(days=("date", "size"), first=("date", "min"), last=("date", "max"))
    st = st.join(per, on="station_id")
    st["k"] = st["khg_name"].map(norm)
    rows = []
    for name in khgs:
        s = st[st.k == norm(name)]
        if s.empty:
            continue
        rec = s.dropna(subset=["days"])
        rows.append({
            "khg": name, "path": "SiTMAT stations_geo.csv + daily_long.csv", "features": len(s),
            "summary": "; ".join(f"{k} {v}" for k, v in s.kind.value_counts().items())
            + (f"; {len(rec)} with water level, {int(rec.days.sum())} station-days, {rec['first'].min()}..{rec['last'].max()}" if len(rec) else "; no water-level records"),
        })
    return rows


def expand(data, pattern, exclude):
    p = Path(pattern)
    files = [p] if p.is_absolute() and p.exists() else sorted(data.glob(pattern))
    if isinstance(exclude, str) and exclude:
        files = [f for f in files if not re.search(exclude, f.name)]
    return files


def label(row):
    if row.theme == "tmat":
        return f"{int(row.features)} stations"
    t = f"{row.tag} " if isinstance(row.get("tag"), str) else ""
    if pd.notna(row.get("res_m")):
        return f"{t}{row.res_m:g} m, {row.coverage_pct:g}%"
    if pd.notna(row.get("length_km")):
        return f"{t}{row.length_km:,.0f} km"
    if pd.notna(row.get("coverage_pct")):
        return f"{t}{row.coverage_pct:g}% area"
    return f"{t}{int(row.features)} pts"


def best(g):
    """Finest raster with >= 50 % coverage, else the widest; vectors: the largest."""
    if g.res_m.notna().any():
        full = g[g.coverage_pct >= 50]
        r = full.sort_values("res_m").iloc[0] if len(full) else g.sort_values("coverage_pct").iloc[-1]
    else:
        lidar = g[g.tag.astype(str).str.startswith("LiDAR")]
        r = (lidar if len(lidar) else g).sort_values(["length_km", "features"], na_position="first").iloc[-1]
    return label(r)


def write_md(df, khgs, data):
    lines = [
        "# 16 Per-KHG data recap",
        "",
        f"Generated by `tools/khg_data_recap.py` on {date.today()} from `{data.name}` and SiTMAT. Do not edit by hand; rerun.",
        "Raster cells: finest resolution covering at least half the KHG, with its coverage. Coverage counted at native resolution.",
        "Long table: [sites/khg_data_recap.csv](../sites/khg_data_recap.csv). Sources: [sites/khg_recap_sources.csv](../sites/khg_recap_sources.csv).",
        "",
        "## Overview",
        "",
        "| KHG | role | " + " | ".join(THEMES) + " |",
        "|---|---|" + "---|" * len(THEMES),
    ]
    for prov, role, name in khgs:
        g = df[df.khg == name]
        cells = [best(g[g.theme == t]) if (g.theme == t).any() else "–" for t in THEMES]
        lines.append(f"| {name.replace('KHG ', '')} | {role} | " + " | ".join(cells) + " |")
    lines += ["", "## Gaps per module", "",
              "| KHG | delineation (survey DTM, canals, rivers) | DEM preprocessing (DEM + LiDAR benchmark) | neraca (DTM, peat depth, canals, TMAT) |",
              "|---|---|---|---|"]
    for prov, role, name in khgs:
        g = df[df.khg == name]
        has = lambda t, cov=50: ((g.theme == t) & ((g.coverage_pct.fillna(100) >= cov))).any()  # noqa: E731
        dtm = has("lidar_dtm") or has("modelled_dtm") or has("demnas")
        miss = lambda items: ", ".join(k for k, ok in items if not ok) or "ok"  # noqa: E731
        lines.append(f"| {name.replace('KHG ', '')} | "
                     + miss([("LiDAR DTM", has("lidar_dtm")), ("canals", has("canals")), ("rivers", has("rivers"))]) + " | "
                     + miss([("DEM to correct", has("demnas") or has("modelled_dtm")), ("LiDAR benchmark", has("lidar_dtm"))]) + " | "
                     + miss([("DTM", dtm), ("peat depth", has("peat_depth")), ("canals", has("canals")), ("TMAT stations", has("tmat"))]) + " |")
    lines += ["", "Contour sets were traced from the LiDAR rasters listed with them: see `tools/check_contour_source.py` and `reports/investigations/contour_source.csv`.",
              "Elevation layers outside `_data` (open DEMs fetched by repeat-dem, ICESat-2) and climate inputs (cloud) are not listed.", "",
              "## Per KHG", ""]
    for prov, role, name in khgs:
        g = df[df.khg == name]
        lines += [f"### {name.replace('KHG ', '')} ({prov}, {role})", "",
                  "| theme | dataset | res (m) | coverage | features | length (km) | values |", "|---|---|---|---|---|---|---|"]
        for _, r in g.iterrows():
            f = lambda v, fmt="{:g}": "" if pd.isna(v) else fmt.format(v)  # noqa: E731
            lines.append(f"| {r.theme} | `{r.dataset}` | {f(r.res_m)} | {f(r.coverage_pct, '{:g}%')} | {f(r.features, '{:,.0f}')} | {f(r.length_km, '{:,.0f}')} | {r.summary if pd.notna(r.summary) else ''} |")
        if g.empty:
            lines.append("| – | nothing found | | | | | |")
        lines.append("")
    MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", nargs="?")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    data = Path(a.data or os.environ.get("REPEAT_DATA") or HUB.parent / "_data").resolve()
    sitmat = Path(os.environ.get("SITMAT_PROCESSED") or HUB.parent / "repeat-sitmat" / "sitmat_out" / "processed")

    sel = pd.read_csv(HUB / "sites" / "selected_khg.csv").dropna(subset=["khg_name_in_gpkg"])
    khgs = [(r.province, r.role, r.khg_name_in_gpkg) for r in sel.itertuples()] + EXTRA_KHG
    b = gpd.read_file(data / BOUNDARY[0], layer=BOUNDARY[1]).to_crs(4326)
    b = b[b.NAMA_KHG.isin([k[2] for k in khgs])].dissolve("NAMA_KHG")
    geoms = {n: b.geometry[n] for n in b.index}

    src = pd.read_csv(SOURCES)
    rjobs, rows, seen = [], [], set()
    for s in src.itertuples():
        for f in expand(data, s.pattern, s.exclude):
            if str(f.resolve()).lower() in seen:  # Windows glob is case-insensitive, patterns may overlap
                continue
            seen.add(str(f.resolve()).lower())
            meta = {"theme": s.theme, "tag": s.tag, "note": s.note}
            if f.suffix.lower() in {".tif", ".img", ".sdat", ".jp2"}:
                rjobs += [((str(f), k, mapping(geoms[k])), meta) for k in geoms]
            else:
                for k in geoms:
                    r = vector_stats(str(f), s.layer if isinstance(s.layer, str) else None,
                                     s.summary_field if isinstance(s.summary_field, str) else None, k, geoms[k])
                    if r and r.get("coverage_pct", 100) >= MIN_COVER:
                        rows.append({**meta, **r})
    # JPEG2000 tiles can span the whole raster height (DEMNAS Sumatra: 20000 x 163366 px), so decoding them in
    # parallel runs out of memory; they run one at a time after the pool, still at native resolution.
    serial = [j for j in rjobs if j[0][0].lower().endswith(".jp2")]
    pooled = [j for j in rjobs if j not in serial]
    print(f"{len(pooled)} raster x KHG jobs on {a.workers} workers, {len(serial)} JPEG2000 jobs serially", flush=True)
    with ProcessPoolExecutor(a.workers) as ex:
        done = list(zip(pooled, ex.map(raster_cover, [j for j, _ in pooled], chunksize=4)))
    done += [(j, raster_cover(j[0])) for j in serial]
    for (job, meta), r in done:
        if r and r["coverage_pct"] >= MIN_COVER:
            rows.append({**meta, **r})
    rows += [{"theme": "tmat", "note": "SiTMAT water-table stations", **r} for r in tmat_rows(list(geoms), sitmat)]

    df = pd.DataFrame(rows)
    for c in ["res_m", "coverage_pct", "features", "length_km", "summary"]:
        if c not in df:
            df[c] = np.nan
    df["dataset"] = [Path(p).relative_to(data).as_posix() if Path(p).is_absolute() and Path(p).is_relative_to(data) else p for p in df.path]
    df["theme"] = pd.Categorical(df.theme, THEMES, ordered=True)
    order = {k[2]: i for i, k in enumerate(khgs)}
    df = df.sort_values(["khg", "theme", "res_m", "coverage_pct"], key=lambda s: s.map(order) if s.name == "khg" else s,
                        ascending=[True, True, True, False])
    cols = ["khg", "theme", "tag", "dataset", "res_m", "coverage_pct", "features", "length_km", "crs", "summary", "note"]
    df[cols].to_csv(CSV, index=False)
    write_md(df, khgs, data)
    print("wrote", CSV, "and", MD)


if __name__ == "__main__":
    main()
