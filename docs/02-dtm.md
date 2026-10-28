# 02 DEMNAS to DTM (`demnas_dtm`)

> **Status after the split (2026-10-20).** Written for the single-folder layout. `demnas_dtm` now lives in the `repeat-dem` repository; read this page for the method, and that repository's README for commands. Its `--peat-depth` option (mineral surface elevation, peat volume) was merged there from the prioritisation repository.

## Why this step exists

Rewetting design depends on height differences of tens of centimetres: the 0.4 m water-table limit, a 0.3 m head drop between canal blocks, the slope that sets block spacing. DEMNAS, Indonesia's national 8 m elevation model, is a radar DSM (IFSAR, TerraSAR-X, ALOS PALSAR) blended toward stereo-plotted mass points. How much canopy it still contains is unknown and varies by sheet; in forest it records something between the canopy and the ground, and at our test sites it sometimes sat below lidar ground. The error is metres, far larger than the signal. Published accuracy is RMSE 2.2–5.0 m at open-ground control points, and our smoothed results were 1.2–2.8 m ([07](07-demnas-literature.md)). This tool estimates and calibrates the correction against satellite ground heights, and smooths the result to the dome scale where it is trustworthy. It cannot reach decimetre accuracy.

**What the output is good for:** dome shape, regional slope, flow direction, sub-KHG delineation, equal-head block candidates, pumping lift.
**What it is not good for:** local detail at the scale of single canal banks or micro-topography. Do not read individual pixels.

## Pipeline

```
1. Mosaic DEMNAS tiles, clip to the KHG (+ buffer), reproject to UTM
2. Fetch land cover and canopy height (cloud) or read local rasters
3. Ground points: ICESat-2 ATL08 (+ GEDI) via SlideRule, or your own points
4. Convert ground points to the DEM datum (geoid) and optionally to the DEM year (subsidence)
5. Fit the correction per land-cover class:  DEM − ground = bias + k[class] × canopy height
6. Apply:  DTM = DEM − k[class] × canopy height − bias
7. Mask water, built-up, canal buffers; remove spikes
8. Smooth (median, gaussian, polynomial trend; configurable chain); fill gaps
9. Validate on held-out ground points; write rasters and reports
```

### The correction model, in plain words

Radar and stereo sensors don't see the ground under dense canopy; they see a surface somewhere inside the canopy. If a forest is 25 m tall and the DEM sits 20 m above the ground there, the sensor "saw" 80% of the canopy height: **k = 0.8**. Shrub might give k = 0.5. Open land gives k = 0. There may also be a constant offset (**bias**) from datum differences or from the DEM being older than the ground points (peat has subsided since). The tool fits both from ground truth instead of guessing.

### Why ICESat-2

ICESat-2 is a laser altimeter. Its ATL08 product classifies photons into ground and canopy along 100 m segments, so it gives true ground heights even under forest, where enough photons get through. GEDI does the same with full waveforms and has denser coverage in the tropics. Both heights are *ellipsoidal* and must be converted to the DEM's datum before comparison.

### Why spatial blocks for validation

Neighbouring ICESat-2 segments along one track are nearly identical. If you split points at random, the validation set contains near-copies of calibration points, and accuracy looks better than it is. The tool assigns whole 2 km blocks to either calibration or validation.

## Running it

```bash
pip install -r requirements.txt
python demnas_dtm.py --dem "demnas/*.tif" --aoi khg_01.gpkg --out out_khg01          # everything
python demnas_dtm.py --print-default-config > my_config.yaml                          # see every option
python demnas_dtm.py --config my_config.yaml
python demnas_dtm.py --dem dem.tif --out out --no-download --landcover lc.tif --chm chm.tif \
       --ground-points rtk_points.csv --peat-depth peat.tif                           # offline, own data
python demnas_dtm.py --dem dem.tif --out out --ground none                             # no calibration
```

## Parameters explained

### General

| Key | Default | What it means | When to change |
|---|---|---|---|
| `dem` | — | DEMNAS tile paths or glob patterns | always set |
| `aoi` | none | KHG boundary; the run is clipped to it | set it; without it the whole mosaic is processed |
| `aoi_buffer_m` | 500 | extra margin so smoothing behaves at the edge | larger for strong smoothing windows |
| `target_crs` | auto-utm | UTM zone from the AOI centre | force a zone if KHGs straddle a boundary and must share a grid |
| `target_res_m` | 8 | output cell size (DEMNAS native ≈ 8 m) | 10–15 m for faster test runs |
| `dem_valid_range_m` | −50 … 4000 | values outside are treated as missing | rarely |
| `peat_depth` | none | peat thickness raster; adds mineral substrate elevation and peat volume | set if you have a peat depth map |

### Corrections (land cover and canopy height)

| Key | Default | What it means |
|---|---|---|
| `corrections.mode` | download | `download` = cloud COGs; `local` = your rasters; `none` = no vegetation correction |
| `worldcover_url` | ESA WorldCover 10 m v200 (2021) | template for land-cover tiles; edit if the provider moves files |
| `chm_url` | Meta/WRI global canopy height | template for canopy height tiles |
| `chm_quadkey_zoom` | 9 | tiling scheme of the canopy height product; do not change unless the product changes |
| `chm_min_m` | 2 | canopy lower than this is treated as 0 (noise, crops) |
| `chm_max_m` | 60 | canopy above this is clipped (implausible) |
| `chm_fallback_m` | tree 20 m, mangrove 12 m | used where no canopy tile is available |
| `k_by_class` | tree 0.8, mangrove 0.8, shrub 0.5, wetland 0.4, grass/crop 0.2, others 0 | prior share of canopy present in the DEM, by ESA WorldCover class; **replaced by fitted values when ground truthing works**. Not supported by data: fitted tree-cover k was 0.04–0.21 at three sites, and the prior made two of them worse than the raw DEM |
| `k_default` | 0.5 | for classes not listed |
| `bias_by_class`, `bias_default` | none, 0 | prior constant offsets |

### Masking and spike removal

| Key | Default | What it means |
|---|---|---|
| `mask.landcover_classes` | 80 (water), 50 (built-up) | excluded from smoothing so they don't distort the ground surface |
| `mask.vectors` | none | e.g. `[{path: canals.gpkg, buffer_m: 15}]`; canal cuts otherwise pull the surface down |
| `mask.despike` | true | remove isolated spikes (buildings, cloud artefacts) |
| `mask.despike_window_m` | 400 | size of the local reference used to detect spikes |
| `mask.despike_threshold_m` | 2.5 | cells further than this from the local median are removed |

### Smoothing

`smoothing.steps` is a list applied in order. Default: median 300 m, then gaussian 150 m.

| Method | Parameter | What it does | Use it for |
|---|---|---|---|
| `median` | `window_m` | robust large-window median (computed on a coarse grid, then interpolated back) | removing leftover canopy steps and outliers |
| `gaussian` | `sigma_m` | smooth blur that ignores masked cells | a clean continuous surface |
| `polynomial` | `degree`, `huber_m`, `sample` | robust trend surface (outliers down-weighted) | the overall dome form; degree 3–4 for one dome |

`fill_max_search_px` (200) limits how far gaps are filled by interpolation.

**Choosing smoothing strength.** Stronger smoothing hides noise but also flattens real features. Look at `dtm_residual.tif` (corrected minus smoothed): if residuals show canal lines or forest edges, the smoothing is too weak or masks are missing; if they show the dome shape itself, it is too strong.

### Ground truthing

| Key | Default | What it means |
|---|---|---|
| `ground.source` | sliderule | `sliderule` (ICESat-2/GEDI online), `local` (your CSV/vector), `none` |
| `ground.datasets` | icesat2_atl08 | add `gedi_l2a` for more points |
| `ground.t0`, `t1` | 2019 … 2025 | time window |
| `ground.cache` | true | reuse fetched points (`ground_points_raw.gpkg`) |
| `icesat2.len`, `res` | 100 m | segment length and step; ATL08 standard |
| `icesat2.night_only` | false | night passes have less solar noise but fewer points |
| `icesat2.min_ground_photons` | 10 | segments with fewer ground photons are dropped (dense canopy) |
| `gedi.min_sensitivity` | 0.95 | GEDI quality filter for dense tropical canopy |
| `datum.mode` | pyproj | how ellipsoidal heights become DEM heights: `pyproj` (EGM2008 via PROJ), `raster` (your geoid grid, e.g. INAGeoid2020), `constant`, `none` |
| `datum.target` | EPSG:4326+3855 | WGS84 + EGM2008 heights; **must match DEMNAS metadata** |
| `epoch.dem_year` + rates | off | shift ground heights back to the DEM year using subsidence rates per class |
| `exclude.edge_buffer_m` | 50 | drop points near land-cover changes (mixed footprints) |
| `exclude.max_abs_residual_m` | 30 | drop gross outliers |
| `split.validation_fraction` | 0.3 | share of spatial blocks held out |
| `split.block_size_m` | 2000 | block size for the split |
| `fit.min_points_per_class` | 30 | fewer vegetated points → keep the prior k |
| `fit.bias_from_chm_below_m` | 2 | points with lower canopy define the global bias |
| `fit.k_bounds` | 0–1 | fitted k is clipped to this range |
| `fit.huber_m` | 1.5 | robustness: residuals beyond this weigh less |
| `fail_on_error` | false | true = stop the run if ground truthing fails |

## Outputs

| File | What to do with it |
|---|---|
| `dtm_smooth.tif` | **the product**: input for `prioritas_khg`, QGIS block siting, flow direction |
| `dtm_corrected.tif` | corrected but unsmoothed; for inspection only |
| `dtm_residual.tif` | corrected minus smoothed; check for artefacts (see above) |
| `mineral_elevation.tif` | DTM minus peat thickness (if `peat_depth` given) |
| `correction_m.tif`, `k_factor.tif`, `canopy_height.tif`, `landcover.tif` | what was subtracted and why |
| `excluded_mask.tif` | cells kept out of smoothing |
| `ground_points.gpkg` | every ground point with datum-corrected height, exclusion reason, split and error per surface; open in QGIS to see where errors are |
| `calibration.json` | fitted k (with standard error and counts) and bias per class |
| `validation.csv` | bias, RMSE, MAE and NMAD on held-out points, per surface and class |
| `run_report.json` | full config snapshot, sources used, statistics |

### Reading `validation.csv`

Four surfaces are compared at the same held-out points: raw DEM, DTM with prior k, DTM with fitted k, smoothed DTM. You want the error to fall in that order. **NMAD** (a robust spread) is more reliable than RMSE when a few points are bad. Report bias and NMAD per class in the paper. If the smoothed DTM is *worse* than the calibrated one in some class, smoothing is removing real relief there.

## Things that go wrong

- **Median DEM − ground difference above 20 m** (logged as a warning): almost always a datum mismatch. Check `datum.target` against DEMNAS metadata.
- **No ground points**: SlideRule unreachable, no coverage, or too strict filters. The run continues with prior k and says so; set `fail_on_error: true` if you'd rather stop.
- **SlideRule field names change**: the error lists the columns received; export points yourself and use `--ground-points`.
- **Dates differ**: DEMNAS, WorldCover (2021) and canopy height come from different years. Clearing or regrowth since DEMNAS will be over- or under-corrected; calibration absorbs part of it.
- **Memory**: a 50 × 50 km KHG at 8 m is about 40 million cells (1–2 GB RAM). Use `--res 10` or 15 for tests.
