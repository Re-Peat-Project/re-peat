"""National data availability for the full chain: one row per registry KHG (865), from the files in the data folder only.

    python tools/khg_availability.py [--only CODE ...] [--workers N]

No downloads and no Earth Engine: products fetched per KHG on demand (DeltaDTM, DEMNAS, ICESat-2, forcing) are listed as
fetchable, and the facts that need Earth Engine (share of the KHG below 10 m, where DeltaDTM is defined; the KHG's own dry
window) are left for a second pass. Per KHG:
  identity      code, name, island, province, kabupaten, registry area; boundary matched in batas_khg_indonesia.gpkg
  derived       area from the boundary, centroid, UTM EPSG, time zone (WIB/WITA/WIT from the province)
  peat depth    best modelled peat-depth raster (national.peat_depth_dirs) and the share of the KHG it covers with depth > 0;
                share with a KLHK FEG 1:50,000 peat-thickness class (klhk_khg_feg_50k.gpkg, layer feg_50k, field peat_thick);
                share with a BBSDLP 1:50k depth class; and the source the chain should use, in this order: modelled raster,
                FEG 50k classes, BBSDLP classes, PEATGRIDS v2.0.1 (1 km, low confidence) for the rest (peat_depth_source)
  LiDAR         share of the KHG covered by valid cells of any raster under national.lidar_dirs
  canals        mapped length by class (KODE_KANAL) and density, national.canals
  licences      share of the KHG under managed licences (PBPH, Perkebunan Kelapa Sawit) and under any licence
  blocks        existing BRGM canal blocks (realised), national.blocks
  stations      SiTMAT stations by kind (stations_geo.csv, matched by KHG name)
and a run class (rules in classify()). Writes sites/khg_availability.csv and docs/20-khg-availability.md; columns added by
tools/khg_availability_ee.py (the Earth Engine pass) are kept from the previous table.
Coverage shares of rasters are sampled on a grid of at most 150 x 150 points over the KHG (inside points only).
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

HUB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HUB / "tools"))
from pipeline import config  # noqa: E402

S = config.load()
sys.path.insert(0, str(S.ws / "repeat-common" / "src"))
from repeat_common import khg as K  # noqa: E402
from repeat_common.gee import BOUNDARY  # noqa: E402

OUT_CSV = HUB / "sites" / "khg_availability.csv"
OUT_MD = HUB / "docs" / "20-khg-availability.md"
EA = "EPSG:6933"   # equal-area, for area shares
MANAGED = ("PBPH", "Perkebunan Kelapa Sawit")
LICENCES = "landstatus/ALL_Updade__IZIN_USAHA__PBPH_Perkebunan_HTRKM_Tambang__2025.gpkg"
WIB = ["aceh", "sumatera", "riau", "jambi", "bengkulu", "lampung", "bangka", "kepulauan", "kalimantan barat", "kalimantan tengah",
       "banten", "jakarta", "jawa", "yogyakarta"]
WITA = ["kalimantan selatan", "kalimantan timur", "kalimantan utara", "sulawesi", "gorontalo", "bali", "nusa tenggara"]
WIT = ["maluku", "papua"]


def tz_of(province: str) -> int | None:
    p = str(province).lower().strip(' "')
    p = re.split(r"[,;/]", p)[0].strip()
    if p.startswith("kepulauan riau") or p.startswith("kepulauan-riau"):
        return 7
    for hours, keys in ((9, WIT), (8, WITA), (7, WIB)):   # WIT/WITA first: 'sulawesi' and 'maluku' are not WIB
        if any(p.startswith(k) for k in keys):
            return hours
    return None


def utm_epsg(lon: float, lat: float) -> int:
    return (32600 if lat >= 0 else 32700) + int((lon + 180) // 6) + 1


def raster_index(dirs: list[str], exts=(".tif", ".img")) -> list[tuple[str, tuple]]:
    import rasterio
    from rasterio.warp import transform_bounds
    out = []
    for d in dirs:
        for f in glob.glob(str(S.data / d / "**" / "*"), recursive=True):
            if not f.lower().endswith(exts):
                continue
            try:
                with rasterio.open(f) as r:
                    if r.crs is None:
                        continue
                    out.append((f, transform_bounds(r.crs, "EPSG:4326", *r.bounds)))
            except Exception:
                continue
    return out


def raster_share(geom, index, n=150) -> tuple[str | None, float]:
    """Best raster (most valid cells inside the KHG) and its share, valid = finite and > 0 (peat depth) or finite (LiDAR)."""
    import rasterio
    from rasterio.warp import transform
    from shapely import contains_xy
    from shapely.geometry import box
    xmin, ymin, xmax, ymax = geom.bounds
    gx, gy = np.meshgrid(np.linspace(xmin, xmax, n), np.linspace(ymin, ymax, n))
    inside = contains_xy(geom, gx, gy)
    px, py = gx[inside], gy[inside]
    if len(px) == 0:
        return None, 0.0
    best, share = None, 0.0
    for f, b in index:
        if not geom.intersects(box(*b)):
            continue
        try:
            with rasterio.open(f) as r:
                xs, ys = transform("EPSG:4326", r.crs, px.tolist(), py.tolist())
                v = np.array([x[0] for x in r.sample(zip(xs, ys))], float)
                if r.nodata is not None:
                    v[v == r.nodata] = np.nan
                v[(v < -100) | (v > 1e5)] = np.nan
        except Exception:
            continue
        sh = float(np.mean(np.isfinite(v) & (v > 0))) if "PeatDepth" in f else float(np.mean(np.isfinite(v)))
        if sh > share:
            best, share = f, sh
    return best, share


def per_khg(job):
    code, geom_wkb, peat_idx, lidar_idx = job
    from shapely import wkb
    g = wkb.loads(geom_wkb)
    pf, ps = raster_share(g, peat_idx)
    lf, ls = raster_share(g, lidar_idx)
    rel = lambda p: None if p is None else Path(p).relative_to(S.data).as_posix()
    return code, rel(pf), round(ps, 3), rel(lf), round(ls, 3)


def share_by(khg_ea: gpd.GeoDataFrame, layer: gpd.GeoDataFrame, col: str) -> pd.Series:
    """Share of each KHG area covered by the (dissolved) layer."""
    if layer.empty:
        return pd.Series(0.0, index=khg_ea.code)
    lay = layer.to_crs(EA)[["geometry"]]
    lay["geometry"] = lay.geometry.make_valid()
    hit = gpd.overlay(khg_ea[["code", "geometry"]], lay.dissolve(), how="intersection", keep_geom_type=True)
    a = hit.assign(a=hit.area).groupby("code").a.sum()
    return (a / khg_ea.set_index("code").area).reindex(khg_ea.code).fillna(0).round(3).rename(col)


def peat_source(r) -> str:
    """Peat depth for the chain, first that covers at least half the KHG."""
    if r.peat_model_share >= 0.5:
        return "modelled raster"
    if r.feg50k_share >= 0.5:
        return "FEG 50k classes"
    if r.bbsdlp_share >= 0.5:
        return "BBSDLP classes"
    return "PEATGRIDS (low confidence)"


def classify(r) -> str:
    """Run class. A: full chain with measured inputs; B: runs with a fallback peat depth; C: runs but block design and the
    neraca model have little to act on; X: cannot run."""
    if not r.boundary_matched:
        return "X: boundary not found"
    canals = r.canal_km_total > 0
    if not canals:
        return "C: no mapped canals"
    if r.peat_depth_source == "modelled raster":
        return "A: modelled peat depth and mapped canals"
    if r.peat_depth_source != "PEATGRIDS (low confidence)":
        return "B1: peat depth from 1:50k classes"
    return "B2: peat depth from PEATGRIDS only"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="registry codes (without KHG.), for a quick test")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    a = ap.parse_args()
    reg = pd.DataFrame(K.registry())
    reg["code"] = reg.khg_code.str[4:]
    if a.only:
        reg = reg[reg.code.isin(a.only)]
    print(f"{len(reg)} KHG in the registry", flush=True)

    b = gpd.read_file(S.data / BOUNDARY[0], layer=BOUNDARY[1])
    b["n"] = b[BOUNDARY[2]].map(K.norm)
    bd = b[["n", "geometry"]].dissolve("n")
    reg["n"] = reg.name.map(K.norm)
    reg["boundary_matched"] = reg.n.isin(bd.index)
    k = gpd.GeoDataFrame(reg[reg.boundary_matched].merge(bd, left_on="n", right_index=True), geometry="geometry", crs=b.crs)
    k["geometry"] = k.geometry.make_valid()
    kll = k.to_crs(4326)
    kea = k.to_crs(EA)
    c = kll.geometry.representative_point()
    facts = pd.DataFrame({"code": k.code.values, "area_ha": (kea.area / 1e4).round(0).values, "lon": c.x.round(3).values,
                          "lat": c.y.round(3).values})
    facts["utm_epsg"] = [utm_epsg(x, y) for x, y in zip(facts.lon, facts.lat)]
    print(f"boundaries matched: {len(k)}; unmatched: {int((~reg.boundary_matched).sum())}", flush=True)

    # rasters: modelled peat depth and LiDAR
    peat_idx = raster_index(S["national"]["peat_depth_dirs"])
    lidar_idx = raster_index(S["national"]["lidar_dirs"] + ["lidar_pulau_padang_2016"])   # the 2 m Pulau Padang DTM is outside lidar_dirs
    print(f"rasters indexed: peat depth {len(peat_idx)}, LiDAR {len(lidar_idx)}", flush=True)
    jobs = [(cd, g.wkb, peat_idx, lidar_idx) for cd, g in zip(kll.code, kll.geometry)]
    rows = []
    with ProcessPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(per_khg, jobs, chunksize=4)):
            rows.append(r)
            if (i + 1) % 100 == 0:
                print(f"  rasters: {i + 1}/{len(jobs)}", flush=True)
    rs = pd.DataFrame(rows, columns=["code", "peat_model_file", "peat_model_share", "lidar_file", "lidar_share"])

    # national vectors
    bbox = tuple(kll.total_bounds)
    bb = gpd.read_file(S.data / "kedalaman_gambut_bbsdlp.gpkg", bbox=bbox)
    s_bbsdlp = share_by(kea, bb, "bbsdlp_share")
    feg = gpd.read_file(S.data / "klhk_khg_feg_50k.gpkg", layer="feg_50k", bbox=bbox)
    t = feg.peat_thick.astype(str).str.strip()
    s_feg = share_by(kea, feg[feg.peat_thick.notna() & (t != "") & (t.str.lower() != "none")], "feg50k_share")
    print("BBSDLP and FEG 50k done", flush=True)
    lic = gpd.read_file(S.data / LICENCES, bbox=bbox)
    licf = next((f for f in ("IZIN_USAHA", "izin_usaha", "JENIS_IZIN") if f in lic.columns), None)
    s_lic_any = share_by(kea, lic, "licence_share_any")
    s_lic_man = share_by(kea, lic[lic[licf].isin(MANAGED)] if licf else lic.iloc[0:0], "licence_share_managed")
    print("licences done", flush=True)
    bl = gpd.read_file(S.data / S["national"]["blocks"]["path"], bbox=bbox)
    where = S["national"]["blocks"].get("where")
    if where:
        bl = bl.query(where)
    nb = gpd.sjoin(bl.to_crs(EA)[["geometry"]], kea[["code", "geometry"]], predicate="within").groupby("code").size()
    print("blocks done", flush=True)
    can = gpd.read_file(S.data / S["national"]["canals"]["path"], bbox=bbox)
    cf = next((f for f in ("KODE_KANAL", "KET_KANAL") if f in can.columns), None)
    can = can[[cf, "geometry"]] if cf else can[["geometry"]].assign(KODE_KANAL=0)
    cut = gpd.overlay(can.to_crs(EA), kea[["code", "geometry"]], how="intersection", keep_geom_type=True)
    # lengths in each KHG's UTM zone (EPSG:6933 distorts lengths)
    lens = []
    epsg = dict(zip(facts.code, facts.utm_epsg))
    for cd, grp in cut.groupby("code"):
        L = grp.to_crs(epsg[cd]).length / 1000
        lens.append(pd.DataFrame({"code": cd, "cls": grp[cf or "KODE_KANAL"].astype(str).values, "km": L.values}))
    cl = pd.concat(lens).pivot_table(index="code", columns="cls", values="km", aggfunc="sum").fillna(0) if lens else pd.DataFrame()
    cl.columns = [f"canal_km_{x}" for x in cl.columns]
    print("canals done", flush=True)
    st = pd.read_csv(S.ws / "repeat-sitmat" / "sitmat_out" / "processed" / "stations_geo.csv")
    st["n"] = ("KHG " + st.khg_name.astype(str)).map(K.norm)
    stc = st.dropna(subset=["khg_name"]).pivot_table(index="n", columns="kind", values="station_id", aggfunc="count").fillna(0).astype(int)
    stc.columns = [f"stations_{x}" for x in stc.columns]

    out = reg[["code", "name", "island", "province", "kabupaten", "area_ha_kepmen", "boundary_matched", "n"]].merge(facts, on="code", how="left")
    out["tz_hours"] = out.province.map(tz_of)
    out = out.merge(rs, on="code", how="left")
    for s_ in (s_bbsdlp, s_feg, s_lic_any, s_lic_man):
        out = out.merge(s_.reset_index().rename(columns={"index": "code"}), on="code", how="left")
    out["blocks_brgm"] = out.code.map(nb).fillna(0).astype(int)
    out = out.merge(cl, left_on="code", right_index=True, how="left")
    kmcols = [x for x in out.columns if x.startswith("canal_km_")]
    out[kmcols] = out[kmcols].fillna(0).round(1)
    out["canal_km_total"] = out[kmcols].sum(axis=1).round(1)
    out["canal_density_km_per_km2"] = (out.canal_km_total / (out.area_ha / 100)).round(3)
    out = out.merge(stc, left_on="n", right_index=True, how="left").drop(columns="n")
    scols = [x for x in out.columns if x.startswith("stations_")]
    out[scols] = out[scols].fillna(0).astype(int)
    for col in ("peat_model_share", "lidar_share", "bbsdlp_share", "feg50k_share", "licence_share_any", "licence_share_managed"):
        out[col] = out[col].fillna(0)
    out["peat_depth_source"] = out.apply(peat_source, axis=1)
    out["run_class"] = out.apply(classify, axis=1)
    if OUT_CSV.exists() and not a.only:                     # keep the Earth Engine pass (tools/khg_availability_ee.py)
        prev = pd.read_csv(OUT_CSV, dtype={"code": str})
        keep = [c for c in prev.columns if c not in out.columns]
        if keep:
            out = out.merge(prev[["code"] + keep], on="code", how="left")
    out["fetch_on_demand"] = "DeltaDTM, DEMNAS, ICESat-2, rain and ET (Earth Engine / SlideRule)"
    out.to_csv(OUT_CSV, index=False)
    write_md(out)
    if "deltadtm_share" in out.columns:
        import khg_availability_ee
        khg_availability_ee.add_md(out)
    print(f"wrote {OUT_CSV.relative_to(HUB)} and {OUT_MD.relative_to(HUB)}")


def write_md(d: pd.DataFrame) -> None:
    n = len(d)
    ha = d.area_ha.fillna(0)
    def row(label, m):
        return f"| {label} | {int(m.sum())} | {100 * m.mean():.0f}% | {ha[m].sum() / 1e6:.1f} |"
    L = [f"# 20 National data availability per KHG", "",
         f"Generated by `tools/khg_availability.py` on {date.today().isoformat()}; do not edit. Table: `sites/khg_availability.csv` "
         f"(one row per registry KHG). From the files in the data folder only; DeltaDTM, DEMNAS, ICESat-2 and forcing are fetched per KHG "
         "when the chain runs. Not yet included (needs Earth Engine): the share of each KHG below 10 m, where DeltaDTM is defined, and the "
         "KHG's own dry window.", "",
         "| | KHG | share of KHG | area (Mha) |", "|---|---|---|---|",
         row("in the registry", pd.Series(True, index=d.index)),
         row("boundary found", d.boundary_matched.astype(bool)),
         row("modelled peat depth covers >= 50%", d.peat_model_share >= 0.5),
         row("KLHK FEG 1:50k peat-thickness classes cover >= 50%", d.feg50k_share >= 0.5),
         row("BBSDLP depth classes cover >= 50%", d.bbsdlp_share >= 0.5),
         row("any of the three covers >= 50%", d.peat_depth_source != "PEATGRIDS (low confidence)"),
         row("LiDAR covers >= 90%", d.lidar_share >= 0.9),
         row("mapped canals", d.canal_km_total > 0),
         row("existing BRGM blocks", d.blocks_brgm > 0),
         row("any SiTMAT station", d[[c for c in d.columns if c.startswith("stations_")]].sum(axis=1) > 0),
         row("community SiTMAT station", d.get("stations_community", pd.Series(0, index=d.index)) > 0), "",
         "## Run classes", "", "| run class | KHG | area (Mha) |", "|---|---|---|"]
    for cls, g in d.groupby("run_class"):
        L.append(f"| {cls} | {len(g)} | {g.area_ha.fillna(0).sum() / 1e6:.1f} |")
    L += ["", "## Peat depth source for the chain", "", "| source | KHG | area (Mha) |", "|---|---|---|"]
    for src, g in d.groupby("peat_depth_source"):
        L.append(f"| {src} | {len(g)} | {g.area_ha.fillna(0).sum() / 1e6:.1f} |")
    L += ["", "## By island", "", "| island | KHG | area (Mha) | modelled peat depth | mapped canals | any station |", "|---|---|---|---|---|---|"]
    for isl, g in d.groupby("island"):
        st = g[[c for c in g.columns if c.startswith("stations_")]].sum(axis=1) > 0
        L.append(f"| {isl} | {len(g)} | {g.area_ha.fillna(0).sum() / 1e6:.1f} | {int((g.peat_model_share >= 0.5).sum())} | "
                 f"{int((g.canal_km_total > 0).sum())} | {int(st.sum())} |")
    L += ["", "## By time zone", "", "| time zone (UTC+) | KHG |", "|---|---|"]
    L += [f"| {'unknown' if pd.isna(t) else int(t)} | {len(g)} |" for t, g in d.groupby(d.tz_hours, dropna=False)]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
