---
name: cost-and-sourcing
description: Prices a hardware product at 1, 10, 100, 1k and 10k units, with one-time costs (tooling, fixtures, certifications) kept separate from per-unit cost, landed cost per destination country, where to buy every part, and the RFQs that replace estimates with quotes. Use when the user asks "how much will it cost", "cost per unit", "BOM cost", "injection molding cost", "where do I buy", "landed cost", "import taxes", "MOQ", or before a presentation or pitch.
---

# Cost and sourcing

You work out what the product costs to make at each order size, and where every part and process comes from. Every number keeps its source. Talk to the user in their language.

The goal is not one magic number. It is a table that shows:
- why one unit costs hundreds of dollars and ten thousand units cost tens;
- which three or four lines drive the cost;
- which numbers are verified and which are still estimates;
- which quotes to ask for next.

## Inputs

- `hw/bom.csv`: the canonical BOM (columns in CONVENTIONS.md §5). `electronics-researcher` fills in the price breaks.
- `hw/brief.md`: target markets, launch quantities and target retail price.
- `hw/pcb/`: board count, layers, size, sides, joint count and hidden-joint parts (QFN, BGA, LGA).
- `hw/mech/`: enclosure parts, materials, finishes and inserts.
- `hw/power/`: the battery, catalog or custom.
- `hw/compliance.md`: certification costs (owned by `compliance-planner`; you read them and never re-estimate them).
- `hw/roadmap.md`: which build stage (EVT/DVT/PVT) uses which process (owned by `prototype-roadmap`).

## Outputs

- `hw/cost/manufacturing.json`: the inputs of the cost model. Start from `templates/manufacturing.example.json`.
- `hw/cost/model.json`, `hw/cost/cost.md` and `hw/cost/cost.svg`: written by `scripts/cost_model.py`. In `cost.md` the script rewrites only the block between `<!-- cost_model:begin -->` and `<!-- cost_model:end -->`. Write your analysis outside the markers, and it survives every re-run. The chart title states the conclusion against `targets.unit_cost`.
- `hw/cost/rfq.md`: the quotes to request, built from `templates/rfq.md`.
- `hw/cost/sourcing.md`: where to buy each part or process, with the authorized channel, MOQ, lead time and second source.

## Procedure

1. **Read the BOM and check that it can be costed.** Every line needs a full orderable MPN with its packaging suffix, a quantity, at least one price break and an evidence tag.
   - If prices are missing, ask `electronics-researcher` to fill them. Do not invent a price.
   - A part with no price stays in the model with a warning.
2. **Model the PCBA from the assembler's published tariff, not from a guess.** Count three things per board:
   - solder joints (pins plus exposed pads);
   - unique part types (each one has a loading fee);
   - hidden-joint parts that need X-ray.

   Put them in the `pcba` block. The example template holds one quick-turn tariff as published on its date. Re-check it before use, and replace it with a real quote once Gerbers exist.
3. **Write every other cost as a line with a value per tier.** Classify each line by how it behaves (section "Cost structure"): recurring, per order, or one-time (NRE).
   - Give every value as a `[low, high]` range unless it is a quote.
   - Tag every line `verified: <source, date>`, `estimate: <basis>` or `assumption`.
4. **Use the right process for each tier.** The same part is made differently at 10 and at 10,000 units. For example, an enclosure goes SLA → urethane casting → rapid aluminum tool → hardened steel. Each process brings its own NRE (`from_tier`/`to_tier`). See `references/cost-reference.md`.
5. **Run the model:**

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/cost_model.py --mfg hw/cost/manufacturing.json --out hw/cost --svg
   ```

   The script applies three rules:
   - Part attrition: the assembler's extra parts per feeder.
   - MOQ: below the MOQ you pay for the whole MOQ or for paid samples, whichever is cheaper.
   - Yield loss: scrapped units still cost their parts.

   It writes the tables, the top cost drivers per tier and the share of cost that rests on verified figures. Test the script with `python3 ${CLAUDE_SKILL_DIR}/scripts/test_cost_model.py`.
6. **Add landed cost for each market in the brief.** Use the method in `references/landed-cost.md`: duty and tax multiplier on CIF, courier versus formal import, FX as a dated assumption. Destination rules change often. Every rule carries a date and the word "verify".
7. **Read the result like an engineer and write `cost.md` around the script's tables,** outside the generated-block markers. Put the brief's unit-cost goals in `targets.unit_cost`, so each tier reads `met`, `not proven` or `not met`. Use the landed **recurring** row for the cost of one more imported unit, and the **incl. NRE** row for the launch budget. Answer these questions:
   - At which order size does NRE stop dominating?
   - Which single part or process is the biggest lever? (A memory chip or a custom battery often outweighs everything else.)
   - What does the launch batch really cost per unit, with certifications spread over it?
   - What is the gap to the target retail price? A retail price usually needs to be about 3–5× the landed cost to leave room for the channel and the margin. Label this as a rule of thumb.
8. **Write `sourcing.md`.** For each BOM line, list:
   - the authorized distributors that stock it;
   - the MOQ and reel size;
   - the lead time;
   - a second source;
   - anything long-lead to buy now.

   For each process (PCB, PCBA, molding, cell, metal parts, packaging, final assembly), list 2–4 established vendors from `references/suppliers.md`.
9. **Write `rfq.md`.** List every estimate that moves the total by more than about 5%. For each one, say what to send, to whom, and which number the quote will close. Order the list by impact.

## Cost structure

| Kind | Behaves like | Examples | In the model |
|---|---|---|---|
| Recurring | paid for every unit | parts at the tier price; bare boards; PCBA per-joint and X-ray fees; molded parts; battery; magnets, membranes, cord; packaging; final assembly, programming and test labor; freight | `recurring`, BOM, `pcba` variable |
| Per order (batch) | paid on every production order, spread over that order | PCBA setup, stencil, feeder loading, fixtures, handling; molding run setup and color change; plating lot charge; prototype board lot | `per_order`, `pcba` batch |
| One-time (NRE) | paid once per design revision | mold tools; stamping dies; photo-etch phototools; test and programming fixtures; custom cell tooling; certifications (radio, EMC, safety, Bluetooth qualification, IP rating, UN38.3); packaging dies; design services | `nre` |
| Yield loss | a percentage on recurring | scrapped and reworked units; cosmetic rejects on clear parts (10–30% early) | `yield_loss_pct` |
| Landed | a multiplier on recurring plus freight | duties, import taxes, broker fees | `landed` |

Keep engineering salaries, marketing, warranty reserve and retail margin out of the unit cost. Say in the report that they are excluded.

## Sourcing rules

- **Buy production parts only from authorized channels.** These are the manufacturer, its franchised distributors (DigiKey, Mouser, Arrow, Avnet, Future, TME, Farnell/Newark, and LCSC for parts it is franchised for), or the EMS's own purchasing.
  - A broker or marketplace is a last resort, for prototypes, and only with traceability.
  - Counterfeit and remarked parts come from brokers.
- **Respect the reel.** Prices at 1k and 10k assume full reels. Cut tape and small quantities cost more and carry an assembler surcharge. Check that the tier price you use matches the packaging suffix of the MPN.
- **Plan attrition.** Assemblers consume extra parts per feeder. For 0201/0402 passives, order at least 20 extra, or 5%.
- **Buy long-lead parts early.** Any part with a lead time over 12 weeks, or with stock below one production run, goes in `sourcing.md` under "buy now".
  - For prototypes, buy enough for EVT and DVT at once.
  - A part that is "early sampling" or NRND at the manufacturer is a design risk. Hand it back to `specs-engineer`. Do not hide it with a price.
- **Second-source passives by value, not by MPN.** Approve 2–3 brands per value and package (for example Murata, Samsung, TDK, Yageo for MLCCs). Single-source an IC only when no pin-compatible alternative exists, and say so.
- **Consign or turnkey.** For quick-turn turnkey assembly, check that the assembler's library stocks your exact parts. Consign the rest: ship them to the assembler, labelled, with spares.
- **Use established vendors only.** Never recommend an unknown company found through a marketplace. Check that a vendor still operates (some well-known startups have closed). Verify each vendor's current status before recommending it.

## Gate

Cost and sourcing pass when all of these are true:
- Every BOM line has a price at every tier, or an explicit warning.
- Every line in `manufacturing.json` has an evidence tag.
- `cost.md` states the share of cost resting on verified figures at the launch tier.
- `rfq.md` covers every estimate that moves the total by more than about 5%.
- The total at the launch quantity, with certifications, is stated next to the target retail price.

## Taste and pitfalls

- **Never present an estimate as a quote.** "About $3–8 for final assembly at 1k (estimate, China box-build range)" is honest. "$5" is not.
- **Don't let one line hide inside a total.** A single 4 Gbit NAND or a custom cell can be half of the recurring cost. Call it out by name, with its share.
- **A custom battery below its MOQ is expensive.** At 100 units you either pay for 2,000 cells or for paid samples. The model shows it, and you say it.
- **Certifications are paid before the first sale, even for a "small" launch batch.** Spread them over the launch batch and show that number. It is usually the uncomfortable one.
- **Tooling dominates at 1k.** At 1,000 units, NRE is often about half the total. Do not quote the 10k recurring cost as "the cost".
- **Clear and cosmetic parts have high scrap.** Budget it in `yield_loss_pct` or in the part price.
- **Use the tariff's real breakpoints.** PCBA X-ray and fixture fees step with quantity. A smooth curve is wrong at 5 and at 100 units.
- **Date every price and every tax rule.** Duties, de minimis thresholds and courier regimes change, sometimes within months.
- **Tables are aligned and readable.** Right-align numbers, keep units in the header, and use one currency per table. Never show more than 3 significant figures for an estimate.

## References

Read these when the step needs them:

| File | Read when |
|---|---|
| `references/cost-reference.md` | you need typical, dated figures for PCB, PCBA, molding, metal parts, batteries, final assembly, packaging and certification lines |
| `references/landed-cost.md` | you compute landed cost or explain import taxes for a destination |
| `references/suppliers.md` | you name vendors for a part or process |
| `references/manufacturing-json.md` | you write or debug `hw/cost/manufacturing.json` |
| `templates/rfq.md` | you write `hw/cost/rfq.md` |
| `templates/manufacturing.example.json`, `templates/bom.example.csv` | you start a new model; they are a complete fictional example that runs |
