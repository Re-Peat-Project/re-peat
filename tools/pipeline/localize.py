"""Make a KHG work folder self-contained: clip every nationwide input the chain reads into <khg>/00_inputs/, so the folder alone (with
the repositories and internet access for the online sources) is enough to run the chain on another machine.

Written by the `local_inputs` step (tools/khg_pipeline.py), into <khg>/00_inputs/:

    national/            the national files the prioritisation's national layers read (repeat-prioritisation national.profile),
                         clipped to the KHG plus BUFFER_M, under their national file names: burnt area, VIIRS hotspots, this year's
                         KLH hotspots (every monthly layer), canals, existing infrastructure, target villages, the national peat-depth
                         polygons, the DPG village list, and the peat-extent rasters (GFW composite, Global Peatland Map)
    feg_protected.gpkg   the peat ecosystem function (FEG 2017) polygons, for the protected share
    peat_depth.tif       the KHG's peat-depth raster (the one khg.yaml names), window on its own grid, nothing resampled
    sitmat/              the SiTMAT stations inside the KHG plus BUFFER_M and their daily readings, same files as
                         repeat-sitmat/sitmat_out/processed (stations.csv, stations_geo.csv, daily_long.csv)
    icesat2_atl08.gpkg   the ICESat-2 ground points of the KHG (copied from the data folder; the icesat2 step fetches them first)
    local_manifest.csv   what each file is, where it came from, its size and sha256

Vector features that touch the buffered KHG are kept whole. Raster windows keep the source grid, data type and nodata.
"""
from __future__ import annotations

import csv
import hashlib
import shutil
from pathlib import Path

BUFFER_M = 5000

NATIONAL = {   # key of national.profile DEFAULTS["inputs"] -> file in the data folder
    "burned": "burnt_area_2015_2026_Indonesia.gpkg",
    "hotspots": "hotspot_viirs_snpp_2012_2025.gpkg",
    "hotspots_now": "hotspots_modis_2026.gpkg",
    "canals": "kanal_osgm_khg_existing_Indonesia.gpkg",
    "blocks": "infrastruktur_hidrologis_existing_BRGM_Indonesia.gpkg",
    "villages": "desa_target_pemulihan_ekosistem_gambut.gpkg",
    "peat_depth": "kedalaman_gambut_bbsdlp.gpkg",
}
NATIONAL_COPY = {"dmpg": "dpg/dmpg_villages_sitmat.gpkg"}          # small tables, copied whole
NATIONAL_RASTERS = {"extent": "peat_extent_gfw_v20230315_z11.tif", "global": "peat_extent_gpm2022_1km.tif"}
FEG = "landstatus/FEG__Indonesia__2017__Rev_Tipologi.gpkg"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(1 << 22):
            h.update(b)
    return h.hexdigest()


def _area(khg_gpkg: Path):
    """The KHG polygon buffered by BUFFER_M, in EPSG:4326."""
    import geopandas as gpd
    g = gpd.read_file(khg_gpkg)
    utm = g.estimate_utm_crs()
    return g.to_crs(utm).buffer(BUFFER_M).to_crs(4326).union_all()


def clip_vector(src: Path, dst: Path, area) -> int:
    """Every layer of ``src`` cut to the features touching ``area`` (EPSG:4326 polygon); returns the number of features written."""
    import geopandas as gpd
    import pyogrio
    from shapely.ops import transform as stransform
    import pyproj
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    n = 0
    for layer, _ in pyogrio.list_layers(src):
        info = pyogrio.read_info(src, layer=layer)
        crs = info["crs"] or "EPSG:4326"
        a = area
        if pyproj.CRS(crs) != pyproj.CRS(4326):
            t = pyproj.Transformer.from_crs(4326, crs, always_xy=True).transform
            a = stransform(t, area)
        g = pyogrio.read_dataframe(src, layer=layer, bbox=a.bounds)
        if len(g):
            g = g[g.intersects(a)]
        if len(g) or not n:                                   # keep empty layers too, so the reader finds them
            pyogrio.write_dataframe(gpd.GeoDataFrame(g, geometry=g.geometry.name, crs=crs) if len(g) else g, dst, layer=layer,
                                    driver="GPKG", append=dst.exists())
        n += len(g)
    return n


def clip_raster(src: Path, dst: Path, area) -> tuple[int, int]:
    """The window of ``src`` covering ``area`` (EPSG:4326), on the source grid; written as GeoTIFF."""
    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds
    with rasterio.open(src) as r:
        b = transform_bounds("EPSG:4326", r.crs, *area.bounds)
        w = from_bounds(*b, transform=r.transform).round_offsets().round_lengths().intersection(
            rasterio.windows.Window(0, 0, r.width, r.height))
        prof = r.profile.copy()
        prof.update(driver="GTiff", width=int(w.width), height=int(w.height), transform=r.window_transform(w), compress="deflate",
                    tiled=True, blockxsize=256, blockysize=256, BIGTIFF="IF_SAFER")
        dst.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(dst, "w", **prof) as o:
            o.write(r.read(window=w))
    return int(w.width), int(w.height)


def clip_sitmat(src: Path, dst: Path, area) -> int:
    """The SiTMAT stations inside ``area`` and their readings, in the files of the processed SiTMAT folder."""
    import pandas as pd
    from shapely import contains_xy
    dst.mkdir(parents=True, exist_ok=True)
    st = pd.read_csv(src / "stations.csv")
    keep = st[contains_xy(area, st["lon"].to_numpy(dtype=float), st["lat"].to_numpy(dtype=float))]
    keep.to_csv(dst / "stations.csv", index=False)
    key = set(zip(keep["kind"].astype(str), keep["station_id"].astype(str)))
    for name in ("stations_geo.csv", "daily_long.csv"):
        f = src / name
        if f.exists():
            t = pd.read_csv(f)
            t[[(str(k), str(s)) in key for k, s in zip(t["kind"], t["station_id"])]].to_csv(dst / name, index=False)
    return len(keep)


def localize(data: Path, kf: Path, peat_depth: str | None, icesat2: Path | None, sitmat: Path | None) -> Path:
    """Write <kf>/00_inputs/{national, feg_protected.gpkg, peat_depth.tif, sitmat, icesat2_atl08.gpkg, local_manifest.csv}."""
    inp = kf / "00_inputs"
    area = _area(inp / "khg.gpkg")
    rows = []

    def note(path: Path, source: str, what: str, count=""):
        rows.append({"file": str(path.relative_to(inp)).replace("\\", "/"), "source": source, "what": what, "count": count,
                     "bytes": path.stat().st_size if path.is_file() else "", "sha256": _sha(path) if path.is_file() else ""})

    for key, name in NATIONAL.items():
        if (data / name).exists():
            n = clip_vector(data / name, inp / "national" / name, area)
            note(inp / "national" / name, name, f"national.profile input '{key}', clipped", n)
    for key, name in NATIONAL_COPY.items():
        if (data / name).exists():
            (inp / "national" / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(data / name, inp / "national" / name)
            note(inp / "national" / name, name, f"national.profile input '{key}', copied whole")
    for key, name in NATIONAL_RASTERS.items():
        if (data / name).exists():
            w, h = clip_raster(data / name, inp / "national" / name, area)
            note(inp / "national" / name, name, f"peat {key} raster, window", f"{w}x{h}")
    if (data / FEG).exists():
        note(inp / "feg_protected.gpkg", FEG, "peat ecosystem function (protected share)", clip_vector(data / FEG, inp / "feg_protected.gpkg", area))
    if peat_depth and Path(peat_depth).exists():
        w, h = clip_raster(Path(peat_depth), inp / "peat_depth.tif", area)
        note(inp / "peat_depth.tif", str(Path(peat_depth).relative_to(data)).replace("\\", "/") if str(peat_depth).startswith(str(data)) else peat_depth,
             "peat depth raster of the KHG, window", f"{w}x{h}")
    if sitmat and sitmat.is_dir():
        note(inp / "sitmat" / "stations.csv", "SiTMAT processed (repeat-sitmat)", "SiTMAT stations in the KHG", clip_sitmat(sitmat, inp / "sitmat", area))
    if icesat2 and icesat2.exists():
        if icesat2.resolve() != (inp / "icesat2_atl08.gpkg").resolve():          # a rerun finds the KHG's copy already there
            shutil.copy2(icesat2, inp / "icesat2_atl08.gpkg")
        src = str(icesat2.relative_to(data)).replace("\\", "/") if icesat2.is_relative_to(data) else "00_inputs (earlier copy)"
        note(inp / "icesat2_atl08.gpkg", src, "ICESat-2 ATL08 ground points")
    out = inp / "local_manifest.csv"
    if out.exists():                    # keep rows other tools added (e.g. field_wtd.csv of repeat_neraca.groundwater.fieldobs) while their file is there
        with open(out, newline="", encoding="utf-8") as fh:
            mine = {r["file"] for r in rows}
            rows += [r for r in csv.DictReader(fh) if r["file"] not in mine and (inp / r["file"]).exists()]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "source", "what", "count", "bytes", "sha256"])
        w.writeheader()
        w.writerows(rows)
    return out
