"""Facts and figures of the national summary of burned area and hotspots by land status, shared by the Word report
(re-peat/tools/fire_landstatus_report.py) and the slide deck (_slides/build_fire.js), so both carry the same numbers.

    .venv/Scripts/python.exe re-peat/tools/fire_landstatus_figs.py [--style report|slides|both]

Reads <REPEAT_WORK>/national_profile/fire_landstatus/ (area.parquet, hot.parquet, layers/summary.gpkg). Writes
  re-peat/reports/fire_landstatus/facts.json and _slides/build/fire_facts.json    every number the text and slides quote
  re-peat/reports/fire_landstatus/charts/figdata.json                              the series every chart draws
  re-peat/reports/fire_landstatus/figures/fig_*.png                                 report style (Source Sans 3)
  _slides/img/fire_*.png                                                            slide style (Plus Jakarta Sans)
The charts are drawn with D3 (fire_charts/charts.js) in headless Chrome (fire_charts/render.mjs, needs node); the page
re-peat/reports/fire_landstatus/charts/charts_<style>.html shows them all, and svg_<style>/ holds each as SVG.
One filter throughout: land inside the 2023 village boundaries; hotspots of medium and high confidence; likely static sources
(gas flares, volcanoes) left out; VIIRS years compared over the same window, 1 January to the last 2026 date. 2026 is read
from VIIRS (375 m, a single sensor since 2012); MODIS, the series KLH reports, is given next to it. Burned area is taken over
2015 to 2025, because the 2026 (and 2024) burned-area maps are incomplete as delivered. Colours: the validated categorical
palette of the dashboard; ramps validated as ordinal scales.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
SRC = Path(os.environ.get("REPEAT_WORK", WORKSPACE / "re-peat" / "reports")) / "national_profile" / "fire_landstatus"
REPORT_OUT = WORKSPACE / "re-peat" / "reports" / "fire_landstatus"
SLIDES = WORKSPACE / "_slides"
PAST = list(range(2015, 2026))
NOW = 2026
CONC = 1 | 2 | 4 | 8            # licence bits that are concessions (PPHKM, 16, is not)

# palette (dashboard / dataviz reference palette, light mode)
INK, INK2, MUTED, GRID, BASE, GREY = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#c3c2b7"
ORANGE, BLUE, GREEN, MAGENTA, VIOLET, AQUA, RED, YELLOW = "#eb6834", "#2a78d6", "#008300", "#e87ba4", "#6250d6", "#1baf7a", "#e34948", "#eda100"
SEQ = ["#fde7dc", "#f9c3a6", "#f3925f", "#d9592a", "#a33a12"]      # one-hue orange ramp, light to dark (rates)
CLASSES = [("Concessions", "conc", ORANGE), ("Forest area", "kawasan", GREEN), ("DMPG villages", "dmpg", MAGENTA), ("Peat", "peat", VIOLET)]


# --- data -----------------------------------------------------------------------------------------------------------------
def load():
    a = pd.read_parquet(SRC / "area.parquet")
    h = pd.read_parquet(SRC / "hot.parquet")
    h = h[h["conf"].isin(["medium", "high"])].copy()
    meta = json.loads((SRC / "meta.json").read_text(encoding="utf-8"))
    for d in (a, h):
        d["conc"] = (d["lic_bits"] & CONC) > 0
        d["forest_class"] = d["kawasan"]                 # cons, hl, prod, hpk, apl, other, none
        d["kws_in"] = d["forest_group"] == "kawasan"
        d["peat_"] = d["peat"] == 1
    a["burned_past"] = a[[f"burned_{y}_ha" for y in PAST]].sum(axis=1)
    return a, h, meta


def viirs(h, year=NOW, static=False):
    v = h[(h["source"] == "viirs") & h["ytd"]]
    if not static:
        v = v[~v["static"]]
    return v if year is None else v[v["year"] == year]


def flag(df, key):
    return df[{"peat": "peat_", "kawasan": "kws_in"}.get(key, key)]


def facts(a, h, meta):
    F = {"window_end": meta["viirs_last"], "modis_last": meta["modis_last"]}
    v26 = viirs(h)
    F["land_mha"] = a["area_ha"].sum() / 1e6
    F["viirs26"] = int(v26["n"].sum())
    F["viirs26_with_static"] = int(viirs(h, static=True)["n"].sum())
    F["viirs26_high"] = int(v26.loc[v26["conf"] == "high", "n"].sum())
    F["modis26"] = int(h.loc[(h["source"] == "modis") & ~h["static"], "n"].sum())
    F["modis26_with_static"] = int(h.loc[h["source"] == "modis", "n"].sum())
    by_year = viirs(h, None).groupby("year")["n"].sum()
    F["viirs_by_year"] = {int(k): int(v) for k, v in by_year.items()}
    F["viirs_mean_past"] = float(by_year.reindex(PAST).mean())
    F["viirs26_ratio"] = F["viirs26"] / F["viirs_mean_past"]
    F["viirs_max_year"] = int(by_year.drop(NOW).idxmax())
    F["viirs_rank_since_2012"] = int((by_year > by_year[NOW]).sum()) + 1
    F["burned_past_mha"] = a["burned_past"].sum() / 1e6
    F["burned_by_year_mha"] = {y: a[f"burned_{y}_ha"].sum() / 1e6 for y in PAST + [NOW]}
    F["rate26"] = F["viirs26"] / a["area_ha"].sum() * 1e4
    F["classes"] = {}
    for name, key, _ in CLASSES:
        ia, ih = flag(a, key), flag(v26, key)
        F["classes"][key] = {
            "name": name, "land_mha": a.loc[ia, "area_ha"].sum() / 1e6, "land_pct": 100 * a.loc[ia, "area_ha"].sum() / a["area_ha"].sum(),
            "burned_mha": a.loc[ia, "burned_past"].sum() / 1e6, "burned_pct": 100 * a.loc[ia, "burned_past"].sum() / a["burned_past"].sum(),
            "viirs26": int(v26.loc[ih, "n"].sum()), "viirs26_pct": 100 * v26.loc[ih, "n"].sum() / F["viirs26"],
            "rate26": v26.loc[ih, "n"].sum() / a.loc[ia, "area_ha"].sum() * 1e4,
            "rate26_outside": v26.loc[~ih, "n"].sum() / a.loc[~ia, "area_ha"].sum() * 1e4}
    vs = viirs(h, static=True)                      # sensitivity: shares with the likely static sources kept
    F["static_share_shift_max"] = max(abs(100 * vs.loc[flag(vs, key), "n"].sum() / vs["n"].sum() - F["classes"][key]["viirs26_pct"]) for _, key, _ in CLASSES)
    m = viirs(h, None)
    mon = m.groupby(["year", "month"])["n"].sum().unstack(fill_value=0)
    F["month26"] = {int(k): int(v) for k, v in mon.loc[NOW].items()}
    F["month_mean_past"] = {int(k): float(v) for k, v in mon.loc[PAST].mean().items()}
    F["peak_month"] = int(mon.loc[NOW].idxmax())
    # provinces, VIIRS 2026
    pr = a.groupby("province")["area_ha"].sum()
    pv = v26.groupby("province")["n"].sum()
    pc = v26[v26["conc"]].groupby("province")["n"].sum()
    P = pd.DataFrame({"area_ha": pr, "viirs26": pv, "conc": pc}).fillna(0)
    P = P[~P.index.str.startswith("Outside")]
    P["rate"] = P["viirs26"] / P["area_ha"] * 1e4
    P["conc_pct"] = 100 * P["conc"] / P["viirs26"].where(P["viirs26"] > 0)
    P = P.sort_values("viirs26", ascending=False)
    F["provinces"] = [{"province": k, "viirs26": int(r.viirs26), "rate": float(r.rate), "conc_pct": None if pd.isna(r.conc_pct) else float(r.conc_pct)} for k, r in P.iterrows()]
    F["top5_share"] = float(P["viirs26"].head(5).sum() / P["viirs26"].sum() * 100)
    F["completeness_ha_per_hotspot"] = {y: (a[f"burned_{y}_ha"].sum() / F["viirs_by_year"][y]) for y in PAST + [NOW] if F["viirs_by_year"].get(y)}
    # rates per class (2026 VIIRS per 100 km2)
    F["rates"] = []
    rows = [("Concession type", "concession", k, lab) for k, lab in
            {"sawit": "Oil palm", "pphtr": "Plantation forest (PPHTR)", "tambang": "Mining", "pbph": "Forest concession (PBPH)", "none": "No concession"}.items()]
    rows += [("Forest area function", "forest_class", k, lab) for k, lab in
             {"cons": "Conservation", "hl": "Protection forest", "prod": "Production forest", "hpk": "Convertible production", "apl": "Other land use (APL)"}.items()]
    for grp, col, k, lab in rows:
        ia, ih = a[col] == k, v26[col] == k
        ar = a.loc[ia, "area_ha"].sum()
        F["rates"].append({"group": grp, "label": lab, "rate": float(v26.loc[ih, "n"].sum() / ar * 1e4) if ar else None, "land_mha": ar / 1e6, "viirs26": int(v26.loc[ih, "n"].sum())})
    for key, lab_in, lab_out in (("dmpg", "DMPG villages", "Outside DMPG villages"), ("peat", "Peat", "Not peat or not mapped")):
        ia, ih = flag(a, key), flag(v26, key)
        for sel_a, sel_h, lab in ((ia, ih, lab_in), (~ia, ~ih, lab_out)):
            ar = a.loc[sel_a, "area_ha"].sum()
            F["rates"].append({"group": "DMPG and peat", "label": lab, "rate": float(v26.loc[sel_h, "n"].sum() / ar * 1e4), "land_mha": ar / 1e6, "viirs26": int(v26.loc[sel_h, "n"].sum())})
    # DMPG against other peat, per province holding DMPG village peat
    pa = a[a["peat_"]]
    pv = v26[v26["peat_"]]
    dprov = sorted(pa.loc[pa["dmpg"], "province"].unique())
    D = []
    for p in dprov:
        ai, ao = pa[(pa["province"] == p) & pa["dmpg"]]["area_ha"].sum(), pa[(pa["province"] == p) & ~pa["dmpg"]]["area_ha"].sum()
        hi, ho = pv[(pv["province"] == p) & pv["dmpg"]]["n"].sum(), pv[(pv["province"] == p) & ~pv["dmpg"]]["n"].sum()
        if ai >= 1e4 and ao >= 1e4:                        # at least 100 km2 of peat on each side
            D.append({"province": p, "dmpg_rate": hi / ai * 1e4, "other_rate": ho / ao * 1e4, "dmpg_km2": ai / 100})
    F["dmpg_by_province"] = sorted(D, key=lambda r: r["dmpg_rate"])
    return F


# --- chart data (drawn with D3 by fire_charts/render.mjs) ----------------------------------------------------------------
FUN_ORDER = ["cons", "hl", "prod", "hpk", "apl", "other"]


def figdata(F, a, h):
    """Every series the charts draw, as plain JSON (the same filters as the facts)."""
    v26 = viirs(h)
    vall = viirs(h, None)
    D = {"facts": F, "now": NOW, "past": [PAST[0], PAST[-1]]}
    t = vall.groupby(["year", "conc"])["n"].sum().unstack(fill_value=0)
    D["years"] = [{"year": int(y), "conc": int(r[True]), "out": int(r[False])} for y, r in t.iterrows()]
    b = pd.DataFrame({y: a.groupby("conc")[f"burned_{y}_ha"].sum() for y in PAST + [NOW]}).T
    D["burned"] = [{"year": int(y), "conc": float(r[True]), "out": float(r[False])} for y, r in b.iterrows()]
    # mosaic: forest group x concession, all land and peat
    D["mosaic"] = []
    for basis, pa, pv in (("all", a, v26), ("peat", a[a["peat_"]], v26[v26["peat_"]])):
        ga = pa.groupby(["forest_group", "conc"])["area_ha"].sum()
        gn = pv.groupby(["forest_group", "conc"])["n"].sum()
        for (g, c), ar in ga.items():
            D["mosaic"].append({"basis": basis, "group": g, "conc": bool(c), "area_ha": float(ar), "n": int(gn.get((g, c), 0))})
    # treemap and sunburst: concession type -> forest function
    fa = a.assign(fun=a["forest_class"].where(a["forest_class"].isin(FUN_ORDER), "other"))
    fv = v26.assign(fun=v26["forest_class"].where(v26["forest_class"].isin(FUN_ORDER), "other"))
    ar = fa.groupby(["concession", "fun"])["area_ha"].sum()
    nn = fv.groupby(["concession", "fun"])["n"].sum()
    D["hier"] = [{"type": k, "fun": f, "area_ha": float(v), "n": int(nn.get((k, f), 0))} for (k, f), v in ar.items()]
    # alluvial: burned area 2015-2025 (sum of yearly areas), forest group -> concession type -> peat
    d = a.assign(p=np.where(a["peat"] == 1, "peat", np.where(a["peat"] == 0, "nopeat", "unknown")))
    D["flows"] = ([{"step": 0, "s": g, "t": c, "v": float(x)} for (g, c), x in d.groupby(["forest_group", "concession"])["burned_past"].sum().items() if x > 0]
                  + [{"step": 1, "s": c, "t": p, "v": float(x)} for (c, p), x in d.groupby(["concession", "p"])["burned_past"].sum().items() if x > 0])
    # heatmap: province x year, VIIRS hotspots per 100 km2 of land over the shared window
    land = a.groupby(["island", "province"])["area_ha"].sum()
    hn = vall.groupby(["island", "province", "year"])["n"].sum()
    D["heat"] = [{"island": i, "province": p, "year": int(y), "rate": float(n / land[(i, p)] * 1e4)} for (i, p, y), n in hn.items()
                 if (i, p) in land.index and not i.startswith("Outside")]
    D["heat_land"] = [{"island": i, "province": p} for (i, p) in land.index if not i.startswith("Outside")]
    # KHG bubbles
    t = pd.read_csv(SRC / "tables" / "t_khg.csv")
    t = t[t["basis"] == "all"]
    g = t.groupby("khg_id")[["area_ha", "viirs_2026_n"]].sum()
    g["conc"] = t[t["concession_any"]].groupby("khg_id")["viirs_2026_n"].sum()
    g = g.fillna(0)
    g = g[g["viirs_2026_n"] > 0]
    reg = pd.read_csv(WORKSPACE / "re-peat" / "sites" / "khg_registry.csv")
    names = dict(zip(reg["khg_code"], reg["name"].str.replace("KHG ", "", regex=False).str.replace("Sungai ", "", regex=False)))
    D["khg"] = [{"id": k, "name": names.get(k, k), "km2": float(r["area_ha"] / 100), "n": int(r["viirs_2026_n"]),
                 "rate": float(r["viirs_2026_n"] / r["area_ha"] * 1e4), "conc_pct": float(100 * r["conc"] / r["viirs_2026_n"])} for k, r in g.iterrows()]
    # times burned (burn years 2015-2026) by concession x forest group and by DMPG village, all land
    tb = pd.read_csv(SRC / "tables" / "t_times_burned.csv")
    tb = tb[tb["basis"] == "all"]
    hc = ["unburned_ha", "burned_1x_ha", "burned_2x_ha", "burned_3x_ha", "burned_4plus_ha"]
    D["times"] = []
    for (c, g), r in tb[tb["forest_group"] != "other"].groupby(["concession_any", "forest_group"])[hc].sum().iterrows():
        D["times"].append({"set": "conc", "conc": bool(c), "group": g, "ha": [float(v) for v in r]})
    for d, r in tb.groupby("dmpg")[hc].sum().iterrows():
        D["times"].append({"set": "dmpg", "dmpg": bool(d), "ha": [float(v) for v in r]})
    D["times_total"] = [float(v) for v in tb[hc].sum()]
    # KLH priority area (repeat-national-ppeg) and who covers it (re-peat/tools/ppeg_roles.py)
    pdir, rdir = SRC.parent / "ppeg", WORKSPACE / "re-peat" / "reports" / "ppeg_roles"
    if (pdir / "ppeg_khg.csv").exists() and (rdir / "roles_actor.csv").exists():
        pk = pd.read_csv(pdir / "ppeg_khg.csv")
        pn = pd.read_csv(pdir / "ppeg_national.csv", index_col=0)["value"]
        both = pk["in_target_villages"] & pk["has_skeg_damage"]
        D["prio"] = {"khg_both": int(both.sum()), "khg_villages_only": int((pk["in_target_villages"] & ~pk["has_skeg_damage"]).sum()),
                     "khg_skeg_only": int((pk["has_skeg_damage"] & ~pk["in_target_villages"]).sum()),
                     "ha_in_villages": float(pn["priority_in_target_villages_ha"]), "ha": float(pn["priority_ha"]),
                     "damage": [float(pn[f"priority_{k}_ha"]) for k in ("ringan", "sedang", "berat", "sangat_berat")],
                     "dome": float(pn["priority_dome_ha"]), "thick3m": float(pn["priority_thick3m_ha"])}
        top = pk[pk["has_skeg_damage"]].nlargest(20, "priority_ha")
        D["prio_khg"] = [{"name": n.removeprefix("KHG ").replace("Sungai ", ""), "ha": float(h), "dome": float(dm), "villages": bool(v)}
                         for n, h, dm, v in zip(top["khg_name"], top["priority_ha"], top["priority_dome_ha"], top["in_target_villages"])]
        ra = pd.read_csv(rdir / "roles_actor.csv")
        D["actors"] = ra.drop(columns=["share"]).to_dict("records")
        rp = pd.read_csv(rdir / "roles_province.csv", index_col=0)
        D["actor_prov"] = [{"province": p, "v": [float(x) for x in r.drop("total")], "total": float(r["total"])} for p, r in rp.head(12).iterrows()]
    # provinces for the map: outlines simplified for drawing only (the analysis uses the full geometry)
    import geopandas as gpd
    import shapely
    pg = gpd.read_file(SRC / "layers" / "summary.gpkg", layer="province", columns=["province"])
    pg["geometry"] = shapely.set_precision(pg.geometry.simplify(0.01), 0.001)
    D["provinces_geo"] = json.loads(pg.to_json(drop_id=True))
    return D


def render(D, style):
    """Draw every chart with D3 in headless Chrome (fire_charts/render.mjs): PNG and SVG per chart."""
    import subprocess
    data = REPORT_OUT / "charts" / "figdata.json"
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_text(json.dumps(D, default=float), encoding="utf-8")
    out, prefix = (REPORT_OUT / "figures", "fig_") if style == "report" else (SLIDES / "img", "fire_")
    r = subprocess.run(["node", str(HERE / "fire_charts" / "render.mjs"), "--data", str(data), "--style", style, "--out", str(out), "--prefix", prefix],
                       capture_output=True, text=True, timeout=600)
    if r.returncode:
        raise RuntimeError(r.stderr or r.stdout)
    return {line.split("\t")[0]: Path(line.split("\t")[1]) for line in r.stdout.splitlines() if "\t" in line}


def build(style):
    a, h, meta = load()
    F = facts(a, h, meta)
    REPORT_OUT.mkdir(parents=True, exist_ok=True)
    (REPORT_OUT / "facts.json").write_text(json.dumps(F, indent=1, default=float), encoding="utf-8")
    (SLIDES / "build").mkdir(exist_ok=True)
    shutil.copyfile(REPORT_OUT / "facts.json", SLIDES / "build" / "fire_facts.json")
    D = figdata(F, a, h)
    return F, {kind: render(D, kind) for kind in (["report", "slides"] if style == "both" else [style])}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="both", choices=["report", "slides", "both"])
    F, out = build(ap.parse_args().style)
    for k, v in out.items():
        print(k, ", ".join(p.name for p in v.values()))
