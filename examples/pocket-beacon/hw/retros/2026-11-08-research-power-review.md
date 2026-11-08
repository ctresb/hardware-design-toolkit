# Retro · 2026-11-08 · Stages 3 to 5: research close-out, power re-run, paper review

## Request
Close the research and power stages of the Pocket Beacon run and decide every open question as product owner. Then run the paper pass of `doability-review` with its fix loop, and hand the mechanical constraints to the next stage.

## Done and verified
- **Open-question IDs:**
  - the three questions the power-mech researcher only proposed are now Q-PB-201 to Q-PB-203;
  - every stage-2 and research question is resolved;
  - one blocking question is open for the enclosure stage, Q-PB-204.

  Check: `state.json`.
- **Decisions D-018 to D-031:** 14 decisions applied to `requirements.md` (issue 2), `architecture.md` (issue 2) and `bom.csv` (27 rows).
  - Check: `bom_merge.py --overwrite` 0 errors; `bom_check.py` 0 errors and 1 explained warning; `check_rails.py` 2 passed, 0 failed.
- **Six new dossiers:** R1, R2, R3, C16/C17, C11/C12 (1.5 pF) and L2 (2.7 nH). They come from the JLC parts API and the TI LaunchPad design files.
  - Seven replaced dossiers moved to `parts/superseded/`.
- **RGE pin map:** read from SWRS272F (Figure 6-2, Table 6-1). Every net is named in `architecture.md` §5.
- **Power budget re-run:** R1 at 330 Ω and the larger bulk capacitance, `power_budget.py` exit 0.
  - Baseline 7.2 µA, empirical 19.3 µA, against the 21.2 µA limit.
- **Paper review:**
  - 13 findings fixed in round 1 and re-checked in round 2;
  - 5 minor or info findings tied to prototype checks V-001 to V-009;
  - `doability_score.py` gives NOT READY, the expected result at this stage. The listed blockers are the build-package items of later stages.
- **`hw/mech/constraints.md`** written.

## Not verified
- The UL 4200A-2023 text itself: the minimum torque and spin angle for the tool-operated option are still to read (free UL IBR copy).
- The U2 pin numbers, which `pcb-engineer` reads from DS41667.
- The exact Johanson ground-clearance rectangle.
- The Tag-Connect TC2030-NL pad mapping.
- The maker datasheets of the FH and UNI-ROYAL passives. Their dimensions are standard envelopes, and their evidence is tagged `estimate`.

## User interventions
- None in this stage. All answers come from the product-owner role (D-001).

## Mistakes and causes
- **Ran `bom_merge.py` on the old BOM.** A Python edit failed first, and the shell chain kept going. Fixed by restoring the backup and re-applying the edit. Rule: chain dependent steps with `&&`, or check the exit code before merging.
- **`git mv -k` did nothing.** It skips files that are not tracked, so the superseded dossiers did not move on the first attempt. Fixed with plain `mv`.
- **Report file name refused.** The harness refused `doability/report.md` for this agent. The content is in `doability/review.md`. The presentation reads the "measured or quoted" list from `report.md`: the orchestrator should copy or rename it.
- **Paper findings were not checked against the TI reference board.** The stage-2 design missed the VDDD capacitor and the harmonic filter. Comparing the design with the TI LaunchPad schematic caught both (F-502).

## Toolkit issues found (for hardware-engineer)
- `doability_score.py` marks an area GO when all its findings are fixed, even when the area is not in `reviewed_areas`. Mechanical and compliance would then read GO before any CAD or certification plan exists. Suggested rule: an area is GO only if it is in `reviewed_areas`, or if it has an open finding that does not block.
- `bom_merge.py` reads `parts/` recursively. Moving superseded dossiers into `parts/superseded/` keeps the warnings away only if the script skips that folder. Today it warns "matches no BOM row" when they sit at the top level.
- `bom_merge.py --overwrite` replaces the BOM `notes` with the dossier `notes`. Notes written by `specs-engineer`, such as "suffix ok", are lost unless they also go in the dossier.

## Knowledge added
- F-501 (US coin-cell rule), F-502 (TI LaunchPad reference)
- E-501 (reading US regulations from an agent)
- L-004 (per-agent ID ranges for every ID kind), L-005 (look-alike assembler listings)
- D-018 to D-031

## Next
- `enclosure-engineer`: the shell, lid bayonet, membranes and sound port in build123d, from `hw/mech/constraints.md` (Q-PB-204).
- `pcb-engineer`: `board.json` from `architecture.md` §5, with the outline taken from the CAD.
- After both: `cost-and-sourcing`, `compliance-planner` and `prototype-roadmap`, then the next `doability-review` round.
