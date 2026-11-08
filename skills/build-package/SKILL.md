---
name: build-package
description: Assembles the release package of a hardware project and runs the READY TO BUILD gate - fab files, assembler BOM/CPL with stock check, purchase carts, enclosure STEP/STL, battery spec, assembly guide, test plan, pin map, ORDER.md with cost and lead time per step, and a hashed manifest. Use when the design is done and the user wants to order, "make it ready to build", "release", "send to the factory", "build N prototypes", or before any money is spent on fabrication.
---

# Build package

The toolkit delivers a design that someone can order and build **without further design work**. This skill
collects the outputs of all stages into one release folder. It also runs the gate that decides whether the
release is **READY TO BUILD**. If the gate fails, the release is not ready. Send each failure back to the
skill that owns it, fix it there, and run the gate again. Do not patch files inside the release by hand.

Talk to the user in their language. Release files are in English unless the user chose another language.

## Inputs

| Path | From | Used for |
|---|---|---|
| `hw/release/release.json` | this skill (you write it) | revision, target level, boards, assembler, build size, enclosure parts, battery, order steps (format: `templates/release.example.json`, fields in `references/release-config.md`) |
| `hw/pcb/<board>/` `drc.json`, `erc.json`, `.kicad_pcb`, `.net` | `pcb-engineer` | DRC/ERC = 0, routed board, pin map |
| `hw/pcb/fab/<board>/` Gerber zip, BOM, CPL | `pcb-engineer` | fab and assembly files |
| `hw/bom.csv` | `specs-engineer`, `electronics-researcher` | orderable MPNs, LCSC numbers, stock dates |
| `hw/mech/cad/` STEP/STL, `hw/mech/dfm.md` | `enclosure-engineer` | enclosure parts |
| `hw/validation/assembly.json` | `enclosure-engineer` | assembly passes, newer than the CAD |
| `hw/drawings/` | `technical-drawing` | the 2D drawing PDF and exploded images |
| `hw/power/` | `battery-and-power` | battery spec, power-measurement thresholds |
| `hw/cost/` | `cost-and-sourcing` | cost and lead time per order step |
| `hw/doability/` | `doability-review` | the overall verdict, and the "Verify on the prototype" list |

## Outputs: `hw/release/<rev>/`

```
README.md            what this release is, its level, how to use it
ORDER.md             numbered order steps: where, what to upload, options, cost, lead time, receiver
MANIFEST.json        every file with sha256, size and source stage
fab/<board>/         Gerber+drill zip, IPC netlist (if exported), fab-notes.md (stack-up, finish, mask, min features, stiffeners, panel)
assembly/<board>/    BOM and CPL in the assembler's format, stock.md (stock per line with date), consigned.csv, options.md
purchasing/          digikey.csv, mouser.csv (BOM-upload format), mechanical.csv, purchasing.md (quantities with attrition)
mech/                <part>.step, <part>.stl, print-settings.md, drawing PDF, mech-bom.csv
battery/             battery.md (catalog cell + holder, or the custom-cell spec for the vendor)
assembly-guide/      assembly-guide.md and its images
test/                test-plan.md (bring-up, test points, power plan with thresholds, functional tests), verify-on-prototype.md
firmware/            pins.json and pins.h for the MCU (from the netlist), when configured
checks/              copies of the reports the gate used (DRC, ERC, validator, doability) and release-check.json
```

## Procedure

1. **Write `hw/release/release.json`.** Copy `templates/release.example.json`, and set the revision
   (`A`, `B`…) and the target level (`prototype` or `production`). Fill in the boards, the assembler
   (JLCPCB first), the build size, the enclosure parts, the battery and the order steps. Take each step's
   cost and lead time from `hw/cost/`, and cite it.
2. **Write the documents that only this skill owns.** Use the templates:
   - `assembly-guide.md` (`templates/assembly-guide.md`): numbered steps, exploded images from
     `technical-drawing`, adhesive and cure time, torque, and a QC check after each step;
   - `test-plan.md` (`templates/test-plan.md`): bring-up order, test points, the power-measurement plan with
     pass thresholds from `battery-and-power`, and the functional tests;
   - `battery.md` (`templates/battery-spec.md`);
   - `print-settings.md` (`templates/print-settings.md`).

   Put them in `hw/release/src/`. Every value comes from a stage file, and you cite its ID or path. Leave
   no `<placeholder>`, TBD or TODO.
3. **Assemble.**
   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/assemble_release.py hw/ --config hw/release/release.json
   ```
   - It copies the stage outputs into `hw/release/<rev>/`.
   - If `pcb-engineer` did not export them, it builds the assembler BOM and CPL from the KiCad position file
     and `hw/bom.csv`, applying the rotation offsets in the config.
   - It writes the purchase carts with attrition, the pin map, `ORDER.md`, `README.md` and `MANIFEST.json`.
4. **Gate.**
   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/release_check.py hw/release/<rev>/ --hw hw/
   ```
   It prints each failure with the owner skill and exits non-zero if the release is not READY TO BUILD
   (checks in `references/ready-to-build.md` §3). Send each failure to its owner. Re-run steps 3–4 until the
   gate passes. After 3 rounds, stop and show the user the remaining blockers with the exact actions.
5. **Pre-order review.** Go through `references/ready-to-build.md` §4 with the release open. Pay attention to
   rotation and polarity in the assembler's preview, basic vs extended part fees, the panel, clear-part
   finishing and cell shipping. Record the result in `hw/release/<rev>/checks/pre-order.md`.
6. **Hand over.** Tell the user the level, the total cost and lead time for the build size, and the first
   step of `ORDER.md`. Ordering spends money: never place an order or upload files for the user without
   their explicit go-ahead.

## Gate

`release_check.py` exits 0 and the doability verdict is `READY TO BUILD (prototype)` or
`READY TO BUILD (production)`, matching `release.json` → `target`. A release that fails the gate is
labelled **NOT READY** in its README, with the failure list.

## Taste and pitfalls

- **"Unrouted" is not "almost done".** A board with zero tracks or with unconnected items fails the gate,
  however good the 3D looks.
- **Stock goes stale fast.** Re-check the assembler stock and distributor stock within 14 days of ordering.
  The gate fails older dates.
- **Rotation offsets are per footprint and per assembler.** Check every polarized part (diodes, LEDs,
  ICs, connectors) in the assembler's 3D preview before you pay. A mirrored LED or a rotated QFN costs a
  whole batch.
- **One source of truth.** The release copies files and never edits them. Fix a wrong value in its stage
  file, then assemble again.
- **The validator must be newer than the CAD.** A passing report from before the last CAD change proves
  nothing.
- **Prototype measurements are not blockers, but they need thresholds.** "Measure the current" is not a
  test. "Average current in mode X ≤ 1.5 mA over 10 min, measured on a PPK2 at 3.0 V" is a test.
- **Clear parts need a finishing plan.** An SLA print is not clear until it is wet-sanded and coated or
  polished. Write the steps, otherwise the prototype looks foggy.
- **Lithium cells ship as dangerous goods.** Order them to the assembly location, never in the same box as
  the boards from a fab that does not ship cells.

## Bundled files

- `scripts/assemble_release.py`, `scripts/release_check.py`, `scripts/release_lib.py` (standard library only, `--help`). `scripts/selftest.py` runs both on the fixture: 1 pass case and 11 failure cases.
- `templates/release.example.json`, `templates/assembly-guide.md`, `templates/test-plan.md`,
  `templates/battery-spec.md`, `templates/print-settings.md`.
- `templates/example/`: a test fixture (a fictional board), used only to test the two scripts.
- `references/ready-to-build.md`: definitions, the gate checks and the pre-order checklist.
- `references/release-config.md`: every field of `release.json`.
