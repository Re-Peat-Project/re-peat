"""Inventory of the SIPALAGA data fetched by repeat_common.fetch_sipalaga.

    python tools/inventory_sipalaga.py [DATA_DIR]      # DATA_DIR defaults to $REPEAT_DATA, then ../_data

Writes reports/investigations/sipalaga.md: the sources; the station table (sipalaga_stations.gpkg) by source, province and
coordinate source, and the stations in the selected KHG; the hourly 2019 crawler records (period, completeness, values
outside a plausible range); the SiTMAT records of the former BRG stations; the monthly peat moisture of Taufik et al.
2023; and the Riau water retention samples with the water released between pF 1 and pF 2.
"""
import os
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

HUB = Path(__file__).resolve().parents[1]
OUT = HUB / "reports" / "investigations" / "sipalaga.md"
PROVINCES = ["JAMBI", "KALIMANTAN_BARAT", "KALIMANTAN_SELATAN", "KALIMANTAN_TENGAH", "PAPUA", "RIAU", "SUMATERA_SELATAN"]
GW_OK = (-3.0, 0.5)          # m, plausible groundwater level (negative below the surface)
SM_OK = (0.0, 100.0)         # % volume


def md(df: pd.DataFrame, fmt="{:,.1f}") -> str:
    cols = [str(c) for c in df.columns]
    rows = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    rows += ["| " + " | ".join("" if pd.isna(v) else (fmt.format(v) if isinstance(v, float) else str(v)) for v in r) + " |"
             for r in df.itertuples(index=False)]
    return "\n".join(rows)


def selected_names() -> set:
    sel = pd.read_csv(HUB / "sites" / "selected_khg.csv")
    return set(sel.khg_name_in_gpkg.dropna().map(lambda s: " ".join(s.split()))) | {"KHG Sungai Kampar - Sungai Gaung"}


def main():
    data = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("REPEAT_DATA", HUB.parent / "_data"))
    d = data / "sipalaga"
    st = gpd.read_file(d / "sipalaga_stations.gpkg")
    L = ["# SIPALAGA: inventory", "",
         "`python tools/inventory_sipalaga.py` on the files written by `python -m repeat_common.fetch_sipalaga` into "
         "`_data/sipalaga/`. SIPALAGA (Sistem Pemantauan Air Lahan Gambut) was the Badan Restorasi Gambut network of automatic "
         "stations logging groundwater level, soil moisture and rain every hour; its portal no longer serves data.", "",
         "| Source | What | Licence |", "|---|---|---|",
         "| github.com/danylaksono/sipalaga-crawler (pinned commit) | daily PDF reports converted to hourly CSV per province; "
         "download URL lists | not stated |",
         "| Taufik et al. 2023, Data in Brief 46, 108889, table 1 | 21 stations with code, KHG, longitude and latitude (2 decimals) | CC BY 4.0 |",
         "| Apers et al. 2022, JAMES 14, e2021MS002784, table B1 | 59 SIPALAGA and 10 SATREPS sites with code, village, "
         "coordinates (3 decimals), drained or undrained, record period | CC BY 4.0 |",
         "| Mendeley Data 27y943wbkw | monthly peat moisture at 10-20 cm, 21 stations | CC BY 4.0 |",
         "| Mendeley Data jj35xcx98v, 9stvfxystv | water retention at pF 1, 2, 2.54, 4.2 of peat samples in Riau, and plot coordinates | CC BY 4.0 |",
         "| SiTMAT station list (`repeat-sitmat`) | community stations named BRG_... with coordinates and 2026 records | not stated |", ""]

    # --- stations ---------------------------------------------------------------------------------------------------
    flags = ["in_crawler_csv", "in_crawler_urls", "in_taufik2023", "in_apers2022", "in_sitmat"]
    t = st.groupby(flags).size().reset_index(name="stations")
    for c in flags:
        t[c] = t[c].map({1: "yes", 0: ""})
    brg = st.code.str.match(r"BRG_\d{6}_\d{2}$")
    L += ["## Stations", "",
          f"`sipalaga_stations.gpkg` holds {len(st)} station codes: {int(brg.sum())} in the BRG_<area code>_<nn> form and "
          f"{int((~brg).sum())} other names (BRG9, LUMPUR1, SELEH2, TINGGI1 in the crawler; SATREPS sites such as TAKA4 in Apers et al. 2022). "
          f"{int(st.lon.notna().sum())} have coordinates.", "",
          "Table: station codes by source.", "", md(t.rename(columns=lambda c: c.replace("in_", ""))), ""]
    t = pd.crosstab(st.province, st.coord_source.replace("", "none"), margins=True, margins_name="total").reset_index()
    L += ["Table: stations by province and source of the coordinates (sitmat: SiTMAT station list; apers2022: Apers et al. 2022 table B1; taufik2023: Taufik et al. 2023 "
          "table; village: representative point of the village the crawler names, KLH 2023 village boundaries; none: no position).",
          "", md(t), ""]
    notes = st.loc[st.coord_note != "", ["code", "coord_note"]]
    L += [f"No position for {int(st.lon.isna().sum())} codes: "
          f"{int((st.lon.isna() & (st.in_crawler_csv == 0) & (st.in_taufik2023 == 0) & (st.in_apers2022 == 0) & (st.in_sitmat == 0)).sum())} are only in the "
          f"URL lists (no location given); {int(notes.coord_note.str.contains('village').sum())} name a village not found by name "
          "(national park or site labels such as TN_SEBANGAU_1, or a name spelled differently); SiTMAT points at 0,0 or outside "
          f"the province are not used ({int(notes.coord_note.str.startswith('SiTMAT').sum())}).", ""]
    sel = st[st.khg.fillna("").map(lambda s: " ".join(s.split())).isin(selected_names())]
    t = sel.groupby("khg").agg(stations=("code", "size"), codes=("code", lambda c: ", ".join(sorted(c))),
                               coordinates=("coord_source", lambda c: ", ".join(sorted(set(c))))).reset_index()
    L += [f"{int(st.khg.notna().sum())} stations fall in a KHG; {len(sel)} in the selected KHG and the Kampar-Gaung test site.", "",
          "Table: stations in the selected KHG.", "", md(t), ""]

    # --- crawler records ----------------------------------------------------------------------------------------------
    c = pd.concat([pd.read_csv(d / "crawler_2019" / "csv" / f"{p}.csv", dtype=str, on_bad_lines="skip") for p in PROVINCES])
    for k in ["gwater_mean", "smoisture_mean", "precip_composite"]:
        c[k] = pd.to_numeric(c[k], errors="coerce")
    gw_ok = c.gwater_mean.between(*GW_OK)
    sm_ok = c.smoisture_mean.between(*SM_OK)
    per = c.groupby("station").agg(days=("date", "nunique"), hours=("time", "size"))
    L += ["## Hourly records 2019 (crawler)", "",
          f"{len(c):,} hourly rows from {c.station.nunique()} stations, table dates {c.date.min()} to {c.date.max()} (the "
          f"reports were downloaded 2019-02-19 to 2019-03-17). Median {per.days.median():.0f} days and "
          f"{per.hours.median():.0f} hours per station. Fields: groundwater level (`gwater`, m, negative below the surface), "
          "soil moisture (`smoisture`, %), rain (`precip`, mm) as mean, min and max per hour, and the portal's status class.", "",
          f"Groundwater level within {GW_OK[0]} to {GW_OK[1]} m: {100 * gw_ok.mean():.1f}% of rows (median "
          f"{c.gwater_mean[gw_ok].median():.2f} m; values up to {c.gwater_mean.max():,.0f} outside). Soil moisture within 0-100%: "
          f"{100 * sm_ok.mean():.1f}%.", ""]
    t = c[gw_ok].groupby("province").agg(stations=("station", "nunique"), rows=("gwater_mean", "size"),
                                          median_m=("gwater_mean", "median"),
                                          deeper_than_40cm_pct=("gwater_mean", lambda x: 100 * (x < -0.4).mean())).reset_index()
    L += ["Table: groundwater level by province, plausible rows only.", "", md(t, "{:,.2f}"), "",
          "Table: status classes as reported.", "", md(c.status.value_counts().rename_axis("status").reset_index(name="rows")), ""]

    # --- SiTMAT records of BRG stations ------------------------------------------------------------------------------------
    sit = Path(os.environ.get("SITMAT_PROCESSED", HUB.parent / "repeat-sitmat/sitmat_out/processed")) / "daily_long.csv"
    if sit.exists():
        dl = pd.read_csv(sit, usecols=["station_id", "date", "water_level_cm"])
        ids = st.loc[st.in_sitmat == 1, ["code", "sitmat_station_id"]]
        r = dl[dl.station_id.isin(ids.sitmat_station_id)]
        t = r.groupby("station_id").agg(days=("date", "nunique"), first=("date", "min"), last=("date", "max"),
                                        median_cm=("water_level_cm", "median")).reset_index()
        t = ids.merge(t, left_on="sitmat_station_id", right_on="station_id", how="left").drop(columns="station_id")
        a = st[(st.in_sitmat == 1) & (st.coord_source == "sitmat")].to_crs(6933)
        b = st[(st.in_sitmat == 0) & st.lon.notna()].to_crs(6933)
        near = gpd.sjoin_nearest(a[["code", "geometry"]], b[["code", "geometry"]], distance_col="m").groupby("code_left").m.min()
        with_level = int(r.dropna(subset=["water_level_cm"]).station_id.nunique())
        L += ["## BRG stations in SiTMAT", "",
              f"{len(ids)} SiTMAT community stations carry a BRG_ code in the same form (the six digits match the "
              "province and district of the site). None of these codes is in the 2019 crawler, its URL lists, Taufik et al. "
              "2023 or Apers et al. 2022, so no SiTMAT record can be joined to a 2019 record by code. The nearest 2019 station to each usable SiTMAT "
              f"point lies {near.min() / 1e3:.1f} to {near.max() / 1e3:.0f} km away (median {near.median() / 1e3:.0f} km); most "
              "2019 positions are village points, so distance cannot show whether a logger was moved or renamed. "
              f"{with_level} of the {len(ids)} have at least one water level in SiTMAT; {int((t.days >= 60).sum())} have 60 days or more.", "",
              md(t.sort_values("code"), "{:,.0f}"), ""]

    # --- moisture and retention ---------------------------------------------------------------------------------------
    m = pd.read_csv(next((d / "mendeley" / "27y943wbkw").glob("*.csv")))
    L += ["## Monthly peat moisture (Taufik et al. 2023)", "",
          f"{m.station_code.nunique()} stations, {m.month.min()} to {m.month.max()}, {len(m)} station-months; volumetric "
          f"water content at 10-20 cm (HydraProbe), as a fraction: median {m.iloc[:, 2].median():.2f}, range "
          f"{m.iloc[:, 2].min():.2f} to {m.iloc[:, 2].max():.2f}.", ""]
    pf = pd.read_csv(next((d / "mendeley" / "jj35xcx98v").glob("*.csv")))
    pf["pF1_minus_pF2"] = pf.pF1 - pf.pF2
    t = pf.groupby("layer").apply(lambda g: pd.Series({
        "plots": int(g["plot"].nunique()), "samples": int(g.nsample.sum()),
        "pF1": (g.pF1 * g.nsample).sum() / g.nsample.sum(), "pF2": (g.pF2 * g.nsample).sum() / g.nsample.sum(),
        "pF1 - pF2": (g.pF1_minus_pF2 * g.nsample).sum() / g.nsample.sum(),
        "min pF1 - pF2": g.pF1_minus_pF2.min(), "max pF1 - pF2": g.pF1_minus_pF2.max()}), include_groups=False).reset_index()
    t[["plots", "samples"]] = t[["plots", "samples"]].astype(int)
    loc = pd.read_csv(next((d / "mendeley" / "9stvfxystv").glob("*.csv"))).dropna(axis=1, how="all")
    L += ["## Water retention, Riau (Taufik et al. 2023)", "",
          f"{pf.nsample.sum()} samples ({pf["plot"].nunique()} plots, sampled 2019 and 2022) at 0-30 cm (topsoil) and 50-70 cm "
          f"(subsoil); {len(loc)} plot coordinates. pF 1 and pF 2 are suctions of 0.1 m and 1 m of water, so the difference "
          "of water content between them is the water a sample releases as suction rises over the first metre. It is an "
          "indication of drainable porosity near the surface, not a measured specific yield.", "",
          "Table: volumetric water content (% volume), sample-weighted means by layer.", "", md(t, "{:,.1f}"), "",
          "Table: by land use, both layers.", "",
          md(pf.groupby("lu").apply(lambda g: pd.Series({"samples": int(g.nsample.sum()),
                                                         "pF1 - pF2": (g.pF1_minus_pF2 * g.nsample).sum() / g.nsample.sum()}),
                                    include_groups=False).reset_index().rename(columns={"lu": "land use"}).astype({"samples": int}), "{:,.1f}"), ""]
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
