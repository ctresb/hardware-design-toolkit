# From spec to fab

## The loop

```
architecture.md + bom.csv + enclosure outline
        │
        ▼
board.json ──► build.py ──► libgen ─► schgen ─► ERC ─► pcbgen (legalizer) ─► DRC ─► exports
        ▲                       │          │       │          │                 │        │
        │                  pin/pad/net   blocks  errors   placement-report   counts   images, GLB,
        │                  cross-check                                                 pads.json, fab
        │                                                                                │
        └──── fix the spec ◄── review images ◄── enclosure-engineer validator ◄──────────┘
```

Each pass takes about 30 s for a 40-part board on a laptop. Iterate on the spec, never on the generated files.

## Reading the reports

| Report | What is acceptable |
|---|---|
| `libgen` errors | none. A pin without a pad means a wrong footprint or a wrong symbol variant. A pin without a net means an undecided connection: decide it. |
| `libgen` warnings | Pads that are not in the symbol are usually exposed pads or mounting pads. Give them a net (GND, or the mounting net) when the datasheet says so. |
| `erc.json` | 0 errors. Read every warning. `pin_to_pin` between a PWR_FLAG and a bidirectional pin is benign. "Power input not driven" means a missing PWR_FLAG or a wrong pin type. |
| `placement-report.json` | `failed` and `fixed_collisions` empty. Read `moved`: a part that moved 3–4 mm is far from its IC, so the decoupling or RF loop is now long. Give it a better starting point or more room. |
| `drc.json` | 0 errors and 0 `schematic_parity`. Warnings for silkscreen are cosmetic. `isolated_copper` is a plane fragment to remove or connect. `unconnected` is the routing work left. |

## Placement order

1. Fixed by the product: connectors, contacts, antenna, LEDs under windows, mics over ports, sensors under the touch area, buttons, battery tabs.
2. Fixed by physics: the RF chain next to the antenna feed, the crystal within ~2–3 mm of the SoC's XC pins, the DC/DC inductor and its caps in a tight loop at the SW pin.
3. Decoupling caps at their pins, on the same side if possible, or directly under them on the other side.
4. Everything else, as close to its IC as the legalizer allows.

Give every part a deliberate starting position. The legalizer resolves overlaps; it does not design the board.

## What to route by hand, before any autorouter

Route these by hand and lock them (KiCad: select, then Lock). `route.py` keeps locked tracks.

- **RF:** the SoC antenna pin → matching network → antenna feed. Use a 50 Ω coplanar waveguide over a solid ground on the next layer, short and straight, with a via fence. Compute the width from the fab's real stack-up.
- **Crystal:** short and symmetric traces, ground guard, no other signals under the crystal.
- **Switching regulators:** the SW node, the inductor, the input and output caps, and the ground return, in the smallest possible loop.
- **Mic clock/data (PDM/I²S)**, USB pairs, and any differential pair, which need length matching and impedance control.
- **Power entry:** contact → ESD → protection → charger, with wide copper.

Then autoroute the rest. Freerouting is fine for low-speed digital nets on small boards. Check every result in KiCad and clean the corners. Autorouting is CPU-heavy: export the DSN here and route it on a workstation or a cloud VM (next section).

## Routing on another machine

Autorouting is a long, CPU-bound job. Run it on a workstation or a cloud VM, never on the laptop that runs the session. Any Linux machine with 4+ cores and Java works; a GPU is not used, and KiCad is not needed there.

1. **Export here:** `<kicad-python> scripts/route.py export hw/pcb/board.json --board main`. It writes `main/main.dsn` and `main/main.zones.json` (the pours it removed), and leaves the board file unchanged. Inner planes of `--keep-planes` nets (default GND) stay in the DSN so the router drops vias onto them.
2. **Copy the DSN** to the machine. On a cloud VM without SSH, use object storage plus a remote command, for example AWS S3 + Systems Manager (`aws s3 cp main.dsn s3://<bucket>/<prefix>/`, then `aws ssm send-command` with the commands of step 3, then copy `main.ses` back the same way). Delete the objects and stop or terminate the VM afterwards.
3. **Route there.** Freerouting 1.9.0: `xvfb-run -a java -jar freerouting-1.9.0.jar -de main.dsn -do main.ses -mp 60` (it opens a window, so a headless Linux machine needs `xvfb`). Freerouting 2.x: `java -Djava.awt.headless=true -jar freerouting-2.5.0.jar -de main.dsn -do main.ses -mp 60 --gui.enabled=false` (2.5.0 needs Java 25).
4. **Import here:** copy `main.ses` next to the board, then `<kicad-python> scripts/route.py import hw/pcb/board.json --board main`. It imports the SES, keeps locked tracks, restores the pours and refills them with `kicad-cli`.
5. **Finish and check** (next section), then `build.py --release`.

`route.py run` does steps 1, 3 and 4 on one machine, which is right for a workstation that has KiCad and Java. `build.py --route` calls it.

### Freerouting versions

| Version | Java | Behavior on a dense small board |
|---|---|---|
| 1.9.0 | 17+ | needs a display: `xvfb-run` on headless Linux. Routed a 28 mm 4-layer, 47-part board to 4 open connections after placement changes |
| 2.5.0 | 25 (class file 69) | headless CLI. Stops after about 19 passes when the score stops improving; left 26 to 35 connections on the same board |

`kicad_env.py` and `toolchain-setup`'s doctor read the Java version each jar needs and refuse a Java that is too old.

## Finishing a dense board

The autorouter rarely closes every connection on a coin-sized 4-layer board. Close the rest in this order, running DRC (JSON, inside the project folder) between steps:

1. `finish.py dupes BOARD --remove`: delete tracks that duplicate a same-net pour or link pads that the part connects internally.
2. `finish.py planes BOARD DRC.json --nets GND,VBAT`: a via and a short track from each unconnected plane-net pad.
3. `finish.py net BOARD NET REF1 PAD1 REF2 PAD2 --layers F.Cu,In2.Cu [--no-under U1] [--no-via-circle X,Y,R]`: one remaining signal, routed over one or more layers with vias. With `--debug`, it writes reachability maps when there is no path.
4. `finish.py islands BOARD --net GND`: one via in each outer-layer pour island that no via or PTH pad anchors.
5. `finish.py prune BOARD DRC.json`: remove vias that DRC reports as dangling.

If `finish.py net` finds no path, move a part or free a layer in the spec and regenerate. Do not force a track through a pad ring.

If `release_check.py` lists anything after routing, fix it in the spec and repeat.

## Fab outputs and the assembler

- `fab/<board>/<board>_gerbers.zip` has copper, mask, paste, silkscreen, outline and drill (PTH and NPTH separately). Upload it as is.
- `<board>_bom.csv` and `<board>_cpl.csv` use JLCPCB's column names. Most assemblers accept them or map them in their upload screen.
- **Fill `lcsc`** (or the assembler's part numbers) in the spec for parts they stock. Mark consigned parts in the order notes.
- **Rotation:** assemblers use their own zero orientation per package. Their upload preview shows each part on its pads. Check every IC, diode, LED and polarized cap in that preview, and correct it in the order, not in KiCad.
- **Small boards:** under the assembler's minimum size (JLCPCB: 70 × 70 mm), order a panel. Use KiCad's panelization or the fab's panel service, with rails, fiducials on the rails and mouse bites.
- **Order 5–10 boards** of each revision. The first build always finds something.

## Revisions

- Bump `rev` in the spec for every board sent to fab. Keep the fab zip of each revision.
- Record the reason for each change in `hw/decisions.md`.
- Expect 3–4 revisions from the first EVT board to production on a new product.
