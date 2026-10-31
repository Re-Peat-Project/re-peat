# 3 Data curation and inputs

## 3.1 Data inventory

The study combines three kinds of data. National layers cover all 865 *KHG* (*Kesatuan Hidrologis Gambut*, peat hydrological units): boundaries, canals, burned area, hotspots, peat extent and land status. Other datasets exist for some KHG only, such as LiDAR terrain models, modelled peat depth and water-table stations. Global satellite products for rain, evapotranspiration, land cover, surface water and elevation come from Google Earth Engine, Microsoft Planetary Computer and other public archives.

For every dataset the inventory records units, resolution, source, date and licence. Where a source is incomplete, it states how far the data can be trusted. Peat depth, for example, covers only part of most KHG, so it is reported and does not drive a ranking.

For the analysis of a single KHG, every national input is clipped to the KHG plus a 5 km buffer: the boundary, canals, rivers, lakes and existing canal blocks; burned area, hotspots, peat extent and the other national layers; the KHG's peat-depth raster; the SiTMAT stations within the area; and the ICESat-2 ground points. Each clip is listed with its source, so the inputs of one KHG can be handed over and the analysis repeated without the national data. At Mendahara-Batanghari the fire, hotspot, canal and peat-share indicators computed from the clipped inputs equal those computed from the national layers, with a largest difference of 4e-16.

The satellite sources (Earth Engine, Planetary Computer, SlideRule, and the land-cover and canopy-height tiles on public cloud storage) are read from the provider at the time of analysis. A later repeat of the analysis can therefore differ slightly where a provider has updated its archive.

## 3.2 Datasets used in the analysis

Table 3.1 lists the datasets by theme. "Not recorded" means the source documentation gives no value for that property. Two datasets carry non-commercial licences, FABDEM and the Global Peatland Map, and both are used only as checks.

Table: Datasets used in the RE-PEAT analysis. Source: RE-PEAT data inventory, the *neraca air* (water balance) method report, the *sub-KHG* prioritisation method and the national profile method.
| Dataset | Provider | Type and resolution | Period | Licence | Used for | Confidence and limits |
|---|---|---|---|---|---|---|
| KHG boundaries and registry | KLHK, SK.129/MENLHK/2017 | Polygons, 865 KHG; registry of codes, names, provinces and areas | 2017 | Not recorded | Unit of every analysis; clipping of all inputs | Boundary file has names only; codes are joined from the registry. Some names have irregular spacing |
| Canal network | OSM-derived (inferred) | Lines, classed primary, secondary and tertiary | 2025 | Not recorded | Canal density by class; outlet canals in delineation; canal reach and blocks needed; block placement; canal boundary of the groundwater model | Provider inferred from the delivered data; no flow direction |
| Rivers and lakes (RBI) | BIG, Rupa Bumi Indonesia | Lines and polygons | Not recorded | Not recorded | Fixed boundaries in delineation; distance to water; water sources | Scale and year to be confirmed; no field for perennial flow or dry-season level |
| Existing canal blocks | BRGM/PPEG, Bluebook 2026 | Points of hydrological infrastructure; canal blocks marked as realised are used | Not recorded | Not recorded | Existing blocks in the block-gap indicator and the interventions module; counts in the national profile | Completeness per KHG to be checked; at Pulau Tebing Tinggi none of the 168 blocks has a build year |
| Proposed canal blocks, Bluebook 2026-2030 | KLH/BRGM | Points by province, placed on LiDAR, BRGM or DEMNAS contours | 2026 | Not recorded | Data readiness review only | Targets, not built. The Riau file placed on BRGM contours has no attributes |
| Peat extent, GFW composite | Global Forest Watch | Raster, about 76 m | Layer version 2023-03-15 | CC BY 4.0 | Peat area per KHG; fire counted on peat | Mapped extent, not a survey. Union of two published peat maps, so it can exceed either; Papua rests on the modelled map |
| Global Peatland Map 2.0 | Greifswald Mire Centre, UNEP | Raster, about 1 km | 2022 | CC BY-NC-SA 4.0, **non-commercial** | Cross-check of the GFW extent only | Coarse; licence to be checked before use in a deliverable |
| Peat depth classes | BBSDLP (inferred) | Polygons, 1:50,000; classes from 50-100 cm to over 700 cm | 2011-2019 | Not recorded | Reported in the national profile with weight 0; fallback depth in the groundwater model | **Covers 89 of 865 KHG**; must not drive a ranking |
| Modelled peat depth per KHG | KLHK Direktorat Gambut archive; modeller not stated | Raster per KHG, about 10 m, about 70 KHG in Sumatra and Kalimantan | Not recorded | Not recorded | Peat depth per sub-KHG (reported), the interventions module and the groundwater model | **Partial**: 53 % to 96 % of each selected KHG where present; none for Kahayan-Sebangau, Kapuas-Barito and Buru Mappi-Buru Obaa. Unit not stated (values suggest cm). Correlation 0.10 with the 2015 Tebing Tinggi cores |
| DEMNAS | BIG | Surface model, about 8.3 m, float metres above EGM2008; 143 map sheets | Not recorded (sheets obtained 25 and 26 October 2026) | Not recorded | DEMNAS variant of the chain, after correction | Includes canopy. No-data value differs by sheet. Older Sumatra copy is resampled and lossy, the Kalimantan mosaic is in whole metres |
| KLHK LiDAR DTMs | KLHK Direktorat Gambut LiDAR archive; Berbak-Muba DTM by Deltares | Bare-earth DTMs, 25 m (Riau, Jambi, Musi Banyuasin, OKI, Kalimantan Barat) and 20 m (Sugihan-Saleh) | Archive 2015-2024; Sugihan-Saleh 2020; Berbak-Muba 2018 | Not recorded | LiDAR variant of the chain; reference for the DEM benchmark | Used as delivered. Two Sugihan-Saleh copies carry a wrong coordinate-system label |
| Pulau Padang LiDAR | UGM study of 2018; acquisition provider not stated | Bare-earth DTM, 2 m | Flown November 2016 | Not recorded | Reference in DEM comparisons; not used in the analysis chain | Stated RMSE 0.35 m against GPS; no vertical datum in the file, about 2.0 m below EGM2008 ICESat-2 heights |
| Copernicus DEM GLO-30 | ESA | Surface model, 1 arcsec (about 30 m) | TanDEM-X 2011-2015 | Not recorded | DEM benchmark only | Includes canopy |
| FABDEM v1.2 | Hawker et al. 2022 | GLO-30 with forests and buildings removed, 1 arcsec | 2023 | CC BY-NC-SA 4.0, **non-commercial** | DEM benchmark only | Non-commercial licence |
| DeltaDTM v1.1 | Deltares (Pronk et al. 2024), through Earth Engine | Coastal bare-earth DTM, 1 arcsec | 2024; inputs to 2023 | CC BY 4.0 | DeltaDTM variant of the chain, after correction | Defined for land below 10 m; the Earth Engine copy stops at 30.00 m |
| Canopy height | Meta and WRI | Raster, 1.19 m | 2024 | CC BY 4.0 | Canopy term of the DEMNAS correction | No no-data value declared |
| ICESat-2 ATL08 | NASA/NSIDC, through SlideRule | Ground heights on 100 m segments, ellipsoidal | 2019-2025 | Not recorded | Calibration and validation of the DEM correction | Never used as truth; some granules could not be retrieved, so coverage can be slightly incomplete |
| GEDI L2A | NASA, through Earth Engine | Ground elevation in 25 m cells | 2019-2025 | Open data | Tested; not used by the chain | Noisy under peat forest: NMAD 4.06 m and 5.02 m against LiDAR at two KHG |
| Hotspots, FIRMS VIIRS | NASA FIRMS | Points, 375 m | 2012-2025 | Not recorded | Hotspot density in both rankings; held-out validation | One satellite (S-NPP), one overpass pair a day; vegetation fires of nominal and high confidence kept |
| KLH hotspots 2026 | KLH (curated), MODIS | Points, 1 km | 1 January to 15 September 2026 | Not recorded | This year's hotspot indicator, with its own weight | Medium and high confidence kept. Not comparable in counts with VIIRS; radiative power in 4 of 9 months; left out of held-out validation |
| Burned area | Not recorded | Polygons with yearly flags and burn frequency | 2015-2026 | Not recorded | Fire frequency and repeat burns in both rankings; burned area in the interventions module | Provenance not recorded; 584,000 polygons |
| Business licences | Project team; issuing agency not stated | Polygons by licence type | 2025 | Not recorded | Overlays (context, not scored); managed land in the groundwater model | Licence types overlap; areas are not summed |
| Peat ecosystem function (FEG) | KLHK (inferred) | Polygons, protected or cultivation function | 2017 | Not recorded | Protected-peat share per sub-KHG, which sets the canal-closing class in the interventions module; overlays | Indicative function |
| Forest area function | KLHK (inferred) | Polygons, 1:250,000 | 2023 | Not recorded | Overlays (context) | 173 polygons undefined |
| Target villages for peat ecosystem restoration | BRGM, Bluebook 2026 | 2,004 village polygons | 2026 | Not recorded | Counts in the national profile; overlays (context) | None noted |
| DPG atlas villages | BRG atlas; boundaries from KLH village boundaries 2023 | 244 villages, 243 with a polygon | Mapping June 2018 to July 2019 | Not stated | Overlays (context, not scored) | Not an official DPG or DMPG layer (section 3.5) |
| SiTMAT water-table stations | SiTMAT portal (concession and community stations) | Daily water level per station, cm | 1 April to 22 October 2026 | Not recorded | KHG deficit; water-table indicators per sub-KHG; groundwater model checks; national profile (shown) | One season; community coverage 27 %; see section 3.4 |
| CHIRPS daily rain | UCSB Climate Hazards Center, through Earth Engine | 0.05° (5.6 km), mm/day | 1981 to 30 September 2026 | Public domain | Rain of the climatic balance and the groundwater model | Rain taken as the KHG mean |
| MOD16A2GF evapotranspiration | NASA LP DAAC, through Earth Engine | 500 m, 8-day | 2000 to December 2025 | No restrictions | Central ET of the climatic balance | Ends in December 2025 |
| MOD16A2 evapotranspiration, not gap-filled | NASA LP DAAC, through Earth Engine | 500 m, 8-day | 2021 to 8 October 2026 | No restrictions | ET of groundwater model runs in 2026 | Gaps not filled |
| WaPOR v3 actual ET | FAO, through Earth Engine | 326 m, dekadal | 1 January 2018 to 11 October 2026 | Free use | Second ET source of the climatic balance | Includes interception; annual totals below measured ET on peat |
| TerraClimate | Through Earth Engine and Planetary Computer | About 4 km, monthly | Earth Engine copy to December 2024; Planetary Computer copy to December 2021 | CC0 | Climate shown on the national profiles (not scored); reproduction of the 2021 Kahayan-Sebangau water balance | Coarse: separates regions, not neighbouring KHG |
| ERA5 | Copernicus | 0.25°, hourly, summed to days | Period of each analysis (2026 for the deficit) | Copernicus | Rain and evaporation of the KHG deficit | Dropped from the national dry-spell indicators and off in the sub-KHG ranking (section 3.3) |
| ESA WorldCover | ESA WorldCover consortium | 10 m land-cover classes | 2020 and 2021 releases | CC BY 4.0 | Interception in the balance; forest share in the sub-KHG ranking; masks and class offsets in the DEM correction; national profiles | Sampled at 250 m for the national profiles |
| JRC Global Surface Water | European Commission Joint Research Centre | 30 m, months with water per year | Version 1.3 (2020 release) | Not recorded | Distance to permanent water in the sub-KHG ranking; permanent water share on national profiles (shown) | None noted |
| Sentinel-2 L2A | ESA, through Planetary Computer | 20 m bands read onto a 30 m grid | Dry season (August to October) of each baseline year | Not recorded | NDMI and NDVI per sub-KHG (reported); moisture layer of the interventions module | Not used for the national profiles, where processing all KHG would be too costly |
| Pulau Tebing Tinggi field survey | KLHK coring team | 1,385 points with peat thickness, water table and chemistry | Late 2015 | Not recorded | Field check of the groundwater model | Exact survey date not recorded; water-table depths differ more by field team than by place |

### What the sources mean for confidence

The national ranking rests on the layers that cover all 865 KHG: boundaries, canals, burned area, hotspots, peat extent, land status and climate. Layers that cover only part of the country, peat depth and LiDAR above all, are used inside a KHG where they exist and are reported without a score at national level. The rankings use default weights proposed by the project for agreement with KLH and the World Bank, and the weights can be adjusted in the dashboard.

Two inputs need particular care. The modelled peat depth has no stated unit or modeller, and at Pulau Tebing Tinggi it agrees poorly with the 2015 field cores: across 881 peat points inside the raster the correlation is 0.10 and the mean absolute difference is 302 cm, and at the 207 mineral-soil points the raster gives a median of 630 cm of peat. The burned-area polygons, which drive the fire indicators, have no recorded provider or method.

## 3.3 Which input each step uses

Table 3.2 shows which inputs each step of the analysis uses, and whether an input enters the result or is only reported.

Table: Inputs used by each step of the analysis (x = used in the result; c = reported, or shown as context, but not in the ranking score or the physics; b = benchmark or check only). Source: RE-PEAT analysis settings for the selected KHG and the methods of each module.
| Input | DEM correction | Delineation | Neraca air balance | KHG deficit | Groundwater model | National prioritisation | Sub-KHG prioritisation | Interventions |
|---|---|---|---|---|---|---|---|---|
| KHG boundary | x | x | x | x | x | x | x | x |
| DEM (corrected DeltaDTM or DEMNAS, or LiDAR) | x | x | | | x | | c | x |
| ICESat-2 ground points | x | | | | | | | |
| Canopy height | x (DEMNAS only) | | | | | | | |
| ESA WorldCover | x | | x | | | c | x | |
| GLO-30, FABDEM, GEDI | b | | | | | | | |
| Sub-KHG units | | | x | | x | | x | x |
| Canals by class | | x | | | x | x | x | x |
| Rivers and lakes | | x | | | | | x | x |
| Existing canal blocks | | | | | | c | c | x |
| CHIRPS rain | | | x | | x | | | |
| MOD16 evapotranspiration | | | x | | x | | | x (optional stage) |
| WaPOR evapotranspiration | | | x | | | | | |
| ERA5 rain and evaporation | | | | x | | | | |
| SiTMAT stations | | | | x | x (checks) | c | c | c |
| Peat depth (modelled; BBSDLP fallback) | | | | | x | c | c | x |
| GFW peat extent | | | | | | x | x | |
| Global Peatland Map | | | | | | b | | |
| Burned area | | | | | | x | x | x |
| VIIRS hotspots | | | | | | x | c | |
| KLH hotspots 2026 | | | | | | x | x | |
| Peat ecosystem function | | | | | c | c | c | x |
| Business licences | | | | | x | c | | |
| Forest area function | | | | | c | c | | |
| Target and DPG villages | | | | | | c | | |
| Sentinel-2 | | | | | | | c | x |
| JRC surface water | | | | | | c | x | |
| TerraClimate | | | | | | c | | |
| Neraca air outputs | | | | | | | c | x |
| Tebing Tinggi field survey | | | | | x (checks) | | | |

Notes on the matrix:

- The DEM correction calibrates against ICESat-2 only; GEDI is not used. For DeltaDTM every canopy factor is zero, so canopy height affects only the DEMNAS correction. LiDAR is used as delivered.
- The climatic balance uses the gap-filled MOD16, which ends in December 2025, and WaPOR. Only the groundwater model uses the MOD16 series without gap filling, for 2026.
- The KHG deficit is a mass balance on ERA5 rain and evaporation and the observed change in station water levels. The DEM, peat depth and canals appear in its diagnostic reports but do not enter the deficit.
- The groundwater model is in development and is not yet part of the analysis chain. It holds managed land (plantation licences) at a target water table.
- The sub-KHG need score uses canal reach, distance to permanent water, forest share, repeat burns, this year's KLH hotspots and canal density by class. NDMI, NDVI, peat depth, VIIRS hotspots and the neraca air P minus ET enter only the rank-sum score of the earlier method, which is computed alongside for comparison. The water-table indicators, protected share, DEM-based lift and block gap are reported per sub-KHG. Fire and canal indicators come from the national layers clipped to the KHG; the online burned-area product, online hotspot data and the TerraClimate deficit are not used. No settlement or road layer is used, so exposure and access are not assessed.
- The interventions module requires a DEM, a moisture layer (the Sentinel-2 NDMI of the prioritisation), the sub-KHG units and the canals. Pumping can be designed only where the river layer shows which rivers flow in the dry season. The RBI river layer has no such field, so the module designs canal blocks without pumping. The neraca air map appears only in its report.
- In the national profile, peat depth, SiTMAT, BRGM structures, villages and the land-status layers are reported or shown as context and carry no weight.

ERA5 is used in one step only. It was dropped from the national dry-spell indicators because its 25 km cells cannot separate neighbouring KHG and its hourly archive was too slow to read for all 865 KHG. It is not used in the sub-KHG ranking, where the rain indicators carry weight 0. For the KHG deficit it remains the adopted forcing, because its evaporation total matches MOD16 and its rain is as close to the IMERG reference as CHIRPS. The groundwater model uses CHIRPS and MOD16 instead, the same products as the climatic balance.

## 3.4 Water table from SiTMAT stations

The SiTMAT stations show that in 2026 the water table in concessions stayed close to the -40 cm limit and fell slowly through the dry season, while the community stations, outside the concessions, sat far deeper from mid-August, when their record starts. In 14 of the 18 KHG that have both kinds of station the community stations are deeper, by a median of 86 cm in those 14. Rewetting outside managed land therefore starts from a much lower water table than inside it, and the drawdown in managed land is concentrated in Kalimantan Tengah and Sumatera Selatan.

SiTMAT is an Indonesian online portal of peatland water-table readings. Its data were extracted into daily tables per station for 1 April to 22 October 2026 (205 days). It is the only water-table record available to the project, and it covers one dry season. The project built an explorer page on these records. The figures in this section use the explorer's methods and default settings.

### Data and quality

{{table: sitmat_quality | SiTMAT stations and data quality, 1 April to 22 October 2026 | Parsed from repeat-sitmat/sitmat_out/processed/qc_report.txt (stations with data, coverage window, mean coverage, stations under 50 %, range and spike flags per kind) and repeat-sitmat/baseline_out/baseline_report.txt (kept / with valid data, median of station medians, Sangat Rawan share); last row: panel and stations with a weekly median from the explorer method (project_report_dashboards.derive)}}

The station counts in this table follow three definitions. "Stations in the extract" are all stations with rows in the extract, with or without a valid reading. The cleaned baseline keeps stations with enough valid days up to 14 October. The analysis below uses stations that have at least one weekly median: 1,132 concession and 48 community stations.

The data have four known weaknesses:

- The record is short. Six months cover one dry-season drawdown and the start of the wet season, so trends cannot be separated from the season.
- Concession stations reporting per day fall from about 740 in April to about 400 in October.
- Rain and soil moisture are zero in every concession row, so the portal gives no rainfall.
- Community stations have low coverage, many flags, and status classes that do not follow the -40 cm and -80 cm breaks. Some stations have bad coordinates and are left out of spatial work.

The chain therefore uses concession stations only, and drops readings flagged out of range or as spikes, unless a run asks for community stations.

The community record has a further problem. Its first readings, from 21 July, come from a few stations. Eight of the nine stations that report through July read 0 to +3 cm, and after a gap in early August the same stations read between -82 and -200 cm. The July values are placeholders. The community series in this section therefore start on 19 August, the first week from which at least half of the community stations report in every following week. Stations whose weekly level never changes look like stuck loggers: 11 concession panel stations over the season and one community panel station from 19 August; leaving them out moves the shares below -40 cm and -80 cm by 3 percentage points or less, so they are kept.

### How the record is read

Stations start and stop reporting through the season, so a plain median of whoever reports on a day would mix a change in the water table with a change in which stations report. The analysis avoids this in four steps:

1. Each station's daily readings are reduced to a weekly median, for weeks with at least 3 valid readings. Flagged readings are dropped.
2. A fixed panel is kept: stations with a weekly median in at least 60 % of the weeks and a start level, the median of their first 4 weeks (at least 2 of them valid).
3. Each panel station is compared with its own start level. The median of these changes across the panel, with the middle 50 % of stations, gives the change since the start. Stations that join or leave cannot move this line.
4. Trends are Theil-Sen slopes of the weekly series, tested with the Mann-Kendall test at 95 %. A station is "clearly falling" when its own trend is negative and significant.

The share of stations below -40 cm and below -80 cm is counted each week on the same panel. Duration curves pool all daily readings of the panel in the first and the last third of the window and show how often each level is reached. The longest dry spell is the longest run of days below -40 cm at a station; gaps of up to 2 days without a reading do not break a run.

### The water table through the 2026 dry season

In the 525 concession panel stations, the median water table in the last 4 weeks was 2.7 cm lower than in the first 4 weeks of April. The fall is small but steady: the trend is -0.22 cm per week and significant. It is uneven across stations. By October the middle half of the stations ranged from 11.5 cm lower to 12.3 cm higher than their own start, and 49 % of the stations fell significantly while 12 % rose.

{{figure: sitmat_change | Change in water level since the start, median of the panel stations against each station's own first 4 weeks, with the middle 50 % of stations shaded. Left: concession stations, 1 April to 22 October 2026. Right: concession and community stations from 19 August. Source: SiTMAT, April to October 2026 | repeat-sitmat/sitmat_out/processed/daily_long.csv (water_level_cm, flag), weekly medians and panel as in the SiTMAT explorer (project_report_dashboards.sitmat_change)}}

The share of concession panel stations below -40 cm moved with the season more than the median did. It was 33 % in the first two weeks of April, fell to 5 % in the week from 20 May, rose to 48 % in the week from 29 July, and was 35 % in the last two weeks. Very few concession stations went below -80 cm: 2 % at the start and 3 % at the end. Among community stations, 83 % were below -40 cm and 56 % below -80 cm in the first two weeks from 19 August, and 72 % and 47 % in the last two weeks.

{{figure: sitmat_share_below | Share of panel stations with a weekly median below -40 cm and below -80 cm, concession stations from 1 April and community stations from 19 August 2026; end labels give the number of panel stations. Source: SiTMAT, April to October 2026 | repeat-sitmat/sitmat_out/processed/daily_long.csv, weekly class shares of the panel (project_report_dashboards.sitmat_share_below)}}

The duration curves show where the change happened. In concessions, 16 % of the daily readings were below -40 cm from 1 April to 7 June, against 41 % from 16 August to 22 October; below -80 cm the shares were 1 % and 5 %. The curves hardly differ above -40 cm: water management keeps most of the concession readings in a narrow band near the limit, and the dry season pushes the deepest third of the readings below it. The community curves for 19 August to 8 September and for 2 to 22 October lie on top of each other, with three quarters of the readings below -40 cm in both.

{{figure: sitmat_duration | Duration curves of the daily water level of the panel stations, first third against last third of the window (share of readings at or above each level), with the -40 cm and -80 cm lines. Left: concession, 1 April to 22 October 2026. Right: community, 19 August to 22 October. Source: SiTMAT, April to October 2026 | repeat-sitmat/sitmat_out/processed/daily_long.csv, pooled daily readings of the panel (project_report_dashboards.sitmat_duration)}}

A weekly median does not show how long a station stays below the limit. Of the 525 concession panel stations, 112 never went below -40 cm. For the others the median longest run below -40 cm was 23 days; 76 stations stayed below for more than 60 days in a row and 61 for more than 90 days.

{{figure: sitmat_dry_spell | Longest run of consecutive days below -40 cm per concession panel station, 1 April to 22 October 2026 (gaps of up to 2 days do not break a run). Source: SiTMAT, April to October 2026 | repeat-sitmat/sitmat_out/processed/daily_long.csv, panel stations (project_report_dashboards.sitmat_dry_spell)}}

### Where the water table fell

Four provinces carry the drawdown in concessions. In Kalimantan Tengah the provincial median fell by 1.14 cm per week (28.5 cm since the start), and the share of stations below -40 cm rose from 15 % to 56 %. In Sumatera Selatan the median fell by 0.59 cm per week (12.0 cm), and the share below -40 cm rose from 19 % to 85 %. Jambi and Kalimantan Barat fell by about 0.25 cm per week. In Jambi 98 % of the panel stations fell significantly, yet the median level ended at -40 cm. Riau, with 221 of the 525 panel stations, shows no trend.

{{figure: sitmat_province_trend | Trend of the water level per province, concession panel stations, 1 April to 22 October 2026: Theil-Sen slope of the provincial median change (filled: significant at 95 %) and the middle 50 % of the station trends; provinces with at least 5 panel stations, panel stations in brackets. Source: SiTMAT, April to October 2026 | repeat-sitmat/sitmat_out/processed/daily_long.csv and stations_geo.csv (adm1), regional statistics as in the SiTMAT explorer (project_report_dashboards.sitmat_province_trend)}}

{{table: sitmat_provinces | Water table per province, concession stations, 1 April to 22 October 2026 | repeat-sitmat/sitmat_out/processed/daily_long.csv and stations_geo.csv (adm1); per province with at least 5 panel stations: stations and panel stations, level now, change since start, trend and significance, share below -40 cm in the first and last 2 weeks, share of stations clearly falling, community stations from 19 August (project_report_dashboards.sitmat_provinces)}}

{{figure: sitmat_station_map | SiTMAT stations in Sumatra and Kalimantan by share of days with the water table below -40 cm: concession stations (circles), 1 April to 22 October 2026, and community stations (triangles), 19 August to 22 October; stations with at least 20 valid days. KHG boundaries in grey. Source: SiTMAT, April to October 2026; KHG map 2017 | repeat-sitmat/sitmat_out/processed/daily_long.csv, stations.csv (lon, lat); repeat-sitmat/assets/geo/adm1.geojson; _data/batas_khg_indonesia.gpkg (project_report_dashboards.sitmat_station_map)}}

### Managed land and community land

Concession stations and community stations describe two different situations. Over the common window from 19 August, the median concession station did not change (0.0 cm) and neither did the median community station (+0.3 cm, not significant). The difference is one of level. In the first and the last two weeks of that window, 38 % and 43 % of the concession stations were below -40 cm, against 83 % and 72 % of the community stations.

The 18 KHG that hold both kinds of station make the comparison inside one hydrological unit. Mean concession levels range from -61.9 cm to -28.8 cm. In 14 of the 18 KHG the community stations are deeper, by a median of 86 cm in those 14, and in 11 KHG the community mean is below -100 cm. Many of these points rest on one or two community stations (36 community against 184 concession stations in all), so a single KHG point shows the direction of the difference more reliably than its size.

{{figure: sitmat_sharing | Mean water level of concession and community stations in the same KHG, 19 August to 22 October 2026, KHG with both kinds of station; numbers of concession and community stations in brackets. Source: SiTMAT, August to October 2026 | repeat-sitmat/sitmat_out/processed/daily_long.csv and stations_geo.csv (khg_name); mean of the station means per kind and KHG, any station with a valid reading, as in the explorer (project_report_dashboards.sitmat_sharing)}}

Concessions also differ among themselves. Of the 122 concessions with at least three stations, the median concession had its water table below -40 cm on 11 % of the days, 27 never went below, 15 were below on half the days or more, and 6 on 80 % or more. The provincial medians run from 0 % in Kalimantan Utara and Sumatera Barat to 21 % in Sumatera Selatan and 27 % in Kalimantan Tengah. Concessions are shown here as a distribution; the report does not name them.

{{figure: sitmat_concessions | Share of days with the water table below -40 cm per concession (mean of its stations with at least 20 valid days; concessions with at least 3 stations), by province, 1 April to 22 October 2026; number of concessions in brackets. Concessions are not named. Source: SiTMAT, April to October 2026 | repeat-sitmat/sitmat_out/processed/daily_long.csv, stations.csv (company_code, used only for grouping) and stations_geo.csv (adm1) (project_report_dashboards.sitmat_concessions)}}

### Coverage of the selected KHG

Station coverage of the selected KHG is uneven. Sugihan-Lumpur has 54 concession stations and no community station; its panel of 51 stations fell by a median of 14.6 cm from April to October (the station mean over the dry-season deficit window of chapter 8 fell about 11 cm), and its stations spent 60 % of the days below -40 cm. Mendahara-Batanghari has 15 concession and 10 community stations with data. Its concession panel fell by 4.8 cm and its community panel by 4.7 cm from 19 August (on the screened record of the 6 community stations off canal cells used in chapter 8, the fall from 19 August to 30 September is 11 cm), but the community stations spent 49 % of the days below -40 cm against 13 % for the concession stations. Saleh-Sugihan, Mempawah-Peniti, Balangan-Batangalai and Buru Mappi-Buru Obaa have no station inside the KHG, so no station-based deficit can be computed for them.

Station counts in this report differ by date and filter: the deficit at Sugihan-Lumpur uses 51 stations, and the groundwater model scores 33 that are not on canal or edge cells.

{{table: sitmat_selected_khg | SiTMAT stations in the selected KHG: concession stations and panel, change since the start, share of days below -40 cm (concession 1 April to 22 October 2026, community from 19 August) | repeat-sitmat/sitmat_out/processed/daily_long.csv and stations_geo.csv (khg_name matched to re-peat/sites/khg_registry.csv for the KHG in re-peat/sites/selected_khg.csv) (project_report_dashboards.sitmat_selected_khg)}}

{{figure: screen_sitmat_overview | The SiTMAT explorer, a page built for this project from the SiTMAT records: headline figures of the concession panel at the default settings, which match the analysis above. Filters set the station kind, province, regency, KHG, dates and panel rules. Source: SiTMAT, April to October 2026 | cropped screenshot of repeat-sitmat/index.html, elements #story and #kpis (project_report_dashboards.screen_sitmat_overview)}}

## 3.5 DPG and DMPG villages

The World Bank asked whether villages of the peat-care village programme (*Desa Peduli Gambut*, DPG; renamed *Desa Mandiri Peduli Gambut*, DMPG, in 2020) are safe from fire and should count in the prioritisation. Three sources were available for the analysis:

- The Badan Restorasi Gambut atlas of DPG villages: one volume per province (Riau, Jambi, Sumatera Selatan, Kalimantan Barat, Kalimantan Tengah, Kalimantan Selatan) with participatory village boundary and land-tenure maps, and village index maps with a coordinate grid. The maps are images, without vector data.
- A list of the 244 villages in the atlas, extracted from the atlas volumes: Riau 40, Jambi 26, Sumatera Selatan 40, Kalimantan Barat 41, Kalimantan Tengah 74, Kalimantan Selatan 23. Mapping took place from June 2018 to July 2019. 177 of the 244 match a Bluebook 2026 target village by village and district name.
- A village boundary file for the atlas villages, built by the project. Each atlas village was matched by name to the KLH village boundaries of 2023, which are the closest in time to the atlas. Village boundaries from BIG (June 2026 edition) were the fallback for villages without a match. Names were compared ignoring case, spaces and punctuation, from exact matches down to close spellings within the same sub-district or district. 243 villages matched in the 2023 boundaries: 224 exactly, 8 with a different sub-district spelling, 1 in another district, 2 as the leading words of a longer name and 8 by close spelling. The one unmatched village, Ampaian Rotan Makmur, is absent from the BIG 2026 boundaries too. The 177 villages that are also target villages have identical polygons.

The atlas holds none of the villages added to the programme later, and its boundaries are approximate: they come from 2023 administrative boundaries, not from the participatory maps.

A national DMPG layer, published on the SiTMAT portal of KLH, was obtained on 28 October 2026. It holds 838 village boundaries in ten provinces, with the programme of each village (DMPG, or DMPG and DMPM for 77 villages) and its support history: the year and source of each round, for example 2018 Kemitraan followed by 2022 APBN. By the first round, 75 villages entered in 2017, 187 in 2018, 132 in 2019, 245 in 2020 and 183 from 2021 to 2024, and 16 have no year; 483 were first funded from the state budget (APBN), 143 through partnerships and 212 by other partners or programmes. Of the 244 atlas villages, 224 are in this layer by village and district name, and for matched villages the two boundaries coincide (median overlap 1.00). The analyses in this report still use the 244 atlas villages; the national layer supersedes them for later work. DPG and DMPG villages are context on the national overlays and are not scored.

![The DPG village page prepared for the World Bank question on peat-care villages: atlas villages with their boundaries, hotspots and burned area. Source: BRG atlas, KLH 2023 village boundaries, VIIRS hotspots, burned area 2015-2025](re-peat/reports/project_report/figures/screen_dmpg.png)

## 3.6 The selected KHG

The detailed work covers 12 main KHG, with two reserves, Pulau Tebing Tinggi and Sugihan-Lumpur (Table 2.1). Each name was matched to the official KHG boundaries. Three needed interpretation: "Menpanwah" was read as Mempawah (KHG Sungai Mempawah - Sungai Peniti, 51,045 ha), "Kahayan-Barito" was corrected to Kapuas-Barito (558,168 ha), and Buru Mappi - Buru Obaa (402,643 ha) was chosen over the reversed pair Buru Obaa - Buru Mappi (98,805 ha). No KHG is named Cawang-Lalang. The nearest is KHG Air Banyuasin - Air Lalang (60,758 ha); it is left out until the choice is confirmed. Kampar-Gaung, the earlier test site, is analysed with the selected KHG, which gives 14 KHG in all.

## 3.7 Data readiness per selected KHG

{{table: khg_data_recap | Data available per selected KHG: LiDAR DTM and its coverage, modelled DTM, DEMNAS, contours, modelled peat depth and its coverage, canals, rivers, existing infrastructure, proposed canal blocks (Bluebook 2026, targets, not built) and SiTMAT stations. Source: per-KHG data recap of 25 October 2026 | re-peat/docs/16-khg-data-recap.md, table "Overview" (one row per KHG, columns lidar_dtm, modelled_dtm, demnas, contour, peat_depth, canals, rivers, infrastructure, canal_blocks, tmat); long form in re-peat/sites/khg_data_recap.csv (columns khg, theme, tag, res_m, coverage_pct, features, length_km, summary)}}

{{table: khg_dem_inputs | Elevation models available for each KHG: product, resolution and share of the KHG covered. Source: DEM input preparation, October 2026 | re-peat/sites/khg_dem_inputs.csv, columns khg, product, res_m, cover_pct; one row per KHG and product}}

The recap shows four main gaps.

- LiDAR covers few KHG. Of the selected KHG, only Mendahara-Batanghari, Air Hitam Laut-Buntu Kecil, Saleh-Sugihan, Sugihan-Lumpur and Pulau Padang have a LiDAR DTM, all in Sumatra. No KHG in Kalimantan or Papua has one. Pulau Padang's 2 m LiDAR covers the whole KHG but is not used in the analysis chain, so Pulau Padang is analysed on DeltaDTM and DEMNAS. Every other KHG relies on the two corrected open DEMs.
- Modelled peat depth covers between 53 % (Balangan-Batangalai) and 96 % (Air Hitam Laut-Buntu Kecil) of the KHG where it exists, and is absent for Kahayan-Sebangau, Kapuas-Barito and Buru Mappi-Buru Obaa. There the peat-depth indicators carry weight 0.
- Water-table stations are missing at Saleh-Sugihan, Mempawah-Peniti, Balangan-Batangalai and Buru Mappi-Buru Obaa, and sparse at Kahayan-Sebangau (2 stations). A KHG deficit from stations cannot be computed where there are none.
- Buru Mappi-Buru Obaa in Papua Selatan has the least data of all: 31 km of mapped canals, no existing or proposed canal blocks, no peat depth, no stations and no LiDAR.

The recap is dated 25 October 2026, before DEMNAS sheets for every KHG were obtained (25 and 26 October), the remaining DeltaDTM areas (26 October) and the ICESat-2 points (27 and 28 October). For elevation the DEM input table supersedes the recap. It shows DEMNAS and DeltaDTM covering at least 97.9 % of every selected KHG, Buru Mappi-Buru Obaa included, where the recap lists no DEMNAS.

For the Saleh-Sugihan LiDAR the recap gives 61.9 % coverage and the DEM input table 98.3 %. The recap figure is correct: the DEM input table measures coverage only within the rectangular extent of the clipped LiDAR, not over the whole KHG. As a result the Saleh-Sugihan LiDAR passed the 90 % coverage threshold of the LiDAR variant although it covers about 62 % of the KHG (chapter 4), and the LiDAR results for Saleh-Sugihan describe only that part of the KHG.

Rivers from the RBI layer are missing at Pulau Padang, Air Hitam Laut-Buntu Kecil and Balangan-Batangalai. This affects delineation, where mapped rivers are fixed boundaries.
