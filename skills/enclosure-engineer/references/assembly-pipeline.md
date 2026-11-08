# Assembly pipeline: the build order that stops regressions

## The problem it solves

A detailed assembly has dozens of steps that each move geometry:

- placing components;
- mating connectors;
- fitting springs;
- cutting pockets;
- shrinking membranes into their seats;
- fitting a flex over components;
- fitting the battery;
- adding solder fillets.

Run in the wrong order, a later step moves something that an earlier step had fitted against. The plug of a connector leaves its socket when the board under it is pushed. Solder floats when the pad moves after the solder was made. The result is a loop in which each fix breaks something else.

Professional mechanical teams avoid this with **constraints and a fixed regeneration order**: the feature tree in a CAD tool. The scripted equivalent follows.

## The order

| # | Step | Moves | Depends on |
|---|---|---|---|
| 1 | Fixed structure: shell, lid, internal ribs and bosses | — | brief, stack-up |
| 2 | Rigid boards at their nominal heights | boards | 1 |
| 3 | Components on boards: from the PCB export, positioned by the board | components | 2 |
| 4 | Mated connectors: plug placed into its receptacle, then **fixed** | plug and the flex end under it | 3 |
| 5 | Springs and contacts scaled or positioned to their working height against the mating surface | springs | 1, 3 |
| 6 | Pockets in fixed parts for components that must protrude into them (full component height + clearance) | fixed parts (cut) | 3 |
| 7 | Membranes, gaskets, adhesives seated (slightly smaller than their seats) | soft parts | 1, 6 |
| 8 | Free-space fit of movable bodies: flex circuits, loose sub-assemblies | movable bodies | 1–7 |
| 9 | Battery fit (often last: it takes the leftover volume, with its swelling allowance) | battery | 1–8 |
| 10 | Details that sit on final surfaces: solder fillets on the final pad surface, markings, labels | details | 1–9 |
| 11 | Validate (`validate_assembly.py`) | — | 1–10 |
| 12 | Freeze: save `assembly_golden.blend` | — | 11 passes |

After step 12:

- **Appearance-only changes** (materials, textures, lights, cameras, color variants) load the golden file. They change shaders and objects that are not geometry. Each iteration takes seconds, not a full rebuild.
- **Geometry changes** go back to the step that owns them and re-run everything after it.

## Rules

1. **A step changes only what it owns.** The battery fit never moves a board. If the battery does not fit, the step reports it and stops.
2. **Mates are constraints, not optimization variables.** Once a plug is in its socket, neither the plug nor the material under it is moved by a later fit. Pass them as `fixed` to the fitting step.
3. **Details come last.** Solder, glue beads and labels sit on surfaces that must be final. Building them earlier means rebuilding them, or leaving them floating.
4. **Validate the frozen, unposed assembly.** For a lifestyle shot, the whole root is moved or rotated as one rigid transform, after validation.
5. **Report physical limits as findings.** "The battery must rise 0.4 mm and the stack has 0.1 mm" is a design decision for the user: a thinner cell, less capacity, or a thicker product. It is not a number to tweak silently.
6. **No whitelists.** A known collision in a simplified vendor model is solved with the vendor's real model or with the corrected dimensions. If a temporary exception is unavoidable for an internal review, it is written in `hw/decisions.md` with an owner and a removal date, and it never reaches a deliverable.

## When fixes regress

Signs:

- the same part fails again after you fixed it;
- two parameters are tuned back and forth;
- a fix in step N changes the result of step N−2.

What to do:

1. Stop editing.
2. Write down which step moved what (from the logs).
3. Find the dependency that points backwards.
4. Change the order or turn the backward dependency into a fixed constraint.
5. Rebuild from step 1 and validate.

Tell the user what you changed in the process, not only in the numbers.
