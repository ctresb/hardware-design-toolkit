"""Close what the autorouter leaves on a dense board. KiCad's Python; run DRC (JSON) in the project folder before
and after each step (outside its folder kicad-cli applies default rules and reports false violations).

    <kicad-python> finish.py dupes   BOARD [--remove]          tracks that duplicate a same-net pour on their layer, and
                                     tracks between pads of one footprint (internal switch links): they block escapes
    <kicad-python> finish.py planes  BOARD DRC.json [--nets GND,VBAT]   via + short track from each unconnected pad of
                                     a plane net down to its plane
    <kicad-python> finish.py islands BOARD [--net GND] [--allow-under REF,..]   one via in every outer-layer pour
                                     island of the net that has no via or PTH pad of that net (an SMD pad alone does not
                                     anchor an island), never under a part body
    <kicad-python> finish.py grid    BOARD [--net GND] [--pitch 2.0]    stitching-via grid
    <kicad-python> finish.py prune   BOARD DRC.json            remove vias DRC reports as dangling
    <kicad-python> finish.py net     BOARD NET REF1 PAD1 REF2 PAD2 [--layers F.Cu,In2.Cu] [--width 0.1] [--clear 0.11]
                                     [--via-d 0.4 --drill 0.2] [--via-cost 40] [--keep-away RF:0.5]
                                     [--no-under REF,..] [--no-via-circle X,Y,R] [--debug]
                                     route one connection over one or more layers with vias (grid A*)

Get DRC.json with `kicad-cli pcb drc --format json --schematic-parity -o DRC.json BOARD.kicad_pcb`, run inside the
board's project folder. Every candidate keeps --clear from the copper of other nets on all copper layers, stays
--edge inside the outline and outside rule areas. Zones are refilled with kicad-cli afterwards (pcbnew.ZONE_FILLER
can crash in KiCad 10 after Python edits). The results are ordinary tracks and vias: DRC checks them.
`--no-under` keeps a route out of a package body (inside a QFN pad ring) and `--no-via-circle` keeps vias of the
net out of an area (under a coin cell); KiCad DRC accepts both, so the router must avoid them.
Tested with KiCad 10.0.8.
"""
import argparse
import heapq
import json
import math
import os
import re
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outline as outl  # noqa: E402
import route as routemod  # noqa: E402


def mm(v):
    return pcbnew.FromMM(v)


class Board:
    def __init__(self, path):
        self.path = path
        self.b = pcbnew.LoadBoard(path)
        sps = pcbnew.SHAPE_POLY_SET()
        self.b.GetBoardPolygonOutlines(sps, True)
        ch = sps.Outline(0)
        self.poly = [(pcbnew.ToMM(ch.CPoint(i).x), pcbnew.ToMM(ch.CPoint(i).y)) for i in range(ch.PointCount())]
        self.cu = list(self.b.GetEnabledLayers().CuStack())
        self.rules = [z for z in self.b.Zones() if z.GetIsRuleArea()]
        self.items = list(self.b.GetTracks()) + [p for fp in self.b.GetFootprints() for p in fp.Pads()]

    def inside(self, pos, margin):
        x, y = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
        return outl.inside(self.poly, x, y) and outl.edge_dist(self.poly, x, y) >= margin

    def in_rule_area(self, pos, layer=None, tracks=False):
        for z in self.rules:
            if layer is not None and not z.GetLayerSet().Contains(layer):
                continue
            if tracks and not z.GetDoNotAllowTracks():
                continue
            if not tracks and not z.GetDoNotAllowVias():
                continue
            if z.Outline().Contains(pos):
                return True
        return False

    def clear(self, shape, net, clr, layers):
        for o in self.items:
            if o.GetNetCode() == net:
                continue
            for lay in layers:
                if o.IsOnLayer(lay) and o.GetEffectiveShape(lay).Collide(shape, mm(clr)):
                    return False
        return True

    def via(self, pos, net, d, drill):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pos)
        v.SetWidth(mm(d))
        v.SetDrill(mm(drill))
        v.SetNetCode(net)
        self.b.Add(v)
        self.items.append(v)
        return v

    def track(self, a, c, net, w, layer):
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(a)
        t.SetEnd(c)
        t.SetWidth(mm(w))
        t.SetLayer(layer)
        t.SetNetCode(net)
        self.b.Add(t)
        self.items.append(t)
        return t

    def courtyards(self, skip=()):
        out = []
        for fp in self.b.GetFootprints():
            if fp.GetReference() in skip:
                continue
            if hasattr(fp, "BuildCourtyardCaches"):
                fp.BuildCourtyardCaches()
            cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
            if cy.OutlineCount():
                out.append(cy)
        return out

    def save(self, fill=True):
        pcbnew.SaveBoard(self.path, self.b)
        if fill:
            routemod.refill(self.path)


PAD_RE = re.compile(r"Pad (\S+) \[([^\]]*)\] of (\S+)")


def unconnected_pads(drc):
    out = set()
    for u in json.load(open(drc)).get("unconnected_items", []):
        for it in u.get("items", []):
            m = PAD_RE.search(it.get("description", ""))
            if m:
                out.add((m.group(3), m.group(1), m.group(2)))         # ref, pad, net
    return out


def cmd_planes(a):
    B = Board(a.board)
    nets = set(a.nets.split(","))
    pads = {(fp.GetReference(), p.GetNumber()): p for fp in B.b.GetFootprints() for p in fp.Pads()}
    todo = [pads[(r, n)] for r, n, net in sorted(unconnected_pads(a.drc)) if net in nets and (r, n) in pads]
    added, failed = 0, []
    for p in todo:
        net, c = p.GetNetCode(), p.GetPosition()
        side = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        done = False
        for k in range(12):
            r = a.via_d / 2 + a.clear + 0.25 + 0.1 * k
            for ang in range(0, 360, 20):
                pos = pcbnew.VECTOR2I(int(c.x + mm(r * math.cos(math.radians(ang)))),
                                      int(c.y + mm(r * math.sin(math.radians(ang)))))
                if not B.inside(pos, a.edge) or B.in_rule_area(pos, side):
                    continue
                if not B.clear(pcbnew.SHAPE_CIRCLE(pos, mm(a.via_d / 2)), net, a.clear, B.cu):
                    continue
                if not B.clear(pcbnew.SHAPE_SEGMENT(c, pos, mm(a.track)), net, a.clear, [side]):
                    continue
                B.via(pos, net, a.via_d, a.drill)
                B.track(c, pos, net, a.track, side)
                added += 1
                done = True
                break
            if done:
                break
        if not done:
            failed.append("%s.%s" % (p.GetParentFootprint().GetReference(), p.GetNumber()))
    B.save()
    print("finish planes: %d unconnected plane pads, %d stitched%s" % (len(todo), added,
          "; no room next to " + ", ".join(failed) if failed else ""))
    return 1 if failed else 0


def cmd_grid(a):
    B = Board(a.board)
    net = B.b.FindNet(a.net).GetNetCode()
    x0, y0, x1, y1 = outl.bbox(B.poly)
    n = 0
    nx, ny = int((x1 - x0) / a.pitch), int((y1 - y0) / a.pitch)
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y = x0 + a.pitch * (i + 0.5), y0 + a.pitch * (j + 0.5)
            pos = pcbnew.VECTOR2I(mm(x), mm(y))
            if not B.inside(pos, a.edge) or B.in_rule_area(pos):
                continue
            if not B.clear(pcbnew.SHAPE_CIRCLE(pos, mm(a.via_d / 2)), net, max(a.clear, 0.2), B.cu):
                continue
            if any(o.GetNetCode() == net and o.GetClass() == "PCB_VIA" and
                   math.hypot(pcbnew.ToMM(o.GetPosition().x) - x, pcbnew.ToMM(o.GetPosition().y) - y) < a.pitch / 2
                   for o in B.items):
                continue                       # a via of the net is already close
            B.via(pos, net, a.via_d, a.drill)
            n += 1
    B.save()
    print("finish grid: %d %s stitching vias at %.2f mm pitch (run prune after DRC)" % (n, a.net, a.pitch))
    return 0


def cmd_islands(a):
    B = Board(a.board)
    net = B.b.FindNet(a.net).GetNetCode()
    cys = B.courtyards(skip=set(x for x in a.allow_under.split(",") if x))
    anchors = [o for o in B.items if o.GetNetCode() == net and
               (o.GetClass() == "PCB_VIA" or (o.GetClass() == "PAD" and o.GetAttribute() == pcbnew.PAD_ATTRIB_PTH))]

    def free(pos):
        if any(cy.Contains(pos) for cy in cys):          # never under a part body
            return False
        if not B.inside(pos, a.edge) or B.in_rule_area(pos):
            return False
        vs = pcbnew.SHAPE_CIRCLE(pos, mm(a.via_d / 2))
        for o in B.items:
            if o.GetClass() == "PCB_VIA" and (o.GetPosition() - pos).EuclideanNorm() < mm(a.via_d / 2 + 0.15) + o.GetWidth(pcbnew.F_Cu) // 2:
                return False                              # via-to-via spacing, any net
            same = o.GetNetCode() == net
            if same and o.GetClass() != "PAD":
                continue
            if same and not (o.IsOnLayer(pcbnew.F_Paste) or o.IsOnLayer(pcbnew.B_Paste)):
                continue                                  # a same-net pad without paste (a cell contact) may carry vias
            clr = 0.05 if same else a.clear
            if any(o.IsOnLayer(L) and o.GetEffectiveShape(L).Collide(vs, mm(clr)) for L in B.cu):
                return False
        return True

    added, missed = 0, 0
    for z in list(B.b.Zones()):
        if z.GetIsRuleArea() or z.GetNetCode() != net:
            continue
        for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not z.IsOnLayer(lay):
                continue
            fill = z.GetFilledPolysList(lay)
            for i in range(fill.OutlineCount()):
                ch = fill.Outline(i)
                if any(ch.PointInside(o.GetPosition()) for o in anchors):
                    continue
                bb, c, step = ch.BBox(), ch.BBox().Centre(), mm(0.05)
                cands = []
                yy = bb.GetY()
                while yy <= bb.GetBottom():
                    xx = bb.GetX()
                    while xx <= bb.GetRight():
                        q = pcbnew.VECTOR2I(int(xx), int(yy))
                        if ch.PointInside(q) and not ch.PointOnEdge(q, mm(a.via_d / 2 + 0.05)):
                            cands.append(((q - c).EuclideanNorm(), q))
                        xx += step
                    yy += step
                cands.sort(key=lambda t: t[0])
                pos = next((q for _d, q in cands if free(q)), None)
                if pos is None:
                    missed += 1
                    print("finish islands: no room on %s near (%.2f, %.2f)" % (B.b.GetLayerName(lay), pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)))
                    continue
                v = B.via(pos, net, a.via_d, a.drill)
                anchors.append(v)
                added += 1
    B.save()
    print("finish islands: %d vias added, %d islands without room" % (added, missed))
    return 1 if missed else 0


def cmd_dupes(a):
    """Tracks that only duplicate a same-net pour on their layer, and tracks joining two pads of one footprint
    (a tactile switch's internal links). Both add copper that blocks the escape of the last nets (lesson L-520)."""
    B = Board(a.board)
    pad_owner = {}
    for fp in B.b.GetFootprints():
        for p in fp.Pads():
            pad_owner[id(p)] = fp.GetReference()
    found = []
    zones = [z for z in B.b.Zones() if not z.GetIsRuleArea()]
    for t in [t for t in B.b.GetTracks() if t.GetClass() == "PCB_TRACK"]:
        lay, net = t.GetLayer(), t.GetNetCode()
        for z in zones:
            if z.GetNetCode() == net and z.IsOnLayer(lay):
                fill = z.GetFilledPolysList(lay)
                if fill.OutlineCount() and fill.Contains(t.GetStart()) and fill.Contains(t.GetEnd()) and \
                        fill.Contains(pcbnew.VECTOR2I((t.GetStart().x + t.GetEnd().x) // 2, (t.GetStart().y + t.GetEnd().y) // 2)):
                    found.append((t, "inside the %s pour on %s" % (t.GetNetname(), B.b.GetLayerName(lay))))
                    break
        else:
            ends = []
            for fp in B.b.GetFootprints():
                for p in fp.Pads():
                    if p.GetNetCode() == net and p.IsOnLayer(lay) and (p.HitTest(t.GetStart()) or p.HitTest(t.GetEnd())):
                        ends.append(fp.GetReference())
            if len(ends) >= 2 and len(set(ends)) == 1:
                found.append((t, "links two pads of %s (internal connection of the part)" % ends[0]))
    for t, why in found:
        print("finish dupes: %s track %.2f mm at (%.2f, %.2f): %s" % (t.GetNetname(), pcbnew.ToMM(t.GetLength()),
              pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y), why))
    if a.remove and found:
        for t, _why in found:
            B.b.Remove(t)
        B.save()
    print("finish dupes: %d duplicate links%s" % (len(found), " removed" if a.remove and found else ""))
    return 0


def cmd_prune(a):
    B = Board(a.board)
    pts = set()
    for v in json.load(open(a.drc)).get("violations", []):
        if v.get("type") == "via_dangling":
            for it in v.get("items", []):
                pts.add((round(it["pos"]["x"], 3), round(it["pos"]["y"], 3)))
    n = 0
    for t in [t for t in B.b.GetTracks() if t.GetClass() == "PCB_VIA"]:
        p = t.GetPosition()
        if (round(pcbnew.ToMM(p.x), 3), round(pcbnew.ToMM(p.y), 3)) in pts:
            B.b.Remove(t)
            n += 1
    B.save()
    print("finish prune: %d dangling vias removed" % n)
    return 0


def cmd_net(a):
    B = Board(a.board)
    lays = [B.b.GetLayerID(n) for n in a.layers.split(",")]
    netcode = B.b.FindNet(a.net).GetNetCode()
    fps = {f.GetReference(): f for f in B.b.GetFootprints()}
    pa = next(p for p in fps[a.ref1].Pads() if p.GetNumber() == a.pad1)
    pb = next(p for p in fps[a.ref2].Pads() if p.GetNumber() == a.pad2)
    G, W, CLR, VD = a.grid, a.width, a.clear, a.via_d
    keep = {}
    for tok in [x for x in a.keep_away.split(",") if x]:
        pre, _, d = tok.partition(":")
        keep[pre] = float(d or 0.5)
    items = [o for o in B.items if o.GetNetCode() != netcode]
    ax, ay = pcbnew.ToMM(pa.GetPosition().x), pcbnew.ToMM(pa.GetPosition().y)
    bx, by = pcbnew.ToMM(pb.GetPosition().x), pcbnew.ToMM(pb.GetPosition().y)
    x0, y0 = min(ax, bx) - a.window, min(ay, by) - a.window             # search window around the two pads
    nx, ny = int((abs(ax - bx) + 2 * a.window) / G) + 1, int((abs(ay - by) + 2 * a.window) / G) + 1

    def at(ix, iy):
        return pcbnew.VECTOR2I(mm(x0 + ix * G), mm(y0 + iy * G))

    def extra(o):
        return max([d for pre, d in keep.items() if o.GetNetname().startswith(pre)] or [0.0])

    def blocked(radius, layers_hit):
        blk = bytearray(nx * ny)
        for o in items:
            if not any(o.IsOnLayer(L) for L in layers_hit):
                continue
            bb, ex = o.GetBoundingBox(), extra(o)
            infl = CLR + radius + ex + G
            ix0 = max(0, int((pcbnew.ToMM(bb.GetX()) - infl - x0) / G))
            ix1 = min(nx - 1, int((pcbnew.ToMM(bb.GetRight()) + infl - x0) / G) + 1)
            iy0 = max(0, int((pcbnew.ToMM(bb.GetY()) - infl - y0) / G))
            iy1 = min(ny - 1, int((pcbnew.ToMM(bb.GetBottom()) + infl - y0) / G) + 1)
            shapes = [o.GetEffectiveShape(L) for L in layers_hit if o.IsOnLayer(L)]
            for iy in range(iy0, iy1 + 1):
                for ix in range(ix0, ix1 + 1):
                    k = iy * nx + ix
                    if not blk[k] and any(sh.Collide(pcbnew.SHAPE_CIRCLE(at(ix, iy), mm(radius)), mm(CLR + ex)) for sh in shapes):
                        blk[k] = 1
        for iy in range(ny):
            for ix in range(nx):
                q = at(ix, iy)
                if not B.inside(q, a.edge + radius):
                    blk[iy * nx + ix] = 1
                elif any(B.in_rule_area(q, L, tracks=True) or B.in_rule_area(q, L) for L in layers_hit):
                    blk[iy * nx + ix] = 1
        return blk

    blk = {L: blocked(W / 2, [L]) for L in lays}
    vblk = blocked(VD / 2, B.cu)
    for ref in [r for r in a.no_under.split(",") if r]:          # inside the package body (the QFN pad ring)
        f = fps[ref]
        if hasattr(f, "BuildCourtyardCaches"):
            f.BuildCourtyardCaches()
        cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
        bx0, by0 = pcbnew.ToMM(bb.GetX()) + 0.5, pcbnew.ToMM(bb.GetY()) + 0.5
        bx1, by1 = pcbnew.ToMM(bb.GetRight()) - 0.5, pcbnew.ToMM(bb.GetBottom()) - 0.5
        for iy in range(ny):
            for ix in range(nx):
                if bx0 <= x0 + ix * G <= bx1 and by0 <= y0 + iy * G <= by1:
                    for L in lays:
                        blk[L][iy * nx + ix] = 1
                    vblk[iy * nx + ix] = 1
    if a.no_via_circle:
        cx, cy, rr = (float(v) for v in a.no_via_circle.split(","))
        for iy in range(ny):
            for ix in range(nx):
                if math.hypot(x0 + ix * G - cx, y0 + iy * G - cy) < rr:
                    vblk[iy * nx + ix] = 1
    for o in B.b.GetTracks():                                    # via-to-via and via-to-hole spacing
        if o.GetClass() == "PCB_VIA":
            vx, vy = pcbnew.ToMM(o.GetPosition().x), pcbnew.ToMM(o.GetPosition().y)
            rr = VD / 2 + pcbnew.ToMM(o.GetWidth(pcbnew.F_Cu)) / 2 + 0.15
            for iy in range(max(0, int((vy - rr - y0) / G)), min(ny, int((vy + rr - y0) / G) + 2)):
                for ix in range(max(0, int((vx - rr - x0) / G)), min(nx, int((vx + rr - x0) / G) + 2)):
                    if math.hypot(x0 + ix * G - vx, y0 + iy * G - vy) < rr:
                        vblk[iy * nx + ix] = 1

    def cell(p):
        return (int(round((pcbnew.ToMM(p.x) - x0) / G)), int(round((pcbnew.ToMM(p.y) - y0) / G)))

    s, t = cell(pa.GetPosition()), cell(pb.GetPosition())
    sl = pa.GetLayer() if pa.GetLayer() in lays else lays[0]
    tl = pb.GetLayer() if pb.GetLayer() in lays else lays[0]
    for (cx, cy), own, L in ((s, pa, sl), (t, pb, tl)):          # free the cells under the two pads themselves
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                ix, iy = cx + dx, cy + dy
                if 0 <= ix < nx and 0 <= iy < ny and own.GetEffectiveShape(L).Collide(pcbnew.SHAPE_CIRCLE(at(ix, iy), 1), 0):
                    blk[L][iy * nx + ix] = 0
    moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    start, goal = (s[0], s[1], sl), (t[0], t[1], tl)
    openq, came, cost = [(0.0, start, None)], {}, {start: 0.0}
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
                    nbrs.append(((x, y, L2), a.via_cost))
        for n, w in nbrs:
            if n in came:
                continue
            g = cost[c] + w
            if g < cost.get(n, 1e18):
                cost[n] = g
                h = math.hypot(goal[0] - n[0], goal[1] - n[1]) + (0 if n[2] == goal[2] else a.via_cost)
                heapq.heappush(openq, (g + h, n, c))
    if goal not in came:
        print("finish net: no path for %s on %s (try more layers, a smaller --width or --clear, or move a part)"
              % (a.net, a.layers))
        if a.debug:
            for L in lays:
                img = bytearray()
                for iy in range(ny):
                    for ix in range(nx):
                        if (ix, iy) in (s[:2], t[:2]):
                            img += bytes((255, 0, 0))
                        elif (ix, iy, L) in came:
                            img += bytes((60, 200, 90))
                        elif blk[L][iy * nx + ix]:
                            img += bytes((40, 40, 40))
                        else:
                            img += bytes((235, 235, 235))
                out = os.path.join(os.path.dirname(os.path.abspath(a.board)),
                                   "finish_net_%s.ppm" % B.b.GetLayerName(L).replace(".", ""))
                with open(out, "wb") as f:
                    f.write(b"P6 %d %d 255\n" % (nx, ny) + bytes(img))
                print("finish net: reachability map", out, "(green reached, grey blocked, red pads)")
        return 1
    pts = [goal]
    while came[pts[-1]] is not None:
        pts.append(came[pts[-1]])
    pts.reverse()
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
        V = [at(q[0], q[1]) for q in simp]
        if ri == 0:
            V[0] = pa.GetPosition()
        if ri == len(runs) - 1:
            V[-1] = pb.GetPosition()
        for q0, q1 in zip(V[:-1], V[1:]):
            B.track(q0, q1, netcode, W, run[0][2])
            nseg += 1
            length += math.hypot(pcbnew.ToMM(q1.x - q0.x), pcbnew.ToMM(q1.y - q0.y))
        if ri < len(runs) - 1:
            B.via(at(run[-1][0], run[-1][1]), netcode, VD, a.drill)
            nvia += 1
    B.save()
    print("finish net: %s routed, %d segments on %s, %d vias, %.1f mm" % (a.net, nseg, a.layers, nvia, length))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("board")
        p.add_argument("--edge", type=float, default=0.3, help="copper-to-edge distance (mm)")
        p.add_argument("--clear", type=float, default=0.12, help="clearance to other nets (mm)")
        p.add_argument("--via-d", type=float, default=0.4)
        p.add_argument("--drill", type=float, default=0.2)
        p.add_argument("--track", type=float, default=0.2)
        return p

    p = common(sub.add_parser("planes"))
    p.add_argument("drc")
    p.add_argument("--nets", default="GND")
    p = common(sub.add_parser("islands"))
    p.add_argument("--net", default="GND")
    p.add_argument("--allow-under", default="", help="parts whose courtyard may hold vias (a coin-cell holder frame)")
    p = common(sub.add_parser("dupes"))
    p.add_argument("--remove", action="store_true")
    p = common(sub.add_parser("grid"))
    p.add_argument("--net", default="GND")
    p.add_argument("--pitch", type=float, default=2.0)
    p = common(sub.add_parser("prune"))
    p.add_argument("drc")
    p = common(sub.add_parser("net"))
    for k in ("net", "ref1", "pad1", "ref2", "pad2"):
        p.add_argument(k)
    p.add_argument("--layers", default="F.Cu", help="comma list; two or more layers allow vias")
    p.add_argument("--layer", dest="layers", help="alias of --layers for one layer")
    p.add_argument("--width", type=float, default=0.1)
    p.add_argument("--grid", type=float, default=0.05)
    p.add_argument("--window", type=float, default=4.0, help="search margin around the two pads (mm)")
    p.add_argument("--via-cost", type=float, default=40.0, help="cost of a via, in grid steps")
    p.add_argument("--keep-away", default="RF:0.5", help="net prefix:extra clearance (mm), comma list")
    p.add_argument("--no-under", default="", help="parts whose package body the route must avoid")
    p.add_argument("--no-via-circle", default="", help="X,Y,R in board mm: no via of this net inside")
    p.add_argument("--debug", action="store_true", help="write reachability maps (PPM) when no path is found")
    a = ap.parse_args()
    if a.cmd == "net" and "--clear" not in sys.argv:
        a.clear = 0.11
    return {"planes": cmd_planes, "islands": cmd_islands, "grid": cmd_grid, "prune": cmd_prune, "net": cmd_net,
            "dupes": cmd_dupes}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
