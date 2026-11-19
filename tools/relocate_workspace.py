"""After moving the workspace folder: rewrite the old absolute workspace path in the files programs read back.

    python tools/relocate_workspace.py --old "C:/Users/me/Documents/Github/_repeat-project" [--write]

Without --write it only lists what would change. The new path is this workspace (the folder holding re-peat). Rewritten:
configs (*.yaml, *.yml), raster mosaics (*.vrt) and the state files read on a resume or by a report (the pump's run_state.json
and run_config.json, the prioritisation's laporan.json, the layer register's hash cache). Each path keeps its separator
style (/ or \\, and \\\\ inside JSON), so the pump's stage fingerprints stay equal to its rewritten configs and no stage reruns.
Logs, reports, provenance records and run_report.json keep the path they were made with: they record what was run where.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
SUFFIXES = {".yaml", ".yml", ".vrt"}
NAMES = {"run_state.json", "run_config.json", "laporan.json", "layer_register_sha256.json"}
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__"}


def pattern(old: str) -> re.Pattern:
    """The old path with any separator (/, \\ or JSON-escaped \\\\) between its parts, any letter case."""
    parts = [re.escape(p) for p in re.split(r"[\\/]+", old.strip().rstrip("\\/")) if p]
    return re.compile(r"(?i)" + parts[0] + r"(?P<sep>\\\\|\\|/)" + r"(?:\\\\|\\|/)".join(parts[1:]))


def new_path(sep: str) -> str:
    return sep.join([WS.drive or WS.parts[0].rstrip("\\/"), *WS.parts[1:]])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--old", required=True, help="the workspace's previous absolute path")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    rx = pattern(a.old)
    n_files = n_hits = 0
    for p in WS.rglob("*"):
        if not p.is_file() or (p.suffix.lower() not in SUFFIXES and p.name not in NAMES) or SKIP_DIRS & set(p.parts):
            continue
        try:
            raw = p.read_bytes()
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new, k = rx.subn(lambda m: new_path(m.group("sep")), text)
        if not k:
            continue
        n_files, n_hits = n_files + 1, n_hits + k
        if a.write:
            p.write_bytes(new.encode("utf-8"))       # bytes: line endings stay as they were
        else:
            print(f"{k:4d}  {p.relative_to(WS)}")
    print(f"{'rewrote' if a.write else 'would rewrite'} {n_hits} paths in {n_files} files -> {WS}")


if __name__ == "__main__":
    main()
