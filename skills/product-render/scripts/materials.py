"""Physically based material library for product renders (Blender 4.2+ / 5.x, Cycles).

Every material is built from a Principled BSDF plus procedural detail: micro relief, per-object color
variation (two parts never come from the same lot), and surface wear (fingerprints, smears, micro-scratches,
dust on up-facing faces). Wear is procedural by default. If you pass a folder with the CC0 ambientCG sets
Fingerprints009, Smear003, Scratches005 and SurfaceImperfections015, the real scans are used instead.

Use as a library (inside Blender):
    import sys; sys.path.insert(0, "<skill>/scripts"); import materials as M
    M.configure(bu_per_mm=None, wear_textures=None)       # None = detect from the scene units
    mat = M.get("plastic_clear", wear=0.5)
    M.assign(obj, mat)

Use from the command line (headless):
    blender -b scene.blend --python materials.py -- \
        --assign "Body*=plastic_black:wear=0.4" "Lid=plastic_black" "Strap=cord_braided:color=0.02,0.02,0.022" \
        --save scene_materials.blend
    blender -b --python materials.py -- --list

Patterns are fnmatch globs on object names. Options after ':' are key=value pairs: wear, color (r,g,b in
linear 0–1), variation, roughness.
"""
import argparse
import fnmatch
import os
import sys

import bpy

KINDS = {
    # enclosure
    "plastic_clear": "Optical polycarbonate/PMMA, polished, faint blue absorption, oily fingerprints",
    "plastic_black": "Black molded PC/ABS with light mold texture (satin)",
    "plastic_white": "White molded PC/ABS with subsurface scattering (not flat white)",
    "plastic_color": "Molded plastic in any color (color=r,g,b)",
    "aluminum_anodized": "Bead-blasted anodized aluminum (color=r,g,b)",
    "aluminum_brushed": "Brushed bare aluminum, anisotropic",
    "stainless": "Polished 316L stainless with micro-scratches",
    "gold": "Hard gold plating (contacts, pogo pins)",
    "silicone": "Soft-touch silicone/TPU strap or button (color=r,g,b)",
    "rubber": "Matte black rubber gasket/foot",
    "glass": "Cover glass with a faint anti-reflective thin film",
    "cord_braided": "Braided nylon cord (needs UVs along the cord; color=r,g,b)",
    "fabric": "Woven fabric (lanyard, case)",
    # electronics
    "solder_mask": "Glossy solder mask over FR4 (color=r,g,b; default green)",
    "enig": "ENIG pad finish (immersion gold, slightly orange, matte-satin)",
    "fr4_edge": "Routed FR4 board edge (fiberglass, pale)",
    "ic_epoxy": "IC mold compound: black, silica-filled, bead-blasted satin",
    "laser_marking": "Laser marking on IC epoxy (grey, matte)",
    "silicon_die": "Bare WLCSP/DSBGA die back (dark, slightly glossy)",
    "mlcc": "MLCC ceramic body (caramel, per-part lot color)",
    "resistor_film": "Thick-film resistor top (black glass overglaze)",
    "alumina": "Alumina substrate / chip antenna body (off-white ceramic)",
    "ferrite": "Molded ferrite / metal-powder inductor body",
    "tin": "Matte tin terminations and leads",
    "nickel": "Nickel-silver cans, springs and shields (brushed)",
    "solder_sac305": "Reflowed SAC305 solder (satin, dendritic frost)",
    "lcp_ivory": "LCP connector housing (ivory)",
    "lcp_dark": "LCP connector housing (dark brown)",
    "led_lens": "Clear LED encapsulant (silicone/epoxy)",
    "led_body": "White LED reflector body",
    "led_phosphor": "White-LED phosphor (yellow, diffuse)",
    # scene
    "floor_matte": "Matte tabletop / seamless paper (color=r,g,b)",
    "floor_gloss": "Glossy black acrylic floor for reflections",
    "dust": "Dust specks",
    "lint": "Fabric lint fibers (thin, slightly translucent)",
}

CFG = {"bu_per_mm": None, "wear_textures": None}
LIB = {}
WEAR_FILES = {
    "fp": ("Fingerprints009", "Opacity", 120.0),     # set name, map, tile size (mm)
    "smear": ("Smear003", "Roughness", 90.0),
    "scratch": ("Scratches005", "Opacity", 60.0),
    "dust": ("SurfaceImperfections015", "Opacity", 110.0),
}


# ---------------------------------------------------------------- units

def configure(bu_per_mm=None, wear_textures=None):
    CFG["bu_per_mm"] = bu_per_mm
    CFG["wear_textures"] = wear_textures
    LIB.clear()


def bu_per_mm():
    """Blender units per millimetre. scale_length 0.001 (BU = mm) -> 1; default metres -> 0.001."""
    if CFG["bu_per_mm"]:
        return CFG["bu_per_mm"]
    sl = bpy.context.scene.unit_settings.scale_length or 1.0
    return 0.001 / sl


def per_mm(features_per_mm):
    """Texture scale (features per BU) for a feature density given per millimetre."""
    return features_per_mm / bu_per_mm()


def mm(x):
    """A length in millimetres expressed in Blender units."""
    return x * bu_per_mm()


# ---------------------------------------------------------------- node helpers

class _T:
    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.N, self.L = self.nt.nodes, self.nt.links
        self.out = self.N.new("ShaderNodeOutputMaterial")
        self.b = self.N.new("ShaderNodeBsdfPrincipled")
        self.L.new(self.b.outputs[0], self.out.inputs["Surface"])
        self._tc = None

    def node(self, kind, **inputs):
        n = self.N.new(kind)
        for k, v in inputs.items():
            self.set(n.inputs[k], v)
        return n

    def set(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.L.new(v, sock)
        else:
            sock.default_value = v

    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.N.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self.set(n.inputs[i], v)
        return n.outputs[0]

    def obj(self):
        if self._tc is None:
            self._tc = self.N.new("ShaderNodeTexCoord")
        return self._tc.outputs["Object"]

    def maprange(self, x, lo, hi, a=0.0, b=1.0):
        mr = self.N.new("ShaderNodeMapRange")
        self.set(mr.inputs[0], x)
        mr.inputs[1].default_value, mr.inputs[2].default_value = a, b
        mr.inputs[3].default_value, mr.inputs[4].default_value = lo, hi
        return mr.outputs[0]

    def seed(self):
        """Per-object random offset vector: each part gets its own wear pattern and lot color."""
        oi = self.N.new("ShaderNodeObjectInfo")
        cx = self.N.new("ShaderNodeCombineXYZ")
        for i, k in enumerate("XYZ"):
            self.L.new(self.math("MULTIPLY", oi.outputs["Random"], 37.0 + 11 * i), cx.inputs[k])
        return cx.outputs[0], oi.outputs["Random"]

    def coords(self, seed_vec=None, scale=1.0, stretch=(1, 1, 1)):
        mp = self.N.new("ShaderNodeMapping")
        self.L.new(self.obj(), mp.inputs["Vector"])
        mp.inputs["Scale"].default_value = tuple(scale * s for s in stretch)
        if seed_vec is not None:
            self.L.new(seed_vec, mp.inputs["Location"])
        return mp.outputs[0]

    def noise(self, vec, scale, detail=6.0, rough=0.5):
        n = self.N.new("ShaderNodeTexNoise")
        self.L.new(vec, n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        return n

    def bump(self, height, strength, distance_mm, normal=None):
        bp = self.N.new("ShaderNodeBump")
        self.set(bp.inputs["Height"], height)
        bp.inputs["Strength"].default_value = strength
        bp.inputs["Distance"].default_value = mm(distance_mm)
        if normal is not None:
            self.L.new(normal, bp.inputs["Normal"])
        return bp.outputs["Normal"]

    def bevel(self, radius_mm):
        bv = self.N.new("ShaderNodeBevel")
        bv.samples = 8
        bv.inputs["Radius"].default_value = mm(radius_mm)
        return bv.outputs["Normal"]


def _principled(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    return m, _T(m)


def _rgb(c):
    return (*c[:3], 1.0)


# ---------------------------------------------------------------- wear (fingerprints, smears, scratches, dust)

def _wear_tex(t, key, seed_vec):
    folder = CFG["wear_textures"]
    if not folder:
        return None
    name, kind, tile = WEAR_FILES[key]
    d = os.path.join(folder, name)
    if not os.path.isdir(d):
        return None
    f = next((os.path.join(d, x) for x in sorted(os.listdir(d)) if kind in x and x.lower().endswith((".jpg", ".png"))), None)
    if not f:
        return None
    im = t.N.new("ShaderNodeTexImage")
    im.image = bpy.data.images.load(f, check_existing=True)
    im.image.colorspace_settings.name = "Non-Color"
    im.projection = "BOX"
    im.projection_blend = 0.25
    t.L.new(t.coords(seed_vec, 1.0 / mm(tile)), im.inputs["Vector"])
    return im.outputs["Color"]


def wear_masks(t, seed_vec, amount):
    """0–1 masks: fingerprint ridges in oval patches, smears, thin scratches, dust (up-facing only)."""
    out = {}
    # fingerprints: ring pattern (ridges ~0.45 mm apart) inside sparse oval blobs ~12 mm
    tex = _wear_tex(t, "fp", seed_vec)
    if tex is None:
        vec = t.coords(seed_vec, 1.0)
        w = t.N.new("ShaderNodeTexWave")
        w.wave_type = "RINGS"
        w.rings_direction = "SPHERICAL"
        t.L.new(vec, w.inputs["Vector"])
        w.inputs["Scale"].default_value = per_mm(1 / 0.45) * 0.314         # ridge spacing ~0.45 mm
        w.inputs["Distortion"].default_value = 6.0
        w.inputs["Detail"].default_value = 3.0
        blob = t.node("ShaderNodeTexVoronoi", Scale=per_mm(1 / 16.0))
        t.L.new(vec, blob.inputs["Vector"])
        patch = t.maprange(blob.outputs["Distance"], 1.0, 0.0, 0.22, 0.45)
        patch = t.math("MULTIPLY", patch, t.math("GREATER_THAN", blob.outputs["Color"], 0.6))   # ~1 cell in 3
        ridge = t.maprange(w.outputs["Fac"], 0.0, 1.0, 0.35, 0.75)
        tex = t.math("MULTIPLY", ridge, patch, clamp=True)
    out["fp"] = t.math("MULTIPLY", t.maprange(tex, 0.0, 1.0, 0.15, 0.9), amount, clamp=True)
    # smears: large soft blotches
    tex = _wear_tex(t, "smear", seed_vec)
    if tex is None:
        tex = t.noise(t.coords(seed_vec, 1.0), per_mm(1 / 18.0), 3.0).outputs["Fac"]
    out["smear"] = t.math("MULTIPLY", t.maprange(tex, 0.0, 1.0, 0.5, 0.75), amount, clamp=True)
    # scratches: thin, long, sparse lines (stretched noise, thresholded), random orientation per object
    tex = _wear_tex(t, "scratch", seed_vec)
    if tex is None:
        n = t.noise(t.coords(seed_vec, per_mm(1 / 20.0), stretch=(40, 1, 1)), 1.0, 2.0)   # long along Y
        line = t.maprange(n.outputs["Fac"], 1.0, 0.0, 0.495, 0.505)
        tri = t.math("SUBTRACT", 1.0, t.math("ABSOLUTE", t.math("SUBTRACT", t.math("MULTIPLY", line, 2.0), 1.0)))
        mask = t.noise(t.coords(seed_vec, per_mm(1 / 9.0)), 1.0, 2.0)
        tex = t.math("MULTIPLY", tri, t.maprange(mask.outputs["Fac"], 0.0, 1.0, 0.55, 0.7), clamp=True)
    out["scratch"] = t.math("MULTIPLY", t.maprange(tex, 0.0, 1.0, 0.3, 1.0), amount, clamp=True)
    # dust: specks on up-facing surfaces
    tex = _wear_tex(t, "dust", seed_vec)
    if tex is None:
        v = t.node("ShaderNodeTexVoronoi", Scale=per_mm(1 / 0.6))
        t.L.new(t.coords(seed_vec, 1.0), v.inputs["Vector"])
        tex = t.math("MULTIPLY", t.maprange(v.outputs["Distance"], 1.0, 0.0, 0.0, 0.08),
                     t.math("GREATER_THAN", v.outputs["Color"], 0.8))
    geo = t.N.new("ShaderNodeNewGeometry")
    sep = t.N.new("ShaderNodeSeparateXYZ")
    t.L.new(geo.outputs["Normal"], sep.inputs[0])
    up = t.maprange(sep.outputs["Z"], 0.0, 1.0, 0.55, 1.0)
    out["dust"] = t.math("MULTIPLY", t.math("MULTIPLY", t.maprange(tex, 0.0, 1.0, 0.65, 1.0), up), amount, clamp=True)
    return out


def _lot_color(t, base, variation, rnd):
    """Base color × (1 ± variation) per object."""
    if not variation:
        t.b.inputs["Base Color"].default_value = _rgb(base)
        return
    k = t.maprange(rnd, 1 - variation, 1 + variation)
    vm = t.N.new("ShaderNodeVectorMath")
    vm.operation = "SCALE"
    vm.inputs[0].default_value = base[:3]
    t.L.new(k, vm.inputs["Scale"])
    t.L.new(vm.outputs[0], t.b.inputs["Base Color"])


def _palette(t, colors, rnd, grain=0.12, grain_per_mm=900.0):
    """Per-part color picked from a palette (real lots differ), with fine surface grain."""
    cr = t.N.new("ShaderNodeValToRGB")
    els = cr.color_ramp.elements
    els[0].position, els[0].color = 0.0, _rgb(colors[0])
    els[1].position, els[1].color = 1.0, _rgb(colors[-1])
    for k, c in enumerate(colors[1:-1], 1):
        e = els.new(k / (len(colors) - 1))
        e.color = _rgb(c)
    t.L.new(rnd, cr.inputs[0])
    no = t.noise(t.obj(), per_mm(grain_per_mm))
    mx = t.N.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "OVERLAY"
    mx.inputs[0].default_value = grain
    t.L.new(cr.outputs["Color"], mx.inputs[6])
    t.L.new(no.outputs["Color"], mx.inputs[7])
    t.L.new(mx.outputs[2], t.b.inputs["Base Color"])


def _grain(t, per, strength, rough=None, bevel_mm=0.03, stretch=(1, 1, 1)):
    """Crystalline/sintered grain (Voronoi + fine noise) for relief and roughness; shader bevel on edges."""
    vec = t.coords(None, 1.0, stretch)
    vo = t.node("ShaderNodeTexVoronoi", Scale=per_mm(per))
    t.L.new(vec, vo.inputs["Vector"])
    no = t.noise(vec, per_mm(per * 2.5), 8.0)
    h = t.math("MULTIPLY_ADD", vo.outputs["Distance"], 0.6, no.outputs["Fac"])
    t.L.new(t.bump(h, strength, 0.0015, t.bevel(bevel_mm) if bevel_mm else None), t.b.inputs["Normal"])
    if rough:
        t.L.new(t.maprange(no.outputs["Fac"], *rough), t.b.inputs["Roughness"])


def _relief(t, per, strength, dist_mm, rough=None, bevel_mm=0.025, extra=None):
    n = t.noise(t.obj(), per_mm(per))
    h = n.outputs["Fac"] if extra is None else t.math("ADD", n.outputs["Fac"], extra)
    t.L.new(t.bump(h, strength, dist_mm, t.bevel(bevel_mm) if bevel_mm else None), t.b.inputs["Normal"])
    if rough:
        t.L.new(t.maprange(n.outputs["Fac"], *rough), t.b.inputs["Roughness"])
    return n


# ---------------------------------------------------------------- the library

def get(kind, color=None, wear=0.5, variation=None, roughness=None, name=None, sss_mm=None):
    """Return (and cache) a material. wear 0–1 scales fingerprints/scratches/dust on enclosure materials.
    sss_mm overrides the subsurface scale in millimetres. Thin translucent parts (membranes, button caps,
    light windows) over a dark cavity need sss_mm <= 0.1, or they read dark: light scatters into the cavity
    instead of back to the camera. Use the default scale only for solid parts or parts lit from inside."""
    if kind not in KINDS:
        raise KeyError(f"unknown material kind '{kind}'. Known: {', '.join(sorted(KINDS))}")
    key = (kind, tuple(color) if color else None, round(wear, 3), variation, roughness, name, sss_mm)
    if key in LIB:
        return LIB[key]
    m, t = _principled(name or f"VH · {kind}" + (f" {tuple(round(c, 3) for c in color)}" if color else "")
                       + (f" wear {wear:g}" if kind.startswith(("plastic", "alum", "stain", "silic", "glass")) else ""))
    s = t.b.inputs
    seed_vec, rnd = t.seed()

    if kind.startswith("plastic"):
        W = wear_masks(t, seed_vec, wear)
        s["IOR"].default_value = 1.585                                   # polycarbonate; PMMA is 1.49
        if kind == "plastic_clear":
            base, r0 = (0.97, 0.985, 1.0), 0.015
            s["Transmission Weight"].default_value = 1.0
            r = t.math("ADD", r0, t.math("MULTIPLY", W["fp"], 0.11))
            r = t.math("ADD", r, t.math("MULTIPLY", W["smear"], 0.05))
            r = t.math("ADD", r, t.math("MULTIPLY", W["scratch"], 0.22), clamp=True)
            s["Coat IOR"].default_value = 1.47                           # skin oil film on top
            s["Coat Roughness"].default_value = 0.3
            t.L.new(t.math("MULTIPLY", W["fp"], 0.6), s["Coat Weight"])
            # absorption 0.05 per mm, expressed per Blender unit
            vol = t.node("ShaderNodeVolumeAbsorption", Color=(0.93, 0.96, 1.0, 1), Density=0.05 / bu_per_mm())
            t.L.new(vol.outputs[0], t.out.inputs["Volume"])
            mold = (3.0, 0.0006)                                         # polished: almost no texture
        elif kind == "plastic_black":
            base, r0 = (0.010, 0.010, 0.011), 0.50
            r = t.math("SUBTRACT", r0, t.math("MULTIPLY", W["fp"], 0.2))  # skin oil fills the texture: smoother
            r = t.math("SUBTRACT", r, t.math("MULTIPLY", W["smear"], 0.08))
            r = t.math("ADD", r, t.math("MULTIPLY", W["scratch"], 0.1), clamp=True)
            mold = (40.0, 0.004)                                         # light mold texture (MT-11010 class)
        elif kind == "plastic_white":
            base, r0 = (0.80, 0.80, 0.77), 0.38
            s["Subsurface Weight"].default_value = 0.6
            s["Subsurface Radius"].default_value = (1.0, 0.85, 0.7)
            s["Subsurface Scale"].default_value = mm(0.6)
            r = t.math("ADD", r0, t.math("MULTIPLY", W["fp"], 0.06))
            r = t.math("ADD", r, t.math("MULTIPLY", W["scratch"], 0.08), clamp=True)
            mold = (40.0, 0.003)
        else:
            base, r0 = (color or (0.3, 0.3, 0.3)), roughness if roughness is not None else 0.42
            s["Subsurface Weight"].default_value = 0.15
            s["Subsurface Radius"].default_value = tuple(min(1.0, 0.3 + c) for c in base[:3])
            s["Subsurface Scale"].default_value = mm(0.4)
            r = t.math("ADD", r0, t.math("MULTIPLY", W["scratch"], 0.1), clamp=True)
            mold = (40.0, 0.003)
        if color and kind != "plastic_color":
            base = color
        _lot_color(t, base, 0.03 if variation is None else variation, rnd)
        t.L.new(r, s["Roughness"])
        t.L.new(t.math("MULTIPLY", W["dust"], 0.12), s["Sheen Weight"])
        s["Sheen Roughness"].default_value = 0.5
        n = t.noise(t.obj(), per_mm(mold[0]), 3.0)
        h = t.math("ADD", n.outputs["Fac"], t.math("MULTIPLY", W["scratch"], -0.6))
        t.L.new(t.bump(h, 0.4, mold[1]), s["Normal"])

    elif kind == "aluminum_anodized":
        _lot_color(t, color or (0.08, 0.08, 0.085), 0.02 if variation is None else variation, rnd)
        s["Metallic"].default_value = 1.0
        W = wear_masks(t, seed_vec, wear * 0.6)
        n = t.noise(t.obj(), per_mm(60.0), 8.0)                        # bead blast
        t.L.new(t.math("ADD", t.maprange(n.outputs["Fac"], 0.32, 0.42), t.math("MULTIPLY", W["fp"], -0.12)), s["Roughness"])
        t.L.new(t.bump(n.outputs["Fac"], 0.25, 0.003), s["Normal"])
    elif kind == "aluminum_brushed":
        s["Base Color"].default_value = _rgb(color or (0.91, 0.92, 0.92))
        s["Metallic"].default_value = 1.0
        s["Anisotropic"].default_value = 0.8
        _grain(t, 600.0, 0.12, (0.18, 0.30), 0.02, stretch=(1, 40, 1))
    elif kind == "stainless":
        s["Base Color"].default_value = _rgb(color or (0.80, 0.79, 0.77))
        s["Metallic"].default_value = 1.0
        W = wear_masks(t, seed_vec, wear)
        t.L.new(t.math("ADD", roughness or 0.10, t.math("MULTIPLY", W["scratch"], 0.25), clamp=True), s["Roughness"])
        t.L.new(t.bump(t.math("MULTIPLY", W["scratch"], -1.0), 0.3, 0.002), s["Normal"])
    elif kind == "gold":
        s["Base Color"].default_value = _rgb(color or (1.0, 0.77, 0.36))
        s["Metallic"].default_value = 1.0
        _grain(t, 900.0, 0.08, (0.14, 0.26), 0.02, stretch=(1, 25, 1))
    elif kind == "silicone":
        _lot_color(t, color or (0.03, 0.03, 0.032), 0.02 if variation is None else variation, rnd)
        s["Roughness"].default_value = roughness or 0.62
        s["Subsurface Weight"].default_value = 0.3
        s["Subsurface Scale"].default_value = mm(0.5)
        s["Sheen Weight"].default_value = 0.2
        _relief(t, 25.0, 0.2, 0.004, bevel_mm=0)
    elif kind == "rubber":
        s["Base Color"].default_value = _rgb(color or (0.02, 0.02, 0.02))
        s["Roughness"].default_value = 0.85
        _relief(t, 30.0, 0.3, 0.004, bevel_mm=0)
    elif kind == "glass":
        s["Base Color"].default_value = (1, 1, 1, 1)
        s["Transmission Weight"].default_value = 1.0
        s["IOR"].default_value = 1.52
        s["Roughness"].default_value = 0.0
        if "Thin Film Thickness" in s:                                  # anti-reflective coating (4.2+)
            s["Thin Film Thickness"].default_value = 120.0
            s["Thin Film IOR"].default_value = 1.38
        W = wear_masks(t, seed_vec, wear)
        t.L.new(t.math("ADD", t.math("MULTIPLY", W["fp"], 0.08), t.math("MULTIPLY", W["smear"], 0.04)), s["Roughness"])
    elif kind in ("cord_braided", "fabric"):
        _lot_color(t, color or (0.010, 0.010, 0.011), 0.04 if variation is None else variation, rnd)
        s["Sheen Weight"].default_value = 0.45
        s["Sheen Roughness"].default_value = 0.35
        if kind == "cord_braided":
            s["Anisotropic"].default_value = 0.7
            uv = t.N.new("ShaderNodeUVMap")
            tan = t.N.new("ShaderNodeTangent")
            tan.direction_type = "UV_MAP"
            t.L.new(tan.outputs[0], s["Tangent"])
            mp = t.N.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = (90.0, 2.5, 1.0)          # fibers run along each strand
            t.L.new(uv.outputs[0], mp.inputs["Vector"])
            nz = t.noise(mp.outputs[0], 1.0, 3.0)
        else:
            nz = t.noise(t.coords(None, per_mm(4.0), stretch=(1, 8, 1)), 1.0, 4.0)
        t.L.new(t.maprange(nz.outputs["Fac"], 0.35, 0.55), s["Roughness"])
        t.L.new(t.bump(nz.outputs["Fac"], 0.5, 0.006), s["Normal"])

    elif kind == "solder_mask":
        s["Base Color"].default_value = _rgb(color or (0.02, 0.16, 0.06))
        s["Roughness"].default_value = roughness or 0.22
        s["Coat Weight"].default_value = 0.6
        s["Coat Roughness"].default_value = 0.12
        s["Subsurface Weight"].default_value = 0.1
        _relief(t, 8.0, 0.08, 0.002, bevel_mm=0)
    elif kind == "enig":
        s["Base Color"].default_value = _rgb(color or (1.0, 0.74, 0.40))
        s["Metallic"].default_value = 1.0
        _relief(t, 900.0, 0.1, 0.0015, (0.28, 0.36), bevel_mm=0)
    elif kind == "fr4_edge":
        s["Base Color"].default_value = _rgb(color or (0.62, 0.60, 0.48))
        s["Roughness"].default_value = 0.7
        s["Subsurface Weight"].default_value = 0.2
        _grain(t, 300.0, 0.3, None, 0, stretch=(1, 1, 6))
    elif kind == "ic_epoxy":
        _palette(t, [(0.028, 0.028, 0.030), (0.034, 0.034, 0.036), (0.024, 0.025, 0.027)], rnd, 0.10, 3000.0)
        s["Specular IOR Level"].default_value = 0.35                   # silica-filled epoxy: bead-blasted matte
        _grain(t, 2200.0, 0.22, (0.50, 0.68), 0.04)
    elif kind == "laser_marking":
        s["Base Color"].default_value = (0.105, 0.105, 0.11, 1)        # laser burns resin: grey and duller
        s["Roughness"].default_value = 0.92
        s["Specular IOR Level"].default_value = 0.2
    elif kind == "silicon_die":
        s["Base Color"].default_value = (0.05, 0.05, 0.07, 1)
        s["Roughness"].default_value = 0.18
        s["Specular IOR Level"].default_value = 0.6
    elif kind == "mlcc":
        _palette(t, [(0.46, 0.34, 0.20), (0.38, 0.27, 0.15), (0.30, 0.20, 0.11), (0.42, 0.33, 0.24)], rnd, 0.18, 1400.0)
        s["Subsurface Weight"].default_value = 0.04
        s["Subsurface Radius"].default_value = (0.04, 0.025, 0.015)
        s["Sheen Weight"].default_value = 0.25
        s["Sheen Roughness"].default_value = 0.4
        _grain(t, 1300.0, 0.30, (0.55, 0.72), 0.03)
    elif kind == "resistor_film":
        s["Base Color"].default_value = (0.020, 0.020, 0.022, 1)
        _relief(t, 1400.0, 0.12, 0.0015, (0.28, 0.40), 0.02)
    elif kind == "alumina":
        _lot_color(t, (0.78, 0.77, 0.72), 0.04 if variation is None else variation, rnd)
        _relief(t, 1600.0, 0.15, 0.0015, (0.55, 0.72), 0.02)
    elif kind == "ferrite":
        s["Base Color"].default_value = (0.05, 0.05, 0.052, 1)
        s["Metallic"].default_value = 0.25
        _grain(t, 1100.0, 0.5, (0.45, 0.85), 0.03)
    elif kind == "tin":
        s["Base Color"].default_value = (0.60, 0.60, 0.58, 1)
        s["Metallic"].default_value = 1.0
        _grain(t, 2600.0, 0.35, (0.40, 0.58), 0.035)
    elif kind == "nickel":
        s["Base Color"].default_value = (0.70, 0.69, 0.66, 1)
        s["Metallic"].default_value = 1.0
        _grain(t, 600.0, 0.12, (0.22, 0.34), 0.02, stretch=(1, 40, 1))
    elif kind == "solder_sac305":
        s["Base Color"].default_value = (0.80, 0.80, 0.78, 1)
        s["Metallic"].default_value = 1.0
        n = t.noise(t.obj(), per_mm(2500.0), 4.0)                      # dendritic frost: satin, not mirror
        t.L.new(t.maprange(n.outputs["Fac"], 0.10, 0.24), s["Roughness"])
        t.L.new(t.bump(n.outputs["Fac"], 0.08, 0.002), s["Normal"])
    elif kind == "lcp_ivory":
        s["Base Color"].default_value = (0.78, 0.71, 0.55, 1)
        s["Roughness"].default_value = 0.45
        s["Subsurface Weight"].default_value = 0.25
        s["Subsurface Radius"].default_value = (0.3, 0.2, 0.1)
    elif kind == "lcp_dark":
        s["Base Color"].default_value = (0.16, 0.14, 0.10, 1)
        s["Roughness"].default_value = 0.5
    elif kind == "led_lens":
        s["Base Color"].default_value = (0.97, 0.98, 1.0, 1)
        s["Transmission Weight"].default_value = 1.0
        s["Roughness"].default_value = 0.05
        s["IOR"].default_value = 1.5
    elif kind == "led_body":
        s["Base Color"].default_value = (0.92, 0.92, 0.90, 1)
        s["Roughness"].default_value = 0.35
        s["Subsurface Weight"].default_value = 0.5
    elif kind == "led_phosphor":
        s["Base Color"].default_value = (0.98, 0.85, 0.42, 1)
        s["Roughness"].default_value = 0.45
        s["Subsurface Weight"].default_value = 0.6
        s["Subsurface Radius"].default_value = (0.3, 0.25, 0.1)

    elif kind == "floor_matte":
        s["Base Color"].default_value = _rgb(color or (0.18, 0.18, 0.18))
        s["Roughness"].default_value = roughness or 0.8
        _relief(t, 2.0, 0.05, 0.01, bevel_mm=0)
    elif kind == "floor_gloss":
        s["Base Color"].default_value = _rgb(color or (0.004, 0.004, 0.005))
        s["Roughness"].default_value = roughness or 0.12
        s["Coat Weight"].default_value = 1.0
        s["Coat Roughness"].default_value = 0.04
    elif kind == "dust":
        s["Base Color"].default_value = (0.55, 0.53, 0.5, 1)
        s["Roughness"].default_value = 0.9
        s["Subsurface Weight"].default_value = 0.3
    elif kind == "lint":
        s["Base Color"].default_value = _rgb(color or (0.62, 0.62, 0.64))
        s["Roughness"].default_value = 0.6
        s["Transmission Weight"].default_value = 0.35
    if sss_mm is not None:
        s["Subsurface Scale"].default_value = mm(sss_mm)
    LIB[key] = m
    return m


def emissive(name, color=(1.0, 0.86, 0.70), strength=60.0):
    """An LED that is on: emission on the lens/phosphor (add a point light too; see studio.py --emit)."""
    m, t = _principled(name)
    t.b.inputs["Base Color"].default_value = _rgb(color)
    t.b.inputs["Emission Color"].default_value = _rgb(color)
    t.b.inputs["Emission Strength"].default_value = strength
    return m


def assign(obj, mat):
    """Put the material on every slot of the object (object-linked, so shared meshes keep their data)."""
    if obj.type not in ("MESH", "CURVE", "FONT", "SURFACE", "META"):
        return 0
    if not obj.material_slots:
        obj.data.materials.append(mat)
        return 1
    for sl in obj.material_slots:
        sl.link = "OBJECT"
        sl.material = mat
    return len(obj.material_slots)


def apply_map(rules, wear_default=0.5):
    """rules: list of 'pattern=kind[:wear=0.4][:color=r,g,b][:variation=0.03][:roughness=0.4]'."""
    done = {}
    for rule in rules:
        pat, spec = rule.split("=", 1)
        kind, *opts = spec.split(":")
        kw = {"wear": wear_default}
        for part in opts:
            k, _, v = part.partition("=")
            if k == "color":
                kw["color"] = tuple(float(x) for x in v.split(","))
            elif k in ("wear", "variation", "roughness"):
                kw[k] = float(v)
            else:
                raise ValueError(f"unknown option '{k}' in rule '{rule}'")
        m = get(kind, **kw)
        n = 0
        for o in bpy.data.objects:
            if fnmatch.fnmatchcase(o.name, pat):
                n += bool(assign(o, m))
        done[f"{pat}->{kind}"] = n
    return done


def main(argv):
    ap = argparse.ArgumentParser(prog="materials.py", description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true", help="print the material kinds and exit")
    ap.add_argument("--assign", nargs="*", default=[], help='rules "Pattern*=kind[:wear=0.4][:color=r,g,b]"')
    ap.add_argument("--wear", type=float, default=0.5, help="default wear 0–1 (fingerprints, scratches, dust)")
    ap.add_argument("--wear-textures", help="folder with ambientCG Fingerprints009, Smear003, Scratches005, "
                                            "SurfaceImperfections015 (optional; procedural otherwise)")
    ap.add_argument("--bu-per-mm", type=float, help="Blender units per mm (default: from scene units)")
    ap.add_argument("--save", help="save the .blend here (never overwrites the input unless you pass the same path)")
    a = ap.parse_args(argv)
    if a.list:
        for k, v in KINDS.items():
            print(f"{k:20s} {v}")
        return 0
    configure(a.bu_per_mm, a.wear_textures)
    res = apply_map(a.assign, a.wear)
    empty = [k for k, n in res.items() if n == 0]
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save), copy=True)
    print("MATERIALS", res, ("no match: " + ", ".join(empty)) if empty else "", f"(1 BU = {1 / bu_per_mm():g} mm)")
    return 1 if empty else 0


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    rc = main(argv)
    if bpy.app.background:
        sys.exit(rc)
