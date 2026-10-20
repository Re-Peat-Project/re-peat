# Input check: configs/sugihan_lumpur/subkhg.yaml

KHG `data_local/sugihan_lumpur/khg.gpkg`: 6,347 km2, bounds 105.173, -3.422, 106.097, -2.391

### Peat depth raster
`C:/Users/danyl/Documents/Projects/2026/REPEAT-LH/_data/Peat depth and DTM/PeatDepth_Sumatera/03_Sumatera Selatan/Peat_depth_model_KHG_Sungai_Sugihan_Sungai_Lumpur.img`

- HFA, 8908 x 9884 px, resolution 9.01333e-05 9.01333e-05, CRS EPSG:4326, nodata -3.4028234663852886e+38
- valid pixels in a 1/3 sample: 5,275,824 (54% of the sample)
- percentiles 0 / 1 / 5 / 25 / 50 / 75 / 95 / 100: 50 / 50 / 50 / 72.14 / 126.2 / 233.9 / 495.2 / 625.5
- **20% of the valid pixels equal 50.0**: the raster has a floor value there (probably a class such as "up to this value"). Anything computed from it is cut off at the low end.
- with `params.peat_depth_scale` 0.01: median 1.26 m, 5th to 95th percentile 0.50 to 4.95 m

### DTM
`C:/Users/danyl/Documents/Projects/2026/REPEAT-LH/_data/Peat depth and DTM/DTM_Sumatera-002/03_Sumatera Selatan/DTM_Sungai_Sugihan_Sungai_Lumpur.tif`

- GTiff, 8313 x 9278 px, resolution 0.000111111 0.000111111, CRS EPSG:4326, nodata -3.3999999521443642e+38
- valid pixels in a 1/3 sample: 4,648,829 (54% of the sample)
- percentiles 0 / 1 / 5 / 25 / 50 / 75 / 95 / 100: 0 / 1 / 1.6 / 2.401 / 2.823 / 4.516 / 8.742 / 21.36

### Canals
`data_local/sugihan_lumpur/canals.gpkg`

- 14,928 features, CRS EPSG:4326, geometry MultiLineString

By `KET_KANAL`: Kanal Tersier: 10541, Kanal Sekunder: 3764, Kanal Primer: 623

### Rivers
`data_local/sugihan_lumpur/rivers.gpkg`

- 2 features, CRS EPSG:4326, geometry MultiLineString

### Existing canal blocks
`data_local/sugihan_lumpur/blocks.gpkg`

- 2,861 features, CRS EPSG:4326, geometry Point

By `Jenis`: Sekat Kanal: 2861

### Water-table stations (SiTMAT)
`C:/Users/danyl/Documents/Github/apps/sitmat-extract/sitmat_out/processed`

- 51 stations inside the KHG with at least 50% coverage in 2026-04-01 to 2026-10-15; readings per station: median 197 days

