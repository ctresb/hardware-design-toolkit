# Tolerances and stack-up

A collision-free CAD model shows nominal values only. Real parts vary. A 0.12 mm gap in CAD can be −0.1 mm in one unit out of twenty. Do a stack-up for every critical gap before you order tools or boards.

## Which gaps are critical

List them all in `hw/mech/tolerances.md`:

- every gap under 0.3 mm in the validated model;
- every spring, pogo pin or contact working height, which must stay inside its working range;
- battery pocket height and outline, including swelling;
- seal compression, for gaskets and adhesive bond lines;
- snap-fit engagement and press fits;
- connector mating height, and the board-to-board or board-to-flex distance;
- optical distances, for LED to wall and sensor to window.

## Method

1. Draw the chain of dimensions that sets the gap: wall → board standoff → board thickness → component height → … → gap.
2. For each link, write the nominal value and its tolerance, and give the source: a datasheet, the fab's capability page, or a molding standard.
3. **Worst case:** gap_min = nominal gap − Σ|tᵢ|. This is safe and pessimistic. Use it for safety-critical gaps (battery, seals) and for chains of 4 links or fewer.
4. **RSS (root sum of squares):** gap_min ≈ nominal gap − √(Σtᵢ²). This is realistic for long chains of independent, centered processes. Use it for cosmetic and non-critical gaps, and state it as a statistical estimate.
5. If the worst case is negative, change the design: add clearance, tighten one dominant tolerance, or remove a link. One option is to reference the part directly to the wall instead of through the board.

Example:

| Link | Nominal (mm) | Tol (mm) | Source |
|---|---|---|---|
| Inner wall to board top (boss height) | 1.50 | ±0.05 | molded, fine class `[estimate]` |
| Board thickness | 0.60 | ±0.06 | fab capability, ±10% `[estimate]` |
| Tallest component (max) | 0.95 | +0.00/−0.05 | datasheet max |
| Battery thickness | 3.50 | ±0.10 | cell spec `[assumption]` |
| Battery swelling allowance | 0.30 | — | 8–10% of thickness `[estimate]` |
| **Gap to the back wall** | 0.20 nominal | worst case −0.01 | **fails: add 0.05 or choose a thinner cell** |

## Typical tolerances to start with (replace with supplier values)

| Item | Typical tolerance | Note |
|---|---|---|
| General machined or molded dimensions, ISO 2768-1 "f" (fine) | ±0.05 (0.5–6 mm), ±0.1 (6–30 mm), ±0.15 (30–120 mm) | ISO 2768-1 table; "m" is about double |
| Molded plastic | per ISO 20457 / DIN 16742, by resin and size | ask the molder which class they hold |
| PCB thickness | ±10%, or ±0.1 mm on thin boards | fab capability page |
| PCB outline (routed) | ±0.1–0.2 mm | fab capability page |
| Flex thickness | ±0.03–0.05 mm | fab capability page; stiffeners add their own |
| Component height | use the datasheet **maximum** | distributor listings often show max > datasheet typical |
| Solder joint standoff | 0.02–0.1 mm | depends on stencil and package |
| PSA adhesive | ±10–20% of thickness | adhesive datasheet |
| Pouch cell thickness | ±0.1–0.2 mm, plus swelling | cell vendor; swelling grows with cycles and temperature |
| SMD spring working range | from the datasheet: free, working and minimum height | stay inside the working range at both extremes |

`[estimate: typical published values; replace each with the value of your supplier]`

## Battery-specific rules

- Model the cell with its **maximum** thickness and its sealed border (about 1 mm on each sealed edge, which holds no charge) and its tabs.
- Leave a swelling allowance above it. Never press a pouch cell between rigid walls with zero clearance.
- Keep sharp features (ribs, component corners, screw tips) away from the cell. A foam or PET layer between the cell and the board is common.

## What to write back

- `hw/mech/tolerances.md`: one table per critical gap, with the result (worst case, RSS) and an action.
- `hw/decisions.md`: every gap you accept with a statistical risk, and why.
- Open questions for suppliers: tolerances you assumed and need confirmed (molder, fab, cell vendor).
