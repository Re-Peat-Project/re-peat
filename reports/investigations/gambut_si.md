# gambut.si TMAT pages: what they hold

Checked 2026-10-29 at https://gambut.si/en/tmat, its sitemap, `llms.txt` and the data sources page (`/en/sumber`).

- Gambut Intelijen (gambut.si, by Gias Oktario) shows water-table points from SiTMAT, read every 3 hours, and announces field surveys by its own team and partners. On 2026-10-29 the sitemap lists 510 points: 85 automatic stations (`KLH-A-MTI-...`) and 425 concession compliance points (`KLH-K-...`). None is a field survey point.
- All 85 automatic stations are in the SiTMAT extract of `repeat-sitmat` (`sitmat_out/processed/stations.csv`, 1,283 stations) under the same ID. All 425 concession points match a SiTMAT concession station once the ID separator is normalised (`152_HMBP-C33` on gambut.si, `<nn>_<company>:<point>` in SiTMAT).
- A point page lists its latest 60 readings (hourly for automatic stations). There is no listing API for the points. The open API serves a national summary (`api.gambut.si/v1/overview`) and a profile per location (`/v1/at?lon=&lat=`). Full data are "for non-commercial research by email request" (`llms.txt`).
- The site also computes a Drought Code and a Keetch-Byram Drought Index per 0.25 degree cell from daily weather and the ECMWF 7-day forecast (data sources page).

Conclusion: the site adds no stations or history beyond what `repeat-sitmat` fetches from SiTMAT directly, so nothing is scraped. Revisit if its own field surveys are published.
