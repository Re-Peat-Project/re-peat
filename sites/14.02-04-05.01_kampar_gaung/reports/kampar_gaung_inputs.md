# Input check: configs/kampar_gaung/subkhg.yaml

KHG `data_local/kampar_gaung/khg.gpkg`: 7,111 km2, bounds 102.281, -0.258, 103.814, 0.545

### Peat depth raster
`C:/Users/danyl/Documents/Projects/2026/REPEAT-LH/_data/Peat depth and DTM/PeatDepth_Sumatera/RIAU/Peat_depth_model_KHG_Sungai_Kampar_Sungai_Guang.img`

- HFA, 15757 x 8909 px, resolution 9.00212e-05 9.00212e-05, CRS EPSG:4326, nodata -3.4028234663852886e+38
- valid pixels in a 1/6 sample: 1,480,250 (38% of the sample)
- percentiles 0 / 1 / 5 / 25 / 50 / 75 / 95 / 100: 34.81 / 50 / 50 / 50 / 192.7 / 651.9 / 838 / 1393
- **37% of the valid pixels equal 50.0**: the raster has a floor value there (probably a class such as "up to this value"). Anything computed from it is cut off at the low end.
- with `params.peat_depth_scale` 0.01: median 1.93 m, 5th to 95th percentile 0.50 to 8.38 m

### DTM
`C:/Users/danyl/Documents/Projects/2026/REPEAT-LH/_data/Peat depth and DTM/DTM_Sumatera-002/RIAU/DTM_Sungai_Kampar_Sungai_Gaung.tif`

- GTiff, 13794 x 7232 px, resolution 0.000111111 0.000111111, CRS EPSG:4326, nodata -3.3999999521443642e+38
- valid pixels in a 1/5 sample: 1,869,893 (47% of the sample)
- percentiles 0 / 1 / 5 / 25 / 50 / 75 / 95 / 100: -0.4956 / 0.7631 / 1.406 / 2.606 / 4.225 / 6.727 / 9.7 / 36.12

### Canals
`data_local/kampar_gaung/canals.gpkg`

- 11,733 features, CRS EPSG:4326, geometry MultiLineString

By `KET_KANAL`: Kanal Tersier: 10756, Kanal Sekunder: 859, Kanal Primer: 118

### Rivers
`data_local/kampar_gaung/rivers.gpkg`

- 16 features, CRS EPSG:4326, geometry MultiLineString

### Existing canal blocks
`data_local/kampar_gaung/blocks.gpkg`

- 2,884 features, CRS EPSG:4326, geometry Point

By `Jenis`: Sekat Kanal: 2884

### Water-table stations (SiTMAT)
`C:/Users/danyl/Documents/Github/apps/sitmat-extract/sitmat_out/processed`

- 86 stations inside the KHG with at least 50% coverage in 2026-04-01 to 2026-10-15; readings per station: median 136 days

