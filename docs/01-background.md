# 01 Background and concepts

## The problem in one paragraph

Tropical peat is a dome of partly decomposed plant material, highest in the middle and sloping gently (a few metres over several kilometres) towards the rivers that bound it. When intact, it stays waterlogged year-round. Drainage canals, dug for plantations, agriculture, transport or logging, pull the water table down, most strongly near the canals. In the dry season, rain stops but evapotranspiration continues at about 4 mm per day, the water table falls further, and the dry upper peat can burn, sometimes for weeks underground. Fires recur where drainage and drought coincide. Rewetting tries to keep the water table high enough, through the dry season, that the peat does not reach that state.

## Glossary

| Term | Meaning |
|---|---|
| **KHG** (*Kesatuan Hidrologis Gambut*) | Peat hydrological unit: a peat area bounded by rivers or the sea that behaves as one water system. The official planning unit (PHU in English literature). |
| **Sub-KHG** | A subdivision of a KHG draining to its own outlet channel (a smaller river or major canal). Our main analysis unit inside a KHG. |
| **Kubah gambut** | Peat dome: the high central part of a KHG; water flows outward from it. |
| **TMA** (*tinggi muka air*) | Water table level in the peat. Reported here as depth below the surface. |
| **Titik penaatan** | Compliance point where the TMA is measured against the 0.4 m standard (Permen LHK P.15/2017). |
| **Fungsi lindung / budidaya** | Protected-function / cultivation-function peat ecosystem zones. Peat ≥ 3 m deep is protected. |
| **Sekat kanal** | Canal block: a small dam that holds water in a canal and stops it draining the peat. |
| **Pintu air** | Water gate: a block whose opening can be adjusted. |
| **Sumur bor** | Deep well, mainly for firefighting water. |
| **Embung** | Small storage pond. |
| **Water sharing** | Moving surplus water held in one compartment (often near the dome top, behind blocks) to compartments in deficit, via gates or pumps. The core idea of the model. |
| **Specific yield (Sy)** | The fraction of peat volume that drains when the water table falls. Not the same as total water content (see the [pitfall](06-pitfalls-faq.md#water-table-decline-is-not-water-loss)). |
| **Neraca air** | Water balance: inputs (rain) minus outputs (evapotranspiration, runoff, drainage). |
| **dNBR** | Difference in Normalised Burn Ratio between before and after a fire; used to map burned area and severity. |
| **NDMI** | Normalised Difference Moisture Index from near- and shortwave-infrared bands; lower means drier vegetation and surface. |
| **IPG** (*infrastruktur pembasahan gambut*) | Peat rewetting infrastructure: blocks, wells, ponds. **Metrik IPG** = existing blocks ÷ blocks needed. |
| **SiPALAGA** | The water-table and rainfall logger network built by BRG/BRGM. |
| **DSM / DTM** | Digital surface model (includes trees and buildings) / digital terrain model (bare ground). DEMNAS is a radar DSM blended toward stereo mass points: canopy content varies by area and is not reliably removed ([07](07-demnas-literature.md)). |

## Policy and institutions (as of October 2026)

- **Standard.** PP 71/2014 jo. PP 57/2016: cultivation peat is damaged if the TMA is more than 0.4 m below the surface at a titik penaatan. Permen LHK P.15/2017 sets how TMA is measured; concessions report through SIMPEL/PROPER. A conflicting agricultural standard (Permentan 14/2009) allows 0.6–0.8 m for oil palm.
- **BRG → BRGM → ended.** The peat restoration agency's mandate ended on 31 December 2024; its functions moved to ministries. Who now hosts SiPALAGA and PRIMS data is not publicly documented.
- **KLH/BPLH.** Runs 2026 dry-season operations, monitors TMA and hotspots, applies water sharing in priority areas, and pushes concessions to block canals. In 2026 it named Pelalawan (Riau), Kubu Raya (West Kalimantan) and South Sumatra as focus areas, with six provinces on alert.
- **BPGMN.** On 24 September 2026 the President decided to create a National Peat and Mangrove Management Agency; the Perpres was being drafted in early October. Its prioritisation method is not yet defined, which is an opening for a transparent, tested method like ours.
- **What is missing publicly.** Prioritisation is visible at province, district and KHG level, driven by current alerts. No published method ranks areas *inside* a KHG by hydrology, feasibility and cost. That is the gap this toolkit fills.

## What the literature told us

These are the findings that shaped the code's defaults. Full numbers and sources are in the [parameter register](05-parameters.md).

1. **Canal influence is narrow.** Field transects find canal blocks raise the water table within roughly 170–240 m of the canal on intact peat; a 200 m reach needs a canal rise of more than about 0.6 m. On recently burnt peat the response is much weaker: in Limbung (West Kalimantan) the water table responded fastest at 20 m and the response fell sharply from 70 m. Modelling in Sumatra found block effects relevant to about 600 m and negligible beyond 1 km. **Default reach: 200 m on intact peat, 60 m on burnt peat** (both adjustable).
2. **Large, dense blocking works.** A 4,800 ha trial with 257 compacted peat dams raised the water table from about −0.6 m to −0.3 m and halved subsidence over 7.5 years. Few, scattered blocks raise landscape water tables only by centimetres.
3. **Fire thresholds.** High fire danger appears mostly below 0.4 m, burned area only below 0.6 m, and danger levels off near 0.85 m. These are our hazard bands.
4. **Evapotranspiration** of degraded and burnt peat is only modestly lower than forest: about 3.8–4.1 mm/day versus 4.5 mm/day.
5. **Specific yield** is about 0.3 near the surface, falling to about 0.1 at 1.5 m depth.
6. **Subsidence** averages about 2.2 cm per year across drained Southeast Asian peat and reaches 4–5 cm per year under plantation drainage. DEMs therefore go out of date.
7. **Blocks decay.** NGO inspections found 70% of 77 blocks damaged (mostly wood and bamboo); wooden poles last roughly 3–5 years. Block condition should be treated as something that declines over time.
8. **Pumps are small.** A standard portable fire pump moves about 22 m³/h on about 4.9 L of fuel per hour; it can offset dry-season evapotranspiration on only about 13 ha. Pumps suit small, high-risk areas, not whole KHGs. Reported relays (9–11 km in Jambi and Ketapang, 2026) took days to deliver water.

## What our 2021 Kahayan–Sebangau study taught us

The team's earlier final report on KHG Sungai Kahayan – Sungai Sebangau is the direct ancestor of this toolkit. What we kept, improved, and dropped:

**Kept and automated**
- **Sub-KHG delineation** from flow direction, flow accumulation and Strahler stream order, with high-order channels (order 7 there) as outlets. It produced 16 sub-KHG. Field checks confirmed modelled flow directions and showed boundaries are the wide outlet canals. Now automated in `delineate.py`.
- **Water balance** ΔS = R(1 − C) − ET with land-cover interception (0% open land to 16.4% forest) and a runoff coefficient of 0.07–0.18 measured on Pulau Padang. Now the `u_wb_mean` and `u_deficit_months` indicators.
- **Both average balance and deficit frequency matter.** The worst sub-KHG by mean balance (2, 4, 8) were not the worst by number of deficit months (16, 14, 12, 11). We keep both indicators.
- **Dry-day water-table decline** from SiPALAGA: 16.4 mm/day (shrub near tidal area), 17.8 (shrub/rice), 23.4 (rice far from tides). Now `u_tma_recession`, and a calibration check for the hydrology model.
- **Metrik IPG**: block spacing from the design water-table limit (0.4 m) divided by land slope, blocks needed from canal length, and the ratio of existing to needed blocks. Now `u_ipg_gap` and `kebutuhan_sekat.csv`.
- **Typical canal dimensions**: primary about 25 m wide × 3 m deep; secondary about 6 m × 1.5 m.
- **Operational rules**: close blocks June–August; in the wet season, open them near settlements to avoid flooding but keep canal levels high elsewhere.
- **Land management**: mining concessions (IUP) are excluded from restoration priority; plantation concessions change hydrology and carry their own responsibility.
- **Tidal areas** rarely dry out and need separate treatment.

**Improved**
- **Single-date images → seasonal composites.** The 2021 study used one Landsat scene per year from different seasons (June 2018, May 2019, January 2020), so NDMI changes mixed season with trend; rain on the acquisition day also shifted values. We use dry-season median composites with cloud masking.
- **Average of ranks → normalised, weighted scores** with sensitivity analysis and validation on held-out years.

**Dropped (errors to avoid)**
- **Treating water-table decline as water volume.** The study multiplied the mean daily decline by the whole KHG area as if every centimetre of decline were a centimetre of water lost (equivalent to Sy = 1), then concluded the water would "run out in 108 days". See the [pitfall](06-pitfalls-faq.md#water-table-decline-is-not-water-loss). The often-quoted "27 cm drop in 14 days" is 14 × 19.2 mm, the average of three stations; it is a reasonable decline check, not a volume.
- **Canal emptying time of 730–770 days**, which assumed canals lose water only by open-water evaporation. The authors already called it unrealistic: canals mainly lose water by seepage into the peat.

## The two levels of prioritisation

Prioritisation happens at two scales because each needs different data:

| | Level 1: national screening | Level 2: detailed |
|---|---|---|
| Question | Which KHG should we work on? | Inside those KHG, where and with what? |
| Unit | one per KHG | sub-KHG (automatic), hexagons, or your polygons |
| Data rule | only layers that exist evenly everywhere | everything available, including DTM, canals, blocks, loggers |
| Grid | 250 m | 30 m |
| Output | `khg_terpilih.gpkg` | classes, ranking, blocks needed |

Detailed layers (good DTMs, canal inventories, loggers) are uneven across Indonesia. Using them at level 1 would reward well-mapped KHGs rather than needy ones, so level 1 sticks to coarse, comparable data.
