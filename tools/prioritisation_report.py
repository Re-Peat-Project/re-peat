"""Build the Word report "National prioritisation of peat hydrological units (KHG) for rewetting" (draft for discussion) and
its annex of KHG profiles, from the outputs of the national prioritisation.

    .venv/Scripts/python.exe re-peat/tools/prioritisation_report.py [--out DIR] [--no-annex] [--annex-only]
    powershell -File re-peat/tools/docx_render.ps1 <DIR>/RE-PEAT_KHG_prioritisation.docx        # fields and fonts

Reads (all produced by the project; nothing in the text is typed by hand):
  re-peat/reports/national_profile/final/            final_khg.csv, final_meta.json, final_validation.json, final_types.csv, final_gaps.csv
  re-peat/reports/national_profile/tenure_complexity/tenure_complexity.csv, ppeg/ppeg_khg.csv, operational/profile.csv
  re-peat/sites/layer_register.csv, khg_klh_priority.csv, khg_availability.csv; reports/investigations/ppeg_verification.csv
  _data/derived/khg_klh_priority.gpkg (KHG polygons), reports/national_profile/ppeg/ppeg_layers.gpkg (SKEG damage per KHG),
  _data/landstatus/ALL_Updade__IZIN_USAHA_..._2025.gpkg (licence outlines), and
  _exports/prioritisation_report/data/khg_holders.csv (tools/prioritisation_holders.py: licence holders per KHG from PPEG)
Writes, in DIR (default _exports/prioritisation_report, outside git: the annex names licence holders):
  RE-PEAT_KHG_prioritisation.docx               main report (English, with an Indonesian executive summary)
  RE-PEAT_KHG_prioritisation_annex_profiles.docx  one page per KHG of KLH's 337 work list
  chapters/*.md, sources.md, figures/*.png, profiles/*.png
Status: draft for discussion; the weights are provisional until agreed with KLH.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]
sys.path.insert(0, str(HERE))
import project_report as PR  # noqa: E402
import project_report_style as STYLE  # noqa: E402

NP = WS / "re-peat" / "reports" / "national_profile"
DATA = Path(os.environ.get("REPEAT_DATA", WS / "_data"))
HUB = WS / "re-peat"
TY = ["A", "B", "C", "D", "E"]
TYN = {"A": "Quick action", "B": "Multi-party coordination", "C": "Medium urgency", "D": "Protect and monitor", "E": "Monitor"}
TYN_ID = {"A": "Aksi cepat", "B": "Koordinasi multipihak", "C": "Urgensi sedang", "D": "Lindungi dan pantau", "E": "Pantau"}
IVO = ["rewetting and revegetation", "rewetting", "revegetation", "protect"]
IVN = {"rewetting and revegetation": "Rewet and revegetate", "rewetting": "Rewet", "revegetation": "Revegetate", "protect": "Protect"}
IVN_ID = {"rewetting and revegetation": "pembasahan dan revegetasi", "rewetting": "pembasahan", "revegetation": "revegetasi", "protect": "perlindungan"}
IVC = {"rewetting and revegetation": "#2b6f9e", "rewetting": "#5fa3cf", "revegetation": "#7aa95c", "protect": "#b9b6ab"}
TYC = {"A": "#d1495b", "B": "#7b3fa0", "C": "#e8a33d", "D": "#2f8f6b", "E": "#8d8a80"}
DIM = [("urgency", "Urgency"), ("stake", "Stake"), ("complexity", "Complexity"), ("feasibility", "Feasibility"), ("people", "People")]
SRC = {}      # number name -> source, for sources.md


def n0(x):
    return f"{x:,.0f}"


def n1(x):
    return f"{x:,.1f}"


def pc(x, nd=0):
    return f"{100 * x:.{nd}f}%"


def id_num(text):
    """Indonesian number format for the executive summary: decimal comma, thousands point."""
    return re.sub(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?![\w])",
                  lambda m: m.group(1).replace(",", ".") + ("," + m.group(2) if m.group(2) else ""), text)


def note(key, value, source):
    SRC[key] = (value, source)
    return value


# ---------------------------------------------------------------------------------------------------------------- data
def load():
    D = {}
    D["f"] = pd.read_csv(NP / "final" / "final_khg.csv")
    D["meta"] = json.loads((NP / "final" / "final_meta.json").read_text(encoding="utf-8"))
    D["val"] = json.loads((NP / "final" / "final_validation.json").read_text(encoding="utf-8"))
    D["types"] = pd.read_csv(NP / "final" / "final_types.csv")
    D["gaps"] = pd.read_csv(NP / "final" / "final_gaps.csv")
    D["iv"] = pd.read_csv(NP / "final" / "final_intervention.csv")
    D["tc"] = pd.read_csv(NP / "tenure_complexity" / "tenure_complexity.csv")
    wt = NP / "whole_khg" / "tenure_complexity" / "tenure_complexity.csv"
    if wt.exists():   # the KHG of the 337 without KLH peat: claim shares with the whole KHG as peat
        w = pd.read_csv(wt)
        w = w[w.khg_id.isin(D["f"].loc[D["f"].get("whole_khg", False) == True, "khg_code"])]
        D["tc_all"] = pd.concat([D["tc"][~D["tc"].khg_id.isin(w.khg_id)], w], ignore_index=True)
    else:
        D["tc_all"] = D["tc"]
    D["pp"] = pd.read_csv(NP / "ppeg" / "ppeg_khg.csv")
    D["pp"] = D["pp"][D["pp"].khg_code.astype(str).str.startswith("KHG.")]
    D["prof"] = pd.read_csv(NP / "operational" / "profile.csv")
    D["reg"] = pd.read_csv(HUB / "sites" / "layer_register.csv", dtype=str, keep_default_na=False)
    D["ver"] = pd.read_csv(HUB / "reports" / "investigations" / "ppeg_verification.csv")
    D["kp"] = pd.read_csv(HUB / "sites" / "khg_klh_priority.csv")
    D["av"] = pd.read_csv(HUB / "sites" / "khg_availability.csv")
    D["av"]["khg_code"] = "KHG." + D["av"]["code"].astype(str)
    hf = WS / "_exports" / "prioritisation_report" / "data" / "khg_holders.csv"
    D["hold"] = pd.read_csv(hf) if hf.exists() else pd.DataFrame(columns=["khg_code", "holder", "licence", "peat_ha", "damaged_ha"])
    f = D["f"].merge(D["tc_all"].drop(columns=["khg", "peat_km2", "points", "tenure_complexity", "tenure_complexity_rank", "c_contested", "c_holders"], errors="ignore")
                     .rename(columns={"khg_id": "khg_code"}), on="khg_code", how="left")
    act = D["pp"].set_index("khg_code")[["priority_company_ha", "priority_company_buffer_ha", "priority_mofor_ha", "priority_klh_ha",
                                          "priority_class01_ha", "priority_class02_ha", "priority_class03_ha", "peat_ha",
                                          "peat_burned_ha", "peat_canal_ha", "peat_dome_ha", "peat_thick3m_ha", "peat_protected_feg_ha"]]
    D["F"] = f.merge(act, left_on="khg_code", right_index=True, how="left")
    tdir = NP / "technical_example"
    if (tdir / f"{EXAMPLE}_points.csv").exists():       # tools/technical_example.py: the worked example of Annex C
        D["tex_pts"] = pd.read_csv(tdir / f"{EXAMPLE}_points.csv")
        D["tex_meta"] = json.loads((tdir / f"{EXAMPLE}_meta.json").read_text(encoding="utf-8"))
    return D


# ------------------------------------------------------------------------------------------------------------- figures
def setup_fig():
    STYLE.register_matplotlib()
    plt.rcParams.update({"axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#" + STYLE.MUTED,
                         "axes.labelcolor": "#" + STYLE.INK, "xtick.color": "#" + STYLE.MUTED, "ytick.color": "#" + STYLE.MUTED,
                         "font.size": 9, "axes.titlesize": 10, "savefig.dpi": 220})


def save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def fig_map(D, out):
    import geopandas as gpd
    g = gpd.read_file(DATA / "derived" / "khg_klh_priority.gpkg", layer="khg")[["khg_code", "geometry"]]
    g = g.merge(D["f"][["khg_code", "type"]].rename(columns={"type": "ptype"}), on="khg_code", how="left")   # GeoDataFrame.type is the geometry type
    g["geometry"] = g.geometry.simplify(0.01)
    fig, ax = plt.subplots(figsize=(10, 4.4))
    land = gpd.read_file(DATA / "basemap" / "locator_context.gpkg", layer="provinces_idn")
    land.plot(ax=ax, color="#f3f2ee", edgecolor="#d6d5cf", linewidth=.3)
    g[g.ptype.isna()].plot(ax=ax, color="#d9d8d1", linewidth=0)
    for t in TY:
        s = g[g.ptype == t]
        if len(s):
            s.plot(ax=ax, color=TYC[t], linewidth=0)
    ax.set_xlim(94.8, 141.2); ax.set_ylim(-9.5, 6.2); ax.set_axis_off()
    hs = [plt.Rectangle((0, 0), 1, 1, color=TYC[t]) for t in TY] + [plt.Rectangle((0, 0), 1, 1, color="#d9d8d1")]
    ax.legend(hs, [f"{t} {TYN[t]}" for t in TY] + ["Not scored"], loc="lower left", frameon=False, fontsize=8, ncol=3)
    return save(fig, out / "map_types.png")


def fig_matrix(D, out):
    f = D["f"][D["f"].type.notna()]
    c = D["meta"]["tercile_cuts"]
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    for t in TY:
        s = f[f.type == t]
        ax.scatter(s.complexity, s.urgency, s=np.clip(s.peat_km2, 5, 3000) ** 0.6 * 2.2, color=TYC[t], alpha=.75, edgecolor="white", linewidth=.4, label=f"{t} {TYN[t]}")
    for v in c["urgency"]:
        ax.axhline(v, color="#" + STYLE.MUTED, lw=.6, ls="--")
    for v in c["complexity"]:
        ax.axvline(v, color="#" + STYLE.MUTED, lw=.6, ls="--")
    ax.set_xlabel("Complexity (0 to 1)"); ax.set_ylabel("Urgency (0 to 1)")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.text(0.01, 0.99, "Dashed lines: borders between low, medium and high thirds. Larger dots: more peat.", transform=ax.transAxes, va="top", fontsize=7.5, color="#" + STYLE.MUTED)
    return save(fig, out / "matrix.png")


def fig_types(D, out):
    t = D["types"].set_index("type").reindex(TY)
    fig, axs = plt.subplots(1, 3, figsize=(10, 2.6), sharey=True)
    for ax, col, lab, k in zip(axs, ["khg", "peat_km2", "priority_ha"], ["KHG", "Peat (km²)", "Damaged peat (ha)"], [1, 1, 1]):
        ax.barh([f"{i} {TYN[i]}" for i in TY][::-1], t[col].values[::-1], color=[TYC[i] for i in TY][::-1])
        ax.set_title(lab, loc="left")
        for y, v in enumerate(t[col].values[::-1]):
            ax.text(v, y, " " + n0(v), va="center", fontsize=8)
        ax.spines["bottom"].set_visible(False); ax.set_xticks([])
    return save(fig, out / "types.png")


def fig_intervention(D, out):
    x = D["iv"].pivot_table(index="type", columns="intervention", values="khg", aggfunc="sum").reindex(index=TY, columns=IVO).fillna(0)
    fig, ax = plt.subplots(figsize=(8, 2.8))
    left = np.zeros(len(TY))
    for v in IVO:
        ax.barh([f"{t} {TYN[t]}" for t in TY][::-1], x[v].values[::-1], left=left[::-1], color=IVC[v], label=IVN[v])
        left += x[v].values
    ax.set_xlabel("Scored KHG")
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    return save(fig, out / "intervention.png")


def fig_validation(D, out):
    f = D["f"][D["f"].in_pool]
    tgt = f.u_burned_now * f.peat_km2
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    # urgency without this year's hotspots is what was validated: recompute it as repeat-national-final does (percentile
    # against the pool, mid-rank for ties, weighted mean of the indicators the KHG has)
    spec = {k: v for k, v in D["meta"]["rule"]["dimensions"]["urgency"].items() if k not in D["meta"]["rule"]["validation"]["exclude"]}
    num = pd.Series(0.0, index=f.index); den = pd.Series(0.0, index=f.index)
    for k, s in spec.items():
        ref = np.sort(f[k].dropna().to_numpy())
        x = f[k].to_numpy()
        r = pd.Series((np.searchsorted(ref, x, "left") + np.searchsorted(ref, x, "right")) / 2 / len(ref), index=f.index).where(f[k].notna())
        ok = r.notna(); num[ok] += s["weight"] * r[ok]; den[ok] += s["weight"]
    uval = num / den.replace(0, np.nan)
    ok = tgt.notna()
    k20 = int(round(.2 * ok.sum()))
    D["capture_check"] = float(tgt[uval[ok].nlargest(k20).index].sum() / tgt[ok].sum())
    ranks = {"Urgency (without 2026 fire detections)": uval[ok], "Past fires alone": f.loc[ok, "u_fire_freq"]}
    tgt = tgt[ok]
    for (lab, s), col in zip(ranks.items(), ["#" + STYLE.ACCENT, "#" + STYLE.MUTED]):
        o = s.sort_values(ascending=False).index
        y = tgt.reindex(o).fillna(0).cumsum() / tgt.sum()
        x = np.arange(1, len(o) + 1) / len(o)
        ax.plot(x, y, color=col, lw=1.8, label=lab)
    ax.plot([0, 1], [0, 1], color="#cccccc", lw=.8, ls=":")
    ax.axvline(.2, color="#" + STYLE.WARM, lw=.8, ls="--")
    ax.set_xlabel("Share of KHG, ranked from most to least urgent"); ax.set_ylabel("Share of 2026 burned peat")
    ax.legend(frameon=False, loc="lower right")
    return save(fig, out / "validation.png")


def fig_stability(D, out):
    f = D["f"][D["f"].in_pool]
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    bins = np.linspace(0, 1, 11)
    bottom = np.zeros(10)
    for t in TY:
        h, _ = np.histogram(f[f.type == t].type_stability, bins)
        ax.bar(bins[:-1] + .05, h, width=.09, bottom=bottom, color=TYC[t], label=t)
        bottom += h
    ax.set_xlabel("Share of 500 reruns with changed weights in which the KHG keeps its type"); ax.set_ylabel("KHG")
    ax.legend(frameon=False, ncol=5, fontsize=8)
    return save(fig, out / "stability.png")


def fig_actors(D, out):
    F = D["F"][D["F"].type.notna()]
    cols = [("priority_company_ha", "Licence holder"), ("priority_company_buffer_ha", "Licence holder with communities (5 km buffer)"),
            ("priority_mofor_ha", "Ministry of Forestry"), ("priority_klh_ha", "KLH/BPLH")]
    g = F.groupby("type")[[c for c, _ in cols]].sum().reindex(TY) / 1e3
    fig, ax = plt.subplots(figsize=(8, 2.8))
    left = np.zeros(len(TY))
    pal = ["#" + STYLE.WARM, "#e8a07a", "#" + STYLE.ACCENT, "#" + STYLE.NATIONAL]
    for (c, lab), col in zip(cols, pal):
        ax.barh([f"{t} {TYN[t]}" for t in TY][::-1], g[c].values[::-1], left=left[::-1], color=col, label=lab)
        left += g[c].values
    ax.set_xlabel("Damaged peat (thousand ha)")
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    return save(fig, out / "actors.png")


def fig_dims(D, out):
    f = D["f"][D["f"].type.notna()]
    dd = [x for x in DIM if x[0] in f]
    fig, axs = plt.subplots(1, len(dd), figsize=(2.5 * len(dd), 2.6), sharey=True)
    for ax, (c, lab) in zip(axs, dd):
        data = [f[f.type == t][c].dropna() for t in TY]
        b = ax.boxplot(data, vert=False, widths=.6, patch_artist=True, showfliers=False, medianprops={"color": "white"})
        for p, t in zip(b["boxes"], TY):
            p.set_facecolor(TYC[t]); p.set_edgecolor(TYC[t])
        ax.set_yticks(range(1, 6), TY); ax.set_title(lab, loc="left"); ax.set_xlim(0, 1)
        ax.invert_yaxis()
    return save(fig, out / "dims.png")


# ------------------------------------------------------------------------------------------------------------- chapters
def md_table(df, caption):
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    rows = ["| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else str(v).replace("|", "/") for v in r) + " |" for r in df.values]
    return f"Table: {caption}\n\n" + "\n".join([head, sep] + rows) + "\n"


def chapters(D, figs):
    f, F, meta, val, types = D["f"], D["F"], D["meta"], D["val"], D["types"]
    rule = meta["rule"]
    pool = f[f.in_pool]
    scored = f[f.type.notna()]
    s337 = scored[scored.klh_337]
    T = types.set_index("type")
    V, S = val["validation"], val["sensitivity"]
    tc = D["tc"]
    peat_tot = tc.peat_km2.sum()
    wsh = lambda c: (tc[c] * tc.peat_km2).sum() / peat_tot
    n337 = int(f.klh_337.sum())
    n337_sc = len(s337)
    dmg_tot = F[F.klh_337].priority_ha.sum() if "priority_ha" in F else D["pp"].priority_ha.sum()
    dmgB = T.loc["B", "priority_ha"]
    dmg_scored = T.priority_ha.sum()
    note("khg_total", len(f), "final_khg.csv rows")
    note("pool", meta["pool"], "final_meta.json pool")
    note("scored", meta.get("scored"), "final_meta.json scored")
    note("n337_scored", n337_sc, "final_khg.csv: klh_337 & type")
    note("dmgB_share", dmgB / dmg_scored, "final_types.csv priority_ha B / total")
    note("val_capture", V["urgency"]["capture_top20pct"], "final_validation.json")
    note("val_capture_fire", V["fire_history_only"]["capture_top20pct"], "final_validation.json")
    note("val_auc", V["urgency"]["auc"], "final_validation.json")
    note("stable80", S["share_khg_type_stable_80pct"], "final_validation.json")
    sm = lambda t: s337[s337.type == t]
    top = lambda t, k=8: sm(t).sort_values("rank_in_type").head(k)
    nm = lambda s: re.sub(r"^KHG\s+", "", re.sub(r"\s+", " ", s))
    lst = lambda t, k=6: ", ".join(nm(x) for x in top(t, k).khg_name)
    corr = pool[[c for c, _ in DIM if c in pool]].corr(method="spearman")
    ivr = rule["intervention"]
    rw_min, rv_min = int(round(100 * ivr["rewetting"]["min"])), int(round(100 * ivr["revegetation"]["min"]))
    iv337 = s337.intervention.value_counts()
    ivB = scored[scored.type == "B"].intervention.value_counts()
    ivt = lambda v, x=iv337: int(x.get(v, 0))
    nf = int(scored.flag_low_feasibility.sum()); nx = int(scored.flag_high_exposure.sum())
    note("iv337", iv337.to_dict(), "final_khg.csv: intervention of the scored 337")
    nwk = int(f.get("whole_khg", pd.Series(False, index=f.index)).fillna(False).sum())
    nsmall = len(scored) - meta['pool'] - nwk
    gpm = D["prof"].set_index("khg_id").peat_frac_gpm1km.reindex(f[f.get("whole_khg", False) == True].khg_code) if nwk else pd.Series(dtype=float)
    note("whole_khg", nwk, "final_khg.csv whole_khg")
    C = {}
    g337 = s337
    sat = {k: g337[k].median() for k in ("forest_loss_2015", "hansen_loss_2015", "burn_recovered_share", "burn_unrecovered_share", "reveg_share", "open_share", "ndvi_dry", "sm_root_dry") if k in g337}
    rho_fl = g337.forest_loss_2015.corr(g337.hansen_loss_2015, method="spearman") if "hansen_loss_2015" in g337 else float("nan")
    rho_nd = g337.ndvi_low_share.corr(g337.open_share, method="spearman") if "ndvi_low_share" in g337 else float("nan")
    n_sm = int(g337.sm_root_dry.notna().sum()) if "sm_root_dry" in g337 else 0
    note("sat_medians_337", {k: round(float(v), 4) for k, v in sat.items()}, "final_khg.csv, scored 337")

    # --- 00 Indonesian executive summary
    C["00_ringkasan"] = f"""# Ringkasan eksekutif

Indonesia memiliki 865 Kesatuan Hidrologis Gambut (KHG), yaitu hamparan gambut yang dibatasi sungai atau laut dan berfungsi sebagai satu sistem air. Gambut yang dikeringkan oleh kanal akan mengering, ambles dan mudah terbakar. Dua langkah utama pemulihannya adalah pembasahan (menyekat kanal agar air tertahan di gambut) dan revegetasi (menanami kembali gambut yang terbuka). Laporan ini mengurutkan KHG untuk membantu memutuskan di mana dana dan tenaga pemulihan sebaiknya dipakai lebih dulu. Laporan disusun oleh tim GIS RE-PEAT (Departemen Teknik Geodesi, Universitas Gadjah Mada) untuk Bank Dunia dan KLH/BPLH. **Status: draf untuk diskusi. Bobot setiap faktor masih sementara sampai disepakati bersama KLH.**

Setiap KHG dilihat dari lima sisi yang dinilai terpisah, tidak dijumlahkan menjadi satu angka:

- **Urgensi:** seberapa besar kemungkinan gambut terbakar atau makin rusak (riwayat kebakaran, titik panas, kerusakan, kanal).
- **Nilai yang dipertaruhkan:** apa yang akan hilang (gambut dalam, kubah gambut, kawasan lindung dan konservasi, luas gambut).
- **Kompleksitas:** berapa banyak pihak yang memiliki klaim atas lahan (perusahaan, kehutanan, desa, masyarakat), sehingga seberapa banyak kesepakatan yang dibutuhkan sebelum pekerjaan dapat dimulai.
- **Kelayakan:** seberapa mudah pembasahan dilakukan di lapangan (jarak ke sungai dan jalan, seberapa kering musim kemaraunya).
- **Penduduk:** berapa banyak orang yang tinggal di atau dekat gambut dan terpapar asap ketika gambut terbakar.

Setiap sisi diberi skor 0 sampai 1. Skor 0,8 berarti KHG itu lebih tinggi daripada sekitar 80% KHG pembandingnya. Urgensi, kompleksitas dan nilai yang dipertaruhkan menempatkan setiap KHG pada satu dari lima tipe tindakan. Kelayakan dan penduduk tidak mengubah tipe, tetapi menambahkan penanda peringatan.

- {n0(len(scored))} KHG dinilai, termasuk {n337_sc} dari {n337} KHG daftar kerja KLH{f". {nwk} di antaranya tidak memiliki gambut pada peta gambut KLH, sehingga seluruh KHG dipakai sebagai sebaran gambut; hasilnya ditandai kurang andal" if nwk else ""}.
- **Tipe A, aksi cepat:** {int(T.loc['A','khg'])} KHG ({int(T.loc['A','in_337'])} dalam 337). Urgensi tinggi, klaim lahan tidak terlalu rumit. Di sini dana dapat paling cepat digunakan. Contoh: {lst('A', 4)}.
- **Tipe B, koordinasi multipihak:** {int(T.loc['B','khg'])} KHG, semuanya dalam 337. Tipe ini memuat **{pc(dmgB / dmg_scored)}** gambut rusak (penilaian kerusakan KLH 2024) pada KHG yang dinilai, yaitu {n1(dmgB / 1e6)} juta ha. Urgensi tinggi, tetapi lahan diklaim bersamaan oleh perusahaan, Kementerian Kehutanan, KLH dan desa, sehingga pekerjaan membutuhkan kesepakatan antarpihak lebih dulu.
- **Tipe C, urgensi sedang:** {int(T.loc['C','khg'])} KHG. **Tipe D, lindungi dan pantau:** {int(T.loc['D','khg'])} KHG bergambut dalam atau berkubah yang jarang terbakar. **Tipe E, pantau:** {int(T.loc['E','khg'])} KHG.
- **Yang dibutuhkan gambutnya,** pada 337 KHG yang dinilai: pembasahan {ivt('rewetting')} KHG, pembasahan dan revegetasi {ivt('rewetting and revegetation')}, revegetasi {ivt('revegetation')}, perlindungan {ivt('protect')}. Pembasahan berarti sedikitnya {rw_min}% gambut berada di sekitar kanal. Revegetasi berarti sedikitnya {rv_min}% gambut perlu ditanami kembali: terbuka menurut peta tutupan lahan KLH 2022, terbakar pada 2015-2023 dan belum tumbuh kembali menurut peta hutan satelit 2024, atau hutannya hilang sejak 2015.
- **Uji terhadap kebakaran 2026:** urutan ini disusun dari data sampai 2025, lalu dibandingkan dengan kebakaran 2026. Seperlima KHG yang paling mendesak memuat **{pc(V['urgency']['capture_top20pct'])}** gambut yang terbakar pada 2026. Bila hanya memakai riwayat kebakaran, angkanya {pc(V['fire_history_only']['capture_top20pct'])}.
- **Seberapa mantap tipenya:** perhitungan diulang {S['runs']} kali dengan setiap bobot diubah secara acak hingga setengahnya, naik atau turun. {pc(S['share_khg_type_stable_80pct'])} KHG tetap pada tipe yang sama dalam sedikitnya 4 dari 5 ulangan.
- Tidak ada KHG berurgensi tinggi di luar 362 KHG prioritas PPEG KLH.

Langkah berikut yang diusulkan: lokakarya pembobotan bersama KLH; permintaan data klaim lahan yang belum tersedia (hutan adat, batas wilayah adat dari BRWA, PIAPS, rilis izin terbaru dari SIGAP, hak atas tanah dari BPN); dan analisis rinci di dalam KHG tipe A dan B (kebutuhan air, pompa, sekat kanal) sebagai dasar desain.
"""
    C["00_ringkasan"] = id_num(C["00_ringkasan"])

    # --- 01 summary
    C["01_summary"] = f"""# 1 Summary

Indonesia has 865 peat hydrological units, known by their Indonesian abbreviation KHG. Each is an area of peat bounded by rivers or the sea that works as one water system. When canals drain peat, it dries out, sinks and burns. The two main ways to restore it are rewetting (blocking canals so the water stays in the peat) and revegetation (replanting peat that has lost its forest). This report ranks the KHG to help decide where restoration money and effort should go first.

The RE-PEAT GIS team at Universitas Gadjah Mada prepared it for the World Bank and for KLH/BPLH, Indonesia's environment ministry. **It is a draft for discussion. The weight given to each factor is provisional until KLH agrees it.**

## {{n}} How the ranking works

We look at every KHG from five angles and keep them separate, rather than adding them up into one number:

- **Urgency:** how likely the peat is to burn or degrade further. It draws on past fires, fire hotspots seen by satellite, KLH's damage assessment and canals.
- **Stake:** what would be lost: deep peat, peat domes, protected and conservation areas, and the size of the peat.
- **Complexity:** how many parties claim the same land (companies, the forestry ministry, villages, community forestry groups), and so how much negotiation is needed before work can start.
- **Feasibility:** how easy rewetting would be on the ground: distance to rivers and roads, and how dry the dry season gets.
- **People:** how many people live on or near the peat and breathe the smoke when it burns.

Each angle gets a score from 0 to 1 that says where the KHG stands among the others. A score of 0.8 means the KHG is higher than about 80% of the KHG it is compared with.

Urgency, complexity and stake place each KHG in one of five types of action:

- **A, quick action:** {int(T.loc['A','khg'])} KHG ({int(T.loc['A','in_337'])} of them in KLH's work list of 337 KHG). Urgency is high and land claims are manageable, so money can be put to work here soonest. The most urgent are {lst('A', 5)}.
- **B, multi-party coordination:** {int(T.loc['B','khg'])} KHG, all in the 337. They hold **{pc(dmgB / dmg_scored)} of the damaged peat** in the scored KHG ({n1(dmgB / 1e6)} million ha). Urgency is high, but companies, the forestry ministry, KLH and villages all hold claims, so work depends on agreement among them first. The most urgent are {lst('B', 5)}.
- **C, medium urgency:** {int(T.loc['C','khg'])} KHG.
- **D, protect and monitor:** {int(T.loc['D','khg'])} KHG with deep or domed peat that rarely burns, mostly outside the 337.
- **E, monitor:** {int(T.loc['E','khg'])} KHG with low urgency and less at stake.

Feasibility and people do not change the type. They add a warning flag instead, for example "low feasibility".

## {{n}} What the peat needs

Separately from the type, each KHG gets a label for the work its peat needs:

- **Rewet** if at least {rw_min}% of the peat lies close enough to a canal to be drained by it.
- **Revegetate** if at least {rv_min}% of the peat needs replanting: it is open land or scrub on KLH's 2022 land cover map, or it burned in 2015 to 2023 and the 2024 satellite forest map shows no regrowth, or its forest was cleared after 2014.
- **Both**, or **protect** if neither applies.

Of the scored KHG in the 337, {ivt('rewetting')} need rewetting, {ivt('rewetting and revegetation')} need both, {ivt('revegetation')} need revegetation and {ivt('protect')} need protection. The type says how urgent and how complicated the work is; the label says what the work is.

## {{n}} Coverage

We scored {n0(len(scored))} KHG, including {n337_sc} of the {n337} in KLH's work list. Most of them ({meta['pool']}) have at least {rule['min_peat_km2']} km² of peat on KLH's peat map; these form the comparison group against which every score is set. Another {nsmall} KHG in the 337 have less peat; they are scored against the same group and flagged as less reliable. {nwk} more KHG in the 337 show no peat at all on KLH's peat map, although they are peat units by definition and an independent global peat map shows peat on {pc(gpm.min()) if nwk else ''} to {pc(gpm.max()) if nwk else ''} of each. For these we treated the whole KHG as peat, and flagged them too.

## {{n}} Can the ranking be trusted?

We built the ranking from data up to 2025 and then checked it against the 2026 fire season, which it had not seen. The fifth of KHG ranked most urgent held **{pc(V['urgency']['capture_top20pct'])} of all the peat that burned in 2026**. Ranking by past fires alone would have caught {pc(V['fire_history_only']['capture_top20pct'])}.

We also tested how much the types depend on the exact weights. We reran the ranking {S['runs']} times, each time moving every weight at random by up to half, up or down. {pc(S['share_khg_type_stable_80pct'])} of the KHG kept the same type in at least 4 runs out of 5. No KHG with high urgency lies outside the 362 KHG that KLH has already marked as priorities.

## {{n}} What it rests on, and what it cannot see

The ranking uses {len(D['reg'])} data layers, each documented with who made it, which version, the terms of use and whether we could check it (Annex A). KLH's main peat analysis was checked against independent copies of its sources and agrees with them on 93 to 100% of the area (Chapter 4).

Some information is not yet available to us: customary forest and customary territory boundaries, the indicative map of areas for community forestry, the newest permit releases and private land titles. Land claims are therefore probably more complicated than shown, especially in KHG with customary land. KLH's 2022 land cover map, one of the inputs to the revegetation label, could not be checked against an independent copy; the satellite forest map used alongside it is independent of KLH.

## {{n}} Next steps

We propose a short weighting session with KLH; data requests for the missing land claims (to the forestry ministry's SIGAP service and to BRWA, the customary territory registry); and detailed design work inside the type A and B KHG (water needs, pumps, canal blocks).
"""

    # --- 02 terms
    C["02_terms"] = f"""# 2 Terms used in this report

## {{n}} Peat and restoration

- **Peat (gambut):** soil made of plant material that never fully rotted because it stayed waterlogged. Tropical peat can be many metres deep and holds a great deal of carbon. When it dries it shrinks and burns easily, often underground and for weeks.
- **KHG (Kesatuan Hidrologis Gambut), peat hydrological unit:** a stretch of peat between rivers, or between a river and the sea, that behaves as one water system. Indonesia's registry lists 865. Draining one part affects the rest, which is why restoration is planned per KHG.
- **Peat dome (kubah gambut):** the raised centre of a KHG, where the peat is deepest. It stores the water that feeds the rest of the unit.
- **Canal-affected zone:** land close enough to a canal for the canal to drain it. KLH's maps use about 1 km from primary canals, 500 m from secondary and 250 m from tertiary canals.
- **Rewetting:** raising the water level in drained peat, mainly by blocking canals, so the peat stays wet and does not burn.
- **Revegetation:** replanting peat that has lost its forest cover.
- **Hotspot:** a spot where a satellite sensor detected heat, usually a fire. We use NASA's VIIRS and MODIS sensors.
- **Burned area:** land mapped by KLH as burned in a given year, usually from satellite images after the fire season.

## {{n}} KLH lists and data

- **KLH/BPLH:** Indonesia's environment ministry and environmental agency.
- **KLH's 337 work list:** the KHG where KLH is preparing rewetting designs, chosen because they contain the 2,004 target villages of the 2026 peat restoration plan (the "Bluebook").
- **PPEG analysis:** KLH's integrated map of peat restoration (April 2026). It combines peat, land use, licences, damage, fire and canals in one layer and marks priority areas. 362 KHG contain such priority areas; all of the 337 are among them.
- **SKEG damage:** KLH's 2024 assessment of peat damage, in classes from light to very heavy.
- **Licence (concession):** a permit to use land, mostly for oil palm or pulpwood plantations, logging or mining. A licence on a KHG is a fact about who holds the land, not a statement about who caused fire or damage.
- **Forest estate (Kawasan Hutan):** state forest land managed by the forestry ministry.
- **Social forestry:** permits that give communities the right to manage state forest land (community forest, village forest, community plantation).
- **PPTPKH:** the programme that settles land occupied by people inside the forest estate, part of agrarian reform.
- **DMPG villages:** villages in KLH's peat-care village programme.

## {{n}} Reading the numbers

- **Comparison group (scoring pool):** the {meta['pool']} KHG with at least {rule['min_peat_km2']} km² of peat. Every score says where a KHG stands within this group.
- **Score from 0 to 1 (percentile rank):** the share of the comparison group that a KHG beats on a measure. A fire score of 0.9 means the KHG burned more than 90% of the others. This lets us combine measures with different units, such as hectares burned and kilometres to the nearest road.
- **Weight:** how much a measure counts within its angle. A measure with weight 2 counts twice as much as one with weight 1. Weight 0 means the measure is shown but does not count.
- **Thirds (terciles):** we split each score into low, medium and high, so that each third holds a third of the comparison group.
- **Median:** the middle value: half of the KHG are above it and half below. The annex compares each KHG with the median of the comparison group.
- **Correlation:** a number from −1 to 1 that says how closely two rankings follow each other. 1 means the same order, 0 means no relation.
- **km² and ha:** 1 km² is 100 ha.
"""

    # --- 03 purpose and scope
    C["03_scope"] = f"""# 3 Purpose and scope

KLH's PPEG analysis shows where peat is damaged and who holds the land. KLH's work list of 337 KHG shows where rewetting designs are being prepared. This prioritisation adds a comparison across all KHG. For each one it asks four questions: how urgent is action, what is at stake, how hard will the work be, and how practical is rewetting on the ground. The answers are turned into types of action that match the tools KLH has.

- **What is ranked.** All 865 KHG of the national registry. Scores are set against the {meta['pool']} KHG with at least {rule['min_peat_km2']} km² of peat on KLH's peat map. KHG in KLH's 337 are scored even when they are smaller.
- **KLH's priorities.** For every KHG we record whether it is in the 337 work list and whether it is one of the 362 PPEG priority KHG.
- **What comes out.** For each KHG: the five scores, the type, the work its peat needs, its rank (nationally, within the 337 and within its type), how firm its type is, and any warning flags. The results are in the national dashboard, in data tables and map layers, and in Annex B (one page per KHG of the 337).
- **Technical details.** Annex C explains each calculation with a worked example, lists the open data sources, and describes how to reproduce the analysis.
- **What it does not do.** It ranks KHG for attention and funding. It does not say where to put canal blocks or pumps; that needs detailed design work inside each KHG.
"""

    # --- 04 data
    reg = D["reg"]
    ver = D["ver"]
    vt = ver[~ver.field.str.startswith("BA_")].copy()
    ba = ver[ver.field.str.startswith("BA_")]
    vt = pd.concat([vt, pd.DataFrame([{"field": "BA_2015 … BA_2024", "source": "burnt_area_2015_2026_Indonesia.gpkg", "agree_share": ba.agree_share.min(), "note": f"lowest of the {len(ba)} years"}])])
    vt["Agrees"] = (vt.agree_share * 100).round(1).astype(str) + "%"
    SRCN = {"batas_khg": "KHG boundaries (2017)", "batas_desa": "Village boundaries 2023 (KLH)", "ALL_Updade__IZIN": "Business licences 2025",
            "KWSHUTAN": "Forest estate map 1:250,000 (2023)", "FEG__Indonesia": "Peat function map 2017", "klhk_khg_feg_50k": "Peat function map 1:50,000",
            "lahan_gambut_indonesia_2025": "Peat map 2025 (SiTMAT)", "burnt_area": "Burned area 2015-2026 (KLHK)"}
    FLDN = {"NAMA_KHG": "KHG name", "PULAU": "Island", "PROV_2023": "Province", "KABKO_2023": "District or city", "KEC_2023": "Sub-district",
            "DESA_2023": "Village", "IZIN_USAHA": "Licence type", "PERUSAHAAN": "Licence holder", "Fungsi_KWS": "Forest estate function",
            "FEG_250K": "Peat function (1:250,000)", "PEAT_THICK": "Peat thickness class", "TNH_GAMBUT": "Peat or mineral soil",
            "FEG_PEAT_1": "Peat function (1:50,000)", "LAHAN_GAMB": "Peat land", "BA_2015 … BA_2024": "Burned area, each year 2015 to 2024"}
    vt["Independent copy of the source"] = vt.source.map(lambda x: next((v for k, v in SRCN.items() if k in str(x)), str(x).split(":")[0]))
    vt["Note"] = vt.note.fillna("").map(lambda x: "only where the 1:50,000 map exists (17% of the points); classes compared by meaning" if "covers" in x else x)
    vt["field"] = vt.field.map(lambda x: FLDN.get(x, x.replace("_", " ")))
    vt = vt[["field", "Independent copy of the source", "Agrees", "Note"]].rename(columns={"field": "Information in KLH's PPEG map"})
    themes = reg.groupby("theme").id.count().reset_index().rename(columns={"theme": "Theme", "id": "Layers"})
    C["04_data"] = f"""# 4 Data

## {{n}} Data layers and how they are documented

The ranking uses {len(reg)} map layers, listed in Annex A. For each one we record who made it, under what authority, which version, its level of detail, when we received it, the terms of use, how we use it, and whether we could check it against an independent source. Readers can therefore see which results rest on checked data and which on layers still to be confirmed. All layers, plus a summary layer with one row per KHG, are shared with KLH and the World Bank as one GIS package. Where two sources hold the same information we keep both. This is how we found and corrected the naming error described below.

{md_table(themes, "Data layers by theme")}
## {{n}} KLH's PPEG analysis and how we checked it

KLH's PPEG analysis (April 2026) cuts Indonesia's peat into 989,398 pieces. Each piece carries KHG, village, licence, forest status, peat depth and function, land cover, damage, burned area and canal information. KLH uses it as the basis for its restoration targets, so we checked it before using it. We picked 20,000 pieces at random (larger pieces had a higher chance of being picked) and compared each piece's information with an independent copy of the original map.

{md_table(vt, "How often KLH's PPEG map agrees with an independent copy of its source (share of the sampled area)")}
- **What matches.** Peat, burned area, KHG and licences agree on 98 to 100% of the area. KLH's summary classes (licensed or not, canal-affected, burned, number of fires) follow correctly from the information they are built on.
- **What we clarified.** The "Buffer 5 Kilometer" class means land within 5 km of a licence. The canal-affected zones reach about 1 km from primary canals, 500 m from secondary and 250 m from tertiary canals.
- **What to confirm with KLH.** About 6.6% of the area is outside the forest estate in PPEG but inside it on the 2023 forest estate map. PPEG probably used a different release of that map. About 1.9% is unlicensed in PPEG but licensed in the 2025 licence map, perhaps because of the date of the licence data.
- **One correction.** Parts of the Papua KHG that fall outside the 2017 administrative maps carry placeholder place names in PPEG. We take place names from the 2023 village boundaries instead.
- **Not yet checked.** Land cover 2022, the 2024 damage assessment, the peat landform and depth information (which includes the peat domes) and KLH's own actor and intervention classes. We have no independent copy of these.

## {{n}} Forest change, plant cover and soil moisture from satellites

Four open satellite products add what the 2022 land cover map cannot show: whether burned peat has grown back, and how wet the peat is now. They are processed the same way for every KHG.

- **Forest change.** The European Commission's Joint Research Centre publishes a yearly map of tropical moist forest at 30 m detail, from Landsat images. Each pixel is marked as untouched forest, degraded forest, cleared, regrowing, water or other land. Comparing December 2014 with December 2024 shows where forest was lost after 2014. Combined with KLH's burned area maps for 2015 to 2023, it also shows which burned peat has grown back and which has not. The University of Maryland's global forest change map (often called the Hansen map) is kept as a cross-check. The two maps disagree a lot: for the middle KHG of the 337, forest lost after 2014 is {pc(sat.get('forest_loss_2015', float('nan')))} of the peat on the Joint Research Centre map and {pc(sat.get('hansen_loss_2015', float('nan')))} on the Hansen map, and the two put the KHG in quite different orders (correlation {rho_fl:.2f}). The Hansen map counts every harvest of plantation trees as forest loss, while the other map follows natural forest only. We therefore use the Joint Research Centre map.
- **Plant cover now.** Two indices from the European Sentinel-2 satellites for the 2025 dry season (July to October), with clouds removed. NDVI measures how green and dense the plants are; NDMI measures how much water the leaves hold. Both run from −1 to 1, and higher means greener or wetter. Low NDVI matches the open land of the 2022 map only weakly (correlation {rho_nd:.2f}), probably because few cloud-free images reach peat in the dry season. We report these values but do not score them.
- **Soil moisture.** NASA's SMAP satellite estimates the water in the top metre of soil, in cubic metres of water per cubic metre of soil. We use the July to October 2025 average and its difference from the 2016-2024 average for the same months. Its pixels are about 9 km wide, so a small KHG is described by only one or two values. {n_sm} of the 337 have a value.

## {{n}} Land claims

To measure how complicated land claims are, we count the claims that overlap on the same piece of peat. These are business licences (2025), social forestry permits, the forest estate, DMPG villages, land being settled under the PPTPKH programme, and forest released for other uses. We obtained the social forestry, PPTPKH and released-forest maps from the forestry ministry's public map services, through the national Satu Peta portal, on 16 November 2026.

Of the {n0(peat_tot)} km² of peat in all KHG, licences cover {pc(wsh('share_licence'), 1)}, the forest estate {pc(wsh('share_forest_estate'), 1)}, DMPG villages {pc(wsh('share_dmpg'), 1)}, released forest {pc(wsh('share_released'), 1)}, PPTPKH {pc(wsh('share_pptpkh'), 1)} and social forestry {pc(wsh('share_community'), 1)}. {pc(wsh('share_3plus_claims'), 1)} of the peat carries three or more claims at once, and {pc(wsh('share_no_claim'), 1)} carries none.

Some claims are missing. The public map service holds no customary forest data. BRWA, the customary territory registry, lists 2,283 territories but shows their boundaries only as pictures. The indicative map of areas for social forestry and the newest permit releases are available only on request from the forestry ministry, and we have no data on private land titles. In the licence map no two licences overlap, so overlapping licences cannot be measured. The complexity scores are therefore a minimum: KHG with customary or private claims may be more complicated than shown.
"""

    # --- 05 method
    dims = rule["dimensions"]
    DESC = {"u_fire_freq": "Average share of the peat burned each year, 2015 to 2025",
            "u_burn_repeat": "Share of the peat that burned twice or more, 2015 to 2025",
            "u_hotspot": "Satellite fire detections per km² of peat per year, 2012 to 2025",
            "u_hotspot_now": "Satellite fire detections this year per km² of peat",
            "damage_share": "Share of the peat that KLH's 2024 assessment rates as damaged",
            "canal_share": "Share of the peat close enough to a canal to be drained by it",
            "thick3m_share": "Share of the peat that is 3 m deep or more",
            "dome_share": "Share of the peat on a peat dome",
            "protected_share": "Share of the peat that the government has set aside for protection",
            "peat_km2": "Area of peat on KLH's map",
            "conservation_share": "Share of the peat in national parks and nature reserves",
            "tenure_complexity": "How many claims overlap on the peat (see below)",
            "actor_types": "How many kinds of land holder hold damaged peat (out of 4)",
            "villages": "Target villages of the restoration plan plus DMPG villages",
            "dry_balance_mm": "Rain minus the water lost to evaporation over the driest 4-5 months, 2018-2025 average (higher is easier)",
            "brgm_blocks_per_km2": "Canal blocks and wells already built, per km² of peat",
            "water_dist_km": "Typical distance from the peat to a large river or lake (shorter is easier)",
            "road_dist_km": "Typical distance from the peat to a road (shorter is easier)",
            "pop_on_peat": "People living on the peat (2025 population map, 40 m detail)",
            "pop_10km": "People living within 10 km of the KHG, who breathe its smoke",
            "villages_peat": "Villages with land on the peat",
            "forest_loss_2015": "Share of the peat that was forest in 2014 and cleared by 2024 (satellite forest map)",
            "sm_root_dry": "Soil moisture in the 2025 dry season (satellite); drier counts as more urgent",
            "u_canal_primary": "Length of primary canal per km² of KHG", "u_canal_secondary": "Length of secondary canal per km² of KHG",
            "u_canal_tertiary": "Length of tertiary canal per km² of KHG"}
    INDN = {"u_fire_freq": "Burned each year", "u_burn_repeat": "Burned repeatedly", "u_hotspot": "Fire detections", "u_hotspot_now": "Fire detections this year",
            "damage_share": "Damaged peat", "canal_share": "Peat near canals", "thick3m_share": "Deep peat", "dome_share": "Peat dome",
            "protected_share": "Protected peat", "peat_km2": "Peat area", "conservation_share": "Conservation areas",
            "tenure_complexity": "Overlapping claims", "actor_types": "Kinds of land holder", "villages": "Villages", "dry_balance_mm": "Dry-season water balance",
            "brgm_blocks_per_km2": "Existing canal blocks", "water_dist_km": "Distance to water", "road_dist_km": "Distance to roads",
            "pop_on_peat": "People on the peat", "pop_10km": "People within 10 km", "villages_peat": "Villages on the peat",
            "forest_loss_2015": "Forest lost since 2015", "sm_root_dry": "Dry-season soil moisture", "u_canal_primary": "Primary canal density",
            "u_canal_secondary": "Secondary canal density", "u_canal_tertiary": "Tertiary canal density"}
    rows = []
    for dname, spec in dims.items():
        for ind, s in spec.items():
            rows.append([dname.capitalize(), INDN.get(ind, ind.replace("_", " ").capitalize()), DESC.get(ind, ""), s["weight"]])
    ind_tab = pd.DataFrame(rows, columns=["Angle", "Measure", "What it measures", "Weight"])
    C["05_method"] = f"""# 5 Method

## {{n}} Why five separate angles

One combined score would let a high fire risk cancel out difficult land claims, and hide exactly what KLH needs to see. A KHG that burns every year and is crowded with competing claims needs a different response from one that burns as often on unclaimed land. A deep, untouched peat dome needs protection, not restoration. So we score the five angles separately and combine them only through the five types, which keep them visible.

## {{n}} From measures to scores

Each angle is built from a few measures, listed in the table below. For each measure, a KHG gets a score from 0 to 1: the share of the comparison group it beats. A KHG that burned more than 70% of the others gets 0.7 for that measure. This puts measures with different units, such as hectares burned and kilometres to the nearest road, on the same footing, and stops one extreme KHG from squeezing all the others together. The score of an angle is the average of its measures, counting each by its weight. A KHG missing a measure is scored on the ones it has. High always means more: more urgent, more at stake, more complex, more feasible, more people.

{md_table(ind_tab, "Measures, what they measure, and their weights (rules dated " + str(rule['written']) + ")")}
"Burned each year" counts double, as it did in the earlier fire-based ranking. "Overlapping claims" counts double within complexity because it already sums up four separate measures.

Some measures have weight 0. They are calculated and shown, and anyone can give them a weight in the dashboard, but they do not affect the result as it stands. The canal densities repeat what "peat near canals" already measures. Forest loss and soil moisture are new and are left for the weighting session with KLH. Other figures are reported only, as background in the dashboard and the profiles: burned peat that has or has not grown back, the satellite forest classes, the Hansen forest loss, plant greenness (NDVI) and leaf moisture (NDMI), and how much drier than usual the soil is. Canal blocks already built are also reported only. The first version scored them, but blocks were built where fires had been, so the measure mostly repeated urgency. The dashboard's Method page explains how every figure is calculated.

**Overlapping claims.** We lay a regular grid of points over each KHG's peat. At each point we note which of six claims are present: a business licence, social forestry, forest estate, a DMPG village, PPTPKH land, or released forest. Four measures per KHG make up the score: the share of the peat where a licence sits on social forestry or village land; the share where claims openly conflict (a licence on PPTPKH or social forestry land, or forest estate on PPTPKH land); the average number of claims per point; and the number of licence holders.

## {{n}} Five types of action

Urgency, complexity and stake are each split into thirds (low, medium, high) within the comparison group. The types follow from those thirds:

- **A, quick action:** high urgency, low or medium complexity.
- **B, multi-party coordination:** high urgency, high complexity.
- **C, medium urgency:** medium urgency.
- **D, protect and monitor:** low urgency, high stake.
- **E, monitor:** low urgency, low or medium stake.

Feasibility and people do not change the type. A KHG in the lowest third of feasibility is flagged "low feasibility" ({nf} KHG), and one in the highest third for people "high exposure" ({nx} KHG). Within each type, KHG are ranked by urgency, then by stake. Each KHG also has an overall urgency rank, among all scored KHG and among the 337.

## {{n}} What the peat needs

The type says how urgent and how complicated a KHG is, but not what its peat needs. A second label does, using two shares of the KHG's peat and fixed thresholds. The thresholds stay the same from year to year, so a label always means the same thing.

- **Rewet:** at least {rw_min}% of the peat lies in KLH's canal-affected zones. The peat is being drained and the canals need blocking.
- **Revegetate:** at least {rv_min}% of the peat needs replanting. We check every 30 m square of peat. It counts if it is open land or scrub on KLH's 2022 land cover map; or if it burned in 2015 to 2023 and the 2024 satellite forest map still shows it cleared or bare; or if it was forest in 2014 and cleared by 2024. Plantations, farmland and settlements never count: they call for help with livelihoods, not replanting.
- **Rewet and revegetate:** both apply.
- **Protect:** neither applies. The peat is mostly forested and undrained, and the task is to keep it wet and free of fire.

## {{n}} Rules written down before the results

We wrote down and dated each rule before computing its result. When a rule changed after that, the change is listed below with its date and reason, and the earlier result is kept. Readers can see what was decided in advance and what was adjusted later.

Table: Rules and later changes

| Date | Rule | Change | Reason |
|---|---|---|---|
| 2026-11-16 | Overlapping claims, version 1 | Written before any result | Measure overlapping claims per KHG |
| 2026-11-16 | Overlapping claims, version 1, change | Overlapping licences reported, not scored | No two licences overlap in the licence map, so the measure is always 0 |
| 2026-11-16 | Overlapping claims, version 2 | Six kinds of claim, openly conflicting claims, number of licence holders | Version 1 missed social forestry and settled forest land, and two of its measures barely varied. Version 1 result kept |
| {rule['written']} | Ranking | Written before any result | Four angles and the types |
| {rule['written']} | Ranking, version 2 | Written before any version 2 result; version 1 kept | Feasibility from distance to large rivers and roads instead of canal blocks built (which repeated urgency); conservation areas added to stake; a fifth angle, people; the label for what the peat needs |
| {rule['written']} | Ranking, change | KHG of the 337 with less than {rule['min_peat_km2']} km² of peat scored against the comparison group and flagged | 99 of the 337 had dropped out, against the aim of covering all 337; they hold 0.09% of its damaged peat |
| {rule['written']} | Ranking, change | KHG of the 337 with no peat on KLH's map scored with the whole KHG as peat, and flagged; population from the 2025 map at 40 m instead of the 2020 map at 1 km | A KHG is a peat unit by definition, and an independent global peat map shows peat in each; the finer population map counts people on the peat more accurately |
| 2026-11-17 | Ranking, change | Primary, secondary and tertiary canal densities added to urgency with weight 0 | Kept visible and adjustable; "peat near canals" already measures drainage |
| 2026-11-18 | Ranking, change | Forest lost since 2015 and dry-season soil moisture added to urgency with weight 0. Revegetation now also counts burned peat that has not grown back and forest lost since 2015 | The 2022 land cover map alone missed old burn scars and recent clearing. Six labels in the 337 changed; types and ranks did not |
| 2026-11-18 | Correction | Dry-season water balance used as rain minus evaporation, as the rule states | The data had held evaporation minus rain, which turned the measure upside down in feasibility. The low-feasibility flags were recalculated |

## {{n}} How we tested the ranking

**Against a year it had not seen.** We rebuilt urgency from data up to 2025, leaving out this year's fire detections, and compared it with the share of each KHG's peat that burned in 2026 according to KLH. We also compared a ranking by past fires alone.

**Against changes in the weights.** We reran the ranking {S['runs']} times. Each time, every weight was multiplied by a random number between 0.5 and 1.5. For each KHG we report how often it kept its type, and how far its urgency rank moved.
"""

    # --- 06 results
    isl = scored.groupby(["type"]).island.value_counts().unstack(fill_value=0).reindex(TY).fillna(0).astype(int)
    isl.columns = [c.replace("Pulau ", "") for c in isl.columns]
    isl.insert(0, "Type", [f"{t} {TYN[t]}" for t in TY])
    tsum = types.copy()
    tsum.insert(0, "Type", [f"{t} {TYN[t]}" for t in tsum.type])
    tsum = tsum[["Type", "khg", "in_337", "peat_km2", "priority_ha", "low_feasibility"]]
    tsum.columns = ["Type", "KHG", "In the 337", "Peat (km²)", "Damaged peat (ha)", "Flagged low feasibility"]
    for c in tsum.columns[1:]:
        tsum[c] = tsum[c].map(n0)

    def toptab(t, k=10, src=None):
        x = (src[src.type == t].sort_values("rank_in_type").head(k)) if src is not None else top(t, k)
        return pd.DataFrame({"Rank in type": x.rank_in_type.astype(int), "KHG": x.khg_name.map(nm), "Province": x.provinces,
                             "Peat (km²)": x.peat_km2.map(n0), "Urgency": x.urgency.map("{:.2f}".format), "Stake": x.stake.map("{:.2f}".format),
                             "Complexity": x.complexity.map("{:.2f}".format),
                             "Type kept under weight changes": x.type_stability.map(lambda v: "not tested (small KHG)" if pd.isna(v) else pc(v))})
    gaps = D["gaps"]
    toptab_note = ("Urgency, stake and complexity are scores from 0 to 1 (the share of the comparison group the KHG beats). "
                   f"\"Type kept under weight changes\" is the share of {S['runs']} reruns, each with every weight changed at random by up to half, in which the KHG kept the same type. "
                   "A value near 100% means the type does not depend on the exact weights; a value near 50% means the KHG sits close to the border with another type. "
                   f"KHG with less than {rule['min_peat_km2']} km² of peat were not part of this test.")
    C["06_results"] = f"""# 6 Results

## {{n}} The national picture

![Scored KHG by type. Grey: not scored (less than {rule['min_peat_km2']} km² of KLH peat and outside the 337, or no KLH peat).]({figs['map']})

{md_table(tsum, "Number of KHG, peat area and damaged peat by type (all scored KHG; damage from KLH's 2024 assessment)")}
![Number of KHG, peat area and damaged peat by type.]({figs['types']})

Type B holds {pc(dmgB / dmg_scored)} of the damaged peat in the scored KHG. These are {int(T.loc['B','khg'])} KHG where high urgency meets complicated land claims: {isl.loc['B', 'Sumatera'] if 'Sumatera' in isl else ''} in Sumatera and {isl.loc['B', 'Kalimantan'] if 'Kalimantan' in isl else ''} in Kalimantan. Type A gathers {int(T.loc['A','khg'])} mostly smaller KHG with high urgency and simpler claims. Type D, protect and monitor, is mostly in Papua and outside the 337.

{md_table(isl, "Scored KHG by type and island")}
## {{n}} What the peat needs

{md_table(D['iv'].assign(Type=lambda x: x.type + " " + x.type.map(TYN), Intervention=lambda x: x.intervention.map(IVN)).sort_values(['type', 'intervention'], key=lambda c: c.map({v: i for i, v in enumerate(IVO)}) if c.name == 'intervention' else c)[['Type', 'Intervention', 'khg', 'in_337', 'peat_km2', 'priority_ha']].rename(columns={'Intervention': 'What the peat needs', 'khg': 'KHG', 'in_337': 'In the 337', 'peat_km2': 'Peat (km²)', 'priority_ha': 'Damaged peat (ha)'}).assign(**{'Peat (km²)': lambda x: x['Peat (km²)'].map(n0), 'Damaged peat (ha)': lambda x: x['Damaged peat (ha)'].map(n0)}), "Scored KHG by type and by what their peat needs")}
![Scored KHG by type and by what their peat needs.]({figs['iv']})

Rewetting dominates. Of the {int(T.loc['B','khg'])} type B KHG, {ivt('rewetting', ivB)} need rewetting and {ivt('rewetting and revegetation', ivB)} need both rewetting and revegetation. Revegetation alone is more common in types C and E, where the peat is open but less drained.

## {{n}} Urgency and complexity go together

![Urgency against complexity for every scored KHG, coloured by type. Each dot is a KHG; larger dots have more peat.]({figs['matrix']})

The KHG that burn most also tend to have the most complicated land claims (correlation {corr.loc['urgency','complexity']:.2f} within the comparison group). This is why type B is large. It comes from the landscape, not from the method: fires are worst where peat was opened up for plantations, and those are the places with the most claims. The message for planning is that most of the damaged peat cannot be rewetted by one agency alone. What is at stake relates much less to urgency (correlation {corr.loc['urgency','stake']:.2f}).

![How the five scores spread within each type. Each box holds the middle half of the KHG of that type; the white line is the median.]({figs['dims']})

## {{n}} Who holds the damaged peat

KLH's PPEG analysis assigns every area of damaged peat to one of four kinds of holder: a licence holder; a licence holder together with nearby communities (land within 5 km of a licence); the forestry ministry; or KLH. The figure shows how the damaged peat in each type is split among them.

![Damaged peat by the holder KLH assigns to it, by type.]({figs['actors']})

## {{n}} Most urgent KHG in the 337

{md_table(toptab('A'), "Type A, quick action: the 10 most urgent KHG in the 337")}
{toptab_note}

{md_table(toptab('B'), "Type B, multi-party coordination: the 10 most urgent KHG in the 337")}
{md_table(toptab("D", 20, scored), "Type D, protect and monitor: all scored KHG (one is in the 337)")}
Results for every scored KHG are in the data tables and the dashboard. Annex B has a one-page profile of each KHG in the 337.

## {{n}} How the lists compare

- **PPEG priority KHG outside the 337:** {int((gaps.gap == 'PPEG priority (362) outside the 337').sum())} KHG. They touch a target village only at the edge, or hold damaged peat but no target village.
- **High-urgency KHG outside the 362 PPEG priorities:** {int(gaps.gap.str.startswith('high urgency').sum())}. Every KHG in the top third for urgency is already a PPEG priority.
- **KHG in the 337 with no peat on KLH's map:** {nwk}, scored with the whole KHG as peat and flagged. {int(gaps.gap.str.contains('not scored').sum())} remain unscored. **KHG in the 337 with less than {rule['min_peat_km2']} km² of peat:** {int(gaps.gap.str.contains('less than').sum())}, scored against the comparison group and flagged.
"""

    # --- 07 validation and robustness
    C["07_validation"] = f"""# 7 How reliable the results are

## {{n}} Test against the 2026 fires

![Share of the peat that burned in 2026 that falls in the most urgent KHG, using data up to 2025. Read from left to right: the further up the line, the more of the burned peat the top KHG hold. The dashed line marks the top fifth of KHG.]({figs['validation']})

Table: Test of the ranking against the peat that burned in 2026 ({V['n_pool']} KHG in the comparison group, {V['n_burned']} of which burned in 2026)

| Ranking | Share of 2026 burned peat in the top fifth of KHG | Chance that a KHG that burned ranks above one that did not |
|---|---|---|
| Urgency (without this year's fire detections) | {pc(V['urgency']['capture_top20pct'])} | {pc(V['urgency']['auc'])} |
| Past fires alone | {pc(V['fire_history_only']['capture_top20pct'])} | {pc(V['fire_history_only']['auc'])} |

The second column shows how well each ranking finds the KHG where most peat burned. The third shows how well it separates KHG that burned from KHG that did not: 50% would be no better than a coin toss, 100% perfect.

Urgency does best where it matters for planning. Its top fifth holds {pc(V['urgency']['capture_top20pct'] - V['fire_history_only']['capture_top20pct'])} points more of the 2026 burned peat than a ranking by past fires alone. The extra comes from damage and canal drainage, which flag KHG that had not burned much before. 2026 is a single fire season, so the test should be repeated each year.

## {{n}} Test against changes in the weights

![How often each KHG kept its type over {S['runs']} reruns in which every weight was changed at random by up to half.]({figs['stability']})

{pc(S['share_khg_type_stable_80pct'])} of the KHG in the comparison group kept their type in at least 4 out of 5 reruns (on average, a KHG kept its type in {pc(S['share_keeping_type_mean'])} of reruns). The typical KHG moved about {S['median_rank_sd']:.0f} places in the urgency ranking. The KHG that changed type are those close to a border between thirds. The dashboard and Annex B show this figure for each KHG, so readers can see where a type is a close call.

## {{n}} Known weaknesses

- **Feasibility is rough.** It uses distance to large rivers and roads and the dry-season water balance. The river maps hold only rivers wide enough to be drawn with two banks, and river levels in the dry season are not included. Detailed water and pump studies inside each KHG would improve it. For now it only adds a flag.
- **The label for what the peat needs rests partly on KLH layers we could not check:** the 2022 land cover map and the canal zones. The forest-change part comes from an independent satellite map, but that map cannot always tell natural regrowth from young plantation. The {rw_min}% and {rv_min}% thresholds are a judgement, to be confirmed with KLH.
- **Soil moisture is coarse** (pixels about 9 km wide), and few cloud-free Sentinel-2 images reach peat in the dry season. Both therefore have weight 0 or are reported only.
- **People and complexity overlap** (correlation {corr.loc['complexity','people']:.2f}): crowded KHG also tend to be contested. People only adds a flag.
- **Complexity is a minimum,** because customary claims, the indicative social forestry map, the newest permits and private land titles are missing (Chapter 4).
- **Stake relies on KLH's peat landform and thickness data,** which we could not check, and on peat area, which favours large KHG.
- **Small KHG** (less than {rule['min_peat_km2']} km² of peat) have unsteady shares: a few hectares can swing them. They are flagged.
"""

    # --- 08 next steps
    C["08_next"] = f"""# 8 Limitations and next steps

- **Agree the weights.** The weights are provisional. A short session with KLH and the World Bank, for example comparing the measures two at a time, would settle them. The report, dashboard and annex can then be updated with the agreed weights.
- **Fill the gaps in land claims.** A data request to the forestry ministry's SIGAP service (customary forest at 1:50,000, the indicative social forestry map, the December 2025 permit releases, the June 2026 forest estate map) and a request to BRWA for customary territory boundaries would complete the claims picture. Land title data from the national land agency (BPN) would add private claims.
- **Confirm KLH's layers.** Which forest estate release and licence date PPEG used, and the source maps of the 2022 land cover, the 2024 damage assessment and the peat landform and depth data, so that they can be checked like the others.
- **Move from KHG to sites.** For type A and B KHG, detailed work inside each KHG (water needs, canal blocks, pumps, layouts) turns the priority into designs. Its results can then replace the rough feasibility flag.
- **Update every year.** Rerun the ranking after each fire season and repeat the test on the new year's fires.

**Reproducibility.** Every figure in this report is calculated from the project's data and from rules that were written down and dated in advance. The analysis can be rerun for any KHG when data are updated or the weights are agreed.
"""

    # --- Annex A: layer register
    r = reg[["description", "theme", "producer", "version", "scale", "verification"]].copy()
    r["description"] = r.description.map(lambda x: re.sub(r"\s*\([^)]*[/.][a-z][^)]*\)", "", x.split(": ")[0]).strip())
    r["description"] = r.description.map(lambda x: x[:1].upper() + x[1:])
    r["producer"] = r.producer.map(lambda x: re.sub(r"\s*\((?:[^)]*(?:tools/|repeat|\.py|_)[^)]*)\)", "", x))
    r["producer"] = r.producer.map(lambda x: re.sub(r", public API .*$", "", re.sub(r", integrated thematic analysis$", "", x)))
    r["producer"] = r.producer.str.replace("this project", "RE-PEAT project", regex=False).str.replace(" (shared drive)", "", regex=False)
    r.columns = ["Layer", "Theme", "Producer", "Version", "Scale", "Verification"]
    C["90_annex_a"] = f"""# Annex A Layer register

This annex lists every map layer used in the ranking, with its theme, who made it, its version, its level of detail and whether we could check it. "Verified" means we checked it against an independent copy of its source. "Partly verified" means only some of its information could be checked. "Not verified" means no independent copy is available. "Source layer" means it is used as delivered, and "derived" means we calculated it from other layers. The full register, shared with the GIS package, also records each layer's legal basis, date received, terms of use, how it is used and the evidence for its check.

{md_table(r, "Registered layers")}"""
    C["91_annex_b"] = f"""# Annex B KHG profiles

The profiles of the {n337_sc} scored KHG in KLH's 337 work list are in a separate volume, one page per KHG, in the order of KLH's list. Each page shows the KHG's scores, its type and what its peat needs, six maps (peat depth and dome, damage, drainage, land cover, land claims, and fire and villages), its main measures next to the median of the comparison group, and the licence holders on its peat. Because they name licence holders, the profiles are shared with KLH and the World Bank only. A licence on a KHG is a land-status fact, not a statement about responsibility for fire or damage.
"""
    C["92_annex_c"] = annex_c(D, figs)
    return C


# ------------------------------------------------------------------------------------------------------------- annex C
EXAMPLE = "KHG.61.12-71.01"
LINKS = [
    ("CHIRPS daily rainfall (Climate Hazards Center, UC Santa Barbara)", "https://www.chc.ucsb.edu/data/chirps",
     "https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY"),
    ("MODIS MOD16A2GF evapotranspiration, 500 m (NASA LP DAAC)", "https://lpdaac.usgs.gov/products/mod16a2gfv061/",
     "https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD16A2GF"),
    ("JRC Tropical Moist Forest, annual change 1990-2024, 30 m (European Commission)", "https://forobs.jrc.ec.europa.eu/TMF",
     "https://developers.google.com/earth-engine/datasets/catalog/projects_JRC_TMF_v1_2024_AnnualChanges"),
    ("Hansen Global Forest Change v1.12, 30 m (University of Maryland)", "https://glad.earthengine.app/view/global-forest-change",
     "https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2024_v1_12"),
    ("Sentinel-2 surface reflectance, harmonized, 10-20 m (Copernicus)", "https://dataspace.copernicus.eu",
     "https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED"),
    ("Cloud Score+ cloud mask for Sentinel-2 (Google)", "https://doi.org/10.1109/CVPR52729.2023.00136",
     "https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_CLOUD_SCORE_PLUS_V1_S2_HARMONIZED"),
    ("SMAP L4 root-zone soil moisture, version 8, 9 km (NASA)", "https://nsidc.org/data/spl4smgp",
     "https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL4SMGP_008"),
    ("VIIRS and MODIS active fire detections (NASA FIRMS)", "https://firms.modaps.eosdis.nasa.gov",
     "https://developers.google.com/earth-engine/datasets/catalog/NASA_LANCE_NOAA20_VIIRS_C2"),
    ("TheTreeMap annual burned area of Indonesia 2019-2024, Sentinel-2, 20 m (CC BY 4.0)", "https://zenodo.org/records/19104282",
     "https://doi.org/10.1371/journal.pone.0331831"),
    ("IHME Populace population estimates 2025, 40 m (non-commercial licence)", "https://populace.healthdata.org", ""),
]


def fig_tc_example(D, out):
    import geopandas as gpd
    from matplotlib.colors import ListedColormap
    p = D["tex_pts"]
    g = gpd.read_file(DATA / "derived" / "khg_klh_priority.gpkg", layer="khg")
    g = g[g.khg_code == EXAMPLE]
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.6))
    cols = ["#e9e7df", "#cfe0c3", "#f2c57c", "#e0803a", "#a8321f"]
    cmap = ListedColormap(cols)
    k = np.clip(p.claims.to_numpy(), 0, 4)
    for ax in axs:
        g.boundary.plot(ax=ax, color="#" + STYLE.INK, linewidth=.7)
        ax.set_axis_off(); ax.set_aspect(1 / np.cos(np.radians(p.lat.mean())))
    axs[0].scatter(p.lon, p.lat, c=k, cmap=cmap, vmin=-.5, vmax=4.5, s=.35, marker="s", linewidths=0)
    axs[0].legend([plt.Rectangle((0, 0), 1, 1, color=c) for c in cols], ["0 claims", "1", "2", "3", "4 or more"],
                  loc="lower left", fontsize=7, frameon=False, ncol=5, bbox_to_anchor=(0, -.08))
    axs[0].set_title("(a) Number of claims at each peat point", loc="left", fontsize=9)
    lc = p.licence_community.to_numpy()
    axs[1].scatter(p.lon[~lc], p.lat[~lc], color="#e9e7df", s=.35, marker="s", linewidths=0)
    axs[1].scatter(p.lon[p.licence & ~lc], p.lat[p.licence & ~lc], color="#9fb6c9", s=.35, marker="s", linewidths=0)
    axs[1].scatter(p.lon[lc], p.lat[lc], color="#c0392b", s=.35, marker="s", linewidths=0)
    axs[1].legend([plt.Rectangle((0, 0), 1, 1, color=c) for c in ("#c0392b", "#9fb6c9", "#e9e7df")],
                  ["licence on community or DMPG land", "licence only", "no licence"], loc="lower left", fontsize=7, frameon=False, ncol=3,
                  bbox_to_anchor=(0, -.08))
    axs[1].set_title("(b) Points counted in 'licence on community land'", loc="left", fontsize=9)
    return save(fig, out / "tc_example.png")


def fig_dist_example(D, out):
    p = D["tex_pts"]
    fig, axs = plt.subplots(1, 2, figsize=(10, 2.6))
    for ax, c, lab in zip(axs, ["water_km", "road_km"], ["Distance to the nearest large river or lake (km)", "Distance to the nearest road (km)"]):
        v = p[c].to_numpy()
        ax.hist(v, bins=40, color="#" + STYLE.ACCENT, alpha=.8)
        m = float(np.median(v))
        ax.axvline(m, color="#" + STYLE.WARM, lw=1.4, ls="--")
        ax.text(m, ax.get_ylim()[1] * .92, f"  median {m:.2f} km", color="#" + STYLE.WARM, fontsize=8)
        ax.set_xlabel(lab); ax.set_ylabel("Peat points")
    return save(fig, out / "dist_example.png")


def field_table():
    """Source and calculation of every field, as on the dashboard's Method page (one definition for both)."""
    js = (WS / "repeat-prioritisation" / "src" / "repeat_prioritisation" / "national" / "assets" / "defs.js").read_text(encoding="utf-8")
    block = js[js.index("const FIELD_SRC={"):]
    block = block[:block.index("};") + 1]
    rows = re.findall(r'\n\s*(\w+):\["((?:[^"\\]|\\.)*)","((?:[^"\\]|\\.)*)"\]', block)
    names = dict(re.findall(r'\n\s*(\w+):\["((?:[^"\\]|\\.)*)",', js[js.index("const IND="):js.index("const FIELD_SRC")])) if "const IND=" in js else {}
    return pd.DataFrame([[k, names.get(k, ""), s, c] for k, s, c in rows], columns=["Field", "Name", "Source", "How it is calculated"])


def md_txt(v):
    """'04-01' -> '1 April'; 'end' and other values unchanged."""
    import calendar
    m = re.match(r"^(\d{2})-(\d{2})$", str(v))
    return f"{int(m.group(2))} {calendar.month_name[int(m.group(1))]}" if m else str(v)


def annex_c(D, figs):
    f, meta = D["f"], D["meta"]
    rule = meta["rule"]
    pool = f[f.in_pool]
    ex = f[f.khg_code == EXAMPLE].iloc[0]
    nm_ex = re.sub(r"^KHG\s+", "", re.sub(r"\s+", " ", ex.khg_name))

    def pct(x, ref):
        r = np.sort(pd.Series(ref).dropna().to_numpy())
        return (np.searchsorted(r, x, "left") + np.searchsorted(r, x, "right")) / 2 / len(r)

    def dim_example(dim):
        rows, num, den = [], 0.0, 0.0
        for k, s in rule["dimensions"][dim].items():
            w = s["weight"]
            v = ex.get(k, np.nan)
            sign = -1 if s.get("direction", "+") == "-" else 1
            if not w or pd.isna(v):
                rows.append([k, "n/a" if pd.isna(v) else f"{v:.4g}", "", fmt_w(w), "not counted" if not w else "missing: left out"])
                continue
            p = pct(sign * v, sign * pool[k])
            num += w * p; den += w
            rows.append([k, f"{v:.4g}", f"{p:.3f}", fmt_w(w), f"{w * p:.3f}"])
        return pd.DataFrame(rows, columns=["Field", "Value", "Percentile rank", "Weight", "Weight x rank"]), num, den

    fmt_w = lambda w: f"{w:g}"
    ut, un, ud = dim_example("urgency")
    ct, cn, cd = dim_example("complexity")
    cuts = meta["tercile_cuts"]
    note("annexc_urgency_check", (un / ud, float(ex.urgency)), "recomputed vs final_khg.csv")
    tc = D["tc"]
    tpool = tc[tc.peat_km2 >= 25]
    TCI = ["c_licence_community", "c_contested", "c_claims_mean", "c_holders"]
    tr = tpool[TCI].rank(pct=True, method="average")
    exr = tc[tc.khg_id == EXAMPLE].iloc[0]
    tci = tr.loc[tpool.khg_id == EXAMPLE].iloc[0]
    TCN = {"c_licence_community": "Share of peat under a licence that is also social-forestry or DMPG village land",
           "c_contested": "Share of peat where claims conflict", "c_claims_mean": "Mean number of claim types per point (0-6)",
           "c_holders": "Number of distinct licence holders on the peat"}
    tct = pd.DataFrame([[k, TCN[k], f"{exr[k]:.4g}", f"{tci[k]:.3f}"] for k in TCI], columns=["Field", "Indicator", "Value", "Percentile rank"])
    tex = D.get("tex_meta")
    av = D["av"].set_index("khg_code")
    a_ex = av.loc[EXAMPLE] if EXAMPLE in av.index else None
    bs = (NP / "final_inputs" / "burned_s2" / "calibration.json")
    burned_txt = ""
    if bs.exists():
        cal = json.loads(bs.read_text(encoding="utf-8"))
        g = pd.DataFrame(cal["grid"])[["dnbr_min", "post_max", "spearman_vs_klhk", "ha_jan_sep", "ha_year_to_date", "klhk_ha_to_15oct"]].round(3)
        g.columns = ["dNBR minimum", "Post-fire NBR maximum", "Spearman with KLHK 2026", "Burned peat Jan-Sep (ha)", "Burned peat to date (ha)", "KLHK to 15 Oct (ha)"]
        burned_txt = (md_table(g, f"Calibration of the burned-area thresholds against KLHK's 2026 burned area ({cal['n_khg']} scored KHG)")
                      + f"\nChosen: dNBR above {cal['chosen']['dnbr_min']} and post-fire NBR below {cal['chosen']['post_max']}.\n")
    else:
        burned_txt = "\nThe 2026 run was in progress when this edition was produced; its calibration table and totals will be added here.\n"
    links = pd.DataFrame([[a, b, c] for a, b, c in LINKS], columns=["Data", "Producer or download page", "Earth Engine catalogue or paper"])
    pts = D.get("tex_pts")
    tc_fig = f"![Worked example, {nm_ex}: the peat grid points and their land claims.]({figs['tc_example']})\n" if "tc_example" in figs else ""
    dist_fig = f"![Worked example, {nm_ex}: distance from every peat point to the nearest large river or lake and road. The dashed line is the median used as the KHG's value.]({figs['dist_example']})\n" if "dist_example" in figs else ""
    return f"""# Annex C Technical details

This annex is for readers who want to check or reproduce the analysis. It names the fields and settings used in the data tables, the GIS package and the configuration file, and works through one KHG, {nm_ex} ({EXAMPLE}), step by step. The numbers in the examples are computed from the same data as the results, by the same functions.

## {{n}} How the scores are calculated

**Percentile rank.** For an indicator x, a KHG's percentile rank is the share of the comparison group (the {meta['pool']} KHG with at least {rule['min_peat_km2']} km² of KLH peat) with a lower value, counting ties as half: rank = (L + R) / (2N), where L is the number of pool KHG with a lower value, R the number with a lower or equal value, and N the pool size. Where a lower value means more urgency or feasibility (direction "−": distances, soil moisture), the value is negated first. KHG outside the pool (the small KHG and the whole-KHG cases in the 337) are ranked against the pool's values without being added to it.

**Dimension score.** Each of the five dimensions is a weighted linear average of its indicators' percentile ranks: score = Σ(wᵢ × rankᵢ) / Σwᵢ, over the indicators the KHG has. An indicator with weight 0 is skipped; a missing indicator is left out of both sums, so the score is the average of the rest. The dimensions are not added together.

**Type.** Urgency, complexity and stake are cut at their terciles in the pool (the values below which one third and two thirds of the pool lie): urgency {cuts['urgency'][0]:.4f} and {cuts['urgency'][1]:.4f}, complexity {cuts['complexity'][0]:.4f} and {cuts['complexity'][1]:.4f}, stake {cuts['stake'][0]:.4f} and {cuts['stake'][1]:.4f}. High means at or above the upper cut, low below the lower cut. Then: A = high urgency and complexity below its upper cut; B = high urgency and complexity at or above it; C = medium urgency; D = low urgency and stake at or above its upper cut; E = low urgency and stake below it. Urgency is therefore not combined with complexity into one number: complexity only splits the high-urgency KHG into A and B, and stake splits the low-urgency KHG into D and E.

**Flags and ranks.** Low feasibility: feasibility below its lower tercile in the pool. High exposure: people at or above its upper tercile. Ranks are by urgency, highest first (ties share the best rank), among all scored KHG, among the 337 and within each type.

**Worked example: urgency of {nm_ex}.**

{md_table(ut, f"Urgency of {nm_ex}: values, percentile ranks in the pool and weights (rule as run on {meta.get('run', '')})")}
Urgency = {un:.3f} / {ud:g} = **{un / ud:.3f}** (reported: {ex.urgency:.3f}). This is {'at or above the upper cut' if ex.urgency >= cuts['urgency'][1] else 'between the cuts' if ex.urgency >= cuts['urgency'][0] else 'below the lower cut'}, so urgency is {'high' if ex.urgency >= cuts['urgency'][1] else 'medium' if ex.urgency >= cuts['urgency'][0] else 'low'}.

{md_table(ct, f"Complexity of {nm_ex}")}
Complexity = {cn:.3f} / {cd:g} = **{cn / cd:.3f}** (reported: {ex.complexity:.3f}), against the upper cut {cuts['complexity'][1]:.4f}. The KHG is type **{ex.type}**.

**Validation and sensitivity.** Validation: urgency is recomputed without this year's inputs and compared with KLHK's 2026 burned share of peat; reported are the share of 2026 burned peat in the top 20% of KHG, and the AUC (the probability that a KHG that burned is ranked above one that did not, from the rank-sum formula). Sensitivity: {D['val']['sensitivity']['runs']} runs, each multiplying every weight by an independent random factor between 0.5 and 1.5 (seed fixed in the configuration); for each KHG the share of runs keeping its type and the spread of its urgency rank.

## {{n}} Tenure complexity

**Grid.** Each KHG is covered by a regular grid of points in an Albers equal-area projection centred on Indonesia (standard parallels 8° S and 4° N, central meridian 118° E). The spacing is chosen per KHG so that a KHG has about 60,000 points: spacing = √(KHG area / 60,000), rounded to 50 m, at least 100 m. Only points on KLH peat are used. Each point stands for one grid cell, so shares are point counts divided by the number of peat points.

**Claims.** At each point six claim types are recorded as present or absent: (1) business licence (2025 licence map: oil palm plantations, forest utilisation licences PBPH and PPHTR, mining), (2) social forestry (community forest permits in the licence map, village forest, community plantation forest), (3) forest estate (Kawasan Hutan 2023, any function except APL), (4) DMPG village, (5) PPTPKH land (land held inside the forest estate that is being settled), (6) forest estate released for other uses.

**Indicators** (all on the KHG's peat points):
- c_licence_community: share of points with a licence and also social forestry or a DMPG village.
- c_contested: share of points with a licence on PPTPKH or social-forestry land, or forest estate on PPTPKH land.
- c_claims_mean: mean number of claim types per point (0 to 6).
- c_holders: number of distinct licence holders (company names in the licence map) with a licence on the peat.

**Index.** tenure_complexity = the average of the four indicators' percentile ranks among the KHG with at least 25 km² of peat (equal weights). It enters the complexity dimension with weight 2, next to the kinds of actor holding damaged peat and the number of villages.

**Worked example: {nm_ex}.** The KHG has {int(exr.points):,} peat points{f" at {tex['cell_m']:.0f} m spacing" if tex else ""} ({exr.peat_km2:,.1f} km² of peat). Licences cover {exr.share_licence:.1%} of the points, the forest estate {exr.share_forest_estate:.1%}, DMPG villages {exr.share_dmpg:.1%}, PPTPKH {exr.share_pptpkh:.1%} and social forestry {exr.share_community:.1%}; {exr.share_no_claim:.1%} of the points carry no claim and {exr.share_3plus_claims:.1%} three or more.

{tc_fig}
{md_table(tct, f"Tenure complexity indicators of {nm_ex}")}
Index = ({' + '.join(f'{tci[k]:.3f}' for k in TCI)}) / 4 = **{tci.mean():.3f}** (reported: {exr.tenure_complexity:.3f}). The indicator ranking highest is {TCN[tci.idxmax()].lower()} ({tci.max():.3f}); the lowest is {TCN[tci.idxmin()].lower()} ({tci.min():.3f}). A value of 0 still has a percentile rank above 0 when many KHG share it, because ties count as half.

## {{n}} Access, water balance and population

**Distances.** On the same peat points, the distance to the nearest feature is measured in World Mercator (EPSG:3395; scale error below 1.3% within 9° of the equator). Large rivers are those the national topographic map (RBI) draws with two banks, plus lakes and reservoirs; roads are the RBI classes toll road, arterial, collector, local and other roads (footpaths, railways and runways excluded). The KHG's value is the median over its peat points, so half the peat is closer than this. Where no feature lies within one degree (rivers) or half a degree (roads), 110 km or 55 km is used.

{dist_fig}
**Dry-season water balance (P − ET).** In Google Earth Engine, for every KHG (whole KHG, 500 m): rain is the sum of CHIRPS daily rainfall per dekad (10-day period; 36 per year), averaged over 2018-2025; evapotranspiration is MOD16A2GF (8-day sums × 0.1 mm), scaled to each dekad's length and averaged over the same years. The dry window is the 14 consecutive dekads (about 140 days, wrapping over the new year) with the largest total of ET minus rain. dry_balance_mm = rain minus ET summed over that window: negative means the dry season loses more water than it receives.{f" For {nm_ex} the window runs from {md_txt(a_ex.dry_first)} to {md_txt(a_ex.dry_last)} and the balance is {-a_ex.dry_shortfall_mm:.0f} mm." if a_ex is not None and not pd.isna(a_ex.dry_shortfall_mm) else ""}

**Population.** The IHME Populace 2025 (third quarter) grid gives people per 40 m cell in an equal-area projection. pop_on_peat is the sum of the cells whose centre lies inside the KHG's KLH peat polygons; pop_10km the sum over the KHG plus a 10 km buffer. For {nm_ex}: {ex.pop_on_peat:,.0f} people on the peat and {ex.pop_10km:,.0f} within 10 km.

## {{n}} Satellite products

The Earth Engine indicators are reduced over the KHG's KLH peat as drawn on the dashboard (simplified to about 120 m); the forest-change indicators use KLH's peat polygons on the 30 m forest-map grid. Where KLH shows no peat, the whole KHG is used.
- **Forest change (JRC TMF).** The December 2014 and December 2024 classes of the annual change collection are downloaded per KHG on their native 30 m grid. Other layers (KLH peat, PPEG land cover 2022, KLHK burned area) are burned onto the same grid (cell centres). forest_loss_2015 = peat cells forest or degraded in 2014 and deforested in 2024; burn recovery and reveg_share as defined in the field table below.
- **Hansen forest loss.** Tree cover ≥ 30% in 2000 and a loss year of 2015 to 2024, mean over the peat at 30 m.
- **Sentinel-2 NDVI and NDMI.** Median of the July-October 2025 images after the Cloud Score+ mask (cs_cdf ≥ 0.6); NDVI = (B8 − B4)/(B8 + B4), NDMI = (B8 − B11)/(B8 + B11); mean over the peat at 30 m; ndvi_low_share = share below 0.5.
- **SMAP soil moisture.** Mean root-zone soil moisture of July-October 2025, and its difference from the July-October mean of 2016-2024; at the product's 9 km cells (summarised at 11 km).

**Open data sources and where to obtain them:**

{chr(10).join(f"- {a}: {b}" + (f"; {c}" if c else "") for a, b, c in LINKS)}

## {{n}} Burned area 2026 from Sentinel-2

Method (rule written before any 2026 result; after Gaveau, Descals and Salim 2026 and KLHK's dNBR protocol), in Google Earth Engine, at 20 m, on peat only:
1. Sentinel-2 images with the Cloud Score+ mask; NBR = (B8 − B12)/(B8 + B12).
2. One composite per month: the median NBR and the 20th percentile NBR of the month's images.
3. For month m: before = median of the three previous monthly medians; after = the 20th percentile of month m; drop = before − after.
4. Burned in month m: drop above the threshold, after-NBR below its maximum, and a fire detection near the pixel in month m or the three months before (VIIRS S-NPP or NOAA-20, nominal or high confidence, within 500 m; MODIS, confidence ≥ 30, within 1 km).
5. The year's burned area is the union of the months; patches smaller than 6.25 ha (KLHK's minimum mapping unit) are removed.
6. Thresholds: ten pairs (drop 0.10 to 0.30, after-NBR below −0.10 or 0.10) are computed; the pair whose January-September burned share ranks the KHG most like KLHK's 2026 burned area (Spearman) is used. Totals are reported, not matched, because KLHK's map may miss burns.
7. u_burned_2026 = burned peat / peat; burned_2026_obs_share = share of the peat seen clear at least once (cloud and smoke gaps).
{burned_txt}
## {{n}} Every field

{md_table(field_table(), "Source and calculation of every field (the same definitions as the dashboard's Method page)")}
## {{n}} Reproducing the analysis

The code is in three public repositories of the RE-PEAT project (github.com/Re-Peat-Project): repeat-common (data fetchers), repeat-prioritisation (the national analysis) and re-peat (reports, layer register, tools); a Docker image (ghcr.io/re-peat-project/repeat-chain) contains the environment. Every setting (indicators, weights, thresholds, years, data paths relative to the data folder) is in one configuration file, national_profile.yaml, with each change dated. The data layers are listed with their sources in Annex A; KLH's own layers are shared with KLH directly. The national steps run in this order: profile (fire, damage, canals), PPEG summaries, tenure complexity, final inputs (access, people), forest cover, Earth Engine indicators, burned area 2026, then the final scoring, which writes the tables used in this report and the dashboard. Each step caches its results per KHG and can be rerun for a single KHG.
"""


# ------------------------------------------------------------------------------------------------------------- annex
def profile_png(row, geom, skeg, lic, out):
    import geopandas as gpd
    from matplotlib.patches import Patch
    fig = plt.figure(figsize=(7.2, 3.3))
    ax = fig.add_axes([0, 0, .55, 1])
    g = gpd.GeoSeries([geom], crs=4326)
    sk = skeg[skeg.khg == row.khg_name]
    colors = {"Tidak Rusak": "#cfe3d4", "Rusak Ringan": "#f2c57c", "Rusak Sedang": "#e8863a", "Rusak Berat": "#c0392b", "Rusak Sangat Berat": "#7b1c12"}
    for k, c in colors.items():
        s = sk[sk.skeg == k]
        if len(s):
            s.plot(ax=ax, color=c, linewidth=0, aspect=None)
    if lic is not None and len(lic):
        lic = lic[lic.geom_type.isin(["Polygon", "MultiPolygon"]) & ~lic.is_empty]
        if len(lic):
            lic.boundary.plot(ax=ax, color="#3d3d3d", linewidth=.4, linestyle=(0, (2, 1)), aspect=None)
    g.boundary.plot(ax=ax, color="#" + STYLE.INK, linewidth=.9, aspect=None)
    x0, y0, x1, y1 = geom.bounds
    pad = max(x1 - x0, y1 - y0) * .04
    ax.set_xlim(x0 - pad, x1 + pad); ax.set_ylim(y0 - pad, y1 + pad); ax.set_aspect(1 / np.cos(np.radians((y0 + y1) / 2))); ax.set_axis_off()
    ax.legend([Patch(color=c) for c in colors.values()] + [plt.Line2D([], [], color="#3d3d3d", lw=.6, ls="--")],
              ["Peat, not damaged", "Light damage", "Moderate", "Heavy", "Very heavy", "Licence boundary"],
              loc="upper left", bbox_to_anchor=(1.02, 0.14), fontsize=6, frameon=False, ncol=3)
    bx = fig.add_axes([.62, .22, .33, .52])
    labs = [lab for c, lab in DIM if hasattr(row, c)]
    vals = [getattr(row, c) for c, lab in DIM if hasattr(row, c)]
    bx.barh(labs[::-1], [0 if pd.isna(v) else v for v in vals[::-1]], color=TYC.get(row.type, "#999"), height=.55)
    bx.barh(labs[::-1], [1] * len(labs), color="#eeeeea", height=.55, zorder=0)
    for y, v in enumerate(vals[::-1]):
        bx.text(1.02, y, "n/a" if pd.isna(v) else f"{v:.2f}", va="center", fontsize=8)
    bx.set_xlim(0, 1); bx.set_xticks([0, .5, 1]); bx.tick_params(labelsize=8)
    bx.spines["left"].set_visible(False)
    fig.text(.62, .9, f"Type {row.type}", fontsize=15, weight="bold", color=TYC.get(row.type, "#333"))
    fig.text(.62, .81, TYN.get(row.type, ""), fontsize=10, color="#" + STYLE.INK)
    return save(fig, out)


def annex(D, outdir):
    import geopandas as gpd
    import shapely
    from docx.shared import Cm, Pt
    f = D["F"]
    s = f[f.klh_337 & f.type.notna()].sort_values("klh_337_no" if "klh_337_no" in f else "rank_urgency_337")
    kp = D["kp"].set_index("khg_code")
    s = s.assign(klh_no=s.khg_code.map(kp.klh_337_no)).sort_values("klh_no")
    khg = gpd.read_file(DATA / "derived" / "khg_klh_priority.gpkg", layer="khg").set_index("khg_code")
    pool = f[f.in_pool]
    med = {c: pool[c].median() for c in ("u_fire_freq", "u_hotspot", "damage_share", "canal_share", "thick3m_share", "dome_share", "protected_share",
                                         "c_licence_community", "c_contested", "share_pptpkh", "share_community",
                                         "water_dist_km", "road_dist_km", "pop_on_peat", "pop_10km", "open_share", "forest_share",
                                         "reveg_share", "burn_unrecovered_share", "forest_loss_2015", "ndvi_dry", "sm_root_dry") if c in pool}
    hold = D["hold"]
    av = D["av"].set_index("khg_code")
    PR.TITLE = "KHG profiles: KLH's 337 work list"
    PR.SUBTITLE = "Annex B to the national prioritisation of KHG for rewetting. Draft for discussion"
    b = PR.Builder()
    b.front()
    b.heading("B KHG profiles", 1)
    PR.runs(b.doc.add_paragraph(), "This annex has one page for each scored KHG in KLH's 337 work list, in the order of KLH's list. Six maps show peat depth and the peat dome; damage (KLH's 2024 assessment); drainage (land close enough to a canal to be drained, canals, large rivers, canal blocks already built); land cover in 2022; land claims (forest estate, business licences, social forestry, PPTPKH); and fire (how many times each place burned in 2015 to 2026, and this year's fire detections), with DMPG villages and roads. "
     "The five scores run from 0 to 1 and give the share of the comparison group (the KHG with enough peat to compare fairly) that the KHG beats: 0.8 means higher than 80% of them. The table gives each measure as a share of the KHG's peat unless a unit is shown, next to the median (the middle KHG of the comparison group). Greenness (NDVI) runs from −1 to 1; soil moisture is in m³ of water per m³ of soil. "
     "\"Type kept under weight changes\" is the share of 500 reruns, each with every weight changed at random by up to half, in which the KHG kept the same type. "
     "Licence holders and their areas come from KLH's PPEG analysis (April 2026). A licence on a KHG is a fact about who holds the land, not a statement about who caused fire or damage. Draft for discussion: the weights are provisional.", Pt(9.5))
    pdir = outdir / "profiles"
    sys.path.insert(0, str(Path(__file__).parent))
    import khg_profile_maps as KM          # six thematic maps per KHG, rendered in parallel (cached by file)
    errs = KM.render_all(list(s.khg_code), pdir, workers=int(os.environ.get("MAP_WORKERS", "3")))
    if errs:
        raise SystemExit(f"maps failed: {errs[:5]}")
    for i, r in enumerate(s.itertuples()):
        png = pdir / f"{r.khg_code}_maps.png"
        d = b.doc
        h = d.add_heading(f"{int(r.klh_no)}. {re.sub(r'^KHG\s+', '', r.khg_name)}", 2)
        h.paragraph_format.page_break_before = True
        p = d.add_paragraph()
        a = av.loc[r.khg_code] if r.khg_code in av.index else None
        ranks = f"rank {int(r.rank_urgency_337)} of the 337 by urgency, {int(r.rank_in_type)} in type {r.type}"
        PR.runs(p, f"{r.khg_code} · {r.provinces} · {r.island.replace('Pulau ', '')} · KLH team: {kp.loc[r.khg_code, 'klh_337_team']} · peat {n0(r.peat_km2)} km² · {ranks} · type kept under weight changes: {pc(r.type_stability) if not pd.isna(r.type_stability) else 'not tested (small KHG)'}"
                + (" · no peat in KLH's peat map: whole KHG used, less reliable" if getattr(r, "whole_khg", False) is True
                   else " · small peat area: less reliable" if not r.in_pool else "") + (" · low feasibility" if r.flag_low_feasibility else "")
                + (" · high exposure" if getattr(r, "flag_high_exposure", False) is True else "")
                + (f" · intervention: {IVN.get(r.intervention, 'n/a').lower()}" if isinstance(getattr(r, "intervention", None), str) else ""), Pt(8.5), PR.MUTED)
        sc = d.add_paragraph()
        PR.runs(sc, f"Type {r.type}, {TYN.get(r.type, '').lower()}. Scores (0 to 1): " + " · ".join(f"{lab.lower()} {getattr(r, c):.2f}" for c, lab in DIM if hasattr(r, c) and not pd.isna(getattr(r, c))), Pt(9))
        sc.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        pic = d.add_paragraph(); pic.add_run().add_picture(str(png), width=Cm(14.0))
        rows = [
            ["Peat burned per year (average 2015-2025)", pc(r.u_fire_freq, 2) if not pd.isna(r.u_fire_freq) else "n/a", pc(med["u_fire_freq"], 2)],
            ["Fire detections per km² of peat per year", f"{r.u_hotspot:.2f}" if not pd.isna(r.u_hotspot) else "n/a", f"{med['u_hotspot']:.2f}"],
            ["Peat rated damaged (KLH 2024)", pc(r.damage_share), pc(med["damage_share"])],
            ["Peat near canals (rewet if 20% or more)", pc(r.canal_share), pc(med["canal_share"])],
            *([["Needs replanting (revegetate if 20% or more) / burned, not regrown / forest lost since 2015", " / ".join(pc(getattr(r, c)) if not pd.isna(getattr(r, c)) else "n/a" for c in ("reveg_share", "burn_unrecovered_share", "forest_loss_2015")),
                " / ".join(pc(med[c]) for c in ("reveg_share", "burn_unrecovered_share", "forest_loss_2015"))]] if "reveg_share" in f else []),
            *([["Dry season 2025: greenness, NDVI / soil moisture (m³/m³)", f"{r.ndvi_dry:.2f} / " + (f"{r.sm_root_dry:.2f}" if not pd.isna(r.sm_root_dry) else "n/a") if not pd.isna(r.ndvi_dry) else "n/a",
                f"{med['ndvi_dry']:.2f} / {med['sm_root_dry']:.2f}"]] if "ndvi_dry" in f else []),
            ["Peat 3 m or deeper / on the dome / set aside for protection", f"{pc(r.thick3m_share)} / {pc(r.dome_share)} / {pc(r.protected_share)}",
             f"{pc(med['thick3m_share'])} / {pc(med['dome_share'])} / {pc(med['protected_share'])}"],
            ["Licence on community land / conflicting claims / social forestry / PPTPKH",
             (f"{pc(r.c_licence_community)} / {pc(r.c_contested)}" if not pd.isna(r.c_licence_community) else "n/a / n/a") + " / " + (f"{pc(r.share_community)} / {pc(r.share_pptpkh)}" if not pd.isna(r.share_community) else "n/a / n/a"),
             f"{pc(med['c_licence_community'])} / {pc(med['c_contested'])} / {pc(med['share_community'])} / {pc(med['share_pptpkh'])}"],
            *([["Distance to a large river or lake / to a road (km)", f"{r.water_dist_km:.1f} / {r.road_dist_km:.1f}" if not pd.isna(r.water_dist_km) else "n/a",
                f"{med['water_dist_km']:.1f} / {med['road_dist_km']:.1f}"],
               ["People on the peat / within 10 km", f"{n0(r.pop_on_peat)} / {n0(r.pop_10km)}" if not pd.isna(r.pop_on_peat) else "n/a",
                f"{n0(med['pop_on_peat'])} / {n0(med['pop_10km'])}"]] if "water_dist_km" in f else []),
            ["Damaged peat by holder: licence / licence and communities / forestry ministry / KLH (ha)",
             " / ".join(n0(x) for x in (r.priority_company_ha, r.priority_company_buffer_ha, r.priority_mofor_ha, r.priority_klh_ha)), ""],
        ]
        tbl(b, ["Measure", "This KHG", "Median KHG"], rows, [9.2, 3.6, 3.2])
        hh = hold[hold.khg_code == r.khg_code].sort_values(["damaged_ha", "peat_ha"], ascending=False)
        if len(hh):
            more = len(hh) - 5
            hrows = [[x.holder, x.licence, n0(x.peat_ha), n0(x.damaged_ha)] for x in hh.head(5).itertuples()]
            if more > 0:
                hrows.append([f"{more} more holders", "", n0(hh.peat_ha.iloc[5:].sum()), n0(hh.damaged_ha.iloc[5:].sum())])
            tbl(b, ["Licence holder", "Licence", "Peat (ha)", "Damaged peat (ha)"], hrows, [7.2, 4.0, 2.4, 2.4])
        else:
            PR.runs(b.doc.add_paragraph(), "No business licence on this KHG in the PPEG analysis.", Pt(8.5), PR.MUTED)
        dc = (("Peat extent: no peat in KLH's peat map; the whole KHG is used as peat, so the indicators are less reliable. " if getattr(r, "whole_khg", False) is True else "")
              + (f"Data for detailed design: elevation model (DeltaDTM) covers {pc(a.deltadtm_share)} of the KHG; peat depth from {a.peat_depth_source}; "
                 f"water-level loggers (SiTMAT): {int(a.stations_community + a.stations_concession)}." if a is not None else ""))
        np_ = b.doc.add_paragraph(); PR.runs(np_, dc, Pt(7.5), PR.MUTED); np_.paragraph_format.space_before = Pt(0); np_.paragraph_format.space_after = Pt(0)
        if i % 25 == 0:
            print(f"  profile {i + 1}/{len(s)}", flush=True)
    for q in b.doc.paragraphs:
        if q.style.name.startswith("Heading"):
            continue
    out = outdir / "RE-PEAT_KHG_prioritisation_annex_profiles.docx"
    b.doc.save(out)
    return out, len(s)


def tbl(b, header, rows, widths):
    from docx.shared import Cm, Pt
    from docx.enum.table import WD_TABLE_ALIGNMENT
    t = b.doc.add_table(rows=1, cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    PR.borders(t)
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""
        PR.runs(c.paragraphs[0], h, Pt(8)); [setattr(x, "bold", True) for x in c.paragraphs[0].runs]
        PR.shade(c, STYLE.ACCENT_SOFT)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            PR.runs(cells[i].paragraphs[0], str(v), Pt(8))
    t.autofit = False
    for row in t.rows:
        for c, w in zip(row.cells, widths):
            c.width = Cm(w)
            for q in c.paragraphs:
                q.paragraph_format.space_after = Pt(0); q.paragraph_format.line_spacing = 1.0; PR.sans(q)
    b.doc.add_paragraph().paragraph_format.space_after = Pt(0)


def drop_blank_before_chapters(doc):
    ps = doc.paragraphs
    for i in range(1, len(ps)):
        if ps[i].style.name != "Heading 1":
            continue
        ps[i].paragraph_format.page_break_before = True
        j = i - 1
        while j >= 0 and not ps[j].text.strip() and not ps[j]._p.xpath(".//w:drawing|.//w:fldChar|.//w:instrText|.//w:fldSimple"):
            ps[j]._p.getparent().remove(ps[j]._p)
            j -= 1


def draft_header(doc, text):
    from docx.shared import Pt
    for sec in doc.sections:
        hp = sec.header.paragraphs[0]
        PR.runs(hp, text, Pt(8), PR.WARM); PR.sans(hp)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=WS / "_exports" / "prioritisation_report")
    ap.add_argument("--no-annex", action="store_true")
    ap.add_argument("--annex-only", action="store_true")
    a = ap.parse_args(argv)
    out = a.out
    (out / "figures").mkdir(parents=True, exist_ok=True)
    setup_fig()
    D = load()
    stamp = f"DRAFT FOR DISCUSSION · {date.today():%d %B %Y} · weights provisional"
    if not a.annex_only:
        figs = {"map": fig_map(D, out / "figures"), "matrix": fig_matrix(D, out / "figures"), "types": fig_types(D, out / "figures"),
                "validation": fig_validation(D, out / "figures"), "stability": fig_stability(D, out / "figures"),
                "actors": fig_actors(D, out / "figures"), "dims": fig_dims(D, out / "figures"), "iv": fig_intervention(D, out / "figures")}
        if "tex_pts" in D:
            figs.update({"tc_example": fig_tc_example(D, out / "figures"), "dist_example": fig_dist_example(D, out / "figures")})
        figs = {k: v.as_posix() for k, v in figs.items()}
        C = chapters(D, figs)
        cdir = out / "chapters"
        cdir.mkdir(exist_ok=True)
        for g in cdir.glob("*.md"):
            g.unlink()
        for k, v in C.items():
            (cdir / f"{k}.md").write_text(v, encoding="utf-8")
        (out / "sources.md").write_text("# Sources of the numbers\n\n" + "\n".join(f"- `{k}` = {v!r}: {s}" for k, (v, s) in SRC.items()) + "\n", encoding="utf-8")
        PR.TITLE = "National prioritisation of KHG for rewetting"
        PR.SUBTITLE = "Data, method, analysis and results. Draft for discussion"
        b = PR.Builder()
        b.front()
        for k in sorted(C):
            b.markdown(C[k])
        drop_blank_before_chapters(b.doc)
        draft_header(b.doc, stamp)
        f1 = out / "RE-PEAT_KHG_prioritisation.docx"
        b.doc.save(f1)
        print(f"wrote {f1}; pending: {b.pending}")
    if not a.no_annex:
        f2, n = annex(D, out)
        b2 = None
        from docx import Document
        doc = Document(f2); draft_header(doc, stamp); doc.save(f2)
        print(f"wrote {f2} ({n} profiles)")


if __name__ == "__main__":
    main()
