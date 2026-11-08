# Assembly guide · Pocket Beacon rev evt0-a

Build size: 10 units. Time per unit: 12–18 min [estimate]. Work area: ESD mat, wrist strap, 20–25 °C, clean bench (no dust on gasket faces).

**WARNING** Do not bend, puncture or short the CR2032 lithium cell. Keep cells in their blister until step 7. Coin cells are dangerous if swallowed: keep loose cells away from children and count them at the end of the shift.

## Parts and tools

| Item | Qty per unit | Source |
|---|---|---|
| PCBA, main board (assembled by JLCPCB) | 1 | `assembly/main/` |
| Front shell (SLA print, finished) | 1 | `mech/shell.stl`, `mech/print-settings.md` |
| Button cap, TPU 80A or flexible resin 80A | 1 | `mech/button.stl` |
| Back plate | 1 | `mech/plate.stl` |
| Cell door | 1 | `mech/door.stl` |
| Acoustic membrane, die-cut Ø2.6 mm, PSA | 1 | `mech/mech-bom.csv` |
| Sounder port gasket, PU foam 0.8 mm, Ø3.0/Ø1.6 mm (D-702) | 1 | `mech/mech-bom.csv` |
| Plate adhesive ring, double-sided 0.10 mm, die-cut to the plate lip | 1 | `mech/mech-bom.csv` |
| Door gasket, silicone 40A, 0.35 mm, Ø21.9/Ø23.7 mm (D-701) | 1 | `mech/mech-bom.csv` |
| Thread-forming screw 1.4 × 3 mm, pan head, stainless | 2 | `mech/mech-bom.csv` |
| Panasonic CR2032 | 1 | `purchasing/digikey.csv` |

| Tool or consumable | Specification |
|---|---|
| Screwdriver | PH000 or T3 micro, with a torque driver set to 0.08 N·m [estimate: thread-forming screw in PC/ABS, confirm strip torque on 2 spare plates] |
| Debug probe | TI XDS110 (e.g. LP-XDS110ET) + Tag-Connect TC2030-CTX-NL cable |
| Instant adhesive | cyanoacrylate for TPU/PC with polyolefin primer (e.g. Loctite 406 + 770), only if the button cap is not a press fit |
| Press | flat block and 10 N weight, or a hand press with a 10 N spring |
| Isopropyl alcohol 99 % and lint-free wipes | gasket and adhesive faces |

## Steps

Each step ends with a QC check. Do not go to the next step if the check fails; mark the unit and set it aside.

### 1. Inspect and program the board

![Exploded view](../drawings/blueprint.png)

1. Inspect the PCBA under magnification: no bridges on U1 (QFN24) and U2, LED D1 polarity mark matches the silkscreen.
2. Power the board from a 3.0 V bench supply on the cell pads, current limit 20 mA.
3. Connect the TC2030 cable and flash the test firmware, then the production firmware.

- **Adhesive / cure:** none
- **Torque:** none
- **QC:** standby current ≤ 1.2 µA after flashing (test plan T-04); LED blinks on a button press; the phone app sees the advertising name.

### 2. Fit the button cap and the acoustic membrane to the shell

1. Press the button cap into the shell's button opening from the inside until the flange is flush.
2. Clean the sound-port seat with IPA and let it dry 1 min.
3. Place the acoustic membrane centred on the Ø2.6 mm seat, PSA side down, and press 5 s with a flat tool.

- **Adhesive / cure:** if the cap is loose, one drop of primer and cyanoacrylate on the flange; 1 min handling, 24 h full cure at 23 °C.
- **Torque:** none
- **QC:** the membrane covers the Ø1.0 mm hole fully with no wrinkle; the cap returns freely when pressed.

### 3. Place the sounder port gasket

1. Peel the foam ring and stick it on the shell ceiling, concentric with the sound port hole.

- **Adhesive / cure:** PSA on the gasket
- **Torque:** none
- **QC:** ring centred on the hole within 0.3 mm (V-010 reference); foam not stretched.

### 4. Insert the PCBA

1. Lower the board into the shell, component side (front) first, onto the locating posts.
2. Check that the SW1 actuator sits under the button nub and LS1 under the foam ring.

- **Adhesive / cure:** none
- **Torque:** none
- **QC:** the board sits flat on the posts; pressing the cap gives a click (2.3–3.3 N, V-015).

### 5. Bond the back plate

1. Clean the shell rim and the plate lip with IPA, dry 1 min.
2. Apply the adhesive ring to the plate lip, remove the liner, align the plate (keyring slot to keyring slot) and close.
3. Press with 10 N for 30 s.

- **Adhesive / cure:** 0.10 mm double-sided tape ring; 72 h at 23 °C for full bond strength before the seal test.
- **Torque:** none
- **QC:** no gap visible at the seam; the keyring slot is continuous; no adhesive squeeze-out on cosmetic faces.

### 6. Fit the door gasket

1. Lay the silicone ring in the door recess of the plate without stretching it.

- **Adhesive / cure:** none
- **Torque:** none
- **QC:** the ring lies flat and fully inside the recess.

### 7. Insert the cell

1. Insert the CR2032 into the 3034 holder through the door bore, positive face outward, as marked on the door.

- **Adhesive / cure:** none
- **Torque:** none
- **QC:** the unit advertises within 5 s; VBAT at the test pad ≥ 2.9 V.

### 8. Close the door

1. Place the door, align the two ears with the bosses, and drive both screws alternately.

- **Adhesive / cure:** none
- **Torque:** 0.08 N·m per screw, alternating, two passes
- **QC:** the door is flush with the plate within 0.1 mm; it cannot be opened by hand (UL 4200A securement, V-014).

### 9. Ship mode and pack

1. Send the ship-mode command from the test app.
2. Pack with the leaflet carrying the coin-cell warnings (compliance.md, D-704).

- **Adhesive / cure:** none
- **Torque:** none
- **QC:** current in ship mode ≤ 1.0 µA (M5); the unit wakes on a button press.

## Final inspection

| Check | Pass criterion |
|---|---|
| Visual | no scratches on the front face, seam closed, door flush within 0.1 mm |
| Function | button press → LED blink and app event; ring from the app ≥ 75 dB(A) at 25 cm on a fresh cell (V-004) |
| Radio | RSSI at 1 m within ±6 dB of the reference unit |
| Current | ship mode ≤ 1.0 µA |
