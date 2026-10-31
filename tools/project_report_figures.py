"""Figures and tables of the RE-PEAT project report, made from the output files (see project_report.py).

Each function returns a PNG path (or (path, width_cm)) for a figure, or a pandas DataFrame for a table. REGISTRY maps
the placeholder id used in the chapter Markdown to its function.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

WORKSPACE = Path(__file__).resolve().parents[2]
KHG = WORKSPACE / "_khg"
OUT = WORKSPACE / "re-peat/reports/project_report/figures"
OUT.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = "#1F2A30", "#5F6B70", "#DDE3E2"
# validated categorical order (dataviz reference palette; adjacent pairs pass CVD and normal-vision checks)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
BLUE_RAMP = {250: "#86b6ef", 450: "#2a78d6", 650: "#104281"}          # sequential / ordinal hue
NEUTRAL = "#d4d3cf"                                                      # no data, not ranked
HELD = "#a9a8a2"                                                         # cells at a held level (managed land, canals) in model maps
import project_report_style as STYLE  # noqa: E402

STYLE.register_matplotlib()
plt.rcParams.update({"font.family": STYLE.SANS, "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 200,
                     "savefig.bbox": "tight", "legend.frameon": False, "axes.titlesize": 9,
                     "axes.titleweight": "bold", "axes.titlecolor": INK, "lines.linewidth": 1.4})
W = 16 / 2.54                       # figure width in inches = text width, so 9 pt prints as 9 pt

COMPLETED = {"14.02-04-05.01": "Kampar-Gaung", "15.05-07-10.01": "Mendahara-Batanghari",
             "16.02-07.01": "Saleh-Sugihan", "16.02.01": "Sugihan-Lumpur"}
DEMS = ["lidar", "deltadtm", "demnas"]
DEM_LABEL = {"lidar": "LiDAR", "deltadtm": "DeltaDTM", "demnas": "DEMNAS"}


def folder(code: str) -> Path:
    return next(KHG.glob(f"{code}_*"))


def save(fig, name: str) -> Path:
    p = OUT / f"{name}.png"
    fig.savefig(p)
    plt.close(fig)
    return p


def norm(s) -> str:
    return " ".join(str(s).split()).lower()


def registry() -> pd.DataFrame:
    r = pd.read_csv(WORKSPACE / "re-peat/sites/khg_registry.csv")
    r["code"] = r.khg_code.str.replace("KHG.", "", regex=False)
    r["key"] = r.name.map(norm)
    return r


# --- chapter 2 --------------------------------------------------------------------------------------------------------
def selected_khg() -> pd.DataFrame:
    s = pd.read_csv(WORKSPACE / "re-peat/sites/selected_khg.csv")
    r = registry().set_index("key")
    rows = []
    for _, x in s.iterrows():
        name = x.khg_name_in_gpkg if isinstance(x.khg_name_in_gpkg, str) else None
        code = r.code.get(norm(name), "") if name else ""
        rows.append({"Province": x.province, "Role": x.role, "KHG": " ".join(name.split()) if name else f"{x.name_as_given} (unresolved)",
                     "Code": code, "Area (ha)": f"{int(x.area_ha):,}" if pd.notna(x.area_ha) else "",
                     "Full chain run": "yes" if code in COMPLETED else ""})
    k = r[r.code == "14.02-04-05.01"].iloc[0]
    rows.append({"Province": k.province, "Role": "earlier test site", "KHG": k["name"], "Code": k.code,
                 "Area (ha)": f"{int(k.area_ha_kepmen):,}", "Full chain run": "yes"})
    return pd.DataFrame(rows)


# --- shared helpers ---------------------------------------------------------------------------------------------------
import json  # noqa: E402
import re  # noqa: E402

import matplotlib.dates  # noqa: E402
import numpy as np  # noqa: E402

KHG_COLOR = dict(zip(COMPLETED, SERIES))                     # colour follows the KHG in every figure
DEM_COLOR = {"lidar": SERIES[0], "deltadtm": SERIES[1], "demnas": SERIES[2]}
NATIONAL = WORKSPACE / "re-peat/reports/national_profile"
NEED_EN = {"tinggi": "high", "sedang": "medium", "rendah": "low"}
NEED_COLOR = {"high": BLUE_RAMP[650], "medium": BLUE_RAMP[450], "low": BLUE_RAMP[250]}


def short(name) -> str:
    """KHG name without 'KHG' and 'Sungai'."""
    return " ".join(str(name).replace("KHG ", "").replace("Sungai ", "").split())


def team() -> dict:
    """Code -> role of the team's KHG (main and reserve rows of selected_khg.csv that resolve to a registry code)."""
    t = selected_khg()
    t = t[t.Role.isin(["main", "reserve"]) & (t.Code != "")]
    out = dict(zip(t.Code, t.Role))
    assert len(out) == 13, f"expected 13 team KHG, found {len(out)}"
    return out


def need_en(kelas) -> str:
    return NEED_EN.get(str(kelas).split(":")[-1].strip(), str(kelas))


def isnum(v) -> bool:
    try:
        return v is not None and np.isfinite(float(v))
    except (TypeError, ValueError):
        return False


def fmt(v, nd=0, pct=False, dash="-"):
    if not isnum(v):
        return dash
    v = float(v) * (100 if pct else 1)
    return f"{v:,.{nd}f}"


def read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else None


def km_axes(ax, crs_label: str, ylabel=True):
    """Axes in km (projected CRS), equal aspect, north up."""
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda v, _: f"{v / 1000:,.0f}")
    ax.xaxis.set_major_formatter(f); ax.yaxis.set_major_formatter(f)
    ax.set_aspect("equal"); ax.grid(False)
    ax.set_xlabel(f"Easting (km, {crs_label})")
    if ylabel:
        ax.set_ylabel("Northing (km)")
    ax.tick_params(labelsize=7.5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(True)


def north_arrow(ax, x=0.94, y=0.95):
    ax.annotate("N", xy=(x, y), xytext=(x, y - 0.1), xycoords="axes fraction", ha="center", va="center",
                fontsize=8, color=INK, arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.8))


def utm(gdf):
    return gdf.estimate_utm_crs()


def crs_name(crs) -> str:
    from pyproj import CRS
    return CRS.from_user_input(crs).name.replace("WGS 84 / ", "").replace("UTM zone ", "UTM ")


# --- chapter 3 --------------------------------------------------------------------------------------------------------
RECAP_HEAD = {"lidar_dtm": "LiDAR DTM", "modelled_dtm": "Modelled DTM", "demnas": "DEMNAS", "contour": "Contours",
              "peat_depth": "Peat depth", "canals": "Canals", "rivers": "Rivers",
              "infrastructure": "Existing structures", "canal_blocks": "Proposed blocks",
              "tmat": "SiTMAT stations"}


def khg_data_recap() -> pd.DataFrame:
    """Overview table of re-peat/docs/16-khg-data-recap.md (written by re-peat/tools/khg_data_recap.py from
    re-peat/sites/khg_data_recap.csv); role column left out (see table 2.1)."""
    md = (WORKSPACE / "re-peat/docs/16-khg-data-recap.md").read_text(encoding="utf-8").splitlines()
    i = md.index("## Overview") + 2
    rows = []
    while i < len(md) and md[i].startswith("|"):
        rows.append([c.strip() for c in md[i].strip().strip("|").split("|")]); i += 1
    head, body = rows[0], rows[2:]
    df = pd.DataFrame(body, columns=head).drop(columns=["role"]).replace({"–": "-"})
    out = pd.DataFrame({"KHG": df.KHG.map(short)})
    for col in head[2:]:
        v = df[col].str.replace("DEMNAS-jp2 ", "DEMNAS jp2 ", regex=False)
        have = v[v != "-"]
        name = RECAP_HEAD.get(col, col)
        tags = have.str.extract(r"^([A-Za-z/]+)\s")[0]
        if len(have) and tags.notna().all() and tags.nunique() == 1:       # same source in every row: move it to the header
            v = v.where(v == "-", v.str.replace(rf"^{re.escape(tags.iloc[0])}\s+", "", regex=True))
            if tags.iloc[0].lower()[:5] not in name.lower():
                name = f"{name} ({tags.iloc[0]})"
        for unit, lab in ((" stations", "n"), (" pts", "points")):
            if len(have) and have.str.endswith(unit).all():
                v = v.str.replace(unit, "", regex=False)
                name = f"{name}, {lab}"
        out[name] = v.values
    out.attrs["note"] = ("Rasters: finest product covering at least half the KHG, its resolution and the share of the KHG polygon "
                         "it covers. jp2: DEMNAS Sumatra re-hosted as lossy JPEG2000. Proposed blocks: Bluebook 2026 targets, "
                         "not built. Kampar-Gaung (test site) is not in the recap.")
    return out


DEM_PRODUCT = {"deltadtm": "DeltaDTM", "demnas": "DEMNAS"}


def dem_inputs() -> pd.DataFrame:
    d = pd.read_csv(WORKSPACE / "re-peat/sites/khg_dem_inputs.csv")
    d["family"] = d["product"].map(lambda p: "lidar" if p.startswith("lidar") else p)
    d["name"] = d.khg.map(short)
    return d


def khg_dem_inputs() -> pd.DataFrame:
    """re-peat/sites/khg_dem_inputs.csv (khg, product, res_m, cover_pct): one row per KHG, one column per DEM family."""
    d = dem_inputs()
    cell = lambda r: "not clipped" if pd.isna(r.res_m) else f"{r.res_m:g} m, {r.cover_pct:g}%"  # noqa: E731
    rows = []
    for name, g in d.groupby("name", sort=False):
        row = {"KHG": name}
        for fam, lab in (("lidar", "LiDAR"), ("deltadtm", "DeltaDTM"), ("demnas", "DEMNAS")):
            x = g[g.family == fam]
            row[f"{lab} (resolution, cover)"] = "; ".join(cell(r) for r in x.itertuples()) if len(x) else "-"
        rows.append(row)
    out = pd.DataFrame(rows)
    out.attrs["note"] = ("Cover: valid cells over KHG cells inside the clipped raster window. Chapter 4 gives the cover of "
                         "the whole KHG polygon.")
    return out


# --- chapter 4 --------------------------------------------------------------------------------------------------------
COVER_CACHE = OUT / "_cache_dem_polygon_cover.csv"


def polygon_cover(raster: Path, khg_gpkg: Path) -> float:
    """Share of the KHG polygon with valid DEM cells, read block by block at native resolution
    (khg_data_recap.raster_cover); cached in figures/ by file size and mtime."""
    import geopandas as gpd
    from shapely.geometry import mapping
    from khg_data_recap import raster_cover
    st, kt = raster.stat(), khg_gpkg.stat()
    key = f"{raster.relative_to(WORKSPACE).as_posix()}|{st.st_size}|{int(st.st_mtime)}|{int(kt.st_mtime)}"
    cache = pd.read_csv(COVER_CACHE) if COVER_CACHE.exists() else pd.DataFrame(columns=["key", "cover"])
    hit = cache[cache.key == key]
    if len(hit):
        return float(hit.cover.iloc[0])
    geom = gpd.read_file(khg_gpkg).to_crs(4326).union_all()
    r = raster_cover((str(raster), "", mapping(geom)))
    cover = r["coverage_pct"] if r else 0.0
    stem = key.split("|")[0] + "|"
    cache = pd.concat([cache[~cache.key.str.startswith(stem)], pd.DataFrame([{"key": key, "cover": cover}])])
    cache.to_csv(COVER_CACHE, index=False)
    return cover


def dem_coverage() -> pd.DataFrame:
    """re-peat/sites/khg_dem_inputs.csv (khg, product, res_m, cover_pct, note), LiDAR row with the highest cover_pct per KHG;
    cover of the KHG polygon computed from _khg/<folder>/01_dem/inputs/<file> (or its source in _data when not clipped)
    and _khg/<folder>/00_inputs/khg.gpkg."""
    d = dem_inputs()
    lid = d[d.family == "lidar"].sort_values("cover_pct", ascending=False, na_position="last").drop_duplicates("khg")
    d = d.loc[sorted(set(d.index[d.family != "lidar"]) | set(lid.index))]
    rows = []
    for r in d.itertuples():
        f = KHG / r.folder
        src = f / "01_dem/inputs" / r.file if isinstance(r.file, str) else WORKSPACE / "_data" / str(r.sources)
        cov = polygon_cover(src, f / "00_inputs/khg.gpkg") if src.exists() else np.nan
        res = r.res_m
        if pd.isna(res) and src.exists():
            import rasterio
            with rasterio.open(src) as ds:
                res = abs(ds.res[0]) * (111320 if ds.crs.is_geographic else 1)
        rows.append({"KHG": r.name, "DEM": "LiDAR" if r.family == "lidar" else DEM_PRODUCT[r.family],
                     "Resolution (m)": f"{res:g}" if pd.notna(res) else "-",
                     "Cover of clip window (%)": fmt(r.cover_pct, 1), "Cover of KHG polygon (%)": fmt(cov, 1),
                     "Source": str(r.note).split(";")[0].split(",")[0]})
    out = pd.DataFrame(rows)
    out.attrs["note"] = ("Clip window: valid cells over KHG cells inside the clipped raster window, the measure the chain's "
                         "coverage gate reads. KHG polygon: valid cells over the whole KHG polygon, counted at native "
                         "resolution. A LiDAR without a clip is measured on its source file.")
    return out


def polygon_cover_of(code: str, dem: str) -> float:
    """Cover of the KHG polygon by the DEM clip of a chain variant (LiDAR: the clip with the highest window cover)."""
    d = dem_inputs()
    f = folder(code)
    x = d[(d.folder == f.name) & (d.family == dem)].sort_values("cover_pct", ascending=False)
    if x.empty or not isinstance(x.file.iloc[0], str):
        return np.nan
    return polygon_cover(f / "01_dem/inputs" / x.file.iloc[0], f / "00_inputs/khg.gpkg")


def dem_label(code: str, dem: str) -> str:
    """DEM name; a LiDAR covering under 90% of the KHG polygon carries its cover."""
    if dem == "lidar":
        c = polygon_cover_of(code, "lidar")
        if isnum(c) and c < 90:
            return f"LiDAR ({c:.0f}% of KHG)"
    return DEM_LABEL[dem]


# --- chapter 5 --------------------------------------------------------------------------------------------------------
def subkhg_units() -> pd.DataFrame:
    """_khg/<folder>/02_delineation/<dem>/delineation_report.json (n_subkhg, pieces_before_merge, min_area_km2, area_km2)
    for the four KHG with completed chains and the three DEMs."""
    rows = []
    for code, name in COMPLETED.items():
        for dem in DEMS:
            rep = read_json(folder(code) / "02_delineation" / dem / "delineation_report.json")
            if not rep:
                rows.append({"KHG": name, "Terrain": DEM_LABEL[dem]}); continue
            r = rep[0] if isinstance(rep, list) else rep
            a = r["area_km2"]
            rows.append({"KHG": name, "Terrain": dem_label(code, dem), "Sub-KHG (n)": r["n_subkhg"],
                         "Pieces before merging (n)": f"{r['pieces_before_merge']:,}",
                         "Minimum area (km²)": fmt(r["min_area_km2"], 1),
                         "Unit area min / median / max (km²)": f"{a['min']:,.0f} / {a['median']:,.0f} / {a['max']:,.0f}",
                         "Units total (km²)": fmt(a["total"])})
    out = pd.DataFrame(rows).fillna("-")
    out.attrs["note"] = "Where a LiDAR covers only part of the KHG, its units cover only that part; the cover is given after the terrain name."
    return out


def subkhg_map_sugihan_lumpur():
    """_khg/16.02.01_sugihan_lumpur/02_delineation/lidar/subkhg_units.gpkg (unit_id), 00_inputs/canals.gpkg (KET_KANAL
    Kanal Primer, Kanal Sekunder), 00_inputs/rivers.gpkg and 00_inputs/khg.gpkg."""
    import geopandas as gpd
    from matplotlib.lines import Line2D
    f = folder("16.02.01")
    units = gpd.read_file(f / "02_delineation/lidar/subkhg_units.gpkg")
    crs = utm(units)
    units = units.to_crs(crs)
    khg = gpd.read_file(f / "00_inputs/khg.gpkg").to_crs(crs)
    can = gpd.read_file(f / "00_inputs/canals.gpkg")
    can = can[can.KET_KANAL.isin(["Kanal Primer", "Kanal Sekunder"])].to_crs(crs)
    riv = gpd.read_file(f / "00_inputs/rivers.gpkg").to_crs(crs)
    fig, ax = plt.subplots(figsize=(W, W))
    units.plot(ax=ax, facecolor="#eef3f8", edgecolor=BLUE_RAMP[650], linewidth=0.8, zorder=1)
    can[can.KET_KANAL == "Kanal Sekunder"].plot(ax=ax, color="#a3a29d", linewidth=0.3, zorder=2)
    can[can.KET_KANAL == "Kanal Primer"].plot(ax=ax, color="#5c5c58", linewidth=0.7, zorder=2)
    if len(riv):
        riv.plot(ax=ax, color=SERIES[0], linewidth=1.0, zorder=3)
    units.boundary.plot(ax=ax, color=BLUE_RAMP[650], linewidth=1.0, zorder=3.5)
    khg.boundary.plot(ax=ax, color=INK, linewidth=1.3, zorder=4)
    for r in units.itertuples():
        p = r.geometry.representative_point()
        ax.text(p.x, p.y, str(r.unit_id).split("_")[-1], ha="center", va="center", fontsize=6.5, color=INK, zorder=5,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))
    km_axes(ax, crs_name(crs)); north_arrow(ax)
    ax.legend(handles=[Line2D([], [], color=INK, lw=1.3, label="KHG boundary"),
                       Line2D([], [], color=BLUE_RAMP[650], lw=1.0, label=f"Sub-KHG unit ({len(units)})"),
                       Line2D([], [], color="#5c5c58", lw=0.7, label="Primary canal"),
                       Line2D([], [], color="#a3a29d", lw=0.5, label="Secondary canal"),
                       Line2D([], [], color=SERIES[0], lw=1.0, label="River")],
              loc="lower left", fontsize=7.5, frameon=True, facecolor="white", edgecolor="none", framealpha=0.85)
    return save(fig, "subkhg_map_sugihan_lumpur")


# --- chapter 6 --------------------------------------------------------------------------------------------------------
PROFILE = NATIONAL / "operational/profile.csv"
FOCUS_EN = {"tinggi": "high", "sedang": "medium", "rendah": "low"}


def focus_en(kelas) -> str:
    k = str(kelas)
    return FOCUS_EN.get(k.split(":")[-1].strip(), "not ranked") if k.startswith("Fokus") else "not ranked"


def canals_pst(r) -> str:
    return " / ".join(fmt(r[c], 2) for c in ("u_canal_primary", "u_canal_secondary", "u_canal_tertiary"))


def team_profile() -> pd.DataFrame:
    p = pd.read_csv(PROFILE)
    t = team()
    p = p[p.khg_id.str.replace("KHG.", "", regex=False).isin(t)].copy()
    p["role"] = p.khg_id.str.replace("KHG.", "", regex=False).map(t)
    return p.sort_values("peringkat", na_position="last")


def national_rank_map():
    """re-peat/reports/national_profile/operational/profile.gpkg (skor_risiko, peringkat, kelas); team KHG from
    re-peat/sites/selected_khg.csv."""
    import geopandas as gpd
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    g = gpd.read_file(NATIONAL / "operational/profile.gpkg", columns=["khg_id", "skor_risiko", "peringkat", "kelas"])
    ranked = g[g.peringkat.notna()]
    cmap = LinearSegmentedColormap.from_list("seq", ["#e3eefc", BLUE_RAMP[250], BLUE_RAMP[450], BLUE_RAMP[650], "#0d366b"])
    t = team()
    sel = g[g.khg_id.str.replace("KHG.", "", regex=False).isin(t)]
    fig = plt.figure(figsize=(W, W * 0.52))
    ax = fig.add_axes([0.07, 0.24, 0.92, 0.74])
    cax = fig.add_axes([0.1, 0.07, 0.36, 0.035])
    g[g.peringkat.isna()].plot(ax=ax, color=NEUTRAL, linewidth=0)
    ranked.plot(ax=ax, column="skor_risiko", cmap=cmap, vmin=0, vmax=1, linewidth=0)
    sel.boundary.plot(ax=ax, color=SERIES[1], linewidth=0.8)
    c = sel.to_crs(6933).centroid.to_crs(4326)
    ax.scatter(c.x, c.y, s=16, facecolor="none", edgecolor=SERIES[1], linewidth=1.0, zorder=5)
    ax.set_aspect("equal"); ax.grid(False)
    ax.set_ylabel("Latitude (°)")
    ax.tick_params(labelsize=7.5)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}°E"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{abs(v):.0f}°{'S' if v < 0 else 'N' if v > 0 else ''}"))
    ax.set_ylabel(""); ax.set_xlabel("")
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    km = 500                                                       # scale bar at the map's mean latitude
    deg = km / (111.32 * np.cos(np.radians((y0 + y1) / 2)))
    xs, ys = x0 + 0.03 * (x1 - x0), y0 + 0.08 * (y1 - y0)
    ax.plot([xs, xs + deg], [ys, ys], color=INK, lw=2, solid_capstyle="butt")
    ax.text(xs + deg / 2, ys + 0.02 * (y1 - y0), f"{km} km", ha="center", va="bottom", fontsize=7.5, color=INK)
    north_arrow(ax, 0.97, 0.95)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 1))
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.ax.tick_params(labelsize=7.5)
    n = ranked.kelas.map(focus_en).value_counts()
    for cls in ("sedang", "tinggi"):                               # class breaks: lowest score of each class
        lo = ranked[ranked.kelas.astype(str).str.endswith(cls)].skor_risiko.min()
        cax.axvline(lo, color=INK, lw=1.2)
    cb.ax.set_title(f"Priority score (0-1); ticks inside: class breaks, low {n.get('low', 0)} / medium "
                    f"{n.get('medium', 0)} / high {n.get('high', 0)} KHG", fontsize=7.5, color=INK, fontweight="normal", loc="left")
    fig.legend(handles=[Patch(color=NEUTRAL, label=f"Not ranked ({int(g.peringkat.isna().sum())} KHG)"),
                        Line2D([], [], marker="o", ls="", mfc="none", mec=SERIES[1], label=f"Team KHG ({len(sel)})")],
               loc="lower left", bbox_to_anchor=(0.58, 0.02), ncol=1, fontsize=7.5)
    return save(fig, "national_rank_map")


def national_top20() -> pd.DataFrame:
    """re-peat/reports/national_profile/operational/profile.csv, peringkat 1-20."""
    p = pd.read_csv(PROFILE)
    p = p[p.peringkat.between(1, 20)].sort_values("peringkat")
    out = pd.DataFrame({
        "Rank": p.peringkat.astype(int), "KHG": p.nama.map(short), "Province": p.province,
        "Peat (km²)": p.peat_km2.map(fmt),
        "Burned / repeat burns (% of peat)": [f"{fmt(a, 1, True)} / {fmt(b, 1, True)}" for a, b in zip(p.u_fire_freq, p.u_burn_repeat)],
        "Hotspots (per km² peat per year)": p.u_hotspot.map(lambda v: fmt(v, 2)),
        "Hotspots 2026 (per km² peat; high conf. %)": [f"{fmt(a, 2)} ({fmt(b, 0, True)})" for a, b in zip(p.u_hotspot_now, p.hs_now_high_share)],
        "Canals P / S / T (km per km²)": [canals_pst(r) for _, r in p.iterrows()],
        "Score": p.skor_risiko.map(lambda v: fmt(v, 2)), "Rank SD": p.sd_peringkat.map(lambda v: fmt(v, 1))})
    out.attrs["note"] = ("Burned: share of peat burned per year; repeat burns: share of peat burned more than once. "
                         "P / S / T: primary, secondary, tertiary canals; '-' = not mapped. Rank SD: standard deviation of "
                         "the rank over the sensitivity runs. Default weights, proposed for agreement with KLH and the World Bank.")
    return out


def national_yearly():
    """re-peat/reports/national_profile/operational/yearly.csv: sum over KHG of burned_peat_km2 (2015-2025) and
    n_hotspot_peat (2012-2025)."""
    y = pd.read_csv(NATIONAL / "operational/yearly.csv")
    b = y[(y.metric == "burned_peat_km2") & y.year.between(2015, 2025)].groupby("year").value.sum()
    h = y[(y.metric == "n_hotspot_peat") & y.year.between(2012, 2025)].groupby("year").value.sum()
    b = b.reindex(range(2015, 2026), fill_value=0); h = h.reindex(range(2012, 2026), fill_value=0)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(W, W * 0.62), sharex=True)
    for ax, s, lab, col in ((a1, b, "Burned peat (km²)", SERIES[1]), (a2, h / 1000, "Hotspots on peat\n(thousand per year)", SERIES[0])):
        ax.plot(s.index, s.values, color=col, marker="o", ms=3.5)
        ax.set_ylabel(lab); ax.set_ylim(0, None)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        top = s.idxmax()
        ax.annotate(f"{s[top]:,.0f}", (top, s[top]), xytext=(5, -2), textcoords="offset points", fontsize=7.5, color=INK, va="top")
    a2.set_xlabel("Year"); a2.set_xticks(range(2012, 2026))
    a2.tick_params(axis="x", labelsize=7.5)
    fig.align_ylabels()
    return save(fig, "national_yearly")


def national_selected() -> pd.DataFrame:
    """re-peat/reports/national_profile/operational/profile.csv for the 13 team KHG; role from re-peat/sites/selected_khg.csv."""
    p = team_profile()
    out = pd.DataFrame({
        "KHG": [short(n) + (" (reserve)" if r == "reserve" else "") for n, r in zip(p.nama, p.role)],
        "Rank (class)": [f"{fmt(a)} ({focus_en(k)})" if isnum(a) else "not ranked" for a, k in zip(p.peringkat, p.kelas)],
        "Peat (km²)": p.peat_km2.map(fmt),
        "Burned / repeat burns (% of peat)": [f"{fmt(a, 1, True)} / {fmt(b, 1, True)}" for a, b in zip(p.u_fire_freq, p.u_burn_repeat)],
        "Hotspots (per km² peat per year)": p.u_hotspot.map(lambda v: fmt(v, 2)),
        "Hotspots on peat 2026 (n; high conf. %)": [f"{fmt(a)} ({fmt(b, 0, True)})" for a, b in zip(p.hs_now_kept, p.hs_now_high_share)],
        "Rank by 2026 hotspots / by area": [f"{fmt(a)} / {fmt(b)}" for a, b in zip(p.peringkat_now_n, p.peringkat_area)],
        "Canals P / S / T (km per km²)": [canals_pst(r) for _, r in p.iterrows()],
        "SiTMAT stations (days deeper than 0.4 m, %)": [f"{int(a)} ({fmt(b, 0, True)})" if isnum(a) and a > 0 else "-"
                                                        for a, b in zip(p.n_tma_stations, p.tma_deep_share)]})
    out.attrs["note"] = ("Rank among the ranked KHG; P / S / T: primary, secondary, tertiary canals, '-' = not mapped. "
                         "Default weights, proposed for agreement with KLH and the World Bank.")
    return out


def national_stage3() -> pd.DataFrame:
    """re-peat/reports/national_profile/stage3/stage3_profile.csv joined to operational/profile.csv (nama, peringkat)."""
    p = team_profile()[["khg_id", "nama", "peringkat"]]
    s = p.merge(pd.read_csv(NATIONAL / "stage3/stage3_profile.csv"), on="khg_id", how="left")
    return pd.DataFrame({
        "KHG": s.nama.map(short), "Rank": s.peringkat.map(fmt),
        "Dry-season deficit 2015-2021 (mm)": s.deficit_mean_mm.map(fmt),
        "Rain, year / Jun-Oct (mm)": [f"{fmt(a)} / {fmt(b)}" for a, b in zip(s.rain_mean_mm, s.rain_dry_mean_mm)],
        "Tree / crop / grass / wetland (% of KHG)": [" / ".join(fmt(r[c], 0, True) for c in ("lc_tree", "lc_crop", "lc_grass", "lc_wetland"))
                                                    for _, r in s.iterrows()],
        "Permanent water (% of KHG)": s.water_perm_frac.map(lambda v: fmt(v, 1, True)),
        "Peat, GFW / GPM 1 km (% of KHG)": [f"{fmt(a, 0, True)} / {fmt(b, 0, True)}" for a, b in zip(s.peat_frac_gfw, s.peat_frac_gpm1km)]})


def national_overlay() -> pd.DataFrame:
    """re-peat/reports/national_profile/stage3/overlay/overlay_summary.csv (licence_any/in, feg/lindung) and
    operational/profile.csv (hs_now_kept), team KHG. No holder names."""
    p = team_profile()[["khg_id", "nama", "hs_now_kept"]]
    o = pd.read_csv(NATIONAL / "stage3/overlay/overlay_summary.csv")
    lic = o[(o.layer == "licence_any") & (o["class"] == "in")].set_index("khg_id")
    feg = o[(o.layer == "feg") & (o["class"] == "lindung")].set_index("khg_id")
    rows = []
    for r in p.itertuples():
        L = lic.loc[r.khg_id] if r.khg_id in lic.index else None
        F_ = feg.loc[r.khg_id] if r.khg_id in feg.index else None
        rows.append({"KHG": short(r.nama),
                     "Peat in licence areas, km² (% of peat)": f"{fmt(L.peat_km2)} ({fmt(L.share_peat, 0, True)})" if L is not None else "-",
                     "Burned peat in licence areas, km² (% of that peat)": f"{fmt(L.burned_peat_km2)} ({fmt(L.burned_share, 0, True)})" if L is not None else "-",
                     "Hotspots 2026 on peat in licence areas (n)": fmt(L.hs_now_peat) if L is not None else "-",
                     "Protected peat function (% of peat)": fmt(F_.share_peat, 0, True) if F_ is not None else "-",
                     "Hotspots 2026 on protected peat (n)": fmt(F_.hs_now_peat) if F_ is not None else "-",
                     "Hotspots 2026 on peat, all (n)": fmt(r.hs_now_kept)})
    out = pd.DataFrame(rows)
    out.attrs["note"] = "Burned peat 2015-2025. Licence areas: any business licence of 2025. Context only, not scored."
    return out


# --- chapter 7 --------------------------------------------------------------------------------------------------------
def prio_dir(code: str, dem: str) -> Path:
    return folder(code) / "04_prioritisation" / dem


def subkhg_maps_sugihan_lumpur():
    """_khg/16.02.01_sugihan_lumpur/04_prioritisation/<lidar|deltadtm|demnas>/unit_prioritas.gpkg (kelas, peringkat) and
    00_inputs/khg.gpkg."""
    import geopandas as gpd
    from matplotlib.patches import Patch
    f = folder("16.02.01")
    khg = gpd.read_file(f / "00_inputs/khg.gpkg")
    crs = utm(khg)
    khg = khg.to_crs(crs)
    layers = {d: gpd.read_file(prio_dir("16.02.01", d) / "unit_prioritas.gpkg").to_crs(crs)
              for d in DEMS if (prio_dir("16.02.01", d) / "unit_prioritas.gpkg").exists()}
    fig, axes = plt.subplots(1, len(layers), figsize=(W, W * 0.5), sharex=True, sharey=True)
    for i, (ax, (dem, g)) in enumerate(zip(np.atleast_1d(axes), layers.items())):
        g["need"] = g.kelas.map(need_en)
        g.plot(ax=ax, color=g.need.map(NEED_COLOR).fillna(NEUTRAL), edgecolor="white", linewidth=0.5)
        khg.boundary.plot(ax=ax, color=INK, linewidth=0.8)
        for r in g.itertuples():
            p = r.geometry.representative_point()
            ax.text(p.x, p.y, f"{int(r.peringkat)}", ha="center", va="center", fontsize=6.5,
                    color="white" if r.need in ("high", "medium") else INK)
        km_axes(ax, crs_name(crs), ylabel=(i == 0))
        ax.set_title(f"{DEM_LABEL[dem]} ({len(g)} units)")
        ax.set_xlabel("")
        if i:
            ax.set_ylabel("")
    north_arrow(np.atleast_1d(axes)[-1], 0.88, 0.95)
    fig.supxlabel(f"Easting (km, {crs_name(crs)}); numbers: rank", fontsize=8.5, y=0.13)
    fig.legend(handles=[Patch(color=NEED_COLOR[k], label=f"{k} need") for k in ("high", "medium", "low")],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.0), fontsize=8)
    fig.subplots_adjust(wspace=0.06, bottom=0.25)
    return save(fig, "subkhg_maps_sugihan_lumpur")


def subkhg_top_sugihan_lumpur() -> pd.DataFrame:
    """_khg/16.02.01_sugihan_lumpur/04_prioritisation/lidar/unit_prioritas.csv, peringkat 1-10."""
    u = pd.read_csv(prio_dir("16.02.01", "lidar") / "unit_prioritas.csv")
    u = u[u.peringkat.between(1, 10)].sort_values("peringkat")
    out = pd.DataFrame({
        "Rank": u.peringkat.astype(int), "Unit": u.unit_id.str.split("_").str[-1], "Area (km²)": u.area_km2.map(fmt),
        "Need score (U / S)": [f"{fmt(a, 2)} ({fmt(b, 2)} / {fmt(c, 2)})" for a, b, c in zip(u.skor_need, u.skor_urgensi, u.skor_dampak)],
        "Burned (% of peat per year)": u.u_fire_freq.map(lambda v: fmt(v, 1, True)),
        "Hotspots (per km² peat per year)": u.u_hotspot.map(lambda v: fmt(v, 2)),
        "Within canal reach (%)": u.f_reach.map(lambda v: fmt(v, 0, True)),
        "Missing blocks (0-1)": u.u_ipg_gap.map(lambda v: fmt(v, 2)),
        "Blocks needed / existing / additional": [f"{fmt(a)} / {fmt(b)} / {fmt(c)}" for a, b, c in zip(u.n_sekat_perlu, u.n_sekat_ada, u.sekat_tambahan)],
        "Peat depth (m)": u.i_peat_depth.map(lambda v: fmt(v, 1)),
        "High class in weight draws (%)": u.p_kebutuhan_tinggi.map(lambda v: fmt(v, 0, True))})
    out.attrs["note"] = "U: need part (urgency); S: stakes part. Default weights, proposed for agreement with KLH and the World Bank."
    return out


def subkhg_classes_by_khg_dem() -> pd.DataFrame:
    """_khg/<folder>/04_prioritisation/<dem>/ringkasan_kelas.csv (kelas, unit, luas_km2), laporan.json (n_units,
    ranking_agreement.spearman, sensitivity.share_units_stable_class) and kebutuhan_sekat.csv (n_sekat_perlu, n_sekat_ada,
    sekat_tambahan) for the four KHG with completed chains."""
    order = ["16.02.01", "16.02-07.01", "15.05-07-10.01", "14.02-04-05.01"]
    rows = []
    for code in order:
        name = COMPLETED[code] + (" (test site)" if code == "14.02-04-05.01" else "")
        for dem in DEMS:
            d = prio_dir(code, dem)
            rep = read_json(d / "laporan.json")
            if not rep:
                rows.append({"KHG": name, "DEM": DEM_LABEL[dem]}); continue
            k = pd.read_csv(d / "ringkasan_kelas.csv")
            k["need"] = k.kelas.map(need_en)
            k = k.set_index("need")
            s = pd.read_csv(d / "kebutuhan_sekat.csv")[["n_sekat_perlu", "n_sekat_ada", "sekat_tambahan"]].sum()
            get = lambda col, lvl: k[col].get(lvl, 0)  # noqa: E731
            rows.append({"KHG": name, "DEM": dem_label(code, dem), "Units (n)": rep["n_units"],
                         "High / medium / low need (units)": " / ".join(str(int(get("unit", x))) for x in ("high", "medium", "low")),
                         "High / medium / low need (km²)": " / ".join(fmt(get("luas_km2", x)) for x in ("high", "medium", "low")),
                         "Spearman, need score vs rank-sum": fmt(rep["ranking_agreement"]["spearman"], 2),
                         "Units with a stable class (%)": fmt(rep["sensitivity"]["share_units_stable_class"], 0, True),
                         "Blocks needed / existing / additional": f"{fmt(s.n_sekat_perlu)} / {fmt(s.n_sekat_ada)} / {fmt(s.sekat_tambahan)}"})
    out = pd.DataFrame(rows).fillna("-")
    out.attrs["note"] = ("Kampar-Gaung is a test site, not one of the 12 selected KHG. Stable class: share of units keeping their "
                         "class over the weight draws. Default weights, proposed for agreement with KLH and the World Bank.")
    return out


def weighted_spearman(a, b, w) -> float:
    """Pearson correlation of weighted mid-ranks (rank = cumulative weight below + half the own weight), weighted by w."""
    def wrank(x):
        s = pd.DataFrame({"x": x, "w": w}).groupby("x").w.sum().sort_index()
        mid = s.cumsum() - s / 2
        return pd.Series(x).map(mid).to_numpy()
    ra, rb = wrank(np.asarray(a)), wrank(np.asarray(b))
    w = np.asarray(w, float) / np.sum(w)
    ma, mb = (w * ra).sum(), (w * rb).sum()
    cov = (w * (ra - ma) * (rb - mb)).sum()
    return float(cov / np.sqrt((w * (ra - ma) ** 2).sum() * (w * (rb - mb) ** 2).sum()))


def subkhg_dem_agreement() -> pd.DataFrame:
    """Overlay of _khg/<folder>/04_prioritisation/<dem_a>/unit_prioritas.gpkg with <dem_b>/unit_prioritas.gpkg (kelas,
    skor_risiko) in an equal-area projection (EPSG:6933); area shares and an area-weighted Spearman over the pieces."""
    import geopandas as gpd
    order = ["16.02.01", "16.02-07.01", "15.05-07-10.01", "14.02-04-05.01"]
    pairs = [("lidar", "deltadtm"), ("lidar", "demnas"), ("deltadtm", "demnas")]
    rows = []
    for code in order:
        lay = {d: gpd.read_file(prio_dir(code, d) / "unit_prioritas.gpkg", columns=["kelas", "skor_risiko"]).to_crs(6933)
               for d in DEMS if (prio_dir(code, d) / "unit_prioritas.gpkg").exists()}
        for a, b in pairs:
            if a not in lay or b not in lay:
                rows.append({"KHG": COMPLETED[code], "DEM pair": f"{DEM_LABEL[a]} - {DEM_LABEL[b]}"}); continue
            x = gpd.overlay(lay[a], lay[b], how="intersection", keep_geom_type=True)
            x["km2"] = x.geometry.area / 1e6
            x = x[x.km2 > 0]
            ca, cb = x.kelas_1.map(need_en), x.kelas_2.map(need_en)
            high_a = x.km2[ca == "high"].sum()
            rows.append({"KHG": COMPLETED[code], "DEM pair": f"{dem_label(code, a)} - {DEM_LABEL[b]}",
                         "Overlap (km²)": fmt(x.km2.sum()),
                         "Same need class (% of overlap)": fmt(x.km2[ca == cb].sum() / x.km2.sum(), 0, True),
                         "High need in first also high in second (%)": fmt(x.km2[(ca == "high") & (cb == "high")].sum() / high_a, 0, True) if high_a else "-",
                         "Spearman of scores, area-weighted": fmt(weighted_spearman(x.skor_risiko_1, x.skor_risiko_2, x.km2), 2)})
    out = pd.DataFrame(rows).fillna("-")
    out.attrs["note"] = ("Units are matched by location, not by name: the unit sets differ per DEM. Shares are of the area both "
                         "variants cover. Default weights, proposed for agreement with KLH and the World Bank.")
    return out


# --- chapter 8a -------------------------------------------------------------------------------------------------------
def neraca_dir(code: str) -> Path:
    return folder(code) / "03_neraca"


def khg_dekadal(code: str, product: str) -> pd.Series:
    """Area-weighted mean over sub-KHG of balance_<product>_dekad.csv (time_cov >= 0.999), DeltaDTM units."""
    d = neraca_dir(code) / "deltadtm/inputs"
    b = pd.read_csv(d / f"balance_{product}_dekad.csv", parse_dates=["start"])
    a = pd.read_csv(d / "units_landcover.csv")[["unit_id", "area_km2"]]
    b = b[(b.time_cov >= 0.999) & b.mm.notna()].merge(a, on="unit_id")
    return b.groupby("start").apply(lambda g: np.average(g.mm, weights=g.area_km2), include_groups=False)


def direct_label(ax, x, y, text, color, dy=0):
    ax.annotate(text, (x, y), xytext=(4, dy), textcoords="offset points", va="center", fontsize=7.5, color=color)


def end_labels(ax, items, gap_pt=9):
    """Direct labels at line ends, nudged apart vertically: items = [(x, y, text, colour)]."""
    fig = ax.figure
    fig.canvas.draw()
    to_px = ax.transData.transform
    pts = sorted(((to_px((float(np.asarray(ax.xaxis.convert_units(x))), y))[1], x, y, t, c) for x, y, t, c in items), key=lambda p: p[0])
    gap = gap_pt * fig.dpi / 72
    ys = [p[0] for p in pts]
    for i in range(1, len(ys)):
        ys[i] = max(ys[i], ys[i - 1] + gap)
    for (py, x, y, t, c), ny in zip(pts, ys):
        ax.annotate(t, (x, y), xytext=(4, (ny - py) * 72 / fig.dpi), textcoords="offset points", va="center",
                    fontsize=7.5, color=c)


def neraca_rain_et_dekadal():
    """_khg/<folder>/03_neraca/deltadtm/inputs/balance_{chirps,mod16,wapor}_dekad.csv (unit_id, start, mm, time_cov),
    area-weighted with units_landcover.csv (area_km2); rows with time_cov < 0.999 dropped."""
    prods = [("chirps", "Rain, CHIRPS", SERIES[0]), ("mod16", "ET, MOD16", SERIES[1]), ("wapor", "ET, WaPOR", SERIES[2])]
    fig, axes = plt.subplots(2, 2, figsize=(W, W * 0.7), sharex=True, sharey=True)
    for ax, (code, name) in zip(axes.flat, COMPLETED.items()):
        for p, lab, col in prods:
            s = khg_dekadal(code, p)
            ax.plot(s.index, s.values, color=col, lw=0.8, label=lab)
        ax.set_title(name, loc="left")
    for ax in axes[:, 0]:
        ax.set_ylabel("mm per dekad")
    for ax in axes[1]:
        ax.xaxis.set_major_locator(matplotlib.dates.YearLocator(2))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
    axes[0, 0].set_ylim(0, None)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.03))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return save(fig, "neraca_rain_et_dekadal")


def neraca_station_depth_2026():
    """_khg/<folder>/03_neraca/runs/deficit/tier1_series.csv (date, obs_mean_cm); deficit window from neraca_khg.csv
    (period_start, period_end)."""
    fig, ax = plt.subplots(figsize=(W, W * 0.48))
    ends, labels = [], []
    for k, (code, name) in enumerate(COMPLETED.items()):
        d = neraca_dir(code) / "runs/deficit"
        if not (d / "tier1_series.csv").exists():
            continue
        s = pd.read_csv(d / "tier1_series.csv", parse_dates=["date"])
        n = pd.read_csv(d / "neraca_khg.csv", parse_dates=["period_start", "period_end"]).iloc[0]
        col = KHG_COLOR[code]
        ax.plot(s.date, s.obs_mean_cm, color=col)
        labels.append((s.date.iloc[-1], s.obs_mean_cm.iloc[-1], f"{name} ({int(n.n_stations)} stations)", col))
        ends.append((n.period_start, n.period_end, col, name))
    lo = min(e[0] for e in ends); hi = max(e[1] for e in ends); first_end = min(e[1] for e in ends)
    ax.axvspan(lo, first_end, color="#e9e8e3", zorder=0, lw=0)
    ax.axvspan(first_end, hi, color="#f3f2ee", zorder=0, lw=0)
    by_end = {}
    for e in ends:
        by_end.setdefault(e[1], []).append(e[3])
    txt = f"Deficit window {lo.day} {lo:%b} to " + "; ".join(
        f"{d.day} {d:%b}" + (f" ({', '.join(n)})" if len(by_end) > 1 and len(n) < len(ends) else "") for d, n in sorted(by_end.items()))
    ax.text(lo, 1.01, " " + txt, transform=ax.get_xaxis_transform(), fontsize=7.5, color=MUTED, va="bottom")
    ax.axhline(40, color=INK, lw=0.8, ls="--")
    ax.text(0.01, 40, "40 cm (PP 57/2016)", transform=ax.get_yaxis_transform(), fontsize=7.5, color=INK, va="center",
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"), zorder=5)
    ax.invert_yaxis()
    ax.set_ylabel("Water-table depth below surface (cm)")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    ax.set_xlabel("2026")
    end_labels(ax, labels)
    return save(fig, "neraca_station_depth_2026")


def neraca_calendar():
    """_khg/<folder>/03_neraca/deltadtm/runs/balance/neraca_balance_monthly.csv (month, unit_id, WB_mm, et_source = mod16),
    2018-01 to 2025-12: mean over units, then over years per calendar month."""
    fig, ax = plt.subplots(figsize=(W, W * 0.45))
    labels = []
    for code, name in COMPLETED.items():
        m = pd.read_csv(neraca_dir(code) / "deltadtm/runs/balance/neraca_balance_monthly.csv")
        m = m[(m.et_source == "mod16") & m.month.between("2018-01", "2025-12")]
        k = m.groupby("month").WB_mm.mean()
        cal = k.groupby(k.index.str[5:7].astype(int)).mean()
        ax.plot(cal.index, cal.values, color=KHG_COLOR[code], marker="o", ms=3)
        labels.append((12, cal.loc[12], name, KHG_COLOR[code]))
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(range(1, 13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_xlim(0.7, 15.2)
    ax.spines["bottom"].set_bounds(1, 12)
    ax.set_ylabel("Climatic balance (mm per month)")
    end_labels(ax, labels)
    return save(fig, "neraca_calendar")


def neraca_units(code: str) -> pd.DataFrame:
    """_khg/<folder>/03_neraca/deltadtm/runs/balance/neraca_balance_unit.csv joined to inputs/units_landcover.csv (area_km2);
    footnote from balance_stable_ok of each DEM variant."""
    d = neraca_dir(code)
    u = pd.read_csv(d / "deltadtm/runs/balance/neraca_balance_unit.csv")
    a = pd.read_csv(d / "deltadtm/inputs/units_landcover.csv")[["unit_id", "area_km2"]]
    u = u.merge(a, on="unit_id", how="left").sort_values("unit_id")
    out = pd.DataFrame({"Sub-KHG": u.unit_id.str.split("_").str[-1], "Area (km²)": u.area_km2.map(fmt),
                        "Balance, MOD16 (mm/month)": u.u_wb_mean.map(lambda v: fmt(v, 1)),
                        "P - ET (mm/month)": u.p_minus_et_mean_mm.map(lambda v: fmt(v, 1)),
                        "Deficit months per year": u.u_deficit_months.map(lambda v: fmt(v, 2)),
                        "Interception (share)": u.interception_share.map(lambda v: fmt(v, 2)),
                        "Balance, WaPOR (mm/month)": u.wb_mean_wapor.map(lambda v: fmt(v, 1))})
    ok = {}
    for dem in DEMS:
        f = d / dem / "runs/balance/neraca_balance_unit.csv"
        if f.exists():
            x = pd.read_csv(f)
            v = x.balance_stable_ok.dropna()
            ok[dem] = (bool(v.iloc[0]) if len(v) else None, x, pd.read_csv(d / dem / "inputs/units_landcover.csv").area_km2.sum()
                       if (d / dem / "inputs/units_landcover.csv").exists() else np.nan)
    this = ok.get("deltadtm", (None,))[0]
    note = f"Order of units {'usable' if this else 'not usable'} with DeltaDTM units (ET products {'agree' if this else 'disagree'} on the order)."
    good = [dem for dem, (v, *_ ) in ok.items() if v and dem != "deltadtm"]
    if good and not this:
        parts = []
        for dem in good:
            area, total = ok[dem][2], ok["deltadtm"][2]
            cover = f", which cover {area:,.0f} of {total:,.0f} km²" if isnum(area) and isnum(total) and area < 0.95 * total else ""
            parts.append(f"{DEM_LABEL[dem]} units{cover}")
        note += " Usable with the " + " and ".join(parts) + "."
    out.attrs["note"] = note + " Period 2018-2025."
    return out


def neraca_units_kampar_gaung():
    return neraca_units("14.02-04-05.01")


def neraca_units_mendahara_batanghari():
    return neraca_units("15.05-07-10.01")


def neraca_units_saleh_sugihan():
    return neraca_units("16.02-07.01")


def neraca_units_sugihan_lumpur():
    return neraca_units("16.02.01")


# --- chapter 8b -------------------------------------------------------------------------------------------------------
SL_MODEL = "16.02.01", "lidar/runs/model"
SL_RUNS = {"tropical-large_p1.2_s1.2_t1.2_e0.3_200m": "Simulated, canals 1.2 m below surface",
           "tropical-large_p0.4_s0.4_t0.4_e0.3_200m": "Simulated, canals 0.4 m below surface"}
MB_BASE = "tropical-large_p1.2_s1.2_t1.2_mt0.4_e0.3_100m_pb_dbbsdlp"
MB_BLOCKS = "tropical-large_p1.2_s1.2_t1.2_mt0.4_blk_e0.3_100m_pb_dbbsdlp"


def model_station_fit_sugihan_lumpur():
    """_khg/16.02.01_sugihan_lumpur/03_neraca/inputs/stations_daily.csv (date, station_id, depth_cm); station_sim_daily.csv,
    station_scores.csv (flag) and model_series.csv (P_mm, ET_mm) of the two lidar model runs named in SL_RUNS."""
    nd = neraca_dir(SL_MODEL[0])
    runs = {r: nd / SL_MODEL[1] / r for r in SL_RUNS}
    keep = None
    for d in runs.values():
        sc = pd.read_csv(d / "station_scores.csv")
        ok = set(sc.station_id[sc.flag.isna() | (sc.flag.astype(str).str.strip() == "")])
        keep = ok if keep is None else keep & ok
    obs = pd.read_csv(nd / "inputs/stations_daily.csv", parse_dates=["date"])
    obs = obs[obs.station_id.isin(keep)]
    start = obs.date.min()
    keep = sorted(keep & set(obs.station_id))
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(W, W * 0.62), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    o = obs.groupby("date").depth_cm.mean()
    ax.plot(o.index, o.values, color=INK, lw=1.6, label=f"Observed, mean of {len(keep)} stations")
    for (r, d), col in zip(runs.items(), (SERIES[1], SERIES[0])):
        s = pd.read_csv(d / "station_sim_daily.csv", parse_dates=["date"]).set_index("date")
        s = s.loc[s.index >= start, keep].mean(axis=1)
        ax.plot(s.index, s.values, color=col, label=SL_RUNS[r])
    ax.axhline(40, color=MUTED, lw=0.8, ls="--")
    ax.invert_yaxis()
    ax.set_ylabel("Water-table depth (cm)")
    ax.legend(loc="lower left", fontsize=7.5)
    m = pd.read_csv(next(iter(runs.values())) / "model_series.csv", parse_dates=["date"])
    m = m[m.date >= start]
    ax2.plot(m.date, m.P_mm - m.ET_mm, color=SERIES[2], lw=1.0)
    ax2.axhline(0, color=INK, lw=0.7)
    ax2.set_ylabel("P - ET\n(mm per day)")
    ax2.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b"))
    ax2.set_xlabel("2026")
    fig.align_ylabels()
    return save(fig, "model_station_fit_sugihan_lumpur")


MB_CANAL_RUNS = {"tropical-large_p1.2_s1.2_t1.2_mt0.4_e0.3_100m_pb_dbbsdlp": "Canals 1.2 m, fixed",
                 "tropical-large_p0.8_s0.3_t0.3_mt0.4_e0.3_100m_pb_dbbsdlp": "Canals at LiDAR levels, fixed",
                 "tropical-large_p0.8_s0.3_t0.3_mt0.4_lk_cs1_e0.3_100m_pb_dbbsdlp": "Canal water balance (store, tau 1 day)"}


def model_community_mendahara():
    """_khg/15.05-07-10.01_mendahara_batanghari/03_neraca/inputs/model/stations_daily.csv (date, station_id, depth_cm), the community
    stations off canal cells in the fixed LiDAR-level run (station_scores.csv: group community, flag empty), screened with
    repeat_neraca.groundwater.fieldcheck.screen; station_sim_daily.csv of the runs in MB_CANAL_RUNS. Daily means over the stations, on
    days with at least 5 of them (gaps break the lines)."""
    from repeat_neraca.groundwater import fieldcheck as FC
    md = neraca_dir("15.05-07-10.01") / "lidar/runs/model"
    sc = pd.read_csv(md / "tropical-large_p0.8_s0.3_t0.3_mt0.4_e0.3_100m_pb_dbbsdlp/station_scores.csv", keep_default_na=False)
    ids = sorted(sc.station_id[(sc.group == "community") & (sc.flag == "")])
    obs = pd.read_csv(neraca_dir("15.05-07-10.01") / "inputs/model/stations_daily.csv", parse_dates=["date"])
    obs = obs[obs.station_id.isin(ids)].pivot(index="date", columns="station_id", values="depth_cm")
    obs = obs.reindex(pd.date_range(obs.index.min(), obs.index.max()))
    scr = pd.DataFrame({i: FC.screen(obs[i])[0] for i in ids}).reindex(obs.index)
    mean = lambda t: t.mean(axis=1).where(t.notna().sum(axis=1) >= 5)
    fig, ax = plt.subplots(figsize=(W, W * 0.5))
    ax.axhspan(0, -100, color=GRID, alpha=0.5, lw=0)
    ax.plot(obs.index, mean(obs), color=MUTED, lw=0.9, marker=".", ms=3, label="Observed, raw record")
    ax.plot(scr.index, mean(scr), color=INK, lw=1.8, label="Observed, screened")
    for (r, lab), col in zip(MB_CANAL_RUNS.items(), (SERIES[1], SERIES[0], SERIES[2])):
        sim = pd.read_csv(md / r / "station_sim_daily.csv", parse_dates=["date"]).set_index("date")[ids]
        sim = sim.loc[sim.index >= obs.index.min()]
        ax.plot(sim.index, sim.mean(axis=1), color=col, label=lab)
    ax.axhline(40, color=MUTED, lw=0.8, ls="--")
    ax.axhline(0, color=INK, lw=0.6)
    ax.text(obs.index.min(), -4, "water above the ground", fontsize=7.5, color=MUTED, va="bottom")
    ax.set_ylim(130, -90)
    ax.set_ylabel("Water-table depth (cm)")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    ax.set_xlabel("2026")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=7.5, ncol=3)
    return save(fig, "model_community_mendahara")


def model_days_map_mendahara():
    """_khg/15.05-07-10.01_mendahara_batanghari/03_neraca/lidar/runs/model/<MB_BASE>/model_season_days_deeper_40cm.tif,
    <MB_BLOCKS>/days_deeper_40cm_change.tif, 00_inputs/khg.gpkg and 02_delineation/lidar/subkhg_units.gpkg. The block
    reaches are not drawn: the scenario used the 27 October interventions plan, and the current sekat_reach layer is a later plan."""
    import geopandas as gpd
    import rasterio
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap, TwoSlopeNorm
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from rasterio.features import geometry_mask
    code = "15.05-07-10.01"
    f = folder(code)
    md = neraca_dir(code) / "lidar/runs/model"
    with rasterio.open(md / MB_BASE / "model_season_days_deeper_40cm.tif") as ds:
        base, tr, crs, nod = ds.read(1).astype(float), ds.transform, ds.crs, ds.nodata
        ext = (ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top)
    with rasterio.open(md / MB_BLOCKS / "days_deeper_40cm_change.tif") as ds:
        chg = ds.read(1).astype(float)
        if ds.nodata is not None and np.isfinite(ds.nodata):
            chg[chg == ds.nodata] = np.nan
    khg = gpd.read_file(f / "00_inputs/khg.gpkg").to_crs(crs)
    units = gpd.read_file(f / "02_delineation/lidar/subkhg_units.gpkg").to_crs(crs)
    inside = geometry_mask(khg.geometry, base.shape, tr, invert=True)
    nodata = ~np.isfinite(base) | ((base == nod) if nod is not None else False)
    base[nodata] = np.nan
    grey = np.where(inside & nodata, 1.0, np.nan)
    vmax = np.nanmax(base)
    seq = LinearSegmentedColormap.from_list("seq", ["#f4f8fd", BLUE_RAMP[250], BLUE_RAMP[450], BLUE_RAMP[650], "#0d366b"])
    div = LinearSegmentedColormap.from_list("div", ["#104281", "#2a78d6", "#9ec5f4", "#f0efec", "#f2b8b0", "#e34948", "#a82b2b"])
    lim = float(np.nanpercentile(np.abs(chg[np.isfinite(chg) & (chg != 0)]), 95)) if np.any(np.isfinite(chg) & (chg != 0)) else 1
    lim = max(5.0, np.ceil(lim / 5) * 5)
    fig, axes = plt.subplots(1, 2, figsize=(W, W * 0.62), sharex=True, sharey=True)
    panels = ((axes[0], np.where(inside, base, np.nan), seq, plt.Normalize(0, vmax), "Days deeper than 40 cm, baseline (days)", "neither"),
              (axes[1], np.where(inside, chg, np.nan), div, TwoSlopeNorm(0, -lim, lim), "Change with blocks (days; negative = wetter)", "both"))
    for i, (ax, arr, cmap, norm, lab, extend) in enumerate(panels):
        ax.imshow(grey, extent=ext, cmap=ListedColormap([HELD]), interpolation="nearest")
        im = ax.imshow(arr, extent=ext, cmap=cmap, norm=norm, interpolation="nearest")
        units.boundary.plot(ax=ax, color="#7a7975", linewidth=0.4)
        khg.boundary.plot(ax=ax, color=INK, linewidth=1.0)
        km_axes(ax, crs_name(crs), ylabel=(i == 0))
        ax.xaxis.label.set_size(8)
        if i:
            ax.set_ylabel("")
        cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.05, pad=0.13, extend=extend)
        cb.set_label(lab, fontsize=8); cb.ax.tick_params(labelsize=7.5)
        b = khg.total_bounds
        ax.set_xlim(b[0] - 1500, b[2] + 1500); ax.set_ylim(b[1] - 1500, b[3] + 1500)
    north_arrow(axes[1], 0.9, 0.95)
    fig.legend(handles=[Patch(color=HELD, label="Managed land and canal cells (level held)"),
                        Line2D([], [], color="#7a7975", lw=0.6, label="Sub-KHG units")],
               loc="lower center", ncol=2, fontsize=7.5, bbox_to_anchor=(0.5, -0.06))
    return save(fig, "model_days_map_mendahara")


FINAL_RUN = "tropical-large_p0.8_s0.3_t0.3_mt0.4_lk_scr_e0.3_{res}m_pb_dbbsdlp"
FINAL_KHG = (("16.02.01", "Sugihan-Lumpur", 200), ("14.02-04-05.01", "Kampar-Gaung", 200), ("15.05-07-10.01", "Mendahara-Batanghari", 100))


def model_days_maps_final():
    """model_season_days_deeper_40cm.tif of the recommended run (FINAL_RUN: canals inside cells at the LiDAR levels, managed land held
    at 0.4 m, screened stations) in _khg/<KHG>/03_neraca/lidar/runs/model/, and 00_inputs/khg.gpkg, for the three KHG of FINAL_KHG."""
    import geopandas as gpd
    import rasterio
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap
    from matplotlib.patches import Patch
    from rasterio.features import geometry_mask
    seq = LinearSegmentedColormap.from_list("seq", ["#f4f8fd", BLUE_RAMP[250], BLUE_RAMP[450], BLUE_RAMP[650], "#0d366b"])
    fig, axes = plt.subplots(1, 3, figsize=(W, W * 0.5))
    for ax, (code, name, res) in zip(axes, FINAL_KHG):
        f = folder(code)
        with rasterio.open(neraca_dir(code) / "lidar/runs/model" / FINAL_RUN.format(res=res) / "model_season_days_deeper_40cm.tif") as ds:
            a, tr, crs = ds.read(1).astype(float), ds.transform, ds.crs
            ext = (ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top)
            if ds.nodata is not None:
                a[a == ds.nodata] = np.nan
        khg = gpd.read_file(f / "00_inputs/khg.gpkg").to_crs(crs)
        inside = geometry_mask(khg.geometry, a.shape, tr, invert=True)
        a[~np.isfinite(a) | (a < 0)] = np.nan
        ax.imshow(np.where(inside & np.isnan(a), 1.0, np.nan), extent=ext, cmap=ListedColormap([HELD]), interpolation="nearest")
        im = ax.imshow(np.where(inside, a, np.nan), extent=ext, cmap=seq, vmin=0, vmax=122, interpolation="nearest")
        khg.boundary.plot(ax=ax, color=INK, linewidth=0.8)
        b = khg.total_bounds
        ax.set_xlim(b[0] - 1000, b[2] + 1000); ax.set_ylim(b[1] - 1000, b[3] + 1000)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel("")
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(f"{name}, {res} m", fontsize=8.5)
        ax.set_aspect("equal")
    cb = fig.colorbar(im, ax=axes, orientation="horizontal", fraction=0.05, pad=0.04, aspect=40)
    cb.set_label("Days with the water table deeper than 40 cm, June to September 2026 (of 122)", fontsize=8); cb.ax.tick_params(labelsize=7.5)
    fig.legend(handles=[Patch(color=HELD, label="Managed land held at 0.4 m, and fixed cells")], loc="lower center", fontsize=7.5,
               bbox_to_anchor=(0.5, -0.08))
    return save(fig, "model_days_maps_final")


def distance_table(md: Path):
    """First 'By distance from the block reaches' table of a scenario report and the depth of its unblocked canals."""
    lines = md.read_text(encoding="utf-8").splitlines()
    head = next(l for l in lines if l.startswith("## "))
    depth = re.search(r"_p([\d.]+)_", head).group(1)
    i = next(k for k, l in enumerate(lines) if l.startswith("By distance from the block reaches"))
    rows = []
    for l in lines[i + 1:]:
        if l.startswith("|"):
            rows.append([c.strip() for c in l.strip().strip("|").split("|")])
        elif rows:
            break
    t = pd.DataFrame(rows[2:], columns=rows[0])
    t["band"] = t.iloc[:, 0].str.replace("–", "-", regex=False)
    t["change"] = t["mean change (days)"].astype(float)
    t["better"] = t["cells at least 10 days better"]
    return float(depth), t


def model_days_by_distance():
    """repeat-neraca/docs/reports/scenarios_15.05-07-10.01_canals1.2.md and scenarios_15.05-07-10.01.md: first table
    'By distance from the block reaches' (mean change (days), cells at least 10 days better)."""
    rep = WORKSPACE / "repeat-neraca/docs/reports"
    series = [distance_table(rep / "scenarios_15.05-07-10.01_canals1.2.md"), distance_table(rep / "scenarios_15.05-07-10.01.md")]
    fig, ax = plt.subplots(figsize=(W, W * 0.45))
    off = {0: -0.12, 1: 0.12}
    for k, ((depth, t), col) in enumerate(zip(series, (SERIES[0], SERIES[1]))):
        x = np.arange(len(t)) + off[k]
        ax.vlines(x, 0, t.change, color=col, lw=1.4)
        ax.scatter(x, t.change, s=36, color=col, zorder=3, label=f"Unblocked canals outside licences {depth:g} m below surface")
        for xi, yi, lab in zip(x, t.change, t.better):
            ax.annotate(lab, (xi, yi), xytext=(0, -9), textcoords="offset points", ha="center", va="top", fontsize=7.5, color=col)
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(range(len(series[0][1])), series[0][1].band)
    ax.set_xlabel("Distance from a block reach")
    ax.set_ylabel("Mean change in days\ndeeper than 40 cm")
    lo = min(t.change.min() for _, t in series)
    ax.set_ylim(lo * 1.3, 3)
    ax.grid(axis="x", visible=False)
    lg = ax.legend(loc="lower right", fontsize=7.5, title="Labels: share of cells at least 10 days better", title_fontsize=7.5)
    lg._legend_box.align = "left"
    return save(fig, "model_days_by_distance")


# --- chapter 9 --------------------------------------------------------------------------------------------------------
def scaled(v, d):
    return float(v) / d if isnum(v) else np.nan


def pump_report(code: str, dem: str):
    p = folder(code) / "05_pump" / dem / "run_report.json"
    return (read_json(p), p) if p.exists() else (None, p)


def interventions_cross_khg() -> pd.DataFrame:
    """_khg/<folder>/05_pump/<dem>/run_report.json: sekat_balance (head_rule, kept), counts['7'] (existing, unsnapped),
    pumps[].units_needed, interventions (held_m3_selected, deficit_m3_selected), budget (total_low_idr, total_idr,
    total_high_idr); run date = file modification date (the report holds no date)."""
    from datetime import datetime
    order = ["16.02.01", "14.02-04-05.01", "15.05-07-10.01", "16.02-07.01"]
    rows = []
    for code in order:
        for dem in DEMS:
            r, p = pump_report(code, dem)
            if not r:
                rows.append({"KHG": COMPLETED[code], "DTM": DEM_LABEL[dem]}); continue
            sb, c7, iv, bg = r["sekat_balance"], r["counts"]["7"], r.get("interventions", {}), r.get("budget", {})
            pumps = sum(int(x.get("units_needed") or 0) for x in (r.get("pumps") or []))
            rows.append({"KHG": COMPLETED[code], "DTM": dem_label(code, dem),
                         "Blocks, head rule / kept (n)": f"{sb['head_rule']:,} / {sb['kept']:,}",
                         "Existing blocks on analysed canals (n)": f"{c7['existing'] - c7['unsnapped']:,}",
                         "Pump units (n)": pumps,
                         "Water held (million m³)": fmt(scaled(iv.get("held_m3_selected"), 1e6), 2),
                         "Deficit (million m³)": fmt(scaled(iv.get("deficit_m3_selected"), 1e6), 1),
                         "Budget low / central / high (billion Rp)": " / ".join(fmt(scaled(bg.get(k), 1e9)) for k in ("total_low_idr", "total_idr", "total_high_idr")),
                         "Run date": datetime.fromtimestamp(p.stat().st_mtime).strftime("%d %b %Y")})
    out = pd.DataFrame(rows).fillna("-")
    out.attrs["note"] = ("Three highest-ranked sub-KHG per run, proposed defaults. Existing blocks: existing structures minus those "
                         "not snapped to an analysed canal. Run date: date the run report was written. Default weights, proposed for "
                         "agreement with KLH and the World Bank.")
    return out


def interventions_blocks_by_dem():
    """_khg/<folder>/05_pump/<dem>/run_report.json, sekat_balance.head_rule and sekat_balance.kept."""
    order = ["16.02.01", "14.02-04-05.01", "15.05-07-10.01", "16.02-07.01"]
    fig, ax = plt.subplots(figsize=(W, W * 0.45))
    bw = 0.26
    for g, code in enumerate(order):
        for j, dem in enumerate(DEMS):
            r, _ = pump_report(code, dem)
            x = g + (j - 1) * (bw + 0.03)
            if not r:
                ax.text(x, 0, "n/a", ha="center", va="bottom", fontsize=7.5, color=MUTED); continue
            hr, kept = r["sekat_balance"]["head_rule"], r["sekat_balance"]["kept"]
            ax.bar(x, hr, bw, color=DEM_COLOR[dem], alpha=0.35, linewidth=0)
            ax.bar(x, kept, bw, color=DEM_COLOR[dem], linewidth=0)
            ax.text(x, hr, f"{hr:,}", ha="center", va="bottom", fontsize=6.5, color=INK)
            if kept < hr * 0.85:
                ax.text(x, kept, f"{kept:,}", ha="center", va="bottom", fontsize=6.5, color=INK)
    ticks = [COMPLETED[c] + (f"\n({dem_label(c, 'lidar')})" if dem_label(c, "lidar") != "LiDAR" else "") for c in order]
    ax.set_xticks(range(len(order)), ticks)
    ax.set_ylabel("Canal blocks (n)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.grid(axis="x", visible=False)
    from matplotlib.patches import Patch
    h = [Patch(color=DEM_COLOR[d], label=DEM_LABEL[d]) for d in DEMS]
    h += [Patch(color=MUTED, alpha=0.35, label="light: head rule"), Patch(color=MUTED, label="solid: kept")]
    ax.legend(handles=h, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.12), fontsize=7.5)
    return save(fig, "interventions_blocks_by_dem")


REGISTRY: dict = {"selected_khg": selected_khg,
                  "khg_data_recap": khg_data_recap, "khg_dem_inputs": khg_dem_inputs, "dem_coverage": dem_coverage,
                  "subkhg_units": subkhg_units, "subkhg_map_sugihan_lumpur": subkhg_map_sugihan_lumpur,
                  "national_rank_map": national_rank_map, "national_top20": national_top20,
                  "national_yearly": national_yearly, "national_selected": national_selected,
                  "national_stage3": national_stage3, "national_overlay": national_overlay,
                  "subkhg_maps_sugihan_lumpur": subkhg_maps_sugihan_lumpur, "subkhg_top_sugihan_lumpur": subkhg_top_sugihan_lumpur,
                  "subkhg_classes_by_khg_dem": subkhg_classes_by_khg_dem, "subkhg_dem_agreement": subkhg_dem_agreement,
                  "neraca_rain_et_dekadal": neraca_rain_et_dekadal, "neraca_station_depth_2026": neraca_station_depth_2026,
                  "neraca_calendar": neraca_calendar, "neraca_units_kampar_gaung": neraca_units_kampar_gaung,
                  "neraca_units_mendahara_batanghari": neraca_units_mendahara_batanghari,
                  "neraca_units_saleh_sugihan": neraca_units_saleh_sugihan, "neraca_units_sugihan_lumpur": neraca_units_sugihan_lumpur,
                  "model_station_fit_sugihan_lumpur": model_station_fit_sugihan_lumpur,
                  "model_days_map_mendahara": model_days_map_mendahara, "model_days_by_distance": model_days_by_distance,
                  "model_community_mendahara": model_community_mendahara, "model_days_maps_final": model_days_maps_final,
                  "interventions_cross_khg": interventions_cross_khg, "interventions_blocks_by_dem": interventions_blocks_by_dem}
