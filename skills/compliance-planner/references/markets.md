# Markets: process, applicant and labelling

Use this file together with `rules.json`. It explains how each market's process works. `rules.json` says which rows apply.

**Status:** knowledge as of 2026-11-08. One fee table (Bluetooth SIG) was read in a primary source. Every other process detail and range is `[estimate]` from prior knowledge and must be verified with a lab or certification body before anyone relies on it.

## Contents

- [How to verify](#how-to-verify)
- [United States (FCC)](#united-states-fcc)
- [Canada (ISED)](#canada-ised)
- [European Union (CE)](#european-union-ce)
- [United Kingdom](#united-kingdom)
- [Brazil (Anatel)](#brazil-anatel)
- [Japan](#japan)
- [South Korea](#south-korea)
- [China](#china)
- [Australia and New Zealand](#australia-and-new-zealand)
- [India](#india)
- [Ecosystem programs](#ecosystem-programs)

## How to verify

1. Read the regulator's own page or the official journal first:
   - FCC: fcc.gov and the KDB database;
   - ISED: ised-isde.canada.ca;
   - EU: eur-lex.europa.eu and the harmonised-standards lists;
   - Anatel: gov.br/anatel.
2. Ask two accredited labs or certification bodies for a quote with the product traits JSON attached. Labs that cover several markets include TÜV, SGS, Intertek, Eurofins, Bureau Veritas, UL and Element.
3. Write each confirmed figure back into `hw/compliance.md` as `[verified: <source>, <date>]`.

Government portals often block automated fetches with CAPTCHAs or 403 errors. When they do, say so and keep the row as an estimate. Never fill the gap with a guess.

## United States (FCC)

- **Radio, chip-down:** certification under Part 15 Subpart C, for example §15.247 for BLE and 2.4 GHz Wi-Fi. An accredited lab runs the tests, and a TCB issues the grant. You need a one-time FCC grantee code, and the product carries an FCC ID.
- **Radio, pre-certified module with modular approval:** the host product needs a Part 15B SDoC and the label "Contains FCC ID: …". This works only within the module grant's conditions. A different antenna, higher power or a body-worn use case can void it.
- **Unintentional radiators:** Part 15B, SDoC.
- **RF exposure:** §1.1307(b)(3) gives a 1 mW blanket exemption and a distance- and frequency-dependent threshold. Body-worn devices above the threshold need SAR.
- **Labels:** tiny devices may put the FCC ID in the manual or on the packaging. Devices with a screen may use an e-label.
- **Lab timing:** typical lab time is 3–6 weeks `[estimate]`.

## Canada (ISED)

- **Standards:** RSS-Gen plus the radio standard (for example RSS-247), ICES-003, and RSS-102 for exposure.
- **Testing:** usually tested together with the FCC.
- **Applicant:** needs an ISED company number. A foreign applicant needs a Canadian representative.

## European Union (CE)

### Radio Equipment Directive 2014/53/EU (RED)

RED covers radio, EMC, safety and RF exposure for radio products.

- **Self-declaration:** Module A is allowed when every applicable harmonised standard is applied in full.
- **Typical standards for a BLE wearable:**
  - EN 300 328 (2.4 GHz radio);
  - EN 301 489-1 and -17 (EMC);
  - EN 62368-1 (safety);
  - EN 62479 (low-power exposure), or EN 50663/EN 50566 for SAR.
- **Cybersecurity:** since 2025-08-01, articles 3.3(d)(e)(f) require cybersecurity under Delegated Regulation 2022/30.
  - Harmonised standards: EN 18031-1 (network), -2 (personal data) and -3 (money).
  - The standards were listed with restrictions. If a restriction applies to your product, a notified body must take part.

### Cyber Resilience Act (EU) 2024/2847

- Vulnerability and incident reporting starts 2026-09-11.
- The remaining obligations start 2027-12-11.
- The work is mostly process: SBOM, vulnerability handling and a declared support period.

### Battery Regulation (EU) 2023/1542

- **Requirements:** batteries need a CE mark, labels and a QR code (phased in), producer registration and take-back in each country, and due diligence for large producers.
- **Article 11 (from 2027-02-18):** portable batteries must be readily removable and replaceable by the end user.
  - The exceptions are narrow. One covers appliances designed to work mainly in an environment regularly exposed to splashing or immersion and meant to be washable.
  - A sealed or glued wearable needs a legal opinion before the enclosure is tooled.

### Other EU obligations

- **WEEE:** register in each country where you sell.
- **RoHS and REACH:** collect declarations from suppliers.
- **Nickel release** for parts in prolonged skin contact.
- **GPSR 2023/988:** an EU responsible person.
- **Common charger directive:** applies to the listed categories.
- **Packaging (PPWR 2025/40):** packaging rules and packaging registration.
- **Accessibility:** the European Accessibility Act covers some consumer devices and their apps. Check whether your category is in scope.

## United Kingdom

- **Radio:** the Radio Equipment Regulations 2017. The UK accepts UKCA, and currently also CE. EU reports usually carry over.
- **Connectable products:** the PSTI Act 2022, in force since 2024-04-29. It bans universal default passwords and requires a vulnerability-disclosure contact and a declared minimum support period.
- **Waste:** UK WEEE and battery producer registration, separate from the EU.

## Brazil (Anatel)

- **Scope:** the sale of any radio product without Anatel homologation is prohibited. This includes BLE and Wi-Fi accessories and small launch batches. Customs can hold telecom products without the mark.
  - **Plan:** pre-sell, and deliver after homologation.
- **Process:** Resolution 715/2019. A designated certification body (OCD) certifies the product, and accredited labs in Brazil run the tests.
  - BLE and Wi-Fi accessories are "restricted radiation" equipment, usually Category II `[estimate]`.
- **Applicant:** a Brazilian legal entity with a CNPJ, either the manufacturer or the importer.
- **Modules:** a homologated module reduces the RF test scope, but the end product still needs its own certificate.
- **Exposure:** Resolution 700/2018. A low-power exclusion exists. Otherwise SAR testing is required.
- **Label:** the Anatel mark with the homologation number, plus the restricted-radiation statement. Tiny products may move it to the packaging and the manual.
- **Batteries and chargers:**
  - An earlier guide mentioned dozens of samples and months of testing for lithium batteries in some categories. Confirm with the OCD.
  - Shipping without a mains adapter usually avoids charger certification.
- **Environment:** reverse logistics under Decree 10.240/2020. The manufacturer or importer joins a take-back scheme.
- **Timing and cost:** roughly 4–10 weeks after samples and documents are ready, and BRL 15–40k per model `[estimate]`.

## Japan

- **Radio:** the Radio Law requires technical conformity, certified by a registered certification body.
  - The product shows the giteki mark and the certification number.
  - A module with Japanese certification reduces the scope.
- **Mains equipment:** PSE (Electrical Appliance and Material Safety Law) covers AC adapters and standalone lithium cells and packs. Built-in batteries are generally outside it.
  - Verify the exemption and the energy-density threshold.

## South Korea

- **Radio and EMC:** KC conformity through RRA.
- **Batteries:** KC safety applies to lithium secondary batteries.
- **Applicant:** usually needs a local applicant or agent.

## China

- **Radio:** SRRC type approval from MIIT.
  - The 2.4/5 GHz rules were revised in 2021–2023.
  - Some micro-power short-range devices are exempt. Whether a low-power BLE product needs approval depends on EIRP and category. Verify with a lab in China.
- **Mains adapters:** CCC applies to listed categories, including adapters.
- **Materials:** China RoHS needs a marking and a hazardous-substance table.

## Australia and New Zealand

- **Marking:** RCM under ACMA rules for radio, EMC and EME, by self-declaration with test reports. EU reports are often accepted.
- **Supplier:** a local responsible supplier is needed.
- **Button and coin cells:** mandatory safety and information standards apply.
- **Mains products:** need EESS registration.

## India

- **Radio:** WPC ETA (Equipment Type Approval), a self-declaration for license-exempt bands.
- **BIS CRS:** registration for listed products. Wearables such as smartwatches are listed, and lithium cells need IS 16046.
  - Tests run in BIS-recognised labs in India.
  - Verify the current list.

## Ecosystem programs

These are contracts, not laws. You need them only to use a name, a logo or a network.

| Program | Needed when | Note |
|---|---|---|
| Bluetooth SIG | always, if the product uses Bluetooth | `[verified: bluetooth.com qualification-listing-fees, read 2026-11-08]` USD 12,000 per product as an Adopter. As a Contributing Adopter (small), USD 3,500 per year plus USD 8,000 for the first qualification. Reusing a qualified stack unmodified avoids lab tests. |
| Apple MFi | MFi-only features (Find My, accessory protocols, authentication) | Plain BLE GATT does not need MFi. |
| Apple Find My, Google Find Hub | finder-network trackers | Program certification plus anti-stalking features, including an audible alert of at least 60 phon. |
| Wi-Fi Alliance | to use the Wi-Fi CERTIFIED logo | Optional. |
| WPC Qi | to use the Qi name or join Qi2/MPP | A proprietary coil needs no Qi certification. |
| USB-IF | to use USB logos | Optional. A USB-C receptacle still has to follow the spec. |
