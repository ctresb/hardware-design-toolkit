# Cost reference: typical figures by line

These are planning figures, collected in November 2026, for a small consumer device (a palm-sized or smaller enclosure, one or two small boards, a LiPo cell). Each figure carries the tag defined in CONVENTIONS.md §6.

- Figures tagged `verified` were read on the vendor's page on that date. Prices and terms change, so re-read the page before you rely on one.
- Figures tagged `estimate` are market ranges. Replace them with quotes (see `templates/rfq.md`).
- Use these numbers to fill `hw/cost/manufacturing.json` when nothing better exists. Copy the tag with the number.

## 1. Electronic parts

- **Distributor price breaks.** Use the catalog break at or below the quantity you actually buy, which is the per-device quantity × units + attrition (`scripts/cost_model.py` does this).
  - Typical breaks are 1, 10, 25, 100, 250, 500, 1k and reel.
  - The 1k and 10k prices are usually tape-and-reel prices. Check that the packaging suffix of the MPN matches.
  - At 10k and above, a franchised quote or a direct quote typically comes in 10–30% below the catalog reel price `[estimate: usual distributor-vs-contract spread]`.
- **Reel fees.** Cut tape is sold from 1 piece. Re-reeled small quantities (for example DigiKey's Digi-Reel) carry a fixed fee of about $7 per reel `[verified: DigiKey product pages, 2026-11-08]`.
- **Supply-constrained parts.** A distributor can stop taking backorders or limit purchases per period. Some memory parts were in that state in late 2026 `[verified: DigiKey product page notices, 2026-11-08]`.
  - A part in that state needs a direct quote and a second source before you commit to a design.
- **Lead times.** Manufacturer lead times on common parts in late 2026 ranged from 4 weeks (pogo pins) to 24–26 weeks (some springs, sensors and LED drivers). MLCCs from a single brand showed 17-week backorders `[verified: DigiKey product pages, 2026-11-08]`.
- **Direct-only parts.** Some parts are not stocked by distributors. Acoustic vents/membranes from the major ePTFE makers, for example, are sold through sales consultation only. Price and MOQ need an RFQ `[verified: Gore acoustic vents page, 2026-11-08]`.

## 2. Bare PCBs

No online calculator could be read without JavaScript or a login. Get real numbers by uploading Gerbers.

| Board | Prototype lot (5–10 panels) | Per board at 1k | Per board at 10k | Tag |
|---|---|---|---|---|
| 4-layer FR4 0.6 mm, ENIG, small (~20×20 mm) | $40–100 | $0.20–0.50 | $0.10–0.30 | `estimate` |
| 2-layer polyimide flex with stiffeners and PSA, ENIG | $50–200 | $0.6–1.5 | $0.3–0.8 | `estimate` |

Several options carry a surcharge over the promotional base price: thin boards, ENIG, black or white mask, filled via-in-pad, steel stiffeners, tight outline tolerance and HDI (laser microvias) `[verified: JLCPCB capability pages, 2026-11-08]`.

## 3. PCB assembly (PCBA)

Some quick-turn assemblers publish their whole tariff. That lets you compute the fee before you have a quote. JLCPCB's Standard PCBA tariff, as published on 2026-11-08 `[verified: https://jlcpcb.com/help/article/pcb-assembly-price]`:

| Fee | Amount | Behaves like |
|---|---|---|
| Setup | $25.56 one side, $51.12 two sides | per order |
| Stencil | $8.21 one side, $16.42 two sides | per order |
| Feeder loading | $1.53 per unique part type | per order |
| Handling | from $14.93 | per order |
| Fixtures (Standard only) | rigid $8.21 each, flex $24.63 each; count steps with quantity: 2 (1–29), 3 (30–99), 5 (100–199), 10 (200–349), 15 (350–499), 20 (500+) | per order |
| Solder joints | $0.0016 (≤50k joints), $0.0013 (≤100k), $0.0012 (≤1M) | per board |
| X-ray, mandatory for BGA/QFN/LGA | per component: $1.64 (1–10), $0.82 (11–50), $0.49 (51–200), $0.33 (201–500), $0.25 (501–1k), $0.16 (1k–3k), $0.082 (3k+) | per board |
| Single-board surcharge | $0.48 per board unless panelized | per board |

The page leaves two things open:
- whether the joint tier applies to the whole order or only marginally;
- whether the X-ray tier counts components or boards.

`templates/manufacturing.example.json` assumes the whole order and counts components. A quote resolves both.

Order limits on the same date: 2–80,000 pieces, both sides. Minimum assembled panel is 70×70 mm with rails and fiducials, so small boards must be panelized. Build time is 4 days or more `[verified: JLCPCB PCBA capabilities page, 2026-11-08]`.

Worked result for a ~20 mm, two-sided, 4-layer board with ~230 joints, ~25 part types and 4 X-ray parts `[estimate: computed from the tariff above]`:

| Quantity | Fee per board |
|---|---|
| 5 | ~$28 |
| 10 | ~$16 |
| 100 | ~$3.2 |
| 1,000 | ~$0.87 |
| 10,000 | ~$0.63 |

- At prototype quantities, X-ray and setup dominate.
- At volume, joints and X-ray set the floor.
- A dedicated EMS quote at 10k is negotiated, not taken from a quick-turn tariff. Sampled X-ray instead of 100% X-ray reduces cost.

Process capability limits that change cost or feasibility (verify each one with the fab for your design):

| Vendor | Capability | Source |
|---|---|---|
| PCBWay | minimum BGA pitch 0.3 mm on rigid, **0.4 mm on flex** | PCBWay assembly capabilities, 2026-11-08 |
| JLCPCB | minimum BGA pitch 0.3 mm; IC lead pitch 0.35 mm (Economic 0.40 mm); parts down to 01005 (Economic 0402) | JLCPCB PCBA capabilities, 2026-11-08 |
| JLCPCB | black/white solder mask needs a 0.13 mm minimum web between pads, against 0.10 mm for other colors | JLCPCB PCB capabilities, 2026-11-08 |
| JLCPCB | 2-layer flex is offered in fixed finished thicknesses (for example 0.11 or 0.12 mm); steel stiffeners are recommended under SMD parts | JLCPCB flex capabilities, 2026-11-08 |

All entries are `[verified]` on the date shown.

## 4. Functional test and programming

| Item | Figure | Tag |
|---|---|---|
| DIY pogo-pin fixture for EVT/DVT (printed nest, 10–15 pogo pins, SWD probe) | $50–300 in parts | `estimate` |
| EMS-built clamshell or pneumatic bed-of-nails, per board type | $500–2,000 | `estimate` |
| Full test/programming jig set for production (RF, audio, charge, seal) | $2–10k | `estimate` |
| Per-unit flashing + functional test | ~1–2 min, about $0.05–0.30 at China labor rates | `estimate` |

Testing through an existing board-to-board connector or the charging contacts avoids test pads on a crowded board.

## 5. Enclosure: prototypes and molding

| Route | Fits | Tooling | Per part | Tag |
|---|---|---|---|---|
| In-house SLA (clear resin, sanded 400→12000 grit or 2K clear coat) | 1–10 | none | material $3–8 + 1.5–3 h labor | finishing method `[verified: Formlabs clear-finishing guide, 2026-11-08]`; cost `estimate` |
| Service-bureau 3D print | 1–50 | none | $20–100 | `[verified: Hubs injection-molding guide, 2026-11-08]` |
| CNC prototype | 1–50 | none | $100–500 | `[verified: Hubs guide, 2026-11-08]` |
| Urethane casting from a polished master | 1–100 | master + silicone mold $400–900, ~15–25 shots per mold | $25–90 | Xometry fits "one to one hundred" `[verified: Xometry urethane casting, 2026-11-08]`; cost `estimate` |
| 3D-printed injection mold | 10–100+ | ~$100 in-house, $1–4k as a service | $4–20 | `[verified: Formlabs injection-molding cost; Hubs guide, 2026-11-08]` |
| Rapid aluminum mold, US on-demand | 100–2,000 | from $1,495; typically $6–15k for a small clear part | $1–5 | "from $1,495", ships "as fast as 7 days", prototype tools guaranteed ≥2,000 shots `[verified: Protolabs injection molding, 2026-11-08]` |
| Aluminum pilot mold | 1k–10k | $3–5k (Hubs); $2–5k for 1k–5k units (Formlabs); up to $10k for 1–2k small parts (Xometry) | $1–5 pilot, cents to $1 at scale | `[verified: Hubs, Formlabs, Xometry, 2026-11-08]` |
| China rapid tool (aluminum 7075 or P20 insert) | ~1k | $3–7k per part, 1 cavity | $0.4–2 | `estimate` |
| Hardened steel (S136/NAK80/Stavax), 2 cavities, China | 10k+ | $12–25k per part | $0.15–0.8 | `estimate` |
| Same, US/EU | 10k+ | $35–70k per part | 2–4× China | `estimate` |

Further rules:

- **Side actions** add 15–30% to the tool, with a minimum of about $1,000–1,500 each `[verified: Hubs guide, 2026-11-08]`.
  - A curved core (for example an arc-shaped tunnel) adds about $3–8k and is fragile `[estimate]`.
  - Avoid it by splitting the feature at the parting line or at the joint between parts.
- **At 1k–10k units, tooling is about 50–70% of the enclosure cost** `[verified: Hubs guide, 2026-11-08]`.
- **Design rules that drive cost** `[verified: Hubs guide, 2026-11-08]`:
  - draft at least 2° (+1–2° for textures);
  - general tolerance ±0.25 mm;
  - thickness changes blended over 3× the difference.
- **Clear optical parts:**
  - SPI A1 polish needs hardened polished steel and adds about $500–2,000 per small tool `[estimate]`.
  - Expect 10–30% cosmetic scrap early in production: gate marks, knit lines, specks `[estimate]`.
  - One clear-ready tool can run clear, black and white with color-change runs ($150–500 per run) `[estimate]`. Purge thoroughly after dark colors.
- **Iterations:** plan 2–3 tool trials (T1→T3).
  - Steel-safe changes cost about $300–2,000 and take 1–2 weeks each `[estimate]`.
  - Lead times: aluminum 3–4 weeks, steel 4–8 weeks (Formlabs); pilot runs 6–8 weeks and steel production 4–6 months from start (Hubs) `[verified, 2026-11-08]`.
- **Machine time** in China is about $5/h in one published example. A 60 s single-cavity cycle is then about $0.08 per part `[verified: FirstMold cost guide, 2026-11-08]`.

## 6. Metal parts, magnets, adhesives, marking

| Item | Figure | Tag |
|---|---|---|
| Photo-etched stainless parts | phototool "less than $350", made in ≤2 days; tools do not wear | `[verified: Wikipedia, Photochemical machining (section unsourced there)]` |
| Photo-etched part price | $1–3 at 100, $0.20–0.60 at 1k, $0.05–0.20 at 10k | `estimate` |
| Progressive stamping die | $3–12k in China; parts $0.02–0.08 at 10k+ | `estimate` |
| Hard gold (Au-Co ~0.76 µm over Ni) | $0.10–0.50 per part at 1k; lot charge $150–500 | `estimate` |
| Skin-contact metal | nickel under worn gold is a nickel-release risk (EU REACH Annex XVII / EN 1811); use thicker gold, a Pd underlayer or bare 316L | `estimate`; check with a lab |
| NdFeB magnets, small discs | $0.03–0.08 each at 1k+ | `estimate` |
| Die-cut adhesive ring | die $100–500; $0.03–0.15 per part at 1k–10k | `estimate` |
| Laser marking at a molder | $0.05–0.30 per part + $50–150 setup | `estimate` |

## 7. Batteries

| Item | Figure | Tag |
|---|---|---|
| Catalog thin LiPo cells | e.g. 2.7×19×21 mm, 65 mAh: $7.50 (1–19), $5.75 (20–99) | `[verified: PowerStream thin Li-ion page, 2026-11-08]` |
| Custom cell terms | "a tooling charge and minimum order of 2000 pieces" | `[verified: PowerStream, 2026-11-08]` |
| Custom shapes and high-voltage chemistry | offered (shaped cells, charge to 4.48 V); no MOQ or NRE published | `[verified: Grepow shaped and custom battery pages, 2026-11-08]` |
| Custom cell NRE | $500–3,000 | `estimate` |
| Custom cell MOQ | 1,000–5,000 cells | `estimate` |
| Custom cell price, ~70 mAh with PCM | $1.5–3 at 1k, $0.8–1.8 at 10k | `estimate` |
| Custom cell samples | $20–100 each, in 3–6 weeks | `estimate` |

Below the MOQ, a custom cell costs either the whole MOQ or paid samples. That makes custom cells expensive at 100 units. Use a catalog cell for EVT, and order the custom cell only after the power budget is measured (`battery-and-power`).

## 8. Final assembly, packaging, freight

| Item | Figure | Tag |
|---|---|---|
| China box-build: final assembly, programming, functional test, seal test, pack | $3–8 per unit at 1k, $1–3 at 10k | `estimate` |
| Box-build MOQ effect | lots of ~100 often carry a setup or MOQ that doubles the unit cost | `estimate` |
| Retail packaging (small rigid or paperboard box with insert) | $0.80–2.50 at 1k, $0.40–1.20 at 10k; artwork and cutting die $200–800 once | `estimate` |
| Air express with a lithium battery (UN3481, PI 967 Section II) | ~$6–12 per kg plus a dangerous-goods surcharge; sea LCL pays off from a few thousand units | `estimate` |

## 9. Certification lines (owned by `compliance-planner`)

Take certification costs from `hw/compliance.md`. The one figure verified in this research:

| Bluetooth SIG membership tier (effective 2026-03-01) | Annual fee | Qualification fee per product |
|---|---|---|
| Adopter | $0 | $12,000 |
| Contributing Adopter, small | $3,500 | $8,000 for the first qualification of the membership year |
| Associate, small | $11,250 | $6,000 |

Source: Bluetooth SIG fee table `[verified, read 2026-11-08]`. One product in a year therefore costs $11,500 on the Contributing Adopter small tier, the cheapest route.

## 10. Rules of thumb (label them as such)

- Recurring cost falls roughly 3–5× from 10 to 10k units. NRE spread over the launch batch often dominates below 1k.
- Retail price ≈ 3–5× landed cost for a consumer device sold through channels; ≈ 2–3× for direct sales.
- Every estimate that moves the total by more than about 5% needs an RFQ before a financial plan uses it.
