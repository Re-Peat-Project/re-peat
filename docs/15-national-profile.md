# 15 National KHG profile and ranking

Profiles all 865 KHG from the layers in `_data` and ranks them for rewetting attention, regardless of the 12 selected KHG ([13](13-selected-khg.md)). Code: `national/profile.py`, `national/stage3.py` and `national/dashboard.py` in `repeat-prioritisation`; the registry parser and the data fetchers are in `re-peat/tools` and `repeat-common`. The result is one self-contained interactive page, `reports/national_profile/dashboard.html` in this repository, with the CSV tables behind it.

The ranking (Stages 1-2) uses fire history, hotspots and canal density, with fire counted on peat. Stage 3 adds climate, land cover, surface water and the water table for the shortlisted KHG; those are shown on the profile pages and are not in the score. It is not the full level-1 run of [03](03-prioritisation.md).

## What is computed per KHG

| Column | From | Notes |
|---|---|---|
| `u_fire_freq` | burnt-area polygons | mean annual burned share of the KHG, baseline years; scored (weight 2) |
| `u_burn_repeat` | same | share burned twice or more in the baseline; scored (1) |
| `u_hotspot` | FIRMS VIIRS S-NPP 2012-2025 | vegetation-fire detections (type 0) of nominal or high confidence per km2 per year; scored (1) |
| `u_canal_primary`, `u_canal_secondary`, `u_canal_tertiary` | OSM-derived canal layer, class from `KODE_KANAL` (Kanal Primer, Sekunder, Tersier) | km of each class per km2 of KHG; scored with weights 0.5, 0.3, 0.2, which split the single canal weight used before (my default: the larger canals drain more; change it in the config or with the sliders). A KHG with no canal in the layer gets no value (not mapped), and its other parameters carry the score. `u_canal_density` (all classes together) is reported with weight 0 |
| `u_hotspot_now` | KLH-curated hotspots of the current year (`_data_hotspot_Januari_September_2026.gpkg`, MODIS) | hotspots of medium or high confidence on peat per km2 of peat, year to date; scored with its **own weight** (config `indicators.u_hotspot_now`, 0 drops it) and also ranked alone, by density (`peringkat_now`) and by number of hotspots (`peringkat_now_n`): density favours KHG with little peat, the count favours large ones, and which answers "most severe this year" is the team's call. Left out of `--mode validate`, because the current year comes after the held-out years |
| `u_burned_now` | burnt-area polygons, current-year flag (`BA_2026`) | burned share of the peat this year; reported, weight 0 |
| `u_frp`, `frp_mean_mw` | same hotspots | fire radiative power: reported, weight 0 (correlation 0.99 with hotspot density). Severity proxy |
| `n_infra_ada`, `n_desa_target` | BRGM structures, Bluebook villages | counts, reported |
| `i_peat_depth`, `peat_cover_frac` | BBSDLP 1:50,000 depth map | reported, weight 0: the map covers about 100 of 865 KHG |
| `n_tma_stations`, `tma_deep_share` | SiTMAT | stations inside and share of days deeper than 0.4 m; one season (2026), reported |
| `confidence` | derived | high = canal layer present, enough fire signal (30 baseline detections or any burned area) and area of 50 km2 or more; medium = two of three; low otherwise |

## Peat basis

The rates are per km2 of **peat**, with fire counted on peat only (`peat.basis: peat` in the config). The peat area per KHG comes from the Global Forest Watch peat extent (a composite, rasterised or resampled to 30 m; CC BY 4.0), which `repeat_common.fetch_peat_extent` builds from GFW's public tile cache at about 76 m. GFW describes it as a composite: for Indonesia the union of Miettinen et al. 2016 and Gumbricht et al. 2017 (so it can exceed either alone), and the Miettinen paper covers Peninsular Malaysia, Sumatra and Borneo, so Papua rests on Gumbricht's modelled map. Cells with partial transparency count as peat (fully opaque cells only would give about 6% less peat in a 24-tile sample). The report compares the peat share with the 1 km map per island, for the tiles that touch a KHG. "On peat" is a point sample: a burned patch counts as peat if its representative point is on a peat cell, a hotspot if the cell under it is peat (a MODIS pixel is much larger than a 76 m cell). KHG with under `min_peat_km2` (25) of peat are not ranked. The same ranking on KHG area is kept as `peringkat_area` for comparison (`peat.basis: area` switches everything back).

Other peat sources checked on 2026-10-22: BIG's RBI REST services (geoservices.big.go.id/rbi) have no national peat theme; the Ministry of Agriculture 1:50,000 map (Dec 2019) is listed by Trase only as province and kabupaten aggregates; the GFW download endpoint needs a free API key (the tile cache does not); the Global Peatland Map 2.0 (1 km, CC BY-NC-SA, non-commercial) is in `_data` as a cross-check.

## Stage 3: layers for the shortlisted KHG

For the top N KHG the engine's fetcher (`repeat-national-run --fetch-only`, config `configs/examples/national_stage3.yaml`) and `repeat-national-stage3` add: the TerraClimate dry-season water deficit and monthly rain (2015-2021; the dataset ends in 2021), ESA WorldCover land-cover shares and the share of permanent open water (both sampled at 250 m), the peat extent, and SiTMAT. Results: `reports/national_profile/stage3/stage3_profile.csv` (one row per KHG) and `stage3_yearly.csv`.

- **JRC** is the European Commission's Joint Research Centre. Its Global Surface Water dataset maps, from Landsat, how many months per year each 30 m cell holds water; "permanent water" here is the share of cells with water in 10 or more months. It is shown, not scored.
- **ERA5 dry spells are not used.** The hourly store costs about 70 s per month per KHG to read, and 25 km cannot tell neighbouring KHG apart. The reader is still in `repeat_common` for other uses.
- NDMI from Sentinel-2 is off (cost).
- These layers are coarse (4 km climate, 250 m sampled land cover) and are shown, not scored.
- A bug in `repeat_common.sources.static_cloud` is fixed here: it kept only the last STAC tile, so a KHG on a tile boundary got land cover or surface water for part of its area. Tiles are now mosaicked. The old caches under `repeat-prioritisation/data_local/cache` (Kampar-Gaung `71`, Sugihan-Lumpur `16.02.01`) were built before the fix; the Kampar-Gaung JRC water layer is 67% empty, so delete its `static/water_season.tif` and `static/worldcover.tif` and re-run to rebuild them.

## Land status overlays

`repeat-national-overlay --config configs/examples/national_stage3.yaml` crosses the profiled KHG (the stage 3 selection: top 25 and the team's) with four layers: forest area function (`KWSHUTAN_AR_250K_2023`), peat ecosystem function (`FEG__Indonesia__2017`), business licences (`ALL_Updade__IZIN_USAHA`, 2025) and the Bluebook target villages. Inputs are named under `inputs:` in the config, so an updated layer is a file swap. The four layers sit in `_data/landstatus/` (licences, FEG, forest area) and `_data/desa_target_pemulihan_ekosistem_gambut.gpkg`.

- **Method:** a regular grid of points inside each KHG (100 m, or 200 m for the largest). Each point gets its peat flag (GFW extent), its class in each layer, whether it burned in 2015 to 2025, and its licences. Areas are point counts times the cell area, never `Shape_Area`.
- **Licences overlap**, so licence areas are not summed: "any licence" counts a point once, and the per-type bars can add up to more than the peat. Forest area has 21 codes, grouped into conservation, protection forest, production forest (HP, HPT), convertible production (HPK), other land use (APL) and water or undefined.
- **5 km ring:** layer `ring` splits the KHG into land in a licence, land within 5 km of a licence but in none, and land farther away; the three add up. Licences are read out to 5 km beyond the KHG, so a licence next door still draws its ring, but only the part inside the KHG is counted. Per holder, `overlay_actors.csv` adds the ring area, its peat, the peat burned in 2015 to 2025 and this year's hotspots (`ring_*`); rings of neighbouring holders overlap and are not summed. The distance is `overlay.ring_km`. The 5 km comes from the Bluebook 2026 canal-block data (field `BUFFER`, "Buffer 5 Kilometer", programme "Kolaborasi Perusahaan (Area Buffer)"). KLH asked concession holders in July 2026 to join peat rewetting "di sekitar wilayah konsesinya" without naming a distance ([Ecobiz Asia, 10 July 2026](https://ecobiz.asia/cegah-karhutla-klh-minta-perusahaan-bantu-restorasi-gambut-di-sekitar-konsesi/)). No regulation text setting a 5 km duty was found, so the page calls it a ring, not an obligation. Holders in the table are sorted by hotspots in the licence and its ring together.
- **DPG villages:** the Desa Peduli Gambut villages of the BRG atlas (244 villages mapped in 2018-2019, six provinces; `python -m repeat_common.fetch_dpg_atlas`) are matched by name to the target village polygons (desa and kabupaten, kecamatan breaks ties): 177 match, listed with their `target_objectid` in `_data/dpg/dpg_atlas_villages.csv` (input `dmpg`). The overlay reports them as layer `dmpg`, the map fills them inside the target-village outlines, and the profile counts them per KHG (`n_dmpg`). The atlas holds only part of all DPG and DMPG villages, and the 67 unmatched have no polygon, so the layer is context and is not scored.
- **Hotspots** of this year are matched to the same polygons; the counts by class add back to the hotspots on peat of the profile (checked for all 34 KHG).
- **Outputs** in `reports/national_profile/stage3/overlay/`: `overlay_summary.csv` (area, peat, burned peat and hotspots per KHG, layer and class; licence rows also show the area on protected peat function and on conservation or protection forest), `overlay_actors.csv` (licence holders per KHG: area, area on protected function, burned peat, hotspots), `overlay_map.json` (clipped polygons for the dashboard).
- **Reading it:** the figures say where fire falls, not who set it. A licence layer dated 2025 is matched to hotspots of 2026 and burns of 2015 to 2025, so a holder may not have held the land in earlier years. Set `overlay: {company_names: false}` in the config to publish the page without holder names.
- Not scored: the overlays do not enter the ranking.

## This year's hotspots

The KLH file has one layer per month and two attribute schemas: January, April, August and September carry a numeric confidence, a class (Rendah, Sedang, Tinggi), FRP and the acquisition date; February, March, May, June and July carry only Kepercayaan (Low, Medium, High), with no FRP and no date. `repeat-prioritisation` harmonises the confidence to low, medium and high across all nine months (month comes from the layer name), keeps medium and high, and counts hotspots, so FRP, which exists for four of nine months, is reported but never summed or scored. The record ends on the last acquisition date in the file (15 September 2026), so it is year to date. MODIS (1 km) counts are not comparable with the VIIRS archive; that is why this is a separate indicator with a separate weight and rank, not an extra year of the history. The file has 9 repeated coordinate pairs out of 167,718 (all in June and July), left in. The profile maps show the actual points of this year (filled = on peat, hollow = off peat, larger = high confidence), not cells.

## The dashboard

`dashboard.html` ranks the 865 KHG live in the browser. The sliders set the weight of eight parameters in three groups (fire history, this year, canals); the filters set the minimum peat area and the island; a switch says how to treat a KHG with no mapped canals (ignore the canal parameters, or give it the average value). The scoring in the page is the scaling of `common.scoring`: each parameter runs from 0 to 1 between the 5th and 95th percentile of the KHG that pass the filters, and the score is the weighted mean of the parameters a KHG has. At the default weights and filters the page reproduces the Python ranking; this is checked on load (`data-parity` on the body, for example `150:0` means 150 ranks compared, 0 differ).

- **Ranking:** bars show how much each group adds to the score; the arrow is the change against the default weights. `Team KHG` lists the team's selected KHG whatever their rank.
- **Rank shift:** default rank against rank at your weights, for the top 12 of each.
- **Profile:** the KHG you click, with the 34 KHG that have one (the top 25 at default weights and the team's). Strip plots place the KHG among all ranked KHG for each parameter; the line charts show burned share, VIIRS hotspots, this year's hotspots by month, TerraClimate deficit and rain; the map has burn counts, canals by class and this year's hotspot points.
- **Hover help:** the weight labels explain each parameter's source and method; the filters, KPI tiles, chart titles, legends and map layer chips have a short note. In the table, a header shows the unit and source, a cell shows the value with its unit, and the table can be searched, sorted by any column and extended to the KHG that are not ranked. In table mode the list spans the full width.
- **Hotspot confidence:** a filter switches this year's hotspot parameter between medium + high (default) and high only (KLH Tinggi). The ranking, the profile tile with its ranks, the monthly chart and the map points follow; the address keeps it as `c=h`. High-only density is the high-confidence count on peat divided by peat area, taken from `hs_now_high_share` in the profile table. The land-status bars still use medium + high.
- **Layer selector:** both maps have checkbox chips to switch layers off. The national map toggles the score fill, the team outline and the place names. The profile map toggles the peat extent (the GFW cells the rates are divided by), burned area, the three canal classes and this year's hotspots, and has the land-status switch below.
- **Land status:** on the profile map a switch shows forest area function, peat function or licences (hover gives the class or the holder) and a chip draws the target villages. Under the strip plots, stacked bars compare how the peat, the burned peat and this year's hotspots split over each layer, followed by the licence holders with the most hotspots in their area.
- **Link state:** the address holds the weights, filters, view, theme, language (`l=id`) and selected KHG, so a view can be shared.
- **Language:** English and Bahasa Indonesia, switched with the EN / ID buttons in the header; the first visit follows the browser language. Interface text, tooltips, table headers and map labels switch together, and numbers use the local format. The Indonesian strings are in `national/assets/i18n_id.js`, a dictionary keyed by the English text; a string missing from it shows in English, so a new label needs one added line. The page also has a table view with a CSV download.

- **Basemap:** both maps use OpenFreeMap vector tiles (Positron style, OpenMapTiles data, OpenStreetMap contributors), drawn with MapLibre GL JS, muted so the data stays in front, with a dark variant for the dark theme. The tiles load from the internet; offline, the page still works and the maps show the KHG without a basemap. D3 and MapLibre are copied into `national/assets`, so nothing else is fetched.

Ties at the top of a single parameter (many KHG at the 95th percentile cap) are ordered by the unclipped values.

## Two modes

- `--mode validate`: indicators from the baseline (2015-2022), tested on 2023-2025 (AUC, share of later fire captured by the top 20%), next to the same measures for "where it burned before" alone.
- `--mode operational`: the baseline runs to the end of the validation years; no held-out test. The report ranks on this.

## Decisions that shaped the result

- Hotspot confidence: low (`l`) dropped, non-vegetation-fire types dropped; both are config settings, and the raw layer keeps everything.
- Hotspots come from VIIRS S-NPP only (the one sensor with a country archive back to 2012). The 2026 MODIS hotspots in `_data` are not mixed in: a different sensor with different counts.
- Weights are provisional. Fire frequency counts double; change them in `configs/examples/national_profile.yaml`.
- The canal layer is OSM-derived and patchy: 517 KHG have none. Zero would read as "no canals" and pull the score down, so it stays missing.

## Not in the score yet

Peat depth (the BBSDLP map covers about 100 KHG), NDMI, concessions, tidal influence, fire severity (dNBR), feasibility (distance to water, DTM), and any scoring of the Stage 3 layers (they are shown only).

## Run

```bash
export REPEAT_DATA=.../_data REPEAT_WORK=.../re-peat/reports REPEAT_HUB=.../re-peat SITMAT_PROCESSED=.../repeat-sitmat/sitmat_out/processed
python tools/fetch_firms.py                   # wrapper of repeat_common.fetch_firms: yearly FIRMS files -> _data/hotspot_viirs_snpp_<y0>_<y1>.gpkg (polite: one file at a time)
python tools/fetch_peat_extent.py             # wrapper of repeat_common.fetch_peat_extent: GFW peat extent for the KHG -> _data/peat_extent_gfw_v20230315_z11.tif
python tools/parse_kepmen_khg.py              # re-peat: official KHG table -> sites/khg_registry.csv (needs pdfplumber)
python tools/catalog_data.py                  # re-peat: refresh the data catalogue
# Stage 3 needs the cloud stack: python -m venv _repeat-project/.venv; pip install -e repeat-common pyogrio pdfplumber matplotlib pysheds
repeat-national-profile --config configs/examples/national_profile.yaml --mode validate        # repeat-prioritisation, about 8 min
repeat-national-profile --config configs/examples/national_profile.yaml --mode operational
repeat-national-dashboard --config configs/examples/national_profile.yaml --top 25   # the interactive page
repeat-national-stage3 select --config configs/examples/national_stage3.yaml            # top-N boundaries from the operational ranking
repeat-national-run --config configs/examples/national_stage3.yaml --fetch-only         # TerraClimate, WorldCover, JRC (about 10 min for 25 KHG)
repeat-national-stage3 summarize --config configs/examples/national_stage3.yaml
repeat-national-overlay --config configs/examples/national_stage3.yaml                  # land-status overlays for the same KHG
repeat-national-dashboard --config configs/examples/national_profile.yaml --top 25   # picks up the stage 3 tables; --reassemble reuses the last data
python -m tests.test_national_profile
```

When the data change (new year of hotspots, a peat map, a better canal layer): update the file, rerun the catalogue, rerun the two profile modes and the report. Add a layer's indicator in `profile.py` and its weight in the config.
