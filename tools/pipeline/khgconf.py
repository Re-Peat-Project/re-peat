"""Per-KHG settings of the full chain, in three layers:

  re-peat/pipeline.yaml                 the national template: every setting shared by all KHG
  re-peat/sites/<folder>/khg.yaml       generated facts of one KHG, never edited by hand (init rewrites it): registry entry, time
                                        zone and UTM zone, the DEM clips of 01_dem/inputs (manifest.csv) or, before they exist, the
                                        planned variants from sites/khg_availability.csv, the peat-depth source and the facts of the
                                        availability table (tools/khg_availability.py, tools/khg_availability_ee.py)
  re-peat/sites/<folder>/overrides.yaml hand-written exceptions only, each with a reason and a date; init never touches it.
                                        Top-level keys are merged into khg.yaml (e.g. dems.lidar.skip), except `steps`, which takes
                                        any pipeline.yaml step key for this KHG (e.g. steps: {delineation: {min_area_km2: 50}})
Paths are written with ${REPEAT_DATA} / ${REPEAT_KHG}, so the files work on any machine whose data folder has the same layout.
A legacy `overrides:` key inside khg.yaml is still read as step overrides.
"""
from __future__ import annotations

import csv
import datetime
import glob
import os
from pathlib import Path

import yaml

from .config import HUB, Settings, expand

AVAILABILITY = HUB / "sites" / "khg_availability.csv"


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


def _availability(code: str) -> dict:
    """The KHG's row of sites/khg_availability.csv (empty if the table or the row is missing)."""
    if not AVAILABILITY.is_file():
        return {}
    for r in csv.DictReader(open(AVAILABILITY, encoding="utf-8")):
        if r["code"] == code:
            return r
    return {}


def _f(r: dict, k: str, nd: int = 3):
    try:
        v = round(float(r[k]), nd)
        return int(v) if nd == 0 else v
    except (KeyError, TypeError, ValueError):
        return None


def _planned_dem(av: dict, dem: str, min_cover: float) -> dict:
    """Before the dem_inputs step: whether the variant should run, from the availability table."""
    share = {"deltadtm": _f(av, "deltadtm_share"), "lidar": _f(av, "lidar_share"), "demnas": 1.0}.get(dem)
    if share is None:
        return {"skip": "01_dem/inputs has no clips yet (run the dem_inputs step)"}
    d = {"planned": True, "cover_pct": round(100 * share, 1)}
    if 100 * share < min_cover:
        d["skip"] = (f"covers {100 * share:.1f} % of the KHG (< {min_cover:g} %, sites/khg_availability.csv)" if dem != "lidar" or share > 0
                     else "no LiDAR in the data folder covers the KHG")
    return d


def _dem(folder: Path, code: str, dem: str, min_cover: float) -> dict:
    rows = _manifest(folder)
    rows = [r for r in rows if (r["product"].startswith("lidar") if dem == "lidar" else r["product"] == dem) and r.get("file")]
    if not rows:
        if not _manifest(folder):
            return _planned_dem(_availability(code), dem, min_cover)
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


TZ_HOURS = (("maluku", 9), ("papua", 9), ("kalimantan selatan", 8), ("kalimantan timur", 8), ("kalimantan utara", 8),
            ("sulawesi", 8), ("gorontalo", 8), ("bali", 8), ("nusa tenggara", 8))


def tz_hours(province: str) -> int:
    """UTC offset of the province (the first one named): WIT 9, WITA 8, else WIB 7."""
    import re
    p = re.split(r"[,;/]", str(province).lower().strip(' "'))[0].strip()
    return next((h for key, h in TZ_HOURS if p.startswith(key)), 7)


def _peat_from_availability(s: Settings, av: dict, geom) -> dict | None:
    """The peat-depth source of the availability table; the modelled raster keeps its path and its valid share."""
    src = av.get("peat_depth_source")
    if not src:
        return _peat_depth(s, geom)
    if src == "modelled raster":
        return {"source": src, "path": "${REPEAT_DATA}/" + av["peat_model_file"], "scale": 0.01, "valid_share": _f(av, "peat_model_share")}
    share = {"FEG 50k classes": "feg50k_share", "BBSDLP classes": "bbsdlp_share"}.get(src)
    return {"source": src, "scale": 0.01, **({"cover_share": _f(av, share)} if share else {"confidence": "low"})}


def _peat_fallback(av: dict) -> dict:
    """Peat depth without the modelled raster: KLHK FEG 1:50k classes, BBSDLP classes, then PEATGRIDS (the order of
    tools/khg_availability.py), each where it covers at least half the KHG."""
    for src, share in (("FEG 50k classes", "feg50k_share"), ("BBSDLP classes", "bbsdlp_share")):
        if (_f(av, share) or 0) >= 0.5:
            return {"source": src, "scale": 0.01, "cover_share": _f(av, share)}
    return {"source": "PEATGRIDS (low confidence)", "scale": 0.01, "confidence": "low"}


def build(s: Settings, code: str) -> dict:
    k = K()
    r = k.lookup(code)
    folder = k.folder(code)
    sel = {row["khg_name_in_gpkg"]: row for row in csv.DictReader(open(HUB / s["khg_list"], encoding="utf-8"))}.get(r["name"], {})
    av = _availability(r["khg_code"][4:])
    geom = None if av else _khg_geometry(s, code)
    prov = r.get("province") or sel.get("province", "")
    facts = {}
    if av:
        facts = {"run_class": av.get("run_class"), "area_ha": _f(av, "area_ha", 0), "deltadtm_share": _f(av, "deltadtm_share"),
                 "lidar_share": _f(av, "lidar_share"), "canal_km_total": _f(av, "canal_km_total", 1), "blocks_brgm": _f(av, "blocks_brgm", 0),
                 "licence_share_managed": _f(av, "licence_share_managed"),
                 "stations_community": _f(av, "stations_community", 0), "stations_concession": _f(av, "stations_concession", 0),
                 "dry_window": f"{av.get('dry_first')} to {av.get('dry_last')}" if av.get("dry_first") else None,
                 "dry_shortfall_mm_2018_2025": _f(av, "dry_shortfall_mm", 0)}
    return {
        "khg": {"code": r["khg_code"][4:], "name": r["name"], "folder": folder.name, "island": r.get("island", ""), "province": prov,
                "kabupaten": r.get("kabupaten", ""), "role": sel.get("role", "national"), "tz_hours": tz_hours(prov),
                **({"utm_epsg": int(float(av["utm_epsg"]))} if av.get("utm_epsg") else {})},
        "dems": {d: _dem(folder, r["khg_code"][4:], d, float(s["dems"]["min_cover_pct"])) for d in s["dems"]["variants"]},
        "peat_depth": _peat_from_availability(s, av, geom),
        "canals": {"class_field": "KET_KANAL"},
        "facts": facts,
    }


HEADER = """# {name} (KHG.{code}): generated facts of the full RE-PEAT chain for this KHG; shared settings in re-peat/pipeline.yaml.
# Written by `python tools/khg_pipeline.py init` on {date} from the data found then (sites/khg_availability.csv, 01_dem/inputs/manifest.csv).
# Do not edit: init rewrites it. Exceptions go in overrides.yaml next to this file (with a reason and a date).
#   dems.<dem>.skip      the variant does not run, with the reason; planned: true until the dem_inputs step has clipped the DEM
#   peat_depth.source    modelled raster, FEG 50k classes, BBSDLP classes or PEATGRIDS (low confidence); the local_inputs step writes
#                        00_inputs/peat_depth.tif from it (tools/pipeline/peat_depth.py)
#   facts                from the availability table, for planning and reports; no step reads them
"""


def write(s: Settings, code: str, overwrite: bool = False) -> tuple[Path, bool]:
    """khg.yaml from the data; an existing one is rewritten only with overwrite (it holds no hand edits since overrides.yaml)."""
    p = path_of(code)
    if p.exists() and not overwrite:
        return p, False
    c = build(s, code)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(HEADER.format(name=c["khg"]["name"], code=c["khg"]["code"], date=datetime.date.today().isoformat())
                 + yaml.safe_dump(c, sort_keys=False, allow_unicode=True, width=140), encoding="utf-8")
    return p, True


def override_files(p: Path, code: str) -> list[Path]:
    """Overrides of one KHG, merged in this order: sites/<folder>/overrides.yaml (tracked), then the peer's own
    $REPEAT_OVERRIDES/<code>.yaml or $REPEAT_OVERRIDES/<folder>.yaml (a folder mounted into the container)."""
    out = [p.with_name("overrides.yaml")]
    peer = os.environ.get("REPEAT_OVERRIDES")
    if peer:
        out += [Path(peer) / f"{code}.yaml", Path(peer) / f"{p.parent.name}.yaml"]
    return [f for f in out if f.is_file()]


def load(s: Settings, code: str) -> dict:
    """khg.yaml with ${REPEAT_DATA}/${REPEAT_KHG} expanded; the pipeline steps merged with this KHG's overrides under 'settings'."""
    p = path_of(code)
    if not p.exists():
        raise SystemExit(f"{p} is missing; run: python tools/khg_pipeline.py init --khg {code}")
    env = {"REPEAT_DATA": str(s.data), "REPEAT_KHG": str(s.khg_root)}
    c = expand(yaml.safe_load(p.read_text(encoding="utf-8")), env)
    from .config import _merge
    folder = s.khg_root / c["khg"]["folder"]
    if any((e or {}).get("planned") for e in (c.get("dems") or {}).values()) and (folder / "01_dem" / "inputs" / "manifest.csv").is_file():
        # khg.yaml still lists planned DEMs, but this machine's dem_inputs step has clipped them (a container whose sites/ is
        # not kept between runs): the variants come from the work folder's manifest, as `init` would write them
        c["dems"] = expand({d: _dem(folder, c["khg"]["code"], d, float(s["dems"]["min_cover_pct"])) for d in c["dems"]}, env)
    pd_ = c.get("peat_depth") or {}
    if pd_.get("source") == "modelled raster" and pd_.get("path") and not Path(pd_["path"]).is_file():
        # the modelled raster is not in this data folder (a peer's): the next source of the agreed order for this KHG
        c["peat_depth"] = {**_peat_fallback(_availability(c["khg"]["code"])),
                           "note": f"fallback: {Path(pd_['path']).name} is not in this data folder"}
    ov = {}
    for ov_file in override_files(p, c["khg"]["code"]):
        ov = _merge(ov, expand(yaml.safe_load(ov_file.read_text(encoding="utf-8")) or {}, env))
    step_ov = _merge(c.get("overrides") or {}, ov.get("steps") or {})          # legacy khg.yaml key, then overrides.yaml
    for key, val in ov.items():
        if key != "steps":
            c[key] = _merge(c.get(key) or {}, val) if isinstance(val, dict) and isinstance(c.get(key), dict) else val
    c["settings"] = {k: _merge(s.get(k) or {}, step_ov.get(k) or {}) if isinstance(s.get(k), dict) else s.get(k)
                     for k in ("dem_correction", "delineation", "neraca", "prioritisation", "pump")}
    return c
