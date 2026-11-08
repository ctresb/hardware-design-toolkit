# Mechanical constraints: Pocket Beacon

Issue: 1 · Date: 2026-11-08 · Owner of the inputs: specs-engineer (architecture.md issue 2, requirements.md issue 2) · Reader: enclosure-engineer, pcb-engineer

This file hands the electronics to the enclosure and board stages. Every height is a datasheet **maximum**. The CAD is the source of truth for geometry once it exists.

## 1. Envelope

| Item | Value | Source |
|---|---|---|
| Outer plan | ≤ 32.0 × 32.0 mm, rounded square, keyring slot through one corner | REQ-001, D-004 |
| Outer height | ≤ 10.0 mm limit (8.5 mm target is v2) | REQ-001, D-007 |
| Mass with cell | ≤ 10 g (cell 3 g) | REQ-016 |
| Board outline | ≤ 28.5 × 28.5 mm rounded square, minus the keyring-slot corner. Final outline comes from the shell CAD (inner wall − 0.3 mm). | estimate: 32 mm − 2 × 1.2 mm wall − 2 × 0.3 mm clearance |

## 2. Stack-up, front (button face) to back (lid), at the thickest point

| # | Layer | Max thickness | Source |
|---|---|---|---|
| 1 | Front shell wall over the sounder | 1.0 mm | assumption, to set by DFM (PC: 0.8–1.5 mm) |
| 2 | Clearance part → wall | 0.15 mm | assumption |
| 3 | Tallest front-side part: LS1 CPT-9019A-SMT-TR | 2.1 mm (9.5 × 9.5 mm) | F-103 |
| 4 | PCB 4-layer 0.8 mm + 10 % | 0.88 mm | D-015 |
| 5 | Keystone 3034TR retainer with CR2032 inside (back side) | 4.1 mm (21.2 × 23.1 mm) | F-202 |
| 6 | Clearance retainer → lid | 0.2 mm | assumption |
| 7 | Lid at the center | 1.2 mm | assumption |
| | **Total** | **9.63 mm** | sum of maxima, 0.37 mm margin to 10.0 mm |

The domed faces may be thinner at the edges. The center height above must hold under the LS1 and the retainer.

## 3. Tall parts and their positions (front side unless noted)

| Ref | Part | Max L × W × H (mm) | Placement rule |
|---|---|---|---|
| LS1 | CPT-9019A-SMT-TR piezo, **top port** | 9.5 × 9.5 × 2.1 | Its port must face the front shell sound opening (§4) |
| SW1 | KMR221GLFS tactile switch | 4.7 × 2.9 × 2.0 | Under the button membrane, center of the front face |
| L1 | MLZ2012M100WT000 inductor | 2.2 × 1.45 × 1.45 | Next to U1 pin 17 (DCDC) |
| ANT1 | 2450AT18A0100001E chip antenna | 3.4 × 1.8 × 1.4 | Board corner (§5) |
| U1 | CC2340R52E0RGER | 4.1 × 4.1 × 1.0 | Near ANT1, short RF line |
| BT1 | Keystone 3034TR, **back side** | 23.1 × 21.2 × 4.1 | Offset toward the edge opposite the antenna, so that the antenna clearance strip is free of cell metal |
| BAT1 | CR2032 | Ø 20.0 × 3.2 | Inside BT1; it is round, and the lid opening is round |
| D1 | LTST-C191KFKT LED | 1.7 × 0.9 × 0.65 | Under the translucent membrane, next to SW1 |

## 4. Openings on the outer shell (minimize: IP67, REQ-012)

| Opening | Position | Requirement | Note |
|---|---|---|---|
| Sound port | front face, over the LS1 port | ePTFE acoustic membrane (IP67 grade), adhesive-sealed to the shell inside. Port area and membrane loss to set for ≥ 75 dB(A) at 25 cm (REQ-006) | Q-PB-204. Membrane vendors sell direct (RFQ) |
| Button | front face center | TPU membrane, two-shot molded or laser-welded to the shell. Total press force 2.3–3.3 N (switch 2.0 ± 0.5 N + membrane 0.3–0.8 N, REQ-009). Translucent window over D1 | D-027 |
| LED window | in the button membrane | translucent over D1. The smoke variant needs a light test | REQ-008 |
| Keyring slot | one corner, diagonal from the antenna | through-slot in the shell only, never into the sealed volume; survives 50 N pull | REQ-017 |
| Lid | back face | coin-operated bayonet, ≥ 90° rotation, detent torque. Face-seal O-ring. Safety-alert and ingestion icons molded on the lid | REQ-015, D-026, F-501 |

## 5. Antenna corner

- ANT1 sits at the board corner diagonally opposite the keyring slot, so the keys stay as far from it as the size allows.
- The ground clearance under and around ANT1 is copper-free on all four layers. The Johanson drawing shows 6.5 mm × 4.0 mm on a 39.5 mm board [estimate: pcb-engineer reads the exact rectangle from the Johanson drawing or CAD, F-106].
- No metal within that clearance on either side of the board. That covers the CR2032 and its retainer, the O-ring spring and the magnets (none in this product). The retainer edge stays at least 1 mm outside the clearance in plan view [assumption: tune on EVT].
- The shell wall over the antenna has no metal insert, no metallized paint and no conductive label.

## 6. Child-resistant compartment (UL 4200A-2023 via 16 CFR 1263, F-501)

The lid design must keep the cell inaccessible through all of these:

- **Securement.** The lid opens only with a coin or a flat screwdriver in a slot and turns ≥ 90°. Read the minimum torque and spin angle for option 1 in UL 4200A §5.5 before the CAD freeze.
- **Preconditioning:**
  - 7 h at ≥ 70 °C;
  - 10 open/close cycles with the cell removed and reinserted.
- **Abuse tests:**
  - 10 drops from 1 m on hardwood;
  - 3 impacts of 2 J;
  - 330 N crush for 10 s;
  - ≥ 136 N compression;
  - ≥ 0.50 N·m torque;
  - ≥ 72 N tension;
  - test probe 11 at 50–60 N.
- **IP67.** The lid stays sealed after the same 10 open/close cycles.

## 7. For pcb-engineer

- Front side: U1, U2, LS1, SW1, D1, ANT1 and the RF chain, Y1, Y2, L1, the decoupling, and the TC2030-NL pads.
- Back side: BT1, test pads TP1–TP8 outside the BT1 footprint, Q1 and D2 next to the BT1 contacts.
- Place C1, C2 and C15 within 5 mm of U1 VDDS (D-022).
- Leave a 5-slot RF chain on a 50 Ω grounded coplanar line, with a via fence (architecture.md §5.3).
- Keep-outs to import from the enclosure CAD:
  - the keyring-slot corner;
  - the lid bayonet ring and the O-ring land;
  - the LS1 port alignment;
  - the button axis.
