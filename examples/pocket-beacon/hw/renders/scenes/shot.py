"""Pocket Beacon shot driver (runs on the GPU host).

Loads the validated golden assembly, adds solder, assigns the per-variant look, poses the assembly rigidly
(or explodes it / duplicates it for a lineup), re-validates the posed scene in memory, then hands over to
product-render's studio.py. Options come from the HDT_SHOT environment variable (JSON); studio.py's own
arguments follow "--" on the command line.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

SCRIPTS = os.environ["HDT_SCRIPTS"]
VSCRIPTS = os.environ["HDT_VALIDATOR"]
sys.path.insert(0, SCRIPTS)
sys.path.insert(0, VSCRIPTS)
import materials as M  # noqa: E402
import solder as SO  # noqa: E402
import studio as S  # noqa: E402
import validate_assembly as VA  # noqa: E402

cfg = json.loads(os.environ.get("HDT_SHOT", "{}"))
M.configure(1.0, os.environ.get("HDT_TEX"))          # scene is in mm: 1 BU = 1 mm
ROOT = bpy.data.objects["Assembly"]

# ------------------------------------------------------------------ probe (find the keyring slot)
if cfg.get("probe"):
    dg = bpy.context.evaluated_depsgraph_get()
    shell = bpy.data.objects["shell"]
    plate = bpy.data.objects["plate"]
    holes = []
    for ix in range(0, 41):
        for iy in range(0, 41):
            x, y = -16 + ix * 0.8, -16 + iy * 0.8
            o = Vector((x, y, 30))
            hit, loc, n, i, ob, mtx = bpy.context.scene.ray_cast(dg, o, Vector((0, 0, -1)))
            # inside the outline but nothing hit at all -> through hole
            r = max(abs(x), abs(y))
            if not hit and r < 15.2:
                holes.append((round(x, 1), round(y, 1)))
    print("PROBE through-holes along Z:", holes)
    for side, d in (("+X", Vector((-1, 0, 0))), ("+Y", Vector((0, -1, 0)))):
        pass
    sys.exit(0)

# ------------------------------------------------------------------ solder (in memory, last geometry step)
if cfg.get("solder", True):
    n, comps, _ = SO.solder_all(os.environ["HDT_PADS"], {"main": bpy.data.collections["Board"]},
                                board_mesh="=>[0:1:1:36]")
    print(f"SHOT solder: {n} fillets on {comps} parts")

# ------------------------------------------------------------------ looks
VARIANTS = {
    "graphite": dict(kind="plastic_black", color=(0.034, 0.035, 0.038), button=(0.11, 0.11, 0.115)),
    "chalk": dict(kind="plastic_white", color=(0.80, 0.79, 0.76), button=(0.86, 0.85, 0.81)),
    "smoke": dict(kind="plastic_clear", color=(0.80, 0.80, 0.82), button=(0.14, 0.14, 0.15)),
}
BOARD_MATS = {   # KiCad GLB material -> material kind
    "mat_0": "tin", "mat_6": "tin", "mat_7": "tin", "mat_10": "tin",
    "mat_1": "mlcc", "mat_2": "ic_epoxy", "mat_5": "ic_epoxy", "mat_13": "ic_epoxy",
    "mat_3": "nickel", "mat_11": "nickel", "mat_4": "gold", "mat_14": "gold",
    "mat_8": "ferrite", "mat_9": "alumina", "mat_12": "resistor_film", "mat_15": "led_lens",
    "mat_16": "enig", "mat_20": "fr4_edge",
}


def smoke_volume(m, density_per_mm=0.22, color=(0.50, 0.50, 0.53)):
    """Turn the clear-PC absorption into a smoke-grey tint (translucent dark grey resin)."""
    for nd in m.node_tree.nodes:
        if nd.type == "VOLUME_ABSORPTION":
            nd.inputs["Color"].default_value = (*color, 1)
            nd.inputs["Density"].default_value = density_per_mm
    return m


def tpu(color, name):
    """Translucent TPU 80A button membrane (frosted): the LED shines through it."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.85 if cfg.get("led") else cfg.get("tpu_rough", 0.38)
    b.inputs["Sheen Weight"].default_value = 0.0 if cfg.get("led") else 0.35
    b.inputs["Coat Weight"].default_value = 0.0 if cfg.get("led") else 0.25
    b.inputs["Coat Roughness"].default_value = 0.3
    b.inputs["IOR"].default_value = 1.5
    lit = bool(cfg.get("led"))
    b.inputs["Transmission Weight"].default_value = cfg.get("tpu_transmission", 0.35 if lit else 0.12)
    b.inputs["Subsurface Weight"].default_value = 1.0
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.8, 0.6)
    b.inputs["Subsurface Scale"].default_value = cfg.get("tpu_sss", 0.8 if lit else 0.12)
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Density"].default_value = cfg.get("tpu_scatter", 6.0) if lit else 0.8
    sc.inputs["Color"].default_value = (*[min(1, 0.6 + c) for c in color], 1)
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
    ab.inputs["Density"].default_value = cfg.get("tpu_absorb", 0.9) if lit else 0.25
    ab.inputs["Color"].default_value = (*([min(1, 0.35 + c) for c in color] if lit else [max(0.05, c) for c in color]), 1)
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(sc.outputs[0], add.inputs[0])
    nt.links.new(ab.outputs[0], add.inputs[1])
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    nt.links.new(add.outputs[0], out.inputs["Volume"])
    # soft-touch micro texture
    tx = nt.nodes.new("ShaderNodeTexNoise")
    tx.inputs["Scale"].default_value = 30.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    bump.inputs["Distance"].default_value = 0.004
    nt.links.new(tx.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def look(objs, variant, tag=""):
    v = VARIANTS[variant]
    wear = cfg.get("wear", 0.45)
    if v["kind"] == "plastic_clear":
        housing = smoke_volume(M.get("plastic_clear", color=v["color"], wear=wear, name=f"Smoke PC{tag}"))
    else:
        housing = M.get(v["kind"], color=v["color"], wear=wear, name=f"{variant} housing{tag}")
    button = tpu(v["button"], f"{variant} TPU{tag}")
    mask = M.get("solder_mask", color=(0.010, 0.010, 0.012))
    silk = M.get("plastic_color", color=(0.86, 0.86, 0.84), roughness=0.7, name="Silkscreen ink")
    cache = {}
    for o in objs:
        if o.type != "MESH":
            continue
        base = o.name.split(" #")[0].split(".")[0]
        if base in ("shell", "plate", "door"):
            M.assign(o, housing)
        elif base == "button":
            M.assign(o, button)
        elif base in ("door_gasket", "port_gasket", "adhesive"):
            M.assign(o, M.get("rubber"))
        elif base == "membrane":
            M.assign(o, M.get("fabric", color=(0.02, 0.02, 0.022)))
        elif base == "screws":
            M.assign(o, M.get("stainless", wear=0.3))
        elif base == "CR2032 cell":
            M.assign(o, M.get("stainless", wear=0.2, roughness=0.14))
        else:
            for sl in o.material_slots:
                src = sl.material.name.split(".")[0] if sl.material else ""
                if src in ("mat_18", "mat_19"):
                    m = mask
                elif src == "mat_17":
                    m = silk
                elif src in BOARD_MATS:
                    k = BOARD_MATS[src]
                    m = cache.get(k) or cache.setdefault(k, M.get(k))
                else:
                    continue
                sl.link = "OBJECT"
                sl.material = m


def tree(root):
    return [root] + list(root.children_recursive)


def led_on(root, strength):
    """Amber LED on: emission on the lens only, plus a small point light just in front of it."""
    d1 = next(o for o in root.children_recursive if o.name.split(".")[0] == "D1" and o.type == "EMPTY")
    lens = [c for c in d1.children_recursive if c.type == "MESH"]
    em = M.emissive("LED amber on", (1.0, 0.52, 0.12), strength)
    for o in lens:
        for sl in o.material_slots:
            if sl.material and "lens" in sl.material.name.lower():
                sl.link = "OBJECT"
                sl.material = em
    bpy.context.view_layer.update()
    R = d1.matrix_world.to_quaternion().to_matrix()        # rotation only: the KiCad GLB parents carry a 1000x scale
    pos = d1.matrix_world.translation + R @ Vector((0, 0, cfg.get("led_bead_z", 1.5)))
    # studio.py hides every light it did not make, so the glow is a tiny emissive bead (a mesh, not a light)
    me = bpy.data.meshes.new("LED glow")
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.25)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("LED glow", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = pos
    ob.visible_shadow = False
    ob.visible_camera = False            # seen only as light diffused by the membrane, never as a bead
    ob.visible_transmission = False
    ob.visible_glossy = False
    bpy.context.view_layer.update()
    M.assign(ob, M.emissive("LED glow bead", (1.0, 0.42, 0.06), cfg.get("led_light", 400.0)))
    print("SHOT LED on:", [(o.name, [sl.material.name for sl in o.material_slots if sl.material]) for o in lens],
          "bead at", tuple(round(x, 2) for x in ob.matrix_world.translation))


def duplicate(root, suffix):
    """Rigid copy of the whole assembly (meshes shared, materials object-linked)."""
    mapping = {}
    for o in tree(root):
        c = o.copy()
        c.name = o.name + suffix
        for col in o.users_collection:
            col.objects.link(c)
        mapping[o] = c
    for o, c in mapping.items():
        if o.parent in mapping:
            c.parent = mapping[o.parent]
            c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
    return mapping[root]


# keyring split ring: flat stainless wire, 2 turns, through the corner slot
def split_ring(center, axis_dir, radius=7.5, wire=(1.5, 0.45), turns=2.0, name="Split ring"):
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    N = int(220 * turns)
    pitch = wire[1] * 1.05
    w, t = wire
    rings = []
    for i in range(N + 1):
        a = 2 * math.pi * turns * i / N
        r = radius
        c = Vector((r * math.cos(a), r * math.sin(a), pitch * a / (2 * math.pi)))
        radial = Vector((math.cos(a), math.sin(a), 0))
        up = Vector((0, 0, 1))
        # flat wire: width along the radial direction, thickness along the ring axis, rounded edges
        prof = []
        for k in range(12):
            th = 2 * math.pi * k / 12
            prof.append(c + radial * (w / 2) * math.cos(th) * 1.0 + up * (t / 2) * math.sin(th))
        rings.append([bm.verts.new(p) for p in prof])
    for i in range(N):
        for k in range(12):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % 12], rings[i + 1][(k + 1) % 12], rings[i + 1][k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    q = Vector((0, 0, 1)).rotation_difference(axis_dir.normalized())
    ob.matrix_world = Matrix.Translation(center) @ q.to_matrix().to_4x4()
    M.assign(ob, M.get("stainless", wear=0.35, roughness=0.18))
    return ob


# ------------------------------------------------------------------ build the shot
pose = cfg.get("pose", "upright")
variants = cfg.get("variants", ["graphite"])
look(tree(ROOT), variants[0])
roots = [ROOT]

if pose == "explode":
    # stack along the product axis (Z = back -> front), greedy so no two layers overlap
    layers = cfg["layers"]
    gap = cfg.get("gap", 3.0)
    bpy.context.view_layer.update()
    z_top = None
    for names in layers:
        objs = []
        for n in names:
            o = bpy.data.objects[n]
            objs += [x for x in tree(o) if x.type == "MESH"]
        lo, hi = S.bbox(objs)
        dz = 0.0 if z_top is None else (z_top + gap) - lo.z
        c = (lo + hi) / 2
        dx, dy = (-c.x, -c.y) if cfg.get("center_layers") else (0.0, 0.0)
        tops = [bpy.data.objects[n] for n in names]
        for t in tops:
            t.matrix_world = Matrix.Translation((dx, dy, dz)) @ t.matrix_world
        bpy.context.view_layer.update()
        z_top = hi.z + dz
elif pose == "lineup":
    for i, v in enumerate(variants[1:], 1):
        r2 = duplicate(ROOT, f" #{i}")
        look(tree(r2), v, tag=f" #{i}")
        roots.append(r2)

# rigid pose of each assembly copy (validated in the frozen frame first, see below)
for i, r in enumerate(roots):
    rx = math.radians(cfg.get("rx", 90 if pose in ("upright", "lineup") else 0))
    rz = math.radians(cfg.get("rz", 0))
    off = Vector(cfg.get("spacing", [0, 0, 0])) * (i - (len(roots) - 1) / 2)
    r.matrix_world = Matrix.Translation(off) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(rx, 4, "X")
bpy.context.view_layer.update()

if cfg.get("ring"):
    rc = cfg["ring"]
    split_ring(Vector(rc["center"]), Vector(rc["axis"]), rc.get("radius", 7.5))


if cfg.get("spare_cell"):
    src = bpy.data.objects["CR2032 cell"]
    bpy.context.view_layer.update()
    for i, xy in enumerate(cfg["spare_cell"]):
        c = src.copy()
        c.name = f"Spare CR2032 {i}"
        bpy.context.scene.collection.objects.link(c)
        c.parent = None
        lo, hi = S.bbox([src])
        mid = (lo + hi) / 2
        # lying flat on the table (z = 0 is the table under the product), at xy
        c.matrix_world = Matrix.Translation((xy[0] - mid.x, xy[1] - mid.y, -lo.z + (xy[2] if len(xy) > 2 else 0))) @ src.matrix_world
        if len(xy) > 3:   # flip it (show the + face) by rotating about its own centre
            ctr = Vector((xy[0], xy[1], (hi.z - lo.z) / 2))
            c.matrix_world = Matrix.Translation(ctr) @ Matrix.Rotation(math.radians(xy[3]), 4, "X") @ Matrix.Translation(-ctr) @ c.matrix_world

# in-memory re-validation of the posed scene (solder + pose + explode); refuse on any failure
reps = [VA.validate(root=r, tol=0.02) for r in roots]          # each copy in its frozen (unposed) frame
if cfg.get("ring") or cfg.get("spare_cell"):
    reps.append(VA.validate(root=None, tol=0.02, unpose_root=False))                # whole scene as posed: ring vs housing
for rep in reps:
    VA.print_report(rep, "SHOT VALIDATE")
if not all(r.get("ok") for r in reps):
    print("SHOT refused: posed scene fails validation")
    sys.exit(3)

if cfg.get("led"):
    led_on(ROOT, cfg.get("led_strength", 25.0))
for n in cfg.get("hide", []):
    for o in tree(bpy.data.objects[n]):
        o.hide_render = True

# camera shift (subject off-centre, e.g. banner) without touching studio.py
if cfg.get("shift_x") or cfg.get("shift_y"):
    _cam = S.camera

    def camera(*a, **k):
        cam, dist = _cam(*a, **k)
        cam.data.shift_x = cfg.get("shift_x", 0.0)
        cam.data.shift_y = cfg.get("shift_y", 0.0)
        return cam, dist
    S.camera = camera
if cfg.get("extra_lights"):
    _rec = S.recipe

    def recipe(name, col, center, size, cam_az, args):
        out = _rec(name, col, center, size, cam_az, args)
        for nm, az, el, dk, sw, sh, pk in cfg["extra_lights"]:
            S.area_light(col, nm, center, cam_az + az, el, dk * size, (sw * size, sh * size), pk)
        return out
    S.recipe = recipe
if "formats" in cfg:
    for k, v in cfg["formats"].items():
        S.FORMATS[k] = tuple(v)

argv = sys.argv[sys.argv.index("--") + 1:]
rc = S.main(argv)
sys.exit(rc)
