# Peat rewetting toolkit: documentation

> **Repository map (2026-10-20).** The code is split into one repository per module; the hub README at the repository root lists them and says how to set up a workstation. This folder keeps the background, the method statements, the plan and the data contracts ([11](11-data-contracts.md)). Pages 02 to 12 were written before the split; each carries a banner where its code lives now.

This folder explains what the RE-PEAT GIS toolkit does, why it is built the way it is, and what every parameter means. It is written for team members who will run, check or extend the code without having followed its development.

## What the toolkit is for

Indonesia's peat fire problem is a water problem: drained peat dries out in the dry season and burns. Government regulation (PP 71/2014 as amended by PP 57/2016) treats cultivation-function peat as damaged when the water table (*tinggi muka air*, TMA) is more than 0.4 m below the surface at a compliance point. Rewetting means holding or bringing back enough water to keep the TMA above that line, using canal blocks (*sekat kanal*), water gates (*pintu air*) and, in emergencies, pumps.

The toolkit helps answer three questions, in order:

1. **Where should we focus?** Which KHG, and which parts of each KHG, are most urgent, most valuable, and most feasible to rewet. (`repeat-prioritisation`)
2. **What ground surface are we working on?** Where no LiDAR exists, the DEM must be corrected and smoothed to the scale of a peat dome; the LiDAR benchmark compares the candidates. (`repeat-dem`)
3. **How do we get water there?** Which canals carry water from a source to the target, and where blocks and pumps go along that route. (`repeat-pump`, method in [04](04-rewetting-design.md))

## How the pieces fit

One chain per KHG, run once per DEM (`tools/khg_pipeline.py`, [19](19-running-the-pipeline.md)):

```
_data ──► 00_inputs (clips of the national layers)
DEM (LiDAR / DeltaDTM / DEMNAS) ──► repeat-dem ──► 01_dem/processed/<dem>/dtm_smooth.tif
        ──► repeat-delineation ──► 02_delineation/<dem>/subkhg_units.gpkg
        ──► repeat-neraca (KHG deficit from SiTMAT; balance per sub-KHG) ──► 03_neraca/
        ──► repeat-prioritisation subkhg ──► 04_prioritisation/<dem>/
        ──► repeat-pump (canal blocks, pumping, report) ──► 05_pump/<dem>/
Nationally: repeat-prioritisation national ranks all 865 KHG ([15](15-national-profile.md)).
```

## Reading guide

| Document | Read it if you want to… |
|---|---|
| [01 Background and concepts](01-background.md) | understand the problem, the terms (KHG, sub-KHG, TMA, water sharing…), the institutional context, and what the literature and our 2021 study taught us |
| [02 DEMNAS to DTM](02-dtm.md) | run or modify the DEM correction (`repeat-dem`); understand every parameter of the vegetation correction, ICESat-2 calibration and smoothing |
| [03 Prioritisation](03-prioritisation.md) | run or modify the delineation and scoring (`repeat-delineation`, `repeat-prioritisation`); understand the two levels, sub-KHG delineation, every indicator, scoring, classes, sensitivity and validation |
| [04 Rewetting design](04-rewetting-design.md) | understand how routes, canal blocks, gates and pumps are placed, the QGIS workflow, and where HEC-RAS fits |
| [05 Parameter register](05-parameters.md) | look up a number: its default, plausible range, source and how confident we are in it |
| [06 Pitfalls, checks and FAQ](06-pitfalls-faq.md) | avoid known mistakes, check results before trusting them, troubleshoot a run |
| [07 DEMNAS literature](07-demnas-literature.md) | see how DEMNAS is built, its published accuracy, and why our fitted canopy factors are so low |
| [09 M0 specification](09-m0-spec.md) | build the package, parameter registry, synthetic testbed and test harness (milestone M0) |
| [08 Build plan](08-build-plan.md) | restructure and build the decision model while the terrain question is open: terrain contract, synthetic testbed, decisions to settle, module map, milestones |
| [10 Neraca air](10-neraca-air.md) | run the physical water balance of a KHG (KHG-level and 2D groundwater), see how it compares with the observed water tables, and what is still missing |
| [11 Data contracts](11-data-contracts.md) | see which files the modules hand to each other (columns, CRS, sign conventions) before changing a module |
| [12 Parked items](12-parked.md) | see what was decided not to do yet and where each item would go |

## Status at a glance (2026-10-28)

| Component | State | Source |
|---|---|---|
| DEM correction (`repeat-dem`) | LiDAR benchmark at two KHG: processed DeltaDTM best (0.64 and 0.47 m error of 1 km height differences), none met the criterion | `reports/dem_benchmark/report.md` |
| Sub-KHG delineation (`repeat-delineation`) | runs per DEM in the chain; outlets are primary and secondary canals and rivers | [17](17-subkhg-delineation-background.md), `pipeline.yaml` |
| Neraca air (`repeat-neraca`) | adopted: climatic balance per sub-KHG and the SiTMAT KHG deficit; the groundwater model for rewetting scenarios is in development | `repeat-neraca/docs/groundwater-model-report.md` |
| Prioritisation (`repeat-prioritisation`) | national ranking of 865 KHG with dashboard; sub-KHG ranking per DEM; weights provisional | [15](15-national-profile.md) |
| Canal blocks and pumping (`repeat-pump`) | 12 stages and QGIS plugin; KLH defaults for block spacing (500 m) and merge distance (100 m) | `repeat-pump/README.md` |
| Full chain | run for Kampar-Gaung, Mendahara-Batanghari and Saleh-Sugihan, all three DEM variants | `python tools/khg_pipeline.py status` |
| Digital twin (`repeat-vis`) | one KHG page (Sugihan-Lumpur) | `repeat-vis/README.md` |

Machine learning and the `peatfr` package / PFVI index are deliberately deferred; see [06](06-pitfalls-faq.md#deferred-components).

## Conventions used everywhere

- **Water table depth** is reported as metres *below* the surface. In files from loggers it is often negative (−0.4 = 40 cm below); the code accepts either and says which in the config.
- **Heights** are in the DEM's vertical datum (DEMNAS: check the metadata; commonly EGM2008). ICESat-2 and GEDI heights are ellipsoidal and are converted before use.
- **Grids** are in the KHG's UTM zone. Units are SI: metres, cubic metres, days; rainfall and ET in mm.
- **Indonesian terms** are kept where they are the working vocabulary (KHG, TMA, sekat kanal, pintu air, fungsi lindung). The [glossary](01-background.md#glossary) translates them.

- [13 Selected KHG](13-selected-khg.md): the 12 main KHG chosen for the project, and reserves.
- [14 Data catalogue](14-data-catalog.md): generated list of the files in `_data`.
- [15 National KHG profile](15-national-profile.md): ranking of all 865 KHG from local data, and how to rerun it.
- [16 Per-KHG data recap](16-khg-data-recap.md): generated; what data each selected KHG has, at what resolution and coverage, and the gaps per module.
- [17 Sub-KHG delineation background](17-subkhg-delineation-background.md): how the Kahayan-Sebangau study and the literature subdivide a KHG, how repeat-delineation compares, and what a water-balance unit still needs.
- [18 Full run plan](18-full-run-plan.md): every selected KHG, once per DEM.
- [19 Running the full chain](19-running-the-pipeline.md): setup, commands and outputs of `tools/khg_pipeline.py`.
