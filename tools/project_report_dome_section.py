"""Hand-drawn cross-section of a peat dome between two canals, as an editable draw.io file.

    .venv/Scripts/python.exe re-peat/tools/project_report_dome_section.py

Writes re-peat/reports/project_report/diagrams/peat_dome_section.drawio (chapter 8b, background). It is a schematic
without a scale: left canal open, right canal held higher by a block across it. The file is the editable source once
written; running this again overwrites it. Colours and font come from project_report_style.py.
"""
from __future__ import annotations

import html
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_report_style import ACCENT, ACCENT_SOFT, INK, MUTED, RULE, SANS, WARM, WARM_SOFT  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "reports" / "project_report" / "diagrams" / "peat_dome_section.drawio"
W, H = 740, 420
FONT = f"fontFamily={SANS};fontColor=#{INK};html=1;"

CREST, EDGE_Y, CANAL_BOTTOM, BASE = 130, 215, 275, 330
XL0, XL1, XR0, XR1, XC = 130, 160, 580, 610, 370          # canal walls, dome centre
WT_CREST, WT_LEFT, WT_RIGHT = 160, 262, 240                # water table at the crest, in the open and in the held canal


def surface(x):
    return CREST + (EDGE_Y - CREST) * ((x - XC) / (XC - XL1)) ** 2


def water_table(x):
    end = WT_LEFT if x < XC else WT_RIGHT
    return WT_CREST + (end - WT_CREST) * (abs(x - XC) / (XC - XL1)) ** 2


class Page:
    def __init__(self):
        self.n = 1
        self.root = ET.Element("mxGraphModel", dx="0", dy="0", grid="1", gridSize="10", page="1", pageWidth=str(W),
                               pageHeight=str(H), math="0", shadow="0")
        r = ET.SubElement(self.root, "root")
        ET.SubElement(r, "mxCell", id="0")
        ET.SubElement(r, "mxCell", id="1", parent="0")
        self.r = r

    def _id(self):
        self.n += 1
        return f"c{self.n}"

    def shape(self, style, x, y, w, h, value=""):
        c = ET.SubElement(self.r, "mxCell", id=self._id(), value=value, style=style, vertex="1", parent="1")
        ET.SubElement(c, "mxGeometry", {"x": f"{x:g}", "y": f"{y:g}", "width": f"{w:g}", "height": f"{h:g}", "as": "geometry"})

    def polygon(self, pts, fill, stroke, width=1.25):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        rel = [[round((x - x0) / (x1 - x0), 4), round((y - y0) / (y1 - y0), 4)] for x, y in pts]
        style = (f"shape=mxgraph.basic.polygon;polyCoords={rel};polyline=0;fillColor=#{fill};strokeColor=#{stroke};"
                 f"strokeWidth={width};")
        self.shape(style, x0, y0, x1 - x0, y1 - y0)

    def text(self, x, y, w, h, value, size=14, align="left", bold=False):
        style = f"text;whiteSpace=wrap;{FONT}fontSize={size};align={align};verticalAlign=middle;fontStyle={1 if bold else 0};"
        self.shape(style, x, y, w, h, html.escape(value, quote=False))

    def line(self, pts, color, width=1.25, dashed=False, arrow=False):
        style = (f"edgeStyle=none;html=1;strokeWidth={width};strokeColor=#{color};endArrow={'block' if arrow else 'none'};"
                 f"endFill=1;endSize=7;{'dashed=1;' if dashed else ''}")
        c = ET.SubElement(self.r, "mxCell", id=self._id(), style=style, edge="1", parent="1")
        g = ET.SubElement(c, "mxGeometry", {"width": "50", "height": "50", "relative": "1", "as": "geometry"})
        ET.SubElement(g, "mxPoint", {"x": f"{pts[0][0]:g}", "y": f"{pts[0][1]:g}", "as": "sourcePoint"})
        ET.SubElement(g, "mxPoint", {"x": f"{pts[-1][0]:g}", "y": f"{pts[-1][1]:g}", "as": "targetPoint"})
        if len(pts) > 2:
            arr = ET.SubElement(g, "Array", {"as": "points"})
            for x, y in pts[1:-1]:
                ET.SubElement(arr, "mxPoint", {"x": f"{x:g}", "y": f"{y:g}"})


def build() -> Path:
    p = Page()
    # mineral soil under the peat, then the peat body with the two canals cut into it
    p.shape(f"rounded=0;html=1;fillColor=#F4F6F6;strokeColor=#{RULE};strokeWidth=1.25;", 20, BASE, 700, 40)
    p.text(30, BASE + 6, 400, 28, "Mineral soil below the peat (peat base)", 14)
    arc = [(x, surface(x)) for x in range(XL1, XR0 + 1, 15)] + [(XR0, surface(XR0))]
    peat = ([(20, BASE), (20, 235), (XL0, EDGE_Y), (XL0, CANAL_BOTTOM), (XL1, CANAL_BOTTOM)] + arc
            + [(XR0, CANAL_BOTTOM), (XR1, CANAL_BOTTOM), (XR1, EDGE_Y), (720, 235), (720, BASE)])
    p.polygon(peat, WARM_SOFT, WARM)
    # saturated peat between the canals and the water in the canals
    xs = list(range(XL1, XR0 + 1, 15))
    sat = [(XL1, WT_LEFT)] + [(x, water_table(x)) for x in xs[1:-1]] + [(XR0, WT_RIGHT), (XR0, BASE), (XL1, BASE)]
    p.polygon(sat, ACCENT_SOFT, ACCENT, 0.5)
    p.shape(f"rounded=0;html=1;fillColor=#{ACCENT};strokeColor=#{ACCENT};", XL0, WT_LEFT, XL1 - XL0, CANAL_BOTTOM - WT_LEFT)
    p.shape(f"rounded=0;html=1;fillColor=#{ACCENT};strokeColor=#{ACCENT};", XR0, WT_RIGHT, XR1 - XR0, CANAL_BOTTOM - WT_RIGHT)
    p.line([(XL1, WT_LEFT)] + [(x, water_table(x)) for x in xs[1:-1]] + [(XR0, WT_RIGHT)], ACCENT, 2.5)
    # fluxes: rain in, evapotranspiration out, sideways flow
    for x in (300, 340, 380, 420):
        p.line([(x, 50), (x, surface(x) - 8)], MUTED, 1.25, arrow=True)
    p.text(290, 24, 140, 24, "Rain", 15, "center", True)
    for x in (490, 530):
        p.line([(x, surface(x) - 6), (x, 100)], MUTED, 1.25, arrow=True)
    p.text(440, 72, 170, 24, "Evapotranspiration", 15, "center", True)
    p.line([(340, 285), (250, 285)], INK, 1.5, arrow=True)
    p.line([(400, 285), (490, 285)], INK, 1.5, arrow=True)
    p.text(270, 296, 200, 30, "Sideways flow = transmissivity × slope of the water table", 14, "center")
    p.text(175, 252, 90, 24, "Water table", 14)
    p.text(190, 112, 120, 22, "Peat surface", 14)
    # callouts for the two canals
    p.text(0, 0, 215, 66, "Open canal: water leaves the peat and the water table falls towards it", 14)
    p.line([(145, 68), (145, WT_LEFT + 4)], MUTED, 1.25, arrow=True)
    p.text(535, 0, 205, 66, "Block across the canal: higher canal level, water table held higher nearby", 14)
    p.line([(595, 68), (595, WT_RIGHT + 4)], MUTED, 1.25, arrow=True)
    p.text(0, BASE + 44, W, 40, "Schematic, not to scale. The effect of a block fades with distance from the canal.", 14)
    ET.indent(p.root)
    mx = ET.Element("mxfile", host="drawio")
    d = ET.SubElement(mx, "diagram", name="Peat dome section", id="peat_dome_section")
    d.append(p.root)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(mx).write(OUT, encoding="utf-8", xml_declaration=True)
    return OUT


if __name__ == "__main__":
    print(build())
