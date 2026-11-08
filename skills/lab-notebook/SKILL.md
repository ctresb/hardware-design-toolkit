---
name: lab-notebook
description: Keeps a hardware project from going backwards. Defines the task cycle (start, work, close), a knowledge base of facts with evidence and experiments with verdicts, project lessons, a report per stage and the writing rules for project files. Use at the start and end of every Hardware Design Toolkit stage, when parallel agents work on one project, when a fix brings back an old failure, and when writing any file in hw/.
---

# Lab notebook

Hardware projects regress when nobody records what was tried. A fix undoes an earlier fix. A measurement
gets repeated. A failed idea comes back a week later. An agent's findings are lost when the conversation
ends. This skill makes every stage leave the project better documented than it found it.

Talk to the user in their language. Write the notebook in English, unless the user chose another language
for project files.

## Inputs and outputs

- **Inputs:** `hw/state.json`, `hw/knowledge/`, `hw/decisions.md`.
- **Outputs:** the files below. This skill owns them.

```
hw/knowledge/FACTS.md        F-001…  measured or verified facts
hw/knowledge/EXPERIMENTS.md  E-001…  what was tried, with a verdict
hw/knowledge/LESSONS.md      L-001…  rules learned, including user corrections
hw/retros/YYYY-MM-DD-<stage>.md       one report per stage or large task
hw/agents/YYYY-MM-DD-<task>.md        the report of each subagent, saved on arrival
```

Copy the headers from `templates/` the first time.

## 1. Start of a stage

1. Read `hw/state.json`, then `hw/knowledge/LESSONS.md`. Each lesson that applies to this stage is a rule.
2. Search `FACTS.md` and `EXPERIMENTS.md` for the subject (`grep -n -i <word> hw/knowledge/*.md`).
   - A fact with evidence is not measured again unless the design changed. Cite its ID.
   - An experiment with the verdict `did not work` is not repeated without a new hypothesis. Write the
     hypothesis down first.
3. If other agents work in the same project, find their files first (`git status`, file modification times).
   Do not edit, move or commit their files.

## 2. During the stage

- **Record facts at the moment you find them.** One entry has:
  - an ID;
  - the date;
  - the statement with its value and unit;
  - an evidence tag (`CONVENTIONS.md` §6);
  - the command or source that reproduces it.

  A number lives only in its fact. Other files cite the ID.
- **Record each experiment with a verdict:** `worked`, `did not work` or `inconclusive`. Add the reason and
  what would change the verdict. Record failures too, because they keep the next session from repeating
  them.
- **Take a new ID when you write the entry,** not from memory. Run `scripts/notebook_check.py --next F` to
  get the next free ID. With parallel agents, give each agent its own range (F-2xx, F-3xx) and name the
  range in its brief.
- **Write each user correction as a lesson when it happens.** Record the user's words, what was wrong and
  the rule that prevents it. Examples of real corrections:
  - "the shape makes no sense, it has to be straight" → L: pouch cells have straight edges;
  - "something is poking through" → L: validate before any render.
- **Regression rule.** If a change brings back a failure that an earlier change fixed:
  1. stop;
  2. write an experiment entry for both changes;
  3. find the shared cause, usually the order of operations or two owners of one value;
  4. change the order or the ownership.

  Do not try a third variant of the same fix.
- **Parallel agents.**
  - Before you split the work, freeze a common base and run its checks.
  - Agree the file formats.
  - Give each agent its own files.
  - Save each agent's report to `hw/agents/` the moment it arrives.
  - Merge one file at a time.

## 3. End of a stage (checklist)

1. **Verify.** Run the checks of the stage's skill, for example `bom_check.py`, the assembly validator or
   DRC. Write what was not verified.
2. **Knowledge.** Add new F-, E- and L- entries. When a fact changes, write a new entry, and mark the old
   one `SUPERSEDED on <date> by F-xxx: <what changed>`. Do not delete it.
3. **Decisions.** Add decisions to `hw/decisions.md`.
4. **State.** Update `hw/state.json`: stage status, gate evidence, open questions.
5. **Report.** Write `hw/retros/YYYY-MM-DD-<stage>.md` from `templates/retro.md`:
   - the request;
   - what was done and verified;
   - what was not verified;
   - the user's interventions;
   - mistakes and their causes;
   - the lessons added;
   - what is next.
6. **Check.** Run `scripts/notebook_check.py hw/`. It must report no duplicate IDs, no fact without
   evidence, and no experiment without a verdict.
7. **Commit,** only if the user wants commits. Never add attribution lines that the user did not ask for.

## Writing rules for project files

These rules apply to every file in `hw/`. They are adapted from the `concise` skill (MIT) and from
ASD-STE100 controlled language. The full list is in `references/writing-rules.md`.

- Use only these normative words: **must**, **must not**, **should** (a deviation needs a written
  reason), **can**. Do not use "shall", "may", "ideally" or "try to".
- Write each fact once, in its owner file. Elsewhere, refer to it by ID (`F-012`, `REQ-004`, `D-007`).
- Replace vague words with values: "small" → "≤ 30 × 30 × 9 mm", "low power" → "≤ 1.5 mA average", "about
  2 weeks" → "10–15 working days [estimate]".
- Use digits and units with a space: `3.3 V`, `68 mAh`, `0.35 mm`. Repeat the unit in ranges: `2 mA to
  4 mA`.
- Keep sentences short: 20 words or fewer for instructions, 25 or fewer for descriptions. Use active voice.
- Use one term for one thing. Put part numbers, file names, nets and commands in code format.
- Do not announce, summarize or restate. Each sentence adds a fact, an instruction or a decision.

## Gate

The stage closes when `notebook_check.py` passes, the retro exists and `hw/state.json` is updated.

## Taste and pitfalls

- An agent report that stays only in the conversation is lost. Save it to a file on arrival.
- Two agents that take "the next ID" at the start of their tasks collide. Take the ID when you write. This includes open-question IDs in `hw/state.json`: give each parallel agent its own prefix or range (`Q-RF-`, `Q-PW-`). In one real run, two research agents both created Q-07 to Q-09.
- A number copied into three documents goes stale in two of them. Keep it in one fact and cite the ID.
- A failed experiment that is not written down gets tried again. Record failures with the same care as
  successes.
- A lesson written only in the chat is forgotten in the next session. Write it in `LESSONS.md` at the
  moment of the correction.
