# Decision log

One entry per decision. Never edit a past entry; supersede it with a new one.

## D-001 · 2026-11-08 · Project, depth and who decides

- **Decision:** Pocket Beacon is the toolkit's proof-of-concept product, run at depth `full`. The interview answers come from the toolkit acting as product owner.
- **Options considered:** full (chosen), concept, review
- **Reason:** the PoC must end READY TO BUILD (prototype), so every stage runs.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** all stages
- **Supersedes:** —

## D-002 · 2026-11-08 · Power source: user-replaceable CR2032

- **Decision:** one standard CR2032 lithium coin cell, replaced by the user. No charging circuit.
- **Options considered:** CR2032 (chosen); CR2450 (larger, does not fit 32 mm with walls); rechargeable LiPo pouch with contacts and a dock.
- **Reason:** a finder spends almost all its life advertising at a few µA, which a coin cell serves for more than a year. A user-replaceable standard cell also removes the charger, the dock and lithium-ion shipping limits. It meets the removable-battery expectation of the EU Battery Regulation by design.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** brief §5, battery-and-power, enclosure-engineer, compliance-planner
- **Supersedes:** —

## D-003 · 2026-11-08 · Standard BLE only in v1

- **Decision:** the beacon talks only to its own app over standard BLE GATT. Joining a phone-maker finder network (Apple Find My, Google Find Hub) is a later option.
- **Options considered:** standard BLE (chosen); join a network at launch.
- **Reason:** each network program needs a contract or membership, its own firmware stack, and its own certification and test steps. Some also add unwanted-tracking rules (the DULT draft and the platform specifications). The v1 hardware keeps the room these programs typically need: loudness target S-04, a button, and a spare GPIO. Network membership can then be added in firmware and certification later. **[assumption]** The hardware requirements of each program must be checked by `compliance-planner` before v2.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** compliance-planner, specs (S-04 loudness kept at finder-network level)
- **Supersedes:** —

## D-004 · 2026-11-08 · Form: rounded-square pebble, original

- **Decision:** rounded-square pebble, domed front and back, keyring slot through one corner. It is not modeled on any existing product.
- **Options considered:** round puck; rounded-square pebble (chosen); tag with a strap loop.
- **Reason:** the square plan gives a corner for the keyring slot away from the cell, and it reads as distinct from the round finders on the market.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** enclosure-engineer, product-render
- **Supersedes:** —

## D-005 · 2026-11-08 · Status light: one amber LED under the button membrane

- **Decision:** one amber 0603 LED (≈ 605 nm, ≈ 2.0 V forward voltage) shines through the translucent elastomer button membrane.
- **Options considered:** white LED (rejected); RGB LED; amber LED (chosen); no LED.
- **Reason:** a white or blue LED needs about 2.7–3.2 V, and a CR2032 sags below that under load and near end of life. The status light would then fail before the radio does. An amber LED works down to the 2.0 V end-of-life voltage. Sharing the membrane with the button means one sealed opening instead of two.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom D1, enclosure (membrane must be translucent)
- **Supersedes:** —

## D-006 · 2026-11-08 · Three color variants from one mold

- **Decision:** graphite (opaque), chalk white (opaque) and smoke (translucent dark grey) from the same shell and lid tools, with three resins.
- **Options considered:** one color; three colors from one mold (chosen); separate tools per color.
- **Reason:** one tool set; color is a resin choice. The smoke variant needs an optical-grade resin and a polished cavity, and it shows the internals. The board must look clean (black solder mask, tidy silkscreen).
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** enclosure-engineer (gate location away from visible faces on the smoke variant), pcb-engineer (black mask), product-render
- **Supersedes:** —

## D-007 · 2026-11-08 · Envelope limit 10.0 mm in v1

- **Decision:** v1 uses an off-the-shelf SMD CR2032 holder and accepts an envelope of up to 32 × 32 × 10.0 mm. The 8.5 mm thickness stays as a target for v2 with a cell retained by the lid and custom contacts.
- **Options considered:** standard holder at ≤ 10.0 mm (chosen); custom lid contacts at about 8.5 mm (new stamped part, more tooling and tolerance risk); CR2025 cell (saves 0.7 mm, loses about 27 % capacity).
- **Reason:** the stack-up in `hw/architecture.md` §6 sums to 9.5–9.9 mm with the standard holder. A standard holder is a catalog part, retains the cell in a drop, and keeps the prototype tooling-free. Battery life (priority 1) outranks size (priority 2).
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** REQ-001, enclosure-engineer
- **Supersedes:** —

## D-008 · 2026-11-08 · No accelerometer in v1

- **Decision:** no motion sensor.
- **Options considered:** accelerometer for "moved" alerts; none (chosen).
- **Reason:** no requirement needs it. It adds about 1–3 µA, area, firmware and a part. Revisit if the app adds motion features.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom
- **Supersedes:** —

## D-009 · 2026-11-08 · NRE planning budget

- **Decision:** plan with USD 40,000 NRE (tooling, certification, prototypes). **[assumption]**
- **Options considered:** —
- **Reason:** a planning figure for `cost-and-sourcing` to test against; replaced by quotes.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** cost-and-sourcing
- **Supersedes:** —

## D-010 · 2026-11-08 · Sound: piezo sounder + charge-pump driver, adaptive drive

- **Decision:** Murata PKMCS0909E4000-R1 piezo sounder (9.0 × 9.0 × 1.9 mm max, externally driven, 4 kHz), driven differentially by a Diodes PAM8904EGPR charge-pump driver. Firmware selects 2× mode by default and 3× mode only when the cell voltage under load allows.
- **Options considered:** magnetic buzzer (rejected: coil drive of tens of mA, which a coin cell cannot hold for 12 s); micro-speaker with an amplifier (rejected: area, current); piezo driven directly from GPIO (rejected: ±1.5 Vo-p gives only the 65 dB(A) rated level at 10 cm); piezo + charge pump (chosen).
- **Reason:**
  - The sounder is rated 65 dB(A) min at ±1.5 Vo-p, 4 kHz, 10 cm, with ±12.5 Vo-p max. **[verified: Murata PKMCS0909E4000-R1 datasheet VPPT-BUZJ083-D, via LCSC C910763, 2026-11-08]**
  - The PAM8904E gives VOUT 5.2 V (2× mode) and 7.2 V (3× mode) from VIN = 3.0 V. Differential current is 6.4 mA (2×) and 14.2 mA (3×) at 47 nF, 3.2 kHz. **[verified: Diodes DS41667 Rev. 4-2, Electrical Characteristics, 2026-11-08]**
  - Expected level: +10.8 dB (2×) to +13.6 dB (3×) over the rated drive, so 75.8–78.6 dB(A) at 10 cm. At 25 cm, assuming free-field −8 dB, that is about 68–71 dB(A) before the port and membrane loss. **[estimate: 20·log(V/1.5 V), inverse-square law, no enclosure gain or loss]**
  - The level is measured on the prototype. The loudness target S-04 may need the enclosure's resonant cavity tuned to 4 kHz.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom LS1 U2, enclosure (sound port + acoustic membrane + cavity), battery-and-power (ring current)
- **Supersedes:** —

## D-011 · 2026-11-08 · BLE defaults

- **Decision:** BLE 5.x, 1M PHY, 0 dBm default TX power (up to +4 dBm only if range tests need it), adaptive advertising at 1.0 s to 2.0 s, over-the-air firmware update from the app.
- **Options considered:** —
- **Reason:** at 0 dBm the SoC's TX current is 5.1 mA, against 7.9 mA at +4 dBm and 10.7 mA at +8 dBm (TI SWRS272F §7.10). Peak current is what limits a coin cell.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** firmware, battery-and-power
- **Supersedes:** —

## D-012 · 2026-11-08 · Architecture: single chip-down BLE SoC, TI CC2340R52E0RGER

- **Decision:** architecture A, a single chip-down BLE SoC: TI CC2340R52E0RGER (VQFN-24, 4 × 4 mm). It is powered directly from the cell through its integrated DC/DC.
- **Options considered:**
  - A: CC2340R5 chip-down (chosen).
  - B: Nordic nRF52805/nRF52810/nRF52832 chip-down.
  - C: a pre-certified BLE module (smaller certification cost, larger and taller).
- **Reason:**
  - Supply 1.71–3.8 V, so it runs from a CR2032 down to its end-of-life voltage with no regulator. **[verified: TI SWRS272F]**
  - Low peak currents: TX 5.1 mA at 0 dBm, RX 5.3 mA, standby 0.71 µA with RTC and full RAM retention. **[verified: TI SWRS272F §7.10 and the power table]**
  - Internal 32 kHz RC oscillator, with an optional 32.768 kHz crystal. **[verified: TI SWRS272F §7.20.3]**
  - In the reel production listing as Active / Production. **[verified: TI SWRS272F package option addendum]**
  - In stock at LCSC (C20416850), about USD 0.80–1.33 at 1k across listings. **[verified: LCSC search, 2026-11-08]**
  - Of the three options, A gives the lowest BOM cost and is assembled at JLCPCB.
  - B is a valid fallback with a stronger ecosystem, but its QFN parts are larger (6 × 6 mm QFN48) and cost more.
  - C would remove most of the radio certification cost but adds about 2 mm of height. It is noted for `compliance-planner` to weigh against the chip-down certification cost.
- **Decided by:** toolkit PoC (product owner role) on the specs-engineer recommendation
- **Affects:** bom U1, pcb-engineer (RF layout, antenna), compliance-planner (chip-down: full radio certification)
- **Supersedes:** —

## D-013 · 2026-11-08 · Cell holder: TE (Linx) BAT-HLD-001-TR

- **Decision:** SMD CR2032 holder TE Connectivity BAT-HLD-001-TR on the board's back side, the board's ENIG pad under the cell serving as the negative contact per the holder drawing. **[assumption]** Holder footprint and height must be verified by electronics-researcher.
- **Options considered:** TE BAT-HLD-001-TR (chosen); Keystone 3034; MPD BU2032SM series; Keystone 1058 (rejected: 31.9 mm long, too big for a 32 mm device).
- **Reason:** high stock at authorized sources. Octopart showed TE Store with 93,362 pcs of the -TR version at about USD 0.48 at 1k. **[verified: Octopart search snapshot, 2026-11-08]**
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom BT1, enclosure stack-up
- **Supersedes:** —

## D-014 · 2026-11-08 · Reverse-polarity protection with a P-MOSFET

- **Decision:** a P-channel MOSFET in the cell's positive path, gate to ground (ideal-diode style), instead of a Schottky diode.
- **Options considered:** none (a reversed cell can damage the SoC); Schottky diode (rejected: 0.2–0.3 V drop wastes 10 % of the cell's useful voltage range); P-MOSFET (chosen).
- **Reason:** near-zero drop and no quiescent current. The FET must have a low gate threshold (|VGS(th)| ≤ 1.0 V), so that it stays fully on at the 2.0 V end-of-life voltage.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom Q1
- **Supersedes:** —

## D-015 · 2026-11-08 · Board: 4-layer FR4, 0.8 mm, ENIG, black mask

- **Decision:** one rigid 4-layer board, 0.8 mm, ENIG, black solder mask, components on both sides (holder on the back).
- **Options considered:** 2-layer 0.8 mm (rejected: the 50 Ω RF line on 0.8 mm 2-layer is about 1.5 mm wide, and the ground return is poor); 4-layer 0.8 mm (chosen).
- **Reason:** solid ground under the RF line and the QFN. ENIG gives a flat finish for the 0.5 mm-pitch QFN and a reliable cell contact. Black mask is for the smoke variant (D-006).
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** pcb-engineer
- **Supersedes:** —

## D-016 · 2026-11-08 · Antenna: chip antenna at a board corner

- **Decision:** Johanson 2450AT18A0100001E chip antenna at the board corner opposite the keyring slot and away from the cell, with a pi matching network.
- **Options considered:** PCB inverted-F antenna (rejected: needs about 15 × 5 mm of clear edge, which a 28 mm board cannot spare next to a 20 mm cell); chip antenna (chosen).
- **Reason:** small, and was confirmed Active with stock in earlier research (renumbered from 2450AT18A100E). **[assumption]** It must be re-verified, and the keep-out must follow the Johanson layout note.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** pcb-engineer, enclosure (no metal near the antenna corner)
- **Supersedes:** —

## D-017 · 2026-11-08 · Fit a 32.768 kHz crystal

- **Decision:** fit a 32.768 kHz crystal (Abracon ABS06 family, 2.0 × 1.2 mm) for the sleep clock.
- **Options considered:** internal LFOSC only; external crystal (chosen).
- **Reason:** a BLE device that sleeps between advertising events needs an accurate sleep clock. The calibrated RC oscillator needs periodic recalibration and wider receive windows, which cost average current. On a 12-month coin-cell budget the crystal (about USD 0.15) pays for itself. **[estimate: to be measured in the battery-and-power stage]**
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom Y2, battery-and-power
- **Supersedes:** —

## D-018 · 2026-11-08 · Cell holder: Keystone 3034TR

- **Decision:** BT1 is Keystone 3034TR (LCSC C5213768), 21.2 × 23.1 × 4.1 mm max.
- **Options considered:** Keystone 3034TR (chosen); TE BAT-HLD-001-TR; MPD BU2032SM-JJ-GTR; a lid-retained cell with molded spring contacts.
- **Reason:**
  - BAT-HLD-001-TR is 4.4 mm max and only 12 pcs on reel at JLC (F-201). 3034TR is 0.3 mm lower, cheaper (USD 0.27 vs 0.475 at 1k) and stocked at DigiKey (121k) and JLC (644) (F-202).
  - BU2032SM-JJ is 5.33 mm.
  - Spring contacts would save about 0.9 mm but need custom contacts and lid preload. Kept as the v2 path (L-003).
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom.csv, pcb-engineer (footprint), enclosure-engineer (stack-up)
- **Supersedes:** D-013

## D-019 · 2026-11-08 · 48 MHz crystal ABM11W 7 pF with external load capacitors

- **Decision:**
  - Y1 is ABM11W-48.0000MHZ-7-B1U-T3 (LCSC C1985532).
  - C16 and C17 are 9 pF C0G load capacitors, 0402CG9R0C500NT (C1580), fitted. Start value 2 × (7 pF − 2.5 pF stray); final value set on EVT from the measured offset (V-006).
- **Options considered:** ABM11W 8 pF D1X (not orderable); Tai-Saw TZ3908AAAO43 (TI-validated, 3,000 MOQ, no LCSC listing); ABM11W 7 pF B1U (chosen).
- **Reason:**
  - The 8 pF D1X has 0 stock at DigiKey and 4 at LCSC (F-104).
  - B1U is drop-in, ESR 40 Ω inside the CC2340 limit of 60 Ω. Its −20…70 °C range covers REQ-014 (−10…45 °C use).
  - TI requires external HFXT load capacitors for systems that target regulatory compliance (F-101).
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom.csv, pcb-engineer, prototype check V-006
- **Supersedes:** —

## D-020 · 2026-11-08 · Antenna match: 5-slot network, LQG15HS inductor

- **Decision:** the RF path is RF_P → C11 (shunt) → L2 (series) → C12 (shunt) → R2 (series, 0 Ω) → C18 (shunt, footprint only, DNP) → ANT1.
  - Fitted as a pi match: C11 1.0 pF, L2 2.2 nH LQG15HS2N2B02D (C162540), C12 1.0 pF, R2 0 Ω (C17168).
  - To use the tee that Johanson recommends: fit R2 as the second series element and C18, and remove C11.
- **Options considered:** fixed pi (3 slots); fixed tee; 5-slot pi/tee (chosen).
- **Reason:**
  - LQP15MN2N2B02D is obsolete (F-107).
  - The final topology and values come from VNA tuning on the EVT board (V-005). A 5-slot layout serves both without a board respin.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom.csv, architecture.md §2, pcb-engineer
- **Supersedes:** —

## D-021 · 2026-11-08 · Sounder: Same Sky CPT-9019A-SMT-TR, top port

- **Decision:** LS1 is CPT-9019A-SMT-TR: 9.5 × 9.5 × 2.1 mm max, 8.4–15.6 nF, 72 dB min at 3 Vpp, top port (F-103).
- **Options considered:** Murata PKMCS0909E4000-R1 (Last Time Buy 2027-03-31, 0 at DigiKey, F-102); Murata PKLCS1212E4001 (12 × 12 × 3 mm, too large); CPT-9019A (chosen).
- **Reason:** it is active with 47k pcs at DigiKey, and its capacitance is below the 47 nF limit of U2. Its top port faces the front shell. The sound path is front-facing through an ePTFE membrane (constraints.md §4).
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom.csv, enclosure-engineer (acoustic port), power budget (ring current unchanged: set by U2)
- **Supersedes:** the LS1 part choice inside D-010

## D-022 · 2026-11-08 · Bulk capacitance: three 22 µF on VBAT, slew rule governs

- **Decision:** C1, C2 and C15 are 22 µF 0603 X5R (CL10A226MQ8NRNC, C59461), placed within 5 mm of U1 VDDS.
- **Options considered:** 2 × 22 µF (stage 2); 3 × 22 µF 0603 (chosen); 2 × 22 µF 0805 (1.40 mm, +USD 0.22).
- **Reason:**
  - **Two methods give two minimums.**
    - The SWRA349 pulse-buffer method (battery-and-power, F-402) gives 6.7 µF: it sizes for a TX burst seen through a 1 kΩ end-of-life cell.
    - The CC2340 VDDS falling slew limit of ≤ 1 mV/µs (F-303) gives 14.2 µF at the start of a 14.2 mA ring (passives research, F-302).
  - **The stricter one wins.** The slew rule is a datasheet limit of the SoC, while the pulse method is an energy estimate. Violating the slew limit risks a brown-out reset, not just a shorter life.
  - **Margin with three capacitors:**
    - 2 × 22 µF give 28.0 µF effective at 3.0 V and 19.7 µF worst case: margin 1.39×.
    - A third 22 µF adds about 10.7 µF effective at 3.0 V. That gives about 38.7 µF typical and about 27 µF worst case: margin ≥ 1.9× [estimate: F-301 DC-bias curve].
  - The cost is USD 0.011, and the height stays 1.0 mm.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom.csv, pcb-engineer (placement), power budget leakage line
- **Supersedes:** —

## D-023 · 2026-11-08 · Charge-pump flying capacitors 25 V

- **Decision:** C9 and C10 are CL05A105KA5NQNC (1 µF 25 V X5R 0402, C52923, JLC basic).
- **Options considered:** CL05A105KO5NNNC (16 V, extended C29266); CL05A105KA5NQNC (chosen).
- **Reason:** the stage-2 row named one part and the LCSC number of another. The 25 V part keeps about twice the capacitance at 6.6 V, and it is a basic part with no feeder fee.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom.csv
- **Supersedes:** —

## D-024 · 2026-11-08 · LED resistor 330 Ω

- **Decision:** R1 is 330 Ω 1 % 0402, 0402WGF3300TCE (C25104, basic).
- **Options considered:** 680 Ω (stage 2); 330 Ω (chosen); 220 Ω; a high-drive GPIO.
- **Reason:**
  - At 680 Ω the LED gives about 3–6 mcd on a fresh cell and about 1 mcd at 2.0 V (F-207).
  - At 330 Ω it gives about 3.5 mA at 3.0 V and about 0.8 mA at 2.0 V [estimate: Vf 1.75–1.85 V], so the light stays visible through the membrane at end of life.
  - The LED is off during 3× rings (D-028), so the peak does not add to the ring current.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom.csv, power budget (D1 line)
- **Supersedes:** —

## D-025 · 2026-11-08 · Keep the 32.768 kHz crystal in v1

- **Decision:**
  - Y2 ABS06-32.768KHZ-9-T stays fitted.
  - C13 and C14 are 0402CG120J500NT, 12 pF C0G (C1547, basic).
  - Using the internal LFOSC instead is a v2 cost-down experiment, run after EVT.
- **Options considered:** keep Y2 (chosen); remove Y2, C13 and C14 and use LFOSC.
- **Reason:**
  - **Sleep clock accuracy.** A crystal sleep clock (±20 ppm) keeps the BLE receive window small. An RC oscillator needs a wider window, so each connection event listens longer. The standby saving with LFOSC is only 0.03 µA (F-101).
  - **Unchecked support.** LFOSC support in the TI BLE stack was not verified in this session.
  - **Cost.** Removing Y2 saves about USD 0.42 at 1k, which the cost model can absorb.
  - **ESR margin.** Only 10 % margin (90 kΩ vs 100 kΩ, F-105). It is covered by a cold start-up check (V-007).
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom.csv, prototype checks
- **Supersedes:** —

## D-026 · 2026-11-08 · Child-resistant cell compartment: coin-operated bayonet lid

- **Decision:** the back lid is a bayonet that opens only with a coin or a flat screwdriver in a slot. It turns ≥ 90° and engages with a detent torque. This is UL 4200A-2023 §5.5 option 1 ("coin, screwdriver, or other tool"), made mandatory in the US by 16 CFR 1263.3 (F-501).
  - The lid face-seals on an O-ring for IP67.
  - It must keep the cell inaccessible after the abuse tests listed in REQ-015.
  - Warnings:
    - on the product, as practicable: the safety-alert symbol and the "keep away from children" icon molded in the lid;
    - on the packaging and in the instructions, per 16 CFR 1263.4.
- **Options considered:** tool-operated bayonet (chosen); press-and-twist with two simultaneous independent actions (option 2); screw-fastened lid with a captive screw.
- **Reason:**
  - The tool lock has no spring latch to mold and tune.
  - A coin is always at hand for a keyring product.
  - Option 2 needs the first action held while the lid turns; that latch adds a part and a failure mode (F-501).
  - A captive screw adds a metal insert and cost.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** requirements.md REQ-015, enclosure-engineer, compliance-planner (EU/UK/BR equivalents: EN IEC 62368-1 coin-cell clause, GPSR), product packaging
- **Supersedes:** —

## D-027 · 2026-11-08 · Button: sealed membrane over KMR221G, force budget

- **Decision:**
  - SW1 stays KMR221GLFS: 2.0 N ± 0.5 N, 200k cycles, IP40 (F-208).
  - The IP67 seal comes from a TPU membrane that is two-shot molded with, or laser-welded to, the front shell. The membrane is translucent over D1.
  - The total press force target is 2.3–3.3 N: the switch plus a membrane designed for 0.3–0.8 N.
  - REQ-009 is revised to 2.0–3.5 N. A keyring product sits in pockets and must not ring the phone on light pressure.
- **Options considered:** 2 N switch (chosen); 1.2 N switch with a stiffer membrane; capacitive touch.
- **Reason:** the user feels the switch force plus the membrane force. A force below 2 N invites pocket presses. Capacitive touch through a wet IP67 shell needs firmware filtering that is out of scope for v1.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** requirements.md REQ-009, enclosure-engineer
- **Supersedes:** —

## D-028 · 2026-11-08 · Adaptive ring rule and the 15 mA peak

- **Decision:** the firmware rule (architecture.md §4):
  - every ring starts in 2× mode;
  - after 100 ms it measures VBAT under load;
  - it steps up to 3× if VBAT ≥ 2.7 V;
  - it drops to 1× and reports a low battery if VBAT < 2.3 V;
  - the LED is off and TX stays ≤ 0 dBm during a 3× ring.

  The 15.05 mA 3× peak at the cell is accepted within the REQ-005 limit of 20 mA.
- **Options considered:** fixed 3× (fails on a cold, aged cell, E-402); fixed 2× (quieter than REQ-006 on a fresh cell); adaptive (chosen).
- **Reason:** at −10 °C on a cell 80 % used, 3× pulls VBAT to about 1.0 V (E-402). The adaptive rule keeps the loud mode for healthy cells only.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** architecture.md §4, firmware, REQ-005, REQ-006
- **Supersedes:** —

## D-029 · 2026-11-08 · Sourcing rules for the prototype build

- **Decision:**
  - Order the assembler parts by **LCSC number**, with the brand checked:
    - Q1 C150470 (Diodes DMG2305UX-7, not the HXY C5261054 listed under the same MPN);
    - D2 C48260 (Texas Instruments, not the TECH PUBLIC listing).
  - Consign from DigiKey any part whose JLC stock is below the build quantity plus attrition. On 2026-11-08 this is LS1 (13 at LCSC) and ANT1 (105) for builds above 10 units.
  - BAT1 is ordered as Panasonic `CR2032` (DigiKey 11-CR2032-ND), not `CR-2032/BN` (F-210). It is inserted at final assembly, never reflowed.
- **Options considered:** —
- **Reason:** look-alike listings at LCSC carry the genuine MPN under another brand (F-209, L-005). JLC stock is a snapshot, so consigning covers the gap.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** bom.csv, build-package, cost-and-sourcing
- **Supersedes:** —

## D-030 · 2026-11-08 · RF path follows the TI reference filter

- **Decision:**
  - C11, L2 and C12 are the TI harmonic low-pass filter, with start values 1.5 pF (GJM1555C1H1R5BB01D, C76900), 2.7 nH ±0.1 nH (LQG15HS2N7B02D, C162541) and 1.5 pF.
  - R2 (0 Ω) and C18 (DNP), with C12, form the antenna match.
- **Options considered:** the stage-2 pi match (1.0 pF – 2.2 nH – 1.0 pF) used as the only network; the TI filter followed by a separate match (chosen).
- **Reason:**
  - The TI board puts a dedicated harmonic filter at the ANT pin before any antenna match (F-502).
  - The filter suppresses the 2nd and 3rd harmonics that FCC Part 15.247 and EN 300 328 limit.
  - Merging it into an antenna-tuned pi would let VNA tuning move the filter corner.
  - 2.7 nH is the closest 0402 value to TI's 0201 2.8 nH. Values are re-tuned on the EVT board (V-005).
- **Decided by:** toolkit PoC (product owner role), from paper-review finding PR-04
- **Affects:** bom.csv, architecture.md §5.3, pcb-engineer, compliance (harmonics pre-scan)
- **Supersedes:** the values in D-020 (the 5-slot topology stays)

## D-031 · 2026-11-08 · Decoupling and reset per the TI reference

- **Decision:** add C19 1 µF on VDDD (CL05A105KA5NQNC); one 100 nF on each VDDS pin (C5, C6, C21) and each VDDR pin (C22, C23); a RSTN pull-up R3 100 kΩ (0402WGF1003TCE, C25741) with C20 100 nF.
- **Options considered:** stage-2 decoupling (2 × 100 nF, no VDDD capacitor, no reset network); TI reference (chosen).
- **Reason:** VDDD is the decoupling pin of the internal 1.28 V regulator, and stage 2 left it without a capacitor (paper-review finding PR-03). TI's reference fits one capacitor per supply pin and a reset RC (F-502). The added parts cost < USD 0.02 at 1k.
- **Decided by:** toolkit PoC (product owner role), from paper-review findings PR-03 and PR-05
- **Affects:** bom.csv, architecture.md §5
- **Supersedes:** —

## D-601 · 2026-11-08 · Market sequencing: US launch batch, then EU, UK and Brazil at 1k

- **Decision:** the launch batch of 100 units is sold in the US only. EU, UK and Brazil certifications are paid for the 1k run.
- **Options considered:** US first (chosen); all four markets before the launch batch.
- **Reason:** it moves USD 12.75k–82k of certification NRE out of the launch batch (`hw/cost/cost.md`). Brazil cannot receive any radio product for sale before Anatel homologation anyway (`hw/compliance.md`).
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** cost/manufacturing.json, compliance.md, roadmap/stages.json
- **Supersedes:** —

## D-602 · 2026-11-08 · Use TI's qualified BLE stack unmodified

- **Decision:** the firmware uses TI's qualified BLE controller and host from the CC2340 SDK without changes to the stack.
- **Options considered:** qualified stack unmodified (chosen); a modified or third-party stack.
- **Reason:** the Bluetooth listing then reuses TI's qualification, so it is a declaration with no lab tests (compliance/matrix.md, bt-sig row).
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** firmware, compliance.md
- **Supersedes:** —

## D-603 · 2026-11-08 · No metal on the outside; PFAS-free acoustic membrane preferred

- **Decision:** the outside of the product is plastic and elastomer only; the keyring passes through a molded slot. The acoustic membrane is a PFAS-free mesh (for example SAATI), with ePTFE as the fallback if its acoustic loss is too high.
- **Options considered:** metal keyring eyelet; ePTFE membrane only.
- **Reason:** no nickel-release test (REACH Annex XVII entry 27), and no exposure to the PFAS restrictions that are phasing in (compliance/matrix.md).
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** enclosure-engineer, cost/rfq.md request 6
- **Supersedes:** —

## D-604 · 2026-11-08 · Firmware is ready for unwanted-tracking rules from v1

- **Decision:** v1 rotates its BLE address (resolvable private address: every 15 min near the owner, every 24 h when separated), keeps the 12 s ring at ≥ 60 phon, and exposes a test mode for the certification lab.
- **Options considered:** implement now (chosen); implement only when joining a finder network.
- **Reason:** the IETF DULT draft makes these practices required for small location-enabled accessories (verified 2026-11-08). V1 reports no location, but a finder-network v2 then needs no hardware change, and the address rotation protects owners from third-party tracking today.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** firmware, compliance.md
- **Supersedes:** —

## D-510 · 2026-11-08 · Board thickness 0.6 mm (4-layer)

- **Decision:** the main board is 4-layer FR4, 0.6 mm (0.54–0.66 mm), ENIG, black mask. Thickness only; the rest of D-015 stands.
- **Options considered:** 0.8 mm (D-015; the stack with maximum heights reaches 10.2 mm); 0.6 mm (chosen).
- **Reason:** with the holder at 4.1 mm max, the sounder at 2.1 mm max and 0.8 mm minimum walls, only 0.6 mm keeps the stack at 10.00 mm (`mech/stackup.md`). JLCPCB builds 4-layer 0.6 mm boards with double-sided assembly on its standard service [estimate: pcb-engineer references/fab-capabilities.md; confirm on the order page].
- **Decided by:** toolkit PoC (product owner role), co-design stage
- **Affects:** pcb-engineer (stack-up 4L-0.6), enclosure-engineer
- **Supersedes:** D-015 (thickness only)

## D-511 · 2026-11-08 · Cell door secured by two captive screws

- **Decision:** the round door over the cell has two ears with captive thread-forming screws (1.4 × 3 mm) into blind bosses of the back plate. A flat silicone gasket under the door flange seals it. A tool opens it (UL 4200A securement by tool).
- **Options considered:** coin-operated bayonet (D-026); two captive screws (chosen).
- **Reason:** the bayonet lugs need about 0.8 mm of height above the plate, inside the radius that the 3034TR holder occupies down to z = 2.0 mm (the KiCad 3D model reaches r ≈ 11.8 mm). Lugs moved outside that radius cannot attach to the door without walls under 0.5 mm. The bayonet also needed 2 side actions in the door tool. The screw door fits the 10.0 mm stack, molds in a straight pull, and seals with a gasket whose compression is set by a hard stop.
- **Decided by:** toolkit PoC (product owner role), co-design stage. **The user should confirm:** this changes the user experience from a coin twist to a small screwdriver.
- **Affects:** enclosure-engineer, compliance-planner (UL 4200A securement option), build-package (screwdriver in the box or a note in the guide)
- **Supersedes:** D-026 (mechanism only; the child-resistance requirement stands)

## D-512 · 2026-11-08 · Enclosure architecture

- **Decision:** a 32 × 32 × 10.0 mm rounded square (R6 corners, R1.8 front edge, R1.0 back edge, 1° draft). Parts: a shell (front and sides, 0.9 mm wall); a back plate bonded with die-cut PSA and a 0.9 mm lip; the door; a two-shot TPU button; an ePTFE vent over a Ø1.0 sound hole. The keyring slot (2.0 × 5.0 mm) runs vertically through the +x+y corner.
- **Options considered:** for the keyring, a horizontal tunnel (side action) or a vertical slot through a corner fill (chosen); for the front edge, a fillet of R3.0 (the slot breaks through it) or R1.8 (chosen).
- **Reason:** every part releases in a straight pull, and the sealed volume has three seams (PSA ring, door gasket, two-shot button) plus one vent. The DFM check passes with 0 errors.
- **Decided by:** toolkit PoC (product owner role)
- **Affects:** pcb-engineer (board outline: 28.4 mm, R4.5, keyring chamfer x + y ≤ 20.75 mm), product-render, technical-drawing
- **Supersedes:** —

## D-513 · 2026-11-08 · Button nub gap 0.2 mm

- **Decision:** 0.2 mm nominal gap between the TPU nub and the SW1 actuator.
- **Options considered:** 0.1 mm (first CAD issue; worst case −0.03 mm, which pre-presses the switch); 0.2 mm (chosen; worst case +0.07 mm).
- **Reason:** tolerance stack T-2 in `mech/tolerances.md`.
- **Decided by:** enclosure-engineer
- **Affects:** button travel 0.45 mm total
- **Supersedes:** —

## D-514 · 2026-11-08 · Sounder port gasket: soft foam, 0.8 mm free

- **Decision:** a die-cut soft polyurethane foam ring (Ø3.0/Ø1.6 mm, 0.8 mm free, PSA one side) seals the LS1 top port to the shell.
- **Options considered:** a 0.3 mm solid gasket (does not seal across the 0.25–0.75 mm gap range); soft foam (chosen).
- **Reason:** tolerance stack T-5; LS1 height is 1.9 ± 0.2 mm.
- **Decided by:** enclosure-engineer
- **Affects:** BOM mechanical lines, build-package assembly guide
- **Supersedes:** —

## D-515 · 2026-11-08 · Holder and antenna placement

- **Decision:** BT1 at (−1.1, −1.1) on the back. ANT1 at (−8.9, −12.4), rotated 180° so the feed faces the RF chain. Antenna copper keep-out: x ≤ −6.0, y ≤ −10.9 on all layers.
- **Options considered:** holder centred (its courtyard collides with the keyring chamfer); offset by (−1.1, −1.1) (chosen).
- **Reason:** the holder courtyard must clear the keyring chamfer, and the cell edge must clear the antenna keep-out. The two pull in opposite directions; the result is 0.96 mm from the cell edge to the keep-out corner (F-512), against a 1 mm assumption. The EVT VNA tune covers it (V-005).
- **Decided by:** pcb-engineer
- **Affects:** enclosure (door centre), RF performance
- **Supersedes:** —

## D-516 · 2026-11-08 · Sounder orientation and sound port position

- **Decision:** LS1 at (8.0, −6.5), rotated 180°. Its top port, at (−3.0, −3.0) in the footprint frame per the drawing, lands at device (11.0, −9.5), under a Ø1.0 hole in the flat zone of the front face.
- **Options considered:** rotation 0 (port at (5.0, −3.5), 0.3 mm from the button hole); rotation 180 (chosen).
- **Reason:** the port is at a corner of the part, not at its centre (datasheet p.2). Rotation 180 keeps the hole 7 mm from the button.
- **Decided by:** pcb-engineer + enclosure-engineer
- **Affects:** shell sound hole, port gasket, Q-CD-01 (confirm the port corner against the vendor footprint)
- **Supersedes:** —

## D-517 · 2026-11-08 · Routing rules for a board with a coin cell on its back

- **Decision:**
  - Inside the cell footprint (r ≤ 10.2 mm around (−1.1, −1.1)) only GND vias are allowed; every other net stays on F.Cu there.
  - Pours connect solidly to SMD pads (thermal spokes only for THT).
  - U1's thermal pad gets 4 GND vias (0.2 mm drill).
  - Routing runs on the cloud VM with Freerouting 1.9.0 headless (xvfb); the GND islands are finished with stitching vias.
- **Options considered:** VBAT and signal vias under the cell, tented (rejected: the cell's negative face presses on the mask, so a worn mask would short VBAT to GND); Freerouting 2.5.0 (stops after about 19 passes on this board, 26–35 connections left); 1.9.0 (chosen).
- **Reason:** the 3034's negative contact is a 17.8 mm B.Cu pad, so a through via of another net cannot pass anywhere under it.
- **Decided by:** pcb-engineer
- **Affects:** pcb routing, release check
- **Supersedes:** —

## D-518 · 2026-11-08 · LED moved to DIO24; DIO12 left as an unconnected spare

- **Decision:** the LED net moves from U1 pin 5 (DIO12) to pin 12 (DIO24); both are high-drive pins. DIO12 has no connection and no test pad on EVT-0. TP7 is removed. SPARE2 (DIO6, TP8) stays.
- **Options considered:** keep the LED on DIO12 (the route from U1's bottom side to R1 cannot be completed on F.Cu: under the cell only GND vias are allowed, D-517); DIO24 (chosen; its escape faces R1 and D1).
- **Reason:** routability under the coin cell.
- **Decided by:** pcb-engineer
- **Affects:** firmware pin map (LED = DIO24), architecture.md §5.1, TP list
- **Supersedes:** —

## D-520 · 2026-11-08 · Free the LED escape by removing duplicate F.Cu connections

- **Decision:** remove three F.Cu items that duplicate existing connections: the EP→C21 GND trace (C21 GND now has a dedicated 0.4/0.2 mm via 0.6 mm from its pad, to the In1 GND plane under U1); the GND trace left of SW1 (the F.Cu GND pour joins the same pads); the BTN trace between SW1's two "1" pads (internally joined; SW1 footprint flag `duplicate_pad_numbers_are_jumpers` set on the board and in `lib/`). Route LED (U1 DIO24 → R1) on F.Cu, 0.15 mm clearance, outside U1's pad ring.
- **Options considered:** remove redundant copper (chosen); via jump under the cell with a Ø10 mm contact pad (rejected: vias under the cell face and a route inside the QFN pad ring, E-520); move D1/R1 (rejected: D1 is fixed by the light window).
- **Reason:** closes the last connection with no new vias and no rule exceptions [verified: F-520, F-521].
- **Decided by:** pcb-engineer
- **Affects:** hw/pcb/main/main.kicad_pcb, lib/pocket_beacon.pretty (SW1), Q-CD-05 (closed), Q-PCB-01
- **Supersedes:** —

## D-521 · 2026-11-08 · Keep the cell's negative contact pad at Ø17.8 mm

- **Decision:** BT1 pad 2 stays Ø17.8 mm (the trial Ø10 mm of E-520 is reverted, on the board and in `lib/`).
- **Options considered:** Ø17.8 mm (chosen); Ø10 mm (only needed for vias under the cell, which D-520 avoids).
- **Reason:** no routing benefit is left, and the larger pad tolerates cell offset in the retainer.
- **Decided by:** pcb-engineer
- **Affects:** BT1 footprint
- **Supersedes:** —

## D-522 · 2026-11-08 · GND stitching vias: never under a part body

- **Decision:** every F.Cu/B.Cu GND pour island without a via or PTH pad gets one 0.4/0.2 mm via (`hw/pcb/island_vias.py`), placed outside all component courtyards except BT1's. Vias inside the paste-free cell contact pad are allowed (same net, no solder).
- **Options considered:** courtyard rule (chosen); `stitch.py --islands` (an SMD GND pad counted as an anchor, so isolated islands stayed open, TB-12).
- **Reason:** DRC accepted vias under C2 and C3 (F-523).
- **Decided by:** pcb-engineer
- **Affects:** hw/pcb/main/main.kicad_pcb
- **Supersedes:** —

## D-701 · 2026-11-08 · Door gasket ordered at 0.35 mm free thickness

- **Decision:** die-cut silicone 40A door gasket, 0.35 mm free, keeping the recess tolerance at ±0.03 mm.
- **Options considered:** 0.35 mm free gasket (chosen); recess held to ±0.02 mm at the molder.
- **Reason:** tolerance stack T-4 gives a 0.17–0.29 mm gap. A 0.35 mm gasket is compressed 17–51 %, inside the 15–55 % working range of soft silicone, without asking the molder for a tighter class [estimate: mech/tolerances.md T-4].
- **Decided by:** doability-review fix loop (product owner role, toolkit PoC)
- **Affects:** release mech BOM, cost/manufacturing.json, prototype check V-013
- **Supersedes:** —

## D-702 · 2026-11-08 · Sounder port gasket: 0.8 mm extra-soft PU foam

- **Decision:** die-cut ring of extra-soft microcellular polyurethane foam, 0.79–0.80 mm free, closed skin, with PSA on one side. Example grade: Rogers PORON 4701-30 Extra Soft, 0.031 in [estimate: grade family from the converter catalogs, confirm in the RFQ].
- **Options considered:** solid 0.30 mm gasket (cannot seal the 0.75 mm worst-case gap, T-5); soft foam 0.8 mm (chosen).
- **Reason:** T-5 gap 0.25–0.75 mm; the foam stays compressed 6–69 % across tolerance.
- **Decided by:** doability-review fix loop (product owner role, toolkit PoC)
- **Affects:** release mech BOM, cost/manufacturing.json, prototype check V-010
- **Supersedes:** —

## D-703 · 2026-11-08 · Screw-secured cell door accepted for EVT-0

- **Decision:** EVT-0 uses the screw-secured door of D-511. A T3/PH000 micro screwdriver is named in the instructions; the launch-batch kit includes one.
- **Options considered:** accept D-511 (chosen); grow the device to about 11 mm to fit the coin bayonet of D-026.
- **Reason:** the 10.0 mm thickness limit (REQ-001) and straight-pull molding both hold only with D-511; UL 4200A securement by tool is met.
- **Decided by:** toolkit PoC (product owner role). **The user can override this** before DVT tooling: the coin bayonet returns only with a thicker device.
- **Affects:** Q-CD-02, Q-PB-204, Q-PB-06 (closed), compliance.md, the assembly guide
- **Supersedes:** —

## D-704 · 2026-11-08 · Product markings

- **Decision:**
  - **Door, molded in:** the coin-cell safety icon and "CR2032 +".
  - **Back plate, laser-marked:** FCC ID, CE and UKCA marks, model and batch, at the legibility minimums of each rule.
  - **Manual and packaging:** the full coin-cell warnings (16 CFR 1263), and the marks repeated.
- **Options considered:** everything on the product (no room at legible size); manual and packaging only (not allowed for the CE mark when the product has room).
- **Reason:** the back plate has a flat 26 mm field. The marks fit at 2 mm minimum height [estimate: compliance.md, marking rules].
- **Decided by:** doability-review fix loop (product owner role, toolkit PoC)
- **Affects:** Q-BZ-03, the CAD back plate (laser, no geometry change), packaging
- **Supersedes:** —
