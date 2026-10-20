# Peatland Rewetting Water-Sharing Model — Methodology

Oct 3, 2026 · @Dany Laksono

## Purpose, scope and users

The model allocates scarce dry-season water inside a KHG — held by canal blocks, routed by water gates, and imported by pumps — so that the water table stays no deeper than 0.4 m below the peat surface where fire risk and burn history are highest. It runs as an interactive dashboard for KLH/BPLH and the new national peat agency (BPGMN).

Why allocation matters: KLH/BPLH already applies real-time groundwater monitoring and *water sharing* in the dry season, but only about 45,430 of an ideal 538,568 canal blocks exist across seven fire-prone provinces, covering 269,284 km of canals ([KLH/BPLH, 18 Jun 2026](https://kemenlh.go.id/news/detail/jaga-gambut-tetap-basah-menteri-lh-perkuat-sekat-kanal-dan-budaya-ekologis-di-pelalawan)). Every block and every pump must therefore go where it rewets the most at-risk peat.

Pumping is already field practice: river water is relayed by pumps through canals and held by blocks, e.g. an 11 km pump relay from the Batang Hari River in Jambi ([ANTARA, Sep 2026](https://www.antaranews.com/berita/5727171/wamen-lh-dukung-praktik-baik-kolaborasi-tangani-karhutla-di-jambi)) and a large intake pump plus five smaller relay pumps over a 9 km canal network from the Pawan River in Ketapang ([Suara Kalbar, Oct 2026](https://ketapang.suarakalbar.co.id/2026/10/pt-aer-terapkan-inovasi-perlindungan.html)).

Decision questions the model answers:

1. Where should the next N canal blocks go to rewet the most high-risk peat?
2. Which compartments can existing blocks and gates keep wet, and which need pumped water?
3. Where should pumps draw from and discharge to, at what capacity and hours, for a given fuel budget?
4. Which areas stay above the 0.4 m threshold even after all interventions, and so need fire-suppression readiness instead?

Scope: one KHG at a time, daily time step, dry-season focus. Out of scope: ignition behaviour (proxied only), fire spread, firefighting tactics, and carbon accounting.

## Design principles

The model is KHG-agnostic: every structure is derived from input layers, and every number is a registered, adjustable parameter.

- **Derived, not hard-coded.** Compartments, the canal graph, block candidates and water sources are built automatically from the KHG boundary, DEM, canal and infrastructure layers. Applying it to a new KHG means loading new layers, not editing code.
- **Parameter registry.** Each parameter has a default, a plausible range, a unit, a source and a scope (global, per KHG, or per compartment). Dashboard edits override defaults; every run stores a snapshot of the parameters used, so results are reproducible and citable.
- **Two tiers of fidelity.** Tier 1 is a fast compartment water-balance model that runs interactively for any KHG. Tier 2 is a 2D groundwater model run offline for pilot KHGs; it calibrates Tier 1's lumped coefficients and checks its spatial pattern.
- **Graceful with missing data.** Where loggers or LiDAR are absent, regional defaults are used and the affected outputs are flagged with wider uncertainty bands.
- **No circular validation.** Hotspots and burnt areas used to validate risk come from years not used to build susceptibility weights.
- **Transparent rules.** Allocation is an explicit optimisation with stated objectives and constraints, so a decision maker can see why a block or pump was recommended.

## Data inputs and preprocessing

Fifteen layers feed the model; only the first six are mandatory, the rest improve accuracy or validation.

| Layer | Likely source | Role in model | Required |
| --- | --- | --- | --- |
| KHG boundary and peat function zones (lindung/budidaya) | KLH/BPLH KHG and FEG maps | Model domain; protected zones get full canal closure | Yes |
| Peat depth | National peat map, field cores | Storage ceiling; ≥3 m flags protected peat; consequence weight | Yes |
| DEM / DTM | LiDAR where available, else DEMNAS | Compartments, flow direction, hydraulic head | Yes |
| Canal network | KLH/BPLH, concession PROPER reports, digitised from imagery | Canal graph | Yes |
| Existing canal blocks and water gates | KLH/BPLH, PROPER/SIMPEL reports, field survey | Infrastructure state and condition | Yes |
| Daily rainfall | CHIRPS or GPM IMERG; BMKG gauges for bias correction | Forcing | Yes |
| Proposed block locations | User input | Scenario | No |
| Water sources (rivers, lakes, embung) | Topographic base maps; river stage if available | Pump intakes | Needed for pump scenarios |
| TMA logger series | SiPALAGA, concession loggers | Initial state, calibration | Strongly recommended |
| Max temperature and reference ET | BMKG, ERA5-Land; MODIS ET for checking | Forcing, PFVI | Recommended |
| Land cover | KLH/BPLH land cover, Sentinel-2 | ET factor, susceptibility | Recommended |
| Burnt area and severity | Sentinel-2 / Landsat dNBR | Susceptibility and priority | Recommended |
| Active fire hotspots | VIIRS 375 m (FIRMS) | Validation only | Recommended |
| Ground subsidence | Sentinel-1 InSAR | Validation of chronic drainage | Optional |
| Villages and roads | National topographic base maps | Ignition proxy; pump access | Optional |

How each layer is prepared and checked before use is set out in the next section.

## Data preparation

On peat domes the hydraulic signal is tens of centimetres, so terrain preparation decides whether the model is usable at all. Every step below writes its output to `data/interim/` and records an accuracy figure that the dashboard shows next to results.

### Terrain

1. **Choose the source per area.** Use a LiDAR DTM wherever it exists. Elsewhere use DEMNAS (8 m) or a bare-earth global product such as FABDEM (30 m) as the starting surface. Keep a raster recording which source each pixel came from.
2. **Harmonise the vertical datum.** Convert every height — DEM, LiDAR, GNSS points, logger tops, block crests — to one orthometric datum, preferably Indonesia's national geoid model (INAGeoid2020). Read each product's stated datum from its metadata rather than assuming it; LiDAR and GNSS are often ellipsoidal.
3. **Convert DSM to DTM (vegetation correction).** DEMNAS is a radar DSM (IFSAR, TerraSAR-X, ALOS PALSAR) blended toward stereo-plotted mass points, so how much canopy it still contains is unknown and varies by sheet (Julzarika & Harintaka 2019; Susetyo et al. 2018). In three test runs (Sebangau, Mendahara, Bengkalis) the fitted tree-cover k was 0.04–0.21, not the 0.8 prior, and the offset to lidar ground differed by site (−3.4, about 0 and +2.2 m). Do not assume a canopy offset; fit it, preferably per source area as well as per land-cover class. Two options, both calibrated against ground points:
   - **Canopy subtraction:** DTM = DSM − k × canopy height, using a global canopy height map and a penetration factor k fitted per land-cover class (radar partly penetrates the canopy, so k is below 1).
   - **Bare-earth start:** begin from FABDEM and fit per-class residual offsets.
   - **Ground points for calibration:** LiDAR overlap areas, ICESat-2 ATL08 terrain heights (strong beams, quality-filtered), GEDI lowest-mode ground returns (quality flag set), and GNSS spot heights on canal banks and at loggers.
4. **Smooth residual artefacts.** Peat domes are smooth, so after masking canals, roads and settlements, remove remaining canopy steps and noise with a low-pass filter or a fitted trend surface at a few hundred metres scale. Inspect forest–clearing edges, where step artefacts concentrate.
5. **Correct to the model year (epoch).** The surface subsides by centimetres per year. Shift the DTM from its acquisition date to the model year using InSAR rates where available, or land-use defaults otherwise (about 2.2 cm/yr mean across Southeast Asian peat, up to about 4–5 cm/yr under plantation drainage). Surveyed block crests are not shifted.
6. **Hydro-condition.** Burn the canal network into the DTM (canals are narrower than a pixel) and resolve depressions by breaching, not filling, because filling creates false flats on domes. Then derive flow direction and accumulation.

**Check:** RMSE and bias against held-out ground points, per land-cover class, plus the relative (detrended) error and slope error over 0.5–2 km, because the model uses height differences, not absolute heights. Design target RMSE ≤0.25 m (adjustable) applies where a LiDAR DTM exists. DEMNAS-only areas cannot reach it: published DEMNAS accuracy is RMSE 2.2–5.0 m at open-ground control points, and our smoothed DTMs reached 1.2–2.8 m at lidar points in vegetation. There, report the achieved error, flag the compartments, and take heads that need decimetre accuracy (canal water levels, crests, logger heads) from GNSS or levelling, not from the DTM. See [07](07-demnas-literature.md).

### Canals and structures

1. **Assemble canals** from KLH/BPLH and concession layers, OpenStreetMap, the unofficial 337-KHG database, and digitising from recent imagery for gaps.
2. **Clean topology:** snap endpoints, split at junctions and structures, remove duplicates, and list disconnected pieces for review.
3. **Attributes:** width from imagery; depth from survey or a default per canal class; bed elevation = bank DTM − depth.
4. **Flow direction:** from DTM slope along each reach. Where the slope is smaller than the DTM error over that reach, direct flow toward the nearest outlet along the network instead.
5. **Structures:** de-duplicate points within a tolerance (default 20 m); record type and year built; take crest elevation from survey, else bank DTM plus reported height; take condition from survey, else from a decay rule by block type and age.

**Check:** overlay on recent imagery and field-verify a random sample of canals and structures.

### Peat depth

1. Interpolate field cores by kriging with surface elevation and distance to river as covariates; where cores are sparse, resample the national peat map instead.
2. Compute substrate elevation (DTM − thickness) and flag negative or implausible values.

**Check:** cross-validation RMSE of thickness.

### Water table loggers

1. **Quality control:** remove spikes, flat-lines and physically impossible values; correct known sensor offsets; gap-fill only short gaps (default ≤3 days).
2. **Re-reference:** subsidence moves the ground relative to the logger, so re-survey each logger's ground and reference elevation by GNSS and convert depth readings to head on the common datum.
3. **Classify** loggers by distance to canal, used later to weight validation.

**Check:** compare against manual dipwell readings where available.

### Climate forcing

1. **Rainfall:** CHIRPS daily, bias-corrected against BMKG gauges (monthly ratio or quantile mapping), then averaged per compartment.
2. **Evapotranspiration:** reference ET by Penman–Monteith from ERA5-Land, scaled by land-cover factors.

**Check:** hold out some gauges for rainfall; compare dry-season ET with eddy-covariance values for Indonesian peat (about 4 mm/day).

### Fire and land-cover layers

1. **Burnt area:** cloud-masked Sentinel-2 or Landsat composites before and after each fire season; dNBR classified with standard severity thresholds; cross-checked against official burned-area maps.
2. **Hotspots:** VIIRS 375 m at nominal or high confidence; remove persistent non-fire sources; cluster detections in space and time into fire events.
3. **Land cover:** map source classes to the model's classes (forest, drained forest, shrub/fern, burnt, plantation, agriculture, settlement, water).

### Tidal zone

Map the tidally influenced zone from river stage or hydrographic tide data where available; otherwise use a proxy of low elevation near the coast and along rivers, flagged as low confidence.

### Accuracy summary

| Layer | Check | Design target (adjustable) |
| --- | --- | --- |
| DTM | RMSE vs held-out ground points, per land cover; relative error over 0.5–2 km | ≤0.25 m with LiDAR; DEMNAS-only: report achieved (1.2–2.8 m in our tests) |
| Datum | Same point in two products agrees after conversion | ≤0.05 m |
| Canals | Field or imagery verification of a random sample | ≥90% correct |
| Structures | Field verification of location and condition | ≥90% located |
| Peat depth | Kriging cross-validation | Report RMSE |
| Loggers | Agreement with manual dipwell readings | ≤0.05 m |
| Rainfall | Gauge hold-out | Report bias and RMSE |

## Spatial framework: compartments and canal graph

Each KHG is represented as a directed canal graph coupled to land compartments; water moves between compartments only through the canals and the peat next to them.

**Canal graph G = (V, E).** Nodes are canal junctions, blocks, gates, outlets to rivers or the sea, and pump intake and discharge points. Edges are canal reaches carrying length, bed and bank elevation, width, and a canal–peat exchange conductance. Flow direction comes from the DEM; reversals are allowed when heads reverse (e.g. after pumping).

**Compartments.** A compartment is the land that drains to one canal reach between two structures, delineated from DEM flow direction and bounded by the peat-dome divide and neighbouring canals. Attributes: area, mean surface elevation, peat depth, land cover, burnt fraction, and the distribution of distance-to-canal. Compartments in protected-function peat are tagged so scenarios can apply full canal closure.

This follows the sub-PHU concept of [Cahyono et al. (2022)](https://www.mdpi.com/2073-445X/11/7/1094), who split the Kahayan–Sebangau PHU into 16 sub-units bounded by closed patterns of outlet canals and rivers, using LiDAR-derived streamlines, peat depth, slope and network connectivity, and verifying boundary canals on orthophotos and in the field. Where their method yields larger units than the reach-based compartments above, sub-PHUs act as the parent level: compartments nest inside them, and results are reported at both levels.

**Block candidates.** Along every reach, a candidate site is placed each time the canal water surface drops by Δh\_max (default 0.3 m). Because 0.3 m is close to the DTM error, the drop is measured on the smoothed bank-elevation profile (trend surface from Data preparation), not on raw pixels, and the terrain Monte Carlo reports how stable each site is. This follows community canal-blocking guidance that spaces blocks so the head difference between them stays below about 30 cm, typically 500 m–1 km apart ([BRG training module](https://www.researchgate.net/publication/322520057_Modul_Pelatihan_Pembangunan_Infrastruktur_Pembasahan_Gambut_Sekat_Kanal_Berbasis_Masyarakat)). User-proposed sites are added to the same candidate set.

**Water-source nodes.** Rivers, lakes and embung within a user-set distance of the canal network (default 2 km) become potential pump intakes, linked to the nearest canal node by a candidate pump edge.

## Hydrological core: water table model

Tier 1 solves a daily water balance per compartment coupled to canal storage per reach; Tier 2 solves the 2D groundwater equation and is used to calibrate Tier 1.

**Tier 1 — compartment balance.** For compartment i with area Aᵢ and spatially averaged water table hᵢ (m above datum):

```latex
S_y(\zeta_i)\,A_i\,\frac{dh_i}{dt} = A_i\,(P - ET_i) - C_i\,(h_i - h_{c,i}) + Q_{\mathrm{pump},i}
```

where ζᵢ = hᵢ − surface elevation is the water table depth (negative below ground), h\_c,i is the water level in the adjacent canal reach, Cᵢ is the canal–peat exchange conductance, and Q\_pump,i is pumped water discharged directly onto the compartment (usually zero; pumps normally discharge into canals).

- **Specific yield** decreases with depth: S\_y(ζ) = s₁·exp(s₂·ζ), with ζ negative below ground so s₂ > 0. Default s₁ = 0.3 at the surface, falling to about 0.1 at 1.5 m depth (s₂ = ln 3 / 1.5 ≈ 0.73 m⁻¹), consistent with field estimates from a drained Indonesian peatland island ([Water table variations, PSWRC](https://www.sciencedirect.com/science/article/pii/S1998956326003058)).
- **Exchange conductance** Cᵢ = K·d\_eff·(2·L\_reach) / L\_inf, combining hydraulic conductivity K, effective saturated thickness d\_eff, reach length on both banks, and the canal influence distance L\_inf. It is the main Tier 1 calibration target. L\_inf depends on peat condition: field transects find about 20 m on burnt peat and 170–240 m elsewhere, and a reach of about 200 m needs a canal rise above 0.6 m (see Parameter register).
- **ET** has a constant dry-season baseline (default 4.17 mm/day, the multi-year tropical peatland mean used by Urzainki et al. 2023), scaled by a land-cover factor and reduced when ζ falls below a rooting threshold.
- **Within-compartment profile.** The compartment mean is spread over distance x from the canal with h(x) = h\_c + (h\_far − h\_c)·(1 − e^(−x/λ)), λ = L\_inf/3. Each day h\_far is solved so that the area-weighted mean of h(x), using the compartment's distance-to-canal distribution, equals the balance result hᵢ. This lets the model report the *fraction of area* meeting the 0.4 m target, not just the mean, and the allocation step uses the same profile to compute deficits (next sections).

**Canal reaches.** Each reach between structures is a storage cell with water level h\_c. It gains lateral inflow from compartments, upstream overflow and pumped water, and loses water over or through the downstream structure (see Interventions). Daily steps are sub-stepped (default 1 hour) when flows are large relative to storage.

**Tier 2 — 2D groundwater.** For pilot KHGs, the model of [Urzainki et al. (2023)](https://bg.copernicus.org/articles/20/2099/2023/) couples a diffusive-wave canal network to the peat equation below, with S\_y and transmissivity T both depending on water table depth:

```latex
S_y(h)\,\frac{\partial h}{\partial t} = \nabla \cdot \left( T(h)\,\nabla h \right) + P - ET
```

Tier 2 runs are used to fit Cᵢ and L\_inf for Tier 1 and to check the spatial pattern of block effects. Two Tier 2 findings shape this design: block effects were relevant up to about 600 m from canals and negligible beyond 1 km, and in a prolonged drought blocks lost effect once canals ran dry, leaving parts of the peat deeper than the 0.4 m limit (Urzainki et al. 2023). Blocks alone cannot carry a severe dry season, which is the hydrological case for pumps.

## Interventions: canal blocks, water gates and pumps

Blocks hold water, gates route it, and pumps import or lift it; all three are nodes or edges on the canal graph with user-editable attributes.

**Canal blocks (sekat kanal).** A block is a fixed weir with crest elevation z\_b. Outflow follows the weir form used by Urzainki et al. (2023), plus a seepage term because real blocks leak:

```latex
Q_b = \eta\,K_b\,\max(0,\; h_{up} - z_b)^{1.5} + k_{leak}\,(h_{up} - h_{down})
```

Free-flow weir flow is only valid while the downstream level stays below the crest. Heads between blocks are about 0.3 m on near-flat peat, so downstream backwater often submerges the weir. When h\_down > z\_b the model multiplies the weir term by a submergence factor (1 − ((h\_down − z\_b)/(h\_up − z\_b))^1.5)^0.385 (Villemonte), which drops to zero as the two levels equalise.

The condition factor η (0–1) and leakage k\_leak represent deterioration; field evaluations have found many blocks degraded by weathering, scour and sedimentation ([Mongabay, Oct 2024](https://mongabay.co.id/2024/10/26/nasib-sekat-kanal-gambut-di-desa-karya-indah/)). Crest height defaults to 0.3 m above the downstream design level and cannot exceed the local peat surface.

**Water gates (pintu air).** A gate is a block with an adjustable crest or opening, governed by an operating rule per gate:

- **Hold** (dry season default): close fully while upstream canal level is below its target band.
- **Share**: open to release water to a downstream receiver when the allocation step (next section) assigns a transfer and upstream stays within its band.
- **Spill** (wet season): open when upstream level exceeds the upper limit, to prevent flooding of crops or villages.

Band limits, rule priority and the season switch date are dashboard parameters.

**Pumps (pompa).** A pump is a directed edge carrying water from a source node to a discharge node, either from an external source (river, lake, embung) into a canal, or from a lower reach to a higher reach across a block (lifting). Its delivered flow is

```latex
Q_p = \min\left(Q_{max},\; Q_{src}\right) \cdot \frac{H_{op}}{24} \cdot \mathbb{1}\left[\Delta z \le H_{lift}\right]
```

where Q\_max is rated capacity, Q\_src is what the source can supply (zero if river stage falls below the intake or water is brackish), H\_op is operating hours per day, and Δz is the head to overcome against the pump's lift limit H\_lift. Fuel use = H\_op × fuel rate, summed against a season fuel budget.

**Pump relays.** Field practice moves river water over long distances with a chain of pumps through canals, held at each step by blocks: an 11 km relay from the Batang Hari River in Jambi, and one large intake pump feeding five smaller pumps over 9 km of canals from the Pawan River in Ketapang (see Purpose). A relay is modelled as a path of pump edges and canal reaches; delivery at the end is the smallest pump capacity on the path, reduced by seepage along the way.

**Seepage is not a loss.** Water that seeps out of a pumped canal enters the adjacent compartments through the same exchange term Cᵢ used in the hydrology. So the model credits relay seepage as distributed rewetting along the route, which is often the point of the relay.

**Rule that couples them.** Pumped water entering a reach with no downstream block or a gate set to spill drains away within days. The model flags any pump whose discharge reach lacks a holding structure, and the optimiser in the next section only assigns pumps to reaches that can retain water.

**Other point sources (optional).** Embung act as storage nodes refilled in the wet season; deep wells (sumur bor) are point sources used for firefighting readiness, reported but not counted as rewetting.

## Water-sharing allocation algorithm

Each decision interval (default 7 days), the model moves surplus water to risk-weighted deficits through gates and pumps, solved as a min-cost network flow on the canal graph; hydrology then runs daily until the next decision.

*Figure (to be inserted): model loop.*

Hydrology and risk run every day; allocation runs once per decision interval and feeds gate settings and pump schedules back into hydrology.

```
daily:    forcing → Tier 1 hydrology → water table → hazard/risk
weekly:   deficits + priorities + supply → look-ahead LP → gate settings, pump schedules
                         ↑_____________________________________________↓
```

**Step 1 — Deficit.** For each compartment, the water needed to bring the water table back to the target depth ζ\* (default 0.4 m below surface). Because S\_y falls with depth, the deficit integrates S\_y over the missing water table rise, summed over distance bands b of the within-compartment profile (area share a\_b, depth d\_b = |ζ\_b|):

```latex
D_i = A_i \sum_b a_b \,\mathbb{1}[d_b > \zeta^{*}] \int_{\zeta^{*}}^{d_b} S_y(z)\,dz
    = A_i \sum_b a_b \,\frac{s_1}{s_2}\left(e^{-s_2 \zeta^{*}} - e^{-s_2 d_b}\right)\mathbb{1}[d_b > \zeta^{*}]
```

Using bands, not the compartment mean, means a compartment that looks fine on average but fails far from the canal still shows a deficit.

**Step 2 — Priority weight.** wᵢ = risk class weight × burn-history multiplier × protected-peat multiplier × village-proximity multiplier. All multipliers are dashboard sliders; defaults are 1 except protected peat (1.5) and repeat-burnt compartments (1.5).

**Step 3 — Supply.** Three kinds of supply are available:

- **Internal surplus**: water a donor compartment or reach holds above its target plus a safety buffer (default 0.1 m), so donors are never drawn down into deficit.
- **Gravity transfer**: release through a gate in Share mode, only downhill along the graph (donor head higher than receiver).
- **Pumped supply**: external sources and lifts, limited by pump capacity, hours, units available and the season fuel budget.

**Step 4 — Optimise.** Choose transfers x on each edge to maximise risk-weighted deficit relief minus operating cost:

```latex
\max_{x}\; \sum_i w_i \min(x_i, D_i) \; - \; \lambda_f \sum_{p} \mathrm{fuel}_p(x_p)
```

subject to mass balance at every node, gate and canal capacity, gravity-only flow on non-pump edges, pump lift and capacity limits, donor surplus limits, and the fuel budget. The λ\_f term sets how much fuel one unit of risk-weighted rewetting is worth. A linear program solves this in seconds for a KHG; a greedy fallback (largest wᵢ·Dᵢ first, cheapest feasible source) keeps the dashboard responsive.

**Look-ahead.** A single-interval LP is myopic: it gains nothing from storing water before a dry spell, and it can send water to a compartment that will lose it again within days. Two additions handle this:

- **Rolling horizon.** Each decision solves over the next H intervals (default 3, so three weeks) using the scenario's own forcing, or the forecast or a rainfall ensemble in operational use, and applies only the first interval's transfers. The deficit term is evaluated at the end of each interval, so transfers that only delay a deficit score less than ones that hold.
- **Retention weight.** Transfers into a reach are discounted by its expected seepage and drain-away over the horizon (from Tier 1), so water goes where it stays. The sanity tests check that the horizon-1 solution reproduces the plain LP.

**Step 5 — Apply and repeat.** Transfers become gate settings and pump schedules for the next interval; daily hydrology runs with them, and the cycle repeats.

**Block siting (planning mode).** Because blocks are scarce, a separate greedy search picks the next N blocks from the candidate set: add the candidate that most reduces season-total risk-weighted deficit, re-run Tier 1, repeat until N or the budget is reached. The output is a ranked list with marginal benefit per block, so decision makers can see where returns diminish.

## Fire risk module

Risk per compartment and day is hazard (how dry the peat is now) times susceptibility (how likely and how damaging a fire there would be); its classes feed the allocation weights.

**Hazard.** Signals driven by modelled water table depth and rainfall:

- **Water table depth class** (primary): modelled depth ≤0.4 m low, 0.4–0.6 m moderate, 0.6–0.85 m high, >0.85 m extreme. The bounds follow Indonesian field evidence: high fire danger mostly once the water table drops below 0.4 m and burned area only below 0.6 m (Taufik et al. 2022), with danger levelling off near 0.85 m (Taufik et al. 2019). All bounds are adjustable.
- **Exceedance and dry spells**: days per season with water table deeper than 0.4 m, maximum depth reached, and longest run of consecutive dry days from CHIRPS. Cahyono et al. (2022) used dry-period length as a degradation indicator and estimated a water-table drop of about 23–31 cm after 14 rainless days and 34–46 cm after 21 ([Land 11, 1094](https://www.mdpi.com/2073-445X/11/7/1094)).
- **PFVI — deferred.** The Peat Fire Vulnerability Index (Taufik et al. 2022) and the peatfr package are on hold until their validity is checked (see Addendum). The hazard slot is built so PFVI can be added later as a third signal without changing the rest of the model.

**Susceptibility.** A weighted score of:

- burn history (number of years burnt and dNBR severity class);
- distance to canal (drainage pressure and access);
- distance to roads and villages (ignition proxy);
- land cover (degraded shrub and fern highest, intact forest lowest);
- peat depth (consequence: deeper peat stores more carbon to lose).

Default weights are expert-set and equal, adjustable on the dashboard. As a cross-check, factors can also be scored by ordinal rank per compartment, following the ranking approach of Cahyono et al. (2022). Fitting weights from burn history (statistical or machine learning) is deferred; see Addendum.

**Combination.** Risk class is a 4 × 3 lookup of hazard class against susceptibility tercile, which keeps the logic explainable to KLH staff. Risk class sets the allocation weight wᵢ in the previous section.

**Kept separate on purpose.** Hotspots never enter the risk score; they are only used to test it.

## Strategy assignment

After each scenario run, a rule-based decision tree assigns every compartment the cheapest intervention that closes its projected deficit, using only modelled quantities so it applies to any KHG.

*Figure (to be inserted): strategy decision tree, 4 tests and 5 outcomes: meets target, operate gate, repair or build block, pump relay, fire readiness.*

The tree works inside a scenario run: it takes the S0–S5 package as the starting infrastructure, labels each compartment's residual need, and its output is the recommendation list. The packages answer "what does this level of intervention buy?"; the tree answers "which action goes where?". It does not change the package definitions.

Tests run in default order of cost: operating an existing gate costs least, then repairing or building a block, then pumping, which needs fuel for the whole season. That order mixes capital and operating cost, so the dashboard also offers a levelised-cost ordering over a user-set horizon (default 10 years): block capital plus repair cycles against pump purchase, fuel and labour. Where the two orderings disagree, the compartment is flagged. After each "yes" the action is applied, Tier 1 is re-run, and the compartment is tested again from the top; a compartment can end with more than one action (for example a new block plus a pump relay that feeds it).

The tests, with adjustable thresholds:

1. **Meets target**: modelled water table no deeper than ζ\* (0.4 m) on at least 95% of season days.
2. **Gravity supply**: an upstream donor reach with surplus above its buffer, connected through a gate, at higher head.
3. **Block in reach**: an existing block with condition η below 0.7, or a block candidate within L\_inf of the compartment on a reach that does not run dry.
4. **Pump reach**: a water source with supply in the dry season within the maximum relay length, lift within the pump limit, and a holding block downstream of the discharge point.

In protected-function peat (≥3 m), "build block" means full canal closure or backfilling, following the rule that drainage in protected peat is closed entirely. The fallback outcome, fire readiness, marks residual-risk areas where hydrology alone cannot meet the target in that climate year; the dashboard lists them separately for suppression planning.

## Scenarios

Every run is one climate year crossed with one intervention package, so results answer "what does this package buy us in this kind of year?"

**Climate years.** Historical daily forcing replayed for a normal year, a moderate El Niño year and a strong El Niño year. Default analogs are 2015 and 2019 for strong and moderate dry seasons; users can pick any year with forcing data, including 2023 and the current 2026 season.

| Package | What it adds | Question it answers |
| --- | --- | --- |
| S0 Baseline | Existing blocks and gates at their surveyed condition | How bad is it now? |
| S1 Repair | S0 with all blocks restored to full condition | What does maintenance alone buy? |
| S2 Proposed blocks | S1 plus user-proposed block sites | Do the planned sites help where it matters? |
| S3 Optimised blocks | S1 plus N blocks chosen by the siting search | How much better is optimal siting than the plan? |
| S4 Gate operation | S3 plus gate rules and gravity water sharing | What does active operation add for free? |
| S5 Pumps | S4 plus pumps and relays within a fuel budget | What is left that only imported water can fix, and at what cost? |

The gap between S5 and the target is the residual-risk area that needs firefighting readiness rather than hydrology.

**Sensitivity runs.** Each package is re-run with block condition η = 0.5, with S\_y and K at the low and high ends of their ranges, and with ±20% rainfall, so the dashboard can show how fragile each recommendation is.

## Calibration and validation

The model is checked at three levels — water table, fire outcome, and intervention effect — each against data it was not tuned on.

| Level | Calibrate on | Validate against | Metric |
| --- | --- | --- | --- |
| Water table | Logger series, training dry seasons | Held-out seasons; leave-one-station-out | RMSE and bias (m), Nash–Sutcliffe efficiency |
| Spatial pattern | Tier 2 runs on a pilot KHG | Sentinel-1 soil moisture anomaly; InSAR subsidence rate | Rank correlation by compartment |
| Fire outcome | Burnt area in training years | Hotspot clusters and burnt area in held-out years | AUC; share of burnt area inside the top 20% risk area |
| Early warning | — | Days of lead between high/extreme hazard class and first hotspot | Hit rate, false-alarm rate |
| Intervention effect | — | Loggers before and after block construction, against unblocked control sites | Before–after–control–impact difference (m) |

Calibration order: fit Cᵢ and S\_y per compartment group against loggers first, then ET factor, then block coefficients K\_b and η where before/after data exist. Parameters without data keep registry defaults and inherit the full range in the uncertainty runs.

**Equifinality.** Cᵢ (K·d\_eff/L\_inf), S\_y and the ET factor trade off against each other when fitted to water table series alone. Calibration therefore fits Cᵢ as one lumped term rather than K, d\_eff and L\_inf separately, uses recession periods (no rain) to separate S\_y and ET from canal exchange, and reports the posterior spread, for example by accepting all parameter sets within a tolerance of the best fit (GLUE style). Those accepted sets, not a single optimum, feed the Monte Carlo above.

**Uncertainty.** A Monte Carlo of at least 200 runs gives, for each compartment, the probability that the water table falls deeper than 0.4 m. The dashboard shows this probability alongside the central estimate, so a recommendation that only holds under optimistic parameters is visible as such. Sampling rules:

- **Parameters** are drawn from the registry ranges: log-uniform for K, L\_inf and k\_leak (ranges span more than an order of magnitude), uniform otherwise. Correlated parameters (S\_y with K, C\_i with L\_inf) are sampled jointly or conditioned on calibration where loggers exist.
- **Terrain error is sampled too.** Each run adds a spatially correlated DTM error field (correlation length a few hundred metres, standard deviation equal to the per-land-cover RMSE from Data preparation, so larger outside LiDAR) and a datum offset drawn within the stated datum tolerance. Flow direction, block-candidate placement and the surface-relative water table are recomputed from the perturbed surface. A block site or pump assignment that is recommended in fewer than a set share of runs (default 70%) is labelled terrain-sensitive. Outside LiDAR coverage this is what separates a robust recommendation from an artefact of the DEM.
- **Compute.** The full Monte Carlo is precomputed offline per KHG and scenario and cached; interactive edits recompute the central run only and mark the cached uncertainty as stale until refreshed.

**Measurement caution.** Loggers sit mostly near canals, where block effects are largest, so naive extrapolation overstates block performance (Urzainki et al. 2023). Validation therefore weights stations by distance-to-canal class, and Tier 2 fills the gap far from canals.

## Dashboard outputs and controls

The dashboard lets a KLH analyst pick a KHG, adjust any assumption, build a scenario on the map, and compare packages on six headline indicators.

**Controls**

- **KHG selector** loads that KHG's layers and its calibrated parameter set, or regional defaults if uncalibrated (flagged).
- **Parameter panel** shows every registry entry with its default, range, unit and source; edits are range-checked and can be reset; each run saves its parameter snapshot.
- **Scenario builder**: choose the climate year; add, remove or degrade blocks on the map; set gate rules; place pumps and relays with capacity, hours and fuel; set the block count N or budget.
- **Priority sliders** for the allocation weights (protected peat, repeat burns, village proximity).

**Views**

- Map layers: water table depth, deficit and surplus, risk class, probability of exceeding 0.4 m, burn history, infrastructure.
- Canal network with daily flow direction and magnitude, including pumped and gate transfers.
- Time series per compartment or logger: modelled versus observed water table, hazard class, pump operation.
- Ranked lists: next block sites by marginal benefit; pump sites by rewetted hectares per litre of fuel.
- Scenario comparison table across S0–S5.

**Headline indicators**

| Indicator | Unit |
| --- | --- |
| Peat area meeting the 0.4 m target, season average | % of KHG |
| Area-days with water table deeper than 0.4 m | ha·day |
| Risk-weighted deficit remaining at season end | m³ (weighted) |
| Area rewetted per new block | ha/block |
| Water pumped and fuel used | m³, litres |
| High/extreme-risk area left after all interventions | ha |

Implementation suggestion: a Python back end for Tier 1 and the optimiser (the central run recomputes on edit), Tier 2 runs and the Monte Carlo precomputed offline and cached, and a web map front end. Uncertainty layers show a "stale" flag after any edit until the Monte Carlo is refreshed.

## Parameter register

These are starting values for any KHG; every row is editable in the dashboard and replaced by calibrated values where data allow. "Assumption" marks a default chosen for this design that still needs a literature or field basis.

| Parameter | Symbol | Default | Range | Unit | Scope | Basis |
| --- | --- | --- | --- | --- | --- | --- |
| Target water table depth | ζ\* | 0.40 | 0.2–0.6 | m below surface | Global | PP 57/2016 limit |
| Share of season days meeting target | – | 95 | 80–100 | % | Global | Assumption; strategy test 1 |
| Specific yield at surface | s₁ | 0.30 | 0.05–0.6; 1.0 when ponded | – | Compartment | Field estimates up to 0.3 (Ismail et al. 2021); 0.05–0.30 in pristine top peat |
| Specific yield at 1.5 m depth | – | 0.10 | 0.03–0.15 | – | Compartment | Ismail et al. 2021 |
| Specific yield decay rate | s₂ | 0.73 (derived from s₁ and S\_y at 1.5 m) | 0.4–1.5 | 1/m | Compartment | Derived; recomputed whenever s₁ or the 1.5 m value is edited |
| Hydraulic conductivity, upper peat | K | 50 | 5–1300 | m/day | Compartment | >10 m/day typical tropical peat (Ritzema et al. 2014); 50 calibrated in Central Kalimantan (Freewat study); lower on drained or burnt peat |
| Canal influence distance | L\_inf | 200 | 20–1000 | m | Compartment | \~20 m on burnt peat; 170–240 m in field transects; \~600 m modelled (Urzainki et al. 2023) |
| Canal rise for \~200 m lateral reach | – | 0.6 | 0.3–0.8 | m | Global | Field dipwell transects, Riau |
| Dry-season baseline ET | ET₀ | 4.17 | 3–5 | mm/day | KHG | Multi-year tropical peatland mean used by Urzainki et al. 2023; Kahayan–Sebangau monthly mean 3.52 mm/day (Cahyono et al. 2022) |
| Dry-spell water-table decline (check only) | – | emergent | 1.0–2.2 | cm/day | Check only | Cahyono et al. 2022 (16–22 mm/day of decline, not water loss); Tier 1 should reproduce this |
| Water-table drop after 14 / 21 dry days | – | 23–31 / 34–46 | – | cm | Check only | Cahyono et al. 2022; decline slows as drainage weakens |
| Max head drop between blocks | Δh\_max | 0.30 | 0.2–0.4 | m | Global | <30 cm in BRG training module |
| Block spacing (derived) | – | 500–1000 | 200–2000 | m | Reach | BRG training module |
| Block condition factor | η | 1.0 new | 0–1 | – | Block | Assumption; set from field survey |
| Block repair threshold | – | 0.7 | 0.5–0.9 | η | Global | Assumption; strategy test 3 |
| Block leakage coefficient | k\_leak | 0.05 | 0–0.2 | m²/s | Block | Assumption (flow m³/s = k\_leak × head difference in m) |
| Allocation look-ahead horizon | H | 3 | 1–6 | decision intervals | Global | Assumption |
| Terrain-sensitive threshold | – | 70 | 50–95 | % of Monte Carlo runs | Global | Assumption |
| Cost-comparison horizon | – | 10 | 3–20 | years | Global | Assumption |
| Gate upper/lower band | – | −0.2 / −0.4 | user | m relative to surface | Gate | Assumption |
| Pump rated capacity | Q\_max | user entry | – | m³/h | Pump | Pump specification |
| Pump operating hours | H\_op | 8 | 0–24 | h/day | Pump | Assumption |
| Pump lift limit | H\_lift | user entry | – | m | Pump | Pump specification |
| Relay length | – | user entry | 0–15 | km | Relay | Field relays of 9–11 km reported in 2026 |
| Season fuel budget | – | user entry | – | litres | KHG | Operator input |
| Donor safety buffer | – | 0.10 | 0–0.3 | m | Global | Assumption |
| Decision interval | – | 7 | 1–14 | days | Global | Assumption |
| Hazard class bounds (water table depth) | – | 0.4 / 0.6 / 0.85 | user | m below surface | Global | Taufik et al. 2022 (danger below 0.4 m, burning below 0.6 m); Taufik et al. 2019 (levels off near 0.85 m) |
| Dry-day threshold | – | 1 | 0–5 | mm/day | Global | Assumption; CHIRPS daily |
| Hotspot confidence threshold | – | 70 | 60–80 | % | Global | Used for tropical peat by Cahyono et al. 2022 (MODIS); for VIIRS use nominal/high classes |
| Protected peat priority | – | 1.5 | 1–3 | × | Global | Assumption |
| Repeat-burn priority | – | 1.5 | 1–3 | × | Global | Assumption |
| PFVI parameters and classes | – | deferred | – | – | – | On hold with peatfr pending validation |
| DTM accuracy target | – | 0.25 | 0.1–0.5 (LiDAR); 1–3 achievable from DEMNAS | m RMSE | KHG | Design target for LiDAR areas; DEMNAS published 2.2–5.0 m, our tests 1.2–2.8 m; see Data preparation |
| Grid / time step | – | 30 m / 1 day | – | – | Global | Design choice |

## Limitations and open questions

The largest risks are data, not equations: DEM accuracy, logger continuity and infrastructure inventories set the ceiling on what any KHG run can claim.

- **DEM accuracy.** Heads that matter differ by tens of centimetres, and micro-topography near canals varies by a similar amount; outside LiDAR coverage, results are indicative only. With DEMNAS the absolute error is metres (see Data preparation), so the 0.3 m block spacing, canal flow direction, gravity-transfer direction and pump lift are the model parts most at risk. A first check against ICESat-2/GEDI points at three sites found the smoothed DTM's height difference between points 1–2 km apart wrong by 1.1–2.6 m RMS (provisional; the ground heights carry their own error), well above the 0.3 m block step. Elevation-based block siting therefore needs LiDAR or survey; see [08](08-build-plan.md). The terrain Monte Carlo makes this visible by labelling terrain-sensitive recommendations, but it cannot remove a systematic bias (for example a canopy correction that is wrong everywhere), which only ground points can catch.
- **Myopic allocation.** The look-ahead horizon is short and depends on forcing that is known only in replay; operational use needs a rainfall forecast or ensemble.
- **Logger continuity.** SiPALAGA was anchored at BRGM, whose mandate ended; how it is now operated is unclear, so calibration may depend on concession loggers.
- **Incomplete inventories.** Canal, block and gate layers are often partial, and block condition is rarely surveyed; S0 baselines inherit those gaps.
- **Coastal KHGs.** Tidal canals and brackish rivers need tidal boundary conditions and a salinity check on pump intakes, not yet in Tier 1.
- **Lumped compartments.** Tier 1 cannot show the local water-table *lowering* that blocks can cause downstream (Urzainki et al. 2023); Tier 2 checks are needed before siting decisions in pilot KHGs.
- **People, not only water.** Ignition is human; blocked areas still burn when fires are set deliberately ([Mongabay, Oct 2024](https://mongabay.co.id/2024/10/26/nasib-sekat-kanal-gambut-di-desa-karya-indah/)). Who operates gates and pumps, and on whose land, is outside the model but decides whether its plan is carried out.

Open questions for the paper:

- [ ] Which KHG is the pilot for calibration and Tier 2?
- [ ] Is Tier 2 in scope for this paper, or reported as future work?
- [ ] Can pump inventories (capacity, lift, fuel use) be obtained from KLH or concession operators?
- [ ] Which agency is the primary dashboard user: KLH/BPLH, BPGMN, or both?

## Local build guide

*This section is implementation guidance, not method; move it to the repository README when the paper is drafted.*

Build it as a Python package in this order: data checks, canal graph and compartments, Tier 1 hydrology, interventions, allocation, strategy tree, and only then the dashboard. Each stage writes files the next stage reads, so any stage can be re-run alone.

**Environment.** Python 3.11+ in a conda environment.

| Purpose | Packages |
| --- | --- |
| Vector and raster I/O | geopandas, shapely, rasterio, rioxarray, xarray |
| Hydrological terrain analysis | pysheds or WhiteboxTools (depression breaching, flow direction, accumulation) |
| Canal graph and min-cost flow | networkx |
| Optimisation (linear program) | PuLP with CBC, or OR-Tools |
| Numerics and time series | numpy, pandas, scipy |
| Parameter registry and validation | pyyaml, pydantic |
| Remote-sensing pulls (optional) | earthengine-api for CHIRPS, Sentinel-1, Sentinel-2 |
| Tier 2 groundwater (later) | FiPy, the finite-volume library cited by Urzainki et al. 2023 |
| Dashboard (last) | Streamlit or Panel, with leafmap or pydeck for maps |
| Tests | pytest |

**Project layout.**

```
peat-watershare/
  config/
    parameters.yaml      # registry: default, range, unit, source, scope
    khg_<id>.yaml        # paths and overrides for one KHG
    scenarios.yaml       # S0–S5 definitions
  data/raw/<khg_id>/     # your input files, untouched
  data/interim/<khg_id>/ # reprojected, cleaned layers
  data/outputs/<khg_id>/<run_id>/
  src/watershare/
    io.py  checks.py  terrain.py  network.py  compartments.py
    hydrology.py  structures.py  allocation.py  risk.py
    strategy.py  scenarios.py  calibrate.py
  app/dashboard.py
  tests/
```

**Input file specification.** One folder per KHG; names can differ if mapped in `khg_<id>.yaml`.

| File | Type | Required fields or content |
| --- | --- | --- |
| khg\_boundary.gpkg | Polygon | khg\_id, name |
| peat\_function.gpkg | Polygon | function (lindung or budidaya) |
| dtm.tif | Raster | Ground elevation, m; state the vertical datum |
| peat\_depth.tif | Raster | Peat thickness, m |
| canals.gpkg | Line | canal\_id, width\_m; depth\_m if known |
| structures.gpkg | Point | struct\_id, type (block, gate), status (existing, proposed), crest\_elev\_m or height\_m, condition (0–1), year\_built |
| water\_sources.gpkg | Point or polygon | source\_id, type (river, lake, embung), dry\_season\_supply (yes/no), brackish (yes/no) |
| pumps.csv | Table | pump\_id, capacity\_m3h, lift\_m, fuel\_l\_per\_h, units\_available |
| tma\_loggers.csv | Table | station\_id, date, wtd\_m (negative below surface), x, y, ground\_elev\_m |
| rainfall/ | Daily raster stack | CHIRPS or equivalent, mm/day |
| et/ | Raster stack | Reference ET, mm/day or monthly mm |
| landcover.tif | Raster | Class codes plus a lookup CSV |
| burnt\_area.gpkg | Polygon | year, severity class |
| hotspots.csv | Table | date, x, y, confidence, sensor |
| villages\_roads.gpkg | Point and line | type |

**Conventions that prevent most bugs.**

- Water table depth is negative below the surface (−0.4 m = 40 cm below), as in Urzainki et al. 2023; store heads as elevation above one datum.
- DTM, logger ground elevations and block crest elevations must share the same vertical datum; a datum mismatch of 20–30 cm is as large as the signal.
- SI units throughout (m, m³, days); convert mm/day once at load time.
- Everything in the KHG's UTM zone; dates in ISO format.

**Pipeline order.**

1. Validate config and inputs (`checks.py`): CRS, required fields, value ranges, datum note present.
2. Preprocess terrain: run the terrain steps in Data preparation (datum, DSM-to-DTM correction, epoch shift, canal burning with breaching), then derive flow direction.
3. Build the canal graph: snap and split lines at junctions and structures, assign direction from the DTM.
4. Delineate compartments per reach, nest them in sub-PHUs, attach peat depth, land cover and burn history.
5. Attach structures and water-source nodes; generate block candidates at Δh\_max.
6. Aggregate daily rainfall and ET to each compartment.
7. Run Tier 1 for S0 and check it against the tests below.
8. Calibrate Cᵢ, S\_y and ET factor against loggers (`calibrate.py`).
9. Compute hazard, susceptibility and risk classes.
10. Run allocation, then the strategy tree, for each scenario.
11. Write outputs as GeoPackage (maps) and CSV (time series), each with a parameter snapshot; the dashboard only reads these.

**Example parameter entry** (`parameters.yaml`):

```yaml
target_wtd:
  default: -0.40
  range: [-0.60, -0.20]
  unit: m
  scope: global
  source: PP 57/2016
linf:
  default: 200
  range: [20, 1000]
  unit: m
  scope: compartment
  sampling: log-uniform
  source: field transects; Urzainki et al. 2023
```

**Sanity tests to pass before trusting any run.**

- [ ] Water balance closes per compartment within 1% over a season.
- [ ] With no rain, modelled water-table decline falls within the observed 1.0–2.2 cm/day, or the difference is explained. Cahyono et al. (2022)'s 16–22 mm/day is a water-table decline, about 5–7 mm/day of water at S\_y = 0.3, not a water loss.
- [ ] Removing all blocks never makes the KHG-average water table shallower.
- [ ] Pumped water into a reach without a holding structure is flagged.
- [ ] Re-running with the same parameter snapshot reproduces outputs exactly.
- [ ] The deficit with a constant S\_y (s₂ = 0) equals the simple depth × S\_y × area form.
- [ ] A submerged block (h\_down ≥ h\_up) passes only the leakage term, and flow is continuous across the free-flow/submerged switch.
- [ ] Allocation with horizon H = 1 reproduces the single-interval LP.
- [ ] With zero DTM error variance the terrain Monte Carlo collapses to the central run.

**Suggested build milestones.** (0) package skeleton, parameter registry and a synthetic testbed with known truth; (1) canal network, structures and compartments; (2) Tier 1 with no interventions, matching loggers; (3) add blocks, gates, pumps and allocation, and test how much terrain error the recommendations tolerate; (4) add strategy tree and scenarios; (5) pilot KHG with LiDAR and loggers; (6) dashboard and a second KHG to prove transferability. The revised sequence, the terrain interface and the decisions still to settle (spatial hierarchy, risk rule, parameter drift, breach vs fill) are in [08](08-build-plan.md).

## Addendum

These notes extend the core model; none is needed for the first working version, but InSAR is the strongest candidate for the next addition.

### A1. InSAR subsidence and its link to susceptibility

Subsidence rate is a direct, wide-area signal of chronic drainage, the condition the model is trying to reverse.

- **Processing.** Sentinel-1 time-series InSAR (SBAS or persistent scatterers) over at least two to three years, with a tool such as MintPy, LiCSBAS or SNAP-StaMPS. Choose reference points on mineral soil or stable infrastructure, since nothing on peat is stable.
- **Peat-specific cautions.** C-band coherence drops over dense vegetation and after fires; the peat surface also rises and falls seasonally with the water table. Remove the seasonal cycle before taking the long-term rate.
- **Use 1 — susceptibility.** Add subsidence rate per compartment as an optional susceptibility factor, and report its rank correlation (Spearman) with burn frequency and hotspot recurrence, controlling for land cover.
- **Use 2 — model check.** Faster subsidence should coincide with deeper modelled mean water table; a mismatch flags compartments where Tier 1 is wrong.
- **Use 3 — keeping geometry current.** Subsidence lowers the surface relative to block crests and canal beds, so a block designed against an old DTM can end up too high or too low. Update DTM and crest elevations from InSAR rates between LiDAR surveys.

### A2. Remote-sensing water table proxies

Sentinel-1 backscatter or soil-moisture products, OPTRAM from Sentinel-2 shortwave infrared, and NDMI (used by Cahyono et al. 2022) can show the spatial pattern of wetness between loggers. Use them first as checks on Tier 1, and only as inputs once each proxy has been compared with logger water table depth in the pilot KHG.

### A3. Terrain and tidal notes

- Cahyono et al. (2022) used a LiDAR DTM where available and a filtered WorldDEM for gaps; record which source each compartment relies on and widen its uncertainty band accordingly.
- They also found few fires in tidally influenced areas. Map the tidal zone from highest astronomical tide and treat it as a fixed-head boundary with lower default priority, while checking pump intakes there for brackish water.

### A4. Deferred components

| Component | Why deferred | What would bring it back |
| --- | --- | --- |
| Machine learning (susceptibility weights, spatial water table regression, fast surrogate of Tier 2) | Strategy choice has no training labels; learned weights may not transfer across KHGs | Enough labelled data from two or more KHGs, and a clear gain over expert weights in held-out years. Test leave-one-KHG-out against registry defaults; staged use for inputs (canals, terrain residual, parameter regionalisation) is outlined in [08](08-build-plan.md) |
| peatfr package and PFVI | peatfr's calibrated van Genuchten n was implausibly high and unstable; skill claims were weak | Retrieve Taufik et al. 2022; compute PFVI from modelled water table; keep it only if it predicts hotspot timing better than the simple depth classes in held-out years |

### A5. Research agenda

Questions a broader literature review should answer, roughly in order of impact on the parameter ranges:

1. Measured specific yield and hydraulic conductivity profiles for Indonesian peat, by region and land cover (including burnt peat).
2. Field evidence on how far canal level changes reach into the peat (influence distance) across peat types.
3. Empirical water table thresholds at which fire probability rises sharply, beyond the 0.4 m regulatory value.
4. Canal block performance and degradation rates by block type and age.
5. Pump and relay operations: capacities, fuel use, costs and conveyance losses from KLH, concession or PROPER reports.
6. InSAR peat subsidence studies in Indonesia and their relation to water table depth.
7. Official guidance on water-sharing practice and water management zones (zona air) under KLH/BPLH.
8. Evapotranspiration of degraded and burnt peat compared with forest.
9. Validation studies of peat fire danger indices (PFVI, KBDI, FWI) in Indonesia.
10. Existing decision-support tools for peat water management in Indonesia, to avoid duplicating them.

## References

Pages marked † were seen only as search summaries; check the full text before citing them in the paper.

- Urzainki, I. et al. (2023). A process-based model for quantifying the effects of canal blocking on water table and CO₂ emissions in tropical peatlands. *Biogeosciences* 20, 2099–2116. [Link](https://bg.copernicus.org/articles/20/2099/2023/)
- Mahdiyasa, A.W. et al. (2025). *Peatfr*: an R package to forecast tropical peatland fire risk (deferred; see Addendum A4). *Ecological Informatics* 92, 103532. [Link](https://www.sciencedirect.com/science/article/pii/S1574954125005412)
- Taufik, M. et al. (2022). Peat Fire Vulnerability Index. Agricultural and Forest Meteorology 312, 108738. doi 10.1016/j.agrformet.2021.108738 (source of the 0.4 m and 0.6 m fire thresholds; PFVI itself deferred).
- Ritzema, H. et al. (2014). Canal blocking strategies for hydrological restoration of degraded tropical peatlands in Central Kalimantan. *Catena*. [Link](https://luk.tsipil.ugm.ac.id/rawa/PLG/1-s2.0-S0341816213002531-main.pdf) †
- Water table variations on different land use units in a drained tropical peatland island of Indonesia. [Link](https://www.sciencedirect.com/science/article/pii/S1998956326003058) †
- The modelling of groundwater table management for canal blocking scenarios in sub peatland hydrological unit (Central Kalimantan, Freewat/MODFLOW). [Link](https://www.researchgate.net/publication/347296452_The_Modelling_of_Groundwater_Table_Management_for_Canal_Blocking_Scenarios_In_Sub_Peatland_Hydrological_Unit) †
- Modul Pelatihan Pembangunan Infrastruktur Pembasahan Gambut: Sekat Kanal Berbasis Masyarakat (BRG). [Link](https://www.researchgate.net/publication/322520057_Modul_Pelatihan_Pembangunan_Infrastruktur_Pembasahan_Gambut_Sekat_Kanal_Berbasis_Masyarakat) †
- Peraturan Pemerintah No. 57 Tahun 2016 on peatland ecosystem protection and management (0.4 m water table limit).
- Villemonte, J.R. (1947). Submerged-weir discharge studies. *Engineering News-Record* 139, 866–869. (Submergence correction; check against the Urzainki et al. weir form before final use.)
- KLH/BPLH press release SR.130/HUMAS/KLH-BPLH/6/2026, 18 June 2026. [Link](https://kemenlh.go.id/news/detail/jaga-gambut-tetap-basah-menteri-lh-perkuat-sekat-kanal-dan-budaya-ekologis-di-pelalawan)
- ANTARA (Sep 2026). Wamen LH dukung praktik baik kolaborasi tangani karhutla di Jambi. [Link](https://www.antaranews.com/berita/5727171/wamen-lh-dukung-praktik-baik-kolaborasi-tangani-karhutla-di-jambi) †
- Suara Kalbar (1 Oct 2026). PT AER terapkan inovasi perlindungan gambut. [Link](https://ketapang.suarakalbar.co.id/2026/10/pt-aer-terapkan-inovasi-perlindungan.html) †
- Mongabay Indonesia (26 Oct 2024). Nasib sekat kanal gambut di Desa Karya Indah. [Link](https://mongabay.co.id/2024/10/26/nasib-sekat-kanal-gambut-di-desa-karya-indah/) †
- Cahyono, B.K., Aditya, T. and Istarno (2022). The determination of priority areas for the restoration of degraded tropical peatland using hydrological, topographical, and remote sensing approaches. *Land* 11(7), 1094. [Link](https://www.mdpi.com/2073-445X/11/7/1094)
- Taufik, M. et al. (2019). *Geoderma* — critical water table of about 0.85 m for fire danger, South Sumatra; cited via the research report, full text still to be retrieved.
- Ismail et al. (2021). Water table variations and specific yield on Padang Island, Riau. *Hydrology Research* 52(6), 1372–1388. doi 10.2166/nh.2021.062
- Hoyt, A.M. et al. (2020). Widespread subsidence and carbon emissions across Southeast Asian peatlands. *Nature Geoscience* 13, 435–440. doi 10.1038/s41561-020-0575-4
- Hawker, L. et al. (2022). A 30 m global map of elevation with forests and buildings removed (FABDEM). *Environmental Research Letters* 17, 024016.
