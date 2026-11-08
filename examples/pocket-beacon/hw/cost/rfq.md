# Requests for quotation — Pocket Beacon

Date: 2026-11-08. Quantities quoted at 100, 1,000 and 10,000 unless stated. Each request closes one or more estimates in `hw/cost/manufacturing.json`. The list is ordered by how much the estimate moves the total per unit at 1,000 units (the target tier, REQ-019).

Send drawings and files, never only a description. Wait for the co-design outputs (`hw/pcb/`, `hw/mech/`) before sending requests 2–5.

| # | What | To whom | Estimate it replaces | Impact on total at 1k |
|---|---|---|---|---|
| 1 | Certification package US + EU + UK, one lab | 2 accredited labs with a TCB and EU notified-body links (for example TÜV SÜD, Element, Bureau Veritas, UL Solutions) | certification NRE $20.3k–46.5k (US) + $12.75k–82k (EU/UK/BR) | $33–129 per unit when spread over 1k; the widest range in the model |
| 2 | Final assembly, cell insertion, flashing, functional/RF/seal test, packing | the PCBA house's box-build line, 1–2 Shenzhen box-build EMS | $1.20–3.50 per unit | up to $2.30 of the $3.60 gap to the target |
| 3 | Enclosure molding: shell + lid, PC/ABS, three colors | Protolabs, Xometry, FirstMold, Fictiv | T1 tools $5k–12k + side action $0–3k; parts $0.80–2.50 per set; color changes $450–1,500 per run | $1.0–4.0 |
| 4 | Bare PCB + PCBA | JLCPCB (online order, quote from Gerbers), PCBWay | bare board $0.20–0.60 at 1k | $0.40 |
| 5 | Button/light membrane (translucent LSR or TPU) | Protolabs LSR, Xometry | tool $2k–6k; part $0.08–0.30 | $2–6 |
| 6 | Acoustic membrane vent, die-cut | SAATI (PFAS-free), Gore, Nitto | $0.15–0.60 per part; die $100–500 | $0.45 |
| 7 | Retail packaging with coin-cell warnings | 2 packaging printers | $0.35–1.00 per unit; die and artwork $200–800 | $0.65 |
| 8 | Brazil: Anatel OCD + importer of record | 2 Brazilian OCDs; a customs broker | Anatel $2.7k–7.3k; landed multiplier 1.6–2.0 | Brazil only |

---

## 1. Certification package (US first, then EU, UK, Brazil)

Send:
- `hw/compliance/traits.json`, the block diagram (`hw/architecture.md`), the BOM, and the antenna datasheet;
- the radio settings: BLE 1M PHY, 0 dBm, channels 37/38/39 advertising and data channels; a test-mode firmware that sets continuous TX and RX per channel;
- the coin-cell compartment description (coin-operated bayonet, ≥ 90°, D-026) and the product photos once DVT parts exist.

Ask for:
- FCC Part 15C (15.247 DTS) + 15B, the TCB grant and the FCC grantee code;
- UL 4200A-2023 test report (16 CFR 1263) and the warning-label review;
- EN 300 328, EN 301 489-1/-17, EN 62368-1 (with clause 4.8 for coin cells), EN 62479, EN 18031-1 and -2;
- UK declaration support (UKCA);
- IP67 test to IEC 60529 on 3 samples;
- a pre-scan day on EVT units;
- price per item, lead time, sample quantity, and the price for a retest after one board revision.

## 2. Final assembly and test

Send:
- the assembly guide and the exploded drawing (`hw/drawings/`);
- the test plan: ship-mode current ≤ 1 µA, active current profile, ring level at 25 cm, RF output, seal test method, and button force;
- the packaging spec and the warning text.

Ask for:
- price per unit at 100, 1,000 and 10,000;
- lot setup and MOQ;
- the fixture they need and its NRE;
- the yield they plan and the rework policy;
- the cell-handling and shipping capability for lithium-metal cells installed in equipment (UN3091, PI 970).

## 3. Enclosure molding (shell and lid)

Send:
- STEP of each part and the 2D drawing with the critical dimensions (bayonet, O-ring groove, membrane seat, keyring slot);
- the material: PC/ABS, UV-stabilized, in graphite, chalk white and a translucent smoke grade (REQ-020, REQ-021);
- the texture (fine matte) and the molded safety icons on the lid;
- annual volume 1k (year 1), 10k (year 2).

Ask for:
- a DFM report with mold flow, gate and knit-line positions;
- whether the keyring slot needs a side action;
- tool cost and lead time to T1, the cost of T2/T3 changes;
- price per part per tier, the color-change cost and the scrap assumption for the smoke grade.

## 4. Bare PCB and PCBA

Send the Gerbers, drill, stack-up (4 layers, 0.8 mm, ENIG, black mask), the JLCPCB BOM and CPL with LCSC numbers, and the consigned-parts list (LS1, ANT1).

Ask for the price at 10, 100, 1,000 and 10,000, the X-ray policy, and written confirmation of the black-mask web and the antenna-area copper rules.

## 5–7. Membranes and packaging

Send the CAD of each part and the quantities. Ask for samples, tool cost, part price per tier, material certificates (PFAS-free for the acoustic membrane; skin-safe for the button membrane).

## 8. Brazil

Ask 2 OCDs for the Anatel homologation quote with a local applicant (CNPJ), and a customs broker for the NCM, the import taxes and whether the product can clear before homologation (it cannot be sold before it).
