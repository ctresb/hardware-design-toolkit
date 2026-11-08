#!/usr/bin/env python3
"""Project workaround for the ortho sheet: remove short stroke segments that lie on top of (within TOL of) a
different, non-adjacent stroke segment. These are tangent-point "ticks" where two nearly coincident outlines
(shell rim and back-plate rim at the seam) are both partly visible. Arcs drawn as chains of short segments are
kept: neighbours that share an endpoint are ignored when testing a segment.

usage: clean_ortho.py in.svg out.svg [--tol 0.3] [--maxlen 2.0]   (sheet units = mm on the sheet)
"""
import argparse
import math
import re
import sys
from collections import defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("dst")
ap.add_argument("--tol", type=float, default=0.3)
ap.add_argument("--maxlen", type=float, default=2.0)
ap.add_argument("--spur", type=float, default=0.4, help="dead-end stubs shorter than this, branching off a line, are removed")
ap.add_argument("--dot", type=float, default=0.6, help="chains shorter than this are dots")
ap.add_argument("--dottol", type=float, default=0.8, help="a dot this close to a longer chain is removed")
a = ap.parse_args()

svg = open(a.src, encoding="utf-8").read()
PATH = re.compile(r'<path d="([^"]*)"([^>]*)/>')
SEG = re.compile(r"M([-\d.]+) ([-\d.]+)L([-\d.]+) ([-\d.]+)")

paths = []
for m in PATH.finditer(svg):
    d, attrs = m.group(1), m.group(2)
    if "stroke=" not in attrs or "fill=\"#" in attrs.replace('fill="none"', ""):
        continue
    segs = [tuple(map(float, s.groups())) for s in SEG.finditer(d)]
    if segs and len(SEG.sub("", d).strip()) == 0:
        paths.append((m, segs))

allsegs = [(pi, si, s) for pi, (_, segs) in enumerate(paths) for si, s in enumerate(segs)]
CELL = 1.0
grid = defaultdict(list)
for k, (_, _, (x1, y1, x2, y2)) in enumerate(allsegs):
    for gx in range(int(min(x1, x2) // CELL) - 1, int(max(x1, x2) // CELL) + 2):
        for gy in range(int(min(y1, y2) // CELL) - 1, int(max(y1, y2) // CELL) + 2):
            grid[(gx, gy)].append(k)


def dist_pt_seg(px, py, s):
    x1, y1, x2, y2 = s
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def shares_end(s, o, eps=1e-3):
    ends_s = ((s[0], s[1]), (s[2], s[3]))
    ends_o = ((o[0], o[1]), (o[2], o[3]))
    return any(math.hypot(p[0] - q[0], p[1] - q[1]) < eps for p in ends_s for q in ends_o)


parent = list(range(len(allsegs)))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i
ends = defaultdict(list)
for k, (_, _, s0) in enumerate(allsegs):
    ends[(round(s0[0], 2), round(s0[1], 2))].append(k)
    ends[(round(s0[2], 2), round(s0[3], 2))].append(k)
for ks in ends.values():
    for j in ks[1:]:
        ra, rb = find(ks[0]), find(j)
        if ra != rb:
            parent[ra] = rb
comp = [find(k) for k in range(len(allsegs))]
clen = defaultdict(float)
for k, (_, _, s0) in enumerate(allsegs):
    clen[comp[k]] += math.hypot(s0[2] - s0[0], s0[3] - s0[1])

drop = set()
for k, (pi, si, s) in enumerate(allsegs):
    L = clen[comp[k]]                     # length of the whole chain this segment belongs to
    if L > a.maxlen:
        continue
    mx, my = (s[0] + s[2]) / 2, (s[1] + s[3]) / 2
    pts = ((s[0], s[1]), (mx, my), (s[2], s[3]))
    near = set()
    for px, py in pts:
        cx, cy = int(px // CELL), int(py // CELL)
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1):
                near |= set(grid[(cx + ddx, cy + ddy)])
    others = [allsegs[j][2] for j in near
              if j != k and j not in drop and comp[j] != comp[k] and clen[comp[j]] > L]
    # every sample point of this short chain sits on some longer, different chain
    hit = bool(others) and all(min(dist_pt_seg(px, py, o) for o in others) < (a.dottol if L < a.dot else a.tol) for px, py in pts)
    if hit:
        drop.add(k)

# spurs: a short segment with one free end whose other end sits on a junction (3+ segments)
for _ in range(3):
    deg = defaultdict(int)
    for k, (_, _, s0) in enumerate(allsegs):
        if k in drop:
            continue
        deg[(round(s0[0], 2), round(s0[1], 2))] += 1
        deg[(round(s0[2], 2), round(s0[3], 2))] += 1
    changed = False
    for k, (_, _, s0) in enumerate(allsegs):
        if k in drop or math.hypot(s0[2] - s0[0], s0[3] - s0[1]) >= a.spur:
            continue
        e1, e2 = (round(s0[0], 2), round(s0[1], 2)), (round(s0[2], 2), round(s0[3], 2))
        if (deg[e1] == 1 and deg[e2] >= 3) or (deg[e2] == 1 and deg[e1] >= 3):
            drop.add(k)
            changed = True
    if not changed:
        break

out, last = [], 0
removed = 0
by_path = defaultdict(set)
for k in drop:
    by_path[allsegs[k][0]].add(allsegs[k][1])
for pi, (m, segs) in enumerate(paths):
    keep = [s for si, s in enumerate(segs) if si not in by_path[pi]]
    removed += len(segs) - len(keep)
    d = "".join(f"M{x1:.2f} {y1:.2f}L{x2:.2f} {y2:.2f}" for x1, y1, x2, y2 in keep)
    out.append(svg[last:m.start()])
    out.append(f'<path d="{d}"{m.group(2)}/>')
    last = m.end()
out.append(svg[last:])
open(a.dst, "w", encoding="utf-8").write("".join(out))
print(f"CLEAN removed {removed} of {len(allsegs)} stroke segments (tol {a.tol}, maxlen {a.maxlen})")
sys.exit(0)
