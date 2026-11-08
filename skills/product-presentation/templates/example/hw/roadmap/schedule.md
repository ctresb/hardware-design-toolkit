# Roadmap — Fixture Tag (fictional example)

Start 2026-12-07. Durations are `[estimate]` unless a stage says otherwise. Best case uses the short end of every range, worst case the long end.

**Finish:** Jun 2027 (best) to Nov 2027 (worst), 26–47 weeks.

**Critical path (worst case):** S0 → E0 → T1 → D0 → R0 → M0.

| Stage | Weeks | Start (best → worst) | End (best → worst) | Exit gate | Critical |
|---|---|---|---|---|---|
| **S0** Dev-kit bench | 3–6 | 2026-12-07 → 2026-12-07 | 2026-12-28 → 2027-01-18 | idle current measured ≤ 18 µA; ring burst holds VBAT ≥ 2.2 V with the reservoir capacitor | yes |
| **E0** EVT-0 layout, fab, bring-up | 5–8 | 2026-12-28 → 2027-01-18 | 2027-02-01 → 2027-03-15 | all functions work on the bench; antenna matched in a printed enclosure | yes |
| **S1** Works-like / looks-like | 3–5 | 2026-12-28 → 2027-01-18 | 2027-01-18 → 2027-02-22 | printed enclosure seals IPX7 for 30 min; lid passes child-resistance check |  |
| **T1** Tooling T1 + iterations | 6–10 | 2027-02-01 → 2027-03-15 | 2027-03-15 → 2027-05-24 | T1 parts within tolerance; O-ring compression 20–25 % | yes |
| **D0** DVT build (100 units) | 5–8 | 2027-03-15 → 2027-05-24 | 2027-04-19 → 2027-07-19 | drop, IP67, ESD and battery-life tests passed; pre-scan passed | yes |
| **R0** Radio certification and SIG listing | 4–9 | 2027-04-19 → 2027-07-19 | 2027-05-17 → 2027-09-20 | FCC, CE/RED and UKCA paperwork complete; Bluetooth SIG listing | yes |
| **P0** PVT line validation | 3–6 | 2027-04-19 → 2027-07-19 | 2027-05-10 → 2027-08-30 | first-pass yield ≥ 97 % |  |
| **M0** Mass production, first lot | 3–6 | 2027-05-17 → 2027-09-20 | 2027-06-07 → 2027-11-01 | 1,000 units shipped | yes |

## Milestones

| Milestone | After | Date (best → worst) |
|---|---|---|
| Engineering freeze | E0 | 2027-02-01 → 2027-03-15 |
| First legal sale | R0 | 2027-05-17 → 2027-09-20 |

## Long-lead purchases

Order date = start of the stage that needs the part (best case) minus the lead time.

| Item | Lead time (weeks) | Needed by | Order by | Status |
|---|---|---|---|---|
| BLE SoC reel for DVT (14 wk factory lead) | 14 | D0 (2027-03-15) | 2026-12-07 | ok |
