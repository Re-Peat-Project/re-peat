# National peat depth sources for all 865 KHG

Checked 2026-11-06. Our current depth inputs: modelled per-KHG rasters (BRGM/KLHK, 50 KHG) and a partial BBSDLP 1:50,000 class layer (100-115 E, field KETEBALAN). Papua (465 KHG, 6.5 Mha) has nothing. This note ranks what else exists, best first for nationwide KHG modelling.

Reading level is given per source: "queried" means I hit the live service myself; "full text" or "partial full text" means I read the body (or long excerpts of it); "abstract" or "snippet" means I only saw that. Anything not checked is marked unverified.

## Ranked list

1. KLHK peat ecosystem function map 1:50,000 (FEG 50k, field `peat_thick`), served by BIG Satupeta. Usable now. It covers 108 KHG, including 24 in Papua, with 0.5 to 1 m depth classes.
2. BBSDLP / Kementan Peta Lahan Gambut Indonesia 1:50,000, December 2019 edition (Anda et al. 2021). The only official nationwide depth-class map, covering Sumatra, Kalimantan, Sulawesi and Papua. Only the Kalimantan part is public. The rest must be requested from BBSDLP or Pusdatin.
3. PEATGRIDS v2.0.1 (Widyastuti et al.). Continuous thickness at 1 km, with a standard deviation layer. It covers all of Indonesia including Papua, is licensed CC BY 4.0, and is on Earth Engine. Use it as a gap filler only: the Indonesian training data partly comes from the MoA class map.
4. LiDAR-DTM minus a flat peat bottom (Deltares/Vernimmen). The deep-peat map for eastern Sumatra is at 100 m, CC BY 4.0. Use it as a cross-check and as a method for coastal domes, not as national coverage.
5. CIFOR Gumbricht et al. 2017 tropical peat depth. Continuous at about 231 m, CC BY 4.0. The authors report that it overestimates depth. Low priority.
6. Wetlands International atlases (Sumatra 2003, Kalimantan 2004, Papua 2006). Depth classes, old. GIS availability is unverified.
7. Extent-only products, not usable for depth: Global Peatland Map 2.0 (UNEP/GMC), Peat-ML (Melton et al.) and Trase statistics.
8. Local machine-learning or LiDAR thickness maps (Bengkalis, Sentarum, Mendahara, a Papua pilot). Useful for validation only.

Recommendation: build the per-KHG depth input as a cascade.

- Keep the modelled rasters where they exist.
- Next, use FEG 50k `peat_thick`, converting each class to its midpoint. This adds about 88 KHG (2.16 Mha) that currently have no depth, including the first 24 Papua KHG.
- Next, use our BBSDLP KETEBALAN classes.
- Then use PEATGRIDS as a flagged, low-confidence continuous fallback for the remaining roughly 700 KHG, most of Papua included.

In parallel, file a formal data request, through KLHK or the World Bank channel, for the full 2019 BBSDLP 1:50,000 map (Papua, Sulawesi, Sumatra west of 100 E, Kalimantan east of 115 E). Once it arrives, it should replace PEATGRIDS wherever it has a polygon. For coastal domes, a DeltaDTM-minus-flat-bottom check (the Deltares method) is a cheap sanity test of any class-based depth.

## Candidates

### 1. KLHK FEG 1:50,000 with peat thickness (BIG Satupeta layer 48)

- What it is: the KLHK peat ecosystem function layer at 1:50,000, with fields `kode_khg`, `peat_thick`, `tnh_gambut`, `feg_peat` and `feg_50k`. Its legal basis is PP 57/2016, Permen LHK 14/2017 and a series of SK decrees up to SK.1152/2022.[1] Reading: queried.
- Coverage: 15,980 polygons, extent 95.97-140.95 E.[1]
  - Polygon counts by longitude band: 11,144 in 95-106 E, 4,359 in 106-120 E, 0 in 120-130 E, and 477 in 130-142 E (Papua). These are my own envelope queries.
  - There are 108 distinct `kode_khg`. 105 match our registry: Sumatra 50 KHG (2.15 Mha registry area), Kalimantan 31 (0.94 Mha), Papua 24 (1.21 Mha, all in Papua province, e.g. KHG.91.17.01 Sungai Wade Nanu - Sungai Wade Assue). Of these, 88 KHG (2.16 Mha) have neither modelled depth nor BBSDLP classes in our current data.
  - No Sulawesi KHG. This is far from all 865 KHG, and polygons may not cover each KHG fully (not checked).
- Depth form: text classes, mostly 0.5 m wide ("0,0 - 0,5 meter" up to "16,5 - 17,0 meter" and "> 14 meter"), mixed with 1 m wide classes ("1,0 - 2,0 meter"). The 1 m classes probably come from different survey batches (my reading of the value list). Parse to lower and upper bounds before use.
- Year: the SK series runs 2017-2022.[1] The survey year per KHG is not in the attributes.
- Licence: not stated on the service. Copyright text names the Direktorat Pengendalian Kerusakan Ekosistem Gambut, KLHK.[1] Treat it as government data that needs acknowledgement, and confirm terms with KLHK before redistribution.
- Access: ArcGIS REST query (JSON/GeoJSON, 1,000 records per page).[1] The KHG 1:50,000 companion is layer 37 (250 features, `kode_khg` only).[29] SIGAP also lists FEG and KHG at 1:50,000 and 1:250,000.[24] Our `klhk_khg_feg_50k.gpkg` holds only a South Kalimantan bbox so far: rerun the fetch without `--bbox`.
- Accuracy: none reported on the service.

### 2. BBSDLP / Kementan Peta Lahan Gambut Indonesia 1:50,000 (2019) and Anda et al. 2021

- What it is: the semi-detailed national peat map, compiled by kabupaten from 2013 and completed for all peat kabupaten by the end of 2019. It was released as an atlas in December 2019, covering 13.43 Mha.[6] It is published as Anda et al. 2021, Geoderma 402:115235.[7] Reading:
  - Anda et al.: title and metadata only. The publisher withholds the abstract from the APIs and the article is closed access.
  - Details below come from a 2024 secondary study (partial full text)[4] and news items (snippets).[5][6]
- Coverage: Sumatra 5.85 Mha, Kalimantan 4.54 Mha, Sulawesi 0.03 Mha, Papua 3.01 Mha.[4] It includes Papua and Sulawesi.
- Depth form: six classes: 50-100, 100-200, 200-300, 300-500, 500-700 and >700 cm.[4][5] In the public Kalimantan service, the class is embedded in the `landform` label (e.g. "Kubah Gambut (300 cm - < 500 cm)"), not in a separate depth field.[2]
- Access:
  - Public: only the Kalimantan part, as catalogue entry PETA_LAHAN_GAMBUT_PULAU_KALIMANTAN_SKALA_50K_PUBLISH (bbox 108.86-118.58 E). Its distribution URL is a sig02.pertanian.go.id MapServer.[3] I got "Token Required" when I queried it. The same Kalimantan polygons are mirrored on BIG Satupeta layer 6 (146 features, all in 106-120 E).[2]
  - A catalogue search for "gambut" returned only this one record. I found no public national or Papua download.
  - Route for the rest: a formal request to BBSDLP (bbsdlp@pertanian.go.id) or Pusdatin (custodian).[3]
- Licence: the catalogue licence field cites PP 1/2021 and PP 69/2020 on non-tax state revenue (PNBP) tariffs.[3] In other words, a fee-bearing government data product, not an open licence.
- Accuracy: no map accuracy figure found. Practitioner critiques:
  - Deltares-linked D4S says Papua extent was cut from over 7 Mha to under 2 Mha in the BBSDLP map, excluding lowland swamps that have peat according to field data. D4S also says depth boundaries are coarse.[22] Note that D4S's "under 2 Mha" disagrees with the 3.01 Mha reported for Papua in [4]. Unresolved.
  - Earlier Deltares work found that peat thickness on the older national maps is "very poor" while extent is well known.[18]
- Note: our KETEBALAN layer (100-115 E) is probably a piece of this product. Confirm it from its metadata.

### 3. PEATGRIDS (Widyastuti, Minasny et al.)

- What it is: global peat thickness (cm), bulk density, carbon content and carbon stock at about 1 km, from quantile random forest. Version 2.0.1 adds mean and standard deviation bands.[8][9] Peer-reviewed in CATENA 258:109243 (2025).[9] Reading:
  - Zenodo record: queried.
  - ESSD preprint: partial full text.[10]
  - CATENA article: abstract.[30]
- Coverage: global peat-dominated area. For Indonesia, the authors replaced the Global Peatland Map extent with the Ministry of Agriculture map (Haryono et al. 2011), which includes Papua.[10]
- Depth form: continuous cm. The Earth Engine bands are `THICKNESS_CM_MEAN` and `THICKNESS_CM_STDEV`.[9]
- Year: v1 August 2024, v2.0.1 November 2024.[8]
- Licence: CC BY 4.0.[8]
- Access: Zenodo record 15070037 (PEATGRIDS_THICKNESS_CM.zip, about 140 MB)[8], or the sat-io community catalog on Earth Engine.[9]
- Accuracy: regional validation R² 0.21-0.61 for thickness in the published version.[9][30] The preprint gave 0.15-0.72 across regions.[10]
- Caveat: in Indonesia, 300 training points were sampled from the national depth-class map (Anda et al. 2021), using class midpoints and a 9 m cap.[10] That makes it partly a smoothed copy of the MoA classes, so it adds little independent information where MoA classes exist. A 1 km cell is coarse relative to many small Papua KHG.

### 4. LiDAR DTM with a flat peat bottom (Deltares, Vernimmen et al. 2020)

- What it is: peat thickness = LiDAR DTM minus a peat-bottom surface. In eastern Sumatra a flat bottom at 0.61 m +MSL, from 2,446 measurements, gave the deep-peat (>3 m) map.[16] Reading: abstract and partial full text (PMC).
- Coverage: eastern Sumatra (about two thirds of Sumatran peat).[16] Kubu Raya and Bengkalis test areas are covered in Peat Prize reports.[18] No Papua coverage.
- Depth form: a deep-peat extent and thickness map at 100 m.[17]
- Licence: CC BY 4.0 for the deep-peat map (Mendeley 10.17632/c83z4df8ky.1). The DTM is 10.17632/72r3bvdd3r.1.[16][17]
- Accuracy:
  - Field thickness against LiDAR surface elevation: R² 0.83-0.88.[16]
  - Kubu Raya validation (65 points): mean difference 0.15 ± 0.55 m. 64.6% of points fall within 0.5 m and 93.8% within 1 m.[18]
- Use for us: a cross-check in Sumatra, and a method we can run on DeltaDTM for coastal raised bogs. Whether flat-bottom domes are common in Papua is unverified.

### 5. CIFOR Gumbricht et al. 2017 tropical and subtropical peat depth

- What it is: an expert-system wetland, peat and peat-depth map of the tropics (40 N to 60 S) at 231 m.[11][12] Reading:
  - Dataset page: snippet.
  - GCB paper: partial full text.
- Depth form: continuous metres, capped at 10 m because "our deepest values (>10m) overestimate depth".[11] The paper reports that the deepest pixels were about twice the profile depths, and it gives min-max volumes by halving depth limits.[12]
- Accuracy:
  - Peat extent agreed with 65% of 275 profiles globally and 74% in Indonesia. There is no depth RMSE.[12]
  - The paper notes a Papua extent above the national map (51,000 vs 39,000 km² of swamp peat).[12]
- Licence: CC BY 4.0.[11]
- Access: CIFOR Dataverse, doi:10.17528/CIFOR/DATA.00058 (guest book).[11] The Global Wetlands V3 viewer shows a peat depth layer. In the v2.1 file list I saw, the "Tropical and Subtropical Peatdepth.7z" file shows 0 B.[11] I did not test the download.
- Verdict: depth is derived from SRTM relief and literature caps, not fitted to Indonesian depth data. It is worse than PEATGRIDS for our use.

### 6. Wetlands International peat atlases (Wahyunto et al. 2003, 2004, 2006)

- What it is: province peat distribution and carbon atlases for Sumatra, Kalimantan and Papua (Papua 2000-2001).[19] Reading: partial full text (Warren et al. 2017).
- Depth form, by region:[19]
  - Sumatra: 50-100, 100-200, 200-400 and 400-800 cm.
  - Kalimantan: <50 up to 800-1200 cm.
  - Papua: <50, 50-100, 100-200 and 200-300 cm, with no peat deeper than 300 cm.
- Area: 20.9 Mha total, of which Papua is 27%.[19]
- Access and licence: unverified. The digital layers circulate (e.g. through GFW-era compilations), but I found no current official download.
- Use: historical Papua depth classes only. They are old and coarse.

### 7. Extent-only products (no depth)

- Global Peatland Map 2.0 (Greifswald Mire Centre / UNEP GPA 2022): about 1 km. Values 1 = peat dominated, 2 = peat in soil mosaic. The producers state it overestimates peat in Indonesia and Malaysia.[13] The sat-io listing gives the licence as CC BY-NC-SA 4.0.[14] Reading: snippets.
- Peat-ML (Melton et al. 2022): global fractional peat cover, CC BY 4.0, R² 0.73.[15] Reading: snippet.
- Trase "Indonesia - Peatland area": kabupaten and province statistics derived from the MoA 2019 1:50,000 map. No geometry with depth.[23] Reading: snippet.

### 8. Local thickness maps (validation only)

- Rudiyanto et al. 2018, Bengkalis (about 50,000 ha): 30 m. Explains up to 98% of variance, median relative error 5%, about 0.3 m average error.[20] Reading: abstract.
- Sentarum National Park: random forest at 12.5 m, RMSE 0.483 m, R² 0.786.[25] Reading: abstract.
- UGM thesis on KHG Mendahara-Batanghari (201,383 ha): Cubist on LiDAR DTM, RMSE 70.88 cm, R² 0.82. It used global peat thickness as a covariate.[26] Reading: abstract.
- Papua: a Sydney/UGM pilot mapped extent and depth class over about 2 Mha with Sentinel-1/2 (Pedometrics 2019 conference). No public dataset found.[21] A Merauke study estimated only the "very shallow" and "shallow" classes from land cover.[28] Reading: snippets/abstract.
- BRG LiDAR 1:2,500 mapping of priority KHG (about 606,000 ha at hand-over) gives DTMs, not depth maps.[27] Reading: news snippet.

## Open items

- Download the full FEG 50k layer (all 15,980 polygons). Then compute per-KHG coverage share and an area-weighted class midpoint, and compare it with our modelled rasters on the 10 Sumatra and 3 Kalimantan KHG where both exist. That gives an empirical error for using class midpoints.
- Request the BBSDLP 2019 national 1:50,000 shapefile, and ask for the depth field rather than the landform label.
- Check whether the CIFOR peat depth file actually downloads before discarding it.

## Sources

[1] https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/SUMBER_DAYA_ALAM_DAN_LINGKUNGAN/MapServer/48
[2] https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/SUMBER_DAYA_ALAM_DAN_LINGKUNGAN/MapServer/6
[3] https://geospasial.pertanian.go.id/katalog/cmroqmrlx002w01qjq1t2l1l1
[4] https://doi.org/10.26525/jtfs2024.36.1.105
[5] https://www.antaranews.com/berita/1522868/balitbangtan-lakukan-pemutakhiran-peta-lahan-gambut
[6] https://www.jurnas.com/ekonomi/63451/kementan-rilis-atlas-peta-lahan-gambut-skala-150000
[7] https://doi.org/10.1016/j.geoderma.2021.115235
[8] https://zenodo.org/records/15070037
[9] https://gee-community-catalog.org/projects/peatgrids
[10] https://essd.copernicus.org/preprints/essd-2024-333/essd-2024-333.pdf
[11] https://data.cifor.org/dataset.xhtml?persistentId=doi%3A10.17528%2FCIFOR%2FDATA.00058&version=2.1
[12] https://onlinelibrary.wiley.com/doi/full/10.1111/gcb.13689
[13] https://www.greifswaldmoor.de/global-peatland-database-en.html
[14] https://gee-community-catalog.org/projects/peatland
[15] https://gee-community-catalog.org/projects/peatland_ml
[16] https://pmc.ncbi.nlm.nih.gov/articles/PMC7227361
[17] https://data.mendeley.com/datasets/c83z4df8ky/1
[18] https://cms.deltares.nl/assets/common/downloads/Peatland-mapping-for-Kubu-Raya-Team-Deltares-1.pdf
[19] https://research.fs.usda.gov/download/treesearch/54642.pdf
[20] https://agris.fao.org/search/en/providers/122535/records/65dfa2f47c7033e84beea380
[21] http://www.digitalsoilmapping.com/articles-in-english/digital-peatland-mapping-in-indonesia
[22] https://www.dataforsustainability.com/report_a4.html
[23] https://trase.earth/open-data/datasets/spatial-metrics-indonesia-peat-area
[24] https://sigap.kehutanan.go.id/kamus/691/727
[25] https://doi.org/10.21163/gt_2022.171.04
[26] https://etd.repository.ugm.ac.id/penelitian/detail/268786
[27] https://www.antaranews.com/berita/648646/brg-serahkan-peta-lidar-gambut-ke-klhk
[28] https://ejournal.brin.go.id/ijreses/article/view/13893
[29] https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/SUMBER_DAYA_ALAM_DAN_LINGKUNGAN/MapServer/37
[30] https://www.sciencedirect.com/science/article/pii/S0341816225005454
