---
name: pcb-engineer
description: Designs the product's PCBs in KiCad from one JSON spec, scripted and reproducible. Covers the outline from the enclosure, footprints from KiCad libraries or datasheets, nets, legalized placement with keepouts, schematic, ERC/DRC, optional autorouting and exports (GLB/STEP, pads.json, Gerbers, BOM, CPL). Use for "make the PCB", "lay out the board", "KiCad", "footprint", "placement", "Gerbers", "flex board", or when the architecture and BOM need a board.
---

# PCB engineer

This skill turns `hw/architecture.md` and `hw/bom.csv` into KiCad boards a named fab can build. Everything comes from one spec file, `hw/pcb/board.json`. The schematic, the board and every export are regenerated from it, so a change never drifts between files.

Talk to the user in their language. Keep every file in English.

## Inputs

- `hw/architecture.md`: blocks, rails, buses and pin assignments.
- `hw/bom.csv`: full MPNs, packages, `size_max_mm`. Only parts with `lifecycle` active or new.
- `hw/parts/<MPN>.md`: pinouts, land patterns, reference circuits, from `electronics-researcher`.
- `hw/power/rails.json`: rail names and voltages, so net names match the power chapter.
- `hw/mech/`: the board outline (SVG or polygon), keep-in height per side, magnet/battery/port positions, from `enclosure-engineer`.
- `hw/state.json`: the fab chosen in `cost-and-sourcing`, if any. Otherwise, design to the common rules in `references/fab-capabilities.md`.

## Outputs

| Path | Content |
|---|---|
| `hw/pcb/board.json` | the spec (the only file edited by hand) |
| `hw/pcb/lib/` | project symbol and footprint library, 3D bodies of generated footprints |
| `hw/pcb/<board>/` | `.kicad_sch`, `.kicad_pcb`, `.kicad_pro`, `erc.json`, `drc.json`, `placement-report.json` |
| `hw/pcb/export/` | `<board>.glb` (and `.step`), `<board>_{top,bottom,iso}.png`, `pads.json`, `tex/` |
| `hw/pcb/fab/<board>/` | `<board>_gerbers.zip`, `<board>_bom.csv`, `<board>_cpl.csv` (JLCPCB columns), `stackup.md`, `order.md`, `panel-plan.json` (+ `panel.json` for KiKit) |
| `hw/pcb/build-summary.json` | counts from every check, and the result line |
| `hw/pcb/release-check.json` | the ready-to-order gate result, with every missing item |
| `hw/pcb/pcb.md` | the PCB chapter: stack-up, fab, rules, open items, images |

## Tools

All scripts are in `scripts/`. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/kicad_env.py` first. It reports KiCad, its Python, the libraries, Java and Freerouting. If something is missing, run `toolchain-setup`.

| Script | Runs with | Job |
|---|---|---|
| `build.py spec [--route] [--step] [--strict] [--release]` | system Python | the whole pipeline below, stops at the first failing gate |
| `pins.py Lib:Symbol [--footprint Lib:Fp]`, `--search`, `--search-footprint` | system Python | pin names and pad numbers, to fill a part's `pins` |
| `spec.py spec` | system Python | validate the spec |
| `libgen.py`, `schgen.py` | system Python | library + pin/pad/net cross-check; schematic |
| `pcbgen.py` | KiCad Python | board, outline, legalized placement (real courtyard polygons), planes, keepouts, stack-up |
| `route.py export \| import \| run` | KiCad Python (+ Java for `run`) | Freerouting in three steps: DSN out here, route on any machine, SES back here (heavy step off the laptop) |
| `finish.py dupes \| planes \| islands \| grid \| prune \| net` | KiCad Python | close what the autorouter leaves: duplicate links, plane stitching, island vias, a multi-layer A* router for the last nets |
| `export.py --what erc,drc,3d,step,fab,render,pads,textures` | system Python | checks and outputs |
| `fabnotes.py` | system Python | `stackup.md` (stack-up and impedance), `order.md`, `panel-plan.json` and KiKit `panel.json` |
| `release_check.py` | system Python | the ready-to-order gate (below); exit 0 only when nothing is missing |
| `outline.py`, `stepbox.py` | either | outline polygons (circle, rounded rect, polygon, SVG path, smooth union); STEP boxes |

`scripts/` runs on KiCad 10.0 with KiCad's bundled Python 3.9; the code is 3.9-compatible on purpose. The example in `templates/example/board.json` builds end to end: a 20 mm round, 4-layer BLE sensor with an SoC, charger, LDO, accelerometer, chip antenna, dock contacts and magnet keepouts. Copy it as a starting point.

Field reference for the spec: `references/spec-format.md`.

## Procedure

1. **Read the inputs and write down the board decisions** in `hw/decisions.md`: how many boards (rigid, flex, rigid + flex with a board-to-board connector), stack-up, thickness, finish, mask color, single- or double-sided assembly, and the target fab. Check each against `references/fab-capabilities.md`. Ask the user only about what changes the product, such as a flex for touch/LED/mics near the shell, or a second board for the dock contacts.
2. **Get the outline from the enclosure.** Use `enclosure-engineer`'s outline (SVG or polygon) inset by the wall clearance. Never draw a board bigger than the cavity "to fit later".
3. **Write `board.json`.**
   - Parts come from `hw/bom.csv`. Prefer KiCad standard symbols and footprints (`Lib:Name`); check them with `pins.py`.
   - If a part has no library footprint, generate one from the datasheet's **recommended land pattern** (not the package drawing), with a `body` of the datasheet's maximum dimensions. Cite the datasheet figure in the footprint `description`.
   - Name the pins as the datasheet does. Write every pin: a net, or `null` for a deliberate no-connect. Use `nc_rest` only for unused GPIOs.
   - Copy the reference circuit of every IC (decoupling, crystal load caps, DC/DC inductor, RF matching) from the manufacturer's reference design, and cite it in `description`.
   - Give rough positions in the device frame: origin at the board center, +x right, +y up, seen from the F side. Mark as `fixed` the parts whose position the product decides: connectors, antenna, contacts, sensors under windows, LEDs under light pipes, mics over ports, battery tabs.
   - Add `keepouts` for everything the enclosure puts against the board (magnets, battery, screw bosses, ribs, mic ports), on the right side. Add `exclusive` areas for the RF corner and for touch electrodes.
4. **Build:** `python3 ${CLAUDE_SKILL_DIR}/scripts/build.py hw/pcb/board.json`. Fix every gate at its cause:
   - library errors (pin without pad, pin without net): fix the spec, never the generated files;
   - ERC errors: fix nets or pin types; read each warning;
   - placement failure: the report names the part and what it hit. Move it, change side, or grow the board **with the enclosure owner**. Do not shrink a courtyard or a keepout to make it pass.
5. **Review the images** (`export/<board>_top.png`, `_bottom.png`, `_iso.png`) before saying anything is done. Check pin 1 marks, part orientation, the RF corner, test point access, and parts under windows.
6. **Feed the 3D model back.** Send `export/<board>.glb` and `export/pads.json` to `enclosure-engineer`, whose assembly validator checks the board against the enclosure. Each collision becomes a keepout or a fixed position in the spec; then rebuild. This loop catches parts placed over magnets, mic ports covered by a stiffener, and connectors taller than the gap.
7. **Route.** Hand-route and lock the critical nets first (`references/workflow.md`). Autorouting (`build.py --route`) is a first pass for the rest. It is CPU-heavy: run it on a workstation or cloud VM, never on the laptop that runs the session.
8. **Make it orderable.** In the spec:
   - fill `lcsc` (or mark `consign`) and `mpn` for every part;
   - set `fab`, `panel` and `fiducials`;
   - add `impedance` to the RF and high-speed net classes.
   Then run `build.py --step --release` on the machine with the routed board.
9. **Finish.** Fix every item `release_check.py` lists until it exits 0. Then write `hw/pcb/pcb.md` (stack-up, fab, rules, images, revision) and update `hw/state.json`.

## Gate

The PCB stage delivers a board that can be ordered **with no further changes**. It is done only when `python3 ${CLAUDE_SKILL_DIR}/scripts/release_check.py hw/pcb/board.json` exits 0, which requires all of the following:

1. **Routed.** Freerouting runs as a documented step on a workstation or cloud machine, never on the laptop running the session (`references/workflow.md`, "Routing on another machine"). The critical nets are routed by hand first. Zones are then refilled (`route.py` and DRC `--refill-zones` both do it). DRC reports 0 unconnected items.
2. **Checks at zero.** DRC has 0 errors, 0 schematic-parity issues, and no warnings except silkscreen cosmetics. ERC has 0 errors and no warnings except PWR_FLAG pin-type notes. Both reports are newer than the board file.
3. **Fab outputs in the chosen fab's format**, in `hw/pcb/fab/<board>/`:
   - a Gerber + drill zip with every copper layer, both masks, paste, the outline, and PTH and NPTH drill files;
   - BOM and CPL in JLCPCB format, listing the same parts. Every line has an LCSC part number where the assembler stocks it, or is marked `consign`.
4. **Stack-up and impedance notes** (`stackup.md`), with an impedance line for every controlled-impedance net class, and **order notes** (`order.md`).
5. **Assembly minimum size handled.** Either the board meets the assembler's minimum (JLCPCB: 70 × 70 mm), or a panel is planned (`panel` in the spec: by the fab's service, or KiKit files generated).
6. **Fiducials.** At least 2 per assembled side on the board, or 3 on the panel rails.
7. **Placement clean.** No failed part and no fixed-part collision. The assembly validator in `enclosure-engineer` passes with this board's GLB.
8. **Every generated footprint cites its land-pattern source**, and every IC's reference circuit is cited in its part `description`.

**A placed but unrouted board is a placement study, not a PCB.** Report it that way, with the `release_check` failure list.

## Taste and pitfalls

- **The spec is the source.** Regenerate, never hand-edit generated files. A manual fix is lost on the next build.
- **Do not bend a footprint to fit a part that does not exist.** If the chosen part's package is not orderable, or is "early sampling", change the part (`specs-engineer`). Do not draw a smaller footprint.
- **Size by maximum dimensions.** Courtyards and 3D bodies use the datasheet maximum, not the nominal. A 0.25 mm nominal LED that is 0.35 mm max hits the shell.
- **Keepouts come from the 3D assembly, and they are permanent.** When the validator finds a part over a magnet, add a keepout to the spec so the legalizer can never put it back.
- **Netclass clearance must fit the package.** A 0.2 mm RF clearance on 0201 parts (0.18 mm pad gap) makes DRC fail on the part itself. Set rules that real packages can meet.
- **Real 3D models for anything mechanical.** Connectors, springs, switches, batteries and shields use the vendor's STEP (`"models"` in the spec). A generic box is only for passives and ICs.
- **Bottom-port mics need a hole in the board,** sealed to the enclosure port. Top-port mics need a port in the shell above them. Read the mic datasheet for which kind it is before placing it.
- **Every exposed contact gets ESD protection** next to the contact, and test points for SWD/reset/rails go on the side reachable from a fixture.
- **Silkscreen on tiny boards is noise.** Use `"footprint_silk": "fab"` under ~30 mm and put the board revision on a fab layer or in copper.
- **Black or white solder mask needs a wider mask web** (0.13 mm vs 0.10 mm at JLCPCB). Check fine-pitch QFNs before you choose the color.
- **Keep local runs light.** Generate, ERC, DRC and exports run in under a minute on the example. Autorouting and STEP export are the heavy steps.
- **Remove duplicate copper links before routing the last nets** (`finish.py dupes`). A track that repeats a same-net pour, or a track between two pads that the part connects internally (a 4-pin tactile switch), adds copper that blocks the escape of the remaining nets.
- **Run DRC inside the board's project folder.** On a copy outside it, `kicad-cli` loses the project rules, applies 0.2 mm defaults and reports hundreds of false violations.
- **DRC does not keep a signal out of a QFN pad ring or a via out of a cell contact area.** Use rule areas in the spec, or `finish.py net --no-under REF --no-via-circle X,Y,R`.
- **An SMD pad does not anchor a pour island.** An island that touches only SMD pads of its net is still unconnected to the plane. `finish.py islands` counts only vias and PTH pads, and never puts a via under a part body.
- **Pick the Freerouting version for the board.** 2.5.0 needs Java 25 and stops after about 19 passes when the score stops improving. 1.9.0 (Java 17+, under `xvfb-run` on headless Linux) routed a dense 28 mm 4-layer board further. `kicad_env.py` checks the Java a jar needs.

## References

- `references/spec-format.md`: every field of `board.json`, with the shortcuts. Read it when writing or changing a spec.
- `references/workflow.md`: the loop from spec to fab, what to hand-route, when to autoroute, and how to read the reports.
- `references/fab-capabilities.md`: the published limits of large prototype fabs to check against (verified 2026-11-08, re-check before ordering).
- `references/layout-rules.md`: antenna, RF, crystal, DC/DC, decoupling, mics, touch, ESD, test points, stack-ups, flex and stiffeners.
