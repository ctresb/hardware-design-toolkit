---
name: technical-drawing
description: Produces vector technical drawings of a product assembly from its Blender model. Outputs an exploded isometric "blueprint" with numbered balloons, a bill of materials, per-unit envelopes and a title block, plus orthographic front/top/side views with overall dimensions. Results are SVG, PDF and PNG files for quotations (RFQ), suppliers and presentations. Use when the user asks for a blueprint, exploded view, technical drawing, dimensioned views or a drawing to get quotes.
---

# Technical drawing

This skill turns a validated 3D assembly into drawings that a supplier can quote from. The output is vector linework: hidden lines are removed, every part has a numbered balloon, and the parts list has real dimensions. Talk to the user in their language. The drawings themselves use the language set in the config `labels`.

## Inputs

- The assembly `.blend` in `hw/mech/`, from `enclosure-engineer`, after the geometry validator passed (`hw/validation/`). Do not draw an assembly that failed validation. Parts that intersect produce wrong linework and a wrong drawing.
- `hw/bom.csv` for item names, part numbers, materials and quantities.
- `hw/brief.md` for the product name. `hw/state.json` for the revision (EVT-0, DVT-1 …).

## Outputs

- `hw/drawings/drawing.json`: the config. Keep it in the project so the drawing can be regenerated after every design change.
- `hw/drawings/<name>_blueprint.svg|pdf|png`: the exploded view, blue theme.
- `hw/drawings/<name>_print.svg|pdf|png`: the exploded view, white theme for print and PDFs.
- `hw/drawings/<name>_ortho_<theme>.svg|pdf|png`: the orthographic views with overall dimensions. Themes come from `ortho_themes`, or from `themes` when it is not set.
- **One slide per drawing.** `product-presentation` turns every file stem in `hw/drawings/` into a slide. Keep one theme there, usually print. Put the other theme in `hw/drawings/<theme>/`, for example `hw/drawings/blue/`.
- `hw/drawings/<name>_items.json`: the anchor, envelope and visibility of each item. Other skills reuse it, for example `product-presentation`.

## Gate

The drawing is done when all of these hold:

1. The script ends with `BLUEPRINT ok` and lists neither `ITEMS WITHOUT GEOMETRY` nor `hidden in this view`.
2. You have looked at the PNG and every check in "Review" passes.
3. The BOM items match `hw/bom.csv`: same items, same quantities.

## Tools

Everything runs headless in Blender, with no UI. Tested with Blender 5.2, using only bpy, mathutils and numpy. If `rsvg-convert` is installed (librsvg, via `toolchain-setup`), the scripts also write PDF and PNG. Without it they write SVG only.

```sh
# exploded isometric + BOM (both themes)
blender -b hw/mech/assembly.blend --python-exit-code 1 --python ${CLAUDE_SKILL_DIR}/scripts/blueprint.py -- hw/drawings/drawing.json hw/drawings/product
# orthographic views with overall dimensions
blender -b hw/mech/assembly.blend --python-exit-code 1 --python ${CLAUDE_SKILL_DIR}/scripts/ortho_views.py -- hw/drawings/drawing.json hw/drawings/product
# self-test on a fictional assembly (builds it, draws it)
BLENDER=/path/to/blender ${CLAUDE_SKILL_DIR}/scripts/selftest.sh /tmp/td-selftest
```

- `scripts/drawing_core.py`: the shared engine, covering mesh extraction, feature edges, ray visibility, sheets, title block and export.
- `scripts/line_clean.py`: the line-merge pass used by `ortho_views.py`. It removes the short ticks and dots that two nearly coincident outlines leave at a seam. Configure it with `line_clean`: `{"enabled", "tol_mm", "maxlen_mm"}`, in paper mm. It is pure Python and tested by `scripts/test_line_clean.py`, which needs no Blender.
- `ortho_include`: the group names to draw in the orthographic views, for example only the exterior parts. All groups are drawn when it is not set.
- `scripts/make_test_scene.py`: builds the fictional sensor puck used by the self-test and by `templates/blueprint.example.json`.

On a large assembly with 1M+ triangles and thousands of parts, ray casting can take minutes. Run it on the machine that holds the assembly. A cloud box is worth it only when it already runs the renders.

## Procedure

1. **Copy the template** `templates/blueprint.example.json` to `hw/drawings/drawing.json` and edit it. Every rule lists in order and the first match wins:
   - `frame_object`: the object whose local axes are the product axes, usually the top empty of the device. The drawing ignores how the device is posed for renders.
   - `root`: draw only meshes under this object.
   - `skip_prefixes`: solder, markings, labels, lights, cords and boolean cutters. They clutter the linework and are not parts.
   - `groups`: what moves together in the explode, with `offset_mm` along `explode_axis`. Use `"fine": true` for PCB assemblies so that the parts are drawn with thin lines.
   - `items`: BOM rows, as `id`, `name`, `spec`, `qty` and `match`. Put specific rules first, such as a connector found through its ancestor `J1`, and general rules after, such as "everything in the board collection".
   - A match rule takes `names` (base names, without `.001`), `prefixes`, `collections`, `ancestors`, or `all: true`.
   - `envelope` per item:
     - `auto`, the default: the whole item when qty is 1, else one unit "(each)";
     - `item`;
     - `largest`;
     - `all`: list each distinct unit, for example the two halves of a connector pair;
     - `false`.
   - `view`: azimuth 35° and elevation 24° is a good three-quarter view. Raise the elevation when the parts are flat.
   - `sheet`: A4, A3, A2, LETTER or TABLOID. `standard_scale: true` snaps to ISO 5455 scales.
   - `projection`: `third` (US) or `first` (Europe and most of Asia). Ask the user which market the supplier is in if it is unknown.
   - `title`: product, subtitle, revision, `date: "auto"`, units, sheet. `decimal: ","` for markets that use a decimal comma.
   - `labels`: translations of all fixed texts, such as "BILL OF MATERIALS" and "Item". Translate them all when the drawing goes to a non-English supplier.
2. **Choose explode offsets** so that each group clears the next in the projected view, not only in 3D.
   - Gap per flat part: about its plan diagonal × sin(view elevation), plus its height. For example, a 32 mm square part at 24° needs about 18 mm, not its thickness.
   - A thin flex or film hidden behind a cover needs more spacing, or it disappears.
   - Put every part on one axis, in assembly order, and include the small visible parts: button caps, membranes, screws and gaskets.
3. **Run `blueprint.py`** and read its last line.
   - `ITEMS WITHOUT GEOMETRY [n]`: a rule matched nothing. Fix the rule.
   - `hidden in this view [n]`: no point of item n is visible, so its leader is dashed. Increase that group's offset, move the part to its own group, or change the view.
4. **Look at the PNG.** Use the Read tool on the `_print.png`, then do the review below. Fix the config and run again until it is clean.
5. **Run `ortho_views.py`** for the overall-dimension sheet. Keep `hidden_lines: false` for assemblies. Dashed internals clutter the sheet. Turn them on for single parts.
6. **Check the numbers:** the overall size in the title block against `hw/brief.md` and `hw/requirements.md`, and each envelope against the datasheet's maximum dimensions in `hw/parts/`. A mismatch is a design error. Report it. Do not edit it in the drawing.
7. **Write the outputs** to `hw/drawings/` and record the drawing revision in `hw/state.json`.

## Review (look at every sheet before you show it)

- Every part is visible and has exactly one balloon. The dots sit on the part they name.
- Leaders do not cross and do not pass over another dot. Balloons do not overlap.
- No text leaves its cell. Long specifications wrap inside the table, and the table ends above the title block.
- Nothing touches the frame. The drawing is centred in its area.
- Outlines are clean single lines. A hatched or doubled edge means a mesh with split vertices. The engine merges vertices by position, so if it persists, check for duplicated, overlapping geometry in the model.
- Envelopes are per unit, and the overall size matches the product.
- The scale shown is a standard scale, and the sheet size is right for it. Small products often read better on A4 or Letter at the same scale.

## Taste and pitfalls

These are mistakes made and fixed while drawing a real wearable:

- **Hatched board edges.** Imported PCB meshes have split vertices at every face, so every edge looked like a boundary and the board edge became a comb of short strokes. Merge vertices by position before you classify edges. The engine does this.
- **Hidden parts.** A thin flex under the cover disappeared in the exploded view. The fix was more spacing between groups, not a different line style.
- **Crossing leaders.** Placing balloons in anchor order is not enough when two anchors are at nearly the same height. The engine places them in order with a minimum gap, then swaps slots while any two leaders cross or a leader runs over another dot.
- **Summed envelopes.** The BOM showed one item the size of all its instances added together. Envelopes are for one physical unit, and an assembly bought as one item, such as a PCBA, shows its whole envelope.
- **Axis views lose outlines.** In exact front, top and side views, many faces are seen edge-on. Treat edge-on faces as not front-facing when you detect silhouettes, or box outlines vanish.
- **Draw from the frozen, validated assembly.** Never draw a scene posed for a render (rotated, on a cord, with fibers). Set `frame_object` so that the product axes are used.
- **Title block overflow.** Bold values are about 0.64 em per character, not 0.56. With the lower estimate, "32.0 × 32.0 × 10.0 mm" ran into the next cell. The engine now shrinks values with the higher factor. Use `title.overall_size` for a shorter text.
- **Seam ticks in orthographic views.** A shell rim and a lid rim with 1° draft are both partly visible and leave short ticks along the seam. `line_clean` removes them. Check the seam at full resolution.
- **Do not decorate.** One accent color for balloons and leaders, ink for the linework, and a grid only on the blueprint theme. The drawing is a document, not a render.
- **Name parts the supplier understands.** Use a material and process ("PC, optical grade, injection molded, SPI A2"), a full orderable part number, and a quantity per product. Never use an internal nickname.

## References

- `references/drawing-standards.md`: what an RFQ drawing must contain, line types (ISO 128), title block (ISO 7200), scales (ISO 5455), projection methods, general tolerances (ISO 2768), and balloon and parts-list conventions. Read it before the first drawing of a project, and when the user asks for a drawing "by the standard".
- `templates/blueprint.example.json`: the full config, with comments, for the fictional test assembly.
