"""Layer register: the layers the prioritisation rests on, with their provenance and evidence, and a check that they are unchanged.

    python re-peat/tools/layer_register.py check            # every row: file there, unchanged (sha256), layer and fields present
    python re-peat/tools/layer_register.py fill             # compute the automatic columns of rows that have none (new rows)
    python re-peat/tools/layer_register.py fill --refresh   # recompute them for every row (after a deliberate data update)
    python re-peat/tools/layer_register.py show [THEME]     # print the register, optionally one theme

The register is sites/layer_register.csv, one row per layer (or per group of fields of a multi-theme file such as the PPEG
analysis). Redundant layers are welcome: list each one, with what it is used for. Hand-written columns:
  id, theme, path (relative to $REPEAT_DATA, or to the re-peat repo when it starts with 're-peat/'), layer, fields_used,
  description, producer, legal_basis, version, scale, received (date and from whom), rights, used_for,
  verification (verified / partly verified / not verified / derived), evidence (file of the evidence), notes
Automatic columns (written by fill, compared by check): size_bytes, sha256, features, file_modified.
To add a layer: append a row with the hand-written columns, run `fill`, then `check`, and commit the CSV.
`check` exits 1 when a file is missing, changed, or lacks a listed field; the hashes are cached by size and modification time in
$REPEAT_DATA/derived/layer_register_sha256.json, so a check of unchanged files takes seconds.
Writes docs/24-layer-register.md (the register, readable) on fill and check.
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyogrio

HUB = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("REPEAT_DATA", HUB.parent / "_data"))
CSV = HUB / "sites" / "layer_register.csv"
MD = HUB / "docs" / "24-layer-register.md"
CACHE = DATA / "derived" / "layer_register_sha256.json"
HAND = ["id", "theme", "path", "layer", "fields_used", "description", "producer", "legal_basis", "version", "scale",
        "received", "rights", "used_for", "verification", "evidence", "notes"]
AUTO = ["size_bytes", "sha256", "features", "file_modified"]


def resolve(p):
    return HUB / p[len("re-peat/"):] if p.startswith("re-peat/") else DATA / p


def sha256(path, cache):
    st = path.stat()
    key = f"{path.as_posix()}|{st.st_size}|{int(st.st_mtime)}"
    if key in cache:
        return cache[key]
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    cache[key] = h.hexdigest()
    return cache[key]


def inspect(row, cache):
    """Automatic values and problems of one row."""
    path = resolve(row.path)
    if not path.exists():
        return {}, [f"missing: {row.path}"]
    auto = {"size_bytes": str(path.stat().st_size), "sha256": sha256(path, cache),
            "file_modified": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d"), "features": ""}
    problems = []
    if path.suffix.lower() in (".gpkg", ".shp", ".geojson", ".fgb"):
        layers = [l[0] for l in pyogrio.list_layers(path)]
        layer = row.layer or layers[0]
        if layer not in layers:
            return auto, [f"layer {layer!r} not in {row.path} (has {layers})"]
        info = pyogrio.read_info(path, layer=layer)
        auto["features"] = str(info["features"])
        have = set(info["fields"])
        for f in [f.strip() for f in row.fields_used.split(";") if f.strip()]:
            if f not in have:
                problems.append(f"field {f!r} not in {row.path}:{layer}")
    elif path.suffix.lower() == ".csv":
        cols = set(pd.read_csv(path, nrows=0).columns)
        auto["features"] = str(sum(1 for _ in open(path, encoding="utf-8", errors="replace")) - 1)
        for f in [f.strip() for f in row.fields_used.split(";") if f.strip()]:
            if f not in cols:
                problems.append(f"column {f!r} not in {row.path}")
    return auto, problems


def load():
    d = pd.read_csv(CSV, dtype=str, keep_default_na=False)
    for c in HAND + AUTO:
        if c not in d.columns:
            d[c] = ""
    dup = d.id[d.id.duplicated()]
    if len(dup):
        sys.exit(f"duplicate ids in {CSV.name}: {list(dup)}")
    return d[HAND + AUTO]


def write_md(d):
    lines = ["# Layer register", "",
             "The layers the prioritisation rests on, with provenance and evidence. Source: `sites/layer_register.csv`; "
             "maintained with `python tools/layer_register.py` (see its docstring to add a layer). Generated; do not edit.", ""]
    for theme, g in d.groupby("theme", sort=False):
        lines += [f"## {theme}", "", "| id | layer | fields used | producer | version | scale | verification | used for |",
                  "|---|---|---|---|---|---|---|---|"]
        for _, r in g.iterrows():
            lay = f"`{r.path}`" + (f" ({r.layer})" if r.layer else "")
            lines.append(f"| {r.id} | {lay}<br>{r.description} | {r.fields_used.replace(';', ', ')} | {r.producer} | {r.version} | "
                         f"{r.scale} | {r.verification}{(' — ' + r.evidence) if r.evidence else ''} | {r.used_for} |")
        lines.append("")
    lines += ["## Provenance details", ""]
    for _, r in d.iterrows():
        lines.append(f"- **{r.id}**: legal basis: {r.legal_basis or 'not stated'}; received: {r.received or 'not recorded'}; "
                     f"rights: {r.rights or 'not stated'}; features {r.features or '-'}; sha256 `{r.sha256[:16]}…`"
                     + (f"; {r.notes}" if r.notes else ""))
    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["check", "fill", "show"])
    ap.add_argument("theme", nargs="?")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    d = load()
    if a.action == "show":
        g = d[d.theme.str.casefold() == a.theme.casefold()] if a.theme else d
        print(g[["id", "theme", "path", "layer", "verification"]].to_string(index=False))
        return
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    bad = 0
    for i, r in d.iterrows():
        if a.action == "fill" and r.sha256 and not a.refresh:
            continue
        auto, problems = inspect(r, cache)
        if a.action == "fill":
            for k, v in auto.items():
                d.at[i, k] = v
        else:
            if auto and auto["sha256"] != r.sha256:
                problems.append(f"changed: sha256 {auto['sha256'][:12]} != registered {r.sha256[:12] or '(none, run fill)'}")
            if auto.get("features") and r.features and auto["features"] != r.features:
                problems.append(f"features {auto['features']} != registered {r.features}")
        for p in problems:
            print(f"{r.id}: {p}")
        bad += bool(problems)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=0))
    if a.action == "fill":
        d.to_csv(CSV, index=False)
    write_md(d)
    print(f"{len(d)} rows, {bad} with problems ({a.action})")
    sys.exit(1 if bad and a.action == "check" else 0)


if __name__ == "__main__":
    main()
