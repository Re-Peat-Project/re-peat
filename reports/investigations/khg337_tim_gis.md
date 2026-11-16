# Team 337-KHG work list (Sept 2026)

Source: `_data/Tim GIS - Intervensi Pembasahan Karhutla pada 337 KHG (2004 Desa DMPG), Sept 2026.xlsx` (one sheet, received 2026-11-13). Inventory script: `re-peat/tools/inventory_337khg.py`; per-KHG table: `khg337_tim_gis.csv`.

## Content

- Title: "Pekerjaan pembuatan desain intervensi pembasahan dalam rangka pengendalian kebakaran hutan dan lahan pada 337 Kesatuan Hidrologis Gambut (2004 desa prioritas program DMPG)".
- 337 KHG rows (Sumatera 162, Kalimantan 147, Papua 25, Sulawesi 3), each with province, the area in the four PPEG intervention classes, total area, the GIS team and five work-stage flags (Jalur Pembasahan, Sekat Kanal, Pompa Air, Pintu Air, Layout Peta).
- Totals row "Total Intervensi 2004 Desa Prioritas DMPG Tahun 2026-2030": 01. Terbakar, Berkanal (R1, R2, R3) 903,709 ha, 02. Terbakar, Non Kanal (R2, R3) 741,449 ha, 03. Non Terbakar, Berkanal (R1, R3) 5,740,282 ha, 04. Non Terbakar, Non Kanal (R3) 5,452,264 ha; total 12,837,704 ha.
- Teams: Tim 1 (56 KHG), Tim 2 (56 KHG), Tim 3 (56 KHG), Tim 4 (56 KHG), Tim 5 (56 KHG), Tim 6 (57 KHG).
- Work stages marked done: Jalur Pembasahan 1, Sekat Kanal 0, Pompa Air 0, Pintu Air 0, Layout Peta 0.

## Reading the numbers

Areas of 1,000 ha or more were typed with dots as thousands separators, so the workbook stores them as decimals (1,105 ha as 1.105) and the totals rows as text. Read as thousands, 336 of 337 rows add up to their total (within 1 ha). Anyone reading the file with a spreadsheet formula will get areas 1,000 times too small for every value of 1,000 ha or more.

## Against the PPEG analysis and the project's priority KHG

- KHG names matched to the registry (SK.129/2017): 337 of 337.
- In the project's 362 priority KHG: 337 of 337; of these, 337 through the Bluebook target villages. Not in the 362: none.
- Priority KHG of the project not in the workbook: 25 (8 through target villages, 17 through SKEG damage only).
- Recomputed from the PPEG file inside the 2,004 target villages: the workbook's KHG total equals the PPEG area within 1 ha for 324 KHG on all land and 1 on peat only. National totals: workbook 12,837,704 ha; PPEG in target villages 12,993,719 ha on all land, 9,233,702 ha on peat.
- So the workbook's areas are the PPEG intervention classes of all land inside the target villages, by KHG.
- The 337 KHG are the KHG that hold target-village land: the project's 345 target-village KHG less 8 whose target-village land is at most 8 ha (boundary slivers between the village and KHG layers). This is the 337 of KLH's FGD terms of reference.

## Rows to check

Rows whose four classes do not add up to the total:

- KHG Sungai Mendahara - Sungai Batanghari: classes 144,302 ha, total 177,268 ha

KHG whose total differs from the PPEG area in the target villages (all land) by more than 1 ha:

| KHG | Workbook (ha) | PPEG in target villages (ha) | Difference (ha) |
|---|---|---|---|
| KHG Lae Sibungkuang | 93 | 8,749 | -8,656 |
| KHG Lae Silabuhan - Lae Tambiski | 7,343 | 8,015 | -672 |
| KHG Sungai Barumun - Sungai Kubu | 113,798 | 232,193 | -118,395 |
| KHG Sungai Batang - Sungai Tungkal | 22,557 | 51,948 | -29,391 |
| KHG Sungai Air Hitam Laut - Sungai Buntu Kecil | 115,551 | 125,475 | -9,924 |
| KHG Sungai Lalan - Sungai Merang | 3,351 | 81,594 | -78,243 |
| KHG Aek Silaut - Aek Menjuto | 5,265 | 12,272 | -7,007 |
| KHG Sungai Keramat - Sungai Jelai | 21,637 | 21,640 | -3 |
| KHG Sungai Lamandau - Sungai Jelai | 85,466 | 85,468 | -2 |
| KHG Sungai Utar - Sungai Serapat | 4,262 | 23,949 | -19,687 |
| KHG Sungai Pasang Kayu - Sungai Bambalamotu | 12,842 | 18,333 | -5,491 |
| KHG Sungai Salo Lariang - Sungai Pasang Kayu | 11,158 | 16,794 | -5,636 |
| KHG Sungai Bumi - Sungai Pepeya | 2,365 | 4,019 | -1,654 |

Priority KHG with target-village land that the workbook leaves out:

| KHG | Target-village land (ha) | SKEG-damaged peat (ha) |
|---|---|---|
| KHG Sungai Kla Sepa - Sungai Kla Kaibus | 8 | 0 |
| KHG Bah Kambang - Batang Airlakitan | 5 | 0 |
| KHG Sungai Embau - Sungai Kapuas | 4 | 0 |
| KHG Krueng Susoh - Krueng Batee | 3 | 0 |
| KHG Sungai Labai - Sungai Kualan | 0 | 6,188 |
| KHG Sungai Ifuleki Kumbe - Sungai Lekiagi | 0 | 12 |
| KHG Sungai Wai Tunun I | 0 | 7 |
| KHG Sungai Jenu - Sungai Labai | 0 | 0 |
