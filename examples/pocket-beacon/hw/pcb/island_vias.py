"""Stitch every GND pour island on F.Cu/B.Cu that has no via or PTH pad with one 0.4/0.2 mm via to the In1 GND plane.
Stricter than stitch.py --islands: an SMD GND pad alone does not anchor an island (TB-12).

  <kicad-python> island_vias.py hw/pcb/main/main.kicad_pcb
"""
import sys
import pcbnew

MM = pcbnew.FromMM
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
gnd = b.FindNet("GND").GetNetCode()
LAYERS = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
tracks = list(b.GetTracks())
pads = [p for f in b.GetFootprints() for p in f.Pads()]
rules = [z for z in b.Zones() if z.GetIsRuleArea()]
outline = pcbnew.SHAPE_POLY_SET()
b.GetBoardPolygonOutlines(outline, True)


courtyards = []
for f in b.GetFootprints():
    cy = f.GetCourtyard(pcbnew.F_CrtYd if f.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd)
    if cy.OutlineCount() and f.GetReference() != "BT1":    # the cell holder spans the board; its contact pad is handled below
        courtyards.append(cy)


def free(pos):
    vs = pcbnew.SHAPE_CIRCLE(pos, MM(0.2))
    if any(cy.Contains(pos) for cy in courtyards):       # never under a component body
        return False
    if not outline.Contains(pos) or outline.Outline(0).PointOnEdge(pos, MM(0.45)):
        return False
    for z in rules:
        if z.GetDoNotAllowVias() and z.Outline().Contains(pos):
            return False
    for o in tracks:
        if o.Type() == pcbnew.PCB_VIA_T:
            d = (o.GetPosition() - pos).EuclideanNorm()
            if d < MM(0.2 + o.GetWidth(pcbnew.F_Cu) / 2e6 + 0.15):
                return False
        if o.GetNetCode() == gnd:
            continue
        for L in LAYERS:
            if o.IsOnLayer(L) and o.GetEffectiveShape(L).Collide(vs, MM(0.12)):
                return False
    for p in pads:
        same = p.GetNetCode() == gnd
        # a same-net pad without solder paste (the cell's negative contact) may carry stitching vias (D-519)
        if same and not (p.IsOnLayer(pcbnew.F_Paste) or p.IsOnLayer(pcbnew.B_Paste)):
            continue
        clr = 0.05 if same else 0.12
        for L in LAYERS:
            if p.IsOnLayer(L) and p.GetEffectiveShape(L).Collide(vs, MM(clr)):
                return False
    return True


vias = [t for t in tracks if t.Type() == pcbnew.PCB_VIA_T and t.GetNetCode() == gnd]
pth = [p for p in pads if p.GetNetCode() == gnd and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
added, failed = 0, 0
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetCode() != gnd:
        continue
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
        if not z.IsOnLayer(lay):
            continue
        fp = z.GetFilledPolysList(lay)
        for i in range(fp.OutlineCount()):
            ch = fp.Outline(i)
            if any(ch.PointInside(v.GetPosition()) for v in vias + pth):
                continue
            bb = ch.BBox()
            c = bb.Centre()
            cands = []
            step = MM(0.05)
            y = bb.GetY()
            while y <= bb.GetBottom():
                x = bb.GetX()
                while x <= bb.GetRight():
                    q = pcbnew.VECTOR2I(int(x), int(y))
                    # the via must sit well inside the island copper
                    if ch.PointInside(q) and not ch.PointOnEdge(q, MM(0.25)):
                        cands.append(((q - c).EuclideanNorm(), q))
                    x += step
                y += step
            cands.sort(key=lambda t: t[0])
            pos = next((q for _d, q in cands if free(q)), None)
            if pos is None:
                failed += 1
                print("island_vias: no room on %s near (%.2f, %.2f)" % (b.GetLayerName(lay), pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)))
                continue
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pos)
            v.SetWidth(MM(0.4))
            v.SetDrill(MM(0.2))
            v.SetNetCode(gnd)
            b.Add(v)
            tracks.append(v)
            vias.append(v)
            added += 1
            print("island_vias: via on %s island at (%.2f, %.2f)" % (b.GetLayerName(lay), pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(path, b)
print("island_vias: %d vias added, %d islands without room" % (added, failed))
sys.exit(1 if failed else 0)
