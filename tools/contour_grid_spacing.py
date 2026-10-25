"""Which grid was a contour set traced from, when the source raster is not on disk? Detect it from the vertices.

    python tools/contour_grid_spacing.py [DATA_DIR] [--khg "KHG ..." ...]

Contours traced from a raster have their vertices on the raster's cell-centre rows and columns, so many vertices share
exactly the same x (or y) and the gaps between those shared values are whole multiples of the cell size. For each KHG
(default: the KHG of kontur_108khg_BRGM.gpkg that tools/check_contour_source.py could not match to a raster on disk,
class C in reports/investigations/brgm_contour_source_khg_summary.csv) this reports, in geographic degrees and in the
KHG's UTM zone, the share of vertices on a shared value and the most common gap (the candidate cell size); and the share
of vertices on each known grid of the KLHK modelled DTMs, extended beyond the file (0.4 arcsec geographic; 10 m UTM 49S
and 50S), against about 4% by chance. Every vertex inside the KHG is used.
Writes reports/investigations/brgm_contour_grid_spacing.csv.
"""
import argparse
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import rasterio
import shapely
from pyproj import Transformer

HUB = Path(__file__).resolve().parents[1]
OUT = HUB / "reports" / "investigations" / "brgm_contour_grid_spacing.csv"
LATTICES = {  # name: a raster on the grid, extended beyond its own extent
    "0.4 arcsec geographic": "Peat depth and DTM/DTM_Kalimantan/05_Kalimantan Tengah/DTM_Sungai_Katingan_Sungai_Sebangau.tif",
    "10 m UTM 49S": "Peat depth and DTM/DTM_Kalimantan/05_Kalimantan Tengah/DTM_Model_KHG_Sungai_Katingan_Sungai_Mentaya.tif",
    "10 m UTM 50S": "Peat depth and DTM/DTM_Kalimantan/06_Kalimantan Selatan/06_Kalimantan Selatan/DTM_Model_KHG_Sungai_Barito_Sungai_Taping.tif",
    "DEMNAS 0.27 arcsec": "dem/Mosaic_DEMNAS__KHG_Pulau_Kalimantan.tif",
}
TOL = 0.01


def steps(v, ndig):
    u, c = np.unique(np.round(v, ndig), return_counts=True)
    shared = c >= 5
    d = np.round(np.diff(u[shared]), ndig)
    d = d[d > 0]
    if not len(d):
        return float(shared.sum()) / max(len(u), 1), None
    vals, cnt = np.unique(d, return_counts=True)
    return float(c[shared].sum() / len(v)), float(vals[np.argmax(cnt)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", nargs="?")
    ap.add_argument("--khg", nargs="*")
    a = ap.parse_args()
    data = Path(a.data or os.environ.get("REPEAT_DATA") or HUB.parent / "_data")
    if a.khg:
        names = a.khg
    else:
        s = pd.read_csv(HUB / "reports" / "investigations" / "brgm_contour_source_khg_summary.csv")
        names = s[s["class"].str.startswith("C")].zone.tolist()
    g = gpd.read_file(data / "batas_khg_indonesia.gpkg", layer="nama__khg__indonesia__2017__rev_tipologi").to_crs(4326)
    lat = {k: rasterio.open(data / p) for k, p in LATTICES.items()}
    rows = []
    for n in names:
        geom = g[g.NAMA_KHG == n].union_all()
        df = pyogrio.read_dataframe(data / "kontur_108khg_BRGM.gpkg", bbox=geom.bounds, columns=["Contour"])
        xy = shapely.get_coordinates(df.geometry.values)
        xy = xy[shapely.contains_xy(geom, xy[:, 0], xy[:, 1])]
        if len(xy) < 1000:
            rows.append({"khg": n, "vertices": len(xy), "note": "too few vertices"})
            continue
        utm = gpd.GeoSeries([geom], crs=4326).estimate_utm_crs()
        q = np.column_stack(Transformer.from_crs(4326, utm, always_xy=True).transform(xy[:, 0], xy[:, 1]))
        r = {"khg": n, "vertices": len(xy), "utm": utm.to_string()}
        for ax, k in (("x", 0), ("y", 1)):
            sh, st = steps(xy[:, k], 7)
            r[f"geo_{ax}_shared_pct"], r[f"geo_{ax}_modal_step_deg"] = round(100 * sh, 1), st
            sh, st = steps(q[:, k], 3)
            r[f"utm_{ax}_shared_pct"], r[f"utm_{ax}_modal_step_m"] = round(100 * sh, 1), st
        for name, d in lat.items():
            p = xy if d.crs.to_epsg() == 4326 else np.column_stack(Transformer.from_crs(4326, d.crs, always_xy=True).transform(xy[:, 0], xy[:, 1]))
            t = d.transform
            fc, fr = (p[:, 0] - t.c) / t.a - 0.5, (p[:, 1] - t.f) / t.e - 0.5
            on = (np.abs(fc - np.round(fc)) < TOL) | (np.abs(fr - np.round(fr)) < TOL)
            r[f"on_{name.replace(' ', '_')}_pct"] = round(100 * float(on.mean()), 1)
        rows.append(r)
        print(r, flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
