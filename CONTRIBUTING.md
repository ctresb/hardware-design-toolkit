# Contributing to Hardware Design Toolkit

Contributions that improve physical/electrical accuracy, CAD/EDA verification gates, and cross-platform agent compatibility are welcome.

## Development & Test Suite

All verification scripts use the Python standard library (Python 3.10–3.13) unless they specifically target Blender (`bpy`), KiCad (`pcbnew`), or `build123d`.

Run the unit and self-test suite from the repository root:

```sh
python3 skills/build-package/scripts/selftest.py
python3 skills/compliance-planner/scripts/test_compliance_matrix.py
python3 skills/cost-and-sourcing/scripts/test_cost_model.py
python3 skills/doability-review/scripts/test_doability_score.py
python3 skills/electronics-researcher/scripts/test_bom_merge.py
python3 skills/pcb-engineer/scripts/test_tools.py
python3 skills/product-render/scripts/test_solder_geom.py
python3 skills/prototype-roadmap/scripts/test_roadmap.py
python3 skills/technical-drawing/scripts/test_line_clean.py
```

## Guidelines

1. **Respect the `hw/` Single-Owner Contract:** Every file in `hw/` has a single owning skill defined in [CONVENTIONS.md](CONVENTIONS.md).
2. **Evidence Tags Required:** Every quantitative output must carry `[verified: source, YYYY-MM-DD]`, `[estimate: basis]`, or `[assumption]`.
3. **Deterministic Scripts:** Prefer standard-library Python scripts with unit tests over prose-only instructions whenever a physical, electrical, or geometric constraint can be computed.
