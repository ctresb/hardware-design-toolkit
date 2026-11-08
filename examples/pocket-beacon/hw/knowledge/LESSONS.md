# Lessons

Rules learned in this project, including every user correction. Each stage reads this file first.

<!-- Entry format:
## L-001 · YYYY-MM-DD · <rule in one line>
- **Origin:** user correction "<user's words>" | own mistake | experiment E-xxx
- **What was wrong:** <the defect>
- **Rule:** <the check or rule that prevents it>
- **Applies to:** <stages or skills>
-->

## L-001 · 2026-11-08 · The package a distributor stocks may be NRND
- **Origin:** own finding, stage 2 (F-004)
- **What was wrong:** the PAM8904E package stocked at LCSC under the first search (EJER, U-QFN3030-16) is NRND in the maker's ordering table; only the 2 × 2 mm packages are Active.
- **Rule:** read the maker's ordering/status table for the exact package suffix before choosing; distributor stock is not lifecycle.
- **Applies to:** specs-engineer, electronics-researcher

## L-002 · 2026-11-08 · White and blue LEDs fail first on a coin cell
- **Origin:** own design check, stage 2 (D-005)
- **What was wrong:** a white LED (Vf 2.7–3.2 V) would stop lighting as the CR2032 sags under load and ages, long before the radio stops.
- **Rule:** on a coin cell without a boost, use LEDs with Vf ≤ 2.1 V (red, amber, yellow, yellow-green), or drive white from a boosted rail.
- **Applies to:** specs-engineer, doability-review

## L-003 · 2026-11-08 · A catalog coin-cell holder sets the device thickness
- **Origin:** own stack-up, stage 2 (D-007)
- **What was wrong:** the 8.5 mm target assumed a cell with no holder; a standard SMD holder plus board, sounder and walls sums to 9.5–9.9 mm.
- **Rule:** do the height stack-up with the holder's maximum height before promising a thickness; if the target is tighter, plan lid-retained cells with custom contacts and their tooling.
- **Applies to:** specs-engineer, enclosure-engineer

## L-004 · 2026-11-08 · Open-question IDs need per-agent ranges too
- **Origin:** own mistake, stage 3 (two research agents both used Q-PB-07 to Q-PB-09; one wrote them to `state.json`, the other only proposed them in its report)
- **What was wrong:** the agents ranges covered F- and E- IDs but not open-question IDs, so two different questions shared one ID. Decisions referencing "Q-PB-08" would have been ambiguous.
- **Rule:** brief every parallel agent with its own range for **every** ID kind it may create (F-, E-, L-, D-, Q-); the orchestrator renumbers anything proposed outside the range before merging (here: Q-PB-201…203).
- **Applies to:** hardware-engineer, lab-notebook, every parallel stage

## L-005 · 2026-11-08 · Assembler listings can carry a genuine MPN under another brand
- **Origin:** research finding F-209 (power-mech research)
- **What was wrong:** LCSC/JLCPCB list HXY parts as "DMG2305UX-7" and TECH PUBLIC parts as "TPD1E10B06DPYR". Choosing by MPN text alone can load a look-alike with different ratings.
- **Rule:** in the BOM and the assembler order, select every part by its **LCSC number** and check the brand field equals the manufacturer in the dossier; `bom.csv` carries the `lcsc` of the genuine listing.
- **Applies to:** electronics-researcher, cost-and-sourcing, build-package

## L-510 · 2026-11-08 · Check a lid mechanism against the holder's 3D model, not its footprint
- **Origin:** own mistake (co-design stage): the bayonet door was specified before checking where the holder's metal sits above the board.
- **What was wrong:** bayonet lugs need height above the plate inside the radius that the holder occupies; the 10.0 mm stack had no room.
- **Rule:** before choosing a lid or door mechanism, slice the real 3D models of everything near it (holder, cell, connectors) and check the swept volume of every moving part.
- **Applies to:** enclosure-engineer, specs-engineer

## L-511 · 2026-11-08 · A part's port position comes from the drawing, not the description
- **Origin:** own finding: "top port" was read as "port in the centre"; the drawing puts it in a corner.
- **What was wrong:** a centred sound hole would have missed the port by 4.2 mm.
- **Rule:** read the mechanical drawing for every port, window or actuator position, and record its offset in the footprint frame.
- **Applies to:** electronics-researcher, pcb-engineer, enclosure-engineer

## L-520 · 2026-11-08 · When the last net will not route, look for redundant copper before adding vias
- **Origin:** experiment E-520 / E-521
- **What was wrong:** the autorouter and a single-layer router both failed on the last net, and the first fix tried was a via jump under a coin cell and under a QFN pad ring. Both are bad practice, even though DRC passed.
- **Rule:** before adding vias in a constrained zone, list the tracks that wall the net's escape and remove those that duplicate a pour connection or a part's internal connection. Forbid routing inside a QFN pad ring (`--no-under`), and keep stitching vias out of component courtyards. DRC does not check either rule.
- **Applies to:** pcb-engineer

## L-530 · 2026-11-08 · Exploded gaps follow the projected depth, not the thickness
- **Origin:** own mistake, Pocket Beacon blueprint run 1 (vent hidden, door and gasket balloons on one edge)
- **What was wrong:** 7–8 mm gaps between 32 mm flat parts at 26° elevation; the upper part covered the lower one.
- **Rule:** set the explode gap of a flat part to about its plan diagonal × sin(elevation) plus its height; check that `blueprint.py` reports no "hidden in this view".
- **Applies to:** technical-drawing

## L-701 · 2026-11-08 · Studio renders drop lights the shot did not create
- **Origin:** own mistake (LED glow invisible in three render rounds)
- **What was wrong:** the LED point light was added before `studio.py`, which hides every light it does not own; a second bug placed the glow 1.6 m away because the KiCad empty carries a 1000× scale.
- **Rule:** make shot-level glows emissive meshes hidden from camera rays, and offset in world units with rotation-only matrices.
- **Applies to:** product-render

## L-702 · 2026-11-08 · Order-step upload paths must use the release layout, not the stage layout
- **Origin:** own mistake
- **What was wrong:** release.json order steps named `mech/pocket-beacon_shell.stl`; the release renames enclosure files to `mech/<part>.stl`, so the gate failed 7 times.
- **Rule:** write `upload` paths as they appear inside `hw/release/<rev>/`; run the gate after every edit of release.json.
- **Applies to:** build-package
