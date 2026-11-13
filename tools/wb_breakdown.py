"""Nationwide breakdown by land status for the World Bank: hotspots, burned area and water table (TMA), one table.

    python re-peat/tools/wb_breakdown.py

Rows: all land; concession or not; forest area (kawasan hutan, legal status) or other land use (APL); DMPG village or not;
peat or not. Classes overlap across groups (a cell is in one row of each group). Sources:
  fire     the national tally ($REPEAT_WORK/national_profile/fire_landstatus: area.parquet, hot.parquet), all land inside the
           2023 village boundaries. Hotspots: VIIRS S-NPP 2026, 1 January to the last VIIRS date, medium and high confidence,
           likely static sources left out; MODIS 2026 (the series KLH reports) to its last date, same filters. Burned area:
           KLHK maps, summed over 2015-2025 (2024 and 2026 maps are incomplete) and land burned in two or more years 2015-2026.
  expected for location   what the class would show if it burned like the rest of the land in the same province and with
           the same peat status (for the peat rows: the same province): observed / expected. 1 = as its location predicts.
  TMA      SiTMAT stations ($SITMAT_PROCESSED), April-October 2026. Each station takes the classes of the 30 m cell it stands
           on (layers/status.vrt). Records flagged range or spike are left out, then screened with
           repeat_neraca.groundwater.fieldcheck.screen (D20: logger restarts, stuck values). Depth = -water_level_cm (cm below
           the surface). Per class: stations with at least 14 screened days in August-October, the median of their median
           depths, and the share of station-days deeper than 40 cm (the PP 57/2016 limit). Stations are placed by companies
           and communities, not sampled: the numbers describe the network, not the class.
Writes re-peat/reports/fire_landstatus/wb_breakdown.csv and _slides/build/wb_breakdown.json.
"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

from repeat_neraca.groundwater.fieldcheck import screen

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]
SRC = Path(os.environ.get("REPEAT_WORK", WS / "re-peat" / "reports")) / "national_profile" / "fire_landstatus"
SIT = Path(os.environ.get("SITMAT_PROCESSED", WS / "repeat-sitmat" / "sitmat_out" / "processed"))
OUT = WS / "re-peat" / "reports" / "fire_landstatus" / "wb_breakdown.csv"
PAST = list(range(2015, 2026))
CONC = 1 | 2 | 4 | 8
LIMIT_CM = 40

ROWS = [("all", "All land", None), ("conc", "Concession", True), ("conc", "No concession", False),
        ("forest", "Forest area (kawasan hutan)", "kawasan"), ("forest", "Other land use (APL)", "apl"),
        ("dmpg", "DMPG villages", True), ("dmpg", "Outside DMPG villages", False),
        ("peat", "Peat", True), ("peat", "Not peat", False)]


def classes(df, conc, kws, dmpg, peat):
    return pd.DataFrame({"conc": conc, "forest": kws, "dmpg": dmpg, "peat": peat}, index=df.index)


def expected(a_area, a_val, h_val, grp, key, strata):
    """observed / expected for one class: the rest of the land in the same strata, weighted by the class's area there."""
    sel = grp == key
    obs = h_val[sel].sum()
    by = pd.DataFrame({"s": strata, "in": sel, "area": a_area, "v": a_val})
    rest = by[~by["in"]].groupby("s")[["area", "v"]].sum()
    rate = (rest["v"] / rest["area"]).reindex(by.loc[by["in"], "s"].unique()).fillna(0)
    exp = (by[by["in"]].groupby("s")["area"].sum() * rate).sum()
    return obs / exp if exp else np.nan


def fire():
    a = pd.read_parquet(SRC / "area.parquet")
    h = pd.read_parquet(SRC / "hot.parquet")
    meta = json.loads((SRC / "meta.json").read_text(encoding="utf-8"))
    now = meta["years"][1]
    h = h[h["conf"].isin(["medium", "high"]) & ~h["static"] & (h["year"] == now)]
    v, m = h[(h["source"] == "viirs") & h["ytd"]], h[h["source"] == "modis"]
    a = a.assign(past=a[[f"burned_{y}_ha" for y in PAST]].sum(axis=1), rep=a["burned_2plus_ha"])
    ca = classes(a, (a["lic_bits"] & CONC) > 0, a["forest_group"], a["dmpg"], a["peat"] == 1)
    # hotspots on the area table's keys, so that expected values use the same strata
    keys = ["island", "province", "in_khg", "forest_group", "kawasan", "concession", "lic_bits", "dmpg", "peat"]
    a = a.merge(v.groupby(keys, as_index=False)["n"].sum().rename(columns={"n": "viirs"}), on=keys, how="left")
    a = a.merge(m.groupby(keys, as_index=False)["n"].sum().rename(columns={"n": "modis"}), on=keys, how="left").fillna({"viirs": 0, "modis": 0})
    ca = classes(a, (a["lic_bits"] & CONC) > 0, a["forest_group"], a["dmpg"], a["peat"] == 1)
    T = {k: a[k].sum() for k in ("area_ha", "past", "rep", "viirs", "modis")}
    out = []
    for grp, label, key in ROWS:
        sel = np.ones(len(a), bool) if grp == "all" else (ca[grp] == key).to_numpy()
        s = a[sel]
        r = {"group": grp, "class": label, "land_mha": s["area_ha"].sum() / 1e6, "land_pct": 100 * s["area_ha"].sum() / T["area_ha"],
             "viirs": int(s["viirs"].sum()), "viirs_pct": 100 * s["viirs"].sum() / T["viirs"],
             "viirs_per100km2": s["viirs"].sum() / s["area_ha"].sum() * 1e4,
             "modis": int(s["modis"].sum()), "modis_pct": 100 * s["modis"].sum() / T["modis"],
             "burned_mha": s["past"].sum() / 1e6, "burned_pct": 100 * s["past"].sum() / T["past"],
             "rep_mha": s["rep"].sum() / 1e6, "rep_pct_of_class": 100 * s["rep"].sum() / s["area_ha"].sum()}
        if grp != "all":
            strata = a["province"] + ("|" + (a["peat"] == 1).astype(str) if grp != "peat" else "")
            g = ca[grp]
            r["viirs_x_expected"] = expected(a["area_ha"], a["viirs"], a["viirs"], g, key, strata)
            r["burned_x_expected"] = expected(a["area_ha"], a["past"], a["past"], g, key, strata)
        out.append(r)
    return pd.DataFrame(out), meta


def tma():
    st = pd.read_csv(SIT / "stations.csv")
    st = st.dropna(subset=["lon", "lat"])
    tf = Transformer.from_crs(4326, "EPSG:6933", always_xy=True)
    x, y = tf.transform(st["lon"].to_numpy(), st["lat"].to_numpy())
    with rasterio.open(SRC / "layers" / "status.vrt") as r:
        vals = np.array(list(r.sample(zip(x, y), indexes=[1, 2, 3, 4])))
    kw = {1: "kawasan", 2: "kawasan", 3: "kawasan", 4: "kawasan", 5: "apl"}
    st = st.assign(kws=[kw.get(int(k), "other") for k in vals[:, 0]], conc=(vals[:, 1] >= 1) & (vals[:, 1] <= 4),
                   dmpg=vals[:, 2] == 1, peat=vals[:, 3] == 1, on_land=vals[:, 0] != 65535)
    d = pd.read_csv(SIT / "daily_long.csv", parse_dates=["date"])
    d = d[d["flag"].isna() & d["water_level_cm"].notna()]
    rows = []
    for sid, g in d.groupby("station_id"):
        s, _ = screen(-g.set_index("date")["water_level_cm"].astype(float))
        s = s.dropna()
        s = s[(s.index.month >= 8) & (s.index.month <= 10)]
        if len(s) >= 14:
            rows.append({"station_id": sid, "kind": g["kind"].iloc[0], "days": len(s), "median_cm": float(s.median()),
                         "deep_days": int((s > LIMIT_CM).sum())})
    S = pd.DataFrame(rows).merge(st[["station_id", "kws", "conc", "dmpg", "peat", "on_land"]], on="station_id", how="inner")
    S = S[S["on_land"]]
    ca = pd.DataFrame({"conc": S["conc"], "forest": S["kws"], "dmpg": S["dmpg"], "peat": S["peat"]})
    out = []
    for grp, label, key in ROWS:
        q = S if grp == "all" else S[ca[grp] == key]
        out.append({"class": label, "tma_stations": len(q), "tma_community": int((q["kind"] == "community").sum()),
                    "tma_median_cm": float(q["median_cm"].median()) if len(q) else np.nan,
                    "tma_deep_pct": 100 * q["deep_days"].sum() / q["days"].sum() if len(q) else np.nan})
    return pd.DataFrame(out), {"stations_listed": int(len(st)), "stations_used": int(len(S)), "first": str(d["date"].min().date()), "last": str(d["date"].max().date())}


def main():
    f, meta = fire()
    t, tm = tma()
    b = f.merge(t, on="class")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    b.round(3).to_csv(OUT, index=False)
    j = WS / "_slides" / "build" / "wb_breakdown.json"
    j.parent.mkdir(exist_ok=True)
    j.write_text(json.dumps({"rows": b.astype(object).where(b.notna(), None).to_dict("records"), "viirs_last": meta["viirs_last"], "modis_last": meta["modis_last"], "tma": tm,
                             "now": meta["years"][1], "past": [PAST[0], PAST[-1]]}, default=float, indent=1), encoding="utf-8")
    pd.set_option("display.width", 250)
    print(b.round(2).to_string(index=False))
    print(tm)


if __name__ == "__main__":
    main()
