"""List the numbers of a per-KHG section of the project report that cannot be traced.

    .venv/Scripts/python.exe re-peat/tools/project_report_khgcheck.py [<code> ...]

For each section chapters/khg/NN_<code>_*.md (prose only: placeholder lines, HTML comments and headings are left out) every number
is looked up in the output of `project_report_khg.py numbers <code>` and in the text of chapters 2 to 9. A number found in neither is
printed with its sentence, so it can be traced to a file, recomputed, or removed. Ratios and differences the writer states as such
show up here too; check them against the numbers they come from. Needs REPEAT_KHG, REPEAT_DATA and REPEAT_HUB as for the build.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]
CH = WS / "re-peat/reports/project_report/chapters"
NUM = re.compile(r"(?<![\w.])[-+−]?\d[\d,]*(?:\.\d+)?")


def tokens(text: str) -> set[str]:
    out = set()
    for m in NUM.finditer(text):
        t = m.group().replace(",", "").replace("−", "-").lstrip("+")
        out.add(t); out.add(t.lstrip("-"))
        if "." in t:
            out.add(t.rstrip("0").rstrip("."))
    return out


def prose(path: Path) -> list[str]:
    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith(("{{", "#", "|", "!["))]
    return re.split(r"(?<=[.;:])\s+", " ".join(lines))


def main(argv=None) -> int:
    codes = (argv or sys.argv[1:])
    files = sorted(f for f in (CH / "khg").glob("*.md") if not f.name.endswith(".sources.md"))
    ctx = set()
    for f in CH.glob("0[2-9]*.md"):
        if not f.name.endswith(".sources.md"):
            ctx |= tokens(f.read_text(encoding="utf-8"))
    bad = 0
    for f in files:
        code = f.stem.split("_")[1]
        if codes and code not in codes:
            continue
        nums = subprocess.run([sys.executable, "-W", "ignore", str(HERE / "project_report_khg.py"), "numbers", code],
                              capture_output=True, text=True, encoding="utf-8").stdout
        known = tokens(nums) | ctx
        miss = []
        for s in prose(f):
            for m in NUM.finditer(s):
                t = m.group().replace(",", "").replace("−", "-").lstrip("+")
                if t.lstrip("-") in known or t in known or re.fullmatch(r"(19|20)\d\d", t) or t in {"0", "1", "2", "3"}:
                    continue
                miss.append((t, s.strip()[:170]))
        print(f"== {code} {f.stem}: {len(miss)} untraced")
        for t, s in miss:
            print(f"   {t:>8}  {s}")
        bad += len(miss)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
