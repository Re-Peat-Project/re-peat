"""Per-KHG results chapter of the RE-PEAT project report (chapter 10): figures and tables for one KHG across the three
DEM variants, read from that KHG's work folder.

Placeholder ids take the KHG code after a colon, e.g. {{figure: khg_units_maps:16.02.01 | caption}}; REGISTRY maps the
part before the colon to a function of the code. A function raises NotAvailable when the KHG's outputs for it do not
exist yet; the build then prints a short note in place of the figure or table. Where some DEM variants have run and
others not, the figure or table shows the ones that exist and marks the others "not run".

    python re-peat/tools/project_report_khg.py init            # write chapters/khg/NN_<folder>.md (never overwrites)
    python re-peat/tools/project_report_khg.py numbers <code>  # every number the tables hold, labelled, for the writers
    python re-peat/tools/project_report_khg.py figures <code>  # make every figure of one KHG (check by eye)
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import project_report_figures as F  # noqa: E402  (sets the report's matplotlib style)

plt = F.plt
WORKSPACE = F.WORKSPACE
SITES = WORKSPACE / "re-peat/sites"
CHAPTERS = WORKSPACE / "re-peat/reports/project_report/chapters/khg"
CACHE = F.OUT / "_cache_khg"
DEMS = F.DEMS
LABEL = F.DEM_LABEL
NOT_RUN = "not run"


class NotAvailable(Exception):
    """The outputs this figure or table needs have not been produced for the KHG yet (message says which step)."""


# --- locating outputs --------------------------------------------------------------------------------------------------
def folder(code: str) -> Path:
    hit = sorted(F.KHG.glob(f"{code}_*"))
    if not hit:
        raise NotAvailable("no work folder for this KHG")
    return hit[0]


def khg_yaml(code: str) -> dict:
    import yaml
    p = SITES / folder(code).name / "khg.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}


def resolve(p: str | None) -> Path | None:
    if not p:
        return None
    s = str(p).replace("${REPEAT_KHG}", str(F.KHG)).replace("${REPEAT_DATA}", str(WORKSPACE / "_data"))
    s = s.replace("${REPEAT_HUB}", str(WORKSPACE / "re-peat")).replace("${WORKSPACE}", str(WORKSPACE))
    return Path(s)


def skip_reason(code: str, dem: str) -> str | None:
    """Why a variant does not run, in client words (None when it runs or is planned)."""
    v = (khg_yaml(code).get("dems") or {}).get(dem) or {}
    r = v.get("skip")
    if not r:
        return None
    return "no LiDAR covers this KHG" if "no lidar" in str(r).lower() else "not used for this KHG"


def pump_json(code: str, dem: str):
    return F.read_json(folder(code) / "05_pump" / dem / "run_report.json")


def dtm_path(code: str, dem: str) -> Path | None:
    """The terrain the chain used for a variant: the interventions run's DTM, else the delineation config's, else the
    order of the pipeline (LiDAR clip of khg.yaml; 01_dem/processed/<dem>/dtm_smooth.tif, then benchmark/04_processed)."""
    import yaml
    f = folder(code)
    cands = []
    r = pump_json(code, dem)
    if r:
        cands.append(Path(r["config"]["inputs"]["dtm"]["path"]))
    dy = SITES / f.name / dem / "delineate.yaml"
    if dy.exists():
        d = yaml.safe_load(dy.read_text(encoding="utf-8")) or {}
        cands.append(resolve((d.get("rasters") or {}).get("dtm")))
    if dem == "lidar":
        cands.append(resolve(((khg_yaml(code).get("dems") or {}).get("lidar") or {}).get("clip")))
    else:
        cands += [f / "01_dem/processed" / dem / "dtm_smooth.tif", f / "01_dem/benchmark/04_processed" / dem / "dtm_smooth.tif"]
    return next((p for p in cands if p is not None and p.is_file()), None)


def dtm_paths_disagree(code: str, dem: str) -> bool:
    """True when the delineation and the interventions run of a variant read different terrain files."""
    import yaml
    r = pump_json(code, dem)
    dy = SITES / folder(code).name / dem / "delineate.yaml"
    if not r or not dy.exists():
        return False
    d = yaml.safe_load(dy.read_text(encoding="utf-8")) or {}
    a = resolve((d.get("rasters") or {}).get("dtm"))
    return a is not None and Path(r["config"]["inputs"]["dtm"]["path"]).resolve() != a.resolve()


STEP_FILE = {"delineation": "02_delineation/{dem}/subkhg_units.gpkg",
             "neraca": "03_neraca/{dem}/runs/balance/neraca_balance_unit.csv",
             "prioritisation": "04_prioritisation/{dem}/unit_prioritas.gpkg",
             "interventions": "05_pump/{dem}/run_report.json"}


def done(code: str, step: str) -> list[str]:
    """DEM variants whose output of one step exists."""
    f = folder(code)
    if step == "dem":
        return [d for d in DEMS if dtm_path(code, d) is not None]
    return [d for d in DEMS if (f / STEP_FILE[step].format(dem=d)).is_file()]


def missing_label(code: str, dem: str) -> str:
    return skip_reason(code, dem) or NOT_RUN


def full_cover(code: str, dem: str) -> bool:
    """False for a LiDAR covering under 90% of the KHG polygon (its units and results cover only that part)."""
    if dem != "lidar":
        return True
    c = F.polygon_cover_of(code, "lidar")
    return not (F.isnum(c) and c < 90)


def name(code: str) -> str:
    r = F.registry()
    x = r[r.code == code]
    return F.short(x.name.iloc[0]).replace(" - ", "-") if len(x) else code


def khg_geom(code: str):
    import geopandas as gpd
    g = gpd.read_file(folder(code) / "00_inputs/khg.gpkg")
    return g.to_crs(F.utm(g))


# --- raster helpers ----------------------------------------------------------------------------------------------------
def display_grid(code: str, px: int = 900, pad_m: float = 1500):
    """A UTM grid over the KHG bounds (plus pad) of about px cells along the longer side: for display only."""
    from rasterio.transform import from_origin
    k = khg_geom(code)
    x0, y0, x1, y1 = k.total_bounds
    x0, y0, x1, y1 = x0 - pad_m, y0 - pad_m, x1 + pad_m, y1 + pad_m
    res = max(x1 - x0, y1 - y0) / px
    w, h = int(np.ceil((x1 - x0) / res)), int(np.ceil((y1 - y0) / res))
    return from_origin(x0, y1, res, res), (h, w), k.crs, k


def warp_to(src: Path, transform, shape, crs, resampling="average") -> np.ndarray:
    import rasterio
    from rasterio.warp import Resampling, reproject
    out = np.full(shape, np.nan, dtype="float32")
    with rasterio.open(src) as ds:
        nod = ds.nodata
        reproject(rasterio.band(ds, 1), out, src_nodata=nod, dst_nodata=np.nan, dst_transform=transform, dst_crs=crs,
                  resampling=getattr(Resampling, resampling))
    out[(out < -100) | (out > 9000)] = np.nan
    return out


def inside_mask(k, transform, shape) -> np.ndarray:
    from rasterio.features import geometry_mask
    return geometry_mask(k.geometry, shape, transform, invert=True)


def frame(ax, k, crs, ylabel=True, xlabel=True):
    F.km_axes(ax, F.crs_name(crs), ylabel=ylabel)
    if not xlabel:
        ax.set_xlabel("")
    if not ylabel:
        ax.set_ylabel(""); ax.tick_params(labelleft=False)
    b = k.total_bounds
    ax.set_xlim(b[0] - 1000, b[2] + 1000); ax.set_ylim(b[1] - 1000, b[3] + 1000)
    ax.tick_params(labelsize=7)
    ax.xaxis.label.set_size(7.5); ax.yaxis.label.set_size(7.5)


def north(ax, k) -> None:
    """North arrow in the corner of the map where the KHG polygon takes the least room."""
    from shapely.geometry import box
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    w, h = (x1 - x0) * 0.16, (y1 - y0) * 0.24
    g = k.union_all()
    corners = {(0.9, 0.95): box(x1 - w, y1 - h, x1, y1), (0.1, 0.95): box(x0, y1 - h, x0 + w, y1),
               (0.9, 0.27): box(x1 - w, y0, x1, y0 + h), (0.1, 0.27): box(x0, y0, x0 + w, y0 + h)}
    (x, y), _ = min(corners.items(), key=lambda c: c[1].intersection(g).area)
    # sizes in points, so the arrow reads the same on short and tall panels: tip 4 pt inside the frame, tail 12 pt
    # below it, "N" under the tail; in a lower corner the whole sign sits 22 pt above the bottom edge
    tip = (x, 1.0) if y > 0.5 else (x, 0.0)
    dy = -4 if y > 0.5 else 26
    from matplotlib.transforms import offset_copy
    t0 = offset_copy(ax.transAxes, fig=ax.figure, x=0, y=dy, units="points")
    t1 = offset_copy(ax.transAxes, fig=ax.figure, x=0, y=dy - 12, units="points")
    t2 = offset_copy(ax.transAxes, fig=ax.figure, x=0, y=dy - 19, units="points")
    ax.annotate("", xy=tip, xycoords=t0, xytext=tip, textcoords=t1,
                arrowprops=dict(arrowstyle="-|>", color=F.INK, lw=0.8, shrinkA=0, shrinkB=0))
    ax.text(*tip, "N", transform=t2, ha="center", va="center", fontsize=8, color=F.INK)


def tidy(row) -> None:
    """Only the first map of a row keeps its northing label and tick labels (map layers can set labels after framing)."""
    for i, ax in enumerate(row):
        if i:
            ax.set_ylabel(""); ax.tick_params(labelleft=False)


def bottom_legend(fig, handles, ncol: int) -> None:
    """Legend just under the drawn map row (equal-aspect maps leave free space in the grid; the saved figure is cropped)."""
    fig.subplots_adjust(wspace=0.08)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    y0 = min(ax.get_tightbbox(r).y0 for ax in fig.axes if ax.get_visible())
    y = fig.transFigure.inverted().transform((0, y0))[1]
    fig.legend(handles=handles, loc="upper center", ncol=ncol, fontsize=7.5, bbox_to_anchor=(0.5, y - 0.01))


def panel_size(k, ncol: int, extra_h: float = 0.0) -> tuple[float, float]:
    """Figure size for ncol equal map panels across the text width, following the KHG's aspect."""
    x0, y0, x1, y1 = k.total_bounds
    asp = min(1.6, max(0.55, (y1 - y0) / (x1 - x0)))
    return F.W, F.W / ncol * asp + extra_h


def empty_panel(ax, text):
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=8, color=F.MUTED, transform=ax.transAxes, wrap=True)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)


SEQ = ["#f4f8fd", F.BLUE_RAMP[250], F.BLUE_RAMP[450], F.BLUE_RAMP[650], "#0d366b"]
DIV = ["#104281", "#2a78d6", "#9ec5f4", "#f0efec", "#f2b8b0", "#e34948", "#a82b2b"]


# --- facts ------------------------------------------------------------------------------------------------------------
def profile_row(code: str):
    p = pd.read_csv(F.PROFILE).set_index("khg_id")
    return p.loc[f"KHG.{code}"] if f"KHG.{code}" in p.index else None


def khg_facts(code: str) -> pd.DataFrame:
    """National profile (province, area, peat, rank and class, canals by class, SiTMAT stations), the KHG polygon
    (00_inputs/khg.gpkg), built canal blocks (00_inputs/blocks.gpkg inside the polygon), LiDAR cover of the polygon and
    the chain outputs per DEM."""
    import geopandas as gpd
    f = folder(code)
    p = profile_row(code)
    k = gpd.read_file(f / "00_inputs/khg.gpkg")
    area = k.to_crs(6933).area.sum() / 1e6
    rows = [("Province", p["province"] if p is not None else "-"),
            ("Area of the KHG polygon (km²)", F.fmt(area))]
    if p is not None:
        rank = (f"{int(p['peringkat'])} of {int(pd.read_csv(F.PROFILE).peringkat.notna().sum())} ({F.focus_en(p['kelas'])} priority)"
                if F.isnum(p["peringkat"]) else "not ranked")
        rows += [("Peat area (km²)", F.fmt(p["peat_km2"])),
                 ("National rank (class)", rank),
                 ("Canals, primary / secondary / tertiary (km)",
                  " / ".join(F.fmt(p[c]) for c in ("canal_km_primary", "canal_km_secondary", "canal_km_tertiary"))
                  if F.isnum(p["canal_km"]) and p["canal_km"] > 0 else "not mapped"),
                 ("Existing water-management structures, all types (n)", F.fmt(p["n_infra_ada"]) if F.isnum(p["n_infra_ada"]) else "-"),
                 ("SiTMAT water-table stations (n)", F.fmt(p["n_tma_stations"]) if F.isnum(p["n_tma_stations"]) else "0")]
    b = f / "00_inputs/blocks.gpkg"
    if b.exists():
        bl = gpd.read_file(b)
        n = int(bl.to_crs(k.crs).within(k.union_all()).sum()) if len(bl) else 0
        rows.append(("Realised canal blocks inside the KHG (n)", f"{n:,}"))
    lid = skip_reason(code, "lidar")
    c = F.polygon_cover_of(code, "lidar") if not lid else np.nan
    rows.append(("LiDAR cover of the KHG (%)", lid if lid else F.fmt(c, 0) if F.isnum(c) else "none"))
    steps = {"Elevation model ready": "dem", "Sub-KHG units": "delineation", "Water balance": "neraca",
             "Priority of sub-KHG": "prioritisation", "Canal blocks and costs": "interventions"}
    for lab, st in steps.items():
        have = done(code, st)
        rows.append((f"{lab}, by elevation model", ", ".join(LABEL[d] for d in have) if have else NOT_RUN))
    dfc = f / "03_neraca/runs/deficit/neraca_khg.csv"
    rows.append(("Dry-season deficit from stations", "computed" if dfc.exists() else "not computed"))
    out = pd.DataFrame(rows, columns=["Item", "Value"])
    out.attrs["note"] = ("Rank among ranked KHG with default weights, proposed for agreement with KLH and the World Bank. "
                         "Canals: mapped canal network. Structures and realised canal blocks: national layer of existing water-management structures (all types, and the canal blocks recorded as realised).")
    return out


# --- DEMs ------------------------------------------------------------------------------------------------------------
def dem_rasters(code: str) -> dict:
    out = {d: dtm_path(code, d) for d in DEMS}
    return {d: p for d, p in out.items() if p is not None}


def khg_dem_maps(code: str):
    """Chain DTM of each variant (dtm_path), warped to one UTM display grid by cell averaging; differences to LiDAR
    (or DeltaDTM minus DEMNAS when there is no LiDAR) and their distribution inside the KHG."""
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    ras = dem_rasters(code)
    if not ras:
        raise NotAvailable("elevation model correction")
    tr, shape, crs, k = display_grid(code)
    ins = inside_mask(k, tr, shape)
    z = {d: np.where(ins, warp_to(p, tr, shape, crs), np.nan) for d, p in ras.items()}
    vals = np.concatenate([a[np.isfinite(a)] for a in z.values()])
    lo, hi = np.percentile(vals, [2, 98])
    ext = (tr.c, tr.c + tr.a * shape[1], tr.f + tr.e * shape[0], tr.f)
    seq = LinearSegmentedColormap.from_list("seq", SEQ)
    div = LinearSegmentedColormap.from_list("div", DIV)
    ref = "lidar" if "lidar" in z else None
    diffs = [(d, z[d] - z[ref]) for d in ("deltadtm", "demnas") if ref and d in z]
    if not ref and {"deltadtm", "demnas"} <= set(z):
        diffs = [("deltadtm", z["deltadtm"] - z["demnas"])]
    w, h = panel_size(k, 3, 0.0)
    fig, axes = plt.subplots(2 if diffs else 1, 3, figsize=(w, (h + 0.55) * (2 if diffs else 1) + 0.3), squeeze=False)
    for i, d in enumerate(DEMS):
        ax = axes[0, i]
        if d not in z:
            empty_panel(ax, f"{LABEL[d]}\n{missing_label(code, d)}"); continue
        im = ax.imshow(z[d], extent=ext, cmap=seq, vmin=lo, vmax=hi, interpolation="nearest")
        k.boundary.plot(ax=ax, color=F.INK, linewidth=0.7)
        frame(ax, k, crs, ylabel=True, xlabel=False)
        ax.set_title(F.dem_label(code, d), fontsize=8.5)
    tidy([axes[0, i] for i, d in enumerate(DEMS) if d in z])
    north(axes[0, -1], k)
    cb = fig.colorbar(im, ax=list(axes[0]), orientation="vertical", fraction=0.025, pad=0.02, extend="both")
    cb.set_label("Ground elevation (m)", fontsize=7.5); cb.ax.tick_params(labelsize=7)
    if diffs:
        allv = np.concatenate([a[np.isfinite(a)] for _, a in diffs])
        lim = float(np.ceil(np.percentile(np.abs(allv), 90))) if allv.size else 1.0
        lim = max(lim, 0.5)
        for j, (d, a) in enumerate(diffs):
            ax = axes[1, j]
            im2 = ax.imshow(a, extent=ext, cmap=div, norm=TwoSlopeNorm(0, -lim, lim), interpolation="nearest")
            k.boundary.plot(ax=ax, color=F.INK, linewidth=0.7)
            frame(ax, k, crs, ylabel=(j == 0))
            ax.set_title(f"{LABEL[d]} minus {LABEL[ref] if ref else 'DEMNAS'}", fontsize=8.5)
        for j in range(len(diffs), 2):
            axes[1, j].set_visible(False)
        drawn = list(axes[1, :len(diffs)])
        tidy(drawn)
        fig.canvas.draw()                        # colour bar under the drawn difference maps and their labels
        r = fig.canvas.get_renderer()
        inv = fig.transFigure.inverted()
        y0 = min(inv.transform((0, a.get_tightbbox(r).y0))[1] for a in drawn)
        x0 = inv.transform((drawn[0].get_window_extent(r).x0, 0))[0]
        x1 = inv.transform((drawn[-1].get_window_extent(r).x1, 0))[0]
        hgt = 0.1 / fig.get_size_inches()[1]
        cax = fig.add_axes([x0, y0 - 0.02 - hgt, x1 - x0, hgt])
        cax.grid(False)
        cb2 = fig.colorbar(im2, cax=cax, orientation="horizontal", extend="both")
        cb2.set_label("Difference (m); positive: higher than the reference", fontsize=7.5); cb2.ax.tick_params(labelsize=7)
        ax = axes[1, 2]
        bins = np.linspace(-lim, lim, 61)
        for d, a in diffs:
            v = a[np.isfinite(a)]
            hst, e = np.histogram(v, bins=bins, density=True)
            ax.plot((e[:-1] + e[1:]) / 2, hst * 100, color=F.DEM_COLOR[d], lw=1.4,
                    label=LABEL[d] if ref else f"{LABEL[d]} minus DEMNAS")
        ax.axvline(0, color=F.INK, lw=0.6)
        ax.set_xlabel("Difference (m)", fontsize=7.5); ax.set_ylabel("% of cells per m", fontsize=7.5)
        ax.tick_params(labelsize=7); ax.set_ylim(0, None)
        ax.yaxis.tick_right(); ax.yaxis.set_label_position("right")
        ax.spines["right"].set_visible(True); ax.spines["left"].set_visible(False)
        ax.legend(fontsize=7, loc="best", frameon=True, facecolor="white", edgecolor="none", framealpha=0.9)
        ax.set_title("Distribution inside the KHG", fontsize=8.5)
    return F.save(fig, f"khg_dem_maps_{code}")


def _stats_cache_key(code: str, ras: dict) -> str:
    parts = [code] + [f"{d}:{p.stat().st_size}:{int(p.stat().st_mtime)}" for d, p in sorted(ras.items())]
    return "|".join(parts)


def dem_stats_raw(code: str) -> pd.DataFrame:
    """Relief and difference statistics on one analysis grid inside the KHG polygon: the LiDAR's own grid where LiDAR
    exists, else the DeltaDTM's (others warped onto it by cell averaging; the native rasters are kept). Cached by file
    size and modification time."""
    import rasterio
    from rasterio.windows import from_bounds
    ras = dem_rasters(code)
    if not ras:
        raise NotAvailable("elevation model correction")
    CACHE.mkdir(parents=True, exist_ok=True)
    cf = CACHE / "dem_stats.csv"
    key = _stats_cache_key(code, ras)
    cache = pd.read_csv(cf) if cf.exists() else pd.DataFrame(columns=["key"])
    hit = cache[cache.key == key]
    if len(hit):
        return hit.drop(columns="key").reset_index(drop=True)
    base = "lidar" if "lidar" in ras else ("deltadtm" if "deltadtm" in ras else next(iter(ras)))
    k = khg_geom(code)
    with rasterio.open(ras[base]) as ds:
        kb = k.to_crs(ds.crs).total_bounds
        win = from_bounds(*kb, transform=ds.transform).round_offsets().round_lengths()
        win = win.intersection(rasterio.windows.Window(0, 0, ds.width, ds.height))
        tr, shape, crs = ds.window_transform(win), (int(win.height), int(win.width)), ds.crs
        grid_res = abs(ds.res[0])
    kk = k.to_crs(crs)
    ins = inside_mask(kk, tr, shape)
    n_in = ins.sum()
    z = {}
    for d, p in ras.items():
        a = warp_to(p, tr, shape, crs, "average" if d != base else "nearest")
        z[d] = np.where(ins, a, np.nan)
    rows = []
    for d, p in ras.items():
        a = z[d][np.isfinite(z[d])]
        with rasterio.open(p) as ds:
            res = abs(ds.res[0]) * (111320 if ds.crs.is_geographic else 1)
        row = {"dem": d, "res_m": res, "relief_p5": np.percentile(a, 5) if a.size else np.nan,
               "relief_p95": np.percentile(a, 95) if a.size else np.nan, "grid_m": grid_res, "grid": base,
               "valid_share": a.size / n_in if n_in else np.nan}
        if "lidar" in z and d != "lidar":
            df = (z[d] - z["lidar"])
            df = df[np.isfinite(df)]
            if df.size:
                med = float(np.median(df))
                row.update({"diff_median": med, "diff_nmad": float(1.4826 * np.median(np.abs(df - med))), "diff_n": int(df.size)})
        rows.append(row)
    out = pd.DataFrame(rows)
    keep = cache[~cache.key.astype(str).str.startswith(code + "|")] if len(cache) else cache
    pd.concat([keep, out.assign(key=key)], ignore_index=True).to_csv(cf, index=False)
    return out


def dem_diff_summary(code: str) -> pd.DataFrame:
    """Numbers behind the difference panels of khg_dem_maps, from the same display grid: for each difference drawn (to
    LiDAR, or DeltaDTM minus DEMNAS without LiDAR) its 5th, 50th and 95th percentile inside the KHG, the share of cells more
    than 2 m above and more than 2 m below the reference, the histogram peak (bin centre of the distribution panel) and
    the 2nd and 98th percentile of the elevation of each model (the colour-scale limits of the elevation panels)."""
    ras = dem_rasters(code)
    if not ras:
        raise NotAvailable("elevation model correction")
    tr, shape, crs, k = display_grid(code)
    ins = inside_mask(k, tr, shape)
    z = {d: np.where(ins, warp_to(p, tr, shape, crs), np.nan) for d, p in ras.items()}
    ref = "lidar" if "lidar" in z else None
    diffs = [(f"{LABEL[d]} minus {LABEL[ref]}", z[d] - z[ref]) for d in ("deltadtm", "demnas") if ref and d in z]
    if not ref and {"deltadtm", "demnas"} <= set(z):
        diffs = [("DeltaDTM minus DEMNAS", z["deltadtm"] - z["demnas"])]
    allv = np.concatenate([a[np.isfinite(a)] for _, a in diffs]) if diffs else np.array([])
    lim = max(float(np.ceil(np.percentile(np.abs(allv), 90))) if allv.size else 1.0, 0.5)
    rows = []
    for d, a in z.items():
        v = a[np.isfinite(a)]
        rows.append({"Quantity": f"{LABEL[d]} elevation", "p5": np.percentile(v, 5), "p50": np.percentile(v, 50),
                     "p95": np.percentile(v, 95), "Max": v.max(), "Min": v.min()})
    for lab, a in diffs:
        v = a[np.isfinite(a)]
        hst, e = np.histogram(v, bins=np.linspace(-lim, lim, 61), density=True)
        rows.append({"Quantity": lab, "p5": np.percentile(v, 5), "p50": np.percentile(v, 50), "p95": np.percentile(v, 95),
                     "Max": v.max(), "Min": v.min(), "Share above +2 m (%)": 100 * (v > 2).mean(),
                     "Share below -2 m (%)": 100 * (v < -2).mean(), "Histogram peak (m)": (e[int(np.argmax(hst))] + e[int(np.argmax(hst)) + 1]) / 2,
                     "Share within 2 m (%)": 100 * (np.abs(v) <= 2).mean()})
    out = pd.DataFrame(rows)
    out.attrs["note"] = (f"p5, p50, p95: percentiles over the KHG cells of the {900}-pixel display grid of the DEM figure (m). Differences "
                         f"are model minus reference; histogram bins {2 * lim / 60:.2f} m wide over +-{lim:.0f} m.")
    return out


SOURCE = {"lidar": "Airborne LiDAR terrain model (KLHK), as delivered",
          "deltadtm": "DeltaDTM v1.1 (global coastal terrain model), after the DEM correction",
          "demnas": "DEMNAS (BIG national surface model), after the DEM correction"}


def khg_dem_stats(code: str) -> pd.DataFrame:
    """dem_stats_raw per DEM; cover of the KHG polygon by the DEM clip (polygon_cover_of)."""
    s = dem_stats_raw(code).set_index("dem")
    rows = []
    for d in DEMS:
        if d not in s.index:
            rows.append({"Elevation model": LABEL[d], "Source": missing_label(code, d)}); continue
        r = s.loc[d]
        c = F.polygon_cover_of(code, d)
        rows.append({"Elevation model": LABEL[d], "Source": SOURCE[d], "Resolution (m)": F.fmt(r.res_m, 0),
                     "Cover of the KHG (%)": F.fmt(c, 0),
                     "Relief, 5th-95th percentile (m)": f"{r.relief_p5:.1f} to {r.relief_p95:.1f}",
                     "Difference to LiDAR, median (m)": F.fmt(r.get("diff_median"), 2) if d != "lidar" else "",
                     "Difference to LiDAR, NMAD (m)": F.fmt(r.get("diff_nmad"), 2) if d != "lidar" else ""})
    out = pd.DataFrame(rows).fillna("")
    if not out["Difference to LiDAR, median (m)"].astype(str).str.strip().isin(["", "-"]).eq(False).any():
        out = out.drop(columns=["Difference to LiDAR, median (m)", "Difference to LiDAR, NMAD (m)"])
    g = s.iloc[0]
    out.attrs["note"] = (f"Statistics over the KHG polygon on a common {g.grid_m:.0f} m grid (the {LABEL[g.grid]} grid; finer "
                         "models averaged onto it). NMAD: normalised median absolute deviation, a spread measure robust to "
                         "outliers. Where LiDAR covers only part of the KHG, differences are over that part.")
    return out


# --- sub-KHG units -----------------------------------------------------------------------------------------------------
def units(code: str, dem: str):
    import geopandas as gpd
    p = folder(code) / "02_delineation" / dem / "subkhg_units.gpkg"
    return gpd.read_file(p) if p.exists() else None


def khg_units_maps(code: str):
    """02_delineation/<dem>/subkhg_units.gpkg (unit_id) per DEM; mapped primary and secondary canals and rivers from
    00_inputs; KHG outline."""
    import geopandas as gpd
    have = done(code, "delineation")
    if not have:
        raise NotAvailable("sub-KHG delineation")
    k = khg_geom(code)
    crs = k.crs
    f = folder(code)
    cf = (khg_yaml(code).get("canals") or {}).get("class_field", "KET_KANAL")
    can = gpd.read_file(f / "00_inputs/canals.gpkg").to_crs(crs) if (f / "00_inputs/canals.gpkg").exists() else None
    if can is not None and cf in can:
        can = can[can[cf].isin(["Kanal Primer", "Kanal Sekunder"])]
        can = can.clip(k.buffer(1000))
    w, h = panel_size(k, 3, 1.1)
    fig, axes = plt.subplots(1, 3, figsize=(w, h), sharex=True, sharey=True)
    for i, (ax, d) in enumerate(zip(axes, DEMS)):
        if d not in have:
            frame(ax, k, crs, ylabel=(i == 0)); k.boundary.plot(ax=ax, color=F.GRID, linewidth=0.7)
            ax.text(0.5, 0.5, f"{missing_label(code, d)}", transform=ax.transAxes, ha="center", va="center", fontsize=8, color=F.MUTED)
            ax.set_title(LABEL[d], fontsize=8.5); continue
        u = units(code, d).to_crs(crs)
        u.plot(ax=ax, facecolor="#eef3f8", edgecolor="none", zorder=1)
        if can is not None and len(can):
            can.plot(ax=ax, color="#a3a29d", linewidth=0.3, zorder=2)
        u.boundary.plot(ax=ax, color=F.DEM_COLOR[d], linewidth=0.9, zorder=3)
        k.boundary.plot(ax=ax, color=F.INK, linewidth=0.8, zorder=4)
        frame(ax, k, crs, ylabel=(i == 0))
        ax.set_title(f"{F.dem_label(code, d)}: {len(u)} units", fontsize=8.5)
    north(axes[-1], k)
    from matplotlib.lines import Line2D
    bottom_legend(fig, [Line2D([], [], color=F.INK, lw=0.8, label="KHG boundary"),
                        Line2D([], [], color="#7a7975", lw=0.9, label="Sub-KHG boundary (colour by elevation model)"),
                        Line2D([], [], color="#a3a29d", lw=0.5, label="Primary and secondary canals")], 3)
    tidy(axes)
    return F.save(fig, f"khg_units_maps_{code}")


def ari_from_table(n: np.ndarray) -> float:
    """Adjusted Rand index from a contingency table of cell counts (here hectares)."""
    c2 = lambda x: x * (x - 1) / 2  # noqa: E731
    s_ij = c2(n).sum(); a = c2(n.sum(1)).sum(); b = c2(n.sum(0)).sum(); t = c2(n.sum())
    exp = a * b / t
    mx = (a + b) / 2
    return float((s_ij - exp) / (mx - exp)) if mx != exp else np.nan


PAIRS = [("lidar", "deltadtm"), ("lidar", "demnas"), ("deltadtm", "demnas")]


def overlay_pair(a, b):
    import geopandas as gpd
    x = gpd.overlay(a, b, how="intersection", keep_geom_type=True)
    x["km2"] = x.geometry.area / 1e6
    return x[x.km2 > 0]


def khg_units_agreement(code: str) -> pd.DataFrame:
    """02_delineation/<dem>/subkhg_units.gpkg per DEM in an equal-area projection (EPSG:6933): count and area of units;
    for each pair of DEMs, the intersection of the two unit sets gives the adjusted Rand index (in hectares) and the
    share of area in the best-matching unit."""
    have = done(code, "delineation")
    if not have:
        raise NotAvailable("sub-KHG delineation")
    lay = {d: units(code, d).to_crs(6933) for d in have}
    rows = []
    for d in DEMS:
        if d not in lay:
            rows.append({"Elevation model or pair": LABEL[d], "Units (n)": missing_label(code, d)}); continue
        a = lay[d].geometry.area / 1e6
        rows.append({"Elevation model or pair": F.dem_label(code, d), "Units (n)": str(len(a)),
                     "Unit area, median (km²)": F.fmt(a.median()), "Unit area, range (km²)": f"{a.min():,.0f} to {a.max():,.0f}",
                     "Units total (km²)": F.fmt(a.sum())})
    for a, b in PAIRS:
        if a not in lay or b not in lay:
            continue
        x = overlay_pair(lay[a][["unit_id", "geometry"]], lay[b][["unit_id", "geometry"]])
        t = x.pivot_table(index="unit_id_1", columns="unit_id_2", values="km2", aggfunc="sum", fill_value=0).to_numpy() * 100
        best = (t.max(1).sum() / t.sum() + t.max(0).sum() / t.sum()) / 2
        rows.append({"Elevation model or pair": f"{LABEL[a]} and {LABEL[b]}", "Overlap (km²)": F.fmt(x.km2.sum()),
                     "Area in best-matching unit (%)": F.fmt(best, 0, True), "Adjusted Rand index": F.fmt(ari_from_table(t), 2)})
    out = pd.DataFrame(rows).fillna("")
    out.attrs["note"] = ("Pairs are compared over the area both cover. Best-matching unit: share of the overlap that lies in "
                         "the unit of the other model it overlaps most, averaged over both directions. Adjusted Rand index: "
                         "1 for identical partitions, about 0 for chance agreement; computed on 1 ha cells.")
    return out


# --- water balance -----------------------------------------------------------------------------------------------------
def balance_units(code: str, dem: str) -> pd.DataFrame | None:
    d = folder(code) / "03_neraca" / dem
    p = d / "runs/balance/neraca_balance_unit.csv"
    if not p.exists():
        return None
    u = pd.read_csv(p)
    lc = d / "inputs/units_landcover.csv"
    if lc.exists():
        u = u.merge(pd.read_csv(lc)[["unit_id", "area_km2"]], on="unit_id", how="left")
    else:
        u["area_km2"] = 1.0
    return u


def order_ok(u: pd.DataFrame) -> bool | None:
    v = u.balance_stable_ok.dropna()
    return bool(v.iloc[0]) if len(v) else None


def khg_water(code: str) -> pd.DataFrame:
    """03_neraca/runs/deficit/neraca_khg.csv (deficit_mm and its band, deficit_m3, deficit_months, n_stations, period) and
    03_neraca/<dem>/runs/balance/neraca_balance_unit.csv (u_wb_mean, u_deficit_months, wb_mean_wapor, balance_stable_ok)
    with inputs/units_landcover.csv (area_km2)."""
    f = folder(code)
    have = done(code, "neraca")
    dfc = f / "03_neraca/runs/deficit/neraca_khg.csv"
    if not have and not dfc.exists():
        raise NotAvailable("water balance")
    rows = []
    if dfc.exists():
        n = pd.read_csv(dfc).iloc[0]
        rows.append({"Quantity": f"Dry-season deficit from {int(n.n_stations)} stations, {pd.Timestamp(n.period_start):%d %b} to "
                                 f"{pd.Timestamp(n.period_end):%d %b %Y} (mm)",
                     "All models": f"{n.deficit_mm:,.0f} ({n.deficit_mm_low:,.0f} to {n.deficit_mm_high:,.0f})"})
        rows.append({"Quantity": "Deficit volume over the KHG (million m³)", "All models": F.fmt(n.deficit_m3 / 1e6)})
        rows.append({"Quantity": "Months in deficit in that window (n)", "All models": F.fmt(n.deficit_months)})
    else:
        p = profile_row(code)
        ns = p["n_tma_stations"] if p is not None else np.nan
        rows.append({"Quantity": "Dry-season deficit from stations",
                     "All models": "not computed: no water-table station inside the KHG" if not F.isnum(ns) or ns == 0 else "not computed yet"})
    per = {}
    for d in DEMS:
        u = balance_units(code, d)
        if u is None:
            per[d] = None; continue
        w = u.area_km2.fillna(0)
        per[d] = {"Sub-KHG units (n)": f"{len(u)}",
                  "Climatic balance, MOD16, area mean (mm/month)": F.fmt(np.average(u.u_wb_mean, weights=w), 1),
                  "Climatic balance, unit range (mm/month)": f"{u.u_wb_mean.min():.1f} to {u.u_wb_mean.max():.1f}",
                  "Climatic balance, WaPOR, area mean (mm/month)": F.fmt(np.average(u.wb_mean_wapor, weights=w), 1) if u.wb_mean_wapor.notna().all() else "-",
                  "Deficit months per year, area mean": F.fmt(np.average(u.u_deficit_months, weights=w), 2),
                  "Order of units usable (ET products agree)": {True: "yes", False: "no", None: "-"}[order_ok(u)]}
    keys = next((list(v) for v in per.values() if v), [])
    out = pd.DataFrame(rows)
    for d in DEMS:
        out[F.dem_label(code, d)] = ""
    for kq in keys:
        r = {"Quantity": kq, "All models": ""}
        for d in DEMS:
            r[F.dem_label(code, d)] = per[d][kq] if per[d] else missing_label(code, d)
        out = pd.concat([out, pd.DataFrame([r])], ignore_index=True)
    out.attrs["note"] = ("The station deficit uses water-table stations and reanalysis rain and evaporation (band: specific "
                         "yield 0.10 to 0.20) and does not depend on the elevation model. The climatic balance is CHIRPS rain "
                         "minus evapotranspiration, 2018-2025, per sub-KHG of each model.")
    return out


def monthly_climatology(code: str, dem: str):
    """(area-weighted KHG mean, per-unit) balance per calendar month, MOD16, 2018-2025; None when not run."""
    d = folder(code) / "03_neraca" / dem
    p = d / "runs/balance/neraca_balance_monthly.csv"
    if not p.exists():
        return None
    m = pd.read_csv(p)
    m = m[(m.et_source == "mod16") & m.month.between("2018-01", "2025-12")]
    lc = d / "inputs/units_landcover.csv"
    a = pd.read_csv(lc)[["unit_id", "area_km2"]] if lc.exists() else pd.DataFrame({"unit_id": m.unit_id.unique(), "area_km2": 1.0})
    m = m.merge(a, on="unit_id")
    m["cal"] = m.month.str[5:7].astype(int)
    k = m.groupby("month").apply(lambda g: np.average(g.WB_mm, weights=g.area_km2), include_groups=False)
    unit = m.groupby(["unit_id", "cal"]).WB_mm.mean().unstack()
    return k.groupby(k.index.str[5:7].astype(int)).mean(), unit


def khg_water_fig(code: str):
    """03_neraca/<dem>/runs/balance/neraca_balance_monthly.csv (month, unit_id, WB_mm, et_source mod16), 2018-2025,
    area-weighted over units, mean per calendar month, with the range over the units; neraca_balance_unit.csv
    (u_wb_mean, balance_stable_ok) per unit."""
    have = done(code, "neraca")
    if not have:
        raise NotAvailable("water balance")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.W, F.W * 0.36), gridspec_kw={"width_ratios": [1.6, 1]})
    cl = {d: monthly_climatology(code, d) for d in have}
    cl = {d: v for d, v in cl.items() if v is not None}
    if not cl:
        raise NotAvailable("water balance")
    units_all = pd.concat([u for _, u in cl.values()])
    a1.fill_between(range(1, 13), units_all.min().values, units_all.max().values, color=F.GRID, alpha=0.8, lw=0,
                    label="Range of sub-KHG units")
    means = pd.DataFrame({d: v[0] for d, v in cl.items()})
    if len(means.columns) > 1 and float((means.max(axis=1) - means.min(axis=1)).max()) < 1.0:
        a1.plot(means.index, means.iloc[:, 0].values, color=F.INK, marker="o", ms=3,
                label="KHG mean, all models (within 1 mm)")
    else:
        for d in means:
            a1.plot(means.index, means[d].values, color=F.DEM_COLOR[d], marker="o", ms=3, ls="--" if d == "demnas" else "-",
                    label=f"KHG mean, {LABEL[d]}")
    a1.axhline(0, color=F.INK, lw=0.7)
    a1.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    a1.set_ylabel("Climatic balance (mm/month)", fontsize=8)
    a1.set_title("Mean year, 2018-2025", fontsize=8.5, loc="left")
    a1.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)
    a1.tick_params(labelsize=7)
    labels = []
    for j, d in enumerate(DEMS):
        u = balance_units(code, d)
        if u is None:
            labels.append(f"{LABEL[d]}\n({missing_label(code, d)})"); continue
        ok = order_ok(u)
        a2.scatter(u.u_wb_mean, np.full(len(u), j), s=16, color=F.DEM_COLOR[d], alpha=0.75, linewidth=0.4, edgecolor="white")
        labels.append(f"{LABEL[d]}\norder {'usable' if ok else 'not usable'}")
    a2.set_yticks(range(3), labels, fontsize=7)
    a2.set_ylim(2.6, -0.6)
    a2.set_xlabel("Unit mean balance (mm/month)", fontsize=8)
    a2.set_title("Sub-KHG units", fontsize=8.5, loc="left")
    a2.tick_params(axis="x", labelsize=7); a2.grid(axis="y", visible=False)
    fig.tight_layout()
    return F.save(fig, f"khg_water_fig_{code}")


# --- priority --------------------------------------------------------------------------------------------------------
def prio(code: str, dem: str):
    import geopandas as gpd
    p = F.prio_dir(code, dem) / "unit_prioritas.gpkg"
    return gpd.read_file(p) if p.exists() else None


def khg_priority_maps(code: str):
    """04_prioritisation/<dem>/unit_prioritas.gpkg (kelas, peringkat) per DEM; KHG outline."""
    from matplotlib.patches import Patch
    have = done(code, "prioritisation")
    if not have:
        raise NotAvailable("sub-KHG prioritisation")
    k = khg_geom(code)
    crs = k.crs
    w, h = panel_size(k, 3, 1.1)
    fig, axes = plt.subplots(1, 3, figsize=(w, h), sharex=True, sharey=True)
    for i, (ax, d) in enumerate(zip(axes, DEMS)):
        frame(ax, k, crs, ylabel=(i == 0))
        if d not in have:
            k.boundary.plot(ax=ax, color=F.GRID, linewidth=0.7)
            ax.text(0.5, 0.5, missing_label(code, d), transform=ax.transAxes, ha="center", va="center", fontsize=8, color=F.MUTED)
            ax.set_title(LABEL[d], fontsize=8.5); continue
        g = prio(code, d).to_crs(crs)
        g["need"] = g.kelas.map(F.need_en)
        g.plot(ax=ax, color=g.need.map(F.NEED_COLOR).fillna(F.NEUTRAL), edgecolor="white", linewidth=0.4)
        k.boundary.plot(ax=ax, color=F.INK, linewidth=0.8)
        for r in g[g.peringkat <= 3].itertuples():
            p = r.geometry.representative_point()
            ax.text(p.x, p.y, f"{int(r.peringkat)}", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
        ax.set_title(F.dem_label(code, d), fontsize=8.5)
    north(axes[-1], k)
    bottom_legend(fig, [Patch(color=F.NEED_COLOR[x], label=f"{x} need") for x in ("high", "medium", "low")]
                  + [Patch(color="none", label="1-3: top-ranked units")], 4)
    tidy(axes)
    return F.save(fig, f"khg_priority_maps_{code}")


def high_need_km2(code: str, dem: str):
    p = F.prio_dir(code, dem) / "ringkasan_kelas.csv"
    if not p.exists():
        return np.nan, np.nan
    k = pd.read_csv(p)
    k = k[k.kelas.map(F.need_en) == "high"]
    return float(k.luas_km2.sum()), int(k.unit.sum())


def khg_priority_agreement(code: str) -> pd.DataFrame:
    """04_prioritisation/<dem>/unit_prioritas.gpkg (kelas, skor_risiko) overlaid per pair of DEMs in EPSG:6933: area in
    the same need class, high-need area kept high, area-weighted Spearman of the scores; ringkasan_kelas.csv for the
    high-need area of each DEM."""
    have = done(code, "prioritisation")
    if not have:
        raise NotAvailable("sub-KHG prioritisation")
    lay = {d: prio(code, d)[["kelas", "skor_risiko", "geometry"]].to_crs(6933) for d in have}
    rows = []
    for d in DEMS:
        if d not in lay:
            rows.append({"Elevation model or pair": LABEL[d], "High need (units, km²)": missing_label(code, d)}); continue
        km, n = high_need_km2(code, d)
        rows.append({"Elevation model or pair": F.dem_label(code, d), "High need (units, km²)": f"{n}, {km:,.0f}"})
    for a, b in PAIRS:
        if a not in lay or b not in lay:
            continue
        x = overlay_pair(lay[a], lay[b])
        ca, cb = x.kelas_1.map(F.need_en), x.kelas_2.map(F.need_en)
        ha = x.km2[ca == "high"].sum()
        try:
            rho = F.weighted_spearman(x.skor_risiko_1, x.skor_risiko_2, x.km2)
        except (ZeroDivisionError, FloatingPointError, ValueError):
            rho = np.nan
        rows.append({"Elevation model or pair": f"{LABEL[a]} and {LABEL[b]}", "Overlap (km²)": F.fmt(x.km2.sum()),
                     "Same need class (% of overlap)": F.fmt(x.km2[ca == cb].sum() / x.km2.sum(), 0, True),
                     "High need in first also high in second (%)": F.fmt(x.km2[(ca == "high") & (cb == "high")].sum() / ha, 0, True) if ha else "-",
                     "Spearman of scores, area-weighted": F.fmt(rho, 2)})
    out = pd.DataFrame(rows).fillna("")
    out.attrs["note"] = ("Units are matched by location, since each model has its own units. Shares are of the area both "
                         "models cover. Default weights, proposed for agreement with KLH and the World Bank.")
    return out


# --- canal blocks and pumping ----------------------------------------------------------------------------------------
def pump_gpkg(code: str, dem: str) -> Path | None:
    r = pump_json(code, dem)
    d = folder(code) / "05_pump" / dem
    if r:
        p = Path(r["config"]["run"]["output_gpkg"])
        if p.is_file():
            return p
        p = d / p.name
        if p.is_file():
            return p
    g = sorted(x for x in d.glob("*.gpkg"))
    return g[0] if g else None


def read_layer(p: Path, layer: str):
    import geopandas as gpd
    import pyogrio
    if layer not in [l for l, _ in pyogrio.list_layers(p)]:
        return None
    g = gpd.read_file(p, layer=layer)
    return g if len(g) and g.geometry.notna().any() else None


def khg_blocks_maps(code: str):
    """05_pump/<dem>/<run>.gpkg: subkhg_selected, canals_clean (canal_class), sekat_proposed (kept blocks),
    sekat_low_benefit (dropped by the 90% rule), sekat_existing_assessed (snapped); 00_inputs canals and KHG outline."""
    import geopandas as gpd
    from matplotlib.lines import Line2D
    have = done(code, "interventions")
    if not have:
        raise NotAvailable("canal blocks and pumping")
    k = khg_geom(code)
    crs = k.crs
    L = {}
    for d in have:
        p = pump_gpkg(code, d)
        L[d] = {n: (read_layer(p, n).to_crs(crs) if p and read_layer(p, n) is not None else None)
                for n in ("subkhg_selected", "canals_clean", "sekat_proposed", "sekat_low_benefit", "sekat_existing_assessed")}
    sel = [v["subkhg_selected"] for v in L.values() if v["subkhg_selected"] is not None]
    box = pd.concat(sel).total_bounds if sel else k.total_bounds
    pad = 0.06 * max(box[2] - box[0], box[3] - box[1])
    box = (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)
    f = folder(code)
    cf = (khg_yaml(code).get("canals") or {}).get("class_field", "KET_KANAL")
    can = gpd.read_file(f / "00_inputs/canals.gpkg").to_crs(crs) if (f / "00_inputs/canals.gpkg").exists() else None
    if can is not None and cf in can:
        can = can[can[cf].isin(["Kanal Primer", "Kanal Sekunder"])].cx[box[0]:box[2], box[1]:box[3]]
    asp = min(1.6, max(0.55, (box[3] - box[1]) / (box[2] - box[0])))
    fig, axes = plt.subplots(1, 3, figsize=(F.W, F.W / 3 * asp + 1.3), sharex=True, sharey=True)
    for i, (ax, d) in enumerate(zip(axes, DEMS)):
        F.km_axes(ax, F.crs_name(crs), ylabel=(i == 0))
        ax.set_xlim(box[0], box[2]); ax.set_ylim(box[1], box[3])
        ax.tick_params(labelsize=7); ax.xaxis.label.set_size(7.5); ax.yaxis.label.set_size(7.5)
        if can is not None and len(can):
            can.plot(ax=ax, color="#d4d3cf", linewidth=0.3, zorder=1)
        k.boundary.plot(ax=ax, color=F.INK, linewidth=0.8, zorder=2)
        if d not in L:
            ax.text(0.5, 0.5, missing_label(code, d), transform=ax.transAxes, ha="center", va="center", fontsize=8, color=F.MUTED)
            ax.set_title(LABEL[d], fontsize=8.5); continue
        v = L[d]
        if v["canals_clean"] is not None:
            v["canals_clean"].plot(ax=ax, color="#7a7975", linewidth=0.45, zorder=3)
        if v["subkhg_selected"] is not None:
            v["subkhg_selected"].boundary.plot(ax=ax, color=F.DEM_COLOR[d], linewidth=1.1, zorder=4)
        ex = v["sekat_existing_assessed"]
        if ex is not None:
            ex = ex[ex.snapped.astype(bool)] if "snapped" in ex else ex
            ax.scatter(ex.geometry.x, ex.geometry.y, s=6, marker="x", color=F.MUTED, linewidth=0.5, zorder=5)
        lb = v["sekat_low_benefit"]
        if lb is not None:
            ax.scatter(lb.geometry.x, lb.geometry.y, s=10, facecolor="white", edgecolor=F.DEM_COLOR[d], linewidth=0.6, zorder=6)
        kp = v["sekat_proposed"]
        if kp is not None:
            ax.scatter(kp.geometry.x, kp.geometry.y, s=11, color=F.DEM_COLOR[d], edgecolor="white", linewidth=0.3, zorder=7)
        sb = (pump_json(code, d) or {}).get("sekat_balance") or {}
        ax.set_title(f"{F.dem_label(code, d)}: {sb.get('kept', 0)} of {sb.get('head_rule', 0)} kept", fontsize=8.5)
    north(axes[-1], k)
    bottom_legend(fig, [Line2D([], [], marker="o", ls="", color=F.MUTED, mec="white", label="Proposed block, kept"),
                        Line2D([], [], marker="o", ls="", mfc="white", mec=F.MUTED, label="Proposed, low benefit (dropped)"),
                        Line2D([], [], marker="x", ls="", color=F.MUTED, label="Existing block"),
                        Line2D([], [], color="#7a7975", lw=0.6, label="Analysed canal"),
                        Line2D([], [], color=F.MUTED, lw=1.1, label="Selected sub-KHG (colour by model)")], 3)
    tidy(axes)
    return F.save(fig, f"khg_blocks_maps_{code}")


def sub_id(s: str) -> str:
    return str(s).split("_")[-1]


def blocks_needed(code: str, dem: str):
    p = F.prio_dir(code, dem) / "kebutuhan_sekat.csv"
    if not p.exists():
        return np.nan, np.nan
    s = pd.read_csv(p)
    return float(s.n_sekat_perlu.sum()), float(s.n_sekat_ada.sum())


def interventions_rows(code: str, dem: str) -> dict | None:
    r = pump_json(code, dem)
    if not r:
        return None
    sb, c7 = r.get("sekat_balance") or {}, (r.get("counts") or {}).get("7", {})
    iv, bg = r.get("interventions") or {}, r.get("budget") or {}
    pumping = (r["config"].get("pumping") or {}).get("enabled")
    pumps = sum(int(x.get("units_needed") or 0) for x in (r.get("pumps") or []))
    need, ada = blocks_needed(code, dem)
    by = bg.get("by_class") or {}
    reveg = by.get("revegetate_fire")
    return {
        "Selected sub-KHG (top 3 by priority)": ", ".join(sub_id(s) for s in r["validation"].get("selected_subkhg", [])),
        "Blocks needed by the slope rule of the ranking, whole KHG (n)": F.fmt(need),
        "Existing blocks counted by the ranking, whole KHG (n)": F.fmt(ada),
        "Existing blocks on analysed canals (n)": F.fmt(c7.get("existing", 0) - c7.get("unsnapped", 0)) if c7 else "-",
        "Blocks proposed by the head rule (n)": F.fmt(sb.get("head_rule")),
        "Blocks kept, 90% of the water-level rise (n)": F.fmt(sb.get("kept")),
        "Pump units (n)": F.fmt(pumps) if pumping else "pumping not assessed",
        "Water held by kept blocks (million m³)": F.fmt(F.scaled(iv.get("held_m3_selected"), 1e6), 2),
        "Deficit of the selected units (million m³)": F.fmt(F.scaled(iv.get("deficit_m3_selected"), 1e6), 1),
        "Budget, low / central / high (billion Rp)": " / ".join(F.fmt(F.scaled(bg.get(x), 1e9)) for x in ("total_low_idr", "total_idr", "total_high_idr")),
        "of which revegetation of burned land, central (billion Rp)": F.fmt(F.scaled(reveg, 1e9)) if reveg is not None else "-",
    }


def khg_interventions(code: str) -> pd.DataFrame:
    """05_pump/<dem>/run_report.json (validation.selected_subkhg, sekat_balance, counts['7'], pumps, config.pumping.enabled,
    interventions held/deficit, budget totals and by_class.revegetate_fire); 04_prioritisation/<dem>/kebutuhan_sekat.csv."""
    have = done(code, "interventions")
    if not have:
        raise NotAvailable("canal blocks and pumping")
    per = {d: interventions_rows(code, d) for d in DEMS}
    keys = list(next(v for v in per.values() if v))
    out = pd.DataFrame({"Quantity": keys})
    for d in DEMS:
        out[F.dem_label(code, d)] = [per[d][x] if per[d] else missing_label(code, d) for x in keys]
    out.attrs["note"] = ("Blocks, water and budget are for the three highest-ranked sub-KHG of each model, which can differ "
                         "between models. Kept: the fewest proposed blocks giving 90% of the water-level rise of all proposed "
                         "blocks. Pumping is not assessed in these results. Default weights, proposed for agreement with KLH and the "
                         "World Bank.")
    return out


# --- DEM effect --------------------------------------------------------------------------------------------------------
def effect_values(code: str) -> pd.DataFrame:
    """Headline numeric outputs per DEM (NaN where a step did not run)."""
    rec = {}
    for d in DEMS:
        v = {}
        rep = F.read_json(folder(code) / "02_delineation" / d / "delineation_report.json") if d in done(code, "delineation") else None
        if rep:
            r = rep[-1] if isinstance(rep, list) else rep
            v["Sub-KHG units (n)"] = r["n_subkhg"]
            v["Median unit area (km²)"] = r["area_km2"]["median"]
            v["Area covered by units (km²)"] = r["area_km2"]["total"]
        u = balance_units(code, d)
        if u is not None:
            v["Climatic balance, area mean (mm/month)"] = np.average(u.u_wb_mean, weights=u.area_km2.fillna(0))
        km, n = high_need_km2(code, d)
        if F.isnum(km):
            v["High-need area (km²)"] = km
            v["High-need units (n)"] = n
        need, _ = blocks_needed(code, d)
        if F.isnum(need):
            v["Blocks needed, slope rule of the ranking, whole KHG (n)"] = need
        r = pump_json(code, d) if d in done(code, "interventions") else None
        if r:
            sb, iv, bg = r.get("sekat_balance") or {}, r.get("interventions") or {}, r.get("budget") or {}
            v["Blocks proposed, head rule (n)"] = sb.get("head_rule", np.nan)
            v["Blocks kept (n)"] = sb.get("kept", np.nan)
            v["Water held by kept blocks (million m³)"] = F.scaled(iv.get("held_m3_selected"), 1e6)
            v["Budget, central (billion Rp)"] = F.scaled(bg.get("total_idr"), 1e9)
        rec[d] = v
    return pd.DataFrame(rec).reindex(columns=DEMS)


DIGITS = {"Climatic balance, area mean (mm/month)": 1, "Water held by kept blocks (million m³)": 2}


def khg_dem_effect(code: str) -> pd.DataFrame:
    """effect_values: delineation_report.json, neraca_balance_unit.csv, ringkasan_kelas.csv, kebutuhan_sekat.csv and
    run_report.json per DEM. Spread: largest over smallest value (range for the balance), over the models that cover
    the whole KHG."""
    v = effect_values(code)
    if v.dropna(how="all").empty:
        raise NotAvailable("sub-KHG delineation")
    full = [d for d in DEMS if full_cover(code, d)]
    rows = []
    for q, r in v.iterrows():
        row = {"Output": q}
        for d in DEMS:
            row[F.dem_label(code, d)] = F.fmt(r[d], DIGITS.get(q, 0)) if F.isnum(r[d]) else missing_label(code, d) if d not in done(code, "delineation") else "-"
        x = r[[d for d in full if F.isnum(r[d])]].astype(float)
        if len(x) >= 2:
            if "balance" in q:
                row["Spread"] = f"range {x.max() - x.min():.1f}"
            elif x.min() > 0:
                row["Spread"] = f"×{x.max() / x.min():.1f}"
            else:
                row["Spread"] = f"range {x.max() - x.min():,.0f}"
        else:
            row["Spread"] = "-"
        rows.append(row)
    out = pd.DataFrame(rows)
    note = ("Spread: largest value over smallest across the models (range for the balance). Blocks kept, water and budget "
            "refer to the three highest-ranked sub-KHG of each model, so they move with the choice of units as well as with "
            "the terrain.")
    if len(full) < 3 and "lidar" in done(code, "delineation"):
        note += f" The spread leaves out the LiDAR column, which covers {F.polygon_cover_of(code, 'lidar'):.0f}% of the KHG."
    out.attrs["note"] = note + " Default weights, proposed for agreement with KLH and the World Bank."
    return out


REGISTRY = {"khg_facts": khg_facts, "khg_dem_maps": khg_dem_maps, "khg_dem_stats": khg_dem_stats,
            "khg_units_maps": khg_units_maps, "khg_units_agreement": khg_units_agreement,
            "khg_water": khg_water, "khg_water_fig": khg_water_fig,
            "khg_priority_maps": khg_priority_maps, "khg_priority_agreement": khg_priority_agreement,
            "khg_blocks_maps": khg_blocks_maps, "khg_interventions": khg_interventions, "khg_dem_effect": khg_dem_effect}
TABLES = ["khg_facts", "khg_dem_stats", "khg_units_agreement", "khg_water", "khg_priority_agreement", "khg_interventions", "khg_dem_effect"]
FIGURES = ["khg_dem_maps", "khg_units_maps", "khg_water_fig", "khg_priority_maps", "khg_blocks_maps"]


# --- chapter files ---------------------------------------------------------------------------------------------------
def chapter_khg() -> list[tuple[str, str, str]]:
    """(code, full name, role) for the chapter: selected_khg.csv main rows, then reserves, then Kampar-Gaung."""
    s = pd.read_csv(SITES / "selected_khg.csv")
    r = F.registry().set_index("key")
    out = []
    for role in ("main", "reserve"):
        for _, x in s[s.role == role].iterrows():
            nm = x.khg_name_in_gpkg if isinstance(x.khg_name_in_gpkg, str) else None
            c = r.code.get(F.norm(nm), "") if nm else ""
            if c:
                out.append((c, " ".join(nm.split()), role))
    k = F.registry()
    k = k[k.code == "14.02-04-05.01"].iloc[0]
    out.append((k.code, " ".join(k["name"].split()), "earlier test site"))
    return out


def chapter_text(code: str, full: str, role: str) -> str:
    short = F.short(full).replace(" - ", "-")
    S = lambda kind, ident, cap, src: (f"{{{{{kind}: {ident}:{code} | {cap}. {src} | made by {ident} in "  # noqa: E731
                                       f"re-peat/tools/project_report_khg.py from the KHG work folder}}}}")
    P = lambda text: f"<!-- Writing prompt: {text} -->"  # noqa: E731
    parts = [
        f"## {{n}} {short} (KHG {code})",
        "",
        f"<!-- Written by the analyst of {short} ({role}). Two to four sentences under each figure or table, then the summary.",
        "Figures and tables fill in from the KHG work folder when the report is built; a step not yet run shows a short",
        "'not yet available' line. To see the numbers behind the tables: python re-peat/tools/project_report_khg.py numbers "
        f"{code}",
        "This file was written by: python re-peat/tools/project_report_khg.py init (it never overwrites). Keep prose plain,",
        "every number with its unit, and state the source of anything not in the tables. -->",
        "",
        S("table", "khg_facts", f"{short}: key facts", "Source: national KHG profile, national canal and structures layers, RE-PEAT results for this KHG"),
        "",
        P("Where the KHG lies, how much of it is peat, how it ranks nationally and why, what canal network and blocks it has, "
          "and which elevation models and steps have run."),
        "",
        "### Terrain and the three elevation models",
        "",
        S("figure", "khg_dem_maps", f"{short}: ground elevation from each elevation model on one colour scale, and their differences",
          "Source: LiDAR terrain model, DeltaDTM and DEMNAS after the DEM correction"),
        "",
        P("Describe the terrain (dome, river levees, coast) and where the models disagree, for example along rivers, "
          "plantations or forest edges, and the likely reason (canopy left in the surface, coarse resolution, datum)."),
        "",
        S("table", "khg_dem_stats", f"{short}: resolution, cover and relief of each elevation model, and its difference to LiDAR",
          "Source: LiDAR terrain model, DeltaDTM and DEMNAS after the DEM correction"),
        "",
        P("Compare relief and the median and spread of the difference to LiDAR; say whether the difference is a constant "
          "offset (datum) or local error, and what that means for the slopes the later steps use."),
        "",
        "### Sub-KHG units",
        "",
        S("figure", "khg_units_maps", f"{short}: sub-KHG units delineated on each elevation model",
          "Source: sub-KHG delineation on each elevation model, mapped canals"),
        "",
        P("How many units each model gives, how their boundaries follow canals and rivers, and where the models draw "
          "them differently and why."),
        "",
        S("table", "khg_units_agreement", f"{short}: number and size of sub-KHG units, and agreement between elevation models (area in the best-matching unit, adjusted Rand index)",
          "Source: sub-KHG delineation on each elevation model"),
        "",
        P("Say how far the unit sets agree (best-matching area, adjusted Rand index) and which pair differs most."),
        "",
        "### Water balance and deficit",
        "",
        S("table", "khg_water", f"{short}: dry-season deficit from water-table stations and climatic balance per sub-KHG",
          "Source: SiTMAT water-table stations, CHIRPS rain, MOD16 and WaPOR evapotranspiration"),
        "",
        P("State the deficit and its period, the months in deficit, and whether the order of units by balance is usable "
          "for each model; explain any model whose order test fails."),
        "",
        S("figure", "khg_water_fig", f"{short}: climatic balance through the mean year, and the balance of each sub-KHG, by elevation model",
          "Source: CHIRPS rain and MOD16 evapotranspiration, 2018-2025"),
        "",
        P("Name the dry months, and say whether the elevation model changes the balance (it enters only through the units)."),
        "",
        "### Priority of sub-KHG",
        "",
        S("figure", "khg_priority_maps", f"{short}: need for intervention per sub-KHG, by elevation model",
          "Source: sub-KHG prioritisation with default weights"),
        "",
        P("Where the high-need units are and what drives them (fire, canals, dryness), and whether the same places come out "
          "on top with every model. Mention that the weights are the defaults proposed for agreement with KLH and the World Bank."),
        "",
        S("table", "khg_priority_agreement", f"{short}: high-need area and agreement of the priority classes between elevation models",
          "Source: sub-KHG prioritisation with default weights"),
        "",
        P("Say how much area keeps its class across models and how strongly the scores agree; explain the largest difference."),
        "",
        "### Canal blocks and pumping",
        "",
        S("figure", "khg_blocks_maps", f"{short}: proposed canal blocks in the three highest-ranked sub-KHG, by elevation model",
          "Source: RE-PEAT Interventions on each elevation model, mapped canals and existing blocks"),
        "",
        P("Where the blocks go and why there (canal slope, burned land), how many are dropped as low benefit, and how the "
          "selected units and block positions change with the model."),
        "",
        S("table", "khg_interventions", f"{short}: canal blocks, water held and budget, by elevation model",
          "Source: RE-PEAT Interventions and sub-KHG prioritisation on each elevation model"),
        "",
        P("Give the blocks proposed and kept, water held against the deficit, and the central budget with its main cost item; "
          "say what drives the cost differences between models."),
        "",
        "### How the elevation model changes the result",
        "",
        S("table", "khg_dem_effect", f"{short}: headline outputs by elevation model and their spread",
          "Source: RE-PEAT results on each elevation model"),
        "",
        P("Which outputs move most with the elevation model and which barely move; for this KHG, which model you would use "
          "for decisions and why."),
        "",
        "### Summary for this KHG",
        "",
        P("Three to five sentences: the main finding for rewetting in this KHG, the recommended elevation model, the "
          "proposed blocks and budget, and what is still missing (data or steps not yet run)."),
        "",
    ]
    return "\n".join(parts)


def init() -> None:
    CHAPTERS.mkdir(parents=True, exist_ok=True)
    for i, (code, full, role) in enumerate(chapter_khg(), start=1):
        try:
            fname = f"{i:02d}_{folder(code).name}.md"
        except NotAvailable:
            print(f"skip {code}: no work folder"); continue
        p = CHAPTERS / fname
        if p.exists():
            print(f"keep {p.name}"); continue
        p.write_text(chapter_text(code, full, role), encoding="utf-8")
        print(f"wrote {p.name}")


def numbers(code: str) -> None:
    print(f"# {name(code)} (KHG {code})")
    for t in TABLES:
        print(f"\n## {t}")
        try:
            df = REGISTRY[t](code)
        except NotAvailable as e:
            print(f"  not yet available ({e})"); continue
        first = df.columns[0]
        for _, r in df.iterrows():
            for c in df.columns[1:]:
                v = r[c]
                if v is None or (isinstance(v, float) and np.isnan(v)) or str(v).strip() == "":
                    continue
                print(f"  {r[first]} | {c}: {v}")
        if df.attrs.get("note"):
            print(f"  note: {df.attrs['note']}")
    print("\n## dem_diff_summary (display-grid cells inside the KHG, as in the DEM figure)")
    try:
        df = dem_diff_summary(code)
        for _, r in df.iterrows():
            for c in df.columns[1:]:
                if not pd.isna(r[c]):
                    print(f"  {r['Quantity']} | {c}: {r[c]:.2f}")
        print(f"  note: {df.attrs['note']}")
    except NotAvailable as e:
        print(f"  not yet available ({e})")
    print("\n## Mean-year climatic balance by calendar month (KHG mean over units weighted by area, MOD16, 2018-2025, mm/month)")
    for d in DEMS:
        cl = monthly_climatology(code, d) if (folder(code) / "03_neraca" / d).is_dir() else None
        if cl is not None:
            k = cl[0]
            print(f"  {LABEL[d]} | " + ", ".join(f"{m}: {v:.0f}" for m, v in zip(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), k.values)))


def figures(code: str) -> None:
    for fid in FIGURES:
        try:
            print(fid, REGISTRY[fid](code))
        except NotAvailable as e:
            print(fid, f"not yet available ({e})")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["init", "numbers", "figures"])
    ap.add_argument("code", nargs="?")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.command == "init":
        init()
    elif not a.code:
        ap.error("give a KHG code")
    else:
        {"numbers": numbers, "figures": figures}[a.command](a.code)
