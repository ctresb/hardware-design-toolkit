# Materials

`scripts/materials.py --list` prints every kind. The values below are why they look real. Change them only
when you can say what the real material does differently.

## Units

Texture scales are features per millimetre, and bump distances are in millimetres. The library converts both
to Blender units from `scene.unit_settings.scale_length`, or from `--bu-per-mm`. If the scene's unit settings
are wrong, fine detail is 1000× too big or vanishes. Check the setting first.

## Enclosure plastics

| Kind | Base | Roughness | Other | Why |
|---|---|---|---|---|
| `plastic_clear` | (0.97, 0.985, 1.0) | 0.015 + wear | transmission 1, IOR 1.585 (PC; PMMA 1.49), volume absorption 0.05/mm slightly blue, coat = skin-oil film where fingerprints are | polished PC is not glass: it has a faint tint, softer highlights and fingerprints |
| `plastic_black` | 0.010 | 0.50 (fingerprints make it smoother: oil fills the texture) | mold texture bump ~40/mm, 0.004 mm | satin molded black; glossy CG black looks cheap |
| `plastic_white` | (0.80, 0.80, 0.77) | 0.38 | subsurface 0.6, radius warm, scale 0.6 mm | real white plastic glows a little at edges; pure white loses its form |
| `plastic_color` | from `color=` | 0.42 | light subsurface | colored PC/ABS |

### Wear

`wear` is 0–1, default 0.5.

| Layer | Look | Source | Effect |
|---|---|---|---|
| Fingerprints | ridges ~0.45 mm apart in oval patches; about one patch in three cells of ~16 mm | ambientCG `Fingerprints009`, tiled at 120 mm | roughness and coat |
| Smears | large soft blotches | `Smear003` | roughness |
| Micro-scratches | thin, long, sparse lines | `Scratches005` | roughness, plus a slight inward bump |
| Dust | specks on faces whose normal points up | `SurfaceImperfections015` | sheen |

- The pattern is offset per object, so two parts never share it.
- Each source is the real CC0 scan when it is in `--wear-textures`, and procedural otherwise.
- **Scale cues matter.** A fingerprint the size of the whole product reads as a smudge on a giant object.
  Keep the 120 mm tile even when the product is 30 mm.

## Metals

| Kind | Base | Roughness | Notes |
|---|---|---|---|
| `aluminum_anodized` | from `color=` | 0.32–0.42, bead-blast noise | fingerprints darken and smooth it |
| `aluminum_brushed` | (0.91, 0.92, 0.92) | 0.18–0.30 | anisotropic 0.8, grain stretched ×40 |
| `stainless` | (0.80, 0.79, 0.77) | 0.10 + scratches | polished 316L contacts |
| `gold` | (1.0, 0.77, 0.36) | 0.14–0.26, stretched grain | hard gold contacts, pogo pins |
| `nickel` | (0.70, 0.69, 0.66) | 0.22–0.34, brushed | springs, cans, shields |
| `tin` | (0.60, 0.60, 0.58) | 0.40–0.58, crystalline grain | matte tin terminations |

## PCB and components

The GLB/VRML models from KiCad have every material metallic with flat colors. Remap every material by role:
- KiCad 3D color → material kind;
- reference prefix → part class (R, C, L, U, D, J).

| Kind | Look | Values |
|---|---|---|
| `ic_epoxy` | silica-filled mold compound, bead-blasted | palette of 3 near-blacks per lot; spec level 0.35; roughness 0.50–0.68; Voronoi grain; shader bevel 0.04 mm |
| `laser_marking` | the laser burns the resin: grey and duller, not white | 0.105 grey, roughness 0.92 |
| `mlcc` | caramel ceramic, each part a different lot | palette (0.46,0.34,0.20) … (0.30,0.20,0.11); sheen 0.25; slight subsurface |
| `resistor_film` | black overglaze | roughness 0.28–0.40 |
| `alumina` | off-white ceramic | (0.78,0.77,0.72) ±4 % |
| `ferrite` | molded powder, sparkly | metallic 0.25, coarse grain |
| `solder_mask` | glossy mask over FR4 | base color from the brief, coat 0.6 |
| `enig` | immersion gold, slightly orange, satin | (1.0,0.74,0.40), roughness 0.28–0.36 |
| `solder_sac305` | satin, frosty, dendritic | roughness 0.10–0.24 noise at 2500/mm |
| `led_lens`, `led_body`, `led_phosphor` | clear silicone / white reflector / yellow phosphor | phosphor subsurface 0.6 |
| `silicon_die` | WLCSP/DSBGA back | dark, slightly glossy |

- **IC markings:** short lines of real-looking text (the part's marking code and a date code), as text
  objects, sized to ≤ 0.42 mm per line. Use the marking from the datasheet's "marking" section, not the full
  part number.
- **Pin 1** is a mold dimple in the same epoxy, with lower roughness (0.38). It is not a white dot.
- **LED dies:** an RGB LED shows three tiny dies (~0.15 mm) under the lens. A white LED shows yellow phosphor.

## Solder (`scripts/solder.py`)

- **Volume:** paste area × stencil (0.10 mm) × metal fraction (0.50), minus 0.02 mm left under the body.
- **Shape:** Young–Laplace constant-mean-curvature surface, with the contact line pinned at the pad edge and
  wetting up the termination:
  - chip passives up to 60 % of the end cap, at most 0.32 mm;
  - QFN 0.09 mm;
  - connectors 0.03 mm.
- **Cap:** a fillet holds at most half the prism of the exposed area × wetting height. The rest stays under the
  part, which prevents blobs on mostly covered pads.
- **Fully covered pads** (BGA, LGA centers) get no visible fillet.
- **Placement:** the base of each fillet is ray cast to the actual board surface, so it stays flush on bent
  flex boards.
- **Orientation:** the footprint frame (KiCad y-down, B-side mirrored) is matched to the 3D model by picking
  the symmetry, among 8, that puts the pads under the body. Decide it with all pads, before removing
  mounting tabs.
- Small wrinkles and asymmetry are real. A smooth identical blob on every pad is not.

## Cords, straps and fabric

- **Braided cord:** model the real braid. Use 16 elliptical strands, 8 each way, in a 2-over-2-under
  pattern, around a dark core, with UVs along each strand. Material: `cord_braided`, with fibers along the
  UV, anisotropy 0.7 and sheen 0.45.
- **Path:** a centripetal Catmull–Rom spline, with frames by parallel transport, so the braid does not
  twist artificially.
- **Draping:** when the cord lies on a surface (keys, a table), simulate it. Use position-based dynamics
  against the surface's signed distance field. A hand-placed spline floats.
- Add a few loose fibers (lint), 0.2–0.6 mm curls coming out of the braid, and a few on nearby surfaces.
- **Black cords read best.** A light cord shows every modeling flaw.

## Scene

- `floor_matte`: roughness 0.8, slight relief.
- `floor_gloss`: black acrylic with a coat, for hero reflections.
- Dust specks: flattened icospheres of 20–70 µm, on up-facing surfaces only.
- Lint: curved fibers ~6 µm thick, lying on the surface.
- Use fewer specks on white products, more on black ones, where they show.
