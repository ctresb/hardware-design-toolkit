---
mpn: CL05A105KO5NNNC
aliases: CL05A105KO5NNN#
manufacturer: Samsung Electro-Mechanics
lcsc: C29266
function: U2 charge-pump flying capacitors 1 uF X5R 16 V (as in the BOM)
package: 0402 (1005 metric) MLCC
size_max_mm: 1.05x0.55x0.55
supply_range_v: 0-16
io_range_v: -
typ_current_ma: -
peak_current_ma: -
lifecycle: production
lifecycle_distributor: Active
key_specs: c_uf=1; v=16; dielectric=X5R; c_eff_3v3_uf=0.47; c_eff_6v6_uf=0.22
distributors: JLCPCB=extended part C29266; LCSC=https://www.lcsc.com/product-detail/C29266.html; DigiKey=https://www.digikey.com/en/products/result?keywords=CL05A105KO5NNNC
price_1: 0.0049
price_10: 0.0049
price_100: 0.0049
price_1k: 0.0037
price_10k: 0.0027
lead_time_wk: 61
stock_snapshot: 1894249 @ JLCPCB 2026-11-08; 1678050 @ LCSC 2026-11-08; 0 @ DigiKey 2026-11-08
alternatives: CL05A105KA5NQNC (drop-in, 25 V, 0.43 uF at 6.6 V, JLC basic C52923: recommended); CL10A105KB8NNNC (needs change: 0603, 50 V, 0.53 uF at 6.6 V, JLC basic C15849)
evidence: verified
source_date: 2026-11-08
notes: BOM conflict: the BOM's LCSC C52923 is CL05A105KA5NQNC (25 V), not this part. Use the 25 V part: basic at JLC and twice the effective capacitance at 6.6 V.
---
# CL05A105KO5NNNC: 1 µF X5R 16 V, 0402 (U2 flying capacitors, as in the BOM)

## Identity

- Samsung Electro-Mechanics. Decode: `05` = 0402; `A` = X5R; `105` = 1 µF; `K` = ±10 %; `O` = 16 V.
- Status: "Mass Production" [verified: https://product.samsungsem.com/mlcc/CL05A105KO5NNN.do, 2026-11-08].
- **BOM conflict:**
  - The BOM row C9/C10 names this MPN, with LCSC `C52923`.
  - LCSC C52923 is **CL05A105KA5NQNC**, the 25 V part [verified: LCSC product API and JLC API, 2026-11-08].
  - This MPN is LCSC **C29266**, an extended part at JLC.

## Why this part

Diodes' application circuit gives C1 = C2 = 1 µF [verified: DS41667 Rev 4-2]. In 3× mode the second flying capacitor sees about 2 × VIN, up to 6.6 V on a fresh cell [estimate: charge-pump tripler topology; DS41667 shows VOUT up to 3 × VDD].

## DC bias comparison

| Part | Rated | At 3.3 V | At 6.6 V | JLC class | Price at 1k |
|---|---|---|---|---|---|
| CL05A105KO5NNNC (this) | 16 V | 0.47 µF (−53.2 %) | **0.22 µF** (−77.9 %) | extended C29266 | 0.0037 |
| CL05A105KA5NQNC | 25 V | 0.73 µF (−27.1 %) | **0.43 µF** (−57.2 %) | **basic** C52923 | 0.0044 |
| CL10A105KB8NNNC (0603) | 50 V | 0.82 µF (−18.4 %) | 0.53 µF (−46.9 %) | basic C15849 | — |

All [verified: Samsung product pages with DC-bias curves, 2026-11-08]. Effective values are [estimate: 1 µF × (1 + change)].

**Recommendation** (Q-PB-08, for specs-engineer): change C9 and C10 to `CL05A105KA5NQNC`. The footprint (0402) stays the same. It doubles the effective flying capacitance, is a JLC basic part with no feeder fee, and costs US$ 0.0007 more per part at 1k.

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Length | 1.00 mm ± 0.05 mm | 1.05 mm | [verified: Samsung page] |
| Width | 0.50 mm ± 0.05 mm | 0.55 mm | [verified: Samsung page] |
| Height | 0.50 mm ± 0.05 mm | 0.55 mm | [verified: Samsung page] |

`CL05A105KA5NQNC` is 1.00 mm ± 0.10 mm in each dimension, so its maximum is 1.10 × 0.60 × 0.60 mm [verified: https://product.samsungsem.com/mlcc/CL05A105KA5NQN.do, 2026-11-08].

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Date |
|---|---|---|---|---|---|---|
| JLCPCB (extended) | 0.0049 | 0.0049 | 0.0049 | 0.0037 | 0.0027 | 2026-11-08 |
| DigiKey | 0.100 | 0.043 | 0.0248 | 0.0111 (10k reel) | 0.0111 | 2026-11-08 |
| JLCPCB, CL05A105KA5NQNC (basic) | 0.0058 | 0.0058 | 0.0058 | 0.0044 | 0.0034 | 2026-11-08 |

## Stock and lead time

| Source | Stock | Lead time | Date |
|---|---|---|---|
| JLCPCB C29266 | 1,894,249 | — | 2026-11-08 |
| LCSC C29266 | 1,678,050 | — | 2026-11-08 |
| DigiKey | 0; 10,000 expected 08-Apr-2027 | 61 weeks | 2026-11-08 |
| JLCPCB C52923 (25 V) | 11,550,069 | — | 2026-11-08 |

## Conflicts between sources

| Field | Value A | Value B | Decision and reason |
|---|---|---|---|
| lcsc | C52923 (BOM) | C29266 (LCSC/JLC lookup of this MPN) | C52923 is a different part (25 V). Adopt that part (Q-PB-08) |

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| Samsung product pages | https://product.samsungsem.com/mlcc/CL05A105KO5NNN.do, https://product.samsungsem.com/mlcc/CL05A105KA5NQN.do, https://product.samsungsem.com/mlcc/CL10A105KB8NNN.do | 2026-11-08 | read |
| JLCPCB parts API | JLCPCB parts API (jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) | 2026-11-08 | read |
| LCSC product API | LCSC product API (wmsc.lcsc.com/ftps/wm/product/detail?productCode=C29266), C52923 | 2026-11-08 | read |
| DigiKey | https://www.digikey.com/en/products/result?keywords=CL05A105KO5NNNC (via r.jina.ai) | 2026-11-08 | read |
| Diodes DS41667 | https://www.diodes.com/assets/Datasheets/PAM8904E.pdf | 2026-11-08 | read |
