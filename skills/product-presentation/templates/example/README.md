# Test fixture: builder input

**This folder is a test fixture for `scripts/build_presentation.py` and `scripts/layout_check.py`. It is not an example product.** It describes a fictional 28 mm Bluetooth LE item finder: CR2032 coin cell, magnetic buzzer, one white LED, one button. Part numbers start with `EXAMPLE-`, and every price, current and date is an illustrative estimate or assumption.

Each file has the format of the script that owns it, so the builder sees real input:

| File | Made by |
|---|---|
| `hw/brief.md`, `hw/requirements.md`, `hw/architecture.md`, `hw/bom.csv` | by hand, in the toolkit formats |
| `hw/power/budget.json` | `battery-and-power/scripts/power_budget.py hw/power/budget_input.json -o hw/power/budget.json` |
| `hw/cost/model.json`, `cost.md`, `cost.svg` | `cost-and-sourcing/scripts/cost_model.py --bom hw/bom.csv --mfg hw/cost/manufacturing.json --out hw/cost --svg` |
| `hw/doability/score.md`, `score.json` | `doability-review/scripts/doability_score.py hw/doability/findings.json --md … --json …` |
| `hw/compliance/matrix.md` | `compliance-planner/scripts/compliance_matrix.py --traits hw/compliance/traits.json --out …` |
| `hw/roadmap/schedule.md`, `timeline.svg` | `prototype-roadmap/scripts/roadmap.py --stages hw/roadmap/stages.json --md … --svg …` |

There are no renders and no drawings. The deck must show them on its "Not produced yet" slide.

Test, writing outside the fixture:

```
python3 scripts/build_presentation.py templates/example/hw -o /tmp/deck-test/index.html --check
```

Expected result: 18 slides, `layout check: 0 finding(s)` at 1440, 1280, 1024, 768 and 390 px in light and dark, and `0 problem(s)` from `--check`.
