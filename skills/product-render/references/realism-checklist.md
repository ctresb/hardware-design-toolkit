# Realism checklist

Run this list on every image before you show it. Each item is a correction a real user made to a real render.
If an item fails, fix it and re-render. Do not explain the failure away.

## 1. Geometry (before rendering)

- [ ] The assembly validator passed on this exact file and pose: no interpenetration, no broken faces, no
      zero-area faces, no loose vertices.
- [ ] No part floats. Solder touches its pad, the battery sits in its pocket, labels lie on surfaces.
- [ ] Parts are sized by datasheet **maximum** dimensions. A part that only fits at nominal size will collide
      in the real product.
- [ ] Shapes are physically possible. A pouch cell has straight edges and a sealed border. Molded plastic
      has draft and minimum wall thickness. A flex board bends with a radius, not a crease.
- [ ] Coincident surfaces are separated by 0.02–0.03 mm (a decal on glass, glass on a colored layer).
      Otherwise the ray tracer flickers between them, triangle by triangle.

## 2. Composition

- [ ] **The product faces the camera.** No accidental back views. The back appears only in a shot about the
      back.
- [ ] The subject fills the frame on purpose (about 50–70 % of the short side for a hero) and is not cropped
      by accident. Vertical frames use sensor height 36 mm.
- [ ] Scale is readable: a hand, a keyboard, a cord or a table texture tells the viewer how big the product
      is. A small product with no scale cue looks like a big one.
- [ ] Horizon and verticals are level unless the tilt is deliberate.
- [ ] Each image shows exactly the benefit its caption claims. If the caption says "glows when recording",
      the LED is visibly on.

## 3. Light

- [ ] No light source is visible in the image, unless it is part of the scene (a lamp, a screen).
- [ ] Edges are drawn by highlights (strip lights or HDRI), so the silhouette separates from the background.
- [ ] Metal and glass reflect something: an HDRI or shaped lights. Never an empty grey world.
- [ ] No big white sheet of reflection lies across a screen or window, unless that is the look you chose.
- [ ] Shadows: a contact shadow where the product touches a surface, and a softer cast shadow. A product
      with no shadow on a table floats.
- [ ] No fireflies, no blotchy denoising. Raise samples before raising the clamp.
- [ ] A lit LED is subtle and plausible. It glows through its window and does not flood the scene.

## 4. Materials

- [ ] Surfaces carry wear at a plausible level: fingerprints near where the product is held, micro-scratches,
      a few dust specks on up-facing faces. A new product still has some.
- [ ] Clear plastic reads as plastic: slight absorption tint, softer highlights than glass, fingerprints.
- [ ] Black plastic is satin with a molded texture, not glossy CG black. White plastic has subsurface
      scattering, not flat white.
- [ ] Parts that come from different lots differ slightly in color (capacitors, plastic parts).
- [ ] PCB parts look like their real materials: matte bead-blasted epoxy with grey laser marking on ICs,
      caramel ceramic MLCCs, matte tin terminations, satin SAC305 solder with a frosty surface, ENIG pads
      slightly orange.
- [ ] Cords and fabric have fiber structure (braid, sheen, anisotropy) and a few loose fibers.
- [ ] Skin has subsurface scattering and stays as bright as the product. Studio light must not leave the hand
      dark.

## 5. Camera

- [ ] Focal length is 85–105 mm equivalent for product shots, with no wide-angle bulge.
- [ ] Depth of field is consistent: objects at the same distance have the same blur. A sharp cord next to
      blurred keys reads as a fake.
- [ ] The focus point is where the eye should go (the front edge, the LED, the logo).
- [ ] For composites, the CG has the same softness, grain and noise as the photo (see
      `photo-compositing.md`).

## 6. Color

- [ ] View transform: AgX (Base Contrast) for studio shots, Khronos PBR Neutral when colors must stay true
      (colorways, screens).
- [ ] Colorways match the brief. A black product reads as black, not dark grey.
- [ ] Export is 16-bit PNG, plus EXR when the image will be composited or graded.

## 7. Before you call it done

- [ ] Look at the image at 100 % zoom: edges, solder, text, small parts.
- [ ] Compare it to a real product photo of a similar object. Put them side by side and ask which one looks
      fake.
- [ ] Write in `hw/decisions.md` any rule the user gave while correcting a render, so the next shots follow it.
