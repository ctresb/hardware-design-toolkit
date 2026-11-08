---
mpn: TPD1E10B06DPYR
aliases: TPD1E10B06DPYT; TPD1E10B06DPYRG4
manufacturer: Texas Instruments
lcsc: C48260
function: Bidirectional ESD/TVS diode on the exposed battery contacts (VBAT)
package: X1SON (DPY) 2-pin, 1.0 x 0.6 mm
size_max_mm: 1.1x0.7x0.45
supply_range_v: 0-5.5
io_range_v: -
typ_current_ma: 0
peak_current_ma: 0
lifecycle: production
lifecycle_distributor: Active
key_specs: VRWM 5.5 V; IEC 61000-4-2 +/-30 kV contact and air; ILEAK 100 nA max at 5 V; C 12 pF typ
distributors: DigiKey=https://www.digikey.com/en/products/detail/texas-instruments/TPD1E10B06DPYR/3197744; LCSC=https://www.lcsc.com/product-detail/C48260.html
price_1: 0.41
price_10: 0.251
price_100: 0.1576
price_1k: 0.11692
price_10k: 0.07317
lead_time_wk: 26
stock_snapshot: 86161 @ DigiKey 2026-11-08; 295520 @ LCSC 2026-11-08 (C48260, TI brand)
alternatives: TPD1E10B06DYAR (needs change: SOD-523, 0.77 mm max height); ESD9B5.0ST5G (needs change: not checked)
evidence: verified
source_date: 2026-11-08
notes: LCSC sells the TI part far below DigiKey (USD 0.0268 at 10k); TECH PUBLIC and Leiditech look-alike listings exist under the same MPN: select C48260 only
---

# TPD1E10B06DPYR: ESD protection for the battery contacts (TI)

## Identity

- Manufacturer: Texas Instruments. Datasheet SLLSEB1G, February 2012, revised August 2024 [verified: ti.com/lit/ds/symlink/tpd1e10b06.pdf, 2026-11-08].
- Orderable: `TPD1E10B06DPYR` (10,000 per reel), `TPD1E10B06DPYT` (250 per reel), `…DPYRG4`. All Active, Level-1-260C, NIPDAU, −40 °C to 125 °C [verified: package option addendum].

## Why this part

The battery contacts are touched by the user every time the cell is changed. VBAT needs IEC 61000-4-2 protection without a leakage current that eats the 12-month budget.

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| VRWM | 5.5 V | either direction | [verified: SLLSEB1G §5] |
| ILEAK | 100 nA max | pin 1 = 5 V | [verified] |
| CIO | 12 pF typ | VIO = 2.5 V, 1 MHz | [verified] |
| IEC 61000-4-2 | ±30 kV contact, ±30 kV air | — | [verified] |
| IEC 61000-4-5 | 6 A, 90 W (8/20 µs) | — | [verified] |
| Clamp | 10 V max at IPP = 1 A | — | [verified] |

## Package and dimensions

| | Min | Maximum | Source |
|---|---|---|---|
| Length | 0.9 | 1.1 mm | [verified: DPY0002A drawing] |
| Width | 0.5 | 0.7 mm | [verified] |
| Height | — | 0.45 mm | [verified: "X1SON - 0.45 mm max height"] |

## Power

Leakage ≤ 100 nA at 5 V, lower at 3 V [estimate]. Worst case ≈ 0.9 mAh per year, 0.4% of a 225 mAh cell [estimate].

## Lifecycle

| Source | Status | Date |
|---|---|---|
| Manufacturer (TI package addendum) | Active, Production | 2026-11-08 |
| DigiKey | Active | 2026-11-08 |

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Packaging | Date |
|---|---|---|---|---|---|---|---|
| DigiKey | 0.41 | 0.251 | 0.1576 | 0.11692 (500 break) | 0.07317 | CT; TR 10k | 2026-11-08 |
| LCSC C48260 | 0.0451 (20+) | 0.0451 | 0.0367 (200+) | 0.0292 (2k) | 0.0268 | reel 10k | 2026-11-08 |

## Stock and lead time

| Source | Authorized stock | Factory lead time | Limits / notes | Date |
|---|---|---|---|---|
| DigiKey | 86,161 | 26 weeks | — | 2026-11-08 |
| LCSC / JLCPCB C48260 | 295,520 / 298,469 | — | TI brand, Extended | 2026-11-08 |

## Checks against the design

- Rail VBAT 2.0–3.3 V inside 0–5.5 V working range: yes.
- Package: X1SON 1.0 × 0.6 mm (0402 class) placeable at JLCPCB: yes.

## Risks

| Risk | Rating | Mitigation |
|---|---|---|
| Look-alike listings (TECH PUBLIC C2937015, Leiditech C2972450) | low | choose C48260 by LCSC number |

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| TI datasheet SLLSEB1G | https://www.ti.com/lit/ds/symlink/tpd1e10b06.pdf | 2026-11-08 | read |
| DigiKey product page | https://www.digikey.com/en/products/detail/texas-instruments/TPD1E10B06DPYR/3197744 | 2026-11-08 | read |
| LCSC API C48260, JLCPCB search API | wmsc.lcsc.com, jlcpcb.com | 2026-11-08 | read |
