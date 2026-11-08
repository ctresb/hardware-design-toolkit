# Example: 20 mm round BLE sensor ("puck")

A fictional product used to test the pipeline. It is a 4-layer, 0.8 mm board with:

- nRF52832 SoC, with a chip antenna, an RF corner and an antenna copper keepout;
- Li-Po charger and 3.0 V LDO;
- accelerometer, from a generated symbol;
- status LED, dock contacts on the back with ESD protection, and magnet keepouts on the back;
- SWD test points;
- a 3 × 3 fab panel with fiducials on the rails.

```sh
python3 ../../scripts/build.py board.json --out /tmp/puck --no-render --release
```

Expected result in about 30 s on a laptop:

- library, ERC, placement and DRC pass;
- `release_check` reports **NOT READY**. The board is not routed, and the example parts have no LCSC numbers or MPNs for the passives.

That is the honest state of a placement study. To finish it:

1. Hand-route the RF, crystal and DC/DC nets, then run `--route` on a workstation (`references/workflow.md`).
2. Fill `lcsc` and `mpn` for every part.
3. Run `--release` until it prints READY TO ORDER.

The component values follow the vendors' reference circuits only loosely, so the board can stay small. Do not fabricate this example as is.
