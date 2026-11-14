"""Build the DEM benchmark report (one self-contained HTML page) from the benchmark outputs.

    python tools/dem_benchmark_report.py

Also reads 03_metrics/height_difference_ci*.csv (script/dem_benchmark_ci.py), 10_canopy/ (dem_benchmark_canopy.py) and
09_profiles/ (dem_benchmark_profile.py, Mendahara) when they exist.
Reads the prose from reports/dem_benchmark/report_text.md ({name} placeholders are filled from the results; [[kind:name]]
markers are replaced by tables, charts and maps), the metrics in _khg/<code>_<name>/01_dem/benchmark/03_metrics/ and
05_pipeline/, the error maps in 02_error_maps/, and the benchmark configs in ../repeat-dem/benchmark/. Writes
reports/dem_benchmark/report.md (the report, with its figures in reports/dem_benchmark/figures/) and an HTML copy, report.html. Every number comes from those files.
Needs pandas, numpy, rasterio, geopandas, matplotlib, pyyaml, pyogrio.
"""
import base64
import html
import io
import os
import re
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import pyogrio
import rasterio
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

HUB = Path(__file__).resolve().parents[1]
WS = HUB.parent
DEM = WS / "repeat-dem"
sys.path.insert(0, str(WS / "repeat-common" / "src"))
from repeat_common import khg  # noqa: E402

BENCH = {"mendahara": khg.folder("KHG Sungai Mendahara - Sungai Batanghari") / "01_dem" / "benchmark",
         "sugihan_lumpur": khg.folder("KHG Sungai Sugihan - Sungai Lumpur") / "01_dem" / "benchmark"}
CHECKS = WS / "repeat-dem" / "runs" / "checks"
OUT = HUB / "reports" / "dem_benchmark"
DATA = Path(os.environ.get("REPEAT_DATA") or WS / "_data")
SITES = {"mendahara": "Mendahara", "sugihan_lumpur": "Sugihan-Lumpur"}
CANDS = ["deltadtm", "klhk_modelled", "demnas", "fabdem", "glo30", "gedtm30"]
LABEL = {"gem15": "GEM-15 v1 DTM", "deltadtm": "DeltaDTM v1.1", "klhk_modelled": "KLHK modelled DTM", "demnas": "DEMNAS", "fabdem": "FABDEM v1.2", "glo30": "Copernicus GLO-30", "gedtm30": "GEDTM30 v1.1"}
COLOR_L = {"deltadtm": "#2a78d6", "klhk_modelled": "#eb6834", "demnas": "#1baf7a", "fabdem": "#eda100", "glo30": "#e87ba4", "gedtm30": "#008300"}
COLOR_D = {"deltadtm": "#3987e5", "klhk_modelled": "#d95926", "demnas": "#199e70", "fabdem": "#c98500", "glo30": "#d55181", "gedtm30": "#008300"}
WC_SHOW = ["tree cover", "shrubland", "grassland", "cropland", "mangroves"]


def load(site):
    m = BENCH[site] / "03_metrics"
    return {k: pd.read_csv(m / f"{k}.csv") for k in ("pointwise", "height_difference", "criterion")}


def fmt(v, d=2):
    return f"{v:.{d}f}"


def table(head, rows, cls="", note=""):
    return {"head": head, "rows": rows, "cls": cls, "note": note}


def html_table(t):
    th = "".join(f"<th>{html.escape(h)}</th>" for h in t["head"])
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in t["rows"])
    cap = f'<p class="note">{t["note"]}</p>' if t["note"] else ""
    return f'<div class="tablewrap"><table class="sortable {t["cls"]}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>{cap}'


NL = chr(10)


def md_cell(c):
    c = re.sub(r"<code>(.*?)</code>", r"`\1`", str(c))
    return html.unescape(re.sub(r"<[^>]+>", "", c)).replace("|", r"\|")


def md_table(t):
    lines = ["| " + " | ".join(md_cell(h) for h in t["head"]) + " |", "|" + "---|" * len(t["head"])]
    lines += ["| " + " | ".join(md_cell(c) for c in r) + " |" for r in t["rows"]]
    if t["note"]:
        lines += ["", "*" + md_cell(t["note"]).replace(" Click a column to sort.", "") + "*"]
    return NL.join(lines)


def dh_chart_png(M):
    """The same chart as dh_chart, as a PNG for the Markdown report."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    xs = [500, 1000, 2000]
    for ax, (s, name) in zip(axes, SITES.items()):
        hd = M[s]["height_difference"]
        hd = hd[hd.reference == "lidar"]
        sig = hd[hd.candidate == "deltadtm"].set_index("baseline_m").reference_signal_rms_m
        ax.plot(xs, [sig[x] for x in xs], color="#b9b8b1", lw=2, label="real relief (LiDAR)")
        ax.axhline(0.3, color="#898781", lw=1, ls=(0, (4, 4)), label="Tier A 0.30 m")
        for c in CANDS:
            r = hd[hd.candidate == f"{c}__processed"].set_index("baseline_m").rms_m
            ax.plot(xs, [r[x] for x in xs], color=COLOR_L[c], lw=2, marker="o", ms=5, label=LABEL[c])
            ax.annotate(LABEL[c].split(" v")[0].replace(" modelled DTM", ""), (2000, r[2000]), xytext=(6, 0), textcoords="offset points",
                        fontsize=8, va="center", color="#52514e")
        ax.set_xscale("log")
        ax.set_xticks(xs, [f"{x / 1000:g} km" for x in xs])
        ax.minorticks_off()
        ax.set_title(name, fontsize=11, loc="left", color="#0b0b0b")
        ax.grid(axis="y", color="#e1e0d9", lw=0.8)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(colors="#52514e", labelsize=8)
    axes[0].set_ylabel("RMS error of height differences (m)", fontsize=9, color="#52514e")
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, fontsize=8, frameon=False, loc="lower center", ncol=len(lab), bbox_to_anchor=(0.5, -0.06))
    fig.subplots_adjust(wspace=0.25)
    png_uri(fig, "height_difference_error")
    return "figures/height_difference_error.png"


def file_uri(src, name):
    """Copy a PNG made by a repeat-dem script into figures/ and return it as a data URI for the HTML page."""
    import shutil
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, OUT / "figures" / f"{name}.png")
    return "data:image/png;base64," + base64.b64encode(Path(src).read_bytes()).decode()


def png_uri(fig, name):
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "figures" / f"{name}.png", dpi=130, bbox_inches="tight", transparent=True)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def error_maps(site):
    cmap = LinearSegmentedColormap.from_list("div", ["#1c5cab", "#86b6ef", "#e8e7e2", "#ee9a92", "#b8302f"])
    show = ["deltadtm__processed", "klhk_modelled__processed", "gedtm30__processed", "demnas__processed"]
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.6))
    for ax, k in zip(axes, show):
        with rasterio.open(BENCH[site] / "02_error_maps" / f"{k}_minus_lidar.tif") as d:
            a = d.read(1).astype(float)
            a[a == d.nodata] = np.nan
        a = a - np.nanmedian(a)
        im = ax.imshow(a, cmap=cmap, vmin=-2, vmax=2, interpolation="nearest")
        ax.set_title(LABEL[k.split("__")[0]] + ", processed", fontsize=10, color="#898781")
        ax.set_axis_off()
    cb = fig.colorbar(im, ax=axes, orientation="horizontal", fraction=0.05, pad=0.04, shrink=0.5)
    cb.set_label("candidate minus LiDAR, median removed (m)", color="#898781", fontsize=9)
    cb.ax.tick_params(colors="#898781", labelsize=8)
    cb.outline.set_edgecolor("#898781")
    return png_uri(fig, f"error_maps_{site}")


def unit_maps():
    base = BENCH["sugihan_lumpur"] / "05_pipeline"
    ref = gpd.read_file(base / "lidar" / "delineate" / "subkhg_units.gpkg")
    ref = ref.to_crs(ref.estimate_utm_crs())
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.8))
    for ax, (v, title) in zip(axes, [("lidar", "LiDAR (reference)"), ("deltadtm__processed", "DeltaDTM, processed"),
                                      ("klhk_modelled_raw", "KLHK modelled DTM as used now")]):
        u = gpd.read_file(base / v / "delineate" / "subkhg_units.gpkg").to_crs(ref.crs)
        if v != "lidar":
            ref.boundary.plot(ax=ax, color="#b9b8b1", linewidth=1.6)
        u.boundary.plot(ax=ax, color="#2a78d6" if v != "lidar" else "#52514e", linewidth=0.8)
        ax.set_title(f"{title}: {len(u)} units", fontsize=10, color="#898781")
        ax.set_axis_off()
    return png_uri(fig, "subkhg_units_sugihan_lumpur")


def dh_chart(M):
    """Small multiples, one per site: error of height differences against baseline, processed candidates (lines)."""
    W, H, pad = 540, 340, {"l": 52, "r": 150, "t": 30, "b": 44}
    xs = [500, 1000, 2000]
    ymax = max(M[s]["height_difference"]["rms_m"][M[s]["height_difference"].candidate.str.endswith("__processed")].max() for s in M) * 1.08
    panels = []
    for s, name in SITES.items():
        hd = M[s]["height_difference"]
        hd = hd[hd.reference == "lidar"]
        px = lambda x: pad["l"] + (np.log(x) - np.log(xs[0])) / (np.log(xs[-1]) - np.log(xs[0])) * (W - pad["l"] - pad["r"])  # noqa: E731
        py = lambda y: H - pad["b"] - y / ymax * (H - pad["t"] - pad["b"])  # noqa: E731
        g = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Height-difference error, {name}">']
        for t in np.arange(0, ymax, 0.5):
            g.append(f'<line class="grid" x1="{pad["l"]}" x2="{W - pad["r"]}" y1="{py(t):.1f}" y2="{py(t):.1f}"/>'
                     f'<text class="tick" x="{pad["l"] - 6}" y="{py(t) + 3:.1f}" text-anchor="end">{t:.1f}</text>')
        for x in xs:
            g.append(f'<text class="tick" x="{px(x):.1f}" y="{H - pad["b"] + 16}" text-anchor="middle">{x / 1000:g} km</text>')
        sig = hd[hd.candidate == "deltadtm"].set_index("baseline_m").reference_signal_rms_m
        pts = " ".join(f"{px(x):.1f},{py(sig[x]):.1f}" for x in xs)
        g.append(f'<polyline class="signal" points="{pts}"/><text class="lab muted" x="{px(2000) + 6:.1f}" y="{py(sig[2000]) + 3:.1f}">real relief</text>')
        g.append(f'<line class="tier" x1="{pad["l"]}" x2="{W - pad["r"]}" y1="{py(0.3):.1f}" y2="{py(0.3):.1f}"/>'
                 f'<text class="lab muted" x="{W - pad["r"] + 6}" y="{py(0.3) + 3:.1f}">Tier A 0.30</text>')
        ends = []
        for c in CANDS:
            r = hd[hd.candidate == f"{c}__processed"].set_index("baseline_m").rms_m
            pts = " ".join(f"{px(x):.1f},{py(r[x]):.1f}" for x in xs)
            g.append(f'<polyline class="ser s-{c}" points="{pts}"/>')
            for x in xs:
                g.append(f'<circle class="pt s-{c}" cx="{px(x):.1f}" cy="{py(r[x]):.1f}" r="4"><title>{LABEL[c]}, processed, {name}: '
                         f'{r[x]:.2f} m RMS error of height differences over {x / 1000:g} km</title></circle>')
            ends.append([py(r[2000]), c])
        ends.sort()
        last = -99
        for y, c in ends:  # direct labels at the line ends, nudged apart
            y = max(y, last + 14)
            last = y
            g.append(f'<text class="lab" x="{px(2000) + 8:.1f}" y="{y + 3:.1f}">{LABEL[c].split(" v")[0].replace(" modelled DTM", "")}</text>')
        g.append(f'<text class="axis" x="{pad["l"]}" y="14">{name}</text>')
        g.append(f'<text class="tick" transform="translate(12,{(H - pad["b"] + pad["t"]) / 2}) rotate(-90)" text-anchor="middle">RMS error (m)</text>')
        g.append("</svg>")
        panels.append("".join(g))
    legend = "".join(f'<span class="key"><i class="sw s-{c}"></i>{LABEL[c]}</span>' for c in CANDS)
    return (f'<figure class="chart"><figcaption>Error of height differences between LiDAR cells 0.5, 1 and 2 km apart, after processing '
            f'(lower is better). Grey: the real height difference in the LiDAR. Dashed: Tier A.</figcaption>'
            f'<div class="legend">{legend}</div><div class="panels">{"".join(panels)}</div></figure>')


def main():
    M = {s: load(s) for s in SITES}
    cfg = {s: yaml.safe_load(open(DEM / "benchmark" / f"{s}.yaml", encoding="utf-8")) for s in SITES}
    pipe = BENCH["sugihan_lumpur"] / "05_pipeline"
    dl = pd.read_csv(pipe / "delineation_compare.csv").set_index("variant")
    # the report shows the full-chain variants (delineation and neraca) and the flat control; the smoothing and dome-fit
    # sweeps (delineation only) are in their own check reports
    dl = dl.loc[[v for v in dl.index if (pipe / v / "neraca" / "neraca_report.md").exists() or v == "flat"]]

    def hd(s, c, b=1000, ref="lidar"):
        t = M[s]["height_difference"]
        return float(t[(t.candidate == c) & (t.baseline_m == b) & (t.reference == ref)].rms_m.iloc[0])

    def sig(s):
        t = M[s]["height_difference"]
        return float(t[(t.candidate == "deltadtm") & (t.baseline_m == 1000)].reference_signal_rms_m.iloc[0])

    rest = [hd(s, f"{c}__processed") for s in SITES for c in ("demnas", "fabdem", "glo30")]
    meds = [float(M[s]["pointwise"].query("reference == 'lidar' and `class` == 'all'").set_index("candidate").loc[f"{c}__processed", "median"])
            for s in SITES for c in CANDS]
    reports = {v: (pipe / v / "neraca" / "neraca_report.md").read_text(encoding="utf-8") for v in dl.index if v != "flat"}
    fixed = re.search(r"fixed \(([\d,]+) of ([\d,]+) cells, (\d+)%\)", reports["lidar"])
    ref = pd.read_csv(CHECKS / "reference_resolution_padang.csv").set_index("name").value
    tiling = pd.read_csv(BENCH["mendahara"] / "04_processed" / "_tiling_check" / "tiling_check.csv")
    load_chk = pd.read_csv(CHECKS / "load_alignment_check.csv").set_index("loader")
    V = {"date": date.today().isoformat(),
         "ref_sd_med": f"{ref['within_block_sd_median_m']:.2f}", "ref_share_gt1": f"{100 * ref['share_blocks_range_gt_1m']:.0f}",
         "ref_dh_1km": f"{ref['block_height_difference_rms_1000m']:.2f}",
         "tiling_max": f"{tiling.max_abs_diff_m.max():.6f}",
         "load_old_nmad": f"{load_chk.loc['old_crop', 'nmad_m']:.2f}", "load_fixed_nmad": f"{load_chk.loc['fixed_crop', 'nmad_m']:.2f}",
         "m_best_1km": fmt(hd("mendahara", "deltadtm__processed")), "s_best_1km": fmt(hd("sugihan_lumpur", "deltadtm__processed")),
         "m_gedtm_1km": fmt(hd("mendahara", "gedtm30__processed")), "s_gedtm_1km": fmt(hd("sugihan_lumpur", "gedtm30__processed")),
         "m_gedtm_raw": fmt(hd("mendahara", "gedtm30")), "s_gedtm_raw": fmt(hd("sugihan_lumpur", "gedtm30")),
         "dl_gd": fmt(dl.loc["gedtm30__processed", "mean_best_iou_vs_lidar"]), "dl_flat": fmt(dl.loc["flat", "mean_best_iou_vs_lidar"]),
         "m_klhk_1km": fmt(hd("mendahara", "klhk_modelled__processed")), "s_klhk_1km": fmt(hd("sugihan_lumpur", "klhk_modelled__processed")),
         "s_rest_range": f"{min(rest):.1f} to {max(rest):.1f}", "m_signal": fmt(sig("mendahara")), "s_signal": fmt(sig("sugihan_lumpur")),
         "dl_dd": fmt(dl.loc["deltadtm__processed", "mean_best_iou_vs_lidar"]), "dl_base": fmt(dl.loc["klhk_modelled_raw", "mean_best_iou_vs_lidar"]),
         "dl_dd_share": f"{100 * dl.loc['deltadtm__processed', 'khg_area_in_matched_overlap']:.0f}",
         "dl_base_share": f"{100 * dl.loc['klhk_modelled_raw', 'khg_area_in_matched_overlap']:.0f}",
         "fixed_pct": fixed.group(3), "median_range": f"+{min(meds):.1f} to +{max(meds):.1f}",
         "m_demnas_raw": fmt(hd("mendahara", "demnas")), "m_demnas_p": fmt(hd("mendahara", "demnas__processed")),
         "s_demnas_raw": fmt(hd("sugihan_lumpur", "demnas")), "s_demnas_p": fmt(hd("sugihan_lumpur", "demnas__processed"))}

    # uncertainty (block bootstrap), canopy test, GEM-15
    ci = {s: pd.read_csv(BENCH[s] / "03_metrics" / "height_difference_ci.csv") for s in SITES}
    cip = {s: pd.read_csv(BENCH[s] / "03_metrics" / "height_difference_ci_paired.csv") for s in SITES}
    can = pd.concat([pd.read_csv(BENCH[s] / "10_canopy" / "canopy_slopes.csv") for s in SITES])
    ucfg = cfg["mendahara"]["uncertainty"]
    main_b = ucfg["block_m"][0]

    def civ(s, c, b=None):
        t = ci[s]
        r = t[(t.candidate == c) & (t.baseline_m == 1000) & (t.block_m == (b or main_b))].iloc[0]
        return r

    def pair(s, c, b):
        t = cip[s]
        return t[(t.candidate == c) & (t.baseline_m == 1000) & (t.block_m == b)].iloc[0]

    kk = {s: pair(s, "klhk_modelled__processed", max(ucfg["block_m"])) for s in SITES}
    V.update({"ci_block_km": f"{main_b / 1000:g}", "ci_draws": f"{ucfg['draws']:,}",
              "m_best_ci": f"{civ('mendahara', 'deltadtm__processed').ci_low_m:.2f} to {civ('mendahara', 'deltadtm__processed').ci_high_m:.2f}",
              "s_best_ci": f"{civ('sugihan_lumpur', 'deltadtm__processed').ci_low_m:.2f} to {civ('sugihan_lumpur', 'deltadtm__processed').ci_high_m:.2f}",
              "m_kk_diff": f"{kk['mendahara'].difference_m:+.3f}", "m_kk_ci": f"{kk['mendahara'].ci_low_m:+.2f} to {kk['mendahara'].ci_high_m:+.2f}",
              "s_kk_diff": f"{kk['sugihan_lumpur'].difference_m:+.3f}", "s_kk_ci": f"{kk['sugihan_lumpur'].ci_low_m:+.2f} to {kk['sugihan_lumpur'].ci_high_m:+.2f}",
              "max_block_km": f"{max(ucfg['block_m']) / 1000:g}",
              "m_blocks": f"{int(civ('mendahara', 'deltadtm__processed').blocks)}", "s_blocks": f"{int(civ('sugihan_lumpur', 'deltadtm__processed').blocks)}",
              "gem_raw": fmt(hd("mendahara", "gem15")), "gem_p": fmt(hd("mendahara", "gem15__processed")),
              "gem_ci": f"{civ('mendahara', 'gem15__processed').ci_low_m:.2f} to {civ('mendahara', 'gem15__processed').ci_high_m:.2f}"})
    cs = can.set_index(["site", "candidate"])
    V.update({"glo_slope": f"{cs.loc[('mendahara', 'glo30'), 'as delivered']:+.2f} to {cs.loc[('mendahara', 'glo30'), 'processed']:+.2f} at Mendahara and "
                           f"{cs.loc[('sugihan_lumpur', 'glo30'), 'as delivered']:+.2f} to {cs.loc[('sugihan_lumpur', 'glo30'), 'processed']:+.2f} at Sugihan-Lumpur",
              "dsm_left": f"{min(cs.loc[(s_, c_), 'processed'] for s_ in SITES for c_ in ('glo30', 'demnas')):.2f} to "
                          f"{max(cs.loc[(s_, c_), 'processed'] for s_ in SITES for c_ in ('glo30', 'demnas')):.2f}",
              "dd_slope": f"{max(abs(cs.loc[(s_, 'deltadtm'), 'processed']) for s_ in SITES):.2f}"})
    gpw = M["mendahara"]["pointwise"].query("reference == 'lidar'")
    V.update({"gem_tree_med": f"{gpw[(gpw.candidate == 'gem15') & (gpw['class'] == 'tree cover')]['median'].iloc[0]:+.1f}",
              "gem_open_med": f"{gpw[(gpw.candidate == 'gem15') & (gpw['class'] == 'grassland')]['median'].iloc[0]:+.1f}"})

    # tables
    bnd = gpd.read_file(DATA / "batas_khg_indonesia.gpkg", layer="nama__khg__indonesia__2017__rev_tipologi")
    site_rows = []
    for s, name in SITES.items():
        c = cfg[s]
        g = bnd[bnd.NAMA_KHG == c["khg"]]
        area = g.to_crs(g.estimate_utm_crs()).area.sum() / 1e6
        n = int(M[s]["pointwise"].query("candidate == 'deltadtm' and `class` == 'all'").n.iloc[0] / M[s]["pointwise"].query("candidate == 'deltadtm' and `class` == 'all'").cover_pct.iloc[0] * 100)
        npts = pyogrio.read_info(DATA / c["processing"]["ground_points"])["features"]
        site_rows.append([html.escape(c["khg"]), f"{area:,.0f}", f"<code>{html.escape(c['lidar']['path'])}</code>", f"{n:,}", fmt(sig(s)), f"{npts:,}"])
    T = {"sites": table(["KHG", "Area (km²)", "LiDAR reference (25 m)", "LiDAR cells inside the KHG", "Real 1 km height difference (m RMS)",
                         "ICESat-2 ATL08 points"], site_rows)}
    cat = pd.read_csv(HUB / "sites" / "data_catalog.csv", dtype=str, keep_default_na=False)

    def cat_src(prefix):
        r = cat[cat.path.str.startswith(prefix)]
        return html.escape(r.source.iloc[0].split(";")[0]) if len(r) else ""

    res = cfg["mendahara"]["processing"]["res_m"]
    drows = []
    for c in CANDS:
        p = cfg["mendahara"]["candidates"][c]["path"]
        folder = p.split("*")[0].rsplit("/", 1)[0] + "/"
        drows.append([LABEL[c], html.escape(cfg["mendahara"]["candidates"][c]["note"].replace(LABEL[c], "").strip(" ,") or cfg["mendahara"]["candidates"][c]["note"]),
                      f"{res[c]:.0f} m" if res[c] >= 8 else f"{res[c]:g} m", cat_src(folder) or cat_src(p.split("/")[0]), f"<code>{html.escape(folder)}</code>"])
    for name, p, what in [("LiDAR DEM (reference)", "lidar_klhk/dem_25m/", "25 m, KLHK archive"), ("ICESat-2 ATL08", "icesat2/", "ground heights 2019 to 2025"),
                          ("ESA WorldCover 2021", "dem/open/worldcover/", "10 m land cover"), ("Meta/WRI canopy height", "canopy/meta_chm_v1/", "1.2 m canopy height")]:
        drows.append([name, what, "", cat_src(p), f"<code>{p}</code>"])
    T["data"] = table(["Dataset", "What it is", "Processed at", "Source (from the data catalogue)", "Folder in _data"], drows)
    steps = [["00", "<code>dem_benchmark.py</code>", "List every input with its sha256", "<code>00_inputs/manifest.csv</code>"],
             ["01", "<code>dem_benchmark.py</code>", "Mosaic each candidate by reference (no copy, no resampling)", "<code>01_candidates/*.vrt</code>"],
             ["02", "<code>dem_benchmark.py</code>", "Candidate minus LiDAR at every LiDAR cell inside the KHG", "<code>02_error_maps/*.tif</code>"],
             ["03", "<code>dem_benchmark.py</code>", "NMAD, error of height differences over 0.5, 1 and 2 km (all cell pairs), variogram, per land cover, tiers",
              "<code>03_metrics/*.csv</code>"],
             ["04", "<code>dem_benchmark_process.py</code>, <code>tiled_dtm.py</code>",
              "repeat-dem method at native resolution: canopy factor and offset per land-cover class fitted to ICESat-2, then despike and smoothing (median 300 m, gaussian 150 m)",
              "<code>04_processed/&lt;candidate&gt;/</code>"],
             ["05", "<code>dem_benchmark_pipeline.py</code>", "Delineation and neraca air (tier 1 and 2) with only the DTM changed; neraca on the LiDAR units",
              "<code>05_pipeline/</code>"]]
    T["steps"] = table(["Step", "Script (repeat-dem/script)", "What it does", "Output (_khg/&lt;code&gt;_&lt;name&gt;/01_dem/benchmark/)"], steps)
    trows = []
    for s, name in SITES.items():
        cr = M[s]["criterion"].query("reference == 'lidar'").set_index("candidate")
        pw = M[s]["pointwise"].query("reference == 'lidar' and `class` == 'all'").set_index("candidate")
        for c in CANDS:
            for k, state in ((c, "as delivered"), (f"{c}__processed", "processed")):
                trows.append([name, LABEL[c], state, fmt(pw.loc[k, "nmad"]), fmt(hd(s, k, 500)), fmt(hd(s, k, 1000)), fmt(hd(s, k, 2000)),
                              "pass" if cr.loc[k, "tier_a_pass"] else "fail", "pass" if cr.loc[k, "tier_b_pass"] else "fail"])
    T["terrain"] = table(["Site", "Candidate", "State", "NMAD (m)", "Δh error 0.5 km (m)", "Δh error 1 km (m)", "Δh error 2 km (m)", "Tier A", "Tier B"],
                         trows, "num", "Against the LiDAR as is; the comparison against the LiDAR smoothed the same way gives the same ranking "
                         "(_khg/&lt;code&gt;_&lt;name&gt;/01_dem/benchmark/README.md). Click a column to sort.")
    lrows = []
    for s, name in SITES.items():
        pw = M[s]["pointwise"].query("reference == 'lidar'")
        for cl in WC_SHOW:
            r = pw[pw["class"] == cl].set_index("candidate")
            if f"deltadtm__processed" not in r.index or r.loc["deltadtm__processed", "cover_pct"] < 2:
                continue
            lrows.append([name, cl, f"{r.loc['deltadtm__processed', 'cover_pct']:.0f}%"] + [fmt(r.loc[f"{c}__processed", "nmad"]) for c in ("deltadtm", "klhk_modelled", "gedtm30", "demnas")])
    T["landcover"] = table(["Site", "Land cover (WorldCover)", "Share of LiDAR cells", "DeltaDTM", "KLHK modelled", "GEDTM30", "DEMNAS"], lrows, "num",
                           "NMAD of candidate minus LiDAR (m) after processing, per land-cover class with at least 2% of the cells.")
    drow = [[v.replace("__processed", ", processed").replace("_raw", ", as used now").replace("klhk_modelled", "KLHK modelled DTM").replace("deltadtm", "DeltaDTM")
             .replace("demnas", "DEMNAS").replace("gedtm30", "GEDTM30").replace("lidar", "LiDAR (reference)").replace("flat", "flat surface (control)"), int(r.units), fmt(r.mean_best_iou_vs_lidar), fmt(r.median_best_iou_vs_lidar),
             f"{100 * r.khg_area_in_matched_overlap:.0f}%"] for v, r in dl.iterrows()]
    T["delineation"] = table(["DTM", "Sub-KHG units", "Mean best-match IoU with LiDAR units", "Median IoU", "KHG area in matched overlap"], drow, "num")
    nrows = []
    for v, txt in reports.items():
        st = re.search(r"Spearman across stations: mean level ([-\d.]+), peak depth ([-\d.]+)", txt)
        bias = re.search(r"\| stations \(cell of each station\) \| ([+\-\d.]+) \|", txt)
        nrows.append([drow[list(dl.index).index(v)][0], st.group(1), st.group(2), bias.group(1)])
    T["neraca"] = table(["DTM", "Rank correlation with stations: mean level", "Rank correlation: peak depth", "Bias at stations (cm)"], nrows, "num",
                        f"Tier 2 groundwater model on a 500 m grid; {fixed.group(1)} of {fixed.group(2)} cells ({fixed.group(3)}%) are canal or edge cells with fixed heads. "
                        "Same forcing and units for every DTM.")
    crow = []
    for s, name in SITES.items():
        for c in ["deltadtm", "klhk_modelled", "gedtm30", "demnas", "fabdem", "glo30", "gem15"]:
            t = ci[s]
            if not ((t.candidate == f"{c}__processed")).any():
                continue
            r = civ(s, f"{c}__processed")
            wide = civ(s, f"{c}__processed", max(ucfg["block_m"]))
            if c == "deltadtm":
                d = "reference"
            else:
                pr, pw_ = pair(s, f"{c}__processed", main_b), pair(s, f"{c}__processed", max(ucfg["block_m"]))
                d = f"{pr.difference_m:+.2f} ({pr.ci_low_m:+.2f} to {pr.ci_high_m:+.2f}; {pw_.ci_low_m:+.2f} to {pw_.ci_high_m:+.2f})"
            crow.append([name, LABEL[c], fmt(r.rms_m), f"{r.ci_low_m:.2f} to {r.ci_high_m:.2f}", f"{wide.ci_low_m:.2f} to {wide.ci_high_m:.2f}", d])
    T["ci"] = table(["Site", "Candidate (processed)", "Δh error 1 km (m)", f"95% interval, {main_b / 1000:g} km blocks",
                     f"95% interval, {max(ucfg['block_m']) / 1000:g} km blocks", f"Minus DeltaDTM (m), interval {main_b / 1000:g} km; {max(ucfg['block_m']) / 1000:g} km"],
                    crow, "num", f"Block bootstrap ({ucfg['draws']:,} draws, seed {ucfg['seed']}) over square blocks of the KHG; each pair of cells belongs to the block of "
                    "its first cell. Same draws for every candidate, so the difference to DeltaDTM has its own interval. Rules written in the site configs "
                    "(<code>uncertainty</code>) before any interval was computed.")
    krow = []
    for _, r in can.iterrows():
        if r.candidate not in LABEL:
            continue
        a, b = r["as delivered"], r["processed"]
        share = f"{100 * (1 - b / a):.0f}%" if abs(a) >= 0.1 else "little to remove"
        krow.append([SITES[r.site], LABEL[r.candidate], f"{a:+.2f}", f"{b:+.2f}", share, "yes" if r.canopy_removed else "no"])
    T["canopy"] = table(["Site", "Candidate", "Slope as delivered (m per m of canopy)", "Slope processed", "Canopy effect removed",
                         "Meets the rule"], krow, "num",
                        "Tree cover only (WorldCover). Least squares on the median error of 2 m canopy-height bins, 0 to 30 m (Meta/WRI canopy height "
                        "averaged into each 25 m LiDAR cell). Rule, written before the run: processed slope within ±0.05 and under a quarter of the "
                        "delivered slope. Sources with almost no slope to begin with fail the second part trivially.")
    T["reproduce"] = table(["Step", "Command (run in repeat-dem unless noted)"], [
        ["Data", "<code>python -m repeat_common.fetch_demnas</code>, <code>fetch_open_dem</code>, <code>fetch_icesat2</code>, <code>repeat_common.gee</code> (see each docstring)"],
        ["00-03", "<code>python script/dem_benchmark.py benchmark/&lt;site&gt;.yaml</code>"],
        ["04", "<code>python script/dem_benchmark_process.py benchmark/&lt;site&gt;.yaml</code>, then step 00-03 again"],
        ["05", "<code>python script/dem_benchmark_pipeline.py benchmark/sugihan_lumpur.yaml</code>"],
        ["Intervals", "<code>python script/dem_benchmark_ci.py benchmark/&lt;site&gt;.yaml</code>"],
        ["Canopy test", "<code>python script/dem_benchmark_canopy.py benchmark/mendahara.yaml benchmark/sugihan_lumpur.yaml</code>"],
        ["Profiles", "<code>python script/dem_benchmark_profile.py benchmark/mendahara.yaml</code>"],
        ["GEM-15 data", "<code>python -m repeat_common.fetch_open_dem --khg \"KHG Sungai Mendahara - Sungai Batanghari\" --product gem15</code>"],
        ["Report", "<code>python tools/dem_benchmark_report.py</code> (in re-peat)"]])
    figs_md = {"error": (NL * 2).join(f"*{name}: candidate minus LiDAR after processing, median removed. Blue = candidate too low, red = too high.*"
                                       + NL * 2 + f"![Error maps, {name}](figures/error_maps_{s}.png)" for s, name in SITES.items()),
               "units": "*Sub-KHG units at Sugihan-Lumpur. Grey: the LiDAR units under each candidate.*" + NL * 2
                        + "![Sub-KHG units](figures/subkhg_units_sugihan_lumpur.png)"}
    pf = BENCH["mendahara"] / "09_profiles"
    cf = BENCH["mendahara"] / "10_canopy" / "canopy_vs_error_light.png"
    extra = {"canopy": (cf, "canopy_vs_error", "Error against canopy height under tree cover, both sites. Grey: as delivered; red: processed. "
                        "A flat processed line means the canopy is removed."),
             "profiles": (pf / "profile_we_candidates_light.png", "profile_we_candidates",
                          "Mendahara, west-east transect through the centre of the LiDAR: every source (grey as delivered, red processed) against the LiDAR (black), same height scale."),
             "gem15": (pf / "profile_we_gem15_light.png", "profile_we_gem15",
                       "Mendahara, same transect: GEM-15 surface (DSM) and terrain (DTM) as delivered against the LiDAR."),
             "transects": (pf / "profile_transects_light.png", "profile_transects", "Where the Mendahara transects run.")}
    figs_md.update({k: f"*{cap}*" + NL * 2 + f"![{name}](figures/{name}.png)" for k, (src, name, cap) in extra.items()})
    figs = {"error": "".join(f'<figure class="map"><figcaption>{name}: candidate minus LiDAR after processing, median removed. Blue = candidate too low, red = too high.</figcaption>'
                             f'<img src="{error_maps(s)}" alt="Error maps, {name}"></figure>' for s, name in SITES.items()),
            **{k: f'<figure class="map"><figcaption>{cap}</figcaption><img src="{file_uri(src, name)}" alt="{name}"></figure>' for k, (src, name, cap) in extra.items()},
            "units": f'<figure class="map"><figcaption>Sub-KHG units at Sugihan-Lumpur. Grey: the LiDAR units under each candidate.</figcaption><img src="{unit_maps()}" alt="Sub-KHG units"></figure>'}

    # prose
    text = (OUT / "report_text.md").read_text(encoding="utf-8").format(**V)
    body, ul, md = [], False, []
    chart_png = dh_chart_png(M)
    for line in text.splitlines():
        m = re.match(r"\[\[(\w+):(\w+)\]\]", line.strip())
        if ul and not line.startswith("- "):
            body.append("</ul>")
            ul = False
        if m:
            kind, name = m.groups()
            body.append(dh_chart(M) if kind == "chart" else html_table(T[name]) if kind == "table" else figs[name])
            md.append("*Error of height differences between LiDAR cells 0.5, 1 and 2 km apart, after processing (lower is better). "
                      "Grey: the real height difference in the LiDAR. Dashed: Tier A.*" + NL * 2 + f"![Height-difference error]({chart_png})"
                      if kind == "chart" else md_table(T[name]) if kind == "table" else figs_md[name])
            continue
        md.append(line)
        inline = re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(line))
        if line.startswith("# "):
            body.append(f"<h1>{inline[2:]}</h1>")
        elif line.startswith("## "):
            sid = re.sub(r"\W+", "-", line[3:].lower()).strip("-")
            body.append(f'<h2 id="{sid}">{inline[3:]}</h2>')
        elif line.startswith("- "):
            if not ul:
                body.append("<ul>")
                ul = True
            body.append(f"<li>{inline[2:]}</li>")
        elif line.strip():
            body.append(f"<p>{inline}</p>")
    if ul:
        body.append("</ul>")
    css_series = "".join(f".s-{c}{{--c:var(--{c})}}" for c in CANDS)
    tok_l = "".join(f"--{c}:{COLOR_L[c]};" for c in CANDS)
    tok_d = "".join(f"--{c}:{COLOR_D[c]};" for c in CANDS)
    page = f"""<title>Peat DTM Benchmark</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400&family=IBM+Plex+Serif:wght@600&display=swap">
<style>
/* layout: one reading column (about 70ch) for prose; tables and figures may run wider, each scrolling inside itself */
:root{{--bg:#fbfbf8;--surface:#ffffff;--fg:#1b1d1a;--muted:#5c605a;--faint:#898781;--rule:#dfe1da;--grid:#e8e9e3;--accent:#1c5cab;--signal:#b9b8b1;
--display:"IBM Plex Serif",Georgia,serif;--body:"IBM Plex Sans",system-ui,"Segoe UI",sans-serif;--mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;{tok_l}}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#141614;--surface:#1a1c19;--fg:#ecede8;--muted:#b8bbb2;--faint:#898781;--rule:#2f322d;--grid:#262924;--accent:#86b6ef;--signal:#5c605a;{tok_d}color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141614;--surface:#1a1c19;--fg:#ecede8;--muted:#b8bbb2;--faint:#898781;--rule:#2f322d;--grid:#262924;--accent:#86b6ef;--signal:#5c605a;{tok_d}color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font:15px/1.6 var(--body)}}
main{{max-width:1100px;margin:0 auto;padding-block:32px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
h1{{font:600 clamp(24px,3.4vw,34px)/1.2 var(--display);text-wrap:balance;max-width:28ch;margin:0 0 8px}}
h2{{font:600 20px/1.3 var(--display);margin:40px 0 8px;padding-top:12px;border-top:1px solid var(--rule);text-wrap:balance}}
p,ul{{max-width:70ch}} li{{margin:4px 0}} code{{font:13px var(--mono);background:var(--grid);padding:1px 4px;border-radius:3px;overflow-wrap:anywhere}}
.note{{font-size:13px;color:var(--muted)}}
.tablewrap{{overflow-x:auto;margin:12px 0 4px}}
table{{border-collapse:collapse;font-size:13.5px;min-width:100%}}
th{{text-align:left;font-weight:600;color:var(--muted);border-bottom:1px solid var(--fg);padding:6px 10px;cursor:pointer;white-space:nowrap}}
td{{border-bottom:1px solid var(--rule);padding:6px 10px;vertical-align:top}}
table.num td{{font-variant-numeric:tabular-nums}} th:focus-visible{{outline:2px solid var(--accent)}}
figure{{margin:18px 0}} figcaption{{font-size:13px;color:var(--muted);margin-bottom:8px;max-width:80ch}}
.panels{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}} .panels svg{{width:100%;height:auto;background:var(--surface);border:1px solid var(--rule);border-radius:6px}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;margin-bottom:8px}} .key{{display:inline-flex;align-items:center;gap:6px}}
.sw{{width:14px;height:3px;border-radius:2px;background:var(--c)}}
{css_series}
.ser{{fill:none;stroke:var(--c);stroke-width:2;stroke-linejoin:round}} .pt{{fill:var(--c);stroke:var(--surface);stroke-width:2}} .pt:hover{{r:6}}
.grid{{stroke:var(--grid);stroke-width:1}} .signal{{fill:none;stroke:var(--signal);stroke-width:2}} .tier{{stroke:var(--faint);stroke-width:1;stroke-dasharray:4 4}}
.tick{{font:11px var(--mono);fill:var(--faint)}} .lab{{font:11px var(--body);fill:var(--fg)}} .lab.muted{{fill:var(--faint)}} .axis{{font:600 12px var(--body);fill:var(--fg)}}
.map img{{width:100%;background:var(--surface);border:1px solid var(--rule);border-radius:6px}}
</style>
<main>
{chr(10).join(body)}
</main>
<script>
document.querySelectorAll("table.sortable").forEach(t=>{{t.querySelectorAll("th").forEach((th,i)=>{{th.tabIndex=0;const go=()=>{{const b=t.tBodies[0],rows=[...b.rows],asc=th.dataset.s!=="a";
rows.sort((x,y)=>{{const p=x.cells[i].innerText,q=y.cells[i].innerText,a=parseFloat(p),c=parseFloat(q);return (isNaN(a)||isNaN(c)?p.localeCompare(q):a-c)*(asc?1:-1)}});
th.dataset.s=asc?"a":"d";rows.forEach(r=>b.appendChild(r))}};th.onclick=go;th.onkeydown=e=>{{if(e.key==="Enter")go()}}}})}});
</script>
"""
    (OUT / "report.html").write_text(page, encoding="utf-8")
    (OUT / "report.md").write_text(re.sub(r"\n{3,}", NL * 2, NL.join(md)) + NL, encoding="utf-8")
    print("wrote", OUT / "report.md")
    print("wrote", OUT / "report.html", f"{(OUT / 'report.html').stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
