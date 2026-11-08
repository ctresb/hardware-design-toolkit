---
mpn: TC2030-IDC-NL
aliases: TC2030-NL footprint
manufacturer: Tag-Connect
lcsc: -
function: Programming and debug cable (tooling, not on the BOM); the board carries only the TC2030-NL footprint
package: 6-pad PCB footprint, no-legs version
size_max_mm: -
supply_range_v: -
io_range_v: -
typ_current_ma: 0
peak_current_ma: 0
lifecycle: production
lifecycle_distributor: -
key_specs: 6-pin plug-of-nails; footprint about the area of an 0805 resistor; no-legs version held by hand or by TC2030-CLIP
distributors: Tag-Connect=https://www.tag-connect.com/product/tc2030-idc-nl
price_1: 33.95
price_10: -
price_100: -
price_1k: -
price_10k: -
lead_time_wk: -
stock_snapshot: -
alternatives: TC2030-CTX-NL (Cortex 10-pin end, not checked); 1.27 mm test pads with a pogo fixture (needs change)
evidence: verified
source_date: 2026-11-08
notes: tooling bought once per bench; DigiKey has no TC2030-IDC-NL listing. TI XDS110 is not listed by Tag-Connect as a supported probe: confirm the debug probe before ordering
---

# TC2030-IDC-NL: programming cable for the TC2030-NL footprint (tooling)

The file name starts with `_`, so `bom_merge.py` skips it. This item is bench tooling, not a BOM line.

## Facts

| Item | Value | Source |
|---|---|---|
| Price | USD 33.95 (10-inch: TC2030-IDC-NL-10) | [verified: tag-connect.com product page via r.jina.ai, 2026-11-08] |
| Board area | "tiny 0.02 sq inch", about an 0805 | [verified: same page] |
| Retention | no-legs version: hand-held or with TC2030-CLIP | [verified] |
| IDC end | 6-pin, 0.1 in pitch ribbon connector | [verified] |
| Listed probes | ST-LINK, Segger J-Link (SWD), PEmicro, others. TI XDS110 not listed | [verified] |
| Pad sizes and keep-out | not on the product page; in the "TC2030-IDC-NL Datasheet Rev B" and the footprint downloads | not read |

## Open items for pcb-engineer

- Draw the footprint from Tag-Connect's datasheet or official KiCad footprint, including the keep-out for the clip.
- Confirm the CC2340R5 SWD probe (TI XDS110 or Segger J-Link) and the cable end before ordering.

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| Tag-Connect product page | https://www.tag-connect.com/product/tc2030-idc-nl | 2026-11-08 | read via r.jina.ai |
| DigiKey search | https://www.digikey.com/en/products/result?keywords=TC2030-IDC-NL | 2026-11-08 | no result |
