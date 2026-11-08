"""Autoroute a board with Freerouting in three steps that can run on different machines. KiCad's Python:

    <kicad-python> route.py export hw/pcb/board.json --board main      -> main/main.dsn + main/main.zones.json
    (any machine with Java)  java -jar freerouting.jar -de main.dsn -do main.ses -mp 60   (exact line: route_cmd)
    <kicad-python> route.py import hw/pcb/board.json --board main      <- main/main.ses, pours restored + refilled
    <kicad-python> route.py run    hw/pcb/board.json --board main      all three steps on this machine

`run` is the default when no step is given (`route.py hw/pcb/board.json --board main`), as build.py calls it.

`export` removes every unlocked track and every copper pour except inner-layer planes of the nets in --keep-planes
(default GND: the router then drops vias onto that plane), and adds a temporary keepout ring `--edge` mm wide on all
copper layers, because Freerouting does not apply KiCad's copper-to-edge rule. The removed pours are written to
<board>.zones.json and restored by `import`. `export` does not change the board file.

Freerouting versions (references/workflow.md, "Freerouting versions"):
  - 1.9.0 needs Java 17+. It opens a window, so a headless Linux machine runs it under `xvfb-run` (done here).
    It routed a dense 28 mm 4-layer board further than 2.5.0.
  - 2.x needs the Java its class files were built for (2.5.0: Java 25). It stops after about 19 passes when the
    score stops improving, so dense boards can stay partially routed.
`kicad_env.py` reads the Java version a jar needs and refuses a Java that is too old.

KiCad 10 swig: zone outlines are rebuilt through a SHAPE_POLY_SET, removed zones and new zones are handed to the
board (thisown = False), and zones are filled by `kicad-cli pcb drc --refill-zones --save-board`, not by
pcbnew.ZONE_FILLER, which can segfault after zones are removed and re-added from Python.
Autorouting is a first pass for low-speed nets. Route RF feeds, crystals, regulator loops and impedance-controlled
nets by hand first and lock them. `finish.py` closes the last plane connections and single nets.
Tested with KiCad 10.0.8, Freerouting 1.9.0 (Java 21, xvfb) and 2.5.0 (Java 25).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_env  # noqa: E402
import outline as outl  # noqa: E402
import spec as specmod  # noqa: E402

OX, OY = 100.0, 100.0


def v(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY - y))


def _paths(out, bname):
    d = os.path.join(out, bname)
    return (d, os.path.join(d, bname + ".kicad_pcb"), os.path.join(d, bname + ".dsn"),
            os.path.join(d, bname + ".ses"), os.path.join(d, bname + ".zones.json"))


def _restorable(board, keep_planes):
    """Pours that leave the DSN: all of them except inner-layer planes of the kept nets."""
    outer = (pcbnew.F_Cu, pcbnew.B_Cu)
    return [z for z in list(board.Zones()) if not z.GetIsRuleArea()
            and not (z.GetLayer() not in outer and z.GetNetname() in keep_planes)]


def _num(f, default):
    try:
        val = f()
        return int(val) if val is not None else default
    except Exception:
        return default


def export(spec, out, bname, edge=0.25, keep_planes=("GND",)):
    b = spec["boards"][bname]
    _d, path, dsn, ses, zjs = _paths(out, bname)
    board = pcbnew.LoadBoard(path)
    for t in [t for t in board.GetTracks() if not t.IsLocked()]:
        board.Remove(t)
    saved = []
    for z in _restorable(board, set(keep_planes)):
        poly = z.Outline()
        chains = []
        for i in range(poly.OutlineCount()):
            ch = poly.Outline(i)
            chains.append([[ch.CPoint(k).x, ch.CPoint(k).y] for k in range(ch.PointCount())])
        saved.append({"net": z.GetNetname(), "layer": board.GetLayerName(z.GetLayer()), "name": z.GetZoneName(),
                      "prio": _num(z.GetAssignedPriority, 0), "min_width": _num(z.GetMinThickness, pcbnew.FromMM(0.1)),
                      "outlines": chains})
        board.Remove(z)
        z.thisown = False
    poly = outl.build(b["outline"], spec["_dir"])
    inset = outl.offset(poly, edge)
    ring = pcbnew.ZONE(board)
    ring.SetIsRuleArea(True)
    ring.SetDoNotAllowTracks(True)
    ring.SetDoNotAllowVias(True)
    ring.SetDoNotAllowZoneFills(False)
    ring.SetDoNotAllowPads(False)
    ring.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for lid in board.GetEnabledLayers().CuStack():
        ls.AddLayer(lid)
    ring.SetLayerSet(ls)
    sps = pcbnew.SHAPE_POLY_SET()
    sps.NewOutline()
    x0, y0, x1, y1 = outl.bbox(poly)
    for x, y in ((x0 - 20, y0 - 20), (x1 + 20, y0 - 20), (x1 + 20, y1 + 20), (x0 - 20, y1 + 20)):
        p = v(x, y)
        sps.Append(p.x, p.y)
    sps.NewHole()
    for x, y in inset:
        p = v(x, y)
        sps.Append(p.x, p.y, 0, 0)
    ring.SetOutline(sps)
    sps.thisown = False
    board.Add(ring)
    ring.thisown = False
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise RuntimeError("DSN export failed")
    with open(zjs, "w") as f:
        json.dump(saved, f)
    if os.path.exists(ses):
        os.remove(ses)
    print("route: export %s: %s (%d pours saved to %s; planes kept in the DSN: %s)"
          % (bname, dsn, len(saved), os.path.basename(zjs), ", ".join(keep_planes) or "none"))
    return dsn


def route_cmd(java, jar, dsn, ses, passes):
    """Freerouting command for this jar. 1.x opens a window: on headless Linux it runs under xvfb-run."""
    ver = kicad_env.freerouting_version(jar) or ""
    if ver.startswith("1."):
        cmd = [java, "-jar", jar, "-de", dsn, "-do", ses, "-mp", str(passes)]
        if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
            xvfb = shutil.which("xvfb-run")
            if not xvfb:
                raise RuntimeError("Freerouting %s needs a display: install xvfb (xvfb-run), or use 2.x" % ver)
            cmd = [xvfb, "-a"] + cmd
        return cmd
    return [java, "-Djava.awt.headless=true", "-jar", jar, "-de", dsn, "-do", ses, "-mp", str(passes),
            "--gui.enabled=false"]


def run_freerouting(dsn, ses, passes=60, timeout=3000):
    java, jar = kicad_env.java(), kicad_env.freerouting_jar()
    if not java or not jar:
        raise RuntimeError("routing needs Java and the Freerouting jar (run toolchain-setup); java=%s jar=%s" % (java, jar))
    need, have = kicad_env.jar_java_required(jar), kicad_env.java_major(java)
    if need and have and have < need:
        raise RuntimeError("%s needs Java %d, found Java %d at %s (install it, or use Freerouting 1.9.0)"
                           % (os.path.basename(jar), need, have, java))
    cmd = route_cmd(java, jar, dsn, ses, passes)
    print(" ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    tail = [ln for ln in (r.stdout + r.stderr).splitlines() if any(k in ln for k in ("INFO", "WARN", "ERROR"))]
    print("\n".join(tail[-12:]))
    if not os.path.exists(ses):
        raise RuntimeError("Freerouting produced no .ses (exit %d)" % r.returncode)


def refill(path):
    cli = kicad_env.kicad_cli()
    if not cli:
        print("route: kicad-cli not found; refill the zones in KiCad (B) or with DRC --refill-zones")
        return
    rpt = os.path.splitext(path)[0] + ".refill.rpt"
    subprocess.run([cli, "pcb", "drc", "--refill-zones", "--save-board", "-o", rpt, path],
                   capture_output=True, text=True, timeout=600)
    if os.path.exists(rpt):
        os.remove(rpt)


def imp(spec, out, bname, fill=True):
    _d, path, _dsn, ses, zjs = _paths(out, bname)
    if not os.path.exists(ses):
        raise RuntimeError("no %s: route the DSN first and copy the .ses next to the board" % ses)
    saved = json.load(open(zjs)) if os.path.exists(zjs) else []
    board = pcbnew.LoadBoard(path)
    # collect every zone before removing anything: in KiCad 10's swig, objects fetched after board.Remove()
    # can come back as bare SwigPyObjects
    keys = {(z["layer"], z["net"], z["name"]) for z in saved}
    gone = [z for z in list(board.Zones()) if not z.GetIsRuleArea()
            and (board.GetLayerName(z.GetLayer()), z.GetNetname(), z.GetZoneName()) in keys]
    for t in [t for t in board.GetTracks() if not t.IsLocked()]:
        board.Remove(t)
    for z in gone:
        board.Remove(z)
        z.thisown = False
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise RuntimeError("SES import failed")
    keep_alive = []                                   # new zones and outlines must outlive SaveBoard
    for zs in saved:
        chains = zs.get("outlines") or [zs.get("pts", [])]
        if not chains or not chains[0]:
            continue
        z = pcbnew.ZONE(board)
        z.SetLayer(board.GetLayerID(zs["layer"]))
        z.SetNet(board.FindNet(zs["net"]))
        z.SetZoneName(zs["name"])
        z.SetAssignedPriority(int(zs.get("prio", 0)))
        z.SetLocalClearance(pcbnew.FromMM(0.15))
        z.SetMinThickness(int(zs.get("min_width", pcbnew.FromMM(0.1))))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)    # solid to SMD pads, thermal spokes for THT
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        sps = pcbnew.SHAPE_POLY_SET()
        sps.NewOutline()
        for x, y in chains[0]:
            sps.Append(int(x), int(y))
        z.SetOutline(sps)
        sps.thisown = False
        board.Add(z)
        z.thisown = False
        keep_alive += [z, sps]
    pcbnew.SaveBoard(path, board)
    if fill:
        refill(path)
    print("route: import %s: SES imported, %d pours restored%s; run DRC next (unconnected items = not done)"
          % (bname, len(saved), " and refilled" if fill else ""))


def main():
    argv = sys.argv[1:]
    mode = "run"
    if argv and argv[0] in ("export", "import", "run"):
        mode = argv.pop(0)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--board", action="append")
    ap.add_argument("--out")
    ap.add_argument("--passes", type=int, default=60)
    ap.add_argument("--edge", type=float, default=0.25, help="copper-to-edge keepout for the run (mm)")
    ap.add_argument("--keep-planes", default="GND", help="nets whose inner-layer planes stay in the DSN (comma list)")
    ap.add_argument("--no-fill", action="store_true", help="import: do not refill zones with kicad-cli")
    a = ap.parse_args(argv)
    s = specmod.load(a.spec)
    out = os.path.abspath(a.out or s["_dir"])
    keep = tuple(x for x in a.keep_planes.split(",") if x)
    for bn in a.board or s["boards"]:
        if mode in ("export", "run"):
            dsn = export(s, out, bn, a.edge, keep)
        if mode == "run":
            run_freerouting(dsn, _paths(out, bn)[3], a.passes)
        if mode in ("import", "run"):
            imp(s, out, bn, fill=not a.no_fill)


if __name__ == "__main__":
    main()
