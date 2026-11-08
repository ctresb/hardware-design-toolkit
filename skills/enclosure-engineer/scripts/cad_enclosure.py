#!/usr/bin/env python3
"""Parametric B-rep enclosure from a JSON spec: the CAD source of truth.

Builds a two-part enclosure (a drafted, filleted shell and a lid) plus its joint parts (an adhesive ring,
a compressed O-ring or a flat gasket with captive screws), an optional round battery door in the lid, then adds features: thin LED windows, sound ports with membrane seats,
lanyard tunnels, bosses and ribs. It exports:

  <name>_assembly.step   all parts, labelled (molders, 3D-print services, mechanical CAD)
  <name>_<part>.step     one STEP per part (one RFQ line each)
  <name>_<part>.stl      one STL per part (SLA/FDM prototypes)
  <name>_assembly.glb    all parts (Blender: assembly, validation, renders). 1 glTF unit = 1 mm.
  <name>_keepouts.step / .glb   board and cell keep-out volumes, for checks and the Blender assembly
  <name>_dfm.json / .md  DFM check: wall thickness, draft, undercuts, keep-out collisions

Geometry changes happen here and nowhere else. Blender only imports the GLB, validates and renders.

Frame: z = 0 is the outer bottom of the lid; +Z is the mold pull direction of the shell (cavity side).
Units: millimetres and degrees.

Usage (run with `cad_python` from toolchain.json, the build123d venv made by toolchain-setup):
    "$CAD_PY" cad_enclosure.py hw/mech/enclosure.json --out hw/mech/cad
    "$CAD_PY" cad_enclosure.py spec.json --out out --formats step,glb --no-dfm

Requires build123d (Python 3.10–3.13 wheels; toolchain-setup installs it with uv or a python3.12 venv). Tested with build123d 0.13 on
Python 3.12. Exit code: 0 = built, no DFM errors; 1 = DFM errors; 2 = spec or build error.
"""
import argparse
import copy
import json
import math
import os
import sys
import time

try:
    from build123d import (Align, Axis, Box, Circle, Compound, Cylinder, Plane, Polygon, Pos, Rectangle, RectangleRounded,
                           Rot, Solid, Unit, Vector, export_gltf, export_step, export_stl, extrude, fillet, offset)
except ImportError:
    print("CAD error: build123d is not importable from this Python. Run with `cad_python` from toolchain.json "
          "(toolchain-setup creates that venv; build123d needs Python 3.10–3.13).")
    sys.exit(2)


class SpecError(Exception):
    pass


# ---------------------------------------------------------------- outlines
def outline(spec, z, inset=0.0):
    """The enclosure outline as a Sketch on the plane z, shrunk by `inset` (mm)."""
    o = spec["outline"]
    kind = o["type"]
    if kind == "rounded_rect":
        w, d, r = o["width"] - 2 * inset, o["depth"] - 2 * inset, o["corner_radius"] - inset
        if w <= 0 or d <= 0:
            raise SpecError(f"outline inset {inset} mm leaves nothing")
        sk = RectangleRounded(w, d, max(r, 0.05)) if r > 0.05 else Rectangle(w, d)
    elif kind == "circle":
        dia = o["diameter"] - 2 * inset
        if dia <= 0:
            raise SpecError(f"outline inset {inset} mm leaves nothing")
        sk = Circle(dia / 2)
    elif kind == "polygon":
        base = Polygon(*[tuple(p) for p in o["points"]], align=None)
        r = o.get("corner_radius", 0.0)
        if r > 0:
            base = fillet(base.vertices(), r)
        sk = offset(base, amount=-inset) if inset else base
    else:
        raise SpecError(f"unknown outline type: {kind}")
    return Plane.XY.offset(z) * sk


def ring(spec, z, inset_outer, inset_inner):
    return outline(spec, z, inset_outer) - outline(spec, z, inset_inner)


def down(z):
    return Plane((0, 0, z), x_dir=(1, 0, 0), z_dir=(0, 0, -1))


def cyl(r, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, z0) * Solid.make_cylinder(r, z1 - z0)


def side_points(spec, inset, count):
    """Points on the outline (shrunk by inset) where joint features go, with the outward direction."""
    o = spec["outline"]
    if o["type"] == "circle":
        R = o["diameter"] / 2 - inset
        out = []
        for k in range(count):
            a = 2 * math.pi * k / count + math.radians(spec["lid"].get("lug_angle_deg", 0))
            out.append((R * math.cos(a), R * math.sin(a), math.degrees(a)))
        return out
    if o["type"] == "rounded_rect":
        w, d = o["width"] / 2 - inset, o["depth"] / 2 - inset
        pts = [(w, 0, 0), (-w, 0, 180), (0, d, 90), (0, -d, 270)]
        return pts[:count] if count in (2, 4) else pts[:2]
    raise SpecError("snap and twist joints need a rounded_rect or circle outline")


# ---------------------------------------------------------------- screw joints and round doors
def screw_positions(spec, cfg, inset):
    """Explicit `positions`, or automatic ones: 4 corners of a rounded_rect (on the corner diagonal), or `count`
    points around a circle, each `inset` mm inside the outer outline."""
    if cfg.get("positions"):
        return [tuple(p) for p in cfg["positions"]]
    o = spec["outline"]
    if o["type"] == "circle":
        R, n = o["diameter"] / 2 - inset, cfg.get("count", 3)
        a0 = math.radians(cfg.get("angle_deg", 90))
        return [(R * math.cos(a0 + 2 * math.pi * k / n), R * math.sin(a0 + 2 * math.pi * k / n)) for k in range(n)]
    if o["type"] == "rounded_rect":
        w, d, r = o["width"] / 2, o["depth"] / 2, o["corner_radius"]
        k = (r - inset) / math.sqrt(2)                      # along the 45 deg diagonal of the corner arc
        cx, cy = w - r, d - r
        if r - inset < 0:
            cx, cy, k = w - inset, d - inset, 0.0
        return [(sx * (cx + k), sy * (cy + k)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))][:cfg.get("count", 4)]
    raise SpecError("screw joint on a polygon outline needs explicit screws.positions")


def _screw_checks(sc, mw, where):
    """Thread-forming screws in plastic: pilot about 0.8 x screw diameter, boss OD 2 to 2.5 x screw diameter,
    engagement at least 2 x diameter (verify with the screw maker's guide)."""
    e = []
    d = sc.get("screw_d", 1.4)
    if sc["boss_d"] < 2.0 * d - 1e-6:
        e.append(f"{where}: boss OD {sc['boss_d']} mm < 2 x screw diameter {d} mm")
    if (sc["boss_d"] - sc["pilot_d"]) / 2 < mw - 1e-6:
        e.append(f"{where}: boss wall {(sc['boss_d'] - sc['pilot_d']) / 2:.2f} mm < min wall {mw} mm")
    if sc.get("engagement", 0) < 2.0 * d - 1e-6:
        e.append(f"{where}: thread engagement {sc.get('engagement', 0):.2f} mm < {2 * d:.2f} mm (2 x screw diameter "
                 f"{d} mm); taller boss or shorter screw")
    return e


def screws_joint(spec, lidp, body, env, zp, zb, z_ceiling, lip_in, lip_h):
    """Lid held by N captive screws into shell bosses, sealed by a flat die-cut gasket under the shell rim."""
    lid, t = spec["lid"], spec["wall"]
    mw = spec.get("dfm", {}).get("min_wall", 0.8)
    sc = {"screw_d": 1.4, "pilot_d": 1.1, "hole_d": 1.6, "cbore_d": 2.6, "cbore_depth": 0.6, "boss_d": 3.2,
          "count": 4, **lid.get("screws", {})}
    g = {"compressed_t": 0.25, "free_t": 0.3, "material": "silicone foam or solid silicone, die-cut", **lid.get("gasket", {})}
    inset = t + sc["boss_d"] / 2 + 0.3
    pos = screw_positions(spec, sc, inset)
    notes, errors = [], []
    bosses = None
    for x, y in pos:
        b = cyl(sc["boss_d"] / 2, zb, spec["height"] + 1, x, y)     # fused into the ceiling (no sliver at fillets)
        bosses = b if bosses is None else bosses + b
    body = body + (bosses & env)
    pilot_top = zb + sc.get("pilot_depth", min(z_ceiling - zb - mw, 3.0))
    sc["engagement"] = pilot_top - zb
    screws = None
    for x, y in pos:
        body = body - cyl(sc["pilot_d"] / 2, zb - 0.01, pilot_top, x, y)
        if lip_h > 0:                                  # square notch across the lip: no knife edges at its ends
            ang = math.degrees(math.atan2(y, x))
            lidp = lidp - Pos(x, y, zp + (lip_h + 0.5) / 2) * Rot(0, 0, ang) * Box(sc["boss_d"] + 2 * t, sc["boss_d"] + 0.3, lip_h + 0.5)
        lidp = lidp - cyl(sc["hole_d"] / 2, -1, zp + 1, x, y) - cyl(sc["cbore_d"] / 2, -0.01, sc["cbore_depth"], x, y)
        head = cyl(sc["cbore_d"] / 2 - 0.15, 0.05, sc["cbore_depth"], x, y)
        shank = cyl(sc["pilot_d"] / 2 - 0.01, sc["cbore_depth"] - 0.01, pilot_top - 0.05, x, y)
        sw = head + shank
        screws = sw if screws is None else screws + sw
    errors += _screw_checks(sc, mw, "lid screw boss")
    gasket = extrude(ring(spec, zp, 0.2, t - 0.1), amount=g["compressed_t"])
    for x, y in pos:
        gasket = gasket - cyl(sc["hole_d"] / 2 + 0.2, zp - 1, zp + 1, x, y)
    if g["compressed_t"] >= g["free_t"]:
        errors.append(f"lid gasket compressed {g['compressed_t']} mm is not thinner than free {g['free_t']} mm")
    notes.append(f"lid: {len(pos)} captive {sc.get('part', 'thread-forming screws for plastics')} into shell bosses "
                 f"Ø{sc['boss_d']} mm (pilot Ø{sc['pilot_d']} mm, engagement {sc['engagement']:.1f} mm); flat gasket "
                 f"{g['free_t']} -> {g['compressed_t']} mm ({g['material']}); straight pull, no side actions")
    return lidp, body, {"screws": screws, "gasket": gasket}, notes, errors


def door_in_lid(spec, lidp, zp, L):
    """A round battery door in the lid (any outline): flange in a recess, plug in a bore, flat gasket between the
    flange and the recess ceiling, held by captive screws through ears (retention 'screws') or by bayonet lugs
    under a collar (retention 'twist'). Optional coin slot. Both need a tool or a coin (coin-cell child safety)."""
    d = spec["lid"]["door"]
    mw = spec.get("dfm", {}).get("min_wall", 0.8)
    cx, cy = d.get("center", (0.0, 0.0))
    r, fl, ft, clr = d["radius"], d.get("flange", 1.2), d.get("flange_t", mw), d.get("clearance", 0.1)
    g = {"compressed_t": 0.2, "free_t": 0.3, "material": "silicone, die-cut", **d.get("gasket", {})}
    ret = d.get("retention", "screws")
    notes, errors, parts = [], [], {}
    if ret == "screws":
        sc = {"screw_d": 1.4, "pilot_d": 1.1, "hole_d": 1.6, "cbore_d": 2.4, "cbore_depth": 0.3, "boss_d": 3.2,
              "count": 2, "angles_deg": [0, 180], "boss_h": 3.0, **d.get("screws", {})}
        ear_r = sc.get("ear_r", max(sc["boss_d"] / 2 + 0.2, sc["cbore_d"] / 2 + mw + 0.05))
        neck0 = r + clr + mw                                # lid wall of min_wall kept between the bore and a pocket
        fl_min = math.hypot(neck0 + clr, ear_r) - r + 0.05  # the flange covers the corners of the ear necks
        if fl < fl_min:
            notes.append(f"door flange widened from {fl} to {fl_min:.2f} mm to carry the screw ears")
            fl = fl_min
    z_rec = ft + g["compressed_t"]                        # recess depth = flange + compressed gasket
    if L - z_rec < mw - 1e-6:
        errors.append(f"door: lid left above the recess is {L - z_rec:.2f} mm < {mw} mm; thicker lid or thinner flange")
    def lobe(rr, z0, z1, x, y, a, start):
        """Circle at the screw plus a radial neck from `start` (radius from the door axis): no knife-edge cusps."""
        rm = (start + math.hypot(x - cx, y - cy)) / 2
        ln = math.hypot(x - cx, y - cy) - start
        nx, ny = cx + rm * math.cos(math.radians(a)), cy + rm * math.sin(math.radians(a))
        return cyl(rr, z0, z1, x, y) + Pos(nx, ny, (z0 + z1) / 2) * Rot(0, 0, a) * Box(max(ln, 0.1), 2 * rr, z1 - z0)

    door = cyl(r + fl, 0, ft, cx, cy) + cyl(r, ft - 0.01, L, cx, cy)
    lidp = lidp - cyl(r + fl + clr, -1, z_rec, cx, cy) - cyl(r + clr, -1, L + 1, cx, cy)
    gasket = cyl(r + fl - 0.1, ft, z_rec, cx, cy) - cyl(r + 0.15, ft - 1, z_rec + 1, cx, cy)
    if ret == "screws":
        rs = sc.get("radius", neck0 + ear_r + 2 * clr)
        ear_top = L - mw                                    # blind ear pocket: a lid skin of min_wall stays above it
        if ear_top - sc["cbore_depth"] < mw - 1e-6:
            errors.append(f"door ears: {ear_top - sc['cbore_depth']:.2f} mm under the screw head < {mw} mm; "
                          f"lid >= {2 * mw + sc['cbore_depth']:.2f} mm thick, or a shallower counterbore")
        top = zp + sc["boss_h"] - mw
        screws = None
        for a in sc["angles_deg"][:sc["count"]]:
            x, y = cx + rs * math.cos(math.radians(a)), cy + rs * math.sin(math.radians(a))
            door = door + lobe(ear_r, 0, ear_top - 0.05, x, y, a, neck0 + clr)     # ear + neck: lobe of the door
            lidp = lidp - lobe(ear_r + clr, -1, ear_top, x, y, a, neck0)           # blind pocket for the lobe
            lidp = lidp + cyl(sc["boss_d"] / 2, zp - 0.01, zp + sc["boss_h"], x, y)  # boss up into the case
            lidp = lidp - cyl(sc["pilot_d"] / 2, ear_top - 0.01, top, x, y)
            door = door - cyl(sc["hole_d"] / 2, -1, ear_top + 1, x, y) - cyl(sc["cbore_d"] / 2, -0.01, sc["cbore_depth"], x, y)
            sw = cyl(sc["cbore_d"] / 2 - 0.15, 0.05, sc["cbore_depth"], x, y) + \
                cyl(sc["pilot_d"] / 2 - 0.01, sc["cbore_depth"] - 0.01, top - 0.05, x, y)
            screws = sw if screws is None else screws + sw
            gasket = gasket - lobe(ear_r + 0.2, ft - 1, z_rec + 1, x, y, a, neck0 + clr - 0.2)
        sc["engagement"] = top - ear_top
        errors += _screw_checks(sc, mw, "door screw boss")
        parts["door_screws"] = screws
        notes.append(f"battery door Ø{2 * r:.1f} mm: {sc['count']} captive screws at {sc['angles_deg'][:sc['count']]} deg "
                     f"(r {rs:.1f} mm) through ears into lid bosses; flat gasket {g['free_t']} -> {g['compressed_t']} mm; "
                     f"needs a screwdriver (coin-cell child safety: tool-secured); straight pull")
    elif ret == "twist":
        lg = {"count": 2, "width": 2.0, "overhang": 0.35, "height": mw, "angle_deg": 45.0, **d.get("lugs", {})}
        ov, hh = lg["overhang"], lg["height"]
        cw = lg.get("collar_wall", ov + 0.05 + mw + 0.05)    # wall behind the groove keeps min_wall
        ch = lg.get("collar_h", 0.1 + hh + 0.1 + mw)          # skin of min_wall above the groove
        rc_in = r + clr
        collar = cyl(rc_in + cw, zp - 0.01, zp + ch, cx, cy) - cyl(rc_in, zp - 1, zp + ch + 1, cx, cy)
        zc = zp + ch - mw - 0.05 - hh / 2
        collar = collar - cyl(rc_in + ov + 0.05, zc - hh / 2 - 0.05, zc + hh / 2 + 0.05, cx, cy)
        for k in range(lg["count"]):
            a = 2 * math.pi * k / lg["count"]
            xs, ys = cx + rc_in * math.cos(a), cy + rc_in * math.sin(a)
            collar = collar - Pos(xs, ys, (zp + zc) / 2) * Rot(0, 0, math.degrees(a)) * Box(2 * (ov + 0.05), lg["width"] + 0.3, zc - zp + hh)
        lidp = lidp + collar
        if cw - ov - 0.05 < mw - 1e-6:
            errors.append(f"door collar wall behind the lug groove is {cw - ov - 0.05:.2f} mm < {mw} mm")
        door = door + cyl(r, L - 0.01, zc + hh / 2, cx, cy)
        lock = math.radians(lg["angle_deg"])
        for k in range(lg["count"]):
            a = 2 * math.pi * k / lg["count"] + lock
            x, y = cx + (r + ov / 2) * math.cos(a), cy + (r + ov / 2) * math.sin(a)
            door = door + Pos(x, y, zc) * Rot(0, 0, math.degrees(a)) * Box(ov + 0.2, lg["width"], hh)
        notes.append(f"battery door Ø{2 * r:.1f} mm: {lg['count']} bayonet lugs turning {lg['angle_deg']} deg in a "
                     f"collar groove; lugs and groove are undercuts (side actions or a split core); flat gasket "
                     f"{g['free_t']} -> {g['compressed_t']} mm")
    else:
        raise SpecError(f"unknown door retention: {ret} (screws or twist)")
    zt = door.bounding_box().max.Z                       # top of the plug (or of the lugs)
    pw = d.get("plug_wall", mw + 0.1)
    if r - pw > 1.0:                                        # core the plug from inside: uniform walls, no sink
        core = cyl(r - pw, ft + mw * 0, zt + 1, cx, cy)
        core = Pos(0, 0, 0) * core
        core = core - cyl(r - pw, -1, ft, cx, cy)
        if d.get("coin_slot"):
            ln, wd, dp = d["coin_slot"]
            core = core - Pos(cx, cy, ft) * Box(ln + 2 * mw, wd + 2 * mw, 2 * (dp + mw))   # solid bar behind the slot
        door = door - core
        notes.append(f"door plug cored to a {pw} mm wall (flange {ft} mm)")
    if d.get("coin_slot"):
        ln, wd, dp = d["coin_slot"]
        door = door - Pos(cx, cy, dp / 2 - 0.01) * Box(ln, wd, dp)
        notes.append(f"coin slot {ln} x {wd} x {dp} mm in the door")
    parts["door"] = door
    parts["door_gasket"] = gasket
    return lidp, parts, notes, errors


# ---------------------------------------------------------------- build
def build(spec):
    H, t, draft = spec["height"], spec["wall"], spec.get("draft_deg", 1.0)
    lid = spec["lid"]
    L = lid["thickness"]
    joint = lid.get("joint", "adhesive_lip")
    clr = lid.get("clearance", 0.1)
    if joint == "adhesive_lip":
        gap = lid.get("adhesive_thickness", 0.1)
    elif joint == "screws":
        gap = lid.get("gasket", {}).get("compressed_t", 0.25)
    else:
        gap = 0.0
    zp = L                                   # parting plane (top of the lid flange)
    zb = zp + gap                            # bottom rim of the shell
    notes, errors = [], []

    # shell: drafted outer prism -> top fillet -> hollow with the bottom open
    env = extrude(outline(spec, zb), amount=H - zb, taper=draft)
    tf = spec.get("top_fillet", 0.0)
    if tf > 0:
        env = fillet(env.faces().sort_by(Axis.Z)[-1].edges(), tf)
    body = offset(env, amount=-t, openings=env.faces().sort_by(Axis.Z)[0])
    z_ceiling = H - t

    # lid: flange drafted toward its outer bottom (lid cavity pulls -Z), bottom fillet, then the joint
    flange = extrude(outline(spec, zp), amount=L, dir=(0, 0, -1), taper=draft)
    bf = min(spec.get("bottom_fillet", 0.0), 0.8 * L)
    if bf > 0:
        flange = fillet(flange.faces().sort_by(Axis.Z)[0].edges(), bf)
    lidp = flange
    extra = {}
    # the screws joint needs no lip (the screws locate the lid); a lip there is optional
    lip_h = lid.get("lip_height", 0.0 if joint == "screws" else 1.0)
    lip_w = lid.get("lip_width", 0.8)
    lip_in = t + clr
    if lip_h > 0:
        lidp = lidp + extrude(ring(spec, zp, lip_in, lip_in + lip_w), amount=lip_h, taper=draft)
    if joint == "adhesive_lip":
        a = gap
        extra["adhesive"] = extrude(ring(spec, zp, 0.2, t - 0.1), amount=a)
        notes.append(f"adhesive ring {a} mm (die-cut PSA) under the shell rim; seam sealed by adhesive")
    elif joint == "snap":
        n, w, ov, hh = lid.get("snap_count", 4), lid.get("snap_width", 3.0), lid.get("snap_overhang", 0.3), 0.6
        zc = zp + lip_h - hh / 2 - 0.1         # catch near the top of the lip: a taller ledge below it
        if ov + 0.05 >= t:
            errors.append(f"snap recess {ov + 0.05} mm would cut through the {t} mm wall")
        ledge = zc - hh / 2 - 0.05 - zb
        if ledge < spec.get("dfm", {}).get("min_wall", 0.8):
            errors.append(f"snap ledge under the recess is {ledge:.2f} mm; raise lip_height to at least "
                          f"{lip_h + spec.get('dfm', {}).get('min_wall', 0.8) - ledge:.2f} mm")
        for x, y, ang in side_points(spec, lip_in, n):
            bump = Pos(x, y, zc) * Rot(0, 0, ang) * Box(2 * ov, w, hh)
            lidp = lidp + bump
            body = body - (Pos(x, y, zc) * Rot(0, 0, ang) * Box(2 * (ov + 0.05 + clr), w + 0.2, hh + 0.1))
        notes.append(f"{n} snap bumps ({ov} mm overhang): undercuts on both parts; need lifters or a bump-off")
    elif joint == "screws":
        lidp, body, ex, nt, er = screws_joint(spec, lidp, body, env, zp, zb, z_ceiling, lip_in, lip_h)
        extra.update(ex)
        notes += nt
        errors += er
    elif joint == "twist":
        if spec["outline"]["type"] != "circle":
            raise SpecError("a twist joint turns the whole lid, so it needs a circle outline. For another outline, "
                            "use joint 'screws' or 'adhesive_lip' and put a round battery door in the lid: "
                            "lid.door with retention 'twist' or 'screws' (references/cad-pipeline.md)")
        n, w, ov, hh = lid.get("lug_count", 3), lid.get("lug_width", 2.0), lid.get("lug_overhang", 0.35), 0.6
        zc = zp + lip_h - hh / 2 - 0.1         # catch near the top of the lip: a taller ledge below it
        if ov + 0.05 >= t:
            errors.append(f"lug groove {ov + 0.05} mm would cut through the {t} mm wall")
        R = spec["outline"]["diameter"] / 2
        body = body - (cyl(R - t + ov + 0.05, zc - hh / 2 - 0.05, zc + hh / 2 + 0.05) - cyl(R - t - 0.5, zc - 1, zc + 1))
        lock = lid.get("lug_angle_deg", 30.0)
        for k in range(n):
            a = 2 * math.pi * k / n
            x, y = (R - lip_in) * math.cos(a + math.radians(lock)), (R - lip_in) * math.sin(a + math.radians(lock))
            lidp = lidp + Pos(x, y, zc) * Rot(0, 0, math.degrees(a) + lock) * Box(2 * ov, w, hh)
            xs, ys = (R - t) * math.cos(a), (R - t) * math.sin(a)       # axial entry slots, open to the rim
            body = body - Pos(xs, ys, (zb + zc) / 2) * Rot(0, 0, math.degrees(a)) * Box(2 * (ov + 0.05), w + 0.3, zc - zb + hh)
        o = lid.get("oring", {"cs": 0.6, "squeeze": 0.25})
        cs, sq = o["cs"], o.get("squeeze", 0.25)
        gw, gd = 1.3 * cs, cs * (1 - sq)
        mw = spec.get("dfm", {}).get("min_wall", 0.8)
        rc = R - t + 0.1 + gw / 2                  # groove under the rim, 0.1 mm from its inner edge
        if R - (rc + gw / 2) < mw + 0.1 or gd > L - mw:
            errors.append(f"O-ring groove {gw:.2f} x {gd:.2f} mm leaves less than {mw} mm of lid wall; needs a rim "
                          f">= {gw + 0.15 + mw:.2f} mm and a lid >= {gd + mw:.2f} mm, or a smaller cross-section")
        else:
            lidp = lidp - (cyl(rc + gw / 2, zp - gd, zp + 0.01) - cyl(rc - gw / 2, zp - gd - 1, zp + 1))
            wc = min(gw * 0.95, math.pi * cs * cs / 4 / gd)
            extra["oring"] = cyl(rc + wc / 2, zp - gd, zp) - cyl(rc - wc / 2, zp - gd - 1, zp + 1)
            notes.append(f"face-seal O-ring CS {cs} mm, groove {gw:.2f} x {gd:.2f} mm ({sq:.0%} squeeze), "
                         f"modelled compressed")
        notes.append(f"{n} twist lugs + groove: undercuts; need lifters, a collapsible core or an unscrewing tool")
    else:
        raise SpecError(f"unknown lid joint: {joint}")

    if lid.get("door"):
        lidp, dparts, nt, er = door_in_lid(spec, lidp, zp, L)
        extra.update(dparts)
        notes += nt
        errors += er

    # features
    windows = []
    zones = [("lip", None)]                   # thin features judged by min_rib instead of min_wall
    for f in spec.get("features", []):
        kind, part = f["type"], f.get("part", "body")
        x, y = (f.get("at") or [0, 0])[:2]
        if kind == "window":
            th = f["thickness"]
            sk = (Circle(f["diameter"] / 2) if f.get("shape", "circle") == "circle" else Rectangle(*f["size"]))
            z0 = z_ceiling - 0.6
            body = body - extrude(Plane.XY.offset(z0) * Pos(x, y) * sk, amount=(H - th) - z0, taper=draft)
            r = f["diameter"] / 2 if f.get("shape", "circle") == "circle" else max(f["size"]) / 2
            windows.append((x, y, r, th))
        elif kind == "sound_port":
            body = body - cyl(f["diameter"] / 2, z_ceiling - 1, H + 1, x, y)
            if f.get("seat_diameter"):
                z0 = z_ceiling - 0.6
                body = body - extrude(Plane.XY.offset(z0) * Pos(x, y) * Circle(f["seat_diameter"] / 2),
                                      amount=z_ceiling + f["seat_depth"] - z0, taper=draft)
                notes.append(f"membrane seat at ({x}, {y}): Ø{f['seat_diameter']} x {f['seat_depth']} mm")
        elif kind == "lanyard":
            # straight drilled segments (path), each exit perpendicular to its wall; joints get spheres
            path = f.get("path") or [f["from"], f["to"]]
            hd, bd, ext = f["diameter"], f["boss_diameter"], 2.0
            boss = hole = None
            for i in range(len(path) - 1):
                p0, p1 = list(path[i]), list(path[i + 1])
                dv = [p1[k] - p0[k] for k in range(3)]
                ln = math.sqrt(sum(c * c for c in dv))
                u = [c / ln for c in dv]
                e0 = ext if i == 0 else 0.0
                e1 = ext if i == len(path) - 2 else 0.0
                org = tuple(p0[k] - u[k] * e0 for k in range(3))
                pl = Plane(origin=org, z_dir=tuple(u))
                L2 = ln + e0 + e1
                mid = [org[k] + u[k] * L2 / 2 for k in range(3)]
                ang = math.degrees(math.atan2(u[1], u[0]))
                seg = Solid.make_cylinder(bd / 2, L2, pl)
                # fill from the tunnel axis up to the ceiling: a pocket above the boss would trap the core
                seg = seg + Pos(mid[0], mid[1], (mid[2] + H + 1) / 2) * Rot(0, 0, ang) * Box(L2, bd, H + 1 - mid[2])
                hs = Solid.make_cylinder(hd / 2, L2, pl)
                if 0 < i:
                    j = Pos(*p0)
                    seg = seg + j * Solid.make_sphere(bd / 2) + Pos(p0[0], p0[1], (p0[2] + H + 1) / 2) * Cylinder(bd / 2, H + 1 - p0[2])
                    hs = hs + j * Solid.make_sphere(hd / 2)
                boss = seg if boss is None else boss + seg
                hole = hs if hole is None else hole + hs
            body = (body + (boss & env)) - hole
            notes.append(f"lanyard tunnel Ø{hd} mm in {len(path) - 1} straight segment(s): one side action per "
                         f"direction, or split the tunnel at the parting line")
        elif kind == "boss":
            h, od, hole = f["height"], f["od"], f.get("hole", 0)
            zones.append(("boss", (part, x, y, od / 2 + 0.3)))
            if part == "body":
                b = extrude(down(z_ceiling + 0.3) * Pos(x, -y) * Circle(od / 2), amount=h + 0.3, taper=draft) & env
                body = body + b
                if hole:
                    zf = z_ceiling - h
                    body = body - extrude(Plane.XY.offset(zf - 0.01) * Pos(x, y) * Circle(hole / 2),
                                          amount=f.get("hole_depth", h * 0.8), taper=draft)
            else:
                lidp = lidp + extrude(Plane.XY.offset(zp - 0.01) * Pos(x, y) * Circle(od / 2), amount=h, taper=draft)
                if hole:
                    lidp = lidp - extrude(down(zp + h + 0.01) * Pos(x, -y) * Circle(hole / 2),
                                          amount=f.get("hole_depth", h * 0.8), taper=draft)
        elif kind == "rib":
            (x0, y0), (x1, y1) = f["from"], f["to"]
            ln, ang = math.hypot(x1 - x0, y1 - y0), math.degrees(math.atan2(y1 - y0, x1 - x0))
            cx, cy, th, h = (x0 + x1) / 2, (y0 + y1) / 2, f["thickness"], f["height"]
            zones.append(("rib", (part, x0, y0, x1, y1, th / 2 + 0.3)))
            if th > 0.6 * t + 1e-9:
                notes.append(f"rib {th} mm is more than 60% of the {t} mm wall: sink risk on the outside")
            if part == "body":
                body = body + (extrude(down(z_ceiling + 0.3) * Pos(cx, -cy) * Rot(0, 0, -ang) * Rectangle(ln, th),
                                       amount=h + 0.3, taper=draft) & env)
            else:
                lidp = lidp + extrude(Plane.XY.offset(zp - 0.01) * Pos(cx, cy) * Rot(0, 0, ang) * Rectangle(ln, th),
                                      amount=h, taper=draft)
        else:
            raise SpecError(f"unknown feature type: {kind}")

    parts = {k: v for k, v in {"body": body, "lid": lidp, **extra}.items() if v is not None}
    for k, v in parts.items():
        v.label = k.capitalize()
    keep = {}
    for k in spec.get("keepouts", []):
        c, sz = k["center"], k["size"]
        r = k.get("corner_radius", 0.0)
        if r > 0:
            keep[k["name"]] = extrude(Plane.XY.offset(c[2] - sz[2] / 2) * Pos(c[0], c[1]) * RectangleRounded(sz[0], sz[1], r),
                                      amount=sz[2])
        else:
            keep[k["name"]] = Pos(*c) * Box(*sz)
    env_all = env + flange
    lip_zone = (zp - 0.05, zp + lip_h + 0.05)
    zones[0] = ("lip", lip_zone)
    return dict(parts=parts, keepouts=keep, envelope=env_all, windows=windows, zones=zones, notes=notes, errors=errors,
                frame=dict(parting_z=zp, shell_rim_z=zb, ceiling_z=z_ceiling))


# ---------------------------------------------------------------- DFM check
def _intersector(shape):
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
    I = IntCurvesFace_ShapeIntersector()
    I.Load(shape.wrapped, 1e-6)
    return I


def _hits(I, p, d, tmin=0.0, tmax=1e3):
    from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
    I.Perform(gp_Lin(gp_Pnt(*p), gp_Dir(*d)), tmin, tmax)
    return sorted(I.WParameter(i) for i in range(1, I.NbPnt() + 1))


def _clusters(items, grid=2.0, top=8):
    """items: (x, y, z, area, value). Groups by a coarse grid; returns the largest groups."""
    g = {}
    for x, y, z, a, v in items:
        k = (round(x / grid), round(y / grid), round(z / grid))
        e = g.setdefault(k, [0.0, 0.0, 0.0, 0.0, v, v])
        e[0] += x * a
        e[1] += y * a
        e[2] += z * a
        e[3] += a
        e[4], e[5] = min(e[4], v), max(e[5], v)
    out = [{"near": [round(e[0] / e[3], 2), round(e[1] / e[3], 2), round(e[2] / e[3], 2)], "area_mm2": round(e[3], 3),
            "min": round(e[4], 3), "max": round(e[5], 3)} for e in g.values() if e[3] > 0]
    return sorted(out, key=lambda c: -c["area_mm2"])[:top]


def _in_zone(c, name, zones):
    for kind, z in zones:
        if kind == "lip" and name == "lid" and z[0] <= c[2] <= z[1]:
            return True
        if kind == "boss" and z[0] == name and math.hypot(c[0] - z[1], c[1] - z[2]) < z[3]:
            return True
        if kind == "rib" and z[0] == name:
            _, x0, y0, x1, y1, r = z
            dx, dy = x1 - x0, y1 - y0
            t = max(0.0, min(1.0, ((c[0] - x0) * dx + (c[1] - y0) * dy) / (dx * dx + dy * dy or 1)))
            if math.hypot(c[0] - x0 - t * dx, c[1] - y0 - t * dy) < r:
                return True
    return False


def _tilted(n, deg=60):
    """Four unit vectors at `deg` from -n (for the thick-section test at wall ends)."""
    import itertools
    m = [-x for x in n]
    a = [1.0, 0, 0] if abs(m[0]) < 0.9 else [0, 1.0, 0]
    u = [m[1] * a[2] - m[2] * a[1], m[2] * a[0] - m[0] * a[2], m[0] * a[1] - m[1] * a[0]]
    lu = math.sqrt(sum(x * x for x in u))
    u = [x / lu for x in u]
    v = [m[1] * u[2] - m[2] * u[1], m[2] * u[0] - m[0] * u[2], m[0] * u[1] - m[1] * u[0]]
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[c * m[i] + s_ * (su * u[i] + sv * v[i]) for i in range(3)] for su, sv in ((1, 0), (-1, 0), (0, 1), (0, -1))]


def dfm_check(shape, name, rules, windows=(), zones=(), max_samples=5000, lift=0.05):
    """Samples the surface (area-weighted), with exact outward normals from the B-rep faces.
    Thickness: a ray from just outside the face, inward; thickness = 2nd hit - 1st hit.
    Draft: angle between the face and the pull axis (Z). Undercut: an up-facing (down-facing) point whose
    ray toward +Z (-Z) hits the part again cannot be released by a straight pull."""
    import random
    faces = shape.faces()
    tris = []
    for fi, f in enumerate(faces):
        v, tr = f.tessellate(0.02, 0.3)
        V = [tuple(p) for p in v]
        for a, b, c in tr:
            A, B, C = V[a], V[b], V[c]
            u = [B[i] - A[i] for i in range(3)]
            w = [C[i] - A[i] for i in range(3)]
            n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
            ar = math.sqrt(sum(x * x for x in n)) / 2
            if ar > 1e-12:
                tris.append(([(A[i] + B[i] + C[i]) / 3 for i in range(3)], fi, ar))
    total = sum(t[2] for t in tris)
    rnd = random.Random(0)
    samples = tris if len(tris) <= max_samples else rnd.choices(tris, weights=[t[2] for t in tris], k=max_samples)
    per = total / len(samples) if len(tris) > max_samples else None
    I = _intersector(shape)
    sin_d = math.sin(math.radians(rules.get("min_draft_deg", 0.5) - 0.05))
    thin, thick, thin_win, undrafted, under = [], [], [], [], []
    tmin_all, tmax_all = 1e9, 0.0
    from OCP.BRep import BRep_Tool
    from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
    from OCP.gp import gp_Pnt
    surf = {}
    for c, fi, a in samples:
        area = per or a
        if fi not in surf:
            surf[fi] = BRep_Tool.Surface_s(faces[fi].wrapped)
        pr = GeomAPI_ProjectPointOnSurf(gp_Pnt(*c), surf[fi])
        if pr.NbPoints():                      # put the tessellation centroid back on the true surface
            P = pr.NearestPoint()
            c = [P.X(), P.Y(), P.Z()]
        n = list(faces[fi].normal_at(Vector(*c)))
        p = [c[i] + n[i] * lift for i in range(3)]
        w = _hits(I, p, [-x for x in n])
        if len(w) >= 2:
            th = w[1] - w[0]
            tmin_all, tmax_all = min(tmin_all, th), max(tmax_all, th)
            win = next((wd for wx, wy, wr, wd in windows if math.hypot(c[0] - wx, c[1] - wy) < wr + 0.3), None)
            if win is not None and th < rules["min_wall"]:
                if th < rules.get("min_window", 0.3):
                    thin_win.append((*c, area, th))
            elif th < rules["min_wall"] - 1e-3:
                if not (_in_zone(c, name, zones) and th >= rules.get("min_rib", 0.5) - 1e-3):
                    thin.append((*c, area, th))
            elif th > rules["max_wall"] + 1e-3:
                # a wall seen end-on (rim, flange edge) is long along its normal but thin: check tilted rays
                ends = []
                for dv in _tilted(n):
                    ww = _hits(I, p, dv)
                    ends.append(ww[1] - ww[0] if len(ww) >= 2 else 0.0)
                if min(ends) > rules["max_wall"]:
                    thick.append((*c, area, min(th, min(ends))))
        nz = n[2]
        if abs(nz) < sin_d:
            undrafted.append((*c, area, math.degrees(math.asin(min(1.0, abs(nz))))))
        else:
            d = (0, 0, 1) if nz > 0 else (0, 0, -1)
            q = [c[i] + n[i] * 0.01 + d[i] * 0.01 for i in range(3)]
            if _hits(I, q, d, 1e-3):
                under.append((*c, area, nz))
    s = lambda L: round(sum(x[3] for x in L), 3)
    return {
        "part": name, "surface_area_mm2": round(total, 1), "samples": len(samples),
        "wall_min_mm": round(tmin_all, 3), "wall_max_mm": round(tmax_all, 3),
        "thin_wall_area_mm2": s(thin), "thin_wall": _clusters(thin),
        "thin_window_area_mm2": s(thin_win), "thin_window": _clusters(thin_win),
        "thick_area_mm2": s(thick), "thick": _clusters(thick),
        "undrafted_area_mm2": s(undrafted), "undrafted": _clusters(undrafted),
        "undercut_area_mm2": s(under), "undercuts": _clusters(under),
    }


def keepout_check(parts, keepouts, envelope, clearance):
    out = []
    for name, k in keepouts.items():
        grown = offset(k, amount=clearance) if clearance > 0 else k
        hits = {}
        for pn, p in parts.items():
            if p is None:
                continue
            inter = grown & p                    # build123d returns None (or an empty shape) when nothing overlaps
            vol = inter.volume if inter is not None else 0.0
            if vol > 1e-4:
                hits[pn] = round(vol, 4)
        rest = k - envelope
        inside = rest is None or rest.volume < 1e-4
        out.append({"keepout": name, "clearance": clearance, "collides_with": hits, "inside_envelope": inside})
    return out


# ---------------------------------------------------------------- report
def write_reports(base, spec, res, dfm, keep):
    errs = list(res["errors"])
    warns = []
    for d in dfm:
        tiny = spec["dfm"].get("min_flag_area_mm2", 0.05)
        if 0 < d["thin_wall_area_mm2"] < tiny:
            warns.append(f"{d['part']}: sliver under {spec['dfm']['min_wall']} mm over only {d['thin_wall_area_mm2']} mm2 "
                         f"(min {d['wall_min_mm']} mm) near {[c['near'] for c in d['thin_wall'][:3]]}: inspect the "
                         f"intersection there")
        elif d["thin_wall_area_mm2"] > 0:
            errs.append(f"{d['part']}: wall below {spec['dfm']['min_wall']} mm over {d['thin_wall_area_mm2']} mm2 "
                        f"(min {d['wall_min_mm']} mm), near {[c['near'] for c in d['thin_wall'][:3]]}")
        if d["thin_window_area_mm2"] > 0:
            errs.append(f"{d['part']}: window thinner than {spec['dfm'].get('min_window', 0.3)} mm")
        if d["thick_area_mm2"] > 0:
            warns.append(f"{d['part']}: thick sections over {spec['dfm']['max_wall']} mm ({d['thick_area_mm2']} mm2, "
                         f"max {d['wall_max_mm']} mm): sink and cycle-time risk, near {[c['near'] for c in d['thick'][:3]]}")
        if d["undrafted_area_mm2"] > 0.05:
            warns.append(f"{d['part']}: {d['undrafted_area_mm2']} mm2 of faces with draft under "
                         f"{spec['dfm']['min_draft_deg']} deg, near {[c['near'] for c in d['undrafted'][:3]]}")
        if d["undercut_area_mm2"] > 0.05:
            warns.append(f"{d['part']}: undercuts over {d['undercut_area_mm2']} mm2 (each cluster needs a side action, "
                         f"lifter or redesign), near {[c['near'] for c in d['undercuts'][:4]]}")
    for k in keep:
        if k["collides_with"]:
            errs.append(f"keep-out {k['keepout']} (+{k['clearance']} mm) collides with {k['collides_with']}")
        if not k["inside_envelope"]:
            errs.append(f"keep-out {k['keepout']} sticks out of the enclosure envelope")
    rep = {"name": spec["name"], "ok": not errs, "errors": errs, "warnings": warns, "notes": res["notes"],
           "frame": res["frame"], "rules": spec["dfm"], "parts": dfm, "keepouts": keep}
    with open(base + "_dfm.json", "w") as f:
        json.dump(rep, f, indent=1)
    L = [f"# DFM check: {spec['name']}", "", f"Result: **{'PASS' if not errs else 'FAIL'}**, "
         f"{len(errs)} errors, {len(warns)} warnings. Automated geometric check; the molder's review is still required.",
         "", "| Part | Wall min (mm) | Wall max (mm) | Undrafted (mm²) | Undercut (mm²) |", "|---|---|---|---|---|"]
    for d in dfm:
        L.append(f"| {d['part']} | {d['wall_min_mm']} | {d['wall_max_mm']} | {d['undrafted_area_mm2']} | {d['undercut_area_mm2']} |")
    for title, items in (("Errors", errs), ("Warnings", warns), ("Design notes", res["notes"])):
        L += ["", f"## {title}", ""] + ([f"- {x}" for x in items] or ["- none"])
    with open(base + "_dfm.md", "w") as f:
        f.write("\n".join(L) + "\n")
    return rep


def main():
    ap = argparse.ArgumentParser(description="Parametric enclosure (STEP/STL/GLB) with a DFM check.")
    ap.add_argument("spec", help="enclosure JSON spec (see templates/enclosure.example.json)")
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--formats", default="step,stl,glb", help="comma list of step, stl, glb")
    ap.add_argument("--no-dfm", action="store_true", help="skip the DFM check")
    a = ap.parse_args()
    t0 = time.time()
    try:
        spec = json.load(open(a.spec))
        spec.setdefault("dfm", {"min_wall": 0.8, "max_wall": 3.0, "min_draft_deg": 0.5, "min_window": 0.3})
        res = build(spec)
    except (SpecError, KeyError, ValueError) as e:
        print(f"CAD error: {type(e).__name__}: {e}")
        sys.exit(2)
    os.makedirs(a.out, exist_ok=True)
    base = os.path.join(a.out, spec["name"])
    fm = set(a.formats.split(","))
    parts = res["parts"]
    for k, p in parts.items():                 # single parts first: a part inside a Compound has a parent
        if "step" in fm:
            export_step(p, f"{base}_{k}.step")
        if "stl" in fm:
            export_stl(p, f"{base}_{k}.stl", tolerance=0.01, angular_tolerance=0.2)
    asm = Compound(children=[copy.copy(p) for p in parts.values()])
    asm.label = spec["name"]
    if "step" in fm:
        export_step(asm, base + "_assembly.step")
    if "glb" in fm:
        export_gltf(asm, base + "_assembly.glb", unit=Unit.M, binary=True, linear_deflection=0.005,
                    angular_deflection=0.2)
    if res["keepouts"]:
        kc = []
        for n, k in res["keepouts"].items():
            k.label = n
            kc.append(k)
        kco = Compound(children=kc)
        kco.label = "Keepouts"
        if "step" in fm:
            export_step(kco, base + "_keepouts.step")
        if "glb" in fm:
            export_gltf(kco, base + "_keepouts.glb", unit=Unit.M, binary=True)
    t1 = time.time()
    rep = None
    if not a.no_dfm:
        rules = spec["dfm"]
        dfm = [dfm_check(p, k, rules, res["windows"] if k == "body" else (), res["zones"])
               for k, p in parts.items() if k in ("body", "lid", "door")]
        keep = keepout_check(parts, res["keepouts"], res["envelope"], rules.get("keepout_clearance", 0.2))
        rep = write_reports(base, spec, res, dfm, keep)
    vols = ", ".join(f"{k} {p.volume:.1f} mm3" for k, p in parts.items())
    status = "built" if rep is None else ("DFM PASS" if rep["ok"] else "DFM FAIL")
    nw = 0 if rep is None else len(rep["warnings"])
    print(f"CAD {status}: {spec['name']} ({vols}); {nw} DFM warnings; build+export {t1 - t0:.1f} s, "
          f"total {time.time() - t0:.1f} s; outputs in {a.out}")
    if rep:
        for e in rep["errors"]:
            print("CAD   error:", e)
        for w in rep["warnings"]:
            print("CAD   warning:", w)
    sys.exit(0 if rep is None or rep["ok"] else 1)


if __name__ == "__main__":
    main()
