"""Pocket Beacon assembly: CAD enclosure + KiCad board + CR2032, validated, frozen as assembly_golden.blend.

Build order (enclosure-engineer references/assembly-pipeline.md):
  1. enclosure parts from the CAD GLB (geometry is never edited here)
  2. the board GLB from pcb-engineer, bottom face at the CAD's pcb.z_bottom
  3. the cell (CR2032, Ø20.0 x 3.2 mm, round) in the holder, on the negative pad
  4. validate the whole assembly in its unposed frame, then save

Run (headless, seconds):
  blender -b --factory-startup --python hw/mech/build_assembly.py -- --out hw/mech/assembly_golden.blend
Exit code 0 = valid and saved; 1 = validation failed (the .blend is saved as assembly_failed.blend).
"""
import importlib.util
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)
TOOL = os.path.abspath(os.path.join(HW, "../../../skills/enclosure-engineer/scripts"))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(HERE, "assembly_golden.blend")
S = json.load(open(os.path.join(HERE, "enclosure.json")))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def move_to(o, c):
    for cc in list(o.users_collection):
        cc.objects.unlink(o)
    c.objects.link(o)
    for ch in o.children:
        move_to(ch, c)


def component(name, parent, c):
    e = bpy.data.objects.new(name, None)
    e["hdt_component"] = True
    e.parent = parent
    c.objects.link(e)
    return e


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system, sc.unit_settings.scale_length = 'METRIC', 1.0
root = bpy.data.objects.new("Assembly", None)
sc.collection.objects.link(root)

# 1. enclosure: the CAD GLB is written with 1 glTF unit = 1 mm
enc = coll("Enclosure")
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, "cad", S["name"] + "_assembly.glb"))
cad_root = next(o for o in bpy.context.selected_objects if o.parent is None)
for ch in list(cad_root.children):
    mw = ch.matrix_world.copy()
    e = component("Enclosure " + ch.name, root, enc)
    ch.parent = e
    ch.matrix_world = mw
    move_to(ch, enc)
bpy.data.objects.remove(cad_root)

# 2. board: KiCad GLB in metres, device origin = file origin, board bottom face at z = 0
brd = coll("Board")
bpy.ops.import_scene.gltf(filepath=os.path.join(HW, "pcb", "export", "main.glb"))
node = next(o for o in bpy.context.selected_objects if o.parent is None)
node.name = "Board main"
node.scale = (1000.0, 1000.0, 1000.0)
node.location = (0.0, 0.0, S["pcb"]["z_bottom"])
node.parent = root
move_to(node, brd)
bpy.context.view_layer.update()
pcb = component("PCB main", node, brd)                    # board layers (substrate, copper, mask) = one part
pcb.matrix_parent_inverse = node.matrix_world.inverted()
for ch in list(node.children):
    if ch.type == 'MESH':
        mw = ch.matrix_world.copy()
        ch.parent = pcb
        ch.matrix_world = mw
    elif ch.type == 'EMPTY':
        ch["hdt_component"] = True                         # one footprint = one part
bpy.context.view_layer.update()

# 3. the cell: on the negative pad, centred in the holder (BT1)
bt = S["parts_max"]["BT1"]
pad_z = min((o.matrix_world @ Vector(c)).z for o in pcb.children if o.type == 'MESH' for c in o.bound_box)
r, t = bt["cell_d"] / 2, bt["cell_t"]
bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=r, depth=t, location=(bt["at"][0], bt["at"][1], pad_z - 0.005 - t / 2))
cell = bpy.context.active_object
cell.name = "CR2032 cell"
bev = cell.modifiers.new("edge", 'BEVEL')
bev.width, bev.segments = 0.25, 3
bpy.ops.object.modifier_apply(modifier="edge")
ce = component("BAT1 CR2032", root, coll("Cell"))
cell.parent = ce
move_to(cell, coll("Cell"))
print(f"ASSEMBLY cell top at z {pad_z - 0.005:.3f} mm (negative pad), holder bottom at "
      f"{min((o.matrix_world @ Vector(c)).z for o in bpy.data.objects if o.type == 'MESH' and 'BT1' in (o.parent.name if o.parent else '') for c in o.bound_box):.3f} mm")

sc.unit_settings.scale_length, sc.unit_settings.length_unit = 0.001, 'MILLIMETERS'
bpy.context.view_layer.update()

# 4. validate in the unposed frame, then freeze
va = load("validate_assembly", os.path.join(TOOL, "validate_assembly.py"))
rep = va.validate(root=root, tol=0.02)
os.makedirs(os.path.join(HW, "validation"), exist_ok=True)
jpath, tpath = os.path.join(HW, "validation", "assembly.json"), os.path.join(HW, "validation", "assembly.txt")
json.dump(rep, open(jpath, "w"), indent=1)
txt = va.report_text(rep, "ASSEMBLY VALIDATE")
open(tpath, "w").write(txt + "\n")
print(txt)
ok = rep.get("ok", False)
dest = OUT if ok else os.path.join(HERE, "assembly_failed.blend")
bpy.ops.wm.save_as_mainfile(filepath=dest)
print(f"ASSEMBLY {'VALID' if ok else 'FAILED'}: saved {dest}")
sys.exit(0 if ok else 1)
