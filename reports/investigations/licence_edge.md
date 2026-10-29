# Fire at the licence edge, by dome position

`python -m repeat_prioritisation.investigations.licence_edge --all-folders` (repeat-prioritisation). Per KHG: peat cells of 200 m, signed distance to the edge of the 2025 licence layer, height above the nearest river from the DTM split in thirds of the KHG's peat (foot, slope, crest), VIIRS hotspots 2012-2025 (nominal and high confidence) on peat per km² of peat. Per-KHG reports and figures: `_khg/<khg>/04_prioritisation/licence_edge/`.

## Hotspot rate 0-2 km outside the licence edge over 0-2 km inside

| KHG                                            |   peat inside 0-2 km (km²) |   peat outside 0-2 km (km²) |   hotspots inside |   hotspots outside |   rate ratio |   lo |   hi | reading             |
|:-----------------------------------------------|---------------------------:|----------------------------:|------------------:|-------------------:|-------------:|-----:|-----:|:--------------------|
| KHG Sungai Kampar - Sungai Gaung               |                    1547    |                     1129.76 |              3463 |              10933 |         4.32 | 3.09 | 6.12 | outside higher      |
| KHG Pulau Bengkalis                            |                      42.52 |                      107.44 |               145 |                230 |         0.63 | 0.13 | 2.47 | no clear difference |
| KHG Pulau Padang                               |                     315.48 |                      367.48 |              1598 |               2601 |         1.4  | 0.92 | 2.31 | no clear difference |
| KHG Pulau Tebing Tinggi                        |                     318.84 |                      686.6  |              3000 |               3446 |         0.53 | 0.37 | 0.78 | inside higher       |
| KHG Sungai Air Hitam Laut - Sungai Buntu Kecil |                     180.12 |                      145.16 |              1901 |               2455 |         1.6  | 0.36 | 3.56 | no clear difference |
| KHG Sungai Mendahara - Sungai Batanghari       |                     406.32 |                      507.32 |              7448 |               6941 |         0.75 | 0.51 | 1.05 | no clear difference |
| KHG Sungai Saleh - Sungai Sugihan              |                      45.76 |                      146.84 |              1086 |               1590 |         0.46 | 0.28 | 1.08 | no clear difference |
| KHG Sungai Sugihan - Sungai Lumpur             |                     834.96 |                      437.12 |             16865 |               3450 |         0.39 | 0.28 | 0.55 | inside higher       |
| KHG Sungai Pungurbesar - Sungai Kapuas         |                     162.72 |                      193    |              3166 |               5552 |         1.48 | 0.92 | 2.11 | no clear difference |
| KHG Sungai Kapuas - Sungai Barito              |                     316.64 |                      388.36 |              1521 |               4024 |         2.16 | 1.22 | 3.66 | outside higher      |
| KHG Sungai Kahayan - Sungai Sebangau           |                     137.4  |                      499.04 |              7312 |              17290 |         0.65 | 0.52 | 0.8  | inside higher       |

lo and hi: 95% interval from resampling 5 km blocks. Ratio above 1: more fire per peat area just outside the edge. Readings: 2 KHG outside higher, 3 inside higher, 6 no clear difference.

## Rate ratio by dome position

|                                                |   crest |   foot |   slope |
|:-----------------------------------------------|--------:|-------:|--------:|
| KHG Sungai Kampar - Sungai Gaung               |    6.62 |   2.12 |    4.47 |
| KHG Pulau Bengkalis                            |    1.53 |   0.45 |    0.42 |
| KHG Pulau Padang                               |    2.01 |   3.87 |    1.64 |
| KHG Pulau Tebing Tinggi                        |    0.58 |   0.57 |    0.71 |
| KHG Sungai Air Hitam Laut - Sungai Buntu Kecil |    2.79 |   0.2  |    0.46 |
| KHG Sungai Mendahara - Sungai Batanghari       |    1.19 |   0.34 |    0.67 |
| KHG Sungai Saleh - Sungai Sugihan              |    1.26 |   0.32 |    0.31 |
| KHG Sungai Sugihan - Sungai Lumpur             |    0.71 |   0.47 |    0.46 |
| KHG Sungai Pungurbesar - Sungai Kapuas         |    1.86 |   0.83 |    1.44 |
| KHG Sungai Kapuas - Sungai Barito              |    3.41 |   1.23 |    3.55 |
| KHG Sungai Kahayan - Sungai Sebangau           |    0.64 |   0.48 |    0.66 |

KHG with no licence on peat (Mempawah-Peniti, Balangan-Batangalai, Buru-Mappi) have no contrast. Position uses the best DTM that covers the KHG (`summary.json` names it); where no river has a DTM value it is height above the lowest 5% of the peat cells.

## Limits

- Association by position. Fire also follows ignition, canals and fire fighting; the canal strata are in each KHG's `edge_contrast.csv`.
- The licence layer is the 2025 map, applied to fire since 2012.
- Hotspots are satellite detections, not area burned; burned area 2015-2025 is in `band_position.csv`.
- This is fire only. Wetness by zone is in `licence_edge_model.md` and `licence_edge_s1.md`; what the rules say is in `licence_rules.csv`.
