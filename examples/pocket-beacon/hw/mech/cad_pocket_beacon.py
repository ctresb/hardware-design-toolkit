#!/usr/bin/env python3
"""Pocket Beacon enclosure: exact B-rep parts from hw/mech/enclosure.json, STEP/STL/GLB, DFM check.

Project script. It reuses the toolkit's DFM and keep-out checks (enclosure-engineer/scripts/cad_enclosure.py).
The generic generator's twist joint needs a circular outline. This product is a rounded square with a round,
coin-operated bayonet door in a bonded back plate, so the parts are built here.

Parts (one STEP each):
  shell      front + side walls, keyring tube, PCB standoffs, sound holes, membrane seat, button hole (PC or PC/ABS)
  plate      back plate, bonded to the shell; door recess and bore with 2 lug notches, PCB posts, lip (PC/ABS)
  door       coin-slot bayonet door, 2 lugs (PC/ABS); needs 2 side actions (lugs)
  door_gasket  flat silicone ring between the door flange and the plate, modelled compressed
  adhesive   die-cut PSA ring between the shell rim and the plate (IP67 seam)
  button     TPU 80A translucent, two-shot molded into the shell; nub on SW1
  membrane   ePTFE acoustic vent in the seat over the sound holes
  port_gasket  foam ring between the sounder port and the shell, modelled compressed

Run:  "$CAD_PY" cad_pocket_beacon.py hw/mech/enclosure.json --out hw/mech/cad
"""
import argparse
import copy
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.abspath(os.path.join(HERE, "../../../../skills/enclosure-engineer/scripts"))
sys.path.insert(0, TOOL)
import cad_enclosure as ce  # noqa: E402  (toolkit DFM + keep-out checks)
from build123d import (Box, Circle, Compound, Plane, Polygon, Pos, Rectangle, RectangleRounded, Rot,  # noqa: E402
                       SlotCenterToCenter, Solid, Unit, Axis, export_gltf, export_step, export_stl, extrude, fillet,
                       offset)


def keepout_check(parts, keepouts, envelope, clearance):
    """Same as the toolkit's keepout_check, but safe when an intersection is empty (build123d returns None)."""
    out = []
    for name, k in keepouts.items():
        grown = offset(k, amount=clearance) if clearance > 0 else k
        hits = {}
        for pn, p in parts.items():
            inter = grown & p
            vol = inter.volume if inter is not None else 0.0
            if vol > 1e-4:
                hits[pn] = round(vol, 4)
        d = k - envelope
        inside = d is None or d.volume < 1e-4
        out.append({"keepout": name, "clearance": clearance, "collides_with": hits, "inside_envelope": inside})
    return out


def cyl(r, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, z0) * Solid.make_cylinder(r, z1 - z0)


def cone(r_big, z0, z1, x=0.0, y=0.0, deg=1.0, big_at="bottom"):
    """Drafted pin: radius r_big at one end, smaller by tan(deg) * length at the other."""
    h = z1 - z0
    r_small = max(0.05, r_big - math.tan(math.radians(deg)) * h)
    r0, r1 = (r_big, r_small) if big_at == "bottom" else (r_small, r_big)
    return Pos(x, y, z0) * Solid.make_cone(r0, r1, h)


def rrect(half, r, z):
    return Plane.XY.offset(z) * RectangleRounded(2 * half, 2 * half, r)


def pcb_outline(p):
    h, r, s = p["half"], p["corner_radius"], p["chamfer_sum"]
    pts = [(-h, -h), (h, -h), (h, s - h), (s - h, h), (-h, h)]
    return fillet(Polygon(*pts, align=None).vertices(), r)


def build(S):
    W, R, H = S["outline"]["width"], S["outline"]["corner_radius"], S["height"]
    half = W / 2
    sh, pl, dr = S["shell"], S["plate"], S["door"]
    t, dft = sh["wall"], sh["draft_deg"]
    Tp = pl["thickness"]
    zb = Tp + sh["adhesive_thickness"]           # shell rim
    zc = H - t                                   # inner ceiling (flat front)
    pz0 = S["pcb"]["z_bottom"]
    pz1 = pz0 + S["pcb"]["thickness"]
    notes, errors = [], []

    # ---------------- shell: drafted prism, top fillet, uniform-wall hollow open at the rim
    env_s = extrude(rrect(half, R, zb), amount=H - zb, taper=dft)
    env_s = fillet(env_s.faces().sort_by(Axis.Z)[-1].edges(), sh["top_fillet"])
    shell = offset(env_s, amount=-t, openings=env_s.faces().sort_by(Axis.Z)[0])

    # keyring: vertical stadium through the whole body at the +x+y corner, with a tube wall around it
    k = S["keyring"]
    s0 = (half - R) * math.sqrt(2)               # corner arc centre, along the diagonal
    s_slot = s0 + R - k["outer_wall"] - k["slot_width"] / 2
    c = s_slot / math.sqrt(2)
    sep = k["slot_length"] - k["slot_width"]

    def stadium(width, z0, z1, taper=0.0):
        sk = Plane.XY.offset(z0) * Pos(c, c) * Rot(0, 0, -45) * SlotCenterToCenter(sep, width)
        if taper:                                   # drafted boss: grows toward the ceiling (the core pulls toward -Z)
            return extrude(sk, amount=z1 - z0, taper=-taper)
        sk = Plane.XY.offset(z0) * Pos(c, c) * Rot(0, 0, -45) * SlotCenterToCenter(sep, width)
        return extrude(sk, amount=z1 - z0)

    def tube_shape(grow, z0, z1):
        wb = k["slot_width"] + 2 * k["tube_wall"] + 2 * grow
        lb = sep + wb
        # corner fill: the half-space beyond the slot axis (s >= s_slot) merges the tube into the wall without fins
        ext = Pos(c + 5.0 / math.sqrt(2), c + 5.0 / math.sqrt(2), (z0 + z1) / 2) * Rot(0, 0, 45) * Box(10.0, 30.0, z1 - z0)
        return stadium(wb, z0, z1, taper=dft if grow == 0 else 0.0) + ext

    tube = tube_shape(0.0, zb, zc + 0.3) & env_s
    shell = shell + tube
    slot = stadium(k["slot_width"], -1, H + 1)
    notes.append(f"keyring slot {k['slot_width']} x {k['slot_length']} mm, vertical (straight pull, no side action); "
                 f"tube wall {k['tube_wall']} mm; outer wall {k['outer_wall']} mm")

    # PCB standoffs from the ceiling down to the PCB top
    po = S["posts"]
    for x, y in po["shell_points"]:
        zs = pz0 + S["pcb"]["thickness_max"] + 0.04            # 0.1 mm compressible pad on nominal boards
        shell = shell + (cone(po["shell_d"] / 2, zs, zc + 0.5, x, y, big_at="top") & env_s)

    # button hole (two-shot TPU) and the sound port: holes, membrane seat
    b = S["button"]
    bx, by = b["at"]
    shell = shell - cyl(b["diameter"] / 2, zc - 1, H + 1, bx, by)
    sp = S["sound_port"]
    sx, sy = sp["at"]
    o = sp["pitch"] / 2
    for dx, dy in ((-o, -o), (o, -o), (o, o), (-o, o))[: sp["holes"]]:
        shell = shell - cyl(sp["hole_d"] / 2, zc - 1, H + 1, sx + dx, sy + dy)
    shell = shell - cyl(sp["seat_d"] / 2, zc - 1, zc + sp["seat_depth"], sx, sy)
    shell = shell - slot

    # ---------------- plate: drafted toward its outer bottom, bottom fillet
    env_p = extrude(rrect(half, R, Tp), amount=Tp, dir=(0, 0, -1), taper=dft)
    env_p = fillet(env_p.faces().sort_by(Axis.Z)[0].edges(), pl["bottom_fillet"])
    plate = env_p
    lip = pl["lip"]
    lip_ring = extrude(rrect(half - lip["inset"], R - lip["inset"], Tp) -
                       rrect(half - lip["inset"] - lip["width"], R - lip["inset"] - lip["width"], Tp),
                       amount=sh["adhesive_thickness"] + lip["height"], taper=dft)
    lip_ring = lip_ring - Pos(half, half, Tp) * Box(2 * (half - 8.8), 2 * (half - 8.8), 4)   # no lip at the keyring corner
    plate = plate + lip_ring
    for x, y in po["plate_points"]:
        plate = plate + cone(po["plate_d"] / 2, Tp - 0.2, pz0 - S["pcb"].get("b_layers_t", 0.05) - 0.01, x, y)   # to the B-side mask
    dx0, dy0 = dr["center"]
    g, sc = dr["gasket"], dr["screws"]
    z_recess = dr["flange_t"] + g["compressed_t"]
    r_bore = dr["body_r"] + dr["bore_clearance"]
    ears = [(dx0 + sc["radius"] * math.cos(math.radians(a)), dy0 + sc["radius"] * math.sin(math.radians(a)), a)
            for a in sc["angles_deg"]]

    def door_plan(grow, z0, z1, lobes=True, neck=True):
        sol = cyl(dr["flange_r"] + grow, z0, z1, dx0, dy0)
        for x, y, a in ears:
            if neck:
                rm = (dr["flange_r"] - 0.5 + sc["radius"]) / 2
                ln = sc["radius"] - (dr["flange_r"] - 0.5)
                sol = sol + (Pos(dx0 + rm * math.cos(math.radians(a)), dy0 + rm * math.sin(math.radians(a)), (z0 + z1) / 2) *
                             Rot(0, 0, a) * Box(ln, sc["neck_w"] + 2 * grow, z1 - z0))
            if lobes:
                sol = sol + cyl(sc["lobe_r"] + grow, z0, z1, x, y)
        return sol

    rc = dr["recess_clearance"]
    plate = plate - door_plan(rc, -1, z_recess)                      # flange + necks + lobes recess
    plate = plate - cyl(r_bore, -1, Tp + 1, dx0, dy0)                # bore for the centring plug
    for x, y, a in ears:
        plate = plate - cyl(sc["lobe_r"] + rc, -1, Tp, x, y)         # lobe pockets through the plate ...
        plate = plate + cyl(sc["lobe_r"] + rc + sc["cap_margin"], Tp - 0.01, Tp + sc["cap_t"], x, y)   # ... closed by a cap
        plate = plate + cone(sc["boss_d"] / 2, Tp, sc["boss_top"], x, y)
        plate = plate - cyl(sc["pilot_d"] / 2, Tp - 0.01, sc["pilot_top"], x, y)   # blind pilot: no leak path
    plate = plate - slot
    ring_wall = Tp - z_recess
    if ring_wall < S["dfm"]["min_wall"]:
        errors.append(f"plate ring above the door recess is {ring_wall:.2f} mm")

    # ---------------- door: flange + necks + lobes (flange thickness), lobes full thickness, centring plug
    door = door_plan(0.0, 0, dr["flange_t"]) + cone(dr["body_r"], dr["flange_t"] - 0.01, Tp, dx0, dy0)
    for x, y, a in ears:
        door = door + cone(sc["lobe_r"], 0, Tp, x, y)
        door = door - cyl(sc["cbore_d"] / 2, -0.01, sc["cbore_depth"], x, y) - cyl(sc["hole_d"] / 2, -1, Tp + 1, x, y)
    gasket = cyl(g["r_out"], dr["flange_t"], z_recess, dx0, dy0) - cyl(g["r_in"], 0, Tp, dx0, dy0)
    screws = None
    for x, y, a in ears:
        head = cyl(sc["cbore_d"] / 2 - 0.15, 0.05, sc["cbore_depth"], x, y)
        shank = cyl(sc["pilot_d"] / 2, sc["cbore_depth"] - 0.01, sc["pilot_top"] - 0.05, x, y)   # thread engagement modelled at the pilot size
        sw = head + shank
        screws = sw if screws is None else screws + sw
    notes.append(f"door: 2 captive {sc['part']} at {sc['angles_deg']} deg, r {sc['radius']} mm; flat gasket "
                 f"{g['free_t']} -> {g['compressed_t']} mm, set by the ear-to-cap stop; blind pilot holes; "
                 f"all parts release in a straight pull")

    # ---------------- small parts
    adhesive = extrude(rrect(half - 0.15, R - 0.15, Tp) - rrect(half - t + 0.05, R - t + 0.05, Tp),
                       amount=sh["adhesive_thickness"]) - stadium(k["slot_width"] + 0.1, Tp - 1, Tp + 2)
    button = cyl(b["diameter"] / 2, zc, H - 0.02, bx, by)
    sw_top = pz1 + S["parts_max"]["SW1"]["size"][2]
    button = button + cyl(b["nub_diameter"] / 2, sw_top + b["nub_gap"], zc + 0.01, bx, by)
    membrane = cyl(sp["seat_d"] / 2 - 0.05, zc, zc + sp["membrane_t"], sx, sy)
    ls_top = pz1 + S["parts_max"]["LS1"]["size"][2]
    pg = sp["gasket"]
    port_gasket = cyl(pg["od"] / 2, ls_top, zc, sx, sy) - cyl(pg["id"] / 2, ls_top - 1, zc + 1, sx, sy)
    if zc - ls_top < 0.15:
        errors.append(f"port gasket compressed to {zc - ls_top:.2f} mm (sounder top {ls_top:.2f}, ceiling {zc:.2f})")

    parts = {"shell": shell, "plate": plate, "door": door, "door_gasket": gasket, "screws": screws, "adhesive": adhesive,
             "button": button, "membrane": membrane, "port_gasket": port_gasket}
    for kname, v in parts.items():
        v.label = kname

    # ---------------- keep-outs: board, sounder, switch, cell + holder (maximum sizes)
    keep = {}
    keep["PCB"] = extrude(Plane.XY.offset(pz0) * pcb_outline(S["pcb"]["outline"]), amount=S["pcb"]["thickness_max"])
    for ref in ("LS1", "SW1"):
        p = S["parts_max"][ref]
        x, y = p["at"]
        sx_, sy_, sz_ = p["size"]
        keep[ref] = Pos(x, y, pz1 + sz_ / 2) * Box(sx_, sy_, sz_)
    bt = S["parts_max"]["BT1"]
    bx_, by_ = bt["at"]
    keep["BT1 + cell"] = cyl(10.05, pz0 - bt["height"] + 0.9, pz0, bx_, by_) + Pos(bx_, by_, pz0 - bt["height"] / 2) * Box(23.3, 18.0, bt["height"])
    env = env_s + env_p
    return dict(parts=parts, keepouts=keep, envelope=env, notes=notes, errors=errors,
                frame=dict(rim_z=zb, ceiling_z=zc, pcb_z=[pz0, pz1], recess_z=z_recess, plate_t=Tp))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-dfm", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    S = json.load(open(a.spec))
    res = build(S)
    os.makedirs(a.out, exist_ok=True)
    base = os.path.join(a.out, S["name"])
    parts = res["parts"]
    for kname, p in parts.items():
        export_step(p, f"{base}_{kname}.step")
        export_stl(p, f"{base}_{kname}.stl", tolerance=0.01, angular_tolerance=0.2)
    asm = Compound(children=[copy.copy(p) for p in parts.values()])
    asm.label = S["name"]
    export_step(asm, base + "_assembly.step")
    export_gltf(asm, base + "_assembly.glb", unit=Unit.M, binary=True, linear_deflection=0.004, angular_deflection=0.15)
    kc = []
    for n, kp in res["keepouts"].items():
        kp.label = n
        kc.append(kp)
    kco = Compound(children=kc)
    kco.label = "Keepouts"
    export_step(kco, base + "_keepouts.step")
    export_gltf(kco, base + "_keepouts.glb", unit=Unit.M, binary=True)
    rep = None
    if not a.no_dfm:
        rules = S["dfm"]
        dfm = [ce.dfm_check(parts[n], n, rules, (), [("lip", (S["plate"]["thickness"] - 0.05, 99))]) for n in ("shell", "plate", "door")]
        keep = keepout_check({n: parts[n] for n in ("shell", "plate", "door", "button", "port_gasket")},
                                res["keepouts"], res["envelope"], rules["keepout_clearance"])
        spec_for_report = dict(S, name=S["name"])
        rep = ce.write_reports(base, spec_for_report, res, dfm, keep)
    dens = {"screws": 7.9, "shell": 1.20, "plate": 1.15, "door": 1.15, "button": 1.20, "door_gasket": 1.15, "adhesive": 1.0,
            "membrane": 0.5, "port_gasket": 0.3}
    mass = sum(p.volume * dens[n] / 1000 for n, p in parts.items())
    vols = ", ".join(f"{n} {p.volume:.1f} mm3" for n, p in parts.items())
    status = "built" if rep is None else ("DFM PASS" if rep["ok"] else "DFM FAIL")
    print(f"CAD {status}: {S['name']} ({vols}); plastic mass {mass:.2f} g; frame {res['frame']}; "
          f"{0 if rep is None else len(rep['warnings'])} warnings; {time.time() - t0:.1f} s")
    if rep:
        for e in rep["errors"]:
            print("CAD   error:", e)
        for w in rep["warnings"]:
            print("CAD   warning:", w)
    for e in res["errors"]:
        print("CAD   design error:", e)
    sys.exit(0 if (rep is None or rep["ok"]) and not res["errors"] else 1)


if __name__ == "__main__":
    main()
