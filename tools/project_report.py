"""Build the RE-PEAT project report (Word) from the chapter Markdown files.

    .venv/Scripts/python.exe re-peat/tools/project_report.py [--out re-peat/reports/project_report/RE-PEAT_project_report.docx]

Reads re-peat/reports/project_report/chapters/NN_*.md in name order (the *.sources.md companions are skipped) and
converts the Markdown subset described in BRIEF.md: headings (# chapter, ##, ###), paragraphs with **bold** and *italic*,
bullet and numbered lists, pipe tables with a "Table: ..." caption line above, images ![caption](path), and the
placeholders {{figure: id | caption | ...}} and {{table: id | caption | ...}}, which are made from the data by the
functions in project_report_figures.py (keyed by id), and {{diagram: id | caption | ...}}, the draw.io file
diagrams/<id>.drawio. Diagrams (.drawio) are exported to PNG with the draw.io desktop app. Figures and tables are numbered per chapter. A placeholder with no
function is printed as a visible "pending" line and listed at the end of the run.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import project_report_style as STYLE  # noqa: E402
import project_report_figures as FIG  # noqa: E402
import project_report_compare as CMP  # noqa: E402
import project_report_dashboards as DASH  # noqa: E402
import project_report_khg as KHGR  # noqa: E402

WORKSPACE = HERE.parents[1]
REPORT = WORKSPACE / "re-peat/reports/project_report"
AUTHOR = "RE-PEAT GIS team, Departemen Teknik Geodesi UGM"
TITLE = "RE-PEAT: peatland rewetting toolkit"
SUBTITLE = "Findings and proposed methodology"
INK, ACCENT, MUTED, WARM = (RGBColor.from_string(c) for c in (STYLE.INK, STYLE.ACCENT, STYLE.MUTED, STYLE.WARM))
RULE = STYLE.RULE
TEXT_WIDTH_CM = 16.0

INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`)")
PLACEHOLDER = re.compile(r"^\{\{\s*(figure|table|diagram)\s*:\s*([^|}]+?)\s*\|\s*([^|}]+?)\s*(?:\|.*)?\}\}\s*$")
IMAGE = re.compile(r"^!\[(.*)\]\((.+)\)\s*$")


def drawio_png(src: Path) -> Path:
    """Export a draw.io diagram to PNG with the draw.io desktop app (DRAWIO, or its default Windows path), when stale."""
    import os
    import subprocess
    out = REPORT / "figures" / f"{src.stem}.png"
    if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
        exe = os.environ.get("DRAWIO", r"C:\Program Files\draw.io\draw.io.exe")
        subprocess.run([exe, "-x", "-f", "png", "-s", "2", "-o", str(out), str(src)], check=True, capture_output=True, timeout=300)
    return out


def set_font(style_or_run, name):
    """Font for every script slot, with Word's theme-font links removed so the named font applies."""
    style_or_run.font.name = name
    rpr = style_or_run.element.get_or_add_rPr()
    rf = rpr.rFonts if rpr.rFonts is not None else rpr._add_rFonts()
    for k in ("ascii", "hAnsi", "eastAsia", "cs"):
        rf.set(qn(f"w:{k}"), name)
    for k in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        rf.attrib.pop(qn(f"w:{k}"), None)


def styles(doc):
    s = doc.styles["Normal"]
    set_font(s, STYLE.SERIF)
    s.font.size, s.font.color.rgb = Pt(10), INK
    s.paragraph_format.space_after, s.paragraph_format.line_spacing = Pt(7), 1.25
    for lvl, size, before, after, color in ((1, 24, 0, 18, ACCENT), (2, 14, 18, 6, ACCENT), (3, 11.5, 12, 4, INK)):
        h = doc.styles[f"Heading {lvl}"]
        set_font(h, STYLE.SANS_SEMI)
        h.font.size, h.font.bold, h.font.italic, h.font.color.rgb = Pt(size), False, False, color
        h.paragraph_format.space_before, h.paragraph_format.space_after = Pt(before), Pt(after)
        h.paragraph_format.keep_with_next = True
        h.paragraph_format.line_spacing = 1.05
    for name in ("List Bullet", "List Bullet 2"):
        doc.styles[name].paragraph_format.space_after = Pt(3)
    c = doc.styles["Caption"]
    set_font(c, STYLE.SANS)
    c.font.size, c.font.italic, c.font.bold, c.font.color.rgb = Pt(8.5), False, False, MUTED
    c.paragraph_format.space_after, c.paragraph_format.line_spacing = Pt(12), 1.1
    # document defaults and theme: no style falls back to Word's Calibri/Cambria theme fonts
    rpr = doc.styles.element.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr"))
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for k in list(rf.attrib):
        del rf.attrib[k]
    for k in ("ascii", "hAnsi", "eastAsia", "cs"):
        rf.set(qn(f"w:{k}"), STYLE.SERIF)
    for st in doc.styles:
        el = st.element.rPr.rFonts if st.element.rPr is not None and st.element.rPr.rFonts is not None else None
        if el is not None and any("Theme" in k or "theme" in k for k in el.attrib):
            set_font(st, STYLE.SANS_SEMI if st.name.startswith(("Heading", "Title")) else STYLE.SERIF)
    # table of contents: chapters in sans semibold, sections in the body serif, tight spacing
    from docx.enum.style import WD_STYLE_TYPE
    for lvl, font, size, before, indent in ((1, STYLE.SANS_SEMI, 10.5, 8, 0), (2, STYLE.SERIF, 9.5, 0, 0.5)):
        name = f"TOC {lvl}"
        t = doc.styles[name] if name in [x.name for x in doc.styles] else doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        t.base_style = doc.styles["Normal"]
        set_font(t, font)
        t.font.size = Pt(size)
        t.font.color.rgb = ACCENT if lvl == 1 else INK
        pf = t.paragraph_format
        pf.space_before, pf.space_after, pf.line_spacing, pf.left_indent = Pt(before), Pt(1), 1.0, Cm(indent)


NUMERIC = re.compile(r"^[-+−<>~≈]?\s?[\d.,]+\s?(%|m|cm|mm|km|ha|km²)?$")


def runs(par, text, size=None, color=None):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**"):
            r = par.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`"):
            r = par.add_run(part[1:-1])
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = par.add_run(part[1:-1]); r.italic = True
        else:
            r = par.add_run(part)
        if size:
            r.font.size = size
        if color:
            r.font.color.rgb = color


def field(par, code):
    r = par.add_run()
    for kind, text in (("begin", None), (None, code), ("separate", None), (None, ""), ("end", None)):
        if kind:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), kind); r._r.append(e)
        elif text:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = text; r._r.append(e)


def column_widths(header, rows, total=TEXT_WIDTH_CM, floor=1.3):
    """Column widths (cm) in proportion to the text each column holds: the square root of its mean cell length, with
    the header's longest word as a minimum, so long-text columns get room and short numeric ones stay narrow."""
    import math
    n = len(header)
    w = []
    for i in range(n):
        cells = [str(r[i]) if i < len(r) and r[i] is not None else "" for r in rows]
        mean = sum(len(s) for s in cells) / max(1, len(cells))
        word = max([len(x) for x in str(header[i]).split()] + [len(x) for s in cells for x in s.split()] + [1])
        w.append(max(math.sqrt(max(mean, 1)), word * 0.45, 2.0))
    s = sum(w)
    out = [max(floor, total * x / s) for x in w]
    k = total / sum(out)
    return [x * k for x in out]


def sans(par, semi=False):
    """Set every run of a paragraph in the report's sans font (tables, cover, footer)."""
    for r in par.runs:
        set_font(r, STYLE.SANS_SEMI if semi else STYLE.SANS)


def rule(par, color, size_eighths, space=4):
    """Bottom border under a paragraph (cover, chapter titles)."""
    pPr = par._p.get_or_add_pPr()
    b = OxmlElement("w:pBdr"); e = OxmlElement("w:bottom")
    for k, v in (("val", "single"), ("sz", str(size_eighths)), ("space", str(space)), ("color", color)):
        e.set(qn(f"w:{k}"), v)
    b.append(e); pPr.append(b)


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hex_fill)
    tcPr.append(sh)


def borders(table):
    tblPr = table._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge, val in (("top", "single"), ("bottom", "single"), ("insideH", "single"), ("left", "nil"), ("right", "nil"), ("insideV", "nil")):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), val); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), RULE); b.append(e)
    tblPr.append(b)


class Builder:
    def __init__(self):
        self.doc = Document()
        styles(self.doc)
        sec = self.doc.sections[0]
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
        sec.left_margin = sec.right_margin = Cm(2.5)
        sec.top_margin, sec.bottom_margin = Cm(2.3), Cm(2.3)
        self.chapter, self.nfig, self.ntab, self.nsec = "0", 0, 0, 0
        self.pending = []

    # --- front matter -------------------------------------------------------------------------------------------------
    def front(self):
        d = self.doc
        cp = d.core_properties
        cp.author = cp.last_modified_by = AUTHOR
        cp.title, cp.subject = TITLE, SUBTITLE
        cp.comments = "World Bank / KLH peatland rewetting project, GIS workstream"
        for _ in range(5):
            d.add_paragraph()
        p = d.add_paragraph(); runs(p, "GIS WORKSTREAM  ·  PEATLAND REWETTING PROJECT", Pt(9.5), ACCENT)
        p.paragraph_format.space_after = Pt(14); sans(p)
        p = d.add_paragraph(); runs(p, TITLE, Pt(34), INK); sans(p, semi=True)
        p.paragraph_format.line_spacing, p.paragraph_format.space_after = 1.0, Pt(8)
        p = d.add_paragraph(); runs(p, SUBTITLE, Pt(17), ACCENT); sans(p)
        rule(p, STYLE.ACCENT, 12, space=14)
        for _ in range(12):
            d.add_paragraph()
        for text, size, color in (("Prepared for the World Bank and the Ministry of Environment / Environmental Control "
                                   "Agency (KLH/BPLH), Republic of Indonesia", 10.5, INK),
                                  ("Departemen Teknik Geodesi, Universitas Gadjah Mada", 10.5, INK),
                                  (date.today().strftime("%B %Y"), 10.5, MUTED)):
            p = d.add_paragraph(); runs(p, text, Pt(size), color); sans(p); p.paragraph_format.space_after = Pt(3)
        p.add_run().add_break(WD_BREAK.PAGE)
        p = d.add_paragraph(); runs(p, "Contents", Pt(24), ACCENT); sans(p, semi=True)
        rule(p, STYLE.ACCENT, 8, space=6); p.paragraph_format.space_after = Pt(18)
        field(d.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u')       # filled by docx_render.ps1 (Word updates the fields)
        fp = d.sections[0].footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = fp.add_run(TITLE + "    "); r.font.size, r.font.color.rgb = Pt(8), MUTED
        field(fp, "PAGE")
        sans(fp)
        d.sections[0].different_first_page_header_footer = True

    # --- blocks ---------------------------------------------------------------------------------------------------------
    def heading(self, text, level):
        if level == 1:
            m = re.match(r"(?:Annex\s+)?(\d+|[A-Z])\b", text)
            self.chapter, self.nfig, self.ntab = (m.group(1) if m else self.chapter), 0, 0
            self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        if level == 1:
            self.nsec = 0
        elif level == 2:                             # "## {n} Title" takes the next section number of the chapter
            m = re.match(r"(\d+|[A-Z])\.(\d+)\b", text)
            if m:
                self.nsec = int(m.group(2))
            elif text.startswith("{n}"):
                self.nsec += 1
                text = f"{self.chapter}.{self.nsec}" + text[3:]
        h = self.doc.add_heading(text, level)
        if level == 1:
            rule(h, STYLE.ACCENT, 8, space=6)

    def caption(self, kind, text):
        if kind == "Figure":
            self.nfig += 1; n = self.nfig
        else:
            self.ntab += 1; n = self.ntab
        p = self.doc.add_paragraph(style="Caption")
        r = p.add_run(f"{kind} {self.chapter}.{n}. "); r.bold = True
        runs(p, text.rstrip("."))
        return p

    def figure(self, path, caption, width_cm=TEXT_WIDTH_CM):
        path = Path(path)
        if not path.is_absolute():
            path = WORKSPACE / path
        if not path.exists():
            return self.missing("figure", str(path), caption)
        if path.suffix == ".drawio":
            path = drawio_png(path)
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(path), width=Cm(width_cm))
        self.caption("Figure", caption)

    def table(self, header, rows, caption, widths=None):
        self.caption("Table", caption).paragraph_format.keep_with_next = True
        t = self.doc.add_table(rows=1, cols=len(header))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        borders(t)
        small = Pt(7.5) if len(header) > 8 else Pt(8.5) if len(header) > 5 else Pt(9)
        for i, h in enumerate(header):
            c = t.rows[0].cells[i]; c.text = ""
            runs(c.paragraphs[0], str(h), small, INK); c.paragraphs[0].runs and setattr(c.paragraphs[0].runs[0], "bold", True)
            for r in c.paragraphs[0].runs:
                r.bold = True
            shade(c, STYLE.ACCENT_SOFT)
        for row in rows:
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""
                runs(cells[i].paragraphs[0], "" if v is None else str(v), small)
                if i and NUMERIC.match(str(v).strip()):
                    cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.space_after = Pt(1); p.paragraph_format.line_spacing = 1.0
        trPr = t.rows[0]._tr.get_or_add_trPr(); h = OxmlElement("w:tblHeader"); h.set(qn("w:val"), "true"); trPr.append(h)
        if not widths:
            widths = column_widths(header, rows)
        t.autofit = False
        for row in t.rows:
            for c, w in zip(row.cells, widths):
                c.width = Cm(w)
        for c in t.rows[0].cells:                    # the header row stays with the first data row
            for q in c.paragraphs:
                q.paragraph_format.keep_with_next = True
        for row in t.rows:                           # a row never breaks across pages
            rp = row._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); cs.set(qn("w:val"), "true"); rp.append(cs)
        for row in t.rows:
            for c in row.cells:
                for q in c.paragraphs:
                    sans(q)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def missing(self, kind, ident, caption):
        self.pending.append((self.chapter, kind, ident))
        p = self.doc.add_paragraph()
        runs(p, f"[{kind} pending: {ident}: {caption}]", Pt(9), RGBColor(0xB0, 0x3A, 0x2E))

    def placeholder(self, kind, ident, caption):
        if kind == "diagram":                       # drawn in draw.io: re-peat/reports/project_report/diagrams/<id>.drawio
            src = REPORT / "diagrams" / f"{ident}.drawio"
            return self.figure(src, caption) if src.exists() else self.missing(kind, ident, caption)
        name, _, arg = ident.partition(":")       # "id:arg" calls REGISTRY[id](arg), e.g. a KHG code
        fn = {**FIG.REGISTRY, **CMP.REGISTRY, **DASH.REGISTRY, **KHGR.REGISTRY}.get(name)
        if fn is None:
            return self.missing(kind, ident, caption)
        try:
            out = fn(arg.strip()) if arg else fn()
        except KHGR.NotAvailable as e:               # outputs not produced yet for this KHG: a quiet note
            p = self.doc.add_paragraph()
            runs(p, f"{caption.split('. Source')[0].rstrip('.')}: not yet available ({e}).", Pt(9), MUTED)
            sans(p); p.runs and setattr(p.runs[0], "italic", True)
            return
        if kind == "figure":
            path, width = (out if isinstance(out, tuple) else (out, TEXT_WIDTH_CM))
            self.figure(path, caption, width)
        else:
            df = out
            self.table(list(df.columns), df.astype(object).where(df.notna(), "").values.tolist(), caption)
            if df.attrs.get("note"):                # footnote under the table (DataFrame.attrs["note"])
                p = self.doc.paragraphs[-1]
                runs(p, df.attrs["note"], Pt(8), MUTED)

    # --- markdown -------------------------------------------------------------------------------------------------------
    def markdown(self, text):
        lines = text.splitlines()
        i, para, tcap = 0, [], None

        def flush():
            if para:
                p = self.doc.add_paragraph(); runs(p, " ".join(s.strip() for s in para)); para.clear()

        while i < len(lines):
            ln = lines[i]
            s = ln.strip()
            if not s:
                flush(); i += 1; continue
            if s.startswith("<!--"):
                while i < len(lines) and "-->" not in lines[i]:
                    i += 1
                i += 1; continue
            m = re.match(r"^(#{1,3})\s+(.*)$", s)
            if m:
                flush(); self.heading(m.group(2).strip(), len(m.group(1))); i += 1; continue
            if s.startswith("Table:"):
                flush(); tcap = s[len("Table:"):].strip(); i += 1; continue
            if s.startswith("|"):
                flush()
                block = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    block.append(lines[i].strip()); i += 1
                cells = [[c.strip() for c in r.strip("|").split("|")] for r in block]
                cells = [r for r in cells if not all(re.fullmatch(r":?-{2,}:?", c) for c in r if c)]
                self.table(cells[0], cells[1:], tcap or "")
                tcap = None; continue
            m = IMAGE.match(s)
            if m:
                flush(); self.figure(m.group(2).strip(), m.group(1).strip()); i += 1; continue
            m = re.match(r"^\{\{\s*include\s*:\s*([^}]+?)\s*\}\}$", s)
            if m:                                    # {{include: dir}}: every dir/*.md (next to the chapters), in name order
                flush()
                for f in sorted(f for f in (REPORT / "chapters" / m.group(1)).glob("*.md") if not f.name.endswith(".sources.md")):
                    self.markdown(f.read_text(encoding="utf-8"))
                i += 1; continue
            m = PLACEHOLDER.match(s)
            if m:
                flush(); self.placeholder(m.group(1), m.group(2).strip(), m.group(3).strip()); i += 1; continue
            m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", ln)
            if m:
                flush()
                indent = len(m.group(1).replace("\t", "    ")) // 2
                style = "List Bullet" if m.group(2) in "-*" else "List Number"
                if indent:
                    style += " 2"
                item = [m.group(3)]
                i += 1
                while i < len(lines) and lines[i].strip() and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) and lines[i].startswith("  "):
                    item.append(lines[i].strip()); i += 1
                if style.startswith("List Number"):
                    # Word's List Number style continues one sequence through the whole document; write the number
                    # from the Markdown with a hanging indent instead, so every list starts where the text says
                    p = self.doc.add_paragraph()
                    pf = p.paragraph_format
                    pf.left_indent, pf.first_line_indent = Cm(0.63 * (indent + 1)), Cm(-0.63)
                    pf.tab_stops.add_tab_stop(Cm(0.63 * (indent + 1)))
                    p.add_run(m.group(2) + "\t")
                    runs(p, " ".join(item))
                else:
                    p = self.doc.add_paragraph(style=style); runs(p, " ".join(item))
                p.paragraph_format.space_after = Pt(3)
                continue
            para.append(s); i += 1
        flush()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(REPORT / "RE-PEAT_project_report.docx"))
    ap.add_argument("--chapters", default=str(REPORT / "chapters"))
    a = ap.parse_args(argv)
    b = Builder()
    b.front()
    files = sorted(f for f in Path(a.chapters).glob("*.md") if not f.name.endswith(".sources.md"))
    for f in files:
        b.markdown(f.read_text(encoding="utf-8"))
    b.doc.save(a.out)
    print(f"wrote {a.out} ({len(files)} chapter files)")
    for ch, kind, ident in b.pending:
        print(f"  pending {kind} in chapter {ch}: {ident}")


if __name__ == "__main__":
    main()
