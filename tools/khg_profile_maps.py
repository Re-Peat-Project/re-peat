"""Six thematic maps of one KHG for the profile annex of the prioritisation report.

    python re-peat/tools/khg_profile_maps.py KHG.16.02.01 [...] [--out DIR] [--workers 3]

Panels (all clipped to the KHG): 1 peat depth and dome, 2 SKEG 2024 damage, 3 drainage (canal-influence zones, canals,
rivers, BRGM structures), 4 land cover 2022, 5 land status (forest-area function, licences, social forestry, PPTPKH),
6 fire and villages (times burned 2015-2026, this year's hotspots, DMPG villages, roads). Each layer is read with the KHG's
bounding box from $REPEAT_DATA (the files of the layer register). Fills are rasterised on a grid of about 900 cells across
(finer than print); lines and points stay vectors, clipped to the KHG. Nothing is written but the PNG.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

DATA = Path(os.environ.get("REPEAT_DATA", Path(__file__).resolve().parents[2] / "_data"))
INK, MUTED, NONPEAT = "#2b2b2b", "#77746c", "#ecebe6"
PPEG = "ALL_Analysis_Integrasi_Tematik__PPEG_Indonesia__April_2026.gpkg"
LIC = "landstatus/ALL_Updade__IZIN_USAHA__PBPH_Perkebunan_HTRKM_Tambang__2025.gpkg"

DEPTH = [("< 1 m", 0, 1, "#f1e3c8"), ("1-2 m", 1, 2, "#dcb47a"), ("2-3 m", 2, 3, "#b98142"), ("3-5 m", 3, 5, "#8a5325"), ("≥ 5 m", 5, 99, "#4f2a10")]
SKEG = [("Not damaged", "Tidak Rusak", "#cfe3d4"), ("Light", "Rusak Ringan", "#f2c57c"), ("Moderate", "Rusak Sedang", "#e8863a"),
        ("Heavy", "Rusak Berat", "#c0392b"), ("Very heavy", "Rusak Sangat Berat", "#7b1c12")]
ZONE = [("Primary canal zone", "Kanal Primer", "#9cc3e0"), ("Secondary", "Kanal Sekunder", "#c3dbee"), ("Tertiary", "Kanal Tersier", "#e2eef7")]
OPEN = {"Semak Belukar Rawa", "Semak Belukar", "Lahan Terbuka", "Rawa", "Savana/ Padang Rumput", "Savana/Padang Rumput"}
LC = [("Forest", lambda s: s.startswith("Hutan") and s != "Hutan Tanaman", "#3f7d4e"), ("Open or degraded", lambda s: s in OPEN, "#e5c35c"),
      ("Plantation", lambda s: s in ("Perkebunan", "Hutan Tanaman"), "#a45ba0"), ("Farmland", lambda s: s.startswith("Pertanian") or s == "Sawah", "#d99a6c"),
      ("Settlement", lambda s: s == "Permukiman", "#6d6d6d"), ("Water", lambda s: s == "Tubuh Air", "#8fb8d8")]
KWS = [("Conservation", ("Suaka", "Taman", "Cagar", "Kawasan Suaka", "Hutan (Kawasan) Suaka"), "#2f7d5b"), ("Protection", ("Hutan Lindung",), "#7fb28f"),
       ("Production", ("Hutan Produksi Tetap", "Hutan Produksi Terbatas"), "#c9d89b"), ("Convertible (HPK)", ("Hutan Produksi yang dapat di Konversi",), "#ead9a4"),
       ("Other land use (APL)", ("Areal Penggunaan Lain",), "#f4efe6")]
BURN = [("Burned once", 1, "#f6c7a6"), ("Twice", 2, "#ec8f5c"), ("3 times", 3, "#cc5326"), ("4+", 4, "#7e2a0c")]


def depth_m(s):
    """Lower bound of a thickness class in metres: '1,0 - 1,5 meter', '100 - <200 cm', '>= 700 cm'."""
    if not isinstance(s, str) or not s.strip() or "NON" in s:
        return np.nan
    m = re.search(r"(\d+(?:[.,]\d+)?)", s)
    if not m:
        return np.nan
    v = float(m.group(1).replace(",", "."))
    return v / 100 if "cm" in s else v


def read(path, bbox, cols=None, where=None):
    import pyogrio
    p = DATA / path
    if not p.exists():
        return None
    try:
        return pyogrio.read_dataframe(p, bbox=bbox, columns=cols, where=where)
    except Exception:
        return None


def inside(df, geom):
    import shapely
    if df is None or not len(df):
        return df
    prep = shapely.prepared.prep(geom) if hasattr(shapely, "prepared") else None
    m = df.geometry.intersects(geom)
    return df[m.values]


def render(code, out_png, khg_gpkg=None):
    import geopandas as gpd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import shapely
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6})
    khg = gpd.read_file(khg_gpkg or DATA / "derived" / "khg_klh_priority.gpkg", layer="khg", where=f"khg_code = '{code}'")
    geom = shapely.make_valid(khg.geometry.iloc[0])
    x0, y0, x1, y1 = geom.bounds
    bbox = (x0, y0, x1, y1)
    tol = max(x1 - x0, y1 - y0) / 1500
    simp = lambda g: g.assign(geometry=g.geometry.simplify(tol)) if g is not None and len(g) else g

    pp = read(PPEG, bbox, ["LAHAN_GAMB", "PEAT_THICK", "LANDFORM", "SKEG_2024", "KET_KANAL", "PL_2022", "Fungsi_KWS"])
    if pp is not None and len(pp):
        pp = pp[shapely.contains_xy(geom, *shapely.get_coordinates(pp.geometry.representative_point()).T)]

    canals = simp(inside(read("kanal_osgm_khg_existing_Indonesia.gpkg", bbox, ["KET_KANAL"]), geom))
    rivers = simp(inside(read("RBI_sungai.gpkg", bbox, []), geom))
    roads = simp(inside(read("Transportasi_Jalan_Detil.gpkg", bbox, ["NAMA_UNSUR"]), geom))
    if roads is not None and len(roads):
        roads = roads[~roads.NAMA_UNSUR.fillna("").str.contains("Setapak|Pematang", case=False)]
    brgm = inside(read("infrastruktur_hidrologis_existing_BRGM_Indonesia.gpkg", bbox, []), geom)
    burn_g = inside(read("burnt_area_2015_2026_Indonesia.gpkg", bbox, ["BURN_FREQ"]), geom)
    hot = inside(read("hotspots_modis_2026.gpkg", bbox, ["level"]), geom)
    if hot is not None and len(hot):
        hot = hot[hot.level.isin(["medium", "high"])]
    dmpg = inside(read("dpg/dmpg_villages_sitmat.gpkg", bbox, []), geom)
    lic = inside(read(LIC, bbox, ["IZIN_USAHA"]), geom)
    if lic is not None and len(lic):
        lic = lic[lic.IZIN_USAHA != "PPHKM"]
    sf = [read(p, bbox, []) for p in ("tenure/hutan_desa.gpkg", "tenure/htr.gpkg", "tenure/iphps.gpkg")]
    sf.append(read(LIC, bbox, ["IZIN_USAHA"], where="IZIN_USAHA = 'PPHKM'"))   # community forestry permits (PPHKM) in the licence file
    parts = [g for g in (inside(x, geom) for x in sf if x is not None and len(x)) if g is not None and len(g)]
    sf = gpd.GeoDataFrame(geometry=np.concatenate([g.geometry.values for g in parts]), crs=4326) if parts else None
    pt = inside(read("tenure/pptpkh.gpkg", bbox, []), geom)


    from matplotlib.colors import to_rgba
    from matplotlib.path import Path as MPath
    from matplotlib.patches import PathPatch
    from rasterio.features import rasterize
    from rasterio.transform import from_bounds
    lat = (y0 + y1) / 2
    pad = max(x1 - x0, y1 - y0) * .03
    X0, Y0, X1, Y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    kx = np.cos(np.radians(lat))
    NX = 900
    NY = max(50, int(NX * (Y1 - Y0) / ((X1 - X0) * kx)))
    if NY > 1400:
        NX, NY = int(NX * 1400 / NY), 1400
    tr = from_bounds(X0, Y0, X1, Y1, NX, NY)
    inkhg = rasterize([(geom, 1)], out_shape=(NY, NX), transform=tr, fill=0, dtype="uint8").astype(bool)
    II, JJ = np.indices((NY, NX))

    _ids = {}

    def idras(g):
        """Feature-index raster of a whole layer (cell centre, 1-based; 0 = none), computed once per layer."""
        k = id(g)
        if k not in _ids:
            geoms = [(x, i + 1) for i, x in enumerate(g.geometry.values) if x is not None and not x.is_empty]
            _ids[k] = rasterize(geoms, out_shape=(NY, NX), transform=tr, fill=0, dtype="int32") if geoms else np.zeros((NY, NX), "int32")
        return _ids[k]

    def burn(g, parent=None):
        """Raster mask of the polygons of g: a lookup in the index raster of its parent layer (one rasterisation per layer)."""
        if g is None or not len(g):
            return np.zeros((NY, NX), bool)
        if parent is None:
            parent = g
        pos = parent.index.get_indexer(g.index)
        lut = np.zeros(len(parent) + 1, bool); lut[pos[pos >= 0] + 1] = True
        return lut[idras(parent)]

    def paint(ax, layers, base=None, pattern=None):
        img = np.zeros((NY, NX, 4))
        if base is not None:
            img[inkhg] = to_rgba(base)
        for m, c in layers:
            img[m & inkhg] = to_rgba(c)
        for pat in ([pattern] if isinstance(pattern, tuple) else (pattern or [])):
            if pat is None or pat[0] is None:
                continue
            m, c, kind = pat
            pm = ((II + JJ) % 7 < 2) if kind == "hatch" else ((II - JJ) % 9 < 2) if kind == "back" else ((II % 6 == 0) & (JJ % 6 == 0))
            img[m & inkhg & pm] = to_rgba(c)
        ax.imshow(img, extent=(X0, X1, Y0, Y1), origin="upper", interpolation="nearest", zorder=1)

    def khg_path():
        verts, codes = [], []
        polys = getattr(geom, "geoms", [geom])
        for p in polys:
            if p.geom_type != "Polygon":
                continue
            for ring in [p.exterior, *p.interiors]:
                c = np.asarray(ring.coords)
                verts += c.tolist(); codes += [MPath.MOVETO] + [MPath.LINETO] * (len(c) - 2) + [MPath.CLOSEPOLY]
        return MPath(verts, codes)
    KP = khg_path()

    def overlay(ax, g, **kw):
        """Lines and outlines, clipped to the KHG by a clip path (no geometric clipping)."""
        if g is None or not len(g):
            return
        c0, l0 = len(ax.collections), len(ax.lines)
        g.plot(ax=ax, aspect=None, zorder=kw.pop("zorder", 3), **kw)
        for art in list(ax.collections)[c0:] + list(ax.lines)[l0:]:
            art.set_clip_path(PathPatch(KP, transform=ax.transData))

    fig = plt.figure(figsize=(7.2, 4.7))
    W, H = 1 / 3, .5
    titles = ["Peat depth and dome", "Peat damage (SKEG 2024)", "Drainage", "Land cover 2022", "Land status", "Fire and villages"]
    axes = []
    for k in range(6):
        cx, cy = k % 3, 1 - k // 3
        ax = fig.add_axes([cx * W + .005, cy * H + .15, W - .01, H - .19])
        ax.set_axis_off()
        ax.set_title(f"{k + 1}  {titles[k]}", fontsize=7.5, loc="left", color=INK, pad=2, weight="bold")
        axes.append(ax)
    kg = gpd.GeoSeries([geom], crs=4326)

    def frame(ax):
        kg.boundary.plot(ax=ax, color=INK, linewidth=.7, aspect=None, zorder=5)
        ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); ax.set_aspect(1 / kx)

    def legend(ax, handles, labels, ncol=2):
        ax.legend(handles, labels, loc="upper left", bbox_to_anchor=(0, -.01), fontsize=5.6, frameon=False, ncol=ncol,
                  handlelength=1.2, handletextpad=.4, columnspacing=.8, borderaxespad=0, labelspacing=.25)

    have = pp is not None and len(pp)
    E = gpd.GeoDataFrame(geometry=[], crs=4326)
    P = pp.reset_index(drop=True) if have else E
    pk = P[P.LAHAN_GAMB.eq("LAHAN GAMBUT")] if have else E
    peat_m = burn(pk, P)
    nonpeat = (NONPEAT, None)
    # 1 depth and dome
    ax = axes[0]
    if have:
        dm = pk.PEAT_THICK.map(depth_m)
        lay = [(peat_m, "#d9d4c7")] + [(burn(pk[(dm >= a) & (dm < b)], P), c) for _, a, b, c in DEPTH]
        dome = burn(pk[pk.LANDFORM.fillna("").str.contains("kubah", case=False)], P)
        paint(ax, lay, base=NONPEAT, pattern=(dome, "#1f4e79", "hatch"))
    frame(ax)
    legend(ax, [Patch(color=c) for *_, c in DEPTH] + [Patch(facecolor="none", edgecolor="#1f4e79", hatch="////", lw=0), Patch(color=NONPEAT)],
           [l for l, *_ in DEPTH] + ["Peat dome", "Not peat"], ncol=4)
    # 2 SKEG
    ax = axes[1]
    if have:
        paint(ax, [(burn(pk[pk.SKEG_2024.eq(v)], P), c) for _, v, c in SKEG], base=NONPEAT)
    frame(ax)
    legend(ax, [Patch(color=c) for *_, c in SKEG] + [Patch(color=NONPEAT)], [l for l, *_ in SKEG] + ["Not peat"], ncol=3)
    # 3 drainage
    ax = axes[2]
    if have:
        paint(ax, [(burn(P[P.KET_KANAL.eq(v)], P), c) for _, v, c in ZONE[::-1]], base=NONPEAT)
    overlay(ax, rivers, color="#2f6db3", linewidth=.9)
    cw = {"Kanal Primer": (.75, "#0b2a4a"), "Kanal Sekunder": (.4, "#24527f"), "Kanal Tersier": (.18, "#5d86ad")}
    if canals is not None and len(canals):
        for v, (lw, c) in sorted(cw.items(), key=lambda x: x[1][0]):
            overlay(ax, canals[canals.KET_KANAL.eq(v)], color=c, linewidth=lw)
    if brgm is not None and len(brgm):
        brgm.plot(ax=ax, color="#d1495b", markersize=.25, alpha=.8, aspect=None, zorder=4)
    frame(ax)
    legend(ax, [Patch(color=c) for *_, c in ZONE] + [Line2D([], [], color="#0b2a4a", lw=1), Line2D([], [], color="#5d86ad", lw=.5), Line2D([], [], color="#2f6db3", lw=1),
                Line2D([], [], marker="o", ls="", color="#d1495b", ms=2)],
           [l for l, *_ in ZONE] + ["Primary canal", "Other canal", "Large river", "BRGM structure"], ncol=2)
    # 4 land cover
    ax = axes[3]
    if have:
        pl = P.PL_2022.fillna("")
        lay, used = [], np.zeros(len(P), bool)
        for lab, f, c in LC:
            m = pl.map(f).values.astype(bool) & ~used
            lay.append((burn(P[m], P), c)); used |= m
        paint(ax, lay, base="#e3e1da")
    frame(ax)
    legend(ax, [Patch(color=c) for *_, c in LC] + [Patch(color="#e3e1da")], [l for l, *_ in LC] + ["Other or unmapped"], ncol=3)
    # 5 land status
    ax = axes[4]
    if have:
        kw = P.Fungsi_KWS.fillna("")
        sfm = burn(sf.reset_index(drop=True)) if sf is not None else None
        lim = burn(lic[lic.geom_type.isin(["Polygon", "MultiPolygon"])].reset_index(drop=True)) if lic is not None and len(lic) else None
        paint(ax, [(burn(P[kw.map(lambda x: any(x.startswith(k) for k in keys)).values], P), c) for _, keys, c in KWS], base="#f4efe6",
              pattern=[(lim, "#55524b", "back"), (sfm, "#2a78d6", "dots")])
    if sf is not None and len(sf):
        overlay(ax, sf.boundary, color="#2a78d6", linewidth=.35)
    if pt is not None and len(pt):
        overlay(ax, pt.boundary, color="#c2307a", linewidth=.6)
    if lic is not None and len(lic):
        lic = lic[lic.geom_type.isin(["Polygon", "MultiPolygon"]) & ~lic.is_empty]
        overlay(ax, lic.boundary, color="#3d3d3d", linewidth=.5)
    frame(ax)
    legend(ax, [Patch(color=c) for *_, c in KWS] + [Patch(facecolor="none", edgecolor="#55524b", hatch="\\\\\\"), Patch(facecolor="none", edgecolor="#2a78d6", hatch="...."),
                Patch(facecolor="none", edgecolor="#c2307a")],
           [l for l, *_ in KWS] + ["Business licence", "Social forestry", "PPTPKH"], ncol=3)
    # 6 fire and villages
    ax = axes[5]
    lay = [(peat_m, "#f7f4ec")]
    if burn_g is not None and len(burn_g):
        burn_g = burn_g.reset_index(drop=True)
        n = burn_g.BURN_FREQ.fillna("").str.extract(r"(\d+)")[0].astype(float).values
        lay += [(burn(burn_g[(n >= v) & (n < v + 1)] if v < 4 else burn_g[n >= 4], burn_g), c) for _, v, c in BURN]
    paint(ax, lay, base=NONPEAT)
    overlay(ax, roads, color="#8d8a80", linewidth=.25)
    if dmpg is not None and len(dmpg):
        overlay(ax, dmpg.boundary, color="#7b3fa0", linewidth=.5)
    if hot is not None and len(hot):
        hot.plot(ax=ax, color="#e8a33d", markersize=.8, aspect=None, zorder=4)
    frame(ax)
    legend(ax, [Patch(color=c) for *_, c in BURN] + [Line2D([], [], marker="o", ls="", color="#e8a33d", ms=2), Line2D([], [], color="#7b3fa0", lw=.6), Line2D([], [], color="#8d8a80", lw=.5)],
           [l for l, *_ in BURN] + ["Hotspot 2026", "DMPG village", "Road"], ncol=2)
    # scale bar on the first panel
    km = (x1 - x0) * 111.32 * np.cos(np.radians(lat))
    step = [1, 2, 5, 10, 20, 50, 100][int(np.searchsorted([1, 2, 5, 10, 20, 50, 100], km / 4))] if km > 4 else 1
    sx = x0 + (x1 - x0) * .03
    axes[0].plot([sx, sx + step / (111.32 * np.cos(np.radians(lat)))], [y0, y0], color=INK, lw=1.2)
    axes[0].text(sx, y0 + (y1 - y0) * .02, f"{step} km", fontsize=5.5, color=INK)
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=220, facecolor="white")
    plt.close(fig)
    return str(out_png)


def _one(a):
    code, out = a
    try:
        return code, render(code, out), None
    except Exception as e:
        return code, None, f"{type(e).__name__}: {e}"


def render_all(codes, outdir, workers=3, force=False):
    outdir = Path(outdir)
    todo = [(c, outdir / f"{c}_maps.png") for c in codes if force or not (outdir / f"{c}_maps.png").exists()]
    errs = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, (c, p, e) in enumerate(ex.map(_one, todo, chunksize=1)):
            if e:
                errs.append((c, e))
            if (i + 1) % 25 == 0:
                print(f"  maps {i + 1}/{len(todo)}", flush=True)
    return errs


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("codes", nargs="+")
    ap.add_argument("--out", type=Path, default=Path("."))
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    errs = render_all(a.codes, a.out, a.workers, a.force)
    for c, e in errs:
        print(c, e, file=sys.stderr)
    sys.exit(1 if errs else 0)
