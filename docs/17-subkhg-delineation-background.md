# 17 Sub-KHG delineation: method background

How a KHG is split into sub-KHG units that serve as the spatial units of the water balance (neraca air) and of canal-block planning. The page covers the sources, how `repeat-delineation` compares with them, and what a water-balance unit still needs. Compiled 2026-10-26. Page numbers for the Kahayan-Sebangau report are the printed page numbers, with the PDF page in brackets (PDF = printed + 9).

## 1. What the Kahayan-Sebangau study (2021) did

Source: `re-peat/docs/Laporan Akhir KHG SK SS _.pdf` (final report, Penyusunan Neraca Air KHG Sungai Kahayan - Sungai Sebangau).

| Item | What the report says | Page |
|---|---|---|
| Purpose of the units | Sub-KHG boundaries are fixed first, to set the analysis unit of the water balance ("penentuan unit area analisis neraca air"), because the KHG is too large for detailed simulation everywhere | 25 (PDF 34) |
| Outlet concept | A KHG outlet carries all water to the mouth (large river or sea). A sub-KHG outlet is a natural or artificial channel that carries part of the water to the KHG outlet, usually a small river or a canal | 27 (PDF 36) |
| Dome as the basic concept | Boundaries also depend on whether a peat dome is present. The dome top generally ("umumnya") has no channels, so rivers and canals lie lower down; a river or canal that joins through to the KHG outlet "dapat pula dianggap sebagai Sub KHG tersendiri" (can count as a sub-KHG of its own). Water flows from the dome to the lower rivers and canals. A DEM is required, and a better DEM resolution gives better boundaries | 27-28 (PDF 36-37) |
| Land use | Mining concessions can be excluded from the KHG or sub-KHG. Plantation concessions may change sub-KHG boundaries because they have turned rivers into canals | 28 (PDF 37) |
| Steps | Flow direction, flow accumulation, connectivity and channel order, canal pattern and outlet channels, sub-KHG boundaries, then field verification of the outlet channels | 45 (PDF 54) |
| Data | LiDAR DTM where available, WorldDEM to fill the rest. The two give different boundaries. Peat thickness and the natural river map were used as support | 45-46 (PDF 54-55) |
| Rule | D8 flow direction, Strahler order (7 orders in the KHG). Outlets are rivers and canals of order 7. Result: 16 sub-KHG | 45-46 (PDF 54-55) |
| Field check | Modelled flow directions matched the field. Sub-KHG boundaries are wide outlet canals that collect the flow of the neighbouring units. Some have strong flow; some boundary canals are silted, including blocked main canals | 47-48 (PDF 56-57) |
| Data limits | The canal network from BRGM had no class or type; the canal-block (IPG) data were not up to date. Field survey checked canals and blocks at sub-KHG boundaries, canal elevation and canal flow direction | 24-25 (PDF 33-34) |
| Unit sizes | 16 units, 35.0 km² (Sub-KHG 06) to 1,491.2 km² (Sub-KHG 16); KHG 4,508 km² | Tables 5.8, 5.9, 64-66 (PDF 73-75) |
| Water balance per unit | Ombrogenous balance, inflow from rain only; "umumnya tidak terdapat masukan dari lahan sekitarnya" (no inflow from neighbouring land, or insignificant) | 36, 99 (PDF 45, 108) |
| Global vs unit balance | The satellite-based balance was KHG-wide and "tidak terbagi sesuai batas sub KHG", so it was recomputed per sub-KHG | 74 (PDF 83) |
| Station-based balance | Spatial balance done only for sub-KHG 8 and 14, the two with SIPALAGA stations | 99-103 (PDF 108-112) |
| Canal blocks per unit | IPG metric counts primary and secondary canals only ("menghiraukan kanal tersier"). Several recommended blocks are on canals between units ("antara sub KHG 4 dan 8", "antara sub KHG 8 dan 11"), others on canals inside a unit ("di dalam sub KHG 8", "di dalam sub KHG 9") | 109, 112-115 (PDF 118, 121-124) |
| Typical canals | Primary 25 m wide, 3 m deep; secondary 6 m, 1.5 m | Table 5.11, 110 (PDF 119) |

The same team's Pulau Padang study (2018) used the same chain: LiDAR DTM, fill (depressionless DEM), flow direction, flow accumulation, sub-KHG boundaries. It then computed rain, ET, river runoff and water balance per sub-KHG and counted canal blocks per sub-KHG (11 units). Source: `re-peat/docs/Kajian Kompre Topo Hidro WM - Penyusunan Peta Arahan Tindakan RGP Padang.pdf`, slides 6, 21, 27-28, 31, 35, 38, 42.

The published version is Cahyono, Aditya & Istarno (2022). Its abstract states that the sub-PHU "was determined based on the peat hydrological unity concept by identifying streamline, outlet channels, peat-depth, slopes, and network connectivity" and that each sub-PHU's water balance used TerraClimate and CHIRPS with field observations. Only the abstract was read (full text refused, HTTP 403).

## 2. Regulation and other practice

| Source | What it sets | Relevance to sub-KHG |
|---|---|---|
| SK.129/MENLHK/SETJEN/PKL.0/2/2017 (`re-peat/docs/reference/KepmenLHK022017.pdf`, p. 4-5) | National KHG map at 1:250,000, 865 KHG, 24,667,804 ha; revisable from provincial and district KHG maps at 1:50,000 | Defines no level below the KHG |
| P.14/MENLHK/SETJEN/KUM.1/2/2017, Pasal 5(3) (PDF p. 8) | KHG boundary delineation considers the area around peat between two main or order-1 rivers, the surface elevation pattern from a 30 m DTM/SRTM, and DAS boundaries; land system data where these are absent | The KHG rule is the same outlet-plus-terrain logic one level up |
| P.14/2017, Pasal 14 (PDF p. 11-12) | Field grid: transects 2 km apart with points every 500 m, and 3 km apart with points every 1,000 m, both starting from a dome peak; record natural and artificial drainage | Sets the resolution of field peat depth |
| P.10/MENLHK/SETJEN/KUM.1/3/2019, Pasal 1, 3 (PDF p. 4-6) | Puncak kubah gambut is the highest part of the dome, determined by a water balance. Darcy method in three steps; data: peat depth, topography at 0.5 m contour interval, porosity, soil moisture | The dome peak is the one regulated internal zone of a KHG |
| P.10/2019, Lampiran (PDF p. 15, 17) | Topography "interval kontur 0,5 meter (Data LiDAR atau World DEM)"; Q_cum from the peak-to-foot elevation difference (E1 − E2), a shape factor FB, porosity n, soil moisture sm and transect length L (A-B); balance d = 0, then "delineasi areal puncak kubah gambut" | Gives a crest zone that a sub-KHG layout should not cut through |
| P.10/2019, Pasal 8(4) (PDF p. 8) | Outside the dome peak, hydrological function is kept through canal blocks with spillways, compliance points for water table and rain stations, and monitoring | Structures and monitoring points are part of the management unit |
| P.15/MENLHK/SETJEN/KUM.1/2/2017, Pasal 2, 4 (PDF p. 5-7) | Compliance points on at least 15% of plantation compartments or production blocks, at the centroid (within 50 m); placement accounts for topography, "zona pengelolaan air", canals and structures. A water management zone is a group of water surface heights within a 1 m range, from topography | The only regulated sub-unit found. It is defined by 1 m elevation bands; drainage plays no part in it |
| P.15/2017, Pasal 6(3), 7 (PDF p. 8) | At least one data logger per water management zone; one rain gauge per 20 compliance points, spread by water management zone | Monitoring density per zone |
| PP 57/2016, explanation of Pasal 26 (PDF p. 5) | "Drainase" means a channel that drains water directly out of the KHG to a river or the sea | Separates outlet channels from internal canals |
| Jaenicke et al. 2010 | Sebangau: study area bounded by the Sebangau River, tributaries and the dome's highest elevation. Two sub-catchments named after their outlet rivers, Bakung and Bangah, delineated from a 30 m DTM (590 km²). Assumption: if all canals draining the peat within a catchment are blocked, the water table can be raised. Dams sized by canal slope with about 25 cm head per dam | Closest published precedent: catchment of an outlet river, crest as boundary |
| Ritzema et al. 2014 | Block C, ex-Mega Rice Project: dome slope 1-2 m/km near rivers, under 0.5 m/km in the centre. Canals perpendicular to the contours need cascades of dams, head difference under 0.5 m; canals parallel to the contours need a different dam type | Canal orientation to the dome decides the block design inside a unit |
| Urzainki et al. 2023 | Model of a 22,000 ha part of the 140,000 ha Merang-Kepayang dome: canal network as a 1-D topology (50 m nodes) coupled to 2-D peat groundwater. No-flow at canal boundary nodes, fixed head −0.2 m at the domain edge; no outlet discharge data. Block effect relevant to about 600 m, negligible beyond 1 km; boundary-condition error estimated to reach about 1 km inside the domain. Two watertight dams in one reach disconnect that segment from the network | Boundary conditions and network topology are what a unit balance needs |
| Cobb et al. 2017 (abstract) | Rainfall and groundwater flow set the stable shape of a tropical peatland "within a network of rivers or canals"; domes reach their final shape first at edges bounded by rivers | Rivers and canals bound the domes. Inference (not in the abstract): a new canal network changes where dome boundaries are |

## 3. Comparison

| Rule | Kahayan-Sebangau 2021 | Regulation and literature | `repeat-delineation` now |
|---|---|---|---|
| Terrain | LiDAR DTM plus WorldDEM | KHG: 30 m DTM/SRTM (P.14); dome peak: 0.5 m contours (P.10); 30 m DTM for sub-catchments (Jaenicke) | Any ground DTM, warped to a 30 m UTM grid |
| Flow routing | D8, Strahler order | Fill, flow direction, accumulation (Padang slides) | pysheds: fill pits and depressions, resolve flats, D8, accumulation, Strahler order |
| Channels | Natural rivers as support; canals had no class | Outlet = drainage out of the KHG (PP 57 explanation) | Rivers and lakes always boundaries; canals burned 3 m; outlet canal classes set in config |
| Outlet rule | Channels of Strahler order 7 (DEM-derived) | Outlet river of each catchment (Jaenicke) | Mapped rivers plus outlet canals first; DEM streams of order ≥ k added only if the count is outside the target |
| Primary canals as boundaries | Field check found boundaries are wide outlet canals (p. 48) | Not stated | Design choice based on that field observation; default classes `primer`, `primary` |
| Secondary canals | Counted for IPG; canal classes were not available for delineation (p. 25) | Not stated | Optional (Sugihan-Lumpur site config: Kanal Primer + Kanal Sekunder) |
| Dome crest | Basic concept, read from DEM flow | Dome peak from Darcy water balance (P.10); crest as study-area edge (Jaenicke) | Implicit: divides from D8. No explicit crest or dome-peak layer |
| Minimum size / count | None stated; result 35-1,491 km² | None found in regulation | `target_count` [6, 30]; `min_area_km2` number or `auto` (from 5 km², +10% steps). Sugihan-Lumpur, last run on file (`delineation_report.json`, made with the KLHK modelled DTM before the config switched to LiDAR on 2026-10-26): merge threshold 116.1 km², 27 units of 131.7-463.4 km². LiDAR run in the stability test: 30 units of 113.0-373.0 km² |
| Merging | Not described | Not stated | Small pieces join the neighbour with the longest divide border (`adjacent`); `flow` (prefer the neighbour draining to the same channel line) is implemented but has no results in `summary.csv` yet |
| Coast-draining land | Not described | Not stated | Split into compact pieces of about 50 km² |
| Concessions | Mining excluded; plantations may change boundaries | Compliance points per production block (P.15) | Not used |
| Field verification | Flow direction and boundary canals checked in the field | Survey grid from the dome peak (P.14) | None; stability test instead |

Stability at Sugihan-Lumpur (`_khg/16.02.01_sugihan_lumpur/02_delineation/stability/summary.csv`, adjusted Rand index against the LiDAR run):

| Outlets | Noise members | Other DTMs | Flat surface | Units |
|---|---|---|---|---|
| Primary canals | 0.471 | 0.48 | 0.348 | 24-30 |
| Primary + secondary | 0.633 | 0.629 | 0.601 | 26-30 |

With primary and secondary canals as outlets, a flat surface agrees with the LiDAR run almost as well as the other DTMs do (0.601 against 0.629). The units are therefore set mainly by the mapped canal network, and the DTM moves the internal divides. With primary canals only, the largest LiDAR unit is 1,353 km² (`members.csv`).

## 4. What a water-balance unit needs

The Kahayan-Sebangau balance treated each unit as rain-fed with no lateral inflow (p. 36, 99). The repeat-neraca 2-D run on Sugihan-Lumpur shows the limit of that view: with canals as fixed drains, every cell behaves as an independent bucket, the per-sub-KHG water table is identical (65 cm), and the held water tables of 35-55 cm need water from outside the rain balance and a managed canal level (`repeat-neraca/docs/neraca-air.md`, sections on results and next steps). Models that work in drained peat all take the canal water level or drainage as an explicit input (`repeat-neraca/docs/references.md`: Taufik et al. 2019, Mezbahuddin et al. 2023, Apers et al. 2022). The boundary condition that matters most for a unit is therefore the water level and structure operation on its boundary canals. Lateral groundwater exchange looks small in the current neraca peat table, but that table's transmissivity is 100 to 1,000 times below measured values (`tropical-peat-hydraulic-parameters.md`). With measured values, exchange with boundary canals matters within roughly 600 m to 1 km of them (Urzainki et al. 2023).

| # | Requirement | Why | Data source | In the project? |
|---|---|---|---|---|
| 1 | Closed boundary on mapped channels or divides | Control volume; KHG and sub-KHG both defined by outlets (report p. 27) | Rivers (RBI), canals (`kanal_osgm_khg_existing_Indonesia.gpkg`), DTM | Yes. Sugihan-Lumpur: canals 14,156 features (primary 549, secondary 3,494, tertiary 10,113); RBI rivers only 2 features, 9.5 km (`khg_data_recap.csv`) |
| 2 | Outlet of each unit and unit-to-unit topology (which unit drains into which, through which canal) | Outflow of one unit is inflow of the next; Urzainki builds the canal model from network topology | Derived from the D8 trace and the canal graph | Missing. Output is `khg_id, unit_id, geometry` only; derivable from data already computed |
| 3 | Canal flow direction | Report checked it in the field (p. 25); decides upstream and downstream units | Field survey; canal bed elevations from LiDAR | Missing. Canal layer has class and length only (`KODE_KANAL`, `KET_KANAL`, `Length__M`) |
| 4 | Canal dimensions | Storage and conveyance; block count (report Table 5.11) | Field; LiDAR for depth and width (Padang slides 39-40) | Missing per canal; typical values only from the 2021 report |
| 5 | Water control structures with type, crest and status | Blocks on boundary canals set the boundary level; Urzainki: two watertight dams disconnect a reach | `infrastruktur_hidrologis_existing_BRGM_Indonesia.gpkg` (Jenis: sekat kanal, spillway, pintu air; Tahun; KETERANGAN realisasi or rencana) | Partial. Sugihan-Lumpur 2,972 points; no crest elevation or condition; nationally 38,449 of 46,961 rows have no year (Tahun = 0). Bluebook 2026 blocks are proposals only |
| 6 | Boundary water level: canal level, river stage, tide | Fixed or prescribed head on the boundary; neraca now assumes surface minus 1.2 m | Loggers in canals, tide predictions, river gauges. The 2021 study listed BRGM tide data (Talio) and BIG tide predictions (Table 4.1, p. 25) | Missing. No tide, river stage or canal level dataset in `data_catalog.csv` |
| 7 | Dome crest or dome peak as a no-flow line | P.10/2019 dome peak; Jaenicke used the crest as an area edge | DTM plus peat depth, P.10 Darcy method | Missing as a layer. `klhk_khg_feg_50k.gpkg` holds lindung/budidaya and peat thickness class for 4 KHG only, no dome peak |
| 8 | Peat depth and storage per unit | Storage term; 2021 study computed peat and water volume per unit (Table 5.9) | Modelled peat depth; BBSDLP 1:50,000 | Partial. Sugihan-Lumpur: modelled depth covers 74.7%, BBSDLP 52.6% of the KHG |
| 9 | Land cover per unit | Interception and ET differ by cover (report p. 99) | ESA WorldCover | Yes (cloud) |
| 10 | Forcing resolution finer than the unit | A per-unit balance needs more than one forcing value per unit | TerraClimate 1/24° (about 4.6 km, about 21 km² per cell); ERA5 and WaPOR in repeat-neraca | Partial. The neraca deficit uses KHG-mean rain minus evaporation; a per-sub-KHG deficit needs finer forcing (`neraca-air.md`, deficit section). Smallest 2021 unit (35 km²) spans about 1.6 TerraClimate cells; smallest Sugihan-Lumpur unit (113-132 km² by DTM) about 6 |
| 11 | Water-table stations inside units | Calibration and checking; 2021 spatial balance only where SIPALAGA existed (p. 99) | SiTMAT | Partial. Sugihan-Lumpur 54 stations, all in concessions, 2026-04-01 to 2026-10-21 |
| 12 | Lateral groundwater exchange across boundaries | Small in the current neraca table, which underestimates T; with measured T, exchange with boundary canals matters within about 600 m to 1 km (Urzainki 2023) | Measured Sy and K profiles (Cobb and Harvey 2019, Ismail et al. 2021, Kurnianto et al. 2019, via `tropical-peat-hydraulic-parameters.md`) | Partial. Tropical parameter sets are listed in repeat-neraca but not yet the default |
| 13 | Unit size against grid and block reach | neraca grid 500 m; block reach about 600 m (Urzainki 2023) | Config | Yes. Units of 100+ km² hold hundreds of 500 m cells |
| 14 | Consistency with regulated zones | Compliance points by water management zone (1 m elevation bands) and production block (P.15/2017); dome peak protected (P.10/2019) | DTM; concession blocks | Partial. DTM yes; production-block boundaries not in `_data` |

## 5. Gaps and recommendations

| # | Gap | Recommendation | Source |
|---|---|---|---|
| 1 | Units carry no outlet or topology | Write per unit: outlet canal reach, downstream unit, boundary canals with class and length. Use the same graph for the neraca canal module | Report p. 27, 48; Urzainki 2023 (canal topology, no-flow outlet) |
| 2 | Boundary canals have no water level or direction | Treat boundary canal level as the unit's boundary condition. Collect canal level and flow direction at unit outlets in the field, as the 2021 survey did | Report p. 25; repeat-neraca results; Taufik et al. 2019 via `references.md` |
| 3 | Primary canals alone give unstable units (ARI 0.47-0.48) | Keep primary + secondary as outlets for Sugihan-Lumpur; report it as a canal-network partition, since the flat surface scores 0.601 | `summary.csv`; report p. 109 (IPG uses primary and secondary) |
| 4 | Dome crest not explicit | Add a crest or dome-peak layer (P.10 method or a DTM ridge on a canal-free surface) and forbid merges across it | P.10/2019 Lampiran; Jaenicke 2010 |
| 5 | Minimum area and count have no external basis | State `target_count` and `min_area` as project settings. Check that each unit has at least several forcing cells and contains its blocks' reach | No regulatory minimum found; TerraClimate cell size; Urzainki 2023 |
| 6 | Structures lack status and crest | Join BRGM structures to boundary canals; flag realised vs planned and year | `infrastruktur_hidrologis_existing_BRGM_Indonesia.gpkg` fields |
| 7 | No link to regulated monitoring zones | Report per unit the 1 m elevation bands and the number of compliance points or SiTMAT stations | P.15/2017 Pasal 4(6), 6(3) |
| 8 | Concessions ignored | Overlay licence areas per unit as context, as the 2021 study did for mining and plantations | Report p. 28 |
| 9 | Merge rule | Tested 2026-10-26: the `flow` merge (prefer the neighbour on the same channel line) agrees slightly less than the `adjacent` merge (noise members ARI 0.603 against 0.633; DTMs 0.606 against 0.629), so `adjacent` stays | `_khg/16.02.01_sugihan_lumpur/02_delineation/stability/summary.csv` |

## References

Local files:
- Laporan Akhir, Penyusunan Neraca Air KHG Sungai Kahayan - Sungai Sebangau (2021). `re-peat/docs/Laporan Akhir KHG SK SS _.pdf`, printed pages as cited.
- Kajian Komprehensif Topo Hidro WM, Penyusunan Peta Arahan Tindakan RG P. Padang. Tim Sipil dan Tim Geospasial FT UGM, 8 Aug 2018. `re-peat/docs/Kajian Kompre Topo Hidro WM - Penyusunan Peta Arahan Tindakan RGP Padang.pdf`, slides as cited.
- SK.129/MENLHK/SETJEN/PKL.0/2/2017, Peta KHG Nasional. `re-peat/docs/reference/KepmenLHK022017.pdf`, p. 4-5.
- `repeat-delineation/README.md`; `repeat-delineation/src/repeat_delineation/delineate.py` (`SUBKHG_DEFAULTS`); `repeat-delineation/docs/delineation_flow.drawio`.
- `_khg/16.02.01_sugihan_lumpur/02_delineation/delineation_report.json`, `stability/summary.csv`, `stability/members.csv`.
- `repeat-neraca/docs/neraca-air.md`, `repeat-neraca/docs/references.md`, `repeat-neraca/docs/tropical-peat-hydraulic-parameters.md`.
- `re-peat/sites/data_catalog.csv`, `re-peat/sites/khg_data_recap.csv`.

Fetched 2026-10-26:
- PermenLHK P.10/MENLHK/SETJEN/KUM.1/3/2019, Penentuan, Penetapan dan Pengelolaan Puncak Kubah Gambut Berbasis KHG. https://peraturan.bpk.go.id/Download/344756/P.10-2019%20KHG.pdf (PDF p. 4-8, 13-17).
- PermenLHK P.14/MENLHK/SETJEN/KUM.1/2/2017, Tata Cara Inventarisasi dan Penetapan Fungsi Ekosistem Gambut. https://jdih.kehutanan.go.id/new2/uploads/files/P.14.pdf (PDF p. 8, 11-12).
- PermenLHK P.15/MENLHK/SETJEN/KUM.1/2/2017, Tata Cara Pengukuran Muka Air Tanah di Titik Penaatan Ekosistem Gambut. https://faolex.fao.org/docs/pdf/ins174419.pdf (PDF p. 4-8).
- Penjelasan PP 57/2016 (Tambahan Lembaran Negara No. 5957). https://peraturan.go.id/files/pp57-2016pjl.pdf (PDF p. 5).
- Cahyono, B. K., Aditya, T., Istarno (2022). The Determination of Priority Areas for the Restoration of Degraded Tropical Peatland Using Hydrological, Topographical, and Remote Sensing Approaches. Land 11(7), 1094. https://doi.org/10.3390/land11071094 (abstract via OpenAlex only).
- Jaenicke, J., Wösten, H., Budiman, A., Siegert, F. (2010). Planning hydrological restoration of peatlands in Indonesia to mitigate carbon dioxide emissions. Mitigation and Adaptation Strategies for Global Change 15, 223-239. https://doi.org/10.1007/s11027-010-9214-5 (full text).
- Ritzema, H., Limin, S., Kusin, K., Jauhiainen, J., Wösten, H. (2014). Canal blocking strategies for hydrological restoration of degraded tropical peatlands in Central Kalimantan, Indonesia. Catena 114, 11-20. https://luk.tsipil.ugm.ac.id/rawa/PLG/1-s2.0-S0341816213002531-main.pdf (full text).
- Urzainki, I., Palviainen, M., Hökkä, H., Persch, S., Chatellier, J., et al. (2023). A process-based model for quantifying the effects of canal blocking on water table and CO2 emissions in tropical peatlands. Biogeosciences 20, 2099-2116. https://doi.org/10.5194/bg-20-2099-2023 (full text).
- Cobb, A. R., Hoyt, A. M., Gandois, L., et al. (2017). How temporal patterns in rainfall determine the geomorphology and carbon fluxes of tropical peatlands. PNAS. https://doi.org/10.1073/pnas.1701090114, PMC5495247 (abstract via Europe PMC only).

## Not verified

- Cahyono et al. (2022) full text: MDPI refused the download (HTTP 403). Thresholds, unit areas and figures in the paper were not checked.
- Cobb et al. (2017) full text: not retrieved; only the abstract is used.
- PP 71/2014 and PP 57/2016 main text. Only the explanation of PP 57/2016 was read. The 0.4 m water-table damage criterion was seen in P.10/2019 Gambar 1 (PDF p. 14, "TMAT > 0.4 m", next to PP 57/2016) and in the 2021 report (p. 42-43, 109), not in the PP text itself.
- The RPPEG regulation and any official rule on how an RPPEG divides a KHG.
- BRG/BRGM technical guidance on canal blocking, "blok pengelolaan" or hydrological units: no official document was found by search.
- Saxon et al. (Mires and Peat), Vernimmen et al. (2020), Urzainki et al. (2020), Sutikno et al. (2019): summarised in `research_notes/Sub KHG prioritisation improvements/delineation_methods.md` (fetched 2026-10-23) but not re-checked here, so not cited above.
- Peer-reviewed work by Hooijer, Baird or Deltares that defines hydrological model domains or management units in Indonesian peat was not fetched.
