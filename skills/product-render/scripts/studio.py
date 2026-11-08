"""Product photo studio for Blender Cycles: lighting recipe + physical camera + render settings + gate.

    blender -b product.blend --python studio.py -- \
        --target "Product" --recipe dark-studio --view hero --format 4k-vertical --preset final \
        --validator-json hw/validation/assembly.json --out hw/renders/hero_dark.png

Conventions:
  - The product's FRONT faces -Y and its top faces +Z (Blender's front view). Views are azimuth/elevation
    around the target: az 0 = camera on -Y looking at the front; positive az moves the camera to +X.
  - All distances scale with the target's size, so the same recipe works for a 20 mm tag or a 300 mm speaker,
    in a scene built in metres or in millimetres. Light power scales with distance², so exposure stays put.
  - Lights are invisible to the camera. Only the backdrop (or the world colour) is seen behind the product.

Gate: the render is refused unless --validator-json points to a passing report of the geometry validator
({"ok": true, ...}) that is newer than the .blend, or you pass --allow-unvalidated (scenes that are not an
assembly, e.g. material tests). The reason: an interpenetration found by the viewer costs trust.

Recipes:
  dark-studio     near-black world, one large soft key at one side, two thin strip lights behind that draw
                  the silhouette, a weak top light. AgX Base Contrast. Best default for dark and clear products.
  tabletop-hdri   the product on a matte surface, lit and reflected by a studio HDRI (pass --hdri), with one
                  soft key for the shadow. Khronos PBR Neutral keeps colours true. "On the desk" shots.
  white-seamless  curved seamless backdrop, large overhead softbox and side fills. Catalog shots.
                  Warning: white products on white go flat; use a dark product or a darker backdrop.
  hero-float      the product floating over a dark graphite wall lit by a soft gradient, key + rim strips,
                  optional glossy floor (--floor gloss). Landing-page hero.
"""
import argparse
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import materials as MAT  # noqa: E402

FORMATS = {
    "4k-vertical": (2160, 3840), "4k-horizontal": (3840, 2160), "4k-square": (3840, 3840),
    "2k-vertical": (1440, 2560), "2k-horizontal": (2560, 1440), "square-2k": (2400, 2400),
    "portrait-4x5": (2400, 3000), "preview": (480, 640), "preview-h": (640, 480), "tiny": (240, 320),
}
PRESETS = {  # samples, denoise, adaptive threshold
    "tiny": (16, True, 0.1), "preview": (64, True, 0.05), "final": (512, True, 0.01), "hero": (1024, True, 0.005),
}
VIEWS = {  # azimuth, elevation (degrees)
    "front": (0, 4), "hero": (-24, 14), "three-quarter": (-38, 22), "three-quarter-right": (38, 22),
    "side": (-90, 6), "top": (0, 88), "low": (-20, -6), "back": (180, 14), "macro": (-30, 30),
}


# ---------------------------------------------------------------- scene helpers

KEEP_LIGHT = "hdt_keep_light"     # custom property: a shot-level light (LED glow, practical) that studio.py keeps


def world_offset(obj, local_vec):
    """Offset expressed in the object's local axes but in world units. Use it for anything placed relative to a
    part: KiCad/GLB component empties often carry a 1000x scale (metre files in a millimetre scene), so
    `obj.matrix_world @ v` puts the point metres away. Rotation only, never the scale."""
    return obj.matrix_world.translation + (obj.matrix_world.to_quaternion() @ Vector(local_vec))

def collect(target):
    """Objects of the target: a collection name, an object (with its children) or a glob."""
    import fnmatch
    if target in bpy.data.collections:
        objs = list(bpy.data.collections[target].all_objects)
    elif target in bpy.data.objects:
        o = bpy.data.objects[target]
        objs = [o] + list(o.children_recursive)
    else:
        cols = [c for c in bpy.data.collections if fnmatch.fnmatchcase(c.name, target)]
        objs = [o for c in cols for o in c.all_objects]
        hits = [o for o in bpy.data.objects if fnmatch.fnmatchcase(o.name, target)]
        for o in hits:                                    # a glob that matches empties takes their children
            objs += [o] + list(o.children_recursive)
    objs = list(dict.fromkeys(o for o in objs if o.type in ("MESH", "CURVE", "FONT", "SURFACE") and not o.hide_render))
    if not objs:
        raise SystemExit(f"STUDIO error: target '{target}' has no renderable objects")
    return objs


def bbox(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def link(ob, col):
    col.objects.link(ob)
    return ob


def studio_collection():
    col = bpy.data.collections.get("VH Studio")
    if col:
        for o in list(col.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        col = bpy.data.collections.new("VH Studio")
        bpy.context.scene.collection.children.link(col)
    return col


def direction(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def area_light(col, name, center, az, el, dist, size, power_k, color=(1, 1, 1), shape="RECTANGLE"):
    """Area light aimed at center. power_k × dist² keeps irradiance independent of units and scale."""
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = shape
    ld.size, ld.size_y = size
    ld.energy = power_k * dist * dist
    ld.color = color
    ob = link(bpy.data.objects.new(name, ld), col)
    ob.location = center + direction(az, el) * dist
    ob.rotation_euler = (center - ob.location).to_track_quat("-Z", "Y").to_euler()
    ob.visible_camera = False
    return ob


def world(color=(0.012, 0.012, 0.013), strength=1.0, hdri=None, hdri_strength=0.6, hdri_rot=0.0, camera_bg=None):
    """World: flat colour, or an HDRI for lighting/reflections while the camera sees camera_bg (if given)."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new("VH World")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputWorld")
    bg = N.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength
    if hdri:
        tc = N.new("ShaderNodeTexCoord")
        mp = N.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0, 0, math.radians(hdri_rot))
        env = N.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(hdri, check_existing=True)
        L.new(tc.outputs["Generated"], mp.inputs["Vector"])
        L.new(mp.outputs[0], env.inputs["Vector"])
        L.new(env.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = hdri_strength
    if camera_bg is not None:
        cam_bg = N.new("ShaderNodeBackground")
        cam_bg.inputs["Color"].default_value = (*camera_bg, 1)
        lp = N.new("ShaderNodeLightPath")
        mix = N.new("ShaderNodeMixShader")
        L.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
        L.new(bg.outputs[0], mix.inputs[1])
        L.new(cam_bg.outputs[0], mix.inputs[2])
        L.new(mix.outputs[0], out.inputs["Surface"])
    else:
        L.new(bg.outputs[0], out.inputs["Surface"])
    return w


def plane(col, name, center, size, mat, z):
    me = bpy.data.meshes.new(name)
    s = size
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    ob = link(bpy.data.objects.new(name, me), col)
    ob.location = (center.x, center.y, z)
    me.materials.append(mat)
    return ob


def cyclorama(col, name, center, S, mat, z, az=0.0, radius_k=3.0, depth_k=6.0, height_k=10.0, width_k=14.0):
    """Seamless backdrop: floor that curves up into a wall behind the product (no horizon line),
    turned so the wall stays behind the product as seen from azimuth az."""
    r, d, h, w = radius_k * S, depth_k * S, height_k * S, width_k * S
    prof = [(-d, 0.0)]
    for i in range(13):                                   # quarter circle from floor to wall, behind (+Y)
        a = math.radians(90 * i / 12)
        prof.append((d - r + r * math.sin(a), r - r * math.cos(a)))
    prof.append((d, h))
    verts, faces = [], []
    for x in (-w, w):
        for y, zz in prof:
            verts.append((x, y, zz))
    n = len(prof)
    for i in range(n - 1):
        faces.append((i, i + 1, n + i + 1, n + i))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.polygons.foreach_set("use_smooth", [True] * len(faces))
    ob = link(bpy.data.objects.new(name, me), col)
    ob.location = (center.x, center.y, z)
    ob.rotation_euler = (0, 0, math.radians(az))
    me.materials.append(mat)
    return ob


def camera(col, center, S, az, el, lens=100.0, fstop=5.6, fill=0.6, res=(2160, 3840), focus=None, objs=None):
    """Physical camera: full-frame 36 mm along the image's long side (sensor_fit follows orientation),
    distance chosen so the product fills `fill` of the short side, focus on the visible front surface."""
    cd = bpy.data.cameras.new("VH Camera")
    cd.lens = lens
    vertical = res[1] > res[0]
    cd.sensor_fit = "VERTICAL" if vertical else "HORIZONTAL"
    cd.sensor_width = 36.0
    cd.sensor_height = 36.0 if vertical else 24.0          # a vertical frame keeps the 36 mm long side
    short_mm = 36.0 * min(res) / max(res)
    half = math.atan(short_mm / 2 / lens)
    dist = (S / fill) / 2 / math.tan(half)
    cd.clip_start = dist * 0.01
    cd.clip_end = dist * 50
    cam = link(bpy.data.objects.new("VH Camera", cd), col)
    cam.location = center + direction(az, el) * dist
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()   # camera Y = up, no roll
    foc = link(bpy.data.objects.new("VH Camera focus", None), col)
    foc.location = center
    if focus and focus in bpy.data.objects:
        foc.location = bpy.data.objects[focus].matrix_world.translation
    elif objs:                                               # focus on the first surface the camera sees
        dg = bpy.context.evaluated_depsgraph_get()
        hit, loc, *_ = bpy.context.scene.ray_cast(dg, cam.location, (center - cam.location).normalized())
        if hit:
            foc.location = loc
    cd.dof.use_dof = True
    cd.dof.focus_object = foc
    cd.dof.aperture_fstop = fstop
    cd.dof.aperture_blades = 9
    cd.dof.aperture_rotation = math.radians(10)
    bpy.context.scene.camera = cam
    return cam, dist


def use_gpu():
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            devs = [d for d in prefs.devices if d.type == kind]
            if devs:
                for d in prefs.devices:
                    d.use = d.type == kind
                bpy.context.scene.cycles.device = "GPU"
                return f"{kind} ×{len(devs)}"
        except Exception:
            continue
    bpy.context.scene.cycles.device = "CPU"
    return "CPU"


def render_settings(preset, res, view_transform="AgX", look="AgX - Base Contrast", exposure=0.0, transparent=False):
    sc = bpy.context.scene
    spp, den, thr = PRESETS[preset]
    sc.render.engine = "CYCLES"
    sc.cycles.samples = spp
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = thr
    sc.cycles.use_denoising = den
    sc.cycles.max_bounces = 24
    sc.cycles.diffuse_bounces = 6
    sc.cycles.glossy_bounces = 12
    sc.cycles.transmission_bounces = 24                    # clear plastic needs many
    sc.cycles.volume_bounces = 2
    sc.cycles.transparent_max_bounces = 16
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 0.5
    sc.cycles.sample_clamp_indirect = 4.0
    sc.render.use_persistent_data = False                  # persistent data caused flicker in animations
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    try:
        sc.view_settings.view_transform = view_transform
    except TypeError:
        sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = look or "None"
    except TypeError:
        pass
    sc.view_settings.exposure = exposure
    st = sc.render.image_settings
    if hasattr(st, "media_type"):
        try:
            st.media_type = "IMAGE"
        except Exception:
            pass
    st.file_format = "PNG"
    st.color_mode = "RGBA" if transparent else "RGB"
    st.color_depth = "16"


# ---------------------------------------------------------------- recipes

def recipe(name, col, center, S, cam_az, args):
    """Builds lights/world/backdrop. Positions are multiples of S (the product's largest dimension)."""
    z0 = center.z - args.half_height
    if name == "dark-studio":
        world((0.012, 0.012, 0.013), 1.0)
        area_light(col, "Key softbox", center, cam_az - 38, 26, 9 * S, (5 * S, 9.3 * S), 8.0, (1.0, 0.985, 0.96))
        area_light(col, "Strip left", center, cam_az - 133, 25, 6.2 * S, (0.33 * S, 10.7 * S), 8.6, (0.92, 0.96, 1.0))
        area_light(col, "Strip right", center, cam_az + 131, 23, 5.7 * S, (0.33 * S, 10.7 * S), 8.0, (1.0, 0.96, 0.92))
        area_light(col, "Top weak", center, cam_az, 81, 8.8 * S, (4 * S, 4 * S), 0.43)
        return ("AgX", "AgX - Base Contrast")
    if name == "tabletop-hdri":
        if not args.hdri:
            print("STUDIO warning: tabletop-hdri without --hdri; using a neutral grey world (reflections will be dull)")
        world((0.5, 0.5, 0.5), 0.6, args.hdri, args.hdri_strength, args.hdri_rotation, camera_bg=None)
        floor = MAT.get("floor_matte", color=args.floor_color or (0.16, 0.15, 0.14))
        plane(col, "Tabletop", center, 60 * S, floor, z0)
        area_light(col, "Key softbox", center, cam_az - 45, 55, 10 * S, (6 * S, 6 * S), 4.0, (1.0, 0.97, 0.93))
        area_light(col, "Strip edge", center, cam_az + 140, 20, 7 * S, (0.33 * S, 8 * S), 4.0)
        return ("Khronos PBR Neutral", None)
    if name == "white-seamless":
        world((0.9, 0.9, 0.9), 0.15)
        cyclorama(col, "Seamless", center, S, MAT.get("floor_matte", color=args.floor_color or (0.72, 0.72, 0.72), roughness=0.9), z0, cam_az)
        area_light(col, "Overhead softbox", center, cam_az, 75, 8 * S, (8 * S, 8 * S), 12.0)
        area_light(col, "Fill left", center, cam_az - 70, 20, 8 * S, (4 * S, 8 * S), 4.0)
        area_light(col, "Fill right", center, cam_az + 70, 20, 8 * S, (4 * S, 8 * S), 3.0)
        area_light(col, "Strip back", center, cam_az + 180, 30, 7 * S, (0.33 * S, 8 * S), 6.0)
        return ("AgX", "AgX - Base Contrast")
    if name == "hero-float":
        world((0.008, 0.008, 0.009), 1.0)
        wall = MAT.get("floor_matte", color=(0.035, 0.035, 0.038), roughness=0.9)
        back = center + direction(cam_az + 180, 0) * 8 * S
        me = bpy.data.meshes.new("Backdrop wall")
        w = 30 * S
        me.from_pydata([(-w, 0, -w), (w, 0, -w), (w, 0, w), (-w, 0, w)], [], [(0, 1, 2, 3)])
        ob = link(bpy.data.objects.new("Backdrop wall", me), col)
        ob.location = back
        ob.rotation_euler = (0, 0, math.radians(cam_az))
        me.materials.append(wall)
        area_light(col, "Wall gradient", back + Vector((0, 0, -4 * S)), cam_az, 60, 6 * S, (14 * S, 6 * S), 1.2)
        area_light(col, "Key softbox", center, cam_az - 40, 30, 9 * S, (5 * S, 8 * S), 7.0, (1.0, 0.985, 0.96))
        area_light(col, "Rim left", center, cam_az - 140, 20, 6 * S, (0.3 * S, 10 * S), 9.0, (0.92, 0.96, 1.0))
        area_light(col, "Rim right", center, cam_az + 140, 20, 6 * S, (0.3 * S, 10 * S), 7.0)
        if args.floor == "gloss":
            plane(col, "Gloss floor", center, 60 * S, MAT.get("floor_gloss"), z0 - args.float_gap * S)
        return ("AgX", "AgX - Base Contrast")
    raise SystemExit(f"STUDIO error: unknown recipe '{name}'")


def emit(spec, col):
    """--emit 'Pattern=r,g,b:strength' turns matching objects into a lit LED and adds a small point light."""
    import fnmatch
    pat, _, rest = spec.partition("=")
    rgb, _, st = rest.partition(":")
    color = tuple(float(x) for x in rgb.split(",")) if rgb else (1.0, 0.86, 0.70)
    strength = float(st or 60)
    m = MAT.emissive(f"VH LED on {pat}", color, strength)
    n = 0
    for o in [o for o in bpy.data.objects if fnmatch.fnmatchcase(o.name, pat)]:
        MAT.assign(o, m)
        lo, hi = bbox([o])
        lt = bpy.data.lights.new(f"LED light {o.name}", "POINT")
        lt.color = color
        size = max((hi - lo).length, 1e-6)
        lt.shadow_soft_size = size * 0.5
        lt.energy = 2.0 * strength * MAT.mm(1.0) ** 2          # ~120 W at strength 60 in a millimetre scene
        lo_ = link(bpy.data.objects.new(f"LED light {o.name}", lt), col)
        lo_[KEEP_LIGHT] = True
        lo_.location = (lo + hi) / 2 + Vector((0, 0, 0.6 * size))     # just above the lens, inside the window
        n += 1
    return n


# ---------------------------------------------------------------- gate

def gate(path, allow):
    if allow:
        print("STUDIO gate: skipped (--allow-unvalidated)")
        return True
    if not path or not os.path.exists(path):
        print("STUDIO gate: REFUSED — no validator report. Run the assembly validator (enclosure-engineer) "
              "and pass --validator-json, or --allow-unvalidated for non-assembly scenes.")
        return False
    rep = json.load(open(path))
    if not rep.get("ok"):
        n = rep.get("n_interpenetrations", rep.get("n_interpenetracoes", "?"))
        print(f"STUDIO gate: REFUSED — validator says the scene fails ({n} interpenetrations). Fix at the source.")
        return False
    blend = bpy.data.filepath
    if blend and os.path.getmtime(blend) > os.path.getmtime(path) + 1:
        print("STUDIO gate: REFUSED — the .blend changed after the validator ran. Validate again.")
        return False
    print("STUDIO gate: ok")
    return True


def main(argv):
    ap = argparse.ArgumentParser(prog="studio.py", description="Product studio render (see module docstring).")
    ap.add_argument("--target", required=True, help="collection, object (with children) or glob of the product")
    ap.add_argument("--recipe", default="dark-studio", choices=["dark-studio", "tabletop-hdri", "white-seamless", "hero-float"])
    ap.add_argument("--view", default="hero", choices=sorted(VIEWS), help="named camera angle")
    ap.add_argument("--az", type=float, help="azimuth override (deg)")
    ap.add_argument("--el", type=float, help="elevation override (deg)")
    ap.add_argument("--lens", type=float, default=100.0, help="focal length (mm, full frame); 85–105 for products")
    ap.add_argument("--fstop", type=float, default=8.0, help="aperture; small products need f/8–f/16 to stay sharp")
    ap.add_argument("--fill", type=float, default=0.6, help="fraction of the short image side the product fills")
    ap.add_argument("--focus", help="object to focus on (default: first visible surface at the center)")
    ap.add_argument("--format", default="preview", choices=sorted(FORMATS))
    ap.add_argument("--preset", default="preview", choices=sorted(PRESETS))
    ap.add_argument("--samples", type=int, help="override samples")
    ap.add_argument("--exposure", type=float, default=0.0)
    ap.add_argument("--hdri", help="studio HDRI (.hdr/.exr), e.g. a Poly Haven studio set")
    ap.add_argument("--hdri-strength", type=float, default=0.6)
    ap.add_argument("--hdri-rotation", type=float, default=0.0)
    ap.add_argument("--floor", choices=["none", "gloss"], default="none", help="hero-float: glossy floor")
    ap.add_argument("--floor-color", type=lambda s: tuple(float(x) for x in s.split(",")))
    ap.add_argument("--float-gap", type=float, default=0.6, help="hero-float: gap to the floor, × product size")
    ap.add_argument("--emit", action="append", default=[], help="'LEDobj*=r,g,b:strength' (repeatable)")
    ap.add_argument("--transparent", action="store_true", help="transparent film (for page compositing)")
    ap.add_argument("--validator-json", help="passing report from the assembly validator")
    ap.add_argument("--allow-unvalidated", action="store_true")
    ap.add_argument("--out", required=True, help="output PNG path")
    ap.add_argument("--save-scene", help="also save the lit scene .blend (to render elsewhere, e.g. a cloud GPU)")
    ap.add_argument("--dry-run", action="store_true", help="build everything, do not render")
    a = ap.parse_args(argv)

    if not gate(a.validator_json, a.allow_unvalidated):
        return 2
    t0 = time.time()
    objs = collect(a.target)
    lo, hi = bbox(objs)
    center = (lo + hi) / 2
    S = max(hi - lo)
    a.half_height = (hi.z - lo.z) / 2
    az, el = VIEWS[a.view]
    az = a.az if a.az is not None else az
    el = a.el if a.el is not None else el
    kept = 0
    for o in bpy.data.objects:                                # only our studio lights, plus tagged shot lights
        if o.type == "LIGHT":
            keep = bool(o.get(KEEP_LIGHT))
            o.hide_render = not keep
            kept += keep
    if kept:
        print(f"STUDIO keeping {kept} light(s) tagged '{KEEP_LIGHT}'")
    col = studio_collection()
    vt, look = recipe(a.recipe, col, center, S, az, a)
    res = FORMATS[a.format]
    cam, dist = camera(col, center, S, az, el, a.lens, a.fstop, a.fill, res, a.focus, objs)
    leds = sum(emit(e, col) for e in a.emit)
    render_settings(a.preset, res, vt, look, a.exposure, a.transparent)
    if a.samples:
        bpy.context.scene.cycles.samples = a.samples
    dev = use_gpu()
    sc = bpy.context.scene
    side = {"recipe": a.recipe, "view": a.view, "az": az, "el": el, "lens": a.lens, "fstop": a.fstop,
            "distance_bu": round(dist, 4), "size_bu": round(S, 4), "resolution": res, "samples": sc.cycles.samples,
            "device": dev, "view_transform": vt, "look": look, "leds": leds, "blend": bpy.data.filepath}
    if a.save_scene:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save_scene), copy=True)
    if a.dry_run:
        print("STUDIO dry run", json.dumps(side))
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    sc.render.filepath = os.path.abspath(a.out)
    bpy.ops.render.render(write_still=True)
    side["seconds"] = round(time.time() - t0, 1)
    json.dump(side, open(os.path.splitext(a.out)[0] + ".json", "w"), indent=1)
    ok = os.path.exists(a.out)
    print(f"STUDIO {'rendered' if ok else 'FAILED'} {a.out} · {a.recipe}/{a.view} · {res[0]}×{res[1]} · "
          f"{sc.cycles.samples} spp · {dev} · {side['seconds']} s")
    return 0 if ok else 1


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    rc = main(argv)
    if bpy.app.background:
        sys.exit(rc)
