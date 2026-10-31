# SIPALAGA and SiTMAT stations: match

`python tools/match_sipalaga_sitmat.py`. 157 SIPALAGA codes documented in 2018-2020 (crawler, its URL lists, Taufik et al. 2023, Apers et al. 2022; the 23 BRG_ codes known only from SiTMAT are the SiTMAT side, not compared with themselves) (139 placed; 109 with the polygon of the village the crawler names) against 1,244 SiTMAT stations with coordinates (85 community, 1,159 concession). Evidence: code, village name in the station name (same province), and place (inside the named village, within 0.3 km of the Apers et al. 2022 coordinate or within 1.5 km of the Taufik et al. 2023 coordinate). The 2019 and 2026 records do not overlap in time, so no pair can be confirmed by comparing readings. Candidate list: `sipalaga_sitmat_candidates.csv`.

98 pairs: 4 likely (same code, name and place, or within 0.3 km of an Apers point), 94 candidates on one kind of evidence. Likely pairs cover 2 SIPALAGA stations and 4 SiTMAT stations (4 community, 0 concession).

Table: pairs by evidence and SiTMAT station kind.

| evidence | kind | pairs |
|---|---|---|
| name | community | 3 |
| name (partial) | community | 1 |
| name (partial); place (village) | community | 1 |
| name; place (village) | community | 3 |
| place (< 1.5 km of article point) | concession | 1 |
| place (village) | community | 6 |
| place (village) | concession | 83 |

Distance from each of the 69 stations placed by Apers et al. 2022 (0.001 degree, about 100 m) to the nearest SiTMAT station of any kind. A logger kept in place, or re-registered, would sit within about 0.1-0.3 km.

Table: nearest SiTMAT station, by distance (km) and kind of that station.

| km | community | concession |
|---|---|---|
| < 0.1 | 0 | 0 |
| 0.1-0.3 | 0 | 0 |
| 0.3-1 | 1 | 0 |
| 1-3 | 2 | 7 |
| 3-10 | 1 | 18 |
| >= 10 | 11 | 34 |

Table: Apers-placed SIPALAGA stations with a SiTMAT station within 3 km.

| code | apers_site | sitmat_name | kind | km |
|---|---|---|---|---|
| BRG5 | Gedong Karya | TMA - Desa Gedong | community | 0.5 |
| BRG_160205_01 | Kedaton | Ds Tanjung Serang | community | 1.2 |
| BRG_160224_02 | Cinta Jaya | KS2-C16 | concession | 1.5 |
| TAKA4 | Palangkaraya | TP-L56 | concession | 1.7 |
| TAKA4 | Palangkaraya | TP-l56 | concession | 1.7 |
| KALBAR1 | Kalbar | KDO-G31 | concession | 2.0 |
| BRG_140806_01 | Dayun | TMA - Desa Dayun | community | 2.2 |
| BRG_160224_03 | Cinta Jaya | KS2-D43 | concession | 2.3 |
| BRG_150710_03 | Pandan Sajahtera | WKD7117 | concession | 3.0 |
| BRG3 | Sumber Agung | BGR-B016 | concession | 3.0 |

Table: likely pairs (km: from the SIPALAGA position, an article point or a village point, to the SiTMAT point).

| code | location | district | sitmat_name | kind | company_code | evidence | km | khg |
|---|---|---|---|---|---|---|---|---|
| BRG5 | GEDONG_KARYA | MUARO_JAMBI | TMA - Desa Gedong | community |  | name (partial); place (village) | 0.5 | KHG Sungai Batanghari - Sungai Air Hitam Laut |
| BRG_150706_01 | CATUR_RAHAYU | TANJUNG_JABUNG_TIMUR | AWS-Catur Rahayu 03 | community |  | name; place (village) | 3.2 | KHG Sungai Mendahara - Sungai Batanghari |
| BRG_150706_01 | CATUR_RAHAYU | TANJUNG_JABUNG_TIMUR | AWS - Catur Rahayu 01 | community |  | name; place (village) | 2.8 | KHG Sungai Mendahara - Sungai Batanghari |
| BRG_150706_01 | CATUR_RAHAYU | TANJUNG_JABUNG_TIMUR | AWS - Catur Rahayu 02 | community |  | name; place (village) | 0.9 | KHG Sungai Mendahara - Sungai Batanghari |

Table: name-only candidates (village name matches, the SiTMAT point lies outside the named village).

| code | location | district | sitmat_name | kind | company_code | evidence | km | khg |
|---|---|---|---|---|---|---|---|---|
| BRG_140313_01 | TASIK_SERAI_BARAT | BENGKALIS | TMA - Desa Tasik Serai | community |  | name (partial) | 9.4 | KHG Sungai Rokan - Sungai Siak Kecil |
| BRG_140806_01 | Dayun |  | TMA - Desa Dayun | community |  | name | 2.2 | KHG Sungai Siak - Sungai Kampar |
| BRG_160609_01 | MUARA_MEDAK_1 | MUSI_BANYUASIN | TMA - Desa Muara Medak II | community |  | name | 7.6 | KHG Sungai Lalan - Sungai Merang |
| BRG_160609_02 | MUARA_MEDAK_2 | MUSI_BANYUASIN | TMA - Desa Muara Medak II | community |  | name | 24.6 | KHG Sungai Medak - Sungai Lalan |

Table: place-only candidates, per SIPALAGA station and kind. A concession point in the same village is not evidence that the logger was reused: concession networks are dense.

| code | kind | stations | nearest_km | companies |
|---|---|---|---|---|
| BRG10 | concession | 1 | 4.4 | 47_SPM |
| BRG2 | community | 2 | 14.7 |  |
| BRG2 | concession | 4 | 4.9 | 42_RHMS |
| BRG5 | concession | 1 | 1.4 | 327_JBP |
| BRG6 | concession | 1 | 4.1 | 321_PDIW |
| BRG8 | concession | 1 | 3.1 | 413_RAPP_TSKB |
| BRG_140405_01 | concession | 1 | 0.5 | 451_SRLBVI |
| BRG_140509_02 | concession | 8 | 5.6 | 109_THIP, 17_SPA, 25_AAI, 38_MHJ, 412_RAPP_SKPR, 54_PTR |
| BRG_140509_03 | concession | 8 | 5.6 | 109_THIP, 17_SPA, 25_AAI, 38_MHJ, 412_RAPP_SKPR, 54_PTR |
| BRG_140613_01 | concession | 3 | 6.2 | 04_BDB, 61_GSI |
| BRG_140613_02 | concession | 3 | 21.6 | 04_BDB, 61_GSI |
| BRG_140802_01 | concession | 1 | 3.1 | 413_RAPP_TSKB |
| BRG_140802_02 | concession | 1 | 17.4 | 413_RAPP_TSKB |
| BRG_140802_03 | concession | 4 | 2.0 | 25_AAI |
| BRG_150611_01 | concession | 3 | 17.5 | 24_WKS |
| BRG_150611_02 | concession | 1 | 20.6 | 24_WKS |
| BRG_150706_01 | concession | 1 | 1.0 | 293_KUL |
| BRG_150709_01 | concession | 2 | 3.6 | 24_WKS, 335_EWFSM |
| BRG_150710_01 | concession | 1 | 5.2 | 293_KUL |
| BRG_160205_02 | community | 1 | 2.0 |  |
| BRG_160214_01 | concession | 1 | 0.7 | 323_BHP |
| BRG_160224_01 | community | 1 | 17.6 |  |
| BRG_160224_01 | concession | 5 | 3.3 | 140_KLS, 437_RAJ, 462_SA |
| BRG_160224_02 | community | 1 | 6.5 |  |
| BRG_160224_02 | concession | 5 | 1.5 | 140_KLS, 437_RAJ, 462_SA |
| BRG_160224_03 | community | 1 | 12.4 |  |
| BRG_160224_03 | concession | 5 | 2.3 | 140_KLS, 437_RAJ, 462_SA |
| BRG_160611_01 | concession | 6 | 9.1 | 22_SCK, 58_BKI |
| BRG_611201_01 | concession | 1 | 1.7 | 312_NJP |
| LUMPUR1 | concession | 5 | 5.2 | 323_BHP, 33_BMH |
| MUBA2 | concession | 11 | 5.8 | 161_WLMS, 48_SHP, 58_BKI, 65_MSA |

Left out: 39 SiTMAT stations at 0,0 or without coordinates (39 community), named APTMA n KLH, AWS, BRG_n_n, DL MTI-..., TMA-n-Mertani, Z Training.

