"""Per-KHG settings of the full chain: re-peat/sites/<folder>/khg.yaml.

`init` writes one per KHG from what is found for it: the registry entry, the DEM clips of 01_dem/inputs (manifest.csv) with their
coverage, and the peat-depth raster that covers the KHG. Paths are written with ${REPEAT_DATA} / ${REPEAT_KHG}, so the file works
on any machine whose data folder has the same layout. An existing khg.yaml is kept unless overwrite is asked, so edits stay;
`overrides` takes any pipeline.yaml step key for this KHG only.
"""
from __future__ import annotations

import csv
import datetime
import glob
from pathlib import Path

import yaml

from .config import HUB, Settings, expand

NO_LIDAR = {"14.10.01": "the LiDAR is a 2 m DTM; left out by decision 2026-10-27"}


def K():
    from repeat_common import khg
    return khg


def khg_codes(s: Settings, codes: list[str] | None) -> list[str]:
    """Registry codes (without 'KHG.'): the given ones, else the confirmed rows of pipeline.khg_list plus extra_khg."""
    k = K()
    if codes:
        return [k.lookup(c)["khg_code"][4:] for c in codes]
    rows = list(csv.DictReader(open(HUB / s["khg_list"], encoding="utf-8")))
    names = [r["khg_name_in_gpkg"] for r in rows if r["match_status"].startswith("confirmed") and r["khg_name_in_gpkg"]]
    out = [k.lookup(n)["khg_code"][4:] for n in names] + [k.lookup(c)["khg_code"][4:] for c in s.get("extra_khg", [])]
    return list(dict.fromkeys(out))


def path_of(code: str) -> Path:
    return HUB / "sites" / K().folder_name(code) / "khg.yaml"


def _templated(p: str, s: Settings) -> str:
    """A path written with ${REPEAT_DATA} / ${REPEAT_KHG} instead of this machine's folders."""
    p = str(Path(p))
    for var, root in (("REPEAT_KHG", s.khg_root), ("REPEAT_DATA", s.data)):
        r = str(Path(root))
        if p.lower().startswith(r.lower()):
            return "${" + var + "}" + p[len(r):].replace("\\", "/")
    return p.replace("\\", "/")


def _manifest(folder: Path) -> list[dict]:
    f = folder / "01_dem" / "inputs" / "manifest.csv"
    return list(csv.DictReader(open(f, encoding="utf-8"))) if f.is_file() else []


def _dem(folder: Path, code: str, dem: str, min_cover: float) -> dict:
    rows = _manifest(folder)
    if dem == "lidar" and code in NO_LIDAR:
        return {"skip": NO_LIDAR[code]}
    rows = [r for r in rows if (r["product"].startswith("lidar") if dem == "lidar" else r["product"] == dem) and r.get("file")]
    if not rows:
        if not _manifest(folder):
            return {"skip": "01_dem/inputs has no clips yet (run the dem_inputs step)"}
        return {"skip": "no LiDAR in the data folder covers the KHG" if dem == "lidar" else f"no {dem} clip (see 01_dem/inputs/manifest.csv)"}
    best = max(rows, key=lambda r: float(r.get("cover_pct") or 0))
    cov = round(float(best.get("cover_pct") or 0), 1)
    d = {"product": best["product"], "clip": f"${{REPEAT_KHG}}/{folder.name}/01_dem/inputs/{best['file']}", "cover_pct": cov,
         "sources": ["${REPEAT_DATA}/" + x.strip() for x in best["sources"].split(";") if x.strip()]}
    if cov < min_cover:
        d["skip"] = f"covers {cov} % of the KHG (< {min_cover:g} %)"
    return d


def _khg_geometry(s: Settings, code: str):
    import geopandas as gpd
    from repeat_common import gee
    from repeat_common.fetch_gee_balance import khg_unit
    b = gpd.read_file(s.data / s["national"]["boundary"]["path"], layer=gee.BOUNDARY[1])
    u = khg_unit(b, gee.BOUNDARY[2], K().lookup(code))
    return None if u.empty else u.to_crs(4326).geometry.union_all()


def _peat_depth(s: Settings, geom) -> dict | None:
    """The raster whose valid cells cover most of the KHG (sampled on a 200 x 200 grid over the KHG), if at least half."""
    import numpy as np
    import rasterio
    from rasterio.warp import transform_bounds
    from shapely.geometry import box
    from shapely import contains_xy
    if geom is None:
        return None
    xmin, ymin, xmax, ymax = geom.bounds
    gx, gy = np.meshgrid(np.linspace(xmin, xmax, 200), np.linspace(ymin, ymax, 200))
    inside = contains_xy(geom, gx, gy)
    px, py = gx[inside], gy[inside]
    best, share = None, 0.0
    for d in s["national"]["peat_depth_dirs"]:
        for f in glob.glob(str(s.data / d / "**" / "*"), recursive=True):
            if not f.lower().endswith((".tif", ".img")):
                continue
            try:
                with rasterio.open(f) as r:
                    if r.crs is None or not geom.intersects(box(*transform_bounds(r.crs, "EPSG:4326", *r.bounds))):
                        continue
                    from rasterio.warp import transform
                    xs, ys = transform("EPSG:4326", r.crs, px.tolist(), py.tolist())
                    v = np.array([x[0] for x in r.sample(zip(xs, ys), masked=True)], dtype=object)
                    valid = np.array([not (np.ma.is_masked(x) or x is None) and np.isfinite(float(x)) and float(x) > 0 for x in v])
            except Exception:
                continue
            sh = float(valid.mean()) if len(valid) else 0.0
            if sh > share:
                best, share = f, sh
    if best is None or share < 0.5:
        return None
    return {"path": _templated(best, s), "scale": 0.01, "valid_share": round(share, 3)}


def build(s: Settings, code: str) -> dict:
    k = K()
    r = k.lookup(code)
    folder = k.folder(code)
    sel = {row["khg_name_in_gpkg"]: row for row in csv.DictReader(open(HUB / s["khg_list"], encoding="utf-8"))}.get(r["name"], {})
    geom = _khg_geometry(s, code)
    return {
        "khg": {"code": r["khg_code"][4:], "name": r["name"], "folder": folder.name, "province": sel.get("province", ""),
                "role": sel.get("role", "extra")},
        "dems": {d: _dem(folder, r["khg_code"][4:], d, float(s["dems"]["min_cover_pct"])) for d in s["dems"]["variants"]},
        "peat_depth": _peat_depth(s, geom),
        "canals": {"class_field": "KET_KANAL"},
        "overrides": {},
    }


HEADER = """# {name} (KHG.{code}): settings of the full RE-PEAT chain for this KHG; shared settings in re-peat/pipeline.yaml.
# Written by `python tools/khg_pipeline.py init` on {date} from the data found then (01_dem/inputs/manifest.csv, the peat-depth
# rasters in the data folder). Edit freely: `init` keeps this file unless --overwrite is given.
#   dems.<dem>.skip      the variant does not run, with the reason
#   peat_depth: null     no peat-depth raster covers the KHG; the criterion gets weight 0
#   overrides            any pipeline.yaml step key for this KHG only, e.g. {{delineation: {{min_area_km2: 50}}}}
"""


def write(s: Settings, code: str, overwrite: bool = False) -> tuple[Path, bool]:
    p = path_of(code)
    if p.exists() and not overwrite:
        return p, False
    c = build(s, code)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(HEADER.format(name=c["khg"]["name"], code=c["khg"]["code"], date=datetime.date.today().isoformat())
                 + yaml.safe_dump(c, sort_keys=False, allow_unicode=True, width=140), encoding="utf-8")
    return p, True


def load(s: Settings, code: str) -> dict:
    """khg.yaml with ${REPEAT_DATA}/${REPEAT_KHG} expanded; the pipeline steps merged with this KHG's overrides under 'settings'."""
    p = path_of(code)
    if not p.exists():
        raise SystemExit(f"{p} is missing; run: python tools/khg_pipeline.py init --khg {code}")
    c = expand(yaml.safe_load(p.read_text(encoding="utf-8")), {"REPEAT_DATA": str(s.data), "REPEAT_KHG": str(s.khg_root)})
    from .config import _merge
    c["settings"] = {k: _merge(s.get(k) or {}, (c.get("overrides") or {}).get(k) or {}) if isinstance(s.get(k), dict) else s.get(k)
                     for k in ("dem_correction", "delineation", "neraca", "prioritisation", "pump")}
    return c
