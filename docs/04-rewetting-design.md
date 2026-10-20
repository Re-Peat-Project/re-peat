# 04 Rewetting design: routes, canal blocks, gates and pumps

> **Status after the split (2026-10-20).** The method is implemented in the `rewetting-algorithm` repository (`repeat-pump`): stages for sekat siting, routing and pump sizing, with a QGIS plugin. Read its README for what exists; this page is the method statement. It reads `subkhg_priority.csv` (contract C6), which `repeat-prioritisation` now writes.

This part is a documented method with QGIS steps; it is not yet a Python module. It takes a priority unit from `prioritas_khg` and answers: which canals bring water there, where the blocks go, and where pumps are needed.

## The water-sharing idea

Inside a KHG, some compartments hold surplus water (often near the dome top, behind blocks) while others are in deficit (burnt or over-drained areas, especially late in the dry season). The model moves water from surplus to deficit in this order of cost:

1. **Gate operation:** release surplus downhill through a water gate. Almost free.
2. **Repair or build blocks:** hold more water where it falls.
3. **Pumps and pump relays:** import water from a river or lift it uphill past blocks. Costs fuel every day and covers small areas only.
4. **Fire readiness:** where none of the above can keep the water table within 0.4 m (wells, patrols, firebreaks).

This order is the decision tree used to assign a strategy to each compartment.

## Step 0: prepare the inputs

| Input | Preparation |
|---|---|
| Canal network | snap endpoints (5–10 m), split at crossings, remove duplicates; keep real dead ends, only bridge short collinear gaps (mark them low-confidence); classify canals (primary/secondary/tertiary) by width if no class exists |
| Rivers / lakes (RBI) | canal endpoints within ~30 m of water become source nodes; tag dry-season reliability and fresh vs brackish |
| DTM | `dtm_smooth.tif` from `demnas_dtm` |
| Burnt / priority areas | from `prioritas_khg`; mark which canal reaches lie within reach of them (200 m intact, 60 m burnt) |

## Step 1: canal network as a directed graph

Each canal reach becomes an edge with a **gravity direction** and a **confidence score**:

- Sample DTM heights at both ends → `dz`, `slope`.
- Confidence = |dz| ÷ (√2 × DTM error). ≥ 2 clear, 1–2 probable, < 1 ambiguous (common on dome tops).
- Ambiguous reaches: the end closer (along the network) to an outlet is downstream.
- Orient all lines consistently (start = downstream), and check for sinks (nodes with only inflows and no outlet).

Direction describes gravity potential, not actual flow. Once blocks and pumps operate, many reaches become still pools and some flow is deliberately reversed. Take actual flow from models, not from this attribute.

## Step 2: least-cost rewetting route

Cost of travelling along a reach:

```
cost = length × a  +  uphill height gained × b  +  uncertainty penalty
```

- Downhill adds nothing beyond length; uphill means pumping, so b ≫ a.
- Penalty for gap-bridged links, routes through settlements or along roads (blocks get broken there).
- A "super source" connects to all water sources (cost reflecting reliability), optionally including surplus compartments.
- Dijkstra from the super source to each target, in priority order; merge paths into a tree so several targets share trunk canals (approximate Steiner tree).

Build this graph in PyQGIS + networkx: QGIS's own network tools support direction but not asymmetric costs.

## Step 3: block placement along the route

### The pool rule

Behind a block the water surface is flat, but the ground along the pool is not. To keep the water table within 0.4 m of the surface along the whole pool, without flooding the lowest bank:

```
max ground height − min ground height within one pool  ≤  0.4 m − freeboard  ≈  0.3 m
```

Walk along the route's smoothed ground profile; extend the pool until the ground range would exceed 0.3 m, then place a block. Pool water level = lowest bank − freeboard.

**Equal-head points** (*titik beda tinggi seragam*) are the same idea expressed as contours: put a block wherever the smoothed ground drops another 0.3 m. In QGIS: contour the smoothed DTM at 0.3 m and intersect with canals. KLH's current proposals use 0.5 m contours on raw DEMNAS; ours uses the smoothed, corrected surface and the 0.3 m step.

The 2021 study's formula is consistent: spacing *js* = *dA* ÷ land slope, number of blocks = height difference between canal ends ÷ *dA*, block height *ts* = canal depth + *js* × tan(slope) − *dA*, crest from the weir equation Q = Cd × L × H^1.5.

### Classify each block

- **Downhill from the source:** gravity block; water spills over the crest.
- **Uphill from the source:** pump station; lifts water from the lower pool to the upper. Lift = level difference + margin.

### Anchor points (placed without elevation)

Some blocks follow from the network layout and matter more than any contour:

- **canal outlets to rivers or lakes:** the first and most important block;
- **just upstream of junctions**, one per branch;
- **downstream edges of burnt areas** and **boundaries of protected peat**;
- **side branches leaving a route**, which must be closed or the pumped water drains away;
- practical sites near roads, away from settlements and boat routes.

Merge rule: anchors win; an equal-head point within ~100 m of an anchor on the same reach is absorbed into it. Then check spacing (remove points closer than ~150 m, flag gaps over ~1 km).

### Uncertainty

DEMNAS error is comparable to the 0.3 m step even after correction. Rerun placement with realistic DEM noise (Monte Carlo, e.g. GRASS `r.random.surface`) and report each block as a **stretch of canal with a confidence**, not a point. Send low-confidence and pump-site stretches for field levelling (RTK GNSS or survey level along the canal water surface, which is a natural level reference) or drone corridor surveys.

## QGIS workflow (with only DEMNAS)

| Step | QGIS tools | Notes |
|---|---|---|
| 1 Clean canals | Topology Checker; GRASS `v.clean` (break, snap, rmdupl); `Snap geometries to layer` | don't use `rmdangle` |
| 2 Correct DEMNAS | `Warp`, `Reclassify by table`, `Raster calculator`; ICESat-2 via `Create points layer from table`, `Sample raster values`, `Statistics by categories` | or run `demnas_dtm` |
| 3 Canal graph | `Split with lines`, `Extract specific vertices`, `Line intersections` | |
| 4 Dome surface | GRASS `v.surf.bspline` or `r.neighbors` (median, 500–1,000 m) | or `dtm_smooth.tif` |
| 5 Anchors | `Buffer` + `Extract by location` (outlets); `Line intersections` (junctions); `Polygons to lines` + `Line intersections` (burnt and lindung edges) | |
| 6 Equal-head candidates | GDAL `Contour` at 0.3 m on the dome surface → `Line intersections` | |
| 7 Merge and compare with KLH | `Join attributes by nearest` (≤ 100 m, same reach), mutual-nearest pairs, status classes agree / klh_only / model_only / klh_off_canal | |
| 8 Confidence | `r.random.surface` + `Raster calculator`, rerun 4–6, `Split lines by maximum length`, `Join attributes by location (summary)` | Graphical Modeler or PyQGIS loop |

## Pumps

- A standard portable pump moves about 22 m³/h on about 4.9 L/h of fuel; relay-class pumps 70–125 m³/h on 17–22 L/h.
- Dry-season evapotranspiration of 4.1 mm/day over 100 ha is about 4,100 m³/day: roughly 8 portable pumps running day and night just to hold the water table steady.
- Raising the water table 10 cm over 100 ha at Sy = 0.3 needs about 30,000 m³.
- Relays are slow because canal storage fills first: an 11 km relay took 6–7 days (about 1.7 km/day, our inference from news reports).
- **Every pump needs a holding block downstream of its discharge**, or the water drains away within days.
- Conveyance losses are not measured; 10–30% is a placeholder. Water seeping out of a relay canal partly rewets the peat along it.

## Where HEC-RAS fits

HEC-RAS (1D unsteady) is suitable for **checking a designed route**: whether block crests hold the planned pool levels, whether each pump lift works, and how long water takes to travel. It handles looped canal networks, inline weirs (blocks), gates and pump stations with on/off rules.

It does not model water seeping between canals and peat, which is the point of rewetting, so it is a verification tool for one pilot route, not the KHG-wide engine:

| Level | Tool | Purpose |
|---|---|---|
| Whole KHG, weekly | Tier 1 compartment model + allocation (planned, Python) | where water should go |
| Selected routes | HEC-RAS 1D unsteady | do the crests, lifts and travel times work? |
| Canal–peat exchange | Tier 2 groundwater model or MODFLOW with stream routing | how far into the peat water reaches |

Practical notes: canal cross-sections must be assumed (trapezoids from survey or class defaults: primary ~25 × 3 m, secondary ~6 × 1.5 m) because DEMNAS cannot see canal beds; dry-season runs need small time steps and a minimum flow (the 2021 study used 0.01 m³/s). EPA SWMM is a lighter alternative for looped networks with pumps.

## Operations calendar

From the 2021 study, consistent with the model's gate rules:

- **Dry season (June–August, earlier in El Niño years):** close blocks as tightly as possible; start rewetting *before* the drought, not after.
- **Wet season:** near settlements, open gates enough to prevent flooding while keeping canal levels high; elsewhere keep blocks closed.
