# Injection molding DFM

This file holds the design rules to apply before you ask a molder for a quote. The numbers are common design-guide values. Each one is marked `[estimate: design guide]`. Confirm every value with the molder chosen for the project, because resin grade, tool steel and part size all change them.

## Walls

| Resin | Typical wall range (mm) | Note |
|---|---|---|
| ABS | 1.1–3.5 | forgiving, opaque |
| PC | 1.0–3.8 | tough; clear grades available; needs drying |
| PC/ABS | 1.0–3.0 | tough, opaque, good finish |
| PMMA (acrylic) | 0.6–3.0 | very clear, brittle on impact |
| PA (nylon) | 0.8–2.9 | absorbs moisture; dimensions change |
| PP | 0.6–3.8 | living hinges; high shrink |
| TPU / TPE | 0.6–3.0 | soft-touch, overmold |
| LCP | 0.3–3.0 | thin-wall connectors, not enclosures |

`[estimate: design guide; values in the style of the Protolabs wall-thickness table]`

- A wall under 1.0 mm is possible on a small part with a short flow length, but it needs a molder's confirmation and often a faster, more expensive process. For small wearables, 0.8–1.2 mm is the usual target.
- **Keep walls uniform.** A thick area next to a thin one causes sink, voids and warp. If a change of thickness is unavoidable, taper it over about 3× the difference.
- Inside corners get a radius of at least 0.5 × the wall. The outside radius is the inside radius plus the wall, so the thickness stays constant around the corner.

## Draft

- Every face parallel to the pull direction needs draft. Use at least 0.5°. 1–2° is typical.
- Textured faces need more draft: about 1–1.5° extra per 0.025 mm of texture depth `[estimate: design guide]`.
- Polished optical faces can use less, about 0.5°, if the molder agrees.
- Model the draft. Reflections on drafted walls look different from reflections on perfectly vertical walls, and renders should show the real part.

## Ribs, bosses, snaps

- **Rib thickness:** 50–60% of the wall it stands on, or about 50% on clear or glossy parts, where sink shows. Height up to 3× the wall. Spacing at least 2× the wall `[estimate: design guide]`.
- **Bosses:** outer diameter about 2× the hole diameter, wall about 60% of the nominal wall. Join bosses to walls with ribs, not with solid material.
- **Snap fits:** strain is the limit. Keep peak strain under the resin's allowable limit (the molder or the resin datasheet gives it). Each snap is an undercut: count it in the tooling (see below).
- **Holes:** a through hole along the pull direction is a cheap shut-off. A side hole needs a side action.

## Undercuts and tool actions

Every feature that cannot be pulled straight out of the tool needs a mechanism:

| Mechanism | Used for | Effect on tool cost |
|---|---|---|
| Side action (slide) | side holes, side ports, side snaps | each adds roughly 15–30% to the tool `[estimate: Hubs design guide]`, plus maintenance |
| Lifter | internal undercuts, inner snaps | similar to a slide; limited travel |
| Bump-off | shallow undercut on a flexible resin | cheap, flexible resins only |
| Collapsible or curved core | arched internal tunnels, curved holes | expensive and slow; avoid |
| Hand-loaded insert | low-volume prototypes | cheap tool, high part cost |

Ways to remove undercuts:

- Put the parting line through the feature. For example, split an arched cord or strap tunnel at the parting line, so that each half is formed by the core and cavity.
- Turn a side port into a port on a face along the pull direction.
- Replace snaps with adhesive or with a screw boss.

## Gates, weld lines and clear parts

- The molder chooses the gate location, but the design decides where a gate vestige and a weld line are acceptable. Mark the cosmetic faces (A-side) on the drawing.
- **Weld lines** form where flow fronts meet: behind holes and around cores. On opaque textured parts they are hard to see. On clear or high-gloss parts they show as lines, and they are weaker.
  - Keep holes and cores out of the optical area.
  - Place the gate so that the weld lines land in hidden areas.
- **Clear parts also show:**
  - gate blush;
  - sink;
  - splay, from moisture: PC must be dried before molding;
  - flow lines;
  - every internal feature, rib and boss.

  Design the inside of a clear part as carefully as the outside.
- **Finish:** SPI A1 (diamond buff) for optical faces, A2–A3 for high gloss, B and C (paper and stone) for semi-gloss, D (bead blast) for matte texture. A1 and A2 cost more in tool polishing and need hardened steel to last.

## Shrink and dimensions

- Typical linear shrink: PC 0.5–0.7%, ABS 0.4–0.7%, PC/ABS 0.5–0.7%, PMMA 0.2–0.8%, PA 0.7–2%, PP 1–2.5% `[estimate: resin datasheets vary by grade]`. The tool is cut oversize. Your CAD shows the final part.
- Critical dimensions (mating features, battery pockets, seal grooves) are marked on the drawing. Plan a tool adjustment (steel safe: tool cut so that the part is slightly too large or too small, then corrected by removing steel) after the first shots.

## Tooling and process path

| Quantity | Typical process | Notes |
|---|---|---|
| 1–20 | SLA/PolyJet print, CNC (PC, PMMA, aluminum) | clear prints need sanding and clear coat to look clear |
| 10–100 | urethane casting in silicone molds | clear urethanes exist; colors and finishes approximate |
| 100–10k | aluminum "rapid" tool | days to weeks; thousands of shots `[estimate: Protolabs, Hubs]` |
| 10k–1M | hardened or pre-hardened steel tool | months; highest cost; best finish |

- Tool prices depend on size, actions, finish and region. Never put a tool price in a report without the label `[estimate]` or a quote. The `cost-and-sourcing` skill owns the numbers.
- Insert molding (metal contacts molded into the plastic) adds tool cost and cycle time, because the inserts are loaded for every shot. Ultrasonic or heat-staked inserts placed after molding are the alternative.
- Two-shot or overmolding (a hard shell plus a soft TPU or silicone layer) needs a second tool or a rotary tool.

## Questions for the molder (put them in `hw/mech/dfm.md`)

1. The minimum wall you accept on this part, in this resin, with this flow length.
2. Gate location, and where the weld lines will be.
3. The number of actions and lifters you see. Can any be removed?
4. The finish per face (SPI grade), and the tool steel needed for it.
5. Shrink allowance and the tolerance you hold on the critical dimensions.
6. Cavities per tool, cycle time, tool life, and lead time to first shots (T1).
7. Insert or overmold handling, if any.
