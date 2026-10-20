# 06 Pitfalls, checks and FAQ

## Known pitfalls

### Water-table decline is not water loss

When the water table falls 20 mm, only the *drainable* part of that peat layer has emptied, the specific yield (about 0.1–0.3), so about 2–6 mm of water left, not 20 mm. Treating decline as water volume (Sy = 1) overstates drying three- to tenfold. Our 2021 study made this mistake when it estimated that the KHG's water would "run out in 108 days". Use decline rates as **checks on modelled water-table behaviour**, never as fluxes. A useful by-product: with ET ≈ 3.5 mm/day and declines of 16–23 mm/day, the implied Sy is about 0.15–0.25, close to our default.

### Total water content is not available water

The 0.7–0.8 "water content of peat volume" describes how much water the peat holds, not how much can be released. Most of it never drains. `i_water_stock` is reported for context, not used as a supply of water for rewetting.

### Raw DEMNAS pixels are not ground heights

DEMNAS can sit metres above the ground in forest and, in some areas we tested, metres below lidar ground in open land; the offset varies by site and probably by source sheet ([07](07-demnas-literature.md)). Never place blocks or compute slopes from raw DEMNAS. Use `dtm_smooth.tif`, and report block positions as stretches with confidence.

### Datum mismatches look like vegetation

ICESat-2 and GEDI heights are ellipsoidal; DEMNAS is orthometric. A forgotten geoid conversion shows up as a constant offset of tens of metres, which the fit would wrongly absorb. The tool warns when the median DEM − ground difference exceeds 20 m.

### Circular validation

If fire history from 2023 is used to build the score and then to validate it, the score "predicts" fires it already contains. Indicators must use baseline years only (`years.baseline`), and validation the later years (`years.validation`).

### Random splits overstate accuracy

Neighbouring ICESat-2 segments and neighbouring hexagons are nearly identical. Split by spatial blocks (done in `demnas_dtm`), and treat level-2 validation on very small units with care.

### Double counting

Water deficit, dry spells and NDMI often move together. Check `korelasi_indikator.csv`; pairs above 0.8 effectively double a weight.

### Coarse climate data look precise

TerraClimate (~4 km) and CHIRPS (~5 km) give every sub-KHG in a zone nearly the same value. They separate KHGs and large zones; contrast between neighbouring units comes from NDMI, fire history, canals and peat depth.

### Single-date imagery

One scene per year from different seasons mixes seasonality with trend, and rain on the acquisition day changes NDMI. Always use seasonal composites.

### Pumps without blocks

Water pumped into a canal with no holding block downstream drains away within days. Every pump site needs a block below its discharge.

## Before trusting a run: checklist

**`demnas_dtm`**
- [ ] Vertical datum of DEMNAS checked and `ground.datum.target` matches.
- [ ] `calibration.json`: fitted k between 0 and 1, highest for tree cover, with enough points per class.
- [ ] `validation.csv`: error falls from raw DEM → prior k → calibrated → smoothed.
- [ ] `dtm_residual.tif`: no canal lines or forest edges visible (else adjust masks or smoothing).

**`prioritas_khg`**
- [ ] `laporan.json → indicator_coverage`: which indicators actually had data.
- [ ] `korelasi_indikator.csv`: no unexpected pairs above 0.8.
- [ ] Sub-KHG map (`cache/<khg>/subkhg.gpkg`) checked against canals, rivers and local knowledge; ideally against the 16 Kahayan–Sebangau sub-KHG.
- [ ] Validation: urgency AUC above 0.5 and clearly above fire history alone; capture of top 20% well above 20%.
- [ ] Sensitivity: share of units with a stable class reported; unstable priority units flagged.
- [ ] Class map discussed with someone who knows the area before it goes to KLH.

## Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| "no ground points available" | SlideRule unreachable, no coverage, strict filters | check network; widen `t0`/`t1`; add `gedi_l2a`; use local points |
| "pyproj could not apply the geoid model" | PROJ grid not downloadable | `datum.mode: raster` with a geoid GeoTIFF, or `constant` for tests |
| A cloud layer "unavailable" in the log | service moved or unreachable | check the URL template in config; use the layer's `local` option; or drop a prepared GeoTIFF into the cache |
| Only 1–3 sub-KHG | mapped channels don't enclose areas and DEM streams failed | check the log for "DEM stream network failed"; set `use_dem_streams: true`, lower `stream_threshold_km2`, or set `outlet_order` |
| Too many tiny sub-KHG | streams of low order used as outlets | raise `min_area_km2`, narrow `target_count`, or set a higher `outlet_order` |
| Indicator "reported but not scored" | data for too few units (often TMA loggers) | expected; it is still in the CSV |
| Every unit in "Siaga pemadaman" | feasibility near zero everywhere (no canals or water layer loaded) | check `vectors.canals`, `rivers`, `rasters.dtm` |
| Level 1 classes look arbitrary | very few KHG in the run | level 1 is meant for many KHG; with a handful, normalisation exaggerates small differences |
| `np.in1d` error from pysheds | NumPy 2 | patched automatically in `delineate.py`; update pysheds if it persists |

## Deferred components

**Machine learning.** Not used for now. Choosing a strategy (gate, block, pump) has no training labels, and models trained on one KHG's burn history may not transfer to others. Reconsider for susceptibility weights or water-table mapping once two or more KHGs have enough labelled data and ML clearly beats expert weights on held-out years.

**PFVI and the `peatfr` package.** PFVI (Taufik et al. 2022) is the best-grounded peat-specific fire index, validated at 8 stations over two years. The `peatfr` R package re-calibrates it per dataset; in its own demonstration the fitted van Genuchten n came out around 55 and changed to 18 with a 10% input perturbation, physically implausible and unstable. Deferred until PFVI with fixed published parameters is shown to predict hotspot timing better than simple water-table depth classes. The modified KBDI from the 2021 study is a simpler candidate.

## FAQ

**Why two levels instead of one big run?** Detailed data (good DTMs, canal and block inventories, loggers) exist unevenly. Ranking KHGs with them would favour well-mapped KHGs. Level 1 uses only comparable national data; level 2 uses everything, where it exists.

**Why sub-KHG and not hexagons?** Sub-KHG follow how water actually drains and how the team and KLH already think about a KHG; interventions on one outlet channel affect one sub-KHG. Hexagons are kept for finer ranking or when the DTM is too poor to delineate.

**Why is impact not validated?** Impact (peat depth, protected status, people nearby) is about what is at stake, not where fire happens. It should be agreed with KLH, not "predicted".

**Why 0.4 m everywhere?** It is the regulatory limit and matches where fire danger rises in field data. Hazard bands at 0.6 and 0.85 m add gradation.

**Can I change a weight without refetching data?** Yes: run with `--skip-fetch`; the cache is reused and only scoring reruns.

**How do I add a new indicator?** Compute it per unit in `indicators.py` (add a column with an `u_`, `i_` or `f_` prefix) and register it in `INDICATOR_DEFAULTS` in `scoring.py` with group, weight, direction and label. It is then normalised, scored, checked for correlation and included in sensitivity automatically.

**Where does the 27 cm in 14 days come from?** From the 2021 study: 14 days × 19.2 mm/day mean dry-day decline at three SiPALAGA stations. It is a decline check, not a water volume (see the first pitfall).
