# Sourcing — Pocket Beacon

Date: 2026-11-08. Stock and lead times are snapshots from `hw/bom.csv` (dossiers in `hw/parts/`). Re-check them within 14 days of any order.

## Rules for this product

- **Buy from authorized channels only:** the manufacturer, DigiKey, Mouser, or LCSC/JLCPCB for parts JLCPCB places. Brokers and marketplace sellers are excluded, even for prototypes.
- **Select assembler parts by LCSC number, not by MPN.** LCSC lists look-alike parts from other makers under the genuine MPNs of Q1 (`DMG2305UX-7`) and D2 (`TPD1E10B06DPYR`) (F-209, L-005). Use `C150470` for Q1 and `C48260` for D2 only.
- **Order the standard cell.** Panasonic `CR2032` (DigiKey 11-CR2032-ND). `CR-2032/BN` appears only from a DigiKey Marketplace seller at USD 9.75 (F-210).
- **Consign LS1 and ANT1 to JLCPCB above 10 units.** LCSC stock is 13 (LS1) and 105 (ANT1); DigiKey holds 47k and 161k (D-029).
- **Attrition:** 5 % or ≥ 20 extra for 0402/0603 passives, as modeled in `manufacturing.json`.

## Parts

| Ref | MPN | Manufacturer | LCSC | Authorized channels | Factory lead time | Stock snapshot | Second source | Action |
|---|---|---|---|---|---|---|---|---|
| U1 | `CC2340R52E0RGER` | Texas Instruments | C20416850 | LCSC, DigiKey, TI | 26 wk | 9278 @ LCSC 2026-11-08 | CC2340R52N0RGER | buy EVT+DVT now (TI caps quantities; 26 wk factory) |
| U2 | `PAM8904EGPR` | Diodes Incorporated | C510550 | LCSC, DigiKey | stock item | 8981 @ LCSC 2026-11-08 | PAM8904EGPR-T |  |
| LS1 | `CPT-9019A-SMT-TR` | Same Sky (formerly CUI Devices) | C20181991 | DigiKey, LCSC | 13 wk | 47328 @ DigiKey 2026-11-08 | PKMCS0909E4000-R1 | buy now at DigiKey, consign (13 at LCSC) |
| D1 | `LTST-C191KFKT` | Lite-On | C160478 | DigiKey, LCSC | 14 wk | 183911 @ DigiKey 2026-11-08 | LTST-C191KRKT |  |
| R1 | `0402WGF3300TCE` | UNI-ROYAL (Uniroyal Electronics) | C25104 | LCSC, JLCPCB | stock item | 1950760 @ LCSC 2026-11-08 | RC0402FR-07330RL |  |
| R3 | `0402WGF1003TCE` | UNI-ROYAL (Uniroyal Electronics) | C25741 | LCSC, JLCPCB | stock item | 8779952 @ LCSC 2026-11-08 | RC0402FR-07100KL |  |
| SW1 | `KMR221GLFS` | C&K | C72443 | DigiKey, LCSC | 13 wk | 106572 @ DigiKey 2026-11-08 (+105000 factory) | KMR231GLFS |  |
| BT1 | `3034TR` | Keystone Electronics | C5213768 | DigiKey, JLCPCB | 14 wk | 121030 @ DigiKey 2026-11-08 (+316500 factory) | BAT-HLD-001-TR | buy now (644 at JLCPCB; DigiKey deep) |
| BAT1 | `CR2032` | Panasonic Energy | — | DigiKey | 22 wk | 2492586 @ DigiKey 2026-11-08 | Energizer CR2032 | buy per build, ground freight |
| Q1 | `DMG2305UX-7` | Diodes Incorporated | C150470 | DigiKey, LCSC | 40 wk | 31853 @ LCSC 2026-11-08 (C150470, Diodes brand) | DMG3415U-7 | buy LCSC C150470 now (DigiKey 0, 40 wk) |
| D2 | `TPD1E10B06DPYR` | Texas Instruments | C48260 | DigiKey, LCSC | 26 wk | 86161 @ DigiKey 2026-11-08 | TPD1E10B06DYAR |  |
| Y1 | `ABM11W-48.0000MHZ-7-B1U-T3` | Abracon | C1985532 | LCSC, DigiKey | 14 wk | 3758 @ LCSC 2026-11-08 | ABM11W-48.0000MHZ-7-D1X-T3 | buy EVT+DVT now (3,758 at LCSC only) |
| C16,C17 | `0402CG9R0C500NT` | FH (Guangdong Fenghua Advanced Technology) | C1580 | LCSC, JLCPCB | stock item | 204474 @ LCSC 2026-11-08 | 0402CG100J500NT |  |
| Y2 | `ABS06-32.768KHZ-9-T` | Abracon | C1985410 | LCSC, DigiKey | 26 wk | 1925 @ LCSC 2026-11-08 | ABS06-32.768KHZ-9-1-T | buy EVT+DVT now (1,925 at LCSC) |
| C13,C14 | `0402CG120J500NT` | FH (Guangdong Fenghua Advanced Technology) | C1547 | LCSC, JLCPCB | stock item | 1946183 @ LCSC 2026-11-08 | GRM1555C1H120JA01D |  |
| C1,C2,C15 | `CL10A226MQ8NRNC` | Samsung Electro-Mechanics | C59461 | JLCPCB, LCSC, DigiKey | stock item | 3843850 @ JLCPCB 2026-11-08 | CL21A226MAQNNNE |  |
| C3 | `CL10A106KP8NNNC` | Samsung Electro-Mechanics | C19702 | JLCPCB, LCSC, DigiKey | 61 wk | 10304806 @ JLCPCB 2026-11-08 | GRM188Z71A106KA73D |  |
| C4 | `CL10A106KP8NNNC` | Samsung Electro-Mechanics | C19702 | JLCPCB, LCSC, DigiKey | 61 wk | 10304806 @ JLCPCB 2026-11-08 | GRM188Z71A106KA73D |  |
| C19 | `CL05A105KA5NQNC` | Samsung Electro-Mechanics | C52923 | JLCPCB, LCSC | stock item | 11550069 @ JLCPCB 2026-11-08 | CL05A105KO5NNNC |  |
| L1 | `MLZ2012M100WT000` | TDK | C88173 | JLCPCB, LCSC, DigiKey | 15 wk | 45383 @ JLCPCB 2026-11-08 | LQM18DN100M70L |  |
| C5,C6,C20,C21,C22,C23 | `CL05B104KO5NNNC` | Samsung Electro-Mechanics | C1525 | JLCPCB, LCSC | stock item | 34285467 @ JLCPCB 2026-11-08 | GRM155R71C104KA88D |  |
| C7,C8 | `CL10A225KO8NNNC` | Samsung Electro-Mechanics | C23630 | JLCPCB, LCSC, DigiKey | 61 wk | 2324513 @ JLCPCB 2026-11-08 | CL10A225KA8NNNC |  |
| C9,C10 | `CL05A105KA5NQNC` | Samsung Electro-Mechanics | C52923 | JLCPCB, LCSC | stock item | 11550069 @ JLCPCB 2026-11-08 | CL05A105KO5NNNC |  |
| ANT1 | `2450AT18A0100001E` | Johanson Technology | C17430588 | DigiKey, LCSC | 18 wk | 160791 @ DigiKey 2026-11-08 | 2450AT18B100E | buy now at DigiKey, consign (105 at LCSC) |
| C11,C12 | `GJM1555C1H1R5BB01D` | Murata Electronics | C76900 | LCSC, JLCPCB | 17 wk | 83078 @ LCSC 2026-11-08 | GRM1555C1H1R5BA01D |  |
| L2 | `LQG15HS2N7B02D` | Murata Electronics | C162541 | LCSC, JLCPCB | stock item | 11865 @ LCSC 2026-11-08 | LQG15HS2N7S02D |  |
| R2 | `0402WGF0000TCE` | UNI-ROYAL (Uniroyal Electronics) | C17168 | LCSC, JLCPCB | stock item | 17009964 @ LCSC 2026-11-08 | RC0402JR-070RL |  |

"Factory lead time" is the manufacturer's quoted lead time at DigiKey; it matters only when stock runs out. The MLCCs show 61 weeks factory lead time but have millions in stock at JLCPCB, so they are not a risk.

## Buy now (before EVT layout freeze)

| Item | Quantity | Why | Where |
|---|---|---|---|
| U1 `CC2340R52E0RGER` | 130 (EVT 10 + DVT 100 + spares) | TI caps purchase quantities; 26 wk factory lead time | LCSC C20416850 (9,278) or DigiKey (3,859) |
| LS1 `CPT-9019A-SMT-TR` | 130 | 13 at LCSC | DigiKey, consign to JLCPCB |
| ANT1 `2450AT18A0100001E` | 130 | 105 at LCSC | DigiKey, consign to JLCPCB |
| Y1 `ABM11W-48.0000MHZ-7-B1U-T3` | 130 | single LCSC lot of 3,758; not on TI's validated list | LCSC C1985532 |
| Y2 `ABS06-32.768KHZ-9-T` | 130 | 1,925 at LCSC | LCSC C1985410 |
| Q1 `DMG2305UX-7` | 130 | DigiKey 0 stock, 40 wk | LCSC C150470 (Diodes brand) |
| BT1 `3034TR` | 130 | 644 at JLCPCB | JLCPCB C5213768, or DigiKey and consign |

## Processes

| Process | Tier | Vendors (established) | Notes |
|---|---|---|---|
| Bare PCB + PCBA | 10–1k | JLCPCB (primary), PCBWay, Seeed Fusion | 4-layer 0.8 mm ENIG black mask; Standard PCBA for two-sided assembly; panel ≥ 70 × 70 mm |
| PCBA | 10k | JLCPCB, or a box-build EMS (see below) | ask for sampled X-ray at 10k |
| Prototype enclosure (SLA/MJF) | 1–10 | Protolabs, Xometry, JLC3DP, in-house Formlabs | graphite and chalk in MJF/SLA; smoke in clear resin, tinted |
| Rapid aluminum tools (T1) | 100–1k | Protolabs, Xometry, Fictiv, FirstMold | PC/ABS, three colors from one tool; DFM with mold-flow |
| Steel tools | 10k | FirstMold, HLH Rapid, Star Rapid, RapidDirect | hardened steel, 1–2 cavities |
| Button/light membrane | 100–10k | silicone/LSR molders via Protolabs (LSR), Xometry | translucent, light-diffusing grade |
| Acoustic membrane | 10–10k | Gore (direct), SAATI, Nitto TEMISH, Donaldson | prefer a PFAS-free mesh (SAATI) |
| O-ring | all | Parker, Trelleborg, Apple Rubber (catalog sizes) | size from the co-design CAD |
| Coin cells | all | Panasonic, Energizer, Murata via DigiKey/Mouser | ship installed, ground freight; UN 38.3 summary from the maker |
| Packaging | 100–10k | packaging printers with dielines and FSC board | carry the coin-cell warnings (compliance.md) |
| Final assembly and test | 100–10k | the PCBA house's box-build line, or a Shenzhen box-build EMS | quote with the test plan (current, ring, RF, seal) |
