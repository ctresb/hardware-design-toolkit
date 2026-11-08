# Doability review: Pocket Beacon (final pass)

**Date:** 2026-11-08 · **Round:** 3 of 3 · **Owner:** doability-review · **Verdict:** READY TO BUILD (prototype) · **Maturity:** EVT-0 release candidate

## Short answer

Pocket Beacon is ready to build as a 10-unit EVT-0 prototype. Every part is orderable today at JLCPCB/LCSC or an authorized distributor. The 4-layer 0.6 mm board is routed with DRC 0, ERC 0 and schematic parity. The enclosure STEP passes DFM with 0 errors, and the assembly validator reports 0 interpenetrations. What remains is measurement on the built units (V-001…V-015), two quotes that decide whether the $12 target at 1k holds, and one purchase of long-lead parts. None of these needs a design change before EVT-0.

Two decisions made in the product-owner role need the user's confirmation before DVT tooling:
- **Door:** a screw-secured cell door (D-511, D-703) instead of the coin bayonet;
- **Market order:** the US launch batch comes first (D-601).

## What the final round changed

- **Cost model:** refreshed with the routed board (126 pads, 26 part types, 2 X-ray parts) and the final enclosure (4 printed parts, 2 screws, 2 gaskets) (FR-12). Recurring cost at 1k is $8.89–17.1.
- **Door gasket:** 0.35 mm free (D-701, FR-02), so compression is 17–51 % across tolerance.
- **Sounder port gasket:** 0.8 mm extra-soft PU foam (D-702, FR-03).
- **Compliance:** compliance.md rewritten for the screw door (FR-08). The marking plan is D-704 (FR-09).
- **Roadmap:** long-lead items now carry stock data. 0 are late and 6 are "buy now from stock" (FR-11).
- **Prototype checks:** six added (V-010…V-015) for the port alignment, the cell access, the SW1 links, the IPX7 seal, the UL 4200A securement and the button force.

## Scored result

| Area | Status | Critical | Major | Minor |
|---|---|---|---|---|
| Parts | GO | 0 | 0 | 1 |
| Electrical | GO | 0 | 0 | 2 |
| Power and battery | GO | 0 | 0 | 1 |
| PCB | GO | 0 | 0 | 1 |
| Mechanical | GO | 0 | 0 | 2 |
| Compliance | GO | 0 | 0 | 0 |
| Cost | GO | 0 | 0 | 1 |
| Schedule | GO | 0 | 0 | 1 |
| Claims vs reality | GO | 0 | 0 | 0 |

Counts are open findings. GO: nothing open blocks the area. FIX: the toolkit fixes it in the loop. BLOCKED: needs the user or the physical world.

### Build package

- [x] Boards routed (no unrouted nets)
- [x] DRC and ERC with 0 violations, schematic parity
- [x] Fab files: Gerbers, drill, pick-and-place, assembly drawing
- [x] BOM in stock at the chosen assembler (or consigned parts bought)
- [x] Enclosure STEP, ready for a print, machining or molding quote
- [x] Assembly validator: 0 interpenetrations; tolerance study done
- [x] Bring-up and test plan written

### Production readiness

- [ ] Prototype measurements done and passed
- [ ] Quotes received for every NRE and recurring cost line
- [x] Certifications planned with lab, cost and dates

## Open items that do not block EVT-0

| ID | Area | Item | Action |
|---|---|---|---|
| FR-10 | cost | $12 at 1k not proven ($8.89–17.1) | RFQ-2 (molder) and RFQ-3 (box-build) in cost/rfq.md, two vendors each |
| FR-11 | schedule | 6 long-lead parts | buy 130 each now from stock (purchase) |
| PR-14…PR-17, FR-01, FR-05…FR-07 | parts, electrical, pcb, mechanical | values and fits that only hardware can confirm | V-005…V-007, V-010…V-015 |
| PR-18 | claims | the 13.1-month calibrated life has a thin margin over 12 months | V-001 |

## Before production

| Item | Replaces | How | Owner | Needed before |
|---|---|---|---|---|
| V-001 to V-009 passed | power, RF and acoustic estimates | EVT bench | hardware-engineer | DVT |
| UL 4200A-2023 test record and certificate of conformity | the REQ-015 paper design | test lab or in-house per the standard; third-party testing is required only for children's products (F-501) | compliance-planner | US sale |
| Acoustic membrane quote and loss data | the sound-port estimate | RFQ to the membrane vendor | cost-and-sourcing | enclosure freeze |
| Radio certification plan (FCC, RED, UKCA, Anatel) | — | compliance-planner stage | compliance-planner | DVT |

## Risk register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| 1 | Advertising event charge above 12 µC drops battery life below 12 months | medium | high | 2000 ms fallback interval (V-002) | battery-and-power |
| 2 | Sound-port membrane loss takes loudness below 75 dB(A) | medium | medium | size the port from the vendor curve; V-004 | enclosure-engineer |
| 3 | Antenna detuned by the cell retainer and the keys | medium | medium | 5-slot match, ≥ 1 mm spacing from the retainer; V-005 | pcb-engineer |
| 4 | Lid fails a UL 4200A abuse test (torque, drop) | medium | high | coin-slot bayonet with a detent; test early on SLA prints | enclosure-engineer |
| 5 | CC2340 purchases capped at the TI store; 26-week lead time | low | medium | buy for the whole first year at the first order; 9,278 at LCSC | cost-and-sourcing |
| 6 | Y2 fails to start at cold with a 10 % ESR margin | low | medium | V-007; LFOSC fallback | specs-engineer |
| 7 | IP67 seal leaks after 10 lid cycles | medium | high | O-ring face seal with a compression stop; IP test on DVT | enclosure-engineer |
| 8 | Stack exceeds 10 mm once the CAD walls are drawn | low | medium | CAD stack-up check in stage 6 | enclosure-engineer |

## Verify on the prototype

The full table with method, instrument and pass criteria is in `doability/score.md` and `score.json` (`prototype_checks`). The release copies it to `test/verify-on-prototype.md`.

## Sources

All read 2026-11-08:

- TI SWRS272F rev F (CC2340R5): Figure 6-2, Tables 6-1 and 6-10, §7.3 to §7.20, §8;
- TI SWRC397: LP-EM-CC2340R53 BOM and schematic;
- eCFR 16 CFR part 1263;
- CPSC final rule 88 FR 65274, Table 3;
- the JLCPCB parts API, for stock, brand and library type of every LCSC number in the BOM;
- the dossiers in `hw/parts/` and the research reports in `hw/agents/`, each with its own sources.

The paper pass (stages 3–5) is preserved in git history and summarized in "What the fix loop changed" of round 1 (`retros/`).
