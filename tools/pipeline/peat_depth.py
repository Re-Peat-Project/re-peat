"""The KHG's peat-depth raster, 00_inputs/peat_depth.tif, from the source khg.yaml names (peat_depth.source).

Sources, in the order tools/khg_availability.py picks them (the first covering at least half the KHG):
  modelled raster   a per-KHG modelled raster in the data folder (peat_depth.path), window on its own grid, nothing resampled
  FEG 50k classes   KLHK peat ecosystem function 1:50,000 (klhk_khg_feg_50k.gpkg, layer feg_50k, field peat_thick, classes such as
                    "1,0 - 1,5 meter"): class midpoints, "0,0 meter" as 0, "> 14 meter" as 15 m (assumed)
  BBSDLP classes    kedalaman_gambut_bbsdlp.gpkg, field KODE_GBT D1-D6: the class midpoints repeat-neraca uses for its fallback
                    (model.BBSDLP_DEPTH_M; D6, > 700 cm, as 8 m assumed)
  PEATGRIDS         PEATGRIDS v2.0.1 thickness (projects/sat-io/open-datasets/PEATGRIDS/THICKNESS_CM, band THICKNESS_CM_MEAN, 1 km,
                    CC BY 4.0) from Earth Engine on its own grid; low confidence (regional R2 0.21-0.61,
                    re-peat/docs/research/national_peat_depth_sources.md)
Every output is float32 in cm (khg.yaml peat_depth.scale 0.01, as the modelled rasters), nodata -9999. Class sources are rasterised
on a 30 m grid in the KHG's UTM zone over the buffered KHG (vector classes have no grid of their own); cells no polygon covers stay
nodata, so the modules' own fallbacks (repeat-neraca --depth-fallback, the KHG median) still apply there.
"""
from __future__ import annotations

import re
from pathlib import Path

FEG = ("klhk_khg_feg_50k.gpkg", "feg_50k", "peat_thick")
BBSDLP = ("kedalaman_gambut_bbsdlp.gpkg", "KODE_GBT")
BBSDLP_DEPTH_M = {"D1": 0.75, "D2": 1.5, "D3": 2.5, "D4": 4.0, "D5": 6.0, "D6": 8.0}   # as repeat_neraca.model.BBSDLP_DEPTH_M
PEATGRIDS = ("projects/sat-io/open-datasets/PEATGRIDS/THICKNESS_CM", "THICKNESS_CM_MEAN")
GRID_M = 30.0
NODATA = -9999.0
SOURCES = ("modelled raster", "FEG 50k classes", "BBSDLP classes", "PEATGRIDS (low confidence)")


def feg_class_m(s) -> float | None:
    """Midpoint (m) of a FEG peat_thick class such as '1,0 - 1,5 meter', '0,0 meter' or '> 14 meter'."""
    if s is None:
        return None
    t = str(s).strip().replace(",", ".")
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", t)]
    if not nums:
        return None
    if t.startswith(">"):
        return nums[0] + 1.0
    return sum(nums[:2]) / len(nums[:2])


def _grid(area):
    """30 m grid in the UTM zone of the area (EPSG:4326 polygon): (crs, transform, width, height)."""
    import geopandas as gpd
    from rasterio.transform import from_origin
    import math
    g = gpd.GeoSeries([area], crs=4326)
    utm = g.estimate_utm_crs()
    x0, y0, x1, y1 = g.to_crs(utm).total_bounds
    x0, y1 = math.floor(x0 / GRID_M) * GRID_M, math.ceil(y1 / GRID_M) * GRID_M
    w, h = int(math.ceil((x1 - x0) / GRID_M)), int(math.ceil((y1 - y0) / GRID_M))
    return utm, from_origin(x0, y1, GRID_M, GRID_M), w, h


def _write(dst: Path, arr, crs, transform, tags: dict) -> None:
    import rasterio
    dst.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dst, "w", driver="GTiff", width=arr.shape[1], height=arr.shape[0], count=1, dtype="float32", crs=crs,
                       transform=transform, nodata=NODATA, compress="deflate", tiled=True, blockxsize=256, blockysize=256) as o:
        o.write(arr.astype("float32"), 1)
        o.update_tags(units="cm", **tags)


def _rasterise(gdf, values_cm, area, dst: Path, tags: dict) -> tuple[int, int]:
    import numpy as np
    from rasterio.features import rasterize
    crs, tf, w, h = _grid(area)
    g = gdf.to_crs(crs)
    arr = rasterize([(geom, v) for geom, v in zip(g.geometry, values_cm) if geom is not None and v is not None and np.isfinite(v)],
                    out_shape=(h, w), transform=tf, fill=NODATA, dtype="float32")
    _write(dst, arr, crs, tf, tags)
    return w, h


def build(data: Path, peat: dict, area, dst: Path, clip_raster) -> tuple[str, str]:
    """Write dst from peat (khg.yaml peat_depth); returns (source note, size note) for local_manifest.csv."""
    import geopandas as gpd
    src = peat.get("source") or ("modelled raster" if peat.get("path") else None)
    if src == "modelled raster":
        p = Path(peat["path"])
        w, h = clip_raster(p, dst, area)
        return (str(p.relative_to(data)).replace("\\", "/") if p.is_relative_to(data) else str(p)), f"{w}x{h}"
    if src == "FEG 50k classes":
        f = gpd.read_file(data / FEG[0], layer=FEG[1], bbox=area.bounds)
        f = f[f.intersects(area)]
        w, h = _rasterise(f, [None if (m := feg_class_m(x)) is None else m * 100 for x in f[FEG[2]]], area, dst,
                          {"source": f"{FEG[0]} layer {FEG[1]}, {FEG[2]} class midpoints"})
        return f"{FEG[0]} ({FEG[1]}.{FEG[2]}), class midpoints, 30 m", f"{w}x{h}"
    if src == "BBSDLP classes":
        f = gpd.read_file(data / BBSDLP[0], bbox=area.bounds)
        f = f[f.intersects(area) & f[BBSDLP[1]].isin(BBSDLP_DEPTH_M)]
        w, h = _rasterise(f, [BBSDLP_DEPTH_M[k] * 100 for k in f[BBSDLP[1]]], area, dst,
                          {"source": f"{BBSDLP[0]}, {BBSDLP[1]} class midpoints"})
        return f"{BBSDLP[0]} ({BBSDLP[1]}), class midpoints, 30 m", f"{w}x{h}"
    if src and src.startswith("PEATGRIDS"):
        from repeat_common import gee
        ee = gee.init()
        img = ee.Image(PEATGRIDS[0]).select(PEATGRIDS[1])
        gee.to_geotiff(img, area, dst, dtype="float32", nodata=NODATA, source=PEATGRIDS[0])
        return f"Earth Engine {PEATGRIDS[0]} ({PEATGRIDS[1]}), native 1 km grid, low confidence", ""
    raise ValueError(f"unknown peat_depth source {src!r}; one of {SOURCES}")
