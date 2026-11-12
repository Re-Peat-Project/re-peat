# Review layers: burned area and hotspots by land status

Written by `repeat-national-fire` (rasters, hotspots) and `repeat-national-fire-tables` (summary polygons). Open in QGIS.

| File | Content |
|---|---|
| `status.vrt` | Mosaic of `tiles/status_<i>_<j>.tif`: the 30 m equal-area grid (EPSG:6933) the tallies were made on. 7 bands, uint16, nodata 65535 outside the 2023 village boundaries. |
| `hotspots_2026.gpkg` | Layers `modis_2026`, `viirs_2026`: every 2026 hotspot of medium or high confidence (low is not used) with the classes it was counted under: province, district, khg_id, kawasan, concession, licence_types, dmpg, peat, static (likely gas flare, volcano or offshore source), on_land (inside the village boundaries). |
| `summary.gpkg` | Layers `province` and `khg`: area, peat, burned area per year and 2015-2025, MODIS 2026 hotspots (medium + high, static left out), hotspots per 100 km2, and the shares (%) of area, burned area 2015-2025 and hotspots inside concessions (`conc`), forest area (`kws`) and DMPG villages (`dmpg`). |

Bands of `status.vrt` (a paletted/unique-values renderer per band works best):

1. kawasan: 0 not mapped, 1 conservation, 2 protection forest, 3 production forest (HP, HPT), 4 convertible production (HPK), 5 other land use (APL), 6 water or undefined
2. concession: 0 none, 1 oil palm, 2 mining, 3 plantation forest (PPHTR), 4 forest concession (PBPH), 5 community forest (PPHKM) only; overlapping licences take the first type in this order
3. DMPG village: 0 no, 1 yes
4. peat (GFW composite): 0 no, 1 yes, 3 peat tile not fetched
5. KHG index (see `../khg_index.csv`), 0 outside every KHG
6. number of years burned, 2015-2026 (KLHK burned area)
7. burn years as bits: bit n set = burned in 2015 + n (2015 = 1, 2016 = 2, 2017 = 4, ... 2026 = 2048)

The burned-area maps of 2024 and 2026 are incomplete as delivered (see `tables/t_completeness.csv`).
