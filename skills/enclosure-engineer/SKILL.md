---
name: enclosure-engineer
description: Designs a hardware product's enclosure as parametric CAD (build123d) with STEP, STL and GLB output and an automated DFM check, then assembles it in Blender. It fits parts with a flood-fill free-space map and runs the interpenetration validator that gates every render and drawing. Covers stack-up, tolerances, molding, sealing and materials. Use for "design the case", "enclosure", "STEP file", "will it fit", "injection molding", "IP rating", "parts are clipping".
---

# Enclosure engineer

You turn the electronics and the industrial-design intent into an enclosure that a molder can quote and an assembly that can be built and sealed. The output is **ready to build**: STEP files per part, a DFM report, and a validated assembly.

Two tools, two jobs:

- **CAD (build123d) is the source of truth for enclosure geometry.** A JSON spec produces exact B-rep parts. It exports STEP for molders and print services, STL for prototypes and GLB for Blender, and runs a DFM check.
- **Blender is the assembly, validation and render stage.** It imports the GLB, places the PCB and battery, fits movable parts and validates. It never edits the enclosure. A geometry change goes back to the spec.

Talk to the user in their language. Show progress as images (viewport captures or quick renders), and save each one.

## Inputs

- `hw/brief.md`: size limits, how the product is worn or used, colors and finishes, environment (sweat, rain, drops).
- `hw/requirements.md`: dimensional, ingress (IP) and drop requirements.
- `hw/architecture.md` and `hw/bom.csv`: which parts exist, their `size_max_mm`, connectors, battery, antenna keep-outs.
- `hw/pcb/`: board outlines and 3D exports (GLB/VRML/STEP from `pcb-engineer`).
- `hw/power/`: battery dimensions and swelling allowance from `battery-and-power`.

## Outputs

- `hw/mech/enclosure.json`: the enclosure spec (from `templates/enclosure.example.json`).
- `hw/mech/cad/`: `<name>_<part>.step`, `<name>_assembly.step`, `<name>_<part>.stl`, `<name>_assembly.glb`, keep-out STEP/GLB, `<name>_dfm.json` and `<name>_dfm.md`.
- `hw/mech/build_assembly.py`: the scripted Blender assembly (imports the CAD GLB and the PCB export), run with `blender -b --python`.
- `hw/mech/assembly_golden.blend`: the frozen, validated assembly. Every render and drawing starts from this file.
- `hw/mech/stackup.md`: the Z stack, layer by layer, with nominal, minimum and maximum values. It lists every gap under 0.3 mm.
- `hw/mech/tolerances.md`: the tolerance stack-up of each critical gap, worst case and RSS.
- `hw/mech/dfm.md`: the molding review (walls, draft, gates, undercuts, side actions, finish) and the questions for the molder.
- `hw/validation/assembly.json` and `assembly.txt`: the validator report of the golden file.
- Entries in `hw/decisions.md` for every mechanical trade-off: wall thickness against battery volume, sealing method, and similar choices.

## Gate

The next stage (renders, drawings, cost quotes) starts only when:

1. `cad_enclosure.py` reports **DFM PASS**. Every undercut and undrafted warning is either removed or accepted in `hw/mech/dfm.md`, with the mechanism and cost it needs.
2. `validate_assembly.py` passes on the golden file: 0 interpenetrations deeper than 0.02 mm, and no non-manifold or non-finite mesh.
3. `free_space.py` reports **no leak** for every cavity that must be sealed.
4. Every gap under 0.3 mm has a tolerance stack-up with a positive worst-case or a stated RSS risk.
5. The DFM review has no open "cannot mold" item, and the STEP files open in a second tool (any CAD viewer) with the right size.

## Tools (scripts/)

| Script | What it does |
|---|---|
| `scripts/cad_enclosure.py` | JSON spec → B-rep shell, lid (adhesive lip, snap, captive screws + flat gasket, or twist), optional round battery door (screws or twist), joint parts and features → STEP, STL, GLB + DFM check (walls, draft, undercuts, keep-outs). Runs with `cad_python` from `toolchain.json` (build123d venv, Python 3.10–3.13). `scripts/test_cad_joints.py` is its regression test. |
| `scripts/import_cad_glb.py` | Imports the CAD GLB (and keep-outs) into a millimetre Blender scene as tagged components, validates and saves. |
| `scripts/validate_assembly.py` | Interpenetration and mesh-quality gate. Writes JSON + text, exits 1 on failure. |
| `scripts/free_space.py` | Voxel flood fill of the cavity: leak detection, distance field, rigid fit of movable parts. |
| `scripts/enclosure_example.py` | A Blender-only demo of fitting and validation: shell, lid, PCB, components, battery. Use it to learn the gate, not to design. |

```bash
# CAD: build, export, DFM check, in the build123d venv that toolchain-setup records as `cad_python`
CAD_PY=$(python3 -c "import json,os; p=[x for x in ('hw/toolchain.json', os.path.expanduser('~/.config/hardware-design-toolkit/toolchain.json')) if os.path.isfile(x)][0]; print(json.load(open(p))['paths']['cad_python'])")
"$CAD_PY" ${CLAUDE_SKILL_DIR}/scripts/cad_enclosure.py hw/mech/enclosure.json --out hw/mech/cad

# into Blender with keep-outs, validated
blender -b --factory-startup --python ${CLAUDE_SKILL_DIR}/scripts/import_cad_glb.py -- --glb hw/mech/cad/<name>_assembly.glb \
    --keepouts hw/mech/cad/<name>_keepouts.glb --validate hw/validation/enclosure --save hw/mech/assembly.blend

# the example, start to finish (seconds)
blender -b --factory-startup --python ${CLAUDE_SKILL_DIR}/scripts/enclosure_example.py -- --out /tmp/hdt_example --collide

# gate an assembly (validate in the unposed frame of the root)
blender -b hw/mech/assembly_golden.blend --python ${CLAUDE_SKILL_DIR}/scripts/validate_assembly.py -- \
    --root Assembly --json hw/validation/assembly.json --txt hw/validation/assembly.txt

# fit a movable part (battery) against fixed collections, along z only
blender -b hw/mech/assembly.blend --python ${CLAUDE_SKILL_DIR}/scripts/free_space.py -- \
    --fixed-collection Shell --fixed-collection Boards --movable "Battery cell" \
    --clearance 0.10 --lock 0 0 1 --save hw/mech/assembly_fitted.blend
```

`free_space.py` uses cupy (GPU) or scipy when they are present, and falls back to numpy only. Blender does not bundle scipy. To install it into Blender's Python, use `toolchain-setup`. For a one-off run, use `PYTHONPATH=<dir with scipy> blender --python-use-system-env ...`. Grids above about 60 M voxels belong on a GPU machine, not on the laptop that is running the session.

## Workflow

### 1. Envelope and stack-up first

Before any modelling, write `hw/mech/stackup.md`. List the Z stack from the outer skin to the back cover: wall, gap, flex or board, tallest component, gap, battery and its swelling allowance, gap, back wall. Use the **maximum** dimensions from the datasheets. Nominal heights hide the gaps that later fail. If the stack does not fit the brief's thickness, say so now and offer options: a smaller cell, fewer layers, components on the other side, or a thicker product. Do not shrink a part below what exists.

### 2. Enclosure in CAD

Read `references/cad-pipeline.md`. Copy `templates/enclosure.example.json` to `hw/mech/enclosure.json` and fill it from the brief and the stack-up:

- outline, height and wall;
- fillets and draft;
- the lid joint;
- windows, ports and tunnels;
- bosses and ribs;
- keep-outs for the board, the components and the cell, at their maximum size.

Run `cad_enclosure.py` and fix every DFM error in the spec. Review every warning with the user when it costs money, for example a side action for a cord tunnel.

### 3. Assemble in Blender, in a fixed build order

Read `references/assembly-pipeline.md` before you write `build_assembly.py`. It starts from `import_cad_glb.py` (the enclosure) and adds the PCB export and the battery. Rules:

- Set scene units to millimetres (`unit_settings.scale_length = 0.001`, length unit `MILLIMETERS`). One Blender unit is 1 mm.
- One root EMPTY named `Assembly`. Each physical component is an EMPTY with the custom property `hdt_component = True` (the validator still reads the legacy name `vh_component`), and its meshes are children. The validator never tests meshes of the same component against each other.
- Never model or cut the enclosure in Blender. Booleans in Blender are only for non-deliverable helpers. If you use them, apply them with the EXACT solver (evaluate, then `bpy.data.meshes.new_from_object`), and make shared mesh data single-user before you cut it.
- Imported vendor models (KiCad GLB, STEP converted to mesh) keep their own empties. Treat containers like `Node`, `Root` and `=>…` as containers (`--container-regex`).
- Build order: fixed structure → boards → mated connectors (fixed constraints) → springs and contacts (fit to their working height) → membranes and gaskets → free-space fit of movable bodies → battery last among bodies → small details (solder, markings, owned by `product-render`) → validate → freeze.
- Save the result as `assembly_golden.blend`. Appearance-only work (materials, lights, cameras) loads the golden file and never moves geometry.

### 4. Fit, do not nudge

When a part collides, do not move it by hand until the render looks right. Run `free_space.py`: it measures the free space around the part and moves it the minimum distance along the escape direction. If the fit needs more than the design allows (for example the battery has to rise 0.4 mm but the stack has 0.1 mm), that is a **design finding**. Report it, and change the source: placement, pocket, part height or cell size.

### 5. Validate, then freeze

Run the validator on the whole assembly in its unposed frame. A posed or rotated copy for a photo is validated before it is posed. Rotation changes floating-point precision on coplanar contacts.

- Every failure is fixed at its source. There is no whitelist. A simplified vendor model that collides is replaced by the vendor's real 3D model.
- If two fixes keep undoing each other, stop. Change the build order so that each step depends only on the steps before it, then rebuild from the start.

### 6. Tolerances and DFM

- Read `references/tolerances.md` and do the stack-up for every gap under 0.3 mm and every spring or contact working height.
- Read `references/dfm-injection-molding.md` and review every molded part beyond what the automated check sees: gate position and weld lines, finish, shrink, and the questions for the molder.
- Read `references/sealing-and-ingress.md` for every opening: microphone and speaker ports, buttons, charging contacts, seams, cord or strap holes.
- Read `references/materials.md` before you pick a resin, metal or finish.

## Taste and pitfalls

- **Fewer holes.** Each opening costs sealing, tooling and certification effort. Prefer molded-in contacts, adhesive-sealed seams, capacitive touch through the wall, and membranes over open grilles.
- **Real batteries have straight edges.** A pouch cell is a rectangle (or a simple polygon) with a sealed border of about 1 mm and tabs. It is not a blob shaped to fill the leftover space. Keep a swelling allowance above it: about 8–10% of cell thickness over its life [estimate: typical pouch swelling guidance; confirm with the cell vendor].
- **Use maximum dimensions.** LED, crystal and connector heights in distributor listings are often larger than the "typical" figure in the datasheet. When the two disagree, model the larger one.
- **A clean mesh is not a real mesh.** Mold parting lines, draft, ejector-pin marks and gate vestiges exist. Include the ones that show in renders, or at least keep draft on vertical walls so that reflections behave.
- **Clear parts are special.** Weld lines, gate blush, sink and every internal feature show through. Gate into a hidden area, keep walls uniform, and polish to SPI A1/A2.
- **An arched tunnel needs a curved core** (an expensive tool). The cheaper option is to split the tunnel at the parting line, so that each half is a straight pull.
- **Contact is allowed and penetration is not.** Parts that seat face to face pass the validator, so model them that way. Do not leave a fake 0.001 mm gap.
- **One source of truth.** Enclosure changes go into the spec and the CAD rebuild. A shell edited by hand in Blender no longer matches the STEP file the molder quotes.
- **Undercuts cost money.** Each cluster the DFM check reports means a slide or a lifter in the tool. Remove it, or show the user its cost and get a decision.
- **A twist lid needs a round product; a round door does not.** A bayonet that turns the whole lid only works on a circular outline, and on a thin product its lugs need the space the battery holder takes. For a coin cell in any outline, put a round door in the lid. Captive screws (`lid.door.retention: screws`) are tool-secured for coin-cell child-safety rules and mold in a straight pull. Bayonet lugs need side actions.
- **Stop when it regresses.** Repeated "fix one thing, break another" cycles mean the build order is wrong. Redesign the order and rebuild. Do not keep patching.

## References

| File | Read when |
|---|---|
| `references/cad-pipeline.md` | writing the enclosure spec; reading the DFM report; sending files to a molder |
| `references/assembly-pipeline.md` | before writing or changing `build_assembly.py`; when fixes regress |
| `references/free-space-and-flex.md` | fitting parts, flex circuits that drape over components, leak findings |
| `references/tolerances.md` | any gap < 0.3 mm, springs, press fits, snap fits, battery pockets |
| `references/dfm-injection-molding.md` | every molded part; before an RFQ to a molder |
| `references/sealing-and-ingress.md` | any opening, seam, port or IP requirement |
| `references/materials.md` | choosing resins, metals, inserts, finishes, skin-contact materials |
