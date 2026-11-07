"""Second pass of the national availability table (needs Earth Engine): DEM coverage and each KHG's own dry window.

    python tools/khg_availability_ee.py [--only CODE ...] [--batch 20]          # after tools/khg_availability.py; needs EE_PROJECT

Adds to sites/khg_availability.csv, per KHG:
  deltadtm_share        share of the KHG with a DeltaDTM v1.1 value (DeltaDTM only covers land below about 10 m +MSL), 30 m
  glo30_below10m_share  share of the KHG where Copernicus GLO-30 is below 10 m (EGM2008), 30 m. GLO-30 is a surface model, so
                        forest canopy lifts it above 10 m where the ground is lower: an indication only, DeltaDTM's own coverage counts
  p_annual_mm, e_annual_mm   mean yearly CHIRPS rain and MOD16A2GF ET, 2018-2025 (KHG mean)
  dry_first, dry_last, dry_shortfall_mm   the dry window by the rule of repeat-neraca's supply_rule.dry_window: the 14 consecutive
                        dekads (circular, 36 a year) with the largest mean sum(ET - rain) over 2018-2025; a negative shortfall means
                        that on average even the driest stretch gets more rain than ET (single dry years still fall short)
Dekad means are built in Earth Engine (rain: sum of CHIRPS daily per dekad and year, averaged over the years; ET: MOD16A2GF
8-day composites starting in the dekad, scaled to the dekad's length), reduced over each KHG at 500 m. The chain itself uses the
sub-KHG balance files for the same rule, so the windows here are a national first look, not the run's window.
Geometries are simplified by 50 m for the requests. Then rewrites docs/20-khg-availability.md with the new section.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

HUB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HUB / "tools"))
import khg_availability as KA  # noqa: E402
from repeat_common import gee  # noqa: E402

DELTADTM = "projects/sat-io/open-datasets/DELTARES/deltadtm_v1-1"
YEARS = (2018, 2025)
DEKADS = 14


def dekad_bounds():
    out = []
    for m in range(1, 13):
        out += [(m, 1, 10), (m, 11, 20), (m, 21, 31)]
    return out


def climate_image(ee):
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filter(ee.Filter.calendarRange(YEARS[0], YEARS[1], "year")).select("precipitation")
    mod16 = ee.ImageCollection("MODIS/061/MOD16A2GF").filter(ee.Filter.calendarRange(YEARS[0], YEARS[1], "year")).select("ET")
    ny = YEARS[1] - YEARS[0] + 1
    bands = []
    for i, (m, d0, d1) in enumerate(dekad_bounds()):
        f = ee.Filter.And(ee.Filter.calendarRange(m, m, "month"), ee.Filter.calendarRange(d0, d1, "day_of_month"))
        p = chirps.filter(f).sum().divide(ny).rename(f"p{i:02d}")
        ndays = 10 if d1 != 31 else (8.25 if m == 2 else (11 if m in (1, 3, 5, 7, 8, 10, 12) else 10))
        # MOD16A2GF ET: kg/m2 per 8 days x 0.1; mean daily rate of the composites starting in the dekad x days in the dekad
        e = mod16.filter(f).mean().multiply(0.1 / 8 * ndays).rename(f"e{i:02d}")
        bands += [p, e]
    return ee.Image.cat(bands)


def dry_window(c: np.ndarray, k: int = DEKADS):
    tot = [sum(c[(i + n) % 36] for n in range(k)) for i in range(36)]
    i = int(np.argmax(tot))
    return i, float(tot[i])


def label(i: int, last: bool = False) -> str:
    """Month-day of a dekad's first day, or of its last day ('end' for the month's last dekad)."""
    m, d0, d1 = dekad_bounds()[i % 36]
    return f"{m:02d}-{d0:02d}" if not last else (f"{m:02d}-{d1:02d}" if d1 != 31 else f"{m:02d}-end")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--batch", type=int, default=20)
    a = ap.parse_args()
    ee = gee.init()
    d = pd.read_csv(KA.OUT_CSV, dtype={"code": str})
    reg = pd.DataFrame(KA.K.registry())
    reg["code"] = reg.khg_code.str[4:]
    reg["n"] = reg.name.map(KA.K.norm)
    b = gpd.read_file(KA.S.data / KA.BOUNDARY[0], layer=KA.BOUNDARY[1])
    b["n"] = b[KA.BOUNDARY[2]].map(KA.K.norm)
    bd = b[["n", "geometry"]].dissolve("n").to_crs(4326)
    k = reg.merge(bd, left_on="n", right_index=True)
    k = gpd.GeoDataFrame(k, geometry="geometry", crs=4326)
    if a.only:
        k = k[k.code.isin(a.only)]
    k["geometry"] = k.to_crs("EPSG:6933").simplify(50).to_crs(4326).make_valid()

    dt = ee.Image(DELTADTM).select(0).mask().gt(0).rename("deltadtm")   # one global image
    glo = ee.ImageCollection("COPERNICUS/DEM/GLO30").select("DEM").mosaic().lt(10).rename("glo30_lt10")
    dem_img = dt.unmask(0).addBands(glo.unmask(0))
    clim = climate_image(ee)
    rows = []
    done = set()
    part = KA.OUT_CSV.with_name("khg_availability_ee.partial.csv")
    if part.exists():
        prev = pd.read_csv(part, dtype={"code": str})
        rows = prev.to_dict("records")
        done = set(prev.code)
    todo = k[~k.code.isin(done)]
    print(f"{len(todo)} KHG to do ({len(done)} done before)", flush=True)
    for s in range(0, len(todo), a.batch):
        chunk = todo.iloc[s:s + a.batch]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry(g.__geo_interface__), {"code": c}) for c, g in zip(chunk.code, chunk.geometry)])
        for attempt in range(3):
            try:
                r1 = dem_img.reduceRegions(fc, ee.Reducer.mean(), scale=30, tileScale=8).getInfo()["features"]
                r2 = clim.reduceRegions(fc, ee.Reducer.mean(), scale=500, tileScale=4).getInfo()["features"]
                break
            except Exception as e:
                print(f"  batch {s}: retry {attempt + 1} ({str(e)[:120]})", flush=True)
                if attempt == 2:
                    raise
        clim_by = {f["properties"]["code"]: f["properties"] for f in r2}
        for f in r1:
            p = f["properties"]
            c = clim_by.get(p["code"], {})
            P = np.array([c.get(f"p{i:02d}") or 0.0 for i in range(36)])
            E = np.array([c.get(f"e{i:02d}") or 0.0 for i in range(36)])
            first, short = dry_window(E - P)
            rows.append({"code": p["code"], "deltadtm_share": round(p.get("deltadtm") or 0, 3),
                         "glo30_below10m_share": round(p.get("glo30_lt10") or 0, 3),
                         "p_annual_mm": round(P.sum()), "e_annual_mm": round(E.sum()),
                         "dry_first": label(first), "dry_last": label(first + DEKADS - 1, last=True),
                         "dry_shortfall_mm": round(short)})
        pd.DataFrame(rows).to_csv(part, index=False)
        print(f"  {len(rows)} done", flush=True)
    R = pd.DataFrame(rows)
    d = d.drop(columns=[c for c in R.columns if c != "code" and c in d.columns]).merge(R, on="code", how="left")
    d.to_csv(KA.OUT_CSV, index=False)
    KA.write_md(d)
    add_md(d)
    if not a.only:
        part.unlink(missing_ok=True)
    print(f"wrote {KA.OUT_CSV.relative_to(HUB)}")


def add_md(d: pd.DataFrame) -> None:
    if "deltadtm_share" not in d or d.deltadtm_share.isna().all():
        return
    ha = d.area_ha.fillna(0)
    L = ["", "## DEM coverage and dry window (Earth Engine pass)", "",
         "From `tools/khg_availability_ee.py`. DeltaDTM covers land below about 10 m only; where it covers less of a KHG, the rest "
         "needs DEMNAS or GLO-30. The dry window is the 14-dekad stretch with the largest mean shortfall of rain against ET, 2018-2025 "
         "(CHIRPS, MOD16A2GF), by the rule of repeat-neraca `supply_rule.dry_window`.", "",
         "| DeltaDTM covers | KHG | area (Mha) |", "|---|---|---|"]
    for lo, hi, lab in ((0.9, 1.01, ">= 90% (the chain's threshold)"), (0.5, 0.9, "50-90%"), (0.0, 0.5, "< 50%")):
        m = (d.deltadtm_share >= lo) & (d.deltadtm_share < hi)
        L.append(f"| {lab} | {int(m.sum())} | {ha[m].sum() / 1e6:.1f} |")
    L += ["", "| dry window starts in | KHG | median shortfall (mm) |", "|---|---|---|"]
    x = d.dropna(subset=["dry_first"]).copy()
    x["month"] = x.dry_first.str[:2]
    for mth, g in x.groupby("month"):
        L.append(f"| month {mth} | {len(g)} | {g.dry_shortfall_mm.median():.0f} |")
    L.append(f"| mean shortfall of the window above 0 (ET exceeds rain on average) | {int((d.dry_shortfall_mm > 0).sum())} | |")
    with open(KA.OUT_MD, "a", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
