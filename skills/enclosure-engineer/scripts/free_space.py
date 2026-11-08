"""Free-space map of an assembly: flood fill + distance field. It tells each movable part how far it can go.

Method:
1. Rasterize the surfaces of all FIXED parts (shell, lid, boards...) into a voxel grid. Triangles are
   sampled barycentrically at half the voxel size, in chunks, so large faces leave no gaps.
2. Dilate once to seal diagonal leaks, then flood-fill the air from a seed inside the cavity, like a
   liquid poured in. What the liquid cannot reach is solid. If the cavity air reaches the grid border,
   the shell has an unwanted opening: a LEAK. That is a design finding, not a numerical detail.
3. Euclidean distance transform over the cavity air: every point knows its distance to the nearest
   solid, and the gradient points away from collisions. Near surfaces (< 3 voxels) the distance is
   exact, from a BVH of the fixed triangles. The sign there comes from the grid gradient, so it does
   not depend on mesh normals, which are often inverted in imported vendor models.
4. fit_rigid() moves each movable part as a rigid block along the escape direction of its worst point
   until every sampled surface point has at least `clearance` of free space.

Backends: cupy (GPU) > scipy > numpy only. Blender bundles numpy but not scipy. Without scipy the
flood fill runs as a vectorized breadth-first search and the distance comes from the BVH everywhere
(exact, slower per point). Install scipy into Blender's Python for large grids (toolchain-setup).

Usage (headless):
    blender -b assembly.blend --python free_space.py -- --fixed-collection Shell --fixed-collection Boards \
        --movable Battery --clearance 0.05 --save hw/mech/assembly_fitted.blend --json hw/mech/fit.json

As a module:
    fs = <load module>;  F = fs.FreeSpace(fixed_objs, h=0.05)
    d, g = F.dist_grad(points)          # mm to nearest solid (negative = inside), escape direction
    fs.fit_rigid(F, [bpy.data.objects["Battery"]], clearance=0.05)

Tested with Blender 5.2, numpy-only and scipy backends.
"""
import argparse
import json
import math
import sys
import time

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

try:
    import cupy as xp
    import cupyx.scipy.ndimage as xnd
    BACKEND = "cupy"
except Exception:
    xp, xnd = np, None
    try:
        import scipy.ndimage as _snd
        BACKEND = "scipy"
    except Exception:
        _snd = None
        BACKEND = "numpy"
try:
    import scipy.ndimage as snd
except Exception:
    snd = None


# ---------------------------------------------------------------- geometry sampling
def world_triangles(objs, M_inv=None):
    """Triangles (N,3,3) of the evaluated meshes, in world space or in the frame M_inv."""
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in objs:
        if o.type != 'MESH':
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        try:
            me.calc_loop_triangles()
            nv, nt = len(me.vertices), len(me.loop_triangles)
            if not nt:
                continue
            co = np.empty(nv * 3, np.float64)
            me.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            M = np.array(ev.matrix_world, dtype=np.float64)
            if M_inv is not None:
                M = np.array(M_inv, dtype=np.float64) @ M
            co = co @ M[:3, :3].T + M[:3, 3]
            tri = np.empty(nt * 3, np.int64)
            me.loop_triangles.foreach_get("vertices", tri)
            out.append(co[tri.reshape(-1, 3)])
        finally:
            ev.to_mesh_clear()
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


def surface_points(objs, step=0.05, cap=20000, M_inv=None):
    """Points spread over the faces, not only the vertices: a large face that crosses another part
    between its vertices is caught too."""
    T = world_triangles(objs, M_inv)
    if not len(T):
        return np.zeros((0, 3))
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    L = np.maximum(np.maximum(np.linalg.norm(B - A, axis=1), np.linalg.norm(C - A, axis=1)), np.linalg.norm(C - B, axis=1))
    n = np.clip(np.ceil(L / step), 1, 200).astype(np.int64)
    out = [A, B, C, (A + B + C) / 3]
    for k in np.unique(n):
        if k < 2:
            continue
        idx = np.nonzero(n == k)[0]
        i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1), indexing="ij")
        m = (i + j) <= k
        u, v = i[m] / k, j[m] / k
        a, b, c = A[idx, None], B[idx, None], C[idx, None]
        out.append((a + u[None, :, None] * (b - a) + v[None, :, None] * (c - a)).reshape(-1, 3))
    P = np.unique(np.round(np.concatenate(out), 4), axis=0)
    if len(P) > cap:
        P = P[np.random.default_rng(0).choice(len(P), cap, replace=False)]
    return P


def rasterize_triangles(T, step, o, h, shape):
    """Mark every voxel touched by a triangle (barycentric sampling at <= step, in chunks)."""
    surf = np.zeros(shape, dtype=bool)
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    L = np.maximum(np.maximum(np.linalg.norm(B - A, axis=1), np.linalg.norm(C - A, axis=1)), np.linalg.norm(C - B, axis=1))
    n = np.clip(np.ceil(L / step), 1, 4000).astype(np.int64)
    lim = np.array(shape) - 1
    count = 0

    def mark(P):
        nonlocal count
        ijk = np.rint((P - o) / h).astype(np.int32)
        ok = ((ijk >= 0) & (ijk <= lim)).all(1)
        ijk = ijk[ok]
        surf[ijk[:, 0], ijk[:, 1], ijk[:, 2]] = True
        count += len(P)

    CH = int(2e7)
    for k in np.unique(n):
        idx = np.nonzero(n == k)[0]
        i, j = np.meshgrid(np.arange(k + 1, dtype=np.float32), np.arange(k + 1, dtype=np.float32), indexing="ij")
        m = (i + j) <= k
        u, v = i[m] / k, j[m] / k
        chunk = max(1, CH // max(1, len(u)))
        for s0 in range(0, len(idx), chunk):
            sl = idx[s0:s0 + chunk]
            aa, bb, cc = (X[sl, None].astype(np.float32) for X in (A, B, C))
            for u0 in range(0, len(u), CH):
                uu, vv = u[u0:u0 + CH], v[u0:u0 + CH]
                mark((aa + uu[None, :, None] * (bb - aa) + vv[None, :, None] * (cc - aa)).reshape(-1, 3))
    return surf, count


# ---------------------------------------------------------------- numpy fallbacks
def _dilate_np(m):
    out = m.copy()
    for ax in range(3):
        sl_a = [slice(None)] * 3
        sl_b = [slice(None)] * 3
        sl_a[ax], sl_b[ax] = slice(1, None), slice(None, -1)
        out[tuple(sl_a)] |= m[tuple(sl_b)]
        out[tuple(sl_b)] |= m[tuple(sl_a)]
    return out


def _flood_np(free, seeds):
    """6-connected flood fill over `free` from flat seed indices; vectorized BFS, O(voxels)."""
    shape = free.shape
    flat = free.ravel()
    seen = np.zeros(flat.shape, bool)
    seeds = np.asarray(seeds, np.int64)
    seeds = seeds[flat[seeds]]
    seen[seeds] = True
    front = seeds
    strides = np.array([shape[1] * shape[2], shape[2], 1], np.int64)
    while len(front):
        ijk = np.stack(np.unravel_index(front, shape), 1)
        nxt = []
        for ax in range(3):
            for dlt in (-1, 1):
                c = ijk[:, ax] + dlt
                ok = (c >= 0) & (c < shape[ax])
                nb = front[ok] + dlt * strides[ax]
                nb = nb[flat[nb] & ~seen[nb]]
                seen[nb] = True
                nxt.append(nb)
        front = np.unique(np.concatenate(nxt)) if nxt else np.zeros(0, np.int64)
    return seen.reshape(shape)


def _border_flat(shape):
    m = np.zeros(shape, bool)
    m[0], m[-1], m[:, 0], m[:, -1], m[:, :, 0], m[:, :, -1] = True, True, True, True, True, True
    return np.flatnonzero(m)


# ---------------------------------------------------------------- the map
class FreeSpace:
    def __init__(self, fixed_objs, h=None, seed=None, bounds=None, margin=1.0, max_voxels=None, M_inv=None,
                 tag="FREESPACE"):
        t0 = time.time()
        T = world_triangles(fixed_objs, M_inv)
        if not len(T):
            raise ValueError("no fixed triangles")
        if bounds is None:
            lo, hi = T.reshape(-1, 3).min(0) - margin, T.reshape(-1, 3).max(0) + margin
        else:
            lo, hi = np.array([b[0] for b in bounds], float), np.array([b[1] for b in bounds], float)
        if max_voxels is None:
            max_voxels = 3e8 if BACKEND == "cupy" else (6e7 if BACKEND == "scipy" else 8e6)
        vol = float(np.prod(hi - lo))
        h_min = (vol / max_voxels) ** (1 / 3)
        if h is None or h < h_min:
            if h is not None:
                print(f"{tag} h={h} needs too many voxels for the {BACKEND} backend; using h={h_min:.3f}")
            h = h_min
        self.h, self.o = float(h), lo
        self.shape = tuple(int(math.ceil((hi[k] - lo[k]) / h)) + 1 for k in range(3))
        surf, npts = rasterize_triangles(T, 0.5 * h, self.o, h, self.shape)
        t1 = time.time()
        if BACKEND == "cupy":
            solid = xnd.binary_dilation(xp.asarray(surf), iterations=1).get()
        elif BACKEND == "scipy":
            solid = _snd.binary_dilation(surf, iterations=1)
        else:
            solid = _dilate_np(surf)
        del surf
        free = ~solid
        outside = _flood_np(free, _border_flat(self.shape)) if BACKEND == "numpy" else None
        if BACKEND != "numpy":
            lab, nlab = (_snd.label(free) if BACKEND == "scipy" else
                         tuple(x.get() if hasattr(x, "get") else x for x in xnd.label(xp.asarray(free))))
            border = np.unique(lab.ravel()[_border_flat(self.shape)])
            outside = np.isin(lab, border[border > 0])
        if seed is not None:
            s = np.clip(np.rint((np.array(seed) - self.o) / h).astype(int), 0, np.array(self.shape) - 1)
            if not free[tuple(s)]:
                raise RuntimeError(f"seed {tuple(seed)} is inside a solid")
            if BACKEND == "numpy":
                air = outside if outside[tuple(s)] else _flood_np(free, [np.ravel_multi_index(tuple(s), self.shape)])
            else:
                air = lab == lab[tuple(s)]
        else:
            cav = free & ~outside
            if cav.any():
                if BACKEND == "numpy":
                    ijk = np.argwhere(cav)
                    c = np.array(self.shape) / 2
                    first = ijk[np.argmin(((ijk - c) ** 2).sum(1))]
                    air = _flood_np(free, [np.ravel_multi_index(tuple(first), self.shape)])
                else:
                    ids, counts = np.unique(lab[cav], return_counts=True)
                    air = lab == ids[np.argmax(counts)]
            else:
                air = outside
        self.leak = bool((air & outside).any())
        self.air = air
        self.air_volume = float(air.sum()) * h ** 3
        self.dist_grid = None
        how = "BVH only (no scipy/cupy)"
        if BACKEND == "cupy":
            try:
                d = xnd.distance_transform_edt(xp.asarray(air), float64_distances=False)
                self.dist_grid = (d * h - h).get().astype(np.float32)
                del d
                xp.get_default_memory_pool().free_all_blocks()
                how = "GPU EDT"
            except Exception:
                xp.get_default_memory_pool().free_all_blocks()
                if snd is not None:
                    self.dist_grid = (snd.distance_transform_edt(air) * h - h).astype(np.float32)
                    how = "CPU EDT (GPU out of memory)"
        elif BACKEND == "scipy":
            self.dist_grid = (_snd.distance_transform_edt(air) * h - h).astype(np.float32)
            how = "CPU EDT"
        if self.dist_grid is not None and snd is None:
            self.dist_grid = None                       # cupy without scipy: no CPU interpolation, use the BVH
            how = "BVH only (no scipy)"
        V = T.reshape(-1, 3)
        self.bvh = BVHTree.FromPolygons(V.tolist(), np.arange(len(V)).reshape(-1, 3).tolist(), all_triangles=True)
        print(f"{tag} grid {self.shape} h={h:.3f} mm, {len(T)} triangles, {npts / 1e6:.1f} M samples "
              f"(raster {t1 - t0:.1f} s); cavity air {self.air_volume:.1f} mm3; leak: {'YES' if self.leak else 'no'}; "
              f"backend {BACKEND}, distance by {how}; {time.time() - t0:.1f} s")

    # -------------------------------------------------------------- queries
    def _air_at(self, pts):
        ijk = np.clip(np.rint((pts - self.o) / self.h).astype(int), 0, np.array(self.shape) - 1)
        return self.air[ijk[:, 0], ijk[:, 1], ijk[:, 2]]

    def _parity_inside(self, p):
        """Inside a closed fixed solid? Majority of 3 ray-parity tests."""
        votes = 0
        for d in (Vector((1, 0.0013, 0.0007)), Vector((-0.0011, 1, 0.0017)), Vector((0.0009, -0.0012, 1))):
            d.normalize()
            n, start = 0, p.copy()
            for _ in range(200):
                loc, _nrm, _i, dist = self.bvh.ray_cast(start, d)
                if loc is None:
                    break
                n += 1
                start = loc + d * 1e-5
            votes += n % 2
        return votes >= 2

    def dist_grad(self, pts):
        """Distance (mm, negative inside a solid or outside the cavity) and unit escape direction."""
        pts = np.asarray(pts, np.float64).reshape(-1, 3)
        h = self.h
        d = np.full(len(pts), np.inf)
        g = np.zeros_like(pts)
        if self.dist_grid is not None:
            q = ((pts - self.o) / h).T
            d = snd.map_coordinates(self.dist_grid, q, order=1, mode="nearest").astype(np.float64)
            far = d >= 3 * h
            for k in range(3):
                dd = np.zeros(3)
                dd[k] = h
                g[:, k] = (snd.map_coordinates(self.dist_grid, ((pts + dd - self.o) / h).T, order=1, mode="nearest")
                           - snd.map_coordinates(self.dist_grid, ((pts - dd - self.o) / h).T, order=1, mode="nearest"))
            near = np.nonzero(~far)[0]
        else:
            near = np.arange(len(pts))
        air = self._air_at(pts)
        for i in near:
            p = Vector(pts[i])
            loc, nrm, _f, dist = self.bvh.find_nearest(p)
            if loc is None:
                continue
            v = np.array(p - loc)
            if self.dist_grid is not None:
                gi = g[i]
                if d[i] > h:
                    sgn = 1.0
                elif np.linalg.norm(gi) > 1e-9 and dist > 1e-6:
                    sgn = 1.0 if float(v @ gi) >= 0 else -1.0
                else:
                    sgn = 1.0 if v @ np.array(nrm) >= 0 else -1.0
            else:
                if not air[i] and dist > 1.5 * h:
                    sgn = -1.0                    # deep in a solid or outside the cavity
                else:
                    sgn = -1.0 if self._parity_inside(p) else 1.0
            d[i] = sgn * dist
            g[i] = v * sgn if dist > 1e-6 else np.array(nrm)
        n = np.linalg.norm(g, axis=1, keepdims=True)
        return d, g / np.maximum(n, 1e-9)

    def dist(self, pts):
        return self.dist_grad(pts)[0]


# ---------------------------------------------------------------- fitting
def _meshes_of(o):
    return [o] if o.type == 'MESH' else [c for c in o.children_recursive if c.type == 'MESH']


def fit_rigid(F, movables, clearance=0.03, iters=12, gain=1.1, max_step=0.5, step=0.05, lock=None, tag="FIT"):
    """Translate each movable object (with its children) until all its surface points have >= clearance.
    lock: e.g. (0, 0, 1) allows motion only along z; None = free.
    Returns {name: {"worst_before", "worst_after", "moved"}}."""
    res = {}
    for o in movables:
        ms = _meshes_of(o)
        start = o.matrix_world.translation.copy()
        worst0 = None
        for it in range(iters):
            pts = surface_points(ms, step=step, cap=4000)
            if not len(pts):
                break
            dd, gg = F.dist_grad(pts)
            need = clearance - dd
            k = int(np.argmax(need))
            if worst0 is None:
                worst0 = float(need[k])
            if need[k] <= 0.004:
                break
            mv = gg[k] * need[k] * gain
            if lock is not None:
                ax = np.array(lock, float)
                ax /= np.linalg.norm(ax)
                along = float(mv @ ax)
                mv = ax * (along if abs(along) > 1e-6 else float(need[k]) * gain)
            L = np.linalg.norm(mv)
            if L > max_step:
                mv *= max_step / L
            o.matrix_world.translation += Vector(mv.tolist())
            bpy.context.view_layer.update()
            print(f"{tag} {o.name} iteration {it + 1}: worst intrusion {need[k]:.3f} mm, moved {np.round(mv, 3).tolist()}")
        pts = surface_points(ms, step=step, cap=4000)
        after = float((clearance - F.dist(pts)).max()) if len(pts) else 0.0
        res[o.name] = {"worst_before": round(worst0 or 0.0, 4), "worst_after": round(after, 4),
                       "moved": [round(c, 4) for c in (o.matrix_world.translation - start)]}
    return res


# ---------------------------------------------------------------- CLI
def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="free_space.py", description="Flood-fill free-space map and rigid fit.")
    ap.add_argument("--fixed-collection", action="append", default=[], help="collection of fixed parts (repeatable)")
    ap.add_argument("--fixed", action="append", default=[], help="fixed object name (repeatable)")
    ap.add_argument("--movable", action="append", default=[], help="object to fit, with its children (repeatable)")
    ap.add_argument("--clearance", type=float, default=0.03, help="required free space around movables (mm)")
    ap.add_argument("--h", type=float, help="voxel size (mm); default: finest that fits the backend's budget")
    ap.add_argument("--seed", type=float, nargs=3, help="a point in the cavity air (default: automatic)")
    ap.add_argument("--lock", type=float, nargs=3, help="allow motion only along this axis, e.g. 0 0 1")
    ap.add_argument("--save", help="save the fitted .blend here")
    ap.add_argument("--json", help="write the result as JSON")
    a = ap.parse_args(argv)
    fixed = []
    for cn in a.fixed_collection:
        c = bpy.data.collections.get(cn)
        if c is None:
            print(f"FREESPACE error: collection not found: {cn}")
            sys.exit(2)
        fixed += [o for o in c.all_objects if o.type == 'MESH' and not o.hide_render]
    for n in a.fixed:
        o = bpy.data.objects.get(n)
        if o is None:
            print(f"FREESPACE error: object not found: {n}")
            sys.exit(2)
        fixed += _meshes_of(o)
    movables = [bpy.data.objects[n] for n in a.movable]
    mov_meshes = {m.name for o in movables for m in _meshes_of(o)}
    fixed = [o for o in dict.fromkeys(fixed) if o.name not in mov_meshes]
    F = FreeSpace(fixed, h=a.h, seed=a.seed)
    res = fit_rigid(F, movables, clearance=a.clearance, lock=a.lock)
    ok = all(r["worst_after"] <= 0.004 for r in res.values()) and not F.leak
    out = {"ok": ok, "leak": F.leak, "air_volume_mm3": round(F.air_volume, 2), "h": F.h, "backend": BACKEND, "parts": res}
    if a.json:
        with open(a.json, "w") as f:
            json.dump(out, f, indent=1)
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=a.save)
    print(f"FREESPACE {'PASS' if ok else 'FAIL'}: leak {'YES' if F.leak else 'no'}, "
          + "; ".join(f"{n} worst {r['worst_before']:.3f} -> {r['worst_after']:.3f} mm, moved {r['moved']}" for n, r in res.items()))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
