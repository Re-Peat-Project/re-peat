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
    put("peat_unknown", float(ar.loc[ar["peat"] == 3, "area_ha"].sum()), "area.parquet, peat code 3 (no peat information)")
    put("peat_klh", float(ar.loc[ar["peat"] == 1, "area_ha"].sum()), "area.parquet, peat code 1 (KLH peat cells on land)")
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
    # repeated burns (t_times_burned, all land)
    tb = T["t_times_burned"]
    tb = tb[tb["basis"] == "all"]
    rep = tb[["burned_2x_ha", "burned_3x_ha", "burned_4plus_ha"]].sum(axis=1)
    put("rep_ha", float(rep.sum()), "t_times_burned basis all, burned_2x_ha + burned_3x_ha + burned_4plus_ha")
    put("rep_conc_share", float(rep[tb["concession_any"]].sum() / rep.sum()), "t_times_burned basis all, concession_any True, share of burned 2+ times")
    put("rep_dmpg_share", float(rep[tb["dmpg"]].sum() / rep.sum()), "t_times_burned basis all, dmpg True, share of burned 2+ times")
    # KLH priority area (repeat-national-ppeg) and actors (re-peat/tools/ppeg_roles.py)
    pdir, rdir = SRC.parent / "ppeg", WORKSPACE / "re-peat" / "reports" / "ppeg_roles"
    pk = pd.read_csv(pdir / "ppeg_khg.csv")
    pn = pd.read_csv(pdir / "ppeg_national.csv", index_col=0)["value"]
    put("pr_ha", float(pn["priority_ha"]), "ppeg_national.csv, priority_ha (SKEG 2024 damaged peat)")
    put("pr_khg", int(pk["priority"].sum()), "ppeg_khg.csv, priority")
    put("pr_khg_vil", int(pk["in_target_villages"].sum()), "ppeg_khg.csv, in_target_villages")
    put("pr_khg_skeg", int(pk["has_skeg_damage"].sum()), "ppeg_khg.csv, has_skeg_damage")
    put("pr_khg_both", int((pk["in_target_villages"] & pk["has_skeg_damage"]).sum()), "ppeg_khg.csv, both flags")
    put("pr_khg_vil_only", int((pk["in_target_villages"] & ~pk["has_skeg_damage"]).sum()), "ppeg_khg.csv, in_target_villages only")
    put("pr_khg_skeg_only", int((pk["has_skeg_damage"] & ~pk["in_target_villages"]).sum()), "ppeg_khg.csv, has_skeg_damage only")
    put("pr_in_vil", float(pn["priority_in_target_villages_ha"]), "ppeg_national.csv, priority_in_target_villages_ha")
    put("pr_dome", float(pn["priority_dome_ha"]), "ppeg_national.csv, priority_dome_ha")
    put("pr_thick", float(pn["priority_thick3m_ha"]), "ppeg_national.csv, priority_thick3m_ha")
    for k in ("ringan", "sedang", "berat", "sangat_berat"):
        put(f"pr_{k}", float(pn[f"priority_{k}_ha"]), f"ppeg_national.csv, priority_{k}_ha")
    srt = pk[pk["has_skeg_damage"]].sort_values("priority_ha", ascending=False)
    cs = srt["priority_ha"].cumsum() / srt["priority_ha"].sum()
    put("pr_half_khg", int((cs < 0.5).sum() + 1), "ppeg_khg.csv, KHG holding half of priority_ha, largest first")
    put("pr_top3", [(n.removeprefix("KHG ").replace("Sungai ", ""), float(h)) for n, h in zip(srt["khg_name"][:3], srt["priority_ha"][:3])], "ppeg_khg.csv, three largest priority_ha")
    ra = pd.read_csv(rdir / "roles_actor.csv")
    put("pr_actors", ra.to_dict("records"), "ppeg_roles/roles_actor.csv")
    rp = pd.read_csv(rdir / "roles_province.csv", index_col=0)
    put("pr_prov", [(p, float(r["total"]), float(r["Intervensi Perusahaan"] + r["Kolaborasi Perusahaan (Area Buffer)"])) for p, r in rp.head(5).iterrows()], "ppeg_roles/roles_province.csv, five largest")
    rf = json.loads((WORKSPACE / "_slides" / "build" / "roles_facts.json").read_text(encoding="utf-8"))
    put("pr_canal", rf["canal_km"], "roles_facts.json canal_km (national profile canal_km_<class> over the priority KHG)")
    put("pr_canal_blank", rf["canal_blank"], "roles_facts.json canal_blank")
    put("pr_ps", rf["ps_ha"], "roles_facts.json ps_ha (KET_KANAL primary or secondary)")
    put("pr_forest", rf["forest_ha"], "roles_facts.json forest_ha"); put("pr_forest_lic", rf["forest_lic_ha"], "roles_facts.json forest_lic_ha")
    put("pr_r1", rf["r1_ha"], "roles_facts.json r1_ha"); put("pr_r2", rf["r2_ha"], "roles_facts.json r2_ha")
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

This report sets out where Indonesia's burned area of 2015 to 2025 and its hotspots of 2026 fall with respect to business licences (concessions), the forest area (*kawasan hutan*), the villages of the Desa Mandiri Peduli Gambut programme (DMPG) and peat. It covers all land inside the 2023 village boundaries, {mha(N['land_ha'])}. The figures say where fires were observed. They do not show the cause of a fire or who is responsible for it. The last chapters set out KLH's priority area for peat restoration, who covers which part of it and the roles of the ministries.

![Left: each class's share of Indonesia's land (hollow dot), of the burned area 2015 to 2025 and of the 2026 VIIRS hotspots. Right: VIIRS hotspots of 2026 per 100 km² inside the class and on the rest of the land. Source: KLHK burned area, NASA FIRMS VIIRS, licences 2025, forest area 2023, SiTMAT DMPG villages, KLH peat (PPEG 2026).]({figs['shares']})

- VIIRS recorded {n0(FX['viirs26'])} hotspots on land from 1 January to {vend}, {FX['viirs26_ratio']:.1f} times the mean of 2015 to 2025 over the same months and {N['viirs26_rank_text']}. MODIS, the series KLH reports, recorded {n0(FX['modis26'])} to {last}.
- Concessions hold {c['land_pct']:.0f}% of the land, {c['burned_pct']:.0f}% of the area burned in 2015 to 2025 ({c['burned_mha']:.2f} of {FX['burned_past_mha']:.2f} million ha) and {c['viirs26_pct']:.0f}% of the 2026 hotspots ({n0(c['viirs26'])}). They had {c['rate26']:.0f} hotspots per 100 km² in 2026, against {c['rate26_outside']:.0f} outside them.
- The forest area holds {k_['land_pct']:.0f}% of the land, {k_['burned_pct']:.0f}% of the burned area and {k_['viirs26_pct']:.0f}% of the 2026 hotspots.
- Peat covers {pt_['land_pct']:.0f}% of the land and holds {pt_['burned_pct']:.0f}% of the burned area and {pt_['viirs26_pct']:.0f}% of the 2026 hotspots.
- DMPG villages cover {dm_['land_pct']:.0f}% of the land and hold {dm_['viirs26_pct']:.0f}% of the 2026 hotspots. The programme works on fire-prone peat; within their provinces, DMPG village peat had {n1(N['dmpgc_in_rate'])} hotspots per 100 km² in 2026 against {n1(N['dmpgc_out_rate'])} on other peat, and hotspots rose about as much in both ({N['dmpgc_in_ratio']:.1f} and {N['dmpgc_out_ratio']:.1f} times the 2015 to 2025 mean).
- {mha(N['rep_ha'])} burned in two or more different years of 2015 to 2026. Concessions hold {P(N['rep_conc_share'])} of this repeatedly burned land and DMPG villages {P(N['rep_dmpg_share'])} (chapter 10).
- Five provinces hold {FX['top5_share']:.0f}% of the 2026 hotspots.
- KLH's priority area is {mha(N['pr_ha'])} of peat with damaged ecosystem status (SKEG 2024) in {N['pr_khg']} priority KHG (chapter 13). KLH assigns {P((N['pr_actors'][0]['ha'] + N['pr_actors'][1]['ha']) / N['pr_ha'])} of it to licence holders, inside their licences or in the 5 km buffer around them, {P(N['pr_actors'][2]['ha'] / N['pr_ha'])} to the Ministry of Forestry and {P(N['pr_actors'][3]['ha'] / N['pr_ha'])} to KLH/BPLH (chapters 14 and 15).
- The burned-area maps of 2024 and 2026 are incomplete as delivered ({N['hapd'][2024]:.1f} and {N['hapd'][2026]:.1f} ha per VIIRS hotspot against {N['hapd_lo']:.1f} to {N['hapd_hi']:.1f} ha in the other years), so 2026 is described through its hotspots.
"""
    pk = FX["peak_month"]
    top = FX["provinces"][:5]
    C["02_season"] = f"""# 2 The 2026 fire season

VIIRS gives the 2026 figures in this report. It sees fires at 375 m against 1 km for MODIS, and one sensor (S-NPP) has recorded Indonesia since 2012, so 2026 can be set against earlier years over the same months. MODIS is the series KLH reports; its 2026 total is given beside each VIIRS figure where it matters. The 2026 VIIRS record runs to {vend}: January to July from the standard product, August to October from the near-real-time product. November and December are not yet in it.

![VIIRS hotspots per month in 2026 against the mean of 2015 to 2025. Medium and high confidence, likely gas flares and volcanoes left out. Source: NASA FIRMS VIIRS S-NPP.]({figs['months_2026']})

Hotspots stayed near the usual level until June. From July they rose far above it: {n0(FX['month26'][str(pk)] if str(pk) in FX['month26'] else FX['month26'][pk])} in {pd.Timestamp(2026, pk, 1):%B}, against a mean of {n0(FX['month_mean_past'][str(pk)] if str(pk) in FX['month_mean_past'] else FX['month_mean_past'][pk])} for that month in 2015 to 2025. Over 1 January to {vend}, VIIRS counts {n0(FX['viirs26'])} hotspots, {FX['viirs26_ratio']:.1f} times the mean of 2015 to 2025; {'no year since 2012 had more' if FX['viirs_rank_since_2012'] == 1 else 'only ' + str(FX['viirs_max_year']) + ' had more' if FX['viirs_rank_since_2012'] == 2 else str(FX['viirs_rank_since_2012'] - 1) + ' years had more'} over the same months.

![VIIRS hotspots per year from 1 January to {vlast}, inside and outside concessions. Source: NASA FIRMS VIIRS S-NPP, licences 2025.]({figs['years']})

![VIIRS hotspots of 2026 per 100 km² of land, by province. Source: NASA FIRMS VIIRS S-NPP, village boundaries 2023.]({figs['map_2026']})

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
| Peat extent | Peat land (lahan gambut) of KLH's integrated thematic analysis for peat ecosystem restoration, {mha(N['peat_klh'])} | KLH | April 2026 | Polygons, counted on the 30 m grid |
| MODIS hotspots 2026 | KLH file to 15 September, NASA FIRMS MODIS near real time after it; low, medium and high confidence | KLH, NASA FIRMS | 1 January to {last} | 1 km |
| VIIRS hotspots | S-NPP country archive 2012 to 2025 and 2026 standard and near-real-time files | NASA FIRMS | 2012 to {vlast} 2026 | 375 m |
| PPEG integrated thematic analysis | Overlay of KHG, peat, SKEG 2024 damage status, canal-affected zone, licences, forest area, landform and peat thickness, with an intervention class and an actor for every polygon | KLH | April 2026 | Polygons |
| Target villages | 2,004 villages for peat ecosystem restoration | Bluebook 2026 | April 2026 | Polygons |

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
    # chapters 6 to 11 lead with charts; the exact values are the annex tables (A.n), one table per chart
    annex = []

    def cell_rates(basis_):
        t = basis(T["t_concession_x_forest"], basis_)
        t = t[t["forest_group"].isin(["kawasan", "apl"])]
        return {(bool(r.concession_any), r.forest_group): rate(r.viirs_2026_n, r.area_ha) for r in t.itertuples()}
    ca, cp = cell_rates("all"), cell_rates("peat")
    GL = {"kawasan": "forest area", "apl": "APL"}

    def cell_txt(c, conc, g):
        return f"{c[(conc, g)]:.0f} ({'in concessions' if conc else 'outside concessions'}, {GL[g]})"
    hi_a, lo_a = max(ca, key=ca.get), min(ca, key=ca.get)
    hi_p, lo_p = max(cp, key=cp.get), min(cp, key=cp.get)
    cfa = basis(T["t_concession_x_forest"], "all").assign(cls=lambda d: np.where(d["concession_any"], "Concession", "No concession") + ", " + d["forest_group"].map({"kawasan": "forest area", "apl": "APL", "other": "water or undefined"}))
    order = [f"{a}, {b}" for a in ("Concession", "No concession") for b in ("forest area", "APL", "water or undefined")]
    h, r = class_table(cfa, "cls", {}, order)
    annex.append(("Concessions and forest area", md_table("Land, burned area and hotspots by concession and forest area, all land. The last column compares VIIRS hotspots of 2026 with the mean of 2015 to 2025 over the same months. Source: this analysis.", h, r)))
    pp = basis(T["t_concession_x_forest"], "peat").assign(cls=lambda d: np.where(d["concession_any"], "Concession", "No concession") + ", " + d["forest_group"].map({"kawasan": "forest area", "apl": "APL", "other": "water or undefined"}))
    h, r = class_table(pp, "cls", {}, order)
    annex.append(("Peat", md_table("Peat, burned peat and hotspots on peat by concession and forest area; shares are of the peat. Source: this analysis.", h, r)))
    C["06_national"] = f"""# 6 Concessions and forest area

![Land by forest area (column width) and concession (height), coloured by VIIRS hotspots of 2026 per 100 km², for all land and for peat. Source: this analysis.]({figs['mosaic']})

On all land, 2026 hotspots per 100 km² range from {cell_txt(ca, *lo_a)} to {cell_txt(ca, *hi_a)}. On peat it is higher in every combination{' than in any combination on all land' if min(cp.values()) > max(ca.values()) else ''}: from {cell_txt(cp, *lo_p)} to {cell_txt(cp, *hi_p)}.

![Burned area per year inside and outside concessions. Grey bands: years whose burned-area map is incomplete. Source: KLHK burned area, licences 2025.]({figs['burned_years']})

Table A.1 in the annex gives the values, and Table A.2 those for peat.
"""
    ct = basis(T["t_concession_type"], "all")
    h, r = class_table(ct, "concession", LIC, ["sawit", "tambang", "pphtr", "pbph", "none"])
    annex.append(("Concession types", md_table("Land, burned area and hotspots by concession type, each cell counted once (overlaps go to the first type in the order of the table), all land. Source: this analysis.", h, r)))
    lt = basis(T["t_licence_type"], "all")
    h2, r2 = class_table(lt, "licence", LIC, ["sawit", "tambang", "pphtr", "pbph", "pphkm"], total=basis(T["t_national"], "all").sum(numeric_only=True))
    annex.append((None, md_table("The same by licence type, overlapping licences counted under each type; community forest permits (PPHKM), which are not concessions, for comparison. Shares are of all land. Source: this analysis.", h2, r2)))
    tr = {x["label"]: x for x in FX["rates"] if x["group"] == "Concession type"}
    ctv = ct.set_index("concession")["viirs_2026_n"]
    C["07_types"] = f"""# 7 Concession types

![VIIRS hotspots of 2026 by concession type (inner ring) and the forest area function inside each type (outer ring). Source: this analysis.]({figs['sunburst']})

Most 2026 hotspots lie outside any concession ({100 * ctv.get('none', 0) / ctv.sum():.0f}%). Of those inside one, most are in forest concessions (PBPH, {100 * ctv.get('pbph', 0) / ctv.sum():.0f}% of all hotspots) and oil palm ({100 * ctv.get('sawit', 0) / ctv.sum():.0f}%).

![Land by concession type and forest area function (box size), coloured by VIIRS hotspots of 2026 per 100 km². Source: this analysis.]({figs['treemap']})

By density the order changes: plantation forest licences (PPHTR) had {tr['Plantation forest (PPHTR)']['rate']:.0f} hotspots per 100 km² and oil palm {tr['Oil palm']['rate']:.0f}, against {tr['Forest concession (PBPH)']['rate']:.0f} in forest concessions, {tr['Mining']['rate']:.0f} in mining licences and {tr['No concession']['rate']:.0f} outside concessions. Tables A.3 and B.4 give the values.
"""
    ff = basis(T["t_forest_function"], "all")
    h, r = class_table(ff, "kawasan", KWS, ["cons", "hl", "prod", "hpk", "apl", "other", "none"])
    annex.append(("Forest area function", md_table("Land, burned area and hotspots by forest area function, all land. Source: this analysis.", h, r)))
    ffc = ff[ff["concession_any"]]
    h2, r2 = class_table(ffc, "kawasan", KWS, ["cons", "hl", "prod", "hpk", "apl", "other"])
    annex.append((None, md_table("Forest area function of the land inside concessions; shares are of the concession land. Source: this analysis.", h2, r2)))
    cf = basis(T["t_concession_x_forest"], "all")
    bsum = past_sum(cf).sum()
    b_kaw_nc = past_sum(cf[(~cf["concession_any"]) & (cf["forest_group"] == "kawasan")]).sum()
    b_apl_nc = past_sum(cf[(~cf["concession_any"]) & (cf["forest_group"] == "apl")]).sum()
    fr = {x["label"]: x["rate"] for x in FX["rates"] if x["group"] == "Forest area function"}
    C["08_forest"] = f"""# 8 Forest area function

![Burned area 2015 to 2025 (sum of the yearly areas, so land that burned twice counts twice) flowing from forest area function to concession type to peat. Source: KLHK burned area, licences 2025, forest area 2023, KLH peat (PPEG 2026).]({figs['alluvial']})

Of the area burned in 2015 to 2025, {100 * b_kaw_nc / bsum:.0f}% lay in the forest area outside any concession and {100 * b_apl_nc / bsum:.0f}% in other land use (APL) outside any concession. Among forest functions, convertible production forest (HPK) had the densest 2026 hotspots ({fr['Convertible production']:.0f} per 100 km²) and protection forest the sparsest ({fr['Protection forest']:.0f}). Tables A.5 and B.6 give the values.
"""
    dmc = T["t_dmpg_comparable"].assign(cls=lambda d: np.where(d["dmpg"], "DMPG village", "Other peat") + np.where(d["concession_any"], ", concession", ", no concession"))
    h, r = class_table(dmc, "cls", {}, ["DMPG village, no concession", "DMPG village, concession", "Other peat, no concession", "Other peat, concession"])
    annex.append(("DMPG villages", md_table("Peat in DMPG villages and other peat, provinces with DMPG villages; shares are of that peat. Source: this analysis.", h, r)))
    q = N.get("q03")
    qtext = (f"The project's investigation of the 2026 season compared the rise in hotspots on DMPG village land with the rise on land outside it within the same KHG and land tenure class. The ratio of the two rises was {q[1]:.2f} (95% interval {q[2]:.2f} to {q[3]:.2f}, {q[4]} KHG), so that test was {q[0]}: it neither shows nor rules out a smaller rise in DMPG villages."
             if q else "")
    C["09_dmpg"] = f"""# 9 DMPG villages

DMPG villages cover {mha(N['dmpg_area'])}, {P(N['dmpg_area'] / N['land_ha'])} of the land, and hold {P(N['dmpg_burned_share'])} of the burned area of 2015 to 2025 and {FX['classes']['dmpg']['viirs26_pct']:.0f}% of the 2026 VIIRS hotspots. The programme chose villages on fire-prone peat, so the comparison below keeps to peat in the {N['dmpgc_prov']} provinces that hold DMPG villages.

![VIIRS hotspots of 2026 per 100 km² of peat in DMPG villages and on other peat, by province (provinces with at least 100 km² of peat on each side). Source: NASA FIRMS VIIRS S-NPP, SiTMAT DMPG villages, KLH peat (PPEG 2026).]({figs['dmpg']})

On this comparable land, {P(N['dmpgc_in_ever'])} of the DMPG village peat burned at least once in 2015 to 2026, against {P(N['dmpgc_out_ever'])} of other peat. VIIRS hotspots of 2026 were {N['dmpgc_in_ratio']:.1f} times the 2015 to 2025 mean in DMPG villages and {N['dmpgc_out_ratio']:.1f} times elsewhere. {qtext} Table A.7 gives the values.
"""
    # repeated burns: times burned in the burn years, by concession x forest group and DMPG (t_times_burned)
    tb = T["t_times_burned"]
    tb = tb[tb["basis"] == "all"].copy()
    HC = ["unburned_ha", "burned_1x_ha", "burned_2x_ha", "burned_3x_ha", "burned_4plus_ha"]
    tb["ever"] = tb[HC[1:]].sum(axis=1)
    tb["rep"] = tb[HC[2:]].sum(axis=1)
    tb["land"] = tb[HC].sum(axis=1)
    tot = tb[["land", "ever", "rep"] + HC].sum()
    cls_ = tb.assign(cls=np.where(tb["concession_any"], "Concession", "No concession") + ", " + tb["forest_group"].map({"kawasan": "forest area", "apl": "APL", "other": "water or undefined"}))
    cg = cls_.groupby("cls")[["land", "ever", "rep"] + HC].sum()
    dg = tb.groupby("dmpg")[["land", "ever", "rep"] + HC].sum()
    ccon = tb[tb["concession_any"]][["land", "ever", "rep"]].sum()
    rrow = []
    for lab, r_ in [(k, cg.loc[k]) for k in order if k in cg.index and "water" not in k] + [("DMPG villages", dg.loc[True]), ("Other villages", dg.loc[False]), ("All land", tot)]:
        rrow.append([lab, kha(r_["land"]), f"{100 * r_['ever'] / r_['land']:.1f}", kha(r_["burned_1x_ha"]), kha(r_["burned_2x_ha"]), kha(r_["burned_3x_ha"]),
                     kha(r_["burned_4plus_ha"]), f"{100 * r_['rep'] / r_['ever']:.0f}" if r_["ever"] else "-", pc(r_["rep"], tot["rep"]) if lab != "All land" else "100%"])
    annex_rep = md_table("Land burned once, twice, three and four or more times in the burn years 2015 to 2026, by concession and forest area and by DMPG village, all land; areas in thousand ha. A cell that burned in two different years counts as burned twice. Water and undefined land (0.8 million ha) is left out of the rows and kept in the total. Source: this analysis.",
                         ["Class", "Land", "Ever burned (%)", "Once", "Twice", "3 times", "4 or more", "Burned again (% of burned)", "Share of land burned 2+ times"], rrow)
    k_nc = cg.loc["No concession, forest area"]; a_nc = cg.loc["No concession, APL"]
    k_c = cg.loc["Concession, forest area"]; a_c = cg.loc["Concession, APL"]
    dmy, dmn = dg.loc[True], dg.loc[False]
    C["09b_repeat"] = f"""# 10 Repeatedly burned land

Of the {mha(tot['land'])} of land, {mha(tot['ever'])} burned at least once in 2015 to 2026 and {mha(tot['rep'])} burned in two or more different years: {mha(tot['burned_2x_ha'])} twice, {mha(tot['burned_3x_ha'])} three times and {mha(tot['burned_4plus_ha'])} four times or more. A cell counts as burned twice when the burned-area maps of two different years cover it. The maps of 2024 and 2026 are incomplete (chapter 5), so these counts are lower bounds.

![Left: share of each class burned once, twice, three times and four or more times in 2015 to 2026. Right: each class's share of all land burned twice or more (bar) against its share of the land (tick). Source: KLHK burned area, licences 2025, forest area 2023, SiTMAT DMPG villages.]({figs['repeat']})

Most repeatedly burned land lies outside concessions: {P(k_nc['rep'] / tot['rep'])} in the forest area and {P(a_nc['rep'] / tot['rep'])} in other land use (APL) without a licence. Concessions hold {P(ccon['land'] / tot['land'])} of the land, {P(ccon['ever'] / tot['ever'])} of the land ever burned and {P(ccon['rep'] / tot['rep'])} of the land burned twice or more. Inside concessions, burned land burned again less often: {100 * k_c['rep'] / k_c['ever']:.0f}% of the ever-burned land in the forest area and {100 * a_c['rep'] / a_c['ever']:.0f}% in APL, against {100 * k_nc['rep'] / k_nc['ever']:.0f}% and {100 * a_nc['rep'] / a_nc['ever']:.0f}% outside them.

DMPG villages cover {P(dmy['land'] / tot['land'])} of the land and hold {P(dmy['ever'] / tot['ever'])} of the land ever burned and {P(dmy['rep'] / tot['rep'])} of the land burned twice or more. {100 * dmy['ever'] / dmy['land']:.1f}% of their land burned at least once, against {100 * dmn['ever'] / dmn['land']:.1f}% elsewhere; the programme chose villages on fire-prone peat (chapter 9). Within burned land the share that burned again is about the same in and outside DMPG villages ({100 * dmy['rep'] / dmy['ever']:.0f}% and {100 * dmn['rep'] / dmn['ever']:.0f}%). Table A.11 gives the values.
"""
    isl = basis(T["t_island"], "all")
    h, r = class_table(isl, "island", {k: k.replace("Pulau ", "") for k in isl["island"]})
    annex.append(("Islands and provinces", md_table("Land, burned area and hotspots by island. Source: this analysis.", h, r)))
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
    pr_head = ["Province", "Island", "Land (thousand ha)", "Burned 2015 to 2025 (thousand ha)", "Burned in concessions (%)", "Burned in forest area (%)",
               "VIIRS hotspots 2026", "Hotspots in concessions (%)", "Hotspots in forest area (%)", "Hotspots per 100 km²"]
    annex.append((None, md_table("Land, burned area and hotspots by province, ordered by VIIRS hotspots of 2026. Source: this analysis.", pr_head, prow)))
    kt = T["t_khg"]
    kt = kt[kt["basis"] == "all"].groupby("khg_id").sum(numeric_only=True)
    names = pd.read_csv(WORKSPACE / "re-peat" / "sites" / "khg_registry.csv")
    nm = dict(zip(names["khg_code"], names["name"]))
    kc = T["t_khg"][(T["t_khg"]["basis"] == "all") & T["t_khg"]["concession_any"]].groupby("khg_id")["viirs_2026_n"].sum()
    top = kt.sort_values("viirs_2026_n", ascending=False).head(30)
    krow = [[str(nm.get(k, k)).removeprefix("KHG "), kha(r_["area_ha"]), kha(past_sum(r_.to_frame().T).iloc[0]), n0(r_["viirs_2026_n"]), pc(kc.get(k, 0), r_["viirs_2026_n"]),
             n1(rate(r_["viirs_2026_n"], r_["area_ha"]))] for k, r_ in top.iterrows()]
    annex.append((None, md_table("The 30 KHG with the most VIIRS hotspots in 2026. Source: this analysis.", ["KHG", "Land (thousand ha)", "Burned 2015 to 2025 (thousand ha)", "VIIRS hotspots 2026", "In concessions (%)", "Hotspots per 100 km²"], krow)))
    yr_by = FX["viirs_by_year"]
    big = sorted(yr_by, key=lambda y: yr_by[y], reverse=True)[:3]
    C["10_regions"] = f"""# 11 Islands and provinces

![VIIRS hotspots per 100 km² of land by province and year, 1 January to {vlast} in every year; provinces grouped by island, 2026 outlined. Source: NASA FIRMS VIIRS S-NPP, village boundaries 2023.]({figs['heatmap']})

The years with the most hotspots over these months were {', '.join(str(y) for y in big)}. In 2026 the highest rates, in hotspots per 100 km², were in {', '.join(f"{p['province']} ({p['rate']:.0f})" for p in sorted(FX['provinces'], key=lambda p: -p['rate'])[:4])}.

![KHG by land area and VIIRS hotspots of 2026 per 100 km² (both on log scales); bubble size: number of hotspots; colour: share of them inside concessions; dashed line: all land. Source: this analysis.]({figs['khg_bubbles']})

Tables A.8 to B.10 give the values by island, province and KHG.
"""
    C["11_peat"] = f"""# 12 Peat

Peat is KLH's peat land map of the integrated thematic analysis for peat ecosystem restoration (April 2026), the map KLH's restoration targets are set on. A cell counts as peat when its centre lies in a peat polygon. The right panel of Figure 6.1 shows peat by concession and forest area, and Table A.2 gives the values.
"""
    A_ = N["pr_actors"]
    lic_share = (A_[0]["ha"] + A_[1]["ha"]) / N["pr_ha"]
    C["11b_priority"] = f"""# 13 The KLH priority area

KLH has set a restoration target of about 3.3 million ha in 337 priority KHG, chosen on the peat ecosystem damage status (SKEG), in particular burned and canal-affected land. In KLH's integrated thematic analysis for peat ecosystem restoration (PPEG, April 2026), peat with SKEG 2024 damage of any class covers {mha(N['pr_ha'])}. This report takes that peat as the priority area. A KHG is a priority KHG when it lies in one of the 2,004 target villages of the Bluebook 2026 ({N['pr_khg_vil']} KHG) or holds damaged peat ({N['pr_khg_skeg_only']} more): {N['pr_khg']} KHG. The 337 KHG of the target are not listed in the sources, so this list is a reconstruction.

![The priority KHG and the damaged peat by attribute: the reason each KHG is listed, the SKEG damage class, whether the peat lies in a target village, on a peat dome and on peat 3 m or deeper. Source: KLH PPEG integrated analysis, Bluebook 2026 target villages.]({figs['prio_parts']})

{N['pr_khg_both']} KHG meet both conditions; {N['pr_khg_vil_only']} lie in target villages without damaged peat, and {N['pr_khg_skeg_only']} hold damaged peat outside the target villages. Most damage is light ({P(N['pr_ringan'] / N['pr_ha'])}); {P(N['pr_sedang'] / N['pr_ha'])} is moderate and {P(N['pr_berat'] / N['pr_ha'])} heavy. The other {P((N['pr_ha'] - N['pr_ringan'] - N['pr_sedang'] - N['pr_berat'] - N['pr_sangat_berat']) / N['pr_ha'])} lies outside any KHG, where KLH's file codes the peat as damaged but gives no damage class. {P(N['pr_in_vil'] / N['pr_ha'])} of the priority area lies in the target villages. {mha(N['pr_dome'])} ({P(N['pr_dome'] / N['pr_ha'])}) lies on peat domes, the ombrogenous part, and {mha(N['pr_thick'])} ({P(N['pr_thick'] / N['pr_ha'])}) on peat 3 m or deeper. Both come from KLH's landform and thickness classes, which are blank in places; Pulau Bengkalis, for one, has no dome in the landform field.

![The 20 KHG with the most damaged peat, on a peat dome and elsewhere. Source: KLH PPEG integrated analysis.]({figs['prio_khg']})

The priority area is concentrated: {N['pr_half_khg']} KHG hold half of it. The largest are {', '.join(f"{n} ({h / 1e3:,.0f} thousand ha)" for n, h in N['pr_top3'])}. Table A.12 lists the 30 KHG with the most damaged peat.
"""
    C["11c_actors"] = f"""# 14 Who covers the priority area

The PPEG analysis assigns every part of the priority area to one actor: licence holders inside their licences, licence holders together with communities in the 5 km buffer around licences, the Ministry of Forestry in the forest area outside licences, and KLH/BPLH in other land use (APL) outside licences. It also codes what the land needs: rewetting (R1) where it is canal-affected, revegetation (R2) where it burned, and livelihood revitalisation (R3) everywhere. The assignment says who acts. It does not say who caused the damage.

![Damaged peat by actor, split into forest area and APL (left), and the share of each actor's area that is canal-affected, burned and near primary or secondary canals (right). Source: KLH PPEG integrated analysis.]({figs['actors']})

Licence holders cover {P(lic_share)} of the priority area: {mha(A_[0]['ha'])} inside licences and {mha(A_[1]['ha'])} in the buffer. The Ministry of Forestry covers {mha(A_[2]['ha'])} and KLH/BPLH {mha(A_[3]['ha'])}. Nearly all of the priority area is canal-affected ({mha(N['pr_r1'])}), so rewetting is needed almost everywhere; {mha(N['pr_r2'])} burned. Land assigned to the Ministry of Forestry burned most often ({100 * A_[2]['r2_ha'] / A_[2]['ha']:.0f}% of it, against {100 * A_[0]['r2_ha'] / A_[0]['ha']:.0f}% inside licences).

{N['pr_prov'][0][0]} holds {P(N['pr_prov'][0][1] / N['pr_ha'])} of the priority area, {P(N['pr_prov'][0][2] / N['pr_prov'][0][1])} of it assigned to licence holders. In {N['pr_prov'][1][0]} the Ministry of Forestry has the largest part. Table A.13 gives the values by province.

![Damaged peat by province and actor, the twelve provinces with the most. Source: KLH PPEG integrated analysis.]({figs['actor_prov']})
"""
    C["11d_roles"] = f"""# 15 Roles

The terms of reference of the focus group discussion of 2 November 2026 set out what KLH asks of each ministry; the discussion notes add the roles of BPGM and Bappenas. Table 15.1 sets these roles beside the part of the priority area each covers.

Table: Roles as stated for the focus group discussion and the part of the priority area each covers. Source: FGD terms of reference (KLH/BPLH, letter B.70/E/PKL.4.5/10/2026, agenda item 9), FGD notes of 2 November 2026, KLH PPEG integrated analysis.

| Institution | Role | Part of the priority area |
|---|---|---|
| Ministry of Public Works | Technical support, field implementation and coordination of canal blocks on primary and secondary canals | {mha(N['pr_ps'])} in the zone affected by primary or secondary canals; {N['pr_canal']['primary']:,.0f} km of primary and {N['pr_canal']['secondary']:,.0f} km of secondary canals in the priority KHG |
| Ministry of Forestry | Technical support, water management and rewetting infrastructure in the forest area, with and without licences | {mha(A_[2]['ha'])} outside licences; {mha(N['pr_forest'])} in the forest area in all, {mha(N['pr_forest_lic'])} of it inside licences |
| KLH/BPLH | Sets the priority area and the PPEG analysis; rewetting in APL outside licences | {mha(A_[3]['ha'])} |
| Licence holders | Water management inside their licences; water sharing with the communities around them | {mha(A_[0]['ha'])} inside licences, {mha(A_[1]['ha'])} in the buffer |
| BPGM | Aligns peat targets and priorities; coordinates the ministries without replacing them | {N['pr_khg']} priority KHG |
| Bappenas | Direction of support and budget for peat restoration; planning and financing | {mha(N['pr_r1'])} to rewet, {mha(N['pr_r2'])} to revegetate |
| Ministry of Finance | No role stated in the FGD documents | |

The canal lengths come from the national canal layer, which is drawn from OpenStreetMap; {N['pr_canal_blank']} priority KHG have no canal in it, so the lengths are lower bounds. An indicative investment envelope needs the number of canal blocks and wells per KHG. It follows from the prioritisation of the KHG within the priority area.
"""
    C["12_limits"] = f"""# 16 Limitations

- The burned-area maps of 2024 and 2026 are incomplete as delivered (chapter 5), and the method used to make the maps is not documented with them.
- The licence layer of 2025 and the forest area map of 2023 are matched to burns since 2015. Land may have been licensed or reclassified after it burned.
- The licence layer holds the licences it was given. Unlicensed plantations and other managed land count as "no concession".
- Hotspots and burned area inside a licence or a forest area class are a spatial overlap. They do not show the cause of a fire or who is responsible.
- MODIS and VIIRS count fires differently and are never added or compared in absolute numbers. The MODIS file joins two sources at 15 September 2026; over the 15 days where both exist the NASA source has 4.3% more detections.
- The static-source flag misses about a third of the static detections and wrongly flags about one in eight of those it flags (chapter 4).
- The priority KHG are reconstructed from KLH's PPEG analysis and the Bluebook target villages; the 337 KHG of KLH's target are not listed in the sources. In Papua, 2.5 million ha inside KHG carry no peat, damage or thickness class in the PPEG analysis. Outside the KHG, {mha(N['pr_ha'] - N['pr_ringan'] - N['pr_sedang'] - N['pr_berat'] - N['pr_sangat_berat'])} of peat is coded damaged without a damage class; it is counted in the priority area.
- The actor of each part of the priority area is KLH's assignment in the PPEG analysis, not a finding of this report.
- A cell or hotspot takes the class at its centre or position. A MODIS pixel is about 1 km across, so a hotspot near a boundary may come from the neighbouring class.
"""
    annex.append(("Repeatedly burned land", annex_rep))
    pk = pd.read_csv(SRC.parent / "ppeg" / "ppeg_khg.csv")
    t30 = pk[pk["has_skeg_damage"]].nlargest(30, "priority_ha")
    prow_ = [[n.removeprefix("KHG "), p_.split(",")[0] + ("..." if "," in p_ else ""), kha(h), pc(dm, h), pc(t3, h), pc(co + bu, h), "yes" if v else "no"]
             for n, p_, h, dm, t3, co, bu, v in zip(t30["khg_name"], t30["provinces"], t30["priority_ha"], t30["priority_dome_ha"], t30["priority_thick3m_ha"],
                                                   t30["priority_company_ha"], t30["priority_company_buffer_ha"], t30["in_target_villages"])]
    annex.append(("KLH priority area", md_table("The 30 KHG with the most SKEG 2024 damaged peat; damaged peat in thousand ha. Source: KLH PPEG integrated analysis, Bluebook 2026 target villages.",
                                              ["KHG", "Province", "Damaged peat", "On a peat dome", "On peat 3 m or deeper", "Licence holders and buffer", "In target villages"], prow_)))
    rp = pd.read_csv(WORKSPACE / "re-peat" / "reports" / "ppeg_roles" / "roles_province.csv", index_col=0)
    rp = rp[rp["total"] >= 1000]
    arow = [[p_, kha(r["Intervensi Perusahaan"]), kha(r["Kolaborasi Perusahaan (Area Buffer)"]), kha(r["Intervensi Kementerian Kehutanan"]), kha(r["Intervensi KLH/BPLH"]), kha(r["total"])] for p_, r in rp.iterrows()]
    annex.append((None, md_table("SKEG 2024 damaged peat by province and actor, thousand ha; provinces with at least 1,000 ha. Source: KLH PPEG integrated analysis.",
                                 ["Province", "Licence holders", "Licence holders and communities, buffer", "Ministry of Forestry", "KLH/BPLH", "Total"], arow)))
    body = "\n".join((f"## {sec}\n\n" if sec else "") + tbl for sec, tbl in annex)
    C["13_annex"] = f"""# Annex A Tables

The values behind the charts. Areas are on the 30 m grid; hotspots are VIIRS of 2026 (1 January to {vlast}), medium and high confidence, likely static sources left out; burned area is the sum of the yearly areas 2015 to 2025.

{body}
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
        lines.append("- KLH (2026). Analisis integrasi tematik pemulihan ekosistem gambut (PPEG) Indonesia, April 2026. GeoPackage delivered to the project.")
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
    PR.TITLE = "2026 Fire: National Breakdown"
    PR.SUBTITLE = "Burned area, hotspots and repeated burns by concession, forest area and DMPG village; the KLH priority area and roles. Indonesia, 2015 to 2026"
    b = PR.Builder()
    b.front()
    for name in sorted(C):
        b.markdown(C[name])
    drop_blank_before_chapters(b.doc)
    b.doc.save(a.out)
    print(f"wrote {a.out}; pending: {b.pending}")


if __name__ == "__main__":
    main()
