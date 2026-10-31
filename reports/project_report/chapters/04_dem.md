# 4 Terrain: DEM investigation

## 4.1 Why terrain matters

Each later step of the toolkit depends on a ground surface. The boundaries of the *sub-KHG* units within a *KHG* (*Kesatuan Hidrologis Gambut*, peat hydrological unit) follow the divides of the terrain, the *neraca air* (water balance) needs the slope towards the canals, and canal-block design needs the height drop along each canal. The design quantities are small. The water-table limit for peat is 0.4 m below the surface, and the head drop between two canal blocks is about 0.3 m. The relief of a peat dome is of the same order. In Block C of the former Mega Rice Project the dome slope is 1 to 2 m per km near the rivers and under 0.5 m per km in the centre (Ritzema et al. 2014). In the airborne LiDAR of the two benchmark KHG, the height difference between two points 1 km apart is only 0.46 m (Mendahara-Batanghari) and 0.38 m (Sugihan-Lumpur), as a root mean square.

A usable terrain model therefore has to get height differences right to a few decimetres over a kilometre. Absolute height matters much less, since a constant offset does not change slopes, divides or head drops. This chapter tests which available elevation source comes closest to that requirement, and what follows for KHG that have no LiDAR.

## 4.2 Candidate elevation sources

Table: Elevation sources tested. Source: DEM benchmark report (data table) and the metadata of each product.

| Source | Type | Grid used (m) | Origin and licence |
|---|---|---|---|
| Airborne LiDAR (KLHK) | Bare-earth terrain model | 20 to 25 | KLHK Direktorat Gambut archive, 2015-2024; flight dates and vertical datum not recorded |
| DEMNAS | Radar surface model blended with stereo mass points | 8 | Badan Informasi Geospasial (BIG), national sheets |
| KLHK modelled DTM | Terrain model, method not documented | 12 | KLHK Direktorat Gambut archive |
| Copernicus GLO-30 | Radar surface model (TanDEM-X, 2011 to 2015) | 30 | ESA Copernicus DEM, open data |
| FABDEM v1.2 | GLO-30 with forests and buildings removed by machine learning | 30 | Hawker et al. 2022; non-commercial licence |
| DeltaDTM v1.1 | GLO-30 corrected with ICESat-2 and GEDI, non-terrain cells removed; defined for land below 10 m above mean sea level | 30 | Pronk et al. 2024; CC BY 4.0 |

### What DEMNAS is

DEMNAS is Indonesia's national elevation model on a 0.27 arc-second grid (about 8 m), with heights on the EGM2008 geoid. It is built from radar surface models (IFSAR and TerraSAR-X at 5 m, ALOS PALSAR at 11.25 m; Julzarika and Harintaka 2019), into which stereo-plotted mass points are merged (Susetyo et al. 2018; Susetyo 2023). The 2018 prototype used IFSAR and TerraSAR-X only, with mass points 20 to 50 m apart, denser on steep terrain and sparser on flat ground (Susetyo et al. 2018). On flat, forested peat domes the product therefore leans most on the radar surface, and so on the canopy that radar sees. From a profile comparison, Julzarika and Harintaka (2019) found DEMNAS "dominated by DSM" in a South Kalimantan sample, and in a Central Java sample in the form of neither a DSM nor a DTM.

All published accuracies are measured at control points on open, accessible ground, so they are a best case for peat forest.

Table: Published vertical accuracy of DEMNAS. Source: DEMNAS literature review of the project.

| Study | Area | Reference points | RMSE (m) | LE90 (m) |
|---|---|---|---|---|
| Susetyo et al. 2018 | Aceh to North Sumatra, prototype | 142 control points | 2.237 | 3.679 |
| BIG portal, as quoted by Susetyo 2023 | Sumatra | control points | 2.79 | not given |
| Susetyo 2023 | Bogor, 30 to 2,000 m relief | 60 GPS pre-marks | 4.968 | 8.172 |

The figure of 8.17 m often quoted for DEMNAS is the LE90 of Susetyo (2023), which is 1.645 times the RMSE; the matching RMSE is 4.97 m. No published value shows sub-metre accuracy for DEMNAS anywhere.

## 4.3 Earlier tests against satellite ground heights

The satellite tests showed that the DEMNAS error differs from site to site and stays far above the head drop between canal blocks even after correction. Before LiDAR was available, DEMNAS was tested at three sites (a 15 km window in Sebangau, Mendahara and Bengkalis) against ground heights from the ICESat-2 laser altimeter (ATL08 product, 2019 to 2025), held out in 2 km spatial blocks. These tests set the method that the benchmark later used.

- The DEMNAS offset to the ground differs by site: the median DEM minus ground was -3.4 m at Sebangau, -0.03 m at Mendahara and +2.16 m at Bengkalis. At Sebangau, open land sat about 4 m below the satellite ground heights, which none of the published papers explains.
- The fitted share of canopy height left in DEMNAS under tree cover was 0.10 (Mendahara), 0.21 (Bengkalis) and about 0.05 (Sebangau), far below the 0.8 assumed at the start. Using 0.8 would have made Mendahara worse than the raw DEM (RMSE 5.9 m against 2.6 m).
- After calibration and smoothing, RMSE at held-out ICESat-2 points was 1.24 m (Sebangau window), 2.32 m (Mendahara) and 2.78 m (Bengkalis), in the range of the published accuracy. No site met the 0.25 m target of the original methodology.
- The error of height differences over 1 to 2 km was 1.16, 1.88 and 2.55 m root mean square at the three sites, and it kept growing out to 8 km. The error behaves as a regional tilt, which more smoothing does not remove.
- GEDI ground heights were also tried as a second calibration source. Against the LiDAR they scatter by 4.06 m (Mendahara) and 5.02 m (Sugihan-Lumpur) as NMAD, against 0.67 and 0.63 m for ICESat-2, so GEDI is not used for calibration under peat forest.
- On the 2 m LiDAR of Pulau Padang (flown November 2016), smoothed DEMNAS had a height-difference error of 1.67 m over 1 km and 2.08 m over 2 km, too coarse to resolve a 0.3 m head drop between blocks. These figures include a sub-cell misregistration of the surfaces that was corrected afterwards; in a later check it accounted for 0.25 m NMAD.

Over the whole Kahayan-Sebangau KHG (22,422 usable ICESat-2 points), calibrated DEMNAS and FABDEM came out level: 2.14 and 2.19 m root mean square over 1 to 2 km. FABDEM did slightly better on open and degraded peat (0.91 against 1.02 m) and in mangrove (2.39 against 3.79 m). FABDEM and GLO-30 cover the KHG wall to wall, while the DEMNAS tile supplied for that test covered only a diagonal strip.

## 4.4 Correction method

The DEM correction turns a surface model into a ground estimate and smooths it to the scale of a peat dome. It works on the native grid of each product.

1. The DEM is mosaicked, clipped to the KHG plus 500 m, and projected to the local UTM zone.
2. Land cover (ESA WorldCover 2021, 10 m) and canopy height (Meta/WRI global canopy height) are taken for the same area. Canopy below 2 m counts as zero and canopy above 60 m is clipped.
3. ICESat-2 ATL08 ground segments of 100 m (2019 to 2025, at least 10 ground photons) are converted from ellipsoidal heights to EGM2008. Points in water or built-up land, within 50 m of a land-cover change, or more than 30 m from the DEM are dropped.
4. The points are split into calibration and validation sets by 2 km blocks, with 30% held out, because neighbouring points along one track are nearly identical.
5. For each land-cover class with at least 30 points under canopy of 2 m or more, a robust line is fitted: DEM minus ground = offset + k × canopy height. Both the offset and the canopy factor k (bounded 0 to 1) are fitted per class. Classes with fewer points keep the prior k and a single offset fitted on all low-canopy points.
6. The corrected surface is DEM minus k × canopy height minus offset. Water and built-up cells are masked, and cells more than 2.5 m from a 400 m local median are removed as spikes.
7. The surface is smoothed with a 300 m median and then a 150 m gaussian, and gaps are filled. Errors are reported at the held-out points.

Two parameter sets are used, the same as in the benchmark.

- DeltaDTM is processed at 30 m. Its prior canopy factor is 0 for every class, because it is already a terrain model. The fit still runs, and the fitted k came out between 0 and 0.007 at Mendahara-Batanghari and Kampar-Gaung, so in practice only the per-class offsets act.
- DEMNAS is processed at 8 m with prior canopy factors of 0.8 for tree cover and mangrove, 0.5 for shrubland, 0.4 for herbaceous wetland and 0.2 for grassland and cropland. The fit replaces them where a class has enough points. At Mendahara-Batanghari it fitted k = 0.087 for tree cover and 0.30 for mangrove. Shrubland, grassland, cropland and wetland had too few points under canopy and kept their priors, which the earlier tests do not support.

## 4.5 LiDAR benchmark design

The KLHK LiDAR made a direct test possible. Five sources were benchmarked at the two KHG that it covers fully, each scored as delivered and again after the correction above. The LiDAR served only as the reference and never entered a fit; the calibration used ICESat-2 alone.

Table: Benchmark sites. Source: DEM benchmark report.

| KHG | Area (km²) | LiDAR reference | LiDAR cells inside the KHG | Real 1 km height difference (m RMS) | ICESat-2 ATL08 points |
|---|---|---|---|---|---|
| Sungai Mendahara - Sungai Batanghari | 2,012 | KLHK, 25 m (Jambi) | 3,219,296 | 0.46 | 68,979 |
| Sungai Sugihan - Sungai Lumpur | 6,347 | KLHK, 25 m (OKI) | 10,151,210 | 0.38 | 266,462 |

{{diagram: dem_benchmark_workflow_report_b | DEM benchmark workflow, part 1: the terrain benchmark against LiDAR, steps 0 to 4 | diagrams/dem_benchmark_workflow_report_b.drawio}}

{{diagram: dem_benchmark_workflow_report_c | DEM benchmark workflow, part 2: test on the sub-KHG delineation and results | diagrams/dem_benchmark_workflow_report_c.drawio}}

Each candidate was compared with the LiDAR at every LiDAR cell inside the KHG, without resampling the candidate. The main metric is the error of height differences: for all pairs of cells 0.5, 1 and 2 km apart, the difference in height in the candidate is compared with the difference in the LiDAR, and the root mean square of that error is reported. A constant offset does not affect it. The NMAD of candidate minus LiDAR is reported alongside.

The pass criterion was fixed before any result was computed. Tier A requires an error of height differences over 1 km of at most 0.30 m, one canal-block head drop. Tier B requires at most half the real 1 km height difference of that site's LiDAR.

All processed candidates sit +0.6 to +1.0 m above the LiDAR. The flight dates and vertical datum of the LiDAR were never recorded, so this offset cannot be assigned to either side. It does not affect the metrics.

### Is a 25 m reference fine enough?

A 25 m reference keeps the dome-scale relief that the water balance needs and loses detail at the scale of canals. This was tested by averaging the 2 m LiDAR of Pulau Padang into 24 m blocks. Inside a block the heights vary by a median standard deviation of 0.05 m, and 5% of the blocks hold more than 1 m of relief (canals, ditches and embankments). Between blocks 1 km apart, the real height difference is 1.35 m root mean square.

## 4.6 Benchmark results

Processed DeltaDTM came closest to the LiDAR at both sites, with an error of 0.64 m (Mendahara) and 0.47 m (Sugihan-Lumpur) over 1 km. The KLHK modelled DTM was second, at 0.67 and 0.49 m. DEMNAS, FABDEM and GLO-30 stayed between 1.66 and 2.49 m after processing. No source passed Tier A or Tier B at either site: the best errors are still larger than the real 1 km relief of the LiDAR (0.46 and 0.38 m).

![Error of height differences between LiDAR cells 0.5, 1 and 2 km apart, after processing (lower is better); grey is the real height difference in the LiDAR, dashed is Tier A. Source: DEM benchmark, Mendahara-Batanghari and Sugihan-Lumpur.](re-peat/reports/dem_benchmark/figures/height_difference_error.png)

Table: Error of each source against the LiDAR, as delivered and after processing. Source: DEM benchmark report (metrics against 25 m KLHK LiDAR).

| Site | Source | State | NMAD (m) | Δh error 0.5 km (m) | Δh error 1 km (m) | Δh error 2 km (m) |
|---|---|---|---|---|---|---|
| Mendahara | DeltaDTM v1.1 | as delivered | 0.68 | 0.54 | 0.74 | 0.94 |
| Mendahara | DeltaDTM v1.1 | processed | 0.64 | 0.40 | 0.64 | 0.86 |
| Mendahara | KLHK modelled DTM | as delivered | 1.10 | 0.61 | 0.80 | 1.05 |
| Mendahara | KLHK modelled DTM | processed | 1.07 | 0.43 | 0.67 | 0.95 |
| Mendahara | DEMNAS | as delivered | 2.12 | 2.70 | 2.94 | 3.25 |
| Mendahara | DEMNAS | processed | 1.60 | 1.14 | 1.66 | 2.16 |
| Mendahara | FABDEM v1.2 | as delivered | 1.58 | 2.31 | 2.84 | 3.40 |
| Mendahara | FABDEM v1.2 | processed | 1.43 | 1.42 | 2.14 | 2.83 |
| Mendahara | Copernicus GLO-30 | as delivered | 3.10 | 3.54 | 4.08 | 4.69 |
| Mendahara | Copernicus GLO-30 | processed | 2.09 | 1.69 | 2.49 | 3.19 |
| Sugihan-Lumpur | DeltaDTM v1.1 | as delivered | 0.49 | 0.45 | 0.56 | 0.66 |
| Sugihan-Lumpur | DeltaDTM v1.1 | processed | 0.46 | 0.33 | 0.47 | 0.59 |
| Sugihan-Lumpur | KLHK modelled DTM | as delivered | 0.71 | 0.35 | 0.49 | 0.66 |
| Sugihan-Lumpur | KLHK modelled DTM | processed | 0.70 | 0.33 | 0.49 | 0.67 |
| Sugihan-Lumpur | DEMNAS | as delivered | 3.21 | 2.89 | 3.46 | 4.15 |
| Sugihan-Lumpur | DEMNAS | processed | 2.28 | 1.45 | 2.19 | 2.98 |
| Sugihan-Lumpur | FABDEM v1.2 | as delivered | 2.44 | 2.10 | 2.65 | 3.29 |
| Sugihan-Lumpur | FABDEM v1.2 | processed | 2.10 | 1.32 | 2.00 | 2.69 |
| Sugihan-Lumpur | Copernicus GLO-30 | as delivered | 3.21 | 2.92 | 3.47 | 4.12 |
| Sugihan-Lumpur | Copernicus GLO-30 | processed | 2.20 | 1.47 | 2.17 | 2.87 |

The correction helps the surface models most, because it removes part of the canopy. DEMNAS improved from 2.94 to 1.66 m at Mendahara and from 3.46 to 2.19 m at Sugihan-Lumpur. DeltaDTM and the KLHK modelled DTM are already terrain models and gained little. For every source the error grows with distance, so what remains is a regional tilt or bow in the surface.

Heavier smoothing does not change this conclusion. With a 1,200 m median and 600 m gaussian, DeltaDTM scored 0.450 m at Mendahara and 0.319 m at Sugihan-Lumpur over 1 km. A perfectly flat surface scores the LiDAR's own relief there, 0.457 and 0.379 m, so at that smoothing DeltaDTM is barely better than assuming the land is flat.

Table: NMAD of processed source minus LiDAR by land-cover class (classes with at least 2% of the LiDAR cells). Source: DEM benchmark report; land cover from ESA WorldCover.

| Site | Land cover | Share of LiDAR cells | DeltaDTM (m) | KLHK modelled (m) | DEMNAS (m) |
|---|---|---|---|---|---|
| Mendahara | tree cover | 82% | 0.62 | 1.15 | 1.70 |
| Mendahara | shrubland | 6% | 0.66 | 0.46 | 0.91 |
| Mendahara | grassland | 8% | 0.69 | 0.90 | 1.18 |
| Mendahara | cropland | 2% | 0.71 | 1.01 | 1.68 |
| Sugihan-Lumpur | tree cover | 49% | 0.45 | 0.72 | 2.65 |
| Sugihan-Lumpur | shrubland | 8% | 0.45 | 0.52 | 1.36 |
| Sugihan-Lumpur | grassland | 18% | 0.48 | 0.68 | 1.65 |
| Sugihan-Lumpur | cropland | 19% | 0.40 | 0.71 | 3.05 |
| Sugihan-Lumpur | mangroves | 4% | 0.40 | 0.41 | 2.85 |

DeltaDTM holds an NMAD of 0.40 to 0.71 m in every class. DEMNAS is worst under tree cover and cropland at Sugihan-Lumpur (2.65 and 3.05 m).

![Mendahara-Batanghari: processed source minus LiDAR, median removed; blue is too low, red too high. Source: DEM benchmark.](re-peat/reports/dem_benchmark/figures/error_maps_mendahara.png)

![Sugihan-Lumpur: processed source minus LiDAR, median removed; blue is too low, red too high. Source: DEM benchmark.](re-peat/reports/dem_benchmark/figures/error_maps_sugihan_lumpur.png)

## 4.7 Effect on sub-KHG units

The choice of terrain changes the sub-KHG units, and no open source reproduces the LiDAR units well. At Sugihan-Lumpur the sub-KHG delineation (chapter 5) was repeated with only the terrain changed, and each set of units was compared with the units delineated from the LiDAR. For each LiDAR unit, the best-matching unit of the candidate is found and their intersection over union (IoU) computed. This test used primary canals and rivers as unit outlets, the setting in use at the time.

Table: Sub-KHG units at Sugihan-Lumpur by terrain source, primary canals and rivers as outlets. Source: DEM benchmark report, test on the sub-KHG delineation.

| Terrain | Sub-KHG units | Mean best-match IoU with LiDAR units | Median IoU | KHG area in matched overlap |
|---|---|---|---|---|
| LiDAR (reference) | 30 | 1.00 | 1.00 | 100% |
| KLHK modelled DTM, as first used in the delineation | 28 | 0.40 | 0.36 | 66% |
| KLHK modelled DTM, processed | 29 | 0.45 | 0.41 | 66% |
| DeltaDTM, processed | 30 | 0.48 | 0.47 | 70% |
| DEMNAS, processed | 30 | 0.38 | 0.34 | 58% |
| Flat surface (control) | 30 | 0.40 | 0.37 | 58% |

![Sub-KHG units at Sugihan-Lumpur from the LiDAR, processed DeltaDTM and the KLHK modelled DTM, primary canals as outlets; grey lines are the LiDAR units. Source: DEM benchmark, test on the sub-KHG delineation.](re-peat/reports/dem_benchmark/figures/subkhg_units_sugihan_lumpur.png)

Processed DeltaDTM matched the LiDAR units best, but a mean IoU of 0.48 is a weak match, and a flat surface (0.40) did better than processed DEMNAS (0.38). The mapped rivers and canals are unit boundaries for every terrain, so part of the boundary network is the same in every case; the terrain decides how the pieces between those channels form and merge. With secondary canals added as outlets, as now adopted, all terrain sources agree more closely with the LiDAR (chapter 5).

The same test ran the groundwater model on each terrain. That model is in development. In its set-up at the time, 19,433 of its 25,391 cells (77%) were canal or edge cells with fixed heads, and it showed no skill at the water-table stations even on the LiDAR, so it could not tell the terrains apart.

## 4.8 Limits of the evidence

- There are two benchmark sites, both in the eastern Sumatra lowland, and one kind of reference: 25 m LiDAR of unknown date and datum.
- ICESat-2 (2019 to 2025) is newer than the LiDAR and the global models (GLO-30 is from TanDEM-X data of 2011 to 2015), so peat subsidence since then is part of the errors.
- Nothing records how the KLHK modelled DTM was made. If it was calibrated on the same LiDAR, its scores at these two sites are better than it would get elsewhere. This has not been tested.
- Part of the ICESat-2 data could not be read, so the calibration used slightly fewer points than exist.

## 4.9 Decision: one chain per DEM

No source passed the criterion, and the best one still has errors larger than the relief it must describe. The project therefore did not pick a single terrain. The whole analysis chain (sub-KHG delineation, neraca air, prioritisation and RE-PEAT Interventions) runs once per DEM:

- LiDAR as delivered, where it covers at least 90% of the KHG;
- DeltaDTM after the correction;
- DEMNAS after the correction.

The differences between the three results show how far a result depends on terrain. The Pulau Padang LiDAR is a 2 m DTM and is left out of the chain.

{{table: dem_coverage | DEM coverage of the selected KHG: share of the KHG with valid data per product. Source: DEM coverage assessment of the project | re-peat/sites/khg_dem_inputs.csv, columns khg, product, res_m, cover_pct, note; one row per KHG and product, keeping for LiDAR only the row with the highest cover_pct per KHG (Sugihan-Lumpur has two LiDAR rows, 1.6% and 100%). Caption note: cover_pct is measured inside the clipped raster window, so for Saleh-Sugihan it reads 98.3% while the LiDAR covers about 1,174 of 1,897 km² (62%) of the KHG polygon; compute coverage against the KHG polygon area from 00_inputs/khg.gpkg if the build allows}}

Of the 14 KHG assessed for terrain coverage, the available LiDAR covers Kampar-Gaung, Air Hitam Laut-Buntu Kecil, Mendahara-Batanghari and Sugihan-Lumpur, part of Saleh-Sugihan, and Pulau Padang, which the chain leaves out. DeltaDTM covers 97.9 to 99.9% and DEMNAS 99.4 to 100% of each of them.

For a KHG without LiDAR, the chain gives two terrain variants and no reference. The benchmark points to processed DeltaDTM as the closer one, with a measured error of 0.47 to 0.64 m over 1 km at the two test sites. That error should be carried into the uncertainty of the neraca air, and unit boundaries should rest on the mapped rivers and canals. Heights that need decimetre accuracy, such as canal water levels, block crests and logger heads, have to come from GNSS or levelling. DeltaDTM is defined only for land below 10 m above mean sea level, so higher ground in a KHG falls outside its scope; its data licence is CC BY 4.0. FABDEM was not taken into the chain. Its licence is non-commercial (CC BY-NC-SA 4.0 at the University of Bristol, Non-Commercial Government Licence v2.0 on the mirror used), and it is not clear whether a KLH deliverable counts as non-commercial use.

The benchmark proposes three next steps: a trend correction from ICESat-2 (regression-kriging, aimed at the long-range part of the error), a test of the KLHK modelled DTM away from the LiDAR footprints, and a review of the fixed-head canal cells in the groundwater model before it is used to judge terrain.
