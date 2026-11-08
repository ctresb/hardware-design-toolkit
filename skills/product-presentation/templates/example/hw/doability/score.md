**Project:** Fixture Tag (fictional example)  
**Date:** 2026-11-08  
**Review round:** 1 of 3  
**Final verdict:** NOT READY  
**Next:** resolve the blockers listed below

| Area | Status | Critical | Major | Minor |
|---|---|---|---|---|
| Parts | GO | 0 | 0 | 0 |
| Electrical | GO | 0 | 0 | 0 |
| Power and battery | GO | 0 | 1 | 0 |
| PCB | GO | 0 | 0 | 1 |
| Mechanical | BLOCKED | 0 | 1 | 0 |
| Compliance | BLOCKED | 0 | 1 | 0 |
| Cost | GO | 0 | 0 | 1 |
| Schedule | GO | 0 | 0 | 0 |
| Claims vs reality | GO | 0 | 0 | 0 |

Counts are open findings. GO: nothing open blocks the area. FIX: the toolkit fixes it in the loop. BLOCKED: needs the user or the physical world.

### Build package

- [ ] Boards routed (no unrouted nets)
- [ ] DRC and ERC with 0 violations, schematic parity
- [ ] Fab files: Gerbers, drill, pick-and-place, assembly drawing
- [x] BOM in stock at the chosen assembler (or consigned parts bought)
- [ ] Enclosure STEP, ready for a print, machining or molding quote
- [ ] Assembly validator: 0 interpenetrations; tolerance study done
- [x] Bring-up and test plan written

### Production readiness

- [ ] Prototype measurements done and passed
- [ ] Quotes received for every NRE and recurring cost line
- [ ] Certifications planned with lab, cost and dates

### Blockers (need the user or the physical world)

- **F-003** [measurement] IP67 with a twist lid needs a compressed O-ring and a vented sound port → Use a 1.0 mm O-ring at 20–25 % compression and an acoustic membrane on the sound port; test IPX7 on SLA parts
- **F-004** [external] Coin-cell product must meet button-battery child-safety rules in the US → Lid needs a tool or two independent motions; warning label on the product and the box
- [external] Boards routed (no unrouted nets) → Complete the build-package item: Boards routed (no unrouted nets)
- [external] DRC and ERC with 0 violations, schematic parity → Complete the build-package item: DRC and ERC with 0 violations, schematic parity
- [external] Fab files: Gerbers, drill, pick-and-place, assembly drawing → Complete the build-package item: Fab files: Gerbers, drill, pick-and-place, assembly drawing
- [external] Enclosure STEP, ready for a print, machining or molding quote → Complete the build-package item: Enclosure STEP, ready for a print, machining or molding quote
- [external] Assembly validator: 0 interpenetrations; tolerance study done → Complete the build-package item: Assembly validator: 0 interpenetrations; tolerance study done

### Verify on the prototype

| ID | What | Method | Instrument | Pass criteria |
|---|---|---|---|---|
| V-001 | Average current while advertising | 10 min, release firmware, 3.0 V supply | power profiler, >= 100 kHz sampling | <= 15 µA average |
| V-002 | Ring loudness | free field, 25 cm, device hanging | class 2 sound level meter | >= 60 phon peak |
