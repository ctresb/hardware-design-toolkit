# Research report · 2026-11-08 · power, mechanical and I/O parts

Scope: BT1, BAT1, Q1, D2, D1, R1, SW1 and the Tag-Connect footprint. Dossiers only: `bom.csv` was not edited. Notebook IDs used: F-201…F-210, E-201.

## Dossiers written (`hw/parts/`)

- `BAT-HLD-001-TR.md`
- `3034TR.md` (proposed replacement for BT1)
- `CR2032.md` (replaces `CR-2032/BN`, alias kept)
- `DMG2305UX-7.md`
- `TPD1E10B06DPYR.md`
- `LTST-C191KFKT.md`
- `RC0402FR-07680RL.md`
- `KMR221GLFS.md`
- `_tooling-TC2030-IDC-NL.md` (tooling, skipped by bom_merge)

`bom_merge.py --dry-run` parses all of them. Its conflicts are the expected differences against the specs-stage BOM values, for example `Production` vs `production`. Merge with `--overwrite`.

## Answers to the open items

1. **Q-PB-01 (BT1).** The TE drawing gives 22.9 × 21.1 × 4.2 mm (max 23.1 × 21.3 × 4.4 mm), not 23 × 21 × 4.3 mm (F-201).
   - LCSC stocks the bulk BAT-HLD-001 (C7501066, 1,681 pcs), not the -TR reel (12 pcs).
   - **Recommendation:** switch to Keystone **3034TR**. It is 21.2 × 23.1 × 4.1 mm, USD 0.2733 at 1k vs 0.475, has 121k + 316k at DigiKey, and is JLCPCB C5213768 (F-202).
   - BU2032SM-JJ-GTR is taller (5.33 mm).
   - An enclosure-held cell with spring contacts would save about 0.9 mm (holder 4.1 mm vs cell 3.2 mm). It needs molded contacts and lid pressure. Treat it as a v2 option [estimate].
2. **Q1.** DMG2305UX-7 has VGS(th) max −0.9 V and RDS(on) ≤ 200 mΩ at −1.8 V, so it is fully on at 2.0 V. It drops ≤ 3 mV at 15 mA (F-205).
   - **Supply:** DigiKey has 0 stock and a 40-week lead time. Build at JLCPCB with C150470 (31,853 pcs, Diodes brand).
   - **Second source:** AO3401A (JLCPCB basic C15127) after its datasheet is checked at VGS = −2.0 V.
   - An ideal-diode IC adds µA-class quiescent current: rejected.
3. **D2.** Leakage ≤ 100 nA at 5 V, worst case 0.4% of the cell per year (F-206). LCSC sells the TI part for USD 0.027–0.045, against DigiKey's USD 0.07–0.41.
4. **D1.** VF is about 1.75 V near 1 mA. Intensity is close to linear, so at R1 = 680 Ω it is about 3–6 mcd fresh and about 1 mcd at 2.0 V (F-207).
   - **Proposal for specs-engineer:** R1 = 330 Ω, or a high-drive GPIO.
5. **SW1.** 2.0 N ± 0.5 N, 200k cycles, 0.25 mm travel, 1.9 mm high, **IP40** (F-208). The IP67 seal must come from the membrane (Q-PB-06). The user feels the switch force plus the membrane force.
6. **CR2032.**
   - **Ordering:** order Panasonic `CR2032` (DigiKey 11-CR2032-ND, USD 0.40 / 0.236 at 800+). `CR-2032/BN` exists only on DigiKey Marketplace at USD 9.75 (F-210).
   - **Capacity:** 225 mAh at 0.2 mA. The curves give about 165 mAh at about 2.7 mA at 20 °C, and about 100 mAh at −10 °C (F-203).
   - **Internal resistance:** pulse capability ends at about 60 Ω for 15 mA and about 30 Ω for 30 mA (TI SWRA349, F-204).
   - **Consequence for battery-and-power:** the 14.2 mA 3× ring for 12 s needs internal resistance ≲ 75 Ω. That means a fresh cell at room temperature only. Choose the ring mode from VBAT measured under load (Q-PB-02).

## Proposed open questions (for hardware-engineer to add to `state.json`)

- **Q-PB-07** (specs-engineer): replace BT1 with Keystone 3034TR (footprint change for pcb-engineer).
- **Q-PB-08** (specs-engineer): R1 value, 680 Ω vs 330 Ω, after the LED window transmission is known.
- **Q-PB-09** (compliance-planner): name and verify the coin-cell child-safety rules for the US and EU markets: child-resistant compartment, warnings, packaging. The Energizer datasheet states the design rule: a tool or two independent, simultaneous movements.

## Lesson candidate (for the orchestrator to record as an L- entry)

- LCSC/JLCPCB list other makers' parts under the exact genuine MPN (F-209). Select assembler parts by LCSC number and check the brand.

## Sources that failed

| Source | Result |
|---|---|
| te.com DocumentDelivery, direct | 403 |
| ckswitches.com KMR2 PDF | HTML |
| liteon.com download | HTML |
| data.energizer.com/pdfs/cr2032.pdf | 404 |
| LCSC search pages | JavaScript only (the reader proxy worked for some) |
| DigiKey Keystone filter page | truncated |

E-201 records these failures.
