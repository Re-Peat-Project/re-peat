"""Roles of the ministries and other actors in the KLH priority area, with the area each one covers.

    python re-peat/tools/ppeg_roles.py

Roles as stated in the FGD terms of reference (KLH, B.70/E/PKL.4.5/10/2026, agenda item 9) and the FGD notes of 2 November
2026; areas from KLH's PPEG integrated analysis (April 2026), whose PROG_DMPG_2025 field assigns every polygon to an actor:
licence holders inside their licences, licence holders with communities in the 5 km buffer around them, the Ministry of
Forestry in the forest area outside them, KLH/BPLH in other land use (APL) outside them. Canal length per KHG from the
national profile (OSM-based canal layer). Priority KHG and area as in repeat-national-ppeg (AGENTS.md, decided 2026-11-13).
Writes re-peat/reports/ppeg_roles/roles_summary.md and roles_*.csv.
"""
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pyogrio

HUB = Path(__file__).resolve().parents[1]
WS = HUB.parent
DATA = Path(os.environ.get("REPEAT_DATA", WS / "_data"))
WORK = Path(os.environ.get("REPEAT_WORK", HUB / "reports"))
PPEG = DATA / "ALL_Analysis_Integrasi_Tematik__PPEG_Indonesia__April_2026.gpkg"
OUT = HUB / "reports" / "ppeg_roles"
COLS = ["NAMA_KHG", "PROV_2023", "PULAU", "LAHAN_GAMB", "CD_SKEG_24", "SKEG_2024", "PROG_DMPG_2025", "PROG_INTERVENSI", "KET_KANAL",
        "CD_KAWASAN", "CD_KONSESI", "IZIN_USAHA", "CD_BURN", "LUAS_HA"]
ACTOR = [("Intervensi Perusahaan", "Licence holders, inside their licences"),
         ("Kolaborasi Perusahaan (Area Buffer)", "Licence holders with communities, 5 km buffer around licences"),
         ("Intervensi Kementerian Kehutanan", "Ministry of Forestry, forest area outside licences"),
         ("Intervensi KLH/BPLH", "KLH/BPLH, other land use (APL) outside licences")]
SHORT = {"Intervensi Perusahaan": "Licence holders", "Kolaborasi Perusahaan (Area Buffer)": "Licence holders and communities (buffer)",
         "Intervensi Kementerian Kehutanan": "Ministry of Forestry", "Intervensi KLH/BPLH": "KLH/BPLH"}


def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def kha(v):
    return f"{v / 1e3:,.0f}"


def main():
    df = pyogrio.read_dataframe(PPEG, read_geometry=False, use_arrow=True, columns=COLS)
    khg = pd.read_csv(WORK / "national_profile" / "ppeg" / "ppeg_khg.csv")
    pri = set(khg.loc[khg["priority"], "khg_name"].map(norm))
    df["khg"] = df["NAMA_KHG"].map(norm)
    area = df[(df["LAHAN_GAMB"] == "LAHAN GAMBUT") & df["CD_SKEG_24"].str.startswith("Rusak")].copy()      # the priority area
    area["r1"] = area["PROG_INTERVENSI"].str.startswith(("01", "03"))           # canal-affected: rewetting (R1)
    area["r2"] = area["PROG_INTERVENSI"].str.startswith(("01", "02"))           # burned: revegetation (R2)
    area["ps"] = area["KET_KANAL"].isin(["Kanal Primer", "Kanal Sekunder"])
    area["kaw"] = area["CD_KAWASAN"] == "Kawasan Hutan"
    tot = area["LUAS_HA"].sum()

    rows = []
    for code, lab in ACTOR:
        a = area[area["PROG_DMPG_2025"] == code]
        ha = a["LUAS_HA"]
        rows.append({"actor": lab, "ha": ha.sum(), "share": ha.sum() / tot, "khg": a.loc[a["khg"] != "non khg", "khg"].nunique(),
                     "r1_ha": ha[a["r1"]].sum(), "r2_ha": ha[a["r2"]].sum(), "ps_ha": ha[a["ps"]].sum(), "forest_ha": ha[a["kaw"]].sum(),
                     "apl_ha": ha[~a["kaw"]].sum()})
    A = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    A.to_csv(OUT / "roles_actor.csv", index=False, float_format="%.1f")

    # licences inside the forest area (the Ministry of Forestry's role covers forest area with and without licences)
    lic = area[(area["PROG_DMPG_2025"] == "Intervensi Perusahaan")]
    lic_k = lic.groupby(["IZIN_USAHA", "CD_KAWASAN"])["LUAS_HA"].sum().unstack(fill_value=0)
    lic_k.to_csv(OUT / "roles_licence_type.csv", float_format="%.1f")
    forest_all = area.loc[area["kaw"], "LUAS_HA"].sum()
    forest_lic = area.loc[area["kaw"] & (area["PROG_DMPG_2025"] == "Intervensi Perusahaan"), "LUAS_HA"].sum()

    # canals in the priority KHG (PU: blocks on primary and secondary canals)
    prof = pd.read_csv(WORK / "national_profile" / "operational" / "profile.csv")
    reg = pd.read_csv(HUB / "sites" / "khg_registry.csv")
    code2name = dict(zip(reg["khg_code"], reg["name"].map(norm)))
    prof["k"] = prof["khg_id"].map(code2name)
    pk = prof[prof["k"].isin(pri)]
    canal = {c: pk[f"canal_km_{c}"].sum() for c in ("primary", "secondary", "tertiary")}
    canal_blank = int((pk["canal_segments"].fillna(0) == 0).sum())

    # by province
    P = area.pivot_table(index="PROV_2023", columns="PROG_DMPG_2025", values="LUAS_HA", aggfunc="sum", fill_value=0)
    P = P.reindex(columns=[c for c, _ in ACTOR], fill_value=0)
    P["total"] = P.sum(axis=1)
    P = P.sort_values("total", ascending=False)
    P.to_csv(OUT / "roles_province.csv", float_format="%.1f")

    n_pri = int(khg["priority"].sum())
    md = ["# Roles in the KLH priority area", "",
          f"KLH's priority area is the peat with damaged ecosystem status (SKEG 2024), {tot / 1e6:.2f} million ha in {n_pri} priority KHG. "
          "KLH's integrated thematic analysis for peat ecosystem restoration (PPEG, April 2026) assigns every part of it to one actor. "
          "The roles below are those stated for the FGD of 2 November 2026; the areas are what each actor would cover.", "",
          "## Roles as stated", "",
          "| Institution | Role | Source |", "|---|---|---|",
          "| Ministry of Public Works (PU) | Technical support, field implementation and coordination of canal blocks on primary and secondary canals | FGD terms of reference, agenda item 9 |",
          "| Ministry of Forestry | Technical support, water management and rewetting infrastructure in the forest area, with and without licences | FGD terms of reference, agenda item 9 |",
          "| BPGM (national peat and mangrove agency) | Aligning peat targets and priorities; coordination and synergy. Coordinates the ministries and does not replace them | FGD terms of reference, agenda item 9; FGD notes (Head of BPGMN) |",
          "| Bappenas | Direction of support and budget for peat restoration; financing and planning | FGD terms of reference, agenda item 9; FGD notes (Head of BPGMN) |",
          "| KLH/BPLH | Sets the priority area (SKEG) and the PPEG analysis; assigned rewetting in APL outside licences | PPEG analysis; FGD terms of reference |",
          "| Licence holders | Water management and rewetting inside their licences; water sharing with communities around them | PPEG analysis; FGD notes (KLH Deputy, UNRI) |",
          "| Ministry of Finance | No role stated in the FGD documents | - |", "",
          "## Who covers which part of the priority area", "",
          "Areas in thousand ha of SKEG-damaged peat; KHG = priority KHG holding that actor's part (328 hold damaged peat; the other 34 priority KHG are listed through the target villages). Canal-affected land calls for rewetting (R1), burned land for revegetation (R2); all of it for livelihood revitalisation (R3), as coded by KLH. Some land is both.", "",
          "| Actor | Area | Share | KHG | Canal-affected (R1) | Burned (R2) | Near primary or secondary canals | In forest area | In APL |", "|---|---|---|---|---|---|---|---|---|"]
    for r in A.itertuples():
        md.append(f"| {r.actor} | {kha(r.ha)} | {100 * r.share:.0f}% | {r.khg} | {kha(r.r1_ha)} | {kha(r.r2_ha)} | {kha(r.ps_ha)} | {kha(r.forest_ha)} | {kha(r.apl_ha)} |")
    md.append(f"| **Total** | **{kha(tot)}** | 100% | {area.loc[area['khg'] != 'non khg', 'khg'].nunique()} | {kha(area.loc[area['r1'], 'LUAS_HA'].sum())} | {kha(area.loc[area['r2'], 'LUAS_HA'].sum())} | {kha(area.loc[area['ps'], 'LUAS_HA'].sum())} | {kha(forest_all)} | {kha(tot - forest_all)} |")
    co = A.set_index("actor")
    md += ["", "## By institution", "",
           f"- **Ministry of Public Works.** {kha(area.loc[area['ps'], 'LUAS_HA'].sum())} thousand ha of the priority area lies in the zone affected by primary or secondary canals, the canals the terms of reference assign to PU. "
           f"The priority KHG hold {canal['primary']:,.0f} km of primary and {canal['secondary']:,.0f} km of secondary canals in the national canal layer ({canal['tertiary']:,.0f} km tertiary)" +
           (f"; {canal_blank} of them have no canal in that layer, where canals may exist unmapped, so these are lower bounds." if canal_blank else "."),
           f"- **Ministry of Forestry.** {kha(co.loc[ACTOR[2][1], 'ha'])} thousand ha outside licences in the forest area ({100 * co.loc[ACTOR[2][1], 'share']:.0f}% of the priority area). "
           f"With the licensed forest area its stated role covers, {kha(forest_all)} thousand ha ({100 * forest_all / tot:.0f}%) lies in the forest area, {kha(forest_lic)} thousand ha of it inside licences.",
           f"- **KLH/BPLH.** {kha(co.loc[ACTOR[3][1], 'ha'])} thousand ha in APL outside licences ({100 * co.loc[ACTOR[3][1], 'share']:.0f}%).",
           f"- **Licence holders.** {kha(co.loc[ACTOR[0][1], 'ha'])} thousand ha inside licences ({100 * co.loc[ACTOR[0][1], 'share']:.0f}%) and {kha(co.loc[ACTOR[1][1], 'ha'])} thousand ha in the 5 km buffer ({100 * co.loc[ACTOR[1][1], 'share']:.0f}%), where KLH foresees collaboration with communities.",
           f"- **BPGM and Bappenas.** Plan and fund the whole: {kha(area.loc[area['r1'], 'LUAS_HA'].sum())} thousand ha to rewet and {kha(area.loc[area['r2'], 'LUAS_HA'].sum())} thousand ha to revegetate across {n_pri} KHG. An indicative investment envelope needs the block and well quantities per KHG; it is the next step of the prioritisation.",
           "", "## By province", "", "Thousand ha of SKEG-damaged peat; provinces with at least 1,000 ha.", "",
           "| Province | " + " | ".join(SHORT[c] for c, _ in ACTOR) + " | Total |", "|---" * (len(ACTOR) + 2) + "|"]
    for p, r in P.iterrows():
        if r["total"] >= 1000:
            md.append(f"| {p} | " + " | ".join(kha(r[c]) for c, _ in ACTOR) + f" | {kha(r['total'])} |")
    md += ["", "Sources: KLH, PPEG integrated thematic analysis, April 2026 (fields SKEG_2024, LAHAN_GAMB, PROG_DMPG_2025, PROG_INTERVENSI, KET_KANAL, CD_KAWASAN); "
           "KLH/BPLH, terms of reference of the FGD of 2 November 2026 (letter B.70/E/PKL.4.5/10/2026); notes of the FGD of 2 November 2026; "
           "canal lengths from the national KHG profile (OSM-based canal layer). The actor of each area is KLH's assignment; it does not say who caused the damage."]
    (OUT / "roles_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(OUT / "roles_summary.md")
    # the same numbers for the slides (_slides/build_fire.js)
    import json
    top = khg[khg["has_skeg_damage"]].nlargest(15, "priority_ha")
    nat = pd.read_csv(WORK / "national_profile" / "ppeg" / "ppeg_national.csv", index_col=0)["value"]
    facts = {"total_ha": float(tot), "khg_priority": n_pri, "khg_skeg": int(khg["has_skeg_damage"].sum()), "khg_villages": int(khg["in_target_villages"].sum()),
             "khg_villages_only": int((khg["in_target_villages"] & ~khg["has_skeg_damage"]).sum()),
             "khg_skeg_only": int((khg["has_skeg_damage"] & ~khg["in_target_villages"]).sum()),
             "in_villages_ha": float(nat["priority_in_target_villages_ha"]), "dome_ha": float(nat["priority_dome_ha"]), "thick3m_ha": float(nat["priority_thick3m_ha"]),
             "damage_ha": {k: float(nat[f"priority_{k}_ha"]) for k in ("ringan", "sedang", "berat", "sangat_berat")},
             "r1_ha": float(area.loc[area["r1"], "LUAS_HA"].sum()), "r2_ha": float(area.loc[area["r2"], "LUAS_HA"].sum()),
             "ps_ha": float(area.loc[area["ps"], "LUAS_HA"].sum()), "forest_ha": float(forest_all), "forest_lic_ha": float(forest_lic),
             "canal_km": {k: float(v) for k, v in canal.items()}, "canal_blank": canal_blank,
             "actors": [{"key": c, "label": lab, "short": SHORT[c], **{k: float(v) for k, v in r._asdict().items() if k not in ("Index", "actor")}}
                        for (c, lab), r in zip(ACTOR, A.itertuples())],
             "provinces": [{"province": p, **{SHORT[c]: float(r[c]) for c, _ in ACTOR}, "total": float(r["total"])} for p, r in P.head(10).iterrows()],
             "top_khg": [{"name": n.removeprefix("KHG ").replace("Sungai ", ""), "ha": float(h), "dome_ha": float(dm), "villages": bool(v)}
                         for n, h, dm, v in zip(top["khg_name"], top["priority_ha"], top["priority_dome_ha"], top["in_target_villages"])]}
    sb = WS / "_slides" / "build"
    sb.mkdir(exist_ok=True)
    (sb / "roles_facts.json").write_text(json.dumps(facts, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
