"""Finish the autorouter's last plane connections: a via plus a short track from each GND / VBAT pad that DRC
still reports as unconnected, to the plane layer of its net (GND: In1, VBAT: In2). KiCad's Python.

  <kicad-python> stitch.py hw/pcb/main/main.kicad_pcb hw/pcb/main/drc.json

For each unconnected pad of a plane net, candidate via positions on rings around the pad are tried, nearest
first. A candidate is kept only if the via and the track keep the netclass clearance to every other copper
item on F.Cu and B.Cu and stay off rule areas. Then all zones are refilled. Run DRC again afterwards.
"""
import json
import math
import sys

import os

import pcbnew

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../skills/pcb-engineer/scripts")))
import outline as outl  # noqa: E402
import spec as specmod  # noqa: E402

SPEC = specmod.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "board.json"))
POLY = outl.build(SPEC["boards"]["main"]["outline"], SPEC["_dir"])


def inside_dev(pos, margin):
    """pos in KiCad internal units -> device frame; inside the outline with an edge margin (mm)."""
    x, y = pcbnew.ToMM(pos.x) - 100.0, 100.0 - pcbnew.ToMM(pos.y)
    return outl.inside(POLY, x, y) and outl.edge_dist(POLY, x, y) >= margin

PLANE = {"GND": True, "VBAT": True}
VIA_D, VIA_DRILL, TRK_W, CLR = 0.4, 0.2, 0.2, 0.12


def mm(v):
    return pcbnew.FromMM(v)


def main():
    path, drc = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(path)
    rep = json.load(open(drc))
    pads = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pads[(fp.GetReference(), p.GetNumber())] = p
    todo = []
    for u in rep.get("unconnected_items", []):
        for it in u["items"]:
            d = it["description"]
            if not d.startswith("Pad "):
                continue
            num = d.split()[1]
            net = d.split("[")[1].split("]")[0]
            ref = d.split(" of ")[1].split()[0]
            if net in PLANE and (ref, num) in pads:
                todo.append(pads[(ref, num)])
    todo = list({(p.GetParentFootprint().GetReference(), p.GetNumber()): p for p in todo}.values())
    obstacles = []
    for t in board.GetTracks():
        obstacles.append(t)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            obstacles.append(p)
    keep_out = [z for z in board.Zones() if z.GetIsRuleArea()]
    edge = board.GetBoardEdgesBoundingBox()
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, True)
    added = 0
    for p in todo:
        net = p.GetNetCode()
        c = p.GetPosition()
        side = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        done = False
        for r in [0.55 + 0.1 * k for k in range(12)]:
            for a in range(0, 360, 20):
                x = c.x + mm(r * math.cos(math.radians(a)))
                y = c.y + mm(r * math.sin(math.radians(a)))
                pos = pcbnew.VECTOR2I(int(x), int(y))
                if not inside_dev(pos, 0.45):
                    continue
                if any(z.GetLayerSet().Contains(side) and z.Outline().Contains(pos) for z in keep_out):
                    continue
                ok = True
                via_shape = pcbnew.SHAPE_CIRCLE(pos, mm(VIA_D / 2))
                seg = pcbnew.SHAPE_SEGMENT(c, pos, mm(TRK_W))
                for o in obstacles:
                    if o.GetNetCode() == net:
                        continue
                    for lay in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu):
                        if not o.IsOnLayer(lay):
                            continue
                        sh = o.GetEffectiveShape(lay)
                        if sh.Collide(via_shape, mm(CLR)):
                            ok = False
                            break
                        if lay == side and sh.Collide(seg, mm(CLR)):
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    continue
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pos)
                v.SetWidth(mm(VIA_D))
                v.SetDrill(mm(VIA_DRILL))
                v.SetNetCode(net)
                board.Add(v)
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(c)
                t.SetEnd(pos)
                t.SetWidth(mm(TRK_W))
                t.SetLayer(side)
                t.SetNetCode(net)
                board.Add(t)
                obstacles += [v, t]
                added += 1
                done = True
                break
            if done:
                break
        if not done:
            print("stitch: no room next to %s pad %s" % (p.GetParentFootprint().GetReference(), p.GetNumber()))
    # GND stitching grid: connects F/B pour islands to the In1 plane
    gnd = board.FindNet("GND").GetNetCode()
    keep_pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
    grid = 0
    if "--grid" in sys.argv:
        pitch = float(sys.argv[sys.argv.index("--grid") + 1])
        bb = outline.BBox()
        x = bb.GetX()
        while x < bb.GetRight():
            y = bb.GetY()
            while y < bb.GetBottom():
                pos = pcbnew.VECTOR2I(int(x), int(y))
                y += mm(pitch)
                if not inside_dev(pos, 0.5):
                    continue
                if any(z.Outline().Contains(pos) for z in keep_out):
                    continue
                vs = pcbnew.SHAPE_CIRCLE(pos, mm(VIA_D / 2))
                bad = False
                for o in obstacles + keep_pads:
                    for lay in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu):
                        if o.IsOnLayer(lay) and o.GetEffectiveShape(lay).Collide(vs, mm(0.2)):
                            bad = True
                            break
                    if bad:
                        break
                if bad:
                    continue
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pos)
                v.SetWidth(mm(VIA_D))
                v.SetDrill(mm(VIA_DRILL))
                v.SetNetCode(gnd)
                board.Add(v)
                obstacles.append(v)
                grid += 1
            x += mm(pitch)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(path, board)
    print("stitch: %d pads, %d vias added, %d GND stitching vias" % (len(todo), added, grid))


def prune(path, drc):
    """Remove GND vias that DRC reports as dangling (connected on one layer only), then refill."""
    board = pcbnew.LoadBoard(path)
    rep = json.load(open(drc))
    pts = set()
    for v in rep.get("violations", []):
        if v["type"] == "via_dangling":
            for it in v["items"]:
                pts.add((round(it["pos"]["x"], 3), round(it["pos"]["y"], 3)))
    n = 0
    for t in list(board.GetTracks()):
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            if (round(pcbnew.ToMM(p.x), 3), round(pcbnew.ToMM(p.y), 3)) in pts:
                board.Remove(t)
                n += 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(path, board)
    print("stitch: pruned %d dangling vias" % n)


def islands(path):
    """Give every GND pour island on F.Cu / B.Cu that has no GND via or pad a via to the In1 plane."""
    board = pcbnew.LoadBoard(path)
    gnd = board.FindNet("GND").GetNetCode()
    zones = list(board.Zones())
    items = list(board.GetTracks()) + [p for fp in board.GetFootprints() for p in fp.Pads()]
    added = 0
    for z in zones:
        if z.GetIsRuleArea() or z.GetNetCode() != gnd or z.GetLayer() not in (pcbnew.F_Cu, pcbnew.B_Cu):
            continue
        lay = z.GetLayer()
        fp_ = z.GetFilledPolysList(lay)
        for i in range(fp_.OutlineCount()):
            ch = fp_.Outline(i)
            anchored = any(o.GetNetCode() == gnd and o.IsOnLayer(lay) and ch.PointInside(o.GetPosition())
                           and (o.GetClass() == "PCB_VIA" or o.GetClass() == "PAD") for o in items)
            if anchored:
                continue
            bb = ch.BBox()
            best = None
            step = pcbnew.FromMM(0.05)
            y = bb.GetY()
            while y < bb.GetBottom() and best is None:
                x = bb.GetX()
                while x < bb.GetRight():
                    pos = pcbnew.VECTOR2I(int(x), int(y))
                    x += step
                    if not ch.PointInside(pos):
                        continue
                    vs = pcbnew.SHAPE_CIRCLE(pos, mm(0.4 / 2))
                    if any(o.GetNetCode() != gnd and any(o.IsOnLayer(L) and o.GetEffectiveShape(L).Collide(vs, mm(0.12))
                           for L in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu)) for o in items):
                        continue
                    best = pos
                    break
                y += step
            if best is None:
                print("islands: no room in an island near", pcbnew.ToMM(bb.Centre().x) - 100, 100 - pcbnew.ToMM(bb.Centre().y))
                continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(best)
            v.SetWidth(mm(0.4))
            v.SetDrill(mm(0.2))
            v.SetNetCode(gnd)
            board.Add(v)
            items.append(v)
            added += 1
    pcbnew.SaveBoard(path, board)
    print("stitch: islands: %d vias added" % added)


if __name__ == "__main__" and "--islands" in sys.argv:
    islands(sys.argv[1])
elif __name__ == "__main__" and "--prune" in sys.argv:
    prune(sys.argv[1], sys.argv[2])
elif __name__ == "__main__":
    main()
