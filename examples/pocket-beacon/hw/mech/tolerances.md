# Tolerance stack-ups: Pocket Beacon

Issue: 1 · Date: 2026-11-08 · Owner: enclosure-engineer · Method: `skills/enclosure-engineer/references/tolerances.md` (worst case and RSS, one line per contributor)

Molded-part tolerances are planning values for small PC and PC/ABS parts, ISO 20457 / DIN 16742 fine grade [estimate: ±0.05 mm on features under 10 mm; confirm with the molder, `dfm.md` Q-M1]. PCB thickness ±10 % [assumption: JLCPCB standard; F-510].

## T-1 Door plug → holder bottom (must stay > 0)

| Contributor | Nominal (mm) | ± (mm) |
|---|---|---|
| Plate post height (sets the PCB bottom) | 4.20 above the plate top | 0.05 |
| Holder height, 3034TR | 4.10 max (4.06 typical) | max used |
| Door plug height above the seat | 1.85 | 0.05 |
| Door seat: ear-to-cap stop | 0 | 0.03 |
| **Gap** | **0.15** | WC 0.13 · RSS 0.077 |

Worst case +0.02 mm, RSS +0.07 mm. A nominal holder (4.06 mm) adds 0.04 mm. **OK.**

## T-2 SW1 actuator → button nub (must stay > 0, so the switch is never pre-pressed)

| Contributor | Nominal | ± |
|---|---|---|
| PCB thickness | 0.60 | 0.06 |
| SW1 height, KMR221G (2.0 max used as nominal) | 2.00 | +0 / −0.10 |
| Shell ceiling height | 9.10 | 0.05 |
| Nub length | 0.20 gap | 0.05 |
| Plate post height | — | 0.05 |
| Adhesive ring | 0.10 | 0.02 |
| **Gap** | **0.20** | WC 0.23 · RSS 0.11 |

Worst case −0.03 mm with every part at its limit. With SW1 at its maximum, which is the only side that closes the gap, the worst case is +0.07 mm. RSS +0.09 mm. **OK after D-513.** The first CAD issue (0.10 mm) failed this stack.

## T-3 PCB top → shell standoffs

Nominal 0.10 mm on a 0.60 mm board. Contributors: PCB ±0.06, shell ±0.05, plate posts ±0.05. Range −0.06 to +0.26 mm. Three 0.15 mm crush ribs on each standoff tip take up the range. The board is clamped without a rattle gap. The ribs are a molder detail; they are not modelled.

## T-4 Door gasket compression

Gap 0.23 mm nominal. Contributors: recess depth ±0.03, flange thickness ±0.03. Range 0.17–0.29 mm. Silicone 40A, 0.30 mm free: compression 3–43 %. The low end (3 %) is too light for IP67. **Action:** order the gasket at 0.35 mm free, 17–51 %, or hold the recess at ±0.02 (Q-CD-03).

## T-5 Sounder port gasket

LS1 height 1.9 ± 0.2 mm [verified: datasheet p.1, general tolerance], PCB ±0.06, ceiling ±0.05: the gap ranges 0.25–0.75 mm. A 0.30 mm solid gasket cannot seal 0.75 mm. **Decision D-514:** a die-cut ring of soft open-cell foam with closed skin and PSA, 0.8 mm free (compressed 6–69 %) [estimate: e.g. polyurethane foams of the Poron family; confirm grade with the vendor, Q-CD-04]. The CAD shows it compressed to the nominal gap.

## T-6 Antenna clearance to cell metal (plan view)

Cell edge (r 10.0 around (−1.1, −1.1)) to the antenna copper-keep-out corner (−6.0, −10.9): **0.96 mm** [verified: geometry F-512]. Target ≥ 1 mm was an assumption (constraints.md §5). Tune on EVT with a VNA (V-005).
