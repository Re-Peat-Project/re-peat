# 05 Parameter register

One place to look up a number: its default, a plausible range, where it comes from, and how much to trust it. Code keys are given where a parameter is configurable.

**Confidence:** **High** = several peer-reviewed Indonesian/SE Asian studies agree. **Medium** = one or two studies, or consistent grey literature. **Low** = single site, inferred, or placeholder; treat as a sensitivity parameter.

## Hydrology

| Parameter | Default | Range | Unit | Source | Confidence | Code key |
|---|---|---|---|---|---|---|
| Target water-table depth | 0.4 | — | m below surface | PP 57/2016 (at titik penaatan) | regulation | `params.tma_threshold_m`, `ipg_dA_m` |
| Specific yield, surface | 0.30 | 0.05–0.6; 1.0 when ponded | – | Ismail et al. 2021 (Padang Island); pristine peat 0.05–0.30 | Medium | methodology |
| Specific yield at 1.5 m | 0.10 | 0.03–0.15 | – | Ismail et al. 2021 | Medium | methodology |
| Hydraulic conductivity, forest upper peat | 30 | 5–100 | m/day | Kurnianto et al. 2019; Brunei slug tests | Medium (very variable) | methodology |
| Hydraulic conductivity, drained/burnt | 5 | 1–25 | m/day | Brunei; Kubu Raya | Medium | methodology |
| Canal influence distance, intact peat | 200 | 20–1000 | m | field transects 170–240 m (Riau); ~600 m modelled (Urzainki et al. 2023) | Medium | `params.l_inf_m` |
| Canal influence distance, burnt peat | 60 | 20–120 | m | Limbung, West Kalimantan: fastest at 20 m, sharp decline from 70 m (single site, 4 months, wells every 50 m) | Low | `params.l_inf_burnt_m` |
| Canal rise for ~200 m reach | 0.6 | 0.3–0.8 | m | Sutikno et al. (Riau) | Medium | methodology |
| Dry-season ET | 4.1 | 3–5 weekly; 1.8–7.3 daily | mm/day | Hirano et al. 2015; Ohkubo et al. 2021; Mawas 2020; Kahayan–Sebangau 2021: 3.47 | High | methodology |
| ET factor, burnt/shrub vs forest | 0.87 | 0.80–0.95 | – | same | Medium | methodology |
| Dry-period water-table decline | emergent | 16–23 (shrub near tide 16.4; shrub/rice 17.8; rice far from tide 23.4) | mm/day | SiPALAGA, Kahayan–Sebangau 2021 | Medium (3 stations) | check value; `u_tma_recession` |
| Runoff coefficient C | 0.12 | 0.07–0.18 | – | Pulau Padang, Nov–Dec 2017 (Aditya & Cahyono 2018) | Low (2 wet months, one site) | `params.runoff_coefficient` |
| Interception | forest 0.164, shrub 0.08, wetland 0.05, grass/crop 0.03 | 0–0.164 | – | Kahayan–Sebangau 2021 (0% open to 16.4% forest); intermediate values are our interpolation | Low–Medium | `params.interception_by_class` |
| Peat water content | 0.8 natural, 0.7 canalised | — | share of peat volume | Kahayan–Sebangau 2021 | Low; **total** water, not drainable | `params.water_content_*` |

## Fire

| Parameter | Default | Range | Unit | Source | Confidence | Code key |
|---|---|---|---|---|---|---|
| Hazard bands (water-table depth) | 0.4 / 0.6 / 0.85 | — | m | Taufik et al. 2022 (danger below 0.4, burning below 0.6); Taufik et al. 2019 (levels off ~0.85) | Medium–High | methodology |
| "Safe" level, South Sumatra 2019 | −0.45 ± 0.09 | — | m | Land 2024 | Medium | — |
| Validation: unit counts as burned | 5% | 1–20% | of unit area | design choice | — | `scoring.validation_burn_threshold` |
| Hotspot confidence | nominal + high | — | VIIRS class | common practice | — | `sources.firms.confidence` |

## Canals, blocks and pumps

| Parameter | Default | Range | Unit | Source | Confidence | Code key |
|---|---|---|---|---|---|---|
| Max head drop between blocks | 0.3 | 0.2–0.5 | m | BRG guidance; Ritzema et al. 2014 | Medium | pool rule |
| Block spacing (derived) | 0.4 m ÷ slope | 50–2000 | m | Kahayan–Sebangau 2021 (IPG) | Medium | `params.ipg_*` |
| Block half-life, wood/bamboo | 2.5 | 1–5 | years | 70% of 77 blocks damaged (Pantau Gambut, grey); poles last 3–5 yr | Low | methodology |
| Block half-life, compacted peat | 7 | 3–15 | years | Hooijer et al. 2024 (7.5 yr working) | Low (inferred) | methodology |
| Primary canal | 25 × 3 | — | m (width × depth) | Kahayan–Sebangau field survey | Medium (one KHG) | HEC-RAS defaults |
| Secondary canal | 6 × 1.5 | — | m | same | Medium | HEC-RAS defaults |
| Portable pump flow / fuel | 22 / 4.9 | 15–30 / 4–6 | m³/h, L/h | Mark-3 specification (dealer) | Medium | methodology |
| Relay-class pump flow / fuel | 100 / 17–22 | 70–125 | m³/h, L/h | Shibaura, Tohatsu specifications | Medium | methodology |
| Relay water-front speed | 1.7 | 1–3 | km/day | 11 km in 6–7 days, Jambi 2026 (news; our inference) | Low | methodology |
| Relay conveyance loss | 20% | 10–30% | – | placeholder, no data | Low | methodology |
| Deep well depth / radius | 30 / 200 | 20–40 / 180–300 | m | BRG module, news | Low | — |

## Terrain and subsidence

| Parameter | Default | Range | Unit | Source | Confidence | Code key |
|---|---|---|---|---|---|---|
| DTM accuracy target | 0.25 | 0.1–0.5 with LiDAR; 1–3 from DEMNAS | m RMSE | design target; DEMNAS published 2.2–5.0 m (07), our tests 1.2–2.8 m | — | report |
| Penetration factor k, tree cover | 0.8 (prior) | 0–1; fitted 0.04–0.21 | – | placeholder; fitted values at Sebangau, Mendahara and Bengkalis are far lower, so the prior is unsupported | Low; fit per site | `k_by_class` |
| Subsidence, mean drained peat | 2.2 | — | cm/yr | Hoyt et al. 2020 (ALOS PALSAR, 2.7 Mha) | High | `ground.epoch` |
| Subsidence, Acacia plantation | 4.3 | 2–6 | cm/yr | Evans et al. 2019 | High | `ground.epoch` |
| Rewetting effect on subsidence | halved | — | – | Hooijer et al. 2024 | Medium | — |

## Prioritisation design choices

These are choices, not measurements; they should be agreed with KLH and tested with the sensitivity runs.

| Parameter | Default | Meaning | Code key |
|---|---|---|---|
| Urgency share of risk | 0.6 | risk = 0.6 urgency + 0.4 impact | `scoring.alpha_urgency` |
| Indicator weights | fire history 2, peat depth 2, canal reach 2, IPG gap 1.5, most others 1 or 0.5 | relative importance within a group | `indicators.*.weight`, `ahp` |
| Normalisation | 5th–95th percentile | robust 0–1 scaling | `scoring.normalise_quantiles` |
| Tidal down-weighting | 0.7 × tidal share | tidal areas rarely dry | `scoring.tidal_factor` |
| Excluded concession types | IUP | mining is no longer peat ecosystem | `vectors.concessions.exclude_types` |
| Baseline / validation years | 2016–2022 / 2023 | indicators vs test years | `years` |
| Sub-KHG count per KHG | 6–30 | automatic outlet-order choice | `units.subkhg.target_count` |
| Minimum sub-KHG area | 5 | km² | `units.subkhg.min_area_km2` |

## Known data gaps

- No measured leakage coefficients for canal blocks.
- No measured conveyance losses for pump relays; no flow data for the 2026 relays.
- Deep-well yields (the BRG module's unit is truncated).
- Runoff coefficient only from two wet-season months at one site.
- Canal influence on burnt peat from one site and four months.
- Who hosts SiPALAGA/PRIMS data after BRGM, and BPGMN's data mandate.
