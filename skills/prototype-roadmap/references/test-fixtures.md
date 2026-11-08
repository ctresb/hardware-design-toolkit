# Production test fixtures

Design test access into the board before routing. Adding a test point after DVT costs a board revision.

## Design for test (at EVT layout)

- **Test pads:** put test pads (not vias) on power rails, ground, SWD/JTAG, UART, reset and the battery terminals. Pads of 0.8–1.0 mm on a 2.54 mm grid keep pogo fixtures cheap. Smaller grids raise the fixture cost.
- **Probe from one side.** Use the side without tall parts, so a single-sided bed of nails can do the job.
- **RF:** provide either a test connector or switch, or a known radiated test position. Without a conducted port, production RF tests must be radiated in a shielded box.
- **Stable fixture position:** add fiducials and tooling holes on the board or panel, or tooling features on the enclosure.
- **Test mode:** factory test firmware must run every test, report pass or fail over UART or BLE, then be replaced by (or switch to) production firmware.

## Fixtures by stage

| Fixture | What it checks | When it is needed | Typical NRE |
|---|---|---|---|
| Pogo bed (board level) | rail voltages, quiescent current, flash and ID, peripheral self-test | late EVT for the build team; validated at PVT | USD 500–3,000 per fixture |
| RF test box (shielded) | output power, frequency offset, sensitivity or packet error rate | DVT | USD 1,000–5,000 |
| Acoustic test (assembled device) | microphone sensitivity, port leaks, speaker output | DVT, if there is audio | USD 1,000–5,000 |
| Leak / pressure-decay tester | sealing of each unit before the IP claim ships | DVT/PVT, if IP-rated | USD 2,000–10,000 |
| Touch and button calibration | thresholds through the real enclosure | DVT | USD 500–2,000 |
| Battery formation and capacity check | incoming-cell capacity and internal resistance; done by the cell vendor, with sampling at your factory | PVT | vendor scope plus sampling |
| Final functional test | charging in the real dock, LEDs, radio pairing, serial-number label | PVT | USD 500–3,000 |

All NRE figures are `[estimate]`. For small runs, an assembler often charges USD 2–10k in total for jigs and programming fixtures.

## Yield and traceability

- Log every unit's results against its serial number.
- Track first-pass yield per test and the escape rate (failures found later by the user).
- Keep golden units, and a known-bad unit for each failure mode, to check the fixtures every shift.
