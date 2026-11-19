"""Earth Engine work done on another machine: a kit for a peer, and the import of what comes back.

    python tools/peer_gee_kit.py build --khg 14.08.01 62.02.03 --dem deltadtm [--name riau_batch1]
    python tools/peer_gee_kit.py import <returned zip or folder> [--force]

build: for each KHG with sub-KHG units of the DEM variant, copies the units into a kit with a run script, the instructions
(English and Bahasa Indonesia) and a copy of repeat-common's source (so the peer runs exactly this code). Products, period
and step come from pipeline.yaml (`neraca:`), as the neraca step uses them. The kit is written to
$REPEAT_KHG/_export/peer_gee/<name>.zip. The peer runs `python run_balance.py --project <their Earth Engine project>` and
sends back results_<name>.zip.

import: checks every KHG of the kit before anything is copied: each product present for the whole period (every unit, every
dekad), the units fingerprint equal to the kit's and to the units now in the KHG folder (a KHG delineated again after the kit
was made is refused), the land-cover table for the same unit ids. Accepted results go to 03_neraca/<dem>/inputs/ and the
yearly files to cache/gee_balance/; the neraca step then finds its inputs complete and makes no Earth Engine call
(repeat_common.fetch_gee_balance). Existing different files are not overwritten without --force.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd

HUB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HUB / "tools"))
from pipeline import config  # noqa: E402
from repeat_common import khg as K  # noqa: E402
from repeat_common.fetch_gee_balance import periods, units_key  # noqa: E402

STEP = "dekad"

RUN_SCRIPT = r'''"""Fetch rain and evapotranspiration per sub-KHG from Earth Engine for every KHG in manifest.json.

    python run_balance.py --project <your Earth Engine cloud project>

Resumes where it stopped (finished years are kept in out/<code>/_gee_cache). At the end it writes results_<kit>.zip.
"""
import argparse, json, subprocess, sys, zipfile
from pathlib import Path

here = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("--project", required=True, help="your Earth Engine cloud project id")
ap.add_argument("--workers", type=int, default=2, help="years fetched at the same time (lower it if Earth Engine says too many requests)")
a = ap.parse_args()
m = json.loads((here / "manifest.json").read_text(encoding="utf-8"))
(here / "logs").mkdir(exist_ok=True)
failed = []
for k in m["khg"]:
    code, out = k["code"], here / "out" / k["code"]
    print(f"== {code} {k['name']} ({k['n_units']} units)", flush=True)
    cmd = [sys.executable, "-m", "repeat_common.fetch_gee_balance", "--units", str(here / "units" / f"{code}.gpkg"),
           "--products", ",".join(m["products"]), "--start", m["start"], "--end", m["end"], "--step", m["step"],
           "--out", str(out), "--workers", str(a.workers), "--project", a.project]
    with open(here / "logs" / f"{code}.log", "a", encoding="utf-8") as log:
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    print("   ok" if r.returncode == 0 else f"   FAILED, see logs/{code}.log (run the script again to resume)", flush=True)
    if r.returncode:
        failed.append(code)
z = here / f"results_{m['kit']}.zip"
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(here / "manifest.json", "manifest.json")
    for p in (here / "out").rglob("*"):
        if p.is_file():
            zf.write(p, p.relative_to(here).as_posix())
    for p in (here / "logs").glob("*.log"):
        zf.write(p, p.relative_to(here).as_posix())
print(f"\nwrote {z.name}" + (f"; {len(failed)} KHG failed: {', '.join(failed)}" if failed else "; all KHG done") + ". Send this file back.")
'''

README = """# Earth Engine kit {kit}

{n} KHG, rain ({rain}) and evapotranspiration ({et}) per sub-KHG per dekad, {start} to {end} (end exclusive).

## English

1. Install Python 3.11 or newer (https://www.python.org/downloads/; on Windows tick "Add python.exe to PATH").
2. Open a terminal in this folder and install the code that comes with the kit:
   `python -m pip install "./repeat-common[gee]"`
3. Sign in to Earth Engine once: `earthengine authenticate` (a browser opens; use the Google account of your Earth Engine
   project). You need a Google Cloud project registered for Earth Engine (noncommercial is fine):
   https://code.earthengine.google.com/register
4. Run: `python run_balance.py --project <your-project-id>`
   It takes roughly 5 to 15 minutes per KHG. If it stops (network, "too many requests"), run the same command again: it
   continues where it stopped. With "too many requests", add `--workers 1`.
5. Send back the file `results_{kit}.zip` that appears in this folder.

## Bahasa Indonesia

1. Pasang Python 3.11 atau lebih baru (https://www.python.org/downloads/; di Windows centang "Add python.exe to PATH").
2. Buka terminal di folder ini dan pasang kode yang disertakan:
   `python -m pip install "./repeat-common[gee]"`
3. Masuk ke Earth Engine sekali: `earthengine authenticate` (browser akan terbuka; pakai akun Google proyek Earth Engine
   Anda). Diperlukan proyek Google Cloud yang terdaftar untuk Earth Engine (nonkomersial cukup):
   https://code.earthengine.google.com/register
4. Jalankan: `python run_balance.py --project <id-proyek-anda>`
   Sekitar 5 sampai 15 menit per KHG. Jika berhenti (jaringan, "too many requests"), jalankan perintah yang sama lagi:
   proses berlanjut dari titik terakhir. Jika muncul "too many requests", tambahkan `--workers 1`.
5. Kirim balik berkas `results_{kit}.zip` yang muncul di folder ini.

## KHG

{table}
"""


def neraca_settings() -> dict:
    s = config.load()
    n = s["neraca"]
    et = n["et"] if isinstance(n["et"], list) else [n["et"]]
    return {"rain": n["rain"], "et": et, "products": [n["rain"], *et], "start": str(n["start"]), "end": str(n["end"]), "step": STEP}


def units_path(code: str, dem: str) -> Path:
    return K.step_dir(code, "02_delineation", dem) / "subkhg_units.gpkg"


def cmd_build(a) -> Path:
    st = neraca_settings()
    name = a.name or f"{date.today():%Y%m%d}_{a.dem}_{len(a.khg)}khg"
    root = Path(tempfile.mkdtemp()) / name
    (root / "units").mkdir(parents=True)
    rows, skipped = [], []
    for code in a.khg:
        r = K.lookup(code)
        u = units_path(r["khg_code"], a.dem)
        if not u.is_file():
            skipped.append(f"{code} (no {a.dem} sub-KHG units: run dem_correction and delineation first)")
            continue
        g = gpd.read_file(u)
        c = r["khg_code"].replace("KHG.", "")
        shutil.copy2(u, root / "units" / f"{c}.gpkg")
        rows.append({"code": c, "name": r["name"], "n_units": len(g), "units_key": units_key(g)})
    if not rows:
        sys.exit("No KHG with units; nothing to pack. " + "; ".join(skipped))
    src = HUB.parent / "repeat-common"
    commit = subprocess.run(["git", "-C", str(src), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "-C", str(src), "status", "--porcelain", "src"], capture_output=True, text=True).stdout.strip())
    shutil.copytree(src / "src", root / "repeat-common" / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
    shutil.copy2(src / "pyproject.toml", root / "repeat-common" / "pyproject.toml")
    man = {"kit": name, "created": str(date.today()), "dem": a.dem, **st,
           "repeat_common": f"{commit}{' with local changes' if dirty else ''}", "khg": rows}
    (root / "manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding="utf-8")
    (root / "run_balance.py").write_text(RUN_SCRIPT, encoding="utf-8")
    table = "| code | KHG | sub-KHG units |\n|---|---|---|\n" + "\n".join(f"| {r['code']} | {r['name']} | {r['n_units']} |" for r in rows)
    (root / "README.md").write_text(README.format(kit=name, n=len(rows), rain=st["rain"], et=", ".join(st["et"]), start=st["start"],
                                                  end=st["end"], table=table), encoding="utf-8")
    out = K.root() / "_export" / "peer_gee" / f"{name}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in root.rglob("*"):
            if p.is_file():
                zf.write(p, (Path(name) / p.relative_to(root)).as_posix())
    shutil.rmtree(root.parent, ignore_errors=True)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB): {len(rows)} KHG, products {', '.join(st['products'])}, {st['start']} to {st['end']}")
    for s in skipped:
        print("skipped", s)
    return out


def check_khg(d: Path, k: dict, man: dict) -> list[str]:
    """Problems with the returned results of one KHG (empty: accepted)."""
    probs = []
    local = units_path(k["code"], man["dem"])
    if not local.is_file():
        return [f"no local {man['dem']} units"]
    g = gpd.read_file(local)
    if units_key(g) != k["units_key"]:
        probs.append("the KHG's units changed since the kit was made (delineated again?): make a new kit")
    ids = set(g["unit_id"].astype(str))
    n_per = len(periods(date.fromisoformat(man["start"]), date.fromisoformat(man["end"]), man["step"]))
    for p in man["products"]:
        f = d / f"balance_{p}_{man['step']}.csv"
        if not f.is_file() or not f.with_suffix(".json").is_file():
            probs.append(f"{p}: missing")
            continue
        meta = json.loads(f.with_suffix(".json").read_text(encoding="utf-8"))
        if (meta.get("units_key"), meta.get("start"), meta.get("end"), meta.get("step")) != (k["units_key"], man["start"], man["end"], man["step"]):
            probs.append(f"{p}: fetched for other units or another period")
        t = pd.read_csv(f, dtype={"unit_id": str})
        if set(t.unit_id) != ids:
            probs.append(f"{p}: unit ids differ")
        if t.groupby("unit_id").start.nunique().min() < n_per:
            probs.append(f"{p}: {t.groupby('unit_id').start.nunique().min()} of {n_per} periods")
    f = d / "units_landcover.csv"
    if not f.is_file():
        probs.append("units_landcover.csv missing")
    elif set(pd.read_csv(f, dtype={"unit_id": str}).unit_id) != ids:
        probs.append("land cover: unit ids differ")
    return probs


def cmd_import(a) -> None:
    src = Path(a.results)
    tmp = None
    if src.is_file():
        tmp = Path(tempfile.mkdtemp())
        with zipfile.ZipFile(src) as zf:
            zf.extractall(tmp)
        src = next(p.parent for p in tmp.rglob("manifest.json"))
    man = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    ok = []
    for k in man["khg"]:
        d = src / "out" / k["code"]
        probs = check_khg(d, k, man) if d.is_dir() else ["no results"]
        print(f"{k['code']:<20} {k['name'][:45]:<45} " + ("ok" if not probs else "REFUSED: " + "; ".join(probs)))
        if not probs:
            ok.append((k, d))
    for k, d in ok:
        dest = K.step_dir(k["code"], "03_neraca", man["dem"]) / "inputs"
        dest.mkdir(parents=True, exist_ok=True)
        files = [f for f in d.iterdir() if f.is_file()]
        clash = [f.name for f in files if (dest / f.name).is_file() and (dest / f.name).read_bytes() != f.read_bytes()]
        if clash and not a.force:
            print(f"{k['code']}: not copied, different files already in {dest}: {', '.join(clash)} (--force to replace)")
            continue
        for f in files:
            shutil.copy2(f, dest / f.name)
        cache = K.folder(k["code"]) / "cache" / "gee_balance"
        cache.mkdir(parents=True, exist_ok=True)
        for f in (d / "_gee_cache").glob("*.csv"):
            if not (cache / f.name).exists():
                shutil.copy2(f, cache / f.name)
        print(f"{k['code']}: copied to {dest}")
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(ok)} of {len(man['khg'])} KHG accepted." + (f" Next: python tools/khg_pipeline.py run --khg {' '.join(k['code'] for k, _ in ok)} "
                                                           f"--dem {man['dem']} --steps deficit neraca prioritisation pump" if ok else ""))
    if len(ok) < len(man["khg"]):
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build")
    p.add_argument("--khg", nargs="+", required=True)
    p.add_argument("--dem", default="deltadtm")
    p.add_argument("--name")
    p = sub.add_parser("import")
    p.add_argument("results", help="results zip (or its unpacked folder) from the peer")
    p.add_argument("--force", action="store_true")
    a = ap.parse_args()
    {"build": cmd_build, "import": cmd_import}[a.cmd](a)


if __name__ == "__main__":
    main()
