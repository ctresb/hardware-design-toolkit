# Suppliers by process

This is a starting list of established vendors, compiled in November 2026. It is not an endorsement.

Before you recommend a vendor:
- check that it still operates and still offers the capability (companies close, merge and change offers);
- check its published capability against the design;
- recommend 2–4 vendors per process, so that the user can compare quotes.

Never add an unknown marketplace seller to this list.

## Electronic parts (authorized channels)

| Channel | Use | Notes |
|---|---|---|
| DigiKey, Mouser | prototypes to mid volume | broad stock, cut tape from 1 piece, clear lifecycle and lead-time data |
| Arrow, Avnet, Future Electronics, TTI | volume quotes, supply programs | franchised; ask for a quote at 1k and 10k |
| Farnell / Newark / element14, TME, RS | regional stock (EU/UK, worldwide) | |
| LCSC | parts for JLCPCB turnkey assembly; low-cost passives | franchised for many Asian brands; check franchise status per manufacturer |
| Manufacturer direct (sales or distributor locator) | parts not stocked by distributors; volume pricing; samples | e.g. acoustic membranes, custom cells, some sensors |
| Octopart, FindChips | price and stock search across distributors | aggregators. Buy from the listed authorized distributor, not from a broker row |

- **Brokers.** Brokers and independent sellers are for traceable prototype emergencies only.
  - Never use a broker for production.
  - A broker row in a stock aggregator does not make a part "available".

## PCB fabrication and assembly (quick-turn and prototype)

| Vendor | Region | Notes to verify for your design |
|---|---|---|
| JLCPCB | CN | public PCBA tariff; Standard PCBA for 0201, two-sided and thin boards; rigid and flex fab; minimum assembled panel 70×70 mm |
| PCBWay | CN | rigid, flex, rigid-flex; minimum BGA pitch 0.4 mm on flex (0.3 mm rigid); flex assembly by email request |
| NextPCB | CN | turnkey assembly; claims fine-pitch BGA and flex assembly; AXI on hidden-joint packages |
| Seeed Fusion | CN | PCBA with free DFM/DFA review and functional testing offers |
| CircuitHub | US | quick-turn assembly, robotic factory |
| MacroFab | US | PCBA and box-build, platform pricing |
| Screaming Circuits | US | quick-turn prototype assembly |
| Sierra Circuits | US | HDI, fine-pitch, quick-turn |
| Bittele / 7PCB | CA | turnkey PCBA |
| Eurocircuits | EU | pooling, no tooling charges on pooled orders; HDI pool |
| AISLER | EU | small-batch boards and stencils |
| OSH Park | US | low-cost 2/4-layer prototype boards (no assembly) |

All rows are as of November 2026.

- **Defunct.** Tempo Automation (US) cut to a skeleton staff and was delisted in 2023. Do not recommend it.
- **Ownership.** Check current ownership and service before naming Advanced Circuits / AdvancedPCB.
- **Local EMS.** Many countries have contract manufacturers for volume. They quote rather than publish prices and seldom serve prototype quantities. Approach them for local-content or 10k+ builds.

## Contract manufacturing and box-build (volume)

- Chinese EMS with box-build, firmware programming and functional test: ask NextPCB, PCBWay and Seeed for referrals, or use an established sourcing agent.
- Large EMS (Flex, Jabil, Foxconn and similar) become relevant from tens of thousands of units a year.
- Ask every EMS for:
  - its IPC-A-610 class;
  - its test capability (ICT, FCT, RF, audio, leak test);
  - its programming method;
  - its packaging capability;
  - references for wearables or consumer products.

## Enclosure prototyping and molding

| Vendor | Offer |
|---|---|
| Protolabs | instant-quote aluminum molds (from $1,495, from ~7 days); on-demand production tools; CNC and 3D printing |
| Xometry | molding, CNC, urethane casting (clear grades), sheet metal; network of shops |
| Protolabs Network (Hubs) | molding and CNC via a network |
| Fictiv | molding and CNC, US/China |
| RapidDirect, HLH Rapid, Star Rapid, FirstMold | China rapid tooling and production molding; DFM with mold-flow analysis |
| Formlabs (in-house printers) | SLA prototypes, including clear resin; printed molds for 10–100+ parts |

- Ask for a DFM report with mold-flow analysis from 3–4 shops. For clear parts, the report must show gate location and knit lines.
- Domestic toolmakers in your country can be competitive for steel tools. Compare an imported tool with landed taxes against importing molded parts.

## Batteries (cells and packs)

| Vendor | Notes |
|---|---|
| Grepow | custom shapes (curved, round, L, D, thin to 0.5 mm), high-voltage chemistry, custom protection; RFQ for MOQ and NRE |
| PowerStream | US; catalog thin cells with published prices; custom cells need tooling + 2,000 MOQ |
| EEMB, other Shenzhen/Huizhou pouch makers | catalog and custom pouch cells; RFQ |
| VARTA, Jauch, Renata | Western/Japanese brands; coin-type Li-ion and premium cells; higher price and MOQ |
| Adafruit, SparkFun | catalog cells with protection, for dev kits and EVT only |

Every cell vendor must supply a UN38.3 test summary and an IEC 62133-2 report (or CB certificate) for the exact cell and pack.

## Metal parts, plating, magnets, membranes, cords, packaging

| Process | Where to ask |
|---|---|
| Photo-etching (stainless, copper alloys) | Fotofab, Tech-Etch, Precision Micro, Chinese PCM shops |
| Laser cutting / small metal parts | SendCutSend, OSHCut (US), local laser shops |
| Stamping dies, deep drawing | regional stamping shops; China for dies |
| Hard-gold and selective plating | regional plating houses; ask for nickel-free or Pd underlayer options for skin contact |
| NdFeB magnets | K&J Magnetics, supermagnete (EU), established Chinese magnet factories (grade certificate, coating, tolerance) |
| Acoustic and vent membranes (ePTFE) | W. L. Gore (sales consultation), SAATI, Nitto (TEMISH), Donaldson (Tetratex); die-cutters supply finished vents |
| Pressure-sensitive adhesives and die-cuts | 3M and tesa converters (die-cutting shops) |
| Cords, lanyards, braids | narrow-fabric and cord makers; ask for pull-strength data and skin-contact declarations |
| Retail packaging | packaging printers that supply dielines, structural samples and FSC paper |

## How to judge a vendor quickly

- The vendor publishes its capabilities, certifications (ISO 9001, IATF if relevant, IPC class) and a physical address.
- It answers an RFQ with a quote that itemizes NRE, unit price per tier, lead time and payment terms.
- It accepts a small paid sample or first article before volume.
- It is referenced by established companies or communities (forums, reviews, case studies). One marketing page is not enough.
