"""Test which raster a contour set was traced from.

    python tools/check_contour_source.py [DATA_DIR]                       # the LiDAR contour sets
    python tools/check_contour_source.py [DATA_DIR] --contour kontur_108khg_BRGM.gpkg --field Contour \
        --rasters "dem/**/*.tif" "dem/**/*.jp2" "Peat depth and DTM/DTM_*/**/*.tif" ... --out brgm_contour_source.csv

DATA_DIR defaults to $REPEAT_DATA, then ../_data. Raster globs are relative to DATA_DIR.
With --zones batas_khg_indonesia.gpkg:nama__khg__indonesia__2017__rev_tipologi:NAMA_KHG the counts are split per KHG:
rasters that share a lattice (the per-KHG modelled DTMs) otherwise also score on vertices of their neighbours.

ArcGIS Contour (and GDAL contour) joins points interpolated linearly between neighbouring cell centres, so a
contour traced from a raster has (a) its vertices on that raster's cell-centre rows or columns and (b) the raster
value, interpolated along that row or column, equal to the contour value. For each contour set and each overlapping
raster this reports the share of vertices on the grid (a raster that was not the source gives about 2 * TOL * 2 = 4 %)
and, for those vertices, the gap between the interpolated raster value and the contour value. Every vertex is used,
at native raster resolution: contours are read in chunks of features and rasters in blocks, so large files fit.

Writes reports/investigations/<out> (default contour_source.csv).
Needs pyogrio, rasterio, shapely, pyproj, pandas.
"""
import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pyogrio
import rasterio
import rasterio.warp
import shapely
from pyproj import Transformer
from rasterio.windows import Window
from shapely.geometry import box

HUB = Path(__file__).resolve().parents[1]
TOL = 0.01  # fraction of a cell
GATE = 0.10  # read pixel values only where at least this share of vertices is on the grid (chance is about 0.04)
CHUNK = 20000  # contour features per read
BLOCK = 2048  # raster rows / columns per read
BINS = np.concatenate([[0], np.logspace(-4, 3, 141)])  # |gap| histogram, 0.1 mm .. 1 km
LIDAR_CONTOURS = [
    "lidar_klhk/dem_25m/lidar__kontur_jambi__ic_25cm.shp",
    "lidar_klhk/dem_25m/lidar__kontur_jambi__ic_50cm.shp",
    "lidar_klhk/dem_25m/lidar__kontur_muba_sumsel__ic_25cm.shp",
    "lidar_klhk/dem_25m/lidar__kontur_muba_sumsel__ic_50cm.shp",
    "lidar_klhk/dem_25m/lidar__kontur_oki_sumsel__ic_25cm.shp",
    "lidar_klhk/dem_25m/lidar__kontur_oki_sumsel__ic_50cm.shp",
    "lidar_klhk/dem_25m/lidar__kontur_riau__ic_25cm.shp",
    "lidar_klhk/dem_25m/lidar__kontur_riau__ic_50cm.shp",
    "lidar_klhk/dem_25m/LIDAR__Kontur_Sugihan_Saleh_SUMSEL__IC_25cm.shp",
    "lidar_klhk/dem_25m/LIDAR__Kontur_Sugihan_Saleh_SUMSEL__IC_50cm.shp",
    "lidar_klhk/dem_25m/LIDAR_Kontur_25cm__RIAU_JAMBI_SUMSEL.shp",
    "lidar_klhk/dem_25m/LIDAR_Kontur_50cm__RIAU_JAMBI_SUMSEL.shp",
]
LIDAR_RASTERS = ["lidar_klhk/**/*.tif"]


class Tally:
    def __init__(self):
        self.inside = self.on = 0
        self.hist = np.zeros(len(BINS) - 1, np.int64)

    def add(self, inside, on, gaps):
        self.inside += inside
        self.on += on
        g = np.abs(gaps[np.isfinite(gaps)])
        self.hist += np.histogram(np.clip(g, 0, BINS[-1]), BINS)[0]

    def row(self):
        n = self.hist.sum()
        med = None
        if n:
            k = np.searchsorted(np.cumsum(self.hist), n / 2)
            med = float(BINS[k + 1])  # upper edge of the bin holding the median
        within = float(self.hist[BINS[1:] <= 0.01].sum() / n) if n else None
        return {"vertices_inside": self.inside, "on_grid_pct": round(100 * self.on / self.inside, 1) if self.inside else None,
                "median_abs_gap_m_upper": None if med is None else round(med, 4),
                "within_1cm_pct": None if within is None else round(100 * within, 1)}


def test_chunk(d, xy, z, zone, crs, tallies):
    if crs != d.crs:
        xy = np.column_stack(Transformer.from_crs(crs, d.crs, always_xy=True).transform(xy[:, 0], xy[:, 1]))
    t = d.transform
    fc = (xy[:, 0] - t.c) / t.a - 0.5
    fr = (xy[:, 1] - t.f) / t.e - 0.5
    inside = (fc >= 0) & (fr >= 0) & (fc <= d.width - 1) & (fr <= d.height - 1)
    if not inside.any():
        return
    fc, fr, z, zone = fc[inside], fr[inside], z[inside], zone[inside]
    on_col = np.abs(fc - np.round(fc)) < TOL
    on_row = (np.abs(fr - np.round(fr)) < TOL) & ~on_col
    sel = on_col | on_row
    gaps_all = np.full(len(z), np.nan)
    if sel.mean() < GATE:  # not this raster's grid: skip the pixel reads, keep the alignment count
        _tally(tallies, zone, sel, gaps_all)
        return
    # each on-grid vertex needs two neighbouring cells: (r0, c0) and (r0 + dr, c0 + dc)
    r0 = np.where(on_col, np.floor(fr), np.round(fr)).astype(np.int64)[sel]
    c0 = np.where(on_col, np.round(fc), np.floor(fc)).astype(np.int64)[sel]
    w = np.where(on_col, fr - np.floor(fr), fc - np.floor(fc))[sel]
    dr = on_col[sel].astype(np.int64)
    dc = 1 - dr
    zz = z[sel]
    gaps = np.full(len(zz), np.nan)
    br, bc = r0 // BLOCK, c0 // BLOCK
    key = br * (d.width // BLOCK + 2) + bc
    order = np.argsort(key, kind="stable")
    keys, starts = np.unique(key[order], return_index=True)
    for k, s, e in zip(keys, starts, list(starts[1:]) + [len(order)]):
        idx = order[s:e]
        R, C = int(br[idx[0]]) * BLOCK, int(bc[idx[0]]) * BLOCK
        win = Window(C, R, min(BLOCK + 1, d.width - C), min(BLOCK + 1, d.height - R))
        a = d.read(1, window=win).astype("float64")
        bad = ~np.isfinite(a) | (a < -100) | (a > 1e5)
        if d.nodata is not None:
            bad |= a == d.nodata
        a[bad] = np.nan
        rr, cc = r0[idx] - R, c0[idx] - C
        rr2 = np.minimum(rr + dr[idx], a.shape[0] - 1)
        cc2 = np.minimum(cc + dc[idx], a.shape[1] - 1)
        gaps[idx] = a[rr, cc] * (1 - w[idx]) + a[rr2, cc2] * w[idx] - zz[idx]
    gaps_all[sel] = gaps
    _tally(tallies, zone, sel, gaps_all)


def _tally(tallies, zone, sel, gaps):
    for u in np.unique(zone):
        m = zone == u
        tallies.setdefault(int(u), Tally()).add(int(m.sum()), int((sel & m).sum()), gaps[m & sel])


def run(data, contour, field, rasters, workers, zones=None):
    info = pyogrio.read_info(data / contour)
    crs, n = info["crs"], info["features"]
    cand = []
    for r in rasters:
        with rasterio.open(r) as d:
            if d.crs is None:
                continue
            cand.append((r, box(*rasterio.warp.transform_bounds(d.crs, crs, *d.bounds))))
    tallies, nvert = {}, 0
    for skip in range(0, n, CHUNK):
        df = pyogrio.read_dataframe(data / contour, columns=[field], skip_features=skip, max_features=CHUNK)
        xy, i = shapely.get_coordinates(df.geometry.values, return_index=True)
        z = df[field].to_numpy(float)[i]
        nvert += len(xy)
        zone = np.full(len(xy), -1, np.int64)
        if zones is not None:  # index of the zone polygon holding each vertex, -1 outside all
            x0, y0 = xy.min(0); x1, y1 = xy.max(0)
            for k in zones.sindex.query(box(x0, y0, x1, y1)):
                g = zones.geometry.iloc[k]
                gx0, gy0, gx1, gy1 = g.bounds
                c = (zone < 0) & (xy[:, 0] >= gx0) & (xy[:, 0] <= gx1) & (xy[:, 1] >= gy0) & (xy[:, 1] <= gy1)
                if c.any():
                    zone[np.flatnonzero(c)[shapely.contains_xy(g, xy[c, 0], xy[c, 1])]] = k
        ext = box(*xy.min(0), *xy.max(0))
        hits = [r for r, rb in cand if rb.intersects(ext)]
        for r in hits:
            tallies.setdefault(r, {})

        def one(r):
            with rasterio.open(r) as d:
                test_chunk(d, xy, z, zone, crs, tallies[r])

        with ThreadPoolExecutor(workers) as ex:  # one raster per thread; each has its own tally
            list(ex.map(one, hits))
        print(f"  {contour}: {min(skip + CHUNK, n):,}/{n:,} features", flush=True)
    rows = []
    for r, per_zone in tallies.items():
        with rasterio.open(r) as d:
            res = abs(d.res[0]) * (111320 if d.crs.is_geographic else 1)
        for k, t in per_zone.items():
            if not t.inside:
                continue
            z_name = {} if zones is None else {"zone": zones.iloc[k][zones.attrs["field"]] if k >= 0 else "(outside)"}
            rows.append({"contour": contour, "contour_vertices": nvert, **z_name, "raster": Path(r).relative_to(data).as_posix(),
                         "res_m": round(res, 2), **t.row()})
    return rows


def summarise(by_zone_csv):
    """One row per zone: the raster whose values best match the contours among those with >= 20 % of vertices on the grid.
    A: traced from this raster (>= 90 % within 1 cm); B: same grid, values differ; C: no matching raster on disk."""
    d = pd.read_csv(by_zone_csv)
    d = d[d.zone != "(outside)"]
    nv = d.groupby("zone").vertices_inside.max().rename("khg_vertices")
    cand = d[(d.on_grid_pct >= 20) & d.within_1cm_pct.notna()]
    best = cand.sort_values(["zone", "within_1cm_pct", "on_grid_pct"], ascending=[True, False, False]).groupby("zone").head(1)
    z = pd.DataFrame(nv).join(best.set_index("zone")[["raster", "vertices_inside", "on_grid_pct", "within_1cm_pct", "median_abs_gap_m_upper"]])
    z["share_of_khg_vertices"] = (100 * z.vertices_inside / z.khg_vertices).round(1)
    z["class"] = np.where(z.raster.isna(), "C: no matching raster in _data",
                          np.where(z.within_1cm_pct >= 90, "A: traced from this DTM", "B: same grid, values differ"))
    out = Path(str(by_zone_csv).replace("_by_khg.csv", "") + "_khg_summary.csv")
    z.reset_index().to_csv(out, index=False)
    print("wrote", out, z["class"].value_counts().to_dict())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", nargs="?")
    ap.add_argument("--contour", nargs="*", help="contour files relative to DATA_DIR (default: the LiDAR sets)")
    ap.add_argument("--field", default="CONTOUR")
    ap.add_argument("--rasters", nargs="*", help="raster globs relative to DATA_DIR (default: lidar_klhk/**/*.tif)")
    ap.add_argument("--exclude", default="peat_thickness|PeatDepth|test-clip", help="regex on raster paths to skip")
    ap.add_argument("--out", default="contour_source.csv")
    ap.add_argument("--zones", help="FILE:LAYER:FIELD (relative to DATA_DIR): report per zone, e.g. per KHG, instead of per raster")
    ap.add_argument("--summarise", help="only rebuild <name>_khg_summary.csv from an existing <name>_by_khg.csv")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    if a.summarise:
        return summarise(HUB / "reports" / "investigations" / a.summarise)
    data = Path(a.data or os.environ.get("REPEAT_DATA") or HUB.parent / "_data").resolve()
    import re
    rasters = sorted({p for g in (a.rasters or LIDAR_RASTERS) for p in data.glob(g)
                      if not re.search(a.exclude, p.as_posix())})
    zones = None
    if a.zones:
        import geopandas as gpd
        f, layer, field = a.zones.split(":")
        zones = gpd.read_file(data / f, layer=layer)[[field, "geometry"]]
        zones.attrs["field"] = field
    rows = []
    for c in a.contour or LIDAR_CONTOURS:
        if zones is not None:
            zones = zones.to_crs(pyogrio.read_info(data / c)["crs"])
            zones.attrs["field"] = a.zones.split(":")[2]
        rows += run(data, c, a.field, [str(r) for r in rasters], a.workers, zones)
    out = HUB / "reports" / "investigations" / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    keys = ["contour", "zone"] if zones is not None else ["contour"]
    pd.DataFrame(rows).sort_values(keys + ["on_grid_pct"], ascending=[True] * len(keys) + [False]).to_csv(out, index=False)
    print("wrote", out)
    if zones is not None and out.name.endswith("_by_khg.csv"):
        summarise(out)


if __name__ == "__main__":
    main()
