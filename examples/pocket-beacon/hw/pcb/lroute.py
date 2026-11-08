"""Route one remaining connection on one copper layer with a grid A* (KiCad's Python). For the last nets the
autorouter leaves; the result is checked by DRC like any other track.

  <kicad-python> lroute.py hw/pcb/main/main.kicad_pcb NET REF1 PAD1 REF2 PAD2 [--layer F.Cu] [--width 0.1] [--clear 0.11]
"""
import heapq
import math
import sys

import pcbnew


def main():
    a = sys.argv
    path, net, r1, p1, r2, p2 = a[1:7]
    layer_name = a[a.index("--layer") + 1] if "--layer" in a else "F.Cu"
    W = float(a[a.index("--width") + 1]) if "--width" in a else 0.1
    CLR = float(a[a.index("--clear") + 1]) if "--clear" in a else 0.11
    G = 0.05
    board = pcbnew.LoadBoard(path)
    lay = board.GetLayerID(layer_name)
    netcode = board.FindNet(net).GetNetCode()
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    pa = next(p for p in fps[r1].Pads() if p.GetNumber() == p1)
    pb = next(p for p in fps[r2].Pads() if p.GetNumber() == p2)
    bb = board.GetBoardEdgesBoundingBox()
    x0, y0 = pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY())
    nx, ny = int(pcbnew.ToMM(bb.GetWidth()) / G) + 1, int(pcbnew.ToMM(bb.GetHeight()) / G) + 1
    blocked = bytearray(nx * ny)
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, True)
    margin = 0.25 + W / 2
    items = [t for t in board.GetTracks()] + [p for f in board.GetFootprints() for p in f.Pads()]
    for o in items:
        if o.GetNetCode() == netcode or not o.IsOnLayer(lay):
            continue
        sh = o.GetEffectiveShape(lay)
        b = o.GetBoundingBox()
        infl = CLR + W / 2 + G
        ix0 = max(0, int((pcbnew.ToMM(b.GetX()) - infl - x0) / G))
        ix1 = min(nx - 1, int((pcbnew.ToMM(b.GetRight()) + infl - x0) / G) + 1)
        iy0 = max(0, int((pcbnew.ToMM(b.GetY()) - infl - y0) / G))
        iy1 = min(ny - 1, int((pcbnew.ToMM(b.GetBottom()) + infl - y0) / G) + 1)
        for iy in range(iy0, iy1 + 1):
            for ix in range(ix0, ix1 + 1):
                k = iy * nx + ix
                if blocked[k]:
                    continue
                c = pcbnew.VECTOR2I(pcbnew.FromMM(x0 + ix * G), pcbnew.FromMM(y0 + iy * G))
                if sh.Collide(pcbnew.SHAPE_CIRCLE(c, pcbnew.FromMM(W / 2)), pcbnew.FromMM(CLR)):
                    blocked[k] = 1
    for z in board.Zones():
        if z.GetIsRuleArea() and z.GetLayerSet().Contains(lay) and z.GetDoNotAllowTracks():
            for iy in range(ny):
                for ix in range(nx):
                    if z.Outline().Contains(pcbnew.VECTOR2I(pcbnew.FromMM(x0 + ix * G), pcbnew.FromMM(y0 + iy * G))):
                        blocked[iy * nx + ix] = 1

    def cell(p):
        return (int(round((pcbnew.ToMM(p.x) - x0) / G)), int(round((pcbnew.ToMM(p.y) - y0) / G)))

    s, t = cell(pa.GetPosition()), cell(pb.GetPosition())
    for (cx, cy) in (s, t):
        for dy in range(-6, 7):
            for dx in range(-6, 7):
                q = (cy + dy) * nx + (cx + dx)
                if 0 <= q < len(blocked):
                    pp = pcbnew.VECTOR2I(pcbnew.FromMM(x0 + (cx + dx) * G), pcbnew.FromMM(y0 + (cy + dy) * G))
                    own = pa if (cx, cy) == s else pb
                    if own.GetEffectiveShape(lay).Collide(pcbnew.SHAPE_CIRCLE(pp, 1), 0):
                        blocked[q] = 0
    for iy in range(ny):
        for ix in range(nx):
            c = pcbnew.VECTOR2I(pcbnew.FromMM(x0 + ix * G), pcbnew.FromMM(y0 + iy * G))
            if not outline.Contains(c) or outline.Outline(0).PointOnEdge(c, pcbnew.FromMM(margin)):
                blocked[iy * nx + ix] = 1
    print("lroute: grid %dx%d, blocked %.0f%%, start blocked %d, end blocked %d" % (nx, ny, 100.0 * sum(blocked) / len(blocked),
          blocked[s[1] * nx + s[0]], blocked[t[1] * nx + t[0]]))
    moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    openq = [(0, s, None)]
    came, cost = {}, {s: 0}
    while openq:
        f, c, prev = heapq.heappop(openq)
        if c in came:
            continue
        came[c] = prev
        if c == t:
            break
        for dx, dy, w in moves:
            n = (c[0] + dx, c[1] + dy)
            if not (0 <= n[0] < nx and 0 <= n[1] < ny) or blocked[n[1] * nx + n[0]] or n in came:
                continue
            turn = 0.3 if prev and (c[0] - prev[0], c[1] - prev[1]) != (dx, dy) else 0
            g = cost[c] + w + turn
            if g < cost.get(n, 1e18):
                cost[n] = g
                heapq.heappush(openq, (g + math.hypot(t[0] - n[0], t[1] - n[1]), n, c))
    if t not in came:
        print("lroute: no path for %s" % net)
        sys.exit(1)
    pts = [t]
    while came[pts[-1]] is not None:
        pts.append(came[pts[-1]])
    pts.reverse()
    simp = [pts[0]]
    for i in range(1, len(pts) - 1):
        d0 = (pts[i][0] - simp[-1][0], pts[i][1] - simp[-1][1])
        d1 = (pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        if d0[0] * d1[1] - d0[1] * d1[0] != 0:
            simp.append(pts[i])
    simp.append(pts[-1])
    P = [pcbnew.VECTOR2I(pcbnew.FromMM(x0 + x * G), pcbnew.FromMM(y0 + y * G)) for x, y in simp]
    P[0], P[-1] = pa.GetPosition(), pb.GetPosition()
    keep = []
    for q0, q1 in zip(P[:-1], P[1:]):
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(q0)
        tr.SetEnd(q1)
        tr.SetWidth(pcbnew.FromMM(W))
        tr.SetLayer(lay)
        tr.SetNetCode(netcode)
        board.Add(tr)
        keep.append(tr)
    pcbnew.SaveBoard(path, board)
    L = sum(math.hypot(pcbnew.ToMM(b.x - a.x), pcbnew.ToMM(b.y - a.y)) for a, b in zip(P[:-1], P[1:]))
    print("lroute: %s routed on %s, %d segments, %.1f mm" % (net, layer_name, len(P) - 1, L))


if __name__ == "__main__":
    main()
