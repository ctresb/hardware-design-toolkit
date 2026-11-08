---
mpn: CL10A106KP8NNNC
aliases: CL10A106KP8NNN#
manufacturer: Samsung Electro-Mechanics
lcsc: C19702
function: 10 uF X5R 10 V: VDDS input (C3) and VDDR DC/DC output (C4) of U1
package: 0603 (1608 metric) MLCC
size_max_mm: 1.70x0.90x0.90
supply_range_v: 0-10
io_range_v: -
typ_current_ma: -
peak_current_ma: -
lifecycle: production
lifecycle_distributor: Active
key_specs: c_uf=10; v=10; dielectric=X5R; tol=10%; c_eff_3v0_uf=4.9
distributors: JLCPCB=basic part C19702; LCSC=https://www.lcsc.com/product-detail/C19702.html; DigiKey=https://www.digikey.com/en/products/result?keywords=CL10A106KP8NNNC
price_1: 0.0203
price_10: 0.0203
price_100: 0.0203
price_1k: 0.0134
price_10k: 0.0111
lead_time_wk: 61
stock_snapshot: 10304806 @ JLCPCB 2026-11-08; 1457860 @ LCSC 2026-11-08; 0 @ DigiKey 2026-11-08
alternatives: GRM188Z71A106KA73D (drop-in, X7R 10 V, used on TI LP-EM-CC2340R53 as C104/C105; DC bias not checked); CL21A106KOQNNNE (needs change: 0805, 7.3 uF at 3.0 V)
evidence: verified
source_date: 2026-11-08
notes: TI requires 10 uF on VDDS for coin cells and 10 uF on VDDR; at 3.0 V this part keeps 4.9 uF. On VDDS the bulk caps C1/C2 add to it; on VDDR it sees the DC/DC output voltage, not VBAT.. suffix ok: Samsung last letter C = 7-inch paper tape
---
# CL10A106KP8NNNC: 10 µF X5R 10 V, 0603 (C3 VDDS, C4 VDDR)

## Identity

- Manufacturer: Samsung Electro-Mechanics. The suffix `C` = cardboard, 7-inch reel, as in the package-code table of the family [verified: https://product.samsungsem.com/mlcc/CL10A226MQ8NRN.do, 2026-11-08].
- Decode: `10` = 0603; `A` = X5R; `106` = 10 µF; `K` = ±10 %; `P` = 10 V.
- Status: "Mass Production" [verified: https://product.samsungsem.com/mlcc/CL10A106KP8NNN.do, 2026-11-08].

## Why this part

- **VDDS (C3):** "For small coin-cell batteries, with high worst-case end-of-life equivalent source resistance, a 10µF VDDS input capacitor must be used to ensure compliance with this slew rate" [verified: TI SWRS272F rev F, §7.3 note 3].
- **VDDR (C4):** "A 10µH and 10µF load capacitor are required on the VDDR voltage rail. They must be placed close to the DCDC output pin" [verified: SWRS272F §7.4 note 2].
- **TI reference:** the LaunchPad LP-EM-CC2340R53 (MCU143A BOM) uses Murata GRM188Z71A106KA73D, 10 µF X7R 10 V 0603, for C104 and C105 [verified: TI SWRC397 design files, MCU143A_BOM.xlsx, 2026-11-08].

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Capacitance | 10 µF ±10 % | 0 V | [verified: Samsung page] |
| Rated voltage | 10 V | | [verified: Samsung page] |
| DC bias | −10.9 % at 1.0 V; −28.5 % at 1.78 V; −33.0 % at 2.0 V; −42.5 % at 2.5 V; −51.2 % at 3.0 V; −55.7 % at 3.3 V | 25 °C | [verified: Samsung embedded DC-bias curve, 2026-11-08] |
| Effective at 3.0 V (C3 on VDDS) | 4.9 µF | | [estimate: 10 µF × 0.488] |
| Effective at 1.5 V (C4 on VDDR) | about 7.8 µF | VDDR voltage not read from TI | [estimate: interpolation of the curve; VDDR level is an assumption] |

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Length | 1.60 mm ± 0.10 mm | 1.70 mm | [verified: Samsung page] |
| Width | 0.80 mm ± 0.10 mm | 0.90 mm | [verified: Samsung page] |
| Height | 0.80 mm ± 0.10 mm | 0.90 mm | [verified: Samsung page] |

## Checks against the design

- On VBAT (C3), 3.3 V is 33 % of the 10 V rating. VDDS capacitance comes mainly from C1, C2 and the proposed C15. TI's "10 µF" is a nominal value; TI's own reference design uses a 0603 part with similar DC-bias loss.
- Keep C4 within 1 mm of the DCDC pin, as SWRS272F §7.4 requires (for pcb-engineer).

## Lifecycle

| Source | Status | Date |
|---|---|---|
| Samsung | Mass Production | 2026-11-08 |
| DigiKey | Active, 0 in stock, manufacturer lead time 61 weeks, limit 100,000 per 30 days | 2026-11-08 |

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Packaging | Date |
|---|---|---|---|---|---|---|---|
| JLCPCB assembly (basic) | 0.0203 | 0.0203 | 0.0203 | 0.0134 | 0.0111 | JLC stock | 2026-11-08 |
| LCSC (min 20) | — | 0.0205 (20) | 0.0157 (200) | 0.0135 | 0.0112 (8k) | 7-inch reel 4000 | 2026-11-08 |
| DigiKey | 0.200 | 0.113 | 0.0705 | 0.0407 (4k reel) | 0.0363 (12k) | cut tape / T&R | 2026-11-08 |

## Stock and lead time

| Source | Stock | Lead time | Notes | Date |
|---|---|---|---|---|
| JLCPCB | 10,304,806 | — | basic | 2026-11-08 |
| LCSC | 1,457,860 | — | | 2026-11-08 |
| DigiKey | 0 | 61 weeks | backorder | 2026-11-08 |

## Alternatives

| MPN | Class | Difference | Price at 1k | Source |
|---|---|---|---|---|
| GRM188Z71A106KA73D | drop-in | X7R; TI LaunchPad part | — | [verified: TI MCU143A BOM] |
| CL21A106KOQNNNE | needs change: 0805 | 16 V; −26.9 % at 3.0 V | — | [verified: Samsung CL21A106KOQNNN page, 2026-11-08] |

## Conflicts between sources

| Field | A | B | Decision |
|---|---|---|---|
| size_max_mm | 1.7 × 0.9 × 0.9 (BOM) | 1.70 × 0.90 × 0.90 (Samsung) | same |

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| Samsung product page | https://product.samsungsem.com/mlcc/CL10A106KP8NNN.do | 2026-11-08 | read |
| TI SWRS272F | https://www.ti.com/lit/ds/symlink/cc2340r5.pdf | 2026-11-08 | read |
| TI LaunchPad design files | https://www.ti.com/lit/zip/SWRC397 | 2026-11-08 | read (MCU143A BOM) |
| JLCPCB parts API | JLCPCB parts API (jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) | 2026-11-08 | read |
| LCSC product API | LCSC product API (wmsc.lcsc.com/ftps/wm/product/detail?productCode=C19702) | 2026-11-08 | read |
| DigiKey | https://www.digikey.com/en/products/result?keywords=CL10A106KP8NNNC (via r.jina.ai) | 2026-11-08 | read |
