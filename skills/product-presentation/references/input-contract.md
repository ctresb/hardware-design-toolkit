# Input contract of `build_presentation.py`

All paths are relative to the workspace folder passed as the first argument (default `hw`). Every input is optional. A missing input removes its slide. The renders, blueprint, architecture, components, battery, doability, cost, certification and roadmap inputs also add a row to the "Not produced yet" slide.

## `brief.md` (product-discovery template)

| Read | From |
|---|---|
| Product name | the first `# ` heading, without a leading `Product brief:` |
| Date | `**Date:** YYYY-MM-DD` |
| Idea (statement slide) | the plain paragraphs of the `## 1. Idea` section; the section number is optional |
| Users and use | `- **Label:** value` bullets of the `## 2. Users and use` section |
| Environment | the first table of `## 3. Environment`, with columns condition, expected and design answer; rows with an empty "expected" cell are skipped |
| Size tile | the `**Size target:**` bullet of `## 4. Body`, up to the first ` · ` |

## `renders/` and `drawings/`

- Image types: `.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`, `.gif`.
- **Order:** the canonical stems come first, in this order: `hero`, `desk`, `hand`, `dark`, `exploded`, `lineup`, `blueprint`, `architecture`. Every other stem follows, sorted by name.
- **One file per stem:**
  - in `renders/`, a raster wins over an SVG, so a real render replaces an SVG of the same name;
  - in `drawings/`, the SVG wins.
- **Slides:**
  - the first render is the cover (or `deck.json` `"hero"`), and every other render gets its own slide;
  - a stem containing `dark`, `night`, `led` or `escuro` gets a dark slide;
  - `drawings/architecture.*` is used on the "What is inside" slide, not as a drawing slide.
- **Captions:** `renders/captions.json` and `drawings/captions.json` map a stem (or a file name) to a caption. `deck.json` `"captions"` overrides both.

## `architecture.svg|png` or `architecture.md`

- An image at `hw/architecture.svg|png|jpg` or `hw/drawings/architecture.svg|png` is shown as is.
- Otherwise, the first `mermaid` code block that starts with `flowchart` or `graph` is drawn natively. It supports:
  - nodes `A[label]`, `A(label)`, `A((hub))` and `A{label}`;
  - edges `-->`, `==>`, `---`, `-.->` and `-- label -->`;
  - chains such as `A --> B --> C`.

  `subgraph`, `classDef` and `style` lines are ignored. Plain paragraphs outside the code block become the note under the diagram.

## `bom.csv` (CONVENTIONS.md §5)

| Columns read | Use |
|---|---|
| `ref`, `qty`, `function` | first column |
| `mpn`, `manufacturer`, `package` | part column |
| `price_1`, `price_100`, `price_1k` | price columns |
| `distributors` | Where to buy |
| `alternatives` | Alternatives, separated by `;` |
| `evidence` | the evidence pill |
| `stock_snapshot` | the "BOM in stock" item of the build package; it must start with a number |
| `source_date` | the date note under the table |

Rules for the `distributors` column:

- Entries are separated by `;` or `|`. Each entry is a name, `Name: https://…` or a bare URL.
- A known distributor name gets a search link for the MPN. The known names are DigiKey, Mouser, LCSC, Octopart, Arrow, Farnell, Newark and TME.
- An MPN that starts with `EXAMPLE` gets no link.

## `power/budget.json` (`battery-and-power/scripts/power_budget.py -o`)

| Fields read | Use |
|---|---|
| `target_runtime_h` | the target line |
| `battery.rated_mah`, `nominal_v`, `usable_fraction` | the title and the subtitle |
| `scenarios[].scenario`, `avg_ma`, `runtime_new_h`, `runtime_eol_h` | the chart rows |
| `limits[].name`, `max_ma`, `worst_peak_ma`, `ok` | the peak checks |
| `measured_avg_ma` | the evidence tag: a value means `verified`, null means `est.` |

- The chart row of each scenario spans from end of life to a new cell.
- A row "meets the target" when its end-of-life runtime is at least `target_runtime_h`.
- The axis unit is picked from the data: h, days, months or years.

## `doability/score.json` and `doability/findings.json` (doability-review)

`score.json` is the output of `doability_score.py --json` and the canonical verdict. `findings.json` is the
reviewer's input to that script. The builder reads `score.json` first and falls back to `findings.json`.

| Field | Values and use |
|---|---|
| `overall` (score.json) | `READY TO BUILD (prototype)`, `READY TO BUILD (production)` or `NOT READY`. The one overall-verdict key of the toolkit, also read by `build-package`. Legacy values are mapped: `GO` → ready (prototype); `GO-WITH-CHANGES` and `NO-GO` → not ready. Computed from the areas when absent. |
| `areas[]` | `{area, status}` (score.json) or `{area, verdict}`, with `GO`, `FIX`, `BLOCKED` or `NOT-REVIEWED`. Legacy `GO-WITH-CHANGES` → FIX, `NO-GO` → BLOCKED. Computed from the findings when absent. |
| `blockers[]` (score.json) | `{title, action, owner}`. Shown when the design is not ready. |
| `findings[]` | `id`, `area`, `severity` (`critical`/`major`/`minor`/`info`), `status` (`open`/`fixed`/`accepted`), `title`, `fix`, `owner` |
| `build_package` | `{routed_board: true, drc_erc_zero: false, …}` (doability_score.py keys). Overridden by `build-package`'s `release-check.json` when a release exists. When neither exists, the builder checks the workspace: `pcb/**/` fab files, BOM stock, `mech/**/*.step`, `**/assembly*.md`, `**/test*plan*.md` and `**/order*.md`. |
| `prototype_checks[]` | `{what, method, instrument, pass_criteria}`: the "Verify on the prototype" list. Shown when the design is ready. Legacy `verify_on_prototype[]` `{measurement, method, pass}` is still read. |
| `maturity` | `concept`, `pre-EVT`, `EVT`, `DVT` or `PVT`. Shown on the cover. |
| `score` (score.json) | shown small, never as the headline |

## `release/<rev>/checks/release-check.json` (build-package)

The latest release's gate result. Each check id (`routing`, `drc`, `assembly`, `stock`, `mech`, `validation`,
`docs`, `order`) is one line of the build package checklist: `fail` → missing, `warn` → partial, else done.

## `doability/review.md` (fallback: `doability/report.md`)

The numbered or bulleted list under a `## Must be measured or quoted` heading (or `## Next steps`, or `## RFQ…`) becomes the "Next steps" slide. `deck.json` `"next_steps"` overrides it.

## `cost/model.json` (`cost-and-sourcing/scripts/cost_model.py`)

| Fields read | Use |
|---|---|
| `date` | the date note |
| `tiers[].units` | the tier |
| `recurring`, `nre_per_unit`, `total` | each a `[low, high]` pair |
| `landed[0].name`, `landed[0].per_unit` | the landed column, first destination only |
| `nre_items[]` | `{name, group, value, evidence}` |
| `nre` | the total one-time cost |
| `verified_share` | the share of the cost that rests on verified prices |

The one-time cost slide uses the tier in `deck.json` `"nre_tier"` (default 1000), or the last tier.

## `compliance/matrix.md` (`compliance_matrix.py --out`)

- The table whose first header is `Scope` gives the certification table: market, cost range and longest lead time.
- The bullets `- **BLOCKING:** …`, `- **DESIGN RISK:** …` and `- **CRITICAL PATH:** …` become flags, at most five.
- `hw/compliance.md` is read when `matrix.md` is absent. Both are compliance-planner outputs: the matrix holds the rows, `compliance.md` the decisions.

## `roadmap/schedule.md` (`roadmap.py --md`)

- The table whose first header is `Stage` gives one Gantt row per stage. Its columns are stage, weeks, start (best → worst), end (best → worst), exit gate and critical. The dates are `YYYY-MM-DD`.
- The `Milestone` table gives the milestone list.
- `**Finish:** …` gives the title.
- When `schedule.md` has no `Stage` table, `hw/roadmap/timeline.svg` (also written by `roadmap.py`) is embedded instead. `hw/roadmap.md` is read when `schedule.md` is absent.

## `presentation/deck.json`

See `templates/deck.example.json`.

| Key | Use |
|---|---|
| `title`, `date`, `maturity` | override the brief and the review |
| `theme` | `auto`, `light` or `dark` |
| `hero` | a path relative to `hw/` |
| `slides` | order and selection. The ids are `cover`, `idea`, `highlights`, `use`, `renders`, `drawings`, `architecture`, `components`, `power`, `doability`, `verify` (all prototype checks, 6 per slide), `risks`, `cost` (chart and table), `nre`, `compliance`, `roadmap`, `next`, `pending` and `sources`. |
| `highlights[]` | `{value, label, evidence}` |
| `hero_fit` | `contain` keeps the whole cover image; default crops a portrait hero to 4:5 around its centre |
| `components_per_slide` | rows per components slide, default 5 |
| `architecture_note` | one short paragraph under the diagram; default is the first paragraph of `architecture.md`, cut at 320 characters |
| `captions` | stem → caption |
| `nre_tier` | the tier used on the one-time cost slide |
| `next_steps[]` | the "Next steps" slide |
