"""Write the method diagrams of the project report as draw.io files (re-peat/reports/project_report/diagrams/<id>.drawio).

    .venv/Scripts/python.exe re-peat/tools/project_report_diagrams.py [builder ...]

Every diagram is laid out here for the printed page: the report places it at the full text width (16 cm on A4
portrait), so the content width is fixed at W px and the font sizes below print at the same size in every figure
(printed pt = px x 453 / W). Flows run top to bottom. Diagrams that cannot hold their text legibly on one page are
split into parts <id>_a, <id>_b, ...

Diagrams drawn for the report: toolkit_chain (chapter 2), national_flow (6), neraca_method_report (8a),
neraca_model_boundaries (8b). Reader versions of module diagrams, with plain-language labels (no paths, commands,
option or column names): dem_benchmark_workflow_report (4), delineation_flow_report (5), subkhg_method_report (7),
pump_method_report (9). The originals in the module repositories are not changed.

Colours and font come from project_report_style.py, shared with the charts and the Word styles. Box heights are
measured from the font files (fonts/), so text does not overflow its box.

The .drawio files are the editable source once written: edit them in draw.io. Running this again overwrites them.
check() fails when an edge lacks source or target or is not orthogonal, when a label looks like a file name, option
or column name, when a diagram is wider than W, or when a font is below the minimum.
"""
from __future__ import annotations

import html
import re
import sys
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_report_style import (ACCENT, ACCENT_SOFT, FONT_DIR, INK, MUTED, NATIONAL, NATIONAL_SOFT, RULE,  # noqa: E402
                                  SANS, WARM, WARM_SOFT)

HUB = Path(__file__).resolve().parents[1]
WS = HUB.parent
OUT = HUB / "reports" / "project_report" / "diagrams"

W = 740                    # content width of every diagram, px
TEXT, SMALL = 15, 14       # box text; notes, edge labels, small keys (px). 15 px -> 9.2 pt, 14 px -> 8.6 pt at W
GAP = 20                   # grid step and gutter
PALE, WHITE = "F4F6F6", "FFFFFF"

FONT = f"fontFamily={SANS};fontColor=#{INK};"
BOX = "rounded=1;absoluteArcSize=1;arcSize=12;whiteSpace=wrap;html=1;spacing=6;strokeWidth=1.25;"


def _fill(fill: str, stroke: str) -> str:
    return f"fillColor={'none' if fill == 'none' else '#' + fill};strokeColor=#{stroke};"


ST = {
    "proc": BOX + _fill(ACCENT_SOFT, ACCENT),
    "review": BOX.replace("strokeWidth=1.25", "strokeWidth=3") + _fill(ACCENT_SOFT, ACCENT),
    "nat": BOX + _fill(NATIONAL_SOFT, NATIONAL),
    "out": BOX + _fill(WARM_SOFT, WARM),
    "input": BOX + _fill(WHITE, MUTED),
    "data": "shape=parallelogram;perimeter=parallelogramPerimeter;fixedSize=1;size=12;whiteSpace=wrap;html=1;spacing=6;"
            "spacingLeft=10;spacingRight=10;strokeWidth=1.25;" + _fill(WHITE, MUTED),
    "store": "shape=cylinder3;boundedLbl=1;size=8;whiteSpace=wrap;html=1;spacing=6;strokeWidth=1.25;" + _fill(WHITE, MUTED),
    "outstore": "shape=cylinder3;boundedLbl=1;size=8;whiteSpace=wrap;html=1;spacing=6;strokeWidth=1.25;"
                + _fill(WARM_SOFT, WARM),
    "user": BOX + _fill(WHITE, WARM),
    "grey": BOX + _fill(PALE, RULE) + f"dashed=1;fontColor=#{MUTED};",
    "param": BOX + _fill(PALE, MUTED),
    "note": BOX + _fill(PALE, RULE),
    "lane": "lane=1;rounded=1;absoluteArcSize=1;arcSize=12;whiteSpace=wrap;html=1;strokeWidth=1.25;" + _fill("none", RULE)
            + f"dashed=1;verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;fontStyle=1;fontColor=#{MUTED};",
    "laneb": "lane=1;rounded=1;absoluteArcSize=1;arcSize=12;whiteSpace=wrap;html=1;strokeWidth=1.25;" + _fill("none", RULE)
             + f"dashed=1;verticalAlign=bottom;align=left;spacingLeft=10;spacingBottom=6;fontStyle=1;fontColor=#{MUTED};",
    "laner": "lane=1;rounded=1;absoluteArcSize=1;arcSize=12;whiteSpace=wrap;html=1;strokeWidth=1.25;" + _fill("none", RULE)
             + f"dashed=1;verticalAlign=top;align=right;spacingRight=12;spacingTop=4;fontStyle=1;fontColor=#{MUTED};",
    "head": f"text;html=1;whiteSpace=wrap;align=left;verticalAlign=bottom;spacingLeft=0;fontStyle=1;fontColor=#{MUTED};",
    "diamond": "rhombus;whiteSpace=wrap;html=1;spacing=6;strokeWidth=1.25;" + _fill(ACCENT_SOFT, ACCENT),
}
LANE_MARK = "lane=1;"                     # identifies lanes (drawn first, never an edge end)
LEFT = "align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;"
EDGE = ("edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=1.25;"
        f"strokeColor=#{MUTED};endArrow=block;endFill=1;endSize=7;fontFamily={SANS};fontSize={SMALL};fontColor=#{INK};"
        "labelBackgroundColor=#FFFFFF;jumpStyle=arc;jumpSize=8;")
TWO_WAY = "startArrow=block;startFill=1;startSize=7;"
DASHED = "dashed=1;"
LANE_TOP = 40              # space for a lane title above the first box


# ---------------------------------------------------------------------------------------------- text measurement

@lru_cache(maxsize=None)
def _font(size: int, bold: bool):
    from PIL import ImageFont
    return ImageFont.truetype(str(FONT_DIR / f"SourceSans3-{'Bold' if bold else 'Regular'}.ttf"), size)


def _words(seg: str):
    """(word, bold) pairs of one line of an html label."""
    out, bold = [], False
    for tok in re.split(r"(<[^>]+>)", seg):
        if tok.startswith("<"):
            t = tok.lower().replace(" ", "")
            bold = True if t in ("<b>",) else False if t in ("</b>",) else bold
            continue
        for w in html.unescape(tok).split():
            out.append((w, bold))
    return out


def lines(text: str, width: float, size: int) -> int:
    """Number of lines draw.io wraps an html label into at this width."""
    n = 0
    for seg in re.split(r"<br\s*/?>", text):
        words = _words(seg)
        if not words:
            n += 1
            continue
        n += 1
        x = 0.0
        for w, b in words:
            f = _font(size, b)
            ww = f.getlength(w)
            sp = f.getlength(" ")
            if x and x + sp + ww > width:
                n += 1
                x = ww
            else:
                x += (sp if x else 0) + ww
    return n


def fit(text: str, w: float, size: int, kind: str, left: bool) -> int:
    """Box height that holds the text, rounded up to 4 px."""
    avail = w - 12 - (8 if left else 0) - 6                     # spacing, spacingLeft, safety for wrapping
    pad = 14 + (4 if left else 0)
    if kind == "data":
        avail -= 32
    if kind in ("store", "outstore"):
        pad += 18
    if kind == "diamond":
        avail = w * 0.55
        pad = 0
    h = lines(text, avail, size) * size * 1.2 + pad
    if kind == "diamond":
        h = h * 2 + 10
    return int(-(-h // 4) * 4)


# ---------------------------------------------------------------------------------------------- diagram

def vstyle(kind: str, size: int, left: bool = False) -> str:
    return FONT + ST[kind] + f"fontSize={size};" + (LEFT if left and not kind.startswith("lane") and kind != "head" else "")


def ex(x, y):   # exit constraint
    return f"exitX={x};exitY={y};exitDx=0;exitDy=0;"


def en(x, y):   # entry constraint
    return f"entryX={x};entryY={y};entryDx=0;entryDy=0;"


def _r(v: float) -> float:
    return round(min(max(v, 0.0), 1.0), 4)


class Diagram:
    def __init__(self, ident: str, name: str):
        self.ident, self.name, self.cells, self.geo = ident, name, [], {}

    def box(self, cid, text, x, y, w, h=None, kind="proc", size=TEXT, left=False) -> float:
        """Add a box; height from the text when h is None. Returns the bottom edge."""
        if h is None:
            h = fit(text, w, size, kind, left)
        self.geo[cid] = (x, y, w, h)
        self.cells.append(("v", cid, text, vstyle(kind, size, left), (x, y, w, h), None))
        return y + h

    def bottom(self, cid) -> float:
        x, y, w, h = self.geo[cid]
        return y + h

    def cy(self, cid) -> float:
        x, y, w, h = self.geo[cid]
        return y + h / 2

    def cx(self, cid) -> float:
        x, y, w, h = self.geo[cid]
        return x + w / 2

    def fx(self, cid, x) -> float:      # x as a fraction of the box width
        bx, by, bw, bh = self.geo[cid]
        return _r((x - bx) / bw)

    def fy(self, cid, y) -> float:
        bx, by, bw, bh = self.geo[cid]
        return _r((y - by) / bh)

    def straight(self, src, tgt) -> str:
        """Exit/entry constraints for a straight line between two boxes that overlap in x or y, else ''."""
        ax, ay, aw, ah = self.geo[src]
        bx, by, bw, bh = self.geo[tgt]
        if bx >= ax + aw or bx + bw <= ax:                    # side by side
            lo, hi = max(ay, by) + 8, min(ay + ah, by + bh) - 8
            if hi < lo:
                return ""
            c = ay + ah / 2
            if not lo <= c <= hi:
                c = by + bh / 2 if lo <= by + bh / 2 <= hi else (lo + hi) / 2
            right = bx >= ax + aw
            return ex(1 if right else 0, self.fy(src, c)) + en(0 if right else 1, self.fy(tgt, c))
        lo, hi = max(ax, bx) + 8, min(ax + aw, bx + bw) - 8
        if hi < lo:
            return ""
        c = ax + aw / 2
        if not lo <= c <= hi:
            c = bx + bw / 2 if lo <= bx + bw / 2 <= hi else (lo + hi) / 2
        down = by >= ay + ah
        return ex(self.fx(src, c), 1 if down else 0) + en(self.fx(tgt, c), 0 if down else 1)

    def edge(self, cid, src, tgt, label="", style="", points=None):
        if "exitX" not in style and "entryX" not in style and points is None:
            style += self.straight(src, tgt)
        self.cells.append(("e", cid, label, EDGE + style, (src, tgt), points))

    def bounds(self):
        xs, ys = [], []
        for kind, cid, text, style, geo, pts in self.cells:
            if kind == "v":
                x, y, w, h = geo
                xs += [x, x + w]
                ys += [y, y + h]
            for px, py in pts or ():
                xs.append(px)
                ys.append(py)
        return min(xs), min(ys), max(xs), max(ys)

    def write(self) -> Path:
        x0, y0, x1, y1 = self.bounds()
        mx = ET.Element("mxfile", host="drawio")
        dg = ET.SubElement(mx, "diagram", id=self.ident, name=self.name)
        model = ET.SubElement(dg, "mxGraphModel", dx="1200", dy="800", grid="1", gridSize="10", guides="1", tooltips="1",
                              connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth=str(round(x1 - x0)),
                              pageHeight=str(round(y1 - y0)), math="0", shadow="0")
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")
        lanes = [c for c in self.cells if c[0] == "v" and LANE_MARK in c[3]]
        rest = [c for c in self.cells if c not in lanes]
        for kind, cid, text, style, geo, pts in lanes + [c for c in rest if c[0] == "v"] + [c for c in rest if c[0] == "e"]:
            if kind == "v":
                c = ET.SubElement(root, "mxCell", id=cid, value=text, style=style, vertex="1", parent="1")
                x, y, w, h = geo
                ET.SubElement(c, "mxGeometry", x=f"{x - x0:g}", y=f"{y - y0:g}", width=f"{w:g}", height=f"{h:g}",
                              **{"as": "geometry"})
            else:
                c = ET.SubElement(root, "mxCell", id=cid, value=text, style=style, edge="1", parent="1",
                                  source=geo[0], target=geo[1])
                g = ET.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})
                if pts:
                    arr = ET.SubElement(g, "Array", **{"as": "points"})
                    for px, py in pts:
                        ET.SubElement(arr, "mxPoint", x=f"{px - x0:g}", y=f"{py - y0:g}")
        ET.indent(mx)
        path = OUT / f"{self.ident}.drawio"
        ET.ElementTree(mx).write(path, encoding="utf-8", xml_declaration=False)
        return path


def legend(d: Diagram, y: float, items) -> float:
    """One row key: (kind, text) boxes after a 'Key' heading. Returns the bottom edge."""
    d.box("key", "Key", 0, y, 40, 36, "head", SMALL)
    x = 50
    for i, (kind, text) in enumerate(items):
        w = max(70, round(_font(SMALL, False).getlength(text)) + 30)
        d.box(f"key{i}", text, x, y, w, 36, kind, SMALL)
        x += w + 10
    return y + 36


# ---------------------------------------------------------------------------------------------- chapter 2

def toolkit_chain() -> Path:
    d = Diagram("toolkit_chain", "RE-PEAT chain")
    bh = 60
    y = d.box("data", "<b>National data</b><br>boundaries, fire, canals, peat", 20, 0, 340, bh, "data")
    d.box("national", "<b>National prioritisation</b><br>all 865 KHG", 400, 0, 340, bh, "nat")
    d.edge("e8", "data", "national")
    cx, cw = 20, 620
    y = d.box("inputs", "<b>KHG inputs</b><br>national layers cut to the KHG", cx, y + 36, cw, bh) + 36
    lane_y = y
    y += 20
    steps = [("dem", "<b>DEM correction</b><br>per DEM", "proc"), ("delin", "<b>Sub-KHG delineation</b>", "proc"),
             ("neraca", "<b>Neraca air</b><br>balance, deficit", "proc"),
             ("prio", "<b>Sub-KHG prioritisation</b>", "proc"),
             ("interv", "<b>RE-PEAT Interventions</b><br>canal blocks, pumps, budget, map layouts", "out")]
    for cid, t, k in steps:
        y = d.box(cid, t, cx + 20, y, cw - 20, bh, k) + 32
    d.box("perdem", "Runs once per elevation model: LiDAR, DeltaDTM, DEMNAS", 0, lane_y, W, y + 8 - lane_y, "laneb")
    chain = ["data", "inputs", "dem", "delin", "neraca", "prio", "interv"]
    for i, (a, b) in enumerate(zip(chain, chain[1:]), 1):
        d.edge(f"e{i}", a, b, style=ex(d.fx(a, 190), 1) + en(d.fx(b, 190), 0) if i <= 2 else "")
    d.edge("e7", "neraca", "interv", style=ex(1, 0.5) + en(1, 0.5),
           points=[(cx + cw + 40, d.cy("neraca")), (cx + cw + 40, d.cy("interv"))])
    return d.write()


# ---------------------------------------------------------------------------------------------- chapter 4

def dem_benchmark_workflow_report() -> list[Path]:
    """Reader version of re-peat/reports/dem_benchmark/dem_benchmark_workflow.drawio, in three parts:
    a: sources and downloads; b: terrain benchmark; c: pipeline test and results."""
    L = {
        "n4": "1. External sources", "n5": "2. Download", "n6": "3. Project data, catalogued",
        "n7": "4. Terrain benchmark", "n8": "5. Pipeline test and outputs",
        "n9": "<b>BIG Tanahair</b><br>DEMNAS sheets, about 8 m, surface model", "n10": "Sheet index, then download",
        "n11": "DEMNAS sheets (31)",
        "n14": "<b>AWS open data</b><br>Copernicus GLO-30 (surface model, 30 m)", "n15": "Download", "n16": "GLO-30",
        "n19": "<b>Hugging Face mirror</b><br>FABDEM (bare earth, 30 m)", "n20": "Download", "n21": "FABDEM",
        "n24": "<b>Google Earth Engine</b><br>DeltaDTM (coastal DTM, 30 m)",
        "n25": "Earth Engine export<br>native grid, in chunks", "n26": "DeltaDTM",
        "n29": "<b>AWS open data</b><br>ESA WorldCover 2021 (10 m)", "n30": "Download", "n31": "Land cover",
        "n34": "<b>AWS open data</b><br>Meta/WRI canopy height (1 m)", "n35": "Download",
        "n36": "Canopy height (8 tiles, 4.0 GB)",
        "n39": "<b>SlideRule</b><br>ICESat-2 ground heights 2019-2025", "n40": "Download by 0.5° tile",
        "n41": "ICESat-2 points (68,979 and 266,462)",
        "n44": "<b>Earlier project data</b><br>Pulau Padang 2 m LiDAR (November 2016)", "n45": "Copy with checksum",
        "n46": "Pulau Padang LiDAR",
        "n49": "<b>BRGM / KLHK archive</b> (no metadata)<br>modelled DTMs 10-12 m, LiDAR DEMs 25 m, 25 cm contours",
        "n50": "No download: already held by the project, catalogued as delivered", "n51": "KLHK modelled DTMs",
        "n52": "KLHK LiDAR DEMs, 25 m (Jambi, OKI)",
        "n56": "<b>Benchmark plan per site</b><br>candidates, reference, metrics, pass criterion; written <i>before</i> any result",
        "n57": "<b>Steps 0-1: inputs</b><br>checksum of every input<br>each candidate read as delivered: no copy, no "
               "resampling<br><br>candidates: DEMNAS, GLO-30, FABDEM, DeltaDTM, KLHK modelled DTM",
        "n58": "<b>Step 2</b><br>candidate minus LiDAR at every LiDAR cell inside the KHG",
        "n59": "<b>Step 4: processing</b>, per candidate at native resolution<br>land cover and canopy onto the grid<br>"
               "fit canopy factor and offset per class to ICESat-2<br>correct, despike, smooth, strip by strip",
        "n60": "<b>Side checks</b><br>reference resolution (2 m against 24 m blocks), contour source and spacing, "
               "tiling, load alignment",
        "n61": "<b>Step 3: metrics</b><br>NMAD, error of height differences over 0.5, 1 and 2 km, variogram, land cover, tiers",
        "n62": "<b>Re-score</b> processed surfaces against the LiDAR and the LiDAR smoothed the same way",
        "n78": "<b>Step 5: pipeline test</b> (Sugihan-Lumpur)<br>only the DTM changes; the LiDAR runs as the reference",
        "n79": "<b>Sub-KHG delineation</b> per DTM<br>units matched to the LiDAR units (IoU)",
        "n80": "<b>Neraca air</b> physical tiers 1 and 2 per DTM<br>on the LiDAR units, same forcing",
        "n81": "<b>Compare</b> delineation and neraca air results",
        "n82": "<b>Benchmark report</b>, generated from the comparison tables",
        "n83": "<b>Product</b>: the DTM and processing for sub-KHG delineation and neraca air, with its measured error",
        "n91": "<b>Not reachable or not used</b><br>• DeltaDTM home repository: connection blocked, so the Earth Engine copy "
               "was used<br>• GEDTM30: host certificate expired (deferred)<br>• FathomDEM, WorldDEM Neo DTM: skipped by "
               "decision<br>• KLHK/BRGM: no further data or metadata obtainable",
        "n92": "<b>How downloads behave</b><br>• files kept as delivered, no resampling<br>• files already present are "
               "skipped<br>• one request at a time, with a pause<br>• the Tanahair access link is never saved",
        "n93": "<b>Data catalogue</b>: source, licence, date and caveats per dataset<br><br><b>Per-KHG data recap</b>: "
               "which data cover each KHG",
        "n94": "<b>Found along the way</b><br>• The earlier DEM loader shifted the surface by part of a cell: 0.25 m NMAD "
               "against exact interpolation, 0.01 m after the fix. Earlier DEM correction runs used the old loader.<br>"
               "• A strip-by-strip run equals the single-pass run to 0.000000 m.<br>• Memory: DEMNAS 8 m over "
               "Sugihan-Lumpur runs in strips with at least 2 km overlap, never coarsened.<br>• The 25 cm KLHK contours "
               "were traced from the 20/25 m LiDAR; the BRGM contours from the modelled DTMs.<br>• The LiDAR is held "
               "out: it never enters a fit.",
        "n95": "<b>Results</b><br>1 km height-difference error, processed: DeltaDTM 0.64 / 0.47 m, KLHK 0.67 / 0.49 m "
               "(Mendahara / Sugihan-Lumpur); real relief 0.46 / 0.38 m.<br>Pass criterion (written first): Tier A "
               "0.30 m, Tier B half the real relief: nothing passes.<br>Delineation, mean IoU with LiDAR units: "
               "DeltaDTM 0.48, KLHK as used then 0.40.<br>Neraca air tier 2: 77 % of cells fixed at canals and edge, so "
               "it cannot judge the DTMs yet.",
    }
    paths = []
    # --- a: sources, downloads, catalogued data
    d = Diagram("dem_benchmark_workflow_report_a", "DEM benchmark: data")
    c1, w1, c2, w2, c3, w3 = 0, 300, 340, 170, 550, 190
    d.box("h1", L["n4"], c1, 0, w1, 28, "head")
    d.box("h2", L["n5"], c2, 0, w2, 28, "head")
    d.box("h3", L["n6"], c3, 0, w3, 28, "head")
    rows = [("n9", "n10", ["n11"]), ("n14", "n15", ["n16"]), ("n19", "n20", ["n21"]), ("n24", "n25", ["n26"]),
            ("n29", "n30", ["n31"]), ("n34", "n35", ["n36"]), ("n39", "n40", ["n41"]), ("n44", "n45", ["n46"]),
            ("n49", "n50", ["n51", "n52"])]
    y = 40
    for src, dl, stores in rows:
        hs = fit(L[src], w1, TEXT, "input", False)
        hd = fit(L[dl], w2, TEXT, "proc", False)
        hst = [fit(L[s], w3, TEXT, "store", False) for s in stores]
        h = max(hs, hd, sum(hst) + 10 * (len(hst) - 1))
        d.box(src, L[src], c1, y, w1, h, "input")
        d.box(dl, L[dl], c2, y, w2, h, "grey" if dl == "n50" else "proc")
        if len(stores) == 1:
            d.box(stores[0], L[stores[0]], c3, y, w3, h, "store")
        else:
            yy = y
            for s, hh in zip(stores, hst):
                yy = d.box(s, L[s], c3, yy, w3, (h - 10) / 2, "store") + 10
        y += h + 14
    for src, dl, stores in rows:
        d.edge(f"e_{src}", src, dl)
        for s in stores:
            d.edge(f"e_{s}", dl, s)
    y += 16
    y = d.box("n91", L["n91"], 0, y, W, None, "note", SMALL, left=True) + 14
    hn = max(fit(L["n92"], 360, SMALL, "note", True), fit(L["n93"], 370, SMALL, "note", True))
    d.box("n92", L["n92"], 0, y, 360, hn, "note", SMALL, left=True)
    d.box("n93", L["n93"], 370, y, 370, hn, "note", SMALL, left=True)
    paths.append(d.write())

    # --- b: terrain benchmark (steps 0-4)
    d = Diagram("dem_benchmark_workflow_report_b", "DEM benchmark: terrain benchmark")
    lx, lw, rx, rw = 20, 210, 310, 410
    y = LANE_TOP
    y = d.box("n56", L["n56"], rx, y, rw, None, "param") + 30
    n57 = L["n57"].replace("<br><br>candidates: DEMNAS, GLO-30, FABDEM, DeltaDTM, KLHK modelled DTM", "")
    y57 = y
    y = d.box("n57", n57, rx, y, rw, None) + 30
    cand = "<b>Candidates</b><br>DEMNAS, GLO-30, FABDEM, DeltaDTM, KLHK modelled DTMs"
    hc = max(d.geo["n57"][3], fit(cand, lw, TEXT, "store", False))
    d.box("cand", cand, lx, y57, lw, hc, "store")
    _reheight(d, "n57", h=hc)
    y = y57 + hc + 30
    y58 = y
    y = d.box("n58", L["n58"], rx, y, rw, None) + 30
    hr = max(d.geo["n58"][3], fit(L["n52"], lw, TEXT, "store", False))
    d.box("ref", L["n52"], lx, y58, lw, hr, "store")
    _reheight(d, "n58", h=hr)
    y = y58 + hr + 30
    y = d.box("n61", L["n61"], rx, y, rw, None) + 30
    y62 = y
    y = d.box("n62", L["n62"], rx, y, rw, None) + 30
    aux = "Land cover · canopy height · ICESat-2 points"
    ya = d.geo["n61"][1]
    d.box("aux", aux, lx, ya, lw, fit(aux, lw, TEXT, "store", False), "store")
    y59 = max(d.bottom("aux") + 30, y62 + d.geo["n62"][3] / 2 - 60)
    d.box("n59", L["n59"], lx, y59, lw, None)
    y = max(y, d.bottom("n59") + 30)
    d.box("pp", L["n46"], lx, y, lw, None, "store")
    y = d.box("n60", L["n60"], rx, y, rw, None, "grey")
    _reheight(d, "pp", h=d.geo["n60"][3])
    for e, s, t, lab in (("n73", "n56", "n57", ""), ("n74", "n57", "n58", ""), ("n75", "n58", "n61", ""),
                         ("n76", "n61", "n62", ""), ("n63", "cand", "n57", ""), ("n68", "ref", "n58", "reference"),
                         ("n69", "aux", "n59", ""), ("n72", "pp", "n60", "")):
        d.edge(e, s, t, lab)
    yc = d.cy("n59")
    d.edge("n77", "n59", "n62", style=ex(1, 0.5) + en(0, d.fy("n62", min(max(yc, d.geo["n62"][1] + 10),
                                                                         d.bottom("n62") - 10))),
           points=[(270, yc), (270, min(max(yc, d.geo["n62"][1] + 10), d.bottom("n62") - 10))]
           if not d.geo["n62"][1] + 8 <= yc <= d.bottom("n62") - 8 else None)
    d.box("lane4", L["n7"], 0, 0, W, y + GAP, "lane")
    y += GAP + 20
    d.box("n94", L["n94"], 0, y, W, None, "note", SMALL, left=True)
    paths.append(d.write())

    # --- c: pipeline test and results
    d = Diagram("dem_benchmark_workflow_report_c", "DEM benchmark: pipeline test")
    lx, lw, rx, rw = 20, 320, 380, 320
    y = LANE_TOP
    d.box("proc4", "<b>Processed DTMs</b><br>from step 4", lx, y, lw, None, "store")
    y = d.box("met", "<b>Metrics</b><br>from step 3 and the re-score", rx, y, rw, d.geo["proc4"][3], "store") + 30
    y = d.box("n78", L["n78"], lx, y, lw, None) + 30
    y = d.box("n79", L["n79"], lx, y, lw, None) + 30
    y = d.box("n80", L["n80"], lx, y, lw, None)
    d.box("n81", L["n81"], rx, d.geo["n80"][1], rw, d.geo["n80"][3])
    y82 = d.geo["n79"][1]
    d.box("n82", L["n82"], rx, y82, rw, d.geo["n79"][3], "out")
    d.box("n83", L["n83"], rx, d.geo["n78"][1], rw, d.geo["n78"][3], "out")
    d.edge("n84", "proc4", "n78")
    for e, s, t in (("n85", "n78", "n79"), ("n86", "n79", "n80"), ("n87", "n80", "n81"), ("n88", "n81", "n82"),
                    ("n89", "n82", "n83")):
        d.edge(e, s, t)
    d.edge("n90", "met", "n82", style=ex(1, 0.5) + en(1, 0.5),
           points=[(rx + rw + 10, d.cy("met")), (rx + rw + 10, d.cy("n82"))])
    d.box("lane5", L["n8"], 0, 0, W, y + GAP, "lane")
    y += GAP + 20
    d.box("n95", L["n95"], 0, y, W, None, "note", SMALL, left=True)
    paths.append(d.write())
    return paths


# ---------------------------------------------------------------------------------------------- chapter 5

def _pair(d: Diagram, a: str, b: str):
    """Give two side-by-side boxes the same top and height (the taller of the two)."""
    h = max(d.geo[a][3], d.geo[b][3])
    y = min(d.geo[a][1], d.geo[b][1])
    for c in (a, b):
        d.geo[c] = (d.geo[c][0], y, d.geo[c][2], h)
    _reheight(d, a, b)
    return y + h


def delineation_flow_report() -> list[Path]:
    """Reader version of repeat-delineation/docs/delineation_flow.drawio, in two parts:
    a: inputs and steps 1-5; b: steps 6-10, outputs and the modules that read them."""
    L = {
        "laneA": "Inputs", "laneB": "Processing", "laneC": "Outputs", "laneD": "Read by",
        "khg": "<b>KHG boundary</b>",
        "dtm": "<b>Ground DTM</b><br>corrected DTM or LiDAR; a surface model gives wrong catchments",
        "riv": "<b>Rivers and lakes</b><br>always unit boundaries",
        "can": "<b>Canals by class</b><br>primary, secondary, tertiary",
        "g": "<b>1. Grid</b><br>30 m grid over the KHG plus 1 km",
        "w": "<b>2. DTM onto the grid</b><br>bilinear; cells without DTM leave the KHG (warning above 1 %)",
        "ch": "<b>3. Channel masks</b><br>rivers and lakes; all canals; <b>outlet canals</b>: primary and secondary "
              "canals<br>outlets = rivers + outlet canals",
        "b": "<b>4. Burn</b><br>DTM lowered 3 m under rivers and all canals (canals are narrower than a cell)",
        "d8": "<b>5. Condition and route</b><br>fill pits and depressions, resolve flats; D8 flow direction; flow accumulation",
        "so": "<b>6. DEM streams</b><br>from 2 km² of contributing area; Strahler order",
        "os": "<b>7. Choose the outlet set</b><br>mapped outlets alone first; if the unit count is outside 6-30, add DEM "
              "streams from the highest order down",
        "pc": "<b>8. Pieces</b><br>outlet network cut into reaches at junctions; every cell traced downstream to its "
              "first outlet cell = the catchment of that reach, split by bank. Flow leaving the KHG without an outlet: "
              "coastal catchments, cut into pieces of about 50 km²",
        "mg": "<b>9. Merge small pieces</b><br>pieces under the minimum area join, smallest first, the neighbour with the "
              "longest shared <i>divide</i> (a border across an outlet channel only if there is no divide neighbour). "
              "Minimum area starts at 5 km² and rises 10 % at a time until at most 30 units remain",
        "fn": "<b>10. Units</b><br>channel cells go to the nearest unit; clipped to the KHG; polygons numbered north to south",
        "fb": "<b>Fallback</b><br>no flow directions: units = land enclosed by the mapped outlets; target count ignored",
        "acc": "<b>Flow accumulation</b> grid", "ord": "<b>Stream order</b> grid",
        "un": "<b>Sub-KHG units</b><br>polygons", "rp": "<b>Delineation report</b><br>settings, inputs, pieces, units, areas",
        "nr": "<b>Neraca air</b><br>water balance per unit", "pr": "<b>Sub-KHG prioritisation</b><br>ranking and map page",
        "n2": "<b>Stability at Sugihan-Lumpur</b> (adjusted Rand index against the LiDAR run; 1 = identical, 0 = chance)"
              "<br>Primary outlets: noisy LiDAR copies 0.471 · other DTMs 0.48 · flat surface 0.348 · 24-30 units"
              "<br>Primary and secondary: 0.633 · 0.629 · 0.601 · 26-30 units"
              "<br>Primary and secondary, merged by flow line: 0.603 · 0.606 · 0.569 · 26-30 units",
        "n3": "<b>Where the boundaries come from</b><br>mapped outlets (rivers, outlet canals) are fixed boundaries; inside "
              "them the DTM decides only the divides (steps 4-8), and step 9 decides which pieces join. Without outlets "
              "inside the KHG, small DTM changes move the divides and the merges",
    }
    paths = []
    lx, lw, rx, rw = 0, 260, 300, 440
    # --- a
    d = Diagram("delineation_flow_report_a", "Sub-KHG delineation: inputs and routing")
    d.box("ha", L["laneA"], lx, 0, lw, 28, "head")
    d.box("hb", L["laneB"], rx, 0, rw, 28, "head")
    y = 40
    d.box("g", L["g"], rx, y, rw, None)
    d.box("khg", L["khg"], lx, y, lw, None, "store")
    y = _pair(d, "g", "khg") + 30
    d.box("w", L["w"], rx, y, rw, None)
    d.box("dtm", L["dtm"], lx, y, lw, None, "store")
    y = _pair(d, "w", "dtm") + 30
    yr = d.box("riv", L["riv"], lx, y, lw, None, "store") + 12
    yr = d.box("can", L["can"], lx, yr, lw, None, "store")
    d.box("ch", L["ch"], rx, y, rw, max(yr - y, fit(L["ch"], rw, TEXT, "proc", False)))
    y = d.bottom("ch") + 30
    y = d.box("b", L["b"], rx, y, rw, None) + 30
    d.box("d8", L["d8"], rx, y, rw, None)
    d.box("acc", L["acc"], lx, y, lw, None, "outstore")
    y = _pair(d, "d8", "acc") + 36
    y = d.box("fb", L["fb"], rx, y, rw, None, "grey") + 30
    for e, s, t in (("e27", "khg", "g"), ("e28", "dtm", "w"), ("e29", "riv", "ch"), ("e30", "can", "ch"),
                    ("e31", "g", "w"), ("e32", "w", "ch"), ("e33", "ch", "b"), ("e34", "b", "d8"),
                    ("e40", "d8", "acc")):
        d.edge(e, s, t)
    d.edge("e42", "d8", "fb", "fails")
    d.box("n3", L["n3"], 0, y, W, None, "note", SMALL, left=True)
    paths.append(d.write())

    # --- b
    d = Diagram("delineation_flow_report_b", "Sub-KHG delineation: units")
    d.box("hc", L["laneC"], lx, 0, lw, 28, "head")
    d.box("hb", L["laneB"], rx, 0, rw, 28, "head")
    y = d.box("d8", "<b>5. Condition and route</b><br>D8 flow direction; flow accumulation", rx, 40, rw, None,
              "grey") + 30
    d.box("so", L["so"], rx, y, rw, None)
    d.box("ord", L["ord"], lx, y, lw, None, "outstore")
    y = _pair(d, "so", "ord") + 30
    for cid in ("os", "pc", "mg", "fn"):
        y = d.box(cid, L[cid], rx, y, rw, None) + 30
    y += 6
    hw = (rw - 20) / 2
    d.box("un", L["un"], rx, y, hw, None, "outstore")
    d.box("rp", L["rp"], rx + hw + 20, y, hw, None, "outstore")
    _pair(d, "un", "rp")
    d.box("nr", L["nr"], lx, y, lw, d.geo["un"][3], "user")
    y = d.box("pr", L["pr"], lx, d.bottom("nr") + 14, lw, None, "user") + 30
    for e, s, t in (("e35", "d8", "so"), ("e41", "so", "ord"), ("e36", "so", "os"), ("e37", "os", "pc"),
                    ("e38", "pc", "mg"), ("e39", "mg", "fn"), ("e43", "fn", "un"), ("e44", "fn", "rp"),
                    ("e45", "un", "nr")):
        d.edge(e, s, t)
    d.edge("e46", "un", "pr", style=ex(0.3, 1) + en(1, 0.5), points=[(rx + 0.3 * hw, d.cy("pr"))])
    d.box("n2", L["n2"], 0, y, W, None, "note", SMALL, left=True)
    paths.append(d.write())
    return paths


# ---------------------------------------------------------------------------------------------- chapter 6

def national_flow() -> Path:
    d = Diagram("national_flow", "National profile")
    lx, lw, rx, rw = 20, 300, 400, 340
    y = 0
    for cid, t in (("burn", "Burnt-area polygons 2015-2026"), ("viirs", "VIIRS hotspots 2012-2025"),
                   ("klh", "KLH hotspots January to September 2026"), ("peat", "GFW peat extent")):
        y = d.box(cid, t, lx, y, lw, 52, "data") + 12
    d.box("pf", "<b>Peat filter</b><br>fire and hotspots kept only where they fall on peat<br>rates per km² of peat",
          rx, 0, rw, y - 12)
    for cid in ("burn", "viirs", "klh", "peat"):
        d.edge(f"e_{cid}", cid, "pf")
    y0 = y + 28
    y = d.box("bnd", "KHG boundaries 2017 (865 KHG)", lx, y0 + 20, lw, 52, "data") + 12
    y = d.box("canal", "Canal layer by class", lx, y, lw, 52, "data")
    ib = d.box("ind", "<b>Indicators per KHG</b><br>burned share<br>repeat burns<br>hotspot density<br>this year's hotspot "
                      "density<br>primary, secondary and tertiary canal density", rx, y0, rw, None)
    d.edge("e_pf", "pf", "ind")
    d.edge("e_bnd", "bnd", "ind")
    d.edge("e_canal", "canal", "ind")
    y = ib + 40
    d.box("val", "<b>Held-out check</b><br>indicators 2015-2022,<br>tested on fire 2023-2025", lx, y, lw, None)
    y = d.box("scale", "<b>Scale and weight</b><br>5th to 95th percentile, weighted mean<br>(default weights)",
              rx, y, rw, d.geo["val"][3]) + 36
    turn = d.geo["val"][1] - 18
    d.edge("e_val", "ind", "val", style=ex(0.08, 1) + en(0.5, 0),
           points=[(rx + 0.08 * rw, turn), (d.cx("val"), turn)])
    d.edge("e_scale", "ind", "scale")
    y = d.box("rank", "<b>Rank and tertile classes</b><br>476 KHG large enough to rank", rx, y, rw, None, "nat") + 36
    d.edge("e_rank", "scale", "rank")
    y = d.box("short", "<b>Shortlist</b><br>top 25 + selected KHG (34 KHG)", rx, y, rw, None, "nat") + 50
    d.edge("e_short", "rank", "short")
    sh = fit("<b>Land-status overlays</b><br>forest area, peat function, licences, target villages", rw, TEXT, "nat", 0)
    d.box("st3", "<b>Context layers</b><br>TerraClimate, WorldCover, JRC water", lx, y, lw, sh, "nat")
    y = d.box("ovl", "<b>Land-status overlays</b><br>forest area, peat function, licences, target villages",
              rx, y, rw, sh, "nat") + 56
    turn = d.bottom("short") + 22
    d.edge("e_st3", "short", "st3", style=ex(0.1, 1) + en(0.5, 0), points=[(rx + 0.1 * rw, turn), (d.cx("st3"), turn)])
    d.edge("e_ovl", "short", "ovl", style=ex(0.6, 1) + en(0.6, 0))
    d.box("dash", "<b>Bilingual dashboard</b> (English, Bahasa Indonesia) with live weights", lx, y, W - lx, 56, "out")
    d.edge("e_d1", "st3", "dash", "shown, not scored", DASHED + d.straight("st3", "dash"))
    d.edge("e_d2", "ovl", "dash", "shown, not scored", DASHED + ex(0.6, 1) + en(d.fx("dash", rx + 0.6 * rw), 0))
    d.edge("e_d3", "rank", "dash", style=ex(0, 0.5) + en(0, 0.5), points=[(4, d.cy("rank")), (4, d.cy("dash"))])
    return d.write()


# ---------------------------------------------------------------------------------------------- chapter 7

def subkhg_method_report() -> list[Path]:
    """Reader version of repeat-prioritisation/docs/figures/subkhg_method.drawio, in two parts:
    a: inputs, steps 1-4 and the weights; b: checks, outputs, users, the validation and what changed from the
    team's earlier method. The chain note of the original is left out (the chain is figure toolkit_chain)."""
    L = {
        "c3": "<b>Per KHG, in the chain:</b> KHG inputs → DTM → sub-KHG units → neraca air → this ranking → "
              "RE-PEAT Interventions",
        "c4": "Inputs", "c5": "Processing", "c6": "Outputs", "c7": "Used by",
        "c8": "Ranking of the sub-KHG of one KHG by need for rewetting intervention",
        "c9": "<b>Sub-KHG units</b> from the delineation",
        "c10": "<b>National layers</b> (as the national profile)<br>• burnt-area polygons 2015-2026<br>• VIIRS hotspots "
               "2012-2025 (nominal, high confidence)<br>• KLH hotspots 2026 (medium, high)<br>• canals by class · GFW peat extent",
        "c11": "<b>KHG vectors</b> (clipped to the KHG)<br>canals, rivers, existing canal blocks<br>peat ecosystem function "
               "2017 (protected)",
        "c12": "<b>Rasters</b> DTM (slope, lift) · peat depth model",
        "c13": "<b>Satellite</b><br>Sentinel-2 NDMI and NDVI, August-October median, 20 m<br>ESA WorldCover (forest) · JRC "
               "water seasonality",
        "c14": "<b>SiTMAT</b> stations 2026 (days deeper than 0.4 m, recession)",
        "c15": "<b>Neraca air</b><br>P − ET per unit, with its order-test result<br>KHG deficit",
        "c16": "<b>1. Fire and canals per unit</b> (same method as the national profile)<br>burned share per year and "
               "repeat burns, hotspots, this year's hotspots, canal km per km² by class; rates per km² of peat; held-out "
               "fire targets",
        "c17": "<b>2. Indicators on a 30 m grid</b><br>• NDMI, NDVI: median of August-October composites, mean over the "
               "years<br>• reach: share within 200 m of a canal (60 m on burned land)<br>• missing blocks: 1 − existing ÷ "
               "needed; spacing 0.4 m ÷ canal slope<br>• distance to dry-season water, lift above it (DTM)<br>• peat depth, "
               "forest share, protected share, SiTMAT",
        "c18": "<b>3. Merge neraca air</b>: P − ET fills the rank-sum water slot; empty where the order test fails",
        "c19": "<b>4. Score</b><br>• each indicator scaled 0-1 between its 5th and 95th percentile within the KHG, "
               "direction applied<br>• need part U and stakes part S: weighted means of the available indicators<br>"
               "• <b>need = 0.8 U + 0.2 S</b>; feasibility reported, not ranked<br>• classes: tertiles of need (high, "
               "medium, low)<br>• rank-sum (earlier method) computed alongside",
        "c20": "<b>5. Checks</b><br>• indicator pairs with Spearman above 0.8 flagged<br>• weight sensitivity: 300 random "
               "weight sets around the defaults<br>• held-out validation: indicators 2015-2018 → fire 2019; 2015-2022 → "
               "fire 2023; Spearman with bootstrap interval, against fire history alone",
        "c21": "<b>Weights</b> (default, for agreement with KLH and the World Bank)<br>Need U: burned share 2 · repeat burns 1 · "
               "hotspots 1 · hotspots this year 1 · NDMI 1 · canals primary 0.5, secondary 0.3, tertiary 0.2 · missing "
               "blocks 1.5 · reach 1.5 · distance to water 1 · forest share 1 (less forest, more need) · SiTMAT 1 + 1 "
               "(only with enough stations)<br>Stakes S: peat depth 2 · protected function 1<br>Weight 0: NDVI, neraca air "
               "balance, single canal density (replaced by classes)<br>Reported only: lift, rates per area<br>An indicator "
               "is scored when at least half the units, and between 3 and 20 units, have a value",
        "c22": "<b>Ranking per unit</b>: every indicator, scaled values, need, stakes and need score, class, rank; "
               "rank-sum and its rank; share of weight draws in the high class<br><b>Run summary</b>: weights, coverage, "
               "correlations, sensitivity, validation",
        "c23": "<b>Priority list</b>: unit, rank, KHG deficit, design period",
        "c24": "<b>Reports</b>: run report, map page, validation report",
        "c25": "<b>RE-PEAT Interventions</b>: canal blocks and pumping, in rank order",
        "c26": "<b>Decision makers</b>: choice of sub-KHG, weights (AHP session)",
        "c27": "<b>Validation on an earlier unit set</b> (Spearman with burned share in the test year, 26-30 units)<br>"
               "Kampar-Gaung 2019 / 2023: need 0.61 / 0.29 · fire history alone 0.38 / 0.22<br>Sugihan-Lumpur 2019 / 2023: "
               "need 0.37 / 0.17 · fire history alone 0.64 / 0.36<br>Intervals overlap: no score clearly better. Stakes "
               "lower the fire prediction by design; drainage indicators cannot be tested against fire. Weights need "
               "expert judgement (AHP), with this as a check.",
        "c46": "What changed from the earlier method (Kahayan-Sebangau 2021)",
        "c47": "<b>Earlier method (kept as the rank-sum)</b><br>• 8 indicators ranked, ranks summed, equal weights<br>"
               "• NDMI, NDVI, peat depth, water decline, water balance, deficit months, dry days, hotspot count<br>"
               "• climate indicators at 4-25 km, nearly constant inside a KHG<br>• no check against later fire",
        "c48": "<b>Now</b><br>• Need score: values scaled within the KHG, explicit weights, need and stakes separate, "
               "feasibility reported<br>• Fire and canals from the same national layers and method as the national "
               "profile, per km² of peat; repeat burns and this year's hotspots added; canals by class<br>• Drainage: "
               "canal reach and missing blocks (IPG) from the canal layer, DTM and existing blocks<br>• Climate: dry days "
               "and TerraClimate dropped (cannot separate sub-KHG); water balance from the neraca air, used only where its "
               "order is trustworthy<br>• NDMI at Sentinel-2's native 20 m; protected peat function in the stakes<br>"
               "• Held-out validation on two El Niño years, compared with fire history alone",
    }
    paths = []
    lx, lw, rx, rw = 0, 300, 340, 380
    # --- a
    d = Diagram("subkhg_method_report_a", "Sub-KHG prioritisation: indicators and score")
    d.box("h4", L["c4"], lx, 0, lw, 28, "head")
    d.box("h5", L["c5"], rx, 0, rw, 28, "head")
    y = 40
    y10 = d.box("c10", L["c10"], lx, y, lw, None, "input", left=True) + 10
    h9 = fit(L["c9"], lw, TEXT, "input", True)
    d.box("c9", L["c9"], lx, y10, lw, h9, "input", left=True)
    split = y10 + h9 / 2
    h16 = max(split - 6 - y, fit(L["c16"], rw, TEXT, "proc", True))
    d.box("c16", L["c16"], rx, y, rw, h16, left=True)
    if h16 > split - 6 - y:                                   # step 1 taller than its inputs: move c9 down
        shift = y + h16 + 6 - split
        d.geo["c9"] = (lx, y10 + shift, lw, h9)
        _reheight(d, "c9")
        split += shift
    y17 = split + 6
    yy = d.bottom("c9") + 10
    for cid in ("c11", "c12", "c13", "c14"):
        yy = d.box(cid, L[cid], lx, yy, lw, None, "input", left=True) + 10
    h17 = max(yy - 10 - y17, fit(L["c17"], rw, TEXT, "proc", True))
    d.box("c17", L["c17"], rx, y17, rw, h17, left=True)
    y = max(yy - 10, d.bottom("c17")) + 30
    d.box("c15", L["c15"], lx, y, lw, None, "input", left=True)
    d.box("c18", L["c18"], rx, y, rw, None, left=True)
    y = _pair(d, "c15", "c18") + 30
    d.box("c21", L["c21"], lx, y, lw, None, "param", SMALL, left=True)
    d.box("c19", L["c19"], rx, y, rw, None, left=True)
    y = _pair(d, "c21", "c19")
    d.edge("c28", "c9", "c16", style=ex(1, 0.25) + en(0, d.fy("c16", d.geo["c9"][1] + 0.25 * h9)))
    d.edge("c30", "c9", "c17", style=ex(1, 0.75) + en(0, d.fy("c17", d.geo["c9"][1] + 0.75 * h9)))
    for e, s, t in (("c29", "c10", "c16"), ("c31", "c11", "c17"), ("c32", "c12", "c17"), ("c33", "c13", "c17"),
                    ("c34", "c14", "c17"), ("c35", "c15", "c18"), ("c38", "c18", "c19"), ("c40", "c21", "c19")):
        d.edge(e, s, t)
    ye = d.geo["c19"][1] + 24
    for e, s in (("c36", "c16"), ("c37", "c17")):                # both join one line into step 4
        d.edge(e, s, "c19", style=ex(1, 0.5) + en(1, d.fy("c19", ye)), points=[(rx + rw + 14, d.cy(s)), (rx + rw + 14, ye)])
    paths.append(d.write())

    # --- b
    d = Diagram("subkhg_method_report_b", "Sub-KHG prioritisation: checks and outputs")
    d.box("h5", L["c5"], lx, 0, lw, 28, "head")
    d.box("h6", L["c6"], rx, 0, rw, 28, "head")
    y = d.box("c19", "<b>4. Score</b><br>need score, classes, rank-sum", lx, 40, lw, None, "grey")
    d.box("c22", L["c22"], rx, 40, rw, None, "out", left=True)
    y = max(y, d.bottom("c22")) + 30
    d.box("c20", L["c20"], lx, y, lw, None, left=True)
    d.box("c23", L["c23"], rx, y, rw, None, "out", left=True)
    y23 = d.bottom("c23") + 20
    d.box("c25", L["c25"], rx, y23, rw, None, "user", left=True)
    y = max(d.bottom("c20"), d.bottom("c25")) + 30
    d.box("c24", L["c24"], lx, y, lw, None, "out", left=True)
    d.box("c26", L["c26"], rx, y, rw, None, "user", left=True)
    y = _pair(d, "c24", "c26") + 30
    d.edge("c41", "c19", "c22")
    d.edge("c42", "c19", "c23", style=ex(1, 0.7) + en(0, 0.3), points=[(320, d.geo["c19"][1] + 0.7 * d.geo["c19"][3]),
                                                                       (320, d.geo["c23"][1] + 0.3 * d.geo["c23"][3])])
    d.edge("c39", "c19", "c20")
    d.edge("c43", "c20", "c24")
    d.edge("c44", "c23", "c25")
    d.edge("c45", "c24", "c26")
    y = d.box("c27", L["c27"], 0, y, W, None, "note", SMALL, left=True) + 30
    d.box("c46", L["c46"], 0, y, W, 28, "head")
    y = d.box("c47", L["c47"], 0, y + 40, W, None, "note", SMALL, left=True) + 36
    d.box("c48", L["c48"], 0, y, W, None, "proc", SMALL, left=True)
    d.edge("c49", "c47", "c48", "extended")
    paths.append(d.write())
    return paths


# ---------------------------------------------------------------------------------------------- chapter 8a

def neraca_method_report() -> Path:
    d = Diagram("neraca_method_report", "Neraca air method")
    lx, lw, rx, rw = 20, 320, 380, 340
    y = LANE_TOP
    ins = [("units", "Sub-KHG units<br>(whole KHG as one unit where none)"), ("chirps", "CHIRPS daily rain"),
           ("mod16", "MOD16 evapotranspiration (central)"), ("wapor", "WaPOR evapotranspiration (second source)"),
           ("wc", "ESA WorldCover land cover")]
    for cid, t in ins:
        y = d.box(cid, t, lx, y, lw, 48, "data") + 10
    d.box("fetch", "<b>Rain and ET per unit per dekad</b><br>each product on its own grid<br>land-cover shares per unit",
          rx, LANE_TOP, rw, y - 10 - LANE_TOP)
    for cid, _ in ins:
        d.edge(f"e_{cid}", cid, "fetch")
    y += 26
    bal = ("<b>Monthly balance</b><br>WB = P (1 − I)(1 − C) − ET<br>P: KHG-mean rain<br>C = 0.12, I from land cover"
           "<br>complete years 2018-2025")
    bh = fit(bal, rw, TEXT, "proc", False)
    d.box("bal", bal, rx, y, rw, bh)
    d.box("perunit", "<b>Per sub-KHG</b><br>mean monthly balance<br>deficit months per year<br>P − ET",
          lx, y, lw, bh, "out")
    d.edge("e_fetch", "fetch", "bal")
    d.edge("e_o", "bal", "perunit")
    y += bh + 36
    d.box("test", "<b>Order test</b>", rx, y, 180, 96, "diamond")
    d.box("crit", "ET products agree; order holds between years (p &lt; 0.01 against a random order)",
          rx + 190, y, rw - 190, None, "note", SMALL)
    _reheight(d, "test", h=max(96, d.geo["crit"][3]))
    tc = d.cy("test")
    d.box("pass", "<b>Usable for ranking</b><br>rank-sum water slot reads P − ET", lx, tc - 28, lw, 56, "out")
    d.box("fail", "Values left empty in the ranking", lx, d.bottom("pass") + 14, lw, 48, "out")
    d.edge("e_test", "bal", "test", style=ex(d.fx("bal", rx + 90), 1) + en(0.5, 0))
    d.edge("e_pass", "test", "pass", "pass", ex(0, 0.5) + en(1, d.fy("pass", tc)))
    d.edge("e_fail", "test", "fail", "fail", ex(0.5, 1) + en(1, 0.5), points=[(rx + 90, d.cy("fail"))])
    end_a = d.bottom("fail") + GAP
    d.box("laneA", "A. Sub-KHG level: climatic water balance", 0, 0, W, end_a, "lane")
    # B
    yb = end_a + GAP
    y = yb + LANE_TOP
    c1, c1w, c2, c2w = 20, 250, 300, 420
    deft = ("<b>KHG deficit = max(0, −Σ(P − E) − Sy × Δz)</b><br>Δz: change in station-mean depth<br>1 June to last "
            "forcing day · Sy 0.15 (0.10-0.20)")
    dh = fit(deft, c2w, TEXT, "proc", False)
    d.box("def", deft, c2, y, c2w, dh)
    s1 = fit("SiTMAT station depths<br>(readings on at least 50 % of days)", c1w, TEXT, "data", False)
    d.box("sitmat", "SiTMAT station depths<br>(readings on at least 50 % of days)", c1, y, c1w, s1, "data")
    e1 = fit("ERA5 daily rain and evaporation", c1w, TEXT, "data", False)
    d.box("era5", "ERA5 daily rain and evaporation", c1, y + s1 + 10, c1w, e1, "data")
    dh = max(dh, s1 + 10 + e1)
    _reheight(d, "def", h=dh)
    d.box("defout", "Deficit in mm and million m³ · deficit months", c2, y + dh + 30, c2w, 44, "out")
    d.edge("e_sitmat", "sitmat", "def")
    d.edge("e_era5", "era5", "def")
    d.edge("e_def", "def", "defout")
    end_b = d.bottom("defout") + GAP
    d.box("laneB", "B. KHG level: supply deficit", 0, yb, W, end_b - yb, "lane")
    y = end_b + 40
    y = d.box("map", "<b>Neraca map</b>: sub-KHG balance, monthly climatology, dry-season mean (July-October), KHG "
                     "deficit, stations", lx, y, W - lx, None, "out") + GAP
    d.edge("e_map1", "defout", "map")
    d.edge("e_map2", "perunit", "map", style=ex(0, 0.5) + en(0, 0.5),
           points=[(6, d.cy("perunit")), (6, d.cy("map"))])
    d.box("phys", "<b>C. Diagnostic only</b>: physical model, tiers 1 and 2, not on the ranking path",
          lx, y, W - lx, 44, "grey")
    return d.write()


# ---------------------------------------------------------------------------------------------- chapter 8b

def neraca_model_boundaries() -> Path:
    d = Diagram("neraca_model_boundaries", "Groundwater model boundaries")
    lx, lw, rx, rw = 20, 300, 360, 360
    d.box("pb", "<b>Peat base</b> (run option): no ET from a cell whose water table is below the peat base",
          lx, 0, lw, None, "note", SMALL, left=True)
    top = d.box("rain", "Rain (CHIRPS) and ET (MOD16)<br>KHG mean per dekad", rx, 0, rw, d.geo["pb"][3], "data")
    y = top + 40
    left = [("edge", "<b>KHG edge</b><br>held 0.3 m below the surface"),
            ("canal", "<b>Canals by class</b><br>primary, secondary, tertiary; each held at a set depth (1.2 m in the "
                      "base runs)"),
            ("man", "<b>Managed land in plantation licences</b> (run setting)<br>canals and cells held at the 0.4 m target "
                    "(PP 57/2016); water used = water-management supply")]
    yy = y
    for cid, t in left:
        yy = d.box(cid, t, lx, yy, lw, None) + GAP
    free_bottom = yy + 20
    d.box("free", "<b>Free peat cells</b><br>2D Boussinesq<br>rain minus ET in, lateral flow between cells",
          rx, y, rw, free_bottom - y)
    d.edge("e_rain", "rain", "free")
    for cid, _ in left:
        d.edge(f"e_{cid}", cid, "free", style=TWO_WAY + d.straight(cid, "free"))
    ly = free_bottom + 40
    d.box("scen", "Scenario inputs from RE-PEAT Interventions", 0, ly, W, 0, "laneb")
    by = ly + GAP
    b1 = d.box("blk", "<b>Block reaches</b><br>canal cells of each reach fixed at the reach water depth; the higher of "
                      "block and managed level kept", lx, by, lw, None, "out")
    b2 = d.box("sup", "<b>Land marked for water supply</b><br>held at 0.4 m; water used = pumping need",
               rx + 40, by, rw - 40, None, "out")
    bb = max(b1, b2)
    d.geo["blk"] = d.geo["blk"][:3] + (bb - by,)
    d.geo["sup"] = d.geo["sup"][:3] + (bb - by,)
    _reheight(d, "blk", "sup")
    _reheight(d, "scen", h=bb + LANE_TOP - ly)
    join = free_bottom - 15
    d.edge("e_blk", "blk", "free", style=ex(0.5, 0) + en(0, d.fy("free", join)),
           points=[(d.cx("blk"), join)])
    d.edge("e_sup", "sup", "free", style=TWO_WAY + d.straight("sup", "free"))
    oy = bb + LANE_TOP + 40
    d.box("out", "<b>Outputs</b><br>• daily KHG series: mean depth, share deeper than 40 cm, supply<br>• season maps: "
                 "days deeper than 40 cm, mean depth, supply<br>• table per sub-KHG<br>• scores against stations",
          lx, oy, W - 2 * lx, None, "out", left=True)
    xo = rx + 20                                  # between the two scenario boxes
    d.edge("e_out", "free", "out", style=ex(d.fx("free", xo), 1) + en(d.fx("out", xo), 0))
    return d.write()


def _reheight(d: Diagram, *cids, h=None):
    """Write the geometry in d.geo back into the cell list (after a height change)."""
    for cid in cids:
        if h is not None:
            d.geo[cid] = d.geo[cid][:3] + (h,)
        for i, c in enumerate(d.cells):
            if c[0] == "v" and c[1] == cid:
                d.cells[i] = c[:4] + (d.geo[cid],) + c[5:]


# ---------------------------------------------------------------------------------------------- chapter 9

def _beside(d: Diagram, right: str, lefts: list, gap: float = 10):
    """Make the box 'right' at least as tall as the stacked boxes 'lefts', or stretch the last of them."""
    top = d.geo[right][1]
    bottom = d.bottom(lefts[-1])
    if bottom - top > d.geo[right][3]:
        _reheight(d, right, h=bottom - top)
    else:
        x, y, w, h = d.geo[lefts[-1]]
        _reheight(d, lefts[-1], h=d.bottom(right) - y)
    return d.bottom(right)


def pump_method_report() -> list[Path]:
    """Reader version of repeat-pump/docs/figures/pump_method.drawio, in three parts:
    a: stages 1-5 (canal network and terrain), with the key; b: stages 6-11 (canal blocks, pumping, optimisation);
    c: stage 12 (interventions, budget and report)."""
    L = {
        "c3": "<b>Any KHG from its code.</b> The batch tool and the QGIS plugin use the same method. "
              "Stages 1-12; review stops after stages 2, 6 and 9 "
              "(thick border). Proposed default values are marked as such.",
        "c4": "Inputs", "c5": "Stages", "c6": "Outputs", "c7": "Read by",
        "c8": "A. Canal network and terrain (stages 1-5)",
        "c9": "<b>DTM</b>: LiDAR first; corrected DeltaDTM or DEMNAS<br>the source sets the suggested vertical error "
              "(LiDAR 0.3 m, DeltaDTM 0.49 m, DEMNAS 4.97 m)",
        "c10": "<b>Canals</b> by class (primary, secondary, tertiary)<br>existing canal blocks, rivers",
        "c11": "<b>Sub-KHG units and ranking</b> from the delineation and the sub-KHG prioritisation",
        "c12": "<b>Moisture</b> (latest NDMI), <b>burned area</b>, <b>peat depth</b> (optional: a criterion without its "
               "layer gets weight 0)",
        "c13": "<b>1. Load and validate</b>: clip to the selected sub-KHG (top n by rank), coordinate system, DTM type "
               "(surface model refused), accuracy warning",
        "c14": "<b>2. Topology</b>: class filter (primary, secondary; tertiary optional), snap gaps, dangles, canal edits",
        "c15": "<b>3. Hydrology</b>: burn canals into the DTM, fill, flow accumulation",
        "c16": "<b>4-5. Segments and profiles</b>: segments of at most 500 m; land profile along each canal; flow "
               "direction from slope, rivers, else flow accumulation",
        "c17": "Clipped inputs, cleaned canals, topology checks (dangles, gaps), canal segments, canal profiles",
        "c18": "Conditioned DTM, flow accumulation",
        "c28": "Key", "c29": "input", "c30": "stage", "c31": "stage with a review stop", "c32": "optional stage",
        "c33": "parameters", "c34": "output",
        "c35": "B. Where the canal blocks go (stages 6-7)",
        "c36": "<b>6. Prioritise</b>: need score per segment (dryness in a ring around the canal, upstream flow, burn, "
               "peat depth), min-max scaled, direct or AHP weights, sensitivity; or the KLH 1-3 scoring",
        "c37": "<b>7. Canal blocks</b>: head rule, a block where the land rises dA = 0.40 m (PP 57/2016); new blocks at "
               "least 500 m apart along a canal; a proposal within 100 m of an existing block is merged; reinforced "
               "type from 5 % slope",
        "c38": "<b>Balance</b> (canal-rise objective, Urzainki et al. 2020): rank blocks by the extra canal water each adds, "
               "from a dry level 1.0 m below the land, capped at the surface; keep the fewest giving <b>90 %</b> (or a "
               "budget cap on the number of blocks)",
        "c39": "<b>Parameters</b>: dA 0.40 m · new blocks at least 500 m apart · merge distance 100 m · reported spacing "
               "capped at 500 m · kept share 90 % (policy) · dry canal level 1.0 m · reinforced from 5 % slope",
        "c40": "Canal segments with need score and rank; sensitivity check",
        "c41": "<b>Proposed blocks</b> (kept, with benefit rank, share, spacing, type) · <b>low-benefit blocks</b> · "
               "existing blocks assessed · <b>block reaches</b>: the canal stretch each kept block holds, drawn "
               "upstream (rise, depth, burned share)",
        "c48": "C. Pumping (stages 8-10; off when no river is perennial or has a dry-season level)",
        "c49": "<b>8. Network</b> of canals, rivers and blocks · <b>9. Routing</b> (review stop): head-aware least cost "
               "from river intakes to the highest node of each target cluster; gates where routes cross blocks · "
               "<b>10. Pumps</b>: demand from deficit and specific yield, units per station",
        "c50": "Network, intakes, targets, <b>pump routes</b> (intake to target), pump stations, gates required",
        "c53": "E. Interventions, budget and report (stage 12, always last)",
        "c54": "<b>Sub-KHG indicators</b> from the prioritisation: protected share, NDMI, burned share, canal reach, "
               "distance to water, canal density",
        "c55": "<b>Neraca air</b> map: KHG deficit, monthly balance, SiTMAT stations",
        "c56": "<b>Unit prices</b>: low, central, high (Rp), with a register of sources (to verify)",
        "c57": "<b>12a. Interventions</b> per sub-KHG (water held from stage 7), first rule that holds: protected peat "
               "≥ 0.5 → close or backfill canals · dry (NDMI &lt; 0.30) or burned (≥ 0.25) and canal reach &lt; 0.4 → "
               "revegetation and fire readiness · reach ≥ 0.4, blocks hold &lt; 0.5 of the deficit, water within 5 km → "
               "blocks and water supply · same but no water within 5 km, dry or burned → blocks and deep wells · reach "
               "≥ 0.4 → blocks · else maintain. Held = rise × Sy 0.15 × 600 m",
        "c58": "<b>12b. Budget</b>: kept blocks by type (or the KLH IPG estimate where none were placed), km of canal to "
               "close, ha to revegetate, wells: burned area ÷ (π × (200 m)²), pumps and fuel × prices",
        "c59": "<b>12c. Report</b>: run report; interactive report page (map with animation, charts, tables); KLH print "
               "layouts A0-A4",
        "c60": "<b>Interventions</b> layer and table (class, reasons, class without the protected rule, water held, deficit)",
        "c61": "<b>Budget</b> layer and table; <b>register of price sources</b> with status and run value",
        "c62": "<b>Run report</b>, <b>report page</b> (one file, English and Indonesian, light and dark), print layouts "
               "(PNG, PDF, templates)",
        "c63": "<b>KLH</b>: plan, budget request, field check of block sites and prices",
        "c74": "D. Optional (stage 11)",
        "c75": "<b>11. Optimise</b>: choose n of the kept blocks by genetic algorithm, simulated annealing or greedy "
               "search; scored by canal rise or the 2D groundwater model, with three peat tables; re-scored as a range",
        "c76": "Optimised blocks; optimisation check (benefit per method, against random, per peat table)",
    }
    paths = []
    lx, lw, rx, rw = 20, 300, 360, 360
    # --- a
    d = Diagram("pump_method_report_a", "RE-PEAT Interventions: stages 1-5")
    y = d.box("c3", L["c3"], 0, 0, W, None, "note", SMALL, left=True) + 16
    y = legend(d, y, [("input", L["c29"]), ("proc", L["c30"]), ("review", L["c31"]), ("grey", L["c32"]),
                      ("param", L["c33"]), ("out", L["c34"])]) + 24
    lane = y
    y += LANE_TOP
    yy = y
    for cid in ("c9", "c10", "c11", "c12"):
        yy = d.box(cid, L[cid], lx, yy, lw, None, "input", left=True) + 10
    d.box("c13", L["c13"], rx, y, rw, None, left=True)
    y = _beside(d, "c13", ["c9", "c10", "c11", "c12"]) + 30
    d.box("c14", L["c14"], rx, y, rw, None, "review", left=True)
    d.box("c17", L["c17"], lx, y, lw, None, "out", left=True)
    y = _pair(d, "c14", "c17") + 30
    d.box("c15", L["c15"], rx, y, rw, None, left=True)
    d.box("c18", L["c18"], lx, y, lw, None, "out", left=True)
    y = _pair(d, "c15", "c18") + 30
    y = d.box("c16", L["c16"], rx, y, rw, None, left=True)
    d.box("c8", L["c8"], 0, lane, W, y + GAP - lane, "lane")
    for e, s, t in (("c19", "c9", "c13"), ("c20", "c10", "c13"), ("c21", "c11", "c13"), ("c22", "c12", "c13"),
                    ("c23", "c13", "c14"), ("c24", "c14", "c15"), ("c25", "c15", "c16"), ("c26", "c14", "c17"),
                    ("c27", "c15", "c18")):
        d.edge(e, s, t)
    paths.append(d.write())

    # --- b
    d = Diagram("pump_method_report_b", "RE-PEAT Interventions: stages 6-11")
    y = LANE_TOP
    y = d.box("c16", "<b>4-5. Segments and profiles</b>", rx, y, rw, None, "grey") + 30
    d.box("c36", L["c36"], rx, y, rw, None, "review", left=True)
    d.box("c40", L["c40"], lx, y, lw, None, "out", left=True)
    y = _pair(d, "c36", "c40") + 30
    d.box("c37", L["c37"], rx, y, rw, None, left=True)
    d.box("c39", L["c39"], lx, y, lw, None, "param", SMALL, left=True)
    y = _pair(d, "c37", "c39") + 30
    d.box("c38", L["c38"], rx, y, rw, None, left=True)
    d.box("c41", L["c41"], lx, y, lw, None, "out", left=True)
    y = _pair(d, "c38", "c41") + GAP
    d.box("c35", L["c35"], 0, 0, W, y, "lane")
    lc = y + 16
    y = lc + LANE_TOP
    d.box("c49", L["c49"], rx, y, rw, None, "grey", left=True)
    d.box("c50", L["c50"], lx, y, lw, None, "out", left=True)
    y = _pair(d, "c49", "c50") + GAP
    d.box("c48", L["c48"], 0, lc, W, y - lc, "lane")
    ld = y + 16
    y = ld + LANE_TOP
    d.box("c75", L["c75"], rx, y, rw, None, "grey", left=True)
    d.box("c76", L["c76"], lx, y, lw, None, "out", left=True)
    y = _pair(d, "c75", "c76") + GAP
    d.box("c74", L["c74"], 0, ld, W, y - ld, "lane")
    for e, s, t in (("c42", "c16", "c36"), ("c43", "c36", "c37"), ("c44", "c37", "c38"), ("c45", "c39", "c37"),
                    ("c46", "c36", "c40"), ("c47", "c38", "c41"), ("c52", "c49", "c50"),
                    ("c77", "c75", "c76")):
        d.edge(e, s, t)
    d.edge("c51", "c38", "c49", style=ex(0.9, 1) + en(0.9, 0))          # clear of the lane C title
    paths.append(d.write())

    # --- c
    d = Diagram("pump_method_report_c", "RE-PEAT Interventions: stage 12")
    sx, sw, ox, ow = 20, 420, 480, 240
    y = LANE_TOP
    d.box("c57", L["c57"], sx, y, sw, None, left=True)
    yy = d.box("c54", L["c54"], ox, y, ow, None, "input", left=True) + 10
    yy = d.box("c55", L["c55"], ox, yy, ow, None, "input", left=True) + 10
    yy = d.box("c60", L["c60"], ox, yy, ow, None, "out", left=True)
    y = _beside(d, "c57", ["c54", "c55", "c60"]) + 30
    d.box("c58", L["c58"], sx, y, sw, None, left=True)
    yy = d.box("c56", L["c56"], ox, y, ow, None, "input", left=True) + 10
    yy = d.box("c61", L["c61"], ox, yy, ow, None, "out", left=True)
    y = _beside(d, "c58", ["c56", "c61"]) + 30
    d.box("c59", L["c59"], sx, y, sw, None, left=True)
    d.box("c62", L["c62"], ox, y, ow, None, "out", left=True)
    y = _pair(d, "c59", "c62") + 30
    y = d.box("c63", L["c63"], ox, y, ow, None, "user", left=True)
    d.box("c53", L["c53"], 0, 0, W, y + GAP, "lane")
    for e, s, t in (("c64", "c54", "c57"), ("c65", "c55", "c57"), ("c66", "c57", "c58"), ("c67", "c56", "c58"),
                    ("c68", "c58", "c59"), ("c69", "c57", "c60"), ("c70", "c58", "c61"), ("c73", "c62", "c63")):
        d.edge(e, s, t)
    xr = ox + ow + 10
    d.edge("c72", "c61", "c63", style=ex(1, 0.5) + en(1, 0.5), points=[(xr, d.cy("c61")), (xr, d.cy("c63"))])
    d.edge("c71", "c59", "c62")
    paths.append(d.write())
    return paths


# ---------------------------------------------------------------------------------------------- checks

SUSPECT = re.compile(r"\.(py|gpkg|csv|tif|yaml|json|md|qpt)\b|--\w|\b[a-z]+_[a-z0-9_]+\b|repeat[-_]|/\w+/|&lt;khg|\bv\d+(\.\d+)+")


def check(path: Path) -> list[str]:
    root = ET.parse(path).getroot()
    cells = {c.get("id"): c for c in root.iter("mxCell")}
    problems = []
    xmax = 0.0
    for cid, c in cells.items():
        style = c.get("style") or ""
        if c.get("edge"):
            s, t = c.get("source"), c.get("target")
            if not (s in cells and t in cells and cells[s].get("vertex") and cells[t].get("vertex")):
                problems.append(f"edge {cid}: source/target missing")
            if "edgeStyle=orthogonalEdgeStyle" not in style:
                problems.append(f"edge {cid}: not orthogonal")
            for end in (s, t):
                if end in cells and LANE_MARK in (cells[end].get("style") or ""):
                    problems.append(f"edge {cid}: ends on a lane")
        m = re.search(r"fontSize=(\d+)", style)
        if c.get("vertex") or c.get("edge"):
            if not m or int(m.group(1)) < SMALL:
                problems.append(f"cell {cid}: font below {SMALL} px")
        g = c.find("mxGeometry")
        if c.get("vertex") and g is not None:
            xmax = max(xmax, float(g.get("x", 0)) + float(g.get("width", 0)))
        for p in c.iter("mxPoint"):
            xmax = max(xmax, float(p.get("x", 0)))
        text = re.sub(r"<[^>]+>", " ", c.get("value") or "")
        if SUSPECT.search(text):
            problems.append(f"label {cid}: {SUSPECT.search(text).group(0)!r} in {text[:80]!r}")
    if xmax > W + 0.5:
        problems.append(f"content width {xmax:g} px > {W}")
    return problems


BUILDERS = {f.__name__: f for f in (toolkit_chain, dem_benchmark_workflow_report, delineation_flow_report, national_flow,
                                     subkhg_method_report, pump_method_report,
                                     neraca_method_report, neraca_model_boundaries)}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    bad = 0
    for name in sys.argv[1:] or BUILDERS:
        res = BUILDERS[name]()
        for p in res if isinstance(res, list) else [res]:
            probs = check(p)
            bad += len(probs)
            print(p.name, "ok" if not probs else "\n  " + "\n  ".join(probs))
    sys.exit(1 if bad else 0)
