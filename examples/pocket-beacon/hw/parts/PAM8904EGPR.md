---
mpn: PAM8904EGPR
aliases: PAM8904E; PAM8904EGPR-T (other package)
manufacturer: Diodes Incorporated
lcsc: C510550
function: Piezo sounder driver with 1x/2x/3x charge pump
package: W-QFN2020-12 (Type US)
size_max_mm: 2.05x2.05x0.80
supply_range_v: 1.5-5.5
io_range_v: 1.5-5.5
typ_current_ma: 6.4
peak_current_ma: 14.2
lifecycle: production
lifecycle_distributor: -
key_specs: vdd=1.5-5.5; vdd_3x_max=4.5; vout3_v=7.2-9.0; idd_2x_diff_ma=6.4; idd_3x_diff_ma=14.2; isd_ua=0.008; cload_max_nf=47
distributors: LCSC=https://www.lcsc.com/product-detail/C510550.html; DigiKey=https://www.digikey.com/en/products/detail/diodes-incorporated/PAM8904EGPR/10295656
price_1: 0.4858
price_10: 0.3795
price_100: 0.2781
price_1k: 0.2372
price_10k: -
lead_time_wk: -
stock_snapshot: 8981 @ LCSC 2026-11-08
alternatives: PAM8904EGPR-T (needs change: U-QFN2020-12 Type UX, 0.65 mm max, different land pattern); PAM8904EJER (NRND, do not use)
evidence: verified
source_date: 2026-11-08
notes: 3x mode draws 14.2 mA differential: firmware must never ring and transmit at the same time on a sagging cell
---

# PAM8904EGPR: piezo sounder driver

## Identity

- Manufacturer: Diodes Incorporated.
- Full orderable MPN: `PAM8904EGPR`. `GPR` = W-QFN2020-12 (Type US) on tape and reel, 3,000 per reel [verified: DS41667 Rev. 4-2, Ordering Information, 2026-11-08].
- Ordering table status: `PAM8904EJER` (U-QFN3030-16) and `PAM8904EJPR` (U-QFN3030-12) are **NRND**. `PAM8904EGPR` and `PAM8904EGPR-T` are **Active** [verified: DS41667 Rev. 4-2, 2026-11-08].
- Datasheet: DS41667 Rev. 4-2, July 2023 [verified: https://www.diodes.com/assets/Datasheets/PAM8904E.pdf, 2026-11-08].

## Why this part

REQ-006 asks ≥ 75 dB(A) at 25 cm from a 3 V coin cell. A piezo needs a large voltage swing. The 3× charge pump gives 7.2 V to 9 V at 3 V input, driven differentially, so the piezo sees 14 Vpp to 18 Vpp. 1× and 2× modes let firmware lower the drive on a weak cell (D-010).

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Supply VIN | 1.5 V to 5.5 V; 3× mode only 1.5 V to 4.5 V | recommended | [verified: DS41667 p.4 and mode table] |
| VOUT 1× / 2× / 3× | 2.8–3.0 V / 5.2–6.0 V / 7.2–9.0 V | VIN 3.0 V | [verified: DS41667 electrical characteristics] |
| VOUT 3× at VIN 2.7 V | 6.8 V to 8.0 V (7.0 V typ) | | [verified: same] |
| VOUT absolute max | 15 V (keep ≤ 13.5 V) | | [verified: DS41667 absolute maximum ratings, note 6] |
| Max load | 47 nF | | [verified: DS41667 description] |
| Recommended parts | CIN = COUT = 2.2 µF; flying caps 1 µF | application circuit | [verified: DS41667 typical application] |

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Length D | 2.000 mm | 2.050 mm | [verified: DS41667 package outline (3), 2026-11-08] |
| Width E | 2.000 mm | 2.050 mm | same |
| Height A | 0.750 mm | 0.800 mm | same |

Pitch 0.4 mm. Exposed pad 0.85 mm to 0.95 mm square.

## Power

| Mode | Typical | Condition | Source |
|---|---|---|---|
| 1× / 2× / 3×, no load | 43 / 118 / 220 µA | | [verified: DS41667 IDD11–13] |
| 1× / 2× / 3×, single-ended | 0.48 / 1.9 / 4.3 mA | application load | [verified: DS41667 IDD21–23] |
| 1× / 2× / 3×, differential | 1.7 / 6.4 / 14.2 mA | application load | [verified: DS41667 IDD31–33] |
| Shutdown | 0.008 µA typ, 1 µA max | DIN = 0 V | [verified: DS41667 ISD] |

The datasheet application load is the one recorded in F-004. The current with LS1 depends on the piezo capacitance and is measured on EVT.

## Interfaces

DIN (tone input from a timer/PWM pin), EN1/EN2 (mode select: 00 shutdown, 01 = 1×, 10 = 2×, 11 = 3×). Auto shutdown when DIN stops (42 ms) [verified: DS41667 mode table].

## Lifecycle

| Source | Status | Date |
|---|---|---|
| Diodes ordering table | Active (GPR) | 2026-11-08 |
| JLCPCB / LCSC | in stock, Extended | 2026-11-08 |

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Packaging | Date |
|---|---|---|---|---|---|---|---|
| JLCPCB / LCSC (C510550) | 0.4858 | 0.3795 | 0.2781 | 0.2372 | — | reel 3,000 | 2026-11-08 |
| DigiKey | 0.87 (quantity not stated on search page) | — | — | — | — | — | 2026-11-08 |

## Stock and lead time

| Source | Authorized stock | Factory lead time | Limits / notes | Date |
|---|---|---|---|---|
| LCSC / JLCPCB | 8,981 (8,874 orderable) | not shown | Extended part | 2026-11-08 |
| DigiKey | not shown on the search page | — | — | 2026-11-08 |

## Alternatives

| MPN | Class | Difference | Price at 1k | Source |
|---|---|---|---|---|
| PAM8904EGPR-T | needs change: U-QFN2020-12 Type UX | 0.65 mm max height, other land pattern | not checked | DS41667 |
| PAM8904EJER / EJPR | **do not use** | NRND | — | DS41667 |

## Checks against the design

- Rail VBAT 2.0 V to 3.3 V inside 1.5 V to 4.5 V (3× mode): **yes**.
- Max dimensions 2.05 × 2.05 × 0.80 mm: yes.
- Load: LS1 must be ≤ 47 nF. The recommended LS1 (CPT-9019A-SMT-TR) is 8.4 nF to 15.6 nF: yes. The Murata part's capacitance is not published on its 2-page sheet.
- Package at JLCPCB: 0.4 mm-pitch QFN with exposed pad, yes.

## Risks

| Risk | Rating | Mitigation |
|---|---|---|
| 14.2 mA draw in 3× on a cold or aged CR2032 | high | firmware picks 2× below 2.6 V loaded (Q-PB-02); 22 µF bulk caps; no TX during a ring |
| COUT sees up to 9 V | low | 16 V-rated COUT (already in BOM) |

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| Diodes DS41667 Rev. 4-2 | https://www.diodes.com/assets/Datasheets/PAM8904E.pdf | 2026-11-08 | read (pdftotext) |
| JLCPCB part detail | https://r.jina.ai/https://jlcpcb.com/partdetail/C510550 | 2026-11-08 | read via reader proxy |
| DigiKey search | https://www.digikey.com/en/products/result?keywords=PAM8904EGPR | 2026-11-08 | search page only, no stock or breaks |
