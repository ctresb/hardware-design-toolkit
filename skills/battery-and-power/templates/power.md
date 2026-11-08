# Power — <product name>

Status: <draft | measured | frozen> · Date: <YYYY-MM-DD> · Owner: battery-and-power

## 1. Answer first

<Two or three sentences. Does the runtime target hold? On which case? What must be measured?>

## 2. Use pattern

| Mode | Share of the day | What runs | Evidence |
|---|---|---|---|
| | | | |

## 3. Budget

| Scenario | Average battery current | Runtime when new | Runtime at end of life | Rated capacity needed |
|---|---|---|---|---|
| Optimistic | | | | |
| Baseline | | | | |
| Pessimistic | | | | |
| Empirical (comparables) | | | | |
| Measured | — until measured | | | |

Largest contributors: <part: mA, share>.

## 4. Rails and supply checks

| Rail | Voltage | Max current | Worst-case load | Parts |
|---|---|---|---|---|
| | | | | |

`check_rails.py`: <pass / failures and fixes>.

## 5. Peak current chain

| Limit | Value | Worst simultaneous peak | Result |
|---|---|---|---|
| Cell (C-rate) | | | |
| Protection board | | | |
| PMIC system load | | | |
| Brown-out drop (R_internal × I_peak) | | | |

## 6. Battery

![Cell fit](battery.svg)

- Pocket: <outline source>, height <mm>.
- Cell: <W × L × T max> mm, <shape>, tabs on <edge>, <catalog part or custom>.
- Capacity: <low–high> mAh `[estimate]`. Planned at <low end> mAh. Claimed before this check: <x> mAh.
- Seals and tabs: <share> of the outline. Swelling allowance: <%>. Thickness tolerance: <mm>.
- Vendor plan: <catalog part for EVT; custom RFQ to 2–3 vendors for DVT>.

## 7. Charging

<Method, charge current (C-rate), charge time, temperature window, ship-mode current, shelf life, fuel gauge.>

## 8. Measurement plan

<Instrument, firmware build, modes, duration, voltages, pass criteria, owner, date.>

## 9. Open items

- [ ] <item> → <skill or person>
