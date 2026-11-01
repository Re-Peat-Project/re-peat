"""Unit costs of Perdirjen PPKL P.16/PPKL/PKEG/PKL.0/10/2022 (Standar Biaya Pembangunan Infrastruktur Pembasahan) as a CSV.

  .venv/Scripts/python.exe re-peat/tools/extract_perdirjen_p16.py

Reads the text layer of `re-peat/docs/reference/Buku Perdirjen P.16 Tahun 2022 (Daftar Isi) 2.pdf` (526 pages; Lampiran I, the cost
tables, is printed pages 9-30 = PDF pages 21-41) and writes `re-peat/docs/reference/perdirjen_p16_2022_unit_costs.csv`:
one row per code, with contractual and self-managed (swakelola) cost in rupiah, dimensions and canal width. Row counts are checked
against the code lists in the book's table of contents (50 priced sekat, 12 penimbunan, 24 sumur bor; KSE-1L is "Harga Pasar Setempat", no standard price); the run stops if they differ.
The PDF is read page range by page range, never whole: the cost tables are about 20 pages of text.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import pymupdf

HUB = Path(__file__).resolve().parents[1]
PDF = HUB / "docs/reference/Buku Perdirjen P.16 Tahun 2022 (Daftar Isi) 2.pdf"
OUT = HUB / "docs/reference/perdirjen_p16_2022_unit_costs.csv"
FIRST, LAST = 21, 41  # PDF pages of Lampiran I


def flat(doc, a: int, b: int) -> str:
    t = " ".join(doc[i - 1].get_text() for i in range(a, b + 1))
    return re.sub(r"\s+", " ", t.replace("≤", "<=").replace("–", "-").replace("�", "-"))


def rp(s: str) -> int:
    return int(s.replace(".", ""))


def main() -> None:
    doc = pymupdf.open(PDF)
    rows = []
    # find the three sections by their headings
    pages = {i: flat(doc, i, i) for i in range(FIRST, LAST + 1)}
    sec = {"sekat": [], "penimbunan": [], "sumur_bor": []}
    cur = "sekat"
    for i, t in pages.items():
        if "STANDAR BIAYA OPERASIONAL TEKNIS PENIMBUNAN" in t:
            cur = "penimbunan"
        if "STANDAR BIAYA OPERASIONAL TEKNIS PEMBANGUNAN SUMUR BOR" in t:
            cur = "sumur_bor"
        sec[cur].append(t)
    # sekat: CODE contractual swakelola width length depth, then canal width limits
    s = " ".join(sec["sekat"])
    pat = re.compile(r"(KSE-[A-Z0-9][A-Z0-9\- ]*?)\s+(\d{1,3}(?:\.\d{3}){2,})\s+(\d{1,3}(?:\.\d{3}){2,})\s+(\d+,\d+)\s+(\d+,\d+)\s+(\d+,\d+)\s+(.{0,40}?)\s+(?:Sekat|Kanal|Permanen)")
    for m in pat.finditer(s):
        code = re.sub(r"\s+", "", m.group(1)).replace("--", "-").replace("-P1", "-P1")
        lk = m.group(7)
        up = re.search(r"<=\s*([\d,]+)", lk)
        rows.append({"jenis": "sekat", "kode": code, "biaya_kontraktual_idr": rp(m.group(2)), "biaya_swakelola_idr": rp(m.group(3)),
                     "lebar_m": m.group(4).replace(",", "."), "panjang_m": m.group(5).replace(",", "."), "dalam_m": m.group(6).replace(",", "."),
                     "lebar_kanal_maks_m": up.group(1).replace(",", ".") if up else "", "keterangan": lk.strip()})
    # penimbunan: CODE contractual width length depth LK
    s = " ".join(sec["penimbunan"])
    for m in re.finditer(r"(KTI-\d+-\d)\s+(\d{1,3}(?:\.\d{3}){2,})\s+(\d+,\d+)\s+(\d+,\d+)\s+(\d+,\d+)\s+(.{0,25}?)\s+Penimbunan", s):
        up = re.search(r"<=\s*([\d,]+)", m.group(6))
        rows.append({"jenis": "penimbunan", "kode": m.group(1), "biaya_kontraktual_idr": rp(m.group(2)), "biaya_swakelola_idr": "",
                     "lebar_m": m.group(3).replace(",", "."), "panjang_m": m.group(4).replace(",", "."), "dalam_m": m.group(5).replace(",", "."),
                     "lebar_kanal_maks_m": up.group(1).replace(",", ".") if up else "", "keterangan": m.group(6).strip()})
    # sumur bor: CODE contractual swakelola pipe size depth
    s = " ".join(sec["sumur_bor"])
    for m in re.finditer(r"(SBO-\d+-\d)\s+(\d{1,3}(?:\.\d{3}){1,2})\s+(\d{1,3}(?:\.\d{3}){1,2})\s+(.{3,30}?)\s+(\d+,\d+\"|3\"\s*&\s*1,5\"|PVC 3\"\+)\s+(?:1,5\"\s+)?(\d+,\d+)\s", s):
        rows.append({"jenis": "sumur_bor", "kode": m.group(1), "biaya_kontraktual_idr": rp(m.group(2)), "biaya_swakelola_idr": rp(m.group(3)),
                     "lebar_m": "", "panjang_m": "", "dalam_m": m.group(6).replace(",", "."), "lebar_kanal_maks_m": "", "keterangan": m.group(4).strip()})
    df = pd.DataFrame(rows).drop_duplicates("kode")
    n = df.jenis.value_counts().to_dict()
    expected = {"sekat": 50, "penimbunan": 12, "sumur_bor": 24}
    print(n)
    if n != expected:
        got = set(df.kode)
        print("expected", expected, "- check the pattern; codes found:", sorted(got)[:80], file=sys.stderr)
        sys.exit(1)
    df.to_csv(OUT, index=False)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
