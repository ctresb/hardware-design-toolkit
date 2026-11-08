"""Bring the CAD enclosure (GLB from cad_enclosure.py) into a Blender assembly, then validate it.

CAD is the source of truth for enclosure geometry. This script only imports. Never edit the imported
meshes in Blender: change the JSON spec, rebuild with cad_enclosure.py, and import again.

What it does:
1. Sets the scene to millimetres (1 Blender unit = 1 mm; cad_enclosure.py writes 1 glTF unit = 1 mm).
2. Imports the assembly GLB. Each part (Body, Lid, Adhesive, Oring...) becomes a component: an EMPTY
   with `hdt_component = True` under the root `Assembly`, in the collection `Enclosure`.
3. Optionally imports the keep-out GLB into the collection `Keepouts`: wireframe, hidden from renders,
   `hdt_keepout = True`. They stand in for the PCB and the cell until the real models are placed.
4. Optionally runs validate_assembly.py with the keep-outs included, and writes the report.
5. Saves the .blend (keep-outs stay hidden from renders).

Usage:
    blender -b --factory-startup --python import_cad_glb.py -- --glb hw/mech/cad/x_assembly.glb \
        --keepouts hw/mech/cad/x_keepouts.glb --validate hw/validation/enclosure --save hw/mech/assembly.blend
To add parts to an existing assembly, open it instead of --factory-startup and pass --append.

Exit code: 0 = imported (and validated, if asked); 1 = validation failed; 2 = usage or import error.
Tested with Blender 5.2.
"""
import argparse
import importlib.util
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))


def _coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def import_glb(path, coll_name, root, keepout=False):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    coll = _coll(coll_name)
    meshes = [o for o in new if o.type == 'MESH']
    made = []
    bpy.context.view_layer.update()
    for m in meshes:
        mw = m.matrix_world.copy()
        name = m.name.split(".")[0]
        e = bpy.data.objects.new(name + (" keep-out" if keepout else ""), None)
        coll.objects.link(e)
        e.parent = root
        e["hdt_keepout" if keepout else "hdt_component"] = True
        for c in list(m.users_collection):
            c.objects.unlink(m)
        coll.objects.link(m)
        m.parent = e
        m.matrix_world = mw
        if keepout:
            m.display_type = 'WIRE'
            m.hide_render = True
            m["hdt_keepout"] = True
        made.append(m)
    names = [o.name for o in new if o.type == 'EMPTY']
    for n in names:                                # glTF container empties are no longer needed
        o = bpy.data.objects.get(n)
        if o is not None and not o.children:
            bpy.data.objects.remove(o)
    return made


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="import_cad_glb.py", description="Import the CAD enclosure GLB into a Blender assembly.")
    ap.add_argument("--glb", required=True, help="assembly GLB from cad_enclosure.py")
    ap.add_argument("--keepouts", help="keep-out GLB from cad_enclosure.py")
    ap.add_argument("--append", action="store_true", help="keep the objects already in the open file")
    ap.add_argument("--validate", metavar="PREFIX", help="run the validator; write PREFIX.json and PREFIX.txt")
    ap.add_argument("--save", help="save the .blend here")
    a = ap.parse_args(argv)
    if not os.path.exists(a.glb):
        print(f"IMPORT error: not found: {a.glb}")
        sys.exit(2)
    sc = bpy.context.scene
    if not a.append:
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o)
    us = sc.unit_settings
    # the glTF importer converts metres to scene units: import at scale 1 (1 glTF unit = 1 BU = 1 mm),
    # then declare the scene in millimetres
    old_scale = us.scale_length
    us.system, us.scale_length = 'METRIC', 1.0
    root = bpy.data.objects.get("Assembly")
    if root is None:
        root = bpy.data.objects.new("Assembly", None)
        sc.collection.objects.link(root)
    parts = import_glb(a.glb, "Enclosure", root)
    keeps = import_glb(a.keepouts, "Keepouts", root, keepout=True) if a.keepouts else []
    us.scale_length, us.length_unit = 0.001, 'MILLIMETERS'
    if a.append and abs(old_scale - 0.001) > 1e-9:
        print(f"IMPORT warning: the open file had scale_length {old_scale}; it is now 0.001 (mm)")
    bpy.context.view_layer.update()

    def world_size(o):
        from mathutils import Vector
        P = [o.matrix_world @ Vector(c) for c in o.bound_box]
        return [round(max(p[i] for p in P) - min(p[i] for p in P), 2) for i in range(3)]
    dims = {m.name: world_size(m) for m in parts}
    ok = True
    if a.validate:
        spec = importlib.util.spec_from_file_location("validate_assembly", os.path.join(HERE, "validate_assembly.py"))
        va = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(va)
        for k in keeps:
            k.hide_render = False
        rep = va.validate(root=root, tol=0.02)
        for k in keeps:
            k.hide_render = True
        txt = va.report_text(rep)
        print(txt)
        os.makedirs(os.path.dirname(os.path.abspath(a.validate)), exist_ok=True)
        with open(a.validate + ".json", "w") as f:
            json.dump(rep, f, indent=1)
        with open(a.validate + ".txt", "w") as f:
            f.write(txt + "\n")
        ok = rep["ok"]
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save))
    print(f"IMPORT {'PASS' if ok else 'FAIL'}: {len(parts)} parts {dims}, {len(keeps)} keep-outs"
          + (f", saved {a.save}" if a.save else ""))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
