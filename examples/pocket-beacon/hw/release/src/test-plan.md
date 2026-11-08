# Test plan · Pocket Beacon rev evt0-a

Applies to: 10 EVT-0 units. Instruments: Nordic PPK2 or Joulescope JS220; TI XDS110 with Tag-Connect TC2030-CTX-NL; class 2 sound level meter; VNA 2–6 GHz; spectrum analyzer; climate chamber to −10 °C; DMM.

**WARNING** Bench supplies replace the cell during bring-up. Set the current limit to 20 mA before connecting a board. Never connect a supply and a cell at the same time.

## 1. Bring-up order (bare PCBA)

| # | Step | Pass |
|---|---|---|
| T-01 | Visual and X-ray report from the assembler for U1 and U2 | no bridges, voids under the U1 thermal pad ≤ 25 % |
| T-02 | SW1 terminal links (V-012) | 1-1 and 2-2 < 1 Ω unpressed; 1-2 < 1 Ω pressed |
| T-03 | Apply 3.0 V, 20 mA limit, to the cell pads | current < 5 mA at power-on, no heating |
| T-04 | Flash test firmware via TC2030 | device ID read; DC/DC running |
| T-05 | 48 MHz offset (V-006) and 32.768 kHz start (V-007) | ±20 ppm; LFXT starts within 1 s |
| T-06 | RF match (V-005) | S11 ≤ −10 dB, 2402–2480 MHz |
| T-07 | Power measurements M1–M9 (`hw/power/power.md` §8) | thresholds in the table below |

## 2. Power plan (from `hw/power/power.md` §8)

| # | Measurement | Pass |
|---|---|---|
| M1 | Standby floor | ≤ 1.2 µA |
| M2 | Charge per slow advertising event, 0 dBm | ≤ 12 µC (fallback: 2000 ms interval) |
| M3 | Charge per connection event, 1000 ms | ≤ 4.5 µC |
| M4 | Ring current, 3× and 2× | 3× ≤ 15.5 mA, 2× ≤ 7.5 mA |
| M5 | Ship-mode current | ≤ 1.0 µA |
| M6 | Weighted daily average, 24 h use pattern | ≤ 14 µA |
| M7 | Loaded cell voltage at −10 °C, 50 % cell, 2× ring | VBAT ≥ 2.3 V |
| M8 | Brown-out margin, 1 kΩ in series from 2.7 V | VBAT ≥ 2.0 V, no reset in 30 s |
| M9 | Cell internal resistance, three brands | replaces the estimates in power.md §5 |

M2, M4, M6 and M7 must pass before the board layout is frozen for DVT.

## 3. Functional tests (assembled unit)

| # | Test | Pass |
|---|---|---|
| T-10 | Button press | LED blink and an app event within 0.5 s |
| T-11 | Ring loudness (V-004) | ≥ 75 dB(A) at 25 cm in 3× on a fresh cell |
| T-12 | Range through a bag (V-009) | connected at 10 m indoor |
| T-13 | Cell access (V-011) and door securement (V-014) | criteria in `verify-on-prototype.md` |
| T-14 | Seal (V-013), after the 72 h adhesive cure | IPX7: no water inside |

## 4. Test points

Test pads, the TC2030-NL footprint and the cell pads are listed in `firmware/pins.json` and on the assembly drawing (`hw/pcb/fab/main/`).

The full "Verify on the prototype" list is in `verify-on-prototype.md`.
