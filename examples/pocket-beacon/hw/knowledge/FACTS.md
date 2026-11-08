# Facts

Measured or verified facts. One entry per fact. Never delete an entry; supersede it.

<!-- Entry format:
## F-001 · YYYY-MM-DD · <short title>
- **Fact:** <statement with value and unit>
- **Evidence:** [verified: <source or measurement>, <date>] | [estimate: <basis>] | [assumption]
- **Reproduce:** <command, instrument setup or source URL + section>
- **Used by:** <REQ-/D-/file references>
-->

## F-001 · 2026-11-08 · CC2340R5 supply and radio currents
- **Fact:** CC2340R52E0RGER runs from 1.71 V to 3.8 V; TX 5.1 mA at 0 dBm, 7.9 mA at +4 dBm, 10.7 mA at +8 dBm; RX 5.3 mA; standby 0.71 µA with RTC and full RAM retention; shutdown 165 nA.
- **Evidence:** [verified: TI SWRS272F rev F (May 2026), features list, §7.10 power consumption radio modes, power table, 2026-11-08]
- **Reproduce:** `pdftotext -layout cc2340r5.pdf` from https://www.ti.com/lit/ds/symlink/cc2340r5.pdf, search "Radio transmit current".
- **Used by:** D-011, D-012, REQ-002, architecture §4

## F-002 · 2026-11-08 · CC2340R5 clocks and DC/DC parts
- **Fact:** radio needs an external 48 MHz crystal (CL 5–9 pF, ESR ≤ 60 Ω for 6–9 pF); internal 32 kHz RC oscillator exists, 32.768 kHz crystal optional (CL 6–12 pF, ESR ≤ 100 kΩ); DC/DC needs 10 µH + 10 µF on VDDR; coin-cell designs need 10 µF on VDDS.
- **Evidence:** [verified: TI SWRS272F §7.20.3.1–7.20.3.4, §7.4 note 2, §7 note 3, 2026-11-08]
- **Reproduce:** same PDF, sections 7.4 and 7.20.3.
- **Used by:** D-017, bom Y1 Y2 L1 C3 C4

## F-003 · 2026-11-08 · CC2340R52E0RGER lifecycle and stock
- **Fact:** CC2340R52E0RGER is "Active / Production" (VQFN RGE, 24 pins, 3000 T&R); 12 GPIO in this package; LCSC C20416850 showed 15,000 and 19,372 pcs from two listings, USD 0.80–1.33 at 1k.
- **Evidence:** [verified: TI SWRS272F package option addendum + device comparison; LCSC search "CC2340R5", 2026-11-08]
- **Reproduce:** https://www.lcsc.com/search?q=CC2340R5 (through a reader proxy if blocked).
- **Used by:** D-012, bom U1

## F-004 · 2026-11-08 · PAM8904E package lifecycle and drive
- **Fact:** PAM8904EJER and PAM8904EJPR (U-QFN3030) are NRND; PAM8904EGPR (W-QFN2020-12, 0.80 mm max) and PAM8904EGPR-T (U-QFN2020-12, 0.65 mm max) are Active. VIN 1.5–5.5 V; VOUT 5.2 V (2×) / 7.2 V (3×) at VIN 3.0 V; differential current 6.4 mA (2×) / 14.2 mA (3×) at 47 nF, 3.2 kHz; shutdown 8 nA typ. LCSC C510550 (EGPR) had 8,794 pcs.
- **Evidence:** [verified: Diodes DS41667 Rev. 4-2, Ordering Information and Electrical Characteristics; LCSC search "PAM8904EGPR", 2026-11-08]
- **Reproduce:** https://www.diodes.com/assets/Datasheets/PAM8904E.pdf
- **Used by:** D-010, bom U2

## F-005 · 2026-11-08 · Murata PKMCS0909E4000-R1 rating
- **Fact:** 9.0 × 9.0 × 1.9 mm max SMD piezo sounder; 65 dB(A) min at ±1.5 Vo-p, 4.0 kHz square, 10 cm; ±12.5 Vo-p max; −40 °C to +85 °C; externally driven. LCSC C910763 had 535 pcs.
- **Evidence:** [verified: Murata VPPT-BUZJ083-D datasheet via https://datasheet.lcsc.com/datasheet/pdf/68ecee76a59241f9b49d94957d1d10cd.pdf, 2026-11-08]
- **Reproduce:** download the PDF above, `pdftotext -layout`.
- **Used by:** D-010, bom LS1, REQ-006

## F-006 · 2026-11-08 · TE BAT-HLD-001-TR availability
- **Fact:** TE Store listed 93,362 pcs of BAT-HLD-001-TR at about USD 0.48 at 1k; Newark 2,021 pcs cut tape at USD 1.03 at 1.
- **Evidence:** [verified: Octopart search snapshot "BAT-HLD-001" through reader proxy, 2026-11-08]
- **Reproduce:** https://octopart.com/search?q=BAT-HLD-001
- **Used by:** D-013, bom BT1

## F-401 · 2026-11-08 · CC2340R5 power-mode currents and supply limits
- **Fact:** with DC/DC on at VDDS 3.0 V: active 2.6 mA (CoreMark 48 MHz), idle 0.8 mA (flash off), standby 0.74 µA with LFXT and full RAM retention, shutdown 165 nA; RF subsystem idle adds 40 µA. DC/DC needs VDDS ≥ 2.2 V, below it the device moves to GLDO and TX at 0 dBm rises from 5.1 mA to 9.0 mA. Brown-out falling threshold 1.67 V. VDDS falling slew rate ≤ 1 mV/µs.
- **Evidence:** [verified: TI SWRS272F rev F (May 2026) §7.9, §7.10 and recommended operating conditions, 2026-11-08]
- **Reproduce:** `curl -sLo cc.pdf https://www.ti.com/lit/ds/symlink/cc2340r5.pdf && pdftotext -layout cc.pdf - | grep -n -E "Standby|Idle|DCDC operation|slew|Brownout"`
- **Used by:** hw/power/budget.input.json U1, power.md §3 and §5

## F-402 · 2026-11-08 · CR2032 effective capacity under BLE-like pulses
- **Fact:** under 15–30 mA pulse profiles to 2.0 V, CR2032 cells from six vendors delivered about 50–95 % of 220 mAh rated; 30 mA instead of 15 mA peaks cost about 9 % on average; a parallel buffer capacitor raised the worst vendor from 138 mAh to 181 mAh (82 % of rated). The 15 mA "limit" is not a hard limit; internal resistance rises steeply with use and in the cold.
- **Evidence:** [verified: TI SWRA349 "Coin cells and peak current draw" (2010) §3, §4, Fig. 3 and 8–11, Appendix A, 2026-11-08]
- **Reproduce:** https://www.ti.com/lit/an/swra349/swra349.pdf
- **Used by:** budget.input.json battery.usable_fraction 0.85, limits; power.md §5 capacitor sizing

## F-403 · 2026-11-08 · CR2032 datasheet figures
- **Fact:** IEC CR2032 Li-MnO2: Ø 20.00 max / 19.70 min mm, height 3.20 max / 2.90 min mm, 3.0 V nominal; Energizer typical 254 mAh to 2.0 V at 15 kΩ (21 °C), self-discharge about 1 %/year, operating −30 °C to 60 °C; Panasonic CR2032 listed at 225 mAh. Child-resistant compartment: a tool, or two independent simultaneous movements.
- **Evidence:** [verified: Energizer datasheets 2032GL0626 and UltimateCR2032EU0920 (data.energizer.com/pdfs/); DigiKey Panasonic CR2032 listing, 2026-11-08]
- **Reproduce:** https://data.energizer.com/pdfs/ultimatecr2032EU0920.pdf ; https://www.digikey.com/en/products/result?keywords=CR-2032%2FBN
- **Used by:** power/battery.json, power.md §6, REQ-015

## F-404 · 2026-11-08 · Shipped CR2032 trackers' published battery life
- **Fact:** Apple AirTag "works for more than a year" on a CR2032; Chipolo ONE "up to 2 years" on a CR2032; Chipolo's comparison table lists "~ 1 year" for its CR2032 variant. Implied averages 11.6–23.1 µA at 225 mAh × 0.9.
- **Evidence:** [verified: apple.com/airtag and chipolo.net/en/products/chipolo-one read through r.jina.ai, 2026-11-08]
- **Reproduce:** `curl -sL https://r.jina.ai/https://chipolo.net/en/products/chipolo-one | grep -i battery`
- **Used by:** budget.input.json comparables (empirical scenario)

## F-405 · 2026-11-08 · Pocket Beacon calculated battery life
- **Fact:** average battery current 7.2 µA baseline, 14.3 µA pessimistic, 19.3 µA empirical; end-of-life runtime 36, 18 and 13.1 months on 225 mAh × 0.85 × 0.97; limit for 12 months 21.2 µA. Ship mode 0.47 µA, 2-year shelf loss ≈ 5.7 %.
- **Evidence:** [estimate: power_budget.py on hw/power/budget.input.json; SoC event charges are estimates from F-401]
- **Reproduce:** `python3 skills/battery-and-power/scripts/power_budget.py examples/pocket-beacon/hw/power/budget.input.json -o /tmp/b.json`
- **Used by:** power.md §1 and §3, REQ-002, REQ-003

## F-301 · 2026-11-08 · 0603 22 µF X5R 6.3 V keeps half its capacitance at 3 V
- **Fact:** CL10A226MQ8NRNC capacitance change at 25 °C: −37.4 % at 2.2 V, −51.2 % at 3.0 V, −55.6 % at 3.3 V. Effective: 13.8 µF, 10.7 µF and 9.8 µF.
- **Evidence:** [verified: Samsung product page with embedded DC-bias data, product.samsungsem.com/mlcc/CL10A226MQ8NRN.do, 2026-11-08]
- **Reproduce:** fetch the page and parse the `datasheetData` JSON, graph `DCBias` (method in `hw/agents/2026-11-08-research-passives.md`)
- **Used by:** parts/CL10A226MQ8NRNC.md, Q-PB-07

## F-302 · 2026-11-08 · Effective capacitance on VBAT
- **Fact:** C1, C2, C3, C5, C6 and C7 give 54.6 µF nominal, 35.8 µF effective at 2.2 V, 28.0 µF effective at 3.0 V, and about 19.7 µF worst case at 3.0 V (tolerance and temperature included).
- **Evidence:** [estimate: Samsung DC-bias curves (F-301, F-303, F-304); −20 %/−10 % tolerance; X5R ±15 %]
- **Reproduce:** table in `parts/CL10A226MQ8NRNC.md` § Bulk capacitance
- **Used by:** Q-PB-07, battery-and-power

## F-303 · 2026-11-08 · CC2340 VDDS falling slew limit and DC/DC passives
- **Fact:** VDDS falling slew rate ≤ 1 mV/µs. Coin cells need a 10 µF VDDS capacitor. The DC/DC needs 10 µH + 10 µF on VDDR and VDDS ≥ 2.2 V, otherwise it falls back to GLDO. No inductor DCR or Isat limit is stated.
- **Evidence:** [verified: TI SWRS272F rev F (May 2026) §7.3 note 3, §7.4 notes 1–2]
- **Reproduce:** `pdftotext -layout cc2340r5.pdf - | sed -n '/7.3 Recommended/,/7.5 Global/p'`
- **Used by:** parts/CL10A106KP8NNNC.md, parts/MLZ2012M100WT000.md

## F-304 · 2026-11-08 · TI LaunchPad DC/DC inductor and capacitors
- **Fact:** LP-EM-CC2340R53 (MCU143A) uses L1 = Murata LQM18DN100M70L (10 µH ±20 %, 0.1 A, 0603), C104/C105 = GRM188Z71A106KA73D (10 µF X7R 10 V 0603) and 0.1 µF 0201 decoupling (8 places).
- **Evidence:** [verified: TI SWRC397 design files, MCU143A_BOM.xlsx, 2026-11-08]
- **Reproduce:** download https://www.ti.com/lit/zip/SWRC397 and read the BOM sheet
- **Used by:** parts/MLZ2012M100WT000.md, parts/CL05B104KO5NNNC.md

## F-305 · 2026-11-08 · MLZ2012M100WT000 ratings and height
- **Fact:** 10 µH ±20 % at 2 MHz; DCR 470 mΩ typ, 611 mΩ max; 350 mA (20 °C rise); 150 mA (50 % L drop); 2.00 × 1.25 × 1.25 mm, each ± 0.20 mm, so 1.45 mm maximum height.
- **Evidence:** [verified: TDK product page via r.jina.ai, 2026-11-08]
- **Reproduce:** `https://r.jina.ai/https://product.tdk.com/en/search/inductor/inductor/smd/info?part_no=MLZ2012M100WT000`
- **Used by:** parts/MLZ2012M100WT000.md, stack-up

## F-306 · 2026-11-08 · Charge-pump capacitor derating
- **Fact:**
  - CL10A225KO8NNNC keeps 22 % at 9.0 V, which is 0.49 µF as COUT.
  - CL05A105KO5NNNC keeps 22 % at 6.6 V.
  - CL05A105KA5NQNC (25 V) keeps 43 % at 6.6 V.
  - PAM8904E VOUT in 3× mode is 7.2 V to 9 V.
- **Evidence:** [verified: Samsung DC-bias curves, 2026-11-08; Diodes DS41667 Rev 4-2]
- **Reproduce:** as F-301 for each part
- **Used by:** parts/CL10A225KO8NNNC.md, parts/CL05A105KO5NNNC.md, Q-PB-08

## F-307 · 2026-11-08 · JLC stock blocks Y1, BT1 and L2
- **Fact:** JLC assembly stock: Y1 ABM11W-48 = 4, BT1 BAT-HLD-001-TR = 12, L2 LQP15MN2N2B02D = 0, ANT1 = 95, LS1 = 535. The BOM LCSC number C52923 for C9/C10 is CL05A105KA5NQNC, not the BOM MPN.
- **Evidence:** [verified: JLCPCB parts API, 2026-11-08]
- **Reproduce:** `parts/_jlc_availability.md` method line
- **Used by:** parts/_jlc_availability.md, build-package stock check

## F-101 · 2026-11-08 · CC2340R5 below 2.2 V, crystal note, package height
- **Fact:** the DC/DC runs from 2.2 V to 3.8 V; below 2.2 V the CC2340R5 switches to the GLDO and TX at 0 dBm rises from 5.1 mA to 9.0 mA (19 mA at +8 dBm). TI names only Tai-Saw TZ3908AAAO43 as a validated 48 MHz crystal and says external HFXT load capacitors are required for systems targeting compliance with certain regulations. RGE24 package is 1 mm max height.
- **Evidence:** [verified: TI SWRS272F §7.4, §7.10, §7.20.3.1 notes 1 and 4; TI RGE package view mpqf124g, 2026-11-08]
- **Reproduce:** `pdftotext -layout` on https://www.ti.com/lit/ds/symlink/cc2340r5.pdf; search "DCDC operation", "TZ3908".
- **Used by:** hw/parts/CC2340R52E0RGER.md, Q-PB-101, Q-PB-05 (closed), battery-and-power end-of-life budget

## F-102 · 2026-11-08 · Murata PKMCS0909E4000-R1 is Last Time Buy
- **Fact:** DigiKey lists PKMCS0909E4000-R1 as Last Time Buy (last buy 31 Mar 2027), 0 in stock, 2,000 expected 26 Nov 2027; Murata's product page returns 404; LCSC C910763 has 535 (400 orderable).
- **Evidence:** [verified: DigiKey search page; JLCPCB part detail C910763; Murata productdetail URL via reader proxy, 2026-11-08]
- **Reproduce:** https://www.digikey.com/en/products/result?keywords=PKMCS0909E4000-R1
- **Used by:** Q-PB-103, hw/parts/PKMCS0909E4000-R1.md

## F-103 · 2026-11-08 · Same Sky CPT-9019A-SMT-TR ratings
- **Fact:** 3 Vpp rated, 1–25 Vpp operating, 72 dB min / 75 dB typ at 10 cm (3 Vpp, 4 kHz, ½-duty square), 8.4–15.6 nF at 1 kHz, 9 × 9 × 1.9 mm (±0.5 mm general tolerance; 2.10 mm max seated height per DigiKey), top port, −40 °C to 85 °C, reflow 250 °C max within 48 h of opening. DigiKey: Active, 47,328 in stock, 13-week lead time; LCSC C20181991: 13 in stock.
- **Evidence:** [verified: Same Sky datasheet dated 02/19/2026; DigiKey search; LCSC search via reader proxy, 2026-11-08]
- **Reproduce:** https://www.sameskydevices.com/product/resource/digikeypdf/cpt-9019a-smt-tr.pdf
- **Used by:** Q-PB-103, REQ-006 sound estimate

## F-104 · 2026-11-08 · ABM11W 48 MHz options and stock
- **Fact:** ABM11W suffix: `-7`/`-8` = CL 7/8 pF; `D1X` = −40…85 °C, ±10 ppm, ±20 ppm; `B1U` = −20…70 °C, ±10 ppm, ±10 ppm; `T3` = 3k reel; ESR 40 Ω max at 38–50 MHz (CL 6–8 pF); 0.5 mm max height. ABM11W-48.0000MHZ-8-D1X-T3: 0 at DigiKey, 4 at LCSC. ABM11W-48.0000MHZ-7-B1U-T3: 3,758 at LCSC (C1985532, USD 0.2699 at 1k), 43,551 at DigiKey. TZ3908AAAO43: not stocked at DigiKey (3,000 MOQ, USD 3.525), no LCSC listing.
- **Evidence:** [verified: Abracon ABM11W datasheet (revised 10.06.2020); DigiKey and JLCPCB/LCSC pages, 2026-11-08]
- **Reproduce:** https://abracon.com/Resonators/ABM11W.pdf; https://r.jina.ai/https://jlcpcb.com/partdetail/C1985532
- **Used by:** Q-PB-04 (resolved by recommendation), hw/parts/ABM11W-48.0000MHZ-7-B1U-T3.md

## F-105 · 2026-11-08 · ABS06-32.768KHZ-9-T ESR margin
- **Fact:** ABS06-32.768KHZ-9-T is CL 9 pF, ESR 90 kΩ max, ±20 ppm, 2.0 × 1.2 mm, 0.60 mm max; the CC2340 LFXT limit is 100 kΩ (10 % margin). LCSC C1985410 1,925 in stock; DigiKey 15,858, 26-week lead time.
- **Evidence:** [verified: DigiKey search; LCSC search via reader proxy, 2026-11-08]
- **Reproduce:** https://www.digikey.com/en/products/result?keywords=ABS06-32.768KHZ-9-T
- **Used by:** Q-PB-102, hw/parts/ABS06-32.768KHZ-9-T.md

## F-106 · 2026-11-08 · Johanson 2450AT18A0100001E layout data
- **Fact:** 3.20 ± 0.20 × 1.60 ± 0.20 × 1.30 +0.10/−0.20 mm (max 3.4 × 1.8 × 1.4 mm); legacy P/N 2450AT18A100; corner mount; peak gain 1.5 dBi, average 0.0 dBi, 74 % efficiency measured on the 39.5 mm eval board 2450AT18A0100001CE1; eval matching 1.0 pF + 2.7 nH + 3.9 nH; Johanson recommends leaving slots for a tee (series-shunt-series) network. DigiKey 160,791 in stock (USD 0.3328 at 1k, 18 weeks); LCSC C17430588 105 in stock.
- **Evidence:** [verified: Johanson datasheet Doc# 36S0021A rev 4.0; DigiKey; LCSC via reader proxy, 2026-11-08]
- **Reproduce:** https://www.johansontechnology.com/docs/3827/Antenna-2450AT18A0100001E-Rev4.0.pdf
- **Used by:** Q-PB-03, Q-PB-104, pcb-engineer antenna keep-out

## F-107 · 2026-11-08 · Obsolete and out-of-stock RF passives
- **Fact:** Murata LQP15MN2N2B02D is obsolete (DigiKey) and "not recommended for new designs" (LCSC C77120, not available); LQG15HS2N2B02D (LCSC C162540) has 31,900 in stock. Murata GRM1555C1H120JA01D has 0 stock at DigiKey (10,000 expected 7 Dec 2026) and at LCSC; FH 0402CG120J500NT is a JLCPCB Basic part (C1547) with 1,946,183 in stock at USD 0.0021 at 1k.
- **Evidence:** [verified: DigiKey and LCSC/JLCPCB pages via reader proxy, 2026-11-08]
- **Reproduce:** https://r.jina.ai/https://www.lcsc.com/search?q=LQP15MN2N2B02D; https://r.jina.ai/https://jlcpcb.com/partdetail/C1547
- **Used by:** Q-PB-104, hw/parts/LQG15HS2N2B02D.md, hw/parts/0402CG120J500NT.md

## F-201 · 2026-11-08 · BT1 TE BAT-HLD-001 retainer dimensions
- **Fact:** TE drawing C-BAT-HLD-001-xx rev E1 (2023-11-15): 22.9 × 21.1 mm, 4.2 mm above the board (DigiKey 4.20 mm); title-block tolerance ±0.2 mm (1 place). The BOM estimate 23.0 × 21.0 × 4.3 mm is replaced by 23.1 × 21.3 × 4.4 mm max. LCSC/JLCPCB carry the bulk BAT-HLD-001 (C7501066, 1,681 pcs, Extended), not the -TR reel (C20607187, 12 pcs).
- **Evidence:** [verified: TE drawing via r.jina.ai; DigiKey; JLCPCB part page, 2026-11-08]
- **Reproduce:** `curl -sL "https://r.jina.ai/https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=C-BAT-HLD-001-xx&DocType=Customer%20Drawing&DocLang=English&DocFormat=pdf&PartCntxt=BAT-HLD-001-TR"`
- **Used by:** parts/BAT-HLD-001-TR.md, Q-PB-01

## F-202 · 2026-11-08 · Keystone 3034TR retainer
- **Fact:** Keystone 3034/3034TR ultra-low-profile CR2032 retainer: A 21.2 mm, W 23.1 mm, H 4.1 mm (DigiKey 4.06 mm), negative PCB pad 3.96 mm square min. DigiKey USD 0.48 (1) / 0.2733 (1k); 121,030 in stock + 316,500 factory; 14-week lead time. JLCPCB C5213768 (644 pcs) and C5199422 (bulk, 1,000 pcs).
- **Evidence:** [verified: Keystone catalog K75p11.pdf; DigiKey 3034TR page; JLCPCB search API, 2026-11-08]
- **Reproduce:** `curl -sL https://www.keyelco.com/userAssets/file/K75p11.pdf | pdftotext -layout - - | grep 3034`
- **Used by:** parts/3034TR.md, Q-PB-01

## F-203 · 2026-11-08 · Panasonic CR2032 capacity under load and cold
- **Fact:** Panasonic CR2032 (April 2022): 225 mAh at 0.2 mA to 2.0 V, −30 °C to 85 °C, Ø 20.0 × 3.2 mm max. Curves read from the datasheet: at 1 kΩ (≈ 2.7 mA) ≈ 165 mAh at 20 °C and ≈ 100 mAh at −10 °C; voltage at 50% depth ≈ 2.75 V (20 °C) and ≈ 2.45 V (−10 °C).
- **Evidence:** [verified: datasheet text values] [estimate: curve readings ±10 mAh / ±0.05 V]
- **Reproduce:** `curl -sL https://api.pim.na.industrial.panasonic.com/file_stream/main/fileversion/250011 -o cr2032.pdf && pdftoppm -r 110 -png cr2032.pdf p`
- **Used by:** parts/CR2032.md, power/battery.json

## F-204 · 2026-11-08 · CR2032 internal-resistance limits for pulses (TI SWRA349)
- **Fact:** With a 2.0 V cut-off, a CR2032 stops supporting 30 mA pulses at ≈ 30 Ω internal resistance and 15 mA pulses at ≈ 60 Ω; internal resistance rises steeply with used capacity. Some vendors, branded included, reached only ≈ 50% of rated capacity. A parallel capacitor added > 40% usable capacity on weak cells and 5–13% on good cells.
- **Evidence:** [verified: TI SWRA349 (2010) §3, §4]
- **Reproduce:** `curl -sL https://www.ti.com/lit/an/swra349/swra349.pdf | pdftotext -layout - - | grep -i ohm`
- **Used by:** parts/CR2032.md, power.md (ring mode rules, Q-PB-02)

## F-205 · 2026-11-08 · DMG2305UX-7 at a 2.0 V cell, and supply
- **Fact:** VGS(th) −0.5 V to −0.9 V; RDS(on) max 200 mΩ at VGS −1.8 V and 100 mΩ at −2.5 V; IGSS ±100 nA max at ±8 V. At 2.0 V and 15 mA the drop is ≤ 3 mV. DigiKey: 0 in stock, 40-week lead time, no in-stock date; LCSC C150470: 31,853 pcs, Diodes brand.
- **Evidence:** [verified: Diodes DS36196 Rev 8-2; DigiKey; LCSC API, 2026-11-08]
- **Reproduce:** `curl -sL https://www.diodes.com/assets/Datasheets/DMG2305UX.pdf | pdftotext -layout - - | grep -i -E "VGS|RDS"`
- **Used by:** parts/DMG2305UX-7.md, D-014

## F-206 · 2026-11-08 · TPD1E10B06DPYR leakage and package
- **Fact:** ILEAK ≤ 100 nA at 5 V; VRWM 5.5 V; IEC 61000-4-2 ±30 kV; X1SON DPY 1.1 × 0.7 × 0.45 mm max; TI status Active. Worst-case leakage ≈ 0.9 mAh per year (0.4% of 225 mAh).
- **Evidence:** [verified: TI SLLSEB1G (rev. Aug 2024)] [estimate: annual charge]
- **Reproduce:** `curl -sL https://www.ti.com/lit/ds/symlink/tpd1e10b06.pdf | pdftotext -layout - - | grep -i leak`
- **Used by:** parts/TPD1E10B06DPYR.md, power budget

## F-207 · 2026-11-08 · LTST-C191KFKT at coin-cell currents
- **Fact:** IV 45–90 mcd at 20 mA (bins P–S, 45–280 mcd); VF 2.0 typ / 2.4 max V at 20 mA; VF ≈ 1.75 V near 1 mA; intensity close to linear with current. With R1 = 680 Ω: ≈ 1.8 mA at 3.0 V, ≈ 0.4 mA at 2.0 V (≈ 3–6 mcd fresh, ≈ 1 mcd at end of life).
- **Evidence:** [verified: Lite-On DS22-2000-222 rev F table] [estimate: values read from Fig. 2 and Fig. 4]
- **Reproduce:** LCSC datasheet mirror for C160478 (`wmsc.lcsc.com/ftps/wm/product/detail?productCode=C160478` → pdfUrl), pages 4–6
- **Used by:** parts/LTST-C191KFKT.md, D-005

## F-208 · 2026-11-08 · KMR221G LFS switch
- **Fact:** C&K KMR2: 2.0 N ± 0.5 N, 200,000 cycles, travel 0.25 ± 0.1 mm, total height 1.9 mm, IP40, contact resistance ≤ 100 mΩ, bounce ≤ 3 ms, −40 °C to 85 °C (silver). Reels of 7,000.
- **Evidence:** [verified: C&K KMR2 datasheet via LCSC mirror C72443, 2026-11-08]
- **Reproduce:** LCSC API pdfUrl for C72443
- **Used by:** parts/KMR221GLFS.md, REQ-009, Q-PB-06

## F-209 · 2026-11-08 · Look-alike LCSC listings under genuine MPNs
- **Fact:** LCSC/JLCPCB list other makers under the exact MPN of a genuine part: "DMG2305UX-7" by HXY MOSFET (C5261054) next to Diodes (C150470); "TPD1E10B06DPYR" by TECH PUBLIC (C2937015) and Leiditech (C2972450) next to TI (C48260). Selecting by MPN alone can place a different maker's part.
- **Evidence:** [verified: JLCPCB search API results, 2026-11-08]
- **Reproduce:** JLCPCB `selectSmtComponentList` API with keyword = MPN; compare `componentBrandEn`
- **Used by:** bom.csv `lcsc` column; build-package BOM review

## F-210 · 2026-11-08 · CR-2032/BN is not an authorized stock line at DigiKey
- **Fact:** DigiKey lists `CR2032/BN` only on its Marketplace (Dantona Industries) at USD 9.75; the authorized Panasonic line is `CR2032` (11-CR2032-ND, tray): USD 0.40 (1), 0.23553 (800+), 0.20706 (4,000+), 2,492,586 in stock, 22-week lead time.
- **Evidence:** [verified: DigiKey search and product page, 2026-11-08]
- **Reproduce:** https://www.digikey.com/en/products/detail/panasonic-energy/CR2032/31939
- **Used by:** parts/CR2032.md

## F-501 · 2026-11-08 · US coin-cell compartment rule (Reese's Law, 16 CFR 1263)
- **Fact:**
  - **Scope.** 16 CFR 1263.3 makes ANSI/UL 4200A-2023 mandatory for every consumer product that contains a coin cell.
  - **Compartment.** A replaceable-cell compartment must open only with a coin, screwdriver or other tool (option 1). A twist-on enclosure must need ≥ 90° rotation, with "two threads engaged or minimum torque + spin angle". The other route is at least two independent and simultaneous hand movements that cannot be combined into one movement of one finger (option 2).
  - **Preconditioning:** 7 h at ≥ 70 °C for thermoplastics, and 10 open/close cycles with the battery removed and reinstalled.
  - **Abuse tests:**
    - drop: 10 drops from 1 m on hardwood for handheld products;
    - impact: 3 × 2 J steel sphere;
    - crush: 330 N for 10 s;
    - compression: ≥ 136 N;
    - torque: ≥ 0.50 N·m;
    - tension: ≥ 72 N;
    - probe 11 (IEC 61032) at 50–60 N.
  - **Warnings:** required on the product packaging, in the accompanying literature and on the product "as practicable" (16 CFR 1263.4).
  - **Certification.** Non-children's products need a certificate of conformity based on testing. Third-party testing is required only for children's products.
- **Evidence:** [verified: eCFR 16 CFR part 1263 §1263.3–1263.4, and the CPSC final rule 88 FR 65274 (21 Sep 2023), Table 3 "Summary of Performance Requirements in UL 4200A-2023", read 2026-11-08]. The UL 4200A text itself was not read; the exact minimum torque and spin angle for option 1 are to be read in the free UL IBR copy.
- **Reproduce:** https://r.jina.ai/https://www.ecfr.gov/current/title-16/chapter-II/subchapter-B/part-1263 and https://r.jina.ai/https://www.federalregister.gov/citation/88-FR-65274 (search "Table 3").
- **Used by:** REQ-015, D-026, hw/mech/constraints.md, compliance-planner

## F-502 · 2026-11-08 · TI LaunchPad decoupling, reset and RF filter (LP-EM-CC2340R53)
- **Fact:** the TI reference board uses:
  - VDDS: 4 × 0.1 µF (one per VDDS pin) + 10 µF;
  - VDDR: 10 µF + 2 × 0.1 µF (one per VDDR pin), with "place L1 and C105 close to the DCDC pin";
  - VDDD: 1 µF (C9, GRM155Z71A105KE01D);
  - RSTN: 100 kΩ pull-up + 0.1 µF;
  - RF: a pi harmonic filter C33 1.5 pF – L33 2.8 nH – C34 1.5 pF, then a pi antenna match Z60 1.2 pF – Z61 2 nH – Z62 0.7 pF, and an ESD diode on the antenna port;
  - 48 MHz external load caps C52/C53 marked Do Not Stuff. Parts are 0201.
- **Evidence:** [verified: TI SWRC397, MCU143A_BOM.xlsx and mcu143a.pdf, read 2026-11-08]
- **Reproduce:** download https://www.ti.com/lit/zip/SWRC397; `pdftotext -layout Schematics/mcu143a.pdf`; read the BOM sheet.
- **Used by:** D-030, D-031, architecture.md §5, V-005, V-006

## F-601 · 2026-11-08 · JLCPCB Standard PCBA tariff (page updated 2026-10-22)
- **Fact:** setup USD 25.56 one side / 51.12 two sides; stencil 8.21 / 16.42; feeder loading USD 1.53 per part type for basic and extended parts alike (Economic PCBA charges 3.07 for extended parts only); joints 0.0016 (≤ 50k) / 0.0013 (≤ 100k) / 0.0012 (≤ 1M); X-ray per component 1.64 (1–10) down to 0.082 (3,001+); handling ≥ 14.93.
- **Evidence:** [verified: https://jlcpcb.com/help/article/pcb-assembly-price, "Last updated on Oct 22, 2026", read 2026-11-08]
- **Reproduce:** fetch the URL above.
- **Used by:** cost/manufacturing.json (pcba.tariff)

## F-602 · 2026-11-08 · EN 18031 scope covers devices that reach the internet through a phone
- **Fact:** Delegated Regulation (EU) 2022/30 art. 1(1) applies art. 3(3)(d) to radio equipment that can communicate over the internet "whether it communicates directly or via any other equipment"; art. 1(2) applies 3(3)(e) to internet-connected radio equipment that processes personal data or traffic and location data.
- **Evidence:** [verified: eur-lex CELEX:32022R0030, art. 1, read 2026-11-08]. The consolidated version (2023-10-27) changed the date of application; the toolkit rules give 2025-08-01.
- **Reproduce:** https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R0030
- **Used by:** compliance.md (EN 18031-1 and -2 apply)

## F-603 · 2026-11-08 · IETF DULT accessory protocol draft requirements
- **Fact:** draft-ietf-dult-accessory-protocol-01 (2026-10-27): practices REQUIRED for small location-enabled accessories; sound ≥ 60 phon peak (ISO 532-1) at 25 cm, 5–30 s, 12 s recommended; address rotation every 15 min near the owner and every 24 h when separated; separated mode after 30 min; advertising interval ≤ 4 s; a physical way to disable; a readable identifier.
- **Evidence:** [verified: https://datatracker.ietf.org/doc/draft-ietf-dult-accessory-protocol/, read 2026-11-08]
- **Reproduce:** fetch the URL above.
- **Used by:** compliance.md, D-604

## F-604 · 2026-11-08 · Pocket Beacon cost model result (estimate-heavy)
- **Fact:** recurring cost per unit USD 231–457 (1), 47.0–138 (10), 22.1–56.8 (100), 8.79–16.4 (1k), 5.57–8.68 (10k); 41 % of the 1k recurring cost rests on verified figures; certification NRE USD 20.3k–46.5k (US launch) + 12.75k–82k (EU/UK/BR).
- **Evidence:** [estimate: cost_model.py run 2026-11-08 on bom.csv and cost/manufacturing.json; BOM and PCBA tariff verified, enclosure, assembly, mechanical and certification lines are estimates]
- **Reproduce:** `python3 skills/cost-and-sourcing/scripts/cost_model.py --bom hw/bom.csv --mfg hw/cost/manufacturing.json --out hw/cost --svg`
- **Used by:** cost/cost.md, REQ-019

## F-510 · 2026-11-08 · Stack height with maximum part heights
- **Fact:** 10.00 mm total at the cell/sounder column with a 0.6 mm board (door 1.85, gap 0.15, holder 4.1, PCB 0.6, LS1 2.1, gasket 0.3, wall 0.9); 10.20 mm with a 0.8 mm board.
- **Evidence:** [verified: hw/mech/enclosure.json + cad_pocket_beacon.py frame output, 2026-11-08]
- **Reproduce:** `"$CAD_PY" hw/mech/cad_pocket_beacon.py hw/mech/enclosure.json --out hw/mech/cad` (frame line)
- **Used by:** D-510, mech/stackup.md

## F-511 · 2026-11-08 · Keystone 3034 3D model occupies r ≈ 11.8 mm near the lid side
- **Fact:** the KiCad model of the 3034 (z 3.0–4.0 mm from the board, i.e. the lid side) spans x ±11 mm, y −9…+8 mm, with corners near (±8, ±8) mm; below the board it reaches z = −4.09 mm.
- **Evidence:** [verified: KiCad 10.0.8 3dmodels/Battery.3dshapes/BatteryHolder_Keystone_3034_1x20mm.step, sliced with build123d on a 1 mm grid, 2026-11-08]
- **Reproduce:** slice the STEP with build123d (`import_step`, `&` with 1 mm boxes)
- **Used by:** D-511

## F-512 · 2026-11-08 · Cell edge to antenna keep-out: 0.96 mm
- **Fact:** the CR2032 edge (r 10.0 mm around (−1.1, −1.1)) is 0.96 mm from the antenna copper keep-out corner (−6.0, −10.9).
- **Evidence:** [verified: geometry of hw/pcb/board.json, 2026-11-08]
- **Reproduce:** distance((−1.1,−1.1),(−6.0,−10.9)) − 10.0
- **Used by:** D-515, V-005

## F-513 · 2026-11-08 · Sounder top port is at a corner of the part
- **Fact:** the CPT-9019A-SMT sound hole (Ø0.65 mm) is 1.5 mm from two edges of the 9 × 9 mm top face, not at its centre.
- **Evidence:** [verified: Same Sky CPT-9019A-SMT-TR datasheet 02/19/2026, p.2 mechanical drawing]
- **Reproduce:** `pdftoppm -f 2 -l 2 -png` of the datasheet
- **Used by:** D-516, Q-CD-01

## F-514 · 2026-11-08 · Freerouting 2.5.0 needs Java 25
- **Fact:** freerouting-2.5.0.jar (SHA-256 starts f6f51bb0) fails on Java 21 with "class file version 69.0"; it runs on Temurin 25.0.5.
- **Evidence:** [verified: run on the cloud VM, 2026-11-08]
- **Reproduce:** `java -jar freerouting-2.5.0.jar --help` on Java 21 and on Java 25
- **Used by:** agents/2026-11-08-codesign.md TB-7

## F-515 · 2026-11-08 · Assembly validation and leak check
- **Fact:** the assembly (enclosure CAD + KiCad board GLB + CR2032) has 0 interpenetrations deeper than 0.02 mm over 72 component pairs; the sealed cavity has no leak (flood fill, h = 0.12 mm, 5511 mm³ of air).
- **Evidence:** [verified: hw/validation/assembly.json and free_space.json, 2026-11-08]
- **Reproduce:** `blender -b --factory-startup --python hw/mech/build_assembly.py`, then free_space.py on the golden file
- **Used by:** gate 7

## F-520 · 2026-11-08 · Main board closes routed, DRC and ERC clean
- **Fact:** the main board (28.4 mm, 4-layer 0.6 mm, 47 parts) has 388 tracks, 150 vias, 0 unconnected items, 0 DRC violations, 0 schematic-parity issues and 0 ERC errors; `release_check.py` reports READY TO ORDER.
- **Evidence:** [verified: hw/pcb/main/drc.json, erc.json, hw/pcb/release-check.json, 2026-11-08]
- **Reproduce:** `kicad-cli pcb drc --schematic-parity --refill-zones hw/pcb/main/main.kicad_pcb`; `python3 skills/pcb-engineer/scripts/release_check.py hw/pcb/board.json --board main`
- **Used by:** gate 6, Q-CD-05

## F-521 · 2026-11-08 · The LED escape needed redundant copper removed, not vias
- **Fact:** with "no non-GND via under the cell" (D-517) and no routing inside U1's pad ring, no LED route existed until three redundant F.Cu items were removed: the EP→C21 GND trace, the GND trace that walled the channel left of SW1, and the BTN link between SW1's two internally joined pads. The final LED route is 10.6 mm on F.Cu, 0 vias, 0.15 mm clearance.
- **Evidence:** [verified: hw/pcb/mlroute.py runs, 2026-11-08; reachability maps in the PCB retro]
- **Reproduce:** `<kicad-python> hw/pcb/mlroute.py hw/pcb/main/main.kicad_pcb LED U1 12 R1 1 --layers F.Cu --clear 0.15 --no-under U1 --debug`
- **Used by:** D-520, D-521

## F-522 · 2026-11-08 · KMR2 duplicate pads are treated as one terminal
- **Fact:** the KiCad library footprint `SW_Push_1P1T-SH_NO_CK_KMR2xxG` numbers the four terminals 1, 1, 2, 2 (identical numbers = internally joined terminals). With the footprint flag `duplicate_pad_numbers_are_jumpers`, KiCad's connectivity treats each pair as one node, and DRC accepts one external connection per pair.
- **Evidence:** [verified: KiCad 10.0.8 DRC on hw/pcb/main/main.kicad_pcb, 2026-11-08]; [estimate: the C&K KMR2 datasheet electrical diagram was not readable as text (Littelfuse PDF returned 403, reader proxy gave graphics only); prototype check requested, Q-PCB-01]
- **Reproduce:** DRC with and without the flag on SW1
- **Used by:** D-520

## F-523 · 2026-11-08 · Stitching-via placement rule that DRC alone does not enforce
- **Fact:** DRC accepted GND stitching vias placed inside the courtyards of C2 and C3 (under the part body). The final island pass keeps vias out of every component courtyard except the cell holder's; 6 F.Cu GND islands were stitched, 0 left without room.
- **Evidence:** [verified: hw/pcb/island_vias.py output, 2026-11-08]
- **Reproduce:** `<kicad-python> hw/pcb/island_vias.py hw/pcb/main/main.kicad_pcb`
- **Used by:** D-522

## F-701 · 2026-11-08 · Final cost model with the routed board and final enclosure
- **Fact:** recurring unit cost $51.4–153 at 10 units, $8.89–17.1 at 1,000 and $5.62–9.01 at 10,000; the $12 target at 1k is not proven
- **Evidence:** [estimate: cost/model.json from manufacturing.json refreshed with 126 pads, 26 part types, 2 X-ray parts; PCBA tariff verified 2026-11-08]
- **Reproduce:** `python3 skills/cost-and-sourcing/scripts/cost_model.py --mfg hw/cost/manufacturing.json --out hw/cost --svg`
- **Used by:** FR-10, release ORDER.md

## F-702 · 2026-11-08 · Release evt0-a passes the ready-to-build gate
- **Fact:** release_check.py reports READY TO BUILD (prototype) with 0 failures and 0 warnings for 47 files
- **Evidence:** [verified: hw/release/evt0-a/checks/release-check.json, 2026-11-08]
- **Reproduce:** `python3 skills/build-package/scripts/release_check.py hw/release/evt0-a/ --hw hw/`
- **Used by:** state.json gates
