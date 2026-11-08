"""One command from spec to checked board files:

    python3 build.py hw/pcb/board.json [--out hw/pcb] [--board main] [--route] [--no-fab] [--strict]

  1. libgen   project symbol/footprint library, pin<->pad<->net cross-check     (stops on error)
  2. schgen   schematic per board
  3. erc      ERC + netlist                                                      (stops on ERC errors)
  4. pcbgen   board, legalized placement, planes, keepouts (KiCad Python)       (stops on placement failure)
  5. route    optional, Freerouting (Java)
  6. drc      DRC + schematic parity; unconnected items are reported, not hidden
  7. exports  GLB (+ STEP with --step), renders, pads.json, Gerbers/BOM/CPL, layer textures

Writes <out>/build-summary.json. Exit code: 0 ok, 1 spec/library/ERC error, 2 placement failure,
3 DRC violations (or, with --strict, any unconnected item: an unrouted board is not finished),
4 release_check failed (with --release).
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import export  # noqa: E402
import kicad_env  # noqa: E402
import libgen  # noqa: E402
import schgen  # noqa: E402
import spec as specmod  # noqa: E402


def kpy(script, args):
    py = kicad_env.kicad_python()
    if not py:
        raise RuntimeError("KiCad's Python (with pcbnew) not found; set KICAD_PYTHON")
    r = subprocess.run([py, os.path.join(HERE, script)] + args, capture_output=True, text=True)
    lines = [ln for ln in (r.stdout + r.stderr).splitlines()
             if not any(k in ln for k in ("assert", "stdpbase", "Gtk-WARNING", "wxWidgets Debug"))]
    print("\n".join(lines[-30:]))
    return r.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out", help="output folder (default: the spec's folder)")
    ap.add_argument("--board", action="append", help="only these boards")
    ap.add_argument("--route", action="store_true",
                    help="autoroute with Freerouting before DRC (long, CPU-heavy: run on a workstation or cloud VM)")
    ap.add_argument("--step", action="store_true", help="also export STEP for CAD (CPU-heavy)")
    ap.add_argument("--no-fab", action="store_true", help="skip Gerbers/BOM/CPL")
    ap.add_argument("--no-render", action="store_true", help="skip kicad-cli renders")
    ap.add_argument("--textures", action="store_true", help="also export layer textures (needs rsvg-convert)")
    ap.add_argument("--strict", action="store_true", help="fail on unconnected items (board must be fully routed)")
    ap.add_argument("--release", action="store_true", help="finish with release_check.py (ready-to-order gate)")
    a = ap.parse_args()
    t0 = time.time()
    s = specmod.load(a.spec)
    out = os.path.abspath(a.out or s["_dir"])
    boards = a.board or list(s["boards"])
    summary = {"spec": s["_path"], "kicad": kicad_env.version(), "boards": {}}

    def done(code, msg):
        summary["result"] = msg
        summary["seconds"] = round(time.time() - t0, 1)
        with open(os.path.join(out, "build-summary.json"), "w") as f:
            json.dump(summary, f, indent=1)
        print("build: %s (%.0f s) -> %s" % (msg, time.time() - t0, os.path.join(out, "build-summary.json")))
        sys.exit(code)

    lib = libgen.build(s, out)
    summary["library"] = lib
    for w in lib["warnings"]:
        print("warning:", w)
    if lib["errors"]:
        for e in lib["errors"]:
            print("ERROR:", e)
        done(1, "library/spec errors: %d" % len(lib["errors"]))
    print("libgen: %d symbols, %d footprints" % (lib["symbols"], lib["footprints"]))

    resolved = json.load(open(os.path.join(out, "resolved.json")))
    for bn in boards:
        rb = summary["boards"].setdefault(bn, {})
        rb["schematic"] = schgen.build(s, out, bn)
        rb["erc"] = export.erc(out, bn)
        print("erc: %s: %d errors, %d warnings %s" % (bn, rb["erc"]["errors"], rb["erc"]["warnings"], rb["erc"]["by_type"]))
        if rb["erc"]["errors"]:
            done(1, "ERC errors on %s (see %s/erc.json)" % (bn, bn))
        if kpy("pcbgen.py", [s["_path"], "--out", out, "--board", bn]) != 0:
            rb["placement"] = json.load(open(os.path.join(out, bn, "placement-report.json")))
            done(2, "placement failed on %s (see %s/placement-report.json)" % (bn, bn))
        rb["placement"] = json.load(open(os.path.join(out, bn, "placement-report.json")))
        if a.route:
            if kpy("route.py", [s["_path"], "--out", out, "--board", bn]) != 0:
                done(3, "routing failed on %s" % bn)
        rb["drc"] = export.drc(out, bn)
        d = rb["drc"]
        print("drc: %s: %d violations (%d errors) %s; %d unconnected; %d parity" % (
            bn, d["violations"], d["errors"], d["by_type"], d["unconnected"], d["parity"]))
        rb["3d"] = export.three_d(out, bn, step=a.step)
        if not a.no_render:
            rb["render"] = export.render(out, bn)
        if not a.no_fab:
            rb["fab"] = export.fab(s, out, bn, resolved[bn])
        if a.textures:
            rb["textures"] = export.textures(out, bn)
    summary["pads"] = export.pads(out, boards)
    bad = [bn for bn in boards if summary["boards"][bn]["drc"]["errors"] or summary["boards"][bn]["drc"]["parity"]]
    if bad:
        done(3, "DRC errors on %s" % ", ".join(bad))
    unrouted = sum(summary["boards"][bn]["drc"]["unconnected"] for bn in boards)
    if unrouted and a.strict:
        done(3, "%d unconnected items: board not routed" % unrouted)
    if a.release:
        r = subprocess.run([sys.executable, os.path.join(HERE, "release_check.py"), s["_path"], "--out", out]
                           + sum([["--board", bn] for bn in boards], []), capture_output=True, text=True)
        print(r.stdout.strip())
        summary["release"] = json.load(open(os.path.join(out, "release-check.json")))
        if r.returncode:
            done(4, "NOT READY TO ORDER (see release-check.json)")
        done(0, "READY TO ORDER")
    done(0, "ok" + (" (UNROUTED: %d unconnected items; placement only; not releasable)" % unrouted if unrouted
                    else ", fully routed; run --release for the order gate"))


if __name__ == "__main__":
    main()
