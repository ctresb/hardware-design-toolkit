# Retro · 2026-11-08 · Discovery and specs (stages 0–2)

## Request
Run the toolkit on the Pocket Beacon PoC: initialize `hw/`, write the brief as product owner, then requirements, architecture and a BOM with real, orderable parts for every function, preferring JLCPCB/LCSC stock.

## Done and verified
- `hw/` initialized: `state.json`, `decisions.md`, `knowledge/`, `retros/`, `agents/`, `refs/`, `power/`, `parts/`.
- `hw/brief.md` v1 approved by the product-owner role (D-001); 15 seed requirements, 5 trade-offs, 4 defaults.
- `hw/requirements.md` issue 1: REQ-001…REQ-021.
- `hw/architecture.md` issue 1: 3 candidates compared, block diagram, rails, peak path, pin budget (10 of 12 GPIO), stack-up, first current estimate.
- `hw/bom.csv`: 23 rows. `bom_check.py hw/bom.csv --rails hw/power/rails.json` → 0 errors, 1 warning (sum of peaks on VBAT, explained in architecture §4).
- Datasheets read: TI SWRS272F (CC2340R5), Diodes DS41667 (PAM8904E), Murata VPPT-BUZJ083-D (PKMCS0909E4000-R1). F-001…F-006.

## Not verified
- 19 of 23 BOM rows are `assumption`: passives, crystals, LED, switch, FET, ESD diode, antenna, holder, cell. electronics-researcher verifies them next.
- BT1 holder footprint and height (Q-PB-01), U1 package height (Q-PB-05), RF match values (Q-PB-03), Y1 load-capacitance fit (Q-PB-04).
- All prices except where noted in facts; prices are left empty for the research stage.

## User interventions
- None in this stage (product-owner role).

## Mistakes and causes
- First requirement draft stated ≤ 18 µA average; the arithmetic (225 mAh × 0.85 ÷ 8,760 h) gives 21.8 µA. Corrected to ≤ 20 µA with self-discharge margin.
- DigiKey, Mouser and several maker sites blocked automated fetches; LCSC search through a reader proxy and direct datasheet PDFs worked. Some LCSC searches returned no rows (JS-rendered); those parts stay `assumption`.

## Knowledge added
- F-001…F-006, L-001…L-003, D-001…D-017

## Next
- electronics-researcher: dossiers for all 23 rows, riskiest first: BT1, Y1, ANT1, LS1 capacitance, Q1, D2 leakage; fill prices 1/10/100/1k/10k and LCSC numbers.
- battery-and-power: calibrated budget, CR2032 datasheet (capacity vs load, pulse behavior, cold), owns `hw/power/rails.json` from now on.
