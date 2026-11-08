---
mpn: CL05A105KA5NQNC
aliases: CL05A105KA5NQN#
manufacturer: Samsung Electro-Mechanics
lcsc: C52923
function: Recommended U2 flying capacitors 1 uF X5R 25 V (replaces CL05A105KO5NNNC, Q-PB-08)
package: 0402 (1005 metric) MLCC
size_max_mm: 1.10x0.60x0.60
supply_range_v: 0-25
io_range_v: -
typ_current_ma: -
peak_current_ma: -
lifecycle: production
lifecycle_distributor: -
key_specs: c_uf=1; v=25; dielectric=X5R; c_eff_3v3_uf=0.73; c_eff_6v6_uf=0.43
distributors: JLCPCB=basic part C52923; LCSC=https://www.lcsc.com/product-detail/C52923.html
price_1: 0.0058
price_10: 0.0058
price_100: 0.0058
price_1k: 0.0044
price_10k: 0.0034
lead_time_wk: -
stock_snapshot: 11550069 @ JLCPCB 2026-11-08; 3163100 @ LCSC 2026-11-08
alternatives: CL05A105KO5NNNC (drop-in, 16 V, half the effective capacitance at 6.6 V); CL10A105KB8NNNC (needs change: 0603, 50 V)
evidence: verified
source_date: 2026-11-08
notes: Not yet in the BOM MPN column (only its LCSC number is): specs-engineer decides Q-PB-08.. suffix ok: Samsung last letter C = 7-inch paper tape
---
# CL05A105KA5NQNC: 1 µF X5R 25 V, 0402 (recommended for C9 and C10)

The full comparison, with sources, is in `CL05A105KO5NNNC.md`.

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Capacitance | 1 µF ±10 % | | [verified: LCSC product API, 2026-11-08] |
| Rated voltage | 25 V | | [verified: Samsung page, 2026-11-08] |
| DC bias | −27.1 % at 3.3 V; −57.2 % at 6.6 V | 25 °C | [verified: Samsung DC-bias curve, 2026-11-08] |
| Dimensions | 1.00 mm ± 0.10 mm each side, so 1.10 × 0.60 × 0.60 mm max | | [verified: https://product.samsungsem.com/mlcc/CL05A105KA5NQN.do, 2026-11-08] |
| Status | Mass Production | | [verified: Samsung page] |

## Price and stock

| Source | 1 | 1k | 10k | Stock | Date |
|---|---|---|---|---|---|
| JLCPCB (basic) | 0.0058 | 0.0044 | 0.0034 | 11,550,069 | 2026-11-08 |
| LCSC (min 100) | — | 0.0045 | 0.0034 | 3,163,100 | 2026-11-08 |

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| Samsung product page | https://product.samsungsem.com/mlcc/CL05A105KA5NQN.do | 2026-11-08 | read |
| JLCPCB parts API | JLCPCB parts API (jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) | 2026-11-08 | read |
| LCSC product API | LCSC product API (wmsc.lcsc.com/ftps/wm/product/detail?productCode=C52923) | 2026-11-08 | read |
