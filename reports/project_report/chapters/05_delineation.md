# 5 Sub-KHG delineation

## 5.1 What a sub-KHG is and why it is needed

A *KHG* (*Kesatuan Hidrologis Gambut*, peat hydrological unit) is too large to plan rewetting as one block. The KHG treated in this chapter range from 1,897 km² (Saleh-Sugihan) to 7,111 km² (Kampar-Gaung). The national KHG map (SK.129/MENLHK/2017) defines no level below the KHG, and no regulation found sets one based on drainage.

The toolkit therefore splits each KHG into *sub-KHG* units. A sub-KHG is the land that drains to one stretch of outlet channel, bounded by water divides and by the outlet channels themselves. It is the spatial unit of the *neraca air* (water balance), of the sub-KHG prioritisation, and of the canal-block planning in RE-PEAT Interventions.

The approach follows the UGM team's 2021 study of the Kahayan-Sebangau KHG (Laporan Akhir KHG Kahayan-Sebangau 2021). That study fixed the sub-KHG boundaries first, to set the analysis unit of the water balance, because the KHG was too large for detailed simulation everywhere. It defined a sub-KHG outlet as a natural or artificial channel, usually a small river or a canal, that carries part of the water to the KHG outlet. It derived flow direction (D8) and Strahler stream order from a LiDAR DTM, filled with WorldDEM elsewhere, took channels of order 7 as outlets, and obtained 16 sub-KHG of 35.0 to 1,491.2 km² in a KHG of 4,508 km². A field check found that the modelled flow directions matched the field and that sub-KHG boundaries are wide outlet canals collecting the flow of neighbouring units. The published version (Cahyono et al. 2022) describes the sub-units as determined from streamlines, outlet channels, peat depth, slopes and network connectivity. The same team's Pulau Padang study of 2018 used the same approach and produced 11 units.

The nearest published precedent is Jaenicke et al. (2010), who delineated two sub-catchments of the Sebangau dome, named after their outlet rivers, from a 30 m DTM. Cobb et al. (2017) describe tropical peat domes as taking their shape "within a network of rivers or canals", which supports using the mapped channels as unit boundaries.

## 5.2 Method

The delineation applies the 2021 approach in the same way to any KHG. It takes a ground DTM, the mapped rivers and lakes, the canal network with its class, and the KHG polygon. The mapped channels set most of the unit layout, and the terrain places the divides between them.

{{diagram: delineation_flow_report_a | Sub-KHG delineation, part 1: inputs and steps 1 to 5 (surface preparation and flow) | diagrams/delineation_flow_report_a.drawio}}

{{diagram: delineation_flow_report_b | Sub-KHG delineation, part 2: steps 6 to 10, outputs and the analyses that use them | diagrams/delineation_flow_report_b.drawio}}

1. The DTM is projected onto a 30 m UTM grid over the KHG plus 1 km, with bilinear interpolation. The 20 m and 25 m LiDAR, 8 m DEMNAS and 30 m DeltaDTM are all resampled to this grid for this step only; the native surfaces are kept.
2. Rivers and all canals are cut 3 m into the DTM, since canals are narrower than a 30 m cell.
3. Pits, depressions and flats are resolved. D8 flow direction, flow accumulation and Strahler order follow. DEM-derived streams start at 2 km² of contributing area.
4. The outlet set is the mapped rivers and lakes plus the outlet canals, which are the primary and secondary canals (*Kanal Primer*, *Kanal Sekunder*) of the BRGM canal layer. Tertiary canals, the plantation drainage grid, are cut into the DTM but are not outlets.
5. Every cell is traced downstream to the first outlet cell it reaches. Each piece is the catchment of one reach of outlet channel on one bank, so divides and outlet channels are its boundaries. Flow that leaves the KHG without meeting an outlet forms coastal catchments, which are cut into compact pieces of about 50 km².
6. Pieces below a minimum area are merged, smallest first, into the neighbour they share the longest divide with; a border across an outlet channel is used only when there is no divide neighbour. With the automatic setting, the minimum area starts at 5 km² and rises by 10% at a time until at most 30 units remain.
7. Channel cells go to the nearest unit, the result is clipped to the KHG, and units are numbered north to south.

The method tries the mapped outlets alone first. Only if they give fewer than 6 or more than 30 units does it add DEM-derived streams, from the highest Strahler order down. In all 12 delineations reported below the mapped outlets alone gave a count in range, so no DEM stream was added.

Table: Delineation settings. Source: delineation method of the toolkit.

| Setting | Value |
|---|---|
| Analysis grid | 30 m, UTM |
| Channel burn depth | 3 m |
| Stream start (DEM streams) | 2 km² contributing area |
| Outlets | rivers, lakes, primary and secondary canals |
| Target unit count | 6 to 30 |
| Minimum area | automatic: from 5 km², +10% per step, until at most 30 units |
| Merge | into the neighbour with the longest shared divide |
| Coastal catchments | cut into pieces of about 50 km² |

The target count and the minimum area are set by the project. No regulation or study found gives an external basis for them.

### Why secondary canals are outlets

With secondary canals as outlets, the units agree much better across terrain sources and terrain noise (section 5.4). The first test delineations at Kampar-Gaung and Sugihan-Lumpur used only primary canals and rivers as outlets; secondary canals were added after the stability test showed this. The 2021 study also counted primary and secondary canals, and ignored tertiary canals, when it assessed canal blocks.

## 5.3 Results for the first four KHG

Every delineation gave a unit count close to the upper limit, and unit size follows the density of the outlet canal network. The delineation has been made for these four KHG, the ones on which the method was developed, each with three terrain variants (chapter 4): LiDAR as delivered, DeltaDTM after correction and DEMNAS after correction. At Mendahara-Batanghari and Sugihan-Lumpur the corrected DeltaDTM and DEMNAS are the surfaces made for the benchmark; at Kampar-Gaung and Saleh-Sugihan they were made with the same correction and the same parameters.

{{table: subkhg_units | Sub-KHG units per KHG and terrain source: number of units, pieces before merging, automatic minimum area and unit areas. Source: sub-KHG delineation results per KHG | _khg/<folder>/02_delineation/<dem>/delineation_report.json for folders 14.02-04-05.01_kampar_gaung, 15.05-07-10.01_mendahara_batanghari, 16.02-07.01_saleh_sugihan, 16.02.01_sugihan_lumpur and dem lidar, deltadtm, demnas; columns: KHG, terrain (dem), n_subkhg, pieces_before_merge, min_area_km2, area_km2.min, area_km2.median, area_km2.max, area_km2.total; one row per KHG and terrain (12 rows). Footnote: the Saleh-Sugihan LiDAR covers about 1,174 of 1,897 km², so its units cover only that part of the KHG}}

All 12 delineations gave 26 to 29 units. The count is close to the cap of 30 in every case because the automatic minimum area rises only until the count falls to 30 or below. What differs by KHG and terrain is the minimum area chosen and the spread of unit sizes.

- Kampar-Gaung (7,111 km²): 27 to 29 units. The minimum area was 105.6 km² on LiDAR and 116.1 km² on DeltaDTM and DEMNAS. Units ran from 109.2 to 621.0 km² on LiDAR, 128.4 to 538.8 km² on DeltaDTM and 127.5 to 510.6 km² on DEMNAS, with medians of 215 to 225 km².
- Mendahara-Batanghari (2,012 km²): 29 units on each terrain. The minimum area was 30.6 km² (LiDAR, DEMNAS) and 33.6 km² (DeltaDTM). Median unit area was 63.5 km² on LiDAR, 54.8 km² on DeltaDTM and 56.5 km² on DEMNAS; the largest unit was 139.8, 202.9 and 151.0 km².
- Saleh-Sugihan (1,897 km²): 26 units on DeltaDTM (31.7 to 137.3 km²) and 27 on DEMNAS (37.3 to 137.8 km²). The LiDAR delineation gave 29 units of 20.3 to 76.5 km², but the LiDAR covers only about 1,174 km² (62%) of the KHG, so these units cover only that part and cannot be compared with the other two.
- Sugihan-Lumpur (6,347 km²): 29 units on LiDAR (126.2 to 373.0 km², median 220.8 km², minimum area 116.1 km²), 29 on DeltaDTM (117.6 to 413.0 km²) and 27 on DEMNAS (121.1 to 481.0 km²), both with a minimum area of 105.6 km².

Mendahara-Batanghari has 2,190 primary and secondary canal segments in 2,012 km², and Saleh-Sugihan 3,080 in 1,897 km², so their catchment pieces are small and the 30-unit cap is reached at a minimum area of about 30 km². Kampar-Gaung has 977 outlet canal segments in 7,111 km², so its units are larger. Sugihan-Lumpur has only 2 river segments, so its 4,387 primary and secondary canal segments make up nearly all of its outlet network.

{{figure: subkhg_map_sugihan_lumpur | Sub-KHG units of Sugihan-Lumpur delineated on the LiDAR, with primary and secondary canals and rivers as outlets | Map of _khg/16.02.01_sugihan_lumpur/02_delineation/lidar/subkhg_units.gpkg, polygons outlined and labelled by field unit_id; overlay the outlet canals from _khg/16.02.01_sugihan_lumpur/00_inputs/canals.gpkg where KET_KANAL is "Kanal Primer" or "Kanal Sekunder" (thin grey lines) and the KHG boundary from 00_inputs/khg.gpkg; scale bar and north arrow}}

## 5.4 Sensitivity to terrain and settings

The unit layout is set mainly by the mapped canal network, and the terrain moves the internal divides. At Sugihan-Lumpur a stability test delineated the KHG with seven terrain surfaces, with five copies of the LiDAR to which spatially correlated noise was added (0.25 m standard deviation, 500 m correlation length), and with a flat surface on which only the mapped channels shape the units. Each result was compared with the LiDAR delineation by the adjusted Rand index (ARI, 1 for an identical partition) and the mean best-match intersection over union (IoU). The test design was fixed before any delineation was made.

Table: Agreement of sub-KHG units with the LiDAR units at Sugihan-Lumpur, by outlet setting. Source: delineation stability test, Sugihan-Lumpur.

| Outlets | ARI, noisy LiDAR copies (mean) | ARI, other terrain sources (mean) | ARI, flat surface | Unit count range |
|---|---|---|---|---|
| Primary canals and rivers | 0.471 | 0.48 | 0.348 | 24 to 30 |
| Primary and secondary canals and rivers | 0.633 | 0.629 | 0.601 | 26 to 30 |
| Primary and secondary, merge by flow line | 0.603 | 0.606 | 0.569 | 26 to 30 |

With primary canals only, the units are unstable: 0.25 m of noise on the LiDAR changes them about as much as switching to another terrain source, and the largest LiDAR unit reaches 1,353 km². With secondary canals added, agreement rises to about 0.63 for both noise and terrain, and the largest LiDAR unit falls to 373 km². The flat surface then scores 0.601, close to the real terrain sources. A merge rule that prefers the neighbour draining to the same channel line agreed slightly less (0.603 and 0.606), so the longest-divide merge is kept.

Table: Mean best-match IoU of each terrain source with the LiDAR units at Sugihan-Lumpur, primary and secondary canals as outlets. Source: delineation stability test, Sugihan-Lumpur.

| Terrain | Units | Best-match IoU | ARI |
|---|---|---|---|
| LiDAR smoothed (300 m median, 150 m gaussian) | 27 | 0.628 | 0.691 |
| KLHK modelled DTM, as delivered | 27 | 0.609 | 0.651 |
| DeltaDTM with ICESat-2 offsets, smoothed (300 m median, 150 m gaussian) | 28 | 0.598 | 0.613 |
| KLHK modelled DTM, processed | 30 | 0.574 | 0.640 |
| Flat surface | 28 | 0.568 | 0.601 |
| DeltaDTM with ICESat-2 offsets, smoothed (1,200 m median, 600 m gaussian) | 29 | 0.556 | 0.609 |
| DEMNAS, processed | 27 | 0.552 | 0.598 |

DeltaDTM with ICESat-2 offsets and the standard smoothing agrees with the LiDAR units better than the flat surface does, and processed DEMNAS slightly worse. The gaps are small, which fits the terrain benchmark of chapter 4: over 1 km the terrain errors of the open DEMs are larger than the relief itself.

![Share of delineations in which each cell is a unit boundary, Sugihan-Lumpur, over all terrain sources and noisy LiDAR copies; left primary canals as outlets, middle primary and secondary, right primary and secondary with the flow-line merge. Source: delineation stability test.](_khg/16.02.01_sugihan_lumpur/02_delineation/stability/boundary_frequency.png)

The minimum area is the other main setting. In the earlier primary-only delineations, raising the minimum area from 5 to 300 km² reduced the count smoothly with the longest-divide merge: 247 to 9 units at Kampar-Gaung (from 5,581 pieces) and 182 to 6 at Sugihan-Lumpur (from 6,219 pieces). An earlier rule that dropped small pieces and gave their cells to the nearest unit collapsed both KHG to 1 or 2 units at a minimum area of 100 km² or more.

Small changes in input also move the result. The same LiDAR gave 30 units with a minimum area of 105.6 km² from the original delivery, and 29 units with 116.1 km² from the copy clipped to the KHG.

## 5.5 Limits

- No official sub-KHG layout exists for the four KHG, so the units cannot be checked against one. The only reference layout is the 16 units of the 2021 Kahayan-Sebangau study; the delineation has not yet been applied to that KHG, so that comparison is still to be made.
- Unit count and minimum area have no external basis; they are set by the project.
- The outlets depend on the canal classes in the BRGM canal layer. The layer has no flow direction or canal dimensions, and the units carry no outlet reach or record of which unit drains into which.
- There is no explicit dome-crest layer. The divides between units come from D8 flow on a surface whose error over 1 km exceeds the relief where no LiDAR exists.
- Licence areas are not used in the delineation. The 2021 study noted that plantations may change sub-KHG boundaries by turning rivers into canals.
- The unit size sets what the water balance can resolve. The smallest units at Sugihan-Lumpur (about 118 to 126 km²) span only about four cells of the CHIRPS rain grid (0.05°, about 31 km² per cell), and the smallest Kahayan-Sebangau unit of 2021 (35 km²) about one cell. Rain cannot differ much between neighbouring units.
