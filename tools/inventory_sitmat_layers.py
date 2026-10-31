"""Inventory of the two map layers fetched from the SiTMAT portal (repeat_common.fetch_sitmat_layers).

    python tools/inventory_sitmat_layers.py [DATA_DIR]      # DATA_DIR defaults to $REPEAT_DATA, then ../_data

Writes reports/investigations/sitmat_layers.md: fields and values of each layer; peat area of the 2025 peat map by island
and province, and per selected KHG against the GFW peat extent of the national profile; DMPG villages by province,
programme and scheme, duplicates, villages per selected KHG, and the match with the 244 BRG atlas villages
(dpg/dpg_villages_boundaries.gpkg). Areas in an equal-area projection (EPSG:6933).
"""
import os
import re
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

HUB = Path(__file__).resolve().parents[1]
OUT = HUB / "reports" / "investigations" / "sitmat_layers.md"
EA = 6933


def key(s) -> str:
    s = re.sub(r"[^a-z0-9]", "", str(s).lower())
    return re.sub(r"^(kabupaten|kab|kota)", "", s)


def md(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    rows = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    rows += ["| " + " | ".join("" if pd.isna(v) else (f"{v:,.0f}" if isinstance(v, float) else str(v)) for v in r) + " |"
             for r in df.itertuples(index=False)]
    return "\n".join(rows)


def selected_khg(data: Path) -> gpd.GeoDataFrame:
    sel = pd.read_csv(HUB / "sites" / "selected_khg.csv")
    names = set(sel.khg_name_in_gpkg.dropna().map(lambda s: " ".join(s.split())))
    names.add("KHG Sungai Kampar - Sungai Gaung")                           # the earlier test site
    k = gpd.read_file(data / "batas_khg_indonesia.gpkg")
    k["name"] = k.NAMA_KHG.map(lambda s: " ".join(str(s).split()))
    k = k[k.name.isin(names)].dissolve("name").reset_index()
    reg = pd.read_csv(HUB / "sites" / "khg_registry.csv")
    reg["name"] = reg.name.map(lambda s: " ".join(str(s).split()))
    return k.merge(reg[["name", "khg_code"]], on="name", how="left")


def main():
    data = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("REPEAT_DATA", HUB.parent / "_data"))
    peat = gpd.read_file(data / "peat/lahan_gambut_indonesia_2025.gpkg", layer="lahan_gambut")
    dmpg = gpd.read_file(data / "dpg/dmpg_villages_sitmat.gpkg", layer="dmpg_villages")
    src = {n: gpd.read_file(data / f, layer="sitmat_source").iloc[0] for n, f in
           (("peat", "peat/lahan_gambut_indonesia_2025.gpkg"), ("dmpg", "dpg/dmpg_villages_sitmat.gpkg"))}
    khg = selected_khg(data)
    L = ["# SiTMAT map layers: inventory", "",
         f"`python tools/inventory_sitmat_layers.py` on the files written by `repeat_common.fetch_sitmat_layers`. Both layers are "
         "served by the SiTMAT portal of the Kementerian Lingkungan Hidup as one GeoJSON each, EPSG:4326. Areas are in EPSG:6933.", ""]

    # --- peat map 2025 -------------------------------------------------------------------------------------------------
    s = src["peat"]
    peat["ha"] = peat.to_crs(EA).area / 1e4
    is_peat = peat.LAHAN_GAMB == "LAHAN GAMBUT"
    L += ["## Lahan gambut Indonesia 2025", "",
          f"Endpoint `{s.endpoint}`, fetched {s.fetched} (ETag {s.etag}). File `peat/lahan_gambut_indonesia_2025.gpkg`, layer "
          f"`lahan_gambut`: {len(peat):,} polygons, {int(s.invalid_geometries)} of them invalid as delivered (kept, not repaired). "
          f"Fields: {', '.join(c for c in peat.columns if c not in ('geometry', 'ha'))}. `LAHAN_GAMB` is "
          f"{' or '.join(sorted(peat.LAHAN_GAMB.unique()))}; island and province names are the 2023 administrative names. "
          "No date, scale, method or licence is given in the response.", "",
          f"Peat: {peat.ha[is_peat].sum() / 1e6:,.2f} million ha in {int(is_peat.sum()):,} polygons; non-peat: "
          f"{peat.ha[~is_peat].sum() / 1e6:,.2f} million ha in {int((~is_peat).sum()):,} polygons.", ""]
    t = peat.groupby(["PULAU", "LAHAN_GAMB"]).ha.sum().unstack(fill_value=0) / 1e3
    t = t.rename(columns={"LAHAN GAMBUT": "peat (thousand ha)", "NON LAHAN GAMBUT": "non-peat (thousand ha)"}).reset_index()
    L += ["Table: by island.", "", md(t.rename(columns={"PULAU": "island"})), ""]
    t = (peat[is_peat].groupby(["PULAU", "PROV_2023"]).ha.sum() / 1e3).reset_index().sort_values("ha", ascending=False)
    L += ["Table: peat by province.", "", md(t.rename(columns={"PULAU": "island", "PROV_2023": "province", "ha": "peat (thousand ha)"})), ""]

    prof = pd.read_csv(HUB / "reports/national_profile/operational/profile.csv").set_index("khg_id")
    kp = gpd.overlay(khg[["name", "khg_code", "geometry"]], peat[is_peat][["geometry"]].assign(geometry=lambda d: d.geometry.make_valid()),
                     how="intersection", keep_geom_type=True)
    kp["ha"] = kp.to_crs(EA).area / 1e4
    khg["khg_ha"] = khg.to_crs(EA).area / 1e4
    rows = []
    for _, r in khg.sort_values("name").iterrows():
        klh = kp.loc[kp.name == r["name"], "ha"].sum()
        gfw = prof.loc[r.khg_code, "peat_km2"] * 100 if r.khg_code in prof.index else float("nan")
        rows.append({"KHG": r["name"].replace("KHG ", ""), "KHG area (ha)": r.khg_ha, "peat, SiTMAT 2025 (ha)": klh,
                     "share of KHG (%)": f"{100 * klh / r.khg_ha:.0f}", "peat, GFW extent (ha)": gfw,
                     "SiTMAT / GFW": f"{klh / gfw:.2f}" if gfw == gfw and gfw else ""})
    L += ["Table: peat in the selected KHG and the earlier test site, SiTMAT 2025 map against the GFW composite extent used by "
          "the national profile (peat_km2).", "", md(pd.DataFrame(rows)), ""]

    # --- DMPG villages ---------------------------------------------------------------------------------------------------
    s = src["dmpg"]
    dmpg["ha"] = dmpg.to_crs(EA).area / 1e4
    dup = dmpg.duplicated(["PROVINSI", "KABUPATEN", "KECAMATAN", "DESA"], keep=False)
    entries = dmpg.Skema_DPG.fillna("").str.split(r"\s*;\s*")             # support history: "2018 Kemitraan; 2022 APBN"
    first = entries.str[0]
    yr = first.str.extract(r"^(\d{4})")[0].fillna("no year")
    src_ = first.str.replace(r"^\d{4}\s*", "", regex=True).str.strip()
    up = src_.str.upper()
    src_ = pd.Series("other partner or programme", index=src_.index).mask(up.str.startswith("KEMITRAAN"), "Kemitraan (partnership)").mask(up.str.contains("APBN"), "APBN (state budget)")
    later = entries.str.len() - 1
    L += ["## Batas desa DMPG", "",
          f"Endpoint `{s.endpoint}`, fetched {s.fetched} (ETag {s.etag}). File `dpg/dmpg_villages_sitmat.gpkg`, layer "
          f"`dmpg_villages`: {len(dmpg):,} village polygons, "
          f"{int(s.invalid_geometries)} invalid. Fields: {', '.join(c for c in dmpg.columns if c not in ('geometry', 'ha'))}. "
          f"{dmpg.DESA.nunique():,} distinct village names; {int(dup.sum())} rows share province, district, sub-district and name "
          f"with another row. Total area {dmpg.ha.sum() / 1e6:,.2f} million ha (median village {dmpg.ha.median():,.0f} ha).", ""]
    L += ["Table: villages by province and programme.", "",
          md(pd.crosstab(dmpg.PROVINSI, dmpg.PROG_DMPG, margins=True, margins_name="total").reset_index().rename(columns={"PROVINSI": "province"})), ""]
    L += ["`Skema_DPG` lists each village's support as entries of year and source, separated by semicolons. The first entry gives "
          f"the year the village entered the programme; {int((later > 0).sum())} villages have one or more later entries "
          "(for example a 2022 or 2024 APBN round, KEDAIREKA, BNPB or a company programme).", "",
          "Table: villages by year and source of the first entry in `Skema_DPG`.", "",
          md(pd.crosstab(yr, src_, margins=True, margins_name="total").reset_index().rename(columns={"row_0": "first year", 0: "first year"})), ""]

    pts = dmpg.copy(); pts["geometry"] = dmpg.to_crs(EA).representative_point().to_crs(4326)
    j = gpd.sjoin(pts[["DESA", "geometry"]], khg[["name", "geometry"]], predicate="within")
    t = j.groupby("name").size().reindex(sorted(khg.name), fill_value=0).reset_index()
    t.columns = ["KHG", "DMPG villages (representative point inside)"]
    t["KHG"] = t.KHG.str.replace("KHG ", "")
    L += ["Table: DMPG villages in the selected KHG and the earlier test site.", "", md(t), ""]

    atlas = gpd.read_file(data / "dpg/dpg_villages_boundaries.gpkg")
    dmpg["k"] = dmpg.DESA.map(key) + "|" + dmpg.KABUPATEN.map(key)
    atlas["k"] = atlas.desa.map(key) + "|" + atlas.kabupaten.map(key)
    m = atlas.merge(dmpg[["k", "PROG_DMPG", "Skema_DPG", "geometry"]].rename(columns={"geometry": "g2"}), on="k", how="left")
    hit = m.g2.notna()
    a1 = gpd.GeoSeries(m.geometry[hit], crs=4326).to_crs(EA).make_valid()
    a2 = gpd.GeoSeries(m.g2[hit], crs=4326).to_crs(EA).make_valid()
    iou = (a1.intersection(a2, align=False).area / a1.union(a2, align=False).area)
    by_prov = atlas.assign(matched=atlas.k.isin(set(dmpg.k))).groupby("province").matched.agg(["size", "sum"]).reset_index()
    by_prov.columns = ["province", "atlas villages", "found in DMPG layer"]
    L += ["### Match with the BRG atlas villages", "",
          f"The 244 villages of the BRG atlas (2018-2019 mapping, boundaries from the KLH 2023 village boundaries) were matched to "
          f"the DMPG layer by village and district name, ignoring case, spaces and punctuation: {atlas.k.isin(set(dmpg.k)).sum()} "
          f"of {len(atlas)} found. For matched pairs the overlap of the two polygons (intersection over union) has median "
          f"{iou.median():.2f}; {int((iou >= 0.8).sum())} pairs reach 0.8 or more and {int((iou < 0.2).sum())} are below 0.2.", "",
          md(by_prov), ""]
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
