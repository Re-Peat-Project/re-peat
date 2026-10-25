"""Draw the DEM benchmark workflow as a draw.io diagram: sources, fetchers, curated data, benchmark steps, pipeline test, report.

    python tools/dem_benchmark_diagram.py [OUT]     # default reports/dem_benchmark/dem_benchmark_workflow.drawio

Layout: five lanes on one row grid. Each dataset has its own row, so it runs source -> fetcher -> _data folder ->
benchmark step along one straight line; a box that takes several inputs spans their rows and each arrow enters at its own
row. Every arrow has fixed exit and entry points, so draw.io does not re-route them. Notes sit in a band below the lanes
with no arrows through them. Counts and results in the labels are read from _data and from the benchmark outputs
(_khg/<code>_<name>/01_dem/benchmark/, repeat-dem/runs/checks/), so rerun this after the benchmark. Open the file in draw.io or the VS Code draw.io extension.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
import pyogrio

HUB = Path(__file__).resolve().parents[1]
WS = HUB.parent
sys.path.insert(0, str(WS / "repeat-common" / "src"))
from repeat_common import khg  # noqa: E402

BENCH = {"mendahara": khg.folder("KHG Sungai Mendahara - Sungai Batanghari") / "01_dem" / "benchmark",
         "sugihan_lumpur": khg.folder("KHG Sungai Sugihan - Sungai Lumpur") / "01_dem" / "benchmark"}
CHECKS = WS / "repeat-dem" / "runs" / "checks"
DATA = Path(os.environ.get("REPEAT_DATA") or WS / "_data")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HUB / "reports" / "dem_benchmark" / "dem_benchmark_workflow.drawio"

STY = {
    "lane": "rounded=1;whiteSpace=wrap;html=1;fillColor={f};strokeColor={s};verticalAlign=top;fontStyle=1;fontSize=14;arcSize=2;",
    "src": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;align=left;spacingLeft=6;",
    "fetch": "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;align=left;spacingLeft=6;",
    "pass": "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#999999;dashed=1;fontSize=11;align=left;spacingLeft=6;",
    "data": "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=7;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;align=left;spacingLeft=6;",
    "step": "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=11;align=left;spacingLeft=6;verticalAlign=top;spacingTop=4;",
    "check": "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;align=left;spacingLeft=6;verticalAlign=top;spacingTop=4;",
    "pipe": "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;align=left;spacingLeft=6;",
    "out": "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=11;align=left;spacingLeft=6;",
    "note": "shape=note;whiteSpace=wrap;html=1;size=12;fillColor=#ffffcc;strokeColor=#b3b300;fontSize=10;align=left;spacingLeft=4;verticalAlign=top;",
    "title": "text;html=1;fontSize=20;fontStyle=1;align=left;verticalAlign=middle;",
    "sub": "text;html=1;fontSize=11;align=left;verticalAlign=top;whiteSpace=wrap;fontColor=#52514e;",
}
EDGE = "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;strokeColor=#52514e;fontSize=10;labelBackgroundColor=#ffffff;"
BR = "<br>"
X = {"A": 20, "B": 320, "C": 610, "D1": 940, "D2": 1270, "E": 1560}
W = {"A": 260, "B": 250, "C": 290, "D1": 300, "D2": 250, "E": 300}
Y0, RH, BH = 210, 82, 58          # first row, row pitch, box height
NOTES_Y = Y0 + 13 * RH + 24

cells, boxes = [], {}


def row_y(r):
    return Y0 + r * RH


def center(r):
    return row_y(r) + BH / 2


def box(name, kind, col, r0, label, r1=None, y=None, h=None, x=None, w=None, **k):
    """A box in lane `col` from row r0 to row r1 (inclusive)."""
    r1 = r0 if r1 is None else r1
    bx, bw = (X[col], W[col]) if x is None else (x, w)
    by = row_y(r0) if y is None else y
    bh = (row_y(r1) + BH - by) if h is None else h
    i = f"n{len(cells) + 2}"
    st = STY[kind].format(**k) if kind == "lane" else STY[kind]
    cells.append(f'<mxCell id="{i}" value="{escape(label, {chr(34): "&quot;"})}" style="{st}" vertex="1" parent="1">'
                 f'<mxGeometry x="{bx}" y="{by}" width="{bw}" height="{bh}" as="geometry"/></mxCell>')
    boxes[name] = (bx, by, bw, bh, i)
    return name


def edge(a, b, ya=None, yb=None, side=("R", "L"), label="", dashed=False, points=()):
    """Arrow from box a to box b. side R/L/B/T picks the exit and entry sides; ya/yb are absolute y on the sides (or None = middle)."""
    ax, ay, aw, ah, ai = boxes[a]
    bx, by, bw, bh, bi = boxes[b]

    def pin(s, x, y, w, h, yy):
        if s == "R":
            return 1, (0.5 if yy is None else (yy - y) / h)
        if s == "L":
            return 0, (0.5 if yy is None else (yy - y) / h)
        if s == "B":
            return 0.5, 1
        return 0.5, 0
    ex, ey = pin(side[0], ax, ay, aw, ah, ya)
    nx, ny = pin(side[1], bx, by, bw, bh, yb)
    st = EDGE + f"exitX={ex:.4f};exitY={ey:.4f};exitDx=0;exitDy=0;entryX={nx:.4f};entryY={ny:.4f};entryDx=0;entryDy=0;" + ("dashed=1;" if dashed else "")
    pts = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in points)
    geo = f'<mxGeometry relative="1" as="geometry">{f"<Array as=\"points\">{pts}</Array>" if pts else ""}</mxGeometry>'
    cells.append(f'<mxCell id="n{len(cells) + 2}" value="{escape(label)}" style="{st}" edge="1" parent="1" source="{ai}" target="{bi}">{geo}</mxCell>')


def results():
    """Numbers for the labels, read from the outputs."""
    v = {}
    for s in ("mendahara", "sugihan_lumpur"):
        hd = pd.read_csv(BENCH[s] / "03_metrics" / "height_difference.csv")
        hd = hd[(hd.reference == "lidar") & (hd.baseline_m == 1000)].set_index("candidate")
        v[s] = {c: hd.loc[c, "rms_m"] for c in hd.index}
        v[s]["signal"] = hd.reference_signal_rms_m.iloc[0]
        cr = pd.read_csv(BENCH[s] / "03_metrics" / "criterion.csv")
        v[s]["any_pass"] = bool(cr.tier_a_pass.any() or cr.tier_b_pass.any())
    pipe = BENCH["sugihan_lumpur"] / "05_pipeline"
    v["iou"] = pd.read_csv(pipe / "delineation_compare.csv").set_index("variant").mean_best_iou_vs_lidar
    v["fixed"] = re.search(r"fixed \(([\d,]+) of ([\d,]+) cells, (\d+)%\)", (pipe / "lidar" / "neraca" / "neraca_report.md").read_text(encoding="utf-8")).group(3)
    v["tiling"] = pd.read_csv(BENCH["mendahara"] / "04_processed" / "_tiling_check" / "tiling_check.csv").max_abs_diff_m.max()
    v["load"] = pd.read_csv(CHECKS / "load_alignment_check.csv").set_index("loader").nmad_m
    v["sheets"] = len(list((DATA / "dem" / "demnas_tiles").glob("DEMNAS_*.tif")))
    v["chm_n"] = len(list((DATA / "canopy" / "meta_chm_v1").glob("*.tif")))
    v["chm_gb"] = sum(f.stat().st_size for f in (DATA / "canopy" / "meta_chm_v1").glob("*.tif")) / 1e9
    v["is"] = [pyogrio.read_info(f)["features"] for f in sorted((DATA / "icesat2").glob("atl08_*.gpkg"))]
    return v


def main():
    v = results()
    m, s = v["mendahara"], v["sugihan_lumpur"]
    box("title", "title", "A", 0, "RE-PEAT DEM benchmark: from raw sources to the DTM choice for sub-KHG neraca air", y=0, h=40, x=20, w=1840)
    box("sub", "sub", "A", 0, "Sites: KHG Sungai Mendahara - Sungai Batanghari (terrain benchmark) and KHG Sungai Sugihan - Sungai Lumpur "
        "(terrain benchmark + pipeline test). Each row is one dataset, read left to right. Rules: nothing downscaled to fit memory; every input kept "
        "in _data and catalogued; every number generated from a file.", y=36, h=36, x=20, w=1840)
    lane_h = NOTES_Y + 290 - 80
    for name, col, x, w, f, st in [("1. External sources", "A", 10, 280, "#eef4fc", "#6c8ebf"), ("2. Fetchers (repeat-common)", "B", 310, 270, "#eef7ec", "#82b366"),
                                   ("3. Curated data (_data, catalogued)", "C", 600, 310, "#fffaeb", "#d6b656"),
                                   ("4. Terrain benchmark (repeat-dem)", "D1", 930, 600, "#f5f0f7", "#9673a6"),
                                   ("5. Pipeline test and outputs", "E", 1550, 320, "#fcf0ef", "#b85450")]:
        box(f"lane_{col}", "lane", col, 0, name, y=80, h=lane_h, x=x, w=w, f=f, s=st)

    # one row per dataset
    rows = [  # row, source, fetcher, data folder
        (0, "<b>BIG Tanahair</b>" + BR + "DEMNAS sheets, 0.27\" (~8 m), surface model",
         "<b>fetch_demnas.py</b>" + BR + "tile index, then download with TANAHAIR_LINK (env only)", f"dem/demnas_tiles/ ({v['sheets']} sheets)"),
        (1, "<b>AWS open data</b>" + BR + "Copernicus GLO-30 (surface model, 30 m)", "<b>fetch_open_dem.py</b> --product glo30", "dem/open/glo30/"),
        (2, "<b>Hugging Face mirror</b>" + BR + "FABDEM v1.2 (bare earth, 30 m)", "<b>fetch_open_dem.py</b> --product fabdem", "dem/open/fabdem/"),
        (3, "<b>Google Earth Engine</b>" + BR + "DeltaDTM v1.1 (coastal DTM, 30 m)", "<b>gee.py</b> (Earth Engine bridge)" + BR + "native grid, chunks under 48 MB",
         "dem/open/deltadtm/"),
        (6, "<b>AWS open data</b>" + BR + "ESA WorldCover 2021 (10 m)", "<b>fetch_open_dem.py</b> --product worldcover", "dem/open/worldcover/"),
        (7, "<b>AWS open data</b>" + BR + "Meta/WRI canopy height (1 m)", "<b>fetch_open_dem.py</b> --product chm", f"canopy/meta_chm_v1/ ({v['chm_n']} tiles, {v['chm_gb']:.1f} GB)"),
        (8, "<b>SlideRule</b>" + BR + "ICESat-2 ATL08 ground heights 2019-2025", "<b>fetch_icesat2.py</b>" + BR + "0.5° tiles, repeat-dem settings",
         "icesat2/ (" + " + ".join(f"{n:,}" for n in v["is"]) + " points)"),
        (9, "<b>REPEAT-LH folder</b>" + BR + "Pulau Padang 2 m LiDAR (Nov 2016)", "<b>copy + sha256 check</b>", "lidar_pulau_padang_2016/"),
    ]
    for r, a, b, c in rows:
        box(f"a{r}", "src", "A", r, a)
        box(f"b{r}", "fetch", "B", r, b)
        box(f"c{r}", "data", "C", r, c)
        edge(f"a{r}", f"b{r}")
        edge(f"b{r}", f"c{r}")
    box("a4", "src", "A", 4, "<b>BRGM / KLHK archive</b> (no metadata)" + BR + "modelled DTMs 10-12 m, LiDAR DEMs 25 m, 25 cm contours", r1=5)
    box("b4", "pass", "B", 4, "no fetch: already on disk," + BR + "catalogued as delivered", r1=5)
    box("c4", "data", "C", 4, "Peat depth and DTM/ (KLHK modelled DTMs)")
    box("c5", "data", "C", 5, "lidar_klhk/dem_25m/ (Jambi25m, OKI25: LiDAR)")
    edge("a4", "b4")
    edge("b4", "c4", ya=center(4), yb=center(4))
    edge("b4", "c5", ya=center(5), yb=center(5))

    # benchmark lane
    box("cfg", "step", "D1", 0, "<b>benchmark/&lt;site&gt;.yaml</b> (tracked)" + BR + "candidates, reference, metrics, pass criterion, processing; written <i>before</i> any result",
        y=110, h=72)
    box("d01", "step", "D1", 0, "<b>Steps 00-01</b> dem_benchmark.py" + BR + "manifest with sha256 of every input" + BR +
        "each candidate as a VRT (mosaic by reference: no copy, no resampling)" + BR + BR + "candidates: DEMNAS, GLO-30, FABDEM, DeltaDTM, KLHK modelled DTM", r1=4)
    box("d02", "step", "D1", 5, "<b>Step 02</b> candidate minus LiDAR at every LiDAR cell inside the KHG")
    box("d04", "step", "D1", 6, "<b>Step 04</b> dem_benchmark_process.py + tiled_dtm.py" + BR + "reads the candidate VRTs of step 01; per candidate, native resolution:" + BR +
        "pass 0 land cover + canopy onto the grid" + BR + "pass 1 fit canopy factor and offset per class to ICESat-2" + BR + "pass 2 correct, despike, smooth, strip by strip", r1=8)
    box("kc", "check", "D1", 9, "<b>Side checks</b>" + BR + "reference_resolution_test.py: 2 m vs 24 m blocks" + BR + "check_contour_source.py, contour_grid_spacing.py" + BR +
        "check_tiling.py, check_load_alignment.py", r1=10)
    box("d03", "step", "D2", 5, "<b>Step 03</b> metrics: NMAD, error of height differences over 0.5/1/2 km, variogram, land cover, tiers")
    box("drs", "step", "D2", 6, "<b>Re-score</b> processed surfaces against the LiDAR and the LiDAR smoothed the same way")
    for r in range(5):
        edge(f"c{r}", "d01", ya=center(r), yb=center(r))
    edge("c5", "d02", label="reference")
    for r in (6, 7, 8):
        edge(f"c{r}", "d04", ya=center(r), yb=center(r))
    edge("c9", "kc", ya=center(9), yb=center(9))
    edge("cfg", "d01", side=("B", "T"))
    edge("d01", "d02", side=("B", "T"))
    edge("d02", "d03")
    edge("d03", "drs", side=("B", "T"))
    edge("d04", "drs", ya=center(6), yb=center(6))

    # pipeline lane
    box("ep", "pipe", "E", 7, "<b>Step 05</b> dem_benchmark_pipeline.py (Sugihan-Lumpur)" + BR + "site configs; only the DTM changes; LiDAR runs as the truth variant")
    box("edl", "pipe", "E", 8, "<b>repeat-delineation</b> per DTM variant" + BR + "sub-KHG units, matched to the LiDAR units (IoU)")
    box("enr", "pipe", "E", 9, "<b>repeat-neraca</b> tier 1 + 2 per DTM variant" + BR + "on the LiDAR units, same forcing")
    box("ecmp", "pipe", "E", 10, "<b>Compare</b> delineation_compare.csv," + BR + "neraca_compare.csv, neraca_unit_compare.csv")
    box("erep", "out", "E", 11, "<b>Report</b> re-peat/reports/dem_benchmark/report.md" + BR + "(tools/dem_benchmark_report.py, from the CSVs)")
    box("edec", "out", "E", 12, "<b>Product</b>: the DTM and processing for sub-KHG delineation and neraca air, with its measured error")
    edge("d04", "ep", ya=center(7), yb=center(7), label="processed DTMs")
    for a, b in (("ep", "edl"), ("edl", "enr"), ("enr", "ecmp"), ("ecmp", "erep"), ("erep", "edec")):
        edge(a, b, side=("B", "T"))
    xr = X["E"] + W["E"] + 14
    edge("drs", "erep", ya=center(6), yb=center(11), side=("R", "R"), label="metrics", points=((xr, center(6)), (xr, center(11))))

    # notes band
    box("nA", "note", "A", 0, "Not reachable / not used" + BR + "- 4TU (home of DeltaDTM): TCP blocked from this machine, so the Earth Engine copy was used" + BR +
        "- GEDTM30: host TLS certificate expired (deferred)" + BR + "- FathomDEM, WorldDEM Neo DTM: skipped by decision" + BR +
        "- KLHK/BRGM: no further data or metadata obtainable", y=NOTES_Y, h=260)
    box("nB", "note", "B", 0, "How the fetchers behave" + BR + "- files kept as delivered (upstream names, no resampling)" + BR + "- files already present are skipped" + BR +
        "- one request at a time, with a pause" + BR + "- the Tanahair link is read from the environment, never saved" + BR + "- wrappers in re-peat/tools/", y=NOTES_Y, h=260)
    box("nC", "note", "C", 0, "Catalogue: re-peat/sites/data_catalog.csv and docs/14-data-catalog.md (tools/catalog_data.py); source, licence, date and caveats per dataset." + BR + BR +
        "Per-KHG availability: docs/16-khg-data-recap.md (tools/khg_data_recap.py).", y=NOTES_Y, h=260)
    box("nD", "note", "D1", 0, "Found along the way" + BR +
        f"- Old repeat-dem loader shifted the DEM by part of a cell: {v['load']['old_crop']:.2f} m NMAD from exact interpolation, {v['load']['fixed_crop']:.2f} m after the fix "
        "(check_load_alignment.py). Earlier repeat-dem runs used the old loader." + BR +
        f"- Strip-by-strip run equals the single-pass run to {v['tiling']:.6f} m (check_tiling.py)." + BR +
        "- Memory: DEMNAS 8 m over Sugihan-Lumpur runs in strips with at least 2 km overlap, never coarsened." + BR +
        "- The 25 cm KLHK contours were traced from the 20/25 m LiDAR; the BRGM contours from the modelled DTMs." + BR +
        "- The LiDAR is held out: it never enters a fit.", y=NOTES_Y, h=260, x=X["D1"], w=W["D1"] + W["D2"] + 30)
    box("nE", "note", "E", 0, "Results" + BR +
        f"1 km height-difference error, processed: DeltaDTM {m['deltadtm__processed']:.2f} / {s['deltadtm__processed']:.2f} m, "
        f"KLHK {m['klhk_modelled__processed']:.2f} / {s['klhk_modelled__processed']:.2f} m (Mendahara / Sugihan-Lumpur); "
        f"real relief {m['signal']:.2f} / {s['signal']:.2f} m." + BR +
        f"Pass criterion (written first): Tier A 0.30 m, Tier B half the real relief: {'some pass' if m['any_pass'] or s['any_pass'] else 'nothing passes'}." + BR +
        f"Delineation, mean IoU with LiDAR units: DeltaDTM {v['iou']['deltadtm__processed']:.2f}, KLHK as used now {v['iou']['klhk_modelled_raw']:.2f}." + BR +
        f"Neraca tier 2: {v['fixed']}% of cells fixed at canals and edge, so it cannot judge the DTMs yet.", y=NOTES_Y, h=260)

    xml = ('<mxfile host="app.diagrams.net"><diagram name="DEM benchmark workflow" id="dem-benchmark">'
           f'<mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" page="1" pageWidth="1920" pageHeight="{NOTES_Y + 320}">'
           '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + "</root></mxGraphModel></diagram></mxfile>")
    OUT.write_text(xml, encoding="utf-8")
    ET.parse(OUT)
    print("valid XML,", len(cells), "cells ->", OUT)


if __name__ == "__main__":
    main()
