# Agent report · 2026-11-08 · research: RF, clocks, sound

Scope: U1, U2, LS1, Y1, Y2, ANT1, L2, C11–C14 (electronics-researcher). Dossiers in `hw/parts/`. `bom.csv` was not edited; the orchestrator merges with `bom_merge.py --overwrite`.

| Ref | Stage-2 MPN | Status | Recommendation |
|---|---|---|---|
| U1 | CC2340R52E0RGER | orderable: 9,278 LCSC, 3,859 DigiKey; USD 0.8391 at 1k (LCSC); TI store capped | keep; buy early |
| U2 | PAM8904EGPR | orderable: 8,981 LCSC; USD 0.2372 at 1k | keep |
| LS1 | PKMCS0909E4000-R1 | **Last Time Buy** (DigiKey, 2027-03-31), 0 DigiKey | replace with CPT-9019A-SMT-TR (Q-PB-103) |
| Y1 | ABM11W-48.0000MHZ-8-D1X-T3 | specs fit; **not orderable** (0 DigiKey, 4 LCSC) | ABM11W-48.0000MHZ-7-B1U-T3 (Q-PB-105) |
| Y2 | ABS06-32.768KHZ-9-T | orderable; ESR 90 kΩ vs 100 kΩ limit | keep, or remove with LFOSC (Q-PB-102) |
| ANT1 | 2450AT18A0100001E | orderable: 160,791 DigiKey, 105 LCSC; max height 1.4 mm | keep; tee/pi pads (Q-PB-104) |
| L2 | LQP15MN2N2B02D | **obsolete** | LQG15HS2N2B02D (Q-PB-104) |
| C11, C12 | GJM1555C1H1R0BB01D | orderable: 196,420 LCSC | keep |
| C13, C14 | GRM1555C1H120JA01D | **0 stock** at DigiKey and LCSC | 0402CG120J500NT, JLCPCB Basic C1547 (Q-PB-106) |

Other findings:
- HFXT external load-capacitor footprints are needed for regulatory compliance (TI note); see Q-PB-101.
- Below 2.2 V, radio currents rise by about 1.8× (GLDO); see F-101.
- Closed: Q-PB-04 (crystal fit, via Q-PB-105) and Q-PB-05 (RGE height 1.0 mm max).
- The sound estimate with CPT-9019A and the PAM8904E in 3× mode is 78–80 dB at 25 cm, free field, before enclosure loss. This is an estimate; measure on EVT.

Notebook: F-101–F-107, E-101.

Not verified:
- RGE body maximum length and width (the drawing is an image);
- the ABS06 `-T` suffix;
- the LQG15HS Q at 2.4 GHz;
- the exact antenna clearance rectangle.
