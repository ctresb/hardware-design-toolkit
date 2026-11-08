---
mpn: CC2340R52E0RGER
aliases: CC2340R52E0RGER.A; CC2340R52E0RGER.B; CC2340R5
manufacturer: Texas Instruments
lcsc: C20416850
function: BLE 5.3 SoC, Cortex-M0+ 48 MHz, 512 KB flash, integrated DC/DC
package: VQFN-24 4x4 0.5 mm pitch (RGE)
size_max_mm: 4.1x4.1x1.0
supply_range_v: 1.71-3.8
io_range_v: 1.71-3.8
typ_current_ma: 0.00074
peak_current_ma: 10.7
lifecycle: production
lifecycle_distributor: Active
key_specs: vdd=1.71-3.8; dcdc_min_v=2.2; tx_0dbm_ma=5.1; tx_0dbm_gldo_ma=9.0; rx_ma=5.3; standby_ua=0.74; gpio=12; hfxt_cl_pf=5-9; hfxt_esr_max_ohm=60
distributors: LCSC=https://www.lcsc.com/product-detail/C20416850.html; DigiKey=https://www.digikey.com/en/products/result?keywords=CC2340R52E0RGER; TI=https://www.ti.com/product/CC2340R5/part-details/CC2340R52E0RGER
price_1: 1.485
price_10: 1.2339
price_100: 0.9399
price_1k: 0.8391
price_10k: 0.7508
lead_time_wk: 26
stock_snapshot: 9278 @ LCSC 2026-11-08; 3859 @ DigiKey 2026-11-08; 0 @ TI store 2026-11-08
alternatives: CC2340R52N0RGER (drop-in, -40 to 85 C); CC2340R53E0RKPR (needs change: VQFN-40 5x5, more GPIO)
evidence: verified
source_date: 2026-11-08
notes: TI store caps purchase quantities to protect samples: buy the build quantity early from LCSC or DigiKey
---

# CC2340R52E0RGER: BLE SoC

## Identity

- Manufacturer: Texas Instruments.
- Full orderable MPN: `CC2340R52E0RGER`. `R5` = 512 KB flash family, `E` = −40 °C to 125 °C grade (`N` = −40 °C to 85 °C), `RGE` = VQFN-24, `R` = 3,000-piece large reel. `.A` and `.B` variants are identical and only the base number is orderable [verified: TI part-details page, 2026-11-08].
- Datasheet: SWRS272F, April 2023, revised May 2026 [verified: TI SWRS272F (rev F, May 2026), https://www.ti.com/lit/ds/symlink/cc2340r5.pdf, 2026-11-08].

## Why this part

REQ-002 (≥ 12 months on a CR2032) needs a radio with a low TX peak and sub-µA standby. REQ-010 needs BLE 5.x. The integrated DC/DC keeps the TX peak at 5.1 mA at 0 dBm, so the coin-cell pulse stays small.

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Supply VDDS | 1.71 V to 3.8 V | recommended operating | [verified: SWRS272F §7.3, 2026-11-08] |
| DC/DC operation | 2.2 V to 3.8 V; below 2.2 V it switches to the GLDO | §7.4 | [verified: SWRS272F §7.4, 2026-11-08] |
| Falling supply slew | ≤ 1 mV/µs; coin-cell designs must use 10 µF on VDDS | §7.3 note 3 | [verified: SWRS272F §7.3, 2026-11-08] |
| 48 MHz crystal | required for radio; CL 5 pF to 9 pF; ESR ≤ 60 Ω (6–9 pF), ≤ 80 Ω (5–6 pF) | §7.20.3.1 | [verified: SWRS272F, 2026-11-08] |
| 32.768 kHz crystal | optional (internal LFOSC exists); CL 6 pF to 12 pF; ESR ≤ 100 kΩ | §7.20.3.3 | [verified: SWRS272F, 2026-11-08] |
| Validated 48 MHz crystal | Tai-Saw TZ3908AAAO43 (the only one named) | §7.20.3.1 note 4 | [verified: SWRS272F, 2026-11-08] |
| HFXT load caps | adjustable caps on chip; external load capacitors are required for systems targeting compliance with certain regulations | §7.20.3.1 note 1 | [verified: SWRS272F, 2026-11-08] |
| VDDR | 10 µH + 10 µF required, close to the DCDC pin | §7.4 note 2 | [verified: SWRS272F, 2026-11-08] |
| ESD | HBM ±1000 V, CDM ±500 V | §7.2 | [verified: SWRS272F, 2026-11-08] |

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Length | 4.0 mm | 4.1 mm | [estimate: JEDEC 4 × 4 VQFN body tolerance ±0.1 mm; the RGE drawing pages are image-only] |
| Width | 4.0 mm | 4.1 mm | same |
| Height | — | 1.0 mm | [verified: TI package view RGE 24, "VQFN - 1 mm max height", https://www.ti.com/lit/ml/mpqf124g/mpqf124g.pdf, 2026-11-08] |

Pitch 0.5 mm. MSL 3, 260 °C [verified: TI part-details page, 2026-11-08]. Q-PB-05 closes: the 1.0 mm maximum height is confirmed.

## Power

| Mode | Typical | Condition | Source |
|---|---|---|---|
| TX 0 dBm | 5.1 mA | DCDC on, 3.0 V | [verified: SWRS272F §7.10, 2026-11-08] |
| TX 0 dBm, DCDC off | 9.0 mA | GLDO (below 2.2 V the device is on GLDO) | [verified: same] |
| TX +4 / +6 / +8 dBm | 7.9 / 8.9 / 10.7 mA | DCDC on | [verified: same] |
| TX +8 dBm, DCDC off | 19 mA | GLDO | [verified: same] |
| RX | 5.3 mA (9 mA DCDC off) | 1 Mbps GFSK | [verified: same] |
| MCU active | 2.6 mA (DCDC), 4.1 mA (GLDO) | CoreMark 48 MHz | [verified: SWRS272F §7.9] |
| Standby | 0.71 µA (LFOSC), 0.74 µA (LFXT) | RTC + full RAM, DCDC | [verified: SWRS272F §7.9] |
| Shutdown | 165 nA | no retention | [verified: SWRS272F §7.9] |

**Note:** below 2.2 V the DC/DC stops and every radio current rises by about 1.8× (GLDO). The end-of-life current budget for `battery-and-power` uses the GLDO column.

## Interfaces

SWD on DIO16/DIO17. 12 GPIO in RGE24. X48P/X48N for the 48 MHz crystal. LFXT on DIO3/DIO4, can be left NC when LFOSC is used [verified: SWRS272F §6 and unused-pin table].

## Lifecycle

| Source | Status | Date |
|---|---|---|
| TI datasheet device table | Released | 2026-11-08 |
| TI part-details page | ACTIVE; purchase quantities capped "to protect sample purchases" until supply improves | 2026-11-08 |
| DigiKey | Active | 2026-11-08 |

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Packaging | Date |
|---|---|---|---|---|---|---|---|
| LCSC (C20416850) | 1.485 | 1.2339 | 0.9399 | 0.8391 | 0.7508 [estimate: LCSC third-party listing at 3,000+, "to be re-confirmed"] | cut tape / reel 3,000 | 2026-11-08 |
| JLCPCB parts library | 1.4703 | 1.2217 | 0.9306 | 0.8309 | — | Extended part | 2026-11-08 |
| DigiKey | 3.17 | 2.739 | 2.3805 | 2.08499 | 1.96322 (3,000 reel) | CT / T&R | 2026-11-08 |
| TI store | — | — | — | — | — | out of stock, quantity capped | 2026-11-08 |

## Stock and lead time

| Source | Authorized stock | Factory lead time | Limits / notes | Date |
|---|---|---|---|---|
| LCSC | 9,278 | — | JLCPCB Extended part | 2026-11-08 |
| DigiKey | 3,859 | 26 weeks | — | 2026-11-08 |
| TI store | 0 | — | purchase cap | 2026-11-08 |

## CAD models

| Kind | Source | Trust |
|---|---|---|
| Footprint | KiCad `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` or TI RGE0024 land pattern | check the exposed-pad size against the TI drawing before release |
| Symbol | TI / generated from the datasheet pin table | pinout to be checked against SWRS272F §6 |
| 3D model | TI or KiCad library | dimensions as above |

## Alternatives

| MPN | Class | Difference | Price at 1k | Source |
|---|---|---|---|---|
| CC2340R52N0RGER | drop-in | −40 °C to 85 °C grade | not checked | TI datasheet device table |
| CC2340R53E0RKPR | needs change: VQFN-40 5 × 5 mm | more GPIO, more flash variants | not checked | TI datasheet |

## Checks against the design

- Rail VBAT 2.0 V to 3.3 V inside 1.71 V to 3.8 V: **yes**. Below 2.2 V the device runs on the GLDO, with higher current.
- Maximum dimensions inside the size budget: 4.1 × 4.1 × 1.0 mm, yes.
- I²C address: not applicable.
- Package inside JLCPCB capabilities: 0.5 mm-pitch QFN, yes (X-ray inspection for the exposed pad is charged per part).

## Risks

| Risk | Rating | Mitigation |
|---|---|---|
| TI store purchase cap and 26-week lead time | medium | buy the EVT, DVT and launch quantities from LCSC/DigiKey now |
| Radio current ×1.8 below 2.2 V (GLDO) | medium | end-of-life budget uses GLDO currents; low-battery warning at 2.3 V (Q-PB-02) |
| HFXT external load caps "required for systems targeting compliance with certain regulations" | medium | add two 0402 C0G footprints at the crystal (Q-PB-101) |

## Open questions and RFQs

- Q-PB-101 (new): add HFXT external load-capacitor footprints (2 × 0402 C0G) to meet the datasheet note for regulatory compliance.
- Q-PB-102 (new): confirm in the TI BLE stack documentation that LFOSC is accepted as the BLE sleep clock. If yes, Y2, C13 and C14 can be removed.

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| TI datasheet SWRS272F | https://www.ti.com/lit/ds/symlink/cc2340r5.pdf | 2026-11-08 | read (pdftotext) |
| TI part details | https://www.ti.com/product/CC2340R5/part-details/CC2340R52E0RGER | 2026-11-08 | read |
| TI RGE package view | https://www.ti.com/lit/ml/mpqf124g/mpqf124g.pdf | 2026-11-08 | read (drawing is an image; height only) |
| DigiKey search | https://www.digikey.com/en/products/result?keywords=CC2340R52E0RGER | 2026-11-08 | read |
| LCSC product page | https://r.jina.ai/https://www.lcsc.com/product-detail/C20416850.html | 2026-11-08 | read via reader proxy |
| JLCPCB part detail | https://r.jina.ai/https://jlcpcb.com/partdetail/C20416850 | 2026-11-08 | read via reader proxy |
| LCSC search (direct) | https://www.lcsc.com/search?q=CC2340R52E0RGER | 2026-11-08 | JavaScript only, no data |
