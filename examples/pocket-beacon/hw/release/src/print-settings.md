# Print settings · prototype enclosure

| Part | File | Process | Material | Orientation | Layer | Supports | Post-processing |
|---|---|---|---|---|---|---|---|
| Front shell | `mech/shell.stl` | SLA | graphite: Tough 2000 or Grey Pro class resin; smoke: Clear resin | front face up, tilted 30° | 50 µm | on the inside rim only, never on the front face | wash, post-cure per the resin data sheet, sand the support marks with 800 grit |
| Back plate | `mech/plate.stl` | SLA | same resin as the shell | outer face up, tilted 30° | 50 µm | on the inner face | wash, cure; check the door recess flatness ≤ 0.05 mm |
| Cell door | `mech/door.stl` | SLA | same resin as the shell | outer face up | 50 µm | on the inner plug | wash, cure; clear the screw holes with a Ø1.5 mm drill by hand |
| Button cap | `mech/button.stl` | SLA | flexible resin, 80A (stands in for the two-shot TPU of production) | flat, nub down | 50 µm | on the flange | wash, cure; translucent finish lets the LED through |

## Clear parts

A printed clear part is foggy until it is finished. For the smoke shell:

1. Wash and cure per the resin maker's data sheet (Clear resin: 15 min IPA wash, 15 min at 60 °C) [estimate: confirm on the resin data sheet].
2. Wet-sand 400 → 800 → 1500 → 3000 grit, then 5000–12000 on the front face.
3. Finish with a thin 2K clear coat, or a dip in the same resin and re-cure.
4. QC: text under the part readable at 30 cm, no visible layer lines on the front face.

## Service bureau order (if not printed in-house)

| Field | Choose |
|---|---|
| Material | SLA standard resin, black or grey (graphite), white (chalk), clear (smoke); flexible 80A for the button |
| Finish | standard, supports removed; sanded + clear coat for the smoke shell |
| Tolerance | ISO 2768-m; critical: door recess and screw bosses per `mech/tolerances.md` |
| Quantity | 10 sets + 2 spare sets |
