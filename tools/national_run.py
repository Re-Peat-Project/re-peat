"""National batch run: many KHG at once, each in its own container (or process), resumable, with retries and a status table.

    python tools/national_run.py --config docker/batch.toml                        # every KHG of the registry
    python tools/national_run.py --config docker/batch.toml --khg 14.08.04 16.02.01
    python tools/national_run.py --config docker/batch.toml --island "PULAU PAPUA" --run-class A B1
    python tools/national_run.py --config docker/batch.toml --dry-run              # print the commands, run nothing
    python tools/national_run.py --config docker/batch.toml --status               # the table of the last batch

Each KHG is one job: `tools/khg_pipeline.py run --khg <code>` (all steps, the DEMs of pipeline.yaml dems.default), inside the
repeat-chain image (`mode = "docker"`, the server) or with the local interpreters (`mode = "native"`). Jobs run `workers` at a
time, largest KHG first by default (the long ones start early, so the batch ends sooner). A job that fails is retried up to
`retries` times; the chain itself skips the steps a KHG has already finished, so a retry or a rerun of the batch resumes where it
stopped. Before any job starts, `config validate` checks the selected KHG; KHG with problems are left out and listed.

Records, in <khg_root>/_batch/<batch>/:
  status.csv      one row per KHG: status (done, failed, skipped, running, queued), attempts, exit code, minutes, log
  <code>.log      the job's output (all attempts)
A file named STOP in that folder stops new jobs from starting; running jobs finish. `--batch <name>` reuses a batch: KHG already
done are skipped (`--rerun` runs them again).

Only the standard library is used (the server's host Python needs nothing installed); settings come from a TOML file
(docker/batch.example.toml).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import shlex
import subprocess
import sys
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

HUB = Path(__file__).resolve().parents[1]
AVAIL = HUB / "sites" / "khg_availability.csv"
FIELDS = ["code", "name", "island", "area_ha", "run_class", "status", "attempts", "exit_code", "minutes", "started", "finished", "log"]


def load_cfg(path: Path) -> dict:
    cfg = tomllib.loads(path.read_text(encoding="utf-8"))
    cfg.setdefault("mode", "docker")
    cfg.setdefault("workers", 2)
    cfg.setdefault("retries", 1)
    cfg.setdefault("order", "large")
    cfg.setdefault("image", "repeat-chain")
    cfg.setdefault("memory", "")
    cfg.setdefault("cpus", "")
    cfg.setdefault("env", {})
    cfg.setdefault("mounts", {})
    cfg.setdefault("extra_args", [])
    return cfg


def khg_table() -> list[dict]:
    """KHG of sites/khg_availability.csv: code, name, island, area, run class."""
    with open(AVAIL, encoding="utf-8") as f:
        return [{"code": r["code"], "name": r.get("name", ""), "island": r.get("island", ""),
                 "area_ha": float(r.get("area_ha") or 0), "run_class": (r.get("run_class") or "").split(":")[0]} for r in csv.DictReader(f)]


def select(rows: list[dict], a) -> list[dict]:
    if a.khg:
        want = set(a.khg)
        rows = [r for r in rows if r["code"] in want]
        missing = want - {r["code"] for r in rows}
        if missing:
            sys.exit(f"not in {AVAIL.name}: {', '.join(sorted(missing))}")
    if a.island:
        rows = [r for r in rows if r["island"] in set(a.island)]
    if a.run_class:
        rows = [r for r in rows if r["run_class"] in set(a.run_class)]
    if a.limit:
        rows = rows[: a.limit]
    return rows


def job_command(cfg: dict, code: str, steps: list[str] | None, chain_args: list[str] | None = None, name: str | None = None) -> list[str]:
    """The command of one KHG job (chain_args: another khg_pipeline.py command instead of `run`)."""
    run = chain_args or (["run", "--khg", code] + (["--steps", *steps] if steps else []) + list(cfg["extra_args"]))
    if cfg["mode"] == "native":
        return [cfg.get("python", sys.executable), str(HUB / "tools" / "khg_pipeline.py"), *run]
    if cfg["mode"] == "fake":                       # scheduler test: sleep, then exit with the code listed for the KHG (default 0)
        rc = int(cfg.get("fake_exit", {}).get(code, 0))
        return [sys.executable, "-c", f"import time,sys; print('fake job {code}'); time.sleep({float(cfg.get('fake_seconds', 1))}); sys.exit({rc})"]
    cmd = ["docker", "run", "--rm", "--name", name or f"repeat-{code.replace('.', '-')}"]
    if cfg["memory"]:
        cmd += ["--memory", str(cfg["memory"])]
    if cfg["cpus"]:
        cmd += ["--cpus", str(cfg["cpus"])]
    for host, inside in cfg["mounts"].items():
        cmd += ["-v", f"{host}:{inside}"]
    for k, v in cfg["env"].items():
        cmd += ["-e", f"{k}={v}" if v is not None else k]       # a bare name passes the host's value (e.g. TANAHAIR_LINK)
    return cmd + [cfg["image"], *run]


def validate(cfg: dict, codes: list[str]) -> set[str]:
    """KHG whose settings fail `config validate` (empty when the check cannot run: then every job reports its own problems)."""
    if cfg["mode"] == "fake" or not codes:
        return set()
    cmd = job_command(cfg, codes[0], None, chain_args=["config", "validate", "--khg", *codes], name="repeat-validate")
    r = subprocess.run(cmd, capture_output=True, text=True)
    bad = set()
    for line in r.stdout.splitlines():
        head = line.split(":", 1)[0].split("/", 1)[0].split(" ", 1)[0]
        code = head.split("_", 1)[0]
        if code in codes and not line.startswith("note") and ": note: " not in line:
            bad.add(code)
            print(f"  config: {line}")
    if r.returncode not in (0, 1):
        print(f"config validate could not run (exit {r.returncode}); jobs start anyway:\n{r.stderr[-800:]}")
    return bad


class Status:
    def __init__(self, path: Path, rows: list[dict]):
        self.path, self.lock = path, Lock()
        old = {}
        if path.exists():
            with open(path, encoding="utf-8") as f:
                old = {r["code"]: r for r in csv.DictReader(f)}
        self.rows = {}
        for r in rows:
            o = old.get(r["code"], {})
            self.rows[r["code"]] = {**{k: "" for k in FIELDS}, **{k: r[k] for k in ("code", "name", "island", "area_ha", "run_class")},
                                    **{k: o[k] for k in ("status", "attempts", "exit_code", "minutes", "started", "finished", "log") if o.get(k)}}
            if self.rows[r["code"]]["status"] in ("", "running", "queued"):
                self.rows[r["code"]]["status"] = "queued"

    def set(self, code: str, **kw):
        with self.lock:
            self.rows[code].update({k: str(v) for k, v in kw.items()})
            tmp = self.path.with_suffix(".tmp")
            with open(tmp, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS)
                w.writeheader()
                w.writerows(self.rows.values())
            os.replace(tmp, self.path)

    def summary(self) -> str:
        from collections import Counter
        c = Counter(r["status"] for r in self.rows.values())
        return ", ".join(f"{k} {v}" for k, v in sorted(c.items()))


def run_job(cfg: dict, code: str, folder: Path, st: Status, steps, stop: Path) -> str:
    log = folder / f"{code}.log"
    tries = int(st.rows[code]["attempts"] or 0)
    for attempt in range(tries + 1, tries + 2 + int(cfg["retries"])):
        if stop.exists():
            st.set(code, status="queued")
            return "stopped"
        t0 = time.time()
        st.set(code, status="running", attempts=attempt, started=dt.datetime.now().isoformat(timespec="seconds"), log=str(log))
        cmd = job_command(cfg, code, steps)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(f"\n# {dt.datetime.now().isoformat(timespec='seconds')} attempt {attempt}: {shlex.join(cmd)}\n")
            fh.flush()
            rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT).returncode
        mins = round((time.time() - t0) / 60, 1)
        if rc == 0:
            st.set(code, status="done", exit_code=0, minutes=mins, finished=dt.datetime.now().isoformat(timespec="seconds"))
            return "done"
        st.set(code, status="failed", exit_code=rc, minutes=mins, finished=dt.datetime.now().isoformat(timespec="seconds"))
    return "failed"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--batch", help="batch name (default: today's date and time); reuse one to resume it")
    ap.add_argument("--khg", nargs="*")
    ap.add_argument("--island", nargs="*", help='e.g. "PULAU SUMATERA" "PULAU PAPUA"')
    ap.add_argument("--run-class", nargs="*", help="A, B1, B2, C (sites/khg_availability.csv)")
    ap.add_argument("--steps", nargs="*", help="only these steps (default all)")
    ap.add_argument("--limit", type=int, help="the first N selected KHG (after ordering)")
    ap.add_argument("--workers", type=int)
    ap.add_argument("--rerun", action="store_true", help="run KHG already done in this batch again")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true", help="print the status table of --batch (default: the latest) and exit")
    a = ap.parse_args()
    cfg = load_cfg(a.config)
    if a.workers:
        cfg["workers"] = a.workers
    root = Path(cfg.get("khg_root") or os.environ.get("REPEAT_KHG") or HUB.parent / "_khg") / "_batch"
    if a.status:
        b = root / a.batch if a.batch else max(root.iterdir(), key=lambda p: p.stat().st_mtime)
        with open(b / "status.csv", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            print(f"{r['code']:<16} {r['status']:<8} attempts {r['attempts'] or 0:<2} {r['minutes'] or '':>6} min  {r['name'][:40]}")
        from collections import Counter
        print(dict(Counter(r["status"] for r in rows)))
        return
    rows = khg_table()
    rows.sort(key=lambda r: r["area_ha"], reverse=cfg["order"] == "large")
    rows = select(rows, a)
    if not rows:
        sys.exit("no KHG selected")
    if a.dry_run:
        for r in rows:
            print(shlex.join(job_command(cfg, r["code"], a.steps)))
        print(f"{len(rows)} job(s), {cfg['workers']} at a time ({cfg['mode']})")
        return
    folder = root / (a.batch or dt.datetime.now().strftime("%Y%m%d_%H%M"))
    folder.mkdir(parents=True, exist_ok=True)
    st = Status(folder / "status.csv", rows)
    bad = validate(cfg, [r["code"] for r in rows])
    for code in bad:
        st.set(code, status="skipped", log="config validate: see the console output")
    todo = [r["code"] for r in rows if st.rows[r["code"]]["status"] not in ("skipped",) and
            (a.rerun or st.rows[r["code"]]["status"] != "done")]
    for code in todo:
        st.set(code, status="queued")
    stop = folder / "STOP"
    print(f"batch {folder}: {len(todo)} job(s), {cfg['workers']} at a time ({cfg['mode']}); stop new jobs: create {stop}", flush=True)
    with ThreadPoolExecutor(max_workers=int(cfg["workers"])) as ex:
        futs = {ex.submit(run_job, cfg, code, folder, st, a.steps, stop): code for code in todo}
        for f in as_completed(futs):
            print(f"{dt.datetime.now():%H:%M} {futs[f]:<16} {f.result():<8} [{st.summary()}]", flush=True)
    print(f"finished: {st.summary()}  ({folder / 'status.csv'})")
    sys.exit(0 if all(st.rows[c]["status"] == "done" for c in todo) else 1)


if __name__ == "__main__":
    main()
