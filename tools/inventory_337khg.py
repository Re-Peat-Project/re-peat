"""Inventory of the team's 337-KHG work list: 'Tim GIS - Intervensi Pembasahan Karhutla pada 337 KHG (2004 Desa DMPG), Sept 2026.xlsx'.

    python re-peat/tools/inventory_337khg.py

The workbook (one sheet) lists the 337 KHG of the rewetting design work ("2004 desa prioritas program DMPG"), with the area of
each KHG in the four intervention classes of KLH's PPEG analysis (01 burned and canal-affected ... 04 not burned, no canal), the
GIS team assigned and five work-stage flags. Numbers of 1,000 or more were typed with dots as thousands separators, so the
workbook stores 1,105 as 1.105 and the totals row as text ('5.740.282'): a number with a fractional part is read as thousands
(x 1000) and the row sums are checked. Then:
  - the KHG names are matched to the registry (SK.129/2017 codes) and to the project's priority KHG (ppeg_khg.csv);
  - the areas are recomputed from the PPEG file (PROG_INTERVENSI x LUAS_HA) inside the 2,004 Bluebook target villages, on all
    land and on peat only, and compared per KHG.
Writes re-peat/reports/investigations/khg337_tim_gis.csv (one row per KHG) and khg337_tim_gis.md.
"""
import os
import re
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import pyogrio

WS = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("REPEAT_DATA", WS / "_data"))
HUB = WS / "re-peat"
XLSX = DATA / "Tim GIS - Intervensi Pembasahan Karhutla pada 337 KHG (2004 Desa DMPG), Sept 2026.xlsx"
PPEG = DATA / "ALL_Analysis_Integrasi_Tematik__PPEG_Indonesia__April_2026.gpkg"
VILLAGES = DATA / "desa_target_pemulihan_ekosistem_gambut.gpkg"
OUT = HUB / "reports" / "investigations"
CLS = ["c01", "c02", "c03", "c04"]
CLS_LABEL = {"c01": "01. Terbakar, Berkanal (R1, R2, R3)", "c02": "02. Terbakar, Non Kanal (R2, R3)",
             "c03": "03. Non Terbakar, Berkanal (R1, R3)", "c04": "04. Non Terbakar, Non Kanal (R3)"}
STAGES = ["Jalur Pembasahan", "Sekat Kanal", "Pompa Air", "Pintu Air", "Layout Peta"]
VKEY = ["PROV_2023", "KABKO_2023", "KEC_2023", "DESA_2023"]


def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def num(v):
    """Area in ha from a cell typed with dots as thousands separators."""
    if v is None or v == "":
        return np.nan
    if isinstance(v, str):
        return float(v.replace(".", "").replace(",", "."))
    v = float(v)
    return round(v * 1000) if v != int(v) else v


def read_xlsx():
    ws = openpyxl.load_workbook(XLSX, data_only=True).worksheets[0]
    merged = {}                                    # island and team cells are merged over blocks of rows
    for rng in ws.merged_cells.ranges:
        v = ws.cell(rng.min_row, rng.min_col).value
        for r in range(rng.min_row, rng.max_row + 1):
            merged[(r, rng.min_col)] = v
    rows, totals = [], []
    for r in range(6, ws.max_row + 1):
        name = ws.cell(r, 4).value
        vals = [num(ws.cell(r, c).value) for c in range(6, 11)]
        if name:
            rows.append({"no": int(ws.cell(r, 3).value), "khg_name_xlsx": str(name).strip(),
                         "island": merged.get((r, 2), ws.cell(r, 2).value), "province": ws.cell(r, 5).value,
                         **dict(zip(CLS + ["total"], vals)),
                         "team": str(merged.get((r, 11), ws.cell(r, 11).value) or "").split("\n")[0],
                         **{s: bool(ws.cell(r, 12 + i).value) for i, s in enumerate(STAGES)}})
        elif ws.cell(r, 2).value:
            totals.append({"label": str(ws.cell(r, 2).value).strip(), **dict(zip(CLS + ["total"], vals))})
    t = pd.DataFrame(rows)
    t["island"] = t["island"].ffill()
    t["team"] = t["team"].replace("", np.nan).ffill()
    t["row_sum_ok"] = (t[CLS].sum(axis=1) - t["total"]).abs() <= 1
    return t, pd.DataFrame(totals)


def ppeg_by_khg():
    tv = pyogrio.read_dataframe(VILLAGES, read_geometry=False, columns=VKEY)
    key = lambda d: d[VKEY].astype(str).apply(lambda c: c.str.strip()).agg("|".join, axis=1)   # noqa: E731
    targets = set(key(tv))
    df = pyogrio.read_dataframe(PPEG, read_geometry=False, use_arrow=True,
                                columns=["NAMA_KHG", "PROG_INTERVENSI", "LAHAN_GAMB", "LUAS_HA"] + VKEY)
    df["in_tv"] = key(df).isin(targets)
    df["cls"] = "c" + df["PROG_INTERVENSI"].astype(str).str[:2]
    df["k"] = df["NAMA_KHG"].map(norm)
    out = {}
    for name, sel in (("tv_all", df["in_tv"]), ("tv_peat", df["in_tv"] & (df["LAHAN_GAMB"] == "LAHAN GAMBUT"))):
        g = df[sel].groupby(["k", "cls"])["LUAS_HA"].sum().unstack(fill_value=0.0).reindex(columns=CLS, fill_value=0.0)
        out[name] = g.assign(total=g.sum(axis=1))
    return out


def main():
    t, tot = read_xlsx()
    t["k"] = t["khg_name_xlsx"].map(norm)
    reg = pd.read_csv(HUB / "sites" / "khg_registry.csv")
    t["khg_code"] = t["k"].map(dict(zip(reg["name"].map(norm), reg["khg_code"])))
    pk = pd.read_csv(HUB / "reports" / "national_profile" / "ppeg" / "ppeg_khg.csv")
    pk["k"] = pk["khg_name"].map(norm)
    t = t.merge(pk[["k", "priority", "in_target_villages", "has_skeg_damage"]], on="k", how="left")
    P = ppeg_by_khg()
    for name, g in P.items():
        m = g.reindex(t["k"])
        t[f"{name}_total"] = m["total"].to_numpy().round(0)
        t[f"{name}_diff"] = (t["total"] - t[f"{name}_total"]).round(0)
    t.drop(columns="k").to_csv(OUT / "khg337_tim_gis.csv", index=False)

    n = len(t)
    in_ours = t["priority"].fillna(False).astype(bool)
    ours = pk[pk["priority"] & (pk["khg_name"] != "NON KHG")]
    not_in_xlsx = ours[~ours["k"].isin(t["k"])]
    gtot = tot.set_index("label")
    grand = gtot.iloc[-1]
    match = {name: int((t[f"{name}_diff"].abs() <= 1).sum()) for name in P}
    best = max(match, key=match.get)
    lines = [
        "# Team 337-KHG work list (Sept 2026)", "",
        f"Source: `_data/{XLSX.name}` (one sheet, received 2026-11-13). Inventory script: `re-peat/tools/inventory_337khg.py`; "
        "per-KHG table: `khg337_tim_gis.csv`.", "",
        "## Content", "",
        "- Title: \"Pekerjaan pembuatan desain intervensi pembasahan dalam rangka pengendalian kebakaran hutan dan lahan pada 337 "
        "Kesatuan Hidrologis Gambut (2004 desa prioritas program DMPG)\".",
        f"- {n} KHG rows ({', '.join(f'{k} {v}' for k, v in t['island'].value_counts().items())}), each with province, the area in "
        "the four PPEG intervention classes, total area, the GIS team and five work-stage flags "
        f"({', '.join(STAGES)}).",
        f"- Totals row \"{grand.name}\": " + ", ".join(f"{CLS_LABEL[c]} {grand[c]:,.0f} ha" for c in CLS) + f"; total {grand['total']:,.0f} ha.",
        f"- Teams: {', '.join(f'{k} ({v} KHG)' for k, v in t['team'].value_counts().sort_index().items())}.",
        "- Work stages marked done: " + ", ".join(f"{s} {int(t[s].sum())}" for s in STAGES) + ".", "",
        "## Reading the numbers", "",
        "Areas of 1,000 ha or more were typed with dots as thousands separators, so the workbook stores them as decimals (1,105 ha "
        "as 1.105) and the totals rows as text. Read as thousands, "
        f"{int(t['row_sum_ok'].sum())} of {n} rows add up to their total (within 1 ha). Anyone reading the file with a spreadsheet "
        "formula will get areas 1,000 times too small for every value of 1,000 ha or more.", "",
        "## Against the PPEG analysis and the project's priority KHG", "",
        f"- KHG names matched to the registry (SK.129/2017): {int(t['khg_code'].notna().sum())} of {n}.",
        f"- In the project's 362 priority KHG: {int(in_ours.sum())} of {n}; of these, {int((in_ours & t['in_target_villages'].fillna(False).astype(bool)).sum())} "
        "through the Bluebook target villages. "
        f"Not in the 362: {', '.join(t.loc[~in_ours, 'khg_name_xlsx']) or 'none'}.",
        f"- Priority KHG of the project not in the workbook: {len(not_in_xlsx)} "
        f"({int(not_in_xlsx['in_target_villages'].sum())} through target villages, {int((~not_in_xlsx['in_target_villages'] & not_in_xlsx['has_skeg_damage']).sum())} through SKEG damage only).",
        f"- Recomputed from the PPEG file inside the 2,004 target villages: the workbook's KHG total equals the PPEG area within 1 ha "
        f"for {match['tv_all']} KHG on all land and {match['tv_peat']} on peat only. National totals: workbook {grand['total']:,.0f} ha; "
        f"PPEG in target villages {P['tv_all']['total'].sum():,.0f} ha on all land, {P['tv_peat']['total'].sum():,.0f} ha on peat.",
        f"- So the workbook's areas are the PPEG intervention classes of {'all land' if best == 'tv_all' else 'peat'} inside the "
        "target villages, by KHG.",
        f"- The 337 KHG are the KHG that hold target-village land: the project's {int(pk['in_target_villages'].sum())} target-village KHG "
        f"less {int(not_in_xlsx['in_target_villages'].sum())} whose target-village land is at most "
        f"{not_in_xlsx.loc[not_in_xlsx['in_target_villages'], 'target_village_ha'].max():,.0f} ha (boundary slivers between the village "
        "and KHG layers). This is the 337 of KLH's FGD terms of reference.", "",
        "## Rows to check", "",
        "Rows whose four classes do not add up to the total:", "",
        *[f"- {r.khg_name_xlsx}: classes {r.c01 + r.c02 + r.c03 + r.c04:,.0f} ha, total {r.total:,.0f} ha" for r in t[~t["row_sum_ok"]].itertuples()], "",
        "KHG whose total differs from the PPEG area in the target villages (all land) by more than 1 ha:", "",
        "| KHG | Workbook (ha) | PPEG in target villages (ha) | Difference (ha) |", "|---|---|---|---|",
        *[f"| {r.khg_name_xlsx} | {r.total:,.0f} | {r.tv_all_total:,.0f} | {r.tv_all_diff:+,.0f} |" for r in t[t["tv_all_diff"].abs() > 1].itertuples()], "",
        "Priority KHG with target-village land that the workbook leaves out:", "",
        "| KHG | Target-village land (ha) | SKEG-damaged peat (ha) |", "|---|---|---|",
        *[f"| {r.khg_name} | {r.target_village_ha:,.0f} | {r.priority_ha:,.0f} |"
          for r in not_in_xlsx[not_in_xlsx["in_target_villages"]].sort_values("target_village_ha", ascending=False).itertuples()], "",
    ]
    (OUT / "khg337_tim_gis.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
