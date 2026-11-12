# 4 Method

![The analysis: every layer on one 30 m grid; cells and hotspots take the classes where they lie. Source: this analysis.](re-peat/reports/fire_landstatus/figures/fig_method.png)

All layers are laid on one equal-area grid of 30 m cells covering Indonesia, processed in tiles of 90 km. Every cell takes the value of each layer at its centre: its district and province, KHG, forest area class, the licence types it lies in, whether it lies in a DMPG village, whether it is peat, and the years it burned. Cells outside the village boundaries (sea, neighbouring countries and small gaps in the village layer) are left out. Areas are cell counts times the cell area, so overlapping polygons are never counted twice.

Hotspots take the classes of the cell they fall in. The VIIRS archive records a type for each detection (vegetation fire, volcano, static land source such as a gas flare, offshore), and only vegetation fires are kept. The MODIS file and the recent VIIRS file carry no type. A detection of these within 1 km (MODIS) or 375 m (VIIRS) of a VIIRS detection typed as volcano, static land source or offshore in any year is flagged as a likely static source and reported apart. Applied to the typed VIIRS file of 2026, with static locations taken from 2012 to 2025 only, the rule flags static sources with a precision of 0.88 and a recall of 0.67. KLH's own hotspot counts include these sources: with them, MODIS 2026 counts 220,060 medium and high confidence hotspots on land.

Rates are hotspots per 100 km² of the class, so that classes of different size can be compared. VIIRS years are compared over the same calendar window, 1 January to 31 October. Burned area is summed per year; "ever burned" counts a cell once however often it burned.

Every result is checked against an independent total:

- the burned area on the grid differs from the exact polygon area by 0.09% over all years and by at most 0.7% in any year;
- every breakdown (by concession, forest area, DMPG, island, province) adds up to the national total exactly;
- the area of each KHG agrees with an earlier count on a 100 m grid to a median of 0.09%, and the forest area classes inside KHG to within 1.87%;
- 53,236 ha of the 2015 burned area lies east of the border at 141° E, in Papua New Guinea, and 4,517 MODIS and 41,322 VIIRS hotspots lie outside the village boundaries; both are left out.

The licences of 2025 and the forest area of 2023 are matched to every year, so earlier burns may have occurred when the land had another status.
