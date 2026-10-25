"""Rewrite old absolute paths inside run records after work was moved into a KHG folder.

    python tools/khg_migrate_paths.py <folder> OLD=NEW [OLD=NEW ...]

Run records written before a move (the config.yaml of each run, VRTs, run_report.json, README.md, CSV manifests) hold
absolute paths to where the files used to be. This replaces each OLD path prefix with NEW in every .yaml, .yml, .vrt,
.json, .md and .csv file under <folder>, matching both slash styles and either case of the drive letter, and prints how
many files changed. Logs are left as they were written (they record history). Paths are given relative to the workspace
or absolute.
"""
import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
EXT = {".yaml", ".yml", ".vrt", ".json", ".md", ".csv"}


def variants(p):
    p = str(p if Path(p).is_absolute() else (WS / p)).replace("\\", "/")
    out = set()
    for s in (p, p.replace("/", "\\"), p.replace("/", "\\\\")):
        out |= {s, s[0].lower() + s[1:], s[0].upper() + s[1:]}
    return sorted(out, key=len, reverse=True)


def main():
    folder = Path(sys.argv[1])
    pairs = [a.split("=", 1) for a in sys.argv[2:]]
    changed = 0
    for f in folder.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in EXT:
            continue
        s = f.read_text(encoding="utf-8", errors="surrogateescape")
        t = s
        for old, new in pairs:
            n = str(new if Path(new).is_absolute() else (WS / new))
            for o in variants(old):
                sep = "\\\\" if "\\\\" in o else "\\" if "\\" in o else "/"
                t = t.replace(o, n.replace("\\", "/").replace("/", sep))
        if t != s:
            f.write_text(t, encoding="utf-8", errors="surrogateescape")
            changed += 1
    print(f"{changed} files rewritten under {folder}")


if __name__ == "__main__":
    main()
