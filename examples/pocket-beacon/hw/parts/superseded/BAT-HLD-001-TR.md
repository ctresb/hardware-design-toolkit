---
mpn: BAT-HLD-001-TR
aliases: BAT-HLD-001; BAT-HLD-001-NO
manufacturer: TE Connectivity (Linx)
lcsc: C7501066
function: SMD retainer for one CR2032 coin cell; negative contact is a PCB pad
package: SMD retainer, 2 solder tails + PCB negative pad
size_max_mm: 23.1x21.3x4.4
supply_range_v: -
io_range_v: -
typ_current_ma: 0
peak_current_ma: 0
lifecycle: production
lifecycle_distributor: Active
key_specs: CR2032 (DigiKey also lists 2025); height 4.2 mm nominal; phosphor bronze T=0.25 mm, bright nickel; -40 to 125 C
distributors: DigiKey=https://www.digikey.com/en/products/detail/te-connectivity-linx/BAT-HLD-001-TR/4876924; JLCPCB/LCSC=https://jlcpcb.com/partdetail/C7501066
price_1: 0.50
price_10: 0.50
price_100: 0.50
price_1k: 0.475
price_10k: 0.475
lead_time_wk: 5
stock_snapshot: 93358 @ DigiKey 2026-11-08; 1681 @ LCSC 2026-11-08 (C7501066, bulk BAT-HLD-001); 12 @ LCSC 2026-11-08 (C20607187, -TR)
alternatives: 3034TR (needs change: Keystone footprint, 4.1 mm high, cheaper, recommended); BU2032SM-JJ-GTR (needs change: 5.33 mm high, closed holder)
evidence: verified
source_date: 2026-11-08
notes: LCSC carries the bulk BAT-HLD-001 (C7501066, 1681 pcs), not the -TR reel (12 pcs); enough for 10 + 100 units, not for 1k
---

# BAT-HLD-001-TR: CR2032 SMD retainer (TE Connectivity / Linx)

## Identity

- Manufacturer: TE Connectivity, Linx brand.
- Orderable MPNs on drawing `C-BAT-HLD-001-xx` rev E1 (2023-11-15): `BAT-HLD-001` (bulk), `BAT-HLD-001-NO` (bulk), `BAT-HLD-001-TR` (tape and reel, 650 per reel, 32 mm embossed tape, 20 mm pitch) [verified: TE customer drawing C-BAT-HLD-001-xx rev E1, read through r.jina.ai, 2026-11-08].
- Rev E increased battery retention ("7.6 dimension was 8.6, 2.2 was 1.9"). Rev E1 updated the recommended PCB layout [verified: same drawing, revision block].

## Why this part

REQ: a user-replaceable CR2032 with reliable contact, SMT-assembled at JLCPCB. An open retainer adds the least height over the cell (the PCB is the negative contact).

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Cell | CR2032 (DigiKey also lists 2025) | — | [verified: TE product page; DigiKey attributes, 2026-11-08] |
| Material | phosphor bronze, T = 0.25 mm, bright nickel finish | — | [verified: drawing title block] |
| Operating temperature | −40 °C to 125 °C | — | [verified: TE product page] |
| Weight | 2.92 g (field labelled "Battery Weight") | — | [verified: TE product page; label is ambiguous] |
| Contact resistance, retention force | not read | — | product spec 108-161665 returned 403 |

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Length | 22.9 mm | 23.1 mm | [verified: drawing 22.9; estimate: max from title-block 1-place tolerance ±0.2] |
| Width | 21.1 mm | 21.3 mm | same |
| Height above board | 4.2 mm | 4.4 mm | [verified: drawing 4.2, DigiKey 4.20 mm; estimate: max ±0.2] |

Recommended footprint on the drawing: 2 tail pads 5.2 × 1.8 mm, 17.0 mm and 21.0 mm reference spans, 10.5 mm / 11.9 mm centre dimensions [verified: drawing; pcb-engineer must redraw from the PDF, not from this list].

## Power

Passive part. The negative contact is a gold (ENIG) PCB pad under the cell centre.

## Lifecycle

| Source | Status | Date |
|---|---|---|
| Manufacturer (te.com) | "Active", but the same page says "This product is not currently available" | 2026-11-08 |
| DigiKey | Active | 2026-11-08 |

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Packaging | Date |
|---|---|---|---|---|---|---|---|
| DigiKey | 0.50 | 0.50 | 0.50 | 0.475 | 0.475 | CT to 649, TR 650+ (no higher break listed) | 2026-11-08 |
| LCSC / JLCPCB C7501066 (BAT-HLD-001 bulk) | 0.9617 | 0.7834 | 0.6068 | 0.5267 | — | bag | 2026-11-08 |
| LCSC C20607187 (-TR) | 1.4409 | 1.1841 | 0.8848 | 0.7834 | — | reel | 2026-11-08 |

## Stock and lead time

| Source | Authorized stock | Factory lead time | Limits / notes | Date |
|---|---|---|---|---|
| DigiKey | 93,358 | 5 weeks | — | 2026-11-08 |
| Arrow | 13,650 | — | quoted on te.com | 2026-11-08 |
| JLCPCB C7501066 | 1,681 (1,594 orderable) | — | Extended part | 2026-11-08 |

## CAD models

| Kind | Source | Trust |
|---|---|---|
| Footprint | TE drawing rev E1 recommended layout | redraw from PDF; check the negative pad size |
| 3D model | TE STEP (te.com document delivery, blocked to scripts) | download by hand |

## Alternatives

| MPN | Class | Difference | Price at 1k | Source |
|---|---|---|---|---|
| Keystone 3034TR | needs change: footprint | 21.2 × 23.1 × 4.1 mm, ultra-low-profile retainer designed for CR2032; DigiKey 121k + 316k factory; JLCPCB C5213768 (644 pcs) | 0.2733 | [verified: Keystone catalog p.11; DigiKey 2026-11-08] |
| MPD BU2032SM-JJ-GTR | needs change | 5.33 mm high, 20-week lead time | 0.66 (2k reel) | [verified: DigiKey 2026-11-08] |
| Q&J / Lian Xin CR2032 retainers on LCSC | not recommended | unknown makers | 0.05–0.24 | [verified: JLCPCB API listing; vendor trust rule] |

## Checks against the design

- Rail: passive.
- Size: 23.1 × 21.3 mm fits a 28 mm board only if the board's other parts sit outside the retainer, or on the opposite side. Stack: PCB + 4.4 mm.
- Fab: SMT tails; JLCPCB can place it (Extended, MSL 1).

## Risks

| Risk | Rating | Mitigation |
|---|---|---|
| LCSC stock covers only ~1.5k units | medium | consign DigiKey reels for 1k+, or switch to 3034TR |
| Upside-down cell insertion reverses polarity | medium | keep Q1 reverse-polarity FET; polarity mark in the molded pocket |
| Retention spec unread (108-161665 blocked) | low | drop test on prototypes |

## Conflicts between sources

| Field | Value A (source) | Value B (source) | Decision and reason |
|---|---|---|---|
| Lifecycle | Active (TE status field) | "not currently available" (TE page text) | production: distributors hold >100k and the drawing was revised in 2023 |
| Height | 4.2 mm (drawing) | 4.20 mm (DigiKey) | agree |
| BOM estimate | 23.0 × 21.0 × 4.3 mm (BOM) | 22.9 × 21.1 × 4.2 mm nominal (drawing) | drawing; maxima per tolerance |

## Open questions and RFQs

- Q-PB-01 answered: see `hw/agents/2026-11-08-research-power-mech.md` (recommendation: Keystone 3034TR).

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| TE customer drawing C-BAT-HLD-001-xx rev E1 | te.com DocumentDelivery (via r.jina.ai) | 2026-11-08 | read (direct fetch: 403 Access Denied) |
| TE product page | https://www.te.com/en/product-BAT-HLD-001-TR.html (via r.jina.ai) | 2026-11-08 | read |
| TE product spec 108-161665, test report 501-161721 | te.com DocumentDelivery | 2026-11-08 | not tried after 403 on drawing |
| DigiKey product page | https://www.digikey.com/en/products/detail/te-connectivity-linx/BAT-HLD-001-TR/4876924 | 2026-11-08 | read |
| JLCPCB part C7501066 | https://jlcpcb.com/partdetail/C7501066 | 2026-11-08 | read |
| LCSC API C7501066, JLCPCB search API | wmsc.lcsc.com / jlcpcb.com API | 2026-11-08 | read |
