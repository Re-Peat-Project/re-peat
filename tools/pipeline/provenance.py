"""What a run depended on, so a result can be traced and repeated: environment lock files, a checksum manifest of the input data,
and one provenance record per run.

- ``lock(s)``: the installed packages of every environment of pipeline.yaml (``python:``) into re-peat/env/<env>.lock.txt; editable
  installs of the module repositories are written as ``-e ./<repo>`` (install from the workspace folder), so the files work on any machine.
- ``repo_lock(s)``: the commit of every module repository into re-peat/env/repos.lock.txt; ``setup --clone`` checks these out.
- ``data_files(s)``: the files of the data folder the chain reads: the national files of pipeline.yaml and, per KHG
  (sites/*/khg.yaml), the DEM sources and the peat-depth raster. ``data_manifest(s, write)`` writes or checks
  sites/data_manifest.csv (path relative to the data folder, size, sha256).
- ``record(s)``: $REPEAT_KHG/pipeline_provenance/<time>.json with the commit and uncommitted-change count of every repository, the
  sha256 of each lock file and whether the installed packages still match it, the sha256 of the data manifest and of the settings,
  and the start time (the access date of the online sources: Earth Engine, Planetary Computer, SlideRule, S3 tiles).
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from .config import HUB, Settings

ENV_DIR = HUB / "env"
MANIFEST = HUB / "sites" / "data_manifest.csv"


def _sha(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


FREEZE = r"""
import importlib.metadata as m, json
for d in m.distributions():
    name = d.metadata["Name"]
    url = d.read_text("direct_url.json")
    info = json.loads(url) if url else {}
    if info.get("dir_info", {}).get("editable") or info.get("url", "").startswith("file:"):
        print("LOCAL", name, info.get("url", ""))
    else:
        print("PKG", name, d.version)
"""


def _freeze(py: str, ws: Path) -> list[str]:
    """The installed distributions of an environment (read with importlib.metadata, so environments without pip work too);
    a local or editable install of a workspace repository is written as ``-e ./<repo>`` (install from the workspace folder)."""
    out = subprocess.run([py, "-c", FREEZE], capture_output=True, text=True, check=True).stdout.splitlines()
    repos = {d.name.lower(): d.name for d in ws.iterdir() if d.is_dir()}
    lines = set()
    for ln in out:
        kind, name, rest = (ln.split(" ", 2) + ["", ""])[:3]
        if kind == "PKG":
            lines.add(f"{name}=={rest}")
        elif kind == "LOCAL":
            folder = Path(rest.replace("file:///", "").replace("file://", "")).name.lower() if rest else ""
            hit = repos.get(folder) or repos.get(name.lower()) or repos.get(name.lower().replace("_", "-"))
            lines.add(f"-e ./{hit}" if hit else f"# local install, not portable: {name} {rest}")
    return sorted(lines, key=str.lower)


def lock(s: Settings) -> list[Path]:
    ENV_DIR.mkdir(exist_ok=True)
    written = []
    for env, py in s["python"].items():
        if env == "qgis" or not py or not Path(py).is_file():
            continue
        f = ENV_DIR / f"{env}.lock.txt"
        f.write_text(f"# installed packages of the '{env}' environment (tools/khg_pipeline.py setup --lock), {datetime.date.today()}\n"
                     f"# install from the workspace folder: python -m venv <env>; <env>/python -m pip install -r re-peat/env/{f.name}\n"
                     + "\n".join(_freeze(py, s.ws)) + "\n", encoding="utf-8")
        written.append(f)
    return written


def lock_matches(s: Settings) -> dict:
    """Per environment: True when the installed packages equal the lock file, False when they differ, None without a lock."""
    res = {}
    for env, py in s["python"].items():
        f = ENV_DIR / f"{env}.lock.txt"
        if env == "qgis" or not py or not Path(py).is_file() or not f.is_file():
            res[env] = None
            continue
        want = [ln for ln in f.read_text(encoding="utf-8").splitlines() if ln and not ln.startswith("#")]
        res[env] = want == [ln for ln in _freeze(py, s.ws) if not ln.startswith("#")]
    return res


def data_files(s: Settings) -> list[Path]:
    n = s["national"]
    files = {s.data / v["path"] for k, v in n.items() if isinstance(v, dict) and v.get("path")}
    for p in sorted((HUB / "sites").glob("*/khg.yaml")):
        kc = yaml.safe_load(p.read_text(encoding="utf-8"))
        for d in (kc.get("dems") or {}).values():
            for src in d.get("sources") or []:
                files.add(Path(src.replace("${REPEAT_DATA}", str(s.data))))
        pdp = (kc.get("peat_depth") or {}).get("path")
        if pdp:
            files.add(Path(pdp.replace("${REPEAT_DATA}", str(s.data))))
    return sorted(f for f in files if f.is_file())


def data_manifest(s: Settings, write: bool) -> list[str]:
    """Write sites/data_manifest.csv, or check the data folder against it; returns the problems found (empty when it matches)."""
    if write:
        rows = [{"path": str(f.relative_to(s.data)).replace("\\", "/"), "bytes": f.stat().st_size, "sha256": _sha(f)} for f in data_files(s)]
        with open(MANIFEST, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["path", "bytes", "sha256"])
            w.writeheader()
            w.writerows(rows)
        return []
    problems = []
    for r in csv.DictReader(open(MANIFEST, encoding="utf-8")):
        f = s.data / r["path"]
        if not f.is_file():
            problems.append(f"missing: {r['path']}")
        elif f.stat().st_size != int(r["bytes"]) or _sha(f) != r["sha256"]:
            problems.append(f"differs: {r['path']}")
    return problems


def _git(repo: Path) -> dict:
    def g(*a):
        r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    head = g("rev-parse", "HEAD")
    return {"commit": head, "uncommitted_files": len((g("status", "--porcelain") or "").splitlines()),
            "pushed": bool(head and g("branch", "-r", "--contains", head))}


REPO_LOCK = ENV_DIR / "repos.lock.txt"


def repo_lock(s: Settings) -> tuple[Path, list[str]]:
    """Write env/repos.lock.txt: the commit of each module repository (re-peat itself is left out: the file lives in it).
    Returns the file and warnings for repositories with uncommitted changes or a commit not on any remote branch."""
    lines, warn = [], []
    for name in s["repos"]:
        st = _git(s.ws / name)
        if not st["commit"]:
            warn.append(f"{name}: not a git repository here, left out")
            continue
        lines.append(f"{name} {st['commit']}")
        if st["uncommitted_files"]:
            warn.append(f"{name}: {st['uncommitted_files']} uncommitted files are not in the locked commit")
        if not st["pushed"]:
            warn.append(f"{name}: commit {st['commit'][:7]} is not on any remote branch; push it before peers clone")
    ENV_DIR.mkdir(exist_ok=True)
    REPO_LOCK.write_text(f"# commit of each module repository (tools/khg_pipeline.py setup --lock), {datetime.date.today()}\n"
                         "# setup --clone checks these out; setup reports repositories on another commit\n"
                         + "\n".join(lines) + "\n", encoding="utf-8")
    return REPO_LOCK, warn


def repo_locked() -> dict:
    if not REPO_LOCK.is_file():
        return {}
    return dict(ln.split() for ln in REPO_LOCK.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#"))


def record(s: Settings) -> str:
    """Write the provenance of a run; returns its id (the file stem)."""
    now = datetime.datetime.now()
    rid = now.strftime("%Y%m%d_%H%M%S")
    settings = (HUB / "pipeline.yaml").read_bytes() + ((HUB / "pipeline.local.yaml").read_bytes() if (HUB / "pipeline.local.yaml").exists() else b"")
    rec = {"id": rid, "started": now.isoformat(timespec="seconds"),
           "repos": {name: _git(s.ws / name) for name in ["re-peat", *s["repos"]]},
           "repos_match_lock": {k: (s.ws / k).is_dir() and _git(s.ws / k)["commit"] == v for k, v in repo_locked().items()},
           "lock_files": {f.stem: _sha(f) for f in sorted(ENV_DIR.glob("*.lock.txt"))},
           "installed_matches_lock": lock_matches(s),
           "data_manifest_sha256": _sha(MANIFEST) if MANIFEST.exists() else None,
           "settings_sha256": hashlib.sha256(settings).hexdigest(),
           "data": str(s.data), "khg_root": str(s.khg_root),
           "online_sources_accessed": now.date().isoformat(),
           "note": "Earth Engine, Planetary Computer, SlideRule and the S3 tiles are read live; their archives can change after this date."}
    d = s.khg_root / "pipeline_provenance"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{rid}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return rid
