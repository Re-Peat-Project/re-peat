# 7 Sub-KHG prioritisation

Within one *KHG* (*Kesatuan Hidrologis Gambut*, peat hydrological unit), the sub-KHG prioritisation sets the order in which parts of the KHG should receive rewetting work. It ranks the *sub-KHG* units by their need for intervention: *sekat kanal* (canal blocks), bored wells and pumping. Each unit gets a need score, a rank (1 = most need) and a class (high, medium or low need, the tertiles within the KHG). The ordered list and the KHG water deficit go to RE-PEAT Interventions, which designs blocks and pumping for the units in that order. Which measure suits a unit is decided afterwards, from the feasibility indicators and the interventions module.

The rankings in this chapter use default weights proposed by the project for agreement with KLH and the World Bank. The weights can be adjusted, and the rankings shown follow from these defaults and the data now available.

{{diagram: subkhg_method_report_a | Sub-KHG prioritisation, part 1: inputs, steps 1 to 4 and the weights | diagrams/subkhg_method_report_a.drawio}}

{{diagram: subkhg_method_report_b | Sub-KHG prioritisation, part 2: checks, outputs, users and validation | diagrams/subkhg_method_report_b.drawio}}

## 7.1 Units and inputs

The choice of DEM changes the units themselves, so a ranking holds only for the DEM it was made on. The units come from the sub-KHG delineation (chapter 5), which is carried out once per DEM: the KLHK LiDAR-derived DEM where it covers the KHG, and the corrected DeltaDTM and DEMNAS. Each DEM variant has its own delineation, its own *neraca air* (water balance) and its own ranking. The units of two variants therefore differ in shape and number, and a unit name such as S03 in one variant does not refer to the same area in another.

Fire and canals per unit are counted with the same method as the national profile (chapter 6). The sub-KHG units take the place of the national KHG, so rates are per km² of peat on the GFW extent and fire is counted only on peat. The other indicators are computed on a 30 m grid and averaged over each unit.

Table: Inputs of the sub-KHG ranking. Source: sub-KHG method of the prioritisation module and its settings for Sugihan-Lumpur.

| Input | Form and resolution | Period | Used for |
|---|---|---|---|
| Sub-KHG units | polygons, one set per DEM | | the units |
| Burnt-area polygons | per-year burn flags | 2015-2026 | burned share, repeat burns, validation target |
| VIIRS S-NPP hotspots (NASA FIRMS) | points, vegetation fires, nominal and high confidence | 2012-2025 | hotspot density, validation target |
| KLH hotspots | points (MODIS), medium and high confidence | 1 Jan to 15 Sep 2026 | this year's hotspot density |
| GFW peat extent | about 76 m raster | | denominator of the fire rates |
| Canal layer | lines, class from the canal code | 2025 | canal density by class, reach, blocks needed |
| Existing canal blocks | BRGM hydrological structures, realised canal blocks | | blocks existing |
| Rivers | RBI lines | | distance to water |
| Peat ecosystem function | 2017 polygons, protected function | | protected share |
| DTM | the DEM of the variant | | canal slope, lift above water |
| Peat depth model | raster, per KHG | | peat depth |
| Sentinel-2 L2A | 20 m bands, cloud-masked | August-October of each baseline year | NDMI, NDVI |
| ESA WorldCover | 10 m | 2020/2021 | forest share |
| JRC Global Surface Water | 30 m, months with water | | permanent water for distance to water |
| SiTMAT stations | daily water-table readings | 1 April to 15 October 2026 | days deeper than 0.4 m, recession rate |
| Neraca air per unit | table per unit with a stability flag | 2018-2025 | P minus ET (rank-sum only) |
| KHG deficit | one value per KHG | June to October 2026 | passed to the interventions module |

The indicators use the baseline years 2015 to 2022. The year 2023, an El Niño year, is held out for validation.

## 7.2 Indicators

The need score combines fire, drainage by canals, missing canal blocks, distance to water and dryness, with a smaller part for what is at risk. Indicators fall into three groups. Need indicators say how urgently a unit needs intervention. Stakes indicators say what is at risk. Feasibility indicators help choose the measure and leave the rank unchanged.

Table: Indicators and default weights of the sub-KHG need score. Source: ranking reports of Sugihan-Lumpur and the method of the prioritisation module.

| Group | Indicator | More need when | Weight |
|---|---|---|---|
| Need | Burned share of peat per year | higher | 2 |
| Need | Repeat burns (peat burned two or more times) | higher | 1 |
| Need | VIIRS hotspots per km² of peat per year | higher | 1 |
| Need | KLH hotspots this year per km² of peat | higher | 1 |
| Need | Dry-season NDMI (Sentinel-2) | lower (drier) | 1 |
| Need | Primary, secondary, tertiary canal density (km per km²) | denser | 0.5, 0.3, 0.2 |
| Need | Missing canal blocks (1 minus the block metric) | more missing | 1.5 |
| Need | Canal reach: share within 200 m of a canal (60 m on burned land) | larger | 1.5 |
| Need | Mean distance to permanent water or a river | farther (wells needed) | 1 |
| Need | Forest share (WorldCover tree cover and mangrove) | smaller | 1 |
| Need | SiTMAT: share of days deeper than 0.4 m; recession rate | deeper; faster | 1; 1 |
| Stakes | Mean peat depth | thicker | 2 |
| Stakes | Share with protected peat function | larger | 1 |
| Feasibility (reported, not ranked) | Median height of the land above the nearest water (DTM) | | 1 within feasibility |
| Reported | NDVI, neraca air balance, this year's burned share, single canal density | | 0 |

Missing canal blocks follow the block metric of the 2021 Kahayan-Sebangau study. Keeping the water table within 0.4 m of the surface on a canal with slope *s* needs a block every 0.4 ÷ *s* metres. The spacing is kept between 50 and 2,000 m. For each unit:

1. The canal slope is the median DTM slope along the primary and secondary canals in the unit.
2. Blocks needed is the length of those canals divided by the spacing, rounded up.
3. Blocks existing is the number of realised canal blocks inside the unit.
4. Additional blocks is blocks needed minus blocks existing, and zero where the unit already has enough.
5. The indicator is 1 minus the ratio of existing to needed blocks, capped between 0 and 1.

The 0.4 m target is the PP 57/2016 water-table criterion.

Rain-based indicators (TerraClimate deficit, dry spells) have weight 0. Their 4 to 25 km cells are nearly constant inside a KHG.

The neraca air balance per unit (rain minus evapotranspiration) is used only when its order of units is stable across evapotranspiration products and years. Even then it fills only the water-balance slot of the rank-sum and never enters the need score. SiTMAT is scored only when enough units contain a station: at least half the units must have a value, with never fewer than 3 and never more than 20 required.

## 7.3 Scoring and classes

Need weighs four times as much as stakes in the final score, and the result is checked against a simpler rank-sum and against changes in the weights.

1. Each indicator is scaled from 0 to 1 between its 5th and 95th percentile within the KHG, oriented so that 1 means most need.
2. The need part (U) and the stakes part (S) are weighted means of the scaled indicators a unit has.
3. The need score is 0.8 U + 0.2 S.
4. Classes are the tertiles of the need score.
5. The rank-sum method used in earlier project work is computed beside it. It ranks the units by each of its eight indicators with equal weights and sums the ranks. The agreement of the two rankings is reported.

The earlier rank-sum used NDMI, NDVI, peat depth, water decline, the water balance, deficit months, dry days and hotspots. At present only four or five of these have data: NDMI, NDVI, peat depth, VIIRS hotspots, and the water balance where it is stable. Deficit months are left out at Sugihan-Lumpur, because their order between units follows land cover.

Two checks follow the scoring. Indicator pairs with a Spearman correlation above 0.8 are flagged. Weight sensitivity uses 300 random weight sets drawn around the defaults (Dirichlet, concentration 20). The share of draws in which a unit lands in the high class is reported; a unit is called stable when that share is at least 0.8 or at most 0.2.

## 7.4 Worked example: Sungai Sugihan - Sungai Lumpur

At Sungai Sugihan - Sungai Lumpur the three DEM variants give a similar split of units and area between the need classes, the need score broadly agrees with the earlier rank-sum, and most units keep their class under changed weights. The KHG (South Sumatra, reserve KHG) covers about 6,347 km² and ranks 31st of 476 KHG nationally (chapter 6).

Table: Sub-KHG units and classes per DEM variant, Sungai Sugihan - Sungai Lumpur (default weights). Source: ranking results per DEM variant.

| | LiDAR | DeltaDTM | DEMNAS |
|---|---|---|---|
| Units (n) | 29 | 29 | 27 |
| Unit area, min to max (km²) | 126 to 373 | 118 to 413 | 121 to 481 |
| Unit area, median (km²) | 221 | 189 | 223 |
| High need: units, area (km²) | 10, 2,175 | 10, 2,379 | 9, 2,057 |
| Medium need: units, area (km²) | 9, 1,823 | 9, 1,808 | 9, 1,922 |
| Low need: units, area (km²) | 10, 2,348 | 10, 2,160 | 9, 2,368 |
| Units with a SiTMAT station | 11 | 10 | 12 |
| Neraca air balance stable | 0 of 29 units | 0 of 29 units | 27 of 27 units |
| Need score against rank-sum: Spearman | 0.76 | 0.68 | 0.69 |
| Top 20% shared with rank-sum | 4 of 6 | 5 of 6 | 3 of 5 |
| Units consistently in or out of the high class in 300 weight draws (share in high at least 0.8 or at most 0.2) | 62% | 62% | 74% |
| Median rank spread across draws (SD, places) | 4.2 | 4.2 | 4.0 |

In all three variants the scored indicators are the same 14: the fire, NDMI, canal, missing-block, reach, distance-to-water and forest indicators, and peat depth and protected function. SiTMAT is not scored in any variant, because too few units contain a station (10 to 12, below the minimum of 13 or 14). The neraca air balance passed its stability check only in the DEMNAS variant. There it entered the rank-sum; in the LiDAR and DeltaDTM variants the rank-sum uses four indicators.

Two pairs of indicators are flagged as correlated. Tertiary canal density and canal reach correlate at 0.85 (LiDAR), 0.88 (DeltaDTM) and 0.87 (DEMNAS). Peat depth and lift correlate at -0.80 in the LiDAR variant. Canals are thus counted partly twice in the need score.

{{figure: subkhg_maps_sugihan_lumpur | Need class per sub-KHG of Sungai Sugihan - Sungai Lumpur for the three DEM variants (default weights) | Three map panels side by side, same extent and legend: _khg/16.02.01_sugihan_lumpur/04_prioritisation/lidar/unit_prioritas.gpkg, .../deltadtm/unit_prioritas.gpkg, .../demnas/unit_prioritas.gpkg; fill by field kelas (Kebutuhan intervensi: tinggi / sedang / rendah, shown as high / medium / low need), label each unit with field peringkat; panel titles LiDAR (29 units), DeltaDTM (29), DEMNAS (27).}}

{{table: subkhg_top_sugihan_lumpur | The ten highest-need sub-KHG of Sungai Sugihan - Sungai Lumpur, LiDAR variant (default weights) | _khg/16.02.01_sugihan_lumpur/04_prioritisation/lidar/unit_prioritas.csv, rows peringkat 1 to 10; columns: peringkat (rank), unit_id, area_km2 (km², 0 decimals), skor_need (need score, 2 decimals), skor_urgensi (need part U), skor_dampak (stakes part S), u_fire_freq x 100 (burned share, % of peat per year), u_hotspot (per km² of peat per year), f_reach (share within reach of canals, %), u_ipg_gap (missing blocks, 0-1), n_sekat_perlu, n_sekat_ada, sekat_tambahan (blocks needed, existing, additional), i_peat_depth (m), p_kebutuhan_tinggi (share of weight draws in the high class).}}

## 7.5 Blocks needed and how the DEM changes them

The number of canal blocks a KHG appears to need depends strongly on the DTM, through the canal slope, and the count on one DEM can be several times the count on another.

Table: Canal blocks needed, existing and additional per DEM variant, Sungai Sugihan - Sungai Lumpur, primary and secondary canals. Source: block summaries and unit tables of the ranking per DEM variant.

| | LiDAR | DeltaDTM | DEMNAS |
|---|---|---|---|
| Median canal slope of the units (m/m) | 0.00028 | 0.00060 | 0.0023 |
| Spacing at that slope, 0.4 m ÷ slope (m) | 1,446 | 671 | 175 |
| Units at the 2,000 m spacing cap | 4 | 0 | 0 |
| Blocks needed | 3,634 | 6,237 | 25,580 |
| Blocks existing | 2,847 | 2,847 | 2,847 |
| Additional blocks | 1,335 | 3,631 | 22,733 |
| Additional blocks in high-need units | 526 | 1,514 | 4,988 |

The LiDAR variant at this KHG uses the 25 m DEM that KLHK derived from LiDAR. The same canal network gives 3,634 blocks needed on that DEM and 25,580 on DEMNAS, seven times as many, because the median canal slope on DEMNAS is eight times the LiDAR slope. The vertical error of each DEM is assessed in the DEM benchmark (chapter 4).

Blocks needed count only primary and secondary canals, while blocks existing count every realised canal block in the unit, on any canal class. The two totals are therefore not a like-for-like comparison. Until a DEM with small slope error covers a KHG, the block count from the ranking is a first, rough figure; the block design in RE-PEAT Interventions sets its own spacing.

Additional blocks are counted per unit and are zero where a unit already has more blocks than needed. On the LiDAR DEM several units have more existing blocks than the rule asks for. The additional total (1,335) is therefore larger than blocks needed minus blocks existing (787).

The KHG deficit passed to the interventions module is 290 mm. It covers 1 June to 9 October 2026 and is built from 51 SiTMAT stations with ERA5 rain and evaporation and a specific yield of 0.15, with a range of 285 to 296 mm for specific yields of 0.10 to 0.20. The deficit is computed once per KHG and is the same for all three DEM variants.

## 7.6 Agreement between DEM variants and across KHG

Whether a place is high need should not depend on which DEM was used, so the variants are compared on the ground. Because each DEM variant draws its own units, the rankings of two variants cannot be compared unit by unit. Instead, the unit layers of two variants are intersected, and each piece carries the class and score of both. Agreement is the share of the KHG area that falls in the same class under both DEMs, plus the rank correlation of the two need scores over the pieces, weighted by area.

Rankings on all three DEM variants are available for four KHG, the ones on which the method was developed: Sungai Sugihan - Sungai Lumpur, Sungai Saleh - Sungai Sugihan, Sungai Mendahara - Sungai Batanghari and the earlier test site Sungai Kampar - Sungai Gaung. The tables below give the classes, block counts and agreement between DEM variants for these four. Chapter 10 gives the results for all 14 analysed KHG.

{{table: subkhg_classes_by_khg_dem | Sub-KHG units and need classes per KHG and DEM variant (default weights) | For each KHG folder in (16.02.01_sugihan_lumpur, 16.02-07.01_saleh_sugihan, 15.05-07-10.01_mendahara_batanghari, 14.02-04-05.01_kampar_gaung) and each dem in (lidar, deltadtm, demnas): _khg/<folder>/04_prioritisation/<dem>/ringkasan_kelas.csv (columns kelas, unit, luas_km2) and laporan.json (n_units, ranking_agreement.spearman, sensitivity.share_units_stable_class); kebutuhan_sekat.csv (n_sekat_perlu, n_sekat_ada, sekat_tambahan summed over kelas). One row per KHG and DEM: KHG name, DEM, units (n), high / medium / low need units (n) and area (km²), Spearman need score vs rank-sum, share of units with a stable class (%), blocks needed, existing, additional. Mark Kampar-Gaung as test site, not one of the 12 selected KHG.}}

{{table: subkhg_dem_agreement | Agreement of the sub-KHG need ranking between DEM variants (default weights) | For each KHG folder as in table subkhg_classes_by_khg_dem and each pair of DEM variants (lidar-deltadtm, lidar-demnas, deltadtm-demnas, only where both exist): intersect _khg/<folder>/04_prioritisation/<dem_a>/unit_prioritas.gpkg with .../<dem_b>/unit_prioritas.gpkg (geometry in an equal-area projection); for each intersection piece keep area, kelas_a, kelas_b, skor_risiko_a, skor_risiko_b. Report: share of the summed piece area with kelas_a = kelas_b (%); share of the high-need area of dem_a that is also high need in dem_b (%); area-weighted Spearman between skor_risiko_a and skor_risiko_b over the pieces (or Spearman over a 100 m grid sampled from both layers). Do not match units by unit_id: the unit sets differ per DEM.}}

## 7.7 Held-out validation

Within a KHG the need score points at later fire better than chance, but fire history alone does as well or better in most comparisons, so the validation cannot by itself justify the weights. The validation builds the indicators from 2015 to 2022, leaves this year's hotspots out, and tests the ranking on 2023. It uses the same measures as the national validation (chapter 6): the AUC and the share of later fire captured by the top 20% of units.

Table: Validation on 2023 of the sub-KHG ranking per DEM variant, Sungai Sugihan - Sungai Lumpur. AUC of the full need score, of the need part only, and of burned share alone. Source: ranking reports per DEM.

| Target | Score | LiDAR | DeltaDTM | DEMNAS |
|---|---|---|---|---|
| Units with 5% or more of peat burned in 2023 | | 3 of 29 | 3 of 29 | 3 of 27 |
| Burned share: AUC | need score | 0.72 | 0.88 | 0.79 |
| | need part only | 0.81 | 0.94 | 0.86 |
| | fire history alone | 0.82 | 0.87 | 0.88 |
| Units with hotspots in 2023 | | 17 of 29 | 17 of 29 | 15 of 27 |
| Hotspots: AUC | need score | 0.56 | 0.59 | 0.60 |
| | need part only | 0.67 | 0.70 | 0.71 |
| | fire history alone | 0.69 | 0.72 | 0.77 |

The AUC of the need score is above 0.5 in every variant, but only modestly for hotspots (0.56 to 0.60). Fire history alone scores the same or higher in five of the six comparisons; the exception is burned share on DeltaDTM (0.88 against 0.87). The burned-share test rests on three units, so one unit more or less changes the AUC by a large step. For hotspots the need part does better than the full score. The stakes part (peat depth, protected function) describes what is at risk and says nothing about where fire will occur, so it lowers fire prediction by design.

An earlier unit set of the same KHG (30 units, delineated before the per-DEM variants) was tested with bootstrap intervals on two folds, 2019 and 2023. For burned share in 2019, the Spearman correlation with the need score was 0.37 (90% interval 0.06 to 0.62), against 0.64 (0.39 to 0.82) for fire history alone. At Sungai Kampar - Sungai Gaung the order was reversed: 0.61 (0.35 to 0.80) for the need score against 0.38 (0.02 to 0.68) for fire history. With 26 to 30 units the intervals overlap, and no score is clearly better than another.

Fire is the only outcome that can be tested. Canals, missing blocks and canal reach describe the need for rewetting itself, and no held-out data can test them yet. The weights therefore cannot be set from the validation alone. They should be set by expert judgement, for example in a pairwise-comparison (AHP) session with KLH and the World Bank, with the validation as a check.

## 7.8 Limits

- The weights are defaults proposed for agreement with KLH and the World Bank. Under other weightings some units move in or out of the high-need class (section 7.4).
- Peat depth carries weight 2 in the stakes part, which makes up 0.2 of the need score. At Sugihan-Lumpur the peat depth model covers 74.7% of the KHG, and it correlates with lift at -0.80 in the LiDAR variant. A depth layer that covers only part of a KHG should not drive the ranking, so this weight needs a decision before the rankings are used.
- The units are large (118 to 481 km² at Sugihan-Lumpur). Their size follows from a cap of 30 units per KHG in the delineation (at Sugihan-Lumpur on the LiDAR DEM, a minimum unit area of 116 km² chosen automatically to stay within the cap) and has no hydrological basis. Block effects reach a few hundred metres: about 600 m in model results (Urzainki et al. 2023). An indicator averaged over 200 km² cannot locate where blocks act.
- Burned share is the heaviest need indicator and comes from burnt-area polygons whose source is not documented, so their accuracy cannot be judged.
- The block count depends strongly on the DTM (section 7.5).
- SiTMAT covers one season (2026), mostly in concessions, and too few units to be scored at Sugihan-Lumpur.
- The canal layer is derived from OpenStreetMap and has no flow direction. Existing blocks come from the BRGM structures and may be incomplete.
- Forest share counts plantations as tree cover.
- Classes are tertiles within one KHG, so a high-need unit in one KHG is not directly comparable with a high-need unit in another.
- With 26 to 30 units per KHG and few burned units in a test year, the validation intervals are wide.
