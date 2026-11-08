# Z stack-up: Pocket Beacon

Issue: 1 · Date: 2026-11-08 · Owner: enclosure-engineer · Source of geometry: `hw/mech/enclosure.json` → `cad_pocket_beacon.py`

Frame: z = 0 is the outer back face; +Z is the front (button) face. Column through the cell centre (−1.1, −1.1) and through LS1, the tallest front part. All part heights are datasheet **maximum** values.

| # | Layer (back → front) | z from (mm) | z to (mm) | Thickness | Source |
|---|---|---|---|---|---|
| 1 | Door (flange 0.8 + centring plug) | 0.00 | 1.85 | 1.85 | CAD |
| 2 | Gap: door plug → holder | 1.85 | 2.00 | **0.15** | CAD; holder 4.1 max [verified: F-202] |
| 3 | Keystone 3034TR holder (cell inside) | 2.00 | 6.10 | 4.10 max (KiCad model 4.09) | F-202, board GLB |
| 4 | B-side copper + mask | 6.05 | 6.10 | 0.05 | board GLB |
| 5 | PCB, 4-layer FR4 | 6.10 | 6.70 | 0.60 (0.54–0.66) | D-510 |
| 6 | LS1 CPT-9019A | 6.70 | 8.80 | 2.10 max (1.9 ± 0.2) | F-103 |
| 7 | Port gasket (soft foam, compressed) | 8.80 | 9.10 | **0.30** (0.25–0.75 over tolerance) | tolerances.md T-5 |
| 8 | Front wall (PC / PC/ABS) | 9.10 | 10.00 | 0.90 | CAD |
| | **Total** | | | **10.00** | REQ-001 limit 10.0 mm |

The 0.6 mm board (D-510) and the flush, screw-secured door (D-511) are what make the 10.0 mm limit hold with maximum part heights. The bayonet of D-026 needed lugs in the space the holder occupies (D-511).

## Every gap under 0.3 mm

| ID | Gap | Nominal | Worst case | Stack | Status |
|---|---|---|---|---|---|
| T-1 | door plug top → holder bottom | 0.15 (holder 4.1 max) / 0.19 (holder 4.06) | +0.02 | tolerances.md | OK, positive worst case |
| T-2 | SW1 actuator → button nub | 0.20 | +0.07 | tolerances.md | OK after D-513 (nub gap 0.1 → 0.2) |
| T-3 | PCB top → shell standoffs | 0.10 (PCB 0.60) / 0.04 (PCB 0.66) | −0.06 | tolerances.md | crush ribs on the standoff tips (molder detail, `dfm.md` Q-M4) |
| T-4 | door flange → recess ceiling (gasket) | 0.23 | 0.17–0.29 | tolerances.md | gasket compression 3–43 % |
| T-5 | LS1 top → front wall (port gasket) | 0.30 | 0.25–0.75 | tolerances.md | 0.8 mm free soft foam, Q-CD-04 |
| T-6 | cell → negative pad | contact | — | holder spring | by design |
| T-7 | PCB edge → inner wall | 0.80 | 0.65 | plan view | OK |
