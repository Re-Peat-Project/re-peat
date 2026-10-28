# 08 Build plan: the decision model while the terrain question is open

> **Status after the split (2026-10-20).** The neraca air part of this plan was built as `repeat-neraca` (the physical model and the KHG deficit). The water-sharing hydrology model (Tier 1 interventions) is not coded. The package `watershare` became `repeat_neraca` inside `repeat-neraca`.

Status 2026-10-12. This page restructures the build so that the water-sharing decision model (Tier 1, interventions, allocation, strategy, scenarios) can be developed now, without waiting for the DEM investigation. It is a plan and a set of proposed decisions, not method. Where it changes something in the [methodology](Peatland%20Rewetting%20Water-Sharing%20Model%20—%20Methodology.md), the proposal is marked and the methodology is unchanged until you confirm.

## 1. Verdict from the design review

The decision logic is sound: deficit, priority weight, cheapest intervention, with residual areas sent to fire readiness. So are the two-tier fidelity, the parameter registry, the S0–S5 packages and the rule against circular validation.

The weak point is terrain. Published DEMNAS accuracy is RMSE 2.2 to 5.0 m and our smoothed DTMs reach 1.2 to 2.8 m ([07](07-demnas-literature.md)), while the model reasons about 0.3 m head drops over 0.5 to 1 km. A first relative-error check on the cached ICESat-2/GEDI points (2026-10-12, provisional) gives 1.1–2.6 m RMS for the height difference between points 1–2 km apart on the smoothed DTM, at the three sites, so 0.3 m steps cannot be resolved from DEMNAS. The plan below keeps the model buildable and testable in spite of that, and makes the terrain requirement something the model can state, not assume.

## 2. Decouple the model from the DEM

### 2.1 Which parts depend on terrain accuracy

| Model part | Needs | Likely status with DEMNAS-only terrain |
|---|---|---|
| Dome shape, regional slope, sub-KHG delineation | km-scale relative height | Probably fine if the error is smooth |
| Compartment delineation per reach | 100 m to km relative height | Uncertain; test |
| Block candidates at Δh_max = 0.3 m | 0.3 m over 0.5–1 km | Not supportable from the DTM alone |
| Canal flow direction, gravity-transfer direction | sign of a head difference | Only where the slope clearly exceeds the error |
| Pump lift | head across a block | Needs surveyed levels |
| ζ = h − surface (water table depth) | absolute surface | Avoidable, see 2.2 |

### 2.2 Proposed design rules (changes to the methodology)

1. **State the water table relative to the local surface and anchor it with data.** Loggers measure depth below ground, so Tier 1 should treat each compartment's surface elevation z_s,i as a **parameter with a prior from the DTM and an uncertainty**, pulled toward truth by loggers and surveyed canal-bank heights. Absolute DTM error then matters only for head differences between compartments and canals.
2. **Head-source hierarchy.** Canal water levels, block crests, gate settings and logger tops come from survey (GNSS or levelling) where they exist; the DTM is used only where nothing better exists, and each such use is flagged. Pump lift and gravity transfers use surveyed levels first.
3. **Direction confidence as a shared definition.** Use the rule from [04](04-rewetting-design.md): confidence = |dz| ÷ (√2 × DTM error), at least 2 clear, 1–2 probable, below 1 ambiguous. Gravity transfers are allowed only on clear or probable reaches; ambiguous reaches fall back to the outlet-direction rule already in the methodology.
4. **Siting is anchor-first when terrain is poor.** Anchors (outlets, junctions, burnt-area edges, protected-peat boundaries, side branches) need no elevation. Elevation-based candidates at Δh_max are generated only where the relative-error test passes; elsewhere the output is a stretch flagged "survey needed", not a point.
5. **Every KHG carries a terrain quality class** (LiDAR / calibrated DEMNAS / uncalibrated), and the dashboard shows it next to every recommendation.

### 2.3 The terrain contract

The model reads terrain only through this interface, so any DEM work can be swapped in later. It is the same list as in the `repeat-dem` repository's `AGENTS.md`.

| Input | Content |
|---|---|
| `dtm.tif` | ground elevation, one stated vertical datum and epoch |
| Error model | per-class bias and RMSE, relative error, slope error, residual correlation length and sill |
| Source raster | which source (LiDAR, DEMNAS sheet, other) each cell came from |
| Quality flag raster | per cell, as in 2.2 rule 5 |
| Survey table | surveyed heads that override the DTM (canal levels, crests, logger tops) |

## 3. Develop against a synthetic KHG first

A synthetic testbed lets the whole decision chain be built and tested now, and it answers the question the DEM workstream cannot: **how much terrain error can the decisions tolerate?**

**Testbed.** Generate a synthetic peat dome with a canal grid, existing blocks, loggers, known peat depth and land cover. Produce a "truth" water table with a separate, finer 2D groundwater solver (finite differences or FiPy), not with Tier 1 itself, to avoid testing the model against itself. Add DTM error fields with the correlation length, sill and bias measured at the three real sites.

**Experiments it supports**
1. Build and unit-test the sanity tests listed in the methodology (water balance closure, no-block monotonicity, submerged weir, horizon-1 LP, constant S_y, zero-error Monte Carlo) with known answers.
2. Compare recommended block sites and gate or pump assignments under the error-perturbed DTM with those under the true surface. Report the share of recommendations that survive, as a function of relative error. This produces a **terrain accuracy specification** (for example, "block siting is stable when relative error over 1 km is below X m") that goes back to the DEM workstream as the target for the LiDAR comparison.
3. Test the logger-anchored surface parameters (2.2 rule 1) against plain DTM use.

### 3.1 Reference implementation: Urzainki et al. 2020 (`LukeEcomod/blopti`)

[Urzainki et al. (2020)](https://bg.copernicus.org/articles/17/4769/2020/bg-17-4769-2020.pdf) is the closest published siting method: a 2D Boussinesq groundwater model (FiPy, 100 m raster) coupled to a genetic algorithm and simulated annealing, applied to 931 km² of drained peat in Siak, Riau. The code is MIT-licensed and includes its Siak rasters.

**What it gives us**
- A working independent 2D solver, usable as the truth generator in section 3 (decided: adapt `hydro.py`).
- A benchmark to reproduce: optimised siting beat random siting (10 optimised blocks matched about 60 random ones; about 7× the improvement at 5 blocks), and the rule-based comparator (blocks at contour × canal intersections) performed like random. If that holds on the testbed, the equal-head rule in [04](04-rewetting-design.md) needs revisiting.
- A cheap screening objective: maximising total canal-level rise performed about as well as the full PDE (the two correlate), which suggests screen first, then refine with Tier 1.
- A marginal-benefit curve per block count, matching the ranked list the dashboard needs.

**What it does not give us**
- It covers siting only: no gates, pumps, flows or allocation.
- Its objective is the mean water table over 3 dry days from a saturated start. It does not weight risk, use the 0.4 m threshold or run a season.
- Canal level is DEM − 1.2 m everywhere, and a block raises upstream pixels found by comparing neighbouring DEM cells. The authors note this makes canal levels non-monotonic and that 100 m pixels join canals less than 100 m apart. This is the terrain problem in its sharpest form, so the canal-level step is replaced, not adopted.
- Absolute effect is small (whole-area annual mean water table −21.45 → −20.08 cm with 80 blocks), and the paper states there is no field validation.
- It never compared the search against greedy selection, which is what the methodology uses.

**Smoke test (2026-10-12, throwaway venv, Python 3.14.7, FiPy 4.0.3, NumPy 2.5)**
- The dependencies install, and the hydrology core runs: 3 simulated days on the Siak grid took about 40 s including loading, with no plotting.
- It does **not** run as shipped, and the repository is dormant (last commit September 2020). Needed fixes: (1) a NumPy 2 error in `preprocess_data.py` (assigning −1 to a `uint8` array); (2) `read.py` has the author's absolute Windows path to the rainfall file; (3) `main.py` unpacks four return values from `hydrology()`, which now returns one (the last commit left them out of sync).
- Things that look wrong in the code and need checking before any reuse: `hydro.py` updates the storage term `C` each day with `tra_to_cut` (transmissivity) where `sto_to_cut` appears intended; the rainfall source term uses two different unit factors in its two branches (`0.001` vs `10.`); tracked pixels and the normalisation constant are hard-coded to the Siak grid; `preprocess_data.py` uses `np.where(a) and np.where(b)`, which applies only the second condition.
- I did not compare its output with the paper's figures at the smoke-test stage. The benchmark work that followed is below.

**Benchmark result (2026-10-12).** Using the stored block sets in the repository and a new SI-unit solver (`repeat_neraca/testbed/groundwater.py` in `repeat-neraca`, moved to `repeat_neraca/groundwater/` on 2026-10-28 and shared with repeat-pump, then `watershare/testbed/groundwater.py`):
- **The shipped hydrology cannot reproduce its own stored results.** Run as shipped, it gives a mean water table of −76 m after 3 days, because the source term is scaled for a 100 m pixel treated as one length unit while the storage term is not. The stored outputs (for example 8,255 ha·m dry peat volume without blocks) come from an older version I do not have.
- **The canal water level rule reproduces exactly.** The stored canal rises of 100.2 m (5 blocks) and 206.6 m (10 blocks) are recovered, with 11,311 canal pixels.
- **Block effect depends strongly on transmissivity.** With the peat tables in the repository (boreal Päivänen retention and conductivity, T about 0.7 m²/day at saturation), three dry days change the water table only within metres of a canal, and blocks make almost no difference (below 0.01%). With transmissivity ×100 (a realistic tropical regime: our registry has K around 30 m/day in the top layer), the stored optimised sets improve the dry peat volume by 0.14% (5 blocks) and 0.27% (10 blocks), against 0.018% and 0.041% for random sets of the same size and 0.048% for the rule-based set. That is about 8× and 7× the random improvement, close to the paper's "7× at 5 blocks", and the rule-based set is no better than random, as the paper reports.
- **What this means.** The ranking result survives; the absolute improvements are unreliable and depend on the conductivity values, which the paper's tables took from boreal peat. Whole-area water table gains from siting are small in any case (paper: 1.4 cm with 80 blocks).
- **Solver choice.** I wrote an SI-unit sparse finite-volume solver instead of porting the FiPy code, because the original scaling was inconsistent. A FiPy cross-check on a small case is still to do.

**Decision (revised after the benchmark):** treat it as a reference, not a dependency. Its peat tables and canal-level rule are reused for the benchmark (MIT notice kept in `testbed/data/NOTICE-urzainki2020.md`; cite the paper), but the solver is new. The acceptance test is the canal-rise match and the improvement ratios over random and rule-based siting, not the paper's absolute percentages.

## 4. Decisions needed to make the pieces consistent

Proposed resolutions; none is applied yet.

| # | Issue | Proposal |
|---|---|---|
| 1 | **Two spatial units.** Prioritisation uses sub-KHG (≥ 5 km²); hydrology uses reach compartments. | One hierarchy: KHG → sub-KHG → compartment → distance bands. A single module (`compartments`) owns delineation; sub-KHG is the parent and compartments nest inside it. |
| 2 | **Two risk frameworks.** `prioritas_khg` uses 0.6·urgency + 0.4·impact and tertile classes; the methodology uses hazard × susceptibility. | `prioritas_khg` supplies static susceptibility, impact and the weight components (re-evaluated at compartment scale with the same indicator code); Tier 1 supplies daily hazard; the 4 × 3 lookup combines them. Prioritisation keeps its own feasibility axis for choosing where to work. |
| 3 | **Hotspots.** The methodology says hotspots never enter risk; `u_hotspot` is an urgency indicator in `prioritas_khg`. | Keep hotspots out of the twin's susceptibility and use them only for validation. In `prioritas_khg` they stay legitimate as a baseline-year indicator, but state the difference. |
| 4 | **Three block-spacing rules** (IPG js = dA ÷ slope, the 04 pool rule, the methodology's Δh_max). | IPG gives level-2 budget counts; the pool rule is the siting rule on the water surface; Δh_max is its parameter. The 0.3 m contour method in 04 is the same rule as a map. |
| 5 | **Parameter drift.** Burnt-peat L_inf is 20 m in the methodology and 60 m in doc 05 and the code; K is 50 (5–1300) in the methodology and 30 / 5 in doc 05; ET is 4.17 vs 4.1. | One `parameters.yaml` is the source and the doc tables are generated from it. Suggested values: L_inf burnt 60 (range 20–120; 20 m is the low end, one site); K by condition (forest 30, drained or burnt 5), with the wide range used only as the outer bound for Monte Carlo; ET 4.17 to match Urzainki et al. |
| 6 | **Breach vs fill.** The methodology says breach, not fill; `delineate.py` runs `fill_pits → fill_depressions → resolve_flats`. | Change delineation to breaching (WhiteboxTools `BreachDepressionsLeastCost`, or pysheds options), and compare unit counts before and after. |
| 7 | **Stale status** in docs and two copies of `demnas_dtm.py`. | Docs README updated. Merge the copies in one package. |

## 5. Package and module map

One package (working name `watershare`, as in the methodology's layout) replaces the two repositories' scripts; terrain stays a separate input stage that writes the terrain contract.

| Stage | Today | Next |
|---|---|---|
| Terrain (`demnas_dtm`) | coded, 3 real sites, accuracy-limited | LiDAR benchmark done (`reports/dem_benchmark/report.md`); the chain runs once per DEM; see `repeat-dem/AGENTS.md` |
| Prioritisation level 1 and 2, delineation | coded, synthetic tests only | breach instead of fill; re-use indicators at compartment scale |
| **Canal network and structures** | **missing; keystone** | clean topology, directed graph with direction confidence, structure inventory with decay, water-source nodes |
| Compartments and block candidates | spec / QGIS steps | code on the synthetic testbed, then a real canal layer |
| Forcing prep, logger QC and re-referencing | spec | code on real CHIRPS/ERA5 and SiPALAGA CSVs |
| Tier 1 hydrology and interventions | spec | code and sanity-test on the testbed |
| Allocation LP and rolling horizon | spec | code; transfers must map to achievable gate and pump settings, with relay travel time (about 6–7 days for 11 km) as a delay |
| Strategy tree, scenarios S0–S5 | spec | after allocation |
| Calibration, Monte Carlo | spec | after Tier 1 on a real KHG |
| Dashboard | spec | last |

**Reuse before writing.** Port the 2D solver from Urzainki et al.'s `LukeEcomod/blopti` (MIT) for the testbed truth and Tier 2, with the fixes in section 3.1. Use FiPy as the numerical library, and do not adopt its canal-level routine.

## 6. Revised milestones

| # | Milestone | Needs real data? |
|---|---|---|
| M0 | Package skeleton, `parameters.yaml`, synthetic testbed, test harness | no |
| M1 | Canal network and structures module; compartments; block candidates | synthetic first, then one real canal layer |
| M2 | Tier 1 hydrology with logger-anchored surface; all sanity tests pass | no |
| M3 | Interventions and allocation LP; terrain-error decision experiment (section 3); siting comparison: greedy vs GA vs cheap screen plus Tier 1, with the Urzainki 2020 random/rule-based benchmark (section 3.1) | no |
| M4 | Strategy tree and S0–S5 on the testbed; terrain accuracy specification written | no |
| M5 | Pilot KHG: LiDAR terrain, canals, loggers; calibration; Tier 2 check | yes, LiDAR plus loggers |
| M6 | Dashboard; second KHG to test transfer | yes |

M0 to M4 do not depend on the DEM investigation.

## 7. Learned components, staged

Machine learning stays deferred (methodology A4) until two or more KHGs have labels. When it comes in, use it for the inputs, not for the decision: canal and structure extraction (fine-tune an Earth-observation foundation model such as OlmoEarth on the complete-canal KHG), terrain residual correction trained on LiDAR from several DEMNAS sheets, and regionalising C_i, L_inf, S_y and the ET factor from covariates. Validate leave-one-KHG-out and compare against registry defaults; drop any component that does not beat them. A learned terrain correction cannot add ground information that no sensor sees under canopy, so it is a late step after the LiDAR comparison.

## 8. Open items that remain yours

- Which KHG has LiDAR, complete canals and loggers (the pilot question in the methodology)?
- Is LiDAR available from more than one DEMNAS sheet?
- Pump inventories and logger data holders (methodology open questions).
- Confirm or change the proposals in section 4 and the design rules in 2.2.
