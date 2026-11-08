# `hw/release/release.json` fields

Paths are relative to `hw/`. The example is `templates/release.example.json`.

| Field | Type | Meaning |
|---|---|---|
| `product` | string | product name in the release documents |
| `rev` | string | release revision; the folder is `hw/release/<rev>/` |
| `target` | `prototype` \| `production` | the level the gate checks (`references/ready-to-build.md` §2) |
| `build_qty` | integer | units in this build; drives stock checks and purchase quantities |
| `stock_max_age_days` | integer | maximum age of a stock/price check (default 14) |
| `warnings_fail` | boolean | DRC/ERC warnings fail the gate (default false: listed as warnings) |
| `assembler.name` | `jlcpcb` \| `pcbway` \| `generic` | sets the BOM/CPL file names and the LCSC rule |
| `assembler.options` | object | order options to choose on the assembler's site, written to `options.md` |
| `assembler.consigned_refs` | list | refs that the assembler places but you supply |
| `boards[]` | list | one entry per board |
| `boards[].name` | string | board name, as in `hw/pcb/<name>/` |
| `boards[].kicad_pcb`, `drc`, `erc`, `netlist` | path | KiCad board, `kicad-cli` DRC/ERC JSON reports, netlist |
| `boards[].fab_dir` | path | where `pcb-engineer` put the Gerber zip, BOM and CPL |
| `boards[].pos` | path | KiCad position file, used only when no CPL exists |
| `boards[].fab_notes` | object | parameter → value, written to `fab/<board>/fab-notes.md` |
| `boards[].rotation_offsets` | object | footprint glob → degrees added to the CPL rotation |
| `enclosure_parts[]` | list | `name`, `step`, `stl`, `process` (SLA, MJF, CNC, injection), `material`, `qty` |
| `cad_sources` | list | CAD source files; the validator report must be newer than these and the STEP files |
| `validator` | path | `enclosure-engineer` validator JSON (`ok`, `n_interpenetrations`) |
| `drawing` | path | 2D drawing PDF from `technical-drawing` |
| `mech_bom[]` | list | `item`, `vendor`, `mpn`, `qty_per_unit`, `unit`, `url` |
| `docs.assembly_guide`, `test_plan`, `battery`, `print_settings` | path | documents written by this skill from its templates |
| `docs.assembly_images` | list | images used by the assembly guide |
| `doability` | path | `doability-review`'s `score.json` (output of `doability_score.py --json`): overall verdict in key `overall`, and the `prototype_checks` list |
| `verify_on_prototype` | path | optional hand-written "Verify on the prototype" list; if absent, it is generated from `prototype_checks` in `score.json` |
| `firmware.board`, `firmware.mcu_ref` | string | board and MCU ref for the pin map |
| `attrition.default_pct`, `min_extra`, `passive_prefixes`, `passive_min_extra` | number, list | purchase quantities |
| `order_steps[]` | list | `title`, `where`, `upload` (release paths), `options`, `cost_usd` [low, high], `lead_time_days` [low, high], `receiver`, `source` |
