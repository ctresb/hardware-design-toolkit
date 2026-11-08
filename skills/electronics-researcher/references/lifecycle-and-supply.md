# Lifecycle and supply

## Lifecycle words (use the manufacturer's word in the dossier)

| Word in dossier | Typical maker labels | Design in? |
|---|---|---|
| `production` | Active, Mass production, In production | yes |
| `preview` | Preview, Advance information, Engineering samples | only with a plan B; specs may change |
| `sampling` | Early sampling, Sampling, Pre-production | prototypes only, unless the maker confirms a production date in writing |
| `nrnd` | NRND, Not recommended for new designs | no; choose a successor unless the maker confirms long-term supply |
| `eol` | Last time buy, End of life announced | no |
| `obsolete` | Obsolete, Discontinued | no |

The maker's label wins over the distributor's. If they differ, put the distributor's label in `lifecycle_distributor`, and add a note.

## Supply-risk signals

Rate each part `low`, `medium` or `high` in the dossier's Risks section.

| Signal | Risk |
|---|---|
| Stock at 2 or more authorized distributors, lead time ≤ 12 weeks | low |
| Stock at one authorized distributor only | medium |
| Factory lead time 16–26 weeks | medium; buy prototype and pilot quantities early |
| "No backorders", purchase limits, allocation notices | high |
| Zero authorized stock, no in-stock date | high |
| Stock only at brokers | high: cannot be ordered |
| Sold direct only, no public price | medium; RFQ needed, MOQ unknown |
| Single source, no drop-in alternative | medium to high |
| Lifecycle `sampling`, `nrnd`, `eol` or `obsolete` | high |

## Alternatives

Classify each alternative:

- **drop-in:** same footprint and pinout, compatible specs. You have compared both datasheets' pin tables and package drawings.
- **needs change:** name the change, e.g. "larger package, re-place", "different I²C address", "needs 3 V rail", "different firmware driver".

Give at least one alternative for every part with medium or high risk. For passives, list 2–3 approved brands for each value.

## Price breaks

- Record the price at quantities 1, 10, 100, 1k and 10k. Where a break is missing, use the next lower one and say so.
- Reel quantities (e.g. 1.5k, 3k, 4k, 10k) set the real price at volume. Quote the reel that matches the build.
- Prices are per unit, in USD, from the source and date in `source_date`. Exclude tax and shipping.
- At 10k and above, distributor prices are a ceiling. The real price comes from a quote from the maker or its franchised distributor. Mark it `[estimate]` and add an RFQ.
