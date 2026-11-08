"""Builds a small fictional assembly (sensor puck) to test the drawing scripts.

usage: blender -b --python make_test_scene.py -- out/test_assembly.blend

Hierarchy (millimetres, scene unit scale 0.001):
  Device (empty)
    Shell, Window            top cover and its light window
    Board (collection "Main board"): PCB, U1/U2/C1..C4/J1 (empties with meshes), Solder (skipped)
    Battery, Battery label
    Lid, Magnet x2, Contact +
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "test_assembly.blend"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 0.001
sc.unit_settings.length_unit = 'MILLIMETERS'
col = sc.collection
board_col = bpy.data.collections.new("Main board")
col.children.link(board_col)


def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    col.objects.link(e)
    e.parent = parent
    e.location = loc
    return e


def box(name, size, loc, parent, bevel=0.0, coll=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        m = o.modifiers.new("bevel", 'BEVEL')
        m.width = bevel
        m.segments = 4
    for c in o.users_collection:
        c.objects.unlink(o)
    (coll or col).objects.link(o)
    o.parent = parent
    return o


def cyl(name, r, h, loc, parent, coll=None, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    for c in o.users_collection:
        c.objects.unlink(o)
    (coll or col).objects.link(o)
    o.parent = parent
    return o


dev = empty("Device")
# top cover: a bevelled block minus an inner pocket (hollow shell), with a round window
shell = box("Shell", (40, 28, 9), (0, 0, 4.5), dev, bevel=2.5)
cut = box("cut", (37, 25, 8), (0, 0, 3.5), None)
b = shell.modifiers.new("hollow", 'BOOLEAN')
b.object = cut
b.operation = 'DIFFERENCE'
cut.hide_render = True
cut.hide_viewport = True
cyl("Window", 3.0, 1.2, (10, 0, 8.6), dev)
# board with parts (each part = empty + mesh, like an imported PCB)
assy = empty("Board assy", dev)       # all parents sit at the origin, so world = local
box("PCB", (34, 22, 0.8), (0, 0, 1.6), assy, coll=board_col)
parts = {"U1": ((6, 6, 0.9), (-6, 2, 2.45)), "U2": ((4, 3, 0.8), (6, -4, 2.4)),
         "C1": ((1.0, 0.5, 0.5), (2, 5, 2.25)), "C2": ((1.0, 0.5, 0.5), (3.5, 5, 2.25)),
         "C3": ((1.0, 0.5, 0.5), (5, 5, 2.25)), "C4": ((1.0, 0.5, 0.5), (6.5, 5, 2.25)),
         "J1": ((8, 3, 1.5), (-8, -7, 2.75))}
for ref, (s, p) in parts.items():
    e = empty(ref, assy)
    board_col.objects.link(e)
    box(f"{ref} body", s, p, e, coll=board_col)
box("Solder joints", (30, 0.2, 0.05), (0, 0, 2.03), assy, coll=board_col)
# battery below the board
box("Battery", (30, 18, 4), (0, 0, -1.2), dev, bevel=0.4)
box("Battery label", (20, 12, 0.05), (0, 0, -3.22), dev)
# lid with magnets and a charge contact
box("Lid", (37, 25, 1.4), (0, 0, -4.0), dev, bevel=0.5)
cyl("Magnet", 1.5, 1.0, (-12, 0, -3.0), dev)
cyl("Magnet.001", 1.5, 1.0, (12, 0, -3.0), dev)
cyl("Contact +", 2.0, 0.6, (0, 0, -4.9), dev)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT))
print("TEST SCENE saved", OUT)
