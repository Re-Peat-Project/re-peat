"""KHG comparison tables of the RE-PEAT project report (chapter 10), read from the per-KHG work folders and the national profile.

Registered with the build through REGISTRY (merged into project_report_figures.REGISTRY by project_report.py).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[2]
KHG = WORKSPACE / "_khg"
NAT = WORKSPACE / "re-peat/reports/national_profile/operational/profile.csv"
DEMS = {"lidar": "LiDAR", "deltadtm": "DeltaDTM", "demnas": "DEMNAS"}
CLASS_HIGH = "tinggi"
CLASS_EN = {"tinggi": "high", "sedang": "medium", "rendah": "low"}


def short(name: str) -> str:
    return " ".join(str(name).replace("KHG ", "").replace("Sungai ", "").split())


def folders() -> list[Path]:
    return sorted(p for p in KHG.iterdir() if p.is_dir() and (p / "00_inputs").exists())


def code(folder: Path) -> str:
    return folder.name.split("_")[0]


def chain_done(f: Path) -> list[str]:
    """DEM variants whose chain ran to the end: an interventions report and layouts exist (read from the outputs, since
    the chain's status file is rewritten for the KHG of each run only)."""
    return [d for d in DEMS if (f / f"05_pump/{d}/report.html").is_file() and list((f / f"05_pump/{d}/layouts").glob("layout_*.png"))]


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def khg_readiness() -> pd.DataFrame:
    """Data and chain status per KHG work folder: national profile (rank, peat, canals, structures, SiTMAT stations),
    the data recap (LiDAR and modelled peat-depth coverage of the KHG polygon) and the chain outputs in each folder."""
    prof = pd.read_csv(NAT).set_index("khg_id")
    recap = pd.read_csv(WORKSPACE / "re-peat/sites/khg_data_recap.csv")
    recap["key"] = recap.khg.map(lambda s: " ".join(str(s).split()).lower())
    dem_inputs = pd.read_csv(WORKSPACE / "re-peat/sites/khg_dem_inputs.csv")
    rows = []
    for f in folders():
        c = code(f)
        p = prof.loc[f"KHG.{c}"] if f"KHG.{c}" in prof.index else None
        key = " ".join(str(p["nama"]).split()).lower() if p is not None else ""
        r = recap[recap.key == key]

        def cover(theme, tag=None):
            if r.empty:                              # not a selected KHG (Kampar-Gaung): no recap row
                return "not in recap"
            x = r[(r.theme == theme) & ((r.tag == tag) if tag else True)]
            return f"{x.coverage_pct.max():.0f}" if len(x) and x.coverage_pct.notna().any() else "none"

        def lidar():                                 # recap measures cover over the KHG polygon; the DEM inputs register only
            if not r.empty:                          # inside the clipped window (overstates partial LiDAR), so it is the fallback
                return cover("lidar_dtm", "LiDAR")
            x = dem_inputs[(dem_inputs.folder == f.name) & (dem_inputs["product"].str.startswith("lidar"))]
            return f"{x.cover_pct.max():.0f}" if len(x) else "none"
        done = [DEMS[d] for d in chain_done(f)]
        rank = "" if p is None or pd.isna(p["peringkat"]) else f"{int(p['peringkat'])} ({CLASS_EN.get(str(p['kelas']).split(':')[-1].strip(), p['kelas'])})"
        rows.append({
            "KHG": short(p["nama"]) if p is not None else f.name,
            "Province": p["province"] if p is not None else "",
            "National rank (class)": rank,
            "Peat (km²)": f"{p['peat_km2']:,.0f}" if p is not None else "",
            "LiDAR cover (%)": lidar(),
            "Peat depth model cover (%)": cover("peat_depth", "model"),
            "Canals (km)": f"{p['canal_km']:,.0f}" if p is not None and p["canal_km"] > 0 else "not mapped",
            "Existing structures": f"{p['n_infra_ada']:,.0f}" if p is not None and pd.notna(p["n_infra_ada"]) else "",
            "SiTMAT stations": f"{p['n_tma_stations']:.0f}" if p is not None and pd.notna(p["n_tma_stations"]) else "0",
            "Full chain": ", ".join(done) if done else "inputs only",
        })
    return pd.DataFrame(rows).sort_values("National rank (class)", key=lambda s: s.str.split(" ").str[0].replace("", "9999").astype(int))


def _completed() -> pd.DataFrame:
    """Numeric rows, one per completed KHG and DEM: units (delineation report), KHG deficit and station count
    (neraca_khg.csv), high-need units and blocks (04_prioritisation/<dem>), blocks kept and central budget
    (05_pump/<dem>/run_report.json)."""
    rows = []
    nat = pd.read_csv(NAT).set_index("khg_id")
    for f in folders():
        done = chain_done(f)
        if not done:
            continue
        dfc = f / "03_neraca/runs/deficit/neraca_khg.csv"
        d = pd.read_csv(dfc).iloc[0] if dfc.exists() else None
        name = short(nat.loc[f"KHG.{code(f)}", "nama"])
        for dem, label in DEMS.items():
            if dem not in done:
                continue
            dl = read_json(f / f"02_delineation/{dem}/delineation_report.json")
            pr = f / f"04_prioritisation/{dem}"
            kelas = pd.read_csv(pr / "ringkasan_kelas.csv") if (pr / "ringkasan_kelas.csv").exists() else None
            sek = pd.read_csv(pr / "kebutuhan_sekat.csv") if (pr / "kebutuhan_sekat.csv").exists() else None
            pu = read_json(f / f"05_pump/{dem}/run_report.json")
            hi = kelas[kelas.kelas.str.contains(CLASS_HIGH)] if kelas is not None else None
            sb = pu.get("sekat_balance") if pu else None
            rows.append({
                "KHG": name, "DEM": label,
                "units": dl[-1]["n_subkhg"] if dl else None,
                "stations": int(d.n_stations) if d is not None else 0,
                "deficit_mm": d.deficit_mm if d is not None else None,
                "deficit_m3": d.deficit_m3 if d is not None else None,
                "hi_n": int(hi.unit.sum()) if hi is not None and len(hi) else None,
                "hi_km2": hi.luas_km2.sum() if hi is not None and len(hi) else None,
                "need": sek.n_sekat_perlu.sum() if sek is not None else None,
                "existing": sek.n_sekat_ada.sum() if sek is not None else None,
                "proposed": sb["head_rule"] if sb else None,
                "kept": sb["kept"] if sb else None,
                "budget": pu["budget"]["total_idr"] / 1e9 if pu and pu.get("budget") else None,
            })
    return pd.DataFrame(rows)


def _fmt(x, nd=0, dash="-"):
    return dash if x is None or pd.isna(x) else f"{x:,.{nd}f}"


def _completed_table(d: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "KHG": d.KHG, "DEM": d.DEM,
        "Sub-KHG": d.units.map(_fmt),
        "Deficit 2026 (mm)": [("no stations" if st == 0 else _fmt(v)) for st, v in zip(d.stations, d.deficit_mm)],
        "Deficit (million m³)": [("-" if st == 0 else _fmt(v / 1e6)) for st, v in zip(d.stations, d.deficit_m3)],
        "High-need units (n, km²)": [f"{n}, {_fmt(a)}" if pd.notna(n) else "-" for n, a in zip(d.hi_n, d.hi_km2)],
        "Blocks needed (ranking)": d.need.map(_fmt),
        "Blocks existing": d.existing.map(_fmt),
        "Blocks proposed, kept": [f"{_fmt(a)}, {_fmt(b)}" if pd.notna(a) else "-" for a, b in zip(d.proposed, d.kept)],
        "Budget, central (billion Rp)": d.budget.map(_fmt),
    })
    return out.reset_index(drop=True)


def khg_completed() -> pd.DataFrame:
    """One row per completed KHG and DEM (all 33 analyses); the report prints it as two tables, below."""
    return _completed_table(_completed())


def khg_completed_lidar() -> pd.DataFrame:
    """The KHG analysed on LiDAR, DeltaDTM and DEMNAS (15 analyses)."""
    d = _completed()
    return _completed_table(d[d.KHG.isin(d[d.DEM == "LiDAR"].KHG)])


def khg_completed_open() -> pd.DataFrame:
    """The KHG analysed on corrected DeltaDTM and DEMNAS only (18 analyses)."""
    d = _completed()
    return _completed_table(d[~d.KHG.isin(d[d.DEM == "LiDAR"].KHG)])


def summary_key_figures() -> pd.DataFrame:
    """One row per KHG on the DeltaDTM variant (the only one that exists for all 14 KHG), for the executive summary.
    The range column spans every elevation model the KHG was analysed on."""
    d = _completed()
    rows = []
    for k, g in d.groupby("KHG", sort=False):
        x = g[g.DEM == "DeltaDTM"].iloc[0]
        rng = f"{_fmt(g.need.min())} to {_fmt(g.need.max())}"
        rows.append({
            "KHG": k,
            "Elevation models (n)": len(g),
            "Sub-KHG": _fmt(x.units),
            "Deficit 2026 (mm; stations)": "no stations" if x.stations == 0 else f"{_fmt(x.deficit_mm)}; {x.stations}",
            "High-need units (n, km²)": f"{x.hi_n}, {_fmt(x.hi_km2)}",
            "Blocks needed (ranking)": _fmt(x.need),
            "Blocks needed, range across models": rng,
            "Blocks proposed, kept": f"{_fmt(x.proposed)}, {_fmt(x.kept)}",
            "Budget, central (billion Rp)": _fmt(x.budget),
        })
    return pd.DataFrame(rows)


REGISTRY = {"khg_readiness": khg_readiness, "khg_completed": khg_completed,
            "khg_completed_lidar": khg_completed_lidar, "khg_completed_open": khg_completed_open,
            "summary_key_figures": summary_key_figures}
