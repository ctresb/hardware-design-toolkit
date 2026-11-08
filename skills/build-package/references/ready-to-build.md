# Ready to build

## 1. Definition

A release is **READY TO BUILD** when a person or a factory can order and build it from the release folder
alone, with no further design work, no open decision and no missing file. "Almost" does not exist. A
release is ready, or it is NOT READY with a list of blockers and the exact action for each.

## 2. Two levels

| | READY TO BUILD (prototype) | READY TO BUILD (production) |
|---|---|---|
| Purpose | build 5–100 units to measure, test and show | build at volume and sell |
| Board | routed, DRC/ERC 0, fab files, assembler BOM/CPL in stock | same, plus a fixture-tested panel and yield data from the prototype run |
| Parts | orderable now; sampling or NRND parts allowed with a warning | mass-production lifecycle, second sources for single-source risks, long-lead parts ordered |
| Enclosure | STEP + STL, printed or machined (SLA, MJF, CNC) | tooling quote accepted, T1 samples approved, DFM signed off by the molder |
| Battery | catalog cell, or custom-cell samples | custom cell qualified, UN 38.3 test summary on file |
| Measurements | listed in `verify-on-prototype.md` with method and pass threshold; not done yet | done, recorded as facts (F-xxx), all passing |
| Certification | planned (`hw/compliance.md`) | pre-scan passed, lab booked or certificates received |
| Cost | estimates with sources | quotes received for every NRE and every per-unit line above 5 % of the unit cost |

A prototype release is the toolkit's normal end point. A production release needs the prototype's
measurements and the real quotes. The toolkit cannot invent those. It lists them, and the gate blocks until
they exist.

## 3. Gate checks (`release_check.py`)

| Check | Fails when | Owner |
|---|---|---|
| structure | README, ORDER, MANIFEST, battery, assembly guide, test plan or verify-on-prototype is missing | build-package, doability-review |
| manifest | a file differs from its sha256, is missing, or is not listed | build-package |
| fab | no Gerber zip, not a zip, no copper layer, no drill file | pcb-engineer |
| drc / erc | errors, unconnected items or schematic-parity issues; report missing (warnings fail only with `warnings_fail`) | pcb-engineer |
| routing | the `.kicad_pcb` has no tracks | pcb-engineer |
| assembly | assembler BOM or CPL missing; refs differ between them; a JLCPCB line has no LCSC number and is not consigned | pcb-engineer, electronics-researcher |
| bom | placeholder MPN; lifecycle not allowed for the target; placed ref not in `hw/bom.csv` | electronics-researcher, specs-engineer |
| stock | no check date, check older than `stock_max_age_days`, no snapshot, stock below the build need | electronics-researcher |
| purchasing | a part the assembler does not place has no purchase cart | build-package |
| mech | an enclosure part has no STEP, the STEP is not ISO 10303-21, a printed part has no STL or print settings | enclosure-engineer, build-package |
| validation | the validator report is missing, failing, or older than the CAD | enclosure-engineer |
| doability | the verdict is not READY TO BUILD for the target | doability-review |
| order | no steps, a step without cost or lead time, an upload that is not in the release | cost-and-sourcing, build-package |
| docs | a `<placeholder>`, TBD or TODO in a document; a test plan without pass thresholds | build-package, battery-and-power |

## 4. Pre-order checklist

Do this with the release open, after the gate passes and before any payment. Record the result in
`checks/pre-order.md`.

### Boards and assembly

1. **Rotation and polarity.** Open the assembler's placement preview. Check pin 1 of every IC, and the
   cathode of every diode and LED. Check every connector's orientation and every polarized capacitor.
   Rotation offsets depend on the footprint and the assembler; fix them in `release.json` →
   `rotation_offsets`, never in the CPL by hand.
2. **Basic vs extended parts.** At JLCPCB, each extended part type adds a loading fee per order (published
   on the assembler's price page). Replace extended passives with basic ones where the value allows.
3. **Stock on the order day.** Re-check each line on the assembler's site. A part that sells out between
   the check and the order stops the whole batch.
4. **Consigned parts.** Ship them with the assembler's consignment form before the order is released. Add
   10 % or at least 5 spare pieces for parts on tape.
5. **Fiducials and tooling holes.** There are 2–3 fiducials per side for fine-pitch parts, and tooling
   holes or rails as the assembler requires.
6. **Minimum sizes and panels.** Boards smaller than the assembler's minimum (often 70 × 70 mm at JLCPCB
   for some options; check the current page) need a panel with rails. Choose V-score or mouse bites by edge
   shape. Mouse bites leave nubs on round boards: sand them if the board sits in a tight pocket.
7. **Thickness and finish.** Check board thickness, copper weight, ENIG vs HASL, and mask color against
   `fab-notes.md`. Black and white mask need a wider mask web at fine pitch.
8. **X-ray and inspection.** QFN, BGA and LGA parts need X-ray inspection. Choose it where the assembler
   offers it.
9. **Double-sided assembly** costs a second setup. Confirm that it is intended.

### Enclosure

10. **Clear parts.** An SLA print is foggy until it is finished: wet-sand, then polish or clear-coat. Budget
    1–2 h per part. Measure fit after finishing, because coating adds thickness.
11. **Print orientation.** Keep supports off cosmetic and sealing faces.
12. **Tolerances.** Ask the service for the tolerance class on the drawing. Default prints are often
    ± 0.1–0.2 mm, which can be larger than a snap-fit's interference.

### Assembly and batteries

13. **Adhesive cure.** Respect the full cure time before drop, ingress or pull tests. UV adhesives need a
    light path, so opaque parts need another adhesive.
14. **Cell shipping.** Lithium cells are dangerous goods. Order them to the assembly location. Most PCB fabs
    do not accept them, and couriers restrict them by Wh and packing instruction.
15. **ESD and first article.** Build one unit first and run the full test plan on it. Then build the rest.

### Order

16. **One order per step in `ORDER.md`.** Keep the order confirmations in `checks/orders/`, with date,
    price paid and promised ship date. They become facts for the next cost model.
