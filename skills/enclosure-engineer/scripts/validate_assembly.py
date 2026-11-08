"""Assembly validator: the gate that runs before every render, drawing or export.

It checks every renderable mesh of an assembly for:

1. Interpenetration between parts. An edge of part A that crosses the surface of part B by more than
   `tol` from both of its ends fails. Touching (face on face, edge resting on a face) does not fail.
2. Broken meshes. Non-finite coordinates and edges shared by more than 2 faces fail. Zero-area faces,
   loose vertices and open borders on parts that must be closed are reported as warnings.

Meshes of one component (body, pins, solder, marking) are not tested against each other. A component
is the nearest ancestor with the custom property `hdt_component` (legacy `vh_component` is still read); if there is none, the nearest EMPTY
ancestor below the root whose name does not match `--container-regex`; if there is none, the object.

Fast path: numpy arrays via foreach_get, one BVH per object built from Blender's own tessellation
(loop_triangles; a naive fan triangulation of concave n-gons invents faces and false hits), AABB
sweep to find candidate pairs, and ray casts only for edges inside the other part's box.

Validate in the frozen, unposed frame of the assembly. With --root, the root's transform is set to
identity while validating and restored afterwards: a rotated pose changes floating-point precision on
coplanar contacts and can create or hide hits.

Usage (headless):
    blender -b scene.blend --python validate_assembly.py -- --root Assembly \
        --json hw/validation/assembly.json --txt hw/validation/assembly.txt

As a module inside another Blender script:
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("va", "<path>/validate_assembly.py")
    va = importlib.util.module_from_spec(spec); spec.loader.exec_module(va)
    rep = va.validate(root=bpy.data.objects["Assembly"], tol=0.02)
    va.print_report(rep)

Exit code: 0 when the assembly passes, 1 when it fails, 2 on a usage error.
Tested with Blender 5.2 (numpy bundled; no other dependency).
"""
import argparse
import json
import re
import sys
import time

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

GRAZING_COS = 0.087          # |n·d| below this (edge within ~5° of the face plane) is a grazing contact
DEFAULT_CONTAINERS = r"^(Node|Root|Scene|Assembly|Group|=>)"


# ---------------------------------------------------------------- selection and grouping
COMPONENT_KEYS = ("hdt_component", "vh_component")   # vh_component: legacy name, accepted until v0.2


def _is_component(o):
    return any(k in o.keys() for k in COMPONENT_KEYS)


def _component_of(o, root, container_re):
    g = o.parent
    while g is not None and g is not root:
        if _is_component(g):
            return g.name
        g = g.parent
    if _is_component(o):
        return o.name
    g = o.parent
    while g is not None and g is not root:
        if g.type == 'EMPTY' and not container_re.match(g.name):
            return g.name
        g = g.parent
    return o.name


def collect(root=None, collections=None):
    """Renderable, visible meshes under `root` and/or in the named collections (all if both empty)."""
    objs = []
    if root is not None:
        objs += list(root.children_recursive)
    for cn in collections or []:
        c = bpy.data.collections.get(cn)
        if c is None:
            raise KeyError(f"collection not found: {cn}")
        objs += list(c.all_objects)
    if root is None and not collections:
        objs = list(bpy.context.scene.objects)
    seen, out = set(), []
    vl = bpy.context.view_layer
    for o in objs:
        if o.name in seen or o.type != 'MESH' or o.hide_render:
            continue
        try:
            if o.hide_get(view_layer=vl) and not o.visible_get(view_layer=vl):
                continue
        except Exception:
            pass
        seen.add(o.name)
        out.append(o)
    return out


# ---------------------------------------------------------------- mesh arrays
def _mesh_arrays(o, dg):
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        nv, ne, npo = len(me.vertices), len(me.edges), len(me.polygons)
        co = np.empty(nv * 3, np.float64)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ev.matrix_world, dtype=np.float64)
        co = co @ M[:3, :3].T + M[:3, 3]
        ed = np.empty(ne * 2, np.int64)
        me.edges.foreach_get("vertices", ed)
        ed = ed.reshape(-1, 2)
        area = np.empty(npo, np.float64)
        me.polygons.foreach_get("area", area)
        le = np.empty(len(me.loops), np.int64)
        me.loops.foreach_get("edge_index", le)
        lv = np.empty(len(me.loops), np.int64)
        me.loops.foreach_get("vertex_index", lv)
        me.calc_loop_triangles()
        tri = np.empty(len(me.loop_triangles) * 3, np.int64)
        me.loop_triangles.foreach_get("vertices", tri)
        tri = tri.reshape(-1, 3)
        scale = float(np.cbrt(abs(np.linalg.det(M[:3, :3])))) or 1.0
        return co, ed, area * scale * scale, lv, le, tri
    finally:
        ev.to_mesh_clear()


_PARITY_DIRS = [Vector(v).normalized() for v in ((1, 0.0013, 0.0007), (-0.0011, 1, 0.0017), (0.0009, -0.0012, 1))]


def _parity_inside(bvh, p):
    """Inside a closed mesh? Majority of three ray-parity tests (independent of normals)."""
    votes = 0
    for d in _PARITY_DIRS:
        n, start = 0, p.copy()
        for _ in range(500):
            loc, _nrm, _i, _dist = bvh.ray_cast(start, d)
            if loc is None:
                break
            n += 1
            start = loc + d * 1e-5
        votes += n % 2
    return votes >= 2


def _really_inside(bvh, v0, d, s_hit, L, tol, closed=False):
    """Confirm a hit: the middle of the stretch that is supposedly inside must be away from the other
    surface (an edge lying on a floor that passes over the seam of two touching parts is contact) and,
    when the other part is a closed mesh, really inside it (an edge that only touches its rim is not)."""
    mid = v0 + d * (s_hit / 2 if s_hit < L - s_hit else (s_hit + L) / 2)
    loc, _n, _i, dist = bvh.find_nearest(mid, 1.0)
    if loc is not None and dist <= 0.5 * tol:
        return False
    return _parity_inside(bvh, mid) if closed else True


def _is_closed(co, tri):
    """Closed (watertight) after welding coincident vertices: every triangle edge is shared by 2 triangles.
    CAD exports (one mesh patch per B-rep face) are closed only once welded."""
    if not len(tri):
        return False
    _, uid = np.unique(np.round(co, 5), axis=0, return_inverse=True)
    uid = uid.ravel()
    t = uid[tri]
    e = np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
    e = e[e[:, 0] != e[:, 1]]
    _, cnt = np.unique(e, axis=0, return_counts=True)
    return bool(len(cnt)) and bool((cnt == 2).all())


# ---------------------------------------------------------------- validation
def validate(root=None, collections=None, tol=0.02, closed_regex=None, container_regex=DEFAULT_CONTAINERS,
             max_report=40, unpose_root=True):
    """tol: penetration depth (scene units, normally mm) from which an interpenetration fails."""
    t0 = time.time()
    saved = None
    if root is not None and unpose_root:
        saved = root.matrix_world.copy()
        root.matrix_world = Matrix.Identity(4)
        bpy.context.view_layer.update()
    try:
        return _validate(root, collections, tol, closed_regex, re.compile(container_regex), max_report, t0)
    finally:
        if saved is not None:
            root.matrix_world = saved
            bpy.context.view_layer.update()


def _validate(root, collections, tol, closed_regex, container_re, max_report, t0):
    dg = bpy.context.evaluated_depsgraph_get()
    objs = collect(root, collections)
    closed_re = re.compile(closed_regex) if closed_regex else None
    data, mesh_issues, fatal = {}, [], False
    for o in objs:
        co, ed, area, lv, le, tri = _mesh_arrays(o, dg)
        if not len(co):
            continue
        iss = {}
        bad = ~np.isfinite(co).all(1)
        if bad.any():
            iss["non-finite coordinates"] = int(bad.sum())
            fatal = True
        tiny = int((area < 1e-10).sum())
        if tiny:
            iss["zero-area faces"] = tiny
        cnt = np.bincount(le, minlength=len(ed)) if len(le) else np.zeros(len(ed), np.int64)
        nm = int((cnt > 2).sum())
        if nm:
            iss["edges with more than 2 faces"] = nm
            fatal = True
        if closed_re and closed_re.search(o.name):
            b = int((cnt == 1).sum())
            if b:
                iss["border edges on a part that must be closed"] = b
        used = np.zeros(len(co), bool)
        if len(ed):
            used[ed.ravel()] = True
        if len(lv):
            used[lv] = True
        loose = int((~used).sum())
        if loose:
            iss["loose vertices"] = loose
        if iss:
            mesh_issues.append({"object": o.name, "issues": iss})
        if not len(tri) or bad.any():
            continue
        bvh = BVHTree.FromPolygons(co.tolist(), tri.tolist(), all_triangles=True, epsilon=0.0)
        data[o] = (co, ed, co.min(0), co.max(0), bvh, _component_of(o, root, container_re), _is_closed(co, tri))

    # candidate pairs by AABB (sweep along x)
    items = sorted(data.items(), key=lambda kv: kv[1][2][0])
    pairs = []
    for i, (a, da) in enumerate(items):
        for b, db in items[i + 1:]:
            if db[2][0] > da[3][0] + tol:
                break
            if (db[2] > da[3] + tol).any() or (da[2] > db[3] + tol).any():
                continue
            if da[5] == db[5]:
                continue
            pairs.append((a, b))

    hits = []
    for a, b in pairs:
        depth, n, where, detail = 0.0, 0, None, None
        for s, t in ((a, b), (b, a)):
            co, ed = data[s][0], data[s][1]
            if not len(ed):
                continue
            lo, hi = data[t][2] - tol, data[t][3] + tol
            p0, p1 = co[ed[:, 0]], co[ed[:, 1]]
            sel = np.nonzero(((np.maximum(p0, p1) >= lo) & (np.minimum(p0, p1) <= hi)).all(1))[0]
            bvh = data[t][4]
            for k in sel:
                v0, v1 = Vector(p0[k]), Vector(p1[k])
                d = v1 - v0
                L = d.length
                if L < 2 * tol:
                    if L > 1e-9 and data[t][6]:
                        mid = (v0 + v1) * 0.5
                        if _parity_inside(bvh, mid):
                            loc_n, _nrm, _idx, dist_n = bvh.find_nearest(mid)
                            if loc_n is not None and dist_n > tol:
                                n += 1
                                if dist_n > depth:
                                    depth = dist_n
                                    where = [round(c, 3) for c in mid]
                                    detail = {"edge_of": s.name, "from": [round(c, 3) for c in v0],
                                              "to": [round(c, 3) for c in v1], "face_normal": [0.0, 0.0, 1.0]}
                    continue
                d /= L
                travelled, start = 0.0, v0
                while travelled < L:
                    loc, nrm, _i, dist = bvh.ray_cast(start, d, L - travelled)
                    if loc is None:
                        break
                    s_hit = travelled + dist
                    pen = min(s_hit, L - s_hit)
                    if pen > tol and abs(nrm.dot(d)) > GRAZING_COS and _really_inside(bvh, v0, d, s_hit, L, tol, data[t][6]):
                        n += 1
                        if pen > depth:
                            depth = pen
                            where = [round(c, 3) for c in loc]
                            detail = {"edge_of": s.name, "from": [round(c, 3) for c in v0],
                                      "to": [round(c, 3) for c in v1], "face_normal": [round(c, 2) for c in nrm]}
                    travelled = s_hit + 1e-6
                    start = v0 + d * travelled
        if n == 0:
            for s, t in ((a, b), (b, a)):
                co_s = data[s][0]
                if len(co_s) and data[t][6]:
                    v_test = Vector(co_s[0])
                    if _parity_inside(data[t][4], v_test):
                        loc_n, nrm_n, _idx, dist_n = data[t][4].find_nearest(v_test)
                        pen_c = float(dist_n) if dist_n is not None else tol * 2.0
                        if pen_c > tol:
                            n = 1
                            depth = pen_c
                            where = [round(c, 3) for c in v_test]
                            detail = {"edge_of": s.name, "from": where, "to": where,
                                      "face_normal": [round(c, 2) for c in (nrm_n or Vector((0, 0, 1)))]}
                            break
        if n:
            hits.append({"depth": round(depth, 4), "edges": n, "a": a.name, "b": b.name,
                         "component_a": data[a][5], "component_b": data[b][5], "near": where, "detail": detail})
    hits.sort(key=lambda h: -h["depth"])
    return {
        "ok": not hits and not fatal,
        "tolerance": tol,
        "objects": len(objs),
        "pairs_tested": len(pairs),
        "n_interpenetrations": len(hits),
        "interpenetrations": hits[:max_report],
        "n_mesh_warnings": len(mesh_issues),
        "mesh_issues": mesh_issues[:max_report],
        "seconds": round(time.time() - t0, 2),
    }


def report_text(rep, tag="VALIDATE"):
    lines = [f"{tag} {'PASS' if rep['ok'] else 'FAIL'}: {rep['objects']} objects, {rep['pairs_tested']} pairs, "
             f"{rep['n_interpenetrations']} interpenetrations, {rep['n_mesh_warnings']} meshes with issues, "
             f"tol {rep['tolerance']} mm, {rep['seconds']} s"]
    for h in rep["interpenetrations"]:
        d = h["detail"]
        lines.append(f"{tag}   {h['depth']:.3f} mm deep ({h['edges']} edges): {h['a']} x {h['b']} near {h['near']}; "
                     f"edge of {d['edge_of']} {d['from']} -> {d['to']}, face normal {d['face_normal']}")
    for m in rep["mesh_issues"]:
        lines.append(f"{tag}   mesh {m['object']}: " + ", ".join(f"{k} {v}" for k, v in m["issues"].items()))
    return "\n".join(lines)


def print_report(rep, tag="VALIDATE"):
    print(report_text(rep, tag))


# ---------------------------------------------------------------- CLI
def _argv():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def main():
    ap = argparse.ArgumentParser(prog="validate_assembly.py",
                                 description="Interpenetration and mesh-quality gate for a Blender assembly.")
    ap.add_argument("--root", help="root object of the assembly (all descendants are tested)")
    ap.add_argument("--collection", action="append", default=[], help="collection to test (repeatable)")
    ap.add_argument("--tol", type=float, default=0.02, help="failing penetration depth in scene units (default 0.02 mm)")
    ap.add_argument("--closed-regex", help="regex of object names that must be closed (watertight) meshes")
    ap.add_argument("--container-regex", default=DEFAULT_CONTAINERS,
                    help="EMPTY names that are containers, not components (default: %(default)s)")
    ap.add_argument("--keep-pose", action="store_true", help="validate in the current pose of the root")
    ap.add_argument("--json", help="write the full report as JSON")
    ap.add_argument("--txt", help="write the text report")
    a = ap.parse_args(_argv())
    root = None
    if a.root:
        root = bpy.data.objects.get(a.root)
        if root is None:
            print(f"VALIDATE error: root object not found: {a.root}")
            sys.exit(2)
    rep = validate(root=root, collections=a.collection, tol=a.tol, closed_regex=a.closed_regex,
                   container_regex=a.container_regex, unpose_root=not a.keep_pose)
    txt = report_text(rep)
    print(txt)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(rep, f, indent=1)
    if a.txt:
        with open(a.txt, "w") as f:
            f.write(txt + "\n")
    sys.exit(0 if rep["ok"] else 1)


if __name__ == "__main__":
    main()
