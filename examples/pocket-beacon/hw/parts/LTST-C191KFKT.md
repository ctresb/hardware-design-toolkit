---
mpn: LTST-C191KFKT
aliases: LTST-C191KFKT-5A
manufacturer: Lite-On
lcsc: C160478
function: Orange (605 nm) status LED, 0603 extra thin
package: 0603 (1608), 2 pads
size_max_mm: 1.7x0.9x0.65
supply_range_v: -
io_range_v: -
typ_current_ma: 1.5
peak_current_ma: 2
lifecycle: production
lifecycle_distributor: Active
key_specs: AlInGaP 605 nm dominant; IV 45-90 mcd at 20 mA (bins P-S 45-280 mcd); VF 2.0 typ / 2.4 max at 20 mA, about 1.75 V near 1 mA; 130 deg viewing angle
distributors: DigiKey=https://www.digikey.com/en/products/result?keywords=LTST-C191KFKT; LCSC=https://www.lcsc.com/product-detail/C160478.html
price_1: 0.14
price_10: 0.098
price_100: 0.0675
price_1k: 0.04869
price_10k: 0.03745
lead_time_wk: 14
stock_snapshot: 183911 @ DigiKey 2026-11-08; 36100 @ LCSC 2026-11-08 (C160478)
alternatives: LTST-C191KRKT (drop-in, red 631 nm, not checked); LTST-C191KGKT (drop-in, green; higher VF, not checked)
evidence: verified
source_date: 2026-11-08
notes: at 1.5 mA expect about 3-6 mcd (6-7 % of the 20 mA value); at VBAT 2.0 V with R1 = 680 Ohm only about 0.4 mA flows (about 1 mcd)
---

# LTST-C191KFKT: orange status LED, 0603 extra thin (Lite-On)

## Identity

- Manufacturer: Lite-On Technology. Spec DS22-2000-222 rev F, effective 2012-01-31 [verified: datasheet via LCSC mirror C160478, 2026-11-08].
- "Extra thin (0.55 H mm) chip LED", AlInGaP orange [verified].

## Why this part

D-005: an AlInGaP LED (low VF) still lights from a 2.0–3.3 V coin cell with only a resistor. A white or blue InGaN LED (VF > 2.6 V) would not.

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Luminous intensity | 45.0 min / 90.0 typ mcd | IF = 20 mA | [verified: datasheet p.4] |
| Intensity bins | P 45–71, Q 71–112, R 112–180, S 180–280 mcd (±15%) | 20 mA | [verified: p.5] |
| VF | 2.0 typ / 2.4 max V | IF = 20 mA | [verified: p.4] |
| VF at low current | ≈ 1.75 V near 1 mA | Fig. 2 | [estimate: read from Fig. 2] |
| Relative intensity vs current | close to linear: ≈ 0.06–0.07 of the 20 mA value at 1.5 mA | Fig. 4 | [estimate: read from Fig. 4] |
| Dominant / peak wavelength | 605 / 611 nm | — | [verified] |
| Viewing angle | 130° | 2θ½ | [verified] |
| Reverse current | 10 µA max | VR = 5 V | [verified] |

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Length × width | 1.6 × 0.8 mm | 1.7 × 0.9 mm | [verified: tolerance ±0.10 mm] |
| Height | 0.55 mm | 0.65 mm | [verified: ±0.10; DigiKey 0.65 max] |

## Power

| Mode | Current | Condition | Source |
|---|---|---|---|
| On, fresh cell | ≈ 1.8 mA | (3.0 − 1.75) V / 680 Ω | [estimate] |
| On, mid-life | ≈ 1.2 mA | (2.6 − 1.75) V / 680 Ω | [estimate] |
| On, end of life | ≈ 0.4 mA | (2.0 − 1.75) V / 680 Ω | [estimate] |

## Lifecycle

| Source | Status | Date |
|---|---|---|
| Manufacturer | product page not read (direct PDF download failed, HTML returned) | 2026-11-08 |
| DigiKey | Active | 2026-11-08 |

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Packaging | Date |
|---|---|---|---|---|---|---|---|
| DigiKey | 0.14 | 0.098 | 0.0675 | 0.04869 | 0.03745 | CT; TR 5k+ | 2026-11-08 |
| LCSC C160478 | 0.0284 (20+) | — | 0.0228 (200+) | 0.0196 (600+) | 0.0145 | reel 5000 | 2026-11-08 |

## Stock and lead time

| Source | Authorized stock | Factory lead time | Limits / notes | Date |
|---|---|---|---|---|
| DigiKey | 183,911 | 14 weeks | — | 2026-11-08 |
| LCSC C160478 | 36,100 | — | Extended | 2026-11-08 |

## Checks against the design

- Brightness: 3–6 mcd at 1.5 mA is visible indoors behind a thin diffuser. It is weak in daylight. At end of life it fades to ≈ 1 mcd.
- Design question for specs-engineer: lower R1 to 330 Ω (≈ 3.8 mA fresh, ≈ 0.8 mA at 2.0 V), or drive the LED from a high-drive GPIO. Blink duty is low, so the energy cost is small [estimate].

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| Lite-On datasheet DS22-2000-222 rev F | LCSC mirror for C160478 | 2026-11-08 | read (curves read from rendered pages 6–7) |
| Lite-On direct download | optoelectronics.liteon.com/upload/download/DS22-2000-223/LTST-C191KFKT.pdf | 2026-11-08 | HTML instead of PDF |
| DigiKey search | https://www.digikey.com/en/products/result?keywords=LTST-C191KFKT | 2026-11-08 | read |
| LCSC API C160478 | wmsc.lcsc.com | 2026-11-08 | read |
