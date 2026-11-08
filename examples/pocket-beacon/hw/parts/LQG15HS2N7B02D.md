---
mpn: LQG15HS2N7B02D
aliases: C162541
manufacturer: Murata Electronics
lcsc: C162541
function: RF harmonic filter series inductor 2.7 nH ±0.1 nH (L2)
package: 0402
size_max_mm: 1.1x0.6x0.55
supply_range_v: -
io_range_v: -
typ_current_ma: -
peak_current_ma: -
lifecycle: production
lifecycle_distributor: -
key_specs: l_nh=2.7; tol=0.1nH; srf_ghz=6; rdc_mohm=120; jlc=extended
distributors: LCSC=https://www.lcsc.com/product-detail/C162541.html; JLCPCB=https://jlcpcb.com/partdetail/C162541
price_1: 0.062
price_10: 0.062
price_100: 0.0532
price_1k: 0.0454
price_10k: 0.0406
lead_time_wk: -
stock_snapshot: 11865 @ LCSC 2026-11-08
alternatives: LQG15HS2N7S02D (Murata, ±0.3 nH, C77108, 218616 stock); LQP15MN2N7B02D (Murata thin film, 0 stock)
evidence: estimate
source_date: 2026-11-08
notes: Start value from TI's 2.8 nH filter inductor (0201 on the LaunchPad); final value set by VNA tuning on EVT (V-005, D-030). suffix ok: Murata D = 180 mm paper reel
---

# LQG15HS2N7B02D: 2.7 nH 0402 multilayer RF inductor (L2)

## Key specs

| Spec | Value | Source |
|---|---|---|
| Inductance | 2.7 nH ±0.1 nH, SRF 6 GHz, 120 mΩ, 800 mA | [verified: JLCPCB parts API C162541, 2026-11-08] |
| Maximum dimensions | 1.1x0.6x0.55 mm | [estimate: standard 0402 envelope with margin; maker datasheet not read] |
| JLCPCB library type | **Extended** | [verified: JLCPCB parts API, 2026-11-08] |
| Reference | TI LaunchPad L33 = 2.8 nH LQP03TN2N8B02J (0201) between ANT and the antenna match | [verified: TI SWRC397 MCU143A BOM and schematic, 2026-11-08] |

## Price breaks (USD per unit)

| Source | 1 | 100 | 1k | 10k | Date |
|---|---|---|---|---|---|
| JLCPCB / LCSC (C162541) | 0.062 | 0.0532 | 0.0454 | 0.0406 | 2026-11-08 |

## Stock

| Source | Stock | Date |
|---|---|---|
| JLCPCB / LCSC | 11865 | 2026-11-08 |

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| JLCPCB parts API | https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList (keyword C162541) | 2026-11-08 | read: model, brand, stock, library type, price ladder |
| TI LP-EM-CC2340R53 design files | https://www.ti.com/lit/zip/SWRC397 (MCU143A_BOM.xlsx, mcu143a.pdf) | 2026-11-08 | read |
