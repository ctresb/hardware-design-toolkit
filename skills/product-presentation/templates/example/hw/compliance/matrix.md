# Certification matrix — Fixture Tag (fictional example)

> Planning aid, not legal advice. Rules, fees and dates change. Every row must be confirmed with an accredited lab, certification body or regulator before you rely on it. Rules file checked 2026-11-08. Costs are in USD. EUR ranges were converted at about 1.1 USD/EUR and BRL at about 5.5 BRL/USD [assumption].

Traits: markets US, EU, UK; radios ble; module pre-certified: no; battery lithium-metal-coin; body-worn: no.

## Summary

| Scope | Rows | Cost range (USD) | Longest single lead time (weeks) |
|---|---|---|---|
| All markets | 3 | $13,300–19,000 | 4 |
| United States | 5 | $6,000–19,500 | 6 |
| European Union | 10 | $9,350–65,200 | 8 |
| United Kingdom | 5 | $200–17,000 | 4 |

Totals add the low ends and the high ends of each row. Tests in one lab session can overlap, so the real total is often lower than the sum; the high end is a budget ceiling, not a quote.

## All markets

| Requirement | Area | Cost (USD) | Lead time (weeks) | Evidence | Notes | Design levers |
|---|---|---|---|---|---|---|
| Bluetooth SIG qualification and listing | radio | $11,500–12,000 | 1–4 | verified | Required for any product that uses Bluetooth or the Bluetooth name, even when it reuses a qualified chip and stack. Adopter: free membership, USD 12,000 per product. Contributing Adopter (small): USD 3,500 per year plus USD 8,000 for the first qualification of the membership year. A 128-bit custom UUID is free; a 16-bit UUID (USD 3,750) or a Company ID (USD 1,250) is optional. | Reuse the chip vendor's qualified controller and host stack without modification, so the qualification is a declaration and needs no lab tests. |
| IP rating test to IEC 60529 (only if you claim an IP code) | ingress | $800–3,000 | 1–2 | estimate | Not a legal requirement, but a claim you make must be backed by a test. Run in-house immersion and pressure-decay pre-tests first. A sealed device without a vent needs pressure and temperature cycling too. | Fewer openings: molded contacts, membranes, adhesive seals. |
| Pre-compliance scan at a lab on EVT/DVT units (radiated emissions, conducted, ESD IEC 61000-4-2, radio) | process | $1,000–4,000 | 1–2 | estimate | A day or two of chamber time before formal tests. Failing the formal test costs a board revision and a retest, which costs more than the pre-scan. | — |

## United States (US)

| Requirement | Area | Cost (USD) | Lead time (weeks) | Evidence | Notes | Design levers |
|---|---|---|---|---|---|---|
| FCC Part 15 Subpart C certification (intentional radiator, e.g. 15.247) via a TCB | radio | $5,000–12,500 | 3–6 | estimate | Chip-down radio. Covers lab tests (US labs cost more than accredited labs in Asia), the TCB grant fee and a one-time FCC grantee code. The product carries an FCC ID; small devices can put it in the manual or on an e-label if they have a screen. | A pre-certified module with modular approval removes this row if you follow the module grant's antenna and layout conditions. |
| FCC Part 15 Subpart B (unintentional radiator), SDoC | emc | $1,000–3,000 | 1–3 | estimate | Every product with a clock or digital logic. Usually tested in the same lab session as 15C. | — |
| RoHS (EU 2011/65 + 2015/863, China RoHS marking) and REACH SVHC declarations | materials | $0–2,000 | 1–4 | estimate | Mostly supplier declarations plus an optional XRF screen. China RoHS needs a hazardous-substance table and a marking. In the US this row is a retailer requirement, not federal law (California has its own RoHS-like rules). | Ask every supplier for RoHS/REACH declarations when you order samples. |
| PFAS restrictions (EU REACH restriction proposal; US state laws, e.g. Minnesota, Maine) | materials | — | — | estimate | TREND RISK, not a certification. ePTFE acoustic or vent membranes, PTFE coatings and some lubricants are fluoropolymers. Bans and reporting duties are phasing in by state and region; check them before volume production. | Qualify a PFAS-free membrane (for example polyester or other non-fluorinated mesh) as an alternative early. |
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
| PFAS restrictions (EU REACH restriction proposal; US state laws, e.g. Minnesota, Maine) | materials | — | — | estimate | TREND RISK, not a certification. ePTFE acoustic or vent membranes, PTFE coatings and some lubricants are fluoropolymers. Bans and reporting duties are phasing in by state and region; check them before volume production. | Qualify a PFAS-free membrane (for example polyester or other non-fluorinated mesh) as an alternative early. |
| General Product Safety Regulation (EU) 2023/988 (since 2024-12-13): EU responsible economic operator, traceability, safety information | market-access | $550–2,200 | 1–4 | estimate | A non-EU seller needs an EU-based responsible person or authorised representative (annual fee). Name and address go on the product or packaging. | — |
| Packaging and Packaging Waste Regulation (EU) 2025/40 and packaging EPR per country | environment | $200–2,000 | 1–4 | estimate | Packaging registration fees per country; recyclability and empty-space rules phase in. Verify dates. | Paper-based packaging without plastic windows or mixed materials. |

## United Kingdom (UK)

| Requirement | Area | Cost (USD) | Lead time (weeks) | Evidence | Notes | Design levers |
|---|---|---|---|---|---|---|
| RED art. 3.1(a) RF exposure: EN 62479 (low power) or EN 50663 / EN 50566 (SAR for body-worn) | rf-exposure | $0–9,000 | 0–3 | estimate | EN 62479 low-power assessment (on the order of 20 mW and below) is usually a report, not a test. A body-worn product above that needs SAR. | TX power cap. |
| RoHS (EU 2011/65 + 2015/863, China RoHS marking) and REACH SVHC declarations | materials | $0–2,000 | 1–4 | estimate | Mostly supplier declarations plus an optional XRF screen. China RoHS needs a hazardous-substance table and a marking. In the US this row is a retailer requirement, not federal law (California has its own RoHS-like rules). | Ask every supplier for RoHS/REACH declarations when you order samples. |
| Great Britain: Radio Equipment Regulations 2017 (UKCA, CE currently accepted) | radio | $0–2,000 | 0–3 | estimate | The EU RED reports normally carry over; the cost is a UK declaration and importer details. | — |
| UK PSTI Act 2022 (since 2024-04-29): no universal default passwords, vulnerability policy, declared support period | cybersecurity | $0–2,000 | 0–2 | estimate | Mainly documentation plus a statement of compliance shipped with the product. | — |
| UK WEEE Regulations 2013 and Waste Batteries Regulations 2009: producer registration or compliance scheme | environment | $200–2,000 | 1–4 | estimate | Small producers can use a distributor take-back scheme or a compliance scheme. Separate from the EU registrations. | — |

