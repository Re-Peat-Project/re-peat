# 9 RE-PEAT Interventions: canal blocks and pumping

RE-PEAT Interventions turns the results of the earlier chapters into a costed rewetting plan for one *KHG* (*Kesatuan Hidrologis Gambut*, peat hydrological unit). In the highest-ranked *sub-KHG* units it proposes where to build *sekat kanal* (canal blocks) on the primary and secondary canals and shows the canal stretch each block holds back. For every sub-KHG in the KHG it assigns a treatment and prices the quantities. Where a river can supply water in the dry season, it also routes pumped water to the driest pools and sizes the pump stations. KLH staff use it through a QGIS plugin; the same method also runs in batch over many KHG.

The module is the last step of the toolkit. It draws on the canal network, rivers and existing blocks of the KHG, the DTM from the DEM correction (chapter 4), the sub-KHG units from the delineation, the KHG water deficit from the *neraca air* (water balance), and the order and indicators of the sub-KHG from the sub-KHG prioritisation.

## 9.1 Inputs

Table: Inputs of RE-PEAT Interventions. Source: interventions module method report and README.

| Input | Source in the toolkit | Used for |
|---|---|---|
| Bare-earth DTM | DEM correction: LiDAR where it exists, then DeltaDTM, then DEMNAS | land profile along each canal, flow accumulation; a surface model (DSM) is refused |
| Canals with class | KHG inputs (primary, secondary, tertiary) | the network; primary and secondary by default |
| Existing canal blocks | KHG inputs | blocks already built, counted as in place |
| Rivers | KHG inputs | flow direction of canals; pump intakes when a river is marked perennial or has a dry-season level |
| Sub-KHG units and ranking | delineation and sub-KHG prioritisation | which sub-KHG are analysed (top n by rank), deficit per unit |
| Moisture (NDMI) | latest annual NDMI of the KHG | dryness of each canal segment |
| Burnt area, peat depth | national layers clipped to the KHG (optional) | criteria of the segment need score |
| Sub-KHG indicators | sub-KHG prioritisation | protected peat share, NDMI, burnt share, canal reach, distance to water, canal density |
| Water balance map | neraca air | KHG deficit, monthly balance and SiTMAT stations for the report |
| Unit prices | proposed defaults, with a register of sources | the budget |

The data inputs are assembled automatically for each KHG. Every parameter that is a policy choice (weights, spacing, pump specifications, prices) starts empty, and no stage runs until its required values are set, either by the user or from a set of proposed defaults. Each value taken from the proposed defaults is listed in the plan's report, so a reviewer can see which choices still need agreement.

## 9.2 The twelve stages

The method has twelve stages, with three points where a reviewer checks the results before the plan goes further: after the canal network is cleaned (stage 2), after canal segments are scored for need (stage 6) and after water routes are drawn (stage 9). Changing a setting or an input recomputes that stage and every later one.

{{diagram: pump_method_report_a | Method of RE-PEAT Interventions, part 1: inputs and stages 1 to 5 | diagrams/pump_method_report_a.drawio}}

{{diagram: pump_method_report_b | Method of RE-PEAT Interventions, part 2: stages 6 to 11 (blocks, pumping, optimisation); review points after stages 6 and 9 | diagrams/pump_method_report_b.drawio}}

{{diagram: pump_method_report_c | Method of RE-PEAT Interventions, part 3: stage 12 (interventions, budget, report) | diagrams/pump_method_report_c.drawio}}

1. Load and validate. Clips every input to the selected sub-KHG plus a 600 m margin, checks the coordinate system and the DTM type, and warns when the DTM's vertical error is too large for head-based placement (when 0.40 m is less than twice the vertical RMSE).
2. Topology (review point). Keeps the chosen canal classes, snaps end points within 1 m, and marks dangles, gaps and canals with no connection to a river for checking. Nothing is deleted without review.
3. Hydrology. Burns the canals 2 m into the DTM (where a canal has no depth) and computes flow accumulation.
4. Segments. Cuts canals into segments of at most 500 m and flags pieces shorter than 25 m, which stay in the network but are not scored.
5. Profiles. Samples the land along each canal every 5 m from the unburned DTM and sets each canal's flow direction from its slope, else its river connection, else flow accumulation (downstream is the end where clearly more water collects).
6. Need score per segment (review point). Scores dryness (moisture in a ring 15 to 100 m from the canal, outside the canal water), upstream contribution, burn frequency and peat depth. Each criterion is min-max normalised and weighted; the top 20 % of segments are selected. A one-at-a-time sensitivity test moves each weight by ±10 % and ±20 %.
7. Canal blocks. Places blocks by the head rule, merges them with existing blocks and keeps the fewest that give 90 % of the canal rewetting (sections 9.3 and 9.4).
8. Network. Builds a directed graph of canals, rivers and blocks (only when pumping is planned).
9. Routing (review point). Finds head-aware least-cost routes from river intakes to the highest pool of each cluster of selected segments.
10. Pumps. Computes water demand, places pump stations along each route and sizes them.
11. Block optimisation (optional, off by default). Chooses a set number of the kept blocks by genetic algorithm, simulated annealing or greedy search, scored by canal rise or by the groundwater model, which is in development.
12. Interventions, budget and report. Assigns a treatment to every sub-KHG, prices the quantities and writes the report.

When no river in the analysis extent is perennial or has a dry-season level, stages 8 to 10 are skipped and the plan covers blocks only. All plans reported in this chapter are block-only for that reason.

## 9.3 Block placement: the head rule and the KLH minimum distance

Blocks are placed where the land along a canal has risen enough to need one, so their number follows the slope of the land and the quality of the DTM. Starting at the downstream end, the method walks up each canal along the land profile and puts a new block where the land has risen *dA* = 0.40 m above the previous block, the water-table limit of PP 57/2016. This is the guide's idea of equal-head points, computed from the profile instead of from vector contours. An existing block resets the baseline.

For each canal the module also reports the required number of blocks (the land rise between the canal ends divided by *dA*, rounded up) and the KLH adequacy index IPG (existing blocks ÷ required blocks). It gives the required spacing *dA* ÷ slope, capped at 500 m, and the block height from the canal depth, spacing and slope. Blocks on a slope of 5 % or more are marked as reinforced; the slope sets the block type and never removes a block.

Two spacing values were taken from the KLH technical guide at the request of KLH users:

- A minimum distance of 500 m between new blocks along a canal (the guide's minimum distance between blocks). After a new block is placed, the next new block on that canal is at least 500 m further upstream. On land steeper than 0.40 m in 500 m (0.08 %) this overrides the head rule and gives fewer blocks.
- A merge distance of 100 m. A proposed block within 100 m of an existing block, or of a block proposed on another canal, is dropped. The guide's script used 50 m.

A new block also never lies within 100 m of an existing block on the same canal. Existing blocks count as built when they lie within 30 m of an analysed canal.

The 500 m maximum caps only the reported required spacing. Flat land does not receive a block every 500 m: on a canal where the land rises less than 0.40 m, the head rule places no block.

## 9.4 Merging with existing blocks and the 90 % balance

The balance step roughly halves the number of blocks while keeping 90 % of the rewetting, which keeps the plan to blocks that each hold a useful amount of water. At Sugihan-Lumpur on LiDAR it kept 43 of 86 head-rule blocks for 90.2 % of the rise.

Existing blocks enter the placement in three ways. They reset the head baseline, they suppress new blocks within 100 m, and in the balance they are held as already in place.

The head rule can propose many blocks that each add little. The balance step ranks the proposed blocks by the canal rewetting each adds, measured as the change in canal water level. Urzainki et al. (2020) used that measure as the simpler of their two block-placement schemes; their main scheme minimises the mean water-table depth, which needs a groundwater model. Each block holds water at its land level minus *dA*. It raises every canal station upstream that lies lower, starting from an unblocked dry-season canal level 1.0 m below the land, and never above the land surface. Blocks are added in order of extra rise, and the fewest that give 90 % of the rise of all head-rule blocks are kept. The rest are reported as low-benefit blocks with their rank and gain. A cap on the number of blocks, set from the budget, can override the share.

The 90 % share was chosen from test layouts at Sugihan-Lumpur made before the 500 m and 100 m spacing values were adopted. On the LiDAR network, past 90 % the water each extra block holds fell by 2.4 to 5 times, and balanced layouts held 1.9 to 2.5 times more water per block than the full head-rule layout. Including tertiary canals gave balanced layouts 2.8 to 3.3 times the water. The KLH guide analyses primary and secondary canals, so tertiary canals stay optional. The order of the blocks barely changed when the unblocked level was set anywhere between 0.8 and 1.2 m. The groundwater model of the neraca air work (chapter 8) uses the same 1.0 m unblocked canal level when it simulates block scenarios, so the two methods start from the same canal state.

For every kept block the plan shows its reach: the canal stretch whose final level that block sets, with the rise, the depth of the water below the land and the share inside burnt area.

## 9.5 Prioritisation of sub-KHG and canal segments

Blocks are planned first in the sub-KHG with the highest need. By default these are the three highest-ranked units of the sub-KHG prioritisation. That ranking uses default weights proposed for agreement with KLH and the World Bank and adjustable in the dashboard, so the selected units may change once the weights are agreed.

Inside the selected units, stage 6 ranks canal segments by need, with equal weights of 0.25 for burn frequency, peat depth, dryness and upstream contribution (the equal weighting of the KLH scoring). These segment weights are also proposed values for agreement. Weights can instead be set by pairwise comparison (AHP, consistency ratio at most 0.10), and the guide's own 1-to-3 scoring with a threshold of 10 out of 12 is available as an option. Concession areas are flagged after scoring and never dropped silently.

At Sugihan-Lumpur the need ranking was stable under weight changes. The lowest Spearman correlation under ±20 % weight changes was 0.988 on LiDAR, 0.983 on DeltaDTM and 0.977 on DEMNAS. The share of top segments retained was at least 0.93, 0.92 and 0.82.

## 9.6 Routing water and sizing pumps

Pumping is designed for KHG where a river can supply water in the dry season. It has not yet been applied to a real KHG, and its values are engineering proposals with low or medium confidence, to be replaced by the procurement specification.

Sources are points where a river meets a canal, found with a 30 m canal buffer as in the guide. Targets are the highest node of each connected cluster of selected segments, where the guide uses segment centroids. The cost of moving along a canal is its length plus a penalty for each metre of uphill lift (by default 1 m of lift costs as much as 1 km of canal). By default one Steiner tree serves all targets, so several targets share trunk canals; one shortest route per target, as in the guide's script, is the alternative. Existing blocks without a gate are dead ends. Proposed blocks on a route are designed with a gate.

Demand for each target is the KHG deficit times the peat area within 600 m of the served segments, delivered over the design period. Without a deficit it is a 0.40 m water-table rise times a specific yield of 0.30 times the same area. The flow is the volume divided by the period (120 days by default, July to October; Ritzema et al. 2014). Stations are placed at the intake and wherever the lift plus canal friction (Manning n 0.035; Chow 1959) would exceed 5 m. A station moves back to the nearest block in that stretch, so a lift station sits at a block. Power is ρgQH divided by the pump efficiency (Karassik et al. 2008), with an efficiency of 0.65 at the low end of the normal range (Haman 2017). Units of 0.10 m³/s each are counted. Shortfalls are reported, never capped silently.

## 9.7 Interventions per sub-KHG and the link to the water balance

Blocks keep water that would otherwise drain away. They do not supply water in the dry season, and they act only on land near the canals. Most sub-KHG therefore need another treatment as well as, or instead of, blocks. Stage 12 gives every sub-KHG the first treatment whose rule holds.

Table: Treatment rules per sub-KHG (proposed policy thresholds, for agreement). Source: interventions module code and proposed defaults.

| Treatment | Rule |
|---|---|
| Close or backfill canals | protected peat function on at least 0.5 of the unit |
| Revegetation and fire readiness | dry (NDMI below 0.30) or burnt (at least 0.25 ever burnt), and canals reach less than 0.4 of the unit |
| Blocks and water supply | canals reach at least 0.4, blocks hold less than 0.5 of the deficit, permanent water within 5,000 m on average |
| Blocks and deep wells | as above, but no water within 5,000 m, and dry or burnt |
| Blocks | canals reach at least 0.4 |
| Maintain and monitor | none of the above |

For units under the protected-peat rule, the plan also reports the treatment they would get without it.

The water the kept blocks hold in a unit is the canal rise times a specific yield of 0.15 (the neraca air value) times a lateral reach of 600 m (Urzainki et al. 2023). This is compared with the unit's deficit: the KHG deficit in mm from the neraca air times the unit area. Units outside the analysed sub-KHG have no block layout, so blocks count as falling short there when the KHG deficit is at least 50 mm.

## 9.8 Budget and its sources

The budget prices the quantities of each sub-KHG at low, central and high unit prices. All prices are proposed unit prices, to be verified, and should be replaced by the KLH cost standard for rewetting infrastructure once KLH provides it.

Table: Budget items, quantities and proposed unit prices. Source: interventions module code, proposed defaults and price register.

| Item | Quantity | Unit price, low / central / high (Rp) |
|---|---|---|
| Standard block | kept blocks of stage 7 in the analysed sub-KHG; elsewhere, for a block treatment, the KLH IPG estimate of missing blocks from the sub-KHG prioritisation | 12 / 18 / 18 million per block |
| Reinforced block | kept blocks on a slope of 5 % or more | 70 million per block |
| Canal closure | canal density (primary and secondary) × peat area, for close-canal units | not priced |
| Revegetation | area ever burnt, revegetation units | 8 / 12.1 / 15 million per ha |
| Deep wells | area ever burnt ÷ area of one well (π × (200 m)², about 12.6 ha), revegetation and block-with-wells units | 3 / 8.5 / 9 million per well |
| Pumps and fuel | pump units of stage 10; power × 12 h/day × design period × 0.3 L/kWh | 15.5 million per pump; diesel 23,554 to 24,886 per L |

The prices come from news reports, a journal article, a marketplace listing and the October 2026 industrial diesel reference, found by web search on 27 October 2026. They are not adjusted for inflation. Each price is recorded in a price register with its source, link, date accessed and status. Of its 19 entries, 15 are marked to verify, 2 unconfirmed, 1 an assumption and 1 to obtain from KLH; none has yet been checked against its source page. No published price per km of canal backfilling was found, so canal closure is reported as length only.

## 9.9 Outputs

Each plan, one per DEM, delivers:

- map layers for every stage: cleaned canals, segments with need score, proposed and low-benefit blocks, block reaches, assessed existing blocks, interventions, budget, and (with pumping) routes and stations;
- tables of interventions per sub-KHG, budget per sub-KHG and item, and the price register with the prices used;
- a report with counts, warnings, the balance, interventions, budget and every value taken from the proposed defaults;
- an interactive report page in English and Bahasa Indonesia, with light and dark themes. It has a map of interventions or the dry-season balance, blocks, animated reaches, burnt area and SiTMAT stations, plus the rewetting curve against blocks or rupiah, the budget with its sources, and a sortable sub-KHG table;
- print layouts in the style of the KLH peat maps, A0 to A4, landscape or portrait. They carry a lat/long border, north arrow, scale bar, legend in columns, data sources, a locator inset and a budget table. Planned blocks are dark green squares and existing blocks magenta squares, following the KLH sheets.

![Print layout (A3 landscape) of the LiDAR plan at Sugihan-Lumpur, 28 October 2026: interventions per sub-KHG, planned and existing blocks, burnt area and SiTMAT stations. Source: RE-PEAT Interventions, Sugihan-Lumpur LiDAR run.](_khg/16.02.01_sugihan_lumpur/05_pump/lidar/layouts/layout_A3_landscape.png)

![The interventions report for Sugihan-Lumpur on the LiDAR DEM: headline numbers, map of interventions, water held by the blocks in order of benefit, interventions per sub-KHG, budget, monthly water balance and the SiTMAT water table. Source: RE-PEAT Interventions run of 28 October 2026](re-peat/reports/project_report/figures/screen_interventions_report.png)

## 9.10 The QGIS plugin for KLH staff

KLH staff receive the module as a QGIS plugin, so a plan can be prepared, reviewed and printed in the GIS software they already use. The plugin runs the same method as the batch version and carries the KLH layout templates, logo and locator map. It is installed once, with an internet connection, and then works in English and Bahasa Indonesia.

A guided wizard takes staff through a plan and is also meant for training:

- Staff choose a KHG, and the wizard fills in the inputs held for it and lists anything missing. It proposes how the canal classes in the data map to primary, secondary and tertiary, for the user to confirm. Pump planning is offered only when a river has a dry-season level or is marked perennial; tertiary canals are off by default.
- Policy values can be filled from the proposed defaults, each marked as such, and a value entered by the user always takes precedence. Datums, DTM error and the moisture direction must always be entered by the user.
- Each stage explains what it does and which decisions it needs, with an optional learning mode that adds the reasoning and references.
- At the three review points (stages 2, 6 and 9) the wizard pauses so staff can inspect the layers on the map and accept or repeat the stage.
- The last step exports the report page and the print layout, which staff can edit further in QGIS.

The plugin has been tested in an automated session in QGIS 4.2.2. It has not yet been used by KLH staff.

## 9.11 How the module follows and departs from the KLH guide

The KLH technical guide (*Panduan Teknis GIS Rewetting KLH*), prepared by the Department of Geodetic Engineering, UGM, with a method developed jointly with KLH, sets out ten manual steps in QGIS, from data preparation to block placement with a Python script. The module follows its order and most of its values. It departs from the guide where the guide's method loses information or depends on manual tuning.

Table: Comparison with the KLH technical guide. Source: KLH technical guide (Appendix A and D) and interventions module code and proposed defaults.

| Topic | KLH guide | RE-PEAT Interventions |
|---|---|---|
| Canal classes | primary and secondary | same by default; tertiary optional |
| Segments | at most 500 m; under 25 m not scored | same |
| Stream burning | fixed 2 m | canal depth where known, else 2 m |
| Moisture and flow extraction | 50 m buffer including the canal | ring 15 to 100 m outside the canal water; the 50 m buffer is used in the guide's scoring mode |
| Scoring | four criteria scored 1 to 3, summed (maximum 12), class breaks fitted by hand to each KHG | min-max normalised criteria, direct or AHP weights, sensitivity test; the guide's scoring available as an option |
| Priority threshold | score of 10 or more (marked temporary) | top 20 % of segments |
| Route targets | centroids of priority segments | highest pool of each cluster of selected segments |
| Routing | shortest path from each start | head-aware least cost; Steiner tree by default, per-target routes as an option |
| Block placement | 0.5 m contours on smoothed DEMNAS crossing the route | land profile, a block at each 0.40 m rise (PP 57/2016), no vector contours |
| Minimum distance between new blocks | 500 m | 500 m (from the guide) |
| Merge distance | 50 m | 100 m |
| Slope 5 % | marks the block type | same |
| Concessions | left out of scoring | flagged after scoring |
| Number of blocks | all placed | fewest giving 90 % of the canal rewetting |

The guide places blocks only along the routes from river mouths to priority segments. The module places them on every analysed canal in the selected sub-KHG, so a block-only plan is possible where no river qualifies as a source.

## 9.12 Results at Sugihan-Lumpur by DEM

At Sugihan-Lumpur (KHG 16.02.01) the plan keeps 39 to 62 blocks in the three selected sub-KHG, depending on the DTM, at a cost below 1.2 billion rupiah. These blocks hold under 7 % of the dry-season deficit, so most of the budget goes to other treatments, chiefly revegetation of burnt land.

Plans were made with each of the three DTM variants, using primary and secondary canals and the proposed defaults, including the 500 m minimum distance and the 100 m merge distance. All three are block-only because no river feature lies inside the analysis extent. The LiDAR variant at this KHG is the KLHK 25 m LiDAR DEM. DeltaDTM (30 m) and DEMNAS (8 m) are the smoothed, corrected surfaces from the DEM correction.

The three highest-ranked sub-KHG differ by DEM, because each DEM has its own sub-KHG delineation and ranking, and unit codes are numbered per variant. The numbers in the next table therefore compare different areas as well as different surfaces.

Table: Canal blocks at Sugihan-Lumpur by DTM, three highest-ranked sub-KHG, 28 October 2026. Source: run reports and map layers of the three plans.

| | LiDAR (25 m) | DeltaDTM (30 m) | DEMNAS (8 m) |
|---|---|---|---|
| Sub-KHG analysed | S21, S03, S02 | S23, S03, S08 | S20, S06, S04 |
| Vertical error assumed (m) | 0.3 | 0.49 | 4.97 |
| Primary and secondary canals after cleaning | 596 | 408 | 476 |
| Canals oriented by flow accumulation | 191 | 165 | 294 |
| Canals with unresolved direction | 302 | 182 | 178 |
| Existing blocks in extent / on an analysed canal | 173 / 76 | 273 / 127 | 380 / 131 |
| Proposals dropped within 100 m of another block | 3 | 4 | 12 |
| Head-rule blocks | 86 | 117 | 226 |
| Blocks kept at 90 % | 43 | 39 | 62 |
| Canal held back by kept blocks (km) | 68.7 | 110.1 | 128.9 |
| of which inside burnt area (km) | 26.9 | 65.0 | 58.9 |
| Water held / deficit, selected sub-KHG (million m³) | 2.19 / 196.9 | 5.06 / 175.9 | 5.02 / 227.1 |
| Share of deficit held per sub-KHG (%) | 0.5 to 1.3 | 0.5 to 6.9 | 1.4 to 3.2 |

The DTM changed the head-rule count 2.6-fold: DEMNAS gives 226 head-rule blocks against 86 on LiDAR. (Adding tertiary canals changes it more, 3 to 4 times at this KHG.) The DEMNAS plan assumed the vertical error of raw DEMNAS, 4.97 m, and the DeltaDTM plan its benchmark error against LiDAR, 0.49 m. Against a step of 0.40 m, much of the rise DEMNAS shows along a canal is likely noise. The method flags every DTM whose assumed error exceeds 0.2 m, which here is all three. After the 90 % balance the gap narrows to 62 against 43 blocks, because many noise-driven blocks add little rise. DeltaDTM gives fewer kept blocks than LiDAR (39 against 43) but more held canal length, on a different set of sub-KHG. These differences are within one KHG and one set of defaults. They show that block counts from DEMNAS should not be taken as a design.

The kept blocks hold under 7 % of the dry-season deficit in every selected sub-KHG (KHG deficit 290 mm). Blocking keeps water in place but cannot cover a deficit of this size, and most sub-KHG get another treatment.

Table: Treatments per sub-KHG at Sugihan-Lumpur by DTM (proposed thresholds). Source: run reports of the three plans.

| Treatment | LiDAR | DeltaDTM | DEMNAS |
|---|---|---|---|
| Close or backfill canals (protected peat) | 20 | 18 | 16 |
| Revegetation and fire readiness | 3 | 2 | 1 |
| Blocks and water supply | 2 | 2 | 4 |
| Blocks and deep wells | 2 | 4 | 5 |
| Blocks | 2 | 3 | 0 |
| Maintain and monitor | 0 | 0 | 1 |
| Total sub-KHG | 29 | 29 | 27 |

Table: Budget estimate at Sugihan-Lumpur by DTM, billion rupiah at proposed 2026 prices (low / central / high). Source: run reports and budget tables of the three plans.

| Item | LiDAR | DeltaDTM | DEMNAS |
|---|---|---|---|
| Kept blocks (number; cost) | 43; 0.52 / 0.77 / 0.77 | 39; 0.47 / 0.70 / 0.70 | 62; 0.74 / 1.12 / 1.12 |
| KLH IPG estimate of blocks elsewhere (number; cost) | 350; 4.20 / 6.30 / 6.30 | 1,615; 19.38 / 29.07 / 29.07 | 7,327; 87.92 / 131.89 / 131.89 |
| Revegetation (ha; cost) | 46,678; 373.4 / 564.8 / 700.2 | 27,641; 221.1 / 334.5 / 414.6 | 8,173; 65.4 / 98.9 / 122.6 |
| Deep wells (number; cost) | 5,636; 16.9 / 47.9 / 50.7 | 5,089; 15.3 / 43.3 / 45.8 | 4,627; 13.9 / 39.3 / 41.6 |
| Canal closure (km, not priced) | 2,124.7 | 1,607.9 | 1,595.9 |
| Total | 395.1 / 619.8 / 758.0 | 256.2 / 407.5 / 490.2 | 167.9 / 271.2 / 297.2 |
| Kept-block cost per m³ held (Rp) | 353 | 139 | 223 |

The total depends mostly on which treatment the sub-KHG receive, and that in turn follows the DEM through the delineation. On LiDAR, revegetation of burnt land is 91 % of the central total. On DEMNAS the KLH IPG estimate of missing blocks outside the analysed sub-KHG is the largest item, at 131.89 billion rupiah for 7,327 blocks. Kept blocks themselves cost under 1.2 billion rupiah on every variant. The budget leaves out canal closure, which has no price, and every price is still to be verified.

## 9.13 Results across the first four KHG

The table covers the four KHG on which the method was developed; chapter 10 gives the results for all 14 analysed KHG.

{{table: interventions_cross_khg | Canal blocks, pumps, water and budget by KHG and DTM, three highest-ranked sub-KHG, proposed defaults (default weights) | One row per KHG (16.02.01_sugihan_lumpur, 14.02-04-05.01_kampar_gaung, 15.05-07-10.01_mendahara_batanghari, 16.02-07.01_saleh_sugihan) and DTM (lidar, deltadtm, demnas) from _khg/<folder>/05_pump/<dem>/run_report.json: head-rule blocks = sekat_balance.head_rule; blocks kept = sekat_balance.kept; existing blocks on analysed canals = counts.7.existing − counts.7.unsnapped; pump units = sum of pumps[].units_needed (0 when pumps is empty); water held = interventions.held_m3_selected / 1e6 (million m³); deficit = interventions.deficit_m3_selected / 1e6; budget low / central / high = budget.total_low_idr, budget.total_idr, budget.total_high_idr / 1e9 (billion Rp). Skip a KHG and DTM pair whose run_report.json is missing; give run date from the file.}}

{{figure: interventions_blocks_by_dem | Head-rule and kept canal blocks by KHG and DTM | Grouped bar chart, one group per KHG, bars per DTM (lidar, deltadtm, demnas), two values per bar pair: sekat_balance.head_rule and sekat_balance.kept from _khg/<folder>/05_pump/<dem>/run_report.json for the four KHG folders named in table interventions_cross_khg.}}

## 9.14 Limits

- Block placement depends on the DTM. A vertical error above 0.2 m makes the 0.40 m head rule noisy. The 0.3 m LiDAR error is an assumed value; the LiDAR delivery states none. The 4.97 m DEMNAS figure comes from a field comparison of DEMNAS itself, while these plans used the corrected surface, whose error at this KHG has not yet been measured.
- The canal-rise measure ignores flow and seepage. On flat, connected networks a few blocks take most of the rise.
- Specific yield 0.15, reach 600 m and the 1.0 m unblocked canal level set the volumes held, not the order of the blocks. The spread of held water toward burnt land is a fixed 600 m band, not modelled.
- Many canals at Sugihan-Lumpur have no clear slope and no river connection (302 unresolved on LiDAR). Their flow direction is estimated by the fallback rule and may be wrong.
- Pumping has not been applied to a real KHG. The pump values are engineering proposals.
- Budget prices are proposed unit prices from web sources, to be verified. Canal closure has no price, and the KLH cost standard was not available.
- The selected sub-KHG come from a ranking with default weights proposed for agreement with KLH and the World Bank. The treatment thresholds are proposed policy values.
- Block optimisation and the groundwater model (in development) depend on peat properties not measured at these KHG and were not used in the reported plans.
