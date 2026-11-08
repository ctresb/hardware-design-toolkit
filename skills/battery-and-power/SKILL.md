---
name: battery-and-power
description: Builds an evidence-tagged power budget and sizes a battery that a real vendor can make, with straight-edged pouch outline, seals, swelling, tolerance and end-of-life derating. Checks peak currents against cell, protection, PMIC and regulator limits, checks every IC's supply range, and chooses a charging method. Use for "how long will the battery last", "what battery fits", "power budget", "mAh", "runtime", "charging", "rails" or before ordering a custom cell.
---

# Battery and power

This skill makes the energy side of a product honest. Its job is to stop the most common hardware fantasy: a battery shaped like the leftover space, credited with a phone's energy density, feeding a current nobody has measured.

Talk to the user in their language. Keep every file in English.

## Inputs

- `hw/requirements.md`: runtime target, size limits, use pattern (how many hours a day in each mode), environment temperature.
- `hw/architecture.md`: power tree, rails, radios, peak loads.
- `hw/bom.csv`: `supply_rail_v` (rail name), `key_specs` (`vdd=lo-hi` tokens), `typ_current_ma`, `peak_current_ma`.
- `hw/mech/`: the battery pocket outline (SVG or polygon) and its height, when `enclosure-engineer` has one. Otherwise, the size limits from the requirements.
- `hw/parts/<MPN>.md`: current figures with sources, from `electronics-researcher`.

## Outputs

| File | Content |
|---|---|
| `hw/power/budget.input.json` | the budget model: modes, duties, parts, rails, comparables, limits. Format: `templates/power_budget.example.json` |
| `hw/power/budget.json` | results from `scripts/power_budget.py` |
| `hw/power/rails.json` | **shared rail table**, owned by this skill (schema below) |
| `hw/power/battery.json`, `hw/power/battery.svg` | results from `scripts/battery_fit.py`: outline, thickness, capacity range, top view |
| `hw/power/power.md` | the human-readable power chapter (`templates/power.md`) |
| `hw/power/measurements/` | captures and notes, once measured |

### Shared rail table: `hw/power/rails.json`

Each rail gives its voltage either as a range or as nominal ± tolerance in volts, plus its current limit. `{"nom": 1.8, "tol": 0.05}` spans 1.75–1.85 V.

```json
{
  "VSYS": {"min": 3.0, "max": 4.4, "max_ma": 125},
  "1V8":  {"nom": 1.8, "tol": 0.05, "max_ma": 150}
}
```

- `hw/bom.csv` → `supply_rail_v` holds the rail **name** (`1V8`). A part on several rails lists them as `VSYS|1V8`, matched in order to `vdd`, `vdd2`, and so on.
- `key_specs` holds tokens such as `vdd=1.7-3.6; vio=1.8; i2c=0x2C`.
- The budget input carries the same fields per rail, plus the regulator model (`type` direct|ldo|buck|boost, `efficiency`, `iq_ma`, `off_modes`). `power_budget.py --rails-out` writes the table.
- `scripts/check_rails.py hw/bom.csv hw/power/rails.json` fails any part whose supply range does not contain its rail's full range. It is the toolkit's single rail implementation: `specs-engineer`'s `bom_check.py` and `electronics-researcher`'s `bom_merge.py` import it.

## Workflow

1. **Collect the use pattern.** Define the modes (for example active, record, stream, sync, idle, ship) and the fraction of a day spent in each. If the user does not know, propose a realistic pattern and log it as an `[assumption]` in `hw/decisions.md`.
2. **Write the budget input.** Write `hw/power/budget.input.json`, with one entry per part that draws current and one current per mode.
   - Every current carries an evidence tag (CONVENTIONS §6).
   - Use the datasheet figure for the mode the firmware will really use: TX power, sample rate, flash program duty.
3. **Add comparables.** Find 2–3 shipped products in the same category that publish battery capacity and runtime. `electronics-researcher` can find them. Put them in `comparables`. Their average current (capacity × usable fraction / runtime) is the empirical case, and it often is 3–5× the bottom-up baseline.
4. **Run the budget:**
   `python3 ${CLAUDE_SKILL_DIR}/scripts/power_budget.py hw/power/budget.input.json -o hw/power/budget.json --rails-out hw/power/rails.json`
   - It reports four scenarios (optimistic, baseline, pessimistic, empirical), runtime when new and at end of life, the rated capacity needed, the largest contributors, and the peak checks.
   - Exit code 2 means a peak limit was exceeded.
5. **Check the rails:** `python3 ${CLAUDE_SKILL_DIR}/scripts/check_rails.py hw/bom.csv hw/power/rails.json`. Fix every failure in the architecture (another rail, a different part, a level shifter) and tell `specs-engineer` through `hw/state.json` → `open_questions`.
6. **Size the battery.** Read `references/battery-reality.md` first.
   1. Look for catalog cells that fit the pocket (§6 of the reference).
   2. Then run the fit:
      `python3 ${CLAUDE_SKILL_DIR}/scripts/battery_fit.py --svg hw/mech/battery_pocket.svg --height <mm> --claimed-mah <current claim> --svg-out hw/power/battery.svg --json hw/power/battery.json`
      - Inputs: `--rect W L` or `--polygon file.json` instead of `--svg`. `--stepped` allows one step (custom cells only). `--chem pouch-hv` selects a high-voltage cell.
      - Exit code 1 means the claimed capacity is above the realistic range.
   3. Show the user `battery.svg`. Plan the product on the **low end** of the capacity range until a vendor quotes it.
7. **Close the loop.** Compare the realistic capacity with the rated capacity each scenario needs. If the pessimistic or empirical case does not fit, present the options as a short table and recommend one:
   - less runtime;
   - a lower duty cycle or a lower-power mode;
   - a different radio or codec;
   - a larger product;
   - a high-voltage or custom cell.
8. **Choose the charging method** with `references/charging-options.md`. Prefer methods that add no opening. Check the charge current against the cell's C-rate, and the charge time against the use pattern.
9. **Plan the measurement** with `references/measurement.md`: instrument, firmware build, modes to capture, pass criteria. This plan is part of the gate.
10. **Write `hw/power/power.md`** from `templates/power.md`. Add each decision to `hw/decisions.md` and each question for the user to `hw/state.json`.

## Gate

The next stage, especially any custom cell, mold or board-size freeze, starts only when all of these hold:

- [ ] Every current in the budget has an evidence tag. The four scenarios are reported.
- [ ] Every peak is below every limit in the chain: cell, protection, PMIC, regulators, brown-out drop.
- [ ] `check_rails.py` passes.
- [ ] The battery is a shape a vendor makes (catalog, rectangle, or one step). Its capacity is the fit's realistic range, not a claim. The fit is shown as an SVG.
- [ ] The planned capacity covers the pessimistic or empirical case at end of life, or the user has accepted a lower runtime in `hw/decisions.md`.
- [ ] A measurement plan exists. Before a custom cell is ordered, a measured average current exists and passes (`references/measurement.md`).

## Taste and pitfalls

- **Never fill leftover space with a blob-shaped cell.** Draw a straight-edged rectangle. Consider a step only when the gain is large and the volume justifies a custom cell. If the user sketches an outline, honor its intent with straight segments and say what each curve costs.
- **Never size a custom cell before measuring.** Freezing the cell first and measuring later is a process inversion. It happened in a real project and forced a lower average current than had ever been shown.
- **Do not trust a bottom-up budget alone.** Show the empirical case next to it, even when it is uncomfortable.
- **Small cells lose a large share to seals.** At about 20 mm, seals and tabs take 25–40 % of the outline. Say so with the number.
- **Thickness is a max dimension.** Subtract the tolerance and the swelling, and never compress the cell.
- **Check radio peaks against the PMIC's system-load limit,** not only the battery's. One high-power radio can exclude a whole PMIC family.
- **Do not promise compatibility with another company's charger or dock.** They are proprietary.
- **The battery fixes shipping and compliance work:** UN38.3 for each cell design, IEC 62133-2, and EU rules on removable batteries (Battery Regulation Article 11, applying from February 2027). Add these as items for `compliance-planner`. Do not decide them here.
- **Use exact, aligned numbers in tables and drawings.** Write a range as `55–65 mAh [estimate]`, never as a bare `70 mAh`.

## Bundled files

- `scripts/power_budget.py`: budget, scenarios, runtime, required capacity, peak chain, rail table.
- `scripts/battery_fit.py`: largest straight-edged cell in a pocket (rectangle, JSON polygon or SVG path); conservative capacity range; SVG top view.
- `scripts/check_rails.py`: each IC's supply range against `rails.json`.
- `templates/power_budget.example.json`: example budget input (a fictional BLE voice clip).
- `templates/pocket.example.svg`: example pocket outline in mm.
- `templates/power.md`: outline of the power chapter.
- `references/battery-reality.md`: cell types, densities, pouch anatomy, shapes, sizing, custom-cell economics, vendor RFQ.
- `references/charging-options.md`: charging methods, charge rules, peak current chain.
- `references/measurement.md`: instruments, procedure, gate, cell testing.
