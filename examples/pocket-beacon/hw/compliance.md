# Compliance plan — Pocket Beacon

> Planning aid, not legal advice. Figures are tagged `[verified: …]`, `[estimate: …]` or `[assumption]`. Confirm every row with an accredited lab or certification body before you commit money or dates.

**Date:** 2026-11-08. **Rules file checked:** 2026-11-08 (`hw/compliance/rules.local.json` = the toolkit rules plus three local rules, see "Local rules"). **Traits:** `hw/compliance/traits.json`. **Rows:** `hw/compliance/matrix.md` (32 rows, 4 markets + global).

## Answer first

- **Can it be sold in US, EU, UK and Brazil?** Yes, as designed. A BLE device at 0 dBm with a user-replaceable CR2032 avoids the hardest rows: no SAR, no mains adapter, no EU battery-removability conflict, no custom-cell UN 38.3.
- **Blocking items:**
  - **Brazil:** no sale or import for sale before Anatel homologation through an OCD, with a Brazilian applicant (CNPJ). The launch batch therefore does not go to Brazil (D-601).
  - **US coin-cell rule:** every unit sold in the US needs a compartment and warnings that pass ANSI/UL 4200A-2023, mandatory through 16 CFR 1263 (F-501). The compartment uses option 1, securement that needs a tool: a cell door held by two captive screws (D-511, superseding the coin bayonet of D-026). A small screwdriver ships in the box or is named in the instructions. The test report is on the DVT critical path.
- **Design risks:** none open. The two that usually hurt are closed by earlier decisions:
  - EU battery removability (art. 11): the cell is user-replaceable (D-002, D-511).
  - PFAS: the acoustic membrane is chosen PFAS-free (D-603).
- **Design changes that save the most:** keep TX at 0 dBm (RF exposure is a report, not a test); reuse TI's qualified BLE stack unmodified (Bluetooth listing becomes a declaration); keep metal off the outside (no nickel-release test).
- **Budget:** USD 20.3k–46.5k for the US launch (global rows + US), plus USD 12.75k–82k for EU, UK and Brazil [estimate]; total USD 33.05k–128.5k. The only verified fee is the Bluetooth SIG fee (USD 11.5k–12k). The high end is a ceiling: one lab session covers FCC 15C/15B, EN 300 328, EN 301 489, EN 62368-1 and EN 62479 together.
- **Longest path:** about 12–20 weeks from DVT units with final RF firmware to the last certificate [estimate]: pre-scan 1–2 weeks → formal tests 4–8 weeks (EU RED and EN 18031 in parallel with FCC) → Anatel 4–10 weeks after the test reports.

## Per-market requirements

The rows are in `hw/compliance/matrix.md`. Summary:

| Scope | Rows | Cost (USD) | Longest single lead (weeks) | Sold from |
|---|---|---|---|---|
| All markets | 5 | 13,300–22,000 | 4 | launch batch (100) |
| United States | 6 | 7,000–24,500 | 6 | launch batch (100) |
| European Union | 12 | 9,650–68,700 | 8 | 1k run |
| United Kingdom | 7 | 500–20,500 | 4 | 1k run (reuses the EU reports) |
| Brazil | 2 | 2,900–9,300 | 10 | 1k run, after homologation |

The sum by scope double-counts three rows shared by several markets (RoHS/REACH, nickel, RF exposure). The budget above counts them once.

### Topics the brief asked for

| Topic | Applies? | What it means for Pocket Beacon | Evidence |
|---|---|---|---|
| FCC Part 15C (15.247 DTS) + 15B | yes | TCB grant, FCC ID in the manual and on the lid (tiny label rules); test-mode firmware for continuous TX/RX | estimate |
| ISED (Canada) | no | Canada is not a target market; ISED adds about USD 2–6k if added later | estimate |
| CE RED: EN 300 328, EN 301 489-1/-17, EN 62368-1, EN 62479 | yes | self-declaration (Module A) with harmonised standards applied in full | estimate |
| RED art. 3.3(d)(e): EN 18031-1 and -2 | yes | the beacon talks to the internet "via any other equipment" (the phone app), so it is internet-connected radio equipment under (EU) 2022/30 art. 1(1); it processes location and traffic data, so art. 1(2) also applies | [verified: eur-lex CELEX:32022R0030 art. 1, read 2026-11-08] for the scope; cost estimate |
| UKCA | yes | the RED reports carry over; UK declaration and UK importer; PSTI statement (no default passwords, a reporting contact, a support period) | estimate |
| Anatel | yes, BLOCKING | OCD homologation, restricted-radiation equipment (Resolution 715/2019); label number on the packaging and manual if the product is too small | estimate (portals not read) |
| Bluetooth SIG | yes | Contributing Adopter (small) USD 3,500 per year + USD 8,000 first qualification, or Adopter USD 12,000 | [verified: bluetooth.com fee table, 2026-11-08] |
| US Reese's Law, 16 CFR 1263 / ANSI/UL 4200A-2023 | yes | compartment option 1 (securement by tool: two captive screws, D-511), preconditioning and abuse tests, warnings on the product, the packaging and the instructions | [verified: eCFR 16 CFR 1263 and CPSC final rule, read 2026-11-08 (F-501)]; test cost estimate |
| US child-resistant packaging of loose cells (16 CFR 1700.15) | not triggered | the CR2032 ships installed, in ship mode; spare cells are not in the box. If a spare is added, it needs child-resistant packaging | estimate |
| EU GPSR + EN IEC 62368-1 clause 4.8 | yes | EU responsible person; coin-cell compartment and warnings assessed in the EN 62368-1 report | estimate |
| Button-battery warnings | yes | warning symbol and text on the lid (molded), the packaging and the leaflet in each market language | estimate |
| EU Battery Regulation (EU) 2023/1542 | yes, light | the cell is user-replaceable, so art. 11 is met; still needed: battery labelling (cell type), producer registration and take-back per country | estimate |
| DULT / unwanted tracking | not mandatory in v1 | the IETF draft makes its practices REQUIRED for small location-enabled accessories; v1 reports no location, so it is outside the definition. A finder-network v2 is inside. The firmware implements address rotation and the 12 s ring now (D-604) | [verified: draft-ietf-dult-accessory-protocol-01, 2026-10-27, read 2026-11-08] |
| Privacy | app scope | no microphone, no camera, no GNSS. BLE privacy: resolvable private addresses, rotated (D-604). The app stores the owner's last-seen location: GDPR and LGPD apply to the app, not to the hardware | estimate |
| RoHS, REACH, WEEE | yes | supplier declarations (all parts are from established makers); WEEE registration per EU country and in the UK; Brazil reverse logistics | estimate |

## Design levers

| Lever | Decision | Saves | Decision log |
|---|---|---|---|
| Module or chip-down radio | chip-down (CC2340R52), because no BLE module fits the board and the cell budget | module would save FCC 15C (USD 5–12.5k) but costs USD 2–4 per unit and 3–4 mm of board | D-012 |
| TX power cap | 0 dBm default, firmware maximum +4 dBm | RF exposure stays a low-power report (EN 62479; FCC exemption) | D-011 |
| Qualified stack | TI's qualified BLE stack, unmodified | Bluetooth listing as a declaration, no lab tests | D-602 |
| Battery removability (EU art. 11) | user-replaceable CR2032 behind a door with two captive screws (commonly available screwdriver) | no legal opinion, no redesign | D-002, D-511 |
| Mains adapter in the box | none | no charger certification in any market | D-002 |
| Openings and sealing | one sound port with a membrane, one sealed button membrane, one O-ring lid | fewer IP67 failure points; IEC 60529 test once | D-027 |
| Acoustic membrane material | PFAS-free mesh preferred (SAATI), ePTFE as the fallback | avoids the PFAS trend risk | D-603 |
| Metal on the outside | none (keyring passes through a molded slot) | no nickel-release test (REACH entry 27) | D-603 |
| Market sequencing | US first (launch batch 100), EU + UK + BR for the 1k run | moves USD 12.75k–82k of NRE out of the launch batch | D-601 |

## Schedule hooks for the roadmap

| Item | Needs | Earliest start | Duration | Feeds |
|---|---|---|---|---|
| UN 38.3 test summary of the CR2032 | none: from Panasonic | now | 0–1 week [estimate] | any air shipment of finished units (UN3091, PI 970 Section II) |
| Pre-scan | EVT units with test-mode firmware | after EVT bring-up | 1–2 weeks [estimate] | the DVT board revision |
| UL 4200A test (coin-cell compartment) | DVT units from T1 tools | DVT | 2–6 weeks [estimate] | US sale |
| Formal radio/EMC/safety tests (FCC + RED + EN 18031) | DVT units with final RF settings | after the pre-scan passes | 4–8 weeks [estimate] | US sale (FCC), EU/UK sale |
| IP67 test | DVT units | DVT | 1–2 weeks [estimate] | the IP67 claim |
| Bluetooth SIG listing | final hardware + stack version | with the formal tests | 1–4 weeks [verified fee; estimate duration] | any sale |
| Anatel homologation | test reports + Brazilian applicant | after the formal tests | 4–10 weeks [estimate] | Brazil sale |

## What was verified

| Fact | Source | Date |
|---|---|---|
| Bluetooth SIG fees (Adopter USD 12k; Contributing Adopter small USD 3.5k/year + USD 8k) | bluetooth.com qualification and listing fees (in effect since 2026-03-01) | 2026-11-08 |
| 16 CFR 1263 makes ANSI/UL 4200A-2023 mandatory; compartment options; preconditioning and abuse tests | eCFR 16 CFR 1263; CPSC final rule (F-501) | 2026-11-08 |
| EN 18031 scope: radio equipment that communicates "directly or via any other equipment" over the internet; personal data and location data under art. 1(2) | eur-lex CELEX:32022R0030, art. 1 | 2026-11-08 |
| DULT draft requirements (60 phon at 25 cm, 5–30 s ring, 12 s recommended; address rotation 15 min / 24 h; separated mode after 30 min) | datatracker.ietf.org draft-ietf-dult-accessory-protocol-01 (2026-10-27) | 2026-11-08 |

Everything else is an estimate from the toolkit rules. Anatel's and FCC's portals were not read in this session.

## Local rules

`hw/compliance/rules.local.json` adds three things to the toolkit's `rules.json` (reported to the toolkit as a gap):

1. UN 38.3 now also triggers for the chemistry `coin-cell` (a CR2032 is a lithium-metal cell). For a catalogue cell the cost is zero.
2. A new EU/UK row for EN IEC 62368-1 clause 4.8 (equipment with coin cells).
3. A new global row for DULT expectations on item finders.

## RFQs to send

1. Lab A (for example TÜV SÜD or Element): full package FCC 15C/15B, EN 300 328, EN 301 489-1/-17, EN 62368-1 (clause 4.8), EN 62479, EN 18031-1/-2, IEC 60529 IP67, UL 4200A. Attach `traits.json` and the block diagram.
2. Lab B (for example Bureau Veritas or UL Solutions): the same, for comparison.
3. Two Brazilian OCDs for Anatel, with a local applicant.
4. Panasonic (via DigiKey or direct): the CR2032 UN 38.3 test summary and SDS.
5. An EU authorised representative or responsible-person service (GPSR, WEEE, batteries, packaging) that covers several countries.

The cost side of these RFQs is in `hw/cost/rfq.md` (request 1).

## Open questions

- Q-BZ-01 (product owner): confirm the market sequencing (US launch, then EU/UK/BR at 1k), or pay the full certification set before the launch batch.
- Q-BZ-02 (firmware): implement the DULT-ready behaviors (address rotation, 12 s ring, ≥ 60 phon) and a test mode for the lab before the pre-scan.
- Q-BZ-03 (enclosure-engineer): mold the coin-cell safety icons and "CR2032 +" on the lid; leave space for the FCC ID and the CE/UKCA marks on the lid; if they do not fit at a legible size, the rules for very small devices allow the manual and the packaging instead (confirm with the lab).
