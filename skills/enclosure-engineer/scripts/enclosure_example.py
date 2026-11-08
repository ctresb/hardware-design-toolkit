"""Parametric example assembly: rounded shell + flat lid + PCB with components + pouch battery.

It shows the scripted workflow end to end, in millimetres, in a fixed build order:
build fixed parts -> place the movable battery -> free-space fit -> validate -> save (the "golden" file).

Usage (headless, runs in seconds):
    blender -b --factory-startup --python enclosure_example.py -- --out /tmp/hdt_example
    blender -b --factory-startup --python enclosure_example.py -- --out /tmp/hdt_example --collide
`--collide` drops the battery 0.4 mm into the components first, so you can see the fit repair it and
the validator pass afterwards. Without the fit (`--no-fit --collide`) the validator fails, as it should.

Outputs in --out: assembly.blend, validation.json, validation.txt, fit.json.
Exit code: 0 when the final assembly passes validation.
Tested with Blender 5.2.
"""
import argparse
import importlib.util
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- geometry helpers
def rounded_rect(w, d, r, seg=8):
    r = min(r, w / 2 - 1e-3, d / 2 - 1e-3)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180),
                       (w / 2 - r, -d / 2 + r, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def prism(name, w, d, r, z0, z1, bevel_top=0.0, bevel_bottom=0.0, coll=None, parent=None):
    """Rounded-rectangle prism, optionally with rounded top/bottom edges. Closed, manifold."""
    bm = bmesh.new()
    poly = rounded_rect(w, d, r)
    bot = [bm.verts.new((x, y, z0)) for x, y in poly]
    top = [bm.verts.new((x, y, z1)) for x, y in poly]
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    fb = bm.faces.new(list(reversed(bot)))
    ft = bm.faces.new(top)
    bm.normal_update()
    for face, e in ((ft, bevel_top), (fb, bevel_bottom)):
        if e > 0:
            bmesh.ops.bevel(bm, geom=list(face.edges), offset=e, segments=4, profile=0.5, affect='EDGES')
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def apply_difference(target, cutter):
    mod = target.modifiers.new("cut", 'BOOLEAN')
    mod.operation, mod.solver, mod.object = 'DIFFERENCE', 'EXACT', cutter
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
    target.modifiers.clear()
    old = target.data
    target.data = me
    bpy.data.meshes.remove(old)
    bpy.data.objects.remove(cutter)


def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def component(name, loc, coll, root):
    e = bpy.data.objects.new(name, None)
    coll.objects.link(e)
    e.parent = root
    e.location = loc
    e["hdt_component"] = True
    return e


# ---------------------------------------------------------------- build
def build(p, collide=False):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    root = bpy.data.objects.new("Assembly", None)
    bpy.context.scene.collection.objects.link(root)
    shell, boards, cells = collection("Shell"), collection("Boards"), collection("Battery")
    W, D, H, t, r = p["w"], p["d"], p["h"], p["wall"], p["corner"]

    # 1. fixed parts: body (open at the bottom, rounded top edge) and a flat lid under it (face contact)
    body = prism("Body", W, D, r, 0.0, H, bevel_top=p["edge"], coll=shell, parent=root)
    cut = prism("cut", W - 2 * t, D - 2 * t, r - t, -1.0, H - t, coll=shell)
    apply_difference(body, cut)
    body["hdt_component"] = True
    lid = prism("Lid", W, D, r, -p["lid"], 0.0, bevel_bottom=0.4, coll=shell, parent=root)
    lid["hdt_component"] = True

    # PCB on standoffs (standoffs omitted: the board is a fixed part at its nominal height)
    zb = p["standoff"]
    pcb_e = component("PCB", (0, 0, 0), boards, root)
    prism("PCB board", W - 2 * t - 1.0, D - 2 * t - 1.0, r - t - 0.5, zb, zb + p["pcb"], coll=boards, parent=pcb_e)
    ztop = zb + p["pcb"]
    for name, (x, y, w, d, h) in {"U1": (-6, 2, 5, 5, 0.9), "U2": (5, -3, 3, 3, 0.8), "C1": (8, 5, 1.0, 0.5, 0.5),
                                  "J1": (-10, -6, 4, 2, 1.0)}.items():
        e = component(name, (x, y, ztop), boards, root)
        prism(f"{name} body", w, d, 0.05, 0.0, h, coll=boards, parent=e)
        # pins touch the body and the board: same component, never tested against each other
        prism(f"{name} pin", min(w, 0.6), d + 0.3, 0.05, 0.0, 0.2, coll=boards, parent=e)
    comp_top = ztop + 1.0

    # 2. movable part: a pouch cell. Straight edges and a small corner radius: real cells are not blobs.
    bw, bd, bh = p["bat"]
    z0 = comp_top + (-0.4 if collide else 0.3)
    bat = component("Battery cell", (0, 0, 0), cells, root)
    prism("Battery pouch", bw, bd, 1.0, z0, z0 + bh, bevel_top=0.3, bevel_bottom=0.3, coll=cells, parent=bat)
    bpy.context.view_layer.update()
    return root, shell, boards, bat


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="enclosure_example.py", description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--collide", action="store_true", help="start with the battery intersecting the components")
    ap.add_argument("--no-fit", action="store_true", help="skip the free-space fit")
    ap.add_argument("--clearance", type=float, default=0.10, help="battery clearance in mm (swelling allowance)")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    p = dict(w=40.0, d=30.0, h=12.0, wall=1.5, corner=5.0, edge=1.2, lid=1.2, standoff=1.0, pcb=1.0,
             bat=(28.0, 18.0, 4.0))
    va, fs = load("validate_assembly"), load("free_space")
    root, shell, boards, bat = build(p, collide=a.collide)

    fit = {}
    if not a.no_fit:
        fixed = [o for c in (shell, boards) for o in c.all_objects if o.type == 'MESH']
        F = fs.FreeSpace(fixed, h=0.1)
        fit = {"leak": F.leak, "air_volume_mm3": round(F.air_volume, 1),
               "parts": fs.fit_rigid(F, [bat], clearance=a.clearance, lock=(0, 0, 1))}
        with open(os.path.join(a.out, "fit.json"), "w") as f:
            json.dump(fit, f, indent=1)

    rep = va.validate(root=root, tol=0.02, closed_regex=r"(?i)(pouch|board|body)$")
    txt = va.report_text(rep)
    print(txt)
    with open(os.path.join(a.out, "validation.json"), "w") as f:
        json.dump(rep, f, indent=1)
    with open(os.path.join(a.out, "validation.txt"), "w") as f:
        f.write(txt + "\n")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(a.out, "assembly.blend"))
    print(f"EXAMPLE {'PASS' if rep['ok'] else 'FAIL'}: {rep['n_interpenetrations']} interpenetrations; "
          f"fit {fit.get('parts', 'skipped')}; leak {fit.get('leak', 'n/a')}; saved {a.out}/assembly.blend")
    sys.exit(0 if rep["ok"] else 1)


if __name__ == "__main__":
    main()
