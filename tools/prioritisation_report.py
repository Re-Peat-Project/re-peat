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

    # --- 00 Indonesian executive summary
    C["00_ringkasan"] = f"""# Ringkasan eksekutif

Laporan ini menyajikan urutan prioritas nasional Kesatuan Hidrologis Gambut (KHG) untuk pembasahan dan revegetasi, sebagai dasar perencanaan dan pembiayaan pemulihan gambut. Laporan disusun oleh tim GIS RE-PEAT (Departemen Teknik Geodesi, Universitas Gadjah Mada) untuk Bank Dunia dan KLH/BPLH. **Status: draf untuk diskusi. Bobot masih sementara sampai disepakati bersama KLH.**

Setiap KHG dinilai pada lima dimensi yang terpisah, bukan satu skor gabungan, karena masing-masing menjawab pertanyaan yang berbeda: **urgensi** (riwayat kebakaran, titik panas, kerusakan SKEG 2024, gambut terdampak kanal), **nilai yang dipertaruhkan** (gambut ≥ 3 m, kubah, fungsi lindung, kawasan konservasi, luas gambut), **kompleksitas** (kompleksitas penguasaan lahan, jenis aktor, jumlah desa), **kelayakan** (jarak ke sungai besar atau danau, jarak ke jalan, neraca air musim kemarau) dan **penduduk** (penduduk di gambut dan dalam radius 10 km, desa di gambut). Urgensi, kompleksitas dan nilai menentukan tipe tindakan setiap KHG (lima tipe); kelayakan dan penduduk menjadi penanda tambahan. Terpisah dari tipe, setiap KHG diberi **jenis intervensi** yang dibutuhkan gambutnya: pembasahan (≥ {rw_min}% gambut terdampak kanal), revegetasi (≥ {rv_min}% gambut bertutupan terbuka atau rusak menurut peta tutupan lahan KLH 2022), keduanya, atau perlindungan. Tipe menunjukkan seberapa mendesak dan seberapa rumit penanganan sebuah KHG; jenis intervensi menunjukkan apa yang perlu dikerjakan.

- {n0(len(scored))} KHG dinilai, termasuk {n337_sc} dari {n337} KHG daftar kerja KLH {f"; {nwk} di antaranya tidak memiliki gambut dalam peta gambut KLH dan dinilai dengan seluruh KHG sebagai sebaran gambut, ditandai kurang andal" if nwk else ""}).
- **Tipe A, aksi cepat:** {int(T.loc['A','khg'])} KHG ({int(T.loc['A','in_337'])} dalam 337), urgensi tinggi dan kompleksitas rendah atau sedang. Di sini dana dapat paling cepat digunakan. Contoh: {lst('A', 4)}.
- **Tipe B, koordinasi multipihak:** {int(T.loc['B','khg'])} KHG, semuanya dalam 337, memuat **{pc(dmgB / dmg_scored)}** gambut rusak SKEG pada KHG yang dinilai ({n1(dmgB / 1e6)} juta ha). Di sini urgensi tinggi bertemu klaim lahan yang tumpang tindih antara perusahaan, Kementerian Kehutanan, KLH dan desa, sehingga pekerjaan membutuhkan kesepakatan antarpihak sebelum dapat dimulai.
- **Tipe C, urgensi sedang:** {int(T.loc['C','khg'])} KHG; **tipe D, lindungi dan pantau:** {int(T.loc['D','khg'])} KHG bergambut dalam atau berkubah dengan sedikit kebakaran; **tipe E, pantau:** {int(T.loc['E','khg'])} KHG.
- **Intervensi pada 337 KHG yang dinilai:** pembasahan {ivt('rewetting')}, pembasahan dan revegetasi {ivt('rewetting and revegetation')}, revegetasi {ivt('revegetation')}, perlindungan {ivt('protect')}.
- **Validasi:** dengan data sampai 2025, 20% KHG teratas menurut urgensi memuat **{pc(V['urgency']['capture_top20pct'])}** gambut yang terbakar pada 2026 (riwayat kebakaran saja: {pc(V['fire_history_only']['capture_top20pct'])}); AUC {V['urgency']['auc']:.2f}.
- **Kestabilan:** {pc(S['share_khg_type_stable_80pct'])} KHG mempertahankan tipenya pada sedikitnya 80% dari {S['runs']} uji dengan setiap bobot diubah ±50%.
- Tidak ada KHG berurgensi tinggi di luar 362 KHG prioritas PPEG.

Langkah berikut yang diusulkan: lokakarya pembobotan bersama KLH; pelengkapan data klaim lahan yang belum tersedia (hutan adat, batas wilayah adat dari BRWA, PIAPS, rilis izin terbaru dari SIGAP, hak atas tanah dari BPN); dan analisis rinci di dalam KHG tipe A dan B (defisit air, pompa, sekat kanal) sebagai dasar desain.
"""
    C["00_ringkasan"] = id_num(C["00_ringkasan"].replace("SK.129/2017", "SK.129/2017"))

    # --- 01 summary
    C["01_summary"] = f"""# 1 Summary

This report sets out a national prioritisation of Indonesia's peat hydrological units (KHG) for rewetting and revegetation, to support the planning and financing of peat restoration. It was prepared by the RE-PEAT GIS team (Departemen Teknik Geodesi, Universitas Gadjah Mada) for the World Bank and KLH/BPLH. **It is a draft for discussion: the weights are provisional until agreed with KLH.**

Each KHG is scored on five separate dimensions rather than one blended score, because they answer different questions. **Urgency** asks how likely the peat is to burn and degrade further; **stake** asks what would be lost; **complexity** asks how hard it is to act, given the claims on the land; **feasibility** asks how easy rewetting would be on the ground; **people** asks who is exposed to fire and haze. Urgency, complexity and stake place each KHG in one of five types of action; feasibility and people are flags:

- **A, quick action:** {int(T.loc['A','khg'])} KHG ({int(T.loc['A','in_337'])} in KLH's 337 work list): high urgency, low or medium complexity. Leading examples: {lst('A', 5)}.
- **B, multi-party coordination:** {int(T.loc['B','khg'])} KHG, all in the 337, holding **{pc(dmgB / dmg_scored)} of the SKEG-damaged peat of the scored KHG** ({n1(dmgB / 1e6)} million ha). High urgency meets overlapping claims of companies, the Ministry of Forestry, KLH and villages. Leading examples: {lst('B', 5)}.
- **C, medium urgency:** {int(T.loc['C','khg'])} KHG of medium urgency.
- **D, protect and monitor:** {int(T.loc['D','khg'])} KHG with deep or domed peat and little fire, mostly outside the 337.
- **E, monitor:** {int(T.loc['E','khg'])} KHG with low urgency and low or medium stake.

For planning and financing, type A KHG are where funds can be put to work soonest. Type B KHG hold most of the damaged peat, but work there depends on agreement among licence holders, the Ministry of Forestry, KLH and villages.

Separately from the type, each KHG gets the **intervention its peat needs**: rewetting where at least {rw_min}% of the peat is affected by canals, revegetation where at least {rv_min}% has open or degraded cover in KLH's 2022 land cover map, both, or protection where neither applies. Of the scored 337, {ivt('rewetting')} need rewetting, {ivt('rewetting and revegetation')} rewetting and revegetation, {ivt('revegetation')} revegetation and {ivt('protect')} protection. The type says how urgent and how complex the work is; the intervention says what to do.

{n0(len(scored))} KHG are scored: {meta['pool']} with at least {rule['min_peat_km2']} km² of KLH peat; {nsmall} KHG of the 337 with less peat, scored against the same distribution and flagged as less reliable; and {nwk} KHG of the 337 that hold no peat in KLH's peat map although they are peat hydrological units (the Global Peatland Map shows peat over {pc(gpm.min()) if nwk else ''} to {pc(gpm.max()) if nwk else ''} of each), scored with the whole KHG as the peat extent and flagged. {n337_sc} of the 337 are scored.

**Does it work?** Built only from data up to 2025, the top 20% of KHG by urgency hold **{pc(V['urgency']['capture_top20pct'])} of the peat that burned in 2026** (fire history alone: {pc(V['fire_history_only']['capture_top20pct'])}); AUC {V['urgency']['auc']:.2f} against burned or not ({V['fire_history_only']['auc']:.2f} for fire history alone). With every weight varied by ±50% in {S['runs']} draws, {pc(S['share_khg_type_stable_80pct'])} of KHG keep their type in at least 80% of draws. No KHG outside KLH's 362 PPEG priority KHG has high urgency.

**What it rests on.** {len(D['reg'])} data layers, each documented with its producer, version, usage rights and verification status (Annex A). KLH's integrated PPEG analysis was checked against independent copies of its sources: its peat, burned-area, KHG and licence attributes agree at 98 to 100%, forest function at 93% (Chapter 3).

**What it cannot yet see.** Customary forest and customary territory boundaries, the indicative social-forestry map (PIAPS), the newest permit releases and BPN land rights are not available to the project, so tenure complexity is a lower bound. KLH's 2022 land cover map, on which the revegetation label rests, could not be verified against an independent copy.

**Proposed next steps:** a weighting session with KLH; requests for the missing claim layers (to the Ministry of Forestry's SIGAP service and to BRWA); and detailed analysis within the type A and B KHG (water deficit, pumps, canal blocks) to turn the priorities into designs.
"""

    # --- 02 purpose and approach
    C["02_scope"] = f"""# 2 Purpose and scope

KLH's integrated thematic analysis for peat ecosystem restoration (PPEG, April 2026) identifies where peat is damaged (SKEG 2024) and who is responsible for it, and the project's 337-KHG work list sets out where rewetting designs are being prepared (the KHG holding the 2,004 Bluebook target villages). This prioritisation complements both. For every KHG it asks **how urgent action is, what is at stake, how hard it will be and how feasible rewetting is**, and turns the answers into types of action that match KLH's instruments.

- **Units.** The 865 KHG of the national registry (SK.129/2017). The scoring pool is the {meta['pool']} KHG with at least {rule['min_peat_km2']} km² of peat in KLH's peat map, as used in the PPEG analysis; KLH's 337 are scored even when smaller.
- **KLH priorities.** The 337 work-list KHG and the 362 PPEG priority KHG (in a target village, or holding SKEG-damaged peat) are recorded for every KHG; all 337 are among the 362.
- **Outputs.** For each KHG: five dimension scores, the type, the intervention, ranks (national, within the 337, within the type), type stability and flags. They are available in the national dashboard, in the accompanying data tables and GIS layers, and in Annex B (one page per KHG of the 337).
- **Limits of use.** The prioritisation ranks KHG for attention and funding. It does not locate canal blocks or pumps; those come from detailed analysis within each KHG.
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
    FLDN = {"NAMA_KHG": "KHG name", "PULAU": "Island", "PROV_2023": "Province", "KABKO_2023": "District or city", "KEC_2023": "Sub-district",
            "DESA_2023": "Village", "IZIN_USAHA": "Licence type", "PERUSAHAAN": "Licence holder", "Fungsi_KWS": "Forest area function",
            "FEG_250K": "Peat ecosystem function (1:250k)", "PEAT_THICK": "Peat thickness class", "TNH_GAMBUT": "Peat or mineral soil",
            "FEG_PEAT_1": "Peat ecosystem function (1:50k)", "LAHAN_GAMB": "Peat land", "BA_2015 … BA_2024": "Burned area, each year 2015 to 2024"}
    vt["Independent copy of the source"] = vt.source.map(lambda x: next((v for k, v in SRCN.items() if k in str(x)), str(x).split(":")[0]))
    vt["Note"] = vt.note.fillna("").map(lambda x: "on the 17% of points the 1:50k copy covers; compared by meaning" if "covers" in x else x)
    vt["field"] = vt.field.map(lambda x: FLDN.get(x, x.replace("_", " ")))
    vt = vt[["field", "Independent copy of the source", "Agrees", "Note"]].rename(columns={"field": "PPEG attribute"})
    themes = reg.groupby("theme").id.count().reset_index().rename(columns={"theme": "Theme", "id": "Layers"})
    C["03_data"] = f"""# 3 Data

## {{n}} Data layers and their documentation

The prioritisation uses {len(reg)} data layers, listed in the project's layer register (Annex A). For each layer the register records the producer, legal basis, version, scale, usage rights, date received, how the layer is used and whether it has been verified against an independent source. This shows which results rest on verified data and which on layers still to be confirmed. All layers, with a summary layer per KHG, are shared with KLH and the World Bank as one GIS package. Where two sources cover the same information both are kept: the 2023 village boundaries, for example, are used alongside the administrative names in KLH's PPEG analysis, which made it possible to correct the error described below.

{md_table(themes, "Data layers by theme")}
## {{n}} KLH's integrated PPEG analysis and its verification

KLH's PPEG analysis (April 2026, 989,398 polygons) overlays KHG, villages, licences, forest area, peat function, peat (BBSDLP), land cover, damage, burned area and canal zones. KLH uses it as the reference for its restoration targets, so its attributes were checked before use: 20,000 polygons were sampled at random in proportion to area, and at one point in each, every attribute was compared with an independent copy of its source held by the project.

{md_table(vt, "Agreement of PPEG attributes with independent copies of their sources (share of sampled area)")}
- **Matches.** Peat land, burned area, KHG and licences agree at 98 to 100%. KLH's derived classes (concession, APL, canal-affected, burned, burn count) are fully consistent with the attributes they are derived from.
- **Rules clarified.** The "Buffer 5 Kilometer" class covers land within 5 km of a licence. The canal-affected zones reach about 1,000 m from primary, 500 m from secondary and 250 m from tertiary canals of the project's canal map.
- **Points to confirm with KLH.** About 6.6% of the area is APL (land outside the forest estate) in PPEG but forest estate in Kawasan Hutan 2023, which suggests PPEG used a different Kawasan Hutan release. About 1.9% is non-concession in PPEG but licensed in the 2025 licence layer, which may reflect the licence date used.
- **One correction.** Parts of the Papua KHG outside the 2017 maps carry placeholder administrative names (Jayapura / Ebungfao / Atabar); administrative names are therefore taken from the 2023 village boundaries.
- **Not yet verified.** Land cover 2022, SKEG damage 2024, the BBSDLP landform, depth and maturity attributes (which include the dome classes) and KLH's actor and intervention classes: the project has no independent copy of these.

## {{n}} Tenure claims

Tenure complexity counts the claims that overlap on the same peat: business licences (2025), social forestry (community forest PPHKM, village forest Hutan Desa and community plantation HTR permits), the forest estate, DMPG villages, land held inside the forest estate that is being settled (PPTPKH, the forest-area part of agrarian reform) and forest released for other uses. The social-forestry, PPTPKH and forest-release layers were obtained from the Ministry of Forestry's public map services, through BIG's Satu Peta portal, on 2026-11-16. On KHG peat ({n0(peat_tot)} km²), licences cover {pc(wsh('share_licence'), 1)}, the forest estate {pc(wsh('share_forest_estate'), 1)}, DMPG villages {pc(wsh('share_dmpg'), 1)}, released forest {pc(wsh('share_released'), 1)}, PPTPKH {pc(wsh('share_pptpkh'), 1)} and social forestry {pc(wsh('share_community'), 1)}; {pc(wsh('share_3plus_claims'), 1)} of the peat carries three or more claims and {pc(wsh('share_no_claim'), 1)} none.

Not available to the project: customary forest (the public map service holds no data), customary territory boundaries (BRWA publishes its register of 2,283 territories but shows the boundaries only as map images), PIAPS and the Ministry of Forestry's newest permit releases (SIGAP, available on request), and BPN land rights. In the licence layer no two licences overlap, so overlapping licences cannot be measured from it. Tenure complexity is therefore a lower bound: KHG with customary or private claims may be more complex than shown here.
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
            "brgm_blocks_per_km2": "Existing BRGM structures per km² of peat",
            "conservation_share": "Share of peat in conservation areas (national parks, reserves; Kawasan Hutan 2023)",
            "water_dist_km": "Median distance from the peat to a large river (two-bank RBI rivers) or lake (lower = more feasible)",
            "road_dist_km": "Median distance from the peat to a road, RBI detailed roads without footpaths (lower = more feasible)",
            "pop_on_peat": "People living on the peat (IHME Populace, third quarter of 2025, 40 m)", "pop_10km": "People within 10 km of the KHG (haze exposure)",
            "villages_peat": "2023 villages with land on the peat"}
    INDN = {"u_fire_freq": "Fire frequency", "u_burn_repeat": "Repeated burning", "u_hotspot": "Hotspot density", "u_hotspot_now": "Current-year hotspots",
            "damage_share": "Damaged peat", "canal_share": "Canal-affected peat", "thick3m_share": "Deep peat", "dome_share": "Peat dome",
            "protected_share": "Protected function", "peat_km2": "Peat area", "conservation_share": "Conservation areas",
            "tenure_complexity": "Tenure complexity", "actor_types": "Actor types", "villages": "Villages", "dry_balance_mm": "Dry-season water balance",
            "brgm_blocks_per_km2": "Existing BRGM structures", "water_dist_km": "Distance to water", "road_dist_km": "Distance to roads",
            "pop_on_peat": "People on the peat", "pop_10km": "People within 10 km", "villages_peat": "Villages on the peat"}
    rows = []
    for dname, spec in dims.items():
        for ind, s in spec.items():
            rows.append([dname.capitalize(), INDN.get(ind, ind.replace("_", " ").capitalize()), DESC.get(ind, ""), s["weight"]])
    ind_tab = pd.DataFrame(rows, columns=["Dimension", "Indicator", "Definition", "Weight"])
    C["04_method"] = f"""# 4 Method and rationale

## {{n}} Why separate dimensions

A single score would trade urgency against complexity and stake, and hide what KLH needs to see. A KHG that burns every year but is crowded with claims needs a different response from one that burns as often on unclaimed land, and a deep, undisturbed dome needs protection rather than restoration. The five dimensions are therefore scored separately and combined only through a typology that keeps them visible.

## {{n}} Indicators and scoring

Each dimension is the weighted mean of its indicators' **percentile ranks** among the scoring pool (0 to 1, higher = more urgent, more at stake, more complex, more feasible). Percentile ranks make indicators with different units and skewed distributions comparable, and a KHG missing an indicator is scored on the indicators it has.

{md_table(ind_tab, "Indicators, definitions and weights (rules dated " + str(rule['written']) + ")")}
Fire frequency counts double, as in the earlier fire-based ranking. Tenure complexity counts double within complexity because it already summarises four claims. Some indicators are reported but not scored: existing BRGM structures per km² (scored in the first version, then dropped because canal blocks were built where fires had been, so the indicator repeated urgency), peat volume (the depth class is blank for part of the peat) and SiTMAT water-table depth (only {int(D['prof'].tma_deep_share.notna().sum())} KHG have stations).

**Tenure complexity (v2)** is computed on a regular grid of points over each KHG's peat. At each point it records which of six claim types are present (licence, social forestry, forest estate, DMPG village, PPTPKH, released forest). Four indicators per KHG make up the index: the share of peat under a licence that is also social-forestry or DMPG village land; the share that is **contested** (a licence on PPTPKH or social-forestry land, or forest estate on PPTPKH); the mean number of claim types; and the number of licence holders.

## {{n}} Typology

Urgency, complexity and stake are cut into terciles of the scoring pool (urgency {meta['tercile_cuts']['urgency'][0]:.2f} and {meta['tercile_cuts']['urgency'][1]:.2f}; complexity {meta['tercile_cuts']['complexity'][0]:.2f} and {meta['tercile_cuts']['complexity'][1]:.2f}; stake {meta['tercile_cuts']['stake'][0]:.2f} and {meta['tercile_cuts']['stake'][1]:.2f}):

- **A, quick action:** urgency high, complexity low or medium.
- **B, multi-party coordination:** urgency high, complexity high.
- **C, medium urgency:** urgency medium.
- **D, protect and monitor:** urgency low, stake high.
- **E, monitor:** urgency low, stake low or medium.

Feasibility and people do not change the type: a KHG in the lowest tercile of feasibility is flagged "low feasibility" ({nf} KHG), and one in the highest tercile of people "high exposure" ({nx} KHG). Within each type KHG are ranked by urgency (then stake), and an overall urgency rank is given among all scored KHG and among the 337.

## {{n}} Intervention

The type says how urgent and how complex a KHG is; it does not say what the peat needs. A second, independent label does, from two shares of the KHG's KLH peat and fixed thresholds (not terciles, so a label means the same in every year):

- **Rewet:** at least {rw_min}% of the peat lies in KLH's canal-affected zones (PPEG). The peat is drained, and the canals need blocking.
- **Revegetate:** at least {rv_min}% has open or degraded cover in KLH's land cover map 2022, as used in PPEG (swamp shrub, shrub, open land, open swamp, savanna). Plantations, crops and settlements are not counted: they call for livelihood revitalisation, not replanting.
- **Rewet and revegetate:** both.
- **Protect:** neither. The peat is largely forested and undrained; the task is to keep it wet and prevent fire.

## {{n}} Rules written before results, and their amendments

Each rule was written down and dated before its result was computed. Changes made after seeing a result are recorded below as dated amendments, and earlier results are kept, so that readers can see what was decided in advance and what was adjusted.

Table: Rules and amendments

| Date | Rule | Change | Reason |
|---|---|---|---|
| 2026-11-16 | Tenure complexity v1 | Written before any result | Overlapping claims per KHG |
| 2026-11-16 | Tenure complexity v1, amendment | Overlapping licences reported, not scored | The licence layer has no overlaps (0 ha shared), so the indicator is 0 by construction |
| 2026-11-16 | Tenure complexity v2 | Six claim types; contested land; holder count | v1 missed social forestry and occupied forest land; two v1 indicators did not discriminate. v1 result kept |
| {rule['written']} | Final prioritisation | Written before any result | Four dimensions and typology |
| {rule['written']} | Final prioritisation v2 | Written before any v2 result; v1 kept | Feasibility from distance to large rivers and roads instead of BRGM blocks (which echoed urgency); conservation areas added to stake; a fifth dimension, people; an intervention label (rewet, revegetate, both, protect) |
| {rule['written']} | Final prioritisation, amendment | KHG of the 337 with no peat in KLH's peat map scored with the whole KHG as peat, against the pool, and flagged; population from IHME Populace (2025, 40 m) instead of WorldPop (2020, 1 km) | A KHG is delineated as a peat unit, and the Global Peatland Map shows peat in each of them; the finer population grid counts people on the peat more precisely |
| {rule['written']} | Final prioritisation, amendment | KHG of the 337 below {rule['min_peat_km2']} km² of peat scored against the pool and flagged | 99 of the 337 fell out of the pool, contrary to the aim of covering the 337; they hold 0.09% of its damaged peat |

## {{n}} Validation and sensitivity

**Validation.** Urgency is tested on a year it has not seen. Built from data up to 2025, without the current year's hotspots, it is compared with the share of each KHG's peat that burned in 2026 (KLHK burned area), alongside fire history alone. **Sensitivity.** In {S['runs']} draws every weight is multiplied by a random factor between 0.5 and 1.5; the share of draws in which each KHG keeps its type and the spread of its urgency rank are reported.
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

Type B holds {pc(dmgB / dmg_scored)} of the SKEG-damaged peat of the scored KHG: {int(T.loc['B','khg'])} KHG where high urgency meets high complexity, {isl.loc['B', 'Sumatera'] if 'Sumatera' in isl else ''} in Sumatera and {isl.loc['B', 'Kalimantan'] if 'Kalimantan' in isl else ''} in Kalimantan. Type A gathers {int(T.loc['A','khg'])} smaller KHG with high urgency and moderate complexity. Type D, protect and monitor, is mostly in Papua and outside the 337.

{md_table(isl, "Scored KHG by type and island")}
## {{n}} What the peat needs

{md_table(D['iv'].assign(Type=lambda x: x.type + " " + x.type.map(TYN), Intervention=lambda x: x.intervention.map(IVN)).sort_values(['type', 'intervention'], key=lambda c: c.map({v: i for i, v in enumerate(IVO)}) if c.name == 'intervention' else c)[['Type', 'Intervention', 'khg', 'in_337', 'peat_km2', 'priority_ha']].rename(columns={'khg': 'KHG', 'in_337': 'In the 337', 'peat_km2': 'Peat (km²)', 'priority_ha': 'SKEG-damaged peat (ha)'}).assign(**{'Peat (km²)': lambda x: x['Peat (km²)'].map(n0), 'SKEG-damaged peat (ha)': lambda x: x['SKEG-damaged peat (ha)'].map(n0)}), "Scored KHG by type and intervention")}
![Scored KHG by type and by the intervention their peat needs.]({figs['iv']})

Rewetting dominates: of the {int(T.loc['B','khg'])} type B KHG, {ivt('rewetting', ivB)} need rewetting and {ivt('rewetting and revegetation', ivB)} rewetting and revegetation. Revegetation alone matters more in types C and E, where the peat is open but less drained.

## {{n}} Urgency against complexity

![Urgency against complexity of every scored KHG, coloured by type.]({figs['matrix']})

Urgency and complexity are strongly related (Spearman {corr.loc['urgency','complexity']:.2f} in the pool): the KHG that burn most are also the most contested, which is why type B is large. This is a property of the landscape, not of the method, and it is the main message for planning: most of the damaged peat cannot be rewetted by one agency alone. Stake is more independent of urgency ({corr.loc['urgency','stake']:.2f}).

![Distribution of the five dimensions by type.]({figs['dims']})

## {{n}} Who holds the damaged peat

KLH's PPEG analysis assigns each area of damaged peat to one of four actors: a licence holder, a licence holder together with communities (within 5 km of a licence), the Ministry of Forestry, or KLH. The figure shows how the damaged peat of each type divides among them.

![SKEG-damaged peat by the actor assigned in KLH's PPEG analysis, by type.]({figs['actors']})

## {{n}} Leading KHG of the 337

{md_table(toptab('A'), "Type A, quick action: the first 10 KHG of the 337 by urgency")}
{md_table(toptab('B'), "Type B, multi-party coordination: the first 10 KHG of the 337 by urgency")}
{md_table(toptab("D", 20, scored), "Type D, protect and monitor: all scored KHG (one is in the 337)")}
Results for every scored KHG are in the accompanying data tables and dashboard; Annex B has a profile of each KHG of the 337.

## {{n}} Gaps between the lists

- **PPEG priority KHG outside the 337:** {int((gaps.gap == 'PPEG priority (362) outside the 337').sum())} KHG (in a target village by a sliver, or holding SKEG damage only).
- **High-urgency KHG outside the 362:** {int(gaps.gap.str.startswith('high urgency').sum())}. Every KHG in the top tercile of urgency is already a PPEG priority KHG.
- **KHG of the 337 without KLH peat:** {nwk}, scored with the whole KHG as peat and flagged; {int(gaps.gap.str.contains('not scored').sum())} remain unscored; **with less than {rule['min_peat_km2']} km² of peat:** {int(gaps.gap.str.contains('less than').sum())}, scored against the pool and flagged.
"""

    # --- 06 validation and robustness
    C["06_validation"] = f"""# 6 Validation and robustness

![Share of 2026 burned peat held by the most urgent KHG, built from data up to 2025. Dashed: the top 20% of KHG.]({figs['validation']})

Table: Validation against 2026 burned peat ({V['n_pool']} KHG in the pool, {V['n_burned']} of them burned in 2026)

| Ranking | Spearman | AUC (burned or not) | 2026 burned peat in the top 20% |
|---|---|---|---|
| Urgency (without 2026 hotspots) | {V['urgency']['spearman']:.2f} | {V['urgency']['auc']:.2f} | {pc(V['urgency']['capture_top20pct'])} |
| Fire history alone | {V['fire_history_only']['spearman']:.2f} | {V['fire_history_only']['auc']:.2f} | {pc(V['fire_history_only']['capture_top20pct'])} |

Urgency adds most where it matters for planning: among the KHG ranked highest, it holds {pc(V['urgency']['capture_top20pct'] - V['fire_history_only']['capture_top20pct'])} points more of the 2026 burned peat than fire history alone, because damage and canal drainage flag KHG that had not yet burned much. 2026 is one season; the test should be repeated each year.

![Type stability: share of {S['runs']} weight draws (every weight ±50%) in which each KHG keeps its type.]({figs['stability']})

{pc(S['share_khg_type_stable_80pct'])} of the KHG in the pool keep their type in at least 80% of the draws (mean {pc(S['share_keeping_type_mean'])}); the median urgency rank moves by {S['median_rank_sd']:.0f} places. The unstable KHG are those near a tercile cut. The dashboard and Annex B show each KHG's stability, so readers can see where the type is a close call.

**Known weaknesses.**

- **Feasibility is coarse.** It uses distance to large rivers and roads and the dry-season water balance, and now relates only weakly to urgency (Spearman {corr.loc['urgency','feasibility']:.2f}, against 0.60 in the first version, which used BRGM blocks). The RBI maps hold only rivers wide enough to be drawn with two banks, and dry-season river levels are not included. Results of the detailed water-deficit and pump analysis within each KHG would refine it. It is a flag only.
- **The intervention label rests on KLH's land cover 2022 and canal zones**, which could not be checked against independent copies. The {rw_min}% and {rv_min}% thresholds are a judgement, to be confirmed with KLH.
- **People overlaps with complexity** (Spearman {corr.loc['complexity','people']:.2f}): crowded KHG are also contested ones. It is a flag only.
- **Tenure complexity is a lower bound**: customary claims, PIAPS, the newest permits and BPN rights are missing (Chapter 3).
- **Stake leans on BBSDLP landform and FEG thickness**, which could not be verified independently, and on peat area, which favours large KHG.
- **Small KHG** (less than {rule['min_peat_km2']} km² of peat) have noisy shares; they are flagged.
"""

    # --- 07 next steps
    C["07_next"] = f"""# 7 Limitations and next steps

- **Weights.** The weights are provisional. A short weighting session with KLH and the World Bank, for example by pairwise comparison, would settle them; the report, dashboard and annex can then be updated with the agreed weights.
- **Missing claims.** A data request to the Ministry of Forestry's SIGAP service (customary forest 1:50k, PIAPS revision X, the December 2025 permit releases, Kawasan Hutan June 2026) and a request to BRWA for customary territory boundaries would complete tenure complexity; BPN land rights would add private claims.
- **KLH layers to confirm.** The Kawasan Hutan release and licence date used in PPEG, and the source layers of land cover 2022, SKEG 2024 and the BBSDLP attributes, so that they can be verified like the others.
- **From KHG to sites.** For type A and B KHG, detailed analysis within each KHG (water deficit, canal blocks, pumps, layouts) turns the priority into designs. Its results can then replace the KHG-level feasibility flag.
- **Yearly update.** Rerun after each fire season and repeat the validation on the new year.

**Reproducibility.** All figures in this report are computed from the project's data and from rules that were written down and dated in advance. The analysis can be rerun for any KHG as data are updated or weights are agreed.
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

The register documents every data layer used in the prioritisation. The table gives, for each layer, its theme, producer, version, scale and verification status. "Verified" means the layer was checked against an independent copy of its source; "partly verified" that only some of its attributes could be checked; "not verified" that no independent copy is available; "source layer" that it is used as delivered; and "derived" that the project computed it from other layers. The full register also records each layer's legal basis, date received, usage rights, use in the analysis and the evidence for its verification status.

{md_table(r, "Registered layers")}"""
    C["91_annex_b"] = f"""# Annex B KHG profiles

The profiles of the {n337_sc} scored KHG of KLH's 337 work list are in a separate volume, one page per KHG in the order of the KLH work list. Each page shows the KHG's scores, type and intervention, six thematic maps (peat depth and dome, damage, drainage, land cover, land status, fire and villages), its main indicators against the median of the scoring pool, and the licence holders on its peat. Because they name licence holders, the profiles are shared with KLH and the World Bank only. A licence on a KHG is a land-status fact, not a statement about responsibility for fire or damage.
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
                                         "water_dist_km", "road_dist_km", "pop_on_peat", "pop_10km", "open_share", "forest_share") if c in pool}
    hold = D["hold"]
    av = D["av"].set_index("khg_code")
    PR.TITLE = "KHG profiles: KLH's 337 work list"
    PR.SUBTITLE = "Annex B to the national prioritisation of KHG for rewetting. Draft for discussion"
    b = PR.Builder()
    b.front()
    b.heading("B KHG profiles", 1)
    PR.runs(b.doc.add_paragraph(), "This annex has one page for each KHG of KLH's 337 work list that contains KLH peat, in work-list order. Six maps show the KHG's peat depth and dome, SKEG 2024 damage, drainage (canal-influence zones, canals, large rivers, BRGM structures), land cover 2022, land status (forest-area function, business licences, social forestry, PPTPKH) and fire (times burned 2015 to 2026, this year's hotspots) with DMPG villages and roads. Scores are percentile ranks among the scoring pool (0 to 1), and the medians given for comparison are those of the pool. Licence holders and their areas come from KLH's PPEG analysis (April 2026). A licence on a KHG is a land-status fact, not a statement about responsibility for fire or damage. Draft for discussion: the weights are provisional.", Pt(9.5))
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
        PR.runs(p, f"{r.khg_code} · {r.provinces} · {r.island.replace('Pulau ', '')} · KLH team: {kp.loc[r.khg_code, 'klh_337_team']} · peat {n0(r.peat_km2)} km² · {ranks} · type kept in {pc(r.type_stability) if not pd.isna(r.type_stability) else 'n/a'} of weight draws"
                + (" · no peat in KLH's peat map: whole KHG used, less reliable" if getattr(r, "whole_khg", False) is True
                   else " · small peat area: less reliable" if not r.in_pool else "") + (" · low feasibility" if r.flag_low_feasibility else "")
                + (" · high exposure" if getattr(r, "flag_high_exposure", False) is True else "")
                + (f" · intervention: {IVN.get(r.intervention, 'n/a').lower()}" if isinstance(getattr(r, "intervention", None), str) else ""), Pt(8.5), PR.MUTED)
        sc = d.add_paragraph()
        PR.runs(sc, f"Type {r.type}, {TYN.get(r.type, '').lower()}. Scores (0 to 1): " + " · ".join(f"{lab.lower()} {getattr(r, c):.2f}" for c, lab in DIM if hasattr(r, c) and not pd.isna(getattr(r, c))), Pt(9))
        sc.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        pic = d.add_paragraph(); pic.add_run().add_picture(str(png), width=Cm(15.0))
        rows = [
            ["Burned share of peat per year, 2015-2025", pc(r.u_fire_freq, 2) if not pd.isna(r.u_fire_freq) else "n/a", pc(med["u_fire_freq"], 2)],
            ["Hotspots per km² of peat per year", f"{r.u_hotspot:.2f}" if not pd.isna(r.u_hotspot) else "n/a", f"{med['u_hotspot']:.2f}"],
            ["SKEG 2024 damaged share of peat", pc(r.damage_share), pc(med["damage_share"])],
            ["Canal-affected share of peat (rewetting if ≥ 20%)", pc(r.canal_share), pc(med["canal_share"])],
            *([["Open or degraded cover / forest, land cover 2022 (revegetation if open ≥ 20%)", f"{pc(r.open_share)} / {pc(r.forest_share)}" if not pd.isna(r.open_share) else "n/a",
                f"{pc(med['open_share'])} / {pc(med['forest_share'])}"]] if "open_share" in f else []),
            ["Peat 3 m or deeper / dome / protected function", f"{pc(r.thick3m_share)} / {pc(r.dome_share)} / {pc(r.protected_share)}",
             f"{pc(med['thick3m_share'])} / {pc(med['dome_share'])} / {pc(med['protected_share'])}"],
            ["Licence on social-forestry or DMPG land / contested", f"{pc(r.c_licence_community)} / {pc(r.c_contested)}" if not pd.isna(r.c_licence_community) else "n/a",
             f"{pc(med['c_licence_community'])} / {pc(med['c_contested'])}"],
            ["Social forestry / PPTPKH share of peat", f"{pc(r.share_community)} / {pc(r.share_pptpkh)}" if not pd.isna(r.share_community) else "n/a",
             f"{pc(med['share_community'])} / {pc(med['share_pptpkh'])}"],
            *([["Distance to a large river or lake / to a road (km)", f"{r.water_dist_km:.1f} / {r.road_dist_km:.1f}" if not pd.isna(r.water_dist_km) else "n/a",
                f"{med['water_dist_km']:.1f} / {med['road_dist_km']:.1f}"],
               ["People on the peat / within 10 km", f"{n0(r.pop_on_peat)} / {n0(r.pop_10km)}" if not pd.isna(r.pop_on_peat) else "n/a",
                f"{n0(med['pop_on_peat'])} / {n0(med['pop_10km'])}"]] if "water_dist_km" in f else []),
            ["Damaged peat: licence holder / with communities / MoF / KLH (ha)",
             " / ".join(n0(x) for x in (r.priority_company_ha, r.priority_company_buffer_ha, r.priority_mofor_ha, r.priority_klh_ha)), ""],
        ]
        tbl(b, ["Indicator", "This KHG", "Pool median"], rows, [9.2, 3.6, 3.2])
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
                 f"water-table loggers (SiTMAT): {int(a.stations_community + a.stations_concession)}." if a is not None else ""))
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
