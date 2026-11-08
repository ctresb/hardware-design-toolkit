---
mpn: LQG15HS2N2B02D
aliases: LQG15HS2N2B02
manufacturer: Murata
lcsc: C162540
function: 2.2 nH 0402 multilayer RF inductor (recommended L2, antenna match)
package: 0402
size_max_mm: 1.1x0.6x0.55
supply_range_v: -
io_range_v: -
typ_current_ma: -
peak_current_ma: -
lifecycle: production
lifecycle_distributor: Active
key_specs: l_nh=2.2; tol_nh=0.1; q=8 at 100MHz; type=multilayer
distributors: LCSC=https://www.lcsc.com/product-detail/C162540.html; DigiKey=https://www.digikey.com/en/products/result?keywords=LQG15HS2N2B02D
price_1: 0.10
price_10: 0.0399
price_100: 0.0319
price_1k: 0.0319
price_10k: 0.0218
lead_time_wk: -
stock_snapshot: 31900 @ LCSC 2026-11-08; 591632 @ DigiKey 2026-11-08
alternatives: LQW15AN2N2B80D (drop-in, wirewound, higher Q)
evidence: estimate
source_date: 2026-11-08
notes: Final value comes from VNA tuning: keep a kit of LQG15HS 1.0-10 nH and GJM 0.5-3 pF for EVT. suffix ok: Murata D = 180 mm paper reel
---

# LQG15HS2N2B02D: 2.2 nH RF inductor (recommended L2)

## Identity

- Manufacturer: Murata, LQG15HS multilayer series. `2N2` = 2.2 nH; `B` = ±0.1 nH [assumption: Murata tolerance code; the LCSC page shows no tolerance]; `D` = 180 mm paper reel [assumption].

## Key specs

| Spec | Value | Source |
|---|---|---|
| Inductance | 2.2 nH | [verified: LCSC listing C162540, 2026-11-08] |
| Q | 8 at 100 MHz | [verified: LCSC listing, 2026-11-08] |
| Size | 0402 | [verified: LCSC listing] |
| Maximum dimensions | 1.1 × 0.6 × 0.55 mm | [estimate: 0402 envelope with margin, as used in the stage-2 BOM; datasheet not read] |

Evidence is `estimate` for the row, because the maximum dimensions and Q at 2.4 GHz come from typical values, not the datasheet.

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Date |
|---|---|---|---|---|---|---|
| DigiKey | 0.10 | — | — | — | — | 2026-11-08 |
| LCSC (C162540) | — | 0.0399 (20+) | 0.0319 (200+) | 0.0319 [estimate: 200+ tier; middle tiers hidden] | 0.0218 | 2026-11-08 |

## Stock

| Source | Authorized stock | Date |
|---|---|---|
| LCSC | 31,900 (+20,000 third-party) | 2026-11-08 |
| DigiKey | 591,632 | 2026-11-08 |

## Checks against the design

- Value is a starting point. The eval board uses 2.7 nH and 3.9 nH (antenna dossier). Order a value kit for EVT tuning.

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| LCSC search | https://r.jina.ai/https://www.lcsc.com/search?q=LQG15HS2N2B02D | 2026-11-08 | read via reader proxy |
| DigiKey (substitute list on the LQP15MN page) | https://www.digikey.com/en/products/result?keywords=LQP15MN2N2B02D | 2026-11-08 | read |
| Murata LQG15HS datasheet | — | — | not read in this session |
