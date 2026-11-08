---
name: product-render
description: Renders photoreal product images of a hardware design in Blender Cycles: studio lighting recipes, a physical camera, wear-aware PBR materials, simulated solder and LED glow, with a validation gate before any render. Use when the user asks for renders, product photos, a hero image, a landing-page shot, an exploded beauty shot, a dark shot with the LED on, a color lineup, or wants the 3D model to "look real".
---

# Product render

Turn a validated 3D assembly into images that read as photographs: for a landing page, a pitch deck or the
final presentation. The bar is "a viewer believes it is a photo of a real, manufactured object". A render that
looks like a CAD screenshot or a toy is worse than no render, because it tells the viewer the product is not
real.

Talk to the user in their language. Show each image as soon as it exists, and save it to `hw/renders/` at the
same moment.

## Inputs

- `hw/mech/` — the assembly `.blend`, built by `enclosure-engineer` (enclosure, boards, battery, parts).
- `hw/validation/*.json` — the assembly validator report. **Required** (see Gate).
- `hw/pcb/export/pads.json` — the real pads, for solder fillets. `pcb-engineer` owns and writes it. For a board it did not build, `scripts/kicad_pads.py` calls the same exporter.
- `hw/brief.md` — colors and finishes, where and how the product is used (this drives the shot list).

## Outputs

- `hw/renders/<shot>.png` (16-bit) plus `<shot>.json`, a sidecar with recipe, camera, samples and time.
- `hw/renders/scenes/<shot>.py` or `.blend` — what is needed to re-render the shot.
- `hw/renders/sheet_<round>.png` — contact sheets of variants compared side by side.

## Gate

Before any render:
1. The geometry validator passed on the exact assembly being rendered. Use the same pose: validate in
   the frozen device frame, then move the whole assembly rigidly for the shot.
2. The report is newer than the `.blend`.

`scripts/studio.py` enforces both. `--allow-unvalidated` exists only for material tests and scenes that are
not an assembly. Never use it to get past a failing assembly. Fix the geometry at the source instead (owner:
`enclosure-engineer`).

Before calling the presentation done, every shot must pass `references/realism-checklist.md`.

## Workflow

1. **Plan the shots** with `references/shot-list.md`. Pick 3–6 shots that show what the brief promises: size
   in the hand or on the body, the main interaction, the materials, and the inside (exploded or close-up).
   Ask the user only about taste decisions that change the set, such as colorway, mood or background. Default
   to a dark product on a dark studio; it reads best (see the checklist).
2. **Freeze the geometry.** Copy the validated assembly to `hw/renders/base.blend` and never edit its
   geometry there. Changes to look (materials, lights, camera) go into a script that opens the frozen file.
   If a fix and a regression start undoing each other, stop. Rebuild in the fixed order: assembly → fit →
   solder → validate → freeze. Do not patch in a loop.
3. **Materials:** `scripts/materials.py` (reference: `references/materials.md`). Map every object to a
   material kind with name globs:
   ```
   blender -b base.blend --python ${CLAUDE_SKILL_DIR}/scripts/materials.py -- \
     --assign "Enclosure*=plastic_black:wear=0.4" "Window*=plastic_clear:wear=0.6" \
              "Strap*=silicone:color=0.02,0.02,0.022" --wear-textures <ambientCG folder> --save look.blend
   ```
   Wear is on by default: fingerprints, smears, micro-scratches, and dust on up-facing faces. Clean surfaces
   look fake. Real scans (ambientCG CC0 sets) look better than the procedural fallback. Fetch them once, with
   `toolchain-setup`.
4. **Solder** (any shot that shows a board): `scripts/solder.py --pads pads.json --board main=<collection>`.
   It simulates each fillet from the real pad, stencil and paste volume. Wrinkles and slight asymmetry are
   correct. Floating or blobby solder is not. Run it last in the build, before validation.
   The contact line sits `--edge-inset` (0.03 mm) inside the copper, so zero-margin masks do not clash. If
   the validator still reports solder × mask on one part, the footprint's pad and mask opening disagree:
   send that to `pcb-engineer`, and solder the rest with `--exclude <ref>`. `--only` and `--exclude` take
   ref globs, so you can enable parts one by one.
5. **Preview first.** Render `--format preview --preset preview` for every shot, and compare variants (HDRI
   rotation, colorway, exposure, f-stop) with `scripts/contact_sheet.py`. Show the sheet. Only then render
   finals.
6. **Final:** `scripts/studio.py` with `--format 4k-vertical|4k-horizontal --preset final|hero`. Run finals on
   a GPU. If the user's computer is a laptop or has no strong GPU, use a cloud GPU
   (`references/cloud-gpu.md`), and pull each image as soon as it finishes.
7. **Check each image** against `references/realism-checklist.md` before showing it. Name the problems you see
   before the user does. If the user rejects an image, write down the reason as a rule for the next shots.

```
blender -b look.blend --python ${CLAUDE_SKILL_DIR}/scripts/studio.py -- --target "Product" --recipe dark-studio \
  --view hero --lens 100 --fstop 8 --format 4k-vertical --preset final \
  --emit "LED*=1,0.86,0.70:60" --validator-json hw/validation/assembly.json --out hw/renders/hero_dark.png
```

## Recipes (`scripts/studio.py --recipe`)

| Recipe | Use | Key settings |
|---|---|---|
| `dark-studio` | default hero, clear or dark products, LED on | world 0.012; one big soft key; 2 thin strips behind; weak top; AgX Base Contrast |
| `tabletop-hdri` | "on the desk", lifestyle-neutral | studio HDRI for reflections, matte table, soft key; Khronos PBR Neutral |
| `white-seamless` | catalog, spec sheets | curved backdrop, overhead softbox, fills; avoid white product on white |
| `hero-float` | landing page hero | dark graphite wall with soft gradient, rim strips, optional glossy floor |

Details, light ratios and why each light is there: `references/lighting-recipes.md`.

## Camera rules

- The scene's front is −Y. `--view` names an azimuth and elevation around the product. The product faces
  the camera unless the shot is explicitly about the back (charging contacts, engraving).
- Physical camera: 85–105 mm full-frame equivalent, which gives no wide-angle distortion on small objects. The
  36 mm sensor side follows the long image side, so a vertical frame uses `sensor_fit=VERTICAL` with
  sensor height 36. Leaving the 24 mm default crops the frame.
- Depth of field is real but consistent. Small products need f/8–f/16 to stay sharp front to back.
  Anything at the same distance as a blurred object must be equally blurred, or the image reads as a
  composite.
- Focus is on the first surface the camera sees at the center, or on `--focus <object>` (for example the LED).

## Taste and pitfalls

- **Never render before validating.** A part poking through a wall gets noticed at once, and it costs more
  trust than any good render earns.
- **Clear plastic is not glass.** Use IOR ~1.49–1.59, a little volume absorption, an oily fingerprint film
  and micro-scratches. If it looks like a jewel, it is wrong.
- **White products on white backgrounds turn into flat shapes.** Use the dark colorway for hero shots and
  show white on dark or high-contrast scenes.
- **Metal and glass look real only through what they reflect.** Give them an HDRI or strip lights to reflect.
  A big softbox must not show as a white sheet across a screen or a window; use thin strips for edges.
- **Cords, straps and fabric:** use a real braided structure with fibers and lint (see the materials
  reference). A smooth tube looks fake at once.
- **Hands and people:** use a real rigged scan, fix its joints, and give the skin subsurface scattering. Do
  not let it go dark under studio light. If no good model is available, do not do a hand shot.
- **Markings and labels are textures** (laser marking, silkscreen, barcode). Use geometry only where it
  changes the silhouette or the reflections.
- **Lights are invisible to the camera.** Only the backdrop is seen. Caustics stay off, clamp indirect is 4,
  and blur glossy is 0.5. These stop fireflies without a visible loss.
- **Animations:** turn persistent data off, because it caused flicker every N frames. Render a low-res motion
  preview of every frame and watch it as a video before the final.
- **Compositing into a user's photo** is hard. Read `references/photo-compositing.md` and set expectations
  first. A clean studio shot beats a bad composite.
- **LED glow:** use emission on the lens or phosphor plus a small point light just above it. Keep it subtle;
  a lit LED should not light up the whole room. `studio.py` hides every light it did not create, so do one
  of these:
  - use `--emit`;
  - tag your light with the custom property `hdt_keep_light = True`;
  - make the glow an emissive mesh hidden from camera rays.
- **Offsets from a component:** use `world_offset(obj, (dx, dy, dz))`, which applies rotation only. KiCad and
  GLB component empties often carry a 1000× scale, and `obj.matrix_world @ v` puts the point metres away.
- **Targets:** `--target` takes a collection, an object (with its children) or a glob. A glob that matches
  empties includes their children, and a glob can also match collection names (for a lineup).
- **Thin translucent parts over a dark cavity** (membranes, TPU button caps, light windows) read dark with
  a large subsurface scale. Use `MAT.get(kind, sss_mm=0.05)` unless the part is lit from inside.
- **Exploded views:**
  - **Gaps:** about each part's plan diagonal × sin(camera elevation) plus its height, so no part covers
    the next one in the image.
  - **Layout:** every part on one axis, in assembly order. Include every visible part (button caps,
    membranes, screws, gaskets).
  - **Check:** look at the image for parts that overlap in 2D, not only in 3D.
- **Engine:** Cycles with OptiX. An A/B test found LuxCore no better for studio products and much slower
  on a cold kernel cache (`references/cloud-gpu.md`).

## Scripts

| Script | What it does |
|---|---|
| `scripts/materials.py` | PBR library (enclosure, metals, PCB parts, solder, LEDs, fabric, floors) with wear and per-part color variation; `--list` shows all kinds |
| `scripts/studio.py` | recipes, camera, render settings, LED emission, the validation gate, sidecar JSON |
| `scripts/solder.py` | Young–Laplace solder fillets from `pads.json`, conformed to the board surface; `--only` and `--exclude` per part, `--edge-inset` |
| `scripts/solder_geom.py` | the pad rules of `solder.py` without Blender (wettable pads, inset, ref selection); tested by `scripts/test_solder_geom.py` |
| `scripts/kicad_pads.py` | `.kicad_pcb` → `pads.json`: a thin wrapper around `pcb-engineer`'s exporter (same format) |
| `scripts/contact_sheet.py` | join previews into one sheet |
| `scripts/selftest.py` | builds a test product and board, runs every recipe at thumbnail size; run it on a render machine (cloud GPU), not on a laptop that is also running the session |

All scripts run headless (`blender -b … --python <script> -- <args>`), print one summary line, and return a
non-zero code on failure. They work in scenes built in millimetres or in metres: sizes, light power and
texture scales follow the scene units.

## References

- `references/realism-checklist.md` — run it on every image before showing it.
- `references/lighting-recipes.md` — each recipe, light by light, and when to change it.
- `references/shot-list.md` — which shots tell the product story, with framing for each.
- `references/materials.md` — material values and the physics behind them, including solder.
- `references/photo-compositing.md` — placing the product into a real photo (camera match, shadow catcher,
  grain match).
- `references/cloud-gpu.md` — rendering on a cloud GPU, with speed and cost and the Cycles-versus-LuxCore note.
