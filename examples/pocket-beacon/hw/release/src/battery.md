# Battery · Pocket Beacon rev evt0-a

Catalog cell, user-replaceable. No custom cell, no charging circuit.

| Field | Value | Source |
|---|---|---|
| Cell | Panasonic CR2032, lithium manganese dioxide, 3.0 V nominal | bom.csv BAT1 |
| Size | Ø20.0 × 3.2 mm max (IEC CR2032) | bom.csv, F-203 |
| Capacity | 225 mAh nominal at 0.2 mA to 2.0 V; about 165 mAh at 2.7 mA, 20 °C; about 100 mAh at −10 °C [verified: research report 2026-11-08] | power.md §6 |
| Holder | Keystone 3034TR, SMD, 4.1 mm max height, on the PCB back (BT1) | D-018, F-202 |
| Contact | negative: 17.8 mm B.Cu pad under the cell; positive: holder retainer | D-521 |
| Peak load | 15.05 mA ring in 3×; adaptive ring rule below 2.7 V under load | power.md §5, D-028 |
| Bulk buffer | 3 × 22 µF 0603 X5R within 5 mm of U1 | D-022 |
| Battery life | 35 months baseline, 13.1 months calibrated, at a 21.2 µA limit for 12 months | power.md §1 |
| Shipping | the cell ships installed in ship mode (≤ 1.0 µA). Lithium metal cells contained in equipment: UN 3091, PI 970 [estimate: confirm with the forwarder] | compliance.md |
| Warnings | coin-cell warnings on the product door (icon), the packaging and the instructions (16 CFR 1263) | D-704 |

Order the cells from an authorized distributor and ship them to the assembly location, not with the boards.
