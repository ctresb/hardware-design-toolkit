# Conventions

Every skill, script and template in this toolkit follows these rules. Contributors and agents read this file before they add or change anything.

## 1. Purpose

The toolkit takes a person with an idea for a physical electronic product to a **doable** design. A doable design has:

- parts that exist, can be bought, and fit;
- a battery that real cells can deliver;
- a PCB that a named fab can build;
- an enclosure that can be molded;
- certifications that are known and budgeted;
- costs at 1, 10, 100, 1k and 10k units, with the source of every number.

The toolkit does not produce a product that only looks good in a render.

The output is **READY TO BUILD**: the final version, with nothing left to change. A finding that the
toolkit can fix is fixed before delivery. Only items that need the user or the physical world stay open,
for example a measurement on the built prototype. Each such item has a plan and a pass threshold. See
`build-package` and `doability-review`.

## 2. Repository layout

```
.claude-plugin/plugin.json        plugin manifest
.claude-plugin/marketplace.json   marketplace manifest (this repo is its own marketplace)
skills/<skill-name>/SKILL.md      one skill per folder; folder name = `name` in front matter
skills/<skill-name>/references/   long reference material, loaded only when needed
skills/<skill-name>/scripts/      executable tools used by the skill
skills/<skill-name>/templates/    files the skill copies into the user's project
assets/                           logo and README images
docs/                             toolkit-level documentation
examples/                         a complete, fictional example project
```

## 3. Skill format

- Front matter has exactly `name` and `description`.
  - `name` is the folder name, in lowercase with hyphens.
  - `description` says what the skill does and when to use it, including trigger phrases. Write it in the third person, in 600 characters or fewer.
- The SKILL.md body is under about 350 lines. Detail goes in `references/*.md`. SKILL.md links each reference and says when to read it.
- Refer to bundled files by paths relative to the skill's base directory, for example `scripts/power_budget.py`. Claude Code shows the base directory when it loads a skill.
- Name the other skills of the toolkit by their skill name, for example "run `doability-review`".
- All files are in English. Each skill tells Claude to talk to the user in the user's language.
- Each skill states these four things, each in its own short section:
  - **Inputs:** the files it reads from the project workspace (section 4).
  - **Outputs:** the files it writes there.
  - **Gate:** what must be true before the next stage starts.
  - **Taste and pitfalls:** the concrete mistakes to avoid (section 7).

## 4. The project workspace (shared contract between skills)

All skills read and write one folder in the user's project: `hw/`. The `hardware-engineer` skill creates it.

| Path | Owner skill | Content |
|---|---|---|
| `hw/state.json` | hardware-engineer | stage status, open questions, gates passed |
| `hw/toolchain.json` | toolchain-setup | resolved tool paths (overrides `~/.config/hardware-design-toolkit/toolchain.json`) |
| `hw/brief.md` | product-discovery | what the product is, who uses it, where, how, size, budget, markets, quantities |
| `hw/refs/` | product-discovery | reference images, sketches and outlines from the user, unchanged |
| `hw/requirements.md` | specs-engineer | numbered requirements `REQ-001…`, each with a target, a limit and its source |
| `hw/architecture.md` | specs-engineer | block diagram (Mermaid), power rails, buses, interfaces |
| `hw/bom.csv` | specs-engineer creates; electronics-researcher fills | canonical BOM (section 5) |
| `hw/parts/<MPN>.md` | electronics-researcher | one dossier per part |
| `hw/power/` | battery-and-power | `budget.json`, `rails.json`, `battery.json`, `power.md`, cell outline SVG |
| `hw/pcb/` | pcb-engineer | `board.json` spec, KiCad projects, ERC/DRC reports, `export/pads.json` (the one pads export), fab outputs |
| `hw/mech/` | enclosure-engineer | CAD spec and build123d source, STEP/STL/GLB, `assembly_golden.blend`, tolerance study, DFM notes |
| `hw/validation/` | enclosure-engineer | assembly validator reports (`assembly.json`, `assembly.txt`) |
| `hw/renders/` | product-render | renders and their scene scripts |
| `hw/drawings/` | technical-drawing | exploded blueprint and orthographic views (SVG/PDF/PNG), item list JSON |
| `hw/cost/` | cost-and-sourcing | `model.json`, `cost.md`, `sourcing.md`, `rfq.md` |
| `hw/compliance.md`, `hw/compliance/` | compliance-planner | the plan (decisions, budget, lead times); `traits.json` and `matrix.md` (generated rows) |
| `hw/roadmap.md`, `hw/roadmap/` | prototype-roadmap | plan; `stages.json`, `schedule.md`, `timeline.svg` |
| `hw/doability/` | doability-review | `findings.json` (review input), `score.json` (canonical verdict: key `overall`, plus `prototype_checks`), `score.md`, `fixes.json`, `review.md` (the human report; never `report.md`) |
| `hw/release/<rev>/` | build-package | the READY TO BUILD package, `MANIFEST.json`, `ORDER.md`, `checks/release-check.json` |
| `hw/presentation/` | product-presentation | `index.html` and a PDF |
| `hw/knowledge/` | lab-notebook | `FACTS.md`, `EXPERIMENTS.md`, `LESSONS.md` |
| `hw/retros/`, `hw/agents/` | lab-notebook | stage retros; subagent reports saved on arrival |
| `hw/decisions.md` | any skill | decision log: `D-001`, date, decision, options, reason, who decided |

A skill never rewrites a file that another skill owns. It writes a request in `hw/state.json` under `open_questions`, or it adds an entry to `hw/decisions.md`.

## 5. BOM columns (`hw/bom.csv`)

`ref, qty, function, manufacturer, mpn, lcsc, package, size_max_mm, lifecycle, key_specs, supply_rail_v, typ_current_ma, peak_current_ma, distributors, price_1, price_10, price_100, price_1k, price_10k, lead_time_wk, stock_snapshot, alternatives, evidence, source_date, notes`

- `size_max_mm` is `LxWxH` taken from the datasheet's **maximum** dimensions, not the nominal ones.
- `mpn` is the full orderable part number, with the packaging suffix.
- `lcsc` is the LCSC part number (`C12345`) for parts placed by JLCPCB assembly, or `-`.
- `supply_rail_v` is the **name** of a rail defined in `hw/power/rails.json` (`VSYS`, `1V8`). A part on two rails lists them as `VSYS|1V8`, in the order of its `vdd`, `vdd2` tokens.
- `key_specs` uses `key=value;` tokens: `vdd=1.7-3.6; vio=1.8; i2c=0x2C; bus=I2C0`.
- `stock_snapshot` reads `<qty> @ <distributor> <date>`, for example `8000 @ LCSC 2026-11-08`.
- `evidence` is `verified`, `estimate` or `assumption` (section 6).
- Prices are in USD. `source_date` is the date of the price check.

## 6. Evidence rules

Every number that can change a decision carries one tag:

- `[verified: <source URL or document + section>, <date>]`. The source was read in this session.
- `[estimate: <basis>]`. Calculated or inferred; the basis is stated.
- `[assumption]`. Chosen for planning; must be replaced by a measurement or a quote.

Further rules:

- Never present an estimate as a fact. A report lists the RFQs and measurements that would replace its estimates.
- Distributor data (stock, price, lifecycle) carries a date. Lifecycle comes from the manufacturer first. A distributor lifecycle label is a second source.
- Name only established manufacturers, distributors and fabs. Do not recommend unknown vendors.

## 7. Taste rules (learned the hard way)

These rules come from real corrections during the design of a small wearable. Each rule is a mistake that was made and fixed.

### Design and engineering

- **Real parts have real shapes.** A pouch battery has straight edges and a sealed border that cannot hold charge. It is not a free-form blob that fills the leftover space. Size parts by the datasheet's maximum dimensions.
- **Measure before you commit to a custom part.** The power budget is measured on a dev kit before you order a custom cell, a mold or a board revision. Products have drawn about 5× the current of a bottom-up datasheet budget.
- **Capacity is energy density × usable volume.** Use cited Wh/L figures for the cell type. A design that claims more is wrong until a cell vendor quotes it.
- **Check every peak current against every limit in the path:** the battery's C-rate, the PMIC's discharge limit, the protection IC, and the regulators. One radio peak can exceed all of them.
- **Check every supply voltage.** Each IC's VCC/VDD range must contain the rail it is connected to.
- **Prefer fewer holes and seams.** Every opening is a sealing, cost and certification problem. Choose molded contacts, membranes and adhesive seals over open ports.
- **Use trusted vendors only.** Check the fab's published capabilities against the design: minimum BGA pitch on flex, solder mask web, panel size, via types.

### Process

- **Validate before you show anything.** Run the geometry validator before any render: no interpenetration, no broken faces. Fix a failure at the source (placement, pocket, part height), never with a whitelist.
- **Freeze a golden state when changes start to regress.** Build geometry once in a fixed order, validate it, save it, and apply appearance-only changes to the frozen file. If two fixes undo each other, stop and redesign the order instead of looping.
- **Ask the questions that change the product. Decide the rest yourself.** Recommend an option, and log the decision.
- **Show progress as images.** Save each render as it arrives.
- **Run heavy compute on a cloud GPU or a strong workstation,** not on a laptop that is also running the session. Shut the machine down afterwards.

### Visual quality

- The product faces the camera. Never render the back by accident.
- Real objects have imperfections: fingerprints, micro-scratches, dust, slight color variation between parts, solder that wets and wrinkles. Perfectly clean surfaces look fake.
- Clear plastic is not glass. Use plastic IOR (~1.49–1.59), slight volume absorption and surface wear.
- Depth of field must be consistent. An object at the same distance as a blurred one must be equally blurred.
- Cords, fabric and hands come from real references or physically based models. Never use a smooth tube.
- Lights are invisible to the camera. A dark studio uses a near-black world, one large soft key, thin strip lights for the edges, and a weak top light.
- Small printed details (markings, labels) can be textures. Geometry is for what changes the silhouette or the reflections.
- Typography and layout in drawings and decks are aligned to a grid. Text never touches edges, and numbers line up with what they label.
- Charts:
  - No text crosses a line, bar or other text. Check every rendered chart for this.
  - One unit per axis, on round ticks: 0, 6, 12, 18 months, not "0 h, 14 months, 2.3 years".
  - The title states the conclusion, and the assumptions go in the subtitle.
  - Target lines are labeled outside the plot area.
- Every visual deliverable passes an automated layout check before anyone sees it:
  - no overflow, no overlapping boxes, no text near the edges;
  - presentations: at five widths, in light and dark;
  - drawings: no label crossing a line.

  A person then looks at the images. A defect the user can see is a failed check, not a matter of taste.
- Never draw a placeholder that pretends to be the product. A round part (a coin cell, a buzzer) is never drawn as a square. If an input is missing, show that it is missing.

## 8. Scripts

- Python 3.10 or newer. CLI with `argparse` and a useful `--help`. No hardcoded paths, accounts or user names.
- Standalone scripts use the standard library only, unless the SKILL.md documents the dependency and `toolchain-setup` installs it.
- Blender scripts run headless: `blender -b scene.blend --python script.py -- <args>`. They may use `numpy`, which Blender bundles. They use `scipy` or `cupy` only when available, with a fallback.
- KiCad scripts run with KiCad's bundled Python (`pcbnew`) or `kicad-cli`. Each script documents the KiCad version it was tested with.
- Each script prints a one-line summary at the end and returns a non-zero exit code on failure.

## 9. Privacy

The repository contains no private data: no names of real unreleased products, no personal paths, no account IDs, bucket names, instance IDs or API keys. Examples use a fictional product.
