# SiTMAT map layers: inventory

`python tools/inventory_sitmat_layers.py` on the files written by `repeat_common.fetch_sitmat_layers`. Both layers are served by the SiTMAT portal of the Kementerian Lingkungan Hidup as one GeoJSON each, EPSG:4326. Areas are in EPSG:6933.

## Lahan gambut Indonesia 2025

Endpoint `https://sitmat.kemenlh.go.id/api/lahan-gambut-indonesia-2025`, fetched 2026-10-28 (ETag W/"4525925b15355a6e0c01427b38c466910c17a250"). File `peat/lahan_gambut_indonesia_2025.gpkg`, layer `lahan_gambut`: 8,586 polygons, 35 of them invalid as delivered (kept, not repaired). Fields: PULAU, PROV_2023, KABKO_2023, LAHAN_GAMB. `LAHAN_GAMB` is LAHAN GAMBUT or NON LAHAN GAMBUT; island and province names are the 2023 administrative names. No date, scale, method or licence is given in the response.

Peat: 13.33 million ha in 3,181 polygons; non-peat: 11.42 million ha in 5,405 polygons.

Table: by island.

| island | peat (thousand ha) | non-peat (thousand ha) |
|---|---|---|
| Pulau Kalimantan | 5,269 | 3,401 |
| Pulau Papua | 1,650 | 4,974 |
| Pulau Sulawesi | 31 | 45 |
| Pulau Sumatera | 6,384 | 3,005 |

Table: peat by province.

| island | province | peat (thousand ha) |
|---|---|---|
| Pulau Sumatera | Riau | 3,957 |
| Pulau Kalimantan | Kalimantan Tengah | 2,940 |
| Pulau Kalimantan | Kalimantan Barat | 1,715 |
| Pulau Sumatera | Sumatera Selatan | 1,166 |
| Pulau Papua | Papua Selatan | 928 |
| Pulau Sumatera | Jambi | 560 |
| Pulau Sumatera | Sumatera Utara | 356 |
| Pulau Kalimantan | Kalimantan Utara | 277 |
| Pulau Papua | Papua Tengah | 275 |
| Pulau Papua | Papua Barat Daya | 265 |
| Pulau Kalimantan | Kalimantan Timur | 264 |
| Pulau Sumatera | Aceh | 158 |
| Pulau Sumatera | Sumatera Barat | 131 |
| Pulau Papua | Papua | 74 |
| Pulau Kalimantan | Kalimantan Selatan | 71 |
| Pulau Papua | Papua Barat | 58 |
| Pulau Papua | Papua Pegunungan | 50 |
| Pulau Sumatera | Kepulauan Bangka Belitung | 24 |
| Pulau Sumatera | Lampung | 22 |
| Pulau Sulawesi | Sulawesi Barat | 20 |
| Pulau Sulawesi | Sulawesi Tengah | 12 |
| Pulau Sumatera | Bengkulu | 6 |
| Pulau Sumatera | Kepulauan Riau | 4 |

Table: peat in the selected KHG and the earlier test site, SiTMAT 2025 map against the GFW composite extent used by the national profile (peat_km2).

| KHG | KHG area (ha) | peat, SiTMAT 2025 (ha) | share of KHG (%) | peat, GFW extent (ha) | SiTMAT / GFW |
|---|---|---|---|---|---|
| Pulau Bengkalis | 90,627 | 75,163 | 83 | 89,331 | 0.84 |
| Pulau Padang | 111,240 | 104,174 | 94 | 110,176 | 0.95 |
| Pulau Tebing Tinggi | 138,029 | 132,767 | 96 | 136,439 | 0.97 |
| Sungai Air Hitam Laut - Sungai Buntu Kecil | 183,705 | 149,260 | 81 | 143,182 | 1.04 |
| Sungai Balangan - Sungai Batangalai | 30,803 | 14,258 | 46 | 13,710 | 1.04 |
| Sungai Buru Mappi - Sungai Buru Obaa | 397,875 | 121,834 | 31 | 169,931 | 0.72 |
| Sungai Kahayan - Sungai Sebangau | 450,293 | 318,829 | 71 | 395,476 | 0.81 |
| Sungai Kampar - Sungai Gaung | 710,814 | 588,362 | 83 | 686,274 | 0.86 |
| Sungai Kapuas - Sungai Barito | 557,372 | 398,048 | 71 | 440,663 | 0.90 |
| Sungai Mempawah - Sungai Peniti | 51,044 | 34,313 | 67 | 37,626 | 0.91 |
| Sungai Mendahara - Sungai Batanghari | 201,283 | 114,904 | 57 | 173,090 | 0.66 |
| Sungai Pungurbesar - Sungai Kapuas | 101,268 | 53,579 | 53 | 74,413 | 0.72 |
| Sungai Saleh - Sungai Sugihan | 189,802 | 61,832 | 33 | 160,691 | 0.38 |
| Sungai Sugihan - Sungai Lumpur | 635,147 | 343,452 | 54 | 542,425 | 0.63 |

## Batas desa DMPG

Endpoint `https://sitmat.kemenlh.go.id/api/batas-desa-dmpg`, fetched 2026-10-28 (ETag W/"562e090a79861c87c564ac3a24adbefd70688a7a"). File `dpg/dmpg_villages_sitmat.gpkg`, layer `dmpg_villages`: 838 village polygons, 0 invalid. Fields: PROVINSI, KABUPATEN, KECAMATAN, DESA, PROG_DMPG, Skema_DPG. 816 distinct village names; 0 rows share province, district, sub-district and name with another row. Total area 8.67 million ha (median village 4,422 ha).

Table: villages by province and programme.

| province | Skema DMPG | Skema DMPG dan DMPM | total |
|---|---|---|---|
| Aceh | 3 | 0 | 3 |
| Jambi | 79 | 0 | 79 |
| Kalimantan Barat | 107 | 29 | 136 |
| Kalimantan Selatan | 47 | 0 | 47 |
| Kalimantan Tengah | 200 | 0 | 200 |
| Kalimantan Utara | 1 | 0 | 1 |
| Papua | 26 | 0 | 26 |
| Riau | 196 | 48 | 244 |
| Sumatera Selatan | 95 | 0 | 95 |
| Sumatera Utara | 7 | 0 | 7 |
| total | 761 | 77 | 838 |

`Skema_DPG` lists each village's support as entries of year and source, separated by semicolons. The first entry gives the year the village entered the programme; 289 villages have one or more later entries (for example a 2022 or 2024 APBN round, KEDAIREKA, BNPB or a company programme).

Table: villages by year and source of the first entry in `Skema_DPG`.

| first year | APBN (state budget) | Kemitraan (partnership) | other partner or programme | total |
|---|---|---|---|---|
| 2017 | 75 | 0 | 0 | 75 |
| 2018 | 75 | 93 | 19 | 187 |
| 2019 | 75 | 0 | 57 | 132 |
| 2020 | 83 | 50 | 112 | 245 |
| 2021 | 53 | 0 | 10 | 63 |
| 2022 | 44 | 0 | 14 | 58 |
| 2023 | 24 | 0 | 0 | 24 |
| 2024 | 38 | 0 | 0 | 38 |
| no year | 16 | 0 | 0 | 16 |
| total | 483 | 143 | 212 | 838 |

Table: DMPG villages in the selected KHG and the earlier test site.

| KHG | DMPG villages (representative point inside) |
|---|---|
| Pulau Bengkalis | 33 |
| Pulau Padang | 11 |
| Pulau Tebing Tinggi | 11 |
| Sungai Air Hitam Laut - Sungai Buntu Kecil | 8 |
| Sungai Balangan - Sungai Batangalai | 13 |
| Sungai Buru Mappi - Sungai Buru Obaa | 8 |
| Sungai Kahayan - Sungai Sebangau | 34 |
| Sungai Kampar - Sungai Gaung | 2 |
| Sungai Kapuas - Sungai Barito | 18 |
| Sungai Mempawah - Sungai Peniti | 13 |
| Sungai Mendahara - Sungai Batanghari | 16 |
| Sungai Pungurbesar - Sungai Kapuas | 14 |
| Sungai Saleh - Sungai Sugihan | 17 |
| Sungai Sugihan - Sungai Lumpur | 15 |

### Match with the BRG atlas villages

The 244 villages of the BRG atlas (2018-2019 mapping, boundaries from the KLH 2023 village boundaries) were matched to the DMPG layer by village and district name, ignoring case, spaces and punctuation: 224 of 244 found. For matched pairs the overlap of the two polygons (intersection over union) has median 1.00; 220 pairs reach 0.8 or more and 1 are below 0.2.

| province | atlas villages | found in DMPG layer |
|---|---|---|
| Jambi | 26 | 24 |
| Kalbar | 41 | 40 |
| Kalsel | 23 | 22 |
| Kalteng | 74 | 65 |
| Riau | 40 | 34 |
| Sumsel | 40 | 39 |

