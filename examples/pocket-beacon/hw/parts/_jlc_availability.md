# JLCPCB assembly availability, every BOM line

- **Checked:** 2026-11-08, with the JLCPCB parts API (`jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`), searched by LCSC number when the BOM has one, else by MPN. Stock is JLC's own assembly stock on that date [verified: JLCPCB parts API, 2026-11-08].
- **Classes:**
  - **basic:** no feeder-loading fee.
  - **preferred extended:** JLC flags these (`preferredComponentFlag`); they cost less to load than other extended parts [estimate: JLC policy; confirm on the quote].
  - **extended:** a loading fee per unique part type per order. It is US$ 1.53 per type in the toolkit's tariff (`skills/cost-and-sourcing/references/cost-reference.md`, read 2026-11-08) [estimate: confirm on the JLC quote; the JLC help page did not render].

| Ref | BOM MPN | LCSC (lookup) | JLC stock 2026-11-08 | Class | Price at 1 (USD) | Note |
|---|---|---|---|---|---|---|
| U1 | CC2340R52E0RGER | C20416850 | 9,278 | extended | 1.4703 | OK for 10–100 builds; reel needed for 1k (consign or JLC pre-order) |
| U2 | PAM8904EGPR | C510550 | 8,981 | extended | 0.4858 | OK |
| LS1 | PKMCS0909E4000-R1 | C910763 | 535 | extended | 1.104 | enough for 100 builds, not 1k: pre-order or consign |
| D1 | LTST-C191KFKT | C160478 | 36,284 | extended | 0.0282 | OK |
| R1 | RC0402FR-07680RL | C137948 (not in BOM) | 675,860 | extended | 0.0034 | **Substitute:** UNI-ROYAL `0402WGF6800TCE` C25130, 680 Ω 1 % 0402, preferred extended, 191,369 in stock |
| SW1 | KMR221GLFS | C72443 | 2,420 | extended | 0.6902 | OK for 100; 1k needs pre-order |
| BT1 | BAT-HLD-001-TR | C20607187 (not in BOM) | **12** | extended | 1.4409 | **Not buildable at JLC beyond 12 units.** Consign from TE, Newark or Master, or choose an alternative. Keystone `3034` C5199422 has 1,000 at JLC and `3034TR` C5213768 has 644. MPD `BU2032SM-HD-G` C2681429 has 3. Footprint decision is Q-PB-01 |
| BAT1 | CR-2032/BN | — (none) | — | not placed | — | the cell is installed at final assembly, bought from DigiKey or Mouser; it is not an SMT part |
| Q1 | DMG2305UX-7 | C150470 (not in BOM) | 33,085 | extended | 0.5725 | OK |
| D2 | TPD1E10B06DPYR | C48260 (not in BOM) | 298,469 | extended | 0.0447 | OK |
| Y1 | ABM11W-48.0000MHZ-8-D1X-T3 | C1986112 | **4** | extended | 0.4874 | **Not buildable.** SCTF `SX1B48.000F0810F30` C7301965 (48 MHz, 8 pF, ±10 ppm, 2016-4P) has 2,160. Tai-Saw `TZ3908AAAO43` C22367622 has 0. Must be checked against the CC2340 HFXT limits (CL 5–9 pF, ESR ≤ 60 Ω): another researcher's dossier |
| Y2 | ABS06-32.768KHZ-9-T | C1985410 (not in BOM) | 1,925 | extended | 0.7393 | OK for 100 |
| C13, C14 | GRM1555C1H120JA01D | C76948 (not in BOM) | **48** | extended | 0.008 | **Substitute:** FH `0402CG120J500NT` C1547, 12 pF C0G ±5 % 50 V 0402, **basic**, 1,946,183 in stock |
| C1, C2 | CL10A226MQ8NRNC | C59461 | 3,843,850 | **basic** | 0.0171 | OK. Effective capacitance: see `CL10A226MQ8NRNC.md` (Q-PB-07) |
| C3, C4 | CL10A106KP8NNNC | C19702 | 10,304,806 | **basic** | 0.0203 | OK |
| L1 | MLZ2012M100WT000 | C88173 (not in BOM) | 45,383 | extended | 0.0579 | OK. Height 1.45 mm max: see dossier |
| C5, C6 | CL05B104KO5NNNC | C1525 | 34,285,467 | **basic** | 0.0031 | OK |
| C7, C8 | CL10A225KO8NNNC | C23630 | 2,324,513 | **basic** | 0.0118 | OK |
| C9, C10 | CL05A105KO5NNNC | BOM says C52923; that is **CL05A105KA5NQNC** (25 V) | 11,550,069 (C52923) / 1,894,249 (C29266) | basic (C52923) / extended (C29266) | 0.0058 / 0.0049 | **BOM conflict.** The BOM MPN is C29266, an extended part. The BOM LCSC is a different, better part. Adopt CL05A105KA5NQNC (Q-PB-08) |
| ANT1 | 2450AT18A0100001E | C17430588 (not in BOM) | **95** | extended | 0.9731 | enough for 10–90 builds; consign for 100+ |
| C11, C12 | GJM1555C1H1R0BB01D | C76898 (not in BOM) | 204,482 | extended | 0.0316 | OK (value to tune) |
| L2 | LQP15MN2N2B02D | C77120 (not in BOM) | **0** | extended | 0.0319 | **Not buildable at JLC.** No LQP15MN thin-film 2.2 nH in stock (`LQP15MN2N2W02D` C703111 also 0). In stock: Murata `LQG15HS2N2S02D` C86061 (multilayer, 71,971) and `LQW15AN2N2C10D` C91240 (wire-wound, 33,462). A tighter-tolerance B part, `LQG15HS2N2B02D` C162540, has 32,730. The RF value is tuned on EVT anyway (Q-PB-03) |

## Totals for one JLC order

| | Before the substitutions | After C9/C10 → C52923 and C13/C14 → C1547 |
|---|---|---|
| Basic part types | 5 (C1/C2, C3/C4, C5/C6, C7/C8, C9/C10 as C52923) | 6 |
| Extended part types placed by JLC | 16 | 15 |
| Extended loading fee per order | 16 × 1.53 = US$ 24.48 [estimate] | 15 × 1.53 = US$ 22.95 [estimate] |

Lines that block a JLC-assembled build today:

- **Y1:** 4 in stock.
- **BT1:** 12 in stock.
- **L2:** 0 in stock.
- **ANT1:** enough for fewer than 100 units.
- **LS1:** enough for fewer than 1k units.

Each one needs a substitute, consigned parts or a JLC pre-order before `build-package` can pass its stock check.
