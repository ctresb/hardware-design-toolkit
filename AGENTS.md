# AGENTS.md — AI Coding Agent Instructions

This repository contains 17 skills and deterministic Python verification scripts for hardware design (`ctresb/hardware-design-toolkit`).

## Multi-Runtime Path Resolution (`CLAUDE_SKILL_DIR` Fallback)

Skill markdown files reference `${CLAUDE_SKILL_DIR}/scripts/...`. When running inside non-Claude runtimes (Codex, Antigravity, Cursor, OpenCode) where `CLAUDE_SKILL_DIR` is unset, resolve script paths relative to the skill directory:

```sh
export CLAUDE_SKILL_DIR="${CLAUDE_SKILL_DIR:-$(pwd)/skills/<skill-name>}"
```

## Workspace & Ownership Contract

- Read [CONVENTIONS.md](CONVENTIONS.md) and [docs/hardening-and-dfm-gates.md](docs/hardening-and-dfm-gates.md) before modifying any skill or script.
- Every artifact in `hw/` has a single owner skill. Never overwrite a file owned by another skill.
- Preserve KiCad 10 SWIG ownership guards (`thisown = False` before `board.Add(...)`).
- Never pass `--allow-file-access-from-files` to headless Chrome/Chromium; always serve local directories over loopback HTTP (`127.0.0.1`).

## Verification Before Completion

Before opening a pull request or claiming completion, run all test scripts:

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
