# Stages from idea to sellable product

Each stage builds a specific thing, answers specific questions and ends at a gate. Durations are `[estimate]` for a small team building a small battery-powered connected device. Replace them with quotes and lead times from your own suppliers.

**The rule behind the order:** spend money on custom parts (cells, molds, board revisions) only after the measurement that sizes them. In one real project the custom battery was cut before the power budget was measured. That turned a firmware unknown into a hard autonomy limit.

## Contents

- [Stage 0 — Dev-kit bench](#stage-0--dev-kit-bench)
- [Stage 1 — Works-like and looks-like prototypes](#stage-1--works-like-and-looks-like-prototypes)
- [EVT — Engineering Validation Test](#evt--engineering-validation-test)
- [DVT — Design Validation Test](#dvt--design-validation-test)
- [PVT — Production Validation Test](#pvt--production-validation-test)
- [MP — Mass production](#mp--mass-production)
- [Critical path](#critical-path)
- [Long-lead parts](#long-lead-parts)
- [How many iterations to expect](#how-many-iterations-to-expect)

## Stage 0 — Dev-kit bench

**Duration:** 4–8 weeks.

**What you build:**

- The manufacturer's development kit for the chosen MCU or SoC.
- Breakout boards for the main sensors, microphones and memory.
- The real firmware pipeline: sampling, codec, storage and radio sync.
- A power profiler, for example a Nordic PPK2, Joulescope or Otii, with source-meter mode.

**Questions it answers:**

- **Average current in each operating mode.** Measure it with the real duty cycle, not datasheet typicals. Bottom-up datasheet budgets have been about 5× too optimistic against shipping products.
- **Peak current and its duration.** Check it against the battery, the PMIC and the regulator limits.
- **Pipeline quality.** Does the sensor or audio pipeline reach the target quality: SNR, WER, accuracy?
- **Memory size.** How much storage the target offline time needs: bitrate × hours, plus file-system overhead.
- **Battery capacity.** The capacity that gives the runtime target at end of life with 2× margin. Plan for 80% capacity at end of life and about 85% usable capacity.

**Gate:**

- The measured average current, × 2 margin, fits the cell that fits the enclosure.
- Memory and battery are chosen from measurements and logged in `hw/decisions.md`.
- If the gate fails, change the product (features, size, runtime) now, while the change is cheap.

## Stage 1 — Works-like and looks-like prototypes

**Duration:** 3–6 weeks. It can overlap the end of Stage 0.

**What you build:**

- **Looks-like:**
  - An SLA print of the enclosure. Clear resin is wet-sanded from 400 to 12000 grit, then given a 2K clear coat or dipped for optical parts.
  - For 1–100 clear parts, urethane casting is an option.
- **Works-like:**
  - Dev-kit electronics or a first rough board in a printed shell.
  - A catalogue cell close to the target size, with existing UN 38.3.

**Questions it answers:**

- Does the stack-up fit with real tolerances?
- Is it comfortable to wear or hold for a week?
- Do the buttons, touch and LEDs work through the real wall thickness?

**Gate:**

- People used it in real conditions.
- The stack-up and wall thicknesses are agreed.
- The enclosure geometry passes the assembly validator in `enclosure-engineer`.

## EVT — Engineering Validation Test

**Duration:** 2 board spins of 5–10 weeks each.

**What you build:**

- Routed boards, made at a fab whose published capabilities match the design (BGA pitch, via types, flex rules, mask web).
- The first assembled units.

**What you do:**

1. **Bring-up:** see `bringup-checklist.md`.
2. **Antenna tuning:** use a VNA, with the board inside the real enclosure, with the battery, magnets and metal parts in place, on a body phantom if the device is worn.
3. **Basic RF:** check conducted or radiated power and sensitivity.
4. **Pre-tests:** IPX7, touch through the wall, acoustics.
5. **Firmware:** drivers for every part, a power-safe storage log, OTA update and encryption.

**Gate:**

- Every rail and peripheral works.
- Current is within 20% of the bench figure.
- RF range meets the requirement while worn.
- No open hardware bug needs a board change.
- This is the engineering freeze.

## DVT — Design Validation Test

**Duration:** 12–20 weeks, including tooling.

**What you build:**

- **Production-intent tooling:** aluminum or soft-steel T1, then 1–2 rounds of corrections (T2 and T3).
- **Production cells:** custom-cell samples from the selected vendor.
- **Pilot units:** 50–200, built on the intended process.

**What you do:**

- **Reliability:**
  - drop (for example 1.5 m onto concrete);
  - ESD (IEC 61000-4-2);
  - thermal cycling;
  - sweat and corrosion;
  - IP test;
  - button and connector life;
  - charging thermal profile.
- **Compliance:**
  - pre-scan;
  - formal certification tests on DVT units with final RF settings;
  - UN 38.3 of the production cell.
- **Field:**
  - beta users;
  - field return analysis.

**Gate:**

- All reliability tests pass.
- The certification test reports are issued, or the remaining tests are scheduled with no open failures.
- The cosmetic specification and AQL are agreed with the molder.

## PVT — Production Validation Test

**Duration:** 4–8 weeks.

**What you build:**

- The production line with its fixtures: see `test-fixtures.md`.
- The work instructions and the packaging line.

**What you do:**

- Run a few hundred units on the real line.
- Measure first-pass yield, cycle time and the test escape rate.
- Get first-article reports from the suppliers (cells, inserts, molded parts).

**Gate:**

- First-pass yield is at or above the target, for example 95% or more.
- Fixtures catch the known failure modes.
- Certificates are in hand for every launch market.

## MP — Mass production

- **First lot:** 1k or more, depending on MOQs.
- **Ongoing:** monitor yield and returns, and run an engineering change process for any part change.
- **Second sources:** qualify alternates for the parts with supply risk.

## Critical path

For small battery-powered radio products, the critical path rarely runs through the PCB. It usually runs:

```
power measurement (Stage 0)
  → battery capacity decision
    → custom cell RFQ, samples and approval
      → UN 38.3 of the production cell
        → certification samples can ship
          → radio certification
            → first legal sale
```

The final enclosure tooling depends on the cell's real dimensions, so a late cell also delays the mold. Start the cell RFQ as soon as Stage 0 has measured the current. Run tooling in parallel only when the cell envelope is fixed, with a written tolerance.

## Long-lead parts

- Factory lead times of 16–26 weeks are common for spring contacts, LED drivers, connectors, MEMS sensors and MLCCs in shortage. Check every part's lead time in `hw/bom.csv`.
- Buy EVT and DVT quantities of every long-lead or low-stock part as soon as the part is chosen.
- Track each long-lead part as a `long_lead` entry with `needed_by` in the stages JSON. `scripts/roadmap.py` back-schedules the order date.

## How many iterations to expect

- **The 3D model freezes the industrial design, not the engineering.** A collision-free CAD assembly is a nominal geometry. Real parts have tolerances, real cells swell and real antennas detune.
- **Boards:** expect 3–4 revisions before mass production. That is two EVT spins, one DVT spin, and often a small PVT fix.
- **Molds:** expect 1–2 iterations after T1.
- **Schedule:** between "the design looks done" and "the product can be sold legally", 12–16 months is a realistic range for a first product `[estimate]`. Budget for that, and do not promise customers dates from the best case.
