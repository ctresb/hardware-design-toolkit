# Power — Pocket Beacon

Status: draft (bottom-up + calibrated, not yet measured) · Date: 2026-11-08 · Owner: battery-and-power

Inputs: `hw/power/budget.input.json` → `hw/power/budget.json` (`power_budget.py`), `hw/power/rails.json`, `hw/bom.csv`.

## 1. Answer first

One CR2032 lasts **about 3 years** in the baseline case, **18 months** in the pessimistic case and **13 months** when calibrated on shipped trackers. All three meet REQ-002 (≥ 12 months). The settings that achieve this are:

- advertising every **1285 ms** when the phone is away;
- a 1000 ms connection with peripheral latency 1 when it is near;
- **0 dBm** TX.

Two things decide the result, so they must be measured on the EVT board before the design is frozen:

- the charge per advertising event: the pass threshold is ≤ 12 µC;
- the ring current: ≤ 15.5 mA in 3× mode.

The cold, aged cell is the real limit, not the average current. At −10 °C on a cell that is 80 % used, only the 1× ring mode keeps the supply above 2.0 V (§5).

## 2. Use pattern

| Mode | Share of the day | What runs | Evidence |
|---|---|---|---|
| Connected idle | 55.0 % (13.2 h) | BLE connection to the phone, 1000 ms interval, latency 1 (one event per 2 s) | [assumption: keys near the phone most of the waking day] |
| Advertising, slow | 44.8 % (10.7 h) | connectable advertising every 1285 ms, 3 channels, 0 dBm | [assumption: phone away or off at night] |
| Advertising, fast | 0.14 % (120 s) | 20 ms advertising for 30 s after each disconnect or button press, 4 per day | [assumption: Apple accessory guideline pattern, 4 events per day] |
| App active | 0.07 % (60 s) | 30 ms connection interval with GATT traffic | [assumption] |
| Ring | 0.005 % (3.95 s) | 10 rings × 12 s per month, piezo driver 3× mode, LED off while ringing in 3× | [assumption: brief use pattern] |
| Button + LED | 0.0004 % (0.3 s) | 3 presses per day, 100 ms LED flash | [assumption] |

## 3. Budget

The battery is rated 225 mAh. 85 % of it is usable under pulse load to 2.0 V. 97 % remains after self-discharge.

| Scenario | Average battery current | Runtime when new | Runtime at end of life | Rated capacity needed for 12 months |
|---|---|---|---|---|
| Optimistic (× 0.8) | 5.7 µA | 46 months | 44 months | 61 mAh |
| **Baseline** | **7.2 µA** | **37 months** | **36 months** | **76 mAh** |
| Pessimistic (× 2.0) | 14.3 µA | 18 months | 18 months | 152 mAh |
| Empirical (comparables) | 19.3 µA | 13.6 months | 13.1 months | 205 mAh |
| Measured | — until measured | | | |

The limit for 12 months is 225 mAh × 0.85 × 0.97 ÷ 8,760 h = **21.2 µA** average.

Largest contributors (baseline, duty-weighted):

| Part | Current | Share |
|---|---|---|
| U1 SoC | 6.20 µA | 87 % |
| U2 piezo driver (rings) | 0.66 µA | 9 % |
| Board leakage | 0.30 µA | 4 % |
| D1 LED | 0.005 µA | < 1 % |

Within U1, slow advertising is 3.9 µA, connected idle 1.4 µA, and fast advertising 0.7 µA.

**How the SoC figures are built** [estimate, from figures verified in TI SWRS272F §7.9/§7.10]:

- **Advertising event: 10.3 µC.** Three channels, each with TX 0.30 ms at 5.1 mA, RX listen 0.20 ms at 5.3 mA and hop 0.15 ms at 1.5 mA. Add 1.2 ms of wake, crystal start and stack processing at 1.5 mA.
- **Connection event: 3.6 µC.**
- **Standby floor:** 0.74 µA with the 32.768 kHz crystal running.

**Calibration.** Shipped CR2032 trackers average **11.6–23.1 µA**:

- Apple AirTag, "more than a year" [verified: apple.com/airtag, 2026-11-08];
- Chipolo ONE, "up to 2 years" [verified: chipolo.net, 2026-11-08];
- a Chipolo CR2032 variant, "~1 year" [verified: same page].

That is 2.7× our baseline. Those products also run finder-network advertising, UWB or louder speakers, so the empirical case is conservative for Pocket Beacon. It still meets 12 months.

### Advertising interval options

| Slow advertising interval | Discovery delay when the app searches | Baseline life | Pessimistic life | Pessimistic life if the event costs 15 µC |
|---|---|---|---|---|
| 1022.5 ms | about 1 s | 31 months | 16 months | 12.0 months |
| **1285 ms (chosen)** | **about 1.3 s** | **36 months** | **18 months** | **13.8 months** |
| 2000 ms | about 2 s | 43 months | 22 months | 17 months |
| 4000 ms | about 4 s | 54 months | 27 months | 22 months |

All lives are at end of life. 1285 ms is the longest interval in Apple's recommended list for accessories found by iOS in the background [assumption: Apple Accessory Design Guidelines, not re-read in this stage]. It keeps 12 months even if the real event charge is 46 % higher than estimated. 2000 ms is the fallback setting if the EVT measurement fails the 12 µC threshold.

## 4. Rails and supply checks

| Rail | Voltage | Max current | Worst-case load | Parts |
|---|---|---|---|---|
| VBAT (CR2032 through Q1, direct) | 2.0–3.3 V | 15 mA (REQ-005 target) | 15.05 mA typical during a 3× ring (U2 14.2 + U1 0.85) | U1, U2, D1, D2, C1–C3, C5–C7 |

`check_rails.py hw/bom.csv hw/power/rails.json` passes: 2 supply checks, 0 failed. U1 (1.71–3.8 V) and U2 (1.5–5.5 V) contain 2.0–3.3 V. D1, D2 and the capacitors have no `vdd` token, so the script skips them. That is correct for passives and the LED.

`power_budget.py` warns that the sum of single-part maxima on VBAT (20.8 mA) exceeds 15 mA. That sum needs a TX burst, a 3× ring and the LED at the same instant. The firmware rules in `architecture.md` §4 forbid it, and the bulk capacitor carries TX bursts, so the cell sees at most 15.05 mA.

## 5. Peak current chain

| Limit | Value | Worst simultaneous peak at the cell | Result |
|---|---|---|---|
| REQ-005 target, ring | ≤ 15 mA | 15.05 mA typical | **0.3 % over the target** (Q-PW-01) |
| REQ-005 limit | ≤ 20 mA | 15.05 mA | OK |
| CR2032 pulse capability | 30 mA peaks cost about 9 % capacity versus 15 mA [verified: TI SWRA349 §3] | 15.05 mA | OK |
| Brown-out drop (R_internal × I_peak), see below | V_loaded ≥ 2.0 V (REQ-004) | | depends on cell age and temperature |
| CC2340 VDDS falling slew rate | ≤ 1 mV/µs [verified: SWRS272F §7 recommended operating conditions] | 15 mA ÷ 26 µF effective = 0.58 mV/µs | OK, **only with the bulk capacitors placed next to U1** |
| CC2340 DC/DC operating minimum | VDDS ≥ 2.2 V; below that the device switches to its GLDO and TX rises from 5.1 mA to 9.0 mA [verified: SWRS272F §7] | | sets the "low battery" threshold at 2.3 V |

**Loaded cell voltage.** CCV = OCV − I × R_internal. The R_internal values are estimates from the SWRA349 IR curve and the Energizer pulse chart: about 15 Ω fresh at 21 °C, rising with use and roughly doubling to tripling in the cold. They must be replaced by a measurement (§8).

| Cell state | OCV | R_internal [estimate] | Ring 3× (15.05 mA) | Ring 2× (7.25 mA) | TX burst without a capacitor (5.1 mA) |
|---|---|---|---|---|---|
| Fresh, 21 °C | 3.0 V | 15 Ω | 2.77 V | 2.89 V | 2.92 V |
| Fresh, 0 °C | 3.0 V | 25 Ω | 2.62 V | 2.82 V | 2.87 V |
| 50 % used, −10 °C | 2.9 V | 60 Ω | 2.00 V | **2.46 V** | 2.59 V |
| 80 % used, 21 °C | 2.85 V | 50 Ω | 2.10 V | 2.49 V | 2.60 V |
| 80 % used, −10 °C | 2.8 V | 120 Ω | 0.99 V | 1.93 V | 2.19 V |

These voltages set the firmware rule (proposed to `specs-engineer` as Q-PW-02):

1. Start every ring in 2×. Measure VBAT after 100 ms.
2. If VBAT ≥ 2.7 V, switch to 3×.
3. If VBAT < 2.3 V, switch to 1×, flag "low battery" to the app, and keep the LED off.

This meets REQ-014 (a ring at −10 °C on a cell at 50 %) in 2× mode. The loudness at 2× is about 3.5 dB below 3× [estimate: 20·log(2/3) drive voltage]. `specs-engineer` should check REQ-006 at that point.

**Bulk capacitor.** TI SWRA349 Appendix A gives C = (Q_event − V_min/R_i × t_event) / (V_max − V_min). For the design point R_i = 1 kΩ (end of life, cold), V_max = 2.6 V, V_min = 2.0 V, Q_event = 10.3 µC and t_event = 3.15 ms:

- the formula gives **C ≥ 6.7 µF effective**;
- the cell recharges the capacitor in 51 ms at 1 kΩ, well inside the 1285 ms interval.

Fitted capacitance:

- C1 + C2 are 2 × 22 µF X5R 6.3 V 0603, and C3 is 10 µF X5R 10 V 0603.
- At 3 V DC bias, they give about **26 µF effective** [estimate: 0603 X5R parts keep about 45 % (6.3 V) and 60 % (10 V) at 3 V; Samsung DC-bias curves not read; electronics-researcher confirms].
- That is a margin of 3.9× over the requirement, which leaves room for aging and cold.

During fast advertising (20 ms), a 1 kΩ cell cannot recharge between events. VBAT then settles at OCV − I_avg × R_i = 2.7 V − 0.515 mA × 1 kΩ = 2.19 V, still above the 2.0 V minimum. Keep both 22 µF parts, and place them within 5 mm of U1 VDDS and Q1.

## 6. Battery

![CR2032 in its holder](battery.svg)

- Cell: **CR2032 Li-MnO2 primary, Ø 20.0 mm × 3.2 mm max, round** [verified: Energizer datasheet dimensions 20.00/19.70 mm × 3.20/2.90 mm].
- Catalog part, no custom cell: Panasonic CR2032 225 mAh [verified: DigiKey listing, 2026-11-08]. Energizer CR2032 is rated 254 mAh typical to 2.0 V at 15 kΩ, with self-discharge of about 1 %/year and an operating range of −30 °C to 60 °C [verified: Energizer UltimateCR2032EU0920].
- Capacity planned: **225 mAh rated × 0.85 usable = 191 mAh**. The planning figure uses the lowest-rated major brand, because users will fit any brand.
- Usable fraction 0.85: in TI SWRA349 a buffer capacitor raised the worst vendor's delivered capacity from 138 mAh to 181 mAh of 220 mAh (82 %), and the best vendors came close to rated [verified: SWRA349 Fig. 8–10].
- Holder: TE BAT-HLD-001-TR, outline about 23 × 21 × 4.3 mm [assumption: drawing not read, Q-PB-01]. `battery.svg` draws that outline dashed for this reason.
- Seals, swelling and custom-cell rules do not apply. `battery_fit.py` is not used, because a catalog coin cell fixes the shape.
- Child safety: the lid must need two independent simultaneous movements or a tool [verified: Energizer datasheet safety note (2)]. This matches REQ-015 and is passed to `enclosure-engineer` and `compliance-planner`.

## 7. Charging

None. The cell is primary and user-replaceable (D-002).

- **Ship mode:** U1 in shutdown with wake on the button. The current is 0.165 µA (U1, verified SWRS272F) + 0.008 µA (U2) + 0.3 µA (leakage, estimate) = **0.47 µA**, which meets REQ-003 (≤ 1 µA).
- **Shelf loss over 2 years:** 8.3 mAh from ship-mode current (3.7 %) plus about 2 % self-discharge gives **≈ 5.7 % lost**, within REQ-003 (≤ 10 %).
- **Fuel gauge:** VBAT measured under ring load (§5). The "low battery" alert is sent at < 2.3 V loaded.
- **EU Battery Regulation 2023/1542 Article 11:** the cell is user-replaceable without tools beyond the lid action. `compliance-planner` confirms this.

## 8. Measurement plan

The instrument is a Nordic PPK2 or a Joulescope JS220, on the EVT board with production firmware (logging off, UART off), at 25 °C.

| # | Measurement | Setup | Pass |
|---|---|---|---|
| M1 | Standby floor | source mode 3.0 V, 60 s between events | ≤ 1.2 µA |
| M2 | Charge per slow advertising event, 0 dBm, 31-byte payload | source 3.0 V, 100 events averaged | ≤ 12 µC (fallback: 2000 ms interval) |
| M3 | Charge per connection event, empty packets, 1000 ms interval | phone connected | ≤ 4.5 µC |
| M4 | Ring current, 3× and 2× | source 3.0 V and 2.5 V | 3× ≤ 15.5 mA, 2× ≤ 7.5 mA |
| M5 | Ship-mode current | after the factory ship command | ≤ 1.0 µA |
| M6 | Weighted daily average | the §2 use-pattern script, 24 h, real phone | ≤ 14 µA (21.2 µA limit with a 1.5× margin for vendor and cold) |
| M7 | Loaded cell voltage, cold | ampere-meter mode on a real CR2032 discharged to 50 % (15 kΩ for 680 h), −10 °C chamber, ring 2× | VBAT ≥ 2.3 V during the ring; ring audible and ≥ 65 dB(A) at 25 cm (REQ-006 limit) |
| M8 | Brown-out margin | fast advertising with a 1 kΩ resistor in series with a 2.7 V source | VBAT ≥ 2.0 V, no reset over 30 s |
| M9 | Internal resistance, three brands | 1 kHz AC IR or a pulse step, fresh and 50 %, 21 °C and −10 °C | replaces the R_internal estimates in §5 |

M2, M4, M6 and M7 must pass before the board layout is frozen for DVT.

## 9. Open items

- [ ] **Q-PW-01** → specs-engineer: the ring peak is 15.05 mA typical against the 15 mA REQ-005 target. Options:
  - accept it as within the 20 mA limit;
  - use an on/off beep pattern of 250 ms / 250 ms, which halves the energy but not the peak;
  - run U1 in a lower-current state while ringing.

  Recommendation: accept, and re-check with M4.
- [ ] **Q-PW-02** → specs-engineer and firmware: the adaptive ring rule in §5 (2× start, 3× at ≥ 2.7 V, 1× and alert at < 2.3 V).
- [ ] **Q-PW-03** → electronics-researcher: the DC-bias curves of CL10A226MQ8NRNC and CL10A106KP8NNNC at 3 V, and the PAM8904 1× mode current.
- [ ] **Q-PW-04** → electronics-researcher: the leakage of TPD1E10B06 at 3.3 V, and the R_DS(on) and V_GS(th) max of DMG2305UX at V_GS = −2.0 V. Both feed the leakage line and the drop at end of life.
- [ ] Measurements M1–M9.
