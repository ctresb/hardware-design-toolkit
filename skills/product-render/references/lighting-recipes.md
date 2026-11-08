# Lighting recipes

`scripts/studio.py` builds each recipe around the target's bounding box:

- **S** is the largest dimension of the product.
- **Positions** are azimuth and elevation relative to the camera azimuth, so the lights follow any view.
- **Distances** are multiples of S.
- **Light power** is `k × distance²`, which keeps irradiance the same at any scale and in any unit system.
  Tune exposure with `--exposure`. Do not tune it by changing the power.

All lights have `visible_camera = False`. Only the backdrop, or the world color, appears behind the product.

## Common render settings

| Setting | Value | Why |
|---|---|---|
| Engine | Cycles, OptiX (CUDA/HIP/Metal fallback) | path tracing for glass, plastic and metal |
| Max / transmission / glossy bounces | 24 / 24 / 12 | clear plastic and LED windows need many transmission bounces |
| Caustics | off | they cost noise for no visible gain in studio shots |
| Clamp indirect | 4 | removes fireflies from small bright highlights |
| Filter glossy (blur glossy) | 0.5 | same, with no visible blur |
| Denoise | on (OpenImageDenoise or OptiX) | always; raise samples if blotchy |
| Persistent data | off | caused a 4-frame flicker in an animation |
| Output | PNG 16-bit (+ EXR for compositing) | grading headroom |

Sample presets: `tiny` 16, `preview` 64, `final` 512, `hero` 1024 spp (adaptive).

## dark-studio (default hero)

This is the "premium product" look: a near-black room, a product drawn by light, and edges that glow.

| Light | Position (rel. to camera) | Size | k | Role |
|---|---|---|---|---|
| Key softbox | az −38°, el 26°, 9 S | 5 S × 9.3 S | 8.0 | large soft key from one side; makes the gradient on curved surfaces |
| Strip left | az −133°, el 25°, 6.2 S | 0.33 S × 10.7 S | 8.6 | behind left; draws the left silhouette edge |
| Strip right | az +131°, el 23°, 5.7 S | 0.33 S × 10.7 S | 8.0 | behind right; draws the right edge (slightly warm) |
| Top weak | el 81°, 8.8 S | 4 S × 4 S | 0.43 | lifts the top surface out of black |

- World: (0.012, 0.012, 0.013). Not pure black, so the darkest plastic keeps some form.
- Look: AgX Base Contrast.
- The two strips are slightly cool (left) and slightly warm (right). This reads as real studio light.
- For a lit LED, add `--emit "LED*=1,0.86,0.70:60"`. Keep the strength below the point where the window
  blooms.
- A clear product: the strips show its thickness. A black product: the key gradient carries the form, so
  move the key elevation (20–35°) until the top face shows a gradient instead of a flat patch.

## tabletop-hdri ("on the desk")

- Use a real studio HDRI for reflections, for example Poly Haven `studio_small_09` (CC0), at strength
  0.4–0.8. Metal and glass look real only through what they reflect.
- Rotate the HDRI (`--hdri-rotation`) and compare 3–4 rotations on a contact sheet before the final.
- Matte table (`floor_matte`), color from the brief. Oak, linen or stone textures can replace it.
- A soft key above-left makes the shadow; a strip behind draws the edge.
- View transform: Khronos PBR Neutral. It keeps product and screen colors true.
- Use a 30–48° side angle so the side material shows. A pure front view hides it.

## white-seamless (catalog)

- Curved seamless backdrop, so there is no horizon line. Overhead softbox, two side fills (1.0 / 0.75 ratio)
  and a back strip for the edge.
- **Risk:** a white product on white turns into a flat shape. Use the dark colorway, darken the backdrop to
  ~0.5, or add black flags (planes) to put dark reflections on the edges.

## hero-float (landing page)

- The product floats over a dark graphite wall. A soft area light low on the wall makes the gradient behind
  it.
- Key from one side, two rim strips. Optional glossy black floor (`--floor gloss`) for a soft reflection;
  `--float-gap` sets the height.
- Leave negative space where the page copy goes: frame wider (`--fill 0.45`) and offset the product (`--az`).

## Lighting a hand

A rigged hand under studio light often goes dark.
- Add a large soft fill from the camera side.
- Give the skin subsurface scattering (radius ~1 mm in red, less in green and blue).
- Check that the skin stays as bright as the product.

## Variations worth comparing on a sheet

- HDRI rotation: 0, 90, 180 and 270°.
- Key elevation: 20, 26 and 35°.
- f-stop: 5.6, 8 and 11.
- Exposure: −0.3, 0 and +0.3.
- Colorway.

Render them with `--format preview`, join them with `contact_sheet.py`, and pick one before the final.
