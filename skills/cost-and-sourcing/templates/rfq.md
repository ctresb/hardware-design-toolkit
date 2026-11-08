# Requests for quotation — <product name>

Date: <YYYY-MM-DD>. Quantities quoted at 100, 1,000 and 10,000 unless stated. Each request closes one or more estimates in `hw/cost/manufacturing.json`.

Order these by impact: put first the request whose estimate moves the total per unit the most.

| # | What | To whom (2–4 vendors) | Estimate it replaces | Impact on total at launch tier |
|---|---|---|---|---|
| 1 | | | | |

Use one block below for each request. Send drawings and files, never only a description.

---

## Battery cell (custom or catalog)

Send:
- the outline drawing: DXF plus a PDF with the maximum envelope. State whether the protection circuit (PCM) and the tabs are inside the outline or outside it;
- the chemistry and charge voltage (for example 4.2 V or 4.35–4.4 V high-voltage);
- the minimum capacity at 0.2C;
- the maximum continuous and peak discharge current;
- the cycle-life target (for example 80% after 300 or 500 cycles);
- the operating and charging temperature range;
- the tab type, wire length, connector, and the PCM spec (over-charge, over-discharge, over-current thresholds);
- the swelling allowance you designed for (for example +8–10% thickness at end of life);
- the quantities: samples, 1k and 10k.

Ask for:
- NRE (tooling for the electrode dies and the pouch cup);
- MOQ;
- the price per tier;
- the sample price and lead time;
- the production lead time;
- the UN38.3 test summary, IEC 62133-2 report or CB certificate, and the safety data sheet for this exact cell;
- the capacity they guarantee for your outline.

## PCB fabrication and assembly (each board)

Send:
- Gerbers or ODB++, the drill files, the stack-up, the board-outline tolerance, and the panel drawing;
- the BOM with full MPNs and approved alternatives;
- the pick-and-place file;
- the assembly drawing, with polarity and any parts not to be fitted;
- your test and programming requirements.

State:
- finish, mask color, thickness, via type (through, filled via-in-pad, microvia);
- impedance control, if needed;
- minimum pitch (for example 0.35 mm), and BGA/CSP on flex, if any;
- stiffeners and PSA for flex;
- IPC class.

Ask for:
- NRE per order (setup, stencil, fixtures);
- the price per tier, bare and assembled;
- X-ray policy (100% or sampled);
- lead time;
- the turnkey parts they cannot source;
- written confirmation of every capability at the edge of their published limits.

## Enclosure molding (each part)

Send:
- STEP of each part;
- a 2D drawing with critical dimensions and tolerances, datums and cosmetic zones;
- the material grade and color, for example optical PC "<grade>", clear / black / white;
- the surface finish per face (SPI A1/A2, texture);
- the inserts, and how they are retained;
- the marking (laser, pad print);
- the annual volume;
- the target tool life.

Ask for:
- a DFM report with mold-flow analysis showing gate location, knit lines, sink and warp;
- tool type and steel, cavity count, side actions;
- tooling cost and lead time to T1;
- the price per part per tier;
- the cost and lead time of each later modification (T2/T3);
- the cosmetic standard they will inspect to, and their scrap assumption for clear parts.

## Metal parts and plating (contacts, inserts, brackets)

Send:
- the DXF/STEP and drawing;
- the material and temper (for example 316L);
- the thickness and tolerance;
- the plating spec (for example Au-Co 0.76 µm over Ni 1.3–2.5 µm, or a nickel-free alternative for skin contact);
- the selective-plating areas;
- the marking.

Ask for:
- the process (photo-etch, laser, stamping);
- tooling;
- the price per tier;
- the plating lot charge;
- lead time;
- material and plating certificates;
- the nickel-release test result (EN 1811) if the part touches skin.

## Final assembly, test and packaging (box-build)

Send:
- the assembly sequence with exploded drawings;
- the adhesive and sealing spec;
- the firmware programming method;
- the functional test plan (RF, audio, LEDs, charge current, standby current), the leak or IP test, and the cosmetic inspection standard;
- the packaging dieline and the contents list.

Ask for:
- the labor cost per unit per tier;
- the jig and fixture NRE;
- the cycle time;
- yield reporting;
- warehousing and shipping options;
- dangerous-goods shipping (UN3481) capability.

## Certification labs

These requests come from `compliance-planner`. Send:
- the product description;
- the radio (chip-down or module; antenna; max TX power);
- the battery documents;
- the target markets.

Ask for:
- the test plan and standards list per market;
- the number of samples;
- the price, lead time and pre-scan options.

## Customs broker / freight forwarder

Send:
- the product description and photos;
- the bill of materials summary;
- the value per unit;
- the origin;
- the destination markets;
- the volumes;
- the battery details.

Ask for:
- the tariff classification (HS / NCM / HTS / CN code);
- the duty and tax rates;
- the approvals needed for clearance;
- the landed-cost worksheet per route (courier, air freight, sea);
- the dangerous-goods surcharge.
