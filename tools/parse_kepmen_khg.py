"""Parse the official KHG table of SK.129/MENLHK/SETJEN/PKL.0/2/2017 into sites/khg_registry.csv.

    python tools/parse_kepmen_khg.py [PDF]      # default docs/reference/KepmenLHK022017.pdf

Reads word positions (pdfplumber), not text order: the PDF's text order scrambles the columns. A row starts at a
number in the first column; lines without a number continue the previous row (long names, extra kabupaten).
Columns: khg_code, island, no, name, province, kabupaten, area_ha_kepmen. Needs pdfplumber.
"""
import re
import sys
from pathlib import Path

import pandas as pd
import pdfplumber

HUB = Path(__file__).resolve().parents[1]
# x boundaries (pt) of the columns on the landscape pages: no | name | code | province | kabupaten | area
COLS = [("no", 0, 85), ("name", 85, 300), ("code", 300, 415), ("province", 415, 560), ("kabupaten", 560, 720), ("area", 720, 900)]


def col(x):
    return next(c for c, a, b in COLS if a <= x < b)


def parse(pdf_path):
    rows, island = [], ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            if not any(w["text"] == "Kode" for w in words):
                continue
            lines = {}
            for w in words:
                lines.setdefault(round(w["top"] / 4), []).append(w)
            for key in sorted(lines):
                ws = sorted(lines[key], key=lambda w: w["x0"])
                text = " ".join(w["text"] for w in ws)
                footer = ws[0]["text"].isdigit() and 300 < ws[0]["x0"] < 560  # page number, sometimes with the island name
                if "Salinan" in text:
                    break  # certification block after the last row
                if footer or text.startswith("Total") or text.replace(" ", "").startswith("INDONESIA"):
                    continue  # page number, island total, grand total, certification
                if re.match(r"^PULAU\b|^KEPULAUAN\b", text) and all(w["x0"] > 300 for w in ws):
                    island = text
                    continue
                first = ws[0]
                if first["x0"] < 85 and re.fullmatch(r"\d+", first["text"]):
                    rows.append({"island": island, "no": int(first["text"]), "page": page.page_number,
                                 **{c: "" for c, _, _ in COLS[1:]}})
                    ws = ws[1:]
                elif not rows or not any(w["x0"] >= 85 for w in ws) or text.startswith(("No.", "Luas", "(Ha)", "Nama")):
                    continue
                for w in ws:
                    t, c = w["text"], col(w["x0"])
                    if re.match(r"^\d+[A-Za-z]", t):  # page number printed over the province: "12Sumatera"
                        t, c = re.sub(r"^\d+", "", t), "province"
                    if c != "no":
                        rows[-1][c] = (rows[-1][c] + " " + t).strip()
    df = pd.DataFrame(rows)
    df["name"] = df["name"].str.replace("’", "'", regex=False)  # the PDF has a typographic apostrophe in "I'wai"
    df["area_ha_kepmen"] = pd.to_numeric(df.pop("area").str.replace(".", "", regex=False), errors="coerce")
    return df


def main():
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else HUB / "docs" / "reference" / "KepmenLHK022017.pdf"
    df = parse(pdf)
    df.insert(0, "khg_code", df.pop("code"))
    out = HUB / "sites" / "khg_registry.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    print(f"{len(df)} rows -> {out}; codes unique: {df.khg_code.nunique()}; empty code: {(df.khg_code == '').sum()}; "
          f"empty area: {df.area_ha_kepmen.isna().sum()}; total area ha: {df.area_ha_kepmen.sum():.0f}")


if __name__ == "__main__":
    main()
