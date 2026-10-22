# Peat rewetting toolkit: documentation

> **Repository map (2026-10-20).** The code is split into one repository per module; the hub README at the repository root lists them and says how to set up a workstation. This folder keeps the background, the method statements, the plan and the data contracts ([11](11-data-contracts.md)). The module and status names in the tables below are from before the split.

This folder explains what the RE-PEAT GIS toolkit does, why it is built the way it is, and what every parameter means. It is written for team members who will run, check or extend the code without having followed its development.

## What the toolkit is for

Indonesia's peat fire problem is a water problem: drained peat dries out in the dry season and burns. Government regulation (PP 71/2014 as amended by PP 57/2016) treats cultivation-function peat as damaged when the water table (*tinggi muka air*, TMA) is more than 0.4 m below the surface at a compliance point. Rewetting means holding or bringing back enough water to keep the TMA above that line, using canal blocks (*sekat kanal*), water gates (*pintu air*) and, in emergencies, pumps.

The toolkit helps answer three questions, in order:

1. **Where should we focus?** Which KHG, and which parts of each KHG, are most urgent, most valuable, and most feasible to rewet. (`prioritas_khg`)
2. **What ground surface are we working on?** DEMNAS is a radar surface model with unknown, area-dependent canopy content, not the peat surface. Rewetting design needs the ground, corrected and smoothed to the scale of a peat dome; with DEMNAS alone, accuracy is metres, not decimetres. (`demnas_dtm`)
3. **How do we get water there?** Which canals carry water from a source to the target, and where blocks and pumps go along that route. (method documented in [04](04-rewetting-design.md); implemented in QGIS steps for now)

## How the pieces fit

```
DEMNAS ──► demnas_dtm ──► dtm_smooth.tif ─┐
            (vegetation correction,        │
             ICESat-2 calibration,         ├──► prioritas_khg, level 1 (all KHG) ──► khg_terpilih.gpkg
             smoothing)                    │                                              │
                                           │    prioritas_khg, level 2 (selected KHG) ◄───┘
cloud data (Sentinel-2, MODIS, CHIRPS,  ───┘      sub-KHG units, indicators, classes,
TerraClimate, WorldCover, JRC, FIRMS)             blocks needed (metrik IPG)
+ your layers (canals, peat depth, TMA...)                        │
                                                                  ▼
                                              rewetting route + block siting (QGIS / method 04)
                                                                  │
                                                                  ▼
                                              hydraulic check (HEC-RAS, one pilot route)
```

## Reading guide

| Document | Read it if you want to… |
|---|---|
| [01 Background and concepts](01-background.md) | understand the problem, the terms (KHG, sub-KHG, TMA, water sharing…), the institutional context, and what the literature and our 2021 study taught us |
| [02 DEMNAS to DTM](02-dtm.md) | run or modify `demnas_dtm`; understand every parameter of the vegetation correction, ICESat-2 calibration and smoothing |
| [03 Prioritisation](03-prioritisation.md) | run or modify `prioritas_khg`; understand the two levels, sub-KHG delineation, every indicator, scoring, classes, sensitivity and validation |
| [04 Rewetting design](04-rewetting-design.md) | understand how routes, canal blocks, gates and pumps are placed, the QGIS workflow, and where HEC-RAS fits |
| [05 Parameter register](05-parameters.md) | look up a number: its default, plausible range, source and how confident we are in it |
| [06 Pitfalls, checks and FAQ](06-pitfalls-faq.md) | avoid known mistakes, check results before trusting them, troubleshoot a run |
| [07 DEMNAS literature](07-demnas-literature.md) | see how DEMNAS is built, its published accuracy, and why our fitted canopy factors are so low |
| [09 M0 specification](09-m0-spec.md) | build the package, parameter registry, synthetic testbed and test harness (milestone M0) |
| [08 Build plan](08-build-plan.md) | restructure and build the decision model while the terrain question is open: terrain contract, synthetic testbed, decisions to settle, module map, milestones |
| [10 Neraca air](10-neraca-air.md) | run the physical water balance of a KHG (KHG-level and 2D groundwater), see how it compares with the observed water tables, and what is still missing |
| [11 Data contracts](11-data-contracts.md) | see which files the modules hand to each other (columns, CRS, sign conventions) before changing a module |
| [12 Parked items](12-parked.md) | see what was decided not to do yet and where each item would go |

## Status at a glance

| Component | State | Tested on |
|---|---|---|
| `demnas_dtm` vegetation correction + smoothing | working, accuracy limited by DEMNAS | synthetic dome; real DEMNAS at Sebangau, Mendahara, Bengkalis (smoothed RMSE 1.2–2.8 m, not the 0.25 m target) |
| `demnas_dtm` ICESat-2 / GEDI calibration (SlideRule) | working; fitted k far below prior, offsets site-specific | live SlideRule at the same three sites |
| `prioritas_khg` level 1 and level 2 scoring | working | synthetic KHG (1 and 6 KHG) |
| `prioritas_khg` sub-KHG delineation | working | synthetic dome; to be checked against the 16 Kahayan–Sebangau sub-KHG |
| `prioritas_khg` cloud fetchers (Planetary Computer, CHIRPS, FIRMS) | written against documented interfaces | not yet reachable from the build environment |
| Canal network and structures module | missing; keystone for prioritisation, siting and hydrology | not yet coded; first build step in [08](08-build-plan.md) |
| Route and block siting | method + QGIS steps | not yet coded |
| Water-sharing hydrology model (Tier 1/Tier 2) | specified in the methodology document | not yet coded; to be built on a synthetic testbed first ([08](08-build-plan.md)) |
| Physical neraca air (`repeat_neraca`, KHG level and 2D groundwater) | built, no fitted parameters; does not reproduce the held dry-season water tables, see [10](10-neraca-air.md) | real KHG: Sungai Sugihan–Sungai Lumpur, Sungai Kampar–Sungai Gaung (SiTMAT stations) |
| Terrain accuracy for the decision model | open blocker; paused pending airborne LiDAR | see `demnas-corrections/AGENTS.md` and [08](08-build-plan.md) |
| 3D explanatory simulation | published web page | browser |

Machine learning and the `peatfr` package / PFVI index are deliberately deferred; see [06](06-pitfalls-faq.md#deferred-components).

## Conventions used everywhere

- **Water table depth** is reported as metres *below* the surface. In files from loggers it is often negative (−0.4 = 40 cm below); the code accepts either and says which in the config.
- **Heights** are in the DEM's vertical datum (DEMNAS: check the metadata; commonly EGM2008). ICESat-2 and GEDI heights are ellipsoidal and are converted before use.
- **Grids** are in the KHG's UTM zone. Units are SI: metres, cubic metres, days; rainfall and ET in mm.
- **Indonesian terms** are kept where they are the working vocabulary (KHG, TMA, sekat kanal, pintu air, fungsi lindung). The [glossary](01-background.md#glossary) translates them.

- [13 Selected KHG](13-selected-khg.md): the 12 main KHG chosen for the project, and reserves.
- [14 Data catalogue](14-data-catalog.md): generated list of the files in `_data`.
- [15 National KHG profile](15-national-profile.md): ranking of all 865 KHG from local data, and how to rerun it.
