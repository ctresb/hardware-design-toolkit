**Project:** Pocket Beacon  
**Date:** 2026-11-08  
**Review round:** 3 of 3  
**Final verdict:** READY TO BUILD (prototype)  
**Next:** build the prototype and run the 'Verify on the prototype' list

| Area | Status | Critical | Major | Minor |
|---|---|---|---|---|
| Parts | GO | 0 | 0 | 1 |
| Electrical | GO | 0 | 0 | 2 |
| Power and battery | GO | 0 | 0 | 1 |
| PCB | GO | 0 | 0 | 1 |
| Mechanical | GO | 0 | 0 | 2 |
| Compliance | GO | 0 | 0 | 0 |
| Cost | GO | 0 | 0 | 1 |
| Schedule | GO | 0 | 0 | 1 |
| Claims vs reality | GO | 0 | 0 | 0 |

Counts are open findings. GO: nothing open blocks the area. FIX: the toolkit fixes it in the loop. BLOCKED: needs the user or the physical world.

### Build package

- [x] Boards routed (no unrouted nets)
- [x] DRC and ERC with 0 violations, schematic parity
- [x] Fab files: Gerbers, drill, pick-and-place, assembly drawing
- [x] BOM in stock at the chosen assembler (or consigned parts bought)
- [x] Enclosure STEP, ready for a print, machining or molding quote
- [x] Assembly validator: 0 interpenetrations; tolerance study done
- [x] Bring-up and test plan written

### Production readiness

- [ ] Prototype measurements done and passed
- [ ] Quotes received for every NRE and recurring cost line
- [x] Certifications planned with lab, cost and dates

### Verify on the prototype

| ID | What | Method | Instrument | Pass criteria |
|---|---|---|---|---|
| V-001 | Standby floor and weighted daily average current (power.md M1, M6) | bench supply 3.0 V at TP1/TP2, cell removed; 60 s idle, then the 24 h use-pattern script with a real phone | power profiler (Nordic PPK2 or Joulescope), ≥ 100 kHz sampling | standby ≤ 1.2 µA; daily average ≤ 14 µA (21.2 µA limit, REQ-002) |
| V-002 | Charge per slow advertising event and per connection event (M2, M3) | 3.0 V source, 0 dBm, 31-byte payload, 100 events averaged; 1000 ms connection, empty packets | power profiler (Nordic PPK2 or Joulescope), ≥ 100 kHz sampling | ≤ 12 µC per advertising event (else 2000 ms interval); ≤ 4.5 µC per connection event |
| V-003 | Ring current in 2× and 3× and the adaptive ring rule (M4, D-028) | source 3.0 V and 2.5 V; ring command from the app; log PZ_EN1/PZ_EN2 and VBAT | power profiler (Nordic PPK2 or Joulescope), ≥ 100 kHz sampling + logic analyzer | 3× ≤ 15.5 mA, 2× ≤ 7.5 mA; firmware selects 2× at 2.5 V under load and 3× at 3.0 V |
| V-004 | Ring loudness (REQ-006) | assembled unit hanging free, mic at 25 cm on axis, 4 kHz ring, fresh cell and a cell at 2.4 V under load | class 2 sound level meter, A-weighted, IEC 61672 | ≥ 75 dB(A) in 3× on a fresh cell; ≥ 65 dB(A) in 2× at 2.4 V loaded |
| V-005 | Antenna match and harmonic filter tuning (D-020, D-030) | assembled unit with cell and closed enclosure; S11 at the RF_P reference plane via a semi-rigid pigtail; tune C11/L2/C12, R2/C18; then conducted harmonics | VNA 2–6 GHz (e.g. NanoVNA V2 or lab VNA) + spectrum analyzer | S11 ≤ −10 dB across 2402–2480 MHz; 2nd and 3rd harmonics ≥ 6 dB below the FCC 15.209 / EN 300 328 limits in the pre-scan |
| V-006 | 48 MHz frequency offset with C16/C17 fitted (D-019) | CW tone at 2440 MHz from the TI test firmware, 25 °C and −10 °C | spectrum analyzer or frequency counter, ≤ 1 ppm resolution | offset within ±20 ppm at both temperatures (BLE ±50 ppm budget with margin); else change C16/C17 |
| V-007 | 32.768 kHz start-up at cold with ESR 90 kΩ (D-025, F-105) | 10 power cycles at −10 °C; measure LFXT start time and sleep-clock accuracy | oscilloscope + TI SDK clock test | starts every time within 1 s; accuracy ≤ ±50 ppm |
| V-008 | Loaded cell voltage at cold and brown-out margin (M7, M8) | CR2032 discharged to 50 % (15 kΩ for 680 h), −10 °C chamber, 2× ring; fast advertising through 1 kΩ from 2.7 V | power profiler (Nordic PPK2 or Joulescope), ≥ 100 kHz sampling in ammeter mode + climate chamber | VBAT ≥ 2.3 V during the ring; VBAT ≥ 2.0 V and no reset over 30 s |
| V-009 | BLE range through a bag (REQ-010) | phone app RSSI and connection at 5 m and 10 m indoor, unit inside a fabric bag with keys | phone app log | connected at 10 m indoor (≥ 5 m limit) |
| V-010 | Sound port alignment over the LS1 top port (Q-CD-01) | view the assembled front shell hole against LS1 under a stereo microscope; then V-004 | stereo microscope with reticle | port centre within 0.3 mm of the Ø1.0 shell hole centre |
| V-011 | CR2032 insertion and removal through the Ø22.0 door bore (Q-CD-06) | 10 insert/remove cycles with fingers only, door open; check the 3034 retainer after cycling | visual check, 4-wire milliohm meter on cell contacts | cell seats without tools; contact resistance ≤ 100 mΩ after 10 cycles; no retainer deformation |
| V-012 | SW1 internal terminal links (Q-PCB-01, D-520) | bare assembled board, probe SW1 pads 1-1 and 2-2 unpressed, then 1-2 pressed | DMM continuity | 1-1 and 2-2 < 1 Ω unpressed; 1-2 < 1 Ω pressed and open when released |
| V-013 | Ingress seal of the door and port gaskets (REQ IP67 target) | assembled EVT unit (machined or molded parts; SLA parts only for a pre-check), immersion 1 m for 30 min per IEC 60529 IPX7, then open and inspect | immersion tank, moisture indicator paper inside | no water inside, indicator unchanged, unit still advertises |
| V-014 | Child-resistant compartment pre-test (UL 4200A securement) | door closed with both screws at 0.08 N·m; apply the UL 4200A abuse sequence on 3 units (drop, crush, torque on the door) | torque driver, drop rig 1 m, force gauge | door stays secured and the cell stays inaccessible on all 3 units |
| V-015 | Button press force through the TPU membrane | press the button cap centre at 1 mm/s, 10 presses | force gauge with ≥ 0.01 N resolution | 2.3–3.3 N actuation force, tactile click felt, no pre-press at rest |
