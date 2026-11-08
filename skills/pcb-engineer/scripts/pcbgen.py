"""Generate the .kicad_pcb of one board from the spec. Run with KiCad's bundled Python (needs `pcbnew`):

    <kicad-python> pcbgen.py hw/pcb/board.json --board main [--out hw/pcb]

Steps: outline -> nets -> footprints at their spec positions -> legalizer -> planes and copper keepouts ->
texts -> stack-up and design rules. Writes <out>/<board>/<board>.kicad_pcb and placement-report.json.

The legalizer moves each non-fixed part along a growing spiral until its courtyard (the real polygon, not
its bounding box)
  - is inside the outline, at least `edge_margin` from the edge,
  - overlaps no other courtyard on the same side (through-hole pads also block the other side),
  - is outside every part keepout of its side (magnets, battery, mic ports, screw bosses...),
  - is outside every exclusive area that does not list it (antenna/RF corner, touch electrode...).
Fixed parts never move; if they collide the report says with what. Exit code 2 if anything failed.

Device frame: mm, origin at the board center, +x right, +y up, seen from the F (top) side.
Tested with KiCad 10.0 (Python 3.9).
"""
import argparse
import json
import math
import os
import sys
import uuid

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outline as outl  # noqa: E402
import sexp  # noqa: E402
import spec as specmod  # noqa: E402
from sexp import Q  # noqa: E402

OX, OY = 100.0, 100.0     # device origin on the KiCad sheet (mm)
CY_TOL = 0.02             # courtyards closer than this count as overlapping (KiCad DRC rounds courtyard outlines)
NS = uuid.UUID("3b8f6c1e-5d2a-4c7b-9e10-7a6b5c4d3e2f")   # same namespace as schgen.py


def sch_uuid(board, ref, unit):
    return str(uuid.uuid5(NS, "%s/%s/%s" % (board, ref, unit)))


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY - y))


def layer_id(board, name):
    lid = board.GetLayerID(name)
    if lid < 0:
        raise ValueError("unknown layer %s" % name)
    return lid


# ---------------------------------------------------------------- geometry of keepouts (device frame)

def shape_polygon(s, n=48):
    if "circle" in s:
        cx, cy, r = s["circle"]
        return outl.circle(r, cx, cy, n)
    if "rect" in s:
        x0, y0, x1, y1 = s["rect"]
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [tuple(p) for p in s["polygon"]]


def courtyard(fp):
    """Bounding box of the courtyard (device frame)."""
    return _bbox_polys(courtyard_polys(fp))


def courtyard_polys(fp):
    """The real courtyard outlines of a footprint as polygons in the device frame (a round coin-cell holder stays
    round, an L-shaped connector stays L-shaped). Falls back to the footprint bounding box."""
    layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    if hasattr(fp, "BuildCourtyardCaches"):
        fp.BuildCourtyardCaches()            # the cache is not rebuilt when the footprint moves or rotates
    sps = fp.GetCourtyard(layer)
    out = []
    for i in range(sps.OutlineCount()):
        ch = sps.Outline(i)
        pts = [(pcbnew.ToMM(ch.CPoint(k).x) - OX, OY - pcbnew.ToMM(ch.CPoint(k).y)) for k in range(ch.PointCount())]
        if len(pts) >= 3:
            out.append(pts)
    if not out:
        bb = fp.GetBoundingBox(False)
        x0, x1 = pcbnew.ToMM(bb.GetX()) - OX, pcbnew.ToMM(bb.GetRight()) - OX
        y1, y0 = OY - pcbnew.ToMM(bb.GetY()), OY - pcbnew.ToMM(bb.GetBottom())
        out = [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
    return out


def _bbox_polys(polys):
    xs = [x for p in polys for x, _ in p]
    ys = [y for p in polys for _, y in p]
    return min(xs), min(ys), max(xs), max(ys)


def _move(polys, dx, dy):
    return [[(x + dx, y + dy) for x, y in p] for p in polys]


def _seg_dist(a, b, c, d):
    """Distance between segments ab and cd (0 if they cross)."""
    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])

    d1, d2, d3, d4 = cross(c, d, a), cross(c, d, b), cross(a, b, c), cross(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0

    def pd(p, q, r):
        dx, dy = r[0] - q[0], r[1] - q[1]
        t = max(0.0, min(1.0, ((p[0] - q[0]) * dx + (p[1] - q[1]) * dy) / (dx * dx + dy * dy or 1e-12)))
        return math.hypot(p[0] - q[0] - t * dx, p[1] - q[1] - t * dy)

    return min(pd(a, c, d), pd(b, c, d), pd(c, a, b), pd(d, a, b))


def poly_gap(A, B):
    """0 if polygons A and B overlap (or touch), else the distance between them."""
    if outl.inside(B, *A[0]) or outl.inside(A, *B[0]):
        return 0.0
    best = 1e9
    for a, b in zip(A, A[1:] + A[:1]):
        for c, d in zip(B, B[1:] + B[:1]):
            best = min(best, _seg_dist(a, b, c, d))
            if best == 0.0:
                return 0.0
    return best


def polys_overlap(PA, PB, gap=0.0):
    ax0, ay0, ax1, ay1 = _bbox_polys(PA)
    bx0, by0, bx1, by1 = _bbox_polys(PB)
    if not (ax0 < bx1 + gap and bx0 < ax1 + gap and ay0 < by1 + gap and by0 < ay1 + gap):
        return False
    return any(poly_gap(a, b) < max(gap, 1e-9) for a in PA for b in PB)


def shape_hits_polys(s, polys):
    """Does a keepout shape (circle, rect or polygon) touch any of the polygons?"""
    if "circle" in s:
        cx, cy, r = s["circle"]
        return any(outl.inside(p, cx, cy) or outl.edge_dist(p, cx, cy) < r for p in polys)
    return polys_overlap([shape_polygon(s)], polys)


def shape_hits_rect(s, rect):
    x0, y0, x1, y1 = rect
    return shape_hits_polys(s, [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]])


def inside_outline(polys, poly, margin):
    """Every courtyard vertex inside the outline at >= margin from the edge, and no outline vertex inside a
    courtyard (catches outline chamfers and notches that cut into a part)."""
    for p in polys:
        for x, y in p:
            if not outl.inside(poly, x, y) or outl.edge_dist(poly, x, y) < margin:
                return False
        if any(outl.inside(p, x, y) for x, y in poly):
            return False
    return True


def overlap(a, b, m=0.0):
    return a[0] < b[2] + m and b[0] < a[2] + m and a[1] < b[3] + m and b[1] < a[3] + m


def set_pose(fp, x, y, rot, side):
    fp.SetOrientationDegrees(rot if side == "F" else (180 - rot) % 360)
    fp.SetPosition(pt(x, y))


def legalize(board, parts, poly, b):
    """Place each part at its spec position or the nearest legal one, testing the real courtyard polygons.
    Through-hole pads block the other side pad by pad; a part whose pads are all on the net of such a pad (a GND
    test point or stitching via under a holder) may sit over it. `allow_overlap: [refs]` on a part allows a
    deliberate overlap with those parts (for example a test pad under a battery holder's open frame)."""
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    margin, gap = b["edge_margin"], b.get("part_gap", 0.0)
    placed = {"F": [], "B": []}           # (name, polys, nets or None, owner ref)
    placed_allow = {}
    rep = {"fixed_collisions": {}, "moved": {}, "failed": [], "keepout_hits": {}}

    def npads(p):
        return len(list(fps[p["ref"]].Pads()))

    def nets_of(fp):
        return {pd.GetNetname() for pd in fp.Pads() if pd.GetNetname()}

    fixed = [p for p in parts if p["fixed"]]
    big = sorted([p for p in parts if not p["fixed"] and npads(p) > 2], key=lambda p: -npads(p))
    small = [p for p in parts if not p["fixed"] and npads(p) <= 2]
    pending_tht = []                       # THT blockers of fixed parts are added after all fixed parts are placed
    first_free = (big + small + [None])[0]
    for p in fixed + big + small:
        if p is first_free and pending_tht:
            for side_, item in pending_tht:
                placed[side_].append(item)
            pending_tht = []
        fp = fps[p["ref"]]
        side = p["side"]
        my_nets = nets_of(fp)
        allow = set(p.get("allow_overlap", []))
        rots = [p["rot"]] if (p["fixed"] or npads(p) > 2 or p.get("lock_rotation")) else [p["rot"], (p["rot"] + 90) % 360]
        base = {}
        for r in rots:
            set_pose(fp, 0, 0, r, side)
            base[r] = courtyard_polys(fp)

        def problems(polys):
            out = []
            if not inside_outline(polys, poly, margin):
                out.append("outside outline / edge margin")
            for k in b["keepouts"]:
                if k.get("parts", True) is False or p["ref"] in k.get("allow", []):
                    continue
                if k.get("side", "both") not in ("both", side):
                    continue
                if shape_hits_polys(k, polys):
                    out.append("keepout " + k.get("name", "?"))
            for e in b["exclusive"]:
                if p["ref"] not in e["only"] and shape_hits_polys(e, polys):
                    out.append("exclusive area " + e.get("name", "?"))
            for name, q, qnets, owner in placed[side]:
                if owner in allow or p["ref"] in placed_allow.get(owner, ()):
                    continue
                if qnets is not None and my_nets and my_nets <= qnets:
                    continue                    # same-net part over a through-hole pad
                if polys_overlap(polys, q, max(gap, CY_TOL)):
                    out.append("overlaps " + name)
            return out

        best = None
        if p["fixed"]:
            r = rots[0]
            polys = _move(base[r], p["x"], p["y"])
            why = problems(polys)
            if why:
                rep["fixed_collisions"][p["ref"]] = why
            best = (p["x"], p["y"], r, polys)
        else:
            step = 0.05
            rmax = p.get("max_move", 2.5 if npads(p) > 2 else 4.0)
            k = 0
            while best is None and k * step <= rmax:
                rad = k * step
                n = max(1, int(2 * math.pi * rad / step))
                for i in range(n):
                    a = 2 * math.pi * i / n
                    x, y = p["x"] + rad * math.cos(a), p["y"] + rad * math.sin(a)
                    for r in rots:
                        polys = _move(base[r], x, y)
                        if not problems(polys):
                            best = (round(x, 3), round(y, 3), r, polys)
                            break
                    if best:
                        break
                k += 1
            if best is None:
                polys = _move(base[rots[0]], p["x"], p["y"])
                rep["failed"].append(p["ref"])
                rep["keepout_hits"][p["ref"]] = problems(polys)
                best = (p["x"], p["y"], rots[0], polys)
        x, y, r, polys = best
        set_pose(fp, x, y, r, side)
        placed[side].append((p["ref"], polys, None, p["ref"]))
        placed_allow[p["ref"]] = allow
        other = "B" if side == "F" else "F"
        olayer = pcbnew.B_Cu if side == "F" else pcbnew.F_Cu
        for pd in fp.Pads():
            if not pd.IsOnLayer(olayer):
                continue
            bbp = pd.GetBoundingBox()
            px0, px1 = pcbnew.ToMM(bbp.GetX()) - OX - 0.2, pcbnew.ToMM(bbp.GetRight()) - OX + 0.2
            py1, py0 = OY - pcbnew.ToMM(bbp.GetY()) + 0.2, OY - pcbnew.ToMM(bbp.GetBottom()) - 0.2
            item = ("%s pad %s (through-hole)" % (p["ref"], pd.GetNumber()),
                    [[(px0, py0), (px1, py0), (px1, py1), (px0, py1)]],
                    {pd.GetNetname()} if pd.GetNetname() else set(), p["ref"])
            if p["fixed"]:
                pending_tht.append((other, item))
            else:
                placed[other].append(item)
        d = math.hypot(x - p["x"], y - p["y"])
        if d > 1e-6 or r != p["rot"]:
            rep["moved"][p["ref"]] = {"x": x, "y": y, "rot": r, "distance": round(d, 3)}
    return rep


# ---------------------------------------------------------------- board items

def add_outline(board, pts):
    for a, c in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(*a))
        s.SetEnd(pt(*c))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.05))
        board.Add(s)


def add_zone(board, net, layer, pts, priority=0, name="", clearance=0.15, min_width=0.1):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(min_width))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.15))
    z.SetThermalReliefSpokeWidth(mm(0.15))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if name:
        z.SetZoneName(name)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(pt(x, y))
    board.Add(z)
    return z


def add_rule_area(board, pts, layers, name, no_copper=True, no_tracks=False, no_vias=True):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowZoneFills(no_copper)
    z.SetDoNotAllowTracks(no_tracks)
    z.SetDoNotAllowVias(no_vias)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for ly in layers:
        ls.AddLayer(ly)
    z.SetLayerSet(ls)
    z.SetZoneName(name)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(pt(x, y))
    board.Add(z)


def add_text(board, s, x, y, layer, size=0.8):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(pt(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    if pcbnew.IsBackLayer(layer):
        t.SetMirrored(True)
    board.Add(t)


def copper_layers(board, n):
    ids = [pcbnew.F_Cu] + [board.GetLayerID("In%d.Cu" % i) for i in range(1, n - 1)] + ([pcbnew.B_Cu] if n > 1 else [])
    return ids


def patch_stackup(path, st):
    """Write the stack-up and finish into the file (the Python API does not expose BOARD_STACKUP)."""
    root = sexp.load(path)
    general = sexp.first(root, "general")
    th = sexp.first(general, "thickness")
    if th:
        th[1] = st["thickness"]
    setup = sexp.first(root, "setup")
    for old in sexp.find(setup, "stackup"):
        setup.remove(old)
    node = ["stackup", ["layer", Q("F.SilkS"), ["type", Q("Top Silk Screen")]],
            ["layer", Q("F.Paste"), ["type", Q("Top Solder Paste")]]]
    for nm, typ, t, mat in st["stack"]:
        ly = ["layer", Q(nm), ["type", Q(typ)], ["thickness", t]]
        if "Mask" in nm:
            ly.append(["color", Q(st["mask_color"])])
        if mat:
            er, tan = (4.5, 0.02) if mat == "FR4" else (3.3, 0.002)
            ly += [["material", Q(mat)], ["epsilon_r", er], ["loss_tangent", tan]]
        node.append(ly)
    node += [["layer", Q("B.Paste"), ["type", Q("Bottom Solder Paste")]],
             ["layer", Q("B.SilkS"), ["type", Q("Bottom Silk Screen")]],
             ["copper_finish", Q(st["finish"])], ["dielectric_constraints", "no"]]
    setup.insert(1, node)
    sexp.save(path, root)


def patch_project(pro, b):
    data = json.load(open(pro)) if os.path.exists(pro) else {}
    ds = data.setdefault("board", {}).setdefault("design_settings", {})
    ds.setdefault("rules", {}).update(b["rules"])
    ns = data.setdefault("net_settings", {})
    r = b["rules"]
    default = {"name": "Default", "clearance": max(0.1, r["min_clearance"]), "track_width": max(0.1, r["min_track_width"]),
               "via_diameter": max(0.4, r["min_via_diameter"]), "via_drill": max(0.2, r["min_through_hole_diameter"]),
               "microvia_diameter": 0.2, "microvia_drill": 0.1, "diff_pair_width": 0.1, "diff_pair_gap": 0.1,
               "wire_width": 6, "bus_width": 12, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
               "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647}
    classes, patterns = [default], []
    for i, (cname, c) in enumerate(b["netclasses"].items()):
        cls = dict(default, name=cname, priority=i)
        for k in ("clearance", "track_width", "via_diameter", "via_drill", "diff_pair_width", "diff_pair_gap"):
            if k in c:
                cls[k] = c[k]
        classes.append(cls)
        patterns += [{"netclass": cname, "pattern": n} for n in c.get("nets", [])]
    ns["classes"] = classes
    ns["netclass_patterns"] = patterns
    data.setdefault("meta", {}).update({"filename": os.path.basename(pro), "version": 3})
    json.dump(data, open(pro, "w"), indent=2)


def build(spec, out, bname):
    b = spec["boards"][bname]
    lib = spec["library"]
    resolved = json.load(open(os.path.join(out, "resolved.json")))[bname]
    pretty = os.path.join(out, "lib", lib + ".pretty")
    d = os.path.join(out, bname)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, bname + ".kicad_pcb")
    st = specmod.stackup(b)

    board = pcbnew.NewBoard(path)
    board.SetCopperLayerCount(st["layers"] if st["layers"] > 1 else 2)
    plane_layers = {pl["layer"] for pl in b["planes"]}
    for i in range(1, st["layers"] - 1):
        nm = "In%d.Cu" % i
        if nm in plane_layers:
            board.SetLayerType(board.GetLayerID(nm), pcbnew.LT_POWER)
    board.GetDesignSettings().SetBoardThickness(mm(st["thickness"]))

    nets = {}

    def net(n):
        if n not in nets:
            nets[n] = pcbnew.NETINFO_ITEM(board, n)
            board.Add(nets[n])
        return nets[n]

    for rp in resolved.values():
        for n in rp["pins"].values():
            if n:
                net(n)
    # unconnected pins get the schematic's "unconnected-(REF-PIN-PadN)" net, so DRC parity passes
    nc_net = {}
    netfile = os.path.join(d, bname + ".net")
    if os.path.exists(netfile):
        for n, nodes in sexp.netlist(netfile).items():
            if n.startswith("unconnected-"):
                for ref, pin, _f in nodes:
                    nc_net[(ref, pin)] = n
                    net(n)

    poly = outl.build(b["outline"], spec["_dir"])
    add_outline(board, poly)

    parts = [p for p in b["parts"] if p["ref"] in resolved and p.get("on_board", True)]
    for p in parts:
        rp = resolved[p["ref"]]
        fp = pcbnew.FootprintLoad(pretty, rp["footprint"])
        if fp is None:
            raise RuntimeError("footprint %s not found in %s" % (rp["footprint"], pretty))
        fp.SetFPID(pcbnew.LIB_ID(lib, rp["footprint"]))
        fp.SetReference(p["ref"])
        fp.SetValue(p["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + sch_uuid(bname, p["ref"], rp["units"][0])))
        fp.SetSheetname("Root")
        fp.SetSheetfile(bname + ".kicad_sch")
        for k, key in (("MPN", "mpn"), ("Manufacturer", "manufacturer"), ("LCSC", "lcsc"), ("Description", "description")):
            fp.SetField(k, p.get(key, ""))       # always set: DRC parity compares symbol and footprint fields
        for f in fp.GetFields():
            if f.GetName() != "Reference":
                f.SetVisible(False)
        if p["dnp"]:
            fp.SetDNP(True)
        if not p.get("in_bom", True):
            fp.SetExcludedFromBOM(True)
        board.Add(fp)
        set_pose(fp, p["x"], p["y"], p["rot"], "F")
        if p["side"] == "B":
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        for pad in fp.Pads():
            num = pad.GetNumber()
            n = rp["pins"].get(num) or nc_net.get((p["ref"], num))
            if n:
                pad.SetNet(net(n))

    rep = legalize(board, parts, poly, b)

    cu = copper_layers(board, st["layers"])
    for i, pl in enumerate(b["planes"]):
        pts = shape_polygon(pl) if any(k in pl for k in ("circle", "rect", "polygon")) else poly
        if pl.get("inset"):
            pts = outl.offset(pts, pl["inset"])
        add_zone(board, net(pl["net"]), layer_id(board, pl["layer"]), pts, pl.get("priority", 0),
                 pl.get("name", "%s %s" % (pl["net"], pl["layer"])), pl.get("clearance", 0.15))
    for k in b["keepouts"]:
        if k.get("copper"):
            lays = cu if k.get("layers", "all") == "all" else [layer_id(board, x) for x in k["layers"]]
            add_rule_area(board, shape_polygon(k), lays, k.get("name", "keepout"),
                          no_tracks=k.get("no_tracks", False), no_vias=k.get("no_vias", True))
    for t in b["texts"]:
        add_text(board, t["text"], t.get("x", 0), t.get("y", 0), layer_id(board, t.get("layer", "F.Fab")), t.get("size", 0.8))

    pcbnew.SaveBoard(path, board)
    patch_stackup(path, st)
    patch_project(os.path.join(d, bname + ".kicad_pro"), b)
    rep["board"] = bname
    rep["outline_bbox"] = [round(v, 3) for v in outl.bbox(poly)]
    with open(os.path.join(d, "placement-report.json"), "w") as f:
        json.dump(rep, f, indent=1)
    ok = not rep["failed"] and not rep["fixed_collisions"]
    worst = max([v["distance"] for v in rep["moved"].values()] or [0])
    print("pcbgen: %s: %d parts, %d moved (max %.2f mm), failed %s, fixed collisions %s -> %s" % (
        bname, len(parts), len(rep["moved"]), worst, rep["failed"] or "none",
        list(rep["fixed_collisions"]) or "none", "ok" if ok else "PLACEMENT PROBLEMS"))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--board", action="append")
    ap.add_argument("--out")
    a = ap.parse_args()
    s = specmod.load(a.spec)
    out = os.path.abspath(a.out or s["_dir"])
    ok = all(build(s, out, bn) for bn in (a.board or s["boards"]))
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
