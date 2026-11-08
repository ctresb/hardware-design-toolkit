# Requirements template (`hw/requirements.md`)

Each requirement has one row. It is measurable, it has a target and a limit, and it traces to the brief.

```markdown
# Requirements: <product name>

Issue: 1 · Date: YYYY-MM-DD · Source: hw/brief.md (issue N)

## Summary
One paragraph: what the product does, for whom, and the two or three numbers that dominate the design
(for example: envelope, autonomy, price at 1k).

## Requirements

| ID | Category | Requirement | Target | Limit | Priority | Source | Verified by |
|---|---|---|---|---|---|---|---|
| REQ-001 | Size | Outer envelope | 30 × 30 × 8.5 mm | ≤ 32 × 32 × 9.5 mm | must | brief §2 | CAD measurement |
| REQ-002 | Power | Autonomy, continuous main function | 16 h | ≥ 12 h at end of life (80 % capacity) | must | brief §3 | bench test on EVT |
| REQ-003 | Power | Standby | 14 days | ≥ 7 days | should | brief §3 | bench test |
| REQ-004 | Charge | Time 0 → 80 % | 45 min | ≤ 90 min | should | brief §3 | bench test |
| REQ-005 | Environment | Sweat and splash | IP67 | IPX4 | must | brief §4 | lab test |
| REQ-006 | Connectivity | Phone link | BLE 5.x, 10 m indoor | ≥ 5 m through a pocket | must | brief §3 | range test |
| REQ-007 | Storage | Offline capture without phone | 24 h of data | ≥ 12 h | must | brief §3 | calculation + test |
| REQ-008 | Indication | Status light visible through enclosure | — | readable in office light | should | brief §3 | prototype |
| REQ-009 | Regulatory | Markets | US, EU, BR | — | must | brief §6 | compliance plan |
| REQ-010 | Cost | Recurring cost at 1k units | ≤ USD 45 | ≤ USD 60 | should | brief §7 | cost model |

## Conflicts and open questions
- REQ-001 vs REQ-002: the envelope allows about X mm³ for the cell. At Y Wh/L that gives Z mAh, so REQ-002 needs an average current of at most W mA. Decision needed: D-00N.

## Out of scope
Functions considered and rejected, each with the reason and a link to the decision.
```

## Rules

- Units: mm, g, mA, mAh, V, h, dB SPL, °C. No unitless numbers.
- A target is what you design for. A limit is the worst value the product may ship with.
- Autonomy and battery requirements state the condition: mode, temperature, and new cell or end of life.
- "Verified by" names the test, measurement or document that will close the requirement.
- Experience phrases from the brief stay in the brief. Here they become numbers.
- When a requirement changes, raise the issue number, keep the old row struck through, and link the decision.

## Typical categories to cover

Size and mass, power and autonomy, charging, connectivity, storage, sensing, user input, output (light, sound, haptics), environment (IP, drop, temperature, UV, chemicals, skin contact), safety (battery, skin temperature, small parts), regulatory markets, cost, lifecycle (target production years), serviceability and repair, sustainability (removable battery rules), firmware update.
