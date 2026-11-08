---
mpn: <full orderable MPN with packaging suffix>
aliases: <truncated or old numbers; other reel suffixes>
manufacturer: <maker>
function: <one line>
package: <name, pin count>
size_max_mm: <LxWxH from package drawing maximums>
supply_range_v: <min-max>
io_range_v: <min-max or ->
typ_current_ma: <number>
peak_current_ma: <number>
lifecycle: <production|preview|sampling|nrnd|eol|obsolete>
lifecycle_distributor: <label or ->
key_specs: <spec 1; spec 2; spec 3>
distributors: <Name=url; Name=url>
price_1: <USD>
price_10: <USD>
price_100: <USD>
price_1k: <USD>
price_10k: <USD or ->
lead_time_wk: <weeks>
stock_snapshot: <Distributor=qty; Distributor=qty>
alternatives: <MPN (drop-in); MPN (needs change: ...)>
evidence: <verified|estimate|assumption>
source_date: <YYYY-MM-DD>
notes: <the one risk that matters most>
---

# <MPN>: <short function>

## Identity

- Manufacturer:
- Full orderable MPN, and what each suffix means [verified: datasheet §Ordering]:
- Family and variants considered:
- Datasheet revision and date:

## Why this part

What the design needs from it (from `hw/requirements.md`), and how this part meets it.

## Key specs

| Spec | Value | Condition | Source |
|---|---|---|---|
| Supply voltage | | recommended operating | [verified: datasheet p.] |
| | | | |

## Package and dimensions

| | Nominal | Maximum | Source |
|---|---|---|---|
| Length | | | |
| Width | | | |
| Height | | | |

Pitch, exposed pad, MSL, reflow limit:

## Power

| Mode | Typical | Maximum | Condition | Source |
|---|---|---|---|---|
| Active | | | | |
| Idle | | | | |
| Sleep / shutdown | | | | |
| Peak | | | | |

## Interfaces

Bus, address and how it is set, logic levels, required pull-ups, interrupts.

## Lifecycle

| Source | Status | Date |
|---|---|---|
| Manufacturer | | |
| Distributor | | |

## Price breaks (USD per unit)

| Source | 1 | 10 | 100 | 1k | 10k | Packaging | Date |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## Stock and lead time

| Source | Authorized stock | Factory lead time | Limits / notes | Date |
|---|---|---|---|---|
| | | | | |

## CAD models

| Kind | Source | Trust |
|---|---|---|
| Footprint | maker / KiCad library / SnapEDA / Ultra Librarian | checked against the package drawing? |
| Symbol | | pinout checked against the datasheet? |
| 3D model | | dimensions checked? |

## Alternatives

| MPN | Class | Difference | Price at 1k | Source |
|---|---|---|---|---|
| | drop-in / needs change: … | | | |

## Checks against the design

- Rail `<x V>` inside the supply range:
- Maximum dimensions inside the size budget:
- I²C address free:
- Package inside the fab's published capabilities:

## Risks

| Risk | Rating | Mitigation |
|---|---|---|
| | low / medium / high | |

## Conflicts between sources

| Field | Value A (source) | Value B (source) | Decision and reason |
|---|---|---|---|

## Open questions and RFQs

-

## Sources

| Source | URL | Read on | Result |
|---|---|---|---|
| | | | read / 403 / 404 / timeout / CAPTCHA |
