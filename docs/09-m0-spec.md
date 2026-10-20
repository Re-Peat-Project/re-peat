# 09 M0 specification: package, registry, synthetic testbed, test harness

> **Status after the split (2026-10-20).** The M0 package, registry and synthetic testbed exist as `repeat_neraca` (first named `watershare`) inside `repeat-neraca`, with tests. This page is the original scope and keeps the original names.

Status 2026-10-12. This is the agreed scope of milestone M0 in [08](08-build-plan.md). It needs no real data. Decisions taken: package in this repository; testbed about 10 × 10 km with truth at 20 m; port the FiPy solver from `LukeEcomod/blopti` (MIT); Python 3.11 or newer, tested on 3.14; provisional error-field parameters from the cached ICESat-2 residuals.

## 1. Package layout

```
re-peat/
  pyproject.toml
  config/parameters.yaml        # the registry (single source of numbers)
  src/watershare/
    params.py                   # load, validate, override, snapshot, sample
    # later in M0:
    testbed/                    # synthetic KHG generator, truth solver, error fields
    checks.py                   # input validation
  scripts/                      # table generators, e.g. registry -> markdown
  tests/
  docs/
```

The module names from the methodology (`network`, `compartments`, `hydrology`, ...) are added in the milestone that needs them, not as empty stubs. The two existing repositories stay separate and connect through files (the terrain contract in 08).

## 2. Parameter registry

- One `config/parameters.yaml`. Each entry has `default`, `range` (plausible), optional `outer_range` (used only as the outer Monte Carlo bound), `unit`, `scope`, `sampling` (`fixed`, `uniform` or `log-uniform`), `source`, `confidence` and an optional `note`.
- Convention: water table depth is negative below the surface, so thresholds are negative (target −0.4 m, hazard bounds −0.4 / −0.6 / −0.85).
- Validation (pydantic): the default lies within the range; the range lies within the outer range; log-uniform needs a positive range; the scope is from a fixed list.
- Overrides are range-checked. `snapshot()` returns the effective values and a SHA-256 hash, saved with every run so a run reproduces exactly.
- Doc tables are generated from the registry (`scripts/registry_table.py`), so the numbers cannot drift from the code.
- Seed values follow the proposals in 08 section 4: L_inf intact 200 m (20–1000) and burnt 60 m (20–120); K by condition (30 forest, 5 drained or burnt; wide range only as `outer_range`); ET₀ 4.17 mm/day.

## 3. Synthetic testbed

A generator that, from a seed, writes a complete synthetic KHG in the input-file format of the methodology.

**Contents:** a parametric peat dome (a few metres of relief over about 10 km); a canal grid with primary outlets to a bounding river and secondary canals about 500–1000 m apart; existing blocks and gates with condition values; peat depth following the dome; land cover patches including burnt areas; loggers; a rainfall and ET series; a pump inventory.

**Truth solver:** a 2D Boussinesq groundwater model (finite volume), run at 20 m with depth-dependent specific yield and transmissivity. It is independent of Tier 1 so the lumped model is not tested against itself. It is written in SI units with its own sparse solver (`testbed/groundwater.py`), not a FiPy port, because the original hydrology turned out to be unit-inconsistent (see 08 section 3.1); a FiPy cross-check on a small case is still to do. Acceptance, revised after the benchmark work: (1) analytic checks pass (steady-state parabola, mass conservation, symmetry); (2) the Siak canal water level rule reproduces the stored canal rise (100.2 m and 206.6 m for the stored 5 and 10 block sets); (3) on the Siak data the stored optimised sets beat rule-based and random siting by the paper's ratios (shown with transmissivity 100 times the original table; see below). The paper's absolute dry-volume percentages are not reproducible from the repository.

**DTM error fields:** a seeded spatially correlated field added to the true surface, so a run can use the truth, a LiDAR-like surface, or a DEMNAS-like surface. Parameters come from section 4. The generator writes the perturbed surface as `dtm.tif` and the error model as the terrain contract's error file.

**Output files:** `khg_boundary.gpkg`, `dtm.tif`, `peat_depth.tif`, `canals.gpkg`, `structures.gpkg`, `tma_loggers.csv`, `rainfall/`, `et/`, `landcover.tif`, `pumps.csv`, plus a `truth/` folder (true surface, true water table series, true optimal block sites) that the model never reads.

## 4. Provisional DTM error presets

Measured with `demnas-corrections/script/relative_error.py` on the smoothed DTM against ICESat-2 (and GEDI) points. The values are the RMS of the height-difference error between points a given distance apart, after removing the site median. They mix DEM error with ground-height error, so they are upper bounds, and the shortest lag bounds the point noise.

| Preset | Basis | 0–150 m | 300–600 m | 1–2 km | 4–8 km |
|---|---|---|---|---|---|
| LiDAR-like | assumed target | 0.1 | 0.15 | 0.2 | 0.25 |
| DEMNAS-low | Sebangau window | 0.37 | 0.74 | 1.16 | 1.73 |
| DEMNAS-mid | Mendahara | 0.58 | 1.19 | 1.88 | 2.94 |
| DEMNAS-high | Bengkalis | 1.01 | 1.64 | 2.55 | 3.40 |

The error does not reach a plateau by 8 km, so each preset is built as a short-range component (correlation length a few hundred metres) plus a long-range or trend component, fitted to these values. The LiDAR-like row is an assumption, not a measurement, and is to be replaced by the airborne LiDAR comparison.

## 5. Test harness

pytest, with these first tests:

1. Registry: defaults within ranges, overrides range-checked, snapshot hash stable and changed by an override.
2. Testbed: the same seed gives byte-identical files; a changed seed gives a different KHG.
3. Truth solver: mass balance closes, a solution with no canals relaxes toward the evapotranspiration deficit, symmetric setups stay symmetric, and the 0 / 5 / 10 block Siak benchmark is within tolerance.
4. Error fields: sampled relative error at the preset lags matches the table within sampling noise; zero variance returns the true surface exactly.
5. Input check: the generated files pass `checks.py` (CRS, required fields, ranges, datum note).

The sanity tests listed in the methodology (water balance closure, constant-S_y deficit, submerged weir, horizon-1 LP, and so on) belong to M2 and M3, when Tier 1 and the allocation exist.

## 6. Acceptance for M0

- `python -m watershare.testbed --seed 1 --preset demnas-mid --out data/synthetic/s1` writes a complete KHG and a `truth/` folder.
- The harness passes on the truth solver, including the Urzainki 0 / 5 / 10 block benchmark.
- The registry loads, validates, snapshots, and generates its doc tables.

## 7. Risks and limits

- The truth solver shares structural assumptions (Boussinesq with a canal boundary) with Tier 1. The testbed checks logic and terrain sensitivity, not whether the model structure matches real peat; the pilot KHG does that.
- The feature list is frozen at what the harness and the siting benchmark need.
- The error presets are provisional until the airborne LiDAR is compared.

## 8. Order of work

1. `pyproject.toml`, registry and its tests. Done (8 tests).
2. Truth solver and benchmark. Done as above: `testbed/groundwater.py` (5 tests), `testbed/reference_urzainki2020.py`, `scripts/benchmark_urzainki2020.py` and `tests/test_urzainki_benchmark.py` (skipped unless `WATERSHARE_SIAK_DATA` points at the Siak rasters). Remaining: the FiPy cross-check.
3. Dome, canal, structure and land-cover generators. Done: `testbed/khg.py` (`KHGConfig`, `generate`, `SyntheticKHG`), `canals.py` (canal cells and the block rule), `fields.py` (smooth random fields), `forcing.py` (Markov dry-season rainfall for normal, moderate and strong El Niño years, plus ET); 11 tests in `tests/test_khg.py`, including a truth-solver run on the generated KHG. Default KHG: 10 × 10 km grid at 20 m with a rounded domain of about 70 km², a parabolic dome 4 m above the river edge (gradient up to about 1.8 m/km), peat 0.3 to 4.8 m with about 35% lindung, 4 primary canals to the river and about 60 dead-end secondaries 600 m apart (one connected network, about 7,600 canal cells), 14 existing blocks and 4 gates with condition and year built, eight land-cover classes with burn counts, 3 villages with a road, 12 loggers across three distance-to-canal classes, 3 river intakes and a 3-model pump inventory. Truth canal levels use the Urzainki rule on the true surface (a world definition; Tier 1 has its own canal model). Not yet generated: peat type variation, the pre-computed logger series (these come from the truth run in step 5).
4. Error-field generator and presets.
5. Output writers and `checks.py`; the acceptance command.
