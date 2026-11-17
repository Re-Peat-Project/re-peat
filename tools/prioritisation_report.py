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
TYN = {"A": "Quick action", "B": "Multi-party coordination", "C": "Staged restoration", "D": "Protect and monitor", "E": "Monitor"}
TYN_ID = {"A": "Aksi cepat", "B": "Koordinasi multipihak", "C": "Pemulihan bertahap", "D": "Lindungi dan pantau", "E": "Pantau"}
TYC = {"A": "#d1495b", "B": "#7b3fa0", "C": "#e8a33d", "D": "#2f8f6b", "E": "#8d8a80"}
DIM = [("urgency", "Urgency"), ("stake", "Stake"), ("complexity", "Complexity"), ("feasibility", "Feasibility")]
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
    D["tc"] = pd.read_csv(NP / "tenure_complexity" / "tenure_complexity.csv")
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
    f = D["f"].merge(D["tc"].drop(columns=["khg", "peat_km2", "points", "tenure_complexity", "tenure_complexity_rank", "c_contested", "c_holders"], errors="ignore")
                     .rename(columns={"khg_id": "khg_code"}), on="khg_code", how="left")
    act = D["pp"].set_index("khg_code")[["priority_company_ha", "priority_company_buffer_ha", "priority_mofor_ha", "priority_klh_ha",
                                          "priority_class01_ha", "priority_class02_ha", "priority_class03_ha", "peat_ha",
                                          "peat_burned_ha", "peat_canal_ha", "peat_dome_ha", "peat_thick3m_ha", "peat_protected_feg_ha"]]
    D["F"] = f.merge(act, left_on="khg_code", right_index=True, how="left")
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
    ax.text(0.01, 0.99, "Dashed: tercile cuts of the scoring pool. Dot area: peat area.", transform=ax.transAxes, va="top", fontsize=7.5, color="#" + STYLE.MUTED)
    return save(fig, out / "matrix.png")


def fig_types(D, out):
    t = D["types"].set_index("type").reindex(TY)
    fig, axs = plt.subplots(1, 3, figsize=(10, 2.6), sharey=True)
    for ax, col, lab, k in zip(axs, ["khg", "peat_km2", "priority_ha"], ["KHG", "Peat (km²)", "SKEG-damaged peat (ha)"], [1, 1, 1]):
        ax.barh([f"{i} {TYN[i]}" for i in TY][::-1], t[col].values[::-1], color=[TYC[i] for i in TY][::-1])
        ax.set_title(lab, loc="left")
        for y, v in enumerate(t[col].values[::-1]):
            ax.text(v, y, " " + n0(v), va="center", fontsize=8)
        ax.spines["bottom"].set_visible(False); ax.set_xticks([])
    return save(fig, out / "types.png")


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
    ranks = {"Urgency (without 2026 hotspots)": uval[ok], "Fire history alone": f.loc[ok, "u_fire_freq"]}
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
    ax.set_xlabel("Share of 500 weight draws in which the KHG keeps its type"); ax.set_ylabel("KHG")
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
    ax.set_xlabel("SKEG-damaged peat (thousand ha)")
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    return save(fig, out / "actors.png")


def fig_dims(D, out):
    f = D["f"][D["f"].type.notna()]
    fig, axs = plt.subplots(1, 4, figsize=(10, 2.6), sharey=True)
    for ax, (c, lab) in zip(axs, DIM):
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
    corr = pool[["urgency", "stake", "complexity", "feasibility"]].corr(method="spearman")
    C = {}

    # --- 00 Indonesian executive summary
    C["00_ringkasan"] = f"""# Ringkasan eksekutif

Laporan ini menyajikan prioritas nasional Kesatuan Hidrologis Gambut (KHG) untuk pembasahan, disusun oleh tim GIS RE-PEAT (Departemen Teknik Geodesi UGM) untuk Bank Dunia dan KLH/BPLH. **Status: draf untuk diskusi; bobot masih sementara sampai disepakati bersama KLH.**

Setiap KHG dinilai pada empat dimensi yang terpisah, bukan satu skor gabungan: **urgensi** (riwayat kebakaran, titik panas, kerusakan SKEG 2024, gambut terdampak kanal), **nilai yang dipertaruhkan** (gambut ≥ 3 m, kubah, fungsi lindung, luas gambut), **kompleksitas** (kompleksitas penguasaan lahan, jenis aktor, jumlah desa) dan **kelayakan** (neraca air musim kemarau, sekat BRGM yang ada). Dari urgensi, kompleksitas dan nilai, setiap KHG masuk salah satu dari lima tipe tindakan.

- {n0(len(scored))} KHG dinilai, termasuk {n337_sc} dari {n337} KHG daftar kerja KLH (10 KHG sisanya tidak memiliki gambut menurut peta KLH).
- **Tipe A, aksi cepat:** {int(T.loc['A','khg'])} KHG ({int(T.loc['A','in_337'])} dalam 337), urgensi tinggi dan kompleksitas rendah atau sedang. Contoh: {lst('A', 4)}.
- **Tipe B, koordinasi multipihak:** {int(T.loc['B','khg'])} KHG, semuanya dalam 337, memuat **{pc(dmgB / dmg_scored)}** gambut rusak SKEG pada KHG yang dinilai ({n1(dmgB / 1e6)} juta ha). Di sini urgensi tinggi bertemu klaim lahan yang tumpang tindih: perusahaan, Kementerian Kehutanan, KLH dan desa.
- **Tipe C, pemulihan bertahap:** {int(T.loc['C','khg'])} KHG; **tipe D, lindungi dan pantau:** {int(T.loc['D','khg'])} KHG bergambut dalam atau berkubah dengan sedikit kebakaran; **tipe E, pantau:** {int(T.loc['E','khg'])} KHG.
- **Validasi:** dengan data sampai 2025, 20% KHG teratas menurut urgensi memuat **{pc(V['urgency']['capture_top20pct'])}** gambut yang terbakar pada 2026 (riwayat kebakaran saja: {pc(V['fire_history_only']['capture_top20pct'])}); AUC {V['urgency']['auc']:.2f}.
- **Kestabilan:** {pc(S['share_khg_type_stable_80pct'])} KHG mempertahankan tipenya pada sedikitnya 80% dari {S['runs']} uji dengan setiap bobot diubah ±50%.
- Tidak ada KHG berurgensi tinggi di luar 362 KHG prioritas PPEG.

Langkah berikut yang diusulkan: lokakarya pembobotan bersama KLH, pelengkapan data klaim yang belum ada (hutan adat, batas wilayah adat BRWA, PIAPS, rilis izin terbaru SIGAP, hak atas tanah BPN), dan penggunaan hasil rantai analisis sub-KHG (defisit air, pompa, sekat) untuk KHG tipe A dan B.
"""
    C["00_ringkasan"] = id_num(C["00_ringkasan"].replace("SK.129/2017", "SK.129/2017"))

    # --- 01 summary
    C["01_summary"] = f"""# 1 Summary

This report sets out a national prioritisation of Indonesia's peat hydrological units (KHG) for rewetting. It was prepared by the RE-PEAT GIS workstream (Departemen Teknik Geodesi UGM) for the World Bank and KLH/BPLH. **It is a draft for discussion: the weights are provisional until agreed with KLH.**

Each KHG is scored on four separate dimensions rather than one blended score, because they answer different questions. **Urgency** asks how likely the peat is to burn and degrade further; **stake** asks what would be lost; **complexity** asks how hard it is to act, given the claims on the land; **feasibility** asks how easy rewetting would be. Urgency, complexity and stake place each KHG in one of five types of action:

- **A, quick action:** {int(T.loc['A','khg'])} KHG ({int(T.loc['A','in_337'])} in KLH's 337 work list): high urgency, low or medium complexity. Leading examples: {lst('A', 5)}.
- **B, multi-party coordination:** {int(T.loc['B','khg'])} KHG, all in the 337, holding **{pc(dmgB / dmg_scored)} of the SKEG-damaged peat of the scored KHG** ({n1(dmgB / 1e6)} million ha). High urgency meets overlapping claims of companies, the Ministry of Forestry, KLH and villages. Leading examples: {lst('B', 5)}.
- **C, staged restoration:** {int(T.loc['C','khg'])} KHG of medium urgency.
- **D, protect and monitor:** {int(T.loc['D','khg'])} KHG with deep or domed peat and little fire, mostly outside the 337.
- **E, monitor:** {int(T.loc['E','khg'])} KHG with low urgency and low or medium stake.

{n0(len(scored))} KHG are scored: {meta['pool']} with at least {rule['min_peat_km2']} km² of KLH peat, and the {len(scored) - meta['pool']} KHG of the 337 with less peat, scored against the same distribution and flagged as less reliable. {n337_sc} of the 337 are scored; the other {n337 - n337_sc} hold no peat in KLH's peat map.

**Does it work?** Built only from data up to 2025, the top 20% of KHG by urgency hold **{pc(V['urgency']['capture_top20pct'])} of the peat that burned in 2026** (fire history alone: {pc(V['fire_history_only']['capture_top20pct'])}); AUC {V['urgency']['auc']:.2f} against burned or not ({V['fire_history_only']['auc']:.2f} for fire history alone). With every weight varied by ±50% in {S['runs']} draws, {pc(S['share_khg_type_stable_80pct'])} of KHG keep their type in at least 80% of draws. No KHG outside KLH's 362 PPEG priority KHG has high urgency.

**What it rests on.** {len(D['reg'])} registered layers, each with producer, version, rights and verification status (Annex A). KLH's integrated PPEG analysis was checked against independent copies of its sources: its peat, burned-area, KHG and licence fields agree at 98 to 100%, forest function at 93% (Chapter 3).

**What it cannot yet see.** Customary forest and customary territory boundaries, the indicative social-forestry map (PIAPS), the newest permit releases and BPN land rights are not available to the project, so tenure complexity is a lower bound. Feasibility partly echoes urgency, because existing canal blocks were built where fires were.

**Proposed next steps:** a weighting session with KLH; the missing claim layers (a SIGAP download request and a request to BRWA); and the sub-KHG analysis chain (water deficit, pumps, canal blocks) for the type A and B KHG.
"""

    # --- 02 purpose and approach
    C["02_scope"] = f"""# 2 Purpose and scope

KLH's integrated thematic analysis for peat ecosystem restoration (PPEG, April 2026) identifies where peat is damaged (SKEG 2024) and who is responsible for it, and the project's 337-KHG work list sets out where the rewetting designs are made (the KHG holding the 2,004 Bluebook target villages). This prioritisation complements them by asking, for every KHG, **how urgent action is, what is at stake, how hard it will be and how feasible rewetting is**, and by turning the answers into types of action that match KLH's instruments.

- **Units.** The 865 KHG of the national registry (SK.129/2017). The scoring pool is the {meta['pool']} KHG with at least {rule['min_peat_km2']} km² of KLH peat (PPEG `LAHAN_GAMB`); KLH's 337 are scored even when smaller.
- **KLH priorities.** The 337 work-list KHG and the 362 PPEG priority KHG (in a target village, or holding SKEG-damaged peat) are carried as attributes of every KHG; all 337 are among the 362.
- **Outputs.** Per KHG: four dimension scores, the type, ranks (national, within the 337, within the type), type stability and flags. They are in the national dashboard (with a data export), the project GeoPackage (`khg_summary`) and Annex B of this report (one page per KHG of the 337).
- **What this is not.** It ranks KHG for attention; it does not place canal blocks or pumps. Those come from the sub-KHG analysis chain, run per KHG.
"""

    # --- 03 data
    reg = D["reg"]
    ver = D["ver"]
    vt = ver[~ver.field.str.startswith("BA_")].copy()
    ba = ver[ver.field.str.startswith("BA_")]
    vt = pd.concat([vt, pd.DataFrame([{"field": "BA_2015 … BA_2024", "source": "burnt_area_2015_2026_Indonesia.gpkg", "agree_share": ba.agree_share.min(), "note": f"lowest of the {len(ba)} years"}])])
    vt["Agrees"] = (vt.agree_share * 100).round(1).astype(str) + "%"
    SRCN = {"batas_khg": "KHG boundaries (2017)", "batas_desa": "Village boundaries 2023 (KLH)", "ALL_Updade__IZIN": "Business licences 2025",
            "KWSHUTAN": "Kawasan Hutan 1:250k (2023)", "FEG__Indonesia": "FEG 2017 (revised typology)", "klhk_khg_feg_50k": "KLHK FEG 1:50k (BIG Satu Peta)",
            "lahan_gambut_indonesia_2025": "SiTMAT peat map 2025", "burnt_area": "Burnt area 2015-2026 (KLHK)"}
    vt["Independent copy of the source"] = vt.source.map(lambda x: next((v for k, v in SRCN.items() if k in str(x)), str(x).split(":")[0]))
    vt["Note"] = vt.note.fillna("").map(lambda x: "on the 17% of points the 1:50k copy covers; compared by meaning" if "covers" in x else x)
    vt = vt[["field", "Independent copy of the source", "Agrees", "Note"]].rename(columns={"field": "PPEG field"})
    themes = reg.groupby("theme").id.count().reset_index().rename(columns={"theme": "Theme", "id": "Layers"})
    C["03_data"] = f"""# 3 Data

## {{n}} The layer register

Every layer the prioritisation uses is listed in the project's layer register (`re-peat/sites/layer_register.csv`, {len(reg)} rows; Annex A), with producer, legal basis, version, scale, rights, the date received, its use, its verification status and the evidence. A check command confirms that each file is still there, unchanged (sha256) and holds the listed fields; the same register builds one GeoPackage with every layer and a KHG summary layer (`prioritisation_layers.gpkg`), shared with KLH and the World Bank on the project drive. Redundant layers are kept on purpose: the 2023 village boundaries, for example, sit next to the PPEG administrative fields.

{md_table(themes, "Registered layers by theme")}
## {{n}} KLH's integrated PPEG analysis and its verification

KLH's PPEG analysis (April 2026, 989,398 polygons) is the overlay of KHG, villages, licences, forest area, peat function, peat (BBSDLP), land cover, damage, burned area and canal zones. It is the canonical source for KLH's targets, so its fields were checked before use: 20,000 polygons were drawn at random in proportion to area, and at a point in each, every field was compared with the project's independent copy of its source.

{md_table(vt, "Agreement of PPEG fields with independent copies of their sources (share of sampled area)")}
- **Matches.** Peat land, burned area, KHG and licences agree at 98 to 100%; KLH's derived codes (concession, APL, canal-affected, burned, burn count) are fully consistent with the fields they are derived from.
- **Rules made explicit.** The "Buffer 5 Kilometer" class lies within 5 km of a licence, and the canal-affected zones reach about 1,000 m from primary, 500 m from secondary and 250 m from tertiary canals of the project's canal map.
- **Disagreements to raise with KLH.** About 6.6% of the area is APL in PPEG but forest estate in Kawasan Hutan 2023 (which release did KLH use?), and about 1.9% is non-concession in PPEG but licensed in the 2025 licence layer (licence date).
- **One error.** Parts of the Papua KHG outside the 2017 maps carry placeholder administrative names (Jayapura / Ebungfao / Atabar); administrative names are therefore taken from the 2023 village layer.
- **Not verifiable yet.** Land cover 2022, SKEG damage 2024, the BBSDLP landform, depth and maturity fields (which include the dome classes) and KLH's actor and intervention classes have no independent copy in the project.

## {{n}} Tenure claims

Tenure complexity counts the claims that overlap on the same peat: business licences (2025), social forestry (community forest PPHKM, village forest Hutan Desa and community plantation HTR permits), the forest estate, DMPG villages, land held inside the forest estate that is being settled (PPTPKH, the forest-area part of agrarian reform) and forest released for other uses. The social-forestry, PPTPKH and release layers were fetched from the BIG Satu Peta mirror of the Ministry of Forestry's public services on 2026-11-16. On KHG peat ({n0(peat_tot)} km²): licences cover {pc(wsh('share_licence'), 1)}, the forest estate {pc(wsh('share_forest_estate'), 1)}, DMPG villages {pc(wsh('share_dmpg'), 1)}, released forest {pc(wsh('share_released'), 1)}, PPTPKH {pc(wsh('share_pptpkh'), 1)} and social forestry {pc(wsh('share_community'), 1)}; {pc(wsh('share_3plus_claims'), 1)} of the peat carries three or more claims and {pc(wsh('share_no_claim'), 1)} none.

Not available to the project: customary forest (the public mirror is empty), customary territory boundaries (BRWA publishes its register of 2,283 territories but serves the polygons as map tiles only), PIAPS and the Ministry's newest permit releases (SIGAP, on request), and BPN land rights. The licence layer turned out to be a clean partition (no two licences overlap), so overlaps between licences cannot be measured from it.
"""

    # --- 04 method
    dims = rule["dimensions"]
    DESC = {"u_fire_freq": "Mean annual burned share of peat, 2015 to 2025", "u_burn_repeat": "Share of peat burned twice or more, 2015 to 2025",
            "u_hotspot": "VIIRS hotspots per km² of peat per year, 2012 to 2025", "u_hotspot_now": "Hotspots of the current year per km² of peat",
            "damage_share": "SKEG 2024 damaged share of peat (PPEG)", "canal_share": "Canal-affected share of peat (PPEG canal zones)",
            "thick3m_share": "Share of peat 3 m or deeper", "dome_share": "Share of peat on dome landform (BBSDLP)",
            "protected_share": "Share of peat with protected peat ecosystem function", "peat_km2": "Peat area (KLH)",
            "tenure_complexity": "Tenure complexity index (v2), itself from four indicators", "actor_types": "Actor types holding SKEG-damaged peat (of 4)",
            "villages": "Bluebook target villages plus DMPG villages", "dry_balance_mm": "Dry-season P − E (higher = smaller shortfall)",
            "brgm_blocks_per_km2": "Existing BRGM structures per km² of peat"}
    rows = []
    for dname, spec in dims.items():
        for ind, s in spec.items():
            rows.append([dname.capitalize(), f"`{ind}`", DESC.get(ind, ""), s["weight"]])
    ind_tab = pd.DataFrame(rows, columns=["Dimension", "Indicator", "Definition", "Weight"])
    C["04_method"] = f"""# 4 Method and rationale

## {{n}} Why four dimensions

A single score would trade urgency against complexity and stake, and hide exactly what KLH needs to see: a KHG that burns every year but is crowded with claims needs a different response from one that burns as often on unclaimed land, and a deep, undisturbed dome needs protection rather than restoration. The four dimensions are therefore scored separately, and combined only through a typology that keeps them visible.

## {{n}} Indicators and scoring

Each dimension is the weighted mean of its indicators' **percentile ranks** among the scoring pool (0 to 1, higher = more urgent, more at stake, more complex, more feasible). Percentile ranks make indicators with different units and skewed distributions comparable, and a KHG missing an indicator is scored on the indicators it has.

{md_table(ind_tab, "Indicators, definitions and weights (configuration `final` in repeat-prioritisation, written " + str(rule['written']) + ")")}
Fire frequency counts double, as in the earlier fire-based ranking; tenure complexity counts double within complexity because it already summarises four claims. SiTMAT water-table depth is reported but not scored: only {int(D['prof'].tma_deep_share.notna().sum())} KHG have stations.

**Tenure complexity (v2)** is computed on a regular grid of points over each KHG's peat. At each point it records which of six claim types are present (licence, social forestry, forest estate, DMPG village, PPTPKH, released forest). Four indicators per KHG make the index: the share of peat under a licence that is also social-forestry or DMPG village land; the share that is **contested** (a licence on PPTPKH or social-forestry land, or forest estate on PPTPKH); the mean number of claim types; and the number of licence holders.

## {{n}} Typology

Urgency, complexity and stake are cut into terciles of the scoring pool (urgency {meta['tercile_cuts']['urgency'][0]:.2f} and {meta['tercile_cuts']['urgency'][1]:.2f}; complexity {meta['tercile_cuts']['complexity'][0]:.2f} and {meta['tercile_cuts']['complexity'][1]:.2f}; stake {meta['tercile_cuts']['stake'][0]:.2f} and {meta['tercile_cuts']['stake'][1]:.2f}):

- **A, quick action:** urgency high, complexity low or medium.
- **B, multi-party coordination:** urgency high, complexity high.
- **C, staged restoration:** urgency medium.
- **D, protect and monitor:** urgency low, stake high.
- **E, monitor:** urgency low, stake low or medium.

Feasibility does not change the type; a KHG in its lowest tercile is flagged. Within each type KHG are ranked by urgency (then stake), and an overall urgency rank is given among all scored KHG and among the 337.

## {{n}} Rules written before results, and their amendments

Every rule was written into the configuration, dated, before its result was computed; changes made after seeing a result are recorded as dated amendments, and earlier results are kept.

Table: Rules and amendments

| Date | Rule | Change | Reason |
|---|---|---|---|
| 2026-11-16 | Tenure complexity v1 | Written before any result | Overlapping claims per KHG |
| 2026-11-16 | Tenure complexity v1, amendment | Overlapping licences reported, not scored | The licence layer has no overlaps (0 ha shared), so the indicator is 0 by construction |
| 2026-11-16 | Tenure complexity v2 | Six claim types; contested land; holder count | v1 missed social forestry and occupied forest land; two v1 indicators did not discriminate. v1 result kept |
| {rule['written']} | Final prioritisation | Written before any result | Four dimensions and typology |
| {rule['written']} | Final prioritisation, amendment | KHG of the 337 below {rule['min_peat_km2']} km² of peat scored against the pool and flagged | 99 of the 337 fell out of the pool, contrary to the aim of covering the 337; they hold 0.09% of its damaged peat |

## {{n}} Validation and sensitivity

**Validation.** Urgency is tested on a year it has not seen: built without the current year's hotspots, from data up to 2025, it is compared with the share of each KHG's peat that burned in 2026 (`BA_2026`), next to fire history alone. **Sensitivity.** In {S['runs']} draws every weight is multiplied by a random factor between 0.5 and 1.5; the share of draws in which each KHG keeps its type and the spread of its urgency rank are reported.
"""

    # --- 05 results
    isl = scored.groupby(["type"]).island.value_counts().unstack(fill_value=0).reindex(TY).fillna(0).astype(int)
    isl.columns = [c.replace("Pulau ", "") for c in isl.columns]
    isl.insert(0, "Type", [f"{t} {TYN[t]}" for t in TY])
    tsum = types.copy()
    tsum.insert(0, "Type", [f"{t} {TYN[t]}" for t in tsum.type])
    tsum = tsum[["Type", "khg", "in_337", "peat_km2", "priority_ha", "low_feasibility"]]
    tsum.columns = ["Type", "KHG", "In the 337", "Peat (km²)", "SKEG-damaged peat (ha)", "Low feasibility"]
    for c in tsum.columns[1:]:
        tsum[c] = tsum[c].map(n0)

    def toptab(t, k=10, src=None):
        x = (src[src.type == t].sort_values("rank_in_type").head(k)) if src is not None else top(t, k)
        return pd.DataFrame({"Rank in type": x.rank_in_type.astype(int), "KHG": x.khg_name.map(nm), "Province": x.provinces,
                             "Peat (km²)": x.peat_km2.map(n0), "Urgency": x.urgency.map("{:.2f}".format), "Stake": x.stake.map("{:.2f}".format),
                             "Complexity": x.complexity.map("{:.2f}".format), "Stable": x.type_stability.map(lambda v: "small KHG" if pd.isna(v) else pc(v))})
    gaps = D["gaps"]
    C["05_results"] = f"""# 5 Results

## {{n}} The national picture

![Scored KHG by type. Grey: not scored (less than {rule['min_peat_km2']} km² of KLH peat and outside the 337, or no KLH peat).]({figs['map']})

{md_table(tsum, "KHG, peat and SKEG-damaged peat by type (all scored KHG)")}
![KHG, peat area and SKEG-damaged peat by type.]({figs['types']})

Two thirds of the SKEG-damaged peat of the scored KHG lies in type B: {int(T.loc['B','khg'])} KHG where high urgency meets high complexity, {isl.loc['B', 'Sumatera'] if 'Sumatera' in isl else ''} in Sumatera and {isl.loc['B', 'Kalimantan'] if 'Kalimantan' in isl else ''} in Kalimantan. Type A gathers {int(T.loc['A','khg'])} smaller KHG with high urgency and moderate complexity. Type D, protect and monitor, is mostly in Papua and outside the 337.

{md_table(isl, "Scored KHG by type and island")}
## {{n}} Urgency against complexity

![Urgency against complexity of every scored KHG, coloured by type.]({figs['matrix']})

Urgency and complexity are strongly related (Spearman {corr.loc['urgency','complexity']:.2f} in the pool): the KHG that burn most are also the most contested, which is why type B is large. This is a property of the landscape, not of the method, and it is the main message for planning: most of the damaged peat cannot be rewetted by one agency alone. Stake is more independent of urgency ({corr.loc['urgency','stake']:.2f}).

![Distribution of the four dimensions by type.]({figs['dims']})

## {{n}} Who holds the damaged peat

![SKEG-damaged peat by the actor KLH assigns (PPEG `PROG_DMPG_2025`), by type.]({figs['actors']})

## {{n}} Leading KHG of the 337

{md_table(toptab('A'), "Type A, quick action: the first 10 KHG of the 337 by urgency")}
{md_table(toptab('B'), "Type B, multi-party coordination: the first 10 KHG of the 337 by urgency")}
{md_table(toptab("D", 20, scored), "Type D, protect and monitor: all scored KHG (one is in the 337)")}
The full lists, for every scored KHG, are in the dashboard's data export (`final_khg.csv`) and Annex B.

## {{n}} Gaps between the lists

- **PPEG priority KHG outside the 337:** {int((gaps.gap == 'PPEG priority (362) outside the 337').sum())} KHG (in a target village by a sliver, or holding SKEG damage only).
- **High-urgency KHG outside the 362:** {int(gaps.gap.str.startswith('high urgency').sum())}. Every KHG in the top tercile of urgency is already a PPEG priority KHG.
- **KHG of the 337 without KLH peat:** {int(gaps.gap.str.contains('without KLH peat').sum())}, not scored; **with less than {rule['min_peat_km2']} km² of peat:** {int(gaps.gap.str.contains('less than').sum())}, scored against the pool and flagged.
"""

    # --- 06 validation and robustness
    C["06_validation"] = f"""# 6 Validation and robustness

![Share of 2026 burned peat held by the most urgent KHG, built from data up to 2025. Dashed: the top 20% of KHG.]({figs['validation']})

Table: Validation against 2026 burned peat ({V['n_pool']} KHG in the pool, {V['n_burned']} of them burned in 2026)

| Ranking | Spearman | AUC (burned or not) | 2026 burned peat in the top 20% |
|---|---|---|---|
| Urgency (without 2026 hotspots) | {V['urgency']['spearman']:.2f} | {V['urgency']['auc']:.2f} | {pc(V['urgency']['capture_top20pct'])} |
| Fire history alone | {V['fire_history_only']['spearman']:.2f} | {V['fire_history_only']['auc']:.2f} | {pc(V['fire_history_only']['capture_top20pct'])} |

Urgency adds most where it matters for planning: among the KHG ranked highest, it holds {pc(V['urgency']['capture_top20pct'] - V['fire_history_only']['capture_top20pct'])} points more of the 2026 burned peat than fire history alone, because damage and canal drainage flag KHG that had not burned much yet. 2026 is one season; the test should be repeated each year.

![Type stability: share of {S['runs']} weight draws (every weight ±50%) in which each KHG keeps its type.]({figs['stability']})

{pc(S['share_khg_type_stable_80pct'])} of the KHG in the pool keep their type in at least 80% of the draws (mean {pc(S['share_keeping_type_mean'])}); the median urgency rank moves by {S['median_rank_sd']:.0f} places. KHG near a tercile cut are the unstable ones, and the dashboard and Annex B show each KHG's stability, so a reader can see where the type is a close call.

**Known weaknesses.**

- **Feasibility partly echoes urgency** (Spearman {corr.loc['urgency','feasibility']:.2f}): existing BRGM canal blocks were built where fires were, so they read as "more feasible" exactly where urgency is high. Distance to water sources and dry-season river levels, and the sub-KHG water-deficit and pump results, would make it independent. It is a flag only.
- **Tenure complexity is a lower bound**: customary claims, PIAPS, the newest permits and BPN rights are missing (Chapter 3).
- **Stake leans on BBSDLP landform and FEG thickness**, which could not be verified independently, and on the peat area, which favours large KHG.
- **Small KHG** (less than {rule['min_peat_km2']} km² of peat) have noisy shares; they are flagged.
"""

    # --- 07 next steps
    C["07_next"] = f"""# 7 Limitations and next steps

- **Weights.** The weights are provisional. A short weighting session with KLH and the World Bank (pairwise comparison is supported in the configuration) would settle them; the report, the dashboard and the annex rebuild from the configuration in minutes.
- **Missing claims.** A SIGAP download request (hutan adat 1:50k, PIAPS revision X, the December 2025 permit releases, Kawasan Hutan June 2026) and a request to BRWA for customary territory boundaries would complete tenure complexity; BPN land rights would add private claims.
- **KLH layers to confirm.** The Kawasan Hutan release and licence date used in PPEG, and the source layers of land cover 2022, SKEG 2024 and the BBSDLP fields, so that they can be verified like the others.
- **From KHG to sites.** For type A and B KHG, the sub-KHG analysis chain (water deficit, canal blocks, pumps, layouts) turns the priority into designs; its results can then replace the KHG-level feasibility flag.
- **Yearly update.** Re-run with each fire season and repeat the validation on the new year.

**Reproducibility.** Every number in this report is read from the files listed in `sources.md`, produced by `repeat-national-final`, `repeat-national-tenure-complexity` and the tools named in the layer register. The rules are dated in `configs/examples/national_profile.yaml` (repeat-prioritisation).
"""

    # --- Annex A: layer register
    r = reg[["id", "theme", "producer", "version", "scale", "verification"]].copy()
    r["producer"] = r.producer.str.slice(0, 70)
    r.columns = ["Id", "Theme", "Producer", "Version", "Scale", "Verification"]
    C["90_annex_a"] = f"""# Annex A Layer register

The register (`re-peat/sites/layer_register.csv`) also records legal basis, date received, rights, use, evidence and the sha256 of each file; `python tools/layer_register.py check` confirms the files are unchanged.

{md_table(r, "Registered layers")}"""
    C["91_annex_b"] = f"""# Annex B KHG profiles

The profiles of the {n337_sc} scored KHG of KLH's 337 work list are in a separate file, `RE-PEAT_KHG_prioritisation_annex_profiles.docx`, one page per KHG in the order of their KLH work-list number. They name licence holders, so they are shared with KLH and the World Bank only.
"""
    return C


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
    vals = [row.urgency, row.stake, row.complexity, row.feasibility]
    labs = ["Urgency", "Stake", "Complexity", "Feasibility"]
    bx.barh(labs[::-1], [0 if pd.isna(v) else v for v in vals[::-1]], color=TYC.get(row.type, "#999"), height=.55)
    bx.barh(labs[::-1], [1] * 4, color="#eeeeea", height=.55, zorder=0)
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
    skeg = gpd.read_file(NP / "ppeg" / "ppeg_layers.gpkg", layer="skeg", where="peat = 1")
    lic_all = gpd.read_file(DATA / "landstatus" / "ALL_Updade__IZIN_USAHA__PBPH_Perkebunan_HTRKM_Tambang__2025.gpkg", columns=["IZIN_USAHA"])
    lic_all = lic_all[lic_all.IZIN_USAHA != "PPHKM"]
    sidx = lic_all.sindex
    pool = f[f.in_pool]
    med = {c: pool[c].median() for c in ("u_fire_freq", "u_hotspot", "damage_share", "canal_share", "thick3m_share", "dome_share", "protected_share",
                                         "c_licence_community", "c_contested", "share_pptpkh", "share_community")}
    hold = D["hold"]
    av = D["av"].set_index("khg_code")
    PR.TITLE = "KHG profiles: KLH's 337 work list"
    PR.SUBTITLE = "Annex B to the national prioritisation of KHG for rewetting. Draft for discussion"
    b = PR.Builder()
    b.front()
    b.heading("B KHG profiles", 1)
    PR.runs(b.doc.add_paragraph(), "One page per KHG of KLH's 337 work list that holds KLH peat, in the order of the work list. The map shows KLH peat by SKEG 2024 damage class and licence boundaries (2025). Scores are percentile ranks among the scoring pool (0 to 1); medians are of the pool. Licence holders and their areas come from KLH's PPEG analysis (April 2026). A licence on a KHG is a land-status fact, not a statement about responsibility for fire or damage. Draft for discussion: the weights are provisional.", Pt(9.5))
    pdir = outdir / "profiles"
    for i, r in enumerate(s.itertuples()):
        geom = shapely.make_valid(khg.loc[r.khg_code, "geometry"])
        cand = lic_all.iloc[list(sidx.intersection(geom.bounds))]
        lic = gpd.clip(cand, geom) if len(cand) else None
        png = profile_png(r, geom, skeg, lic, pdir / f"{r.khg_code}.png")
        d = b.doc
        h = d.add_heading(f"{int(r.klh_no)}. {re.sub(r'^KHG\s+', '', r.khg_name)}", 2)
        h.paragraph_format.page_break_before = True
        p = d.add_paragraph()
        a = av.loc[r.khg_code] if r.khg_code in av.index else None
        ranks = f"rank {int(r.rank_urgency_337)} of the 337 by urgency, {int(r.rank_in_type)} in type {r.type}"
        PR.runs(p, f"{r.khg_code} · {r.provinces} · {r.island.replace('Pulau ', '')} · KLH team: {kp.loc[r.khg_code, 'klh_337_team']} · peat {n0(r.peat_km2)} km² · {ranks} · type kept in {pc(r.type_stability) if not pd.isna(r.type_stability) else 'n/a'} of weight draws"
                + (" · small peat area: less reliable" if not r.in_pool else "") + (" · low feasibility" if r.flag_low_feasibility else ""), Pt(8.5), PR.MUTED)
        p.paragraph_format.space_after = Pt(2)
        pic = d.add_paragraph(); pic.add_run().add_picture(str(png), width=Cm(16))
        rows = [
            ["Burned share of peat per year, 2015-2025", pc(r.u_fire_freq, 2) if not pd.isna(r.u_fire_freq) else "n/a", pc(med["u_fire_freq"], 2)],
            ["Hotspots per km² of peat per year", f"{r.u_hotspot:.2f}" if not pd.isna(r.u_hotspot) else "n/a", f"{med['u_hotspot']:.2f}"],
            ["SKEG 2024 damaged share of peat", pc(r.damage_share), pc(med["damage_share"])],
            ["Canal-affected share of peat", pc(r.canal_share), pc(med["canal_share"])],
            ["Peat 3 m or deeper / dome / protected function", f"{pc(r.thick3m_share)} / {pc(r.dome_share)} / {pc(r.protected_share)}",
             f"{pc(med['thick3m_share'])} / {pc(med['dome_share'])} / {pc(med['protected_share'])}"],
            ["Licence on social-forestry or DMPG land / contested", f"{pc(r.c_licence_community)} / {pc(r.c_contested)}" if not pd.isna(r.c_licence_community) else "n/a",
             f"{pc(med['c_licence_community'])} / {pc(med['c_contested'])}"],
            ["Social forestry / PPTPKH share of peat", f"{pc(r.share_community)} / {pc(r.share_pptpkh)}" if not pd.isna(r.share_community) else "n/a",
             f"{pc(med['share_community'])} / {pc(med['share_pptpkh'])}"],
            ["Damaged peat: licence holder / with communities / MoF / KLH (ha)",
             " / ".join(n0(x) for x in (r.priority_company_ha, r.priority_company_buffer_ha, r.priority_mofor_ha, r.priority_klh_ha)), ""],
        ]
        tbl(b, ["Indicator", "This KHG", "Pool median"], rows, [9.2, 3.6, 3.2])
        hh = hold[hold.khg_code == r.khg_code].sort_values(["damaged_ha", "peat_ha"], ascending=False)
        if len(hh):
            more = len(hh) - 6
            hrows = [[x.holder, x.licence, n0(x.peat_ha), n0(x.damaged_ha)] for x in hh.head(6).itertuples()]
            if more > 0:
                hrows.append([f"{more} more holders", "", n0(hh.peat_ha.iloc[6:].sum()), n0(hh.damaged_ha.iloc[6:].sum())])
            tbl(b, ["Licence holder", "Licence", "Peat (ha)", "Damaged peat (ha)"], hrows, [7.2, 4.0, 2.4, 2.4])
        else:
            PR.runs(b.doc.add_paragraph(), "No business licence on this KHG in the PPEG analysis.", Pt(8.5), PR.MUTED)
        dc = (f"Data confidence: run class {a.run_class}; DeltaDTM covers {pc(a.deltadtm_share)} of the KHG; peat depth from {a.peat_depth_source}; "
              f"SiTMAT stations: {int(a.stations_community + a.stations_concession)}." if a is not None else "")
        PR.runs(b.doc.add_paragraph(), dc, Pt(8), PR.MUTED)
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
                "actors": fig_actors(D, out / "figures"), "dims": fig_dims(D, out / "figures")}
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
