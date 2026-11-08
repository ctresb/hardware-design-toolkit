# CAD pipeline: from a JSON spec to files a molder can quote

## Source of truth

```
hw/mech/enclosure.json ──cad_enclosure.py──▶ STEP (molder, print service, mechanical CAD)
        (edit here)                      ├─▶ STL  (SLA/FDM prototypes)
                                         ├─▶ GLB  ──import_cad_glb.py──▶ Blender assembly ──▶ validator ──▶ renders, drawings
                                         └─▶ DFM report (walls, draft, undercuts, keep-outs)
```

- **Enclosure geometry changes happen only in the spec and `cad_enclosure.py`.** Blender imports the GLB and never edits it. If a render shows a problem in the shell, fix the spec, rebuild, re-import and re-validate.
- The B-rep (STEP) is exact. The GLB and STL are tessellations of it, for viewing and printing.
- Molders and print services quote from STEP. Send one STEP per part, plus the assembly STEP, plus a drawing that marks the cosmetic faces, critical dimensions and finish (`technical-drawing`).

## Install

build123d is a Python CAD library on top of OpenCascade:

`toolchain-setup` installs it in a dedicated venv, `~/.local/share/hardware-design-toolkit/venv`, and records
its interpreter in `toolchain.json` as `cad_python`. It needs Python 3.10–3.13, because its wheels do not cover
newer Python versions yet. The installers use uv when present:

```bash
uv venv -p 3.12 ~/.local/share/hardware-design-toolkit/venv
uv pip install -p ~/.local/share/hardware-design-toolkit/venv/bin/python build123d
```

Without uv: `python3.12 -m venv <venv> && <venv>/bin/pip install build123d`. Tested with build123d 0.13 on
Python 3.12.

## Commands

```bash
# build, export and check (about 2 s for a small part); cad_python comes from toolchain.json
CAD_PY=$(python3 -c "import json,os; p=[x for x in ('hw/toolchain.json', os.path.expanduser('~/.config/hardware-design-toolkit/toolchain.json')) if os.path.isfile(x)][0]; print(json.load(open(p))['paths']['cad_python'])")
"$CAD_PY" scripts/cad_enclosure.py hw/mech/enclosure.json --out hw/mech/cad

# into Blender, with keep-outs, validated, saved
blender -b --factory-startup --python scripts/import_cad_glb.py -- \
    --glb hw/mech/cad/<name>_assembly.glb --keepouts hw/mech/cad/<name>_keepouts.glb \
    --validate hw/validation/enclosure --save hw/mech/assembly.blend
```

Then place the real PCB export (from `pcb-engineer`) and the battery model into the same assembly. Fit with `free_space.py` and validate the whole thing (`assembly-pipeline.md`).

## The spec (`templates/enclosure.example.json`)

| Key | Meaning |
|---|---|
| `outline` | `rounded_rect` (width, depth, corner_radius), `circle` (diameter), or `polygon` (points, corner_radius) |
| `height`, `wall` | overall height from the lid's outer bottom; nominal wall |
| `top_fillet`, `bottom_fillet` | outer edge fillets of the shell top and the lid bottom |
| `draft_deg` | draft on all walls, bosses, ribs and lip; neutral plane at the parting line |
| `lid.joint` | `adhesive_lip` (lip + die-cut adhesive ring), `snap` (bumps + recesses), `screws` (captive thread-forming screws into shell bosses + flat die-cut gasket; any outline; positions automatic on rounded_rect and circle, explicit on polygon; no side actions), `twist` (lugs + groove + face-seal O-ring; the whole lid turns, so circle outline only) |
| `lid.door` | a round battery door in the lid, for any outline: `center`, `radius`, `flange`, `flange_t`, `retention` `screws` (captive screws through ears into lid bosses; straight pull) or `twist` (bayonet lugs in a collar groove; undercuts), `gasket` (`free_t`, `compressed_t`), optional `coin_slot` [length, width, depth]. Example: `templates/enclosure.door.example.json` |
| `features[]` | `window` (thin LED area: `thickness`), `sound_port` (hole + `seat_diameter`/`seat_depth` for a membrane), `lanyard` (straight drilled `path` segments, `boss_diameter`), `boss`, `rib` (`part`: body or lid) |
| `keepouts[]` | named boxes or rounded boxes (`corner_radius`) for the board, components and cell, at their maximum size |
| `dfm` | `min_wall`, `max_wall`, `min_draft_deg`, `min_window`, `min_rib`, `keepout_clearance`, `min_flag_area_mm2` |

Frame: z = 0 is the outer bottom of the lid, and +Z is the pull direction of the shell. The parting plane is the top of the lid flange.

## The DFM check

This is an automated, geometric first pass. It does not replace the molder's review.

| Check | Method | Result |
|---|---|---|
| Wall thickness | area-weighted samples, exact face normals; ray inward from just outside the face; thickness = distance between the first two hits | error below `min_wall` (ribs, bosses and the lid lip are judged against `min_rib`, windows against `min_window`); warning above `max_wall` only if 4 tilted rays agree, so that a wall seen end-on (rim, flange edge) is not reported as thick |
| Draft | angle between each sample's normal and the XY plane | warning for faces with less than `min_draft_deg` |
| Undercuts | an up-facing point whose ray toward +Z hits the part again (or down-facing toward −Z) cannot be released by a straight pull | warning per cluster: each one needs a side action, a lifter, a bump-off or a redesign |
| Keep-outs | keep-out grown by the clearance, intersected with each part; and contained in the envelope | error on any overlap |
| Joint geometry | snap ledge height, lug groove depth, O-ring groove fit under the rim and in the lid, screw bosses (OD ≥ 2 × screw, wall ≥ min_wall, engagement ≥ 2 × screw), gasket compression, door ears and collar walls | error with the size that would work |

Findings print with their location (`near [x, y, z]`). Very small thin areas (below `min_flag_area_mm2`) are reported as slivers to inspect, not as errors.

Reading the results:

- **Undercut warnings are often intended.** For example, a lanyard tunnel or snap bumps. Each cluster is a tool mechanism and a cost. List them in `hw/mech/dfm.md` with the decision: keep it (with a side action), redesign it, or split it at the parting line.
- **Undrafted warnings on small through-holes** (sound ports, tunnels) are common. Molders often accept them on short cores. Ask.
- **A thin wall error is a design error.** Fix the spec: move the feature, thicken the wall, or change the feature size.

## What the generator does not do

- Gate, runner and cooling design, or mold flow. Those belong to the molder.
- Texture, engraving or logos. Do them as a feature in a full CAD tool or on the drawing; mark laser engraving in the BOM.
- Organic or free-form surfaces. For those, use a full CAD tool (FreeCAD, Onshape, Fusion, SolidWorks) and keep the same outputs: STEP for parts, GLB into Blender, the same validator and DFM review.
