# 11 Findings, limits and decisions needed

## 11.1 What the toolkit can deliver now

For any *KHG*, RE-PEAT produces a set of outputs per elevation model: sub-KHG units, a water balance and dry-season supply deficit, a ranked list of sub-KHG, and a plan of canal blocks with its water need, budget and print layouts. The full chain has been applied to 14 KHG: five on three elevation models each and nine on corrected DeltaDTM and DEMNAS, 33 analyses in all (chapter 10). The 14 are eleven of the 12 main KHG, two reserve KHG and the earlier test site; the twelfth main KHG, Cawang-Lalang, awaits confirmation with KLH.

The main findings are:

- Terrain is the weakest input. No open elevation model met the accuracy needed on flat peat domes; the best, corrected DeltaDTM, still errs by 0.47 to 0.64 m over 1 km, which is more than the real relief (chapter 4). Results that depend on slope, above all the number of canal blocks, change several-fold between elevation models (chapters 7 and 9): 2.6 to 7.0 times at the five KHG with LiDAR, and DEMNAS gives 1.6 to 4.2 times the DeltaDTM count at the nine without (chapter 10). The chain therefore runs once per elevation model, and the spread between runs is part of the result.
- Sub-KHG boundaries are set mainly by the mapped canals and rivers. With secondary canals as outlets, units agree about as well across terrain sources as across noisy copies of the LiDAR (chapter 5).
- The national ranking follows later fire well (AUC 0.956 to 0.973 on 2023-2025), and 10 of the 11 resolved main KHG are in its top third. It uses default weights proposed by the project for agreement with KLH and the World Bank, which can be adjusted in the dashboard (chapter 6).
- In managed concessions, water management holds the water table up where rain alone would not. At Sugihan-Lumpur the stations fell 11 cm while the climate removed 307 mm in the 2026 dry season, which implies about 290 mm, 1.8 billion m³, supplied from outside the rain balance (chapter 8).
- The 2026 dry-season supply deficit differs widely between KHG: 7 mm at Kampar-Gaung, 119 mm at Mendahara-Batanghari, 132 mm at Pungurbesar-Kapuas, 211 mm at Air Hitam Laut-Buntu Kecil, 290 mm at Sugihan-Lumpur, 299 mm at Kapuas-Barito and 348 mm at Kahayan-Sebangau, the last from one station. It is 0 mm at Pulau Padang, Pulau Bengkalis and Pulau Tebing Tinggi, where rain exceeded evapotranspiration (chapter 10).
- Open climate data give a reliable calendar of dry months per KHG, but separate sub-KHG reliably in only 2 of 12 runs at the four KHG where this was tested (chapter 8).
- The groundwater model, which is in development, reproduces the supply in managed land when that land is held at 0.4 m, and shows canal blocks acting within about 350 m of a blocked reach. For land outside licences the only test is 6 community stations in one KHG: on their screened record and the 100 m grid, canals at the levels measured in LiDAR reproduce the stations' level and fall (chapter 8).

## 11.2 How the outputs serve the KLH focus group discussion

The KLH/BPLH discussion of 2 November 2026 on fire prevention through KHG water governance asks for four things (KLH/BPLH 2026). Table 11.1 shows what the toolkit offers for each and where it stops.

Table: Questions of the KLH/BPLH focus group discussion and the toolkit outputs that address them. Source: terms of reference of the discussion (KLH/BPLH 2026) and chapters 3 to 9 of this report.
| Question of the discussion | What the toolkit provides | Not covered |
|---|---|---|
| Current condition and fire risk of the priority KHG | National ranking of 865 KHG on burned peat, hotspots 2012-2025, this year's KLH hotspots and canals by class; profile and map per KHG; SiTMAT water-table summary per KHG (chapters 3 and 6) | Climate projections; the list of 337 priority KHG, which was not available to the project |
| Factors that make peat vulnerable | Canal density by class, missing canal blocks, distance to water, water balance and dry months, station water tables, land status overlays (licences, peat function, forest area) per KHG and sub-KHG (chapters 6 to 8) | Institutional and governance factors |
| Roles of ministries and agencies | Blocks are placed on primary and secondary canals, the canals the discussion links to the Ministry of Public Works; overlays separate forest area, licence areas and land outside them (chapters 6 and 9) | Assignment of roles itself |
| A KHG-based action plan: locations, interventions, timing, funding | Ranked sub-KHG, proposed canal blocks per sub-KHG with the water they hold, water need from the deficit, budget range with price sources, dry-season months per KHG, print layouts in the KLH style (chapters 7 to 9) | Prices are unverified; canal closure has no price; pumping has not yet been applied to a real KHG |

Water sharing between licence holders and the communities around them, which the discussion names, needs two kinds of data the project does not have: canal water levels in concessions and water-table records in land outside licences. Section 11.5 lists them.

## 11.3 Limits that apply across the report

- The rankings rest on default weights. The order of KHG and sub-KHG may change once KLH and the World Bank agree the weights.
- The burned-area polygons carry the largest weight in both rankings and are the validation target, but their provider and method are not documented, so their accuracy cannot be stated.
- SiTMAT covers one season, April to October 2026, mostly in concessions. Four of the 14 KHG (Saleh-Sugihan, Mempawah-Peniti, Balangan-Batangalai, Buru Mappi-Buru Obaa) have no station inside them, so no station-based deficit can be computed for them. The deficit of Kahayan-Sebangau rests on one station, that of Pungurbesar-Kapuas on three and that of Kapuas-Barito on six.
- Peat depth covers part of most KHG, and where it can be checked it agrees poorly with field cores (correlation 0.10 at Pulau Tebing Tinggi). Kahayan-Sebangau, Kapuas-Barito and Buru Mappi-Buru Obaa have no modelled peat-depth layer, so peat depth is not scored in their sub-KHG ranking.
- LiDAR is used at five KHG, all in Sumatra. At Saleh-Sugihan it covers about 62 % of the KHG, and the LiDAR results there describe only that part. The other nine KHG rest on corrected DeltaDTM and DEMNAS, so their block counts are ranges between the two results, not design figures. Pulau Padang has a 2 m LiDAR that the analysis leaves out.
- Interventions budgets use proposed unit prices that are still to be verified; the KLH cost standard for rewetting works was not available to the project.
- Pumping was not assessed in any of the 33 analyses.
- The groundwater model is in development; its scenario maps are indicative.

## 11.4 Decisions needed from KLH and the World Bank

1. The weights of the national and sub-KHG rankings, for example set in a pairwise-comparison session with the project team, with the held-out validation as a check.
2. Whether peat depth keeps its weight in the sub-KHG ranking where it covers only part of the KHG (chapter 7).
3. Confirmation of the twelfth KHG, Cawang-Lalang, whose name does not match the official boundary file (nearest match KHG Air Banyuasin - Air Lalang).
4. Whether FABDEM, under its non-commercial licence, may be used in a KLH deliverable (chapter 4).
5. How the groundwater model represents water management in concessions (a target water table, or a supply sized from the station deficit), and what field evidence it is checked against (chapter 8).
6. Whether the KLH cost standard can replace the price register and treatment thresholds of RE-PEAT Interventions (chapter 9).

## 11.5 Data needed

- Water-table stations in land outside licences, recording through a full dry season, in several KHG.
- Canal water levels in concessions and community land, by season.
- LiDAR, or an equally accurate terrain model, for the KHG where block design and scenarios are wanted; GNSS heights for canal levels and block crests.
- The source and method of the burned-area layer.
- A river layer that records which rivers keep water in the dry season, so that pumping can be planned.
- The KLH list of 337 priority KHG and the official DMPG village list, to compare with the national ranking and the overlays.

## 11.6 Next steps

- Confirm Cawang-Lalang with KLH and apply the chain to it.
- Obtain LiDAR, or an equally accurate terrain model, and water-table stations for the KHG outside Sumatra, starting with those that rank highest (Pungurbesar-Kapuas, Balangan-Batangalai, Kahayan-Sebangau), so that block counts there stop depending on a range between DeltaDTM and DEMNAS.
- Add stations at Saleh-Sugihan, Mempawah-Peniti, Balangan-Batangalai and Buru Mappi-Buru Obaa, and more than one at Kahayan-Sebangau, so that a deficit can be computed or confirmed.
- Compare the delineation of Kahayan-Sebangau with the 16 sub-KHG of the 2021 study.
- Check the block counts in the field at the KHG where a design is planned, at least one KHG per elevation-model group.
- Assess pumping with RE-PEAT Interventions at the KHG with a deficit, starting with those that have stations.
- Run the groundwater model at further KHG beyond those of chapter 8, on a baseline that matches the canal level of RE-PEAT Interventions, and test it against stations outside licences as soon as they exist.
- Test a trend correction of DeltaDTM with ICESat-2, and the KLHK modelled DTM away from the LiDAR footprints.
- Measure LiDAR coverage against the whole KHG, so that a LiDAR covering only part of a KHG is flagged before its results are used.
