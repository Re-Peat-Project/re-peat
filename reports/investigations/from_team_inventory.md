# Team deliveries in `_khg/from_team`: inventory

Source: `_khg/from_team/` (5.3 GB, 17 delivery folders, 12 KHG). Read on 2026-11-01 by `re-peat/tools/inventory_from_team.py`, metadata only, nothing extracted or moved.
Full tables: `from_team_inventory.csv` (one row per file, layer or raster) and `from_team_entries.csv` (the 88 entries inside the 6 zip archives).
Facts in the "Notes" columns come from the delivery's own `BACA_DULU.md`, `README.txt`, `run_report.md` and `run_config.yaml`. Items marked (inferred) are not stated by the team.

## 1. What is there

| Delivery folder | KHG (code) | DEM in the folder | Grid | Pump run | Sub-KHG units | Kind of package |
|---|---|---|---|---|---|---|
| KHG Air Hitam Laut - Buntu Kecil | Air Hitam Laut - Buntu Kecil (15-16.01) | LiDAR | 25 m | results only (`pompa.gpkg`) | 30 scored | web package, layers split by theme |
| KHG Mendahara - Batanghari | Mendahara - Batanghari (15.05-07-10.01) | LiDAR | 25 m | results only | 30 scored | web package |
| KHG Punggurbesar-Kapuas LiDAR | Punggur Besar - Kapuas (61.12-71.01) | `dtm_brgm_10m.tif` (BRGM contour DTM, named LiDAR) | 10 m | results only | 29 scored | web package |
| KHG Punggurbesar-Kapuas DEMNAS | same | DEMNAS | 30 m | results only | 30 scored | web package |
| KHG Sugihan Lumpur WorldDEM 12m | Sugihan - Lumpur (16.02.01) | WorldDEM | 12.3 m | `pump_run.gpkg`, 34 layers | none | run + DMPG and concession |
| KHG Sugihan Lumpur DEMNAS | same | none (run only) | n/a | `pump_run_demnas_sugihan lumpur.gpkg`, 32 layers | none | run only |
| KHG Sugihan Saleh | Saleh - Sugihan (16.02-07.01) | LiDAR 20 m (62% of KHG) and WorldDEM 12 m (inside `pump_work`, and in the zip) | 20 m / 12.3 m | run A (LiDAR, S02+S03), run B (WorldDEM, S01-S03), plus a third `pump_run.gpkg` | 3 | two full run folders (config, report, state, logs, rasters) + web zip + DMPG zips |
| P Padang LiDAR | Pulau Padang (14.10.01) | LiDAR 2 m, 25 m in web zip | 2 / 25 m | `pump.gpkg`, 18 layers (stages 1-7) | 11 | run + base layers + web zip |
| P Padang DEMNAS | same | DEMNAS corrected (repeat-dem DTM_Smooth), 25 m in the LiDAR zip | 25 m | `pump.gpkg`, 18 layers | 11 | run only |
| KHG BENGKALIS | Pulau Bengkalis (14.03.02) | WorldDEM (`DTM_BENGKALIS_WD`) | 12.3 m | `pump_run.gpkg`, 35 layers | 28 scored | shapefiles + run |
| KHG Balangan Batangalai | Balangan - Batangalai (63.07-08-11.01) | WorldDEM | 10 m | `pump_run.gpkg`, 34 layers | 26 scored | shapefiles + run |
| KHG Menpawah Peniti | Mempawah - Peniti (61.02-08.01) | WorldDEM | 12.3 m | `pump_run.gpkg`, 34 layers | 28 (in run) | shapefiles + run + moisture |
| KHG Menpawah Peniti DEMNAS | same | DEMNAS smoothed | 8 m | `pump_run_demnas.gpkg`, 32 layers | 28 (in run) | DEM + run |
| KHG KAPUAS BARITO | Kapuas - Barito (62.03-04.01) | DTM from BRGM contours | 8 m | `kapuasbarito.gpkg`, 26 layers | 30 scored | shapefiles + run |
| KHG Kahayan-Sebangau | Kahayan - Sebangau (62.11-14.02) | `DTM_KHSB_49S` (README says "DEMNAS atau LiDAR") | 12.3 m | pump stations and routes as shapefiles/gpkg | 5 scored | shapefiles + README |
| HASIL KAHAYAN SEBANGAU DEMNAS | same | DEMNAS smoothing | 8 m | `pump_run3.gpkg`, 19 layers (no pump layers) | 6 | DEM + run |
| Buru Mappi - buru obaa | Buru Mappi - Buru Obaa (91.18-17.01) | DTM from BRGM contours, 0.4 m interval | 8 m | `pump.gpkg`, 18 layers, one sub-KHG (S29) | 30 (no scores) | DEM + run + web zip |

Not delivered: Kampar - Gaung (14.02-04-05.01) and Pulau Tebing Tinggi (14.10.03). Kampar-Gaung is part of the project's own chain runs (see `_khg/pipeline_status.csv`).

## 2. DEM variants per KHG

| KHG | LiDAR | WorldDEM 12 m | DEMNAS | BRGM contour DTM |
|---|---|---|---|---|
| Air Hitam Laut - Buntu Kecil | yes | | | |
| Mendahara - Batanghari | yes | | | |
| Pulau Padang | yes (2 m) | | yes (corrected) | |
| Saleh - Sugihan | yes (62%) | yes | | |
| Sugihan - Lumpur | | yes | yes | |
| Mempawah - Peniti | | yes | yes | |
| Kahayan - Sebangau | | (12.3 m grid, source to confirm) | yes | |
| Punggur Besar - Kapuas | | | yes (30 m) | yes (10 m) |
| Kapuas - Barito | | | | yes (8 m) |
| Buru Mappi - Buru Obaa | | | (run only per the team, not in folder) | yes (8 m) |
| Bengkalis | | yes | | |
| Balangan - Batangalai | | yes | | |

Six KHG have one DEM and six have two. Paired runs on the same KHG exist for Pulau Padang, Sugihan-Lumpur, Mempawah-Peniti, Kahayan-Sebangau, Punggur-Kapuas and Saleh-Sugihan (LiDAR vs WorldDEM), so they can be used to compare DEM effect on the block and pump result.

## 3. Pump outputs compared

Feature counts of the main result layers in each pump GeoPackage. `-` means the layer is not in the file.

| Run | Sekat proposed | Sekat optimised | Existing sekat assessed | Pump stations | Targets | Gates required | Unreachable targets | Interventions / budget |
|---|---|---|---|---|---|---|---|---|
| Bengkalis (WorldDEM) | 44 | 44 | 0 | 16 | 44 | 21 | 22 | 28 / 60 |
| Balangan-Batangalai (WorldDEM) | 23 | 23 | 0 | 28 | 133 | 3 | 2 | 26 / 76 |
| Mempawah-Peniti (WorldDEM) | 269 | 269 | 0 | 153 | 307 | 48 | 38 | 28 / 58 |
| Mempawah-Peniti (DEMNAS) | 611 | 611 | 0 | 115 | 251 | 102 | 20 | - |
| Sugihan-Lumpur (WorldDEM) | 54 | 54 | 370 | 2 | 93 | 4 | 83 | 28 / 12 |
| Sugihan-Lumpur (DEMNAS) | 434 | 434 | 0 | 109 | 364 | 86 | 56 | - |
| Kapuas-Barito (contour DTM) | (see shapefile, 307) | - | 0 | - | - | - | - | - |
| Kahayan-Sebangau (DEMNAS, `pump_run3`) | 326 | - | 0 | - | - | - | - | - |
| Saleh-Sugihan A (LiDAR 20 m, S02+S03) | 2337 | - | 0 | 13 | 159 | 589 | 14 | - |
| Saleh-Sugihan B (WorldDEM, S01-S03) | 906 | - | 25 | 100 | 273 | 98 | 21 | - |
| Saleh-Sugihan `pump_run.gpkg` (third run) | 373 | - | 25 | 26 | 201 | 50 | 122 | - |
| Pulau Padang (LiDAR, stages 1-7) | 678 | - | 156 | - | - | - | - | - |
| Pulau Padang (DEMNAS, stages 1-7) | 695 | - | 156 | - | - | - | - | - |
| Buru Mappi (S29 only) | 0 | - | 0 | - | - | - | - | - |

Read this with care:
- The runs are not on the same footing. Files with `sekat_optimised`, `interventions` and `budget` were made with a later pipeline version than those that stop at `sekat_proposed` (Saleh runs, Pulau Padang, Kahayan-Sebangau, Buru Mappi). Compare counts only inside one group.
- Sekat counts differ 5 to 20 times between DEMNAS and WorldDEM or LiDAR runs on the same KHG (Sugihan-Lumpur 434 vs 54, Mempawah-Peniti 611 vs 269, Saleh 2337 vs 906). Pulau Padang LiDAR vs DEMNAS agree in count (678 vs 695), but the team's own check puts the location agreement at 64%, below the 76% expected by chance.
- Buru Mappi: 0 proposed blocks is stated as a data fact (maximum head difference along the S29 canals is 0.20 m against a 0.4 m rule); no pumps were run.
- Saleh-Sugihan has three pump GeoPackages and the third (`pump_run.gpkg`) has no config or report; which run it belongs to is not recorded.

## 4. Assumptions the team recorded

- Canal dimensions are assumed in Saleh-Sugihan and Pulau Padang (primary 8 x 2.5 m, secondary 4 x 1.5 m, tertiary 2 x 1 m, Sugihan sizes). Dry-season river level is set to 0 m MSL. Pump power (32.2 MW at Saleh-Sugihan) is dominated by friction in the S01 canal because of these dimensions. Pump results are labelled simulation.
- DEM vertical datum is unknown in several deliveries (taken as MSL). Pulau Padang LiDAR is on a local MSL checked with 13 benchmarks (bias -0.28 m, SD 0.20 m); DEMNAS is on EGM2008 and sits on average 1.8 m above LiDAR (SD 2.2 m).
- The Saleh-Sugihan run report warns that the 0.4 m sekat rule is below twice the DTM vertical error (1.0 m): head-based block placement is dominated by DTM noise.
- Water deficit is a KHG value copied to every sub-KHG (Buru Mappi 225 mm, Saleh-Sugihan 331 mm, Pulau Padang 0 mm), from ERA5 P - E with no water-table change, because no SiTMAT station lies inside the KHG. The project dropped ERA5 for the neraca (see AGENTS.md); these numbers are not comparable with the project's own deficit.
- Moisture raster (Sentinel-2 wetness, dry season 2026) uses the open Sentinel-2 index without Sentinel-1.
- Peat depth sources differ: BRGM model at 10 m (Air Hitam Laut, Mendahara, Punggur), UGM soil team model at 125 m (Pulau Padang), KLH 2020 survey Thiessen at 20 m (Saleh-Sugihan), class midpoints of `PEAT_THICK` at 100 m (Saleh, Pulau Padang, Buru Mappi), a 100 m raster for Kahayan-Sebangau. Buru Mappi has no peat-depth model, only classes (96% of S29 is 0 to 0.5 m).

## 5. Common layers

Naming differs by delivery. Web-package deliveries (Air Hitam Laut, Mendahara, Punggur, and inside the three zips) share one scheme: `batas_khg`, `batas_subkhg` (layer `subkhg_prioritas`), `kanal` (`kanal_existing`, `kanal_terpilih`), `sekat` (`sekat_existing`, `sekat_terpilih`), `pompa`, `sungai_danau`, `burnt_area`, `hotspot` (`hotspot_sedang_tinggi`), `konsesi`, `dmpg`, `tma` (`tma_stasiun`, `tma_harian`) and three priority rasters (`prioritas_dampak`, `_kelayakan`, `_urgensi`). They are EPSG:4326 for vectors and UTM for rasters, nodata -9999.
Shapefile deliveries (Bengkalis, Kapuas-Barito, Kahayan-Sebangau, Mempawah-Peniti, Balangan) use Indonesian upper-case names in UTM and carry the same themes with different names. All pump GeoPackages share the repeat-pump layer set (`inputs_clipped_*`, `qa_topology_*`, `canal_*`, `sekat_*`, `network_*`, `pump_*`, `gates_required`, `budget`).

Per-sub-KHG scoring (`unit_prioritas`) has the same 70-odd columns in Balangan and Kahayan-Sebangau: indicators `u_*`, `i_*`, `f_*`, scores `skor_urgensi`, `skor_dampak`, `skor_kelayakan`, `skor_need`, `skor_ranksum`, `kelas`, `peringkat`. Kahayan-Sebangau has extra columns (`n_u_ipg_gap`, `n_i_protected`, `n_i_exposure`) that Balangan lacks. Buru Mappi sub-KHG have no scores yet.

TMA: daily `tma_harian.csv` files exist for Air Hitam Laut (10 stations, 1,558 records), Mendahara (27, 2,885), Punggur (5, 676, same counts in the LiDAR and DEMNAS copies), Kahayan-Sebangau (1 station, 130) and Pulau Padang (3 stations, 355 records, 17 Jun to 13 Oct 2026). Saleh-Sugihan has 5 stations within 10 km and none inside the KHG; Buru Mappi has none (nearest 477 km).

## 6. Gaps and loose ends

- Lock files and raw `.sbn`, `.sbx` sidecars sit in the Balangan folder; four `.pkl` network caches and 24 stage logs sit in the Saleh runs. The Balangan KHG boundary shapefile is EPSG:3395, the only one not in WGS 84 or UTM.
- Several deliveries copy the same layer: Punggur LiDAR and DEMNAS carry identical `burnt_area` (10,591), `hotspot` (12,437), `konsesi`, `dmpg`. Not compared byte by byte, so none is removed.
- Delivery names do not always match content: "Punggurbesar-Kapuas LiDAR" holds a BRGM-contour DTM, not LiDAR; "HASIL KAHAYAN SEBANGAU DEMNAS" and "KHG Kahayan-Sebangau" are two different runs of the same KHG with 6 vs 5 sub-KHG units.
- Missing against the Air Hitam Laut template (from the team's own notes): Buru Mappi priority scores and peat-depth model; Saleh-Sugihan hotspots before 2019 or after 2021; Pulau Padang hotspots 2025; river water level, canal dimensions and sekat attributes (type, material, year) at Saleh-Sugihan and Pulau Padang.
- Hotspots in the web packages combine VIIRS S-NPP with the 2026 KLH set (Jan to Sep). Year coverage differs between KHG (Saleh 2019-2021, Buru Mappi and Pulau Padang 2014-2024).
- The delivery uses the project's pump pipeline and the Part-A ranking, but on local team copies (`F:\gambut\...`, `D:\GAMBUT\BASELINE BLUEBOOK`), so rerunning needs the config paths pointed at `_data` and `_khg`.

## 7. Next steps (not yet done)

1. Decide what goes into `_khg/<code>_<name>/` (derived files only; the team folders are the source of truth for these runs) and catalogue it in `re-peat/sites/data_catalog.csv` with source, date and DEM.
2. Check the table of pump outputs for pipeline version before it enters the report; the DEM comparison is only valid inside one version.
3. Update the project report and slides with: coverage (12 KHG, 6 with paired DEM runs), the DEM comparison, and the recorded assumptions.
