"""Route one connection over two copper layers with vias (grid A*, KiCad's Python). Used for the last net the
autorouter left (Q-CD-05). Pours are ignored (they refill around the new copper); rule areas block; RF nets
get an extra keep-away. The result is checked by DRC like any other track.

  <kicad-python> mlroute.py hw/pcb/main/main.kicad_pcb NET REF1 PAD1 REF2 PAD2
        [--layers F.Cu,In2.Cu] [--width 0.1] [--clear 0.11] [--via 0.4/0.2] [--rf-keep 0.5] [--via-cost 40]
        [--no-under REF,REF]      never route inside the package body (courtyard) of these parts, except their own pad
        [--no-via-circle X,Y,R]   no via of this net within R mm of (X, Y) (board coordinates), e.g. under a coin cell
"""
import heapq
import math
import sys

import pcbnew

MM = pcbnew.FromMM
TOMM = pcbnew.ToMM


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    path, net, r1, p1, r2, p2 = sys.argv[1:7]
    layer_names = arg("--layers", "F.Cu,In2.Cu").split(",")
    W = float(arg("--width", "0.1"))
    CLR = float(arg("--clear", "0.11"))
    VD, VH = (float(x) for x in arg("--via", "0.4/0.2").split("/"))
    RFK = float(arg("--rf-keep", "0.5"))
    VCOST = float(arg("--via-cost", "40"))
    G = 0.05
    b = pcbnew.LoadBoard(path)
    lays = [b.GetLayerID(n) for n in layer_names]
    allcu = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
    netcode = b.FindNet(net).GetNetCode()
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    pa = next(p for p in fps[r1].Pads() if p.GetNumber() == p1)
    pb = next(p for p in fps[r2].Pads() if p.GetNumber() == p2)
    items = [t for t in b.GetTracks()] + [p for f in b.GetFootprints() for p in f.Pads()]
    items = [o for o in items if o.GetNetCode() != netcode]
    rules = [z for z in b.Zones() if z.GetIsRuleArea()]
    outline = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(outline, True)

    # search window: bounding box of the two pads, grown by 4 mm
    ax, ay, bx, by = (TOMM(pa.GetPosition().x), TOMM(pa.GetPosition().y), TOMM(pb.GetPosition().x), TOMM(pb.GetPosition().y))
    x0, y0 = min(ax, bx) - 4, min(ay, by) - 4
    nx, ny = int((abs(ax - bx) + 8) / G) + 1, int((abs(ay - by) + 8) / G) + 1

    def P(ix, iy):
        return pcbnew.VECTOR2I(MM(x0 + ix * G), MM(y0 + iy * G))

    def extra(o):
        return RFK if o.GetNetname().startswith("RF") else 0.0

    def blocked_map(lay, radius, layers_hit):
        """Cells where a disc of `radius` mm collides (with clearance) with copper on any of `layers_hit`."""
        blk = bytearray(nx * ny)
        for o in items:
            if not any(o.IsOnLayer(L) for L in layers_hit):
                continue
            bb = o.GetBoundingBox()
            infl = CLR + radius + extra(o) + G
            ix0 = max(0, int((TOMM(bb.GetX()) - infl - x0) / G))
            ix1 = min(nx - 1, int((TOMM(bb.GetRight()) + infl - x0) / G) + 1)
            iy0 = max(0, int((TOMM(bb.GetY()) - infl - y0) / G))
            iy1 = min(ny - 1, int((TOMM(bb.GetBottom()) + infl - y0) / G) + 1)
            shapes = [o.GetEffectiveShape(L) for L in layers_hit if o.IsOnLayer(L)]
            for iy in range(iy0, iy1 + 1):
                for ix in range(ix0, ix1 + 1):
                    k = iy * nx + ix
                    if blk[k]:
                        continue
                    c = pcbnew.SHAPE_CIRCLE(P(ix, iy), MM(radius))
                    if any(sh.Collide(c, MM(CLR + extra(o))) for sh in shapes):
                        blk[k] = 1
        for iy in range(ny):
            for ix in range(nx):
                q = P(ix, iy)
                if not outline.Contains(q) or outline.Outline(0).PointOnEdge(q, MM(0.3 + radius)):
                    blk[iy * nx + ix] = 1
                    continue
                for z in rules:
                    if any(z.GetLayerSet().Contains(L) for L in layers_hit) and z.Outline().Contains(q) and \
                            (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()):
                        blk[iy * nx + ix] = 1
                        break
        return blk

    blk = {L: blocked_map(L, W / 2, [L]) for L in lays}
    vblk = blocked_map(None, VD / 2, allcu)
    for ref in [r for r in arg("--no-under", "").split(",") if r]:
        f = fps[ref]
        cy_ = f.GetCourtyard(pcbnew.F_CrtYd if f.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd)
        bb_ = cy_.BBox() if cy_.OutlineCount() else f.GetBoundingBox(False)
        # the package body: the courtyard shrunk by 0.5 mm (inside the pad ring of a QFN)
        bx0, by0 = TOMM(bb_.GetX()) + 0.5, TOMM(bb_.GetY()) + 0.5
        bx1, by1 = TOMM(bb_.GetRight()) - 0.5, TOMM(bb_.GetBottom()) - 0.5
        for iy in range(ny):
            for ix in range(nx):
                qx, qy = x0 + ix * G, y0 + iy * G
                if bx0 <= qx <= bx1 and by0 <= qy <= by1:
                    # keep only the copper of the pads themselves reachable (the escape starts at the pad's outer end)
                    for L in lays:
                        blk[L][iy * nx + ix] = 1
                    vblk[iy * nx + ix] = 1
    if "--no-via-circle" in sys.argv:
        cx_, cy2, rr_ = (float(v) for v in arg("--no-via-circle", "").split(","))
        for iy in range(ny):
            for ix in range(nx):
                if math.hypot(x0 + ix * G - cx_, y0 + iy * G - cy2) < rr_:
                    vblk[iy * nx + ix] = 1
    # holes: keep via-to-via and via-to-hole spacing
    for o in b.GetTracks():
        if o.Type() == pcbnew.PCB_VIA_T:
            cx, cy = TOMM(o.GetPosition().x), TOMM(o.GetPosition().y)
            rr = VD / 2 + TOMM(o.GetWidth(pcbnew.F_Cu)) / 2 + 0.15
            for iy in range(max(0, int((cy - rr - y0) / G)), min(ny, int((cy + rr - y0) / G) + 2)):
                for ix in range(max(0, int((cx - rr - x0) / G)), min(nx, int((cx + rr - x0) / G) + 2)):
                    if math.hypot(x0 + ix * G - cx, y0 + iy * G - cy) < rr:
                        vblk[iy * nx + ix] = 1

    def cell(p):
        return (int(round((TOMM(p.x) - x0) / G)), int(round((TOMM(p.y) - y0) / G)))

    s, t = cell(pa.GetPosition()), cell(pb.GetPosition())
    sl, tl = pa.GetLayer() if pa.GetLayer() in lays else lays[0], pb.GetLayer() if pb.GetLayer() in lays else lays[0]
    # free the cells of the two own pads on their layers
    for (cx, cy), own, L in ((s, pa, sl), (t, pb, tl)):
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                ix, iy = cx + dx, cy + dy
                if 0 <= ix < nx and 0 <= iy < ny and own.GetEffectiveShape(L).Collide(pcbnew.SHAPE_CIRCLE(P(ix, iy), 1), 0):
                    blk[L][iy * nx + ix] = 0
    moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    start, goal = (s[0], s[1], sl), (t[0], t[1], tl)
    openq = [(0.0, start, None)]
    came, cost = {}, {start: 0.0}
    while openq:
        _f, c, prev = heapq.heappop(openq)
        if c in came:
            continue
        came[c] = prev
        if c == goal:
            break
        x, y, L = c
        nbrs = []
        for dx, dy, w in moves:
            n = (x + dx, y + dy, L)
            if 0 <= n[0] < nx and 0 <= n[1] < ny and not blk[L][n[1] * nx + n[0]]:
                turn = 0.3 if prev and prev[2] == L and (x - prev[0], y - prev[1]) != (dx, dy) else 0.0
                nbrs.append((n, w + turn))
        if not vblk[y * nx + x]:
            for L2 in lays:
                if L2 != L and not blk[L2][y * nx + x]:
                    nbrs.append(((x, y, L2), VCOST))
        for n, w in nbrs:
            if n in came:
                continue
            g = cost[c] + w
            if g < cost.get(n, 1e18):
                cost[n] = g
                h = math.hypot(goal[0] - n[0], goal[1] - n[1]) + (0 if n[2] == goal[2] else VCOST)
                heapq.heappush(openq, (g + h, n, c))
    if goal not in came:
        print("mlroute: no path for %s" % net)
        if "--debug" in sys.argv:
            for L in lays:
                img = bytearray()
                for iy in range(ny):
                    for ix in range(nx):
                        if (ix, iy) in ((s[0], s[1]), (t[0], t[1])):
                            img += bytes((255, 0, 0))
                        elif (ix, iy, L) in came:
                            img += bytes((60, 200, 90))
                        elif blk[L][iy * nx + ix]:
                            img += bytes((40, 40, 40))
                        else:
                            img += bytes((235, 235, 235))
                out = "/tmp/mlroute_%s.ppm" % b.GetLayerName(L).replace(".", "")
                open(out, "wb").write(b"P6 %d %d 255\n" % (nx, ny) + bytes(img))
                print("mlroute: debug map", out)
        sys.exit(1)
    pts = [goal]
    while came[pts[-1]] is not None:
        pts.append(came[pts[-1]])
    pts.reverse()
    # split into per-layer runs, simplify collinear points, add tracks and vias
    runs, cur = [], [pts[0]]
    for q in pts[1:]:
        if q[2] != cur[-1][2]:
            runs.append(cur)
            cur = [q]
        else:
            cur.append(q)
    runs.append(cur)
    nseg, nvia, length = 0, 0, 0.0
    for ri, run in enumerate(runs):
        simp = [run[0]]
        for i in range(1, len(run) - 1):
            d0 = (run[i][0] - simp[-1][0], run[i][1] - simp[-1][1])
            d1 = (run[i + 1][0] - run[i][0], run[i + 1][1] - run[i][1])
            if d0[0] * d1[1] - d0[1] * d1[0] != 0:
                simp.append(run[i])
        if len(run) > 1:
            simp.append(run[-1])
        V = [P(q[0], q[1]) for q in simp]
        if ri == 0:
            V[0] = pa.GetPosition()
        if ri == len(runs) - 1:
            V[-1] = pb.GetPosition()
        for q0, q1 in zip(V[:-1], V[1:]):
            tr = pcbnew.PCB_TRACK(b)
            tr.SetStart(q0)
            tr.SetEnd(q1)
            tr.SetWidth(MM(W))
            tr.SetLayer(run[0][2])
            tr.SetNetCode(netcode)
            b.Add(tr)
            nseg += 1
            length += math.hypot(TOMM(q1.x - q0.x), TOMM(q1.y - q0.y))
        if ri < len(runs) - 1:
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(P(run[-1][0], run[-1][1]))
            v.SetWidth(MM(VD))
            v.SetDrill(MM(VH))
            v.SetNetCode(netcode)
            b.Add(v)
            nvia += 1
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(path, b)
    print("mlroute: %s routed, %d segments on %s, %d vias, %.1f mm" % (net, nseg, "/".join(layer_names), nvia, length))


if __name__ == "__main__":
    main()
