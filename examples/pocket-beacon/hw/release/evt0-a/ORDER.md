# Order · Pocket Beacon rev evt0-a · build of 10

Total: USD 800–1,800 [estimate, sources per step]. Steps that do not depend on each other can run in parallel; the lead times are per step.

**WARNING** Ordering spends money. Confirm the release check passed (`checks/release-check.json`) and the stock dates are current before each step.

## 1. Order 10 boards with assembly at JLCPCB

- **Where:** https://jlcpcb.com/
- **Upload:** `fab/main/main_gerbers.zip`, `assembly/main/main_bom_jlcpcb.csv`, `assembly/main/main_cpl_jlcpcb.csv`
- **Options:** See fab/main/fab-notes.md and assembly/main/options.md
- **Cost:** USD 260–330
- **Lead time:** 10–18 days
- **Receiver:** Builder
- **Source:** cost/model.json tier 10: PCBA batch $138.67 [verified tariff], bare boards $30–90 [estimate], BOM $7.72 × 10 [verified], placement $1.84 × 10

## 2. Order 12 CR2032 cells from an authorized distributor

- **Where:** https://www.digikey.com/
- **Upload:** `purchasing/digikey.csv`
- **Options:** Panasonic CR2032 (not the marketplace CR-2032/BN); ship to the builder, not to the PCB fab
- **Cost:** USD 8–20
- **Lead time:** 2–5 days
- **Receiver:** Builder
- **Source:** bom.csv BAT1, sourcing.md

## 3. Order 12 enclosure sets as SLA prints

- **Where:** an SLA service bureau (e.g. JLC3DP, Protolabs, Xometry) or an in-house SLA printer
- **Upload:** `mech/shell.stl`, `mech/plate.stl`, `mech/door.stl`, `mech/button.stl`
- **Options:** See mech/print-settings.md
- **Cost:** USD 140–700
- **Lead time:** 5–12 days
- **Receiver:** Builder
- **Source:** cost/model.json tier 10: enclosure $14–70 per set [estimate]

## 4. Order the mechanical parts (screws, gaskets, foam, acoustic vents, tape rings)

- **Where:** die-cut converter and fastener supplier
- **Upload:** `mech/mech-bom.csv`, `mech/door_gasket.step`, `mech/port_gasket.step`, `mech/adhesive.step`
- **Options:** 12 sets; die-cut from the STEP outlines
- **Cost:** USD 42–190
- **Lead time:** 5–15 days
- **Receiver:** Builder
- **Source:** cost/model.json tier 10: mechanical $4.2–19 per unit [estimate]

## 5. Buy the long-lead parts for DVT from stock (optional now, needed by DVT)

- **Where:** LCSC and DigiKey
- **Upload:** `purchasing/purchasing.md`
- **Options:** 130 each of U1, Q1 (LCSC C150470), Y2, D2 (LCSC C48260), ANT1, LS1 — FR-11
- **Cost:** USD 200–300
- **Lead time:** 3–10 days
- **Receiver:** Builder
- **Source:** roadmap/schedule.md, bom.csv prices [verified 2026-11-08]

## 6. Get the bring-up tools if not on hand

- **Where:** TI store / DigiKey, Tag-Connect, Nordic distributors
- **Upload:** `test/test-plan.md`
- **Options:** TI XDS110 debug probe, Tag-Connect TC2030-CTX-NL, Nordic PPK2
- **Cost:** USD 150–260
- **Lead time:** 2–7 days
- **Receiver:** Builder
- **Source:** estimate: catalog prices of the three tools
