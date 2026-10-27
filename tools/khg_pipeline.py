"""The full RE-PEAT chain for many KHG, once per DEM (docs/18-full-run-plan.md, docs/19-running-the-pipeline.md).

    python tools/khg_pipeline.py setup [--lock]             # check repositories, interpreters, folders, lock files (--clone, --lock: write them)
    python tools/khg_pipeline.py data [--write]             # check the data folder against sites/data_manifest.csv (--write: make it)
    python tools/khg_pipeline.py init [--khg CODE ...] [--overwrite]   # write sites/<folder>/khg.yaml per KHG
    python tools/khg_pipeline.py status [--khg ...]         # what is done, what can run, what is missing -> $REPEAT_KHG/pipeline_status.csv
    python tools/khg_pipeline.py plan [--khg ...] [--steps ...] [--dem ...]   # the commands `run` would execute, nothing run
    python tools/khg_pipeline.py run  [--khg ...] [--steps ...] [--dem ...] [--force]
    python tools/khg_pipeline.py compare [--khg ...]        # one row per KHG and DEM: units, sekat, water, budget -> $REPEAT_KHG/pipeline_compare.csv

Settings: pipeline.yaml (shared; pipeline.local.yaml overrides it on one machine) and sites/<folder>/khg.yaml (per KHG). Without
--khg, the KHG with a khg.yaml are used (for `init`: the confirmed rows of sites/selected_khg.csv plus extra_khg).
`run` executes one command at a time (parallel heavy jobs ran this machine out of memory on 2026-10-27), skips a step whose output
is there (--force reruns it), logs each step to $REPEAT_KHG/<folder>/logs/pipeline_<step>[_<dem>].log, records a failure and goes on
with the next KHG or DEM (steps after a failed one are skipped for that KHG or DEM), and refreshes pipeline_status.csv.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pipeline import config  # noqa: E402

S = config.load()
sys.path.insert(0, str(S.ws / "repeat-common" / "src"))
from pipeline import khgconf, provenance  # noqa: E402
from pipeline.steps import STEPS, Ctx  # noqa: E402


def codes(a, init: bool = False) -> list[str]:
    if a.khg:
        return khgconf.khg_codes(S, a.khg)
    if init:
        return khgconf.khg_codes(S, None)
    return [khgconf.load(S, p.parent.name.split("_", 1)[0])["khg"]["code"] for p in sorted((config.HUB / "sites").glob("*/khg.yaml"))]


def units(a) -> list[tuple[str, dict, str, str | None]]:
    """(code, khg config, step, dem) in run order: per KHG, each step, each DEM for the per-DEM steps."""
    steps = a.steps or S["steps"]
    dems = a.dem or S["dems"]["variants"]
    out = []
    for code in codes(a):
        kc = khgconf.load(S, code)
        for st in [x for x in S["steps"] if x in steps]:
            for dem in (dems if STEPS[st].per_dem else [None]):
                out.append((code, kc, st, dem))
    return out


# ---------------------------------------------------------------------------------------------------------------- commands
def cmd_setup(a) -> None:
    ok = True
    print(f"workspace {S.ws}\ndata      {S.data} ({'ok' if S.data.is_dir() else 'MISSING'})\nkhg root  {S.khg_root} ({'ok' if S.khg_root.is_dir() else 'will be created'})")
    if a.lock:
        f, warn = provenance.repo_lock(S)
        print(f"wrote {f.relative_to(config.HUB)}" + "".join(f"\n  warning: {w}" for w in warn))
    pinned = provenance.repo_locked()
    for repo, url in S["repos"].items():
        p = S.ws / repo
        if not p.is_dir() and a.clone:
            subprocess.run(["git", "clone", url, str(p)], check=False)
            if repo in pinned:
                subprocess.run(["git", "-C", str(p), "checkout", "--quiet", pinned[repo]], check=False)
        if not p.is_dir():
            print(f"repo   {repo:<22} MISSING  git clone {url}")
            ok = False
            continue
        head = provenance._git(p)["commit"]
        want = pinned.get(repo)
        note = ("" if not want else "at the locked commit" if head == want
                else f"DIFFERS from env/repos.lock.txt ({want[:7]}): git -C {repo} fetch; git -C {repo} checkout {want[:7]}")
        print(f"repo   {repo:<22} ok  {(head or '')[:7]}  {note}")
    for env, py in S["python"].items():
        there = bool(py) and Path(py).is_file()
        print(f"python {env:<22} {'ok' if there else ('not set' if not py else 'MISSING')}  {py}")
        ok &= there or env == "qgis"
    for k, v in (S.get("environment") or {}).items():
        print(f"env    {k:<22} {v}")
    if a.lock:
        for f in provenance.lock(S):
            print(f"wrote {f.relative_to(config.HUB)}")
    for env, match in provenance.lock_matches(S).items():
        if match is not None:
            print(f"lock   {env:<22} {'installed packages match env/' + env + '.lock.txt' if match else 'DIFFERS from env/' + env + '.lock.txt'}")
    print("\nready" if ok else "\nnot ready: see docs/19-running-the-pipeline.md, 'Setting up a machine'")


def cmd_data(a) -> None:
    if a.write:
        provenance.data_manifest(S, write=True)
        print(f"wrote {provenance.MANIFEST.relative_to(config.HUB)} ({len(provenance.data_files(S))} files)")
        return
    problems = provenance.data_manifest(S, write=False)
    print("\n".join(problems) if problems else f"the data folder matches {provenance.MANIFEST.relative_to(config.HUB)}")


def cmd_init(a) -> None:
    for code in codes(a, init=True):
        p, written = khgconf.write(S, code, a.overwrite)
        print(f"{'wrote' if written else 'kept '} {p.relative_to(config.HUB)}")


def state(code: str, kc: dict, st: str, dem: str | None) -> str:
    c = Ctx(S, kc, dem)
    why = STEPS[st].applies(c)
    if why:
        return "n/a: " + why
    return "done" if STEPS[st].done(c) else "to do"


def cmd_status(a) -> Path:
    rows = {}
    for code, kc, st, dem in units(a):
        key = (code, dem or "")
        r = rows.setdefault(key, {"khg": code, "name": kc["khg"]["name"], "dem": dem or "(once)"})
        r[st] = state(code, kc, st, dem)
    out = S.khg_root / "pipeline_status.csv"
    cols = ["khg", "name", "dem"] + [s for s in S["steps"]]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows.values())
    short = {"done": "x", "to do": ".", "": ""}
    head = [s[:8] for s in S["steps"]]
    print(f"{'KHG':<16}{'DEM':<9}" + "".join(f"{h:<9}" for h in head))
    for r in rows.values():
        print(f"{r['khg']:<16}{r['dem']:<9}" + "".join(f"{(short.get(r.get(s, ''), '-') if not str(r.get(s, '')).startswith('n/a') else '-'):<9}" for s in S["steps"]))
    print(f"\nx done, . to do, - does not apply (reason in {out})")
    return out


def cmd_plan(a) -> None:
    for code, kc, st, dem in units(a):
        c = Ctx(S, kc, dem)
        why = STEPS[st].applies(c)
        if why or (STEPS[st].done(c) and not a.force):
            continue
        try:
            cmds = STEPS[st].commands(c)
        except SystemExit as e:
            print(f"# {code} {st} {dem or ''}: blocked: {e}")
            continue
        for env, argv, cwd in cmds:
            print(f"# {code} {st} {dem or ''}\ncd {cwd} && {S.python(env)} {' '.join(argv)}")


def cmd_run(a) -> None:
    failed: set = set()                     # (code, dem) and (code, None) whose later steps are skipped
    rid = provenance.record(S)              # code, packages, data and settings of this run: $REPEAT_KHG/pipeline_provenance/<rid>.json
    print(f"provenance {rid}", flush=True)
    for code, kc, st, dem in units(a):
        c = Ctx(S, kc, dem)
        if (code, None) in failed or (code, dem) in failed:
            continue
        if STEPS[st].applies(c):
            continue
        if STEPS[st].done(c) and not a.force:
            continue
        log = c.kf / "logs" / f"pipeline_{st}{'_' + dem if dem else ''}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        t0, status = time.time(), "done"
        print(f"=== {code} {st} {dem or ''}", flush=True)
        try:
            cmds = STEPS[st].commands(c)
            with open(log, "a", encoding="utf-8") as fh:
                for env, argv, cwd in cmds:
                    fh.write(f"\n# {datetime.datetime.now().isoformat(timespec='seconds')}  provenance {rid}  cd {cwd} && {S.python(env)} {' '.join(argv)}\n")
                    fh.flush()
                    r = subprocess.run([S.python(env), *argv], cwd=cwd, stdout=fh, stderr=subprocess.STDOUT, env=os.environ.copy())
                    if r.returncode != 0:
                        raise RuntimeError(f"exit {r.returncode}; see {log}")
            if not STEPS[st].done(c):
                raise RuntimeError(f"finished but its output is missing; see {log}")
        except (Exception, SystemExit) as e:   # noqa: BLE001
            if STEPS[st].optional:                 # recorded, and the chain goes on without it
                status = f"not available: {e}"
                note = STEPS[st].note(c)
                note.parent.mkdir(parents=True, exist_ok=True)
                tail = log.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-3:] if log.exists() else []
                note.write_text(f"{st} not available ({datetime.date.today()}): {e}\n" + "\n".join(tail) + "\n", encoding="utf-8")
            else:
                status = f"failed: {e}"
                failed.add((code, dem if STEPS[st].per_dem else None))
        print(f"    {status} ({time.time() - t0:.0f} s)", flush=True)
        log_run({"time": datetime.datetime.now().isoformat(timespec="seconds"), "khg": code, "step": st, "dem": dem or "",
                 "status": status, "seconds": round(time.time() - t0, 1), "log": str(log), "provenance": rid})
    cmd_status(argparse.Namespace(khg=a.khg, steps=None, dem=None))


RUN_FIELDS = ["time", "khg", "step", "dem", "status", "seconds", "log", "provenance"]


def log_run(row: dict) -> None:
    """Append one step to $REPEAT_KHG/pipeline_runs.csv as soon as it ends (a killed batch keeps its record); an older file without
    the provenance column is rewritten with it."""
    runlog = S.khg_root / "pipeline_runs.csv"
    if runlog.exists():
        with open(runlog, encoding="utf-8") as fh:
            head = fh.readline().strip().split(",")
        if head != RUN_FIELDS:
            old = list(csv.DictReader(open(runlog, encoding="utf-8")))
            with open(runlog, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=RUN_FIELDS, extrasaction="ignore")
                w.writeheader()
                w.writerows(old)
    new = not runlog.exists()
    with open(runlog, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=RUN_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def cmd_compare(a) -> Path:
    """The results of every KHG and DEM side by side, read from the run reports (nothing recomputed)."""
    import json
    rows = []
    for code in codes(a):
        kc = khgconf.load(S, code)
        for dem in S["dems"]["variants"]:
            c = Ctx(S, kc, dem)
            rep = c.sd("05_pump") / "run_report.json"
            if not rep.is_file():
                continue
            r = json.loads(rep.read_text(encoding="utf-8"))
            c7, iv, bd, bal = r.get("counts", {}).get("7", {}), r.get("interventions") or {}, r.get("budget") or {}, r.get("sekat_balance") or {}
            held, deficit = iv.get("held_m3_selected"), iv.get("deficit_m3_selected")
            rows.append({"khg": code, "name": kc["khg"]["name"], "dem": dem, "dem_product": kc["dems"][dem].get("product", ""),
                         "subkhg_units": iv.get("units"), "sekat_head_rule": c7.get("head_rule"), "sekat_kept": c7.get("proposed"),
                         "rise_share_kept": bal.get("share_kept"), "existing_sekat_on_canals": (c7.get("existing") or 0) - (c7.get("unsnapped") or 0),
                         "water_held_m3": round(held) if held is not None else None, "deficit_m3": round(deficit) if deficit else None,
                         "held_pct_of_deficit": round(100 * held / deficit, 1) if held is not None and deficit else None,
                         **{f"iv_{k}": v for k, v in (iv.get("counts") or {}).items()},
                         "budget_low_bn": round(bd["total_low_idr"] / 1e9, 1) if bd.get("total_low_idr") is not None else None,
                         "budget_bn": round(bd["total_idr"] / 1e9, 1) if bd.get("total_idr") is not None else None,
                         "budget_high_bn": round(bd["total_high_idr"] / 1e9, 1) if bd.get("total_high_idr") is not None else None,
                         "warnings": len(r.get("warnings", []))})
    out = S.khg_root / "pipeline_compare.csv"
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['khg']:<16}{r['dem']:<9} units {r['subkhg_units']!s:<4} sekat {r['sekat_kept']!s:>4}/{r['sekat_head_rule']!s:<5} "
              f"held {r['held_pct_of_deficit']!s:>5} % of deficit   budget {r['budget_bn']!s:>7} bn Rp")
    print(f"\nwrote {out}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("setup")
    p.add_argument("--clone", action="store_true", help="git clone the missing repositories, at the commits of env/repos.lock.txt")
    p.add_argument("--lock", action="store_true", help="write env/<env>.lock.txt from the installed packages and env/repos.lock.txt from the repository commits")
    p = sub.add_parser("data")
    p.add_argument("--write", action="store_true", help="write sites/data_manifest.csv (default: check the data folder against it)")
    p = sub.add_parser("init")
    p.add_argument("--khg", nargs="*")
    p.add_argument("--overwrite", action="store_true")
    for name in ("status", "plan", "run"):
        p = sub.add_parser(name)
        p.add_argument("--khg", nargs="*")
        p.add_argument("--steps", nargs="*", choices=list(STEPS))
        p.add_argument("--dem", nargs="*", choices=list(S["dems"]["variants"]))
        p.add_argument("--force", action="store_true")
    p = sub.add_parser("compare")
    p.add_argument("--khg", nargs="*")
    a = ap.parse_args()
    {"data": cmd_data, "compare": cmd_compare, "setup": cmd_setup, "init": cmd_init, "status": cmd_status, "plan": cmd_plan, "run": cmd_run}[a.cmd](a)


if __name__ == "__main__":
    main()
