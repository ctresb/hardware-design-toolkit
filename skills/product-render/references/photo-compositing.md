# Placing the product into a real photo

Users often send a photo, such as their desk or their keyboard, and ask for the product "in it". This is the
hardest kind of render to make convincing. Say so before you start. Offer a studio shot as the reliable
option, and treat the composite as an experiment that can fail. A user who saw two bad composites dropped the idea
entirely. A failed composite costs more than a skipped one.

## When it can work

- The photo is sharp at the spot where the product goes, and the light in it is readable: the window
  direction, any screen glow, the shadows.
- The photo has known geometry near that spot, such as keyboard keys, a ruler, a sheet of paper, or a phone of
  known size. You can calibrate the camera from it.
- The EXIF data is intact: focal length and sensor, aperture, ISO. HEIC is fine. Convert it to a 16-bit PNG
  or EXR with the platform tool (`sips` on macOS, `heif-convert` or ImageMagick elsewhere).

## Procedure

1. **Camera match.**
   - Take the focal length from EXIF, as a 35 mm equivalent.
   - Click or detect at least 8 points of known geometry, and solve the camera pose with PnP using that
     fixed focal length.
   - Check the reprojection error: under ~10 px at 4K is good.
   - Write the calibration to JSON, so the shot is reproducible.
2. **Proxy geometry.** Model the surfaces near the product: the tabletop or keys, and the screen if it lights
   the scene. Make them shadow catchers (`is_shadow_catcher`), so they receive the product's shadow and
   reflections without rendering themselves.
3. **Light match.**
   - Find each light in the photo (window, lamp, screen), with its direction, color and softness.
   - Recreate it as area lights. A screen becomes an emissive plane that shows the photo's own screen
     content.
   - Add an HDRI made from the photo, or a similar one, for reflections.
   - Check the result: the product's shadow must point the same way, and be as soft, as the shadows of real
     objects in the photo.
4. **Physical contact.** A cord or soft part must rest on the proxy, not float over it. Simulate the drape
   against the proxy's distance field.
5. **Render passes.** Output a multilayer EXR with Combined, the Noisy Image, and the Shadow Catcher pass.
6. **Compose in linear light.**
   - Use the photo in linear color.
   - Composite: `out = CG + photo × shadow × (1 − alpha)`.
   - The shadow is luminance only, slightly blurred, and applied only where it really darkens, with a small
     dead zone. Far from the product the result must equal the photo exactly. Check that the difference is 0
     there.
7. **Match the camera's flaws.**
   - **Softness.** Measure the edge width (10–90 %) of a sharp edge in the photo, and blur the CG to match,
     with a Gaussian sigma ≈ edge width / 2.6. A phone at f/1.6, 1/15 s and ISO 1600 is softer than any
     render.
   - **Denoiser wax.** Mix 5–10 % of the noisy pass back in to remove the waxy look.
   - **Grain.** Measure the band-pass noise of the photo (the image minus a 12 px Gaussian of it) on a flat
     patch, separately for luma and chroma. Generate noise with the same measures, and add it only over
     the CG.
   - **Sharpening.** Apply a light unsharp mask only if the photo shows phone sharpening halos.
8. **QA.**
   - Show the composite next to the original.
   - Check the shadow direction, the softness, the grain, the reflections (does the product reflect the
     screen?) and the depth of field. Objects at the same depth have the same blur.

## Typical failures

| Symptom | Cause | Fix |
|---|---|---|
| Product looks pasted on | CG sharper than the photo | measure the photo's softness and match it |
| Product floats | no contact shadow, or the cord does not touch the surface | shadow catcher, plus drape simulation |
| Wrong mood | product lit by the studio, not by the room | rebuild the lights from the photo |
| Plastic too clean | no wear | turn wear up; real objects on a desk have dust |
| Colors off | composed in sRGB | compose in linear light |

If the composite still fails after one careful attempt, show the best result honestly and recommend the
studio shot.
