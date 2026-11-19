#!/usr/bin/env python3
"""Worked example for Annex C of the prioritisation report: the peat points of one KHG with their land claims (tenure complexity)
and their distances to the nearest large river or lake and road (feasibility), computed with the same functions as the national run.

  python tools/technical_example.py --config <repeat-prioritisation>/configs/examples/national_profile.yaml [--khg KHG.61.12-71.01]

Writes <out>/technical_example/<khg>_points.csv and <khg>_meta.json, read by prioritisation_report.py.
"""
import argparse
import copy
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
import yaml

from repeat_prioritisation.national import final_inputs as FI
from repeat_prioritisation.national import land as L
from repeat_prioritisation.national import overlay as O
from repeat_prioritisation.national import profile as P
from repeat_prioritisation.national import tenure_complexity as TC


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--khg", default="KHG.61.12-71.01")
    a = ap.parse_args(argv)
    cfg = L.load_cfg(a.config)                 # as repeat-national-tenure-complexity loads it (overlay inputs included)
    k = P.load_khg(cfg, {a.khg})
    r = k.iloc[0]
    out, cc, pts, info = TC.one(cfg, r.khg_id, r.nama, r.geometry, points=True)
    data, lay = Path(cfg["data"]), cfg["final"]["inputs_layers"]
    g = shapely.make_valid(r.geometry)
    pm = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts.lon, pts.lat), crs=4326).to_crs(FI.METRIC)
    x0, y0, x1, y1 = g.bounds
    riv = pyogrio.read_dataframe(data / lay["rivers"], mask=shapely.box(x0 - 1, y0 - 1, x1 + 1, y1 + 1), columns=[])
    lak = pyogrio.read_dataframe(data / lay["lakes"], mask=shapely.box(x0 - 1, y0 - 1, x1 + 1, y1 + 1), columns=[])
    water = gpd.GeoDataFrame(pd.concat([riv[["geometry"]], lak[["geometry"]]], ignore_index=True), geometry="geometry", crs=4326).to_crs(FI.METRIC)
    rd = pyogrio.read_dataframe(data / lay["roads"], mask=shapely.box(x0 - .5, y0 - .5, x1 + .5, y1 + .5), columns=["NAMA_UNSUR"])
    rd = rd[rd.NAMA_UNSUR.isin(lay["road_classes"])]
    pts["water_km"] = FI._nearest_km(pm, water, 110.0)
    pts["road_km"] = FI._nearest_km(pm, rd.to_crs(FI.METRIC) if len(rd) else None, 55.0)
    od = Path(cfg["out"]) / "technical_example"
    od.mkdir(parents=True, exist_ok=True)
    pts.to_csv(od / f"{a.khg}_points.csv", index=False, float_format="%.6g")
    meta = {"khg": a.khg, "name": r.nama, "cell_m": info["cell_m"], "n_holders": len(info["holders"]), "indicators": out,
            "water_median_km": float(np.median(pts.water_km)), "road_median_km": float(np.median(pts.road_km))}
    (od / f"{a.khg}_meta.json").write_text(json.dumps(meta, indent=1, default=float), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k != "indicators"}, default=float), {k: out[k] for k in ("c_licence_community", "c_contested", "c_claims_mean", "c_holders")})


if __name__ == "__main__":
    main()
