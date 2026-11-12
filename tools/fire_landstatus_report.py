"""Build the Word report "Burned area and hotspots by land status in Indonesia" from the national tallies.

    .venv/Scripts/python.exe re-peat/tools/fire_landstatus_report.py [--out re-peat/reports/fire_landstatus/RE-PEAT_fire_land_status.docx]

Reads <REPEAT_WORK>/national_profile/fire_landstatus/ (outputs of `repeat-national-fire` and `repeat-national-fire-tables` in
repeat-prioritisation): tables/*.csv, area.parquet, hot.parquet, checks.csv, meta.json. Writes, in re-peat/reports/fire_landstatus/:
  figures/*.png          charts made from those tables
  chapters/*.md          the chapter text with every number filled in from the tables (generated: edit this script, not the files)
  sources.md             where each number of the text comes from
  <out>.docx             the Word file, assembled with the project report builder (project_report.py)
Rerun after the national tallies change; nothing in the text is typed by hand.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
sys.path.insert(0, str(HERE))
import project_report as PR  # noqa: E402
import project_report_style as STYLE  # noqa: E402

SRC = Path(os.environ.get("REPEAT_WORK", WORKSPACE / "re-peat" / "reports")) / "national_profile" / "fire_landstatus"
OUT = WORKSPACE / "re-peat" / "reports" / "fire_landstatus"
NOW, PAST = 2026, (2015, 2025)
COL = {"conc": "#eb6834", "noconc": "#2a78d6", "kawasan": "#008300", "apl": "#eda100", "other": "#8a8f91", "dmpg": "#e87ba4",
       "sawit": "#eb6834", "tambang": "#e34948", "pphtr": "#6250d6", "pbph": "#1baf7a", "pphkm": "#e87ba4", "none": "#2a78d6",
       "cons": "#008300", "hl": "#1baf7a", "prod": "#6250d6", "hpk": "#e87ba4"}
GROUP = {"kawasan": "Forest area", "apl": "Other land use (APL)", "other": "Water, undefined or not mapped"}
KWS = {"cons": "Conservation", "hl": "Protection forest", "prod": "Production forest (HP, HPT)", "hpk": "Convertible production (HPK)",
       "apl": "Other land use (APL)", "other": "Water, undefined", "none": "Not mapped"}
LIC = {"sawit": "Oil palm", "tambang": "Mining", "pphtr": "Plantation forest (PPHTR)", "pbph": "Forest concession (PBPH)",
       "pphkm": "Community forest (PPHKM)", "none": "No concession"}


# --- formatting ---------------------------------------------------------------------------------------------------------
def n0(v):
    return f"{v:,.0f}"


def n1(v):
    return f"{v:,.1f}"


def kha(v):
    """hectares as thousand ha with one decimal below 100 thousand"""
    return f"{v / 1e3:,.1f}" if v < 1e5 else f"{v / 1e3:,.0f}"


def mha(v):
    """hectares in prose: million ha above one million, else thousand ha"""
    return f"{v / 1e6:,.1f} million ha" if v >= 1e6 else f"{v / 1e3:,.0f} thousand ha"


def pc(a, b, nd=0):
    return "-" if not b else f"{100 * a / b:.{nd}f}%"


def rate(n, ha):
    return n / ha * 1e4 if ha else float("nan")


def mean_past(df, prefix="burned_", suffix="_ha"):
    return df[[f"{prefix}{y}{suffix}" for y in range(PAST[0], PAST[1] + 1)]].sum(axis=1) / (PAST[1] - PAST[0] + 1)


# --- data ---------------------------------------------------------------------------------------------------------------
def load():
    T = {f.stem: pd.read_csv(f) for f in (SRC / "tables").glob("*.csv")}
    meta = json.loads((SRC / "meta.json").read_text(encoding="utf-8"))
    chk = pd.read_csv(SRC / "checks.csv")
    return T, meta, chk


def basis(df, b):
    return df[df["basis"] == b].copy()


# --- numbers and tables -------------------------------------------------------------------------------------------------
COMPLETE = [y for y in range(PAST[0], PAST[1] + 1) if y != 2024]     # years whose burned-area layer passes the completeness check


def past_sum(df, years=tuple(range(PAST[0], PAST[1] + 1))):
    return df[[f"burned_{y}_ha" for y in years]].sum(axis=1)


def class_table(df, label_col, labels, order=None, total=None):
    """Markdown rows: class, area, share of area, burned 2015-2025 (sum of yearly areas), share, ever burned share,
    VIIRS 2026 hotspots (1 January to the last 2026 date), share, per 100 km2, and against the 2015-2025 mean over the same window."""
    g = df.groupby(label_col).sum(numeric_only=True)
    if order:
        g = g.reindex([o for o in order if o in g.index])
    tot = g.sum() if total is None else total      # total: shares of another whole (overlapping rows do not add up)
    vmean = g[[f"viirs_{y}_ytd_n" for y in range(PAST[0], PAST[1] + 1)]].sum(axis=1) / (PAST[1] - PAST[0] + 1)
    head = ["Class", "Area (thousand ha)", "Area (%)", "Burned 2015 to 2025 (thousand ha)", "Burned (%)", "Ever burned (% of class)",
            "VIIRS hotspots 2026", "Hotspots (%)", "Hotspots per 100 km²", "2026 / mean 2015 to 2025"]
    rows = []
    for k, r in g.iterrows():
        b = past_sum(r.to_frame().T).iloc[0]
        rows.append([labels.get(k, str(k)), kha(r["area_ha"]), pc(r["area_ha"], tot["area_ha"]), kha(b), pc(b, past_sum(tot.to_frame().T).iloc[0]),
                     f"{100 * r['burned_any_ha'] / r['area_ha']:.1f}" if r["area_ha"] else "-", n0(r["viirs_2026_n"]), pc(r["viirs_2026_n"], tot["viirs_2026_n"]),
                     n1(rate(r["viirs_2026_n"], r["area_ha"])), f"{r['viirs_2026_ytd_n'] / vmean[k]:.1f}" if vmean[k] else "-"])
    return head, rows


def md_table(caption, head, rows):
    out = [f"Table: {caption}", "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def numbers(T, meta, chk):
    """Every number the text quotes, with the table and column it comes from (written to sources.md)."""
    N, src = {}, {}

    def put(key, value, where):
        N[key], src[key] = value, where
    nat = basis(T["t_national"], "all").iloc[0]
    natp = basis(T["t_national"], "peat").iloc[0]
    put("land_ha", nat["area_ha"], "t_national basis all, area_ha")
    put("peat_ha", natp["area_ha"], "t_national basis peat, area_ha")
    put("modis", nat["modis_2026_n"], "t_national basis all, modis_2026_n (medium + high, static left out)")
    put("modis_high", nat["modis_2026_high_n"], "t_national basis all, modis_2026_high_n")
    put("modis_static", nat["modis_2026_static_n"], "t_national basis all, modis_2026_static_n")
    put("modis_peat", natp["modis_2026_n"], "t_national basis peat, modis_2026_n")
    put("viirs26", nat["viirs_2026_n"], "t_national basis all, viirs_2026_n")
    for y in range(2012, 2026):
        if f"viirs_{y}_n" in nat:
            put(f"viirs{y}", nat[f"viirs_{y}_n"], f"t_national basis all, viirs_{y}_n")
    vmean = np.mean([nat[f"viirs_{y}_ytd_n"] for y in range(PAST[0], PAST[1] + 1)])
    put("viirs_ytd_mean", vmean, "t_national basis all, mean of viirs_<2015..2025>_ytd_n")
    put("viirs26_ratio", nat["viirs_2026_ytd_n"] / vmean, "viirs_2026_ytd_n / mean of viirs_<2015..2025>_ytd_n")
    for y in range(meta["years"][0], meta["years"][1] + 1):
        put(f"burned{y}", nat[f"burned_{y}_ha"], f"t_national basis all, burned_{y}_ha")
    put("burned_past_sum", past_sum(nat.to_frame().T).iloc[0], "t_national basis all, sum of burned_<2015..2025>_ha")
    put("burned_any", nat["burned_any_ha"], "t_national basis all, burned_any_ha")
    put("burned_2plus", nat["burned_2plus_ha"], "t_national basis all, burned_2plus_ha")
    put("burned_peat_share", past_sum(natp.to_frame().T).iloc[0] / N["burned_past_sum"], "t_national peat/all, burned 2015-2025")
    # concession x forest
    cf = basis(T["t_concession_x_forest"], "all")
    conc = cf[cf["concession_any"]].sum(numeric_only=True)
    kaw = cf[cf["forest_group"] == "kawasan"].sum(numeric_only=True)
    apl_nc = cf[(~cf["concession_any"]) & (cf["forest_group"] == "apl")].sum(numeric_only=True)
    kaw_nc = cf[(~cf["concession_any"]) & (cf["forest_group"] == "kawasan")].sum(numeric_only=True)
    for k, s in (("conc", conc), ("kaw", kaw), ("aplnc", apl_nc), ("kawnc", kaw_nc)):
        put(f"{k}_area", s["area_ha"] / nat["area_ha"], f"t_concession_x_forest basis all, area_ha share ({k})")
        put(f"{k}_burned", past_sum(s.to_frame().T).iloc[0] / N["burned_past_sum"], f"t_concession_x_forest basis all, burned 2015-2025 share ({k})")
        put(f"{k}_modis", s["modis_2026_n"] / nat["modis_2026_n"], f"t_concession_x_forest basis all, modis_2026_n share ({k})")
        put(f"{k}_rate", rate(s["modis_2026_n"], s["area_ha"]), f"t_concession_x_forest basis all, modis_2026_n per 100 km2 ({k})")
    put("rate_all", rate(nat["modis_2026_n"], nat["area_ha"]), "t_national basis all, modis_2026_n per 100 km2")
    put("rate_peat", rate(natp["modis_2026_n"], natp["area_ha"]), "t_national basis peat, modis_2026_n per 100 km2")
    put("peat_modis_share", natp["modis_2026_n"] / nat["modis_2026_n"], "t_national peat/all, modis_2026_n")
    put("peat_area_share", natp["area_ha"] / nat["area_ha"], "t_national peat/all, area_ha")
    # in KHG
    sc = basis(T["t_scope"], "all").set_index("in_khg")
    put("khg_area", sc.loc[True, "area_ha"] / nat["area_ha"], "t_scope basis all, in_khg True, area_ha share")
    put("khg_modis", sc.loc[True, "modis_2026_n"] / nat["modis_2026_n"], "t_scope basis all, in_khg True, modis_2026_n share")
    put("khg_burned", past_sum(sc[sc.index.to_numpy(bool)]).iloc[0] / N["burned_past_sum"], "t_scope basis all, in_khg True, burned 2015-2025 share")
    # DMPG
    dm = basis(T["t_dmpg"], "all").groupby("dmpg").sum(numeric_only=True)
    put("dmpg_area", dm.loc[True, "area_ha"], "t_dmpg basis all, dmpg True, area_ha")
    put("dmpg_modis_share", dm.loc[True, "modis_2026_n"] / nat["modis_2026_n"], "t_dmpg basis all, dmpg True, modis_2026_n share")
    put("dmpg_burned_share", past_sum(dm[dm.index.to_numpy(bool)]).iloc[0] / N["burned_past_sum"], "t_dmpg basis all, dmpg True, burned 2015-2025 share")
    dc = T["t_dmpg_comparable"].groupby("dmpg").sum(numeric_only=True)
    put("dmpgc_prov", int(T["t_dmpg_comparable"]["provinces"].iloc[0]), "t_dmpg_comparable, provinces")
    for k, lab in ((True, "in"), (False, "out")):
        put(f"dmpgc_{lab}_area", dc.loc[k, "area_ha"], f"t_dmpg_comparable dmpg {k}, area_ha (peat)")
        put(f"dmpgc_{lab}_rate", rate(dc.loc[k, "viirs_2026_n"], dc.loc[k, "area_ha"]), f"t_dmpg_comparable dmpg {k}, viirs_2026_n per 100 km2 of peat")
        put(f"dmpgc_{lab}_ever", dc.loc[k, "burned_any_ha"] / dc.loc[k, "area_ha"], f"t_dmpg_comparable dmpg {k}, burned_any_ha / area_ha")
        vm = np.mean([dc.loc[k, f"viirs_{y}_ytd_n"] for y in range(PAST[0], PAST[1] + 1)])
        put(f"dmpgc_{lab}_ratio", dc.loc[k, "viirs_2026_ytd_n"] / vm, f"t_dmpg_comparable dmpg {k}, viirs_2026_ytd_n / mean 2015-2025")
    # completeness
    cp = T["t_completeness"]
    cn = cp[cp["scope"] == "Indonesia"].set_index("year")["ha_per_detection"]
    put("hapd", cn.to_dict(), "t_completeness scope Indonesia, ha_per_detection")
    ok = cn.drop([2024, 2026], errors="ignore")
    put("hapd_lo", ok.min(), "t_completeness, min over complete years")
    put("hapd_hi", ok.max(), "t_completeness, max over complete years")
    cv = cp[(cp["scope"] == "province") & (cp["year"] == 2026)].sort_values("viirs_n", ascending=False).head(4)
    put("hapd_prov", list(zip(cv["name"], cv["ha_per_detection"], cv["viirs_n"])), "t_completeness scope province, 2026, top 4 by viirs_n")
    # checks
    bt = pd.read_csv(SRC / "checks_burned_tiles.csv")
    g = bt.groupby("year")[["exact_ha", "raster_ha"]].sum()
    put("raster_err_max", float(((g["raster_ha"] - g["exact_ha"]).abs() / g["exact_ha"]).max()), "checks_burned_tiles, max over years of |raster-exact|/exact")
    put("raster_err_all", float((g["raster_ha"].sum() - g["exact_ha"].sum()) / g["exact_ha"].sum()), "checks_burned_tiles, all years")
    off = (bt["raster_ha"] - bt["raster_land_ha"]).groupby(bt["year"]).sum()
    put("png_2015", float(off.get(2015, 0)), "checks_burned_tiles 2015, raster_ha - raster_land_ha")
    st = pd.read_csv(SRC / "checks_static.csv").iloc[0]
    put("static_prec", st["precision"], "checks_static, precision")
    put("static_rec", st["recall"], "checks_static, recall")
    ka = pd.read_csv(SRC / "checks_khg_area.csv")
    put("khg_area_med", float(ka["rel_diff"].abs().median()), "checks_khg_area, median |rel_diff|")
    kf = pd.read_csv(SRC / "checks_khg_forest.csv").groupby("class")[["land_km2", "fire_km2"]].sum()
    kf = kf.drop(index=["none"], errors="ignore")
    put("khg_forest_max", float(((kf["fire_km2"] - kf["land_km2"]).abs() / kf["land_km2"]).max()), "checks_khg_forest, max class |diff|/land (mapped classes)")
    out = pd.read_csv(SRC / "hotspots_outside_villages.csv").groupby("source")["n"].sum()
    put("out_modis", int(out.get("modis", 0)), "hotspots_outside_villages, modis")
    put("out_viirs", int(out.get("viirs", 0)), "hotspots_outside_villages, viirs")
    # peat coverage
    ar = pd.read_parquet(SRC / "area.parquet")
    put("peat_unknown", float(ar.loc[ar["peat"] == 3, "area_ha"].sum()), "area.parquet, peat code 3 (peat tile not fetched)")
    put("peat_unknown_in_khg", float(ar.loc[(ar["peat"] == 3) & ar["in_khg"], "area_ha"].sum()), "area.parquet, peat code 3 inside KHG")
    import pyogrio
    data = Path(os.environ.get("REPEAT_DATA", WORKSPACE / "_data"))
    v = pyogrio.read_dataframe(data / meta["inputs"]["villages"], columns=["PROV_2023", "KABKO_2023"], read_geometry=False)
    put("L_vil", len(v), "village layer, rows"); put("L_prov", v["PROV_2023"].nunique(), "village layer, PROV_2023 distinct")
    put("L_kab", v.dropna().groupby(["PROV_2023", "KABKO_2023"]).ngroups, "village layer, province and district pairs")
    lic = pyogrio.read_dataframe(data / meta["inputs"]["licences"], columns=["IZIN_USAHA"], read_geometry=False)
    put("L_lic", lic["IZIN_USAHA"].value_counts().to_dict(), "licence layer, IZIN_USAHA counts")
    kw = pyogrio.read_dataframe(data / meta["inputs"]["forest_area"], columns=["Fungsi"], read_geometry=False)
    put("L_kws", len(kw), "forest area layer, rows"); put("L_kws_codes", kw["Fungsi"].nunique(), "forest area layer, Fungsi distinct")
    dm_ = pyogrio.read_dataframe(data / meta["inputs"]["dmpg"], layer="dmpg_villages", columns=["PROVINSI"], read_geometry=False)
    put("L_dmpg", len(dm_), "DMPG layer, rows"); put("L_dmpg_prov", dm_["PROVINSI"].nunique(), "DMPG layer, PROVINSI distinct")
    put("viirs2015_ytd", nat["viirs_2015_ytd_n"], "t_national, viirs_2015_ytd_n")
    prev = {y: nat[f"viirs_{y}_ytd_n"] for y in range(2016, 2026)}
    put("viirs_prev_max_year", max(prev, key=prev.get), "t_national, year of max viirs_<2016..2025>_ytd_n")
    put("viirs_prev_max", max(prev.values()), "t_national, max viirs_<2016..2025>_ytd_n")
    ytd = {y: nat[f"viirs_{y}_ytd_n"] for y in range(2012, 2027) if f"viirs_{y}_ytd_n" in nat}
    rank = sorted(ytd, key=ytd.get, reverse=True)
    above = [y for y in rank[: rank.index(2026)]]
    put("viirs26_rank_text", "the highest of any year since 2012" if not above else
        f"the {['', 'second', 'third', 'fourth'][len(above)]} highest since 2012, after {' and '.join(str(y) for y in above)} ({', '.join(n0(ytd[y]) for y in above)})",
        "t_national, viirs_<2012..2026>_ytd_n ranked")
    # DMPG verdict published by the investigation page
    hy = WORKSPACE / "re-peat" / "reports" / "national_profile" / "hypotheses" / "hypotheses.json"
    if hy.exists():
        q = [q for q in json.loads(hy.read_text(encoding="utf-8"))["questions"] if q["id"] == "q03"]
        if q:
            r = q[0]["result"]["all"]
            put("q03", (q[0]["verdict"]["label"], r["ratio"], r["lo"], r["hi"], r["n_clusters"]), "national_profile/hypotheses/hypotheses.json q03")
    return N, src


# --- chapters -----------------------------------------------------------------------------------------------------------
def chapters(T, meta, N, figs, FX):
    P = lambda v: f"{100 * v:.0f}%"          # noqa: E731
    yrs = list(range(meta["years"][0], meta["years"][1] + 1))
    last = pd.Timestamp(meta["modis_last"]).strftime("%-d %B %Y") if os.name != "nt" else pd.Timestamp(meta["modis_last"]).strftime("%d %B %Y").lstrip("0")
    vlast = pd.Timestamp(meta["viirs_last"]).strftime("%d %B").lstrip("0")
    C = {}
    hp = N["hapd_prov"]
    c, k_, dm_, pt_ = FX["classes"]["conc"], FX["classes"]["kawasan"], FX["classes"]["dmpg"], FX["classes"]["peat"]
    vend = pd.Timestamp(FX["window_end"]).strftime("%d %B %Y").lstrip("0")
    C["01_summary"] = f"""# 1 Summary

This report sets out where Indonesia's burned area of 2015 to 2025 and its hotspots of 2026 fall with respect to business licences (concessions), the forest area (*kawasan hutan*), the villages of the Desa Mandiri Peduli Gambut programme (DMPG) and peat. It covers all land inside the 2023 village boundaries, {mha(N['land_ha'])}. The figures say where fires were observed. They do not show the cause of a fire or who is responsible for it.

![Share of the land, of the burned area 2015 to 2025 and of the 2026 VIIRS hotspots inside concessions, forest area, DMPG villages and peat; absolute values on the right. Source: KLHK burned area, NASA FIRMS VIIRS, licences 2025, forest area 2023, SiTMAT DMPG villages, GFW peat.]({figs['shares']})

- VIIRS recorded {n0(FX['viirs26'])} hotspots on land from 1 January to {vend}, {FX['viirs26_ratio']:.1f} times the mean of 2015 to 2025 over the same months and {N['viirs26_rank_text']}. MODIS, the series KLH reports, recorded {n0(FX['modis26'])} to {last}.
- Concessions hold {c['land_pct']:.0f}% of the land, {c['burned_pct']:.0f}% of the area burned in 2015 to 2025 ({c['burned_mha']:.2f} of {FX['burned_past_mha']:.2f} million ha) and {c['viirs26_pct']:.0f}% of the 2026 hotspots ({n0(c['viirs26'])}). They had {c['rate26']:.0f} hotspots per 100 km² in 2026, against {c['rate26_outside']:.0f} outside them.
- The forest area holds {k_['land_pct']:.0f}% of the land, {k_['burned_pct']:.0f}% of the burned area and {k_['viirs26_pct']:.0f}% of the 2026 hotspots.
- Peat, where it is mapped, covers {pt_['land_pct']:.0f}% of the land and holds {pt_['burned_pct']:.0f}% of the burned area and {pt_['viirs26_pct']:.0f}% of the 2026 hotspots.
- DMPG villages cover {dm_['land_pct']:.0f}% of the land and hold {dm_['viirs26_pct']:.0f}% of the 2026 hotspots. The programme works on fire-prone peat; within their provinces, DMPG village peat had {n1(N['dmpgc_in_rate'])} hotspots per 100 km² in 2026 against {n1(N['dmpgc_out_rate'])} on other peat, and hotspots rose about as much in both ({N['dmpgc_in_ratio']:.1f} and {N['dmpgc_out_ratio']:.1f} times the 2015 to 2025 mean).
- Five provinces hold {FX['top5_share']:.0f}% of the 2026 hotspots.
- The burned-area maps of 2024 and 2026 are incomplete as delivered ({N['hapd'][2024]:.1f} and {N['hapd'][2026]:.1f} ha per VIIRS hotspot against {N['hapd_lo']:.1f} to {N['hapd_hi']:.1f} ha in the other years), so 2026 is described through its hotspots.
"""
    pk = FX["peak_month"]
    top = FX["provinces"][:5]
    C["02_season"] = f"""# 2 The 2026 fire season

VIIRS gives the 2026 figures in this report. It sees fires at 375 m against 1 km for MODIS, and one sensor (S-NPP) has recorded Indonesia since 2012, so 2026 can be set against earlier years over the same months. MODIS is the series KLH reports; its 2026 total is given beside each VIIRS figure where it matters. The 2026 VIIRS record runs to {vend}: January to July from the standard product, August to October from the near-real-time product. November and December are not yet in it.

![VIIRS hotspots per month in 2026 against the mean of 2015 to 2025. Medium and high confidence, likely gas flares and volcanoes left out. Source: NASA FIRMS VIIRS S-NPP.]({figs['months']})

Hotspots stayed near the usual level until June. From July they rose far above it: {n0(FX['month26'][str(pk)] if str(pk) in FX['month26'] else FX['month26'][pk])} in {pd.Timestamp(2026, pk, 1):%B}, against a mean of {n0(FX['month_mean_past'][str(pk)] if str(pk) in FX['month_mean_past'] else FX['month_mean_past'][pk])} for that month in 2015 to 2025. Over 1 January to {vend}, VIIRS counts {n0(FX['viirs26'])} hotspots, {FX['viirs26_ratio']:.1f} times the mean of 2015 to 2025; {'no year since 2012 had more' if FX['viirs_rank_since_2012'] == 1 else 'only ' + str(FX['viirs_max_year']) + ' had more' if FX['viirs_rank_since_2012'] == 2 else str(FX['viirs_rank_since_2012'] - 1) + ' years had more'} over the same months.

![VIIRS hotspots per year from 1 January to {vlast}, inside and outside concessions. Source: NASA FIRMS VIIRS S-NPP, licences 2025.]({figs['years']})

![VIIRS hotspots of 2026 per 100 km² of land, by province. Source: NASA FIRMS VIIRS S-NPP, village boundaries 2023.]({figs['map']})

Five provinces hold {FX['top5_share']:.0f}% of the 2026 hotspots: {', '.join(f"{p['province']} ({n0(p['viirs26'])})" for p in top)}. The share inside concessions differs widely between them, from {min(p['conc_pct'] for p in top):.0f}% to {max(p['conc_pct'] for p in top):.0f}%.

![The ten provinces with the most VIIRS hotspots in 2026, inside and outside concessions. Source: NASA FIRMS VIIRS S-NPP, licences 2025.]({figs['provinces']})

![VIIRS hotspots of 2026 per 100 km² by land status; dashed line: all land. Source: this analysis.]({figs['rates']})

Near known static heat sources such as gas flares, {n0(FX['viirs26_with_static'] - FX['viirs26'])} further VIIRS detections are set apart. With them the 2026 total is {n0(FX['viirs26_with_static'])}, and the shares by land status change by at most {FX['static_share_shift_max']:.1f} percentage points. With them, MODIS counts {n0(FX['modis26_with_static'])}.
"""
    C["03_data"] = f"""# 3 Data

All layers were used as delivered. Table 3.1 lists them.

Table: Input layers. Source: data catalogue of the project.

| Layer | Content | Source | Date | Scale or resolution |
|---|---|---|---|---|
| Village boundaries | {n0(N['L_vil'])} villages, {N['L_prov']} provinces, {N['L_kab']} districts and cities; the land mask and the province of every cell | KLH | 2023 | Polygons |
| KHG boundaries | 865 peat hydrological units | KLHK | 2017 | Polygons |
| Business licences | {n0(N['L_lic']['Perkebunan Kelapa Sawit'])} oil palm, {n0(N['L_lic']['Pertambangan'])} mining, {n0(N['L_lic']['PBPH'])} forest concession (PBPH), {n0(N['L_lic']['PPHTR'])} plantation forest (PPHTR) and {n0(N['L_lic']['PPHKM'])} community forest (PPHKM) polygons | Project team; issuing agency not stated | 2025 | Polygons |
| Forest area function | {n0(N['L_kws'])} polygons in {N['L_kws_codes']} function codes | Project team, inferred KLHK | 2023 | 1:250,000 |
| DMPG villages | {n0(N['L_dmpg'])} villages in {N['L_dmpg_prov']} provinces | SiTMAT portal, KLH | 2017 to 2024 | Polygons |
| Burned area | One polygon per burned patch, with a flag for each burn year 2015 to 2026 | KLHK; production method not stated | 2015 to 2026 | Polygons |
| Peat extent | Union of Miettinen et al. (2016) and Gumbricht et al. (2017) | Global Forest Watch, CC BY 4.0 | Version 2023 | About 76 m |
| MODIS hotspots 2026 | KLH file to 15 September, NASA FIRMS MODIS near real time after it; low, medium and high confidence | KLH, NASA FIRMS | 1 January to {last} | 1 km |
| VIIRS hotspots | S-NPP country archive 2012 to 2025 and 2026 standard and near-real-time files | NASA FIRMS | 2012 to {vlast} 2026 | 375 m |

A cell is in a concession when it lies in an oil palm, mining, PBPH or PPHTR licence. Community forest permits (PPHKM, *perhutanan sosial*) are social forestry permits and are not counted as concessions: their land keeps its forest area class. Where licences overlap, the land counts once in the concession totals and, in the table by type, under the first type in the order oil palm, mining, plantation forest, forest concession. The licence layer covers only the licences it holds. Land with unlicensed plantations counts as "no concession": at one KHG studied by the project, Mendahara-Batanghari, a forest-type map shows 43.7% of the land as tree crops outside any licence.

The {N['L_kws_codes']} forest area function codes are grouped into conservation (nature reserves, wildlife reserves, national parks, recreation parks, grand forest parks, hunting parks and their marine counterparts), protection forest (HL), production forest (HP, HPT), convertible production forest (HPK), other land use (APL), and water or undefined. "Forest area" means the first four groups.

A hotspot is a satellite detection of heat. One fire can give many detections, and a short or small fire may give none. VIIRS (375 m pixels, one sensor since 2012) gives the 2026 figures and the comparison with earlier years. MODIS (1 km pixels) is the series KLH reports and is given beside it. The two are never added. Low-confidence detections are left out.
"""
    C["04_method"] = f"""# 4 Method

![The analysis: every layer on one 30 m grid; cells and hotspots take the classes where they lie. Source: this analysis.]({figs['method']})

All layers are laid on one equal-area grid of 30 m cells covering Indonesia, processed in tiles of 90 km. Every cell takes the value of each layer at its centre: its district and province, KHG, forest area class, the licence types it lies in, whether it lies in a DMPG village, whether it is peat, and the years it burned. Cells outside the village boundaries (sea, neighbouring countries and small gaps in the village layer) are left out. Areas are cell counts times the cell area, so overlapping polygons are never counted twice.

Hotspots take the classes of the cell they fall in. The VIIRS archive records a type for each detection (vegetation fire, volcano, static land source such as a gas flare, offshore), and only vegetation fires are kept. The MODIS file and the recent VIIRS file carry no type. A detection of these within 1 km (MODIS) or 375 m (VIIRS) of a VIIRS detection typed as volcano, static land source or offshore in any year is flagged as a likely static source and reported apart. Applied to the typed VIIRS file of 2026, with static locations taken from 2012 to 2025 only, the rule flags static sources with a precision of {N['static_prec']:.2f} and a recall of {N['static_rec']:.2f}. KLH's own hotspot counts include these sources: with them, MODIS 2026 counts {n0(N['modis'] + N['modis_static'])} medium and high confidence hotspots on land.

Rates are hotspots per 100 km² of the class, so that classes of different size can be compared. VIIRS years are compared over the same calendar window, 1 January to {vlast}. Burned area is summed per year; "ever burned" counts a cell once however often it burned.

Every result is checked against an independent total:

- the burned area on the grid differs from the exact polygon area by {100 * abs(N['raster_err_all']):.2f}% over all years and by at most {100 * N['raster_err_max']:.1f}% in any year;
- every breakdown (by concession, forest area, DMPG, island, province) adds up to the national total exactly;
- the area of each KHG agrees with an earlier count on a 100 m grid to a median of {100 * N['khg_area_med']:.2f}%, and the forest area classes inside KHG to within {100 * N['khg_forest_max']:.2f}%;
- {n0(N['png_2015'])} ha of the 2015 burned area lies east of the border at 141° E, in Papua New Guinea, and {n0(N['out_modis'])} MODIS and {n0(N['out_viirs'])} VIIRS hotspots lie outside the village boundaries; both are left out.

The licences of 2025 and the forest area of 2023 are matched to every year, so earlier burns may have occurred when the land had another status.
"""
    hapd = N["hapd"]
    rows = [[y, n0(N[f"burned{y}"]), n0(N.get(f"viirs{y}", N["viirs26"] if y == 2026 else 0)), f"{hapd[y]:.2f}", "incomplete" if y in (2024, 2026) else ""] for y in yrs]
    C["05_quality"] = f"""# 5 Completeness of the burned-area maps

Burned area and hotspots measure the same fires in different ways. Between 2015 and 2025 the burned area per VIIRS hotspot lies between {N['hapd_lo']:.1f} and {N['hapd_hi']:.1f} ha in every year except 2024 ({hapd[2024]:.2f}). In 2026 it is {hapd[2026]:.2f}: VIIRS recorded {n0(N['viirs26'])} hotspots on land to {vlast}, {N['viirs26_rank_text']}, while the burned-area map holds {n0(N['burned2026'])} ha. In the provinces with the most hotspots in 2026 the ratio is {', '.join(f'{p} {v:.2f}' for p, v, _ in hp[:3])}. The 2026 map, and that of 2024, are therefore incomplete as delivered.

{md_table("Burned area and VIIRS hotspots per year, all land. Source: KLHK burned area, NASA FIRMS VIIRS S-NPP (medium and high confidence, vegetation fires).", ["Year", "Burned area (ha)", "VIIRS hotspots", "ha per hotspot", "Note"], rows)}
Burned-area shares in this report are taken over 2015 to 2025, which includes the incomplete 2024 at its small weight. The 2026 season is described through the MODIS and VIIRS hotspots.
"""
    cfa = basis(T["t_concession_x_forest"], "all").assign(cls=lambda d: np.where(d["concession_any"], "Concession", "No concession") + ", " + d["forest_group"].map({"kawasan": "forest area", "apl": "APL", "other": "water or undefined"}))
    order = [f"{a}, {b}" for a in ("Concession", "No concession") for b in ("forest area", "APL", "water or undefined")]
    h, r = class_table(cfa, "cls", {}, order)
    C["06_national"] = f"""# 6 Concessions and forest area

Table 6.1 crosses the two layers. The last column compares VIIRS hotspots of 2026 with the mean of 2015 to 2025 over the same months; 1 means as in earlier years.

{md_table("Land, burned area and hotspots by concession and forest area, all land. Source: this analysis.", h, r)}
![Burned area per year inside and outside concessions. Grey bands: years whose burned-area map is incomplete. Source: KLHK burned area, licences 2025.]({figs['burned']})
"""
    ct = basis(T["t_concession_type"], "all")
    h, r = class_table(ct, "concession", LIC, ["sawit", "tambang", "pphtr", "pbph", "none"])
    lt = basis(T["t_licence_type"], "all")
    h2, r2 = class_table(lt, "licence", LIC, ["sawit", "tambang", "pphtr", "pbph", "pphkm"], total=basis(T["t_national"], "all").sum(numeric_only=True))
    C["07_types"] = f"""# 7 Concession types

In Table 7.1 every cell counts once: where licences overlap, the land goes to the first type in the order of the table. Table 7.2 counts each licence type over all the land it covers, so overlapping licences appear under each of their types and the rows do not add up; community forest permits (PPHKM), which are not concessions, are shown for comparison.

{md_table("Land, burned area and hotspots by concession type, each cell counted once, all land. Source: this analysis.", h, r)}
{md_table("The same by licence type, overlapping licences counted under each type. Shares are of all land. Source: this analysis.", h2[:1] + h2[1:], r2)}
"""
    ff = basis(T["t_forest_function"], "all")
    h, r = class_table(ff, "kawasan", KWS, ["cons", "hl", "prod", "hpk", "apl", "other", "none"])
    ffc = ff[ff["concession_any"]]
    h2, r2 = class_table(ffc, "kawasan", KWS, ["cons", "hl", "prod", "hpk", "apl", "other"])
    C["08_forest"] = f"""# 8 Forest area function

{md_table("Land, burned area and hotspots by forest area function, all land. Source: this analysis.", h, r)}
Table 8.2 shows the same for the land inside concessions only; shares are of the concession land.

{md_table("Forest area function of the land inside concessions. Source: this analysis.", h2, r2)}
"""
    dmc = T["t_dmpg_comparable"].assign(cls=lambda d: np.where(d["dmpg"], "DMPG village", "Other peat") + np.where(d["concession_any"], ", concession", ", no concession"))
    h, r = class_table(dmc, "cls", {}, ["DMPG village, no concession", "DMPG village, concession", "Other peat, no concession", "Other peat, concession"])
    q = N.get("q03")
    qtext = (f"The project's investigation of the 2026 season compared the rise in hotspots on DMPG village land with the rise on land outside it within the same KHG and land tenure class. The ratio of the two rises was {q[1]:.2f} (95% interval {q[2]:.2f} to {q[3]:.2f}, {q[4]} KHG), so that test was {q[0]}: it neither shows nor rules out a smaller rise in DMPG villages."
             if q else "")
    C["09_dmpg"] = f"""# 9 DMPG villages

DMPG villages cover {mha(N['dmpg_area'])}, {P(N['dmpg_area'] / N['land_ha'])} of the land, and hold {P(N['dmpg_burned_share'])} of the burned area of 2015 to 2025 and {FX['classes']['dmpg']['viirs26_pct']:.0f}% of the 2026 VIIRS hotspots. The programme chose villages on fire-prone peat, so a national comparison mixes the programme with where it works. Table 9.1 compares DMPG village peat with other peat in the {N['dmpgc_prov']} provinces that hold DMPG villages.

{md_table(f"Peat in DMPG villages and other peat, provinces with DMPG villages. Shares are of that peat. Source: this analysis.", h, r)}
On this comparable land, {P(N['dmpgc_in_ever'])} of the DMPG village peat burned at least once in 2015 to 2026, against {P(N['dmpgc_out_ever'])} of other peat. VIIRS hotspots of 2026 were {N['dmpgc_in_ratio']:.1f} times the 2015 to 2025 mean in DMPG villages and {N['dmpgc_out_ratio']:.1f} times elsewhere. {qtext}

![VIIRS hotspots of 2026 per 100 km² of peat in DMPG villages and on other peat, by province (provinces with at least 100 km² of peat on each side). Source: NASA FIRMS VIIRS S-NPP, SiTMAT DMPG villages, GFW peat.]({figs['dmpg']})
"""
    isl = basis(T["t_island"], "all")
    h, r = class_table(isl, "island", {k: k.replace("Pulau ", "") for k in isl["island"]})
    pr = basis(T["t_province"], "all")
    g = pr.groupby(["island", "province"]).sum(numeric_only=True).reset_index()
    cpr = pr[pr["concession_any"]].groupby("province").sum(numeric_only=True)
    kpr = pr[pr["forest_group"] == "kawasan"].groupby("province").sum(numeric_only=True)
    g = g.sort_values("viirs_2026_n", ascending=False)
    prow = []
    for _, x in g.iterrows():
        b = past_sum(x.to_frame().T).iloc[0]
        cb = past_sum(cpr.loc[[x["province"]]]).iloc[0] if x["province"] in cpr.index else 0
        kb = past_sum(kpr.loc[[x["province"]]]).iloc[0] if x["province"] in kpr.index else 0
        prow.append([x["province"], x["island"].replace("Pulau ", ""), kha(x["area_ha"]), kha(b), pc(cb, b), pc(kb, b), n0(x["viirs_2026_n"]),
                     pc(cpr["viirs_2026_n"].get(x["province"], 0), x["viirs_2026_n"]), pc(kpr["viirs_2026_n"].get(x["province"], 0), x["viirs_2026_n"]),
                     n1(rate(x["viirs_2026_n"], x["area_ha"]))])
    C["10_regions"] = f"""# 10 Islands and provinces

{md_table("Land, burned area and hotspots by island. Source: this analysis.", h, r)}
Table A.1 in the annex gives every province, ordered by the number of 2026 hotspots.
"""
    pp = basis(T["t_concession_x_forest"], "peat").assign(cls=lambda d: np.where(d["concession_any"], "Concession", "No concession") + ", " + d["forest_group"].map({"kawasan": "forest area", "apl": "APL", "other": "water or undefined"}))
    h, r = class_table(pp, "cls", {}, order)
    C["11_peat"] = f"""# 11 Peat

Peat is taken from the composite peat map of Global Forest Watch. It was obtained for the map tiles that touch a KHG. The other {mha(N['peat_unknown'])} of land{' (none of it inside a KHG)' if N['peat_unknown_in_khg'] < 1 else ''} has no peat information and counts as not peat, so the peat figures are a lower bound outside the KHG. Table 11.1 repeats Table 6.1 for peat only; shares are of the peat.

{md_table("Peat, burned peat and hotspots on peat by concession and forest area. Source: this analysis.", h, r)}
"""
    C["12_limits"] = f"""# 12 Limitations

- The burned-area maps of 2024 and 2026 are incomplete as delivered (chapter 5), and the method used to make the maps is not documented with them.
- The licence layer of 2025 and the forest area map of 2023 are matched to burns since 2015. Land may have been licensed or reclassified after it burned.
- The licence layer holds the licences it was given. Unlicensed plantations and other managed land count as "no concession".
- Hotspots and burned area inside a licence or a forest area class are a spatial overlap. They do not show the cause of a fire or who is responsible.
- MODIS and VIIRS count fires differently and are never added or compared in absolute numbers. The MODIS file joins two sources at 15 September 2026; over the 15 days where both exist the NASA source has 4.3% more detections.
- The static-source flag misses about a third of the static detections and wrongly flags about one in eight of those it flags (chapter 4).
- A cell or hotspot takes the class at its centre or position. A MODIS pixel is about 1 km across, so a hotspot near a boundary may come from the neighbouring class.
"""
    pr_head = ["Province", "Island", "Land (thousand ha)", "Burned 2015 to 2025 (thousand ha)", "Burned in concessions (%)", "Burned in forest area (%)",
               "VIIRS hotspots 2026", "Hotspots in concessions (%)", "Hotspots in forest area (%)", "Hotspots per 100 km²"]
    kt = T["t_khg"]
    kt = kt[kt["basis"] == "all"].groupby("khg_id").sum(numeric_only=True)
    names = pd.read_csv(WORKSPACE / "re-peat" / "sites" / "khg_registry.csv")
    ncol = next(c for c in names.columns if c.lower() in ("nama", "name", "nama_khg", "khg"))
    icol = next(c for c in names.columns if c.lower() in ("khg_code", "khg_id", "kode", "code"))
    nm = dict(zip(names[icol], names[ncol]))
    kc = T["t_khg"][(T["t_khg"]["basis"] == "all") & T["t_khg"]["concession_any"]].groupby("khg_id")["viirs_2026_n"].sum()
    top = kt.sort_values("viirs_2026_n", ascending=False).head(30)
    krow = [[str(nm.get(k, k)).removeprefix("KHG "), kha(r_["area_ha"]), kha(past_sum(r_.to_frame().T).iloc[0]), n0(r_["viirs_2026_n"]), pc(kc.get(k, 0), r_["viirs_2026_n"]),
             n1(rate(r_["viirs_2026_n"], r_["area_ha"]))] for k, r_ in top.iterrows()]
    C["13_annex"] = f"""# Annex A Tables

{md_table("Land, burned area and hotspots by province, ordered by VIIRS hotspots of 2026. Source: this analysis.", pr_head, prow)}
{md_table("The 30 KHG with the most VIIRS hotspots in 2026. Source: this analysis.", ["KHG", "Land (thousand ha)", "Burned 2015 to 2025 (thousand ha)", "VIIRS hotspots 2026", "In concessions (%)", "Hotspots per 100 km²"], krow)}
"""
    return C


def write_sources(N, src):
    lines = ["# Sources of the numbers in the report", "",
             f"Tables and checks in {SRC.relative_to(WORKSPACE).as_posix()} (repeat-national-fire, repeat-national-fire-tables).", ""]
    for k in N:
        v = N[k]
        lines.append(f"- {k} = {v if not isinstance(v, float) else round(v, 4)}: {src[k]}")
    lines += ["", "Figures stated in the text from other workspace files", "",
              "- 43.7% of Mendahara-Batanghari as tree crops with no licence: repeat-neraca/docs/reports/forest_type_managed.md, table of KHG Sungai Mendahara - Sungai Batanghari, row tree_crop, column no licence (ForTy 2020, share of the KHG area).",
              "- MODIS file joins KLH and NASA FIRMS at 15 September 2026, FIRMS 4.3% more detections over 1 to 15 September: re-peat/docs/15-national-profile.md, section This year's hotspots (from reports/investigations/hotspot_splice/hotspot_splice.md).",
              "- 2026 test of DMPG villages (ratio, interval, verdict): re-peat/reports/national_profile/hypotheses/hypotheses.json, question q03.",
              "", "References cited", ""]
    refs = WORKSPACE / "re-peat" / "reports" / "project_report" / "references.csv"
    if refs.exists():
        r = pd.read_csv(refs)
        key = r.columns[0]
        for k in ("Miettinen2016", "Gumbricht2017"):
            row = r[r[key] == k]
            if len(row):
                lines.append(f"- {row.iloc[0, 1]}")
    (OUT / "sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def drop_blank_before_chapters(doc):
    """Start each chapter with "page break before" on its heading instead of a paragraph holding a page break: a break
    paragraph that lands on a fresh page (the page before was full) would leave that page blank. Empty spacers go too."""
    ps = doc.paragraphs
    for i in range(1, len(ps)):
        if ps[i].style.name != "Heading 1":
            continue
        ps[i].paragraph_format.page_break_before = True
        j = i - 1
        while j >= 0 and not ps[j].text.strip() and not ps[j]._p.xpath(".//w:drawing|.//w:fldChar|.//w:instrText|.//w:fldSimple"):
            ps[j]._p.getparent().remove(ps[j]._p)
            j -= 1


def method_png():
    """The method diagram (diagrams/method.drawio, editable in draw.io) exported to PNG with the draw.io desktop app when stale."""
    import subprocess
    src, png = OUT / "diagrams" / "method.drawio", OUT / "figures" / "fig_method.png"
    if not png.exists() or png.stat().st_mtime < src.stat().st_mtime:
        exe = os.environ.get("DRAWIO", r"C:\Program Files\draw.io\draw.io.exe")
        subprocess.run([exe, "-x", "-f", "png", "-s", "2", "-o", str(png), str(src)], check=True, capture_output=True, timeout=300)
    return png


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(OUT / "RE-PEAT_fire_land_status.docx"))
    a = ap.parse_args(argv)
    T, meta, chk = load()
    import fire_landstatus_figs as FG
    FX, out = FG.build("report")
    figs = {k: v.relative_to(WORKSPACE).as_posix() for k, v in out["report"].items()}
    figs["method"] = method_png().relative_to(WORKSPACE).as_posix()
    N, src = numbers(T, meta, chk)
    C = chapters(T, meta, N, figs, FX)
    cdir = OUT / "chapters"
    cdir.mkdir(parents=True, exist_ok=True)
    for f in cdir.glob("*.md"):
        f.unlink()
    for name, text in C.items():
        (cdir / f"{name}.md").write_text(text, encoding="utf-8")
    write_sources(N, src)
    PR.TITLE = "Burned area and hotspots by land status"
    PR.SUBTITLE = "Indonesia: concessions, forest area and DMPG villages, 2015 to 2026"
    b = PR.Builder()
    b.front()
    for name in sorted(C):
        b.markdown(C[name])
    drop_blank_before_chapters(b.doc)
    b.doc.save(a.out)
    print(f"wrote {a.out}; pending: {b.pending}")


if __name__ == "__main__":
    main()
