# `board.json` format

One JSON file describes every board of the product. `scripts/spec.py` loads it and fills in the defaults. A complete working example is in `templates/example/board.json`.

## Top level

| Key | Type | Default | Meaning |
|---|---|---|---|
| `project` | string | file name | project name |
| `library` | string | `"project"` | nickname of the generated library (`<library>.kicad_sym`, `<library>.pretty`) |
| `company` | string | `""` | title block |
| `footprint_silk` | `"keep"` or `"fab"` | `"keep"` | `"fab"` moves the footprint silkscreen to the Fab layer. Use it on boards under ~30 mm. |
| `symbols` | object | `{}` | generated symbols (below) |
| `footprints` | object | `{}` | generated footprints (below) |
| `models` | object | `{}` | 3D model overrides per footprint name: `{"Fp": {"file": "vendor/part.step", "offset": [x,y,z], "rotate": [x,y,z]}}`. Paths are relative to the spec. |
| `sym_libs` | object | `{}` | extra symbol libraries: `{"nordic": "vendor/nordic.kicad_sym"}`; then use `"nordic:nRF54L15"` |
| `fp_libs` | object | `{}` | extra footprint libraries: `{"vendor": "vendor/vendor.pretty"}` |
| `fab` | object | JLCPCB | `{"name": "jlcpcb", "assembly": "standard", "min_assembly": [70, 70], "quantity": 10}`: the assembler's minimum size and the order quantity, used by `fabnotes.py` and `release_check.py` |
| `boards` | object | required | one entry per board, keyed by board name (lowercase, hyphens) |

## Board

| Key | Default | Meaning |
|---|---|---|
| `title`, `rev` | name, `"A"` | title block |
| `outline` | required | see Outline |
| `stackup` | `"2L-1.6"` | preset (`2L-1.6`, `2L-1.0`, `2L-0.8`, `2L-0.6`, `4L-1.6`, `4L-1.0`, `4L-0.8`, `4L-0.6`, `6L-1.6`, `6L-0.8`, `2L-flex-0.11`, `2L-flex-0.13`, `1L-flex-0.07`) or a full object `{layers, thickness, finish, mask_color, stack: [[name, type, thickness, material], ...]}`. Replace the preset's dielectric split with the fab's published stack-up before an impedance-controlled order. |
| `finish` | `"ENIG"` | `ENIG`, `HASL(with lead)`, `LeadFree HASL`, `OSP`, `Immersion silver`... |
| `mask_color` | `Green` (flex: amber) | `Green`, `Black`, `White`, `Blue`, `Red`, or `#RRGGBBAA` |
| `edge_margin` | `0.2` | minimum courtyard-to-edge distance for the legalizer (mm) |
| `part_gap` | `0.0` | extra spacing between courtyards (mm); courtyards already include their own clearance |
| `rules` | fab defaults | KiCad design-rule minimums (`min_clearance`, `min_track_width`, `min_via_diameter`, `min_through_hole_diameter`, `min_via_annular_width`, `min_hole_to_hole`, `min_copper_edge_clearance`, `min_hole_clearance`, `min_text_height`, ...) |
| `netclasses` | `{}` | `{"Power": {"track_width": 0.25, "clearance": 0.12, "via_diameter": 0.45, "via_drill": 0.25, "nets": ["VBAT", "VSYS"]}}`. Add `"impedance": {"ohms": 50, "type": "microstrip", "layer": "F.Cu", "ref": "In1.Cu"}` to RF and high-speed classes: `stackup.md` then estimates the width and the order notes request impedance control. |
| `fiducials` | `[]` | `[{"x": 8, "y": 0, "side": "F"}]`: board fiducials (become FID1… with `Mechanical:Fiducial` and `Fiducial:Fiducial_1mm_Mask2mm`). Use ≥ 2 per assembled side, or put them on the panel rails. |
| `panel` | `{"mode": "none"}` | `{"mode": "fab" or "kikit", "array": [3, 3], "spacing": 2.0, "rails": 5.0, "rail_sides": "all"/"tb"/"lr", "tabs": "mousebites", "fiducials": "rails"}`. Required when the board is below `fab.min_assembly`. `fab` writes the panel request into `order.md`. `kikit` writes a KiKit preset and the `kikit panelize` command; `release_check` then needs the panel file. |
| `release` | `{}` | `{"allow_drc_warnings": ["..."]}`: extra DRC warning types accepted by `release_check.py`, each one justified in `hw/decisions.md` |
| `planes` | `[]` | copper pours: `{"net": "GND", "layer": "In1.Cu", "priority": 0, "clearance": 0.15}`. The outline is the board, unless the plane has its own `circle`/`rect`/`polygon`. Inner layers with a plane become power layers. |
| `keepouts` | `[]` | see Keepouts |
| `exclusive` | `[]` | `{"name": "RF corner", "rect": [x0, y0, x1, y1], "only": ["ANT1", "L3", "C10"]}`: only the listed parts may overlap this area |
| `texts` | `[]` | `{"text": "REV A", "x": 0, "y": -8, "layer": "B.Fab", "size": 0.6}`; back-layer text is mirrored |
| `groups` | one block | schematic blocks: `[{"title": "Power", "refs": ["U2", "C11"]}]`. Unlisted parts go in "Other". |
| `pwr_flags` | `"auto"` | nets that get a PWR_FLAG. Auto: every net with a `power_in` pin and no `power_out` pin (batteries, connectors). |
| `parts` | `[]` | see Parts |

## Outline

All forms are in mm, in the device frame: origin at the board center, +x right, +y up, seen from the F side.

```json
{"type": "circle", "r": 10}
{"type": "rounded_rect", "w": 24, "h": 16, "r": 2}
{"type": "polygon", "points": [[-5, -5], [5, -5], [5, 5], [-5, 5]]}
{"type": "svg", "file": "../mech/board_outline.svg", "size": 19.2}
{"type": "union", "fillet": 0.6, "shapes": [{"circle": [0, 0, 6.3]}, {"rect": [-3, -18, 3, -4]}]}
```

- `svg` reads the first `<path d=...>` of the file (`path_index` selects another). It scales the path so its larger side is `size` mm and centers it. Use `svg_scale` instead for a fixed mm-per-unit scale.
- `union` is a smooth union of circles, rectangles and polygons. Use it for flex boards: a flex tears at sharp inner corners, so `fillet` (mm) rounds every corner and junction: rect corners, polygon corners (convex and concave) and the joins between shapes.
- Any form accepts `"scale": k` and `"inset": d`. `inset` shrinks the outline inward by `d` mm, for example by the enclosure wall clearance.

## Keepouts

```json
{"name": "magnet NE", "side": "B", "circle": [5.2, 5.2, 1.75]}
{"name": "battery", "side": "F", "rect": [-8, -9, 8, -2]}
{"name": "antenna ground clearance", "parts": false, "copper": true, "rect": [-2.6, 6.9, 2.6, 10.2]}
{"name": "screw boss", "side": "both", "polygon": [[...]], "allow": ["TP1"]}
```

| Key | Default | Meaning |
|---|---|---|
| `circle` / `rect` / `polygon` | required | the area, device frame |
| `side` | `"both"` | `F`, `B` or `both`: which side's parts are kept out |
| `parts` | `true` | the legalizer keeps courtyards out |
| `allow` | `[]` | parts allowed inside anyway |
| `copper` | `false` | also add a KiCad rule area with no copper pour (and no vias) |
| `layers` | `"all"` | copper layers for the rule area, e.g. `["F.Cu", "In1.Cu"]` |
| `no_tracks`, `no_vias` | `false`, `true` | extra rule-area restrictions |

## Parts

| Key | Default | Meaning |
|---|---|---|
| `ref` | required | reference designator |
| `symbol` | required | `Lib:Name` (KiCad standard library or `sym_libs`) or a name in `symbols` |
| `footprint` | symbol's default | `Lib:Name` or a name in `footprints` |
| `value` | ref | value shown in the schematic and BOM |
| `manufacturer`, `mpn`, `lcsc`, `description` | `""` | BOM fields. `mpn` is the full orderable part number. Cite the datasheet section in `description`. |
| `pins` | `{}` | `{pin number or pin name: net or null}`. A pin name applies to every pin with that name (for example `"VSS": "GND"`). `null` marks a deliberate no-connect. |
| `nc_rest` | `false` | every pin not listed becomes a no-connect. Use it for unused GPIOs only. |
| `x`, `y`, `rot` | `0` | position (mm) and rotation (degrees, counter-clockwise seen from F), device frame |
| `side` | `"F"` | `F` or `B` |
| `fixed` | `false` | the legalizer never moves it; collisions are reported |
| `max_move` | 2.5 (ICs) / 4.0 (2-pin) | how far the legalizer may move it (mm) |
| `lock_rotation` | `false` | do not try the 90° alternative for 2-pin parts |
| `allow_overlap` | `[]` | refs of parts this part may overlap on purpose (a test pad inside a battery holder's open frame). The legalizer tests real courtyard polygons, not bounding boxes, and lets a part whose pads are all on one net sit over a through-hole pad of that net |
| `dnp` | `false` | do not populate (tuning and option parts) |
| `in_bom` | not `dnp` | include in the BOM |
| `consign` | `false` | the part has no assembler part number and is shipped to the assembler; listed in `order.md` |

### Shortcuts for 2-pin parts and test points

```json
{"ref": "C1", "kind": "C", "value": "100nF", "size": "0201", "nets": ["VDD", "GND"], "x": 1, "y": 2}
{"ref": "TP1", "kind": "TP", "nets": ["SWDIO"], "side": "B"}
```

| `kind` | Symbol | Footprint (by `size`: 0201, 0402, 0603, 0805, 1206) | Pins |
|---|---|---|---|
| `R` | Device:R_Small | Resistor_SMD:R_<size>_<metric>Metric | 1, 2 |
| `C` | Device:C_Small | Capacitor_SMD:C_... | 1, 2 |
| `L`, `FB` | Device:L_Small, FerriteBead_Small | Inductor_SMD:L_... | 1, 2 |
| `LED`, `D` | Device:LED_Small, D_Small | LED_SMD:LED_..., Diode_SMD:D_... | 1 = K (cathode), 2 = A |
| `TP` | Connector:TestPoint | TestPoint:TestPoint_Pad_D1.0mm | 1 |

`nets` lists the nets in pin order.

## Generated symbols

```json
"symbols": {
  "LIS2DH12": {"ref": "U", "description": "...", "datasheet": "https://...",
    "pins": [["1", "SCL/SPC", "input", "L"], ["9", "VDD", "power_in", "T"], ["6", "GND", "power_in", "B"]]}
}
```

Each pin row is `[number, name, electrical type, side]`:

- the side is `L`, `R`, `T` or `B`;
- the electrical type is one of `input`, `output`, `bidirectional`, `tri_state`, `passive`, `power_in`, `power_out`, `open_collector`, `open_emitter`, `no_connect`, `free` or `unspecified`.

Use `power_out` only for pins that really supply a rail (regulator and charger outputs). ERC and the automatic PWR_FLAG depend on it.

## Generated footprints

```json
"footprints": {
  "SENSOR_LGA8_2x2": {
    "description": "Land pattern from datasheet rev 3, figure 12 (recommended footprint)",
    "pads": [{"n": "1", "x": -0.65, "y": -0.75, "w": 0.35, "h": 0.5, "shape": "roundrect"},
             {"n": "", "x": 0, "y": 0, "w": 0.6, "type": "npth"}],
    "courtyard": [-1.2, -1.2, 1.2, 1.2],
    "body": {"w": 2.0, "l": 2.0, "h": 0.9, "color": [0.1, 0.1, 0.11]}
  }
}
```

| Pad key | Default | Meaning |
|---|---|---|
| `n` | required | pad number, matching the symbol's pin numbers (`""` for mechanical holes) |
| `x`, `y`, `w`, `h`, `a` | `h = w`, `a = 0` | KiCad footprint frame: mm, **+y down**, origin at the part center |
| `shape` | `roundrect` | `rect`, `roundrect`, `circle`, `oval` |
| `type` | `smd` | `smd`, `thru` (needs `drill`), `npth` |
| `paste` | `true` | paste opening (set `false` for spring contacts, test pads, mic sound holes) |
| `mask_margin`, `paste_margin` | KiCad default | per-pad solder mask and paste expansion (mm) |
| `rratio` | 0.25 | roundrect corner ratio |

- `courtyard` defaults to the pads plus 0.15 mm, grown to cover the `body`.
- `body` writes a VRML box and a STEP box of the given **maximum** size, so the GLB and STEP exports carry the right envelope.
- A real vendor model goes in `models`.

## Coordinates in the outputs

- KiCad sheet: the device origin is at (100, 100) mm on the sheet, and the sheet's +y points down.
- `export/<board>.glb` and `.step` use the device origin as the file origin.
- `export/pads.json`: per board and footprint, `x, y, rot` are KiCad sheet values. `x_dev, y_dev` are the device frame. Pad `x, y, a` are footprint-local and unrotated.
- `fab/<board>/<board>_cpl.csv` uses the same absolute frame as the Gerbers, which is what assemblers expect. Check the assembler's rotation conventions before ordering (`references/workflow.md`).
