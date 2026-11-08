# BOM merge report

bom_merge: 27 BOM rows, 25 dossiers, 0 errors, 20 warnings, 48 changes

## Errors and conflicts (0)

- none

## Warnings (20)

- **BOM LS1 (CPT-9019A-SMT-TR)**: supply_rail_v empty: rail not checked against the supply range
- **BOM R1 (0402WGF3300TCE)**: supply_rail_v empty: rail not checked against the supply range
- **BOM R3 (0402WGF1003TCE)**: supply_rail_v empty: rail not checked against the supply range
- **BOM SW1 (KMR221GLFS)**: supply_rail_v empty: rail not checked against the supply range
- **BOM BT1 (3034TR)**: supply_rail_v empty: rail not checked against the supply range
- **BOM BAT1 (CR2032)**: supply_rail_v empty: rail not checked against the supply range
- **BOM Q1 (DMG2305UX-7)**: supply_rail_v empty: rail not checked against the supply range
- **BOM Y1 (ABM11W-48.0000MHZ-7-B1U-T3)**: supply_rail_v empty: rail not checked against the supply range
- **BOM C16,C17 (0402CG9R0C500NT)**: supply_rail_v empty: rail not checked against the supply range
- **BOM Y2 (ABS06-32.768KHZ-9-T)**: supply_rail_v empty: rail not checked against the supply range
- **BOM C13,C14 (0402CG120J500NT)**: supply_rail_v empty: rail not checked against the supply range
- **BOM C4 (CL10A106KP8NNNC)**: supply_rail_v empty: rail not checked against the supply range
- **BOM C19 (CL05A105KA5NQNC)**: supply_rail_v empty: rail not checked against the supply range
- **BOM L1 (MLZ2012M100WT000)**: supply_rail_v empty: rail not checked against the supply range
- **BOM C7,C8 (CL10A225KO8NNNC)**: supply_rail_v empty: rail not checked against the supply range
- **BOM C9,C10 (CL05A105KA5NQNC)**: supply_rail_v empty: rail not checked against the supply range
- **BOM ANT1 (2450AT18A0100001E)**: supply_rail_v empty: rail not checked against the supply range
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: supply_rail_v empty: rail not checked against the supply range
- **BOM L2 (LQG15HS2N7B02D)**: supply_rail_v empty: rail not checked against the supply range
- **BOM R2 (0402WGF0000TCE)**: supply_rail_v empty: rail not checked against the supply range

## Changes written (48)

- **BOM R3 (0402WGF1003TCE)**: size_max_mm = `1.1x0.6x0.4`
- **BOM R3 (0402WGF1003TCE)**: key_specs = `r=100k; tol=1%; p_w=0.0625; jlc=basic`
- **BOM R3 (0402WGF1003TCE)**: distributors = `LCSC=https://www.lcsc.com/product-detail/C25741.html; JLCPCB=https://jlcpcb.com/partdetail/C25741`
- **BOM R3 (0402WGF1003TCE)**: price_1 = `0.0012`
- **BOM R3 (0402WGF1003TCE)**: price_10 = `0.0012`
- **BOM R3 (0402WGF1003TCE)**: price_100 = `0.0012`
- **BOM R3 (0402WGF1003TCE)**: price_1k = `0.001`
- **BOM R3 (0402WGF1003TCE)**: price_10k = `0.0007`
- **BOM R3 (0402WGF1003TCE)**: stock_snapshot = `8779952 @ LCSC 2026-11-08`
- **BOM R3 (0402WGF1003TCE)**: alternatives = `RC0402FR-07100KL (Yageo, drop-in)`
- **BOM R3 (0402WGF1003TCE)**: source_date = `2026-11-08`
- **BOM R3 (0402WGF1003TCE)**: notes = `Reset pull-up as on the TI LaunchPad (R1 100k + C92 0.1 uF) (D-031)`
- **BOM C19 (CL05A105KA5NQNC)**: package: `0402` -> `0402 (1005 metric) MLCC` (overwrite)
- **BOM C19 (CL05A105KA5NQNC)**: size_max_mm = `1.10x0.60x0.60`
- **BOM C19 (CL05A105KA5NQNC)**: key_specs = `c_uf=1; v=25; dielectric=X5R; c_eff_3v3_uf=0.73; c_eff_6v6_uf=0.43`
- **BOM C19 (CL05A105KA5NQNC)**: distributors = `JLCPCB=basic part C52923; LCSC=https://www.lcsc.com/product-detail/C52923.html`
- **BOM C19 (CL05A105KA5NQNC)**: price_1 = `0.0058`
- **BOM C19 (CL05A105KA5NQNC)**: price_10 = `0.0058`
- **BOM C19 (CL05A105KA5NQNC)**: price_100 = `0.0058`
- **BOM C19 (CL05A105KA5NQNC)**: price_1k = `0.0044`
- **BOM C19 (CL05A105KA5NQNC)**: price_10k = `0.0034`
- **BOM C19 (CL05A105KA5NQNC)**: stock_snapshot = `11550069 @ JLCPCB 2026-11-08; 3163100 @ LCSC 2026-11-08`
- **BOM C19 (CL05A105KA5NQNC)**: alternatives = `CL05A105KO5NNNC (drop-in, 16 V, half the effective capacitance at 6.6 V); CL10A105KB8NNNC (needs change: 0603, 50 V)`
- **BOM C19 (CL05A105KA5NQNC)**: source_date = `2026-11-08`
- **BOM C19 (CL05A105KA5NQNC)**: notes = `Not yet in the BOM MPN column (only its LCSC number is): specs-engineer decides Q-PB-08.. suffix ok: Samsung last letter C = 7-inch paper tape`
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: manufacturer: `Murata` -> `Murata Electronics` (overwrite)
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: key_specs: `c_pf=1.0; tol_pf=0.1; v=50; dielectric=C0G; high_q=yes` -> `c_pf=1.5; tol=0.1pF; dielectric=C0G; high_q=yes; jlc=extended` (overwrite)
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: distributors: `LCSC=https://www.lcsc.com/product-detail/C76898.html; DigiKey=https://www.digikey.com/en/products/result?keywords=GJM1555C1H1R0BB01D` -> `LCSC=https://www.lcsc.com/product-detail/C76900.html; JLCPCB=https://jlcpcb.com/partdetail/C76900` (overwrite)
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: price_1: `0.12` -> `0.0347` (overwrite)
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: price_10: `0.066` -> `0.0347` (overwrite)
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: price_100: `0.0396` -> `0.0283` (overwrite)
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: price_1k: `0.0251` -> `0.0226` (overwrite)
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: price_10k: `0.0164` -> `0.0202` (overwrite)
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: stock_snapshot: `196420 @ LCSC 2026-11-08; 368849 @ DigiKey 2026-11-08` -> `83078 @ LCSC 2026-11-08` (overwrite)
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: alternatives: `GRM1555C1H1R0BA01D (Murata standard Q, drop-in)` -> `GRM1555C1H1R5BA01D (Murata standard Q); GJM1555C1H1R2BB01D (1.2 pF, tuning step)` (overwrite)
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: evidence: `verified` -> `estimate` (overwrite)
- **BOM C11,C12 (GJM1555C1H1R5BB01D)**: notes: `Values are starting points for VNA tuning. suffix ok: Murata D = 180 mm paper reel` -> `Start value from TI's 1.5 pF filter capacitors (C33, C34 on the LaunchPad); final value set by VNA tuning (V-005, D-030). suffix ok: Murata D = 180 mm paper reel` (overwrite)
- **BOM L2 (LQG15HS2N7B02D)**: manufacturer: `Murata` -> `Murata Electronics` (overwrite)
- **BOM L2 (LQG15HS2N7B02D)**: key_specs: `l_nh=2.2; tol_nh=0.1; q=8 at 100MHz; type=multilayer` -> `l_nh=2.7; tol=0.1nH; srf_ghz=6; rdc_mohm=120; jlc=extended` (overwrite)
- **BOM L2 (LQG15HS2N7B02D)**: distributors: `LCSC=https://www.lcsc.com/product-detail/C162540.html; DigiKey=https://www.digikey.com/en/products/result?keywords=LQG15HS2N2B02D` -> `LCSC=https://www.lcsc.com/product-detail/C162541.html; JLCPCB=https://jlcpcb.com/partdetail/C162541` (overwrite)
- **BOM L2 (LQG15HS2N7B02D)**: price_1: `0.10` -> `0.062` (overwrite)
- **BOM L2 (LQG15HS2N7B02D)**: price_10: `0.0399` -> `0.062` (overwrite)
- **BOM L2 (LQG15HS2N7B02D)**: price_100: `0.0319` -> `0.0532` (overwrite)
- **BOM L2 (LQG15HS2N7B02D)**: price_1k: `0.0319` -> `0.0454` (overwrite)
- **BOM L2 (LQG15HS2N7B02D)**: price_10k: `0.0218` -> `0.0406` (overwrite)
- **BOM L2 (LQG15HS2N7B02D)**: stock_snapshot: `31900 @ LCSC 2026-11-08; 591632 @ DigiKey 2026-11-08` -> `11865 @ LCSC 2026-11-08` (overwrite)
- **BOM L2 (LQG15HS2N7B02D)**: alternatives: `LQW15AN2N2B80D (drop-in, wirewound, higher Q)` -> `LQG15HS2N7S02D (Murata, ±0.3 nH, C77108, 218616 stock); LQP15MN2N7B02D (Murata thin film, 0 stock)` (overwrite)
- **BOM L2 (LQG15HS2N7B02D)**: notes: `Final value comes from VNA tuning: keep a kit of LQG15HS 1.0-10 nH and GJM 0.5-3 pF for EVT. suffix ok: Murata D = 180 mm paper reel` -> `Start value from TI's 2.8 nH filter inductor (0201 on the LaunchPad); final value set by VNA tuning on EVT (V-005, D-030). suffix ok: Murata D = 180 mm paper reel` (overwrite)
