# Test plan · <product> rev <rev>

Every test has a method, an instrument and a pass threshold. Values come from the stage files; cite their IDs.

## 1. Bring-up (bare board, before the cell)

| # | Step | Instrument | Pass |
|---|---|---|---|
| 1 | Visual check: polarity of <parts>, no bridges on <fine-pitch parts> | 10× loupe or microscope | no defect |
| 2 | Resistance <rail> to GND, unpowered | multimeter | ≥ <value> kΩ |
| 3 | Power from bench supply at <V>, current limit <mA> | bench supply | idle current ≤ <mA> |
| 4 | Rail voltages | multimeter | <rail> = <V> ± <tol> |
| 5 | Program the test firmware via <port> | <programmer> | readback OK |

## 2. Test points

| TP | Net | Expected |
|---|---|---|
| <TPn> | <net> | <value ± tol> |

## 3. Power measurement (gate for any custom cell or battery change)

| Mode | Duration | Instrument and setup | Pass |
|---|---|---|---|
| <mode> | <min> | <power profiler, supply V, sample rate> | average ≤ <mA> (budget <F-/REQ- ID>) |

## 4. Functional tests

| # | Function | Method | Pass |
|---|---|---|---|
| 1 | <radio / sensor / LED / speaker> | <method> | <threshold> |

## 5. Verify on the prototype

See `verify-on-prototype.md` (from `doability-review`).
