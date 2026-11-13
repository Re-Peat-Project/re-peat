"""Inventory of every peat depth source in the workspace, and their agreement with the PPEG peat thickness fields.

    python re-peat/tools/compare_peat_depth.py

Needs the dissolved PPEG layers (repeat-national-ppeg --layers): layers peat_thickness (PEAT_THICK) and peat_depth_bbsdlp
(KDLMN_GBT) of $REPEAT_WORK/national_profile/ppeg/ppeg_layers.gpkg. Writes to re-peat/reports/investigations/:
  peat_depth_sources.csv            one row per source: kind, files, features or pixels, CRS, resolution, units, year, provenance
  peat_depth_same_source.csv        PPEG classes against the layers they appear to come from, area per KHG and class
  peat_depth_raster_vs_class.csv    each depth raster against each PPEG class field, per class
  peat_depth_points.csv             field points against the PPEG classes
  peat_depth_comparison.md          the summary

Checks:
1. Same source? PPEG PEAT_THICK against the KLHK FEG 1:50,000 layer (klhk_khg_feg_50k.gpkg, peat_thick), and PPEG KDLMN_GBT
   against the BBSDLP 1:50,000 depth map (kedalaman_gambut_bbsdlp.gpkg, KELAS_GBT): class areas per KHG.
2. Agreement with independent data. Rasters (the modelled per-KHG depth rasters in "Peat depth and DTM" and the Saleh-Sugihan
   LiDAR-constrained thickness) are read block by block in their own CRS and resolution; the class polygons are burned into
   each block. Field points (Saleh-Sugihan 208, Tebing Tinggi 1,385) take the class they fall in.
   Reported per class: share of pixels or points whose depth lies inside the class, median depth, and agreement on the
   3 m split (protected peat function, FEG lindung).
"""
import glob
import os
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import rasterio
from rasterio.features import rasterize
import rasterio.warp
from rasterio.windows import Window

HUB = Path(__file__).resolve().parents[1]
WS = HUB.parent
DATA = Path(os.environ.get("REPEAT_DATA", WS / "_data"))
WORK = Path(os.environ.get("REPEAT_WORK", HUB / "reports"))
LAYERS = WORK / "national_profile" / "ppeg" / "ppeg_layers.gpkg"
PPEG = DATA / "ALL_Analysis_Integrasi_Tematik__PPEG_Indonesia__April_2026.gpkg"
OUT = HUB / "reports" / "investigations"
FIELDS = {"peat_thickness": "peat_thick", "peat_depth_bbsdlp": "depth_bbsdlp"}     # PPEG layer: class column
LABEL = {"peat_thickness": "PPEG PEAT_THICK", "peat_depth_bbsdlp": "PPEG KDLMN_GBT"}
SALEH = DATA / "lidar_klhk" / "sugihan_saleh_2020" / "peat_thickness"
TEBING = DATA / "Peat depth and DTM" / "Tebingtinggi.csv"
HIST = np.arange(0, 20.05, 0.05)            # depth histogram bins (m) for medians
BLOCK = 2048


def bounds_m(label):
    s = str(label).replace(",", ".")
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    if not nums:
        return np.nan, np.nan
    k = 0.01 if "cm" in s else 1.0
    return nums[0] * k, (nums[1] * k if len(nums) > 1 else np.inf)


def nice(lo, hi):
    return f">= {lo:g} m" if np.isinf(hi) else f"{lo:g}-{hi:g} m"


def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def depth_rasters():
    model = sorted(glob.glob(str(DATA / "Peat depth and DTM" / "PeatDepth_*" / "**" / "*.img"), recursive=True))
    lidar = [str(SALEH / "TopoToR_PEAT__KHG_Sugihan_Saleh__UTM_48S.tif"), str(SALEH / "CON__TopoToR_PEAT__KHG_Sugihan_Saleh__UTM_48S.tif")]
    return [(p, "modelled KHG depth raster") for p in model] + [(p, "LiDAR-based thickness (TopoToRaster)") for p in lidar if Path(p).exists()]


# --- inventory --------------------------------------------------------------------------------------------------------
def inventory():
    rows = []
    for f, label, col in [("peat_thickness", "PPEG PEAT_THICK", "PEAT_THICK"), ("peat_depth_bbsdlp", "PPEG KDLMN_GBT", "KDLMN_GBT")]:
        rows.append(dict(source=label, kind="vector classes", path=PPEG.name, files=1, count=pyogrio.read_info(PPEG)["features"],
                         crs="EPSG:4326", resolution="polygons", units="class (0.5 m steps, or BBSDLP cm classes)", year="2026 (April)",
                         provenance=f"KLH PPEG integrated analysis, field {col}"))
    i = pyogrio.read_info(DATA / "klhk_khg_feg_50k.gpkg", layer="feg_50k")
    rows.append(dict(source="KLHK FEG 1:50,000", kind="vector classes", path="klhk_khg_feg_50k.gpkg (feg_50k)", files=1, count=i["features"],
                     crs=i["crs"], resolution="1:50,000", units="class, 0.5 m steps", year="SK by KHG 2017-2024", provenance="KLHK, via BIG; field peat_thick"))
    i = pyogrio.read_info(DATA / "kedalaman_gambut_bbsdlp.gpkg")
    rows.append(dict(source="BBSDLP peat depth 1:50,000", kind="vector classes", path="kedalaman_gambut_bbsdlp.gpkg", files=1, count=i["features"],
                     crs=i["crs"], resolution="1:50,000", units="class D1-D6 (50 cm to >700 cm)", year="2019", provenance="BBSDLP (Ministry of Agriculture); field KELAS_GBT"))
    for kind, group in pd.DataFrame(depth_rasters(), columns=["path", "kind"]).groupby("kind"):
        res, crs, px = set(), set(), 0
        for p in group["path"]:
            with rasterio.open(p) as r:
                res.add(f"{r.res[0]:.3g}"); crs.add(str(r.crs.to_epsg())); px += r.width * r.height
        rows.append(dict(source=kind, kind="raster", path=str(Path(group["path"].iloc[0]).parent.parent.parent.name if kind.startswith("modelled") else SALEH.name),
                         files=len(group), count=px, crs=", ".join(sorted(crs)), resolution=", ".join(sorted(res)), units="cm, float32 (-8888 = no data)",
                         year="not stated" if kind.startswith("modelled") else "2020 (LiDAR)", provenance="KLHK delivery 'Peat depth and DTM'" if kind.startswith("modelled") else "KLHK LiDAR Sugihan-Saleh 2020"))
    clips = sorted(glob.glob(str(WS / "_khg" / "*" / "00_inputs" / "peat_depth.tif")))
    rows.append(dict(source="per-KHG clips (_khg/*/00_inputs/peat_depth.tif)", kind="raster", path="_khg", files=len(clips), count=np.nan, crs="as source",
                     resolution="as source", units="m", year="", provenance="windows of the modelled KHG rasters (local_manifest.csv); not compared again"))
    pts = pyogrio.read_info(SALEH / "PEAT_THICK__KHG_Saleh_Sugihan__UTM_48S.shp")
    rows.append(dict(source="Saleh-Sugihan survey points", kind="points", path="lidar_klhk/sugihan_saleh_2020/peat_thickness/PEAT_THICK__*.shp", files=1,
                     count=pts["features"], crs=pts["crs"], resolution="points", units="cm (P_DEPTH_CM)", year="field survey (TANGGAL_SU)", provenance="KLHK LiDAR delivery"))
    poly = pyogrio.read_info(SALEH / "TopoToR__PEAT_THICK__KHG_Sugihan_Saleh__UTM_48S.shp")
    rows.append(dict(source="Saleh-Sugihan thickness class polygons", kind="vector classes", path="TopoToR__PEAT_THICK__*.shp", files=1, count=poly["features"],
                     crs=poly["crs"], resolution="polygons", units="class", year="2020", provenance="classes of the LiDAR-based raster; not compared again"))
    n = len(pd.read_csv(TEBING, usecols=["TebalGmbt1"]))
    rows.append(dict(source="Tebing Tinggi survey points", kind="points", path="Peat depth and DTM/Tebingtinggi.csv", files=1, count=n, crs="EPSG:4326 (POINT_X, POINT_Y)",
                     resolution="points", units="m (TebalGmbt1)", year="2015", provenance="field survey; depths differ more by field team than by place"))
    masks = glob.glob(str(DATA / "Peat depth and DTM" / "PeatDepth_*" / "**" / "PEAT_*.shp"), recursive=True)
    rows.append(dict(source="peat masks (PEAT_*.shp)", kind="vector", path="Peat depth and DTM/PeatDepth_*", files=len(masks), count=np.nan, crs="", resolution="",
                     units="1 peat / 0 not peat", year="", provenance="masks of the modelled rasters; no depth"))
    return pd.DataFrame(rows)


# --- 1. same source ---------------------------------------------------------------------------------------------------
def same_source():
    reg = pd.read_csv(HUB / "sites" / "khg_registry.csv")
    code = dict(zip(reg["name"].map(norm), reg["khg_code"]))
    p = pyogrio.read_dataframe(PPEG, read_geometry=False, use_arrow=True, columns=["NAMA_KHG", "PEAT_THICK", "KDLMN_GBT", "LUAS_HA"])
    p["khg_code"] = p["NAMA_KHG"].map(lambda s: code.get(norm(s), ""))
    feg = gpd.read_file(DATA / "klhk_khg_feg_50k.gpkg", layer="feg_50k", columns=["kode_khg", "peat_thick"])
    feg["ha"] = feg.to_crs("EPSG:6933").area / 1e4
    bb = pyogrio.read_dataframe(DATA / "kedalaman_gambut_bbsdlp.gpkg", read_geometry=False)
    out = []
    for name, a, acol, b, bcol, bkhg, bha in [("PEAT_THICK vs FEG 50K", p, "PEAT_THICK", feg, "peat_thick", "kode_khg", "ha"),
                                              ("KDLMN_GBT vs BBSDLP", p, "KDLMN_GBT", bb, "KELAS_GBT", "KODE_KHG", "LUAS_HA")]:
        b = b.assign(cls=b[bcol].map(lambda s: nice(*bounds_m(s)) if not np.isnan(bounds_m(s)[0]) else "no data"))
        a = a.assign(cls=a[acol].map(lambda s: nice(*bounds_m(s)) if not np.isnan(bounds_m(s)[0]) else "no data"))
        khgs = set(b[bkhg].dropna())
        ga = a[a["khg_code"].isin(khgs) & (a["cls"] != "no data")].groupby(["khg_code", "cls"])["LUAS_HA"].sum()
        gb = b[b["cls"] != "no data"].groupby([bkhg, "cls"])[bha].sum().rename_axis(["khg_code", "cls"])
        t = pd.concat({"ppeg_ha": ga, "source_ha": gb}, axis=1).fillna(0).reset_index()
        t.insert(0, "check", name)
        out.append(t)
    return pd.concat(out, ignore_index=True)


# --- 2. rasters -------------------------------------------------------------------------------------------------------
def raster_vs_class(path, kind):
    rows = []
    with rasterio.open(path) as r:
        b4326 = rasterio.warp.transform_bounds(r.crs, "EPSG:4326", *r.bounds)
        classes = {}
        for lyr, col in FIELDS.items():
            g = gpd.read_file(LAYERS, layer=lyr, bbox=b4326)
            if g.empty:
                continue
            g = g[g[col] != "no data"].dissolve(col).reset_index().to_crs(r.crs)
            g["lo"], g["hi"] = zip(*g[col].map(bounds_m))
            classes[lyr] = g.reset_index(drop=True)
        if not classes:
            return rows
        acc = {lyr: {i: dict(n=0, inside=0, deep_r=0, hist=np.zeros(len(HIST) - 1)) for i in range(len(g))} for lyr, g in classes.items()}
        for row0 in range(0, r.height, BLOCK):
            win = Window(0, row0, r.width, min(BLOCK, r.height - row0))
            z = r.read(1, window=win, masked=True)
            valid = ~np.ma.getmaskarray(z) & (z.data > -1000) & np.isfinite(z.data)      # -8888 and -3.4e38 are no data
            if not valid.any():
                continue
            zz = np.clip(z.data / 100.0, 0, None)       # all depth rasters are in cm (repeat-pump peat_depth.units, repeat-neraca scale 0.01); interpolation dips below 0 count as 0
            tr = r.window_transform(win)
            for lyr, g in classes.items():
                lab = rasterize(((geom, i + 1) for i, geom in enumerate(g.geometry)), out_shape=zz.shape, transform=tr, fill=0, dtype="int32")
                for i in range(len(g)):
                    m = valid & (lab == i + 1)
                    if not m.any():
                        continue
                    v = zz[m]
                    a = acc[lyr][i]
                    a["n"] += v.size
                    a["inside"] += int(((v >= g.at[i, "lo"]) & (v < g.at[i, "hi"])).sum())
                    a["deep_r"] += int((v >= 3).sum())
                    a["hist"] += np.histogram(np.clip(v, 0, HIST[-1] - 1e-6), HIST)[0]
        px_ha = abs(r.res[0] * r.res[1]) / 1e4 if not r.crs.is_geographic else np.nan
        for lyr, g in classes.items():
            for i in range(len(g)):
                a = acc[lyr][i]
                if a["n"] == 0:
                    continue
                cdf = np.cumsum(a["hist"]) / a["hist"].sum()
                med = HIST[np.searchsorted(cdf, 0.5) + 1]
                rows.append(dict(raster=Path(path).name, kind=kind, field=LABEL[lyr], cls=g.at[i, FIELDS[lyr]], lo=g.at[i, "lo"], hi=g.at[i, "hi"],
                                 pixels=a["n"], area_ha=a["n"] * px_ha if px_ha == px_ha else np.nan, inside=a["inside"], raster_ge3=a["deep_r"], median_m=med))
    return rows


# --- 2b. points -------------------------------------------------------------------------------------------------------
def points():
    s = gpd.read_file(SALEH / "PEAT_THICK__KHG_Saleh_Sugihan__UTM_48S.shp").to_crs("EPSG:4326")
    s = gpd.GeoDataFrame({"set": "Saleh-Sugihan", "depth_m": s["P_DEPTH_CM"] / 100}, geometry=s.geometry, crs="EPSG:4326")
    t = pd.read_csv(TEBING, usecols=["POINT_X", "POINT_Y", "TebalGmbt1", "Surveyor"])
    t = gpd.GeoDataFrame({"set": "Tebing Tinggi", "depth_m": t["TebalGmbt1"]}, geometry=gpd.points_from_xy(t["POINT_X"], t["POINT_Y"]), crs="EPSG:4326")
    p = pd.concat([s, t], ignore_index=True)
    rows = []
    for lyr, col in FIELDS.items():
        g = gpd.read_file(LAYERS, layer=lyr, bbox=tuple(p.total_bounds))
        j = gpd.sjoin(p, g[[col, "geometry"]], how="left", predicate="within")
        j = j[~j.index.duplicated()]
        j["cls"] = j[col].fillna("outside layer")
        lohi = j["cls"].map(bounds_m)
        j["lo"], j["hi"] = zip(*lohi)
        j["inside"] = (j["depth_m"] >= j["lo"]) & (j["depth_m"] < j["hi"])
        j["field"] = LABEL[lyr]
        rows.append(j.drop(columns=["geometry", "index_right", col], errors="ignore"))
    return pd.concat(rows, ignore_index=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inv = inventory()
    inv.to_csv(OUT / "peat_depth_sources.csv", index=False)
    ss = same_source()
    ss.to_csv(OUT / "peat_depth_same_source.csv", index=False, float_format="%.1f")
    rr = []
    for p, kind in depth_rasters():
        print("raster", Path(p).name, flush=True)
        rr += raster_vs_class(p, kind)
    rv = pd.DataFrame(rr)
    rv.to_csv(OUT / "peat_depth_raster_vs_class.csv", index=False, float_format="%.3f")
    pt = points()
    pt.to_csv(OUT / "peat_depth_points.csv", index=False, float_format="%.3f")
    write_md(inv, ss, rv, pt)
    print(OUT / "peat_depth_comparison.md")


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "n/a"


def write_md(inv, ss, rv, pt):
    md = ["# Peat depth sources and the PPEG peat thickness fields", "",
          "Generated by `re-peat/tools/compare_peat_depth.py`. Tables: `peat_depth_sources.csv`, `peat_depth_same_source.csv`, "
          "`peat_depth_raster_vs_class.csv`, `peat_depth_points.csv`.", "", "## Sources", "",
          "| Source | Kind | Files | Features or pixels | CRS | Resolution | Units | Year | Provenance |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in inv.iterrows():
        cnt = "" if pd.isna(r["count"]) else f"{int(r['count']):,}"
        md.append(f"| {r['source']} | {r['kind']} | {r['files']} | {cnt} | {r['crs']} | {r['resolution']} | {r['units']} | {r['year']} | {r['provenance']} |")
    md += ["", "## 1. Same source?", "",
           "Class area per KHG in PPEG against the layer it appears to come from, over the KHG that layer covers. "
           "Dissimilarity is half the sum of absolute differences of the class shares (0 = identical distribution, 1 = disjoint).", "",
           "| Check | KHG | PPEG (million ha) | Source (million ha) | Dissimilarity, median | Dissimilarity, 90th percentile | KHG with dissimilarity > 0.1 |", "|---|---|---|---|---|---|---|"]
    for name, t in ss.groupby("check", sort=False):
        sh = t.pivot_table(index="khg_code", columns="cls", values=["ppeg_ha", "source_ha"], fill_value=0)
        a = sh["ppeg_ha"].div(sh["ppeg_ha"].sum(1), axis=0).fillna(0)
        b = sh["source_ha"].div(sh["source_ha"].sum(1), axis=0).fillna(0)
        d = (a - b).abs().sum(1) / 2
        md.append(f"| {name} | {len(d)} | {t['ppeg_ha'].sum() / 1e6:.3f} | {t['source_ha'].sum() / 1e6:.3f} | {d.median():.3f} | {d.quantile(.9):.3f} | {(d > 0.1).sum()} ({", ".join(d[d > 0.1].sort_values(ascending=False).index[:6])}) |")
    md += ["", "## 2. Rasters against the PPEG classes", "",
           "Pixels with a valid depth inside each class polygon (raster cm converted to m). Inside = raster depth within the class bounds. "
           "The 3 m split: share of pixels on which class (lower bound >= 3 m) and raster (>= 3 m) agree.", "",
           "| Field | Raster kind | Rasters | Pixels | Inside class | Agree on 3 m split | Class >= 3 m but raster < 3 m | Class < 3 m but raster >= 3 m |",
           "|---|---|---|---|---|---|---|---|"]
    if len(rv):
        rv = rv.assign(cdeep=rv["lo"] >= 3)
        for (f, k), t in rv.groupby(["field", "kind"]):
            n = t["pixels"].sum()
            agree = t.loc[t["cdeep"], "raster_ge3"].sum() + (t.loc[~t["cdeep"], "pixels"] - t.loc[~t["cdeep"], "raster_ge3"]).sum()
            fn = (t.loc[t["cdeep"], "pixels"] - t.loc[t["cdeep"], "raster_ge3"]).sum()
            fp = t.loc[~t["cdeep"], "raster_ge3"].sum()
            md.append(f"| {f} | {k} | {t['raster'].nunique()} | {n:,} | {pct(t['inside'].sum(), n)} | {pct(agree, n)} | {pct(fn, n)} | {pct(fp, n)} |")
        md += ["", "Median raster depth per class, pooled over the modelled rasters (pixel-weighted mean of the per-raster medians):", "",
               "| Field | Class | Pixels | Inside class | Median depth (m) |", "|---|---|---|---|---|"]
        m = rv[rv["kind"].str.startswith("modelled")]
        for (f, c), t in m.groupby(["field", "cls"]):
            md.append(f"| {f} | {c} | {t['pixels'].sum():,} | {pct(t['inside'].sum(), t['pixels'].sum())} | {np.average(t['median_m'], weights=t['pixels']):.2f} |")
        md += ["", "Per raster (modelled and LiDAR), PPEG PEAT_THICK:", "", "| Raster | Pixels | Inside class | Agree on 3 m split |", "|---|---|---|---|"]
        for ras, t in rv[rv["field"] == "PPEG PEAT_THICK"].groupby("raster"):
            n = t["pixels"].sum()
            agree = t.loc[t["cdeep"], "raster_ge3"].sum() + (t.loc[~t["cdeep"], "pixels"] - t.loc[~t["cdeep"], "raster_ge3"]).sum()
            md.append(f"| {ras} | {n:,} | {pct(t['inside'].sum(), n)} | {pct(agree, n)} |")
    md += ["", "## 3. Field points against the PPEG classes", "",
           "| Field | Point set | Points | In a class | Inside class | Agree on 3 m split | Median depth (m) |", "|---|---|---|---|---|---|---|"]
    for (f, s), t in pt.groupby(["field", "set"]):
        c = t[t["lo"].notna()]
        agree = ((c["lo"] >= 3) == (c["depth_m"] >= 3)).sum()
        md.append(f"| {f} | {s} | {len(t):,} | {len(c):,} | {pct(c['inside'].sum(), len(c))} | {pct(agree, len(c))} | {t['depth_m'].median():.2f} |")
    md += ["", "The Tebing Tinggi depths differ more by field team than by place (repeat-neraca report), so they test the level, not the pattern. "
           "The Saleh-Sugihan points are mostly 0 cm (mineral or shallow sites).", ""]
    (OUT / "peat_depth_comparison.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
