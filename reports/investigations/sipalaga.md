# SIPALAGA: inventory

`python tools/inventory_sipalaga.py` on the files written by `python -m repeat_common.fetch_sipalaga` into `_data/sipalaga/`. SIPALAGA (Sistem Pemantauan Air Lahan Gambut) was the Badan Restorasi Gambut network of automatic stations logging groundwater level, soil moisture and rain every hour; its portal no longer serves data.

| Source | What | Licence |
|---|---|---|
| github.com/danylaksono/sipalaga-crawler (pinned commit) | daily PDF reports converted to hourly CSV per province; download URL lists | not stated |
| Taufik et al. 2023, Data in Brief 46, 108889, table 1 | 21 stations with code, KHG, longitude and latitude (2 decimals) | CC BY 4.0 |
| Apers et al. 2022, JAMES 14, e2021MS002784, table B1 | 59 SIPALAGA and 10 SATREPS sites with code, village, coordinates (3 decimals), drained or undrained, record period | CC BY 4.0 |
| Mendeley Data 27y943wbkw | monthly peat moisture at 10-20 cm, 21 stations | CC BY 4.0 |
| Mendeley Data jj35xcx98v, 9stvfxystv | water retention at pF 1, 2, 2.54, 4.2 of peat samples in Riau, and plot coordinates | CC BY 4.0 |
| SiTMAT station list (`repeat-sitmat`) | community stations named BRG_... with coordinates and 2026 records | not stated |

## Stations

`sipalaga_stations.gpkg` holds 180 station codes: 135 in the BRG_<area code>_<nn> form and 45 other names (BRG9, LUMPUR1, SELEH2, TINGGI1 in the crawler; SATREPS sites such as TAKA4 in Apers et al. 2022). 160 have coordinates.

Table: station codes by source.

| crawler_csv | crawler_urls | taufik2023 | apers2022 | sitmat | stations |
|---|---|---|---|---|---|
|  |  |  |  | yes | 23 |
|  |  |  | yes |  | 16 |
|  |  | yes |  |  | 1 |
|  |  | yes | yes |  | 1 |
|  | yes |  |  |  | 6 |
|  | yes |  | yes |  | 1 |
| yes | yes |  |  |  | 71 |
| yes | yes |  | yes |  | 42 |
| yes | yes | yes |  |  | 10 |
| yes | yes | yes | yes |  | 9 |

Table: stations by province and source of the coordinates (sitmat: SiTMAT station list; apers2022: Apers et al. 2022 table B1; taufik2023: Taufik et al. 2023 table; village: representative point of the village the crawler names, KLH 2023 village boundaries; none: no position).

| province | apers2022 | none | sitmat | taufik2023 | village | total |
|---|---|---|---|---|---|---|
| JAMBI | 7 | 0 | 0 | 2 | 5 | 14 |
| KALIMANTAN BARAT | 10 | 1 | 6 | 0 | 7 | 24 |
| KALIMANTAN SELATAN | 4 | 0 | 0 | 0 | 1 | 5 |
| KALIMANTAN TENGAH | 20 | 5 | 4 | 0 | 16 | 45 |
| PAPUA | 1 | 1 | 0 | 0 | 0 | 2 |
| RIAU | 21 | 3 | 11 | 7 | 23 | 65 |
| SUMATERA SELATAN | 6 | 4 | 0 | 2 | 7 | 19 |
| total | 69 | 14 | 21 | 11 | 59 | 174 |

No position for 20 codes: 6 are only in the URL lists (no location given); 12 name a village not found by name (national park or site labels such as TN_SEBANGAU_1, or a name spelled differently); SiTMAT points at 0,0 or outside the province are not used (2).

156 stations fall in a KHG; 59 in the selected KHG and the Kampar-Gaung test site.

Table: stations in the selected KHG.

| khg | stations | codes | coordinates |
|---|---|---|---|
| KHG Pulau Bengkalis | 6 | BRG_140301_01, BRG_140301_02, BRG_140301_03, BRG_140301_04, BRG_140302_01, BRG_140302_02 | apers2022, sitmat, taufik2023, village |
| KHG Pulau Padang | 3 | BRG_141005_01, BRG_141005_02, BRG_141008_01 | sitmat |
| KHG Pulau Tebing Tinggi | 5 | BRG_141004_01, BRG_141004_02, BRG_141007_01, TINGGI1, TINGGI2 | sitmat, village |
| KHG Sungai Air Hitam Laut - Sungai Buntu Kecil | 1 | BRG6 | village |
| KHG Sungai Balangan - Sungai Batangalai | 5 | BRG16, BRG_630708_01, BRG_630805_01, BRG_630805_02, BRG_631104_01 | apers2022, village |
| KHG Sungai Kahayan - Sungai Sebangau | 14 | BRG_621101_01, BRG_621101_02, BRG_621105_02, BRG_621105_03, BRG_621107_01, BRG_621107_02, BRG_621107_03, BRG_621107_04, BRG_621107_06, BRG_621107_07, KALTENG1, TAKA1_PALANGKRAYA, TAKA5_SEBANGAU, TARUNA-B1 | apers2022, village |
| KHG Sungai Kampar - Sungai Gaung | 3 | BRG_140412_01, BRG_140412_02, BRG_140416_01 | apers2022, village |
| KHG Sungai Kapuas - Sungai Barito | 4 | BRG12, BRG13, BRG14, TAKA4 | apers2022, village |
| KHG Sungai Mempawah - Sungai Peniti | 4 | BRG_610207_01, BRG_610207_02, BRG_610216_01, BRG_610218_01 | apers2022, village |
| KHG Sungai Mendahara - Sungai Batanghari | 7 | BRG_150706_01, BRG_150709_01, BRG_150709_02, BRG_150710_01, BRG_150710_02, BRG_150710_03, JAMBI1 | apers2022, taufik2023, village |
| KHG Sungai Pungurbesar -  Sungai Kapuas | 3 | BRG19, BRG_611209_01, KALBAR1 | apers2022, village |
| KHG Sungai Sugihan - Sungai Lumpur | 4 | BRG_160214_01, BRG_160214_02, LUMPUR1, OKI2 | taufik2023, village |

## Hourly records 2019 (crawler)

67,394 hourly rows from 132 stations, table dates 2018-12-08 to 2019-03-18 (the reports were downloaded 2019-02-19 to 2019-03-17). Median 27 days and 600 hours per station. Fields: groundwater level (`gwater`, m, negative below the surface), soil moisture (`smoisture`, %), rain (`precip`, mm) as mean, min and max per hour, and the portal's status class.

Groundwater level within -3.0 to 0.5 m: 92.8% of rows (median -0.46 m; values up to 2,186 outside). Soil moisture within 0-100%: 92.0%.

Table: groundwater level by province, plausible rows only.

| province | stations | rows | median_m | deeper_than_40cm_pct |
|---|---|---|---|---|
| JAMBI | 13 | 6221 | -0.30 | 36.81 |
| KALIMANTAN_BARAT | 12 | 6778 | -0.49 | 67.47 |
| KALIMANTAN_SELATAN | 5 | 1032 | -0.16 | 4.17 |
| KALIMANTAN_TENGAH | 32 | 17306 | -0.20 | 20.11 |
| PAPUA | 2 | 102 | -0.28 | 43.14 |
| RIAU | 45 | 24927 | -0.70 | 92.08 |
| SUMATERA_SELATAN | 15 | 6159 | -0.12 | 2.57 |

Table: status classes as reported.

| status | rows |
|---|---|
| BAHAYA | 36048 |
| SIAGA | 22094 |
| AMAN | 8995 |
| KOSONG | 257 |

## BRG stations in SiTMAT

23 SiTMAT community stations carry a BRG_ code in the same form (the six digits match the province and district of the site). None of these codes is in the 2019 crawler, its URL lists, Taufik et al. 2023 or Apers et al. 2022, so no SiTMAT record can be joined to a 2019 record by code. The nearest 2019 station to each usable SiTMAT point lies 2.1 to 210 km away (median 18 km); most 2019 positions are village points, so distance cannot show whether a logger was moved or renamed. 12 of the 23 have at least one water level in SiTMAT; 9 have 60 days or more.

| code | sitmat_station_id | days | first | last | median_cm |
|---|---|---|---|---|---|
| BRG_140301_03 | MTI-9BT33VBEJTHV | 79 | 2026-07-21 | 2026-10-22 | -208 |
| BRG_140301_04 | MTI-13R6GKKDBU1X | 79 | 2026-07-21 | 2026-10-22 | -179 |
| BRG_140313_02 | MTI-3J5MPFRRO7N0 | 1 | 2026-08-20 | 2026-08-20 |  |
| BRG_140706_01 | MTI-6RN68VCBRTEN | 2 | 2026-08-20 | 2026-08-26 | 90 |
| BRG_140710_01 | MTI-BWMJEF9L0EJ4 | 1 | 2026-08-20 | 2026-08-20 |  |
| BRG_140714_01 | MTI-J78DI8MRXN59 | 1 | 2026-08-20 | 2026-08-20 |  |
| BRG_141004_01 | MTI-X1R4W07JKW0U | 1 | 2026-08-20 | 2026-08-20 |  |
| BRG_141004_02 | MTI-HPDWC0NK0G2E | 79 | 2026-07-21 | 2026-10-22 | -152 |
| BRG_141005_01 | MTI-JK3UT52ST1GS | 73 | 2026-07-21 | 2026-10-21 | -69 |
| BRG_141005_02 | MTI-778N952JF9Q9 | 79 | 2026-07-21 | 2026-10-22 | -148 |
| BRG_141007_01 | MTI-0QPGP748RCSW | 79 | 2026-07-21 | 2026-10-22 | -150 |
| BRG_141008_01 | MTI-0PY44HEH6LBX | 1 | 2026-08-20 | 2026-08-20 |  |
| BRG_141009_02 | MTI-P7C7AJVB3RQT | 1 | 2026-08-20 | 2026-08-20 |  |
| BRG_610412_01 | MTI-96DGTXVHGWYA | 2 | 2026-08-20 | 2026-09-27 | 150 |
| BRG_610417_01 | MTI-A1547QSJXCF1 | 1 | 2026-08-20 | 2026-08-20 |  |
| BRG_611203_03 | MTI-1UHDSWLVN1C4 | 1 | 2026-08-20 | 2026-08-20 |  |
| BRG_611203_04 | MTI-JYLQBI8YDMWF | 1 | 2026-08-20 | 2026-08-20 |  |
| BRG_611205_01 | MTI-6IY9N869MOWZ | 1 | 2026-08-20 | 2026-08-20 |  |
| BRG_611206_02 | MTI-WKQURWGVYLJW | 79 | 2026-07-21 | 2026-10-22 | -155 |
| BRG_620102_01 | MTI-RX2VD81WKKTS | 79 | 2026-07-21 | 2026-10-22 | -1 |
| BRG_620102_02 | MTI-1IKTIWUIRETP | 3 | 2026-07-21 | 2026-07-23 | 0 |
| BRG_620201_01 | MTI-1UM6LFUBJ628 | 79 | 2026-07-21 | 2026-10-22 | -138 |
| BRG_620309_03 | MTI-BHTOIBDSAJH2 | 1 | 2026-08-20 | 2026-08-20 |  |

## Monthly peat moisture (Taufik et al. 2023)

21 stations, 2018-10 to 2019-12, 224 station-months; volumetric water content at 10-20 cm (HydraProbe), as a fraction: median 0.42, range 0.15 to 0.78.

## Water retention, Riau (Taufik et al. 2023)

107 samples (19 plots, sampled 2019 and 2022) at 0-30 cm (topsoil) and 50-70 cm (subsoil); 19 plot coordinates. pF 1 and pF 2 are suctions of 0.1 m and 1 m of water, so the difference of water content between them is the water a sample releases as suction rises over the first metre. It is an indication of drainable porosity near the surface, not a measured specific yield.

Table: volumetric water content (% volume), sample-weighted means by layer.

| layer | plots | samples | pF1 | pF2 | pF1 - pF2 | min pF1 - pF2 | max pF1 - pF2 |
|---|---|---|---|---|---|---|---|
| subsoil | 18 | 52 | 69.2 | 48.1 | 21.1 | 14.8 | 30.2 |
| topsoil | 19 | 55 | 70.9 | 48.5 | 22.4 | 12.8 | 28.4 |

Table: by land use, both layers.

| land use | samples | pF1 - pF2 |
|---|---|---|
| Cropland | 12 | 16.4 |
| Imperata | 6 | 25.5 |
| Mixed garden | 10 | 21.9 |
| Oil Palm | 50 | 22.4 |
| Pinapple | 4 | 25.0 |
| Rubber | 14 | 23.9 |
| Shrub | 11 | 18.9 |

