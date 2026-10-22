# 13 Selected KHG

Decided by the team, recorded 2026-10-22. These 12 KHG are the main focus of RE-PEAT for the integration analysis (delineation, neraca, prioritisation, pump design). Reserve (*cadangan*) KHG may be analysed too, but the 12 come first.

| # | Province | KHG (as given) | Role |
|---|---|---|---|
| 1 | Riau | Pulau Padang | main |
| 2 | Riau | Bengkalis | main |
| | Riau | Pulau Tebing Tinggi | reserve |
| 3 | Sumatera Selatan | Sugihan-Saleh | main |
| 4 | Sumatera Selatan | cawang-lalang | main |
| | Sumatera Selatan | sugihan-lumpur | reserve |
| 5 | Jambi | Mendahara-Batanghari | main |
| 6 | Jambi | Air Hitam Laut-Buntukecil | main |
| 7 | Kalimantan Barat | Peniti-Menpanwah | main |
| 8 | Kalimantan Barat | Punggurbesar-Kapuas | main |
| 9 | Kalimantan Tengah | Kahayan-Sebangau | main |
| 10 | Kalimantan Tengah | Kapuas-Barito (first written as kahayan-barito) | main |
| 11 | Kalimantan Selatan | Balangan - batangalai | main |
| 12 | Papua (Selatan) | Buru Mappi-Buru Oba | main |

The machine-readable list is [sites/selected_khg.csv](../sites/selected_khg.csv), matched to the names in `_data/batas_khg_indonesia.gpkg` (layer `nama__khg__indonesia__2017__rev_tipologi`, field `NAMA_KHG`, EPSG:4326). Other modules read the selection from that file, not from a copy.

## Open points (to confirm with the team)

- **cawang-lalang**: the boundary file has no KHG with "cawang". The nearest is *KHG Air Banyuasin - Air Lalang* (60,758 ha), which is probably meant.
- "Menpanwah" was read as Mempawah, and "Punggurbesar-Kapuas" matches the boundary file's spelling "Pungurbesar - Kapuas". Check these are the intended ones.
- Buru Mappi - Buru Obaa (402,643 ha) was chosen over the reversed pair Buru Obaa - Buru Mappi (98,805 ha).

## Data

`_data` (next to the repositories, path in `REPEAT_DATA`) holds the local data: KHG boundaries, hotspots, burnt area, RBI rivers and water bodies, existing canals and hydrological infrastructure, target villages, BRGM contours. More will be added (DTM, concessions, ...). Large files stay out of the repositories.
