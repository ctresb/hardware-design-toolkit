"""Self-test: builds a fictional test product and a tiny PCB, applies materials, simulates solder and renders
every recipe at thumbnail size. Use it to check a new machine (or a cloud GPU) before real work.

    blender -b --factory-startup --python selftest.py -- /tmp/hdt_selftest [--units mm|m] [--samples 16]

Writes <out>/<recipe>.png, <out>/solder_macro.png, <out>/sheet.png and prints SELFTEST ok/FAIL.
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import materials as MAT  # noqa: E402
import solder as SOL  # noqa: E402
import studio as ST  # noqa: E402


def box(name, size, loc, col, bevel=0.0, parent=None):
    """Axis-aligned box (size and loc in mm), optional bevel modifier."""
    k = MAT.mm(1.0)
    sx, sy, sz = (s * k / 2 for s in size)
    v = [(x, y, z) for z in (-sz, sz) for y in (-sy, sy) for x in (-sx, sx)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.location = tuple(c * k for c in loc)
    if parent:
        ob.parent = parent
    if bevel:
        m = ob.modifiers.new("bevel", "BEVEL")
        m.width = bevel * k
        m.segments = 6
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return ob


def build(units, wear_textures=None):
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 0.001 if units == "mm" else 1.0
    MAT.configure(None, wear_textures)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    col = bpy.data.collections.new("Test product")
    sc.collection.children.link(col)
    # a 40 × 40 × 12 mm puck: clear top shell over a black base, front facing -Y
    base = box("Base", (40, 40, 6), (0, 0, 3), col, bevel=2.0)
    top = box("Shell", (40, 40, 6), (0, 0, 9.05), col, bevel=2.5)
    MAT.assign(base, MAT.get("plastic_black", wear=0.5))
    MAT.assign(top, MAT.get("plastic_clear", wear=0.6))
    led = box("LED lens", (1.6, 0.8, 0.6), (0, -12, 6.4), col)
    MAT.assign(led, MAT.get("led_lens"))
    # a tiny PCB, separate collection, with a 0402 capacitor and a 3 × 3 mm QFN
    pcb_col = bpy.data.collections.new("Test board")
    sc.collection.children.link(pcb_col)
    pcb = box("Test PCB", (10, 8, 0.6), (60, 0, -0.3), pcb_col)
    MAT.assign(pcb, MAT.get("solder_mask", color=(0.01, 0.01, 0.012)))
    comps = {}
    for ref, at, body, kind in (("C1", (57.5, 0, 0), (1.0, 0.5, 0.5), "mlcc"), ("U1", (61.5, 0, 0), (3.0, 3.0, 0.75), "ic_epoxy")):
        e = bpy.data.objects.new(ref, None)
        pcb_col.objects.link(e)
        e.location = tuple(c * MAT.mm(1) for c in at)
        b = box(f"{ref} body", body, (0, 0, body[2] / 2), pcb_col, parent=e)
        MAT.assign(b, MAT.get(kind))
        if ref == "C1":
            for sx in (-1, 1):
                t = box(f"{ref} term {sx}", (0.2, 0.5, 0.5), (sx * 0.4, 0, 0.25), pcb_col, parent=e)
                MAT.assign(t, MAT.get("tin"))
        comps[ref] = e
    pads = {"C1": {"layer": "F.Cu", "x": 0, "y": 0, "rot": 0, "pads": [
        {"n": str(i + 1), "shape": "roundrect", "x": sx * 0.48, "y": 0.0, "a": 0.0, "w": 0.56, "h": 0.62, "paste": True, "cu": True}
        for i, sx in enumerate((-1, 1))]}}
    qfn = []
    for side in range(4):
        for k in range(4):
            off = -0.75 + k * 0.5
            x, y, w, h = ((-1.45, off, 0.7, 0.25), (off, 1.45, 0.25, 0.7), (1.45, -off, 0.7, 0.25), (-off, -1.45, 0.25, 0.7))[side]
            qfn.append({"n": str(side * 4 + k + 1), "shape": "roundrect", "x": x, "y": y, "a": 0.0, "w": w, "h": h, "paste": True, "cu": True})
    qfn.append({"n": "17", "shape": "rect", "x": 0, "y": 0, "a": 0, "w": 1.6, "h": 1.6, "paste": False, "cu": True})
    for i in range(4):
        qfn.append({"n": "", "shape": "rect", "x": (i % 2 - 0.5) * 0.8, "y": (i // 2 - 0.5) * 0.8, "a": 0, "w": 0.6, "h": 0.6, "paste": True, "cu": False})
    pads["U1"] = {"layer": "F.Cu", "x": 0, "y": 0, "rot": 0, "pads": qfn}
    return col, pcb_col, {"test": pads}


def main(argv):
    ap = argparse.ArgumentParser(prog="selftest.py")
    ap.add_argument("out")
    ap.add_argument("--units", choices=["mm", "m"], default="mm")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--format", default="tiny", help="studio format (tiny = 240×320)")
    ap.add_argument("--hdri", help="optional studio HDRI for the tabletop recipe")
    ap.add_argument("--wear-textures", help="optional ambientCG wear folder (see materials.py)")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    col, pcb_col, pads = build(a.units, a.wear_textures)
    pj = os.path.join(a.out, "pads.json")
    json.dump(pads, open(pj, "w"))
    made, comps, _ = SOL.solder_all(pj, {"test": pcb_col}, "PCB")
    print(f"SELFTEST solder: {made} fillets on {comps} components")
    ok = made >= 10
    shots = []
    for rec, view in (("dark-studio", "hero"), ("tabletop-hdri", "three-quarter"), ("white-seamless", "hero"), ("hero-float", "front")):
        out = os.path.join(a.out, f"{rec}.png")
        rc = ST.main(["--target", "Test product", "--recipe", rec, "--view", view, "--format", a.format, "--preset", "tiny",
                      "--samples", str(a.samples), "--allow-unvalidated", "--out", out]
                     + (["--emit", "LED lens=1,0.86,0.7:40"] if rec == "dark-studio" else [])
                     + (["--floor", "gloss"] if rec == "hero-float" else [])
                     + (["--hdri", a.hdri] if rec == "tabletop-hdri" and a.hdri else []))
        ok &= rc == 0 and os.path.exists(out)
        shots.append(out)
    out = os.path.join(a.out, "solder_macro.png")
    rc = ST.main(["--target", "Test board", "--recipe", "dark-studio", "--view", "macro", "--format", a.format, "--preset", "tiny",
                  "--samples", str(a.samples), "--fstop", "11", "--fill", "0.8", "--allow-unvalidated", "--out", out])
    ok &= rc == 0
    shots.append(out)
    # gate must refuse without a report
    ok &= ST.gate(None, False) is False
    import contact_sheet
    contact_sheet.main([os.path.join(a.out, "sheet.png"), *shots, "--height", "320", "--cols", "5"])
    print("SELFTEST", "ok" if ok else "FAIL", a.out)
    return 0 if ok else 1


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    rc = main(argv)
    if bpy.app.background:
        sys.exit(rc)
