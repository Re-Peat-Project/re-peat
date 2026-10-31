# 6 National prioritisation of 865 KHG

The national profile shows which *KHG* (*Kesatuan Hidrologis Gambut*, peat hydrological unit) should get rewetting attention first. It describes every KHG in the 2017 national KHG map and ranks those large enough to compare, using fire history, this year's hotspots and canal density, with fire counted on peat. For a shortlist, further layers on climate, land cover, surface water and land status are shown beside the score as context; they do not enter it.

The rankings in this chapter use default weights proposed by the project for agreement with KLH and the World Bank. The weights can be changed in the dashboard, which re-ranks the KHG at once.

KLH has a peat restoration target of about 3.3 million ha in 337 priority KHG, selected using the peat ecosystem damage status (SKEG), in particular burned land and land affected by canals (KLH/BPLH 2026). The ranking in this chapter is a separate exercise. It covers all 865 KHG and states its method and weights openly, so it can be compared with the list of 337 KHG or used alongside it. The list itself was not available to the project, so no comparison is made here.

{{diagram: national_flow | National profile: from national layers to the ranking, the shortlist layers and the dashboard | top-to-bottom flow, see diagrams/national_flow.drawio}}

## 6.1 Units and peat basis

The ranking covers almost all peat inside KHG, although only about half of the KHG are ranked. A KHG is ranked when it is at least 50 km² in area and has at least 25 km² of peat. Of the 865 KHG in the national map, 476 pass both tests; the other 389 are profiled but not ranked. The ranked KHG hold 180,004 km² of the 185,920 km² of peat that the peat extent places inside KHG.

Each KHG gets its area in an equal-area projection and its peat area from the Global Forest Watch (GFW) peat extent. For Indonesia that layer is the union of two published peat maps (Miettinen et al. 2016; Gumbricht et al. 2017), at about 76 m. All fire rates are per km² of peat, and fire is counted only on peat: a burned patch counts when its representative point falls on a peat cell, a hotspot when the cell under it is peat.

The Global Peatland Map (1 km, non-commercial licence) serves only as a cross-check. Its median peat share per KHG is higher than the GFW share on every island.

Table: Median peat share per KHG, GFW extent against the 1 km Global Peatland Map. Source: national profile dashboard data.

| Island | KHG (n) | GFW extent (share) | Global Peatland Map (share) |
|---|---|---|---|
| Kalimantan | 190 | 0.66 | 0.93 |
| Papua | 465 | 0.82 | 0.93 |
| Sulawesi | 3 | 0.06 | 0.64 |
| Sumatera | 207 | 0.74 | 0.97 |

## 6.2 Indicators

The score rests mainly on where peat has burned and where hotspots fall, with canal density as a measure of drainage. Seven indicators enter it, and fire history covers 2015 to 2025.

Table: Scored indicators of the national ranking and their default weights. Source: national profile report and its default settings.

| Indicator | Data | Unit | Weight |
|---|---|---|---|
| Burned share | burnt-area polygons with a burn flag per year, on peat | % of peat burned per year, mean 2015-2025 | 2 |
| Repeat burns | same | % of peat burned two or more times, 2015-2025 | 1 |
| Hotspot density | VIIRS S-NPP 375 m active fires (NASA FIRMS), vegetation fires, nominal and high confidence, on peat | hotspots per km² of peat per year | 1 |
| Hotspots this year | KLH hotspots (MODIS) 1 January to 15 September 2026, medium and high confidence, on peat | hotspots per km² of peat, year to date | 1 |
| Primary canals | canal layer, class from the canal code (*Kanal Primer*) | km per km² of KHG | 0.5 |
| Secondary canals | same (*Kanal Sekunder*) | km per km² of KHG | 0.3 |
| Tertiary canals | same (*Kanal Tersier*) | km per km² of KHG | 0.2 |

Hotspots are filtered by confidence. In the VIIRS archive, low-confidence detections and non-vegetation types (volcanoes, static sources, offshore) are dropped. The KLH hotspot data mix two confidence schemes across its nine monthly layers; both are mapped to low, medium and high, and low is dropped. Of 167,718 KLH points, 160,207 are medium or high, and 37,657 of these fall on peat inside a KHG. The dashboard can switch this year's indicator to high confidence only.

This year's hotspots are a separate indicator with their own weight. MODIS at 1 km and VIIRS at 375 m give counts that cannot be compared, so the 2026 record is kept apart from the history. It also has two ranks of its own, by density and by count, because density favours KHG with little peat and the count favours large ones. By density the top KHG is Sungai Tolak - Sungai Siduk (3.93 hotspots per km² of peat, 604 hotspots). By count it is Sungai Kahayan - Sungai Sebangau (2,538 hotspots on peat).

The three canal weights add up to 1, with more weight on the larger canals. The canal layer is derived from OpenStreetMap and is patchy: 517 of the 865 KHG have no canal segment in it, 213 of them among the 476 ranked KHG. Where no canals are mapped, the canal indicators are treated as missing rather than as zero, and the KHG is scored on its fire indicators alone.

Several further indicators are reported with weight 0: this year's burned share, fire radiative power (Spearman 0.99 with hotspot density), peat depth (the 1:50,000 depth map covers 100 of 865 KHG), existing hydrological structures, target villages, and the water table from SiTMAT, the online portal of daily peat water-table readings. SiTMAT concession stations lie in 164 KHG. For each, the profile reports the share of days with the water table deeper than 0.4 m, using stations with at least 30 days of valid readings in the 2026 season.

## 6.3 Scaling, score and classes

Fire dominates the score, and the classes of most KHG hold when the weights change. Each indicator is scaled from 0 to 1 between its 5th and 95th percentile over the ranked KHG, and values beyond those limits are clipped. The score is the weighted mean of the scaled indicators a KHG has. A KHG without mapped canals is therefore scored on the four fire indicators, with the weights renormalised. No impact indicator is scored at national level, so the score is the urgency score.

Classes are tertiles by rank: the top third of the 476 ranked KHG is "national focus: high" (158 KHG), the next third "medium" (159) and the rest "low" (159). A KHG with a score of zero is always "low".

Three pairs of scaled indicators correlate above 0.8 (Spearman), the level at which overlap is flagged: burned share and hotspot density 0.89, burned share and repeat burns 0.87, hotspot density and this year's hotspots 0.83. Fire therefore counts for more than the nominal weight of burned share (2 out of a total weight of 6).

Weight sensitivity was tested with 300 random weight sets drawn around the defaults (Dirichlet, concentration 20). In 89.3% of ranked KHG the class "high" either held in at least 80% of the draws or in at most 20%. The median standard deviation of rank across the draws is 13.1 places.

## 6.4 Held-out validation

The ranking picks out the KHG where peat burns later far better than chance, which supports its use for targeting fire-prone peat. The validation builds the indicators from 2015 to 2022, without this year's hotspots, and tests the ranking on fire in 2023 to 2025. It reports two measures for each target: the AUC, which is how well the score separates KHG with later fire from those without, and the share of later fire that falls in the top 20% of KHG (capture, weighted by KHG area; random choice gives 20%). Each measure is computed for the full score and for burned share alone ("fire history alone").

Table: Held-out validation of the national score, indicators 2015-2022, test years 2023-2025, 476 KHG. Source: validation report of the national profile.

| Target | KHG with the target | Score | AUC | Capture, top 20% | Spearman |
|---|---|---|---|---|---|
| Burned share of peat 5% per year or more | 10 | full score | 0.973 | 0.846 | 0.735 |
| | | fire history alone | 0.970 | 0.886 | 0.771 |
| Hotspots on peat (any) | 282 | full score | 0.956 | 0.771 | 0.829 |
| | | fire history alone | 0.882 | 0.815 | 0.784 |

Both scores point at later fire far better than chance. The full score separates KHG with and without later hotspots better than fire history alone (AUC 0.956 against 0.882). Fire history alone captures more of the later fire in its top 20% for both targets (88.6% against 84.6% of burned area, 81.5% against 77.1% of hotspots). The burned-share test rests on only 10 KHG that burned 5% or more of their peat per year in 2023 to 2025. The validation therefore shows that the ranking follows fire. It cannot settle the canal weights, because no held-out outcome measures drainage.

## 6.5 National ranking

The highest-priority KHG lie mostly in Kalimantan and Sumatera. Of the top 20 KHG, 11 are in Kalimantan, 8 in Sumatera and 1 in Papua. By province, Kalimantan Barat and Sumatera Selatan have 6 each. Ranking on KHG area instead of peat area keeps 14 of the top 20.

{{figure: national_rank_map | National rewetting priority score per KHG (default weights) | Choropleth map of Indonesia from re-peat/reports/national_profile/operational/profile.gpkg, field skor_risiko (0-1, sequential palette); KHG with peringkat empty (389 KHG not ranked, too small or too little peat) in neutral grey; outline the 13 KHG listed in table national_selected; inset or note: classes from field kelas.}}

{{table: national_top20 | Top 20 KHG of the national ranking (default weights) | re-peat/reports/national_profile/operational/profile.csv, rows with peringkat 1 to 20 sorted by peringkat; columns: peringkat (rank), nama (KHG), province, peat_km2 (peat, km², 0 decimals), u_fire_freq x 100 (burned share, % of peat per year, 1 decimal), u_burn_repeat x 100 (repeat burns, % of peat, 1 decimal), u_hotspot (hotspots per km² of peat per year, 2 decimals), u_hotspot_now (hotspots this year per km² of peat, 2 decimals), hs_now_high_share (share of this year's hotspots on peat with high confidence, %), u_canal_primary + u_canal_secondary + u_canal_tertiary shown as three columns (km per km², 2 decimals; empty = not mapped), skor_risiko (score, 2 decimals), sd_peringkat (rank SD in sensitivity runs, 1 decimal).}}

{{figure: national_yearly | Burned peat and hotspots on peat per year, all 865 KHG | Two stacked line panels sharing the x axis (year). Source re-peat/reports/national_profile/operational/yearly.csv, columns khg_id, year, metric, value. Panel 1: sum over all khg_id of value where metric = burned_peat_km2, years 2015-2025 (2026 left out: part year), km². Panel 2: sum over all khg_id of value where metric = n_hotspot_peat, years 2012-2025, hotspots per year. Lines only, no bars. Leave out the hs_now_* metrics.}}

Summed over all KHG, 11,346 km² of peat burned in 2015, 4,547 km² in 2019 and 2,861 km² in 2023, against 68 to 1,532 km² in the other years from 2016 to 2025. VIIRS hotspots on peat follow the same pattern, with 345,772 in 2015 and 166,389 in 2019.

## 6.6 Where the selected KHG rank

Most of the KHG selected for detailed work fall in the national high class. The project selected 12 main KHG and some reserves. Cawang-Lalang could not be matched to a KHG in the national boundary map and is left out. Of the other 11 main KHG, 10 are in the top third ("high") and Pulau Padang is in the middle third. Four main KHG are in the national top 25: Sungai Pungurbesar - Sungai Kapuas (rank 1), Sungai Balangan - Sungai Batangalai (4), Sungai Kahayan - Sungai Sebangau (7) and Sungai Mempawah - Sungai Peniti (21).

Table: Rank of the selected main and reserve KHG (default weights). Source: national profile.

| KHG | Role | Rank (of 476) | Class | Share of draws in class "high" |
|---|---|---|---|---|
| Sungai Pungurbesar - Sungai Kapuas | main | 1 | high | 1.00 |
| Sungai Balangan - Sungai Batangalai | main | 4 | high | 1.00 |
| Sungai Kahayan - Sungai Sebangau | main | 7 | high | 1.00 |
| Sungai Mempawah - Sungai Peniti | main | 21 | high | 1.00 |
| Sungai Saleh - Sungai Sugihan | main | 30 | high | 1.00 |
| Sungai Sugihan - Sungai Lumpur | reserve | 31 | high | 1.00 |
| Pulau Bengkalis | main | 69 | high | 1.00 |
| Sungai Mendahara - Sungai Batanghari | main | 71 | high | 1.00 |
| Sungai Air Hitam Laut - Sungai Buntu Kecil | main | 90 | high | 0.98 |
| Sungai Kapuas - Sungai Barito | main | 96 | high | 0.99 |
| Sungai Buru Mappi - Sungai Buru Obaa | main | 138 | high | 0.74 |
| Pulau Padang | main | 194 | medium | 0.08 |
| Pulau Tebing Tinggi | reserve | 204 | medium | 0.01 |

The low ranks of Pulau Padang and Pulau Tebing Tinggi come from little fire on their peat: their burned share is below 0.4% of peat per year. Sungai Buru Mappi - Sungai Buru Obaa has a low burned share (0.7% of peat per year), but its 920 hotspots on peat this year place it 12th of the ranked KHG by this year's count.

{{table: national_selected | Indicators of the selected KHG (default weights) | re-peat/reports/national_profile/operational/profile.csv, rows khg_id in (KHG.61.12-71.01, KHG.63.07-08-11.01, KHG.62.11-14.02, KHG.61.02-08.01, KHG.16.02-07.01, KHG.16.02.01, KHG.14.03.02, KHG.15.05-07-10.01, KHG.15-16.01, KHG.62.03-04.01, KHG.91.18-17.01, KHG.14.10.01, KHG.14.10.03), sorted by peringkat; role from re-peat/sites/selected_khg.csv (main or reserve); columns: nama, role, peringkat, kelas, peat_km2 (km²), u_fire_freq x 100 (% of peat per year), u_burn_repeat x 100 (% of peat), u_hotspot (per km² of peat per year), hs_now_kept (hotspots on peat 2026, count), hs_now_high_share (high-confidence share, %), peringkat_now_n (rank by this year's count), u_canal_primary, u_canal_secondary, u_canal_tertiary (km per km²), n_tma_stations, tma_deep_share (share of days deeper than 0.4 m), peringkat_area (rank on KHG area).}}

## 6.7 Context layers for the shortlist

Climate, land cover and surface water give context for the shortlisted KHG. These layers are coarse, so they are shown on the profile pages and not scored. The shortlist is the top 25 KHG and the selected KHG, 34 KHG in all. The layers are:

- TerraClimate dry-season water deficit (June to October) and monthly rain, 2015 to 2021, about 4 km; the dataset ends in 2021.
- ESA WorldCover land-cover shares, sampled at 250 m.
- JRC Global Surface Water: the share of cells with any water and with water in 10 or more months a year (permanent water).
- The GFW and 1 km peat shares, as a check.

Across the 34 KHG, the mean dry-season deficit runs from 5 mm (Krueng Pneunom - Krueng Lambalik) to 120 mm (Sungai Kahayan - Sungai Sebangau), and tree cover from 25% to 95% of the KHG. Dry-spell indicators from the ERA5 reanalysis are not used, because its 25 km grid cannot tell neighbouring KHG apart.

{{table: national_stage3 | Context layers of the selected KHG (shown, not scored) | re-peat/reports/national_profile/stage3/stage3_profile.csv joined to operational/profile.csv on khg_id for nama and peringkat; rows: the 13 khg_id of table national_selected; columns: nama, peringkat, deficit_mean_mm (mean dry-season deficit 2015-2021, mm), rain_mean_mm (mean annual rain 2015-2021, mm), rain_dry_mean_mm (June-October rain, mm), lc_tree, lc_crop, lc_grass, lc_wetland (shares of KHG, %), water_perm_frac (permanent water, % of KHG), peat_frac_gfw and peat_frac_gpm1km (peat share, %).}}

## 6.8 Land-status overlays

The land-status overlays show how much of the burned peat and of this year's hotspots lie inside licence areas or on peat with a protected function. For the same 34 KHG, the profile is crossed with four layers: forest area function (2023), peat ecosystem function (2017), business licences (2025) and the target villages for peat restoration. These overlays are context and do not enter the score. A regular grid of points is laid inside each KHG. The cell size grows with KHG area from 100 m, in 50 m steps, so that each KHG gets about 60,000 points. Each point carries its peat flag, its class in each layer, whether it burned between 2015 and 2025, and the licences it lies in. Areas are point counts times the cell area. Licences overlap, so licence areas are never summed; "any licence" counts each point once.

The figures say where burned peat and hotspots fall, and nothing about who caused a fire. The licence layer of 2025 is also matched with burns from 2015 onwards, when the holder may have been different. No holder names are given in this report.

The share of peat inside licence areas differs widely among the selected KHG. In Sungai Sugihan - Sungai Lumpur, 4,313 km² of peat (80% of its peat) lies in licence areas; 1,748 km² of that peat burned between 2015 and 2025, and 193 of the 213 hotspots on peat in 2026 fell inside licence areas. In Sungai Kahayan - Sungai Sebangau, licence areas hold 3.5% of the peat and 98 of the 2,538 hotspots on peat this year. Sungai Mempawah - Sungai Peniti had none of its 691 hotspots on peat inside a licence area. Sungai Buru Mappi - Sungai Buru Obaa (920 hotspots on peat) has no licence area in the 2025 layer.

Peat with a protected function holds most of this year's hotspots in several of the selected KHG: 128 of 146 in Sungai Saleh - Sungai Sugihan, where 92% of the peat has that function, and 1,636 of 1,825 in Sungai Pungurbesar - Sungai Kapuas.

{{table: national_overlay | Burned peat 2015-2025 and hotspots on peat 2026 inside licence areas and on protected peat function, selected KHG (context, not scored) | re-peat/reports/national_profile/stage3/overlay/overlay_summary.csv; rows: the 13 khg_id of table national_selected; for layer = licence_any, class = in: peat_km2 (peat in licence areas, km²), share_peat (% of the KHG's peat), burned_peat_km2 (km²), burned_share (%), hs_now_peat (count); for layer = feg, class = lindung: share_peat (%), hs_now_peat (count); total hotspots on peat from operational/profile.csv column hs_now_kept. No holder names (do not read overlay_actors.csv).}}

The overlay also draws a 5 km ring around licence areas, following the "Buffer 5 Kilometer" zone of the BlueBook 2026 canal-block data. No regulation setting a 5 km duty was found, so the ring is shown as a zone and implies no obligation.

## 6.9 Reading the ranking

Fire history decides the top of the national ranking. Canals and this year's hotspots mostly reorder KHG that already have a fire record. Seven of the 11 main selected KHG stay within the top 158 places, the size of the "high" class, under every weight preset in the dashboard. Pulau Padang and Pulau Tebing Tinggi stay below rank 170 under every preset. The figures in this section use the dashboard's own scoring at the default weights proposed by the project for agreement with KLH and the World Bank. These weights can be changed in the dashboard.

### What drives the top ranks

Each bar in the next figure splits a KHG's score into what its fire history, this year's hotspots and its canals add. Across the top 25, fire history gives 79 % of the summed score, this year's hotspots 12 % and canals 9 %. Fire history can add at most 0.67 to the score (its weights are 4 of the total of 6). Eleven KHG reach that maximum, all of them in the top 25: they rank at or above the 95th percentile on burned share, repeat burns and hotspot density. Among these KHG the order is set by this year's hotspots and by canals. Within the top 25, canals add the most at Barito-Taping (0.17), and two KHG have no mapped canal.

{{figure: nat_contrib | What each group of indicators adds to the national score, top 25 KHG and the selected KHG below them, default weights proposed for agreement with KLH and the World Bank (adjustable in the dashboard); rank before the name, selected KHG marked. Source: national profile, hotspots to 15 September 2026 | re-peat/reports/national_profile/dashboard_data.json (khg.v, params, meta.weights), scored as in the dashboard (compute() of dashboard.js) (project_report_dashboards.nat_contrib)}}

### How robust the ranks are to the weights

The dashboard offers four presets besides the default. History drops this year's hotspots. This year keeps only this year's hotspots. Canals keeps only the three canal densities, so only the 263 KHG with mapped canals can be scored. Equal gives every parameter, including this year's burned area, a weight of 1.

{{table: nat_presets_top25 | The dashboard's weight presets: weights, KHG that can be ranked, how many of the default top 25 stay in the top 25, selected KHG in the top 25, and the top 3 | re-peat/reports/national_profile/dashboard_data.json, scored as in the dashboard for each preset of buildControls() in dashboard.js (project_report_dashboards.nat_presets_top25)}}

The top of the list holds as long as fire history keeps its weight. Without this year's hotspots, 21 of the default top 25 stay in the top 25, and with equal weights 18. Scored on this year's hotspots alone, only 9 stay, and on canals alone 7. The validation in section 6.4 tested the fire indicators; nothing yet tests the canal weights, so the canal-only ranking is a view of drainage and carries no validated weight of its own.

{{figure: nat_rank_presets | Rank of the selected KHG under the dashboard's weight presets: Default, History (no indicators of this year), This year (hotspots this year only), Canals (canal indicators only) and Equal (all weights 1); grey bar: range across presets. Source: national profile, hotspots to 15 September 2026 | re-peat/reports/national_profile/dashboard_data.json, scored as in the dashboard (project_report_dashboards.nat_rank_presets)}}

For the selected KHG the presets separate three groups:

- Pungurbesar-Kapuas, Balangan-Batangalai and Kahayan-Sebangau rank in the top 7 at default weights and under History. Each drops under one preset: Balangan-Batangalai to 54 on this year's hotspots, Kahayan-Sebangau to 75 on canals.
- Mempawah-Peniti (21 at default weights) rises under every preset that weighs this year or canals more: 10 on this year's hotspots, 6 on canals, 3 with equal weights. Saleh-Sugihan and Sugihan-Lumpur (30 and 31) rise to 23 and 24 on fire history alone and fall to 151 and 193 on this year's hotspots.
- Buru Mappi-Buru Obaa ranks 138 at default weights and 49 on this year's hotspots. Pulau Padang and Pulau Tebing Tinggi stay between 171 and 269 under every preset.

### How the selected KHG compare

The next figure places each team KHG among the ranked KHG on every parameter of the dashboard, as the strip plots of its profile page do. Most indicators compare with all 476 ranked KHG (repeat burns with the 287 that have a value), canal densities with the 263 that have mapped canals. Saleh-Sugihan is at the 99th percentile for burned share and repeat burns, and Sugihan-Lumpur at the 96th for burned share. Both are low on this year's hotspots (68th and 59th). Mempawah-Peniti is at the 98th percentile for this year's hotspots and, among KHG with mapped canals, for secondary and tertiary canal density. Pulau Padang and Pulau Tebing Tinggi are at the 70th and 68th percentiles for burned share: 217 of the 476 ranked KHG have no burned peat at all, so a small burned share still places them in the upper half.

{{figure: nat_team_percentiles | Position of the selected KHG among the ranked KHG on each dashboard parameter (percentile: share of the ranked KHG with a value that have a lower one; n in the header), with the default weight of each parameter; rows by rank. Source: national profile, hotspots to 15 September 2026 | re-peat/reports/national_profile/dashboard_data.json (khg.v), ranked KHG at default weights (project_report_dashboards.nat_team_percentiles)}}

The yearly lines of the profile pages show what lies behind these positions. The 2015 fires burned 42.6 % of the peat in Saleh-Sugihan, 38.9 % in Kahayan-Sebangau and 37.0 % in Sugihan-Lumpur. Saleh-Sugihan burned again in 2019 (28.3 %) and 2023 (11.9 %), and Kahayan-Sebangau in 2019 (17.6 %), while Sugihan-Lumpur has burned at most 5.5 % a year since 2015. Pungurbesar-Kapuas burns in most years, with 16.6 % in 2018, 11.0 % in 2023 and 8.0 % in the part of 2026 covered so far. In Mempawah-Peniti and Pulau Bengkalis, 6.0 % of the peat has burned in that part of 2026, more than in any full year since 2015. This year's burned area enters the score only through the Equal preset.

This year's hotspots come in different months. Pungurbesar-Kapuas had 710 of its 1,825 hotspots on peat in March, Pulau Bengkalis 389 of 674 in February, Buru Mappi-Buru Obaa 703 of 920 in July, and Kahayan-Sebangau 1,333 of 2,538 in the first half of September (the record ends on 15 September). TerraClimate puts the largest dry-season water deficit of 2015 to 2021 in 2015 for 9 of the 13 KHG, up to 403 mm in Sugihan-Lumpur.

{{figure: nat_team_profiles | Profile lines of the selected KHG, rows by rank: burned share of peat per year 2015-2025 with 2026 as a partial year (hollow point), KLH hotspots on peat per month from January to 15 September 2026, and TerraClimate dry-season water deficit 2015-2021. Each column has one scale for all rows; the label gives the peak. Source: national profile, hotspots to 15 September 2026; TerraClimate | re-peat/reports/national_profile/dashboard_data.json, profiles.<khg_id>.burned, .now_m (second value: on peat), .deficit (project_report_dashboards.nat_team_profiles)}}

### The dashboard

The ranking is published as one self-contained page in English and Bahasa Indonesia, so that KLH can test its own weights. Sliders set the weight of each of the eight parameters, or a preset sets them all at once. The page re-ranks all KHG at once with the same scaling as the national ranking and shows the rank shift against the default weights. Filters set the minimum peat area, the island, the hotspot confidence and how a KHG without mapped canals is treated. A profile page for each of the 34 shortlisted KHG holds the strip plots, the yearly lines, a map of burns, canals, this year's hotspots and land status, and a sortable table with a CSV download. The page address stores the weights, filters, language and selected KHG, so any view can be shared as a link.

{{figure: screen_national_ranking | The national dashboard: weight sliders by group and the ranking with the contribution of each group, at default weights proposed for agreement with KLH and the World Bank. Source: national profile, hotspots to 15 September 2026 | cropped screenshot of re-peat/reports/national_profile/dashboard.html, elements #controls and #rank (project_report_dashboards.screen_national_ranking)}}

## 6.10 Limits

- The weights are defaults proposed for agreement with KLH and the World Bank; a different weighting changes the order, although most classes hold (section 6.3).
- The canal layer is missing for 517 KHG, so drainage plays no part in their score.
- Peat depth, concessions, tidal influence, fire severity and feasibility are not scored.
- The context layers and land-status overlays cover only the 34 shortlisted KHG.
- The burnt-area polygons carry the largest weight and are also the validation target, but their source is not documented, so their accuracy cannot be judged.
- The validation tests prediction of fire only. No held-out data can yet test the drainage part of the score.
