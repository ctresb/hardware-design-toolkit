# Requirements: Pocket Beacon

Issue: 2 · Date: 2026-11-08 · Source: hw/brief.md (version 1, approved) · Changes in issue 2: REQ-005, REQ-006, REQ-009, REQ-015 revised after research (D-022 to D-028)

## Summary

Pocket Beacon is a keyring item finder. It advertises over BLE for at least 12 months on one user-replaceable CR2032 and rings loudly when the phone asks. Three numbers dominate the design:

- the average current, which must stay ≤ 20 µA for 12 months on a 225 mAh cell (REQ-002);
- the ring loudness on an aged coin cell (REQ-006);
- the envelope of ≤ 32 × 32 × 10.0 mm (REQ-001).

## Requirements

| ID | Category | Requirement | Target | Limit | Priority | Source | Verified by |
|---|---|---|---|---|---|---|---|
| REQ-001 | Size | Outer envelope | 32 × 32 × 8.5 mm | ≤ 32 × 32 × 10.0 mm | must | brief S-02, D-007 | CAD measurement |
| REQ-002 | Power | Battery life on one CR2032, 20 °C, standby advertising + 10 rings of 12 s per month | 18 months | ≥ 12 months (average current ≤ 20 µA: 225 mAh × 0.85 usable ÷ 8,760 h = 21.8 µA, less about 1 %/year self-discharge) | must | brief S-01 | current profile on EVT (power profiler), life calculation |
| REQ-003 | Power | Shelf life in ship mode with cell installed | 2 years, ≤ 10 % capacity lost | ship-mode current ≤ 1 µA | should | brief S-15 | bench test |
| REQ-004 | Power | Operation down to end-of-life cell voltage | full function at VBAT ≥ 2.2 V under load | radio and LED work at 2.0 V | must | brief S-06 | bench supply sweep |
| REQ-005 | Power | Peak current drawn from the cell | ≤ 15 mA during ring (3× only on a healthy cell, D-028), ≤ 8 mA during TX | ≤ 20 mA; TX bursts during a ring are fed by ≥ 27 µF effective bulk (D-022) | must | coin-cell pulse capability (F-204) | current profile on EVT (V-002) |
| REQ-006 | Output | Ring loudness, 4 kHz, at 25 cm, free field | ≥ 75 dB(A) in 3× mode on a fresh cell | ≥ 65 dB(A) in 2× mode on a cell at 2.4 V under load | must | brief S-04, D-028 | sound level meter, class 2, on EVT (V-004) |
| REQ-007 | Output | Ring duration | 12 s per command, stops on button press | 5 s to 30 s | must | brief §2 | firmware test |
| REQ-008 | Indication | Status light visible through the membrane | readable at 500 lx at 1 m | — | should | brief S-08 | prototype review |
| REQ-009 | Input | One button through a sealed membrane | total press force 2.3–3.3 N (switch 2.0 ± 0.5 N + membrane 0.3–0.8 N), ≥ 100,000 cycles | 2.0–3.5 N; ≥ 50,000 cycles | must | brief §4, D-027 | force gauge on the assembled shell + cycle test on DVT |
| REQ-010 | Connectivity | BLE link to phone | 10 m indoor through a bag | ≥ 5 m | must | brief S-05 | range test on EVT |
| REQ-011 | Connectivity | Firmware update | over the air from the app | — | must | D-011 | firmware test |
| REQ-012 | Environment | Ingress | IP67 (1 m, 30 min) | IPX7 | must | brief S-09 | lab test IEC 60529 on DVT |
| REQ-013 | Environment | Drop | 1.5 m on concrete, 26 drops | no functional loss, cell retained | must | brief S-10 | drop test on DVT |
| REQ-014 | Environment | Temperature | −10 °C to +45 °C use; −20 °C to +60 °C storage | ring works at −10 °C on a cell at 50 % | must | brief S-06 | chamber test on DVT |
| REQ-015 | Safety | Coin-cell compartment per 16 CFR 1263 / ANSI/UL 4200A-2023 (F-501) | lid opens only with a coin or flat screwdriver, ≥ 90° bayonet rotation (option 1, D-026); cell stays inaccessible after preconditioning (7 h ≥ 70 °C, 10 open/close cycles) and abuse tests (10 × 1 m drops, 3 × 2 J impact, 330 N crush, ≥ 136 N compression, ≥ 0.50 N·m torque, ≥ 72 N tension, probe 11 at 50–60 N); warnings on packaging and literature, safety-alert and ingestion icons molded on the lid | all UL 4200A-2023 §5–§7 clauses for replaceable cells; option-1 minimum torque and spin angle as written in the standard (to read) | must | brief S-14, F-501 | design review now; UL 4200A test report on DVT (compliance-planner) |
| REQ-016 | Mechanical | Mass with cell | 9 g | ≤ 10 g | should | brief S-03 | scale |
| REQ-017 | Mechanical | Keyring slot | survives 50 N pull | ≥ 30 N | must | brief §4 | pull test on DVT |
| REQ-018 | Regulatory | Markets | US, EU, UK, BR | — | must | brief S-12 | compliance plan |
| REQ-019 | Cost | Recurring cost at 1k units | ≤ USD 12 | ≤ USD 15 | should | brief S-11 | cost model |
| REQ-020 | Appearance | Variants | graphite, chalk white, smoke translucent; one mold | — | should | brief §4, D-006 | molding samples |
| REQ-021 | Appearance | Smoke variant UV stability | no visible yellowing after 1 year outdoors | — | should | brief S-13 | resin datasheet + UV test |

## Functions

| Function | Requirements | Implementation (see `hw/architecture.md`) |
|---|---|---|
| Compute and connect | REQ-002, REQ-010, REQ-011 | BLE SoC with integrated DC/DC, chip antenna |
| Power | REQ-002, REQ-003, REQ-004, REQ-005 | CR2032 in SMD holder, P-FET reverse protection, bulk capacitance |
| Ring | REQ-006, REQ-007 | piezo sounder + charge-pump driver |
| Indicate | REQ-008 | amber LED |
| Input | REQ-009 | tactile switch under a membrane |
| Protect | REQ-004, REQ-012 | ESD diode at the cell holder |

## Conflicts and open questions

- **REQ-001 vs the stack-up.** The 8.5 mm target cannot be met with an off-the-shelf holder: the stack sums to 9.5–9.9 mm (architecture §6). This was decided in D-007: limit 10.0 mm in v1, with a custom contact design for v2.
- **REQ-006 vs REQ-005.** The 3× drive mode draws 14.2 mA (datasheet typical). A cold or aged CR2032 sags under that load: at −10 °C and 80 % used, 3× pulls VBAT to about 1.0 V (E-402). Resolved by the adaptive ring rule (D-028): start in 2×, step up to 3× only if VBAT ≥ 2.7 V under load, drop to 1× with a low-battery report below 2.3 V. The loudness limit is stated for 2× at a 2.4 V loaded cell.

## Out of scope

- Accelerometer and "moved" alerts (D-008).
- Phone-maker finder networks in v1 (D-003).
- Rechargeable cell and charging (D-002).
