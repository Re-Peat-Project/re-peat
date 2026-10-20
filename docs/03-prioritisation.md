# 03 Prioritisation (`prioritas_khg`)

> **Status after the split (2026-10-20).** Written for `prioritas_khg`. Delineation is now `repeat-delineation`, scoring is `repeat-prioritisation` (national and sub-KHG), and the shared readers are in `repeat-common`. `units.mode: subkhg` no longer exists: delineate first, then score the polygons with `mode: vector`. Read this page for the method; the repositories' READMEs have the commands.

## What it produces

For every analysis unit (a whole KHG at level 1, a sub-KHG at level 2) the tool computes three scores between 0 and 1, combines two of them into a risk score, and assigns a class:

- **Urgency (urgensi):** how fast and how badly this unit dries and burns if left alone.
- **Impact (dampak):** what is lost if it burns: deep peat, protected peat, people nearby, remaining forest.
- **Feasibility (kelayakan):** how realistically it can be rewetted: canal reach, water source, pumping lift, access.
- **Risk = 0.6 × urgency + 0.4 × impact.**

Risk and feasibility together decide the action: rewet (high risk, feasible) or prepare for firefighting (high risk, not feasible). That split is the most useful thing to show decision makers.

## Pipeline

```
1. Units           level 1: KHG polygons; level 2: automatic sub-KHG (or hexagons / your polygons)
2. Cache           per KHG, on a common UTM grid; fetched once, reused
3. Indicators      per unit, from BASELINE years only
4. Normalise       each indicator to 0–1, robustly (5th–95th percentile)
5. Score           weighted mean per group (missing indicators skipped, weights re-scaled)
6. Classify        risk tertiles × feasibility tertiles (+ tidal / excluded overrides)
7. Check           correlation · weight sensitivity · validation on held-out years
```

## Level 1 vs level 2

```bash
python run.py --config level1.yaml --level khg       # all KHG in the boundary file
python run.py --config level2.yaml --level subkhg    # khg: out_L1/khg_terpilih.gpkg
```

What the `khg` level preset changes automatically:

| Setting | Level 1 | Level 2 |
|---|---|---|
| `units.mode` | khg | subkhg |
| `grid_res_m` | 250 | 30 |
| Sentinel-2 NDMI | off (too heavy nationally) | on |
| Feasibility indicators, IPG | weight 0 (canal and DTM data uneven) | on |
| Sensitivity runs | 0 | 300 |
| Classes | Fokus nasional: tinggi / sedang / rendah | five action classes |

Anything you set in your own config overrides the preset.

## Units

| `units.mode` | What a unit is | Use when |
|---|---|---|
| `khg` | the whole KHG | level 1 |
| `subkhg` (default) | automatically delineated sub-KHG | level 2, standard |
| `vector` | your polygons (`units.path`, `units.id_field`) | you already have agreed sub-KHG, e.g. the 16 Kahayan–Sebangau units |
| `hex` | hexagons of `hex_area_km2` (default 1 km²) | finer ranking, or when the DTM is too poor to delineate |

### Sub-KHG delineation (`delineate.py`)

The method follows the 2021 Kahayan–Sebangau study, automated:

1. **Burn channels.** Mapped rivers and canals are lowered by `burn_depth_m` (3 m) in the DTM, because canals are narrower than a cell and would otherwise be invisible to flow routing.
2. **Flow routing.** D8 flow direction (each cell drains to its steepest neighbour) after filling pits and depressions and resolving flats; flow accumulation counts how many cells drain through each cell.
3. **Streams.** Cells with contributing area above `stream_threshold_km2` (2 km²) are streams; Strahler order ranks them (two order-1 streams meeting make order 2, and so on).
4. **Outlet channels.** Mapped rivers + canals of the classes in `outlet_canal_classes` (primary by default, read from `canal_class_field`) + DEM streams of order ≥ k. If `outlet_order` is not set, k is chosen automatically so the number of sub-KHG falls in `target_count` (6–30).
5. **Catchments by bank.** Each cell is traced downstream to the first outlet cell it reaches; cells reaching the same channel reach form a catchment, then each catchment is split along the channel into its two banks. Divides and outlet channels therefore form the boundaries, matching the field finding that sub-KHG boundaries are the wide outlet canals.
6. **Clean-up.** Pieces smaller than `min_area_km2` (5 km²) are merged into a neighbour; channel cells go to the nearest unit.

Check files: `cache/<khg>/subkhg.gpkg`, `stream_order.tif`, `flow_accumulation.tif`. The log lists the counts tried for each order.

| Key (`units.subkhg.*`) | Default | Meaning |
|---|---|---|
| `burn_depth_m` | 3.0 | how deep mapped channels are cut into the DTM |
| `stream_threshold_km2` | 2.0 | contributing area that starts a DEM stream; smaller = more streams |
| `outlet_order` | auto | fix the Strahler order used for outlets |
| `target_count` | [6, 30] | wanted sub-KHG per KHG in automatic mode |
| `min_area_km2` | 5.0 | minimum sub-KHG size |
| `canal_class_field` | none | attribute holding canal class; if empty, every canal is an outlet |
| `outlet_canal_classes` | primer, primary | canal classes treated as outlets |
| `use_dem_streams` | true | false = mapped channels only |

## Indicators

Every indicator is computed **only from baseline years** (default 2016–2022) so the ranking can be tested on later years. Direction "↑" means a higher value raises the score; "↓" means a lower value raises it.

### Urgency (`u_*`)

| Code | What it measures | How it's computed | Data | Dir | Weight |
|---|---|---|---|---|---|
| `u_deficit` | dry-season climatic water deficit | sum of TerraClimate `def` (PET − AET) over `dry_months`, mean over years | TerraClimate | ↑ | 0.5 |
| `u_wb_mean` | average monthly water balance | P × (1 − interception) × (1 − C) − ET, monthly, unit mean | TerraClimate `ppt`, `aet`; WorldCover | ↓ | 1 |
| `u_deficit_months` | how long deficits last | months per year with negative balance | same | ↑ | 1 |
| `u_deficit_elnino` | worst-case deficit | `u_deficit` in El Niño years within the baseline | TerraClimate | ↑ | 0.5 |
| `u_ndmi` | surface and vegetation dryness | median NDMI of an August–October composite (clouds masked), unit median, mean over years | Sentinel-2 L2A | ↓ | 1 |
| `u_dryspell` | longest drought run | longest run of days with rain < 1 mm | CHIRPS daily | ↑ | 0.5 |
| `u_spell14` | frequency of long droughts | dry spells ≥ 14 days per year (the TMA can fall ~25 cm in 14 days) | CHIRPS daily | ↑ | 0.5 |
| `u_fire_freq` | fire history | mean share of years burned per pixel | MODIS MCD64A1 or your dNBR maps | ↑ | 2 |
| `u_hotspot` | fire activity | VIIRS hotspots per km² per year (nominal/high confidence, static sources removed) | FIRMS | ↑ | 1 |
| `u_canal_density` | drainage pressure | canal km per km² | your canal layer | ↑ | 1 |
| `u_tma` | measured dryness | share of logger days with TMA deeper than 0.4 m | your TMA CSV | ↑ | 1 |
| `u_tma_recession` | how fast it dries | mean water-table decline (mm/day) over intervals when it fell; rises ignored | your TMA CSV | ↑ | 1 |
| `u_ipg_gap` | missing blocks | 1 − metrik IPG (see below) | canals, DTM, existing blocks | ↑ | 1.5 |

Fire history carries the most weight because it is closest to what we want to prevent, but it is not enough on its own: validation compares the full score against fire history alone to show what the other indicators add.

### Impact (`i_*`)

| Code | What it measures | How | Data | Dir | Weight |
|---|---|---|---|---|---|
| `i_peat_depth` | carbon and subsidence at stake | mean peat thickness | your peat depth raster | ↑ | 2 |
| `i_protected` | legal priority | share in fungsi lindung | your zoning layer | ↑ | 1 |
| `i_exposure` | people affected by fire and haze | share within 2 km of settlements | your settlement layer | ↑ | 1 |
| `i_forest` | remaining forest | share of tree cover and mangrove | WorldCover | ↑ | 1 |
| `i_water_stock` | peat water stock | thickness × 0.8 (0.7 within canal reach) | peat depth + canals | ↑ | 0 (reported only; duplicates peat depth) |

### Feasibility (`f_*`)

| Code | What it measures | How | Data | Dir | Weight |
|---|---|---|---|---|---|
| `f_reach` | how much of the unit canals can rewet | share within 200 m of a canal (60 m on burnt peat) | canals + burned area | ↑ | 2 |
| `f_water_dist` | distance to dry-season water | mean distance to water present ≥ 10 months a year, rivers, lakes, tidal zone | JRC surface water + your vectors | ↓ | 1 |
| `f_lift` | pumping effort | median height above the nearest water source | `dtm_smooth.tif` | ↓ | 1 |
| `f_access` | logistics | mean distance to roads | your road layer | ↓ | 0.5 |

### Metrik IPG (block adequacy)

From the 2021 study: on a canal with land slope *s*, keeping the water table within *dA* = 0.4 m of the surface needs a block every *js* = *dA* ÷ *s* metres. For each unit:

```
canal length L         (primary + secondary canals only, if classes are given)
canal slope s          (median DTM slope along those canals)
spacing js             = clip(0.4 / s, 50 m, 2000 m)        × 2 for category B ("adequate")
blocks needed Ns       = L / js
existing blocks ns     (points inside the unit)
metrik IPG             = ns / Ns        (≥ 1 is good)
u_ipg_gap              = 1 − min(1, metrik IPG)
sekat_tambahan         = Ns − ns        (first estimate of blocks to build)
```

`kebutuhan_sekat.csv` sums these by KHG and class: a first, rough basis for a budget. Category B doubling the spacing is our reading of the 2021 report's "adequate" category; check before quoting.

### Extra attributes (not scored)

| Field | Meaning |
|---|---|
| `tidal_share` | share of the unit in the tidal zone |
| `pengelola` | dominant land manager: concession type covering ≥ 50%, "Campuran" (mixed) or "Non-konsesi" |
| `porsi_dikecualikan` | share covered by excluded concession types (default IUP) |
| `kemiringan_kanal`, `n_sekat_ada`, `n_sekat_perlu`, `sekat_tambahan`, `m_ipg` | IPG details |
| `cakupan_urgensi`, `cakupan_dampak`, `cakupan_kelayakan` | share of the group's weight that had data for this unit |
| `v_burned_frac`, `v_hotspot` | burned share and hotspot density in validation years (targets only, never used in scores) |

## Scoring

### Normalisation

Each indicator is rescaled so the 5th percentile becomes 0 and the 95th becomes 1 (values beyond are clipped). Using percentiles instead of min/max stops a single extreme unit from squashing everyone else. For "↓" indicators the scale is flipped so 1 is always "more urgent/important/feasible".

`normalise_scope`:
- `all` (default): units are compared across every KHG in the run. Use when KHGs compete for one budget.
- `khg`: each KHG is normalised separately. Use when each KHG has its own budget and you only need a ranking inside it.

Indicators available for fewer than `min_units_per_indicator` units (20, or half the units in small runs) are reported but not scored. Sparse logger data usually falls here.

### Group scores and weights

A group score is the weighted mean of the normalised indicators the unit has. If a unit lacks one, the others' weights are scaled up, and `cakupan_*` records how much of the weight was covered (treat low coverage with care).

Weights can be changed per indicator:

```yaml
indicators:
  u_fire_freq: {weight: 3}
  u_dryspell: {enabled: false}
```

or derived from expert pairwise comparisons (AHP) per group:

```yaml
ahp:
  u:
    indicators: [u_fire_freq, u_wb_mean, u_ndmi]
    matrix: [[1, 3, 3], [0.333, 1, 1], [0.333, 1, 1]]   # "fire history is 3× as important as…"
```

The consistency ratio is reported; above 0.10 the comparisons contradict each other and should be revised. AHP is a good format for an FGD with KLH.

`alpha_urgency` (0.6) sets how much risk depends on urgency versus impact.

### Classes (level 2)

| Risk \ Feasibility | Low | Medium | High |
|---|---|---|---|
| **High** | Siaga pemadaman | Prioritas 1: pembasahan | Prioritas 1: pembasahan |
| **Medium** | Pantau dan rencanakan | Pantau dan rencanakan | Prioritas 2: pembasahan |
| **Low** | Pantau | Pantau | Pantau |

Thresholds are tertiles of all units, or fixed values in `fixed_thresholds`. Overrides:
- **Pengaruh pasang surut: pantau** if `tidal_mode: exclude` and ≥ 50% of the unit is tidal. The default `downweight` reduces urgency by `tidal_factor` (0.7) × tidal share instead, since tidal areas rarely dry out.
- **Dikecualikan (pengelolaan lahan)** if ≥ 50% is an excluded concession type (default IUP).

Within a class, units are ordered by risk; `peringkat` is the overall rank.

## Checks

### Correlation

Spearman correlation between normalised indicators. Pairs above 0.8 are flagged: two indicators measuring the same thing (e.g. water deficit and dry spells) double their weight without adding information. Drop one or lower both weights.

### Weight sensitivity

300 runs perturb the weights (random draws centred on yours; `sensitivity_concentration` = 20 controls how far they move) and alpha (± 0.1). Per unit:
- `p_prioritas1`: share of runs in which the unit is Prioritas 1. Above 0.8 or below 0.2 = stable decision.
- `p_top_risiko`: share of runs in the top 20% by risk.
- `sd_peringkat`: how much its rank moves.

Report the share of units with a stable class; present unstable units as "depends on how you weigh things", not as firm priorities.

### Validation on held-out years

Indicators use baseline years only; the ranking is then tested against what happened in validation years (default 2023):
- **AUC:** probability that a randomly chosen unit that burned (≥ 5% of its area) scored higher than one that didn't (0.5 = no skill, 1 = perfect).
- **Capture:** share of the validation year's burned area falling in the top 20% of units (random = 20%).
- **Spearman:** rank agreement between score and burned share.

The same metrics are computed for **urgency alone** and **fire history alone**. Expect urgency to predict fire better than the combined risk score: impact describes what is at stake, not where fire will happen. In the paper, validate urgency as the predictor and present impact as a value judgement agreed with KLH. For the operational ranking, extend the baseline to the latest year.

## Data and parameters

### Inputs you provide (`vectors`, `rasters`)

| Key | Content | Required for |
|---|---|---|
| `khg` | KHG boundaries | always |
| `vectors.canals` | canal lines; optional class field | canal density, reach, IPG, delineation |
| `vectors.rivers`, `lakes` | RBI water features | water source, delineation |
| `vectors.blocks` | existing canal blocks (points) | metrik IPG |
| `vectors.tidal` | tidal zone polygons | tidal handling |
| `vectors.concessions` | `path`, `type_field`, `exclude_types` | land manager, exclusion |
| `vectors.protected` | `path`, `field`, `values` (e.g. lindung) | `i_protected` |
| `vectors.settlements`, `roads` | RBI layers | exposure, access |
| `vectors.tma_csv` | `station_id, date, wtd_m, lon, lat` | `u_tma`, `u_tma_recession` |
| `rasters.peat_depth` | thickness (m) | impact |
| `rasters.dtm` | `dtm_smooth.tif` | delineation, lift, IPG |

### Cloud sources (`sources`)

| Source | Default | Notes |
|---|---|---|
| `ndmi` | Sentinel-2 L2A, Planetary Computer STAC; bands B8A/B11/SCL; 20 m; scenes < 60% cloud; SCL classes 4–7 kept | the +1000 reflectance offset of processing baseline ≥ 04.00 is removed |
| `burned` | MODIS MCD64A1 (500 m) | replace with dNBR or KLH burned area via `local` for detail |
| `deficit` | TerraClimate Zarr: `def`, plus monthly `ppt`, `aet` | ~4 km: separates KHG and large zones, not neighbouring units |
| `chirps` | CHIRPS 2.0 daily COGs | ~5 km; daily reads are cached per year |
| `worldcover` | ESA WorldCover 10 m | land cover classes used throughout |
| `water` | JRC Global Surface Water seasonality | months per year with water |
| `firms` | VIIRS country yearly CSV | large files; download once and use `local` |

Each source has a `local` key (`"path/ndmi_{year}.tif"`) and can be disabled. Files already in `cache/<khg>/` are never refetched, so you can also drop prepared GeoTIFFs there.

### Main parameters (`params`, `scoring`)

| Key | Default | Meaning |
|---|---|---|
| `l_inf_m` / `l_inf_burnt_m` | 200 / 60 | canal reach on intact / burnt peat |
| `water_min_months` | 10 | months of water a year for a pixel to count as a dry-season source |
| `exposure_m` | 2000 | distance from settlements counted as exposed |
| `tma_threshold_m` | 0.4 | regulatory limit |
| `tma_max_gap_days` | 10 | longer gaps between logger readings are not used for recession |
| `runoff_coefficient` | 0.12 | C in the water balance (0.07–0.18 measured) |
| `interception_by_class` | forest/mangrove 16.4%, shrub 8%, wetland 5%, grass/crop 3% | rain caught by vegetation |
| `ipg_dA_m` | 0.4 | design water-table limit for block spacing |
| `ipg_category` | A | A = ideal spacing; B = twice as far |
| `ipg_js_min_m` / `max` | 50 / 2000 | spacing limits |
| `years.baseline` / `validation` / `elnino` | 2016–2022 / 2023 / 2015, 2019, 2023 | see Validation |
| `dry_months` / `ndmi_months` | Jun–Oct / Aug–Oct | season definitions |
| `alpha_urgency` | 0.6 | urgency share of risk |
| `top_fraction` | 0.2 | "top" for capture and sensitivity |
| `validation_burn_threshold` | 0.05 | a unit "burned" if ≥ 5% of it burned |
| `level1_top_n` | 10 | KHG passed from level 1 to level 2 |

## Outputs

| File | Content |
|---|---|
| `unit_prioritas.gpkg` / `.csv` | every unit: raw indicators, normalised `n_*`, scores, risk, class, rank, sensitivity, IPG, attributes |
| `khg_terpilih.gpkg` | level 1 only: KHG to run at level 2 |
| `kebutuhan_sekat.csv` | level 2: blocks needed, existing and additional per KHG and class |
| `ringkasan_kelas.csv` | units and km² per class per KHG |
| `peta_prioritas_<khg>.png` | urgency, impact, feasibility and class maps |
| `korelasi_indikator.csv` | Spearman matrix |
| `laporan.json` | weights, AHP consistency, thresholds, class counts, correlated pairs, sensitivity, validation, coverage, delineation details, config |
