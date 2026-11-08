---
mpn: CL05B104KO5NNNC
aliases: CL05B104KO5NNN#
manufacturer: Samsung Electro-Mechanics
lcsc: C1525
function: 100 nF X7R 16 V pin decoupling
package: 0402 (1005 metric) MLCC
size_max_mm: 1.05x0.55x0.55
supply_range_v: 0-16
io_range_v: -
typ_current_ma: -
peak_current_ma: -
lifecycle: production
lifecycle_distributor: -
key_specs: c_nf=100; v=16; dielectric=X7R; tol=10%; c_eff_3v0_nf=97
distributors: JLCPCB=basic part C1525; LCSC=https://www.lcsc.com/product-detail/C1525.html
price_1: 0.0031
price_10: 0.0031
price_100: 0.0031
price_1k: 0.0023
price_10k: 0.0017
lead_time_wk: -
stock_snapshot: 34285467 @ JLCPCB 2026-11-08; 3539900 @ LCSC 2026-11-08
alternatives: GRM155R71C104KA88D (drop-in, Murata); CL05A104KA5NNNC (drop-in, X5R 25 V)
evidence: verified
source_date: 2026-11-08
notes: DC bias negligible (-3.2 % at 3.0 V). TI's reference uses 0201 0.1 uF; count per pin from the LaunchPad schematic (pcb-engineer).. suffix ok: Samsung last letter C = 7-inch paper tape
---
# CL05B104KO5NNNC: 100 nF X7R 16 V, 0402

## Identity

- Samsung Electro-Mechanics. Decode: `05` = 0402; `B` = X7R; `104` = 100 nF; `K` = ±10 %; `O` = 16 V; `C` = 7-inch cardboard reel [verified: Samsung CL family package-code table, 2026-11-08].
- Status: "Mass Production" [verified: https://product.samsungsem.com/mlcc/CL05B104KO5NNN.do, 2026-11-08].

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Capacitance | 100 nF ±10 % | | [verified: Samsung page] |
| DC bias | +0.2 % at 1.0 V; −0.8 % at 2.0 V; −3.2 % at 3.0 V; −4.0 % at 3.3 V | 25 °C | [verified: Samsung DC-bias curve, 2026-11-08] |

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Length | 1.00 mm ± 0.05 mm | 1.05 mm | [verified: Samsung page] |
| Width | 0.50 mm ± 0.05 mm | 0.55 mm | [verified: Samsung page] |
| Height | 0.50 mm ± 0.05 mm | 0.55 mm | [verified: Samsung page] |

## Checks against the design

- 3.3 V is 21 % of the 16 V rating.
- TI's LaunchPad uses eight 0.1 µF 0201 X7S parts, GRM033C71A104KE14D [verified: SWRC397 MCU143A BOM]. pcb-engineer must take the pin-by-pin decoupling count from the LaunchPad schematic. The BOM's "2" is an assumption.

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Date |
|---|---|---|---|---|---|---|
| JLCPCB (basic) | 0.0031 | 0.0031 | 0.0031 | 0.0023 | 0.0017 | 2026-11-08 |
| LCSC (min 100) | — | — | 0.0032 | 0.0024 | 0.0018 | 2026-11-08 |

## Stock

| Source | Stock | Date |
|---|---|---|
| JLCPCB | 34,285,467 | 2026-11-08 |
| LCSC | 3,539,900 | 2026-11-08 |

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| Samsung product page | https://product.samsungsem.com/mlcc/CL05B104KO5NNN.do | 2026-11-08 | read |
| JLCPCB parts API | JLCPCB parts API (jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) | 2026-11-08 | read |
| LCSC product API | LCSC product API (wmsc.lcsc.com/ftps/wm/product/detail?productCode=C1525) | 2026-11-08 | read |
| DigiKey | https://www.digikey.com/en/products/result?keywords=CL05B104KO5NNNC (via r.jina.ai) | 2026-11-08 | failed: the reader proxy returned a 600-character page |
