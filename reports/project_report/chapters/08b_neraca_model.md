## 8.6 Why a groundwater model

The rewetting programme needs to know which peat stays deeper than 40 cm through the dry season if *sekat kanal* (canal blocks) are built on given reaches, or if water is pumped onto given units, and how much water that takes. The adopted *neraca air* cannot answer either question. It has two outputs: a monthly climatic balance per *sub-KHG* and a station-based supply deficit for the whole *KHG*.

The climatic balance has no stored water, no canal level and no blocks, so an intervention has nothing to act on. The deficit is a mass balance on observed water tables (*TMA*) and has no spatial form. A what-if question needs three things the adopted method lacks: a water table in every place, a way for canals to drain or supply the peat, and a way for a block or a pump to change that exchange. The two-dimensional groundwater-flow equation, with canals as boundary conditions, provides all three. Every model in the review below that simulated canal blocking on tropical peat has this structure.

The groundwater model described in this chapter is in development. It can be applied to any KHG from its code, takes its climate forcing from satellite products and scores itself against field data. It has passed the supply check where that check can be made. It has not passed the checks on water-table level and dynamics outside managed land, and its scenario results are first results for one KHG.

## 8.7 Review of existing models

The review looked for models that have simulated canal blocks or water-table management on tropical *gambut* (peat), and asked what each would need to run on an Indonesian KHG. Its main result for the project is that the choice of equation matters less than two inputs: the transmissivity of tropical peat and a canal level that responds to blocks. The table summarises the review. "Not stated" means the review did not record the item.

Table: Groundwater and peat-hydrology models considered for rewetting scenarios. Source: RE-PEAT review of groundwater models (October 2026), with the literature notes on tropical peat parameters.

| Model | Dimension and form | Canals, blocks, pumps | Data needs | Use on tropical peat | Licence, availability | Decision |
|---|---|---|---|---|---|---|
| Urzainki et al. 2020 | 2D Boussinesq, 100 m grid | canal fixed 1.2 m below the land; a block lifts upstream canal cells to a set level; no pump | DTM, canal map, peat depth, peat hydraulic table | no quantitative validation, as the authors state | open source (MIT) | form adopted; its fixed canal rule failed in our earlier runs |
| Urzainki et al. 2023, Merang-Kepayang, 22,000 ha, 168 blocks | 2D peat (triangular mesh) coupled to a 1D canal network | canal stage is a state; a weir equation per block; no pump | canal network with bed and width | qualitative only: microtopography prevented a one-to-one comparison with 141 dipwells | open source (MIT) | its tropical peat parameters adopted; canal network deferred |
| MIKE SHE with MIKE Hydro River (Kurnianto et al. 2026), Pulau Padang | 3D/2D, 100 m, about 113,000 cells, 3 peat layers, tide boundary | 123 dams as broad-crested weirs; dynamic canal stage; no pump in the text | layered peat conductivity, tide, canal network | 15 wells, 2018: RMSE 0.05-0.09 m, NSE 0.36-0.87 | commercial (DHI) | not chosen: commercial, closed source |
| SIMGRO (Jaenicke et al. 2010), Sebangau | quasi-3D finite element with channels | dams along canals; no pump | not stated | one dipwell: R² 0.74 | legacy | not chosen |
| MODFLOW via FREEWAT (Suryadi et al. 2021), Kahayan-Sebangau | 2D grid | block heights 0.2-0.6 m at canal spacing 200-400 m; a well term exists, not used | not stated | NSE 0.73-0.95 near one canal, 30-day calibration | open | deferred (see below) |
| DigiBog_Hydro (Putra et al. 2022) | 2.5D Boussinesq, 1 m grid, synthetic 0.2 km² | a dam as two fixed ditch levels; no pump | not stated | scenario study, no validation | open source (GPL-3.0) | not chosen: 1 m grid only |
| PEATCLSM-Trop (Apers et al. 2022) | 1D per 9 km cell | static ditch depth 0.68 m, spacing 31.4 m; no network, no blocks | not stated | water-level anomaly R 0.68, drained peat in Southeast Asia | part of a NASA land surface model | not chosen: 1D, no maps |
| SWAP (Taufik et al. 2019), South Sumatra | per site, canals as a lateral drainage flux | canal level set by season (not deeper than 1.3 m below the surface dry, 0.5 m wet) | canal level, drainage resistance | water table deeper than 85 cm 34% of the time with canal drainage, 1.9% without | not stated | not chosen; it confirms that the canal level decides the water table |
| DRAINMOD (Imanudin et al. 2018), oil palm on peat | 1D field between parallel drains | outlet level; no pump | not stated | on peat under oil palm, water table down to 90 cm, and 30-40 cm with tertiary channels held at 70 cm | licence not confirmed | not chosen: 1D, no maps |
| MONALAGA, Universitas Riau | not documented online | the product page lists canal-blocking scenarios | not stated | not published | not public | not available |
| MPeat2D (Mahdiyasa et al. 2024) | 2D bog development over about 5,000 years | none | not stated | none | not stated | not relevant |

MONALAGA ("Model Neraca Air Lahan Gambut") was applied to KHG Pulau Tebing Tinggi in 2020, according to the university's product page. The same group's published peat balances are monthly balances per sub-KHG with no water table or canal level. Whether MONALAGA is that balance could not be confirmed, and its report was not available to the project.

The review led to four conclusions for the RE-PEAT model:

- The equation did not cause the failure of the project's earlier runs. Urzainki et al. (2023) and DigiBog solve the same 2D Boussinesq equation, and MIKE SHE, SIMGRO and MODFLOW solve the same Darcy flow. Two inputs separated those models from the earlier runs: transmissivity, and a canal level that responds to blocks.
- Tropical transmissivity is 100 to 1,000 times the boreal table the earlier runs used. The boreal table gave 0.59 m²/day at the surface. Urzainki et al. (2023) use 50 or 500 m²/day; Jaenicke et al. (2010) used 30 m²/day in the top metre.
- Urzainki et al. (2020) and Kurnianto et al. (2026) used a 100 m grid. Block effects fade within a few hundred metres, so the 500 m grid of the earlier runs was too coarse.
- None of the tropical studies reviewed models a pump. A pump needs a new term in the model.

The review also gave the expected size of a block effect, against which any run can be checked. Kurnianto et al. (2026) found the drainage effect on the adjacent forest averaged 9 cm at 100 m from a dammed canal and fell below 5 cm by about 300 m. Urzainki et al. (2023) found a mean rise of 1.44 cm in a dry year and 1.57 cm in a wet year over their 22,000 ha study area, part of a 140,000 ha dome. Field reports from Tebing Tinggi give rewetting up to about 400 m upstream of a block (Sutikno et al. 2023).

MODFLOW 6 was considered as the computing engine and deferred. It would bring a standard, peer-recognised code with a water budget per boundary, canal packages, a pump term and a Newton solver. Its costs are layering thin unconfined peat into about 8 to 10 layers to follow transmissivity falling with depth, and a separate compiled program that users of the RE-PEAT Interventions desktop tool would have to install. The deciding reason was that MODFLOW faces the same open questions as the RE-PEAT solver: the canal level in managed land, the specific yield of the peat, and the data the model is tested against. A different engine answers none of them. MODFLOW remains the fallback if a full canal network is needed.

## 8.8 The model

### Equation and grid

The model solves the two-dimensional nonlinear Boussinesq equation for the water table in the peat:

Sy(z) dh/dt = div( T(z) grad h ) + R

Here h is the water-table elevation, z its depth below the land surface (negative downwards), Sy the specific yield (the water released per metre of fall), T the transmissivity of the saturated peat below the water table, and R the net recharge, rain minus evapotranspiration, in metres per day. In words: each day the water table in a cell rises with rain, falls with evapotranspiration, and exchanges water with its neighbours in proportion to the slope of the water table and the ease with which water moves through the peat. Ponded water is removed each day; runoff in tropical peat is saturation-excess (Katimon et al. 2013).

The KHG is divided into square cells of 100 m or 200 m on a metric grid. The model advances one day at a time with an implicit scheme and iterates within each day for the nonlinearity. RE-PEAT Interventions uses the same solver for its block optimisation, so both tools share one water model. A simulation starts with the peat saturated at the start of a wet season (1 November 2025 for the 2026 simulations) and spins up for several months before the dry season it reports.

### Peat hydraulic properties

Specific yield and transmissivity both fall with depth. The working parameter sets are the tropical sets of Urzainki et al. (2023), calibrated at the Merang-Kepayang dome in South Sumatra:

- specific yield 0.6 at the surface, falling exponentially with depth;
- transmissivity 50 m²/day ("small") or 500 m²/day ("large") at the surface, falling by a factor e for every 0.4 m of depth, down to the peat base.

These values were calibrated at one site and were not measured. The surface specific yield of 0.6 fits intact forest with the water table near the surface. Measurements in drained peat point to 0.1 to 0.3: Ismail et al. (2021) report up to 0.3 near the surface and 0.1 at 1.5 m depth at Pulau Padang, and Kurnianto et al. (2026) calibrated 0.10 to 0.15. Cobb and Harvey (2019) give about 0.29 near the surface in Brunei, a value on a curve fitted to their data. A third set, labelled "drained", takes its specific yield from Ismail et al. (2021): an exponential through their two values (0.3 at the surface, 0.1 at 1.5 m), fitted by the RE-PEAT team because the paper gives no coefficients. Its transmissivity is the large tropical set. The boreal table of the earlier runs is kept only as a reference for the known failure. No parameter is fitted to the stations.

Peat depth comes from the KHG's modelled peat-depth map. Where that map is empty, the BBSDLP 1:50,000 peat-depth classes fill the gap (class midpoints, 8 m for the deepest class), and then the KHG median. With the tropical sets, transmissivity below 2 m is small whatever the depth, so a weak depth map matters less for flow than it would for storage.

### Boundaries

The model treats the following as fixed or held water levels:

- The KHG edge, held 0.3 m below the local surface (a river rule).
- Canals by class (primary, secondary, tertiary), each held at a set depth below the local surface: 1.2 m in the base simulations, with 0.6 m and 0.4 m as alternatives, and the levels measured in the Pulau Padang LiDAR (primary 0.8 m, secondary and tertiary 0.3 m). A class can also be left free. Two variants change how canals act. In the first, canals narrower than a cell exchange water with the cell instead of holding the whole cell at the canal level. In the second, a canal water balance per *sub-KHG* lets the canal level fall in the dry season, with the class levels as the outlet sill.
- Managed land. Plantation licences (forest plantation and oil palm, from the 2025 licence layer) are held at a target water table. Their canals are fixed at the target, and each day any managed cell that fell below the target is brought back to it. The water this takes is the model's water-management supply. Holding managed land is optional; results that use it say so, and hold the land at 0.4 m, the compliance level of PP 57/2016. An alternative gives each licence the median level of the concession stations outside it.
- Canal blocks. RE-PEAT Interventions places blocks and gives each block's reach, the canal stretch it holds water in, with the water depth below the land. A block scenario fixes the canal cells of each reach at that depth. Where a reach falls on a canal cell that is already fixed, by its class or by managed land, the higher water level is kept, so a block never lowers a canal.
- Pumped land. The sub-KHG units that RE-PEAT Interventions marks for water supply are held at 0.4 m, like managed land, and the water this takes is the pumping need. Where managed and pumped land overlap, the shallower target applies.

{{diagram: neraca_model_boundaries | Boundaries of the groundwater model and how a scenario changes them (model in development) | Centre box: free peat cells (2D Boussinesq: rain minus ET in, lateral flow between cells). Around it, arrows into and out of the free cells from: KHG edge (held 0.3 m below the surface); canals by class (primary, secondary, tertiary, each held at a set depth, 1.2 m in the base runs); managed land in plantation licences (canals and cells held at the 0.4 m target, PP 57/2016; output: water-management supply). A second row "scenario inputs from RE-PEAT Interventions" with two boxes: block reaches (canal cells of each reach fixed at the reach water depth; higher of block and managed level kept) and land marked for water supply (held at 0.4 m; output: pumping need). Outputs box at the right: daily KHG series, season maps (days deeper than 40 cm, mean depth, supply), table per sub-KHG, scores against stations. A side note on the peat base: no ET below the peat.}}

In simulations that hold managed land, the model also stops evapotranspiration from a cell whose water table has fallen below the peat base. The model has no infiltration limit for burned land: the review of burned-peat hydrology found no established drop in infiltration after fire on tropical peat (Setiawan et al. 2020). The effects that are supported, a lower surface after fire (Konecny et al. 2016) and lower evapotranspiration on burned land (Hirano et al. 2015), are already captured by a post-fire LiDAR DTM or would need evapotranspiration per cell.

### Forcing and inputs

Rain is CHIRPS and evapotranspiration is MOD16, both as KHG means per dekad, spread evenly over the days of the dekad and extracted with Google Earth Engine. For 2026, MOD16 without gap filling is used, because the gap-filled product ends in December 2025. The DTM is the LiDAR DTM where it exists, otherwise the corrected DeltaDTM or DEMNAS. Each simulation records every input, its source and the share of the KHG it covers.

### Outputs

The model computes the water-table depth of every cell every day. Each simulation produces:

- a daily KHG series: mean depth, share of the area deeper than 40 cm, rain, evapotranspiration, the water exchanged between the peat and the canals and edge, and the water supplied to managed land;
- season maps for June to September (122 days): the days each cell of open land was deeper than 40 cm, the mean depth, and the water supplied to each managed cell;
- a table per sub-KHG: open and managed area, the open land's mean depth and days deeper than 40 cm, the share of open land deeper than 40 cm for more than half the season, and the water supplied to managed land;
- scores against stations or field points.

Open land is land not held by water management or pumping. A sub-KHG "still needs rewetting" when more than half of its open land is deeper than 40 cm for more than half the season.

## 8.9 Design choices

The table lists the main design choices of the model, with the reason for each and the evidence behind it.

Table: Design choices of the groundwater model. Source: RE-PEAT groundwater model report, October 2026.

| Design choice | Reason | Evidence |
|---|---|---|
| The scenario model is part of the water-balance tool, as a separate component | one water model for the project; the tool already holds the solver and peat tables | project decision |
| The groundwater model becomes the neraca air once it passes a field check; the climatic balance stays as the fallback | scenarios need a water table and a canal mechanism; LiDAR covers few KHG, and open DEM errors are of the order of a dome's relief | review; project decision |
| One solver, shared with RE-PEAT Interventions | the solver existed twice, identical; users of the desktop tool need a simple installation | installation tested |
| Groundwater components consolidated without changing existing results | three methods were mixed together | 74 of 74 established outputs identical after the change |
| 2D nonlinear Boussinesq on a regular grid, implicit with iteration | open, tested and shared between tools; the models that simulated blocks solve the same flow | review (section 8.7) |
| Peat: the tropical sets of Urzainki et al. (2023); boreal table kept as the known failure; nothing fitted | tropical transmissivity is 100-1,000 times the boreal table | measured surface Sy (0.29-0.3) is about half the 0.6 used, recorded as an open question |
| Canals: a fixed level per class first; a canal network later | tests transmissivity before the canal mechanism changes, so the two effects are not confused | earlier failed runs |
| Forcing: CHIRPS and MOD16, KHG mean, per dekad | the same products as the climatic balance | adopted balance |
| DTM: corrected surface where it exists; raw DeltaDTM where not, stated with the result | DeltaDTM is a bare-earth product; Tebing Tinggi has no LiDAR | DEMNAS 1.86 m above the survey elevations at Tebing Tinggi |
| Domain: the whole KHG; gaps in peat depth filled | neither peat mask separated peat from mineral survey points | field-input check at Tebing Tinggi |
| Acceptance criteria fixed before any simulation; two simple predictions scored the same way; no parameter fitted | the criteria must not drift towards whatever a simulation gives; a model that cannot beat distance to canal adds nothing | design principle |
| Every step can be repeated for any KHG from its code, and every reported number is produced by the method | results can be updated with new data and extended to all 865 KHG | design principle |
| Managed land held at a target water table (0.4 m); the water this takes is the water-management supply | in three KHG the stations in managed land stay almost flat through the dry season while the model drained them | section 8.11 |
| For managed-land simulations, stations in managed land are left out; the supply must be within a factor of 2 of the station deficit, or (amended after the Kampar-Gaung results) within 50 mm | holding a target makes managed stations agree by construction; a ratio of two small numbers fails on small differences | Kampar-Gaung deficit 7 mm |
| Inputs from national layers with fallbacks, cell by cell; each simulation lists its inputs and their share | not every KHG has every input | input tables per simulation |
| No ET below the peat base; existing blocks left for the block scenario | with a low Sy at depth, the water table fell below the peat | 642 cm drawdown at Sugihan-Lumpur where peat is about 1.3 m thick |
| Blocks and pumped land come from RE-PEAT Interventions | one canal network and one set of block positions for both tools; reach depths are relative to the land, so they apply on any DTM | project decision |
| Canals narrower than a cell exchange water with it; canal cells outside managed land are no longer fixed | fixed cells covered up to 40% of the grid at 200 m and made the land up to 19 cm too wet against a 5 m grid; the exchange term is within 0.7 cm | numerical check against a 5 m grid |
| Optional canal water balance per sub-KHG: canal water rises with seepage and rain and leaves by evaporation and through the outlet | no canal level series exists for these KHG | canal widths and beds taken in advance from published plantation surveys |
| Station records screened for restarts after gaps, settling days and stuck loggers | SiTMAT quality control passes these; one community result rested on them | 17% of concession and 23% of community readings left out nationally |
| Recommended set-up: canals inside cells at the LiDAR levels, no canal water balance, scores on the screened record | best match to the screened community record; the canal water balance overshoots and rests on an unmeasured outlet constant | comparison of canal settings (section 8.11) |

## 8.10 How the model is judged

The acceptance criteria were fixed before the simulations they judge, so they cannot drift towards a result. A model is compared with two simple predictions scored the same way:

- the constant prediction: the median observed depth everywhere;
- the distance prediction: observed depth regressed on the logarithm of distance to the nearest canal, fitted to the same points. It is fitted in-sample, so it is favoured.

The field check on water-table levels passes when the model's Spearman rank correlation across points is at least 0.3 and above that of the distance prediction, and its RMSE is below that of the constant prediction. Simulations scored against stations add a check on timing: the median correlation of each station's daily series with the model must be at least 0.5. A station counts only with at least 30 days of record, and the level checks need at least 8 stations.

Simulations with managed land held at a target add a supply check: the water the model supplies to managed land from June to early October must be within a factor of 2 of the station-based deficit. This criterion was fixed before the first managed-land simulation. After the Kampar-Gaung results it was amended to also pass when the two are within 50 mm, about two weeks of dry-season evapotranspiration. Kampar-Gaung had a near-neutral dry season and a deficit of 7 mm, and a ratio of two small numbers fails on small absolute differences. The amendment turned the Kampar-Gaung result with the large tropical set from fail to pass; the change and its reason are documented in the model report.

Three rules decide which data a check uses:

- A check with too few data is "not testable", which is different from "fail". A simulation passes when every check that could be made passed.
- A station on a canal or edge cell shows only the imposed canal level and is left out of the level and dynamics scores.
- A station inside land held at a target shows only the target, and is left out too. With managed land held, the independent tests are therefore the stations outside managed land, and the supply.

## 8.11 Test sites and evidence

The evidence so far shows that water management controls the dry-season water table in plantation land, and that the canal level outside licences controls it in open land. Holding plantations at a target reproduces the observed supply deficit where the dry season was dry. Outside licences the model matches the few community stations only with shallow canal levels and on the screened record.

### Pulau Tebing Tinggi: a field survey that cannot test the pattern

The first test used the 2015 field survey of Pulau Tebing Tinggi: 1,385 points, 1,132 on peat. Of the peat points, 329 have a water table of 0. The zeros cluster by field team (up to 91% of one team's points) and in mangrove (91%), and the ponding column is 0 everywhere, so they were treated as missing. After flagging implausible depths, 528 points were scored on the 200 m grid. The KHG has no LiDAR, so the simulation used DeltaDTM, which agrees with the survey elevations at r 0.91 and sits a median 0.37 m lower.

All six configurations (three peat sets, canals at 0.6 m and 1.2 m) fail the check. The Spearman correlation is 0.01 to 0.05 and the model is 48 to 71 cm shallower than the readings. The constant prediction has an RMSE of 40 cm; the model's is 67 to 81 cm. A 100 m simulation gives the same result (Spearman -0.01, 584 points).

The survey itself cannot test a spatial pattern. Its depths follow neither distance to canal (Spearman 0.00) nor recorded peat thickness (0.02). Between field teams that worked the same 2 km block, the team accounts for 76% of the variance (258 points), and this does not follow visit timing: across 25 teams the Spearman of a team's median depth with its median last-rain date is 0.13. A model that matched the true water table would still score near zero against these readings, so the failure says nothing about the model's spatial skill, in either direction.

### Choosing sites with stations

The SiTMAT stations were ranked by KHG. Of 1,181 stations in 178 KHG, a station counted as good with at least 120 unflagged days (concession) or 45 days (community, whose records start later). Three KHG with LiDAR and sub-KHG units were chosen.

Table: KHG used to test the groundwater model against SiTMAT stations, 2026. Source: SiTMAT station ranking for the groundwater model.

| KHG | Good concession stations | Good community stations | Station level spread (cm) | Median drawdown of good stations, June to September 2026 (cm) | Why chosen |
|---|---|---|---|---|---|
| Kampar-Gaung | 78 | 0 | 11.0 | 7.0 | most stations; more spread of levels than Sugihan-Lumpur |
| Sugihan-Lumpur | 51 | 0 | 3.1 | 11.0 | selected KHG; earlier work |
| Mendahara-Batanghari | 12 | 9 | 12.7 | 1.0 | the only KHG with at least 5 concession and 3 community stations |

All simulations use the LiDAR DTM, CHIRPS and MOD16 without gap filling, from 1 November 2025 (saturated) to 30 September 2026.

### Sugihan-Lumpur: right timing, wrong amplitude

With canals fixed 1.2 m below the surface, the model gets the timing of the stations right and the size of the dry-season fall wrong. Of the 51 stations, 18 sit on canal or edge cells and 33 are scored. The median per-station correlation is 0.87 and the mean curve of the 33 stations correlates at 0.94 with the model. The stations fall a median 12 cm over the record; the model falls 126 cm. The KHG-mean depth at the end of September is 122 cm, while the stations hold about 42 cm. From June to September rain minus evapotranspiration was -376 mm.

Holding the canals at 0.4 m instead brings the mean level to the stations (36.5 cm simulated, 42.3 cm observed) but still leaves a 72 cm fall. Canals at a fixed level supply water only once the peat beside them falls below that level: 14 mm in August and 25 mm in September.

{{figure: model_station_fit_sugihan_lumpur | Observed and simulated water-table depth at the SiTMAT stations of Sugihan-Lumpur, November 2025 to September 2026 (model in development) | Line chart, depth in cm positive down, y axis reversed. Three lines: the daily mean over the 33 stations not on a canal or edge cell, observed; the same stations simulated with canals 1.2 m below the surface; and simulated with canals 0.4 m below the surface. Observed: _khg/16.02.01_sugihan_lumpur/03_neraca/inputs/stations_daily.csv (date, station_id, depth_cm). Simulated: station_sim_daily.csv (date, one column per station_id, cm) in _khg/16.02.01_sugihan_lumpur/03_neraca/lidar/runs/model/tropical-large_p1.2_s1.2_t1.2_e0.3_200m/ and .../tropical-large_p0.4_s0.4_t0.4_e0.3_200m/. Keep stations whose flag is empty in each run's station_scores.csv (drop flag on_fixed_cell). Plot from 2026-04-01, the first observed day. Optional thin lines: rain minus ET per day from model_series.csv (P_mm, ET_mm) of the 1.2 m run on a second panel.}}

### Three KHG: the stations in managed land stay flat

Across the three KHG the stations in managed land barely move through the dry season, and the model drains in every configuration with fixed canals.

Table: Model results against SiTMAT stations, 2026, canals fixed per simulation (no managed target). Source: summary of groundwater model simulations scored against SiTMAT stations.

| KHG | Peat set | Canal level (m) | Stations scored | Spearman, model / distance | Bias (cm) | RMSE, model / constant (cm) | Median station r | Drawdown observed / simulated (cm) |
|---|---|---|---|---|---|---|---|---|
| Sugihan-Lumpur | tropical large | 1.2 | 33 | -0.21 / 0.15 | +34 | 37 / 4 | 0.87 | 12 / 126 |
| Sugihan-Lumpur | tropical large | 0.4 | 33 | -0.24 / 0.15 | -6 | 11 / 4 | 0.90 | 12 / 72 |
| Sugihan-Lumpur | drained (Ismail Sy) | 1.2 | 33 | -0.25 / 0.15 | +144 | 145 / 4 | 0.77 | 12 / 642 |
| Sugihan-Lumpur | drained (Ismail Sy) | 0.4 | 33 | -0.33 / 0.15 | +12 | 15 / 4 | 0.90 | 12 / 108 |
| Kampar-Gaung | tropical large | 1.2 | 55 | 0.05 / 0.34 | +3 | 19 / 12 | 0.65 | 1 / 31 |
| Kampar-Gaung | tropical large | 0.4 | 55 | 0.03 / 0.34 | -23 | 27 / 12 | 0.65 | 1 / 19 |
| Kampar-Gaung | drained (Ismail Sy) | 1.2 | 55 | 0.10 / 0.34 | +17 | 28 / 12 | 0.67 | 1 / 82 |
| Kampar-Gaung | drained (Ismail Sy) | 0.4 | 55 | 0.21 / 0.34 | -17 | 21 / 12 | 0.63 | 1 / 33 |
| Mendahara-Batanghari (100 m) | tropical large | 1.2 | 15 | -0.32 / 0.17 | +45 | 60 / 11 | 0.38 | 21 / 64 |
| Mendahara-Batanghari (100 m) | tropical large | 1.2, plantations 0.4 | 15 | -0.09 / 0.17 | +23 | 48 / 11 | 0.38 | 21 / 40 |

Every simulation in the table fails the check, and three findings come out of it:

- Station levels in managed land differ little. At Sugihan-Lumpur the constant prediction is within 4 cm RMSE, so a Spearman across stations measures almost nothing. Kampar-Gaung has more spread, and there distance to canal (0.34) beats every model configuration.
- The measured lower specific yield of drained peat (Ismail et al. 2021) makes every fall larger. With canals at 1.2 m the water table at the Sugihan-Lumpur stations fell a median 642 cm, far below the peat itself (about 1.3 m thick). That led to the rule that no evapotranspiration is taken below the peat base.
- Evapotranspiration that falls as the water table deepens, with the natural-peat thresholds of Apers et al. (2022), changed nothing at Sugihan-Lumpur with canals at 0.4 m: the model reached the first threshold only at the end of September.

At Mendahara-Batanghari the stations split by kind. The 9 concession stations (8 inside plantation licences) sit at 37 cm and fall 6 cm through the dry season; the model with plantation canals at 0.4 m puts them at 28 cm and lets them fall 52 cm. The 6 community stations off canal cells sit at 29 cm and fall 63 cm; the model puts them at 95 cm with a 38 cm fall. The flatness belongs to managed land. What the model lacks is the water supplied to managed land by canal operation, gates or pumping, which exceeds what seepage from a fixed canal level gives.

### Managed land held at a target

Holding plantation licences at 0.4 m gives a supply of the right size where the dry season was dry.

Table: Water supplied to managed land, June to early October 2026, against the station-based deficit. Source: summary of groundwater model simulations scored against SiTMAT stations.

| KHG | Managed share of the KHG | Peat set | Target | Model supply (mm) | Station deficit (mm) | Stations outside managed land | Result |
|---|---|---|---|---|---|---|---|
| Sugihan-Lumpur | 77% | tropical large | 0.4 m | 244 | 290 | 0 | pass (supply only) |
| Sugihan-Lumpur | 77% | tropical large | station median per licence | 233 | 290 | 0 | pass (supply only) |
| Sugihan-Lumpur | 77% | drained (Ismail Sy) | 0.4 m | 324 | 290 | 0 | pass (supply only) |
| Kampar-Gaung | 44% | tropical large | 0.4 m | 42 | 7 | 0 | pass (supply only, within 50 mm) |
| Kampar-Gaung | 44% | tropical large | station median per licence | 41 | 7 | 0 | pass (supply only, within 50 mm) |
| Kampar-Gaung | 44% | drained (Ismail Sy) | 0.4 m | 104 | 7 | 0 | fail (supply) |
| Mendahara-Batanghari | 22% | tropical large | 0.4 m | 194 | 119 | 7 | fail (dynamics) |
| Mendahara-Batanghari | 22% | tropical large | station median per licence | 209 | 119 | 7 | fail (dynamics) |
| Mendahara-Batanghari | 22% | drained (Ismail Sy) | 0.4 m | 250 | 119 | 7 | fail |
| Mendahara-Batanghari, canals outside licences 0.6 m | 22% | tropical large | 0.4 m | 181 | 119 | 7 | fail (dynamics) |

At Sugihan-Lumpur the supply that holding the plantations takes (233 to 324 mm) is close to the 290 mm the stations imply. At Mendahara-Batanghari it is within a factor of 2. The targets taken from other concessions' stations at Sugihan-Lumpur (0.43 to 0.44 m) are close to the regulatory 0.4 m. At Sugihan-Lumpur and Kampar-Gaung every station off a canal cell lies inside a licence, so these two sites test only the supply.

Land outside licences is the weak part. Mendahara-Batanghari's 6 community stations, off canal cells, are the only independent test of levels there. They sit at 29 cm and fall 63 cm. The model gives 95 cm and a 38 cm fall with the large tropical set, and 165 cm and 99 cm with the Ismail specific yield. The median station correlation is 0.38, below the 0.5 criterion. With canals outside licences at 0.6 m instead of 1.2 m, the community stations come out at 66 cm with a 23 cm fall, and the mean of the 7 stations outside licences matches (37 cm simulated, 36 cm observed). A shallower canal corrects the level of unmanaged land; its swing stays too small. The 6 stations start in late July 2026 and cover only the falling limb, which limits what they can test.

### The managed-land target

The concession stations follow the 40 cm rule, so they show compliance with the regulation more than the water table that management actually holds. Across 1,157 SiTMAT concession stations, readings at -40 cm outnumber readings at -41 cm by 2.5 to 1; community stations show no such step. Published plantation water tables are deeper: about 70 cm under Acacia (Evans et al. 2019; Hooijer et al. 2012), and canal water about 0.6 m below oil palm and 0.85 m below Acacia above 5 m elevation (Vernimmen and Hooijer 2026). The 0.4 m target is therefore treated as a scenario setting with a band of 0.4, 0.6 and 0.8 m.

Table: Effect of the managed-land target and of the canal level outside licences, June to September 2026 (model in development). Source: groundwater model simulations, managed-target band.

| KHG | Canals outside licences | Target | Open land: days deeper than 40 cm (of 122) | Supply to managed land (mm) |
|---|---|---|---|---|
| Sugihan-Lumpur | 1.2 m | 0.4 m | 68 | 244 |
| Sugihan-Lumpur | LiDAR levels | 0.4 / 0.6 / 0.8 m | 56 / 56 / 56 | 243 / 149 / 103 |
| Kampar-Gaung | 1.2 m | 0.4 m | 24 | 42 |
| Kampar-Gaung | LiDAR levels | 0.4 / 0.6 / 0.8 m | 5 / 5 / 5 | 40 / 16 / 8 |
| Mendahara-Batanghari | 1.2 m | 0.4 m | 61 | 194 |
| Mendahara-Batanghari | LiDAR levels | 0.4 / 0.6 / 0.8 m | 41 / 41 / 41 | 172 / 124 / 92 |

The target changes the water supplied to managed land and leaves the open land unchanged. The canal level outside licences sets the open land. The LiDAR levels were measured at Pulau Padang only, on one flight date, and the narrow drains are below the LiDAR pixel size, so their 0.3 m is a shallow bound.

### Canals narrower than a cell, and a canal water balance

Letting canals narrower than a cell exchange water with it, instead of fixing the whole cell, changes the days deeper than 40 cm on the same cells by 0 to 2. The canal water balance lets the canals fall to a season median of 0.41 to 0.55 m below the land at Mendahara-Batanghari and Sugihan-Lumpur, inside the published range, with an outlet time constant of 1 or 0.1 day; neither value has been measured.

### Outliers in the station record

SiTMAT's quality control flags single spikes and passes loggers that restart after a gap at a shifted level and loggers stuck at one value. A screening rule for these cases, with thresholds set after inspecting the records, leaves out 17% of concession and 23% of community readings nationally. At Mendahara-Batanghari the community stations report 3 days in July, stop for three weeks, and restart about 50 cm above the ground before dropping within a week. Their earlier "fall of 63 cm" comes from these days. On the screened record they sit at 44 cm and fall 11 cm from 19 August to 30 September.

{{figure: model_community_mendahara | Community stations at Mendahara-Batanghari, raw and screened record, against three canal settings, 2026 (model in development) | Line chart, depth in cm positive down, y axis reversed, band above 0 shaded as water above the ground. Daily mean of the 6 community stations off canal cells, on days with at least 5 of them: raw record (thin, markers) and screened record (fieldcheck.screen). Simulated means of the same stations: canals 1.2 m fixed, canals at the LiDAR levels fixed, and the canal water balance (store, tau 1 day). Source: _khg/15.05-07-10.01_mendahara_batanghari/03_neraca/inputs/model/stations_daily.csv and station_sim_daily.csv of the three runs.}}

Table: Community stations at Mendahara-Batanghari, screened record, 19 August to 30 September 2026 (model in development). Source: groundwater model simulations, canal settings.

| Canals outside licences | Level, observed / model (cm) | Fall, observed / model (cm) |
|---|---|---|
| 1.2 m, fixed | 44 / 101 | 11 / 25 |
| LiDAR levels, fixed | 44 / 47 | 11 / 6 |
| LiDAR levels, canals exchanging water with their cells | 44 / 48 | 11 / 9 |
| LiDAR levels, canal water balance | 44 / 56 to 63 | 11 / 24 |

On the screened record and the 100 m grid, canals at the LiDAR levels match the stations' level and fall, and the canal water balance makes them too dry. On the 200 m grid the 4 comparable stations fall 2 cm against about 21 cm in the model, and the station correlation on the screened record is not yet available. These are 6 stations over six weeks in one KHG. The recommended set-up scores the screened record, lets canals exchange water with their cells at the LiDAR levels and leaves the canal water balance off. The station-based deficit of the adopted *neraca air* reads the same records and does not yet apply this screening.

{{figure: model_days_maps_final | Days with the water table deeper than 40 cm, June to September 2026, recommended set-up (model in development) | Three map panels, Sugihan-Lumpur and Kampar-Gaung at 200 m, Mendahara-Batanghari at 100 m; sequential blue, 0 to 122 days; managed land held at 0.4 m in grey. Source: model_season_days_deeper_40cm.tif of tropical-large_p0.8_s0.3_t0.3_mt0.4_lk_scr_e0.3_<res>m_pb_dbbsdlp.}}

With this set-up the open land outside licences is deeper than 40 cm on 49 days on average at Sugihan-Lumpur, 6 at Kampar-Gaung and 40 at Mendahara-Batanghari. At Mendahara-Batanghari the check now passes on levels, on the community stations and on supply, and fails on daily dynamics (median station correlation 0.30 against 0.5).

### Season outputs, and a dry and a wet year

The season outputs per sub-KHG show how much the dry-season water table and the managed-land supply vary inside each KHG, with managed land held at 0.4 m.

Table: Range over sub-KHG units of the June to September 2026 season outputs, managed land held at 0.4 m, large tropical set (model in development). Source: per sub-KHG season tables of the groundwater model simulations.

| KHG | Units | Open land: mean depth (cm) | Open land: days deeper than 40 cm (of 122) | Managed supply (mm) |
|---|---|---|---|---|
| Sugihan-Lumpur (canals outside licences 1.2 m) | 30 | 35 to 97 | 50 to 120 | 181 to 319 |
| Kampar-Gaung (canals 1.2 m) | 28 | 12 to 45 | 1 to 68 | 13 to 152 |
| Mendahara-Batanghari (canals 0.6 m) | 29 | 23 to 62 | 30 to 105 | 101 to 316 |

Two further simulations at Sugihan-Lumpur used a dry and a wet year chosen from the climatic-balance calendar (6 and 0 deficit months), with gap-filled MOD16.

Table: Sugihan-Lumpur in a dry and a wet year, June to September, managed land held at 0.4 m. Source: groundwater model simulations for 2019 and 2022.

| Year | Rain minus ET (mm) | Water supplied to managed land | Open land at the end of September |
|---|---|---|---|
| 2019 (El Niño) | -285 | 163 mm (480 million m³) | mean depth 79 cm; all deeper than 40 cm |
| 2022 | +602 | 1 mm | mean depth 9 cm; 7% deeper than 40 cm |

The supply follows the dryness of the season and is close to zero in a wet year. No stations cover 2019 or 2022, so these simulations show how the model behaves without testing its skill. Some units stay dry even in the wet year: unit S02 had open land deeper than 40 cm on 96 of 122 days in 2019 and 48 in 2022.

## 8.12 Scenarios at Mendahara-Batanghari

Canal blocks rewet the peat close to the blocked reaches and change little beyond about 350 m, so their effect should be judged by distance from a reach and per sub-KHG. Pumping onto the units marked for water supply adds about 50 million m³ to the water needed in the dry season. These first scenarios show how the interventions act; they do not test the current block plan.

The scenarios ran at Mendahara-Batanghari on the 100 m grid with the LiDAR DTM. They take 160 block reaches and the land marked for water supply from the RE-PEAT Interventions plan of this KHG made on 27 October 2026, before the KLH block spacing was adopted. The current plan, with that spacing, has 150 reaches. The baseline holds plantation licences at 0.4 m. Three scenarios are compared: baseline, blocks, and blocks with pumping. RE-PEAT Interventions marks 8 sub-KHG units for water supply, 29% of the KHG, and pumping holds them at 0.4 m.

The baseline canal level outside licences matters. RE-PEAT Interventions computes the water each block holds from an unblocked canal level 1.0 m below the land, and its reaches hold water at a median 0.59 m below the land. On a baseline with canals already at 0.6 m, most reaches raise nothing, because a block never lowers a canal. The scenarios below use a 1.2 m baseline, which is closer to the 1.0 m of RE-PEAT Interventions without being equal to it; a scenario on a matching baseline has not yet been simulated.

Table: Rewetting scenarios at Mendahara-Batanghari, June to September 2026, canals outside licences 1.2 m below the land (model in development). Source: scenario comparison of the groundwater model, Mendahara-Batanghari.

| Scenario | Open land (km²) | Open land: days deeper than 40 cm (area-weighted, of 122) | Water supplied in the season, all held land (million m³) | Sub-KHG still needing rewetting |
|---|---|---|---|---|
| Baseline | 1,207 | 60.9 | 58.5 | 12 of 29 |
| Blocks | 1,207 | 60.2 | 58.3 | 12 of 29 |
| Blocks and pumping | 823 | 58.0 | 108.7 | 9 of 29 |

The blocks change no unit's status. Averaged over the open land they cut the days deeper than 40 cm by 0.7 days, because their effect is local.

Table: Change in days deeper than 40 cm by distance from a block reach, blocks scenario against baseline, Mendahara-Batanghari, June to September 2026. Source: scenario comparisons of the groundwater model, baselines with canals outside licences at 1.2 m and 0.6 m.

| Distance from a block reach | Cells | Mean change, 1.2 m baseline (days) | Cells at least 10 days better, 1.2 m baseline | Mean change, 0.6 m baseline (days) | Cells at least 10 days better, 0.6 m baseline |
|---|---|---|---|---|---|
| 0-150 m | 2,009 | -26.2 | 62% | -13.6 | 26% |
| 150-350 m | 2,693 | -8.9 | 35% | -4.1 | 17% |
| 350-1,000 m | 7,064 | -0.8 | 1% | -0.4 | 0% |
| beyond 1,000 m | 108,945 | 0.0 | 0% | 0.0 | 0% |

Within 150 m of a reach, 62% of cells have at least 10 fewer days deeper than 40 cm; beyond 350 m almost none do. This matches the literature: a lateral effect under 5 cm by about 300 m (Kurnianto et al. 2026) and rewetting up to about 400 m upstream of blocks in Tebing Tinggi (Sutikno et al. 2023). The 160 reaches touch a small share of this densely canalled KHG, so the KHG-wide figure barely moves, and the KHG average is the wrong measure for judging blocks.

{{figure: model_days_map_mendahara | Days deeper than 40 cm in June to September 2026 at Mendahara-Batanghari: baseline, and change under the blocks scenario of the 27 October 2026 plan (model in development) | Two map panels on the KHG boundary (_khg/15.05-07-10.01_mendahara_batanghari/00_inputs/khg.gpkg) with sub-KHG units (_khg/15.05-07-10.01_mendahara_batanghari/02_delineation/lidar/subkhg_units.gpkg). Left: baseline days deeper than 40 cm on open land, sequential scale 0 to 122 days, from _khg/15.05-07-10.01_mendahara_batanghari/03_neraca/lidar/runs/model/tropical-large_p1.2_s1.2_t1.2_mt0.4_e0.3_100m_pb_dbbsdlp/model_season_days_deeper_40cm.tif (nodata -9999: managed and canal cells, shown grey). Right: change in days (scenario minus baseline, negative is wetter), diverging scale centred on 0; block reaches of the 27 October plan not drawn, from _khg/15.05-07-10.01_mendahara_batanghari/03_neraca/lidar/runs/model/tropical-large_p1.2_s1.2_t1.2_mt0.4_blk_e0.3_100m_pb_dbbsdlp/days_deeper_40cm_change.tif, with the block reaches overlaid as lines from _khg/15.05-07-10.01_mendahara_batanghari/05_pump/lidar/mendahara_batanghari.gpkg, layer sekat_reach. No licence holder names.}}

{{figure: model_days_by_distance | Mean change in days deeper than 40 cm by distance from a block reach, Mendahara-Batanghari, June to September 2026 (model in development) | Dot or bar chart, x axis the four distance bands (0-150 m, 150-350 m, 350-1,000 m, beyond 1,000 m), y axis mean change in days (negative is wetter). Two series: baseline canals outside licences at 1.2 m (repeat-neraca/docs/reports/scenarios_15.05-07-10.01_canals1.2.md, first scenario section, table "By distance from the block reaches", column "mean change (days)") and at 0.6 m (repeat-neraca/docs/reports/scenarios_15.05-07-10.01.md, same table). Label each point with the share of cells at least 10 days better (column "cells at least 10 days better").}}

Pumping takes about 50 million m³ more water in June to September (108.7 against 58.5 million m³). The number of units still needing rewetting falls from 12 to 9 only because pumping takes three of the dry units (S01, S02 and S09) out of open land: they are now held at the target. No unit left open changes status. The scenario therefore shows how much water pumping needs and where blocks act; the three units count as rewetted because they are held by assumption. On the 0.6 m baseline the pattern is the same, with smaller effects: blocks cut 13.6 days within 150 m, pumping takes 105.1 against 54.6 million m³, and the count falls from 8 to 7 because S09 is held. Given the limitations below, the ranking of the scenarios can be used; the absolute water table cannot yet.

## 8.13 Limitations and what is needed

The model can be applied to any KHG, but its results can be trusted only where they can be checked against field data. Its present limits, by their effect on the results:

- Water management in managed land is imposed and not simulated. Holding plantations at 0.4 m reproduces the supply at Sugihan-Lumpur, but the target is a regulatory assumption. Real canal levels in concessions are unknown, and they control the result.
- Results on land outside licences rest on 6 community stations in one KHG with six weeks of usable record. With canals at 1.2 m the model is far too deep there (101 cm against 44 cm on the screened record); with the LiDAR canal levels it matches on the 100 m grid (47 cm), less well at 200 m. The raw record, with its restarts and stuck loggers, gave a different picture (29 cm and a 63 cm fall).
- The surface specific yield of 0.6 in the tropical sets is about twice the measured values for drained peat. The measured lower value makes the drawdown worse where stations show the water table held up, so it is kept as a sensitivity case.
- Canal levels are set per class, or move with one canal water balance per sub-KHG whose outlet constant has not been measured. With no canal network, a block holds a reach at one level and water does not flow along canals. Canals in managed land stay fixed at the target. Tides are not represented, and the KHG edge is held by a river rule even on a coast.
- Forcing is a KHG mean per dekad, so evapotranspiration does not vary by land cover or fire history.
- Inputs are uneven. At Mendahara-Batanghari 36% of the KHG takes its peat depth from the KHG median of 3.9 m. At Tebing Tinggi the peat-depth map agrees with field thickness at r 0.10. LiDAR covers few KHG, and open DEMs can be wrong by as much as a dome's relief.
- No measurement before and after blocking is available to the project, so the simulated block response is untested in the field. It agrees with the published range.

To make the model operational, the project needs:

- water-table stations in land outside licences, with records through a full dry season, in several KHG;
- measured canal water levels in concessions and community land, by season;
- LiDAR or an equally good DTM for the KHG where scenarios are wanted;
- a baseline canal level that matches the one RE-PEAT Interventions assumes.

Decisions needed from KLH and the World Bank:

1. How the canal boundary in managed land is represented: a target water table as now (0.4 m, PP 57/2016), or a supply term sized from the deficit. Either is an assumption, and it sets the result in managed land.
2. What the field check rests on. The Tebing Tinggi survey cannot test spatial pattern, and managed station levels carry little spatial signal. Options are the 2026 Tebing Tinggi stations (5 concession stations at about 20 cm, 3 community stations at about 150 cm, one season), a site with stations and LiDAR, and the supply deficit as a second check.
3. Whether to adopt a measured specific yield (about 0.3 at the surface to 0.1 at 1.5 m) and evapotranspiration that falls with depth. Both come after the canal boundary, because neither replaces the missing supply.
4. Whether to build the canal network with a weir per block (Urzainki et al. 2023) or move to MODFLOW 6 with a stage per reach.

Until the model passes its checks outside managed land, the climatic balance and the station deficit remain the adopted neraca air, and the groundwater model's scenario maps are indicative.

## 8.14 Questions and answers

### What does the model produce?

Maps. The KHG is divided into cells of 100 m or 200 m, and the model computes the water-table depth of every cell every day. A simulation gives maps for a season (days deeper than 40 cm, mean depth, water supplied to managed land), a daily KHG series, a table per sub-KHG, and scores against stations.

### Does a result hold for one date only?

No. The result is a daily series for every cell. A map is a summary over a period, by default June to September, or a snapshot of one day. Any other season can be chosen.

### Why not model every KHG now, with blocks and pumps?

The model can already be applied to any KHG. What is missing is confidence in the answer. In managed land the model drains far more than the stations show unless water management is imposed, and on land outside licences it is still too deep. Canal water levels are unknown, and blocks and pumps work by changing them. Many KHG lack a good DTM and peat-depth map, and only KHG with enough stations can show whether the model works.

### Why does the model need to "hold" managed land at 0.4 m?

The stations there stay almost flat through the dry season (a median fall of 1 to 12 cm) while rain minus evapotranspiration is strongly negative. Companies hold canal water up with blocks, gates and pumps. The model cannot represent how, so it imposes the result and reports the water this takes. That water matched the station-based deficit at Sugihan-Lumpur (233 to 324 mm against 290 mm). The stations, though, cluster at the 40 cm compliance limit, so they do not measure the managed water table. A target of 0.6 or 0.8 m leaves the open land unchanged and cuts the water by a factor of 2 to 5.

### How far does a canal block reach?

In the Mendahara-Batanghari scenario, cells within 150 m of a block reach were deeper than 40 cm on average on 26 fewer days of the 122-day dry season; at 150 to 350 m, 9 fewer; beyond 1 km, no change. Published studies give a similar reach.

### How much water would pumping need?

At Mendahara-Batanghari, holding the 8 units that RE-PEAT Interventions marks for water supply at 0.4 m takes about 50 million m³ in June to September 2026, on top of the 58.5 million m³ the model gives for managed land.

### Does burned peat need different parameters?

Not for infiltration. On tropical peat, permeability did not fall significantly after fire across four Indonesian sites (Setiawan et al. 2020). Burned land sits lower and evaporates less; a post-fire LiDAR DTM already captures the lower surface.

### Is the model ready to replace the adopted neraca air?

No. It is in development. It replaces the climatic balance only after it passes the field checks, and then only on KHG with adequate inputs.
