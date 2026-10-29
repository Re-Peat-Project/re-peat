# Groundwater model: open land beside licences

`python -m repeat_prioritisation.investigations.licence_edge_model --khg <code> ...`. Change in days deeper than 40 cm over June to September 2026 on open land, when licence land is held at 0.4 m against the same run without a managed target (LiDAR canal levels, canals inside cells), by distance to the licence edge (negative inside). Method and per-KHG tables: `licence_edge_model.py`, `_khg/<khg>/04_prioritisation/licence_edge/model_report.md`.

## Change in days deeper than 40 cm (of 122)

| band          |   14.02-04-05.01_kampar_gaung |   15.05-07-10.01_mendahara_batanghari |   16.02.01_sugihan_lumpur |
|:--------------|------------------------------:|--------------------------------------:|--------------------------:|
| < -5 km       |                        nan    |                                nan    |                    nan    |
| -5 to -2 km   |                        nan    |                                  0    |                    nan    |
| -2 to -0.5 km |                        nan    |                                 -0    |                      0.13 |
| -0.5 to 0 km  |                          2.44 |                                  0.14 |                      0.2  |
| 0 to 0.5 km   |                          1.19 |                                  0.57 |                      0.13 |
| 0.5 to 2 km   |                          0    |                                  0    |                      0    |
| 2 to 5 km     |                          0    |                                  0    |                      0    |
| > 5 km        |                          0    |                                  0    |                      0    |

## Baseline days deeper than 40 cm, no managed target

| band          |   14.02-04-05.01_kampar_gaung |   15.05-07-10.01_mendahara_batanghari |   16.02.01_sugihan_lumpur |
|:--------------|------------------------------:|--------------------------------------:|--------------------------:|
| < -5 km       |                         nan   |                                 nan   |                     nan   |
| -5 to -2 km   |                         nan   |                                  39.3 |                     nan   |
| -2 to -0.5 km |                         nan   |                                  34.1 |                      41.4 |
| -0.5 to 0 km  |                          13.9 |                                  31.9 |                      44.1 |
| 0 to 0.5 km   |                           7.5 |                                  34.5 |                      51.1 |
| 0.5 to 2 km   |                           5.6 |                                  34.4 |                      49.8 |
| 2 to 5 km     |                           5.6 |                                  37.9 |                      47.7 |
| > 5 km        |                           5.6 |                                  53   |                      47.6 |

The only link between licence land and open land in the model is groundwater flow between cells and the canal cells; there is no canal routing between them and no outflow control. The managed target is an assumption (`repeat-neraca/docs/reports/concession_levels.md`).
