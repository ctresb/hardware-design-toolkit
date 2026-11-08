# Fab and assembly capabilities to check

These are the published limits of large prototype fabs, read on their capability pages on 2026-11-08. Fabs change these pages. **Re-read the vendor's current capabilities page before you freeze the rules or order**, and update this table.

Every line is `[verified: page, 2026-11-08]` unless it is marked otherwise.

## JLCPCB, rigid boards ([PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities))

| Item | Limit |
|---|---|
| Trace / space, multilayer | 0.09 / 0.09 mm (3.5 mil); "3 mil is acceptable in BGA fan-outs" |
| Mechanical via | 0.15 mm drill / 0.25 mm pad; 0.1 / 0.2 mm only for boards ≤ 1 mm with ENIG or OSP |
| Via-in-pad | epoxy or copper filled and capped, for 0.15–0.55 mm vias |
| HDI | 1–3 step, 0.075–0.15 mm laser vias |
| Solder mask web (dam) | 0.10 mm for most colors, **0.13 mm for black and white** |
| Copper to board edge | ≥ 0.2 mm |
| Outline tolerance (CNC) | ± 0.2 mm (± 0.1 mm precision option) |

## JLCPCB, flex boards ([flex capabilities](https://jlcpcb.com/capabilities/flex-pcb-capabilities))

| Item | Limit |
|---|---|
| Rigid-flex | not offered |
| 2-layer finished thickness (25 µm PI) | 0.11, 0.12 or 0.2 mm |
| Trace / space | 3/3 mil at 0.33 oz, 3.5/3.5 at 0.5 oz, 4/4 at 1 oz |
| BGA pads | ≥ 0.25 mm, ≥ 0.2 mm pad-to-trace |
| Stiffeners | PI 0.1–0.25 mm; steel 0.1–0.3 mm (slightly magnetic: keep it away from magnets and hall sensors); FR4 "prone to chipping". Steel is recommended under SMD parts. |
| Finish | ENIG only; no impedance control |
| Bend radius | ≥ 10× thickness for multilayer; 10–15× for dynamic bending |
| Size | no minimum; panelize boards under 20 × 20 mm |

## JLCPCB, assembly ([PCBA capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities))

| Item | Limit |
|---|---|
| Smallest passive | 01005 (Standard PCBA); 0402 (Economic) |
| BGA pitch | ≥ 0.3 mm; IC lead pitch ≥ 0.35 mm (Economic 0.40 mm) |
| Double-sided, 0.6 mm boards | Standard PCBA only |
| X-ray | mandatory and automatic for BGA, QFN and LGA, charged per component |
| Minimum assembly size | 70 × 70 mm; panels 70 × 70 to 250 × 250 mm |
| Flex assembly | needs dedicated fixtures (extra cost per order) |

## PCBWay, assembly ([assembly capabilities](https://www.pcbway.com/assembly-capabilities.html))

| Item | Limit |
|---|---|
| BGA pitch | **0.3 mm on rigid, 0.4 mm on flex**, X-ray verified; fine pitch to 0.25 mm |
| Passives | 01005, 0201, 0402 |
| Flex / rigid-flex assembly | by email request first |

## NextPCB, assembly ([assembly capabilities](https://www.nextpcb.com/pcb-assembly-capabilities))

| Item | Limit |
|---|---|
| BGA / LGA | to 0.25 mm pitch; fine-pitch ICs to 0.38 mm; 01005 |
| Substrates | flex and rigid-flex |
| Inspection | AXI for every board with BGA/QFN/LGA; IPC-A-610 Class 2 default, Class 3 on request |

## What this means for a design

- **Most small wearables need no HDI.** QFN/DFN at 0.4 mm pitch, 0201 passives and 0.35 mm board-to-board connectors escape on standard 0.15/0.25 mm vias with 3.5–4 mil traces. HDI is a routing outcome (no room for through-vias), not a package requirement. A 0.35 mm WLCSP is a package requirement for HDI. `[estimate: from the limits above]`
- **Fine-pitch BGA/DSBGA on flex is the usual capability trap.** A 0.35 mm DSBGA is outside PCBWay's published flex limit, and JLCPCB publishes none for flex. In order of preference:
  1. get the assembler's written confirmation, with a steel stiffener under the part;
  2. choose a QFN/SON variant;
  3. move the part to the rigid board.
- **0201 on flex:** place 0201s only over stiffened areas.
- **Black mask on a 0.4 mm QFN:** the pad gap is ~0.2 mm. Black mask needs a 0.13 mm web plus 2 × mask expansion; check it, or use solder-mask-defined pads.
- **Finished flex thickness** must be one of the fab's stack-ups (for example 0.11 or 0.12 mm at JLCPCB), not a free number.
- **Under 70 × 70 mm, panelize.** A 19 mm board in a 3 × 3 array with 5 mm rails is ~73 × 73 mm.

## Choosing a fab

Use established fabs and assemblers only, and say why. In 2026 the known options are:

- **Large Chinese prototype fabs:** JLCPCB, PCBWay, NextPCB, Seeed Fusion.
- **US quick-turn and assembly:** CircuitHub, MacroFab, Screaming Circuits, Sierra Circuits, Advanced Circuits/AdvancedPCB.
- **Europe:** Eurocircuits, AISLER.
- **Hobby and small runs:** OSH Park.

Check that a company still operates before recommending it. At least one US assembly start-up shut down in 2023.

For quantities above ~1k, ask a contract manufacturer (EMS) for a quote. Tariff prices are a prototype ceiling, not a production price.
