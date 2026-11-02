"""Inventory and check of the burn-scar data in _data/burnscar/ (fetched by repeat_common.fetch_burnscar).

    python re-peat/tools/inventory_burnscar.py [--year 2026]

Writes re-peat/reports/investigations/burnscar_<year>_files.csv (one row per raster: product, KHG, size, last month in the source,
grid), burnscar_<year>_by_month.csv (burned area in the KHG by source and month, with the area of the 2026 KLHK polygon layer and
the VIIRS detections of the same month) and burnscar_<year>_checks.csv, with the markdown summary burnscar_<year>.md. Every number
is read from the files; rerun after fetching more KHG.

Checks, per KHG and source:
  hit_rate    share of VIIRS SNPP detections (confidence nominal or high, vegetation fire where typed, inside the KHG) of the year
              that lie within 500 m of a polygon of the source
  area_share  share of the KHG area within 500 m of a polygon of the source (the hit rate a random point would have)
  s2_in_mcd   share of the MCD64A1 area of the months both cover (Jun-Aug) that Sentinel-2 dNBR also marks
  mcd_in_s2   share of the Sentinel-2 area of those months that MCD64A1 also marks
  klhk_vs_<product>  area of the KLHK 2026 polygons (burnt_area_2015_2026_Indonesia.gpkg, BA_2026) and of the product, and the share of
              each that the other covers. The KLHK layer has no burn date, the products cover January to August.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

HUB = Path(os.environ.get("REPEAT_HUB") or Path(__file__).resolve().parents[1])
DATA = Path(os.environ.get("REPEAT_DATA") or HUB.parent / "_data")
BOUNDARY = ("batas_khg_indonesia.gpkg", "nama__khg__indonesia__2017__rev_tipologi", "NAMA_KHG")
VIIRS = ["hotspot_viirs_snpp_sp_{y}.gpkg", "hotspot_viirs_snpp_nrt_{y}.gpkg"]
SOURCES = ["mcd64a1", "vnp64a1", "s2_dnbr", "klhk_ba"]
NEAR_M = 500.0


def khg_boundary(name):
    from repeat_common import khg
    b = gpd.read_file(DATA / BOUNDARY[0], layer=BOUNDARY[1])
    return b[b[BOUNDARY[2]].map(khg.norm) == khg.norm(name)]


def hotspots(box, year):
    out = []
    for f in VIIRS:
        p = DATA / f.format(y=year)
        if not p.exists():
            continue
        cols = ["acq_date", "confidence"] + (["type"] if "type" in pyogrio.read_info(p)["fields"] else [])
        d = pyogrio.read_dataframe(p, columns=cols, bbox=tuple(box))
        d = d[d["confidence"].isin(["n", "h"])]
        if "type" in d:
            d = d[d["type"] == 0]
        out.append(d)
    if not out:
        return gpd.GeoDataFrame({"month": []}, geometry=[], crs=4326)
    d = pd.concat(out)
    d["month"] = pd.to_datetime(d["acq_date"]).dt.strftime("%Y-%m")
    return d[["month", "geometry"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    a = ap.parse_args()
    from repeat_common import khg
    root = DATA / "burnscar"
    out = HUB / "reports" / "investigations"
    out.mkdir(parents=True, exist_ok=True)
    files, by_month, checks = [], [], []
    klhk_path = DATA / "burnt_area_2015_2026_Indonesia.gpkg"
    rasters = sorted(root.glob(f"*/*_{a.year}_*.tif"))
    for t in rasters:
        meta = json.loads(t.with_suffix(".json").read_text(encoding="utf-8")) if t.with_suffix(".json").exists() else {}
        files.append({"product": t.parent.name, "file": t.name, "size_mb": round(t.stat().st_size / 1e6, 2), "fetched": meta.get("fetched"),
                      "last_month": meta.get("last_month") or (meta.get("bands") or [""])[-1][5:], "collection": meta.get("collection"),
                      "grid": meta.get("grid") or meta.get("grid_crs")})
    pd.DataFrame(files).to_csv(out / f"burnscar_{a.year}_files.csv", index=False)

    slugs = sorted({t.stem.split(f"_{a.year}_", 1)[1] for t in rasters})
    reg = {khg.slug(r["name"]): r for r in khg.registry()}
    for slug in slugs:
        r = reg[slug]
        b = khg_boundary(r["name"])
        utm = b.estimate_utm_crs()
        bu = b.to_crs(utm)
        area_ha = float(bu.area.sum() / 1e4)
        poly = {}
        for s in SOURCES:
            p = root / f"burnscar_{a.year}_{s}_{slug}.gpkg"
            if p.exists():
                g = gpd.read_file(p).to_crs(utm)
                g = gpd.clip(g, bu)
                g["area_ha"] = g.area / 1e4
                poly[s] = g
                for m, v in g.groupby("month")["area_ha"].sum().items():
                    by_month.append({"khg_code": r["khg_code"], "khg": r["name"], "source": s, "month": m, "burned_ha": round(float(v), 1)})
        if klhk_path.exists():
            k = pyogrio.read_dataframe(klhk_path, columns=[f"BA_{a.year}"], bbox=tuple(b.to_crs(4326).total_bounds))
            k = k[k[f"BA_{a.year}"].notna()].to_crs(utm)          # the field holds the year as text where burned, else empty
            k = gpd.clip(k, bu)
            k["area_ha"], k["month"] = k.area / 1e4, str(a.year)
            poly["klhk_ba"] = k
            by_month.append({"khg_code": r["khg_code"], "khg": r["name"], "source": "klhk_ba", "month": str(a.year), "burned_ha": round(float(k.area.sum() / 1e4), 1)})
        h = hotspots(b.to_crs(4326).total_bounds, a.year)
        h = gpd.clip(h.to_crs(utm), bu) if len(h) else h
        for m, v in h.groupby("month").size().items():
            by_month.append({"khg_code": r["khg_code"], "khg": r["name"], "source": "viirs_hotspots", "month": m, "burned_ha": np.nan, "n": int(v)})
        shape_bu = bu.union_all()
        for s, g in poly.items():
            row = {"khg_code": r["khg_code"], "khg": r["name"], "source": s, "burned_ha": round(float(g.area_ha.sum()), 1), "khg_ha": round(area_ha)}
            if len(g) and len(h):
                near = g.union_all().buffer(NEAR_M)
                row["hit_rate"] = round(float(h.geometry.within(near).mean()), 3)
                row["area_share"] = round(float(near.intersection(shape_bu).area / shape_bu.area), 3)
                row["n_hotspots"] = int(len(h))
            checks.append(row)
        if "klhk_ba" in poly:
            kl = poly["klhk_ba"].union_all() if len(poly["klhk_ba"]) else None
            for s in ("mcd64a1", "vnp64a1"):
                if s in poly and len(poly[s]) and kl is not None:
                    u = poly[s].union_all()
                    inter = u.intersection(kl).area / 1e4
                    checks.append({"khg_code": r["khg_code"], "khg": r["name"], "source": f"klhk_vs_{s}", "klhk_ha": round(float(kl.area / 1e4), 1),
                                   f"{s}_ha": round(float(u.area / 1e4), 1), f"klhk_in_{s}": round(float(inter / (kl.area / 1e4)), 3),
                                   f"{s}_in_klhk": round(float(inter / (u.area / 1e4)), 3)})
        if "mcd64a1" in poly and "s2_dnbr" in poly:
            both = ["2026-06", "2026-07", "2026-08"] if a.year == 2026 else [f"{a.year}-0{m}" for m in (6, 7, 8)]
            m_ = poly["mcd64a1"][poly["mcd64a1"].month.isin(both)].union_all()
            s_ = poly["s2_dnbr"][poly["s2_dnbr"].month.isin(both)].union_all()
            inter = m_.intersection(s_).area / 1e4
            checks.append({"khg_code": r["khg_code"], "khg": r["name"], "source": "s2_vs_mcd64a1_jun_aug", "mcd_ha": round(float(m_.area / 1e4), 1),
                           "s2_ha": round(float(s_.area / 1e4), 1), "s2_in_mcd": round(float(inter / (m_.area / 1e4)), 3) if m_.area else None,
                           "mcd_in_s2": round(float(inter / (s_.area / 1e4)), 3) if s_.area else None})
    bm = pd.DataFrame(by_month)
    bm.to_csv(out / f"burnscar_{a.year}_by_month.csv", index=False)
    ck = pd.DataFrame(checks)
    ck.to_csv(out / f"burnscar_{a.year}_checks.csv", index=False)

    md = [f"# Burn scars {a.year}: data and checks", "", "Generated by `re-peat/tools/inventory_burnscar.py` from `_data/burnscar/`; do not edit by hand.", "",
          "## Files", "", pd.DataFrame(files).to_markdown(index=False) if files else "none", ""]
    if len(bm):
        piv = bm[bm.source != "viirs_hotspots"].pivot_table(index=["khg_code", "source"], columns="month", values="burned_ha", aggfunc="sum")
        md += ["## Burned area in the KHG by month (ha)", "", piv.round(0).to_markdown(), ""]
        hot = bm[bm.source == "viirs_hotspots"].pivot_table(index="khg_code", columns="month", values="n", aggfunc="sum")
        md += ["## VIIRS detections in the KHG by month (nominal and high confidence)", "", hot.to_markdown(), ""]
    if len(ck):
        md += ["## Checks", "", ck.to_markdown(index=False), ""]
    (out / f"burnscar_{a.year}.md").write_text("\n".join(md), encoding="utf-8")
    print("wrote", out / f"burnscar_{a.year}.md")


if __name__ == "__main__":
    main()
