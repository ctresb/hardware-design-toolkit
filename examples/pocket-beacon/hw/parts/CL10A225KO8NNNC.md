---
mpn: CL10A225KO8NNNC
aliases: CL10A225KO8NNN#
manufacturer: Samsung Electro-Mechanics
lcsc: C23630
function: U2 CIN (C7, on VBAT) and COUT (C8, charge-pump output up to 9 V) 2.2 uF X5R 16 V
package: 0603 (1608 metric) MLCC
size_max_mm: 1.70x0.90x0.90
supply_range_v: 0-16
io_range_v: -
typ_current_ma: -
peak_current_ma: -
lifecycle: production
lifecycle_distributor: Active
key_specs: c_uf=2.2; v=16; dielectric=X5R; tol=10%; c_eff_3v0_uf=1.47; c_eff_9v0_uf=0.49
distributors: JLCPCB=basic part C23630; LCSC=https://www.lcsc.com/product-detail/C23630.html; DigiKey=https://www.digikey.com/en/products/result?keywords=CL10A225KO8NNNC
price_1: 0.0118
price_10: 0.0118
price_100: 0.0118
price_1k: 0.0089
price_10k: 0.0065
lead_time_wk: 61
stock_snapshot: 2324513 @ JLCPCB 2026-11-08; 163800 @ LCSC 2026-11-08; 50758 @ DigiKey 2026-11-08
alternatives: CL10A225KA8NNNC (drop-in, 25 V, -75.7 % at 9 V, JLC extended C57895); GRM188R61C225KE15D (drop-in, Murata; DC bias not checked)
evidence: verified
source_date: 2026-11-08
notes: As COUT at 7.2-9 V (3x mode) it keeps only 0.49 uF of 2.2 uF (-77.8 % at 9 V); Diodes' application circuit gives 2.2 uF nominal.. suffix ok: Samsung last letter C = 7-inch paper tape
---
# CL10A225KO8NNNC: 2.2 µF X5R 16 V, 0603 (U2 CIN and COUT)

## Identity

- Samsung Electro-Mechanics. Decode: `10` = 0603; `A` = X5R; `225` = 2.2 µF; `K` = ±10 %; `O` = 16 V; `C` = 7-inch cardboard reel.
- Status: "Mass Production" [verified: https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do, 2026-11-08].

## Why this part

Diodes' application circuit for the PAM8904E gives CIN = COUT = 2.2 µF [verified: Diodes DS41667 Rev 4-2, typical application circuit]. VOUT in 3× mode is 7.2 V min to 9 V max [verified: DS41667, VOUT3 row]. The absolute maximum of VOUT is 13.5 V [verified: DS41667 note 6].

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Capacitance | 2.2 µF ±10 % | | [verified: Samsung page] |
| Rated voltage | 16 V | | [verified: Samsung page] |
| DC bias | −4.0 % at 1.0 V; −17.7 % at 2.0 V; −33.2 % at 3.0 V; −37.5 % at 3.3 V; −63.6 % at 6.0 V; −77.8 % at 9.0 V; −79.9 % at 9.9 V | 25 °C | [verified: Samsung DC-bias curve, 2026-11-08] |
| Effective as CIN at 3.0 V | 1.47 µF | | [estimate] |
| Effective as COUT at 9.0 V | 0.49 µF | | [estimate] |

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Length | 1.60 mm ± 0.10 mm | 1.70 mm | [verified: Samsung page] |
| Width | 0.80 mm ± 0.10 mm | 0.90 mm | [verified: Samsung page] |
| Height | 0.80 mm ± 0.10 mm | 0.90 mm | [verified: Samsung page] |

## Checks against the design

- COUT at 9 V is 56 % of the 16 V rating. That is within the rating, but the part keeps only 0.49 µF.
- The piezo load is ≤ 47 nF [verified: DS41667 CLOAD max, via bom.csv]. COUT at 0.49 µF is still 10× the load, so the risk is ripple, not function [estimate].
- A 25 V 0603 does not help: CL10A225KA8NNNC keeps 24.3 % at 9 V [verified: Samsung CL10A225KA8NNN page, 2026-11-08].
- Measure the VOUT ripple on EVT. If needed, use an 0805 25 V part; the data for CL21A225KAQNNN was not readable (HTTP 500).

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Date |
|---|---|---|---|---|---|---|
| JLCPCB (basic) | 0.0118 | 0.0118 | 0.0118 | 0.0089 | 0.0065 | 2026-11-08 |
| LCSC (min 50) | — | — | 0.012 (50) | 0.0090 (500) | 0.0066 (4k) | 2026-11-08 |
| DigiKey | 0.110 | 0.058 | 0.0345 | 0.0193 (4k reel) | 0.0168 (12k) | 2026-11-08 |

## Stock and lead time

| Source | Stock | Lead time | Date |
|---|---|---|---|
| JLCPCB | 2,324,513 | — | 2026-11-08 |
| LCSC | 163,800 | — | 2026-11-08 |
| DigiKey | 50,758 | 61 weeks | 2026-11-08 |

## Risks

| Risk | Rating | Mitigation |
|---|---|---|
| COUT effective 0.49 µF at 9 V | low | measure VOUT ripple and loudness on EVT (verify-on-prototype) |

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| Samsung product page | https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do | 2026-11-08 | read |
| Samsung CL10A225KA8NNN page | https://product.samsungsem.com/mlcc/CL10A225KA8NNN.do | 2026-11-08 | read |
| Samsung CL21A225KAQNNN page | https://product.samsungsem.com/mlcc/CL21A225KAQNNN.do | 2026-11-08 | HTTP 500 |
| Diodes DS41667 | https://www.diodes.com/assets/Datasheets/PAM8904E.pdf | 2026-11-08 | read |
| JLCPCB parts API | JLCPCB parts API (jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) | 2026-11-08 | read |
| DigiKey | https://www.digikey.com/en/products/result?keywords=CL10A225KO8NNNC (via r.jina.ai) | 2026-11-08 | read |
