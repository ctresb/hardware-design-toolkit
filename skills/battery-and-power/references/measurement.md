# Measuring current before you commit

A bottom-up budget from datasheets is a hypothesis. Shipped products often draw 3–5× that budget, and sometimes much more. The reasons are firmware wake-ups, radio retries, peripherals left on, leakage through pull-ups and LEDs, regulator efficiency at light load, and logging. Measure before you order a custom cell, cut a mold or freeze the board size.

## Instruments

| Instrument | Range | Use |
|---|---|---|
| Power-profiler kit (e.g. Nordic PPK2) | about 200 nA to 1 A, high sample rate | first choice for BLE/IoT dev kits; acts as source or ammeter |
| Joulescope (e.g. JS220) | nA to A, very high dynamic range | accurate long captures, energy over hours |
| Qoitech Otii Arc/Ace | µA to A, with a battery emulator and profiling | battery-profile-based runtime estimates |
| uCurrent-style shunt amplifier + oscilloscope | µA to mA | cheap; good for peaks, poor for long averages |
| Bench multimeter | — | **not suitable**: it misses the peaks and wake-ups that set the average |

## Procedure

1. Use the real chips on a dev kit or an EVT board, with firmware that does the real job (sampling rate, codec, radio interval, flash writes). An idle demo firmware tells you nothing.
2. Power the board from the instrument at the cell's nominal voltage (e.g. 3.7 V). Repeat at the cell's minimum (3.0–3.3 V) and full (4.2 V or 4.35 V) voltage.
3. Capture each mode in `hw/power/budget.json` for at least 10 minutes, or longer than its longest periodic event (a sync, a log flush, an advertising cycle).
4. Record the average and the peak, plus a screenshot or CSV. Store them in `hw/power/measurements/`.
5. Weight the modes by their duty cycle. Put the result in `measured_avg_ma` in the budget input, and re-run `scripts/power_budget.py`.
6. Compare the measurement with the baseline. If they differ by more than 30 %, find the reason before you change the budget's factors.

## Gate

A custom cell, a mold or a board-size freeze needs:

- a measured duty-weighted average current, with its evidence: file, instrument, firmware version and date;
- a measured average no higher than `max_avg_ma_eol` for the target runtime, with about 20 % margin;
- measured peaks below every limit in the peak chain (`references/charging-options.md`).

If the measurement does not pass, change the product, not the spreadsheet. The options are a lower duty cycle, a lower-power mode (for example wake on sound instead of always recording), a lower bit rate, a shorter runtime target or a bigger enclosure. Log the choice in `hw/decisions.md`.

## Testing candidate cells

- Discharge two or three samples of each candidate with the real load profile, not only at 0.2C. Small cells deliver noticeably less at pulsed loads and in the cold.
- Measure the voltage drop at the peak current, at 20 % charge and at 0–10 °C. That is where brown-outs happen.
- Measure the ship-mode current on the assembled device. It sets the shelf life between factory and customer.
