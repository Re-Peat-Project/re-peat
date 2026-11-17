"""Profile of the 2,004 Bluebook target villages: land status, damage, fire and the actors present in each village.

    python re-peat/tools/village_actors.py [--out DIR]

One row per target village (desa_target_pemulihan_ekosistem_gambut.gpkg), joined on province, district, subdistrict and village
name to KLH's PPEG integrated analysis (April 2026), plus three spatial joins:
  PPEG       area (LUAS_HA) of the village: all land, KLH peat, SKEG 2024 damaged peat, burned (CD_BURN), burned two or more
             times (BURN_PERIOD), canal-affected (CD_ATK), forest area (CD_KAWASAN), and the four intervention classes
             (PROG_INTERVENSI); the damaged peat by the actor KLH assigns (PROG_DMPG_2025: licence holder, licence holder with
             communities in the 5 km buffer, Ministry of Forestry, KLH/BPLH); the KHG of the village and whether the KHG is in
             the team's 337-KHG work list
  licences   business licences 2025 overlapping the village (oil palm, mining, PBPH, PPHTR, and community forest permits PPHKM),
             holder and area inside the village (EPSG:6933, equal area)
  DMPG       whether the village is a Desa Mandiri Peduli Gambut village (SiTMAT layer; at least half the target village inside a
             DMPG polygon), its programme, and the partners and years of its scheme (Skema_DPG)
  hotspots   VIIRS and MODIS hotspots of 2026 inside the village (medium and high confidence, likely static sources left out;
             fire_landstatus/layers/hotspots_2026.gpkg)
Writes, in DIR (default: the workspace's _exports/target_villages, outside git, because it names licence holders):
  target_villages.csv / .gpkg   one row per village
  village_licences.csv          one row per village and licence holder
  village_partners.csv          one row per village and DMPG partner
  summary.md                    counts by province, actor and partner
A licence overlapping a village is a spatial overlap, not a statement about responsibility for a fire.
"""
import argparse
import os
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio

WS = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("REPEAT_DATA", WS / "_data"))
WORK = Path(os.environ.get("REPEAT_WORK", WS / "re-peat" / "reports"))
TV = DATA / "desa_target_pemulihan_ekosistem_gambut.gpkg"
PPEG = DATA / "ALL_Analysis_Integrasi_Tematik__PPEG_Indonesia__April_2026.gpkg"
LIC = DATA / "landstatus" / "ALL_Updade__IZIN_USAHA__PBPH_Perkebunan_HTRKM_Tambang__2025.gpkg"
DMPG = DATA / "dpg" / "dmpg_villages_sitmat.gpkg"
HOT = WORK / "national_profile" / "fire_landstatus" / "layers" / "hotspots_2026.gpkg"
K337 = WS / "re-peat" / "reports" / "investigations" / "khg337_tim_gis.csv"
VKEY = ["PROV_2023", "KABKO_2023", "KEC_2023", "DESA_2023"]
EA = "EPSG:6933"
ACTOR = {"Intervensi Perusahaan": "licence_holder", "Kolaborasi Perusahaan (Area Buffer)": "licence_holder_buffer",
         "Intervensi Kementerian Kehutanan": "mofor", "Intervensi KLH/BPLH": "klh"}
ACTOR_LABEL = {"licence_holder": "Licence holder", "licence_holder_buffer": "Licence holder with communities (5 km buffer)",
               "mofor": "Ministry of Forestry", "klh": "KLH/BPLH"}
LIC_TYPE = {"Perkebunan Kelapa Sawit": "oil palm", "Pertambangan": "mining", "PBPH": "forest concession (PBPH)",
            "PPHTR": "plantation forest (PPHTR)", "PPHKM": "community forest permit (PPHKM)"}


def key(d):
    return d[VKEY].astype(str).apply(lambda c: c.str.strip()).agg("|".join, axis=1)


def ppeg(villages):
    cols = ["NAMA_KHG", "LAHAN_GAMB", "CD_SKEG_24", "CD_BURN", "BURN_PERIOD", "CD_ATK", "CD_KAWASAN", "PROG_INTERVENSI",
            "PROG_DMPG_2025", "LUAS_HA"] + VKEY
    df = pyogrio.read_dataframe(PPEG, read_geometry=False, use_arrow=True, columns=cols)
    df["vk"] = key(df)
    df = df[df["vk"].isin(set(villages["vk"]))]
    ha, peat = df["LUAS_HA"], df["LAHAN_GAMB"] == "LAHAN GAMBUT"
    dmg = peat & df["CD_SKEG_24"].astype(str).str.startswith("Rusak")
    f = pd.DataFrame({"vk": df["vk"], "area_ha": ha, "peat_ha": ha * peat, "damaged_peat_ha": ha * dmg,
                      "burned_ha": ha * (df["CD_BURN"] == "Areal Terbakar"),
                      "burned_2plus_ha": ha * df["BURN_PERIOD"].isin(["Terbakar 2x", "Terbakar 3x", "Terbakar >3x"]),
                      "canal_affected_ha": ha * (df["CD_ATK"] == "Area Terdampak Kanal"),
                      "forest_area_ha": ha * (df["CD_KAWASAN"] == "Kawasan Hutan")})
    for k in ["01", "02", "03", "04"]:
        f[f"intervention_{k}_ha"] = ha * df["PROG_INTERVENSI"].astype(str).str.startswith(k)
    for v in ACTOR.values():
        f[f"damaged_{v}_ha"] = ha * (dmg & (df["PROG_DMPG_2025"].map(ACTOR) == v))
    out = f.groupby("vk").sum()
    khg = df[df["NAMA_KHG"].astype(str).str.strip().ne("NON KHG")].groupby(["vk", "NAMA_KHG"])["LUAS_HA"].sum().reset_index()
    khg["NAMA_KHG"] = khg["NAMA_KHG"].map(lambda s: re.sub(r"\s+", " ", str(s)).strip())
    out["khg"] = khg.sort_values("LUAS_HA", ascending=False).groupby("vk")["NAMA_KHG"].agg("; ".join)
    return out


def licences(v):
    lic = gpd.read_file(LIC, columns=["PERUSAHAAN", "IZIN_USAHA", "KEG_USAHA"], bbox=tuple(v.to_crs(4326).total_bounds)).to_crs(EA)
    lic["geometry"] = lic.geometry.make_valid()
    x = gpd.overlay(v[["vk", "geometry"]], lic, how="intersection", keep_geom_type=True)
    x["area_ha"] = x.geometry.area / 1e4
    x = x[x["area_ha"] >= 1]
    x["type"] = x["IZIN_USAHA"].map(LIC_TYPE).fillna(x["IZIN_USAHA"])
    return x.groupby(["vk", "PERUSAHAAN", "type"], as_index=False)["area_ha"].sum().rename(columns={"PERUSAHAAN": "holder"})


def dmpg(v):
    d = gpd.read_file(DMPG, layer="dmpg_villages", columns=["DESA", "PROG_DMPG", "Skema_DPG"]).to_crs(EA)
    d["geometry"] = d.geometry.make_valid()
    x = gpd.overlay(v[["vk", "area_m2", "geometry"]], d, how="intersection", keep_geom_type=True)
    x["share"] = x.geometry.area / x["area_m2"]
    x = x.sort_values("share", ascending=False).drop_duplicates("vk")
    x = x[x["share"] >= 0.5]
    return x.set_index("vk")[["DESA", "PROG_DMPG", "Skema_DPG", "share"]]


def partners(scheme):
    """'APBN; 2022 KEDAIREKA; 2023 APBN' -> [('', 'APBN'), ('2022', 'KEDAIREKA'), ('2023', 'APBN')]."""
    out = []
    for part in re.split(r"[;,]", str(scheme)):
        part = part.strip()
        if not part or part == "nan":
            continue
        m = re.match(r"((?:19|20)\d{2})\s+(.*)", part)
        year, name = (m.group(1), m.group(2)) if m else ("", part)
        name = re.sub(r"\s+", " ", name).strip()
        name = {"KEMITRAAN": "Kemitraan", "PROFOREST": "Proforest", "CPI OPS": "PT CPI", "DMPG APBN": "APBN", "APBN-2": "APBN"}.get(name.upper(), name)
        if name and name.upper() not in ("DMPG", "SKEMA DMPG"):
            out.append((year, name))
    return out


def hotspots(v):
    out = {}
    for src in ("viirs", "modis"):
        h = gpd.read_file(HOT, layer=f"{src}_2026", columns=["static", "on_land"])
        h = h[h["static"].astype(str).str.lower().isin(["false", "0"])].to_crs(EA)
        j = gpd.sjoin(h[["geometry"]], v[["vk", "geometry"]], predicate="within")
        out[f"{src}_2026_n"] = j.groupby("vk").size()
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=WS / "_exports" / "target_villages")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    v = gpd.read_file(TV, columns=["PULAU"] + VKEY)
    v["vk"] = key(v)
    v["geometry"] = v.geometry.make_valid()
    v = v.to_crs(EA)
    v["area_m2"] = v.geometry.area

    P = ppeg(v)
    L = licences(v)
    D = dmpg(v)
    H = hotspots(v)
    k337 = set(pd.read_csv(K337)["khg_name_xlsx"].map(lambda s: re.sub(r"\s+", " ", str(s)).strip())) if K337.exists() else set()

    t = v.drop(columns="geometry").set_index("vk").join(P).join(H)
    t[["viirs_2026_n", "modis_2026_n"]] = t[["viirs_2026_n", "modis_2026_n"]].fillna(0).astype(int)
    t["in_ppeg"] = t["area_ha"].notna()
    t["khg_in_337"] = t["khg"].fillna("").map(lambda s: any(k in k337 for k in s.split("; ") if k))
    dm = [c for c in t.columns if c.startswith("damaged_") and c != "damaged_peat_ha"]
    t["main_actor"] = t[dm].idxmax(axis=1).str.replace("damaged_", "").str.replace("_ha", "").map(ACTOR_LABEL).where(t[dm].sum(axis=1) > 0, "")
    lt = L.groupby("vk").agg(n_licence_holders=("holder", lambda s: s[L.loc[s.index, "type"] != LIC_TYPE["PPHKM"]].nunique()),
                             n_pphkm_permits=("holder", lambda s: s[L.loc[s.index, "type"] == LIC_TYPE["PPHKM"]].nunique()))
    top = pd.Series({vk: "; ".join(f"{h} ({ty}, {ar:,.0f} ha)" for h, ty, ar in g[["holder", "type", "area_ha"]].head(5).itertuples(index=False))
                     for vk, g in L[L["type"] != LIC_TYPE["PPHKM"]].sort_values("area_ha", ascending=False).groupby("vk")}, dtype=object)
    t = t.join(lt).join(top.rename("licence_holders_top5"))
    t[["n_licence_holders", "n_pphkm_permits"]] = t[["n_licence_holders", "n_pphkm_permits"]].fillna(0).astype(int)
    t = t.join(D.rename(columns={"DESA": "dmpg_village_name", "PROG_DMPG": "dmpg_programme", "Skema_DPG": "dmpg_scheme", "share": "dmpg_overlap"}))
    t["dmpg_supported"] = t["dmpg_programme"].notna()            # in SiTMAT's DMPG layer: the village has had DMPG support
    pr = [(vk, y, n) for vk, s in t["dmpg_scheme"].dropna().items() for y, n in partners(s)]
    PR = pd.DataFrame(pr, columns=["vk", "year", "partner"])
    t["dmpg_partners"] = PR.groupby("vk")["partner"].agg(lambda s: "; ".join(dict.fromkeys(s)))
    t = t.reset_index().rename(columns={"PULAU": "island", "PROV_2023": "province", "KABKO_2023": "district", "KEC_2023": "subdistrict", "DESA_2023": "village"})
    num = [c for c in t.columns if c.endswith("_ha")]
    t[num] = t[num].round(1)
    t = t.drop(columns=["area_m2"])
    t.drop(columns="vk").to_csv(a.out / "target_villages.csv", index=False)
    g = v[["vk", "geometry"]].merge(t, on="vk").drop(columns="vk").to_crs(4326)
    (a.out / "target_villages.gpkg").unlink(missing_ok=True)
    g.to_file(a.out / "target_villages.gpkg", layer="target_villages", driver="GPKG")
    vmeta = t.set_index("vk")[["province", "district", "subdistrict", "village"]]
    L.join(vmeta, on="vk").drop(columns="vk").round(1).to_csv(a.out / "village_licences.csv", index=False)
    PR.join(vmeta, on="vk").drop(columns="vk").to_csv(a.out / "village_partners.csv", index=False)

    # summary
    n = len(t)
    act = t[[c for c in t.columns if c.startswith("damaged_") and c != "damaged_peat_ha"]].sum()
    hold = L[L["type"] != LIC_TYPE["PPHKM"]].groupby("holder")["vk"].nunique().sort_values(ascending=False)
    prt = PR.groupby("partner")["vk"].nunique().sort_values(ascending=False)
    lines = ["# The 2,004 target villages: land, damage, fire and actors", "",
             f"{n} villages; {int(t['in_ppeg'].sum())} matched to KLH's PPEG analysis by name; {int(t['khg_in_337'].sum())} in a KHG of the 337-KHG work list.",
             f"Land {t['area_ha'].sum() / 1e6:.2f} million ha, of it peat {t['peat_ha'].sum() / 1e6:.2f}, SKEG-damaged peat {t['damaged_peat_ha'].sum() / 1e6:.2f}, "
             f"canal-affected {t['canal_affected_ha'].sum() / 1e6:.2f}, burned {t['burned_ha'].sum() / 1e6:.2f} (PPEG).",
             f"VIIRS hotspots 2026 in the villages: {t['viirs_2026_n'].sum():,}; MODIS: {t['modis_2026_n'].sum():,}.", "",
             "## Who KLH assigns the damaged peat to", "", "| Actor | Damaged peat (ha) | Villages where it is the main actor |", "|---|---|---|"]
    for c, val in act.items():
        lab = ACTOR_LABEL[c.replace("damaged_", "").replace("_ha", "")]
        lines.append(f"| {lab} | {val:,.0f} | {int((t['main_actor'] == lab).sum())} |")
    lines += ["", f"Villages with at least one business licence: {int((t['n_licence_holders'] > 0).sum())}; with a community forest permit (PPHKM): "
              f"{int((t['n_pphkm_permits'] > 0).sum())}; villages already in SiTMAT's DMPG layer (DMPG support so far): {int(t['dmpg_supported'].sum())}.", "",
              "## Licence holders present in the most target villages", "", "| Holder | Villages |", "|---|---|"]
    lines += [f"| {h} | {k} |" for h, k in hold.head(25).items()]
    lines += ["", "## Partners and funders of DMPG support so far (Skema_DPG; APBN = state budget, Kemitraan = partnership)", "", "| Partner | Villages |", "|---|---|"]
    lines += [f"| {p} | {k} |" for p, k in prt.head(25).items()]
    lines += ["", "## By province", "", "| Province | Villages | DMPG support so far | With licences | Damaged peat (ha) | VIIRS 2026 |", "|---|---|---|---|---|---|"]
    for p, g_ in t.groupby("province"):
        lines.append(f"| {p} | {len(g_)} | {int(g_['dmpg_supported'].sum())} | {int((g_['n_licence_holders'] > 0).sum())} | {g_['damaged_peat_ha'].sum():,.0f} | {g_['viirs_2026_n'].sum():,} |")
    lines += ["", "A licence overlapping a village is a spatial overlap, not a statement about responsibility for a fire. "
              "Licence layer 2025: received through the project team; issuing agency not stated in the file."]
    (a.out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:30]))


if __name__ == "__main__":
    main()
