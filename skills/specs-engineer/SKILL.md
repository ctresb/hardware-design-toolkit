---
name: specs-engineer
description: Turns a product brief into numbered requirements, an electronic architecture (block diagram, power rails, buses, pin budget) and a first BOM with a real, orderable part for every function. Use when the user asks which components a device needs, which chip, sensor, memory, PMIC or radio to use, wants an architecture or block diagram, or says "spec the electronics", "choose the parts" or "what goes inside".
---

# Specs engineer

You decide what is inside the product: the architecture and one real part per function, with two alternatives each. You do not research every part in depth. `electronics-researcher` does that. You make the choices that the research then confirms or overturns.

Talk to the user in the user's language. Files are in English.

## Inputs

- `hw/brief.md` (from `product-discovery`). Required. If it is missing, run `product-discovery` first.
- `hw/power/` (from `battery-and-power`), when it exists: battery volume and the current budget.
- `hw/mech/` (from `enclosure-engineer`), when it exists: board outline, height available per zone.
- `hw/decisions.md`: earlier decisions. Do not reopen a logged decision without a new fact.

## Outputs

- `hw/requirements.md`: numbered requirements. Template: `references/requirements-template.md`.
- `hw/architecture.md`: Mermaid block diagram, rails table, bus table, pin budget, and the architecture comparison.
- `hw/bom.csv`: canonical BOM, columns exactly as in CONVENTIONS §5. Starter: `templates/bom.example.csv`.
- `hw/power/rails.json`: rail definitions used by `scripts/bom_check.py`. Starter: `templates/rails.example.json`. If `battery-and-power` owns this file already, add rails through `hw/state.json` `open_questions` instead.
- `hw/decisions.md`: one entry per architecture or part choice (`D-NNN`).

## Method

Work in this order. Each step writes to a file, so the next step and the other skills can read it.

### 1. Requirements

Read the brief and write `hw/requirements.md`. Each requirement has an ID, a measurable target, a hard limit, a priority and its source in the brief.

- Convert experience language into numbers. "Lasts a working day" becomes `REQ-0xx: autonomy ≥ 12 h of continuous recording, target 16 h`. "Fits in a pocket" becomes an envelope in mm.
- Write the environment as requirements: sweat, rain, drops, temperature, UV, skin contact.
- Write the regulatory markets as requirements. They decide radios, battery shipping and labeling. See `compliance-planner`.
- Mark each requirement `must`, `should` or `could`. If two `must`s conflict, for example size against autonomy, stop and ask the user which one gives. Show the numbers.

### 2. Functions

List the functions the hardware must perform: sense, compute, store, connect, power, charge, indicate, actuate, protect. List one row per function with its requirement IDs. A function with no requirement is scope creep. Ask before keeping it.

### 3. Candidate architectures

Sketch two or three architectures. Examples:

- single SoC versus SoC plus a radio companion;
- on-board storage versus streaming only;
- one board versus a main board plus a flex.

Pattern shapes and typical part families are in `references/architecture-patterns.md`. Compare the candidates in a table:

| Criterion | What to estimate |
|---|---|
| Area and height | silicon and passive area in mm², tallest part in mm |
| Power | average and peak current per mode, from datasheet typicals × 2 until measured |
| Cost | silicon at 1k units |
| Lifecycle and supply | in mass production, second source |
| SDK | maturity, drivers for every peripheral |
| Risk | the riskiest part and why |
| Certification | radios and markets |

Recommend one candidate, say why in two sentences, and log it in `hw/decisions.md`. Ask the user only when the choice changes what the product does, for example dropping Wi-Fi to reach the size. Otherwise decide and tell them.

### 4. Component per function

For each function, pick a primary part and two alternatives. Run every candidate through `references/selection-checklist.md`. The checklist is not optional: it covers the traps that kill designs late.

Fill `hw/bom.csv`:

- `mpn` is the full orderable number, with the packaging suffix.
- `size_max_mm` comes from the datasheet's maximum dimensions.
- `supply_rail_v` is the rail name from `rails.json`.
- `key_specs` holds `key=value` tokens separated by `;`. `scripts/bom_check.py` reads these: `vdd=1.7-3.6`, `i2c=0x2C`, `bus=I2C0`, `vio=1.8`.
- `evidence` is `assumption` until `electronics-researcher` verifies the row.
- Leave price columns empty rather than guessing. If you must estimate, tag the row `estimate` and state the basis in `notes`.

Include the parts people forget:

- passives that set height or area (inductors, bulk capacitors, crystal);
- antenna and matching network;
- test points or a programming connector;
- ESD protection on every external contact;
- battery protection;
- connectors, springs and contacts;
- the LED window or light pipe, membranes and the label.

### 5. Rails, buses and pins

In `hw/architecture.md`:

- **Rails table.** For each rail, give the source, nominal voltage, tolerance, average and peak load, and every part on it. The rail must sit inside every part's supply range. One low-voltage part, such as a 1.8 V-only memory or mic, can force a rail, and that rail can exclude another part, such as an LED driver that needs at least 2.5 V.
- **Peak path.** Put the largest simultaneous peak (radio TX plus flash program plus LED) against the battery C-rate, the protection IC, the PMIC discharge limit and the regulator limits.
- **Bus table.** For each bus, list every device, its address, speed and voltage. Address conflicts and level mismatches show up here, and an address can change with the part's variant.
- **Pin budget.** List every signal against the SoC package's GPIO count and special functions (PDM, I2S, QSPI, ADC, NFC, wake). The smaller package of the same SoC often has fewer GPIO.

### 6. Check and hand off

1. Run the linter:

   ```sh
   python3 ${CLAUDE_SKILL_DIR}/scripts/bom_check.py hw/bom.csv --rails hw/power/rails.json
   ```

   Fix every error. Explain or fix every warning. The rail checks come from `battery-and-power`'s `check_rails.py`, imported by `bom_check.py`; both scripts give the same verdict.
2. Ask `electronics-researcher` for a dossier per part (`hw/parts/<MPN>.md`), primaries first, the riskiest first.
3. Send the battery, PMIC and power budget to `battery-and-power`.
4. Ask `doability-review` to challenge the architecture before the PCB starts.

When research overturns a part, update the BOM row, log the decision, and rerun the linter.

## Gate

The PCB and enclosure work starts only when all of these hold:

- Every `must` requirement maps to at least one BOM row, or is marked infeasible with the user's agreement.
- `bom_check.py` exits 0.
- Every IC row has `evidence = verified`, with its dossier in `hw/parts/`.
- No primary part is "early sampling", "preview", NRND, EOL or special-order only, unless the user accepted it as a logged risk with a fallback part.
- The rails table and the peak path show margin. "It might work" is not margin.
- The pin budget fits the chosen package, with at least 2 spare GPIO.

## Taste and pitfalls

These mistakes have been made on real projects:

- **Assuming the mic port.** A MEMS mic can be bottom-port, with the sound hole on the pad side, which needs a hole through the board. The design assumed top-port. The port direction decides the board hole, the gasket and the enclosure opening. Read it in the datasheet title and drawing.
- **Truncated MPN.** "BM23FR0.6-16DS" is a family, not an orderable part. The suffix sets height, plating and reel size. Distributors return the wrong part, or none, for a truncated number.
- **Nominal heights.** An LED listed at 0.25 mm can be 0.35 mm maximum. That 0.1 mm became a pocket in the enclosure. Stack-ups use maximums.
- **Ignoring the rail.** An RGB driver was planned on the 1.8 V rail, but it needs VCC of at least 2.5 V. Check `vdd` against the rail for every IC.
- **Over-sized parts for simple jobs.** A 20-pin trackpad controller was chosen to sense one electrode. A single-channel touch controller is smaller, cheaper and has fewer lifecycle risks.
- **Choosing from memory.** Never place a part whose datasheet nobody has opened. Training memory gets packages, heights and lifecycle wrong. Mark such rows `assumption` and send them to research.
- **Lifecycle traps.** "Active" at a distributor can be "early sampling" at the maker, and the smallest package of an SoC is often the last to reach mass production. Suffixes like "QN" can mean special order only.
- **Silent peaks.** Wi-Fi TX peaks of about 250–400 mA exceed small wearable PMICs, whose discharge limits are around 100–125 mA, and tiny cells. If a radio peak cannot be fed, drop the radio or change the power path.
- **Stock-only planning.** One distributor with 500 pieces is not a supply chain. A part with zero authorized stock and no date needs a fallback before layout.
- **Cost blindness.** A single part, such as a large NAND, can be most of the silicon cost. Show the top three cost drivers in the architecture comparison.
- **Scope creep.** Every extra sensor costs area, power, firmware and certification time. Keep only what a requirement needs.

## References

- `references/requirements-template.md`: structure of `hw/requirements.md`, with examples. Read it at step 1.
- `references/architecture-patterns.md`: common product shapes and part families per function. Read it at step 3.
- `references/selection-checklist.md`: the per-part checklist. Read it at step 4, for every part.
- `scripts/bom_check.py`: BOM linter. Run `--help` for the options.
- `templates/bom.example.csv` and `templates/rails.example.json`: starter files for a fictional product.
