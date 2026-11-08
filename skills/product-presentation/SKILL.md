---
name: product-presentation
description: Builds the final design-review deck of a hardware product as one HTML file (plus PDF), from the hw/ workspace. The deck covers renders, blueprint, architecture, components with where to buy and alternatives, battery life, ready-to-build status, cost per unit, certifications, roadmap and next steps. A browser layout lint then checks it. Use for "make the presentation", "deck", "pitch the product", "show me everything", or the last stage of hardware-engineer.
---

# Product presentation

This skill turns the project workspace into a deck that a founder, a manufacturer or an investor can read in ten minutes. Every slide comes from a file another skill produced. The deck adds no fact, no claim and no art of its own.

Talk to the user in their language. The deck itself stays in the language of `hw/brief.md`. Set `"lang"` in `deck.json` when it is not English.

## Inputs

The builder reads only what exists. A missing input removes its slide and adds a row to a final **"Not produced yet"** slide, which names the skill that produces it. It never draws placeholder art. The exact formats are in `references/input-contract.md`.

| Slide | File | Producer |
|---|---|---|
| Cover, idea, use, key numbers | `hw/brief.md` | product-discovery |
| Renders, one per slide | `hw/renders/hero.png`, `desk.png`, `hand.png`, `dark.png`, `exploded.png`, `lineup.png` (any other name follows, sorted by name), plus `captions.json` | product-render |
| Blueprint | `hw/drawings/blueprint.svg` (SVG preferred over PNG), plus `captions.json` | technical-drawing |
| What is inside | `hw/architecture.svg`, or a Mermaid `flowchart` in `hw/architecture.md` (the builder draws it) | specs-engineer |
| Components | `hw/bom.csv` (CONVENTIONS.md §5) | specs-engineer, electronics-researcher |
| Battery life | `hw/power/budget.json` (output of `power_budget.py -o`) | battery-and-power |
| Ready to build, open findings | `hw/doability/score.json` (canonical verdict, key `overall`; output of `doability_score.py --json`) and `hw/doability/findings.json` (findings) | doability-review |
| Build package checklist | `hw/release/<rev>/checks/release-check.json` (output of `release_check.py`), latest release | build-package |
| Cost per unit, one-time costs | `hw/cost/model.json` (output of `cost_model.py`) | cost-and-sourcing |
| Certifications | `hw/compliance/matrix.md` (output of `compliance_matrix.py`), else `hw/compliance.md` | compliance-planner |
| Roadmap | `hw/roadmap/schedule.md` (output of `roadmap.py --md`), else `hw/roadmap/timeline.svg`, else `hw/roadmap.md` | prototype-roadmap |
| Next steps | the "Must be measured or quoted" list in `hw/doability/review.md`, or `next_steps` in `deck.json` | doability-review |
| Overrides | `hw/presentation/deck.json` (`templates/deck.example.json`) | this skill |

A real render (`hero.png`) replaces an SVG of the same name. Captions are keyed by file stem (`"hero"`), so they survive the swap.

## Outputs

- `hw/presentation/index.html`: self-contained. Images are inlined below 25 MB in total (`--inline-limit`). Above that, they are copied to `hw/presentation/assets/`.
- `hw/presentation/presentation.pdf` with `--pdf`: one 1600 × 900 page per slide, printed by headless Chrome, Chromium or Edge.
- `hw/presentation/layout-check/`: `findings.json` and screenshots of the slides that fail.

## Gate

The deck is done when all of these are true:

1. `layout_check` passes at 1440, 1280, 1024, 768 and 390 px, in light and dark. It finds no overflow, overlap, crowding, edge or spill. `build_presentation.py` runs it automatically when a browser is available and exits with code 4 on any finding.
2. `--check` (the chart geometry check) reports no problem.
3. You have looked at every screenshot yourself.
4. Every number on a slide carries its evidence tag, or comes from a file whose evidence the "How to read the numbers" slide explains.

## Method

1. Make sure the producing skills have run, then run the builder:
   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/build_presentation.py hw --check --pdf
   ```
2. Read the summary line. `missing inputs` lists the slides that are absent. Decide with the user whether to produce them now or to ship the deck with the "Not produced yet" slide.
3. Look at the screenshots. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/layout_check.py hw/presentation/index.html --shots all` to get every slide at 1440 px. Fix each finding at its source:
   - a style or chart issue: in this skill's builder;
   - a too-long text: in the producing file, by shortening the caption or splitting the table.

   Never hide a finding with CSS. Rerun until the gate passes.
4. Order and trim with `deck.json` when the audience needs it. An investor deck can skip `nre` and `compliance`. A manufacturer deck keeps them.
5. Present the result in a few sentences: what the deck shows, the ready-to-build status, and what is "not produced yet".

## Writing on slides

- **One idea per slide.** The title states the conclusion, for example "Baseline lasts 13–15 months on a 225 mAh cell". It is not a topic like "Battery".
- **Experience before specification.** Write "15 months on one coin cell" before "18 µA average". The data stays one level below.
- **Say it once.** No eyebrow labels, taglines or summary paragraphs that repeat the title. A caption adds a fact or is left out.
- **Never invent.** Do not add highlights, quotes, metrics or claims that are not in the workspace. Text that a user wrote is quoted as written.
- **Be honest about status.** Show the maturity on the cover. Estimates carry `est.`. Missing parts appear on "Not produced yet". Never use a stock photo or placeholder art for the product.

## Taste and pitfalls

- **Charts follow the dataviz rules:**
  - one axis and one unit, picked from the data;
  - round ticks such as 0, 6, 12, 18 months;
  - thin bars with 4 px ends;
  - the value at the tip, and solid hairline gridlines;
  - a dashed target line, labelled above the plot area;
  - emphasis by color (meets the target, or below it) with a legend.
  Labels never touch a line: the builder measures them and moves them past the target, or inside the bar, or onto a halo in the page color.
- **Chart colors were validated with the dataviz palette validator:** `#E8590C` on light and `#E8661C` on dark, for single-series marks. Status colors (green, amber, red) always come with an icon and a label.
- **Stat tiles fit to width.** The number shrinks down to a floor, then the unit wraps onto its own line, smaller and lighter. The evidence pill stays with the last word of its label.
- **Tables stack into cards below 900 px.** Every cell carries its header as a label. Numbers use tabular figures and align right.
- **Images:**
  - render slides show the whole image (`object-fit: contain`), never cropped;
  - a file name with `dark`, `night` or `led` gets a dark slide;
  - drawings sit on white.
- **Ready-to-build slide:**
  - the headline is the overall status: "Ready to build · prototype", "Ready to build · production" or "Not ready to build";
  - under it: GO, FIX or BLOCKED per area, and the build package checklist;
  - then "Verify on the prototype" when the design is ready, or the blockers with their exact actions when it is not.
  The score, if any, stays small.
- **Print:** `@page` is 1600 × 900 px with one slide per page. The theme button and tooltips are hidden. Print uses the light theme unless `--theme dark` is set.

## Files

- `scripts/build_presentation.py`: the builder. It uses the standard library only. `--help` lists the options.
- `scripts/layout_check.py`: the browser layout lint. It also runs on its own.
- `references/input-contract.md`: every input path, the fields read from it and the fallbacks.
- `templates/deck.example.json`: overrides for slide order, hero, highlights, captions, theme and next steps.
