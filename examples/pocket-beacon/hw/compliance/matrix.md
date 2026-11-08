# Certification matrix — Pocket Beacon (fictional toolkit proof of concept): BLE item finder on a user-replaceable CR2032

> Planning aid, not legal advice. Rules, fees and dates change. Every row must be confirmed with an accredited lab, certification body or regulator before you rely on it. Rules file checked 2026-11-08. Costs are in USD. EUR ranges were converted at about 1.1 USD/EUR and BRL at about 5.5 BRL/USD [assumption].

> Project-local rules applied (rules.local.json): replaced un38-3, replaced coin-cell-62368, replaced dult-item-finder.

Traits: markets US, EU, UK, BR; radios ble; module pre-certified: no; battery coin-cell; body-worn: no.

## Read first

- **BLOCKING:** Brazil: Anatel homologation through an OCD (restricted-radiation equipment), Resolution 715/2019.
- **CRITICAL PATH:** UN 38.3 transport tests and UN 38.3 test summary for every lithium cell/battery shipped.

## Summary

| Scope | Rows | Cost range (USD) | Longest single lead time (weeks) |
|---|---|---|---|
| All markets | 5 | $13,300–22,000 | 4 |
| United States | 6 | $7,000–24,500 | 6 |
| European Union | 12 | $9,650–68,700 | 8 |
| United Kingdom | 7 | $500–20,500 | 4 |
| Brazil | 2 | $2,900–9,300 | 10 |
| **Total, all target markets (each row once)** | 26 | $33,050–128,500 | 10 |

A market's row lists everything that market requires, so a requirement shared by several markets appears in each of them (5 shared: rohs-reach, pfas, eu-red-rf-exposure, nickel-skin, coin-cell-62368). The bold total counts each requirement once; do not add the market rows. Tests in one lab session can overlap, so the real total is often lower; the high end is a budget ceiling, not a quote.

## All markets

| Requirement | Area | Cost (USD) | Lead time (weeks) | Evidence | Notes | Design levers |
|---|---|---|---|---|---|---|
| Bluetooth SIG qualification and listing | radio | $11,500–12,000 | 1–4 | verified | Required for any product that uses Bluetooth or the Bluetooth name, even when it reuses a qualified chip and stack. Adopter: free membership, USD 12,000 per product. Contributing Adopter (small): USD 3,500 per year plus USD 8,000 for the first qualification of the membership year. A 128-bit custom UUID is free; a 16-bit UUID (USD 3,750) or a Company ID (USD 1,250) is optional. | Reuse the chip vendor's qualified controller and host stack without modification, so the qualification is a declaration and needs no lab tests. |
| UN 38.3 transport tests and UN 38.3 test summary for every lithium cell/battery shipped | battery | — | 0–1 | estimate | CRITICAL PATH. A custom cell does not inherit the vendor's existing reports: each new model needs its own tests before it can fly. Ask the cell vendor to include UN 38.3, the test summary and the MSDS in the cell NRE. Air shipping follows IATA PI 965–970 (UN3480/3481/3090/3091); couriers charge dangerous-goods surcharges. LOCAL PATCH (Pocket Beacon): a lithium-metal coin cell (CR2032) also needs a UN 38.3 test summary for shipping; for a catalogue cell it comes from the cell maker at no cost. | Choose a catalogue cell that already has UN 38.3 for prototypes. |
| IP rating test to IEC 60529 (only if you claim an IP code) | ingress | $800–3,000 | 1–2 | estimate | Not a legal requirement, but a claim you make must be backed by a test. Run in-house immersion and pressure-decay pre-tests first. A sealed device without a vent needs pressure and temperature cycling too. | Fewer openings: molded contacts, membranes, adhesive seals. |
| Pre-compliance scan at a lab on EVT/DVT units (radiated emissions, conducted, ESD IEC 61000-4-2, radio) | process | $1,000–4,000 | 1–2 | estimate | A day or two of chamber time before formal tests. Failing the formal test costs a board revision and a retest, which costs more than the pre-scan. | — |
| Unwanted-tracking expectations for item finders (IETF DULT accessory protocol draft; Apple/Google industry specification) | ecosystem | $0–3,000 | 0–4 | verified | The draft makes its best practices REQUIRED for small, not easily discoverable location-enabled accessories: sound maker >= 60 phon at 25 cm, 5-30 s (12 s recommended); address rotation every 15 min near the owner and every 24 h when separated; separated mode after 30 min; a physical disable; a readable identifier. A tag without any location report to its owner is outside the definition, but joining a finder network brings it in. The cost range is firmware work. | Keep v1 without location reporting, and implement address rotation and the 12 s / >= 60 phon ring now so a finder-network v2 needs no hardware change. |

## United States (US)

| Requirement | Area | Cost (USD) | Lead time (weeks) | Evidence | Notes | Design levers |
|---|---|---|---|---|---|---|
| FCC Part 15 Subpart C certification (intentional radiator, e.g. 15.247) via a TCB | radio | $5,000–12,500 | 3–6 | estimate | Chip-down radio. Covers lab tests (US labs cost more than accredited labs in Asia), the TCB grant fee and a one-time FCC grantee code. The product carries an FCC ID; small devices can put it in the manual or on an e-label if they have a screen. | A pre-certified module with modular approval removes this row if you follow the module grant's antenna and layout conditions. |
| FCC Part 15 Subpart B (unintentional radiator), SDoC | emc | $1,000–3,000 | 1–3 | estimate | Every product with a clock or digital logic. Usually tested in the same lab session as 15C. | — |
| RoHS (EU 2011/65 + 2015/863, China RoHS marking) and REACH SVHC declarations | materials | $0–2,000 | 1–4 | estimate | Mostly supplier declarations plus an optional XRF screen. China RoHS needs a hazardous-substance table and a marking. In the US this row is a retailer requirement, not federal law (California has its own RoHS-like rules). | Ask every supplier for RoHS/REACH declarations when you order samples. |
| PFAS restrictions (EU REACH restriction proposal; US state laws, e.g. Minnesota, Maine) | materials | — | — | estimate | TREND RISK, not a certification. ePTFE acoustic or vent membranes, PTFE coatings and some lubricants are fluoropolymers. Bans and reporting duties are phasing in by state and region; check them before volume production. | Qualify a PFAS-free membrane (for example polyester or other non-fluorinated mesh) as an alternative early. |
| US Reese's Law (16 CFR 1263): child-resistant compartments and warnings for button/coin cells | safety | $1,000–5,000 | 2–6 | estimate | Covers consumer products that contain or ship with button or coin cells, including rechargeable ones. Australia has similar mandatory standards. | A secured battery door (tool or two simultaneous actions) designed in from the start. |
| California Proposition 65 warnings for listed substances (for example some plasticisers, lead in brass) | materials | $0–2,000 | 0–3 | estimate | Mostly a materials-declaration exercise. Cables and soft-touch plastics are the usual sources. | — |

## European Union (EU)

| Requirement | Area | Cost (USD) | Lead time (weeks) | Evidence | Notes | Design levers |
|---|---|---|---|---|---|---|
| CE under RED 2014/53/EU, art. 3.2 radio: EN 300 328 (2.4 GHz), EN 301 893 (5 GHz), EN 300 330 (NFC), EN 303 413 (GNSS) as applicable | radio | $4,500–11,000 | 4–8 | estimate | Self-declaration (Module A) is allowed when harmonised standards are applied in full; otherwise a notified body is needed. Includes EMC (EN 301 489-1 and -17) and safety (EN 62368-1) in a typical package. A GNSS receiver counts as radio equipment under RED. | A pre-certified module cuts the radio test scope but not the declaration. |
| RED art. 3.1(a) RF exposure: EN 62479 (low power) or EN 50663 / EN 50566 (SAR for body-worn) | rf-exposure | $0–9,000 | 0–3 | estimate | EN 62479 low-power assessment (on the order of 20 mW and below) is usually a report, not a test. A body-worn product above that needs SAR. | TX power cap. |
| RED delegated regulation (EU) 2022/30, art. 3.3(d)(e)(f): EN 18031-1/-2/-3, mandatory since 2025-08-01 | cybersecurity | $3,300–11,000 | 3–8 | estimate | Applies to radio equipment that can communicate over the internet, directly or through another device such as a phone (-1). Parts -2 and -3 apply when the product processes personal data or money. EN 18031 was harmonised with restrictions; if a restriction applies (for example, passwords the user may skip), you need a notified body. | No default passwords, signed firmware updates, encrypted storage of personal data, a documented update policy. |
| Cyber Resilience Act (EU) 2024/2847: vulnerability reporting from 2026-09-11, full obligations from 2027-12-11 | cybersecurity | $0–20,000 | — | estimate | Covers products with digital elements. Requires secure-by-design practices, an SBOM, vulnerability handling and a declared support period. The cost is mostly process and documentation. Check how it overlaps with RED art. 3.3 for radio products. | Set up a vulnerability disclosure policy and an SBOM in the firmware build from the start. |
| EU Battery Regulation (EU) 2023/1542: CE for batteries, labelling, QR code, EPR registration per country | battery | $500–5,000 | 2–8 | estimate | Labelling and QR-code dates are phased in during 2026–2027. Producer registration and take-back fees apply in every member state where you sell. Verify the current phase-in dates. | Use a compliance scheme or an authorised representative that covers several countries. |
| WEEE 2012/19/EU: producer registration per member state, crossed-out bin symbol | environment | $300–3,000 | 2–6 | estimate | Annual fee per country and per volume. Marketplaces can delist products without a registration number. | — |
| RoHS (EU 2011/65 + 2015/863, China RoHS marking) and REACH SVHC declarations | materials | $0–2,000 | 1–4 | estimate | Mostly supplier declarations plus an optional XRF screen. China RoHS needs a hazardous-substance table and a marking. In the US this row is a retailer requirement, not federal law (California has its own RoHS-like rules). | Ask every supplier for RoHS/REACH declarations when you order samples. |
| REACH Annex XVII entry 27: nickel release for parts in prolonged skin contact (EN 1811) | materials | $300–1,500 | 1–3 | estimate | Nickel-plated magnets, screws, charging contacts or clasps that touch skin. Test or choose non-nickel finishes. | Keep nickel-plated parts inside the sealed body, or use gold over a nickel-free barrier, PVD or stainless steel with low nickel release. |
| PFAS restrictions (EU REACH restriction proposal; US state laws, e.g. Minnesota, Maine) | materials | — | — | estimate | TREND RISK, not a certification. ePTFE acoustic or vent membranes, PTFE coatings and some lubricants are fluoropolymers. Bans and reporting duties are phasing in by state and region; check them before volume production. | Qualify a PFAS-free membrane (for example polyester or other non-fluorinated mesh) as an alternative early. |
| General Product Safety Regulation (EU) 2023/988 (since 2024-12-13): EU responsible economic operator, traceability, safety information | market-access | $550–2,200 | 1–4 | estimate | A non-EU seller needs an EU-based responsible person or authorised representative (annual fee). Name and address go on the product or packaging. | — |
| Packaging and Packaging Waste Regulation (EU) 2025/40 and packaging EPR per country | environment | $200–2,000 | 1–4 | estimate | Packaging registration fees per country; recyclability and empty-space rules phase in. Verify dates. | Paper-based packaging without plastic windows or mixed materials. |
| EN IEC 62368-1 clause 4.8: equipment containing coin/button cells (compartment, warnings, instructions) | safety | $0–2,000 | 0–2 | estimate | Tested in the same EN 62368-1 session as the RED art. 3.1(a) safety report. Similar intent to UL 4200A: a compartment that needs a tool or two independent actions, warning marking and instructions. Under the EU GPSR the coin-cell hazard is a known risk the safety assessment must address. | Design the lid once to pass both UL 4200A option 1 and EN IEC 62368-1 clause 4.8; test both in one lab. |

## United Kingdom (UK)

| Requirement | Area | Cost (USD) | Lead time (weeks) | Evidence | Notes | Design levers |
|---|---|---|---|---|---|---|
| RED art. 3.1(a) RF exposure: EN 62479 (low power) or EN 50663 / EN 50566 (SAR for body-worn) | rf-exposure | $0–9,000 | 0–3 | estimate | EN 62479 low-power assessment (on the order of 20 mW and below) is usually a report, not a test. A body-worn product above that needs SAR. | TX power cap. |
| RoHS (EU 2011/65 + 2015/863, China RoHS marking) and REACH SVHC declarations | materials | $0–2,000 | 1–4 | estimate | Mostly supplier declarations plus an optional XRF screen. China RoHS needs a hazardous-substance table and a marking. In the US this row is a retailer requirement, not federal law (California has its own RoHS-like rules). | Ask every supplier for RoHS/REACH declarations when you order samples. |
| REACH Annex XVII entry 27: nickel release for parts in prolonged skin contact (EN 1811) | materials | $300–1,500 | 1–3 | estimate | Nickel-plated magnets, screws, charging contacts or clasps that touch skin. Test or choose non-nickel finishes. | Keep nickel-plated parts inside the sealed body, or use gold over a nickel-free barrier, PVD or stainless steel with low nickel release. |
| Great Britain: Radio Equipment Regulations 2017 (UKCA, CE currently accepted) | radio | $0–2,000 | 0–3 | estimate | The EU RED reports normally carry over; the cost is a UK declaration and importer details. | — |
| UK PSTI Act 2022 (since 2024-04-29): no universal default passwords, vulnerability policy, declared support period | cybersecurity | $0–2,000 | 0–2 | estimate | Mainly documentation plus a statement of compliance shipped with the product. | — |
| UK WEEE Regulations 2013 and Waste Batteries Regulations 2009: producer registration or compliance scheme | environment | $200–2,000 | 1–4 | estimate | Small producers can use a distributor take-back scheme or a compliance scheme. Separate from the EU registrations. | — |
| EN IEC 62368-1 clause 4.8: equipment containing coin/button cells (compartment, warnings, instructions) | safety | $0–2,000 | 0–2 | estimate | Tested in the same EN 62368-1 session as the RED art. 3.1(a) safety report. Similar intent to UL 4200A: a compartment that needs a tool or two independent actions, warning marking and instructions. Under the EU GPSR the coin-cell hazard is a known risk the safety assessment must address. | Design the lid once to pass both UL 4200A option 1 and EN IEC 62368-1 clause 4.8; test both in one lab. |

## Brazil (BR)

| Requirement | Area | Cost (USD) | Lead time (weeks) | Evidence | Notes | Design levers |
|---|---|---|---|---|---|---|
| Brazil: Anatel homologation through an OCD (restricted-radiation equipment), Resolution 715/2019 | radio | $2,700–7,300 | 4–10 | estimate | BLOCKING: no radio product may be sold or imported for sale before homologation, including a small launch batch. The applicant must be a Brazilian legal entity (CNPJ). Tests run in accredited Brazilian labs. A homologated module reduces RF tests but the end product still needs its own certificate. The label carries the Anatel number and the restricted-radiation sentence; tiny products may move it to the packaging and manual. The cost range was BRL 15–40k (lower with a module). | Pre-sell with delivery after homologation. Use a homologated module. Cap TX power to stay under the SAR exclusion. |
| Brazil: reverse logistics for electronics and batteries (Decree 10.240/2020, CONAMA rules) | environment | $200–2,000 | 2–6 | estimate | The manufacturer or importer joins a take-back scheme (managing entity). Annual fee by volume. | — |

## Checked and not triggered

- FCC host integration of a modular-approved radio (Part 15B SDoC + 'Contains FCC ID') (US)
- FCC RF exposure (47 CFR 1.1307/1.1310, KDB 447498): exemption or SAR test (US)
- CE under EMC 2014/30/EU (and LVD 2014/35/EU if 50–1000 V AC) for products without radio (EU)
- EU 2023/1542 art. 11: portable batteries readily removable and replaceable by the end user, from 2027-02-18 (EU)
- Common charger directive (EU) 2022/2380: USB-C receptacle for listed categories (from 2024-12-28) (EU)
- Brazil: SAR for body-worn transmitters (Resolution 700/2018), unless under the low-power exclusion (BR)
- Brazil: certification of mains chargers and power supplies (INMETRO/Anatel) if one ships in the box (BR)
- IEC 62133-2 (secondary lithium cells/batteries safety), usually through a CB scheme report (*)
- US CPSIA children's product certificate (CPC), third-party testing, tracking labels (US)
- Recording-device privacy: consent laws, a visible recording indicator, data-protection law (GDPR, LGPD, US state laws) (*)
- Finder networks (Apple Find My via MFi, Google Find Hub): program certification and anti-stalking features (*)
- Apple MFi program (only for MFi features: Lightning/USB accessory protocols, Find My, AirPlay, MFi authentication) (*)
- WPC Qi certification (only to use the Qi name and logo or join MPP/Qi2) (*)

