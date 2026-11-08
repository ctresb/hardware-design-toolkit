# Landed cost: duties, import taxes, FX

Landed cost is what one unit costs once it has cleared customs in the destination country, before your margin. Import rules change often, sometimes within months, and some changes are political. Treat every rule below as dated and tagged:

- Verify a rule on the official source before it goes into a financial plan.
- Ask a customs broker to confirm the tariff classification of the product.

## Method

1. **FOB.** Use the recurring cost from `cost_model.py`: parts, boards, assembly, enclosure, packaging, yield loss and per-order fees, ex-factory.
2. **CIF** = FOB + international freight + insurance. Most countries charge duty and tax on CIF. The US charges duty on the transaction value, which is usually FOB.
3. **Duty** = rate × customs value. The rate depends on:
   - the tariff classification (HS code; 6 digits are international, 8–10 digits are national);
   - the country of origin;
   - trade agreements.

   The Information Technology Agreement (ITA) sets many electronics headings to 0% duty in its member countries. Not every heading is covered, and an ITA heading does not exempt the product from tariff surcharges.
4. **Import taxes.** VAT/GST or the local equivalent, usually charged on CIF + duty. Some countries add further taxes, and some compute a tax "inside" its own base (see Brazil).
5. **Fees.** Broker fee, customs processing fees and port or airport handling. Courier imports have their own clearance fee.
6. **Recoverable or not.** A registered company can usually recover VAT or GST. A consumer cannot. Report both views when it matters.

In `manufacturing.json`, each destination is a `multiplier` range on (recurring + freight), plus an optional `fx` currency for a local-currency column. Put the derivation in `cost.md`, for example "1.6–2.0× = duty 14–20% + IPI 0–15% + PIS/COFINS 11.75% + ICMS 18% computed inside the base".

## Courier versus formal import

- **Courier or postal (small parcels).** This is the route for prototypes and for direct-to-consumer shipping from abroad.
  - Many countries have simplified regimes, low-value thresholds or flat rates.
  - These regimes are where most of the recent changes happened.
- **Formal import (a company imports stock).** Full duty and tax computation, a broker, and often a product registration or radio approval before clearance.
- **Radio products.** Customs can hold a radio product that has no national radio approval. Brazil (Anatel) is an example. Do not plan to import stock for sale before the approval is granted. The certification plan is owned by `compliance-planner`.
- **Lithium batteries.** Shipping a product with a lithium cell inside needs:
  - a UN38.3 test summary;
  - the safety data sheet;
  - the correct UN number: UN3481 for cells contained in or packed with equipment;
  - the IATA packing instruction (PI 967 for contained cells).

  Couriers add a dangerous-goods surcharge. Without the test summary, a shipment can be refused.

## Country notes (examples, dated, verify)

### Brazil

- **Courier purchases, consumer, from certified sites (Remessa Conforme):**
  - Up to US$50: import duty 0%.
  - Above US$50: 60% of the value minus US$30.
  - Sites that are not certified: 60% from the first cent.
  - State ICMS of 17–20% applies on top. It is computed "inside" its own base: (value + freight + insurance + duty) ÷ (1 − rate).

  `[verified: Receita Federal, "Quanto pagarei de imposto", page updated 2026-09-14, read 2026-11-08]`
- **Quick-turn PCB and parts vendors were not on the certified list** on that date (for example JLCPCB, LCSC, PCBWay, Seeed) `[verified: Receita Federal list of certified companies, read 2026-11-08]`. Prototype boards and parts shipped by courier from them pay about 93–100% on top of the value `[estimate: 60% duty + ICMS computed inside]`.
- **Company import (regime comum):**

  | Component | Rate |
  |---|---|
  | Import duty (TEC, by NCM) | often 14–20% for electronics, sometimes reducible through an "ex-tarifário" |
  | IPI (by TIPI) | 0–15% |
  | PIS-Importação | 2.1% |
  | COFINS-Importação | 9.65% |
  | ICMS, computed inside the base | 17–22% |
  | AFRMM | 8% of sea freight |
  | Siscomex, broker, storage | variable |

  Typical landed multiplier for electronics: about 1.6–2.0× FOB before recoverable credits `[estimate: prior knowledge; a customs broker confirms the NCM and rates]`.
- **Tax reform (LC 214/2025):** CBS and IBS replace PIS/COFINS, ICMS and ISS gradually from 2027 to 2033. Re-check the computation for any plan that runs past 2026 `[estimate: prior knowledge, verify]`.

### United States

- **Low-value (de minimis) imports.** The US$800 duty-free de minimis was suspended for goods from China and Hong Kong in May 2025, and for all countries from 29 August 2025. Small parcels now pay duty `[estimate: prior knowledge, verify on cbp.gov]`.
- **Tariffs on Chinese-origin electronics.** These have changed repeatedly since 2018 (Section 301 lists, then country-specific surcharges from 2025). Look up the current rate for the HTS code and origin at the time of import. Never copy a rate from an old plan `[estimate: verify on the USITC HTS and current CBP guidance]`.
- **Formal entry** applies above US$2,500 and needs a customs bond. Processing fees (MPF, plus HMF for sea freight) apply.

### European Union

- **VAT** is 17–27% depending on the member state, charged on CIF + duty. Duty depends on the CN code; many ITA headings are 0%.
- **Low-value parcels:**
  - Below €150, the duty exemption has been under removal: a flat per-item duty during a transition, then full duty `[estimate: prior knowledge of the 2025–2026 reform, verify on taxation-customs.ec.europa.eu]`.
  - VAT has applied from the first euro since 2021, collected through the IOSS scheme for consignments up to €150.
- **Product obligations that are not taxes but are costs:** an EU economic operator (GPSR), WEEE registration, battery EPR registration per country, and the CE documentation. These are in `compliance-planner`.

### United Kingdom

- VAT is 20%. For consignments up to £135, the seller collects VAT at the point of sale. Duty applies by commodity code `[estimate: prior knowledge, verify on gov.uk]`.

## FX

- Write the exchange rate as `[assumption: planning rate, <date>]` in `landed.fx`. Show the local-currency column only where the brief names that market.
- For plans longer than a quarter, show the sensitivity: the landed cost at ±10% FX.

## What to put in `cost.md`

For each target market, state:
- the route assumed (courier or formal import);
- the multiplier and its derivation;
- the freight per unit;
- the landed cost per tier;
- what the broker must confirm (classification, rates, approvals needed for clearance).
