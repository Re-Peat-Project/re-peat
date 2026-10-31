# 8 Neraca air (water balance)

*Neraca air* is the water balance of a peat hydrological unit (*KHG*) and of its sub-units (*sub-KHG*). For rewetting planning it tells when a KHG runs short of water and how much water the managed system has to supply to hold the water table. This chapter has two parts. Sections 8.1 to 8.5 cover the method the project has adopted: a climatic balance per sub-KHG from open satellite products, and a supply deficit per KHG from observed water tables. From section 8.6 the chapter covers the groundwater model for simulating rewetting scenarios, which is in development and is described separately.

## 8.1 Purpose and the regulatory target

Government Regulation PP 71/2014, as amended by PP 57/2016, treats cultivation-function peat (*gambut*) as damaged when the water table (*TMA*, *tinggi muka air*) is more than 0.4 m below the surface at a compliance point. Rewetting means holding or bringing back enough water to keep the water table above that line, with canal blocks (*sekat kanal*), water gates and, in emergencies, pumps. RE-PEAT uses the 0.4 m depth as its target throughout.

For rewetting, neraca air has to answer three questions:

1. In which months of the year does a KHG, or a sub-KHG, lose more water to evapotranspiration than rain supplies?
2. Do some sub-KHG lose more water than others, so that the balance can help rank them for intervention?
3. How much water, in millimetres and in cubic metres, must the managed system supply over a dry season to hold the water table where it was observed?

The adopted method answers the first and third questions with numbers for every selected KHG that has the data. Its answer to the second is weaker, because the open data separate sub-KHG reliably at only some sites (section 8.4).

## 8.2 Earlier work

The adopted method starts from the 2021 Kahayan-Sebangau study and the Pulau Padang work of Amal et al. (2021). Reproducing the 2021 balance showed that its published figures depend on runoff coefficients that vary between units without a stated reason, so the project fixed a single coefficient and a single form of the equation.

### The 2021 Kahayan-Sebangau study

The starting point is the neraca air of the 2021 study of KHG Kahayan-Sebangau by the UGM team. Its Earth Engine scripts compute a monthly balance from TerraClimate (about 4.6 km, monthly, 2010-2020):

WB = P - ET - C × P

where P is rain, ET is actual evapotranspiration and C is a runoff coefficient. The scripts use C = 0.25 for every unit. One script assigns 0.35 to ten of the 16 sub-KHG and 0.25 to the other six, with no reason given. The TerraClimate runoff band is loaded but not used, and the scripts have no interception term. The study's final report adds interception by land cover, from 0 % on open land to 16.4 % under forest, and cites C = 0.07-0.18 from two months of measurements on Pulau Padang; the measurements behind that range could not be traced. The report's Table 5.10 gives a sub-KHG balance for 2010-2020 of 41 to 65 mm/month and 3.9 to 5.3 deficit months per year.

### Reproduction of the 2021 scripts

The project rebuilt the 2021 balance on the same 16 sub-KHG polygons and TerraClimate data. Monthly values match the 2021 Earth Engine expression within 0.1 mm at six test points (two months, three sub-KHG). The remaining difference comes from the 2021 charts being computed at 2,500 m against TerraClimate's 4,638 m grid.

The reproduction does not match the published Table 5.10. With C = 0.25 everywhere, the 16 units range from 49.3 to 54.0 mm/month with 3.6 to 5.0 deficit months per year. With the 0.25/0.35 split, the ten units at 0.35 drop by about 21 mm/month, and the range becomes 28.7 to 50.9 mm/month with 4.1 to 5.4 deficit months. The KHG-mean calendar shows deficits in July (-39 mm), August (-39 mm), September (-5 mm) and October (-4 mm), with 90 % and 91 % of sub-KHG-months in deficit in July and August.

The scripts also carry material from other sites: their headers name KHG Pulau Padang and Tebing Tinggi, one map layer named "January 2019" shows August 2020, and one boundary layer is labelled Mempawah. The 16 polygons are Kahayan-Sebangau (4,523 km2 in total, against 451,507 ha in the KHG registry).

### The earlier design

An early design for the water balance followed the Pulau Padang water balance of Amal et al. (2021): storage change equals rain minus evapotranspiration minus runoff to canals, extended with pump inflow and inflow from upstream units. It proposed a dekadal time step, a runoff coefficient conditioned on canal-block status and antecedent water table, calibration against water-table stations, and a deficit for prioritisation of Sy × (TMA - 0.4 m) × area. Most of it could not be built, because it depended on canal discharge, block status and station networks that are not available to the project.

### The runoff coefficient

The project uses C = 0.12, the value from Pulau Padang, with a range of 0.07-0.18, and does not use separate values by land class. The full text of Amal et al. (2021), a two-month field campaign in November and December 2017, gives no runoff coefficient. It reports that on community land without canal blocks the water table sat between -0.6 and -1.9 m and rain "directly flows as runoff", while on company land with blocks it stayed between -0.4 and -0.6 m. The dissertation abstract (Amal 2022) states that runoff enters the balance through a coefficient, splits Pulau Padang into 11 sub-KHG, and finds deficit months in January, February, March, June and July, worst in February in the north. A MIKE SHE study of Pulau Padang (Kurnianto et al. 2026) found that converting forest to managed land raised runoff by about 6 %, while differences in rain between years changed runoff up to eightfold.

## 8.3 Why climate data alone cannot predict water tables

In managed peat, water management sets the water table more than the weather does. Open rain and evaporation data could not predict water tables per sub-KHG, so the adopted method uses the climate only for timing and measures the management term from water-table stations. The tests used the SiTMAT water-table stations in managed concessions, the only daily water-table series at the test KHG, which cover one season (2026).

### A rain-driven bucket fitted to stations

The first model was a daily bucket per sub-KHG: the water table falls when ERA5 rain minus evaporation is negative, scaled by an effective storage coefficient, with an optional drainage loss near canals. Storage, drainage and the starting depth were fitted to 86 stations at Kampar-Gaung (1 April to 9 October 2026) and scored on spatial blocks left out of the fit.

- Timing was moderate: the median correlation per station was 0.63.
- Spatial skill was nil. The Spearman correlation across held-out stations was -0.03 for peak depth and -0.02 for days deeper than 40 cm. The out-of-fold error (16.5 cm) was worse than a no-skill baseline in which every station follows the KHG-mean curve (15.3 cm).
- Every fitted parameter ran to the edge of its allowed range: specific yield 3.0, drainage 4.0 mm/day, starting depth 40 cm. A specific yield of 3.0 is not physical; measured values on drained Sumatran peat are 0.3 near the surface and 0.1 at 1.5 m depth (Ismail et al. 2021). The fit absorbed a missing drainage term and returned a nearly flat water table at 40 cm.
- The observed mean water table sat at about 40 cm from April to August and fell to 60-70 cm in September, a pattern consistent with managed water levels.
- No site property explained which stations were deepest (Spearman 0.34 or less for peat depth, elevation, canal distance and density, river distance, distance to the KHG edge, NDMI and NDVI).

The concession a station belongs to explains 64 % of the variance in peak depth (10 concessions with 3 or more stations, 85 stations). Sentinel-1 radar backscatter ranked peak depth across stations with a Spearman of 0.53, but inside concessions this fell to 0.21. The radar mostly reflects how a concession is managed.

Replacing ERA5 evaporation with WaPOR made the fit worse at both test KHG: out-of-fold error 24.0 against 20.4 cm at Kampar-Gaung and 14.2 against 11.3 cm at Sugihan-Lumpur, without the drainage term.

A further test fitted one canal level per concession and season, after Taufik et al. (2019). Leaving one station out, the error at Kampar-Gaung was 12.4 cm, against 14.6 cm for the all-station mean curve and 10.9 cm for copying the other stations of the same concession. With a whole concession left out, the model had no skill (17.2 against 17.0 cm). The fitted dry-season canal levels ranged from 28 to 88 cm between concessions at Kampar-Gaung; at Sugihan-Lumpur they sat at 32-36 cm from June after 52-56 cm in April and May. The project did not develop the bucket approach further.

### Physical tiers 1 and 2

The project then tested a physical model with no fitted parameters. Tier 1 is one water table for the whole KHG draining to canals; tier 2 is a 2D groundwater model on a 500 m grid with canals and the KHG edge as fixed heads. Both use ERA5 forcing and peat tables after Urzainki et al. (2020).

Table: Tier 1 physical model against the station-mean water table, 1 April to 15 October 2026, base transmissivity. Source: tier 1 model results of the neraca air analysis.

| KHG | Stations | Simulated mean depth (cm) | Observed mean depth (cm) | Bias (cm) | RMSE (cm) | Correlation |
|---|---|---|---|---|---|---|
| Sugihan-Lumpur | 51 | 65.7 | 43.0 | +22.7 | 56.6 | 0.96 |
| Kampar-Gaung | 86 | 25.1 | 42.0 | -16.9 | 27.5 | 0.68 |

At Sugihan-Lumpur the model gets the timing right and the level wrong. Raising transmissivity a thousandfold made it worse (100.2 cm simulated at a canal drawdown of 1.2 m), because the canals then pull the water table towards their level. Letting evaporation fall as the water table deepens, with the natural-peat thresholds of Apers et al. (2022), cut the error from 56.6 to 46.2 cm and left most of the gap. In the 2D model, 30 % of cells were fixed as canal or edge, and every free cell followed the same curve: all 28 sub-KHG had the same mean depth, 65 cm. These tiers were an early diagnostic version of the groundwater model. The rewetting model of section 8.6 builds on it, holds managed land at 0.4 m and uses a 100 m grid; it will replace the adopted outputs only after it passes a check against field water tables.

### What the failures show

At Sugihan-Lumpur, rain minus evaporation from June to October summed to about -306 mm. With a specific yield of 0.14-0.2 the water table should have fallen 1.5 to 2 m. The station mean fell about 11 cm. Water came in from outside the rain balance, through tidal and river inflow in canals, gates and pumping, and held the level. Stations in managed concessions stay almost flat through the dry season, so water management sets their level.

The literature agrees. Every model reviewed that works in drained tropical peat treats drainage as an explicit input. SWAP in South Sumatra sets the canal water level by season, no deeper than 130 cm below the surface in the dry season and 50 cm in the wet (Taufik et al. 2019). The *ecosys* model across Riau prescribes a lateral boundary water table (Mezbahuddin et al. 2023). PEATCLSM-Trop uses ditch depth, interval and conductivity, and notes that its drainage map does not take local canal management into account, which it names among its main remaining errors (Apers et al. 2022). None of these models predicts the water table from rain minus evaporation alone, which is what the bucket attempted.

The adopted method therefore keeps the climatic balance for what it can show (when a KHG is short of water, and how sub-KHG compare where the data agree) and measures the management term directly from the stations as a supply deficit.

## 8.4 The adopted method

The method gives planners two results at two levels, kept apart:

- Per sub-KHG, a climatic water balance: how much water the climate leaves each unit, in how many months a year it falls short, and whether the order of units is reliable enough to use in ranking.
- Per KHG, a supply deficit: how much water the managed system supplied to hold the observed water table through the 2026 dry season.

{{diagram: neraca_method_report | Adopted neraca air method: climatic balance per sub-KHG and supply deficit per KHG | see diagrams/neraca_method_report.drawio}}

### Inputs

Table: Inputs of the adopted neraca air method. Source: neraca air method report and the Earth Engine product definitions.

| Input | Product | Grid | Period available | Used for |
|---|---|---|---|---|
| Sub-KHG units | sub-KHG delineation; the whole KHG as one unit where none exist | polygons | | balance |
| Rain | CHIRPS daily | 0.05° (about 5.6 km) | 1981 to 30 September 2026 | balance |
| Evapotranspiration, central | MODIS MOD16A2GF v061, gap-filled 8-day | 500 m | 2000 to December 2025 | balance |
| Evapotranspiration, near real time | MODIS MOD16A2 v061, not gap-filled | 500 m | 2021 to October 2026 | 2026 balance |
| Evapotranspiration, second source | FAO WaPOR v3 L1 AETI, dekadal | 326 m | 2018 to 11 October 2026 | balance (agreement test) |
| Land cover | ESA WorldCover v200 | 10 m | 2021 | interception |
| Rain reference | IMERG Final monthly V07 | 0.1° | 1998 to September 2025 | checks |
| Water table | SiTMAT concession stations, daily depth | points | 1 April to 22 October 2026 | deficit |
| Rain and evaporation, KHG mean | ERA5 daily | 0.25° | deficit window of each KHG | deficit |

SiTMAT is the only daily water-table series used by the adopted method. Its stations do not report rain, and no rain-gauge record was available to the project.

### The climatic balance per sub-KHG

The balance is computed per dekad and summarised per month and per year. A dekad is days 1-10, 11-20, or 21 to the end of the month.

Step 1 retrieves rain and evapotranspiration per unit and per dekad from Earth Engine. The total for a dekad is the sum, over the source images that overlap it, of the image's daily rate times the days of overlap. The daily rate is the image value times its scale factor, divided by the image length when the value is a total (one CHIRPS day, one MOD16 8-day composite), and used as is when it is a mean daily rate (WaPOR). MOD16 fill values are excluded. Each value is an area-weighted mean over the unit, computed on the product's own grid with no resampling, and carries its count of valid pixels and the share of the dekad covered by images. WorldCover class shares are counted per unit. Since each period must start and end on a dekad boundary, the series used here end on 1 October 2026.

Step 2 forms the monthly balance:

WB(u, month) = P_KHG × (1 - I_u) × (1 - C) - ET_u

- P_KHG is the area-weighted KHG mean of the month's rain, the same for every unit. CHIRPS and IMERG order the sub-KHG differently by mean rain (Spearman -0.34 over 30 units at Sugihan-Lumpur, -0.06 over 26 at Kampar-Gaung), so rain cannot separate units.
- ET_u is MOD16 for the unit. Its annual level, 1,385 to 1,441 mm/yr at the two test KHG over 2018-2025, lies within eddy-covariance measurements over Central Kalimantan peat of 1,636, 1,553 and 1,374 mm/yr at undrained, drained and drained-burnt sites (Hirano et al. 2015). WaPOR (1,101 to 1,180 mm/yr) lies below the lowest site, so it serves as a second source only.
- C = 0.12.
- I_u is the unit's interception share: the sum over WorldCover classes of class share times interception (tree cover and mangroves 0.164, shrubland 0.08, herbaceous wetland 0.05, grassland and cropland 0.03, other classes 0).

A month counts only when all its dekads are fully covered for both rain and evapotranspiration, and a year only when all 12 months count. Over the complete years the method gives, per unit:

- the mean monthly balance (mm/month);
- deficit months, the number of months a year with a negative balance;
- P - ET, rain minus evapotranspiration without the runoff and interception terms (mm/month);
- the spread of the yearly mean between years.

### Can the order of sub-KHG be trusted?

A ranking of sub-KHG by water balance is only useful where the order of units reflects water, and this holds at few sites. With the same rain for every unit, the mean balance follows forest share: the interception term is 6-16 % of about 240 mm/month of rain and is fixed by land cover, which is larger than the differences in evapotranspiration between units (standard deviation 3-7 mm/month). Across units the mean balance correlated with forest share at -0.44 at Sugihan-Lumpur and -0.82 on the 2021 Kahayan-Sebangau units, while P - ET correlated at 0.07 and 0.11. P - ET therefore carries the water signal between units. Satellite evapotranspiration already includes evaporation of intercepted rain, so the interception term counts it a second time; the formula is kept because it is the established form of the 2021 study.

The method tests, for each KHG and DEM variant, whether the order of units can be used. The order passes when both of these hold:

1. MOD16 and WaPOR order the units' mean evapotranspiration alike, and
2. the yearly balance keeps its order between years (median Spearman over all pairs of complete years),

each at or above the 99th percentile of the same statistic for a random order of the same number of units, found by simulation (10,000 draws). A fixed threshold such as 0.5 would not be equally strict for every number of units: the 99th percentile for one Spearman is 0.43 for 30 units, 0.46 for 26, 0.58 for 16 and 0.72 for 10. The year test is weak, because a land-cover term fixed in time keeps the order between years whatever the water does, so the evapotranspiration test carries the decision. With fewer than 5 units no order is tested.

Where the test fails, the balance values of those units are left out of the sub-KHG ranking. The water indicator of the sub-KHG ranking uses P - ET, and deficit months carry a weight of 0. The ranking uses default weights proposed by the project for agreement with KLH and the World Bank, and adjustable in the dashboard.

### The KHG supply deficit

The supply deficit gives the volume of water that had to reach a KHG from outside the rain balance to hold the observed water table, which is the quantity that water supply and pumping plans have to cover. It is a mass balance on the observed water table, with nothing fitted:

deficit (mm) = max(0, -Σ(P - E) - Sy × Δz × 10)

deficit (m3) = deficit (mm) / 1,000 × KHG area

- P - E is the daily ERA5 rain minus evaporation, KHG mean, summed over the window.
- Δz is the change in the station-mean depth (cm, positive deeper) between the mean of the first 7 and the last 7 days of the window. A water table that fell supplied part of the loss itself. One that rose against a negative balance adds to what had to come from outside.
- Sy = 0.15, with a band from 0.10 to 0.20. The peat tables after Urzainki et al. (2020) are not used here, because they rest on boreal retention curves.
- The window runs from 1 June to the last day with forcing, at most 31 October. Only stations with readings on at least half the window's days are used.
- Deficit months are the calendar months in the window with negative P - E; a partial last month counts.

ERA5 remains the deficit's forcing. Against IMERG over 21 dry-season months of 2019-2021, ERA5 rain was biased +18 % at Sugihan-Lumpur and +7 % at Kampar-Gaung, against +27 % and +7 % for CHIRPS. ERA5 evaporation totals were within -6 % and +2 % of MOD16 over the same months, and 17 % and 28 % above WaPOR. Using CHIRPS and WaPOR for the deficit would lower evapotranspiration by about a quarter, and the deficit with it. WaPOR is also revised by its provider: six dekads of 2026 (11 June to 10 August) changed after the project first retrieved them. For June to September 2026 at Sugihan-Lumpur, CHIRPS gave 208 mm of rain against 140 mm from ERA5, and the Earth Engine pair (CHIRPS minus WaPOR) gave -211 mm against -281 mm from ERA5.

### Checks

The checks confirm the arithmetic and the KHG calendar of dry months. They do not confirm the order of sub-KHG.

Table: Checks of the adopted method. Source: neraca air method report and the check reports it names.

| Check | Result |
|---|---|
| Reproduction of the 2021 scripts | within 0.1 mm |
| Dekad arithmetic: one period equal to one source image | maximum difference 5e-14 mm (WaPOR), 1e-6 mm (TerraClimate) |
| Deficit months at Pulau Padang, 2018-2025, against Amal (2022) | February in deficit in 75 % of years, July 62 %, January 38 %, March 25 %, June 12-25 % (MOD16 or WaPOR); August 25-38 %, not named by Amal |
| Station deficit per sub-KHG against the long-term balance, Sugihan-Lumpur, 9 units with 3 or more stations | deficit 123 to 277 mm (median 181); Spearman with mean balance 0.32 and with deficit months 0.49, where a negative and a positive value were expected |
| Same, Kampar-Gaung, 6 units | deficit 0 in every unit |

Over 2018-2025 the deficit months at Pulau Padang match the months Amal (2022) names, with February the most frequent, as in that study. The station deficit per sub-KHG runs against the order of units from the long-term balance at Sugihan-Lumpur and is zero in every unit at Kampar-Gaung.

### Outputs

For each KHG and DEM variant the method produces:

- the balance per sub-KHG: mean monthly balance, deficit months per year, P - ET, spread between years, interception share, the WaPOR values for comparison, and the result of the order test;
- the monthly balance per sub-KHG and evapotranspiration source;
- a summary with the KHG calendar of monthly balance, evapotranspiration agreement, year stability and the forest-share check, and the parameters used;
- the KHG deficit with its band, volume, deficit months and the evidence behind it (stations, valid days);
- the neraca map, with sub-KHG polygons carrying the balance, the monthly climatology, the dry-season mean (July to October) and the KHG deficit, and the stations with their start, end and deepest depth in the window and their share of days deeper than 40 cm. Units that fail the order test are shown grey and not ranked. The map has no water-table surface, because the gridded model failed the station check.

The method applies to any list of KHG, up to the full registry of 865, and gives one summary per KHG and DEM variant. A KHG without delineated sub-KHG is treated as one unit.

## 8.5 Results at the first four KHG with completed chains

At KHG level the balance gives a consistent calendar of dry months, and the 2026 supply deficit gives the volume of water the managed system supplied at three of the four KHG. The order of sub-KHG is reliable in only two of twelve combinations of KHG and DEM. Chapter 10 gives the water balance and deficit of all 14 analysed KHG.

The full analysis chain is complete at Kampar-Gaung (KHG 14.02-04-05.01), Mendahara-Batanghari (15.05-07-10.01), Saleh-Sugihan (16.02-07.01) and Sugihan-Lumpur (16.02.01), once for each DEM variant: LiDAR, DeltaDTM and DEMNAS. The climatic balance uses CHIRPS rain, MOD16 evapotranspiration and the complete years 2018-2025 throughout.

### Rain and evapotranspiration

Table: Annual rain and evapotranspiration, KHG mean, 2018-2025. Source: dekadal rain and evapotranspiration per sub-KHG from Earth Engine, DeltaDTM variant, area-weighted over sub-KHG.

| KHG | CHIRPS rain, mean (min-max) (mm/yr) | MOD16 ET (mm/yr) | WaPOR ET (mm/yr) |
|---|---|---|---|
| Kampar-Gaung | 2,785 (2,051-3,286) | 1,385 | 1,101 |
| Mendahara-Batanghari | 2,855 (2,202-3,435) | 1,408 | 1,071 |
| Saleh-Sugihan | 2,971 (2,325-3,504) | 1,350 | 1,139 |
| Sugihan-Lumpur | 2,885 (2,212-3,483) | 1,441 | 1,180 |

{{figure: neraca_rain_et_dekadal | Dekadal rain and evapotranspiration per KHG, 2018 to September 2026 | Four small multiples (one per KHG: Kampar-Gaung, Mendahara-Batanghari, Saleh-Sugihan, Sugihan-Lumpur), lines, x = dekad start, y = mm per dekad. Three lines per panel: CHIRPS rain, MOD16 ET, WaPOR ET. Source: _khg/<folder>/03_neraca/deltadtm/inputs/balance_chirps_dekad.csv, balance_mod16_dekad.csv, balance_wapor_dekad.csv, columns unit_id, start, mm, time_cov; KHG value = area-weighted mean over unit_id using area_km2 from _khg/<folder>/03_neraca/deltadtm/inputs/units_landcover.csv; drop rows with time_cov < 0.999. MOD16 ends in December 2025 (later dekads are partial and must be dropped); CHIRPS and WaPOR run to the dekad starting 2026-09-21. Folders: 14.02-04-05.01_kampar_gaung, 15.05-07-10.01_mendahara_batanghari, 16.02-07.01_saleh_sugihan, 16.02.01_sugihan_lumpur.}}

### The KHG supply deficit, dry season 2026

Sugihan-Lumpur needed about 290 mm of water from outside the rain balance in one dry season, about 1.8 billion m3 over the KHG. Its water table fell 11 cm while the climate removed 307 mm. Mendahara-Batanghari needed 119 mm (240 million m3); its 12 stations fell 22 cm, which supplied 33 mm of the 152 mm loss. At Mendahara-Batanghari the window has 133 days of forcing out of 135, and 7 of the 12 stations belong to one concession.

Table: KHG supply deficit, dry season 2026. Source: KHG deficit results of the neraca air analysis (SiTMAT stations, ERA5).

| KHG | Window | Stations | Area (km2) | ERA5 P - E (mm) | Station-mean depth, start to end (cm) | Deficit (mm), Sy 0.15 | Band, Sy 0.10-0.20 (mm) | Volume (million m3) | Months with P - E < 0 |
|---|---|---|---|---|---|---|---|---|---|
| Sugihan-Lumpur | 1 Jun to 9 Oct | 51 | 6,348 | -306.7 | 40.2 to 51.2 | 290.2 | 284.7-295.7 | 1,842 | 5 |
| Mendahara-Batanghari | 1 Jun to 13 Oct | 12 | 2,012 | -152.3 | 33.4 to 55.6 | 119.1 | 108.0-130.2 | 240 | 4 |
| Kampar-Gaung | 1 Jun to 9 Oct | 78 | 7,115 | +9.3 | 43.2 to 32.3 | 7.1 | 1.6-12.5 | 50 | 2 |
| Saleh-Sugihan | | 0 | 1,907 | | | no station | | | |

At Kampar-Gaung the climate was close to neutral (+9 mm), but the station mean rose 10.9 cm. At Sy 0.15 that rise stored 16 mm, more than the rain balance supplied, so 7 mm had to come from outside. The stations there are held at about 40 cm through the season (section 8.3).

No SiTMAT station lies inside Saleh-Sugihan, so no station-based deficit can be computed for this KHG.

The deficit covers 2026 only, the one season the stations record. Its deficit months count ERA5 rain minus evaporation in that season, while the calendar below uses the CHIRPS and MOD16 balance with runoff and interception over 2018-2025, so the two need not agree.

{{figure: neraca_station_depth_2026 | Station-mean water-table depth, 1 April to 15 October 2026 | Lines, one per KHG (Kampar-Gaung, Mendahara-Batanghari, Sugihan-Lumpur), x = date, y = depth below surface in cm, axis inverted (deeper downwards). Horizontal reference line at 40 cm (PP 57/2016). Shade the deficit window from 1 June to 9 October (Kampar-Gaung, Sugihan-Lumpur) and 13 October (Mendahara-Batanghari). Source: _khg/<folder>/03_neraca/runs/deficit/tier1_series.csv, columns date and obs_mean_cm only (do not plot depth_cm_k1_dd1.2, the failed tier 1 model curve). Folders: 14.02-04-05.01_kampar_gaung, 15.05-07-10.01_mendahara_batanghari, 16.02.01_sugihan_lumpur. Saleh-Sugihan has no stations.}}

### The climatic balance per sub-KHG

Every KHG has a positive mean balance over the year, from 58 to 84 mm/month, and 2.2 to 2.7 deficit months a year on average. Within a KHG the sub-KHG means span 13 to 45 mm/month. The year-to-year order test passed in every case (median Spearman 0.64 to 0.94, against thresholds of 0.11 to 0.12), so the evapotranspiration test decided the outcome each time.

Table: Climatic balance per sub-KHG by KHG and DEM variant, 2018-2025 (CHIRPS rain as KHG mean, MOD16). Mean balance is the unweighted mean over sub-KHG. Source: neraca air summary and the sub-KHG balance of each variant.

| KHG | DEM | Sub-KHG | Area (km2) | Mean balance (mm/month) | Sub-KHG range (mm/month) | P - ET range (mm/month) | Deficit months per year, mean (range) | ET order agreement (needed) | Order usable |
|---|---|---|---|---|---|---|---|---|---|
| Kampar-Gaung | LiDAR | 28 | 7,126 | 58.4 | 50.9-64.5 | 109.1-122.1 | 2.66 (2.38-3.25) | -0.48 (0.45) | no |
| Kampar-Gaung | DeltaDTM | 27 | 7,140 | 58.8 | 50.9-67.2 | 109.1-122.3 | 2.66 (2.38-3.25) | -0.48 (0.44) | no |
| Kampar-Gaung | DEMNAS | 29 | 7,140 | 58.8 | 50.5-63.8 | 109.1-122.7 | 2.66 (2.38-3.25) | -0.59 (0.43) | no |
| Mendahara-Batanghari | LiDAR | 29 | 2,021 | 62.2 | 53.4-74.8 | 114.8-128.4 | 2.48 (2.12-3.12) | 0.06 (0.43) | no |
| Mendahara-Batanghari | DeltaDTM | 29 | 2,022 | 63.0 | 51.5-78.9 | 112.3-132.3 | 2.44 (2.00-2.88) | -0.10 (0.43) | no |
| Mendahara-Batanghari | DEMNAS | 29 | 2,022 | 62.7 | 48.3-73.6 | 108.9-126.9 | 2.49 (2.12-3.25) | 0.08 (0.43) | no |
| Saleh-Sugihan | LiDAR | 29 | 1,180 | 75.0 | 65.9-105.3 | 111.7-149.1 | 2.47 (1.62-2.75) | 0.56 (0.43) | yes |
| Saleh-Sugihan | DeltaDTM | 26 | 1,907 | 83.5 | 68.0-113.1 | 117.7-152.1 | 2.19 (1.38-2.75) | 0.38 (0.46) | no |
| Saleh-Sugihan | DEMNAS | 27 | 1,907 | 83.9 | 68.0-113.0 | 117.7-152.7 | 2.18 (1.50-2.75) | 0.30 (0.44) | no |
| Sugihan-Lumpur | LiDAR | 29 | 6,378 | 69.7 | 56.5-94.1 | 104.4-135.4 | 2.44 (2.12-2.75) | 0.41 (0.43) | no |
| Sugihan-Lumpur | DeltaDTM | 29 | 6,380 | 69.7 | 57.6-88.0 | 110.5-132.1 | 2.45 (2.12-2.75) | 0.41 (0.43) | no |
| Sugihan-Lumpur | DEMNAS | 27 | 6,380 | 69.6 | 60.5-88.0 | 108.5-130.7 | 2.43 (2.12-2.62) | 0.53 (0.44) | yes |

The order between sub-KHG can be used in only two of the twelve cases:

- At Kampar-Gaung, MOD16 and WaPOR order the units in opposite directions in all three variants (Spearman -0.48 to -0.59).
- At Mendahara-Batanghari the two products are unrelated (Spearman -0.10 to 0.08), and the mean balance follows forest share almost entirely (Spearman -0.77 to -0.87), so the interception term sets the order.
- At Sugihan-Lumpur the agreement sits on the threshold. It passes with DEMNAS units (0.53) and fails with LiDAR and DeltaDTM units (0.41 against 0.43). An earlier delineation with 30 units passed at 0.46.
- At Saleh-Sugihan it passes only with the LiDAR units (0.56). The LiDAR covers 1,180 of the 1,907 km2 of this KHG, so that case describes a different and drier area: 75.0 against 83.5-83.9 mm/month.

The DEM changes the sub-KHG boundaries and their number (26 to 29 per KHG), and through them the units' evapotranspiration. It barely changes the KHG-level result: where the variants cover the same area, mean balance differs by at most 0.8 mm/month and mean deficit months by at most 0.05. The usable order of units does change with the DEM at the two KHG where agreement is near the threshold.

### Dry-season months

The timing of the dry season differs by region, which sets when interventions need to be in place. The two Riau and Jambi KHG have a short, sharp dry season centred on July, and Kampar-Gaung has a second one in February (mean -13 mm). The two South Sumatra KHG have a longer dry season from July to October; at Sugihan-Lumpur the mean is negative in July, August and September. The worst year was 2019, with 4 to 6 deficit months across the four KHG; in 2022 Saleh-Sugihan and Sugihan-Lumpur had none.

{{figure: neraca_calendar | Mean monthly climatic balance by calendar month, 2018-2025 | Lines, one per KHG (Kampar-Gaung, Mendahara-Batanghari, Saleh-Sugihan, Sugihan-Lumpur), x = calendar month 1-12, y = balance in mm/month, horizontal zero line. Source: _khg/<folder>/03_neraca/deltadtm/runs/balance/neraca_balance_monthly.csv, rows with et_source = mod16 and month from 2018-01 to 2025-12; KHG value per month = mean of WB_mm over unit_id (unweighted, as in the balance report), then mean over the 8 years for each calendar month.}}

Table: Calendar months with a negative KHG-mean balance, share of years 2018-2025. Months where no KHG reaches 30 % are left out. Source: monthly sub-KHG balance of the DeltaDTM variant (MOD16), mean over sub-KHG.

| KHG | Feb | Jul | Aug | Sep | Oct | Lowest mean month (mm) |
|---|---|---|---|---|---|---|
| Kampar-Gaung | 50 % | 75 % | 38 % | 25 % | 12 % | July, -25 |
| Mendahara-Batanghari | 25 % | 88 % | 62 % | 25 % | 25 % | July, -38 |
| Saleh-Sugihan | 12 % | 50 % | 62 % | 50 % | 38 % | July, -6 |
| Sugihan-Lumpur | 12 % | 50 % | 62 % | 50 % | 38 % | July, -18 |

The tables below give the values per sub-KHG for each KHG. They use the DeltaDTM variant, the one that covers the full area at all four KHG.

{{table: neraca_units_kampar_gaung | Climatic balance per sub-KHG, Kampar-Gaung, 2018-2025 (DeltaDTM units) | _khg/14.02-04-05.01_kampar_gaung/03_neraca/deltadtm/runs/balance/neraca_balance_unit.csv: one row per unit_id, columns unit_id, u_wb_mean (mm/month), p_minus_et_mean_mm (mm/month), u_deficit_months (per year), interception_share (share), wb_mean_wapor (mm/month); area_km2 joined from _khg/14.02-04-05.01_kampar_gaung/03_neraca/deltadtm/inputs/units_landcover.csv; sorted by unit_id. Footnote: order of units not usable (ET products disagree).}}

{{table: neraca_units_mendahara_batanghari | Climatic balance per sub-KHG, Mendahara-Batanghari, 2018-2025 (DeltaDTM units) | _khg/15.05-07-10.01_mendahara_batanghari/03_neraca/deltadtm/runs/balance/neraca_balance_unit.csv: same columns and join as neraca_units_kampar_gaung, area from _khg/15.05-07-10.01_mendahara_batanghari/03_neraca/deltadtm/inputs/units_landcover.csv. Footnote: order of units not usable.}}

{{table: neraca_units_saleh_sugihan | Climatic balance per sub-KHG, Saleh-Sugihan, 2018-2025 (DeltaDTM units) | _khg/16.02-07.01_saleh_sugihan/03_neraca/deltadtm/runs/balance/neraca_balance_unit.csv: same columns and join, area from _khg/16.02-07.01_saleh_sugihan/03_neraca/deltadtm/inputs/units_landcover.csv. Footnote: order of units not usable with DeltaDTM units; usable with the LiDAR units, which cover 1,180 of 1,907 km2.}}

{{table: neraca_units_sugihan_lumpur | Climatic balance per sub-KHG, Sugihan-Lumpur, 2018-2025 (DeltaDTM units) | _khg/16.02.01_sugihan_lumpur/03_neraca/deltadtm/runs/balance/neraca_balance_unit.csv: same columns and join, area from _khg/16.02.01_sugihan_lumpur/03_neraca/deltadtm/inputs/units_landcover.csv. Footnote: order of units not usable with DeltaDTM units (0.41 against 0.43); usable with DEMNAS units.}}

### What the results support

The balance is most useful at KHG level and for comparing KHG. It is consistent across DEM variants and gives a calendar of dry-season months for every selected KHG, which can guide when canal blocks and water supply need to be in place. The 2026 deficit gives the volume of water the managed system supplied at three KHG, from 50 million m3 at Kampar-Gaung to 1.8 billion m3 at Sugihan-Lumpur. Between sub-KHG, the open climate data separate units in two of twelve cases, and the station deficit per sub-KHG does not confirm that order, so the balance should carry little weight in a ranking inside a KHG. The deficit covers one season, and the balance cannot be checked against water tables for 2018-2025.
