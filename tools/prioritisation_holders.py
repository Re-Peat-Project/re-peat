"""Licence holders per KHG from KLH's PPEG analysis (attributes only): peat and SKEG-damaged peat of each holder.
Writes _exports/prioritisation_report/data/khg_holders.csv (outside git: it names licence holders)."""
import re
from pathlib import Path
import pandas as pd
import pyogrio

W = Path(__file__).resolve().parents[2]          # the workspace (re-peat/tools/ -> _repeat-project)
P = W / "_data/ALL_Analysis_Integrasi_Tematik__PPEG_Indonesia__April_2026.gpkg"
OUT = W / "_exports/prioritisation_report/data"
OUT.mkdir(parents=True, exist_ok=True)
norm = lambda s: re.sub(r"\s+", " ", str(s)).strip().casefold()
d = pyogrio.read_dataframe(P, columns=["NAMA_KHG", "PERUSAHAAN", "IZIN_USAHA", "LAHAN_GAMB", "CD_SKEG_24", "LUAS_HA"], read_geometry=False, use_arrow=True)
d = d[d.IZIN_USAHA.str.upper() != "NON KONSESI"]
d["peat"] = d.LAHAN_GAMB.str.upper() == "LAHAN GAMBUT"
d["dmg"] = d.peat & d.CD_SKEG_24.str.startswith("Rusak")
g = d.assign(peat_ha=d.LUAS_HA.where(d.peat, 0), damaged_ha=d.LUAS_HA.where(d.dmg, 0)).groupby(["NAMA_KHG", "PERUSAHAAN", "IZIN_USAHA"], as_index=False)[["LUAS_HA", "peat_ha", "damaged_ha"]].sum()
k = pd.read_csv(W / "re-peat/sites/khg_klh_priority.csv")[["khg_code", "khg_name"]]
m = dict(zip(k.khg_name.map(norm), k.khg_code))
g["khg_code"] = g.NAMA_KHG.map(norm).map(m)
print("unmatched KHG names:", g[g.khg_code.isna()].NAMA_KHG.unique()[:10])
g = g.rename(columns={"PERUSAHAAN": "holder", "IZIN_USAHA": "licence", "LUAS_HA": "area_ha"}).drop(columns="NAMA_KHG")
g = g[g.khg_code.notna()].round(1).sort_values(["khg_code", "damaged_ha", "peat_ha"], ascending=[True, False, False])
g.to_csv(OUT / "khg_holders.csv", index=False)
print(len(g), "rows,", g.khg_code.nunique(), "KHG,", g.holder.nunique(), "holders")
