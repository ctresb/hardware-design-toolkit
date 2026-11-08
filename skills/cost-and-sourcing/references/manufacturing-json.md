# `hw/cost/manufacturing.json` format

`scripts/cost_model.py` reads this file together with `hw/bom.csv`. A complete fictional example that runs is in `templates/manufacturing.example.json`.

## Values

A value is one of:
- a number: `3.5`;
- a range: `[3, 8]` (low, high);
- a range string from the BOM: `"1.1-1.4"`;
- a per-tier map: `{"1": [60, 250], "100": [25, 50], "1000": [3, 6]}`.

In a per-tier map, the value for a tier is the entry at the nearest tier at or below it. A tier below every key takes the lowest key. Every line carries an `evidence` string that starts with `verified`, `estimate` or `assumption`. A line without one counts as an assumption.

## Keys

| Key | Type | Meaning |
|---|---|---|
| `project`, `currency`, `date` | string | header of the report; `date` is the price date |
| `tiers` | list of int | order sizes to model; default `[1, 10, 100, 1000, 10000]` |
| `bom.path` | string | BOM CSV, relative to this file or absolute (`--bom` overrides it) |
| `bom.attrition` | object | `default_pct`, `min_extra`, and `by_ref_prefix: {"C": {"pct": 5, "min_extra": 20}}`; extra parts bought per order |
| `bom.moq_overrides` | object | per MPN: `moq`, `price` (at or above MOQ), `sample_price`, `sample_max` (largest lot that can be bought as paid samples, default 50); below the MOQ the cheaper of samples and the whole MOQ is used |
| `pcba.tariff` | object | an assembler's published price list (see the example); `fixtures_count`, `per_joint` and `xray_per_component` are `[[upper_bound, value], …]` tables |
| `pcba.boards` | list | per board: `name`, `per_device`, `sides`, `flex`, `joints`, `unique_parts`, `xray_parts`, `panelized` |
| `pcba.evidence` | string | evidence for the tariff |
| `recurring` | list | per-unit lines: `name`, `category`, `value`, optional `qty`, `from_tier`, `to_tier`, `evidence` |
| `per_order` | list | lines paid once per order and spread over it: `name`, `value`, `from_tier`, `to_tier`, `evidence` |
| `yield_loss_pct` | value | scrap percentage by tier; applied to recurring cost before per-order fees |
| `nre` | list | one-time lines: `name`, `group` (tooling, fixtures, certification, battery, packaging, design), `value`, `from_tier`, `to_tier`, `evidence` |
| `landed.fx` | object | `{"BRL": {"rate": 5.5, "evidence": "assumption: …"}}` |
| `landed.destinations` | list | `name`, `multiplier` (on recurring + freight), `freight_per_unit`, optional `fx`, `evidence`, `note`; the output has `recurring_per_unit` (landed, without NRE) and `per_unit` (landed + NRE spread) |
| `targets.unit_cost` | object | recurring (FOB) unit-cost goal per tier, `{"1000": 12, "10000": 8}`; the model, `cost.md` and the chart give each tier `met`, `not proven` (the target is inside the low–high range) or `not met` |

## Modelling tips

- **Change process with the tier, not the price.** Write one NRE line per process, with `from_tier` and `to_tier`. For example, urethane molds for 10–100 units, a rapid aluminum tool for 1,000 units and steel tools for 10,000 units. The model then shows the step that tooling makes.
- **Put certifications in `nre` with `from_tier` set to the first tier you will sell.** Take their values from `hw/compliance.md`.
- **Count joints honestly.** Each pin and each exposed pad is a joint. A QFN-40 with an exposed pad is 41 joints, and a two-terminal passive is 2.
- **Count `xray_parts`.** Every BGA, QFN, LGA, DFN or WSON on the board counts.
- **Keep the BOM electronic-only.** Put the battery in the BOM only if it is bought as a part. Put mechanical parts in `recurring` with their own evidence.
- **Re-run after every quote.** Replace the range with the quoted number and change the tag to `verified: quote <vendor> <date>`. The verified share in `cost.md` rises as quotes arrive.
