---
mpn: CL10A226MQ8NRNC
aliases: CL10A226MQ8NRN#; CL10A226MQ8NRND (13-inch reel)
manufacturer: Samsung Electro-Mechanics
lcsc: C59461
function: Bulk capacitor 22 uF X5R 6.3 V on VBAT for coin-cell pulses
package: 0603 (1608 metric) MLCC
size_max_mm: 1.80x1.00x1.00
supply_range_v: 0-6.3
io_range_v: -
typ_current_ma: -
peak_current_ma: -
lifecycle: production
lifecycle_distributor: Active
key_specs: c_uf=22; v=6.3; dielectric=X5R; tol=20%; c_eff_3v0_uf=10.7; c_eff_2v2_uf=13.8
distributors: JLCPCB=basic part C59461; LCSC=https://www.lcsc.com/product-detail/C59461.html; DigiKey=https://www.digikey.com/en/products/result?keywords=CL10A226MQ8NRNC
price_1: 0.0171
price_10: 0.0171
price_100: 0.0171
price_1k: 0.0113
price_10k: 0.0094
lead_time_wk: -
stock_snapshot: 3843850 @ JLCPCB 2026-11-08; 717040 @ LCSC 2026-11-08; 0 @ DigiKey 2026-11-08
alternatives: CL21A226MAQNNNE (needs change: 0805 footprint, 1.40 mm max height, keeps 15.8 uF at 3.0 V, JLC basic C45783, about 11x the price); GRM188R60J226MEA0D (drop-in footprint; DC bias not checked)
evidence: verified
source_date: 2026-11-08
notes: Keeps only 10.7 uF of 22 uF at 3.0 V (-51 %). The VBAT net needs >= 14.2 uF effective for the ring start (TI slew rule): add a third one (Q-PB-07).. suffix ok: Samsung last letter C = 7-inch paper tape
---
# CL10A226MQ8NRNC: bulk 22 µF X5R 6.3 V, 0603

## Identity

- Manufacturer: Samsung Electro-Mechanics.
- Full orderable MPN: `CL10A226MQ8NRNC`. The page lists the family as `CL10A226MQ8NRN#`, where `#` is the package code. `C` = cardboard tape, 7-inch reel. `D` and `L` = 13-inch cardboard. `E` and `F` = embossed. `R` and `Z` = horizontally aligned, low acoustic noise. [verified: https://product.samsungsem.com/mlcc/CL10A226MQ8NRN.do, package-code table, 2026-11-08]
- Decode [verified: Samsung CL catalog part-numbering key, via LCSC datasheet mirror, 2026-11-08]:
  - `10` = 0603;
  - `A` = X5R;
  - `226` = 22 µF;
  - `M` = ±20 %;
  - `Q` = 6.3 V.
- Status: "Mass Production" [verified: Samsung product page, 2026-11-08].

## Why this part

REQ-005 limits the peak current from the cell. Architecture §5 puts 2 × 22 µF on VBAT so that the cell sees the average of the TX and ring pulses. SWRS272F §7.3 note 3 requires enough VDDS capacitance on coin cells to keep the falling supply slew rate ≤ 1 mV/µs [verified: TI SWRS272F rev F, May 2026, §7.3].

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Capacitance | 22 µF ±20 % | 0 V DC | [verified: Samsung product page, 2026-11-08] |
| Rated voltage | 6.3 V DC | | [verified: same] |
| Dielectric | X5R, −55 °C to +85 °C | | [verified: same] |
| Capacitance change, DC bias | −10.4 % at 1.0 V; −33.5 % at 2.0 V; −37.4 % at 2.2 V; −42.8 % at 2.5 V; −51.2 % at 3.0 V; −55.6 % at 3.3 V | 25 °C | [verified: Samsung product page, embedded DC-bias curve data, 2026-11-08; interpolated linearly between curve points] |
| Effective capacitance | 13.8 µF at 2.2 V; 10.7 µF at 3.0 V; 9.8 µF at 3.3 V | 25 °C, nominal | [estimate: 22 µF × (1 + change)] |

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Length | 1.60 mm ± 0.20 mm | 1.80 mm | [verified: Samsung product page, 2026-11-08] |
| Width | 0.80 mm ± 0.20 mm | 1.00 mm | [verified: same] |
| Height | 0.80 mm ± 0.20 mm | 1.00 mm | [verified: same] |

The BOM listed `1.7x0.9x0.9`. That is too small: the tolerance on this part is ±0.20 mm, so the maximum is 1.80 × 1.00 × 1.00 mm.

## Bulk capacitance on VBAT: what the design really gets

These parts sit on the VBAT net, where the cell is at 2.0 V to 3.3 V:

| Ref | Part | Nominal | Effective at 2.2 V | Effective at 3.0 V |
|---|---|---|---|---|
| C1, C2 | CL10A226MQ8NRNC | 2 × 22 µF | 2 × 13.8 = 27.5 µF | 2 × 10.7 = 21.5 µF |
| C3 | CL10A106KP8NNNC | 10 µF | 6.3 µF | 4.9 µF |
| C7 (U2 CIN) | CL10A225KO8NNNC | 2.2 µF | 1.7 µF | 1.5 µF |
| C5, C6 | CL05B104KO5NNNC | 2 × 0.1 µF | 0.2 µF | 0.2 µF |
| **Total** | | **54.6 µF** | **35.8 µF** | **28.0 µF** |

Each value is [estimate: nominal × (1 + Samsung DC-bias change at that voltage, 25 °C)]. Worst case at 3.0 V: about **19.7 µF**. This adds the −20 % tolerance on the 22 µF parts, −10 % on the K parts and −15 % for X5R over temperature [estimate: X5R limit ±15 %, product page class].

**Requirement 1: falling slew rate ≤ 1 mV/µs on VDDS** [verified: SWRS272F §7.3 note 3]. When a load step ΔI starts, the initial slope is ΔI / C, because the cell's internal resistance limits how fast it can respond.
- TX at 0 dBm, 5.1 mA [verified: SWRS272F §7.10, quoted in architecture.md]: needs C ≥ 5.1 µF. Met.
- Ring start in 3× mode, 14.2 mA [verified: Diodes DS41667 Rev 4-2, IDD33]: needs C ≥ 14.2 µF. Met with 19.7 µF worst case, a margin of only 1.39×. This assumes the charge pump draws no inrush above its steady current; Diodes says only "small inrush" [verified: DS41667 p.1].

**Requirement 2: droop during an advertising event.** The droop is V = I·R·(1 − e^(−t/τ)), with τ = R·C. Assumptions: about 3 ms at 5.1 mA [estimate: architecture.md §5, 3 channels], and a cell source resistance R of 30 Ω fresh to 100 Ω at end of life or cold [assumption: battery-and-power must cite the Panasonic CR2032 data].
- R = 30 Ω, C = 28 µF: droop = 0.15 V.
- R = 100 Ω, C = 28 µF: τ = 2.8 ms, droop = 0.34 V.
- R = 100 Ω, C = 38.8 µF (three 22 µF parts): τ = 3.9 ms, droop = 0.27 V.

Below 2.2 V on VDDS, the DC/DC stops and the SoC falls back to the GLDO, which draws more current [verified: SWRS272F §7.4 note 1]. More effective capacitance keeps an aged cell in DC/DC mode longer.

**Recommendation** (Q-PB-07, for specs-engineer):
1. Add a third CL10A226MQ8NRNC (C15) on VBAT.
   - Nominal effective capacitance rises to 38.8 µF at 3.0 V, and the worst case to about 27 µF.
   - It adds US$ 0.011 at 1k, keeps the 1.00 mm height and is a JLC basic part.
2. The alternative is 2 × CL21A226MAQNNNE, an 0805 rated 25 V.
   - It keeps 15.8 µF at 3.0 V, −28.1 % [verified: Samsung CL21A226MAQNNN page, 2026-11-08].
   - It is 1.40 mm tall and adds about US$ 0.22 at 1k [verified: JLC C45783 price, 2026-11-08].

## Lifecycle

| Source | Status | Date |
|---|---|---|
| Manufacturer (Samsung) | Mass Production | 2026-11-08 |
| DigiKey | Active, 0 in stock, "estimated in-stock date unavailable" | 2026-11-08 |

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Packaging | Date |
|---|---|---|---|---|---|---|---|
| JLCPCB assembly (basic) | 0.0171 | 0.0171 | 0.0171 | 0.0113 | 0.0094 | reel, JLC stock | 2026-11-08 |
| LCSC (min 20) | — | 0.0172 (20) | 0.0132 (200) | 0.0114 | 0.0095 (8k) | 7-inch reel 4000 | 2026-11-08 |
| DigiKey | 0.250 | 0.143 | 0.0903 | 0.0537 (4k reel) | 0.0483 (12k) | cut tape / T&R | 2026-11-08 |

## Stock and lead time

| Source | Authorized stock | Factory lead time | Limits / notes | Date |
|---|---|---|---|---|
| JLCPCB | 3,843,850 | — | basic part: no feeder fee | 2026-11-08 |
| LCSC | 717,040 | — | | 2026-11-08 |
| DigiKey | 0 | not shown | backorder allowed | 2026-11-08 |

## CAD models

| Kind | Source | Trust |
|---|---|---|
| Footprint | KiCad `Capacitor_SMD:C_0603_1608Metric` | standard IPC land; matches 1.6 × 0.8 body |
| 3D model | KiCad library | nominal 0.8 mm height; use 1.0 mm in the stack-up |

## Alternatives

| MPN | Class | Difference | Price at 1k | Source |
|---|---|---|---|---|
| CL21A226MAQNNNE | needs change: 0805 | 15.8 µF at 3.0 V; 1.40 mm max | 0.1227 | [verified: Samsung page + JLC C45783, 2026-11-08] |
| GRM188R60J226MEA0D | drop-in | Murata; DC bias not checked | — | [assumption] |

## Checks against the design

- The VBAT rail, 2.0 V to 3.3 V, is inside the 6.3 V rating. At 3.3 V the part runs at 52 % of its rating.
- Maximum dimensions are 1.80 × 1.00 × 1.00 mm. The BOM row must be corrected from 1.7 × 0.9 × 0.9.
- Effective capacitance is marginal for the ring-start slew rule: see the recommendation above.

## Risks

| Risk | Rating | Mitigation |
|---|---|---|
| Effective capacitance only 1.39× above the slew rule at worst case | medium | third capacitor (Q-PB-07) or firmware soft start (2× mode for 20 ms, then 3×) |
| DigiKey out of stock | low | JLC and LCSC stock is in the millions |

## Conflicts between sources

| Field | Value A (source) | Value B (source) | Decision and reason |
|---|---|---|---|
| size_max_mm | 1.7 × 0.9 × 0.9 (BOM, assumption) | 1.80 × 1.00 × 1.00 (Samsung page) | Samsung: ±0.20 mm tolerance for this part |

## Open questions and RFQs

- Q-PB-07: three 22 µF parts, or 0805, on VBAT (specs-engineer).

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| Samsung product page with DC-bias data | https://product.samsungsem.com/mlcc/CL10A226MQ8NRN.do | 2026-11-08 | read |
| JLCPCB parts API | JLCPCB parts API (jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) | 2026-11-08 | read |
| LCSC product API | LCSC product API (wmsc.lcsc.com/ftps/wm/product/detail?productCode=C59461) | 2026-11-08 | read |
| LCSC product page | https://www.lcsc.com/product-detail/C59461.html | 2026-11-08 | redirected to a datasheet PDF, no stock shown |
| DigiKey | https://www.digikey.com/en/products/result?keywords=CL10A226MQ8NRNC (via r.jina.ai) | 2026-11-08 | read |
| TI SWRS272F | https://www.ti.com/lit/ds/symlink/cc2340r5.pdf | 2026-11-08 | read (rev F, May 2026) |
| Diodes DS41667 | https://www.diodes.com/assets/Datasheets/PAM8904E.pdf | 2026-11-08 | read (Rev 4-2, July 2023) |
