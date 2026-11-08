---
mpn: CPT-9019A-SMT-TR
aliases: CPT-9019A-SMT
manufacturer: Same Sky (formerly CUI Devices)
lcsc: C20181991
function: Piezo transducer 4 kHz, externally driven, SMD 9 x 9 mm, top port
package: SMD 9x9
size_max_mm: 9.5x9.5x2.1
supply_range_v: -
io_range_v: -
typ_current_ma: 1.0
peak_current_ma: -
lifecycle: production
lifecycle_distributor: Active
key_specs: f0_khz=4.0; spl_db_min=72 at 10cm 3Vpp; vin_vpp=1-25; cap_nf=8.4-15.6; port=top; reflow_max_c=250
distributors: DigiKey=https://www.digikey.com/en/products/result?keywords=CPT-9019A-SMT-TR; LCSC=https://www.lcsc.com/product-detail/C20181991.html
price_1: 1.31
price_10: 0.992
price_100: 0.762
price_1k: 0.64
price_10k: 0.49
lead_time_wk: 13
stock_snapshot: 47328 @ DigiKey 2026-11-08; 13 @ LCSC 2026-11-08
alternatives: PKMCS0909E4000-R1 (Last Time Buy, do not use); CPT-9019S-SMT-TR (Same Sky, 3 V, check datasheet)
evidence: verified
source_date: 2026-11-08
notes: Only 13 at LCSC: buy at DigiKey and consign to JLCPCB, or pre-order an LCSC reel
---

# CPT-9019A-SMT-TR: piezo transducer (recommended LS1)

## Identity

- Manufacturer: Same Sky (formerly CUI Devices).
- Full orderable MPN: `CPT-9019A-SMT-TR` (tape and reel, 1,500 per reel) [verified: datasheet p.3 packaging, 2026-11-08].
- Datasheet: dated 02/19/2026 [verified: https://www.sameskydevices.com/product/resource/digikeypdf/cpt-9019a-smt-tr.pdf, 2026-11-08].

## Why this part

It replaces the end-of-life Murata PKMCS0909E4000-R1 at the same 9 × 9 mm size. It is about 7 dB more sensitive at the same drive, and its capacitance is published, well inside the PAM8904E 47 nF limit.

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Rated voltage | 3 Vpp | | [verified: datasheet p.1] |
| Operating voltage | 1 Vpp to 25 Vpp | | [verified: datasheet p.1] |
| SPL | 72 dB min, 75 dB typ | 10 cm, rated voltage, 4,000 Hz, ½-duty square | [verified: datasheet p.1] |
| Current | 1 mA max | at rated voltage | [verified: datasheet p.1] |
| Capacitance | 8,400 pF min, 12,000 pF typ, 15,600 pF max | 1 kHz | [verified: datasheet p.1] |
| Temperature | −40 °C to 85 °C | operating and storage | [verified: datasheet p.1] |
| Reflow | 250 °C max; reflow within 48 h of opening, else bake 40 °C 24 h | | [verified: datasheet p.1] |
| Port | top | | [verified: DigiKey attributes, 2026-11-08] |

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Length | 9.0 mm | 9.5 mm | [verified: datasheet p.2, general tolerance ±0.5 mm] |
| Width | 9.0 mm | 9.5 mm | same |
| Height | 1.9 mm | 2.1 mm | [verified: DigiKey "max seated height 2.10 mm", 2026-11-08] |

**Note:** the drawing's general tolerance is ±0.5 mm. The stack-up and the enclosure pocket must use 9.5 × 9.5 × 2.1 mm.

## Sound estimate with the PAM8904E

| Drive | Swing across piezo | SPL at 10 cm | SPL at 25 cm, free field |
|---|---|---|---|
| 3 Vpp (rated) | 3 Vpp | 72 dB min | 64 dB [estimate: −8 dB for 10 → 25 cm, inverse square] |
| 3× differential, VBAT 3.0 V | 14.4–18 Vpp (2 × VOUT3) | 86–88 dB min | 78–80 dB |
| 3× differential, VBAT 2.4 V loaded | about 14 Vpp (VOUT3 ≈ 3 × 2.4 V) | 86 dB min | 78 dB |
| 2× differential, VBAT 2.4 V loaded | about 9.6 Vpp | 82 dB min | 74 dB |

[estimate: SPL rises 20·log10(V/3 Vpp) with drive voltage; real piezos fall short of this at high drive, and the enclosure, port and membrane cost several dB. REQ-006 (≥ 75 dB(A) at 25 cm, ≥ 65 dB(A) at end of life) looks reachable, but only the EVT measurement with a class-2 sound level meter counts.]

## Lifecycle

| Source | Status | Date |
|---|---|---|
| DigiKey | Active, 13-week standard lead time | 2026-11-08 |
| LCSC | in stock (13), Extended | 2026-11-08 |

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Packaging | Date |
|---|---|---|---|---|---|---|---|
| DigiKey | 1.31 | 0.992 | 0.762 | 0.64 [estimate: 500+ cut-tape break 0.63992; next break is the 1,500 reel at 0.5703] | 0.49 [estimate: 7,500 reel break 0.49025] | CT / T&R 1,500 | 2026-11-08 |
| LCSC (C20181991) | 2.5283 | 2.1602 | — | 1.5678 (500+) | 1.5216 (1,500+) | reel 1,500 | 2026-11-08 |

## Stock and lead time

| Source | Authorized stock | Factory lead time | Limits / notes | Date |
|---|---|---|---|---|
| DigiKey | 47,328 | 13 weeks | — | 2026-11-08 |
| LCSC | 13 | — | too few for JLCPCB assembly of 100 | 2026-11-08 |

## CAD models

| Kind | Source | Trust |
|---|---|---|
| Footprint | Same Sky "Recommended PCB Layout" (datasheet p.2) and their PCB footprint download | draw from the datasheet drawing |
| 3D model | Same Sky 3D model link on the datasheet | check against 9.5 × 9.5 × 2.1 mm max |

## Alternatives

| MPN | Class | Difference | Price at 1k | Source |
|---|---|---|---|---|
| CPT-9019S-SMT-TR (Same Sky) | needs change: check datasheet | 3 V, 9 × 9 mm; listed by DigiKey as a substitute | 2.33 at 1 | DigiKey search |
| PKMCS0909E4000-R1 (Murata) | do not use | Last Time Buy | — | dossier |

## Checks against the design

- PAM8904E load ≤ 47 nF: 15.6 nF max, **yes**.
- Max drive 25 Vpp vs 3× differential 18 Vpp max: **yes**.
- Size: 9.5 × 9.5 × 2.1 mm max. Check the stack-up (L-003).
- Port: top. The board needs no sound hole. The enclosure needs a cavity and port over the top face (Q-PB-06).

## Risks

| Risk | Rating | Mitigation |
|---|---|---|
| Low LCSC stock | medium | consign DigiKey parts to JLCPCB, or order an LCSC reel |
| SPL at 25 cm in the enclosure unknown | medium | EVT measurement plan (REQ-006) |
| Moisture-sensitive reflow window (48 h) | low | note for the assembler in the release package |

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| Same Sky datasheet | https://www.sameskydevices.com/product/resource/digikeypdf/cpt-9019a-smt-tr.pdf | 2026-11-08 | read (pdftotext) |
| DigiKey search | https://www.digikey.com/en/products/result?keywords=CPT-9019A-SMT-TR | 2026-11-08 | read |
| LCSC search | https://r.jina.ai/https://www.lcsc.com/search?q=CPT-9019A-SMT-TR | 2026-11-08 | read via reader proxy |
