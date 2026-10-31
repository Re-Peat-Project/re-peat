# KLH hotspots against FIRMS MODIS NRT

KLH: 167,718 detections in the file, 63,100 with a date (2026-01-01 to 2026-09-15; the other months carry no date). FIRMS MODIS NRT: 2026-09-01 to 2026-10-30, 99,383 detections (the API serves about two months, so the two overlap from 2026-09-01 to 2026-09-15 only, 15 days).

KLH confidence classes against the numeric confidence cut at 30 and 80: 1.0000 of rows agree (low < 30, medium 30-79, high >= 80).

Over the overlap FIRMS has 27,877 detections and KLH 26,726 (FIRMS / KLH 1.043; daily ratio from 1.005 to 1.196). Points found in both (same satellite, date, time, position within 0.01 degree): 25,642, 100.0% of KLH and 95.8% of FIRMS points.

## By class, overlap

| class | KLH | FIRMS |
|---|---|---|
| high | 9,364 | 9,602 |
| low | 1,523 | 1,637 |
| medium | 15,839 | 16,638 |

## Per day, overlap

| date | KLH | FIRMS | FIRMS / KLH |
|---|---|---|---|
| 2026-09-01 | 3,776.0 | 3,796.0 | 1.005 |
| 2026-09-02 | 990.0 | 1,001.0 | 1.011 |
| 2026-09-03 | 2,249.0 | 2,387.0 | 1.061 |
| 2026-09-04 | 1,215.0 | 1,240.0 | 1.021 |
| 2026-09-05 | 1,369.0 | 1,429.0 | 1.044 |
| 2026-09-06 | 1,722.0 | 1,861.0 | 1.081 |
| 2026-09-07 | 767.0 | 811.0 | 1.057 |
| 2026-09-08 | 1,288.0 | 1,427.0 | 1.108 |
| 2026-09-09 | 1,041.0 | 1,085.0 | 1.042 |
| 2026-09-10 | 1,055.0 | 1,262.0 | 1.196 |
| 2026-09-11 | 3,418.0 | 3,627.0 | 1.061 |
| 2026-09-12 | 874.0 | 902.0 | 1.032 |
| 2026-09-13 | 2,280.0 | 2,303.0 | 1.010 |
| 2026-09-14 | 2,472.0 | 2,506.0 | 1.014 |
| 2026-09-15 | 2,210.0 | 2,240.0 | 1.014 |
