# Sentinel-1: wet to dry change beside licences

`python -m repeat_common.gee_s1 --khg <code> --start 2026-04 --end 2026-09`, then `python -m repeat_prioritisation.investigations.licence_edge_s1 --khg <code>`. VV backscatter (dB, ascending orbit, ESA WorldCover classes on the 200 m licence-edge grid), mean of April-May against July-September 2026, inside one cover class. Value shown: change dry minus wet, 0-2 km outside the licence edge minus 0-2 km inside; positive means backscatter fell less outside. Interval from resampling 5 km blocks.

| KHG                                 | cover   | all                    | foot                   | slope                  | crest                  |
|:------------------------------------|:--------|:-----------------------|:-----------------------|:-----------------------|:-----------------------|
| 14.02-04-05.01_kampar_gaung         | open    | -0.07 (-0.15 to +0.01) | +0.08 (+0.02 to +0.15) | -0.08 (-0.23 to +0.11) | -0.15 (-0.29 to -0.02) |
| 14.02-04-05.01_kampar_gaung         | tree    | +0.11 (+0.06 to +0.16) | +0.07 (+0.03 to +0.11) | +0.11 (+0.03 to +0.22) | +0.16 (+0.07 to +0.26) |
| 14.10.01_pulau_padang               | open    | -0.04 (-0.26 to +0.16) | +0.04 (-0.02 to +0.10) | -0.03 (-0.34 to +0.26) | -0.17 (-0.53 to +0.15) |
| 14.10.01_pulau_padang               | tree    | +0.05 (-0.00 to +0.14) | +0.01 (-0.03 to +0.04) | +0.08 (+0.00 to +0.19) | +0.02 (-0.06 to +0.11) |
| 15.05-07-10.01_mendahara_batanghari | open    | -0.00 (-0.14 to +0.14) | +0.23 (-0.17 to +0.59) | -0.17 (-0.28 to +0.09) | +0.01 (-0.19 to +0.21) |
| 15.05-07-10.01_mendahara_batanghari | tree    | +0.13 (+0.03 to +0.25) | +0.04 (-0.05 to +0.11) | +0.13 (+0.03 to +0.23) | +0.17 (+0.00 to +0.42) |
| 16.02.01_sugihan_lumpur             | open    | +0.21 (-0.01 to +0.46) | +0.02 (-0.20 to +0.26) | +0.39 (+0.07 to +0.76) | -0.62 (-1.22 to +0.13) |
| 16.02.01_sugihan_lumpur             | tree    | +0.03 (-0.05 to +0.11) | -0.06 (-0.13 to -0.01) | -0.06 (-0.15 to +0.03) | +0.31 (+0.04 to +0.46) |

A backscatter change is a moisture signal, not a measured water table. C-band is weak under dense canopy and for a deep water table. Tree and open cover inside and outside a licence can be different kinds of stand (planted, natural, regrowth, harvested): holding the cover class equal does not make the land comparable.
