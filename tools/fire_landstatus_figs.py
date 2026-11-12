"""Facts and figures of the national summary of burned area and hotspots by land status, shared by the Word report
(re-peat/tools/fire_landstatus_report.py) and the slide deck (_slides/build_fire.js), so both carry the same numbers.

    .venv/Scripts/python.exe re-peat/tools/fire_landstatus_figs.py [--style report|slides|both]

Reads <REPEAT_WORK>/national_profile/fire_landstatus/ (area.parquet, hot.parquet, layers/summary.gpkg). Writes
  re-peat/reports/fire_landstatus/facts.json and _slides/build/fire_facts.json    every number the text and slides quote
  re-peat/reports/fire_landstatus/figures/fig_*.png                                 report style (Source Sans 3)
  _slides/img/fire_*.png                                                            slide style (Plus Jakarta Sans)
One filter throughout: land inside the 2023 village boundaries; hotspots of medium and high confidence; likely static sources
(gas flares, volcanoes) left out; VIIRS years compared over the same window, 1 January to the last 2026 date. 2026 is read
from VIIRS (375 m, a single sensor since 2012); MODIS, the series KLH reports, is given next to it. Burned area is taken over
2015 to 2025, because the 2026 (and 2024) burned-area maps are incomplete as delivered. Colours: the validated categorical
palette of the dashboard, one hue against grey per comparison.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
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


# --- style ----------------------------------------------------------------------------------------------------------------
class Style:
    def __init__(self, kind):
        self.kind = kind
        if kind == "report":
            import sys
            sys.path.insert(0, str(HERE))
            import project_report_style as PS
            PS.register_matplotlib()
            self.font, self.out, self.prefix, self.w, self.fs = PS.SANS, REPORT_OUT / "figures", "fig_", 6.3, 8.5
        else:
            from matplotlib import font_manager
            for f in sorted((SLIDES / "fonts").glob("PlusJakartaSans-*.ttf")):
                font_manager.fontManager.addfont(str(f))
            self.font, self.out, self.prefix, self.w, self.fs = "Plus Jakarta Sans", SLIDES / "img", "fire_", 6.0, 10
        plt.rcParams.update({"font.family": self.font, "font.size": self.fs, "text.color": INK, "axes.edgecolor": BASE, "axes.labelcolor": INK2,
                             "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlesize": self.fs + 1, "axes.titleweight": "semibold"})
        self.out.mkdir(parents=True, exist_ok=True)

    def save(self, fig, name):
        p = self.out / f"{self.prefix}{name}.png"
        fig.savefig(p, dpi=220, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return p


def clean(ax, grid="x"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(BASE)
    if grid:
        ax.grid(axis=grid, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def fmt_n(v):
    return f"{v / 1e6:.2f} M" if v >= 1e6 else f"{v / 1e3:.0f} k" if v >= 1e4 else f"{v:,.0f}"


# --- figures --------------------------------------------------------------------------------------------------------------
def fig_shares(F, S):
    """For each class: its share of the land, of the area burned 2015-2025 and of the 2026 VIIRS hotspots (one hue against grey)."""
    rows = [("Land", "land_pct", "land_mha", lambda v: f"{v:.1f} Mha"), (f"Burned area {PAST[0]}–{PAST[-1]}", "burned_pct", "burned_mha", lambda v: f"{v:.2f} Mha"),
            (f"Hotspots {NOW}", "viirs26_pct", "viirs26", lambda v: f"{v / 1e3:.0f}k")]
    fig, axes = plt.subplots(len(CLASSES), 1, figsize=(S.w, 0.95 * len(CLASSES) + 0.5), sharex=True)
    for ax, (name, key, col) in zip(axes, CLASSES):
        c = F["classes"][key]
        for i, (lab, pk, ak, f) in enumerate(rows):
            y = len(rows) - 1 - i
            ax.barh(y, 100, color=GREY, height=0.62, alpha=0.35, lw=0)
            ax.barh(y, c[pk], color=col, height=0.62, lw=0)
            ax.text(-1.5, y, lab, ha="right", va="center", fontsize=S.fs - 0.5, color=INK2)
            ax.text(c[pk] + 1.2, y, f"{c[pk]:.0f}%", ha="left", va="center", fontsize=S.fs, color=INK, fontweight="semibold")
            ax.text(102, y, f(c[ak]), ha="left", va="center", fontsize=S.fs - 1, color=INK2)       # absolute value in its own column
        ax.set_title(name, loc="left", fontsize=S.fs + 0.5, color=INK, pad=3, x=-0.3 if S.kind == "report" else -0.33)
        ax.set_xlim(0, 100)
        ax.set_yticks([])
        ax.spines[:].set_visible(False)
        ax.tick_params(length=0)
    axes[-1].set_xticks([0, 25, 50, 75, 100])
    axes[-1].set_xticklabels(["0", "25", "50", "75", "100%"])
    fig.subplots_adjust(left=0.27, hspace=0.55)
    return S.save(fig, "shares")


def fig_months(F, S):
    """VIIRS hotspots per month: 2026 against the 2015-2025 mean and the record year."""
    fig, ax = plt.subplots(figsize=(S.w, 2.7))
    ms = sorted(F["month26"])
    mean = [F["month_mean_past"].get(m, 0) / 1e3 for m in ms]
    ax.plot(ms, mean, color=MUTED, lw=2, ls=(0, (4, 2)))
    ax.plot(ms, [F["month26"][m] / 1e3 for m in ms], color=ORANGE, lw=2.2, marker="o", ms=4.5, mfc=ORANGE, mec="white", mew=1)
    pk = F["peak_month"]
    ax.annotate(f"{NOW}: {F['month26'][pk] / 1e3:,.0f}k in {pd.Timestamp(NOW, pk, 1):%B}", (pk, F["month26"][pk] / 1e3), xytext=(-8, 4),
                textcoords="offset points", ha="right", va="bottom", fontsize=S.fs - 0.5, color=INK)
    ax.annotate(f"mean {PAST[0]}–{PAST[-1]}", (ms[-1], mean[-1]), xytext=(6, 0), textcoords="offset points", va="center", fontsize=S.fs - 1, color=INK2)
    ax.set_xticks(ms)
    ax.set_xticklabels([pd.Timestamp(2026, m, 1).strftime("%b") for m in ms])
    ax.set_ylabel("VIIRS hotspots (thousand)")
    ax.set_ylim(0)
    clean(ax, "y")
    return S.save(fig, "months_2026")


def fig_years(F, S, a, h):
    """VIIRS hotspots per year, 1 January to the 2026 end date, inside and outside concessions (2026 emphasised)."""
    v = viirs(h, None)
    t = v.groupby(["year", "conc"])["n"].sum().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(S.w, 2.6))
    for conc, col, lab in ((False, BLUE, "No concession"), (True, ORANGE, "Concessions")):
        ys = t.index.tolist()
        ax.plot(ys, t[conc] / 1e3, color=col, lw=2)
        ax.plot(ys[-1:], (t[conc] / 1e3).iloc[-1:], "o", color=col, ms=5, mec="white", mew=1)
        ax.annotate(f"{lab}", (ys[-1], t[conc].iloc[-1] / 1e3), xytext=(7, 0), textcoords="offset points", va="center", fontsize=S.fs - 0.5, color=INK)
    ax.set_xticks([y for y in t.index if y % 2 == 0])
    ax.set_ylabel(f"VIIRS hotspots, 1 Jan–{pd.Timestamp(F['window_end']):%d %b} (thousand)")
    ax.set_ylim(0)
    clean(ax, "y")
    return S.save(fig, "years")


def fig_burned(F, S, a):
    """Burned area per year inside and outside concessions; 2024 and 2026 maps incomplete (hollow markers, grey bands)."""
    t = pd.DataFrame({y: a.groupby("conc")[f"burned_{y}_ha"].sum() for y in PAST + [NOW]}).T / 1e3
    fig, ax = plt.subplots(figsize=(S.w, 2.6))
    for y in (2024, NOW):
        ax.axvspan(y - 0.45, y + 0.45, color=GRID, lw=0, zorder=0)
        ax.text(y, 1.0, "incomplete", transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=S.fs - 2, color=MUTED)
    for conc, col, lab in ((False, BLUE, "No concession"), (True, ORANGE, "Concessions")):
        ax.plot(t.index, t[conc], color=col, lw=2, label=lab)
    ax.legend(loc="upper center", frameon=False, fontsize=S.fs - 1, ncol=2)
    ax.set_xticks([y for y in t.index if y % 2 == 1])
    ax.set_ylabel("Burned area (thousand ha)")
    ax.set_ylim(0)
    clean(ax, "y")
    return S.save(fig, "burned_years")


def fig_rates(F, S):
    """VIIRS hotspots 2026 per 100 km2 by class, ranked within each group, with the national rate."""
    R = pd.DataFrame(F["rates"]).dropna(subset=["rate"])
    groups = list(dict.fromkeys(R["group"]))
    fig, ax = plt.subplots(figsize=(S.w, 0.27 * (len(R) + 2 * len(groups)) + 0.4))
    y, ticks, labels = 0, [], []
    for g in groups:
        sub = R[R["group"] == g].sort_values("rate")
        for _, r in sub.iterrows():
            ax.barh(y, r["rate"], color=ORANGE, height=0.66, lw=0)
            ax.text(r["rate"] + 0.6, y, f"{r['rate']:.0f}", va="center", fontsize=S.fs - 1, color=INK)
            ticks.append(y); labels.append(r["label"])
            y += 1
        ax.text(0, y + 0.1, g, fontsize=S.fs - 0.5, color=INK2, fontweight="semibold", va="bottom", zorder=5,
                bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"))
        y += 1.6
    ax.axvline(F["rate26"], color=INK, lw=1, ls=(0, (3, 2)))
    ax.annotate(f"Indonesia, all land: {F['rate26']:.0f}", (F["rate26"], -1.1), xytext=(4, 0), textcoords="offset points",
                fontsize=S.fs - 1, color=INK, va="center")
    ax.set_ylim(-1.7, y - 0.4)
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels, fontsize=S.fs - 0.5)
    ax.set_xlabel(f"VIIRS hotspots {NOW} per 100 km²")
    clean(ax, "x")
    return S.save(fig, "rates")


def fig_map(F, S):
    """Province choropleth of 2026 VIIRS hotspots per 100 km2 (classed, one hue). Outlines simplified in memory for drawing only."""
    import geopandas as gpd
    g = gpd.read_file(SRC / "layers" / "summary.gpkg", layer="province", columns=["province"])
    g["geometry"] = g.geometry.simplify(0.02)
    r = pd.DataFrame(F["provinces"]).set_index("province")["rate"]
    g["rate"] = g["province"].map(r).fillna(0)
    br = [5, 15, 40, 80]
    g["cls"] = np.digitize(g["rate"], br)
    fig, ax = plt.subplots(figsize=(S.w * 1.25, S.w * 0.5))
    for k in range(len(SEQ)):
        sub = g[g["cls"] == k]
        if len(sub):
            sub.plot(ax=ax, color=SEQ[k], edgecolor="white", linewidth=0.4)
    ax.set_axis_off()
    labs = [f"< {br[0]}"] + [f"{br[i]}–{br[i + 1]}" for i in range(len(br) - 1)] + [f"≥ {br[-1]}"]
    from matplotlib.patches import Patch
    ax.legend([Patch(color=c) for c in SEQ], labs, title=f"VIIRS hotspots {NOW}\nper 100 km²", loc="upper left", bbox_to_anchor=(1.0, 1.0), frameon=False,
              fontsize=S.fs - 1.5, title_fontsize=S.fs - 1, ncol=1, handlelength=1.2, alignment="left")
    # the four highest rates, labelled off the land with a leader line (offsets in degrees: up for Kalimantan, down elsewhere)
    for _, row in g.sort_values("rate", ascending=False).head(4).iterrows():
        c = row.geometry.representative_point()
        up = "Kalimantan" in row["province"] and "Selatan" not in row["province"]
        tx, ty = (c.x - 3, 5.5) if up else (c.x + (2 if c.x > 120 else -2), -9.5)
        ax.annotate(f"{row['province']} {row['rate']:.0f}", (c.x, c.y), xytext=(tx, ty), fontsize=S.fs - 2, color=INK, ha="center",
                    va="bottom" if up else "top", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    ax.set_ylim(-11.5, 7)
    return S.save(fig, "map_2026")


def fig_provinces(F, S, n=10):
    """The provinces with the most 2026 VIIRS hotspots, split inside and outside concessions."""
    P = pd.DataFrame(F["provinces"]).head(n).iloc[::-1]
    conc = P["viirs26"] * P["conc_pct"].fillna(0) / 100
    narrow = S.kind == "slides"                       # the slide puts it beside the map: narrower and taller, short labels
    fig, ax = plt.subplots(figsize=(4.4, 0.42 * n + 0.8) if narrow else (S.w, 0.3 * n + 0.6))
    y = np.arange(len(P))
    ax.barh(y, conc / 1e3, color=ORANGE, height=0.66, lw=0, label="In concessions")
    ax.barh(y, (P["viirs26"] - conc) / 1e3, left=conc / 1e3 + P["viirs26"].max() / 1e3 * 0.004, color=BLUE, height=0.66, lw=0, label="Outside concessions")
    for yi, tot, pcc in zip(y, P["viirs26"], P["conc_pct"]):
        ax.text(tot / 1e3 * 1.01 + 0.5, yi, f"{tot / 1e3:,.0f}k · {pcc:.0f}%" if narrow else f"{tot / 1e3:,.0f}k · {pcc:.0f}% in concessions",
                va="center", fontsize=S.fs - 1.5, color=INK2)
    ax.set_yticks(y)
    ax.set_yticklabels(P["province"], fontsize=S.fs - 0.5)
    ax.set_xlabel(f"VIIRS hotspots {NOW} (thousand)")
    ax.legend(loc="lower right", frameon=False, fontsize=S.fs - 1.5, title="% = share in concessions" if narrow else None, title_fontsize=S.fs - 2)
    ax.set_xlim(0, P["viirs26"].max() / 1e3 * (1.3 if narrow else 1.45))
    clean(ax, "x")
    return S.save(fig, "provinces")


def fig_dmpg(F, S):
    """Dumbbell: 2026 VIIRS hotspots per 100 km2 of peat in DMPG villages and on other peat, per province."""
    D = pd.DataFrame(F["dmpg_by_province"])
    fig, ax = plt.subplots(figsize=(S.w, 0.32 * len(D) + 0.7))
    y = np.arange(len(D))
    for yi, (_, r) in zip(y, D.iterrows()):
        ax.plot([r["other_rate"], r["dmpg_rate"]], [yi, yi], color=GREY, lw=2, zorder=1)
    ax.scatter(D["other_rate"], y, s=46, color=BLUE, zorder=2, label="Other peat", edgecolor="white", linewidth=1)
    ax.scatter(D["dmpg_rate"], y, s=46, color=MAGENTA, zorder=3, label="DMPG village peat", edgecolor="white", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(D["province"], fontsize=S.fs - 0.5)
    ax.set_xlabel(f"VIIRS hotspots {NOW} per 100 km² of peat")
    ax.legend(loc="lower right", frameon=False, fontsize=S.fs - 1)
    clean(ax, "x")
    return S.save(fig, "dmpg")


def build(style):
    a, h, meta = load()
    F = facts(a, h, meta)
    REPORT_OUT.mkdir(parents=True, exist_ok=True)
    (REPORT_OUT / "facts.json").write_text(json.dumps(F, indent=1, default=float), encoding="utf-8")
    (SLIDES / "build").mkdir(exist_ok=True)
    shutil.copyfile(REPORT_OUT / "facts.json", SLIDES / "build" / "fire_facts.json")
    out = {}
    for kind in (["report", "slides"] if style == "both" else [style]):
        S = Style(kind)
        out[kind] = {"shares": fig_shares(F, S), "months": fig_months(F, S), "years": fig_years(F, S, a, h), "burned": fig_burned(F, S, a),
                     "rates": fig_rates(F, S), "map": fig_map(F, S), "provinces": fig_provinces(F, S), "dmpg": fig_dmpg(F, S)}
    return F, out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="both", choices=["report", "slides", "both"])
    F, out = build(ap.parse_args().style)
    for k, v in out.items():
        print(k, ", ".join(p.name for p in v.values()))
