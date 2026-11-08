"""Line-merge pass for projected drawings (pure Python, no Blender).

Two nearly coincident outlines (a shell rim and a lid rim at the seam, parts with 1° draft) are both partly
visible, so the projection leaves short "tick" chains lying on top of a longer line, and dots near it. This
pass removes every short chain whose segments all lie within `tol` of a segment of a different chain.
Arcs drawn as many short segments are one chain (segments sharing endpoints), so they are kept.

    clean(segs_by_class, tol, maxlen) -> (new_segs_by_class, removed_count)

segs_by_class: {"contour": [(x1, y1, x2, y2), ...], "detail": [...], ...} in any consistent unit.
"""
import math
from collections import defaultdict


def _dist_pt_seg(px, py, s):
    x1, y1, x2, y2 = s
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _seg_len(s):
    return math.hypot(s[2] - s[0], s[3] - s[1])


def clean(segs_by_class, tol=0.15, maxlen=1.0, ndigits=4):
    flat = [(cls, s) for cls, ss in segs_by_class.items() for s in (ss or [])]
    n = len(flat)
    if n == 0:
        return {k: list(v or []) for k, v in segs_by_class.items()}, 0
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    ends = defaultdict(list)
    for k, (_, s) in enumerate(flat):
        ends[(round(s[0], ndigits), round(s[1], ndigits))].append(k)
        ends[(round(s[2], ndigits), round(s[3], ndigits))].append(k)
    for ks in ends.values():
        for j in ks[1:]:
            a, b = find(ks[0]), find(j)
            if a != b:
                parent[a] = b
    comp = [find(k) for k in range(n)]
    clen = defaultdict(float)
    members = defaultdict(list)
    for k, (_, s) in enumerate(flat):
        clen[comp[k]] += _seg_len(s)
        members[comp[k]].append(k)

    cell = max(tol * 4, 1e-6)
    grid = defaultdict(list)
    for k, (_, s) in enumerate(flat):
        for gx in range(int(math.floor(min(s[0], s[2]) / cell)) - 1, int(math.floor(max(s[0], s[2]) / cell)) + 2):
            for gy in range(int(math.floor(min(s[1], s[3]) / cell)) - 1, int(math.floor(max(s[1], s[3]) / cell)) + 2):
                grid[(gx, gy)].append(k)

    def covered(k):
        """All sample points of segment k lie within tol of one segment of another, longer chain."""
        s = flat[k][1]
        pts = [(s[0] + (s[2] - s[0]) * t, s[1] + (s[3] - s[1]) * t) for t in (0.0, 0.5, 1.0)]
        cand = set()
        for px, py in pts:
            cand.update(grid[(int(math.floor(px / cell)), int(math.floor(py / cell)))])
        for j in cand:
            if comp[j] == comp[k] or clen[comp[j]] <= clen[comp[k]]:
                continue
            o = flat[j][1]
            if all(_dist_pt_seg(px, py, o) <= tol for px, py in pts):
                return True
        return False

    drop = set()
    for c, ks in members.items():
        if clen[c] > maxlen:
            continue
        if all(covered(k) for k in ks):
            drop.update(ks)
    out = defaultdict(list)
    for k, (cls, s) in enumerate(flat):
        if k not in drop:
            out[cls].append(s)
    res = {cls: out.get(cls, []) for cls in segs_by_class}
    return res, len(drop)
