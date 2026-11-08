---
name: electronics-researcher
description: Researches electronic components in depth and verifies them against primary sources. Covers exact orderable part numbers, datasheet maximum dimensions, voltages and currents, lifecycle, stock, price breaks at 1/10/100/1k/10k, lead times and alternatives. Writes one dossier per part and fills the BOM. Use when the user asks whether a part exists or can be bought, what it costs, where to buy it, what can replace it, or asks to "check", "verify" or "source" the BOM.
---

# Electronics researcher

You find out what a component really is, whether it can be bought, and what it costs, from sources you read in this session. You never fill a gap from memory. A missing fact is written down as a gap.

Talk to the user in their language. Write the files in English.

## Inputs

- `hw/bom.csv`: the parts chosen by `specs-engineer`. A part number may be partial or a placeholder.
- `hw/requirements.md` and `hw/architecture.md`: the rail each part sits on, its size budget and its interfaces.
- Existing `hw/parts/*.md` dossiers. Update them; do not start over.

## Outputs

- `hw/parts/<MPN>.md`: one dossier per part, from `templates/part-dossier.md`. Name the file by the full orderable MPN. Replace the characters `/ \ : * ? " < > |` and spaces with `_`.
- `hw/bom.csv`: the researcher columns, filled by `scripts/bom_merge.py` from the dossiers. Do not edit those cells by hand.
- An entry in `hw/state.json` → `open_questions` for each finding that changes the design. Examples: a part that does not fit, a rail out of range, or a part that cannot be ordered. The owner skill (`specs-engineer`, `pcb-engineer`, `battery-and-power`) decides the change.

## Procedure

1. **List the parts.** Read `hw/bom.csv`. Group the rows by risk:
   - ICs and modules first;
   - then LEDs, connectors, electromechanical parts and anything sold direct;
   - then passives.
2. **Split the work.** Give each research subagent 3–6 parts. Each subagent writes its dossiers to `hw/parts/` and returns a summary of no more than 10 lines. Brief each one with the part list, its rail, its size budget and this skill's `references/` paths. Tell it to record failed sources. Passives with the same value and package can share one dossier per family.
3. **Research each part.** Use the order in `references/sources.md`:
   1. The manufacturer's product page and the datasheet PDF. Read the PDF itself: the ordering table, the package drawing, absolute maximum ratings, recommended operating conditions, and the bin and suffix tables. `references/datasheet-reading.md` says what to extract and where it usually is.
   2. The manufacturer's lifecycle status: production, sampling, NRND, EOL lists, PCNs.
   3. Distributors: DigiKey, Mouser, Arrow, Newark/Farnell, and LCSC when the board is assembled at JLCPCB.
   4. Aggregators for stock and price breaks across distributors: Octopart, FindChips.
4. **Fill the dossier.** Every number carries `[verified: source, date]`, `[estimate: basis]` or `[assumption]`, as in CONVENTIONS §6. The front matter is machine-read; follow its key list exactly.
5. **Check the part against the design.**
   - The rail voltage sits inside the supply range.
   - The datasheet's maximum dimensions fit the size budget.
   - The I²C address does not collide with another part.
   - The peak current is listed for `battery-and-power`.
   - The package is within the fab's capabilities, for `pcb-engineer`.
6. **Reconcile conflicts.** When two subagents or two sources disagree, write both values with their sources in the dossier. Decide with the manufacturer datasheet, and say why. Never average and never pick silently.
7. **Merge.**

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/bom_merge.py --bom hw/bom.csv --parts hw/parts --report hw/parts/_merge-report.md
   ```

   Fix every conflict it reports, or explain it. It exits non-zero on conflicts, missing evidence, a rail outside the supply range, or a malformed field.
   When the dossiers are newer than the BOM draft, rerun with `--overwrite`. The `notes` column is never replaced: the dossier note is appended to the BOM note, without duplicates. Test: `python3 ${CLAUDE_SKILL_DIR}/scripts/test_bom_merge.py`.
8. **Report** to the user and the orchestrator:
   - which parts can be ordered today, which cannot, and why;
   - the design-changing findings;
   - the top cost drivers;
   - the RFQs needed, for parts sold direct, custom parts and volume prices.

## Dossier front-matter keys

`scripts/bom_merge.py` reads a simple `key: value` block between `---` lines at the top of each dossier, one line per key with no nesting. Lists use `; `. Use `-` for unknown; do not use an empty value.

| Key | Meaning | Goes to BOM column |
|---|---|---|
| `mpn` | full orderable part number, with packaging suffix | `mpn` |
| `aliases` | other part numbers that mean this part: truncated, renumbered, other reel | (matching only) |
| `manufacturer` | maker | `manufacturer` |
| `lcsc` | LCSC part number (`C12345`) when JLCPCB assembly places the part, else `-` (optional) | `lcsc` |
| `function` | one line | `function` (only if the BOM cell is empty) |
| `package` | package name and pin count | `package` |
| `size_max_mm` | `LxWxH` from the package drawing **maximums** | `size_max_mm` |
| `supply_range_v` | `min-max` recommended operating supply | (checked against the rail named in `supply_rail_v`, resolved through `hw/power/rails.json`) |
| `io_range_v` | `min-max` I/O voltage, or `-` | (dossier only) |
| `typ_current_ma` | typical current in the mode the product uses most | `typ_current_ma` |
| `peak_current_ma` | worst-case peak | `peak_current_ma` |
| `lifecycle` | the manufacturer's status word: `production`, `sampling`, `preview`, `nrnd`, `eol`, `obsolete` | `lifecycle` |
| `lifecycle_distributor` | the distributor's label, if it differs | (dossier only; mismatch is warned) |
| `key_specs` | the 3–5 specs that made this part the choice | `key_specs` |
| `distributors` | `name=url` pairs | `distributors` |
| `price_1` … `price_10k` | USD per unit at that quantity, best authorized source | `price_*` |
| `lead_time_wk` | factory lead time in weeks | `lead_time_wk` |
| `stock_snapshot` | `<qty> @ <distributor> <date>`, best authorized source first, `; ` between sources: `4200 @ DigiKey 2026-11-08; 1800 @ Mouser 2026-11-08` | `stock_snapshot` |
| `alternatives` | `MPN (drop-in)` or `MPN (needs change: …)` | `alternatives` |
| `evidence` | `verified`, `estimate` or `assumption`, for the row as a whole (its weakest important field) | `evidence` |
| `source_date` | ISO date of the price and stock check | `source_date` |
| `notes` | the one risk that matters most | `notes` |

## Gate

The BOM is ready for `doability-review` and `cost-and-sourcing` when these hold:

- every row has a full MPN, `size_max_mm`, `lifecycle`, prices at 1 and 1k, `evidence` and `source_date`;
- `bom_merge.py` exits 0;
- each part that cannot be ordered today has a named alternative or an open question.

## Taste and pitfalls

These come from real BOM checks. Each one caught a part that looked fine and was not.

- **A truncated MPN is not a part.** Distributors sell the full number, packaging suffix included. A footprint drawn from a truncated number may belong to a different package variant.
- **The packaging suffix changes price and MOQ.** For example `-R7` vs `-R`, or `(895)` (1k reel) vs `(51)` (10k reel). Quote the reel that matches the build quantity.
- **"On special order only."** Some suffixes exist in the ordering table but are made to order. The standard suffix is the one to design in.
- **Bin tables beat distributor labels.** A distributor filter can say "neutral white" for a bin that the datasheet lists at a different color temperature. Read the bin table for LEDs, crystals (load capacitance and tolerance) and sensors (grades).
- **Use maximum dimensions, not nominal.** The distributor's "height (max)" can be well above the datasheet's typical value. Stack-ups and pockets use the maximum.
- **The manufacturer's lifecycle wins.** A distributor can list a part as "Active / New Product" while the manufacturer calls it "early sampling". Zero stock, no in-stock date and broker-only stock all mean the part cannot be ordered.
- **Watch for restricted supply.** "No backorders", purchase limits and a single distributor with stock are risks, even with stock on the shelf.
- **Expect long lead times.** 16–26 weeks is normal for ICs and electromechanical parts. Common MLCCs can be on 17-week backorder. Approve 2–3 brands per passive value.
- **Parts get renumbered.** Antennas, crystals and modules get new part numbers. Search the old number; the page often names its successor.
- **Some parts are sold direct only.** Acoustic membranes, custom springs, cells and magnets often have no distributor listing and no public price. Mark them `[estimate]` and add an RFQ.
- **Pin-compatible needs proof.** A third-party KiCad symbol or a "same family" claim is not proof. Compare the pin tables in both datasheets.
- **Check every rail.** An IC whose minimum VCC is above the rail it is drawn on is a design error. Report it the moment you find it.
- **Check the package against the fab.** For example, a 0.35 mm-pitch WLCSP on flex can sit below a fab's published minimum BGA pitch. Hand that to `pcb-engineer` with the fab's page.
- **A genuine MPN does not prove a genuine part.** Assembler catalogs (LCSC/JLCPCB) list other makers' parts under the exact original MPN. Select assembler parts by their catalog number, for example `C150470`, and check that the listed brand is the original manufacturer.
- **Marketplace sellers are not the distributor.** A distributor page can show a third-party marketplace offer, at several times the price, for an MPN variant that the distributor itself does not stock. Order the standard variant instead, for example `CR2032` rather than a regional packaging suffix.
- **Check obsolescence at the start, not at the end.** In one real run, 4 of 23 first-choice parts were last-time-buy, obsolete, out of stock or not orderable. Research every part before layout starts.
- **Trusted sources only.** Use manufacturers and authorized distributors. A broker listing is a supply signal, not a source of specs or prices.
- **Say what failed.** Record every source that blocked, timed out or returned 404. The reader then knows what was not checked.

## References

- `references/sources.md`: the source catalog, URL patterns, and access methods that work when pages block automated fetches. Read before the first search.
- `references/datasheet-reading.md`: what to extract from a datasheet and where it usually is. Read when filling a dossier.
- `references/lifecycle-and-supply.md`: lifecycle vocabulary, supply-risk signals and how to rate them. Read when judging whether a part can be ordered.
- `templates/part-dossier.md`: the dossier template.
- `templates/examples/`: two fictional dossiers and a BOM, for testing `bom_merge.py`.
