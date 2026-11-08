# Agent report · 2026-11-08 · research of passives and the JLC availability check

- **Scope:** C1–C10 and L1 dossiers, plus JLC availability for every BOM line. Notebook range: F-301 to F-399. `bom.csv` was not edited; `bom_merge.py` runs after all researchers finish.

## Written

- `parts/CL10A226MQ8NRNC.md`, with the VBAT bulk-capacitance analysis.
- `parts/CL10A106KP8NNNC.md`, `CL05B104KO5NNNC.md`, `CL10A225KO8NNNC.md`.
- `parts/CL05A105KO5NNNC.md` (the BOM part) and `CL05A105KA5NQNC.md` (the recommended part).
- `parts/MLZ2012M100WT000.md`.
- `parts/_jlc_availability.md`.
- Facts F-301 to F-307. Open questions Q-PB-07, Q-PB-08 and Q-PB-09 in `state.json`.

## Findings that change the design

1. **Bulk capacitance:**
   - At 3.0 V, 2 × 22 µF 0603 deliver 21.5 µF, and the whole VBAT net 28 µF (19.7 µF worst case).
   - The CC2340 falling-slew rule needs ≥ 14.2 µF at the ring start, so the margin is only 1.39×.
   - Recommendation: a third 0603 22 µF (Q-PB-07).
2. **C9/C10:** the BOM MPN and its LCSC number are two different parts. The 25 V part (C52923) is basic and has twice the effective capacitance at 6.6 V (Q-PB-08).
3. **L1:** the maximum height is 1.45 mm, not 1.0 mm. The DCR is 470 mΩ, a third of TI's reference inductor. TI requires only 10 µH.
4. **JLC stock:** Y1 (4), BT1 (12) and L2 (0) block a JLC build. ANT1 (95) and LS1 (535) limit the build size. C13/C14 has a basic substitute (C1547). R1 has a preferred-extended substitute (C25130) (Q-PB-09).
5. **Size limits in the BOM:** CL10A226MQ8NRNC is 1.80 × 1.00 × 1.00 mm, with ±0.20 mm tolerance. The BOM gives 1.7 × 0.9 × 0.9.

## Method that worked

- **JLC stock, class and price ladders:** POST `{"keyword": "<LCSC or MPN>", "currentPage": 1, "pageSize": 10}` to `https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`.
- **LCSC price ladders and parameters:** `https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=<Cxxxx>`. The LCSC search endpoint returned "Access Denied".
- **Samsung DC-bias curves:** the product page `product.samsungsem.com/mlcc/<PN without packaging letter>.do` embeds a `datasheetData = [...]` JSON with graph type `DCBias`. Parse it and interpolate.
- **DigiKey through `r.jina.ai`:** the product data sits after the first 100,000 characters, so read with offset 100000.
- **TI LaunchPad BOM:** in `https://www.ti.com/lit/zip/SWRC397`.

## Sources that failed

- The LCSC product page redirected to the datasheet PDF.
- The LCSC search API returned 403.
- The TDK page returned 403 directly; it worked through r.jina.ai.
- The TI LP-EM-CC2340R5 tool page returned 404.
- The Murata LQM18DN100M70 page returned "not found".
- The JLC help page on basic and extended parts did not render.
- DigiKey for CL05B104KO5NNNC returned an empty page.
- The Samsung CL21A225KAQNNN page returned HTTP 500.

## Not verified

- The JLC extended-part fee (US$ 1.53 per type, taken from the toolkit tariff).
- The VDDR operating voltage.
- The CR2032 source resistance (battery-and-power's part).
- The DC-bias curve of the Murata alternatives.
