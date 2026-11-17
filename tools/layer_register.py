"""Layer register: the layers the prioritisation rests on, with their provenance and evidence, and a check that they are unchanged.

    python re-peat/tools/layer_register.py check            # every row: file there, unchanged (sha256), layer and fields present
    python re-peat/tools/layer_register.py fill             # compute the automatic columns of rows that have none (new rows)
    python re-peat/tools/layer_register.py fill --refresh   # recompute them for every row (after a deliberate data update)
    python re-peat/tools/layer_register.py show [THEME]     # print the register, optionally one theme
    python re-peat/tools/layer_register.py pack [--replace] # one GeoPackage with every registered layer (after a passing check)

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

pack writes $REPEAT_DATA/derived/prioritisation_layers.gpkg (--out to change; not tracked: it holds KLH data):
  khg_summary      the 865 KHG polygons with every per-KHG attribute: KLH priority (337, 362), data availability and run class
                   (av_*), PPEG sums (ppeg_*), tenure areas (tenure_*), tenure complexity (c_*, tenure_complexity), and the
                   prioritisation (pr_*: indicators, the five scores, type, intervention, ranks)
  ppeg_integrated  KLH's PPEG analysis whole, plus one view per field group (v_ppeg_damage = SKEG 2024, v_ppeg_canal, ...)
  <id>             every registered vector layer, copied whole with its CRS and fields; CSV rows as attribute tables; rows that
                   share one file and layer (the PPEG field groups) share one pack layer named after the file
  layer_register   the register, with the pack layer of each row and the pack date
An existing pack is renamed with its date, never overwritten; the pack is built under a temporary name and renamed when complete;
--resume continues an interrupted build (layers whose feature count matches the source are kept, khg_summary is rewritten).
"""
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import geopandas as gpd
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


def pack_name(d):
    """Layer name in the pack for each row: the row id, or for a file/layer shared by several rows (the PPEG analysis) one name."""
    names = {}
    for (path, layer), g in d.groupby(["path", "layer"], sort=False):
        if len(g) == 1:
            nm = g.id.iloc[0]
        elif g.id.str.startswith("ppeg_").all():
            nm = "ppeg_integrated"            # KLH's PPEG integrated analysis; one view per field group (v_<id>)
        else:
            nm = re.sub(r"[^a-z0-9]+", "_", Path(path).stem.lower()).strip("_")[:50]
        for i in g.index:
            names[i] = nm
    return pd.Series(names).reindex(d.index)


def khg_summary():
    """The 865 KHG polygons with every per-KHG attribute the project holds (one row per KHG)."""
    rep = HUB / "reports"
    g = gpd.read_file(DATA / "derived" / "khg_klh_priority.gpkg", layer="khg")
    av = pd.read_csv(HUB / "sites" / "khg_availability.csv")
    keep = ["code", "run_class", "peat_depth_source", "deltadtm_share", "lidar_share", "bbsdlp_share", "feg50k_share",
            "licence_share_any", "blocks_brgm", "canal_km_total", "canal_density_km_per_km2", "stations_community",
            "stations_concession", "p_annual_mm", "e_annual_mm", "dry_shortfall_mm"]
    g = g.merge(av[[c for c in keep if c in av]].rename(columns={"code": "khg_code"}).add_prefix("av_").rename(columns={"av_khg_code": "khg_code"}),
                on="khg_code", how="left")
    pp = pd.read_csv(rep / "national_profile" / "ppeg" / "ppeg_khg.csv")
    pp = pp[pp.khg_code.astype(str).str.startswith("KHG.")]
    pp = pp.drop(columns=[c for c in ("khg_name", "island", "provinces", "priority", "priority_rank", "in_target_villages",
                                        "has_skeg_damage", "target_village_ha", "priority_ha", "priority_in_target_villages_ha") if c in pp])
    g = g.merge(pp.add_prefix("ppeg_").rename(columns={"ppeg_khg_code": "khg_code"}), on="khg_code", how="left")
    ta = pd.read_csv(rep / "national_profile" / "tenure" / "tenure_area.csv")
    tw = ta.pivot_table(index="khg_id", columns="tenure", values=["peat_km2", "burned_peat_km2"], aggfunc="sum").fillna(0)
    tw.columns = [f"tenure_{t}_{v}" for v, t in tw.columns]
    g = g.merge(tw.round(3), left_on="khg_code", right_index=True, how="left")
    tc = pd.read_csv(rep / "national_profile" / "tenure_complexity" / "tenure_complexity.csv").drop(columns=["khg"])
    g = g.merge(tc.rename(columns={"khg_id": "khg_code", "peat_km2": "tc_peat_km2", "points": "tc_points"}), on="khg_code", how="left")
    fk = rep / "national_profile" / "final" / "final_khg.csv"      # the prioritisation: indicators, five scores, type, intervention, ranks
    if fk.exists():
        f = pd.read_csv(fk).drop(columns=["khg_name", "island", "provinces"], errors="ignore")
        f = f.drop(columns=[c for c in f.columns if c != "khg_code" and c in g.columns])
        g = g.merge(f.add_prefix("pr_").rename(columns={"pr_khg_code": "khg_code"}), on="khg_code", how="left")
    return g


def ppeg_views(gpkg, d):
    """One SQL view per field group of the PPEG analysis (v_<id>: the group's fields, the KHG and the geometry), so a theme such
    as SKEG 2024 damage opens as its own layer without copying the 989,398 polygons again. Registered in gpkg_contents."""
    import sqlite3
    con = sqlite3.connect(gpkg)
    cols = {r[1] for r in con.execute("PRAGMA table_info(ppeg_integrated)")}
    if not cols:
        return 0
    geo = con.execute("SELECT column_name, geometry_type_name, srs_id FROM gpkg_geometry_columns WHERE table_name='ppeg_integrated'").fetchone()
    ext = con.execute("SELECT min_x, min_y, max_x, max_y FROM gpkg_contents WHERE table_name='ppeg_integrated'").fetchone()
    n = 0
    for r in d[d.pack_layer == "ppeg_integrated"].itertuples():
        f = [c for c in str(r.fields_used).split(";") if c in cols and c not in ("NAMA_KHG",)]
        v = f"v_{r.id}"
        con.execute(f"DROP VIEW IF EXISTS {v}")
        con.execute(f"CREATE VIEW {v} AS SELECT fid, {geo[0]}, NAMA_KHG{''.join(', ' + c for c in f)} FROM ppeg_integrated")
        con.execute("DELETE FROM gpkg_contents WHERE table_name=?", (v,)); con.execute("DELETE FROM gpkg_geometry_columns WHERE table_name=?", (v,))
        con.execute("INSERT INTO gpkg_contents (table_name, data_type, identifier, description, min_x, min_y, max_x, max_y, srs_id) VALUES (?,?,?,?,?,?,?,?,?)",
                    (v, "features", v, f"{r.description} (view of ppeg_integrated)", *ext, geo[2]))
        con.execute("INSERT INTO gpkg_geometry_columns (table_name, column_name, geometry_type_name, srs_id, z, m) VALUES (?,?,?,?,0,0)", (v, geo[0], geo[1], geo[2]))
        n += 1
    con.commit(); con.close()
    return n


def copy_layer(src, layer, dst, name, chunk=100_000):
    """Copy a vector layer into the pack in chunks (the PPEG file is 989,398 polygons), keeping its CRS and fields."""
    info = pyogrio.read_info(src, layer=layer or None)
    n = info["features"]
    for off in range(0, max(n, 1), chunk):
        part = pyogrio.read_dataframe(src, layer=layer or None, skip_features=off, max_features=chunk)
        pyogrio.write_dataframe(part, dst, layer=name, driver="GPKG", append=off > 0)
    return n


def pack(d, out, replace, resume=False):
    tmp = out.with_suffix(".building.gpkg")
    have = {}
    if resume and tmp.exists():
        have = {l: pyogrio.read_info(tmp, layer=l)["features"] for l, _ in pyogrio.list_layers(tmp)}
        print(f"resuming {tmp.name}: {len(have)} layers there")
    elif tmp.exists():
        tmp.unlink()
    if out.exists():
        if not replace:
            sys.exit(f"{out} exists: pass --replace to rename it (date suffix) and build a new one")
        old = out.with_name(f"{out.stem}_{datetime.fromtimestamp(out.stat().st_mtime):%Y%m%d_%H%M}{out.suffix}")
        out.rename(old)
        print(f"renamed the previous pack to {old.name}")
    d = d.copy()
    d["pack_layer"] = pack_name(d)
    t0 = datetime.now()
    s = khg_summary()
    pyogrio.write_dataframe(s, tmp, layer="khg_summary", driver="GPKG", layer_options={"OVERWRITE": "YES"})
    print(f"khg_summary: {len(s)} KHG, {s.shape[1] - 1} attributes")
    done = set()
    for _, r in d.iterrows():
        if r.pack_layer in done:
            continue
        done.add(r.pack_layer)
        src = resolve(r.path)
        if r.pack_layer in have:
            want = (pyogrio.read_info(src, layer=r.layer or None)["features"] if src.suffix.lower() != ".csv"
                    else len(pd.read_csv(src, dtype=str, keep_default_na=False)))
            if have[r.pack_layer] == want:
                print(f"{r.pack_layer}: already packed ({want:,})")
                continue
            sys.exit(f"{r.pack_layer} is incomplete in {tmp.name} ({have[r.pack_layer]:,} of {want:,}): rebuild without --resume")
        if src.suffix.lower() in (".gpkg", ".shp", ".geojson", ".fgb"):
            n = copy_layer(src, r.layer, tmp, r.pack_layer)
        elif src.suffix.lower() == ".csv":
            t = pd.read_csv(src, dtype=str, keep_default_na=False)
            pyogrio.write_dataframe(t, tmp, layer=r.pack_layer, driver="GPKG")
            n = len(t)
        else:
            d.loc[d.pack_layer == r.pack_layer, "pack_layer"] = "(not packed: " + src.suffix + ")"
            print(f"{r.id}: {src.suffix} not packed")
            continue
        print(f"{r.pack_layer}: {n:,} ({(datetime.now() - t0).seconds} s)", flush=True)
    nv = ppeg_views(tmp, d)
    if nv:
        print(f"ppeg_integrated: {nv} theme views (v_ppeg_*)")
        d.loc[d.pack_layer == "ppeg_integrated", "pack_layer"] = "ppeg_integrated (view v_" + d.id + ")"
    reg = d.assign(packed=str(date.today()))
    pyogrio.write_dataframe(reg, tmp, layer="layer_register", driver="GPKG", layer_options={"OVERWRITE": "YES"})
    tmp.rename(out)
    print(f"wrote {out} ({out.stat().st_size / 1e9:.2f} GB, {len(done) + 2} layers, {(datetime.now() - t0).seconds} s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["check", "fill", "show", "pack"])
    ap.add_argument("theme", nargs="?")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", type=Path, default=DATA / "derived" / "prioritisation_layers.gpkg")
    ap.add_argument("--replace", action="store_true", help="pack: rename an existing pack (date suffix) and build a new one")
    ap.add_argument("--resume", action="store_true", help="pack: continue an interrupted build, keeping the complete layers already copied")
    a = ap.parse_args()
    d = load()
    if a.action == "pack":
        cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
        bad = [r.id for _, r in d.iterrows() if inspect(r, cache)[1] or inspect(r, cache)[0].get("sha256") != r.sha256]
        if bad:
            sys.exit(f"not packing: rows fail the check ({bad}); run `check` and fix them first")
        pack(d, a.out, a.replace, a.resume)
        return
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
