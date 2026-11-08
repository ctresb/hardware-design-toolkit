# DFM check: pocket-beacon

Result: **PASS**, 0 errors, 3 warnings. Automated geometric check; the molder's review is still required.

| Part | Wall min (mm) | Wall max (mm) | Undrafted (mm²) | Undercut (mm²) |
|---|---|---|---|---|
| shell | 0.8 | 25.287 | 134.02 | 0 |
| plate | 0.8 | 24.891 | 237.66 | 0 |
| door | 0.8 | 26.162 | 94.236 | 0 |

## Errors

- none

## Warnings

- shell: 134.02 mm2 of faces with draft under 0.5 deg, near [[11.83, 10.82, 4.63], [12.03, 13.41, 7.32], [10.83, 11.82, 7.32]]
- plate: 237.66 mm2 of faces with draft under 0.5 deg, near [[-8.05, 7.93, 1.79], [-10.11, 12.09, 1.72], [5.99, 8.26, 1.62]]
- door: 94.236 mm2 of faces with draft under 0.5 deg, near [[-8.1, 11.5, 1.23], [-8.1, 10.55, 1.23], [5.9, 11.5, 1.23]]

## Design notes

- keyring slot 2.0 x 5.0 mm, vertical (straight pull, no side action); tube wall 1.0 mm; outer wall 2.14 mm
- door: 2 captive 2x thread-forming screw for plastics, 1.4 x 3 mm, pan head, stainless, captive (retaining washer) at [60, 120] deg, r 14.0 mm; flat gasket 0.3 -> 0.23 mm, set by the ear-to-cap stop; blind pilot holes; all parts release in a straight pull
