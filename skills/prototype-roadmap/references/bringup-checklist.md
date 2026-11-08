# Board bring-up checklist

Bring up each new board in this order. Do not move to the next step until the current one passes. Record each result in `hw/roadmap.md` under the board revision, including measured values and the instrument used.

## 0. Before power

- [ ] Inspect the board visually and with a microscope: solder bridges on fine-pitch parts, polarity of diodes, LEDs and tantalum caps, and rotation of ICs against the pin-1 marks.
- [ ] Ask the assembler for X-ray images of BGA, QFN and LGA parts. Many assemblers require X-ray for these packages.
- [ ] Measure the resistance from each rail to ground. The value should not be near 0 Ω. Compare it with a known-good board when you have one.
- [ ] Check that the battery connector or contacts are not swapped.

## 1. First power

- [ ] Power the board from a current-limited bench supply or a source-measure unit, not from a battery. Set the limit to about 2× the expected peak.
- [ ] Raise the voltage slowly, and watch the current while you do.
- [ ] Measure every rail. Each must be within tolerance and in the right power-up order.
- [ ] Check that no part runs hot. Use a thermal camera or a finger test only at low current.
- [ ] Measure quiescent current in ship, off or hibernate mode against the budget.

## 2. Debug and programming

- [ ] The SWD or JTAG debugger connects, and the chip ID reads back.
- [ ] Flash a blinky or test firmware. The clocks start: HFXO and LFXO, or an LFRC calibration plan.
- [ ] Program the device unique ID or keys if the product needs them. Lock debug only on production firmware.

## 3. Power management

- [ ] Charge a real cell. Check the charge current, termination voltage (4.20 V or the HV value such as 4.35 or 4.40 V), NTC window, and charge-complete flag.
- [ ] Discharge it, and check the undervoltage cutoff and the brown-out behavior.
- [ ] Run the fuel gauge against a measured discharge. Many gauges need a battery model characterised for the exact cell.
- [ ] Check load switches for back-powering. A switched-off rail must not be fed through I/O pins or pull-ups. Tri-state or drive low the lines into an unpowered part.

## 4. Peripherals, one at a time

- [ ] Run a bus scan on I²C and SPI. Every device answers at its expected address. Address straps and variants matter, because some part variants change the address.
- [ ] Memory: identify it, then run a full erase, write and read-back. Check bad-block handling on NAND, and do a power-cut test during writes.
- [ ] Sensors: read raw data and check its plausibility. Verify interrupts and wake lines.
- [ ] Microphones and audio: record raw PCM, then check SNR, clipping and the frequency response against the open-air bench.
- [ ] LEDs: check each channel's current, color and brightness at minimum battery voltage, because headroom shrinks at end of discharge.
- [ ] Touch and buttons: test them through the real enclosure wall, with water and sweat present.

## 5. Radio

- [ ] Measure the conducted output power through a test port or a coax pigtail, if the board has one. Otherwise, run a radiated check in a shielded box.
- [ ] Measure antenna matching with a VNA: on the board, then in the enclosure, then on a body.
- [ ] Check link range and throughput while the device is worn. Check reconnection after it goes out of range.
- [ ] Measure current during advertising, connection, bulk sync and idle.

## 6. System

- [ ] Measure average current in every operating mode with the real duty cycle. Compare it with the Stage 0 bench figure. It must be within 20%, or you must explain the gap.
- [ ] Measure runtime on a full cycle with a new cell. Then estimate the end-of-life runtime at 80% capacity.
- [ ] Run OTA update, including power loss during the update.
- [ ] Run a long-run soak test of 24–72 h with logging. Look for leaks, resets and memory growth.
- [ ] Put the device in a thermal chamber, or at least in the sun and in a pocket.

## Exit

Write up the result in `hw/roadmap.md`:

- the open bugs;
- for each bug, whether it needs a board change or can be fixed in firmware;
- the scope of the next revision.

Close each item with a test result, not with "should work".
