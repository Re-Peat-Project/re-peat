"""Visual identity of the RE-PEAT project report: fonts and colours shared by the Word build (project_report.py), the
charts (project_report_figures.py, project_report_dashboards.py) and the draw.io diagrams (project_report_diagrams.py).

Fonts are Source Serif 4 (body text) and Source Sans 3 (headings, captions, tables, charts, diagrams), SIL Open Font
Licence, kept in re-peat/reports/project_report/fonts/. Word and draw.io need them installed for the user (copy the
.ttf files to %LOCALAPPDATA%/Microsoft/Windows/Fonts and register them under HKCU, or double-click and Install);
docx_render.ps1 embeds them in the Word file so readers without them see the same page. Matplotlib loads them by path.
"""
from __future__ import annotations

from pathlib import Path

FONT_DIR = Path(__file__).resolve().parents[1] / "reports" / "project_report" / "fonts"
SANS, SANS_SEMI, SERIF = "Source Sans 3", "Source Sans 3 Semibold", "Source Serif 4"

# colours (hex without #)
INK = "1F2A30"        # text
ACCENT = "0B5D5B"     # deep teal: headings, method boxes, rules
ACCENT_SOFT = "E3EDEC"
WARM = "C2632E"       # outputs, highlights
WARM_SOFT = "F6E9E0"
NATIONAL = "4C6FA8"   # national-scale steps
NATIONAL_SOFT = "E8ECF4"
MUTED = "5F6B70"      # secondary text, axes
RULE = "B8C4C2"       # table rules
GRID = "DDE3E2"


def register_matplotlib() -> None:
    """Add the report fonts to matplotlib and set them as the default family."""
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    for f in sorted(FONT_DIR.glob("SourceSans3-*.ttf")):
        font_manager.fontManager.addfont(str(f))
    plt.rcParams["font.family"] = SANS
