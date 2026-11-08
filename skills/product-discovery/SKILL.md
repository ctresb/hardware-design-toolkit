---
name: product-discovery
description: Interviews the user to turn a vague idea for a physical electronic product into a written brief (hw/brief.md) — use, environment, size, interaction, connectivity, battery life, charging, ingress, markets, quantities, budget. Use at the start of any hardware project, or when the user says "I want to build a device that…", "help me design a gadget", "hardware idea", or when hw/brief.md is missing or stale.
---

# Product discovery

Turn an idea into a brief that every later stage can design against. The brief records what the user wants, and what each wish costs physically. Reality checks come later. This stage makes sure the wishes are explicit, measurable and ranked.

Talk to the user in their language. The files are written in English unless the user asks otherwise.

## Inputs

- The user's first description, any reference images, sketches or SVG outlines, and products they mention.
- `hw/brief.md` and `hw/decisions.md`, if they exist (re-interview only what is missing or changed).

## Outputs

- `hw/brief.md`, from `templates/brief.md`. Keep its headings exactly; other skills parse them.
- `hw/decisions.md`: one entry per decision made in the interview (`D-001`, date, decision, options considered, reason, decided by).
- `hw/refs/`: every reference the user gives, copied with a short name. This covers images, sketches and SVG outlines (for example the top-view shape of the device or of a part), plus `hw/refs/README.md`, which lists them with one line each.
- `hw/state.json`: set `stages.discovery = "done"` after the gate. Add any unresolved items to `open_questions`.

## Procedure

### 1. Read before you ask

Extract everything the first message already answers. Restate the idea in two sentences: the job the product does, and the moment of use. Never ask a question the user already answered.

### 2. Interview in rounds

Use `AskUserQuestion`, with at most 4 questions per call and at most 4 rounds in total when possible.

- Put the recommended option first and mark it "(Recommended)". The user can always pick "Other".
- Use `preview` when the user compares shapes, sizes or layouts. ASCII top views with dimensions work well:

  ```
  ┌──────────┐   28 × 28 × 9 mm
  │   ◯ LED  │   pendant, cord loop on top
  └──────────┘
  ```
- Ask only questions that change the product. For everything else, state the default you are taking and log it as a decision. The full bank, with the reason for each question and its typical default, is in `references/question-bank.md`. Read it before round 1.

Suggested order (merge rounds when answers are already known):

1. **Use.** What it does, who uses it, where and how it is carried or mounted, the moment of use, and the products the user admires.
2. **Body.** Size and shape targets, whether size is the top priority, weight, interaction (buttons, touch, LED, sound, haptics), look and finish (colors, transparent variant, materials).
3. **Life.** Battery-life target for each mode (in hours), standby, charging method, connectivity and phone pairing, offline storage, sensors, ingress target.
4. **Business.** Markets where it will be sold, quantities and dates (first prototype, first batch, 1k, 10k), unit-cost target, NRE budget.

Read `references/use-environments.md` once the environment is known. It turns "worn on the chest", "used in the shower" or "for kids" into concrete requirements.

### 3. Be honest about physics, gently

When a wish is expensive, say it once, in one or two sentences, with numbers. Offer two or three options. Record the user's choice; never refuse. Typical cases:

- **Continuous operation in a tiny body.** A coin-sized pendant holds about 0.2–0.3 Wh. Twenty-four hours of continuous audio recording needs an average draw of about 2–3 mA. That is possible only with firmware designed for it from day one.
  - Options: shorter life, a bigger body, or recording triggered by an event (voice, touch).
- **Wi-Fi or cellular in a tiny body.** Peaks of 250–400 mA exceed what a small cell and a small PMIC can deliver.
  - Options: BLE only (the phone relays the data), a bigger cell, or Wi-Fi only on the dock.
- **IP68 with many openings.** Every port, button and seam is a sealing problem.
  - Options: membranes, molded contacts, capacitive touch instead of buttons, fewer openings.
- **Wireless charging in a tiny body.** It adds a coil, heat and thickness, and charges no faster than the cell's own limit allows.
  - Options: magnetic pogo or molded contacts with a dock.
- **"Product X does more in less space."** Accept the reference, and plan to check it with data (teardown, FCC photos, spec sheet) in `doability-review`. Big companies use custom silicon, custom cells and stacked boards.

### 4. Turn wishes into a seed table

Write every wish as a measurable target with priority `must`, `should` or `nice`, the reason, and where it came from. "Small" becomes "≤ 30 × 30 × 9 mm, size is priority 1". "Long battery" becomes "≥ 12 h recording + 7 days standby". `specs-engineer` turns this table into `REQ-xxx`.

Rank the top three priorities explicitly (for example size > battery life > cost). Later trade-offs use this ranking instead of asking the user again.

### 5. Gate: the user approves the brief

Show a short summary in chat:

- the idea in two sentences;
- the top three priorities;
- the five to eight key targets;
- the costly trade-offs and what was chosen;
- the defaults you took;
- the open questions.

Ask with `AskUserQuestion`: "Approve the brief", "Change something", "Add something". Iterate until approved. Then set the state, and hand over to `hardware-engineer` (or to `specs-engineer` if the user is running the stages manually).

## Taste and pitfalls

- **Do not interrogate.** Four rounds of four questions is the maximum, not the target. A clear first message may need one round.
- **Do not ask what a default answers well.** For example: USB-C vs. contacts for a desk device, or the BLE version. State the default and log it.
- **Ask what only the user knows.** Where it is worn, which markets, how many units, what it must feel like, which compromise hurts least.
- **Numbers, not adjectives.** Every target has a unit and a limit, in mm, hours, grams, IP code and USD.
- **Separate modes.** "Battery life" means nothing until each mode has a duration (active, connected idle, standby, shipping), and each mode costs a different current.
- **Never round a wish into something easier without saying so.** If you propose 12 h instead of 24 h, it is a decision with a reason, logged.
- **Keep the user's references as given.** An SVG outline the user drew is a design input. Store it unmodified, and redraw it only on request.
- **A shape must stay buildable.** A battery outline is a pouch with straight edges and a sealed border. An enclosure has draft and minimum walls. Note this in the brief when the user's shape conflicts with it, and let the later stages solve it.
- **Variants are real cost.** Each color or transparent variant needs its own material, molding and validation, and may need its own render. Ask how many variants the first batch has.
- **Markets decide certification.** "Worldwide" is not an answer. Ask which first markets ship in the first year.
