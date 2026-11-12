# 12 Limitations

- The burned-area maps of 2024 and 2026 are incomplete as delivered (chapter 5), and the method used to make the maps is not documented with them.
- The licence layer of 2025 and the forest area map of 2023 are matched to burns since 2015. Land may have been licensed or reclassified after it burned.
- The licence layer holds the licences it was given. Unlicensed plantations and other managed land count as "no concession".
- Hotspots and burned area inside a licence or a forest area class are a spatial overlap. They do not show the cause of a fire or who is responsible.
- MODIS and VIIRS count fires differently and are never added or compared in absolute numbers. The MODIS file joins two sources at 15 September 2026; over the 15 days where both exist the NASA source has 4.3% more detections.
- The static-source flag misses about a third of the static detections and wrongly flags about one in eight of those it flags (chapter 4).
- A cell or hotspot takes the class at its centre or position. A MODIS pixel is about 1 km across, so a hotspot near a boundary may come from the neighbouring class.
