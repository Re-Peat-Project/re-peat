"""KHG attributes for KLH's priorities: which of the 865 KHG are KLH's 337 work-list KHG and the 362 priority KHG of the PPEG analysis.

    python re-peat/tools/khg_klh_priority.py

Inputs (all already in the project, nothing recomputed here):
  _data/batas_khg_indonesia.gpkg                         the 865 KHG polygons (NAMA_KHG, Luas__HA)
  reports/investigations/khg337_tim_gis.csv              KLH/team work list of 337 KHG (tools/inventory_337khg.py, from
                                                         'Tim GIS - Intervensi Pembasahan Karhutla pada 337 KHG (2004 Desa DMPG), Sept 2026.xlsx')
  reports/national_profile/ppeg/ppeg_khg.csv             per-KHG sums of the PPEG analysis (repeat-national-ppeg): priority flag,
                                                         reasons (target villages, SKEG 2024 damage), rank and priority area
Writes:
  sites/khg_klh_priority.csv                             one row per KHG (865), tracked
  $REPEAT_DATA/derived/khg_klh_priority.gpkg (layer khg) the KHG polygons with the same attributes, for maps and overlays
Columns: khg_code, khg_name, island, provinces, area_ha_sk (Luas__HA of the boundary file),
  klh_337 (in the 337 work list), klh_337_no, klh_337_team, klh_337_area_ha and klh_337_c01..c04_ha (the workbook's areas in
  the four intervention classes, inside the 2,004 target villages), klh_priority_362, priority_reason, priority_rank,
  target_village_ha, priority_ha (SKEG 2024 damaged peat), priority_in_target_villages_ha.
"""
import os
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

HUB = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("REPEAT_DATA", HUB.parent / "_data"))
KHG = DATA / "batas_khg_indonesia.gpkg"
L337 = HUB / "reports" / "investigations" / "khg337_tim_gis.csv"
PPEG = HUB / "reports" / "national_profile" / "ppeg" / "ppeg_khg.csv"
CSV = HUB / "sites" / "khg_klh_priority.csv"
GPKG = DATA / "derived" / "khg_klh_priority.gpkg"


def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().casefold()


def flag(v):
    return str(v).strip().lower() in ("true", "1", "yes")


def main():
    khg = gpd.read_file(KHG, engine="pyogrio")
    ppeg = pd.read_csv(PPEG)
    ppeg = ppeg[ppeg.khg_code.astype(str).str.startswith("KHG.")]
    l337 = pd.read_csv(L337)
    name2code = dict(zip(ppeg.khg_name.map(norm), ppeg.khg_code))
    khg["khg_code"] = khg.NAMA_KHG.map(norm).map(name2code)
    miss = khg[khg.khg_code.isna()]
    if len(miss):
        raise SystemExit(f"{len(miss)} KHG polygons not matched to a code: {list(miss.NAMA_KHG)[:5]}")
    if khg.khg_code.duplicated().any():
        raise SystemExit(f"duplicate codes: {list(khg.khg_code[khg.khg_code.duplicated()])}")
    out = khg[["khg_code", "NAMA_KHG", "Luas__HA", "geometry"]].rename(columns={"NAMA_KHG": "khg_name", "Luas__HA": "area_ha_sk"})
    p = ppeg.set_index("khg_code")
    out["island"] = out.khg_code.map(p.island)
    out["provinces"] = out.khg_code.map(p.provinces)
    w = l337.set_index("khg_code")
    out["klh_337"] = out.khg_code.isin(w.index)
    out["klh_337_no"] = out.khg_code.map(w["no"]).astype("Int64")
    out["klh_337_team"] = out.khg_code.map(w["team"])
    out["klh_337_area_ha"] = out.khg_code.map(w["total"])
    for c in ("c01", "c02", "c03", "c04"):
        out[f"klh_337_{c}_ha"] = out.khg_code.map(w[c])
    tv = out.khg_code.map(p.in_target_villages).map(flag)
    sk = out.khg_code.map(p.has_skeg_damage).map(flag)
    out["klh_priority_362"] = out.khg_code.map(p.priority).map(flag)
    out["priority_reason"] = [" + ".join(r for r, f in (("target villages", a), ("SKEG 2024 damage", b)) if f) for a, b in zip(tv, sk)]
    out["priority_rank"] = out.khg_code.map(p.priority_rank).astype("Int64")
    for c in ("target_village_ha", "priority_ha", "priority_in_target_villages_ha"):
        out[c] = out.khg_code.map(p[c]).round(2)
    out = out.sort_values("khg_code").reset_index(drop=True)
    unmatched_337 = sorted(set(w.index) - set(out.khg_code))
    if unmatched_337:
        raise SystemExit(f"337 list codes not in the boundary file: {unmatched_337}")
    pd.DataFrame(out.drop(columns="geometry")).to_csv(CSV, index=False)
    GPKG.parent.mkdir(parents=True, exist_ok=True)
    if GPKG.exists():
        GPKG.unlink()
    out.to_file(GPKG, layer="khg", driver="GPKG")
    n337, n362 = int(out.klh_337.sum()), int(out.klh_priority_362.sum())
    both = int((out.klh_337 & out.klh_priority_362).sum())
    print(f"{len(out)} KHG; in the 337 list: {n337}; priority (362): {n362}; both: {both}; "
          f"337 area {out.klh_337_area_ha.sum():,.0f} ha")
    print(f"wrote {CSV} and {GPKG}")


if __name__ == "__main__":
    main()
