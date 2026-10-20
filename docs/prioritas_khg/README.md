# prioritas_khg: rewetting prioritisation for KHG, in Python

> **Full documentation:** see [`../docs/`](../docs/README.md), especially [`03-prioritisation.md`](../docs/03-prioritisation.md) for every parameter explained, [`05-parameters.md`](../docs/05-parameters.md) for sources and confidence, and [`06-pitfalls-faq.md`](../docs/06-pitfalls-faq.md) before trusting results.

Ranks peat areas by how urgently they need rewetting, what is at stake there, and how feasible rewetting is. It works at two levels:

| Level | Unit | Question | Layers |
|---|---|---|---|
| **1 — national screening** (`level: khg`) | one unit per KHG | Which KHG should we focus on? | Coarse, wall-to-wall: climate, burned area, hotspots, peat depth, protected peat, canal density. 250 m grid. No Sentinel-2, no feasibility. |
| **2 — detailed** (`level: subkhg`) | sub-KHG (automatic), hexagons or your polygons | Inside the selected KHG, where and with what? | Everything, including NDMI, DTM, canal reach, pumping lift, metrik IPG, tidal zone, concessions. 30 m grid. |

Level 1 writes `khg_terpilih.gpkg`; use it as the `khg` input of level 2. It's the Python alternative to a GEE workflow: layers are read from cloud-native sources (STAC + COG/Zarr), so only each KHG's window is transferred, and every step runs locally.

## Sub-KHG delineation (level 2 default)

Follows the Kahayan–Sebangau study (2021), automated:

1. Rivers and canals are burned into the DTM (`dtm_smooth.tif` from `demnas_dtm`).
2. D8 flow direction and accumulation (pits, depressions and flats resolved), stream network, Strahler order.
3. Outlet channels = mapped rivers + primary canals (`canal_class_field`, `outlet_canal_classes`) + DEM streams of order ≥ k. k is chosen automatically so each KHG gets `target_count` sub-KHG (default 6–30).
4. Each cell is traced downstream to the first outlet channel. Each sub-KHG is the catchment of one channel reach on one bank, so divides and outlet channels form the boundaries, as found in the field in that study.
5. Pieces smaller than `min_area_km2` are merged into a neighbour. The result is saved to `cache/<khg>/subkhg.gpkg` with `stream_order.tif` and `flow_accumulation.tif` for checking.

`units.mode: vector` uses your own sub-KHG polygons instead (e.g. the 16 Kahayan–Sebangau sub-KHG), and `hex` uses 1 km² hexagons.

## Algorithm

```
KHG boundary ─► units (1 km² hexagons, or your sub-KHG polygons)
      │
      ├─ cache per KHG on a 30 m UTM grid (fetched once, reused)
      │     annual: NDMI, burned area, water deficit, dry spells
      │     static: land cover, surface water;  points: FIRMS hotspots
      │     plus your vectors/rasters: canals, rivers, peat depth, DTM, protected peat, TMA
      │
      ├─ indicators per unit, from BASELINE years only
      │     urgency u_*   impact i_*   feasibility f_*
      │
      ├─ robust 0–1 normalisation across all KHG (5th–95th percentile)
      ├─ group scores = weighted mean of available indicators (weights or AHP)
      ├─ risk = α·urgency + (1−α)·impact          (α = 0.6)
      ├─ classes: risk tertiles × feasibility tertiles
      │
      └─ checks: indicator correlation · weight sensitivity · validation on held-out years
```

### Indicators

| Code | Meaning | Source (default) | Direction |
|---|---|---|---|
| `u_deficit` | Dry-season climatic water deficit (mm), mean of baseline years | TerraClimate `def` (Planetary Computer Zarr) | ↑ urgent |
| `u_wb_mean` | Mean monthly water balance P(1 − interception)(1 − C) − ET (mm) | TerraClimate `ppt`, `aet` + WorldCover interception | ↓ urgent |
| `u_deficit_months` | Months per year with negative water balance | same | ↑ |
| `u_deficit_elnino` | Same, El Niño years only | TerraClimate | ↑ |
| `u_ndmi` | Median dry-season NDMI (Aug–Oct composite) | Sentinel-2 L2A (STAC), SCL cloud mask, BOA offset corrected | ↓ urgent |
| `u_dryspell` | Longest run of dry days (< 1 mm) | CHIRPS daily COGs | ↑ |
| `u_spell14` | Number of dry spells ≥ 14 days per year | CHIRPS daily | ↑ |
| `u_fire_freq` | Mean share of years burned | MODIS MCD64A1, or your dNBR/KLH maps | ↑ |
| `u_hotspot` | Hotspots per km² per year | FIRMS VIIRS (nominal/high confidence) | ↑ |
| `u_canal_density` | Canal length per km² | your canal layer | ↑ |
| `u_tma` | Share of logger days with water table deeper than 0.4 m | your TMA CSV | ↑ |
| `u_tma_recession` | Mean dry-period water-table decline (mm/day), intervals where it rose ignored | your TMA CSV | ↑ |
| `u_ipg_gap` | 1 − metrik IPG; IPG = existing blocks ÷ blocks needed, spacing = 0.4 m ÷ canal slope | canals (+ class), DTM, existing blocks | ↑ |
| `i_peat_depth` | Mean peat depth | your raster | ↑ important |
| `i_water_stock` | Peat water stock (m): thickness × 0.8, or × 0.7 within canal reach | peat depth + canals | reported, weight 0 by default |
| `i_protected` | Share in protected-function peat (lindung) | your vector | ↑ |
| `i_exposure` | Share within 2 km of settlements | your vector | ↑ |
| `i_forest` | Share of remaining forest / mangrove | ESA WorldCover | ↑ |
| `f_reach` | Share within canal influence distance (200 m; 60 m on burnt peat) | canals + burned area | ↑ feasible |
| `f_water_dist` | Mean distance to dry-season water (JRC seasonality ≥ 10 months, RBI rivers/lakes) | JRC GSW + your vectors | ↓ feasible |
| `f_lift` | Median height above the nearest water source (pumping lift proxy) | `dtm_smooth.tif` from `demnas_dtm` | ↓ feasible |
| `f_access` | Mean distance to roads | your vector | ↓ feasible |
| `v_burned_frac`, `v_hotspot` | Burned share and hotspot density in **validation** years | same sources | targets only |

Water balance and IPG parameters come from the team's Kahayan–Sebangau study (2021): interception from 0 % (open land) to 16.4 % (forest), runoff coefficient 0.07–0.18 measured on Pulau Padang (default 0.12), water content 0.8 / 0.7, design water-table limit dA = 0.4 m. The water-stock indicator is total water, not drainable water: only the specific-yield part drains as the water table falls.

Extra unit attributes (not scored): `tidal_share`, `pengelola` (dominant concession type or "Non-konsesi"), `porsi_dikecualikan`, `kemiringan_kanal`, `n_sekat_ada`, `n_sekat_perlu`, `sekat_tambahan`.

Missing indicators don't break a unit: each group score is the weighted mean of what's available, and `cakupan_*` columns report how much of the weight was covered. Indicators available for fewer than 20 units (e.g. sparse TMA loggers) are reported but not scored.

### Classes

| Risk \ Feasibility | Low | Medium | High |
|---|---|---|---|
| **High** | Siaga pemadaman | Prioritas 1: pembasahan | Prioritas 1: pembasahan |
| **Medium** | Pantau dan rencanakan | Pantau dan rencanakan | Prioritas 2: pembasahan |
| **Low** | Pantau | Pantau | Pantau |

Tertiles are computed across all KHG, or set fixed thresholds in `scoring.fixed_thresholds`. Two override classes:

- **Pengaruh pasang surut: pantau**, when `scoring.tidal_mode: exclude` and at least half the unit is tidal. The default `downweight` instead reduces urgency by 70 % × tidal share.
- **Dikecualikan (pengelolaan lahan)**, when at least half the unit is a concession type listed in `vectors.concessions.exclude_types` (default IUP).

At level 1 the classes are **Fokus nasional: tinggi / sedang / rendah** (risk tertiles).

`scoring.normalise_scope: all` compares units across every KHG in the run. Use `khg` to rank within each KHG separately, for example when each KHG has its own budget.

### Checks

- **Correlation.** Spearman between normalised indicators; pairs above 0.8 are flagged as possible double counting (e.g. deficit and dry spells often move together).
- **Sensitivity.** 300 Monte Carlo runs perturb weights (Dirichlet around your weights) and α. Per unit you get `p_prioritas1` (share of runs in Prioritas 1), `p_top_risiko` and `sd_peringkat`.
- **Validation.** Indicators use baseline years only (default 2016–2022). The ranking is then tested on burned area and hotspots in the held-out year(s) (default 2023):
  - AUC;
  - share of validation burned area captured by the top 20% of units (random = 20%);
  - Spearman correlation.

  The same metrics are computed for urgency alone and for fire history alone, so you can show what the method adds over "where it burned before".

## Run

```bash
# level 1: national screening, then level 2 on the selected KHG
python run.py --config level1.yaml --level khg          # writes out/khg_terpilih.gpkg
python run.py --config level2.yaml --level subkhg       # khg: out/khg_terpilih.gpkg

pip install -r requirements.txt
python run.py --print-default-config > config.yaml     # edit paths and years
python run.py --config config.yaml                     # fetch missing layers, then score
python run.py --config config.yaml --fetch-only        # just build the cache
python run.py --config config.yaml --skip-fetch        # re-score from cache (e.g. new weights)
```

Minimal config:

```yaml
khg: data/khg_sample8.gpkg
khg_id_field: khg_id
units: {mode: hex, hex_area_km2: 1.0}       # or {mode: vector, path: data/sub_khg.gpkg}
years: {baseline: [2016, 2022], validation: [2023], elnino: [2015, 2019, 2023]}
vectors:
  canals: data/kanal.gpkg
  rivers: data/rbi_sungai.gpkg
  settlements: data/rbi_permukiman.gpkg
  protected: {path: data/fungsi_ekosistem_gambut.gpkg, field: fungsi, values: [lindung]}
  tma_csv: data/sipalaga.csv                # station_id, date, wtd_m, lon, lat
  blocks: data/sekat_kanal_existing.gpkg    # for metrik IPG
  tidal: data/zona_pasang_surut.gpkg
  concessions: {path: data/konsesi_iup.gpkg, type_field: jenis, exclude_types: [IUP]}
rasters:
  peat_depth: data/kedalaman_gambut.tif
  dtm: out_dtm/dtm_smooth.tif
```

For the operational ranking (rather than validation), set `baseline` to include the latest year and leave `validation` empty or set to a year you only want for reporting.

### Using your own layers instead of the cloud

Every source has a `local` key, for example:

```yaml
sources:
  burned: {local: "data/dnbr/burned_{year}.tif"}     # any value > 0 = burned
  ndmi:   {local: "data/ndmi/ndmi_{year}.tif"}
  firms:  {local: "data/firms/viirs_indonesia_2015_2023.csv"}
```

Local files are reprojected to the KHG grid. Files already in `cache/<khg_id>/` are never refetched, so you can also drop prepared GeoTIFFs there directly.

### Weights and AHP

Change weights per indicator (`indicators: {u_fire_freq: {weight: 3}}`), disable one (`enabled: false`), or give a pairwise matrix per group:

```yaml
ahp:
  u:
    indicators: [u_fire_freq, u_deficit, u_ndmi]
    matrix: [[1, 3, 3], [0.333, 1, 1], [0.333, 1, 1]]
```

The consistency ratio is reported; above 0.10 triggers a warning.

## Outputs (`out/`)

| File | Content |
|---|---|
| `unit_prioritas.gpkg` / `.csv` | Every unit: raw indicators, normalised `n_*`, group scores, `skor_risiko`, `kelas`, `peringkat`, sensitivity fields, validation targets |
| `khg_terpilih.gpkg` | Level 1: top KHG (`scoring.level1_top_n`) to run at level 2 |
| `kebutuhan_sekat.csv` | Level 2: blocks needed, existing and additional per KHG and class (first cost estimate) |
| `peta_prioritas_<khg>.png` | Urgency, impact, feasibility and class maps per KHG |
| `ringkasan_kelas.csv` | Units and km² per class per KHG |
| `korelasi_indikator.csv` | Spearman matrix |
| `laporan.json` | Weights, AHP consistency, thresholds, class counts, correlated pairs, sensitivity, validation, indicator coverage, config |

## Status of the code

- **Tested on synthetic data**: six KHG for level 1 (ranking followed the built-in risk intensity) and sub-KHG delineation, IPG, tidal and concession handling at level 2 (12 and 11 sub-KHG per KHG, bounded by divides and primary canals; see `contoh_subkhg_sintetis.png`). With a known fire-risk field, the top 20% of units captured 64% of held-out burned area (random would be 20%). Urgency alone reached AUC 0.79, above fire history alone at 0.77.
- **Not yet tested on live data.** The cloud fetchers (Planetary Computer STAC for Sentinel-2, MODIS burned area, WorldCover and JRC water; TerraClimate Zarr; CHIRPS COGs; FIRMS country CSVs) are written against those services' documented interfaces but couldn't be reached from the build environment. Run `--fetch-only` on one small KHG first and check the log. Every source fails independently, logs why, and can be replaced by a local file.
- **Coarse climate layers.** TerraClimate (~4 km) and CHIRPS (~5 km) are much coarser than 1 km² units. They separate KHG and large zones, not neighbouring hexagons. Fine-scale contrast comes from NDMI, fire, canals and peat depth.
- **FIRMS country files** are large; for many runs, download them once and point `sources.firms.local` at the file.
