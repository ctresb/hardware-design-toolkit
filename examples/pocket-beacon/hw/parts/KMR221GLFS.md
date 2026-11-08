---
mpn: KMR221GLFS
aliases: KMR221G LFS; KMR221GLFS-TR
manufacturer: C&K
lcsc: C72443
function: SMD tactile switch under the elastomer button membrane
package: SMD 4.2 x 2.8 mm, 4 terminals + ground pin
size_max_mm: 4.7x2.9x2.0
supply_range_v: -
io_range_v: -
typ_current_ma: 0
peak_current_ma: 0
lifecycle: production
lifecycle_distributor: Active
key_specs: 2.0 N +/-0.5 N; 200,000 cycles; travel 0.25 +/-0.1 mm; total height 1.9 mm; IP40; tactile feel >= 30 %; bounce <= 3 ms; -40 to 85 C
distributors: DigiKey=https://www.digikey.com/en/products/result?keywords=KMR221GLFS; LCSC=https://www.lcsc.com/product-detail/C72443.html
price_1: 0.67
price_10: 0.576
price_100: 0.4792
price_1k: 0.39622
price_10k: 0.34297
lead_time_wk: 13
stock_snapshot: 106572 @ DigiKey 2026-11-08 (+105000 factory); 1535 @ LCSC 2026-11-08 (C72443); 2420 @ JLCPCB 2026-11-08
alternatives: KMR231GLFS (drop-in, 3.0 N, 150,000 cycles); KMR211GLFS (drop-in, 1.2 N, 200,000 cycles); KMR221G ULC LFS (drop-in, low-current contacts)
evidence: verified
source_date: 2026-11-08
notes: the switch itself is only IP40; the IP67 target rests on the enclosure's elastomer membrane over it (Q-PB-06). Actuation force felt by the user = switch force + membrane force. suffix ok: C&K LFS = lead-free, tape and reel is standard for KMR2
---

# KMR221GLFS: SMD tactile switch, 2 N (C&K KMR2)

## Identity

- C&K KMR2 series, 1.9 mm height. `KMR2` series, `2` = 2.0 N force, `1` = silver contacts, `G` = ground pin, `LFS` = lead-free, silver plated [verified: C&K KMR2 datasheet, LCSC mirror for C72443, 2026-11-08].
- Packed in reels of 7,000, 330 mm diameter [verified].

## Why this part

REQ-009 button: a small, low-profile SMD switch with a clear tactile click that works through a membrane. 200,000 cycles is far above a finder's use.

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Operating force | 2.0 N (200 gf) ± 0.50 N | — | [verified: KMR2 datasheet table] |
| Operating life | 200,000 cycles | — | [verified] |
| Travel | 0.25 ± 0.1 mm | — | [verified] |
| Tactile feel | ≥ 30% (2 N / 3 N / 4 N versions) | — | [verified] |
| Contact resistance | ≤ 100 mΩ | — | [verified] |
| Bounce time | ≤ 3 ms | — | [verified] |
| Insulation resistance | ≥ 1 GΩ | — | [verified] |
| Sealing | IP40 | — | [verified: datasheet feature list] |
| Operating temperature | −40 °C to 85 °C (silver) | — | [verified] |
| Low-current note | ULC version specified down to 1 µA at 1.8 V DC | — | [verified] |

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Body | 4.2 × 2.8 mm | — | [verified: datasheet drawing] |
| Overall incl. terminals | 4.6 × 2.8 mm | 4.7 × 2.9 mm | [verified: JLCPCB "SMD,4.6x2.8mm"; estimate: max +0.1] |
| Total height | 1.9 mm | 2.0 mm | [verified: 1.9 mm; estimate: max +0.1, tolerance not printed] |

## Lifecycle

| Source | Status | Date |
|---|---|---|
| Manufacturer | datasheet current; product page not read | 2026-11-08 |
| DigiKey | Active | 2026-11-08 |

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Packaging | Date |
|---|---|---|---|---|---|---|---|
| DigiKey | 0.67 | 0.576 | 0.4792 | 0.39622 | 0.34297 (7k reel) | CT; TR 7k | 2026-11-08 |
| LCSC C72443 | 0.6967 | 0.5729 | 0.4507 | 0.3731 | — | reel 7000 | 2026-11-08 |

## Stock and lead time

| Source | Authorized stock | Factory lead time | Limits / notes | Date |
|---|---|---|---|---|
| DigiKey | 106,572 + 105,000 factory | 13 weeks | — | 2026-11-08 |
| LCSC / JLCPCB C72443 | 1,535 / 2,420 | — | Extended | 2026-11-08 |

## Checks against the design

- Through a membrane: the user feels 2.0 N plus the membrane's own preload. Keep the membrane force ≤ 1.0 N, or move to KMR211 (1.2 N) [estimate].
- Accidental press in a bag: 2.0 N with 0.25 mm travel; firmware should ignore presses shorter than 50 ms [assumption].

## Risks

| Risk | Rating | Mitigation |
|---|---|---|
| IP40 switch in an IP67 product | medium | seal at the membrane; no path from the switch cavity to the PCB |
| LCSC stock 1.5–2.4k | low | DigiKey consignment for 1k+ |

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| C&K KMR2 datasheet | LCSC mirror for C72443 | 2026-11-08 | read |
| C&K direct | https://www.ckswitches.com/media/1480/kmr2.pdf | 2026-11-08 | HTML instead of PDF |
| DigiKey search | https://www.digikey.com/en/products/result?keywords=KMR221GLFS | 2026-11-08 | read |
| LCSC API, JLCPCB search API | wmsc.lcsc.com, jlcpcb.com | 2026-11-08 | read |
