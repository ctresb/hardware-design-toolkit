# DFM review: Pocket Beacon enclosure

Issue: 1 · Date: 2026-11-08 · Owner: enclosure-engineer · Automated check: `hw/mech/cad/pocket-beacon_dfm.md` (**PASS**, 0 errors, 3 draft warnings)

## Parts and process

| Part | Material | Process | Pull | Mechanisms | Note |
|---|---|---|---|---|---|
| Shell | PC optical grade (smoke) or PC/ABS (graphite, chalk) | 2-shot injection with the button | +Z | none | wall 0.9 mm, front 0.9 mm, edge fillet R1.8 |
| Button | TPU 80A, translucent | 2nd shot into the shell | +Z | 2-shot tool (rotary platen) or an overmold insert tool | LED D1 shines through it |
| Back plate | PC/ABS, shell color | injection | −Z (outer face) | none | bonded to the shell with die-cut PSA plus a 0.9 mm lip |
| Door | PC/ABS, shell color | injection | −Z | none | 2 ears with counterbores for the captive screws |
| Door gasket | silicone 40A, 0.35 mm (T-4) | die-cut | — | — | flat ring, set by the ear-to-cap stop |
| Port gasket | soft PU foam, 0.8 mm, PSA (T-5) | die-cut | — | — | ring Ø3.0/Ø1.6 on the LS1 port |
| Acoustic vent | ePTFE membrane, IP67 grade, PSA | die-cut | — | — | Ø2.5 in the Ø2.6 seat; Gore / Saati / Nitto (RFQ) |
| Screws | 2 × thread-forming for plastics, 1.4 × 3 mm, stainless, captive | bought | — | — | UL 4200A option 1: a tool opens the compartment |

All parts release in a straight pull. **No side actions and no lifters.** The keyring slot is vertical, at the +x+y corner, so it needs no side action. The bayonet design needed 2 side actions in the door tool (D-511).

## Automated warnings, and the decision for each

| Warning | Where | Decision |
|---|---|---|
| shell: 134 mm² with draft under 0.5° | keyring slot walls (8 mm long through-hole), small core pins | Accept. The molder adds 0.5° per side to the slot core, or splits it into two pins that meet at mid-height (Q-M2) |
| plate: 238 mm² with draft under 0.5° | screw pilot holes, lobe pockets, door bore | Accept. Short cores; the molder adds draft to the bore (0.5°) and keeps the pilots straight for the screw |
| door: 94 mm² with draft under 0.5° | screw holes and counterbores in the ears | Accept. Standard straight holes |

## Gates, weld lines and cosmetics

- **Shell gate:** a submarine gate on the inner rim at the −x−y corner, which is hidden under the plate. The flow front splits around the button hole and the keyring slot. Weld lines form on the +x+y side of the button hole and around the slot. On the smoke PC part, the button hole weld line is visible. Ask the molder for a flow simulation, and move the gate if the line lands on the front face (Q-M3).
- **Finish:** front SPI A2 on the smoke variant (optical), SPI B1 / MT-11010 texture on graphite and chalk. Sides take the same finish, with 1° draft for texture.
- **Markings:** the safety-alert and ingestion icons on the door (UL 4200A), regulatory marks and the model on the plate. Laser marking, not molded text, so that one tool serves all variants.

## Questions for the molder

- **Q-M1:** confirm ±0.05 mm on features under 10 mm (T-1, T-2, T-4).
- **Q-M2:** keyring slot core: drafted single pin or two pins.
- **Q-M3:** gate and weld line on the smoke shell, with a flow simulation.
- **Q-M4:** crush ribs on the 5 shell standoffs (T-3).
- **Q-M5:** 2-shot PC + TPU bonding grade (PC with TPU of a compatible grade). If 2-shot is not offered, quote a bonded TPU button as the fallback.
- **Q-M6:** steel or aluminum tool life for 10k parts, family tool for plate + door.
