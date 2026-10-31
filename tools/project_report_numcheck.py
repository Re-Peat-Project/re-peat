"""Compare the numbers in two versions of a report chapter, to check that an edit of the prose moved no number.

    .venv/Scripts/python.exe re-peat/tools/project_report_numcheck.py <before.md> <after.md>

Lists every number token (digits with , . % and units glued on stripped) whose count differs between the two files.
Placeholder lines ({{figure: ...}}, {{table: ...}}, {{diagram: ...}}) are left out of both sides, since their source
descriptions are not prose. Exit status 1 when any count differs.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

NUM = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")


def numbers(path: str) -> Counter:
    text = "\n".join(ln for ln in Path(path).read_text(encoding="utf-8").splitlines() if not ln.strip().startswith("{{"))
    return Counter(m.group().replace(",", "").lstrip("-") for m in NUM.finditer(text))


def main(argv=None) -> int:
    a, b = (argv or sys.argv[1:])[:2]
    na, nb = numbers(a), numbers(b)
    diff = sorted(k for k in set(na) | set(nb) if na[k] != nb[k])
    for k in diff:
        print(f"{k:>14}  before {na[k]:>3}  after {nb[k]:>3}")
    print(f"{len(diff)} number(s) differ")
    return 1 if diff else 0


if __name__ == "__main__":
    sys.exit(main())
