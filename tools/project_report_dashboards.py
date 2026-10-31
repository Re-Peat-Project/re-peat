"""Figures and tables of the project report drawn from the data behind the SiTMAT explorer and the national dashboard.

REGISTRY maps the placeholder id used in the chapter Markdown to its function (see project_report.py).

SiTMAT: the methods of repeat-sitmat/assets/js/data.js, overview.js, insights.js and regions.js are reproduced here at the
explorer's default settings (flagged readings dropped, panel = stations reporting in at least 60 % of the weeks and with
a start level, regional series need 2 stations, national series 5). Inputs: repeat-sitmat/sitmat_out/processed/
daily_long.csv, stations.csv, stations_geo.csv.

National: the scoring of repeat-prioritisation/src/repeat_prioritisation/national/assets/dashboard.js (compute()) is
reproduced on re-peat/reports/national_profile/dashboard_data.json and checked against the Python ranks (ref_rank).

`python project_report_dashboards.py numbers` prints every number the draft text quotes.
"""
from __future__ import annotations

import json
import sys
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import project_report_figures as F  # noqa: E402

plt = F.plt
WS = F.WORKSPACE
SITMAT = WS / "repeat-sitmat/sitmat_out/processed"
GEO = WS / "repeat-sitmat/assets/geo"
NAT = WS / "re-peat/reports/national_profile"

# =====================================================================================================================
# SiTMAT explorer: data model (data.js)
# =====================================================================================================================
THRESH, DEEP = -40.0, -80.0
MIN_WEEK_DAYS, BASE_WEEKS, MIN_COV = 3, 4, 0.6
COMM_FIRST = "2026-07-21"          # first day with a community reading
KIND_COLOR = {"concession": F.SERIES[0], "community": F.SERIES[1]}
KIND_LABEL = {"concession": "Concession", "community": "Community"}


@cache
def _raw():
    d = pd.read_csv(SITMAT / "daily_long.csv", dtype={"flag": str})
    st = pd.read_csv(SITMAT / "stations.csv")
    geo = pd.read_csv(SITMAT / "stations_geo.csv")
    dates = np.array(sorted(d.date.unique()), dtype=object)
    st = st.merge(geo, on=["kind", "station_id"], how="left")
    st["has_loc"] = st.lon.between(94, 142) & st.lat.between(-12.5, 7)      # data.js build(): inside Indonesia
    for c in ("adm1", "khg_name"):
        st.loc[~st.has_loc, c] = np.nan
    st.loc[~st.has_loc, "khg_id"] = np.nan
    # stations in daily_long but not in stations.csv are kept, as in data.js
    extra = d[["kind", "station_id"]].drop_duplicates().merge(st[["kind", "station_id"]], how="left", indicator=True)
    extra = extra[extra._merge == "left_only"].drop(columns="_merge")
    st = pd.concat([st, extra], ignore_index=True).reset_index(drop=True)
    key = st.kind + "|" + st.station_id
    idx = pd.Series(range(len(st)), index=key.values)
    di = pd.Series(range(len(dates)), index=dates)
    wl = np.full((len(st), len(dates)), np.nan)
    flag = np.zeros((len(st), len(dates)), bool)
    r = idx[(d.kind + "|" + d.station_id).values].values
    c = di[d.date.values].values
    wl[r, c] = d.water_level_cm.values
    flag[r, c] = d.flag.fillna("").values != ""
    return st, dates, wl, flag


def _theil_sen(xs, ys):
    """Theil-Sen slope and tie-corrected Mann-Kendall z, as data.js theilSen()."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    n = len(xs)
    i, j = np.triu_indices(n, 1)
    dy = ys[j] - ys[i]
    slope = float(np.median(dy / (xs[j] - xs[i])))
    s = float(np.sign(dy).sum())
    _, t = np.unique(ys, return_counts=True)
    v = (n * (n - 1) * (2 * n + 5) - (t * (t - 1) * (2 * t + 5))[t > 1].sum()) / 18
    z = (s - np.sign(s)) / np.sqrt(v) if v > 0 else 0.0
    return slope, z, abs(z) >= 1.96


def _edge_mean(a, weeks, k, from_end):
    v = [a[w] for w in (weeks[::-1] if from_end else weeks) if np.isfinite(a[w])][:k]
    return float(np.mean(v)) if v else np.nan


@cache
def derive(kind: str, d0: str | None = None, d1: str | None = None) -> dict:
    """deriveStations() + selectPop() of data.js for one station kind over the days d0..d1 (default: all)."""
    st, dates, wl, flag = _raw()
    i0 = 0 if d0 is None else int(np.searchsorted(dates, d0))
    i1 = len(dates) - 1 if d1 is None else int(np.searchsorted(dates, d1))
    nd = len(dates)
    nw = (nd - 1) // 7 + 1
    val = np.where(flag, np.nan, wl)                                   # QC toggle on: flagged readings dropped
    bin_days = np.bincount(np.arange(i0, i1 + 1) // 7, minlength=nw)
    weeks = [w for w in range(nw) if bin_days[w] >= MIN_WEEK_DAYS]
    sel = np.where(st.kind.values == kind)[0]
    v = val[sel]
    wk = np.full((len(sel), nw), np.nan)
    for w in weeks:
        a, b = max(i0, w * 7), min(i1, w * 7 + 6)
        blk = v[:, a:b + 1]
        ok = np.isfinite(blk).sum(1) >= MIN_WEEK_DAYS
        with np.errstate(all="ignore"):
            wk[ok, w] = np.nanmedian(blk[ok], axis=1)
    nv = np.isfinite(wk[:, weeks]).sum(1)
    cov = nv / len(weeks)
    first = wk[:, weeks[:BASE_WEEKS]]
    with np.errstate(all="ignore"):
        base = np.where(np.isfinite(first).sum(1) >= 2, np.nanmedian(np.where(np.isfinite(first).any(1)[:, None], first, 0), axis=1), np.nan)
    anom = wk - base[:, None]
    rng = v[:, i0:i1 + 1]
    with np.errstate(all="ignore"):
        mean = np.nanmean(rng, axis=1)
    slope = np.full(len(sel), np.nan); z = np.full(len(sel), np.nan); sig = np.zeros(len(sel), bool)
    for k in range(len(sel)):
        xs = [w for w in weeks if np.isfinite(wk[k, w])]
        if len(xs) >= 8:
            slope[k], z[k], sig[k] = _theil_sen(xs, wk[k, xs])
    now = np.array([_edge_mean(wk[k], weeks, 2, True) for k in range(len(sel))])
    df = st.iloc[sel].reset_index(drop=True).copy()
    df = df.assign(nv=nv, cov=cov, base=base, mean=mean, slope=slope, z=z, sig=sig, now=now, change=now - base,
                   n_days=np.isfinite(rng).sum(1))
    df["panel"] = (df["cov"] >= MIN_COV) & df.base.notna()
    return {"st": df, "wk": wk, "anom": anom, "val": rng, "weeks": weeks, "dates": dates, "i0": i0, "i1": i1,
            "kind": kind, "week_start": [dates[min(nd - 1, w * 7)] for w in range(nw)]}


@cache
def comm_start() -> str:
    """Start of the community series: the first weekly bin from which, in every later bin, at least half of the community
    stations that have any weekly median report one. July readings come from a few stations, many of them at a
    placeholder level of +1 to +2 cm, followed by a gap, so a baseline set in July would measure the restart."""
    D = derive("community", COMM_FIRST)
    has = np.isfinite(D["wk"])
    n_any = int(has.any(1).sum())
    cnt = [int(has[:, w].sum()) for w in D["weeks"]]
    ok = [all(c >= n_any / 2 for c in cnt[k:]) for k in range(len(cnt))]
    w = D["weeks"][ok.index(True)]
    return str(D["dates"][w * 7])


def stuck(D) -> pd.Series:
    """Panel stations whose weekly medians never change (one value through the window): a stuck logger."""
    w = D["wk"][:, D["weeks"]]
    with np.errstate(all="ignore"):
        rng = np.nanmax(w, 1) - np.nanmin(w, 1)
    return pd.Series((rng == 0) & D["st"].panel.values, index=D["st"].index)


def weekly_series(D, rows, field="anom", min_n=5):
    """weeklySeries(): median and quartiles across stations per week (NaN where fewer than min_n report)."""
    a = D[field][rows]
    out = {k: np.full(a.shape[1], np.nan) for k in ("med", "q1", "q3")}
    out["n"] = np.zeros(a.shape[1], int)
    for w in D["weeks"]:
        x = a[:, w][np.isfinite(a[:, w])]
        out["n"][w] = len(x)
        if len(x) >= min_n:
            out["med"][w], out["q1"][w], out["q3"][w] = np.quantile(x, [0.5, 0.25, 0.75])
    return out


def class_shares(D, rows, min_n=5):
    """classShares(): share of reporting stations at or above -40 cm, -40 to -80 cm, below -80 cm per week (%)."""
    a = D["wk"][rows]
    out = {k: np.full(a.shape[1], np.nan) for k in ("ok", "mid", "bad", "below")}
    out["n"] = np.zeros(a.shape[1], int)
    for w in D["weeks"]:
        x = a[:, w][np.isfinite(a[:, w])]
        out["n"][w] = len(x)
        if len(x) >= min_n:
            out["ok"][w] = (x >= THRESH).mean() * 100
            out["mid"][w] = ((x < THRESH) & (x >= DEEP)).mean() * 100
            out["bad"][w] = (x < DEEP).mean() * 100
            out["below"][w] = (x < THRESH).mean() * 100
    return out


def trend_of(D, series, min_pts=8):
    xs = [w for w in D["weeks"] if np.isfinite(series[w])]
    return _theil_sen(xs, series[xs]) if len(xs) >= min_pts else (np.nan, np.nan, False)


def overview(D) -> dict:
    """KPIs of the Overview tab (overview.js renderOverview)."""
    s = D["st"]
    p = s.panel.values
    an, sh = weekly_series(D, p), class_shares(D, p)
    slope, z, sig = trend_of(D, an["med"])
    sl = s[p & s.slope.notna()]
    return {"panel": int(p.sum()), "with_data": int((s.nv > 0).sum()),
            "change": _edge_mean(an["med"], D["weeks"], 4, True), "slope": slope, "z": z, "sig": sig,
            "below_start": _edge_mean(sh["below"], D["weeks"], 2, False), "below_end": _edge_mean(sh["below"], D["weeks"], 2, True),
            "deep_start": _edge_mean(sh["bad"], D["weeks"], 2, False), "deep_end": _edge_mean(sh["bad"], D["weeks"], 2, True),
            "drying": (sl.sig & (sl.slope < 0)).mean() * 100, "wetting": (sl.sig & (sl.slope > 0)).mean() * 100,
            "n_slope": len(sl), "an": an, "sh": sh}


def region_stats(D, col="adm1", min_n=2) -> pd.DataFrame:
    """regionStats(): per region, all stations of the kind and the panel inside it."""
    s = D["st"]
    rows = []
    for key, g in s[s[col].notna()].groupby(col):
        m = s.index.isin(g.index)
        pm = m & s.panel.values
        an = weekly_series(D, pm, min_n=min_n)
        lev = weekly_series(D, m, "wk", min_n=min_n)
        sh = class_shares(D, m, min_n=min_n)
        slope, z, sig = trend_of(D, an["med"]) if pm.sum() >= min_n else (np.nan, np.nan, False)
        sl = s[pm & s.slope.notna()]
        rows.append({col: key, "n": int((g.nv > 0).sum()), "nP": int(pm.sum()), "slope": slope, "z": z, "sig": sig,
                     "cur_level": _edge_mean(lev["med"], D["weeks"], 4, True),
                     "cur_change": _edge_mean(an["med"], D["weeks"], 4, True),
                     "start_below": _edge_mean(sh["below"], D["weeks"], 2, False),
                     "cur_below": _edge_mean(sh["below"], D["weeks"], 2, True),
                     "drying": (sl.sig & (sl.slope < 0)).mean() * 100 if len(sl) else np.nan,
                     "st_q1": sl.slope.quantile(0.25) if len(sl) else np.nan,
                     "st_q3": sl.slope.quantile(0.75) if len(sl) else np.nan})
    return pd.DataFrame(rows)


def pooled(D, rows, a, b):
    """pooled(): sorted daily readings of the stations over days a..b (indices into the range)."""
    x = D["val"][rows][:, a:b + 1]
    return np.sort(x[np.isfinite(x)])


def share_below(x, lim):
    return np.searchsorted(x, lim, side="left") / len(x) * 100 if len(x) else np.nan


def longest_spell(v, lim=THRESH, gap=2):
    """longestSpell(): longest run of days below lim; up to `gap` missing days do not break a run."""
    best, start, last = 0, -1, -1
    for i, x in enumerate(v):
        if not np.isfinite(x):
            continue
        if x < lim:
            if start < 0 or i - last > gap + 1:
                start = i
            last = i
            best = max(best, last - start + 1)
        else:
            start = -1
    return best


def station_below_share(D, min_days=20):
    """Share of valid days below -40 cm per station (concessionStats(): stations with 20 or more valid days)."""
    v = D["val"]
    n = np.isfinite(v).sum(1)
    with np.errstate(all="ignore"):
        sh = (v < THRESH).sum(1) / n * 100
    s = D["st"].assign(n_valid=n, below=sh)
    return s[s.n_valid >= min_days]


def concession_stats(min_st=3) -> pd.DataFrame:
    """concessionStats() on concession stations, full period; concessions with at least min_st stations."""
    s = station_below_share(derive("concession"))
    g = s[s.company_code.notna()].groupby("company_code")
    out = pd.DataFrame({"n": g.size(), "share": g.below.mean(), "prov": g.adm1.agg(lambda x: x.value_counts().index[0] if x.notna().any() else "")})
    return out[out.n >= min_st]


def sharing(d0=None) -> pd.DataFrame:
    """renderSharing(): KHG with both kinds of station; mean of station mean levels per kind, days d0 to the end."""
    rows = []
    d0 = d0 or comm_start()
    for kind in ("concession", "community"):
        s = derive(kind, d0)["st"]
        s = s[s.khg_id.notna() & s["mean"].notna()]
        rows.append(s.assign(kind=kind)[["kind", "khg_id", "khg_name", "adm1", "mean"]])
    a = pd.concat(rows)
    g = a.groupby(["khg_id", "kind"])["mean"].agg(["mean", "size"]).unstack("kind")
    g = g.dropna()
    names = a.drop_duplicates("khg_id").set_index("khg_id")
    g.columns = [f"{x}_{k}" for x, k in g.columns]
    return g.join(names[["khg_name", "adm1"]]).reset_index()


# =====================================================================================================================
# SiTMAT figures and tables
# =====================================================================================================================
def _date_axis(ax, last="2026-10-31"):
    """Month ticks up to the end of the record only (room on the right is for direct labels)."""
    import matplotlib.dates as mdates
    lo = mdates.num2date(ax.get_xlim()[0]).replace(tzinfo=None)
    ticks = [t for t in pd.date_range("2026-04-01", last, freq="MS") if t >= lo - pd.Timedelta(days=1)]
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))


def _wdates(D, series):
    w = [x for x in D["weeks"] if np.isfinite(series[x])]
    return pd.to_datetime([D["week_start"][x] for x in w]) + pd.Timedelta(days=3), w   # plotted at mid-week


# drier = darker, one hue (orange ramp of the validated palette family), five ordinal steps
DRY_RAMP = ["#fbe3d6", "#f5b896", "#eb6834", "#b84a1d", "#7a2e10"]
DRY_EDGES = [0, 20, 40, 60, 80, 100.001]
MAP_CRS = "EPSG:3395"          # World Mercator: scale error under 0.6 % within 6 degrees of the equator


def _station_layer():
    """Stations with a location and 20 or more valid days in their kind's window: share of days below -40 cm."""
    out = []
    for kind, d0 in (("concession", None), ("community", comm_start())):
        s = station_below_share(derive(kind, d0))
        out.append(s[s.has_loc].assign(kind=kind))
    return pd.concat(out, ignore_index=True)


def sitmat_station_map():
    """repeat-sitmat/sitmat_out/processed/daily_long.csv, stations.csv: share of valid days below -40 cm per station
    (concession 1 April to 22 October, community from comm_start()); context: assets/geo/adm1.geojson and
    _data/batas_khg_indonesia.gpkg."""
    import geopandas as gpd
    from matplotlib.lines import Line2D
    s = _station_layer()
    box = (95.0, -4.6, 119.2, 5.9)
    s = s[s.lon.between(box[0], box[2]) & s.lat.between(box[1], box[3])]
    pts = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.lon, s.lat), crs=4326).to_crs(MAP_CRS)
    adm = gpd.read_file(GEO / "adm1.geojson").to_crs(MAP_CRS)
    khg = gpd.read_file(WS / "_data/batas_khg_indonesia.gpkg", bbox=box).to_crs(MAP_CRS)
    fig, ax = plt.subplots(figsize=(F.W, F.W * 0.56))
    adm.plot(ax=ax, color="#f1f0ec", edgecolor="#c9c8c2", linewidth=0.3)
    khg.plot(ax=ax, facecolor="#e3e2dc", edgecolor="#a9a8a2", linewidth=0.25)
    cls = np.digitize(pts.below, DRY_EDGES) - 1
    for kind, mk, sz in (("concession", "o", 7), ("community", "^", 22)):
        m = (pts.kind == kind).values
        ax.scatter(pts.geometry.x[m], pts.geometry.y[m], c=[DRY_RAMP[c] for c in cls[m]], marker=mk, s=sz,
                   edgecolors=F.INK if kind == "community" else "none", linewidths=0.4, zorder=3 if kind == "concession" else 4)
    x0, y0, x1, y1 = gpd.GeoSeries.from_xy([box[0], box[2]], [box[1], box[3]], crs=4326).to_crs(MAP_CRS).total_bounds
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    F.km_axes(ax, "World Mercator")
    F.north_arrow(ax, 0.97, 0.95)
    h = [Line2D([], [], marker="s", ls="", mfc=c, mec="none", ms=6, label=l)
         for c, l in zip(DRY_RAMP, ["under 20 %", "20-40 %", "40-60 %", "60-80 %", "80 % or more"])]
    h += [Line2D([], [], marker="o", ls="", mfc="#ffffff", mec=F.INK, mew=0.6, ms=4, label=f"Concession ({int((pts.kind == 'concession').sum()):,})"),
          Line2D([], [], marker="^", ls="", mfc="#ffffff", mec=F.INK, mew=0.6, ms=5, label=f"Community ({int((pts.kind == 'community').sum())})")]
    ax.legend(handles=h, title="Share of days with the water table below -40 cm", loc="upper left", bbox_to_anchor=(0, -0.2),
              fontsize=7.5, title_fontsize=7.5, ncol=4, alignment="left", columnspacing=1.2, handletextpad=0.3)
    return F.save(fig, "sitmat_station_map")


def sitmat_change():
    """Median change of the panel stations against each station's own first 4 weeks, with the middle 50 % of stations
    (overview.js 'change in water level since start'). Left: concession, whole season. Right: both kinds from comm_start()."""
    c0 = comm_start()
    fig, (a, b) = plt.subplots(1, 2, figsize=(F.W, F.W * 0.42), sharey=True, gridspec_kw={"width_ratios": [2.1, 1]})
    lab = []
    for ax, runs in ((a, [("concession", None)]), (b, [("concession", c0), ("community", c0)])):
        for kind, d0 in runs:
            D = derive(kind, d0)
            o = overview(D)
            x, w = _wdates(D, o["an"]["med"])
            col = KIND_COLOR[kind]
            ax.fill_between(x, o["an"]["q1"][w], o["an"]["q3"][w], color=col, alpha=0.16, lw=0)
            ax.plot(x, o["an"]["med"][w], color=col, lw=1.6)
            if ax is b:
                lab.append((x[-1], o["an"]["med"][w][-1], f"{KIND_LABEL[kind]}, {o['panel']}", col))
            else:
                F.direct_label(ax, x[-1], o["an"]["med"][w][-1], f"{o['panel']} stations", col)
        ax.plot([x[0] - pd.Timedelta(days=4), x[-1]], [0, 0], color=F.MUTED, lw=0.8, zorder=1)
    a.set_title("Concession stations, April to October", loc="left")
    b.set_title(f"Both kinds, from {pd.Timestamp(c0):%d %B}", loc="left")
    a.set_ylabel("Change against the station's\nown first 4 weeks (cm)")
    a.text(0.01, 0.97, "shaded: middle 50 % of stations", transform=a.transAxes, fontsize=7.5, color=F.MUTED, va="top")
    b.set_xlim(None, pd.Timestamp("2026-11-20"))
    a.set_xlim(None, pd.Timestamp("2026-11-15"))
    _date_axis(a); _date_axis(b)
    fig.tight_layout()
    F.end_labels(b, lab)
    return F.save(fig, "sitmat_change")


def sitmat_share_below():
    """Share of panel stations whose weekly median is below -40 cm and below -80 cm (classShares of overview.js)."""
    c0 = comm_start()
    fig, axes = plt.subplots(1, 2, figsize=(F.W, F.W * 0.4), sharey=True)
    for ax, key, title in ((axes[0], "below", "Below -40 cm"), (axes[1], "bad", "Below -80 cm")):
        lab = []
        for kind, d0 in (("concession", None), ("community", c0)):
            D = derive(kind, d0)
            o = overview(D)
            x, w = _wdates(D, o["sh"][key])
            ax.plot(x, o["sh"][key][w], color=KIND_COLOR[kind], lw=1.6)
            lab.append((x[-1], o["sh"][key][w][-1], f"{KIND_LABEL[kind]}, {o['panel']}", KIND_COLOR[kind]))
        ax.set_title(title, loc="left")
        ax.set_ylim(0, 100)
        ax.set_xlim(None, pd.Timestamp("2026-12-05"))
        _date_axis(ax)
        ax._lab = lab
    axes[0].set_ylabel("Panel stations (%)")
    fig.tight_layout(w_pad=5)
    for ax in axes:
        F.end_labels(ax, ax._lab)
    return F.save(fig, "sitmat_share_below")


MIN_PROV_PANEL = 5


def sitmat_province_trend():
    """Trend of the provincial median change (Theil-Sen, cm per week; filled = Mann-Kendall significant at 95 %) and the
    middle 50 % of the station trends, concession panel stations, 1 April to 22 October (regionStats of data.js)."""
    r = region_stats(derive("concession"))
    r = r[r.nP >= MIN_PROV_PANEL].sort_values("slope")
    fig, ax = plt.subplots(figsize=(F.W, 0.32 * len(r) + 0.7))
    y = np.arange(len(r))
    ax.hlines(y, r.st_q1, r.st_q3, color=F.NEUTRAL, lw=3.2, zorder=2)
    col = np.where(r.slope < 0, F.SERIES[1], F.SERIES[0])
    ax.scatter(r.slope, y, s=34, c=np.where(r.sig, col, "#ffffff"), edgecolors=col, linewidths=1.3, zorder=3)
    ax.axvline(0, color=F.MUTED, lw=0.8)
    ax.set_yticks(y, [f"{a}  ({b})" for a, b in zip(r.adm1, r.nP)])
    ax.tick_params(axis="y", length=0, labelsize=8)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Trend of the water level, cm per week (negative: falling)")
    ax.text(1, 1.01, "dot: provincial median   bar: middle 50 % of stations   hollow: not significant", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7.5, color=F.MUTED)
    fig.tight_layout()
    return F.save(fig, "sitmat_province_trend")


def duration_parts(kind, d0=None):
    """First and last third of the window: (label, sorted pooled readings) for the panel stations."""
    D = derive(kind, d0)
    p = D["st"].panel.values
    n = D["i1"] - D["i0"] + 1
    third = max(7, n // 3)
    da, db = pd.Timestamp(str(D["dates"][D["i0"]])), pd.Timestamp(str(D["dates"][D["i1"]]))
    return D, p, [(f"{da:%d %b}-{da + pd.Timedelta(days=third - 1):%d %b}", pooled(D, p, 0, third - 1)),
                  (f"{db - pd.Timedelta(days=third - 1):%d %b}-{db:%d %b}", pooled(D, p, n - third, n - 1))]


def sitmat_duration():
    """Duration curves of the pooled daily readings of the panel stations, first third against last third of the window
    (insights.js renderDuration). Left: concession, whole season. Right: community, from comm_start()."""
    fig, axes = plt.subplots(1, 2, figsize=(F.W, F.W * 0.45), sharey=True)
    for ax, kind, d0 in ((axes[0], "concession", None), (axes[1], "community", comm_start())):
        D, p, parts = duration_parts(kind, d0)
        pct = np.arange(0, 101)
        for i, ((lab, v), col, lw) in enumerate(zip(parts, (F.MUTED, KIND_COLOR[kind]), (1.3, 1.8))):
            ax.plot(pct, np.quantile(v, 1 - pct / 100), color=col, lw=lw)
            ax.text(3, -158 - 17 * i, f"{lab}: {share_below(v, THRESH):.0f} % below -40 cm", color=col, fontsize=7.5)
        for lim in (THRESH, DEEP):
            ax.axhline(lim, color=F.INK, lw=0.7, ls=(0, (4, 2)))
        ax.set_title(f"{KIND_LABEL[kind]}, {int(p.sum())} panel stations", loc="left")
        ax.set_xlim(0, 100)
        ax.set_xlabel("Share of readings at or above the level (%)")
    for lim in (THRESH, DEEP):
        axes[1].text(101, lim, f"{lim:.0f} cm", fontsize=7.5, color=F.INK, va="center", ha="left")
    axes[0].set_ylim(-200, 40)
    axes[0].set_ylabel("Water level (cm, 0 = surface)")
    fig.tight_layout()
    return F.save(fig, "sitmat_duration")


SPELL_BINS = [(0, 0, "never"), (1, 7, "1-7"), (8, 14, "8-14"), (15, 30, "15-30"), (31, 60, "31-60"), (61, 90, "61-90"),
              (91, 120, "91-120"), (121, 10**9, "over 120")]


def spells(kind="concession", d0=None) -> pd.Series:
    D = derive(kind, d0)
    p = D["st"].panel.values
    return pd.Series([longest_spell(v) for v in D["val"][p]])


def sitmat_dry_spell():
    """Longest run of days below -40 cm per concession panel station, 1 April to 22 October; gaps of up to 2 days do not
    break a run (insights.js renderSpells)."""
    sp = spells()
    n = [int(((sp >= a) & (sp <= b)).sum()) for a, b, _ in SPELL_BINS]
    fig, ax = plt.subplots(figsize=(F.W, F.W * 0.36))
    x = np.arange(len(n))
    ax.bar(x, n, width=0.86, color=[F.NEUTRAL] + [F.SERIES[1]] * (len(n) - 1), edgecolor="#ffffff", linewidth=1)
    for xi, v in zip(x, n):
        ax.text(xi, v, f"{v}", ha="center", va="bottom", fontsize=7.5, color=F.INK)
    ax.set_xticks(x, [b[2] for b in SPELL_BINS])
    ax.set_xlabel("Longest run of consecutive days below -40 cm")
    ax.set_ylabel("Panel stations")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return F.save(fig, "sitmat_dry_spell")


def sitmat_sharing():
    """KHG with both concession and community stations: mean of the station mean levels per kind, from comm_start() to
    22 October (regions.js renderSharing, same window for both kinds)."""
    g = sharing().sort_values("mean_community")
    fig, ax = plt.subplots(figsize=(F.W, 0.3 * len(g) + 0.9))
    y = np.arange(len(g))
    ax.hlines(y, g.mean_concession, g.mean_community, color=F.NEUTRAL, lw=1.6, zorder=1)
    for kind, mk in (("concession", "o"), ("community", "^")):
        ax.scatter(g[f"mean_{kind}"], y, s=30, marker=mk, color=KIND_COLOR[kind], edgecolors="#ffffff", linewidths=0.8,
                   zorder=3, label=KIND_LABEL[kind])
    ax.axvline(THRESH, color=F.INK, lw=0.7, ls=(0, (4, 2)))
    ax.text(THRESH + 2, len(g) - 0.4, "-40 cm", fontsize=7.5, color=F.INK, va="bottom")
    ax.set_yticks(y, [f"{F.short(a)}  ({int(b)} / {int(c)})" for a, b, c in zip(g.khg_name, g.size_concession, g.size_community)])
    ax.tick_params(axis="y", length=0, labelsize=7.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Mean water level (cm, 0 = surface)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, fontsize=7.5, handletextpad=0.2)
    ax.text(1, 1.01, "in brackets: concession / community stations", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7.5, color=F.MUTED)
    fig.tight_layout()
    return F.save(fig, "sitmat_sharing")


def sitmat_concessions():
    """Mean share of days below -40 cm per concession (stations with 20 or more valid days; concessions with 3 or more
    stations), 1 April to 22 October, by province (insights.js concessionStats). Concessions are not named."""
    c = concession_stats()
    c = c[c.prov != ""]
    order = c.groupby("prov").share.median().sort_values()
    order = order[c.prov.value_counts().reindex(order.index) >= 3]
    fig, ax = plt.subplots(figsize=(F.W, 0.34 * len(order) + 0.8))
    rng = np.random.default_rng(1)
    for i, pv in enumerate(order.index):
        v = c[c.prov == pv].share.values
        ax.scatter(v, i + rng.uniform(-0.18, 0.18, len(v)), s=14, color=F.SERIES[1], alpha=0.75, edgecolors="none", zorder=3)
        ax.plot([np.median(v)] * 2, [i - 0.32, i + 0.32], color=F.INK, lw=1.4, zorder=4)
    ax.set_yticks(range(len(order)), [f"{pv}  ({int((c.prov == pv).sum())})" for pv in order.index])
    ax.tick_params(axis="y", length=0, labelsize=8)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(-2, 102)
    ax.set_xlabel("Days with the water table below -40 cm, mean of the concession's stations (%)")
    ax.text(1, 1.01, "dot: one concession   bar: provincial median", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7.5, color=F.MUTED)
    fig.tight_layout()
    return F.save(fig, "sitmat_concessions")


def _report_value(text, pattern, cast=float):
    import re
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f"pattern not found: {pattern}")
    return [cast(x.replace(",", "")) for x in m.groups()]


def sitmat_quality() -> pd.DataFrame:
    """repeat-sitmat/sitmat_out/processed/qc_report.txt and repeat-sitmat/baseline_out/baseline_report.txt, both kinds."""
    qc = (SITMAT / "qc_report.txt").read_text(encoding="utf-8")
    bl = (WS / "repeat-sitmat/baseline_out/baseline_report.txt").read_text(encoding="utf-8")
    cols = {}
    for kind in ("community", "concession"):
        blk = qc.split(f"[{kind}]")[1].split("[")[0]
        n, start, days = _report_value(blk, r"stations with data: (\d+) \(coverage measured from (\S+), (\d+) days\)", str)
        cov, under = _report_value(blk, r"mean coverage: (\d+)%; stations under 50% coverage: (\d+)")
        rng = _report_value(blk, r"'range': (\d+)")[0]
        spk = _report_value(blk, r"'spike': (\d+)")[0]
        b = bl.split(f"[{kind}]")[1].split("[")[0]
        nv = _report_value(b, r"stations with any valid data: (\d+)")[0]
        kept = _report_value(b, r"kept: (\d+)")[0]
        med, sr = _report_value(b, r"median of station medians: (-?[\d.]+) cm; share of station-days in Sangat Rawan: (\d+)%")
        D = derive(kind, None if kind == "concession" else comm_start())
        cols[f"{KIND_LABEL[kind]} stations"] = [
            f"{int(n):,}", f"{int(days)} days from {pd.Timestamp(start):%d %B}", f"{cov:.0f} %", f"{int(under):,}",
            f"{int(rng)} / {int(spk)}", f"{int(kept)} of {int(nv):,}", f"{med:.1f} cm", f"{sr:.0f} %",
            f"{int(D['st'].panel.sum())} of {int((D['st'].nv > 0).sum()):,}"]
    out = pd.DataFrame(cols, index=[
        "Stations in the extract", "Period over which coverage is measured", "Mean coverage of days",
        "Stations under 50 % coverage", "Readings flagged out of range (below -500 or above +100 cm) / as spikes (jump over 60 cm)",
        "Stations kept in the cleaned baseline (to 14 October) / with valid data",
        "Median of station medians, cleaned baseline", "Station-days 80 cm or more below the surface, cleaned baseline",
        "Panel stations / stations with a weekly median, this chapter's analysis"]).reset_index(names="")
    out.attrs["note"] = ("Panel: stations with a weekly median in at least 60 % of the weeks and a start level; concession "
                         f"weeks 1 April to 22 October, community weeks from {pd.Timestamp(comm_start()):%d %B}.")
    return out


def sitmat_provinces() -> pd.DataFrame:
    """Compare tab of the explorer at province level (regions.js renderCompare), concession stations, 1 April to 22 October;
    provinces with at least MIN_PROV_PANEL panel stations; community stations counted from comm_start()."""
    r = region_stats(derive("concession"))
    r = r[r.nP >= MIN_PROV_PANEL].sort_values("slope")
    cm = derive("community", comm_start())["st"]
    nc = cm[cm.nv > 0].groupby("adm1").size()
    out = pd.DataFrame({
        "Province": r.adm1, "Concession stations (panel)": [f"{a} ({b})" for a, b in zip(r.n, r.nP)],
        "Level now (cm)": r.cur_level.map(lambda v: F.fmt(v, 0)),
        "Change since start (cm)": r.cur_change.map(lambda v: f"{v:+.1f}"),
        "Trend (cm per week)": [f"{a:+.2f}{'*' if s else ''}" for a, s in zip(r.slope, r.sig)],
        "Below -40 cm, start / now (% of stations)": [f"{F.fmt(a)} / {F.fmt(b)}" for a, b in zip(r.start_below, r.cur_below)],
        "Stations clearly falling (%)": r.drying.map(lambda v: F.fmt(v)),
        "Community stations": [str(int(nc.get(a, 0))) if nc.get(a, 0) else "-" for a in r.adm1]})
    out.attrs["note"] = ("Level now: median of the last 4 weekly medians of all reporting stations. Change: median of the "
                         "panel, last 4 weeks against each station's first 4 weeks. Trend: Theil-Sen slope of that median; "
                         "* = Mann-Kendall significant at 95 %. Start / now: first 2 and last 2 weeks. Clearly falling: "
                         "station trend significant and negative.")
    return out


def team_khg_names() -> dict:
    """Code -> registry name of the 13 team KHG."""
    reg = F.registry().set_index("code")
    return {c: reg.loc[c, "name"] for c in F.team()}


def sitmat_selected_khg() -> pd.DataFrame:
    """Stations of each team KHG (stations_geo.csv khg_name matched to the registry name), concession 1 April to
    22 October, community from comm_start(); share of days below -40 cm averaged over stations with 20 or more valid days."""
    rows = []
    cs, cm = derive("concession"), derive("community", comm_start())
    bs, bm = station_below_share(cs), station_below_share(cm)
    for code, name in team_khg_names().items():
        k = F.norm(F.short(name))
        m = cs["st"].khg_name.map(lambda x: F.norm(F.short(x))) == k
        mm = cm["st"].khg_name.map(lambda x: F.norm(F.short(x))) == k
        p = (m & cs["st"].panel).values
        an = weekly_series(cs, p, min_n=2)
        rows.append({"KHG": F.short(name),
                     "Concession stations (panel)": f"{int((m & (cs['st'].nv > 0)).sum())} ({int(p.sum())})" if m.any() else "-",
                     "Change since start, concession (cm)": f"{_edge_mean(an['med'], cs['weeks'], 4, True):+.1f}" if p.sum() >= 2 else "-",
                     "Days below -40 cm, concession (%)": F.fmt(bs[bs.khg_name.map(lambda x: F.norm(F.short(x))) == k].below.mean()),
                     "Community stations": str(int((mm & (cm['st'].nv > 0)).sum())) if mm.any() else "-",
                     "Days below -40 cm, community (%)": F.fmt(bm[bm.khg_name.map(lambda x: F.norm(F.short(x))) == k].below.mean())})
    out = pd.DataFrame(rows)
    out = out.assign(_n=out["Concession stations (panel)"].str.extract(r"^(\d+)")[0].astype(float).fillna(-1)).sort_values("_n", ascending=False).drop(columns="_n")
    out.attrs["note"] = ("Stations with at least one weekly median. Change: median of the panel stations, last 4 weeks against "
                         "each station's first 4 weeks. '-' = no station.")
    return out


# =====================================================================================================================
# National dashboard: scoring (dashboard.js compute())
# =====================================================================================================================
GROUPS = ["hist", "now", "canal"]
GROUP_LABEL = {"hist": "Fire history", "now": "This year", "canal": "Canals"}
GROUP_COLOR = {"hist": F.SERIES[0], "now": F.SERIES[1], "canal": F.SERIES[2]}   # as in the dashboard


@cache
def nat_data() -> dict:
    return json.loads((NAT / "dashboard_data.json").read_text(encoding="utf-8"))


def nat_frame() -> pd.DataFrame:
    d = nat_data()["data"]
    K = d["khg"]
    df = pd.DataFrame({k: K[k] for k in ("id", "name", "prov", "island", "area", "peat", "team", "ref_rank", "has")})
    for p, v in zip(d["params"], K["v"]):
        df[p["id"]] = pd.to_numeric(pd.Series(v), errors="coerce")
    df["code"] = df.id.str.replace("KHG.", "", regex=False)
    return df


def presets() -> dict:
    """The weight presets of the dashboard (buildControls)."""
    d = nat_data()["data"]
    P, DEF = d["params"], [d["meta"]["weights"][p["id"]] for p in d["params"]]
    return {"Default": DEF,
            "History": [0 if p["group"] == "now" else w for p, w in zip(P, DEF)],
            "This year": [1 if p["id"] == "n1" else 0 for p in P],
            "Canals": [w if p["group"] == "canal" else 0 for p, w in zip(P, DEF)],
            "Equal": [1] * len(P)}


def score(w, min_peat=None) -> pd.DataFrame:
    """compute(w) of dashboard.js: 5th-95th percentile scaling over the eligible KHG, weighted mean of the scaled values a
    KHG has, group contributions, ties at the cap ordered by the unclipped score, then by index."""
    d = nat_data()["data"]
    meta, P = d["meta"], d["params"]
    df = nat_frame()
    min_peat = meta["min_peat"] if min_peat is None else min_peat
    elig = (df.area >= meta["min_area"]) & df.peat.notna() & (df.peat >= min_peat)
    ne = int(elig.sum())
    min_units = min(20, max(3, ne // 2))
    num = np.zeros(len(df)); den = np.zeros(len(df)); tie = np.zeros(len(df))
    contrib = {g: np.zeros(len(df)) for g in GROUPS}
    for k, p in enumerate(P):
        if not w[k] > 0:
            continue
        v = df[p["id"]].where(elig)
        vals = np.sort(v.dropna().values)
        if len(vals) < min_units:
            continue
        lo, hi = np.quantile(vals, 0.05), np.quantile(vals, 0.95)
        if not hi - lo > 1e-12:
            continue
        zr = ((v - lo) / (hi - lo)).values
        z = np.clip(zr, 0, 1)
        ok = np.isfinite(z)
        num[ok] += w[k] * z[ok]; den[ok] += w[k]; tie[ok] += w[k] * zr[ok]
        contrib[p["group"]][ok] += w[k] * z[ok]
    with np.errstate(all="ignore"):
        out = pd.DataFrame({"score": np.where(elig & (den > 0), num / den, np.nan), "tie": tie / den,
                            **{g: contrib[g] / den for g in GROUPS}}, index=df.index)
    out = out.join(df[["id", "code", "name", "prov", "island", "team", "ref_rank"]])
    order = out[out.score.notna()].assign(i=lambda x: x.index).sort_values(["score", "tie", "i"], ascending=[False, False, True])
    out["rank"] = pd.Series(np.arange(1, len(order) + 1), index=order.index)
    return out


def parity() -> dict:
    """Default-weight scores and ranks against the Python ranking (operational/profile.csv skor_risiko, peringkat).
    The dashboard data hold indicator values to 4 decimals, so ranks can swap only between KHG whose Python scores differ
    by less than 1e-4, and within the block of KHG with a score of 0 (ordered by index)."""
    s = score(presets()["Default"])
    p = pd.read_csv(NAT / "operational/profile.csv", usecols=["khg_id", "skor_risiko", "peringkat"])
    m = s.merge(p, left_on="id", right_on="khg_id")
    r = m[m.peringkat.notna()].sort_values("peringkat").copy()
    r["gap"] = np.fmin(r.skor_risiko.diff().abs(), r.skor_risiko.diff(-1).abs())
    bad = r[r["rank"] != r.peringkat]
    unexplained = bad[(bad.skor_risiko > 0) & ~(bad.gap < 1e-4)]
    return {"ranked": int(s["rank"].notna().sum()), "python_ranked": len(r),
            "max_score_diff": float((r.score - r.skor_risiko).abs().max()),
            "identical_to_rank": int(bad.peringkat.min() - 1) if len(bad) else len(r),
            "swaps_near_ties": int(((bad.skor_risiko > 0) & (bad.gap < 1e-4)).sum()),
            "zero_score": int((r.skor_risiko == 0).sum()), "unexplained": len(unexplained)}


def _checked_default() -> pd.DataFrame:
    p = parity()
    assert p["unexplained"] == 0 and p["max_score_diff"] < 1e-4 and p["ranked"] == p["python_ranked"], p
    return score(presets()["Default"])


def team_codes() -> dict:
    t = F.team()
    flagged = set(nat_frame().query("team != ''").code)
    assert flagged == set(t), f"team flags differ: dashboard {sorted(flagged)} vs selected_khg {sorted(t)}"
    return t


# =====================================================================================================================
# National dashboard: figures and tables
# =====================================================================================================================
def _team_label(name, code, t):
    return F.short(name) + (" (reserve)" if t.get(code) == "reserve" else "")


def nat_contrib():
    """What each indicator group adds to the score (dashboard ranking bars), default weights: top 25 and the team KHG
    below them. Score = sum of the three segments."""
    d = _checked_default()
    t = team_codes()
    top = d[d["rank"] <= 25].sort_values("rank")
    rest = d[d.code.isin(t) & (d["rank"] > 25)].sort_values("rank")
    rows = pd.concat([top, rest])
    y = np.r_[np.arange(len(top)), np.arange(len(rest)) + len(top) + 0.8]
    fig, ax = plt.subplots(figsize=(F.W, 0.165 * len(rows) + 0.75))
    left = np.zeros(len(rows))
    for g in GROUPS:
        ax.barh(y, rows[g].values, left=left, height=0.74, color=GROUP_COLOR[g], edgecolor="#ffffff", linewidth=0.8,
                label=GROUP_LABEL[g])
        left += rows[g].values
    cap = sum(w for p, w in zip(nat_data()["data"]["params"], presets()["Default"]) if p["group"] == "hist") / sum(presets()["Default"])
    ax.axvline(cap, color=F.INK, lw=0.7, ls=(0, (4, 2)))
    ax.text(cap + 0.01, -1.3, "fire history at its maximum", fontsize=7.5, color=F.INK, ha="left", va="bottom")
    labels = [f"{int(r)}  {F.short(n)}{'  ◆' if c in t else ''}" for r, n, c in zip(rows["rank"], rows.name, rows.code)]
    ax.set_yticks(y, labels)
    for lab, c in zip(ax.get_yticklabels(), rows.code):
        lab.set_color(F.INK if c in t else F.MUTED)
    ax.tick_params(axis="y", length=0, labelsize=7.5)
    ax.invert_yaxis()
    ax.set_ylim(y.max() + 0.6, -1.6)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Score (0-1), split by what each group of indicators adds")
    ax.legend(loc="lower right", bbox_to_anchor=(1, 0.0), ncol=1, fontsize=7.5, frameon=True, facecolor="#ffffff",
              edgecolor="none", title="◆ selected KHG", title_fontsize=7.5, alignment="left")
    fig.tight_layout()
    return F.save(fig, "nat_contrib")


PRESET_STYLE = {"History": (F.SERIES[1], "o"), "This year": (F.SERIES[3], "s"), "Canals": (F.SERIES[0], "D"),
                "Equal": (F.SERIES[2], "^")}


def nat_rank_presets():
    """Rank of the team KHG under the dashboard's weight presets (Default, History, This year, Canals, Equal)."""
    d = _checked_default()
    t = team_codes()
    R = {k: score(w) for k, w in presets().items()}
    tm = d[d.code.isin(t)].sort_values("rank")
    fig, ax = plt.subplots(figsize=(F.W, 0.27 * len(tm) + 1.0))
    y = np.arange(len(tm))
    allr = pd.DataFrame({k: R[k].loc[tm.index, "rank"] for k in R})
    ax.hlines(y, allr.min(1), allr.max(1), color=F.NEUTRAL, lw=2.4, zorder=1)
    for k, (col, mk) in PRESET_STYLE.items():
        v = allr[k]
        ax.scatter(v, y, s=26, marker=mk, color=col, edgecolors="#ffffff", linewidths=0.6, zorder=3, label=k)
    ax.scatter(allr["Default"], y, s=60, marker="|", color=F.INK, linewidths=2, zorder=4, label="Default")
    ax.set_xscale("log")
    ticks = [1, 2, 5, 10, 25, 50, 100, 200, 476]
    ax.set_xticks(ticks, [str(x) for x in ticks])
    ax.minorticks_off()
    ax.set_xlim(0.8, 520)
    ax.set_yticks(y, [_team_label(n, c, t) for n, c in zip(tm.name, tm.code)])
    ax.tick_params(axis="y", length=0, labelsize=8)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Rank among the ranked KHG (log scale)")
    h, l = ax.get_legend_handles_labels()
    order = [l.index("Default")] + [l.index(k) for k in PRESET_STYLE]
    ax.legend([h[i] for i in order], [l[i] for i in order], loc="lower left", bbox_to_anchor=(0, 1.0), ncol=5,
              fontsize=7.5, handletextpad=0.2, columnspacing=1.0)
    fig.tight_layout()
    return F.save(fig, "nat_rank_presets")


def nat_presets_top25() -> pd.DataFrame:
    """For each dashboard preset: KHG that can be scored, how many of the default top 25 stay in the top 25, the team KHG
    in the top 25 and the top 3."""
    d = _checked_default()
    t = team_codes()
    P = nat_data()["data"]["params"]
    top0 = set(d.index[d["rank"] <= 25])
    rows = []
    for k, w in presets().items():
        r = score(w)
        top = r[r["rank"] <= 25]
        rows.append({"Preset": k,
                     "Weights": ", ".join(f"{p['label'].lower()} {x:g}" for p, x in zip(P, w) if x > 0),
                     "KHG ranked": int(r["rank"].notna().sum()),
                     "Default top 25 still in top 25": len(top0 & set(top.index)),
                     "Selected KHG in top 25": int(top.code.isin(t).sum()),
                     "Top 3": "; ".join(F.short(n) for n in top.sort_values("rank").name.head(3))})
    out = pd.DataFrame(rows)
    out.attrs["note"] = ("Presets as in the dashboard. History: this year's indicators set to 0. This year: hotspots this "
                         "year only. Canals: canal indicators only, so KHG without mapped canals drop out.")
    return out


def nat_team_percentiles():
    """Position of each team KHG among the ranked KHG on every dashboard parameter (strip plots of the profile page):
    percentile = share of ranked KHG with a lower value."""
    d = _checked_default()
    t = team_codes()
    df = nat_frame()
    P = nat_data()["data"]["params"]
    elig = d["rank"].notna()
    tm = d[d.code.isin(t)].sort_values("rank")
    M = np.full((len(tm), len(P)), np.nan)
    for k, p in enumerate(P):
        vals = np.sort(df.loc[elig, p["id"]].dropna().values)
        for i, idx in enumerate(tm.index):
            v = df.loc[idx, p["id"]]
            if np.isfinite(v):
                M[i, k] = np.searchsorted(vals, v, side="left") / len(vals) * 100
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("b", ["#eef4fc", F.BLUE_RAMP[250], F.BLUE_RAMP[450], F.BLUE_RAMP[650]])
    fig, ax = plt.subplots(figsize=(F.W, 0.25 * len(tm) + 1.25))
    ax.imshow(np.ma.masked_invalid(M), cmap=cmap, vmin=0, vmax=100, aspect="auto")
    for i in range(M.shape[0]):
        for k in range(M.shape[1]):
            v = M[i, k]
            if np.isfinite(v):
                ax.text(k, i, f"{v:.0f}", ha="center", va="center", fontsize=7.5, color="#ffffff" if v >= 60 else F.INK)
            else:
                ax.add_patch(plt.Rectangle((k - 0.5, i - 0.5), 1, 1, color=F.NEUTRAL, lw=0))
                ax.text(k, i, "none", ha="center", va="center", fontsize=7, color=F.MUTED)
    for k in range(1, len(P)):
        ax.axvline(k - 0.5, color="#ffffff", lw=1.5)
    for i in range(1, len(tm)):
        ax.axhline(i - 0.5, color="#ffffff", lw=1.5)
    W = presets()["Default"]
    short = {"f1": "Burned\nshare", "f2": "Repeat\nburns", "f3": "Hotspots\n2015-2025", "n1": "Hotspots\nthis year",
             "n2": "Burned\nthis year", "c1": "Primary\ncanals", "c2": "Secondary\ncanals", "c3": "Tertiary\ncanals"}
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(tm)), [f"{int(r)}  {_team_label(n, c, t)}" for r, n, c in zip(tm["rank"], tm.name, tm.code)])
    ax.tick_params(length=0, labelsize=7.5)
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    nv = pd.Series([int(df.loc[elig, p["id"]].notna().sum()) for p in P], index=[p["id"] for p in P])
    ax.set_xticks(range(len(P)), [f"{short[p['id']]}\nweight {w:g}\nn = {nv[p['id']]}" for p, w in zip(P, W)], fontsize=7.5)
    ax.set_xlabel("Percentile among the ranked KHG that have a value (n in the header; 100 = highest value)",
                  fontsize=7.5, color=F.MUTED)
    fig.tight_layout()
    return F.save(fig, "nat_team_percentiles")


def nat_team_profiles():
    """Profile-page lines of the team KHG: burned share per year 2015-2025 (2026 partial, hollow), KLH hotspots on peat per
    month 2026, TerraClimate dry-season deficit 2015-2021 (dashboard_data.json profiles: burned, now_m, deficit). Each
    column has one y scale for all rows."""
    d = _checked_default()
    t = team_codes()
    prof = nat_data()["profiles"]
    tm = d[d.code.isin(t)].sort_values("rank")
    cols = [("burned", "Burned (% of peat)", F.SERIES[1]), ("now_m", "Hotspots 2026, per month", F.SERIES[3]),
            ("deficit", "Dry-season deficit (mm)", F.MUTED)]
    data = {c: [] for c, _, _ in cols}
    for idx in tm.index:
        P = prof[d.loc[idx, "id"]]
        data["burned"].append(np.array(P["burned"], float))
        data["now_m"].append(np.array([[m[0], m[1]] for m in P["now_m"]], float))
        data["deficit"].append(np.array(P["deficit"], float))
    ymax = {c: max(a[:, 1].max() for a in v) for c, v in data.items()}
    fig, axes = plt.subplots(len(tm), 3, figsize=(F.W, 0.36 * len(tm) + 0.7), sharex="col",
                             gridspec_kw={"width_ratios": [1.15, 1, 0.85], "hspace": 0.25, "wspace": 0.12})
    for i, idx in enumerate(tm.index):
        for j, (c, title, col) in enumerate(cols):
            ax = axes[i, j]
            a = data[c][i]
            if c == "burned":
                full = a[a[:, 0] <= 2025]
                ax.plot(full[:, 0], full[:, 1], color=col, lw=1.1)
                part = a[a[:, 0] == 2026]
                if len(part):
                    ax.plot([2025, 2026], [full[-1, 1], part[0, 1]], color=col, lw=0.8, ls=(0, (2, 1.5)))
                    ax.scatter(part[:, 0], part[:, 1], s=8, facecolor="#ffffff", edgecolor=col, lw=0.8, zorder=3)
            else:
                ax.plot(a[:, 0], a[:, 1], color=col, lw=1.1)
            k = int(np.argmax(a[:, 1]))
            ax.text(a[k, 0], a[k, 1], f"{a[k, 1]:,.0f}" if c != "burned" else f"{a[k, 1]:.1f}", fontsize=6.5,
                    color=F.INK, va="bottom", ha="center")
            ax.set_ylim(0, ymax[c] * 1.3)
            ax.set_yticks([]); ax.grid(False)
            for sp in ("left", "top", "right"):
                ax.spines[sp].set_visible(False)
            ax.spines["bottom"].set_color(F.GRID)
            ax.tick_params(axis="x", labelsize=7, length=0)
            if i == 0:
                ax.set_title(title, loc="left", fontsize=7.5)
        axes[i, 0].set_ylabel(f"{int(tm.loc[idx, 'rank'])}  {_team_label(tm.loc[idx, 'name'], tm.loc[idx, 'code'], t)}",
                              rotation=0, ha="right", va="center", fontsize=7.5, color=F.INK)
    axes[-1, 0].set_xticks([2015, 2020, 2025])
    axes[-1, 1].set_xticks([1, 3, 5, 7, 9], ["Jan", "Mar", "May", "Jul", "Sep"])
    axes[-1, 2].set_xticks([2015, 2018, 2021])
    fig.subplots_adjust(left=0.3, right=0.99, top=0.95, bottom=0.05)
    return F.save(fig, "nat_team_profiles")


# =====================================================================================================================
# Cropped screenshots of one part of each page (served and shot as in project_report_screens.py)
# =====================================================================================================================
SCREENS = {   # name: (page, query, viewport width, height, wait ms, css selectors whose union is cropped)
    "screen_sitmat_overview": ("repeat-sitmat/index.html", "", 1440, 1400, 9000, ["#story", "#kpis"]),
    "screen_national_ranking": ("re-peat/reports/national_profile/dashboard.html", "", 1440, 1500, 9000, ["#controls", "#rank"]),
}


def shoot_screens(names=None):
    """Shoot the cropped screenshots (needs Chrome and internet for basemaps and CDN libraries)."""
    import project_report_screens as S
    from playwright.sync_api import sync_playwright
    srv = S.serve()
    out = []
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(executable_path=S.CHROME, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            page = b.new_page(device_scale_factor=2)
            for name, (rel, q, w, h, wait, sels) in SCREENS.items():
                if names and name not in names:
                    continue
                page.set_viewport_size({"width": w, "height": h})
                page.goto(f"http://127.0.0.1:{S.PORT}/{rel}{q}", wait_until="networkidle", timeout=120000)
                page.wait_for_timeout(wait)
                boxes = [page.locator(s).first.bounding_box() for s in sels]
                x0, y0 = min(bx["x"] for bx in boxes), min(bx["y"] for bx in boxes)
                x1 = max(bx["x"] + bx["width"] for bx in boxes); y1 = max(bx["y"] + bx["height"] for bx in boxes)
                p = F.OUT / f"{name}.png"
                page.screenshot(path=str(p), clip={"x": x0 - 6, "y": y0 - 6, "width": x1 - x0 + 12, "height": y1 - y0 + 12},
                                full_page=True)
                out.append(p)
            b.close()
    finally:
        srv.shutdown()
    return out


def _screen(name):
    p = F.OUT / f"{name}.png"
    if not p.exists():
        shoot_screens([name])
    return p, (10 if name == "screen_national_ranking" else 16)


def screen_sitmat_overview():
    return _screen("screen_sitmat_overview")


def screen_national_ranking():
    return _screen("screen_national_ranking")


# =====================================================================================================================
# Numbers quoted in the draft text
# =====================================================================================================================
def numbers():
    """Print every number the draft sections quote, with the computation it comes from."""
    pr = lambda k, v: print(f"{k}: {v}")  # noqa: E731
    r1 = lambda v, n=1: round(float(v), n)  # noqa: E731
    c0 = comm_start()
    print("== SiTMAT ==")
    pr("community series start (comm_start)", c0)
    J = derive("community", COMM_FIRST)
    jp = J["st"].panel.values
    w0, w1 = J["weeks"][:2], [w for w in J["weeks"] if w * 7 >= int(np.searchsorted(J["dates"], c0))]
    first = np.nanmedian(J["wk"][jp][:, w0], axis=1)
    after = np.nanmedian(J["wk"][jp][:, w1[:1]], axis=1)
    pr("community panel from 21 July: stations / July weekly level between 0 and +3 cm", (int(jp.sum()), int(((first >= 0) & (first <= 3)).sum())))
    pr("  their first weekly level from comm_start (cm, min/max)", (r1(after[(first >= 0) & (first <= 3)].min(), 0), r1(after[(first >= 0) & (first <= 3)].max(), 0)))
    bd = pd.read_csv(WS / "repeat-sitmat/baseline_out/baseline_daily.csv")
    bj = bd[(bd.kind == "community") & (bd.date < "2026-08-01")]
    ph = bj.water_level_cm.between(0, 3)
    pr("baseline_daily.csv community July: readings / stations / readings 0..+3 cm / their stations",
       (len(bj), bj.station_id.nunique(), int(ph.sum()), bj[ph].station_id.nunique()))
    pr("  weeks with no community weekly median between July and comm_start", [J["week_start"][w] for w in J["weeks"] if w not in w1 and not np.isfinite(J["wk"][:, w]).any()])
    for kind, d0 in (("concession", None), ("concession", c0), ("community", c0)):
        D = derive(kind, d0)
        o = overview(D)
        tag = f"{kind} {d0 or '2026-04-01'}..2026-10-22"
        pr(f"{tag}: panel / with weekly median / weeks", (o["panel"], o["with_data"], len(D["weeks"])))
        pr(f"{tag}: change last 4 wk vs first 4 wk (cm)", r1(o["change"]))
        pr(f"{tag}: Theil-Sen of panel median (cm/wk), z, sig", (r1(o["slope"], 2), r1(o["z"], 2), bool(o["sig"])))
        pr(f"{tag}: below -40 first 2 wk -> last 2 wk (%)", (r1(o["below_start"], 0), r1(o["below_end"], 0)))
        pr(f"{tag}: below -80 first 2 wk -> last 2 wk (%)", (r1(o["deep_start"], 0), r1(o["deep_end"], 0)))
        pr(f"{tag}: stations clearly falling / rising (% of {o['n_slope']} with a trend)", (r1(o["drying"], 0), r1(o["wetting"], 0)))
        sh = o["sh"]["below"]
        w = [x for x in D["weeks"] if np.isfinite(sh[x])]
        k_min, k_max = int(np.nanargmin(sh[w])), int(np.nanargmax(sh[w]))
        pr(f"{tag}: weekly share below -40 min (week start, %)", (D["week_start"][w[k_min]], r1(sh[w][k_min], 0)))
        pr(f"{tag}: weekly share below -40 max (week start, %)", (D["week_start"][w[k_max]], r1(sh[w][k_max], 0)))
        st = stuck(D)
        p = D["st"].panel.values & ~st.values
        s2 = class_shares(D, p)
        pr(f"{tag}: stuck panel stations (one weekly value throughout)", int(st.sum()))
        pr(f"{tag}: without stuck, below -40 / below -80 first -> last 2 wk (%)",
           [r1(_edge_mean(s2[a], D["weeks"], 2, e), 0) for a in ("below", "bad") for e in (False, True)])
        if kind == "concession" and d0 is None:
            an = o["an"]
            ww = [x for x in D["weeks"] if np.isfinite(an["med"][x])]
            k = int(np.nanargmax(an["med"][ww]))
            pr(f"{tag}: highest panel median change (week start, cm)", (D["week_start"][ww[k]], r1(an["med"][ww][k])))
            pr(f"{tag}: IQR of change in the last week (cm)", (r1(an["q1"][ww[-1]]), r1(an["q3"][ww[-1]])))
        _, _, parts = duration_parts(kind, d0)
        for lab, v in parts:
            pr(f"{tag}: duration, {lab}: below -40 / below -80 (% of readings)", (r1(share_below(v, THRESH), 0), r1(share_below(v, DEEP), 0)))
    sp = spells()
    dip = sp[sp > 0]
    pr("dry spell, concession panel: stations / never below -40 / median longest spell of the others (days) / over 60 days / over 90 days",
       (len(sp), int((sp == 0).sum()), r1(dip.median(), 0), int((sp > 60).sum()), int((sp > 90).sum())))
    r = region_stats(derive("concession"))
    r = r[r.nP >= MIN_PROV_PANEL].sort_values("slope")
    pr("provinces with >= 5 concession panel stations", len(r))
    for x in r.itertuples():
        pr(f"  {x.adm1}", f"panel {x.nP}, trend {x.slope:+.2f} cm/wk sig={bool(x.sig)}, change {x.cur_change:+.1f} cm, "
                          f"below -40 {x.start_below:.0f} -> {x.cur_below:.0f} %, falling {x.drying:.0f} %, level now {x.cur_level:.0f} cm")
    c = concession_stats()
    pr("concessions with >= 3 stations (20+ valid days)", len(c))
    pr("  median of concession mean share below -40 (%)", r1(c.share.median(), 0))
    pr("  concessions with share 0 / >= 50 % / >= 80 %", (int((c.share == 0).sum()), int((c.share >= 50).sum()), int((c.share >= 80).sum())))
    pr("  provincial medians (%)", {k: r1(v, 0) for k, v in c.groupby("prov").share.median().items() if (c.prov == k).sum() >= 3})
    g = sharing()
    diff = g.mean_community - g.mean_concession
    pr("sharing: KHG with both kinds", len(g))
    pr("  KHG where community mean is deeper than concession mean", int((diff < 0).sum()))
    pr("  median difference community - concession (cm)", r1(diff.median()))
    pr("  KHG with community mean below -100 cm", int((g.mean_community < -100).sum()))
    pr("  concession means range (cm)", (r1(g.mean_concession.min()), r1(g.mean_concession.max())))
    pr("  community stations / concession stations in these KHG", (int(g.size_community.sum()), int(g.size_concession.sum())))
    print(sitmat_selected_khg().to_string())
    for name in ("Sungai Mendahara - Sungai Batanghari", "Sungai Sugihan - Sungai Lumpur"):
        k = F.norm(F.short(name))
        for kind, d0 in (("concession", None), ("concession", c0), ("community", c0)):
            D = derive(kind, d0)
            m = (D["st"].khg_name.map(lambda x: F.norm(F.short(x))) == k) & D["st"].panel
            if m.sum() >= 2:
                an = weekly_series(D, m.values, min_n=2)
                pr(f"{F.short(name)} {kind} {d0 or 'season'}: panel, change (cm)", (int(m.sum()), r1(_edge_mean(an["med"], D["weeks"], 4, True))))
    print("== National ==")
    pr("parity", parity())
    d = _checked_default()
    t = team_codes()
    top = d[d["rank"] <= 25]
    tot = top[GROUPS].sum()
    pr("top 25: share of summed score by group (%)", {g: r1(tot[g] / tot.sum() * 100, 0) for g in GROUPS})
    W0 = presets()["Default"]; P0 = nat_data()["data"]["params"]
    cap = sum(w for p, w in zip(P0, W0) if p["group"] == "hist") / sum(W0)
    capn = sum(w for p, w in zip(P0, W0) if p["group"] == "now") / sum(W0)
    pr("top 25: KHG with fire history at its maximum (weight share of fire history)", int((top["hist"] > cap - 1e-9).sum()))
    pr("top 25: KHG with no canal contribution", int((top["canal"] == 0).sum()))
    pr("top 25: canal contribution max (KHG, value)", (top.loc[top["canal"].idxmax(), "name"], r1(top["canal"].max(), 3)))
    pr("top 25: this-year contribution at its maximum (weight share)", int((top["now"] > capn - 1e-9).sum()))
    pr("ranked KHG with fire history at its maximum", int((d["hist"] > cap - 1e-9).sum()))
    print(nat_presets_top25().to_string())
    R = {k: score(w) for k, w in presets().items()}
    tm = d[d.code.isin(t)].sort_values("rank")
    print(pd.DataFrame({k: R[k].loc[tm.index, "rank"] for k in R}).assign(name=tm.name.map(F.short).values).to_string())
    print(tm[["name", "rank", "score"] + GROUPS].round(3).to_string())
    df = nat_frame()
    el = d["rank"].notna()
    pr("ranked KHG with a value per parameter", {p["id"]: int(df.loc[el, p["id"]].notna().sum()) for p in nat_data()["data"]["params"]})
    pr("ranked KHG with burned share 0 / under the value of Pulau Padang", (int((df.loc[el, "f1"] == 0).sum()),
       int((df.loc[el, "f1"] < df.loc[df.code == "14.10.01", "f1"].iloc[0]).sum())))
    gsh = sharing(); dd = gsh.mean_community - gsh.mean_concession
    pr("sharing: median difference over the KHG where community is deeper (cm)", r1(dd[dd < 0].median()))
    rk = pd.DataFrame({k: R[k].loc[tm.index, "rank"] for k in R})
    n_high = int((d["rank"] <= d["rank"].max() / 3).sum())
    main = tm.code.map(t) == "main"
    pr("team main KHG / within the size of the 'high' class under every preset", (int(main.sum()), n_high,
       int((rk[main.values].max(1) <= 158).sum()), list(tm[main.values & (rk.max(1) > 158).values].name.map(F.short))))
    pr("team KHG best / worst rank across presets", {F.short(n): (int(a), int(b)) for n, a, b in zip(tm.name, rk.min(1), rk.max(1))})
    prof = nat_data()["profiles"]
    for idx in tm.index:
        pr(f"  burned series {F.short(d.loc[idx, 'name'])}", [(y, round(v, 1)) for y, v in prof[d.loc[idx, "id"]]["burned"]])
    for idx in tm.index:
        P = prof[d.loc[idx, "id"]]
        b = max(P["burned"], key=lambda x: x[1]); n = max(P["now_m"], key=lambda x: x[1]); de = max(P["deficit"], key=lambda x: x[1])
        pr(f"  {F.short(d.loc[idx, 'name'])}", f"peak burned {b[0]} {b[1]} %; 2026 burned {dict(map(tuple, P['burned'])).get(2026)} %; "
                                             f"hotspots 2026 total on peat {sum(m[1] for m in P['now_m'])}, peak month {n[0]} ({n[1]}); "
                                             f"deficit peak {de[0]} {de[1]} mm")


REGISTRY: dict = {"sitmat_station_map": sitmat_station_map, "sitmat_change": sitmat_change,
                  "sitmat_share_below": sitmat_share_below, "sitmat_province_trend": sitmat_province_trend,
                  "sitmat_duration": sitmat_duration, "sitmat_dry_spell": sitmat_dry_spell, "sitmat_sharing": sitmat_sharing,
                  "sitmat_concessions": sitmat_concessions,
                  "sitmat_quality": sitmat_quality, "sitmat_provinces": sitmat_provinces, "sitmat_selected_khg": sitmat_selected_khg,
                  "nat_contrib": nat_contrib, "nat_rank_presets": nat_rank_presets, "nat_presets_top25": nat_presets_top25,
                  "nat_team_percentiles": nat_team_percentiles, "nat_team_profiles": nat_team_profiles,
                  "screen_sitmat_overview": screen_sitmat_overview, "screen_national_ranking": screen_national_ranking}


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "numbers"
    if cmd == "numbers":
        numbers()
    elif cmd == "screens":
        print(shoot_screens(sys.argv[2:] or None))
    elif cmd == "all":
        for k, fn in REGISTRY.items():
            print(k, fn() if not isinstance(fn(), pd.DataFrame) else "table")
