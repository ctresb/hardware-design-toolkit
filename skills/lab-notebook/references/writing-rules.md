# Writing rules for project files

These rules are controlled language for every file in `hw/`. They are adapted from the `concise` skill
(MIT License, © 2026 C3B), which restates S1000D Issue 7 and ASD-STE100 rules.

## 1. Normative words

| Word | Meaning |
|---|---|
| must | mandatory |
| must not | prohibited |
| should | recommended; a deviation needs a written reason |
| should not | not recommended; same rule |
| can | permitted option |
| is, are, does | statement of fact |

- Do not use "shall", "may", "might", "could", "need to", "have to", "ideally" or "try to".
- Write each requirement in its own sentence with an ID (`REQ-012`).

## 2. Replace words that need judgment

| Do not write | Write instead |
|---|---|
| appropriate, adequate, proper, reasonable | the criterion: "a wall of 0.8 mm to 1.2 mm" |
| as needed, if necessary | the condition: "if DRC reports a clearance error" |
| some, several, many, few | the number or the full list |
| usually, typically, normally | the condition, or the frequency and its source |
| small, tiny, low, high, fast, long | the value and unit: "≤ 1.5 mA", "8 weeks" |
| about, approximately, around | the value with its range or tolerance: "60 mAh to 68 mAh [estimate]" |
| etc., such as (open list) | the full list, or "for example" plus a statement that the list is not complete |
| and/or | "A, B, or both" |
| ensure, make sure (no check) | the check: "DRC reports 0 errors" |
| improve, optimize, support (no measure) | the measure: "average current from 2.4 mA to 1.6 mA" |
| simple, easy, just, basically, obviously | delete the word |
| robust, premium, seamless, intuitive | the property that can be tested: "survives 1.5 m drop on concrete, 6 faces" |
| TBD, TODO, ??? | an open question in `hw/state.json` with an ID |

## 3. One term, one meaning

- Use one term for one thing in all files. Do not vary words for style ("cell", "battery" and "pack" are
  three things; choose one for each).
- Write part numbers, nets, reference designators, file names and commands exactly, in code format:
  `nRF54L15-QFAA-R7`, `VSYS`, `U3`, `hw/bom.csv`.

## 4. Sentences and lists

| Text | Limit |
|---|---|
| Sentence in an instruction | 20 words |
| Sentence in a description | 25 words |
| Paragraph | 6 sentences, one topic |
| Noun cluster | 3 words |

- Put the key information first. Use active voice. Use the simple present for facts, the simple past for
  events.
- Do not use semicolons. Write two sentences.
- Use a vertical list for three or more parallel items. Two levels maximum.

## 5. Instructions

- Use the imperative: "Run DRC."
- One instruction per sentence.
- A condition comes before the instruction: "If the cell swells more than 0.3 mm, stop the test."
- Write the expected result after the action when the reader checks it: "Run `bom_check.py`. It reports 0
  errors."

## 6. Numbers and units

- Use digits for every value with a unit. Put one space between number and unit: `3.3 V`, `0.6 mm`.
- Repeat the unit in a range: `2 mA to 4 mA`.
- Write a tolerance once, after the value: `0.60 ± 0.06 mm`.
- Write a leading zero: `0.5`.
- Use SI units and mm for mechanics. Use USD with a date for prices.
- A number with a source lives in one file only. Other files cite its ID.

## 7. Warnings

| Label | Use for |
|---|---|
| **WARNING** | risk of injury, fire, permanent data loss, or a cost that cannot be recovered (lithium cells, mains voltage, tooling orders) |
| **CAUTION** | risk of damage that can be repaired (a burnt prototype, a wrong board order) |
| **Note** | helpful information; never an instruction |

Start a warning with a command, then the risk: "**WARNING** Do not puncture or bend the cell. A damaged
lithium cell can catch fire."

## 8. Redundancy

- State each fact once. Refer to it elsewhere.
- Do not announce content ("This section describes…"). The heading does that.
- Do not summarize what the reader just read.
- Before you write a fact, search for it. If it exists, cite it. If it is wrong, change it at its source.
