# Retro · 2026-11-08 · Final review and release evt0-a

## Request
Run the final doability review with its fix loop, then assemble the build package, ending READY TO BUILD (prototype).

## Done and verified
- Cost, roadmap and compliance refreshed for the final design — `cost_model.py` 0 warnings; `roadmap.py` 0 late, 6 buy-now; `compliance_matrix.py` 32 rows.
- Final review, round 3 of 3: READY TO BUILD (prototype), 0 fixes, 0 blockers, 15 prototype checks — `doability/score.json`.
- Release `hw/release/evt0-a/`: 47 files; `release_check.py` READY TO BUILD (prototype), 0 failures.

## Not verified
- Prices and stock are 2026-11-08 snapshots; re-check within 14 days of ordering.
- Screw torque 0.08 N·m and the door gasket compression are estimates; V-013 and V-014 confirm them.

## User interventions
- "tem que terminar logo isso ai… a gpu ta cara" → the stage ran with no further exploration.

## Mistakes and causes
- Order-step paths used stage names instead of release names — fixed, L-702.

## Knowledge added
- F-701, F-702, L-702, D-701…D-704

## Next
- product-presentation builds the deck. The user confirms D-703 (screw door) and D-601 (US first), sends RFQ-2 and RFQ-3, and places the orders in ORDER.md.
