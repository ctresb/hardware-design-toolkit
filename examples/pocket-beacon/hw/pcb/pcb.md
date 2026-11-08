# PCB: Pocket Beacon main board

Issue: EVT-0 A · Date: 2026-11-08 · Owner: pcb-engineer · Spec: `hw/pcb/board.json` · Gate: `hw/pcb/release-check.json`

**Status: READY TO ORDER** (`release_check.py` exit 0, F-520). The last 4 connections were closed on 2026-11-08: the LED net on F.Cu after removing duplicate copper (D-520), and the GND islands with stitching vias (D-522).

| Item | Value |
|---|---|
| Board | 28.4 × 28.4 mm, R4.5 corners, keyring chamfer x + y ≤ 20.75 mm (D-512) |
| Stack-up | 4-layer FR4, 0.6 mm, ENIG, black mask (D-510): F signals + GND pour, In1 GND plane, In2 signals + VBAT pour, B GND pour + cell contact |
| Parts | 47 (holder, 6 test pads and the antenna corner on the rules below); JLC BOM/CPL with LCSC numbers |
| Routing | Freerouting 1.9.0 on the cloud VM (xvfb), 3 passes; then `stitch.py` (GND vias for pads and pour islands) and `lroute.py` (grid router for the last nets). 2.5.0 stopped at ≈ 19 passes (TB-8) |
| Rules | 0.1/0.1 mm track/space, 0.4/0.2 mm vias; under the cell only GND vias (D-517); antenna copper keep-out x ≤ −6.0, y ≤ −10.9 on all layers (D-515) |
| DRC | 0 violations (pth_inside_courtyard ignored for U1's GND thermal vias inside the holder courtyard, D-517), 0 parity issues, 0 unconnected |
| Copper | 388 tracks, 150 vias |
| ERC | 0 errors, 0 warnings |
| Panel | 3 × 3 by the fab, 5 mm rails, mouse bites, fiducials on the rails |

## How the board was closed

1. `island_vias.py`: one GND via in every F.Cu/B.Cu pour island without a via or PTH pad, never inside a component courtyard (D-522).
2. Removed the duplicate F.Cu connections that walled the LED escape (D-520).
3. `mlroute.py LED U1 12 R1 1 --layers F.Cu --clear 0.15 --no-under U1`: 10.6 mm, 0 vias.
4. `export.py --what erc,drc,3d,fab,pads`, `release_check.py`, then `hw/mech/build_assembly.py` (0 interpenetrations, 73 pairs).

The board preview PNGs in `export/` predate this routing (Q-PCB-02).
