"""Physically simulated solder fillets, pad by pad, from the real PCB pads (pads.json).

Physics. At sub-millimetre scale the Bond number is ~1e-3, so gravity is negligible and molten solder takes a
surface of constant mean curvature (Young–Laplace) holding a fixed volume:

    div( ∇z / sqrt(1 + |∇z|²) ) = -κ     on the free nodes of the pad
    z = 0                                at the pad edge (the contact line is pinned at the ENIG/copper edge)
    z = h_wet                            against the component termination (wetting climb)
    Σ z·dA = V                           V = paste area × stencil × metal fraction − solder under the body

κ (the Laplace pressure) is found by secant iteration until the volume matches; each κ is solved by red-black
Gauss–Seidel with over-relaxation, re-evaluating the non-linear coefficients every sweep. A small version of
what Surface Evolver does, with the same result for chip fillets. The base of each fillet follows the actual
board surface (ray cast), so solder sits flush on curved flex boards too.

    blender -b assembly.blend --python solder.py -- --pads hw/pcb/pads.json \
        --board main=MainBoardCollection --board flex=FlexCollection --save assembly_solder.blend

pads.json (written by pcb-engineer's export.py; kicad_pads.py in this folder calls the same exporter):
    { "<board name>": { "<ref>": { "layer": "F.Cu", "x": 104.6, "y": 96.4, "rot": 0.0,
          "pads": [ { "n": "1", "shape": "roundrect", "x": -0.32, "y": 0.0, "a": 0.0, "w": 0.46, "h": 0.40,
                      "paste": true, "cu": true }, ... ] } } }
    Pad x/y/a are in the footprint's own frame (KiCad, mm, y down, angle relative to the footprint).
    Optional per pad: "mask": false (no solder-mask opening: no fillet), "mask_margin": mm (negative = the
    mask overlaps the copper; the fillet shrinks to the opening).

Mask clashes. The contact line sits --edge-inset (0.03 mm) inside the copper so a zero-margin mask wall
never touches the fillet. If the validator still reports solder × mask on a pad, the pad and its mask
opening disagree at the source (fix the footprint in pcb-engineer); meanwhile solder the rest with
--exclude <ref> and enable parts one by one with --only.
    A pad with paste and no copper is a separate paste aperture (e.g. windowed thermal pad).

In the scene each component is an object (usually an empty from the KiCad GLB/VRML export) whose name is the
reference designator ("U1", "U1.001", ...), with the part meshes as children. Run it LAST in the build, after
every placement/fit step, so the fillets are conformed to the final board surface.
"""
import argparse
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import materials as MAT  # noqa: E402
import solder_geom as G  # noqa: E402

STENCIL = 0.10          # mm, 100 µm stencil
METAL = 0.50            # volume fraction of metal in SAC305 paste after reflow
STANDOFF = 0.02         # mm of solder left under the termination / body
LIFT = 0.0005           # mm: fillet top barely above the pad (no floating solder)
SKIP_CHILDREN = ("Solder", "Marking", "LED die", "Pin 1")
_cache = {}


def _solve(free, fixed, h, vol, iters=260):
    """Constant-mean-curvature surface with volume `vol` (mm³) over the `free` nodes (grid step h, mm)."""
    z = np.where(free, 0.0, fixed)
    fi = free[1:-1, 1:-1]
    ii, jj = np.indices(fi.shape)
    red = fi & ((ii + jj) % 2 == 0)
    blk = fi & ((ii + jj) % 2 == 1)
    area = h * h

    def sweep(kappa, n):
        for _ in range(n):
            for col in (red, blk):
                gx = np.zeros_like(z)
                gy = np.zeros_like(z)
                gx[1:-1, :] = (z[2:, :] - z[:-2, :]) / (2 * h)
                gy[:, 1:-1] = (z[:, 2:] - z[:, :-2]) / (2 * h)
                w = np.sqrt(1 + gx * gx + gy * gy)
                c = w[1:-1, 1:-1]
                cE, cW = 2 / (c + w[2:, 1:-1]), 2 / (c + w[:-2, 1:-1])
                cN, cS = 2 / (c + w[1:-1, 2:]), 2 / (c + w[1:-1, :-2])
                num = cE * z[2:, 1:-1] + cW * z[:-2, 1:-1] + cN * z[1:-1, 2:] + cS * z[1:-1, :-2] + kappa * area
                znew = num / (cE + cW + cN + cS)
                zc = z[1:-1, 1:-1]
                zc[col] = np.maximum(0.0, zc[col] + 1.7 * (znew[col] - zc[col]))
        return float(z[free].sum() * area)

    k0, v0 = 0.0, sweep(0.0, iters)
    if vol <= 0:
        return z
    k1 = 4.0 * (vol - v0) / max(1e-9, free.sum() * area * 0.05)
    v1 = sweep(k1, iters)
    for _ in range(10):                       # secant on κ until the volume matches within 1 %
        if abs(v1 - vol) < 0.01 * vol or v1 == v0:
            break
        k2 = k1 + (vol - v1) * (k1 - k0) / (v1 - v0)
        k0, v0 = k1, v1
        k1, v1 = k2, sweep(k2, iters)
    sweep(k1, iters // 2)
    return z


def _mesh_from_grid(name, P, Z, LU):
    """Closed solid: top = height field Z over points P (nu×nv×2), flat bottom. Inputs in mm, output × LU."""
    nu, nv = Z.shape
    top = np.concatenate([P, (Z + LIFT)[..., None]], -1).reshape(-1, 3)
    bot = np.concatenate([P, np.full((nu, nv, 1), 0.0001)], -1).reshape(-1, 3)
    verts = (np.concatenate([top, bot]) * LU).tolist()
    idx = np.arange(nu * nv).reshape(nu, nv)
    off = nu * nv
    a, b, c, d = idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()
    faces = np.stack([a, b, c, d], 1).tolist() + (np.stack([a, d, c, b], 1) + off).tolist()
    ring = list(idx[:, 0]) + list(idx[-1, 1:]) + list(idx[::-1, -1][1:]) + list(idx[0, ::-1][1:-1])
    for i in range(len(ring)):
        p, q = int(ring[i]), int(ring[(i + 1) % len(ring)])
        faces.append((q, p, p + off, q + off))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return me


def _local_units(e):
    """Local units of the component frame per mm (handles boards imported in metres and scaled up)."""
    return MAT.bu_per_mm() / max(e.matrix_world.to_scale().x, 1e-12)


def _local_bbox(e, LU):
    inv = e.matrix_world.inverted()
    pts = np.array([tuple(inv @ (c.matrix_world @ v.co)) for c in e.children_recursive
                    if c.type == "MESH" and not c.name.startswith(SKIP_CHILDREN) for v in c.data.vertices])
    if not len(pts):
        return None
    return pts.min(0) / LU, pts.max(0) / LU


def _corners(p):
    a = math.radians(p["a"])
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = u * p["w"] / 2, v * p["h"] / 2
        out.append((p["x"] + x * ca + y * sa, p["y"] - x * sa + y * ca))
    return out


FRAMES = [(sx, sy, sw) for sw in (False, True) for sx in (1, -1) for sy in (-1, 1)]


def _apply(f, xy):
    sx, sy, sw = f
    x, y = xy
    if sw:
        x, y = y, x
    return sx * x, sy * y


def _pick_frame(pads, lo, hi):
    """KiCad footprint frame (y down; B side mirrored) → the 3D model's local frame: choose the one of the 8
    symmetries that puts the pads under / next to the body. Decide with ALL pads, before excluding any."""
    best, bs = FRAMES[0], -1
    for f in FRAMES:
        s = 0
        for p in pads:
            for q in _corners(p) + [(p["x"], p["y"])]:
                x, y = _apply(f, q)
                s += (lo[0] - 0.35 <= x <= hi[0] + 0.35) and (lo[1] - 0.35 <= y <= hi[1] + 0.35)
        if s > bs:
            best, bs = f, s
    return best


def wet_cap(ref, H):
    """How high solder climbs the termination (mm), by part class."""
    pre = "".join(ch for ch in ref.split(".")[0] if ch.isalpha()).upper()
    if pre in ("C", "R", "L", "FB", "CM", "RM", "ANT", "F"):
        return min(0.6 * H, 0.32)            # chip passives: up to ~60 % of the end cap
    if pre in ("U", "IC", "Q"):
        return 0.09                          # QFN/LGA/SOT: short copper flank
    if pre in ("J", "P", "CN"):
        return 0.03                          # connectors: shallow tabs; the mating part passes over them
    return 0.12


def _board_gap(e, lo, hi, bvh, LU):
    """Distance from the bottom of the body to the board along the component's local -Z (mm)."""
    if bvh is None:
        return 0.0
    M = e.matrix_world
    down = (M.to_3x3() @ Vector((0, 0, -1))).normalized()
    bpm = MAT.bu_per_mm()
    best = None
    for fx, fy in ((0.5, 0.5), (0.2, 0.2), (0.8, 0.8), (0.2, 0.8), (0.8, 0.2)):
        p = M @ (Vector((lo[0] + fx * (hi[0] - lo[0]), lo[1] + fy * (hi[1] - lo[1]), lo[2] + 0.05)) * LU)
        loc, _n, _i, dist = bvh.ray_cast(p, down, 1.0 * bpm)
        if loc is not None:
            g = dist / bpm - 0.05
            best = g if best is None else min(best, g)
    return max(0.0, best) if best is not None and best < 0.4 else 0.0


def _pad_surface(e, P, lo, gap, bvh, LU):
    """Local z (mm) of the board surface under each node; flat lo.z − gap without a board mesh."""
    nu, nv = P.shape[:2]
    out = np.full((nu, nv), lo[2] - gap)
    if bvh is None:
        return out
    M = e.matrix_world
    Mi = M.inverted()
    down = (M.to_3x3() @ Vector((0, 0, -1))).normalized()
    bpm = MAT.bu_per_mm()
    for i in range(nu):
        for j in range(nv):
            pw = M @ (Vector((float(P[i, j, 0]), float(P[i, j, 1]), lo[2] + 0.1)) * LU)
            loc, _n, _f, _d = bvh.ray_cast(pw, down, 0.6 * bpm)
            if loc is not None:
                out[i, j] = (Mi @ loc).z / LU + 0.0003
    return out


def solder_component(e, ref, fp, col, mat, bvh=None, stats=None, inset=G.EDGE_INSET):
    LU = _local_units(e)
    bb = _local_bbox(e, LU)
    if bb is None:
        return 0
    lo, hi = bb
    gap = _board_gap(e, lo, hi, bvh, LU)
    H = hi[2] - lo[2] + gap
    pads = [p for p in fp["pads"] if p.get("cu", True)]
    paste = [p for p in fp["pads"] if p.get("paste") and not p.get("cu", True)]
    if not pads:
        return 0
    frame = _pick_frame(pads, lo, hi)                # frame from ALL copper pads, before excluding any
    pads = [G.inset_pad(p, inset) for p in pads if G.pad_wettable(p, ref)]   # no MP tabs, no mask-covered pads
    made = 0
    for k, p in enumerate(pads):
        area = p["w"] * p["h"]
        pa = area if p.get("paste") else 0.0
        for q in paste:                               # separate paste windows inside this pad
            if abs(q["x"] - p["x"]) <= p["w"] / 2 and abs(q["y"] - p["y"]) <= p["h"] / 2:
                pa += q["w"] * q["h"]
        if pa <= 0:
            continue
        c4 = [_apply(frame, q) for q in _corners(p)]
        o = np.array(c4[0])
        eu, ev = np.array(c4[1]) - o, np.array(c4[3]) - o
        Lu, Lv = np.linalg.norm(eu), np.linalg.norm(ev)
        hc = max(min(Lu, Lv) / 34, 0.006)
        nu, nv = max(6, int(math.ceil(Lu / hc)) + 1), max(6, int(math.ceil(Lv / hc)) + 1)
        U, V = np.meshgrid(np.linspace(0, 1, nu), np.linspace(0, 1, nv), indexing="ij")
        P = o + U[..., None] * eu + V[..., None] * ev
        body = (P[..., 0] > lo[0]) & (P[..., 0] < hi[0]) & (P[..., 1] > lo[1]) & (P[..., 1] < hi[1])
        exposed = (~body).sum() / body.size
        if exposed < 0.04:
            continue                                  # pad fully under the body (BGA/LGA): solder hidden
        a_under = area * (1 - exposed)
        vol = max(pa * STENCIL * METAL - a_under * STANDOFF, 0.12 * pa * STENCIL * METAL)
        ext = area * exposed / max(Lu, Lv)
        hw = min(wet_cap(ref, H), vol / max(1e-6, 0.4 * ext * max(Lu, Lv))) if body.any() else 0.0
        # a fillet holds at most ~half the prism (exposed area × wetting height); the rest stays under the
        # termination. A pad without a wall gets a cap of at most 1/4 of its short side.
        a_exp = area * exposed
        vol = min(vol, 0.5 * a_exp * ((hw + gap) if hw > 0 else 0.25 * min(Lu, Lv)))
        if ref.upper().startswith(("J", "CN")):
            vol = min(vol, a_exp * 0.02)
        free = ~body
        free[0, :] = free[-1, :] = free[:, 0] = free[:, -1] = False
        edge = np.minimum(np.minimum(U, 1 - U) * Lu, np.minimum(V, 1 - V) * Lv)
        ramp = np.clip(edge / max(1e-6, 1.2 * hw), 0, 1) if hw > 0 else 0
        ramp = ramp * ramp * (3 - 2 * ramp)           # meniscus, not a cliff, near the pad sides
        fixed = np.where(body, (hw + gap) * ramp, 0.0)
        h = min(Lu / (nu - 1), Lv / (nv - 1))
        key = (round(Lu, 3), round(Lv, 3), int(body.sum()), round(hw, 3), round(gap, 3), round(vol, 4), body.tobytes())
        if key not in _cache:
            Z = _solve(free, fixed, h, vol)
            _cache[key] = np.minimum(Z, max(hw + gap, 0.25 * min(Lu, Lv)) * 1.1)
        Z = _cache[key]
        cxy = P.reshape(-1, 2).mean(0)
        if cxy[0] < lo[0] - 1.0 or cxy[0] > hi[0] + 1.0 or cxy[1] < lo[1] - 1.0 or cxy[1] > hi[1] + 1.0:
            print(f"SOLDER skipped {e.name} pad {p.get('n') or k}: would land >1 mm from the body (wrong frame?)")
            if stats is not None:
                stats["skipped"] = stats.get("skipped", 0) + 1
            continue
        me = _mesh_from_grid(f"Solder {e.name} {p.get('n') or k}", P, Z, LU)
        me.materials.append(mat)
        base = _pad_surface(e, P, lo, gap, bvh, LU)
        bz = np.concatenate([base.ravel(), base.ravel()]) * LU
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        co[:, 2] += bz
        me.vertices.foreach_set("co", co.ravel())
        ob = bpy.data.objects.new(me.name, me)
        col.objects.link(ob)
        ob.parent = e
        ob.matrix_parent_inverse.identity()
        made += 1
    return made


def board_bvh(col, board_mesh):
    verts, tris = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in col.all_objects:
        if o.type == "MESH" and (board_mesh in o.name or board_mesh in o.data.name):
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            me.calc_loop_triangles()
            base = len(verts)
            verts += [tuple(ev.matrix_world @ v.co) for v in me.vertices]
            tris += [tuple(base + i for i in lt.vertices) for lt in me.loop_triangles]
            ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, tris, all_triangles=True) if tris else None


def solder_all(pads_json, boards, board_mesh="PCB", only=None, exclude=None, inset=G.EDGE_INSET):
    """boards: {board name in pads.json: Blender collection}. only/exclude: ref globs (per-part enable).
    Returns (fillets made, components soldered, stats)."""
    P = json.load(open(pads_json))
    mat = MAT.get("solder_sac305")
    total, comps, stats = 0, 0, {}
    for board, col in boards.items():
        if board not in P:
            raise SystemExit(f"SOLDER error: board '{board}' not in {pads_json} (has: {', '.join(P)})")
        for o in [o for o in col.all_objects if o.name.startswith("Solder ")]:
            bpy.data.objects.remove(o, do_unlink=True)
        refs = {}
        for o in col.all_objects:
            if o.children and o.name[:1].isalpha():
                refs.setdefault(o.name.split(".")[0], o)
        bvh = board_bvh(col, board_mesh)
        if bvh is None:
            print(f"SOLDER warning: no board mesh containing '{board_mesh}' in '{col.name}'; fillets sit on a flat plane")
        for ref in G.select_refs(list(P[board]), only, exclude):
            fp = P[board][ref]
            e = refs.get(ref)
            if e is None:
                continue
            n = solder_component(e, ref, fp, col, mat, bvh, stats, inset)
            total += n
            comps += n > 0
    return total, comps, stats


def main(argv):
    ap = argparse.ArgumentParser(prog="solder.py", description="Physically simulated solder fillets from pads.json.")
    ap.add_argument("--pads", required=True, help="pads.json (see module docstring)")
    ap.add_argument("--board", action="append", required=True, help="'<board in pads.json>=<Blender collection>'")
    ap.add_argument("--board-mesh", default="PCB", help="substring of the board substrate mesh name")
    ap.add_argument("--stencil", type=float, default=STENCIL, help="stencil thickness, mm (default 0.10)")
    ap.add_argument("--bu-per-mm", type=float, help="Blender units per mm (default: from scene units)")
    ap.add_argument("--only", action="append", default=[], help="solder only these refs (glob, repeatable): 'C*'")
    ap.add_argument("--exclude", action="append", default=[], help="never solder these refs (glob, repeatable)")
    ap.add_argument("--edge-inset", type=float, default=G.EDGE_INSET,
                    help="mm the contact line sits inside the copper edge (default 0.03; clears zero-margin masks)")
    ap.add_argument("--save", help="save the result here")
    a = ap.parse_args(argv)
    globals()["STENCIL"] = a.stencil
    MAT.configure(a.bu_per_mm)
    boards = {}
    for spec in a.board:
        name, _, cname = spec.partition("=")
        if cname not in bpy.data.collections:
            raise SystemExit(f"SOLDER error: collection '{cname}' not found")
        boards[name] = bpy.data.collections[cname]
    total, comps, stats = solder_all(a.pads, boards, a.board_mesh, a.only or None, a.exclude or None, a.edge_inset)
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save), copy=True)
    print(f"SOLDER {total} fillets on {comps} components; skipped {stats.get('skipped', 0)}"
          + (f"; saved {a.save}" if a.save else ""))
    return 0 if total else 1


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    rc = main(argv)
    if bpy.app.background:
        sys.exit(rc)
