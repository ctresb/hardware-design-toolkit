# Experiments

What was tried, and whether it worked. Failures are recorded with the same care as successes.

<!-- Entry format:
## E-001 · YYYY-MM-DD · <short title>
- **Hypothesis:** <what we expected and why>
- **Change:** <what was done, files and parameters>
- **Result:** <what happened, with numbers>
- **Verdict:** worked | did not work | inconclusive
- **Would change the verdict:** <new evidence that would reopen it>
-->

## E-401 · 2026-11-08 · Advertising interval sweep for 12-month life
- **Hypothesis:** an Apple-recommended interval ≤ 1285 ms keeps 12 months in the pessimistic case even if the event charge is 15 µC instead of 10.3 µC.
- **Change:** ran power_budget.py with adv_slow at 1022.5, 1285, 2000 and 4000 ms and event charge 10.3 and 15 µC.
- **Result:** pessimistic end-of-life life 15.7 / 17.7 / 21.6 / 26.9 months at 10.3 µC; 12.0 / 13.8 / 17.2 / 22.3 months at 15 µC. 1022.5 ms fails margin at 15 µC (exactly 12.0).
- **Verdict:** worked
- **Would change the verdict:** EVT measurement M2 above 12 µC per event, or M6 above 14 µA → move to 2000 ms.

## E-402 · 2026-11-08 · Ring drive mode against cold, aged cells
- **Hypothesis:** the 3× piezo mode is usable over the whole cell life.
- **Change:** loaded-voltage table CCV = OCV − I × R_internal for 3× (15.05 mA), 2× (7.25 mA) at estimated R_internal 15–120 Ω.
- **Result:** 3× drops to 2.0 V at 50 % used and −10 °C, and to 1.0 V at 80 % used and −10 °C; 2× holds 2.46 V and 1.93 V.
- **Verdict:** did not work (3× everywhere); adaptive rule 2× start → 3× if ≥ 2.7 V → 1× below 2.3 V proposed (Q-PW-02)
- **Would change the verdict:** measured R_internal (M9) much lower than the estimates.

## E-101 · 2026-11-08 · Reading LCSC, JLCPCB and PDF datasheets from an agent
- **Hypothesis:** LCSC and JLCPCB pages can be read through the reader proxy, and PDFs through a local text extraction.
- **Change:** fetched `https://www.lcsc.com/search?q=<MPN>` directly; then `https://r.jina.ai/https://www.lcsc.com/search?q=<MPN>` and `https://r.jina.ai/https://jlcpcb.com/partdetail/<C-number>`; PDFs fetched to disk and run through `pdftotext -layout`.
- **Result:** the direct LCSC fetch returned only navigation (JavaScript page). The reader proxy returned stock, price breaks and the Basic/Extended tag. Direct PDF reads by the fetch tool returned compressed binary; `pdftotext` on the saved file gave full text for the TI, Diodes, Abracon, Same Sky and Johanson datasheets. Image-only package drawings (TI RGE) gave only the title text.
- **Verdict:** worked
- **Would change the verdict:** the proxy being blocked or rate-limited; then use the distributor API.

## E-201 · 2026-11-08 · Direct datasheet downloads from makers
- **Hypothesis:** maker PDFs can be fetched directly by URL.
- **Change:** curl/WebFetch of TE DocumentDelivery, C&K /media/1480/kmr2.pdf, Lite-On download URL, Energizer cr2032.pdf.
- **Result:** TE returned 403 "Access Denied"; C&K and Lite-On returned HTML; Energizer cr2032.pdf returned 404. The r.jina.ai reader proxy read the TE drawing, and the LCSC product API `pdfUrl` mirror delivered the C&K and Lite-On PDFs.
- **Verdict:** did not work
- **Would change the verdict:** the maker sites allowing scripted downloads. Use the reader proxy or the LCSC mirror first for these makers.

## E-501 · 2026-11-08 · Reading US federal regulations from an agent
- **Hypothesis:** the eCFR renderer API and a guessed Federal Register document URL return the rule text.
- **Change:** fetched the eCFR renderer API, a guessed FR document number, `/citation/88-FR-65274` and eCFR through the r.jina.ai reader.
- **Result:** the eCFR API returned 0 bytes and the guessed FR number opened an unrelated document. The `/citation/<vol>-FR-<page>` URL and the eCFR page through the reader both returned the full text.
- **Verdict:** worked
- **Would change the verdict:** the reader proxy stops serving government pages; then use govinfo.gov PDFs.

## E-520 · 2026-11-08 · Close the LED net with vias under the cell
- **Hypothesis:** an inner-layer jump (F.Cu → In2.Cu → F.Cu) closes U1 DIO24 → R1 if the cell's negative contact pad shrinks from Ø17.8 mm to Ø10 mm (Keystone 3034 minimum 3.96 mm square).
- **Change:** BT1 pad 2 Ø10 mm; two-layer grid A* (`mlroute.py`).
- **Result:** routed, 14.3 mm with 2 vias, but the F.Cu escape ran inside U1's pad ring (between the thermal pad and pins 9–11), and both vias sat under the cell's negative face (r = 5.3 mm and 5.8 mm from the cell centre). With routing inside U1 forbidden, no path existed at any via radius (5.5, 6.5, 7.6, 8.3 mm).
- **Verdict:** did not work
- **Would change the verdict:** filled-and-capped vias (POFV) priced into the order, or a part move that frees a via site outside the cell. The pad was restored to Ø17.8 mm; D-517 stands.

## E-521 · 2026-11-08 · Close the LED net on F.Cu by removing redundant copper
- **Hypothesis:** some F.Cu tracks that wall the LED escape duplicate connections that the GND pour or a part's internal connection already makes.
- **Change:** removed the EP→C21 GND trace (C21 gets its own GND via 0.6 mm from its pad), the GND trace left of SW1 (the pour connects the same pads), and the BTN link between SW1's two "1" pads (internally joined, F-522); then routed on F.Cu only with 0.15 mm clearance.
- **Result:** routed, 10.6 mm, 0 vias; DRC 0, 0 unconnected, parity 0.
- **Verdict:** worked
- **Would change the verdict:** a prototype where SW1's two "1" terminals are not joined (Q-PCB-01).
