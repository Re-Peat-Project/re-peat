"""Data package of the national fire breakdown (burned area and hotspots by land status) for partners such as the World Bank.

    python re-peat/tools/export_fire_data.py [--out DIR] [--no-rasters] [--no-zip]

Packs $REPEAT_WORK/national_profile/fire_landstatus with repeat_prioritisation.national.fire_export (tables as CSV and Excel,
tallies, checks, layers, data dictionary) and adds the KLH PPEG summaries behind the priority-KHG chapters (extra/). Sources are
written for the reader (SOURCES, from re-peat/sites/data_catalog.csv). Writes
DIR/RE-PEAT_fire_land_status_data_to_<last VIIRS date>/ and its zip (default DIR: the workspace's _exports, outside git). Licence holder names are not in any of these files.
"""
import argparse
import json
import os
from pathlib import Path

from repeat_prioritisation.national import fire_export as E

HUB = Path(os.environ.get("REPEAT_HUB", Path(__file__).resolve().parents[1]))
WORK = Path(os.environ.get("REPEAT_WORK", HUB / "reports"))
DATA = Path(os.environ.get("REPEAT_DATA", HUB.parent / "_data"))
EXTRA = {"ppeg_khg.csv": WORK / "national_profile/ppeg/ppeg_khg.csv", "ppeg_national.csv": WORK / "national_profile/ppeg/ppeg_national.csv",
         "roles_summary.md": WORK / "ppeg_roles/roles_summary.md", "roles_actor.csv": WORK / "ppeg_roles/roles_actor.csv",
         "roles_licence_type.csv": WORK / "ppeg_roles/roles_licence_type.csv", "roles_province.csv": WORK / "ppeg_roles/roles_province.csv"}

SOURCES = {
    "villages": "KLH, village boundaries 2023",
    "khg": "KHG boundaries, 865 KHG (layer dated 2017; agency inferred as KLHK); codes from SK.129/MENLHK/2017",
    "forest_area": "Forest area function 1:250,000, 2023 (received through the project team; agency inferred as KLHK)",
    "licences": "Business licences 2025: oil palm, mining, PBPH, PPHTR, PPHKM (received through the project team; issuing agency not stated in the file)",
    "dmpg": "KLH SiTMAT portal, DMPG village layer (sitmat.kemenlh.go.id), retrieved 2026-10-28",
    "burned": "KLHK burned area 2015-2026, one flag per burn year",
    "peat": "KLH integrated analysis for peat ecosystem restoration (PPEG), April 2026: peat land (LAHAN_GAMB = LAHAN GAMBUT) on the 30 m grid",
    "modis": "KLH MODIS hotspot record 2026, continued after its last date with NASA FIRMS MODIS near real time",
}
VIIRS = ["NASA FIRMS VIIRS S-NPP archive 2012-2025", "NASA FIRMS VIIRS S-NPP standard processing, 1 January to 31 July 2026",
         "NASA FIRMS VIIRS S-NPP near real time, 1 August to 31 October 2026"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=HUB.parent / "_exports")
    ap.add_argument("--no-rasters", action="store_true")
    ap.add_argument("--no-zip", action="store_true")
    a = ap.parse_args()
    src = WORK / "national_profile" / "fire_landstatus"
    meta = json.loads((src / "meta.json").read_text(encoding="utf-8"))
    clean = E.clean_meta(meta, DATA)
    src_of = {clean["inputs"][k]: v for k, v in SOURCES.items() if isinstance(clean["inputs"].get(k), str)}
    src_of.update(dict(zip(clean["inputs"]["viirs"], VIIRS)))
    dest = E.export(src, a.out / f"RE-PEAT_fire_land_status_data_to_{meta['viirs_last']}", rasters=not a.no_rasters,
                    extra={k: v for k, v in EXTRA.items() if v.exists()}, data_dir=DATA, sources=src_of)
    with open(dest / "README.md", "a", encoding="utf-8") as f:
        f.write("\n## extra/\n\nKLH's integrated analysis for peat restoration (PPEG, April 2026) summarised per KHG (`ppeg_khg.csv`, "
                "`ppeg_national.csv`) and by restoration actor, licence type and province (`roles_*.csv`, explained in `roles_summary.md`). "
                "Areas in hectares from the file's LUAS_HA.\n")
    print(dest)
    if not a.no_zip:
        z = E.zip_dir(dest)
        print(z, f"{z.stat().st_size / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
