# Roadmap — Pocket Beacon (fictional toolkit PoC)

Start 2026-11-16. Durations are `[estimate]` unless a stage says otherwise. Best case uses the short end of every range, worst case the long end.

**Finish:** Jul 2027 (best) to Jan 2028 (worst), 33–60 weeks.

**Critical path (worst case):** S0 → E0 → E1 → T1 → D0 → R1 → M1.

| Stage | Weeks | Start (best → worst) | End (best → worst) | Exit gate | Critical |
|---|---|---|---|---|---|
| **S0** Dev-kit bench | 3–6 | 2026-11-16 → 2026-11-16 | 2026-12-07 → 2026-12-28 | measured average current <= 20 uA with the chosen advertising (1285 ms) and 10 rings/month (power.md M1-M9); ring >= 75 dB(A) at 25 cm in 3x on a fresh cell | yes |
| **S1** Works-like / looks-like | 3–5 | 2026-11-23 → 2026-12-14 | 2026-12-14 → 2027-01-18 | printed enclosure closes on the real stack (10.0 mm limit); bayonet turns >= 90 deg with a coin; IPX7 pre-test in a bucket passes |  |
| **E0** EVT-0 build and bring-up | 5–8 | 2026-11-23 → 2026-12-14 | 2026-12-28 → 2027-02-08 | all rails up, BLE link at 10 m, current within 20 % of the bench, antenna matched in the printed shell | yes |
| **E1** EVT-1 revision + pre-scan | 4–7 | 2026-12-28 → 2027-02-08 | 2027-01-25 → 2027-03-29 | pre-scan passes FCC 15.247 / EN 300 328 margins; ESD +/-8 kV contact on the button and lid; engineering freeze | yes |
| **T1** Tooling T1 | 5–9 | 2027-01-25 → 2027-03-29 | 2027-03-01 → 2027-05-31 | T1 parts within drawing tolerances; bayonet torque and O-ring compression measured; cosmetic spec agreed for three colors | yes |
| **D0** DVT build (100 units) | 5–8 | 2027-03-01 → 2027-05-31 | 2027-04-05 → 2027-07-26 | IP67, 1.5 m drop (26 drops), -10 C ring, button life, UL 4200A pre-check passed; 12-month life confirmed from measured current | yes |
| **R0** US certification | 5–9 | 2027-04-05 → 2027-07-26 | 2027-05-10 → 2027-09-27 | FCC grant, UL 4200A test report, IP67 report, Bluetooth listing |  |
| **P0** PVT line validation | 3–6 | 2027-04-05 → 2027-07-26 | 2027-04-26 → 2027-09-06 | fixtures validated; first-pass yield >= 95 %; packaging with coin-cell warnings approved |  |
| **M0** Launch batch (100, US) | 3–5 | 2027-05-10 → 2027-09-27 | 2027-05-31 → 2027-11-01 | 100 units shipped to US customers |  |
| **R1** EU/UK/BR certification | 8–16 | 2027-04-05 → 2027-07-26 | 2027-05-31 → 2027-11-15 | EU DoC with reports, UK DoC, Anatel certificate | yes |
| **M1** 1k production run | 5–8 | 2027-05-31 → 2027-11-15 | 2027-07-05 → 2028-01-10 | first 1k lot shipped | yes |

## Milestones

| Milestone | After | Date (best → worst) |
|---|---|---|
| Engineering freeze | E1 | 2027-01-25 → 2027-03-29 |
| First legal sale (US) | R0 | 2027-05-10 → 2027-09-27 |
| First legal sale in Brazil | R1 | 2027-05-31 → 2027-11-15 |

## Long-lead purchases

Order date = start of the stage that needs the part (best case) minus the factory lead time. A part whose order date has passed but that is in stock now (`stock.on_hand` ≥ `qty_needed`) is a buy-now item, not a late one.

| Item | Lead time (weeks) | Needed by | Order by | Status |
|---|---|---|---|---|
| U1 CC2340R52E0RGER (TI 26 wk factory; buy 130 from LCSC/DigiKey stock now) | 26 | D0 (2027-03-01) | 2026-08-31 | in stock (9,278 @ LCSC 2026-11-08): buy 130 now; the factory lead time would be late |
| Q1 DMG2305UX-7 (40 wk at DigiKey; buy 130 of LCSC C150470 now) | 40 | D0 (2027-03-01) | 2026-05-25 | in stock (31,853 @ LCSC 2026-11-08): buy 130 now; the factory lead time would be late |
| Y2 ABS06-32.768KHZ-9-T (26 wk factory; 1,925 at LCSC) | 26 | D0 (2027-03-01) | 2026-08-31 | in stock (1,925 @ LCSC 2026-11-08): buy 130 now; the factory lead time would be late |
| D2 TPD1E10B06DPYR (26 wk factory; deep stock) | 26 | D0 (2027-03-01) | 2026-08-31 | in stock (86,161 @ DigiKey 2026-11-08): buy 130 now; the factory lead time would be late |
| ANT1 2450AT18A0100001E (18 wk factory; consign from DigiKey) | 18 | E0 (2026-11-23) | 2026-07-20 | in stock (160,791 @ DigiKey 2026-11-08): buy 130 now; the factory lead time would be late |
| LS1 CPT-9019A-SMT-TR (13 wk factory; consign from DigiKey) | 13 | E0 (2026-11-23) | 2026-08-24 | in stock (47,328 @ DigiKey 2026-11-08): buy 130 now; the factory lead time would be late |
| BT1 3034TR (14 wk factory; 644 at JLCPCB) | 14 | D0 (2027-03-01) | 2026-11-23 | ok |
