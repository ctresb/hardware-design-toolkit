"""Split Freerouting run for a remote machine (KiCad's Python). Same steps as pcb-engineer route.py, in two halves:

  <kicad-python> route_remote.py export hw/pcb/board.json --board main      -> main/main.dsn (+ zones saved)
  (run Freerouting on the workstation/cloud VM:  java -jar freerouting.jar -de main.dsn -do main.ses -mp 60)
  <kicad-python> route_remote.py import hw/pcb/board.json --board main      <- main/main.ses, planes restored

The toolkit's route.py runs Java locally; this project routes on a cloud VM (CONVENTIONS §7), so the DSN
export and the SES import are separated. Tested with KiCad 10.0.8 and Freerouting 2.5.0.
"""
import argparse
import json
import os
import sys

import pcbnew

TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../skills/pcb-engineer/scripts"))
sys.path.insert(0, TOOLS)
import outline as outl  # noqa: E402
import spec as specmod  # noqa: E402

OX, OY = 100.0, 100.0


def v(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY - y))


def export(s, bname, edge):
    b = s["boards"][bname]
    d = os.path.join(s["_dir"], bname)
    path = os.path.join(d, bname + ".kicad_pcb")
    board = pcbnew.LoadBoard(path)
    for t in list(board.GetTracks()):
        if not t.IsLocked():
            board.Remove(t)
    # outer pours and non-GND inner pours leave the DSN (the router may use those layers for tracks);
    # the GND plane on In1 stays, so the router drops GND vias onto it
    strip = (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu)
    outer = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetLayer() in strip]
    saved = []
    for z in outer:
        ch = z.Outline().Outline(0)
        saved.append({"net": z.GetNetname(), "layer": z.GetLayer(), "name": z.GetZoneName(), "prio": z.GetAssignedPriority(),
                      "pts": [[ch.CPoint(i).x, ch.CPoint(i).y] for i in range(ch.PointCount())]})
        board.Remove(z)
    poly = outl.build(b["outline"], s["_dir"])
    inset = outl.offset(poly, edge)
    ring = pcbnew.ZONE(board)
    ring.SetIsRuleArea(True)
    ring.SetDoNotAllowTracks(True)
    ring.SetDoNotAllowVias(True)
    ring.SetDoNotAllowZoneFills(False)
    ring.SetDoNotAllowPads(False)
    ring.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        ls.AddLayer(lay)
    ring.SetLayerSet(ls)
    o = ring.Outline()
    o.NewOutline()
    x0, y0, x1, y1 = outl.bbox(poly)
    for x, y in ((x0 - 20, y0 - 20), (x1 + 20, y0 - 20), (x1 + 20, y1 + 20), (x0 - 20, y1 + 20)):
        o.Append(v(x, y))
    o.NewHole()
    for x, y in inset:
        o.Append(v(x, y), 0, 0)
    board.Add(ring)
    dsn = os.path.join(d, bname + ".dsn")
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise RuntimeError("DSN export failed")
    json.dump(saved, open(os.path.join(d, bname + ".zones.json"), "w"))
    print("route_remote: wrote %s (%d outer zones saved)" % (dsn, len(saved)))


def imp(s, bname):
    d = os.path.join(s["_dir"], bname)
    path = os.path.join(d, bname + ".kicad_pcb")
    ses = os.path.join(d, bname + ".ses")
    saved = json.load(open(os.path.join(d, bname + ".zones.json")))
    board = pcbnew.LoadBoard(path)
    # read the zones before removing anything: in KiCad 10's swig, objects fetched after board.Remove()
    # can come back as bare SwigPyObjects
    zones = list(board.Zones())
    strip = (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu)
    gone = []
    for z in zones:
        if z.GetIsRuleArea():
            continue
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)    # solid to SMD pads, spokes only for THT
        if z.GetLayer() in strip:
            gone.append(z)
    tracks = [t for t in board.GetTracks() if not t.IsLocked()]
    for t in tracks:
        board.Remove(t)
    for z in gone:
        board.Remove(z)
        z.thisown = False                  # do not let Python free a zone the board history may still reference
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise RuntimeError("SES import failed")
    keep_alive = []                       # new zones must outlive the fill (swig ownership)
    for zs in saved:
        z = pcbnew.ZONE(board)
        keep_alive.append(z)
        z.SetLayer(zs["layer"])
        z.SetNet(board.FindNet(zs["net"]))
        z.SetZoneName(zs["name"])
        z.SetAssignedPriority(zs["prio"])
        z.SetLocalClearance(pcbnew.FromMM(0.15))
        z.SetMinThickness(pcbnew.FromMM(0.1))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)   # solid to SMD pads, thermal spokes only for THT
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        sps = pcbnew.SHAPE_POLY_SET()
        sps.NewOutline()
        for x, y in zs["pts"]:
            sps.Append(int(x), int(y))
        z.SetOutline(sps)
        sps.thisown = False                # the zone keeps a pointer to it
        keep_alive.append(sps)
        board.Add(z)
        z.thisown = False
    # no ZONE_FILLER here: it segfaults in KiCad 10.0.8 after zones are removed and re-added from Python;
    # the DRC step (kicad-cli --refill-zones --save-board) fills them
    pcbnew.SaveBoard(path, board)
    print("route_remote: %s: SES imported, planes restored (filled by the DRC step); run DRC next" % bname)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["export", "import"])
    ap.add_argument("spec")
    ap.add_argument("--board", default="main")
    ap.add_argument("--edge", type=float, default=0.25)
    a = ap.parse_args()
    s = specmod.load(a.spec)
    export(s, a.board, a.edge) if a.mode == "export" else imp(s, a.board)


if __name__ == "__main__":
    main()
