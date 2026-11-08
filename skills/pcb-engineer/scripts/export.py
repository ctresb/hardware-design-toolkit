"""Checks and outputs for generated boards, through kicad-cli. Pure Python 3.9+.

    python3 export.py hw/pcb/board.json [--board main] [--what erc,drc,3d,fab,render,pads,textures]

  erc       ERC of the schematic + netlist (pcbgen.py reads the netlist for no-connect pins)
  drc       DRC with schematic parity and zone refill; counts violations and unconnected items separately
  3d        <out>/export/<board>.glb (+ .step with "step"); device origin = file origin; for Blender/CAD
  fab       <out>/fab/<board>/: Gerbers + drill zipped, BOM and CPL in JLCPCB column format,
            stackup.md (stack-up + impedance), order.md, panel-plan.json (+ KiKit panel.json)
  render    <out>/export/<board>_{top,bottom,iso}.png (kicad-cli pcb render) for visual review
  pads      <out>/export/pads.json: every SMD pad per footprint (solder simulation, stencil checks)
  textures  <out>/export/tex/<board>_<F|B>_<cu|mask|silk>.png at 80 px/mm (needs rsvg-convert)
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fabnotes  # noqa: E402
import kicad_env  # noqa: E402
import sexp  # noqa: E402
import spec as specmod  # noqa: E402

OX, OY = 100.0, 100.0


def run(cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode not in (0, 5):          # 5 = violations found (with --exit-code-violations)
        raise RuntimeError("command failed (%d): %s\n%s" % (r.returncode, " ".join(cmd), (r.stderr or r.stdout)[-2000:]))
    return r


def _paths(out, bname):
    d = os.path.join(out, bname)
    return d, os.path.join(d, bname + ".kicad_sch"), os.path.join(d, bname + ".kicad_pcb")


def _count(js, key):
    items = js.get(key, [])
    sev = {}
    for v in items:
        sev[v.get("severity", "?")] = sev.get(v.get("severity", "?"), 0) + 1
    return sev, items


def erc(out, bname):
    cli = kicad_env.kicad_cli()
    d, sch, _ = _paths(out, bname)
    rj = os.path.join(d, "erc.json")
    run([cli, "sch", "erc", "--format", "json", "--severity-all", "-o", rj, sch])
    run([cli, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", os.path.join(d, bname + ".net"), sch])
    js = json.load(open(rj))
    viol = [v for s in js.get("sheets", []) for v in s.get("violations", [])]
    errs = [v for v in viol if v.get("severity") == "error"]
    warns = [v for v in viol if v.get("severity") == "warning"]
    types = {}
    for v in viol:
        types[v.get("type")] = types.get(v.get("type"), 0) + 1
    return {"errors": len(errs), "warnings": len(warns), "by_type": types}


def drc(out, bname):
    cli = kicad_env.kicad_cli()
    d, _, pcb = _paths(out, bname)
    rj = os.path.join(d, "drc.json")
    run([cli, "pcb", "drc", "--format", "json", "--severity-all", "--schematic-parity", "--refill-zones",
         "--save-board", "-o", rj, pcb])
    js = json.load(open(rj))
    types = {}
    for v in js.get("violations", []):
        types[v.get("type")] = types.get(v.get("type"), 0) + 1
    errs = sum(1 for v in js.get("violations", []) if v.get("severity") == "error")
    return {"violations": len(js.get("violations", [])), "errors": errs, "by_type": types,
            "unconnected": len(js.get("unconnected_items", [])),
            "parity": len(js.get("schematic_parity", []))}


def three_d(out, bname, step=True):
    cli = kicad_env.kicad_cli()
    _, _, pcb = _paths(out, bname)
    ex = os.path.join(out, "export")
    os.makedirs(ex, exist_ok=True)
    common = ["--include-tracks", "--include-pads", "--include-zones", "--include-soldermask",
              "--include-silkscreen", "--user-origin", "%gx%gmm" % (OX, OY), "-f"]
    run([cli, "pcb", "export", "glb"] + common + ["-o", os.path.join(ex, bname + ".glb"), pcb])
    res = {"glb": os.path.join(ex, bname + ".glb")}
    if step:     # CPU-heavy (OpenCascade): run it for CAD hand-off, not on every iteration
        run([cli, "pcb", "export", "step", "--subst-models", "--user-origin", "%gx%gmm" % (OX, OY), "-f",
             "-o", os.path.join(ex, bname + ".step"), pcb])
        res["step"] = os.path.join(ex, bname + ".step")
    return res


def render(out, bname, size=(1600, 1200)):
    cli = kicad_env.kicad_cli()
    _, _, pcb = _paths(out, bname)
    ex = os.path.join(out, "export")
    os.makedirs(ex, exist_ok=True)
    files = []
    for name, extra in (("top", ["--side", "top"]), ("bottom", ["--side", "bottom"]),
                        ("iso", ["--side", "top", "--rotate", "-45,0,35", "--perspective"])):
        f = os.path.join(ex, "%s_%s.png" % (bname, name))
        run([cli, "pcb", "render", "--quality", "high", "--background", "opaque", "--use-board-stackup-colors",
             "-w", str(size[0]), "-h", str(size[1]), "--zoom", "0.9"] + extra + ["-o", f, pcb])
        files.append(f)
    return files


def fab(spec, out, bname, resolved):
    """Gerbers + drill (zip), BOM and CPL in the JLCPCB format (also accepted by most fabs)."""
    cli = kicad_env.kicad_cli()
    _, _, pcb = _paths(out, bname)
    b = spec["boards"][bname]
    n = specmod.stackup(b)["layers"]
    fd = os.path.join(out, "fab", bname)
    gd = os.path.join(fd, "gerbers")
    os.makedirs(gd, exist_ok=True)
    for f in os.listdir(gd):
        os.remove(os.path.join(gd, f))
    cu = ["F.Cu"] + ["In%d.Cu" % i for i in range(1, n - 1)] + (["B.Cu"] if n > 1 else [])
    layers = cu + ["F.Paste", "B.Paste", "F.SilkS", "B.SilkS", "F.Mask", "B.Mask", "Edge.Cuts"]
    run([cli, "pcb", "export", "gerbers", "--check-zones", "--subtract-soldermask", "-l", ",".join(layers), "-o", gd + "/", pcb])
    run([cli, "pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--generate-map",
         "--map-format", "gerberx2", "-o", gd + "/", pcb])
    zp = os.path.join(fd, "%s_gerbers.zip" % bname)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(gd)):
            z.write(os.path.join(gd, f), f)
    # CPL (pick and place)
    pos = os.path.join(fd, "pos_raw.csv")
    run([cli, "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp", "-o", pos, pcb])
    parts = {p["ref"]: p for p in b["parts"]}
    rows = list(csv.DictReader(open(pos)))
    cpl = os.path.join(fd, "%s_cpl.csv" % bname)
    with open(cpl, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            ref = r["Ref"]
            if ref in parts and not parts[ref].get("in_bom", True):
                continue
            # same absolute frame as the Gerbers (KiCad writes Y up), so the assembler's alignment matches
            w.writerow([ref, "%.4fmm" % float(r["PosX"]), "%.4fmm" % float(r["PosY"]),
                        "Top" if r["Side"].lower().startswith("top") else "Bottom", r["Rot"]])
    os.remove(pos)
    # BOM grouped by value + footprint + MPN
    groups = {}
    for p in b["parts"]:
        if p["dnp"] or not p.get("in_bom", True) or p["ref"] not in resolved:
            continue
        key = (p["value"], resolved[p["ref"]]["footprint"], p.get("mpn", ""), p.get("lcsc", ""), p.get("manufacturer", ""))
        groups.setdefault(key, []).append(p["ref"])
    bom = os.path.join(fd, "%s_bom.csv" % bname)
    with open(bom, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "Quantity", "Manufacturer", "MPN", "LCSC Part #"])

        def natural(r):
            m = re.match(r"([A-Za-z#]+)(\d+)", r)
            return (m.group(1), int(m.group(2))) if m else (r, 0)

        for (val, fpn, mpn, lcsc, man), refs in sorted(groups.items(), key=lambda kv: natural(sorted(kv[1], key=natural)[0])):
            refs = sorted(refs, key=natural)
            w.writerow([val, ",".join(refs), fpn, len(refs), man, mpn, lcsc])
    notes = fabnotes.write(spec, out, bname)
    return {"gerbers": zp, "bom": bom, "cpl": cpl, "layers": len(layers), "stackup": notes["stackup"],
            "order": notes["order"], "panel": notes["panel"]["mode"]}


def pads_of_board(pcb_path):
    """SMD pads of one .kicad_pcb: {ref: {layer, x, y, rot, x_dev, y_dev, pads: [{n, shape, x, y, a, w, h, paste, cu}]}}.
    x, y, rot: KiCad sheet coordinates (mm, +y down) of the footprint; pad x, y: footprint-local, unrotated.
    x_dev, y_dev: the same footprint position in the device frame (origin at OX, OY, +y up).
    This is the toolkit's single pads exporter; product-render/scripts/kicad_pads.py calls it."""
    t = sexp.load(pcb_path)
    fps = {}
    for fp in sexp.find(t, "footprint"):
        at = sexp.first(fp, "at")
        layer = sexp.first(fp, "layer")[1]
        rot = float(at[3]) if len(at) > 3 else 0.0
        ref = next((n[2] for n in sexp.find(fp, "property") if n[1] == "Reference"), "?")
        plist = []
        for p in sexp.find(fp, "pad"):
            if p[2] != "smd":
                continue
            pa, sz, ly = sexp.first(p, "at"), sexp.first(p, "size"), sexp.first(p, "layers")
            mm = sexp.first(p, "solder_mask_margin")
            plist.append({"n": str(p[1]), "shape": p[3], "x": float(pa[1]), "y": float(pa[2]),
                          "a": (float(pa[3]) if len(pa) > 3 else 0.0) - rot, "w": float(sz[1]), "h": float(sz[2]),
                          "paste": any("Paste" in str(x) for x in ly[1:]), "cu": any("Cu" in str(x) for x in ly[1:]),
                          # solder sim (product-render solder_geom.py): no mask opening -> no fillet;
                          # negative margin shrinks the wettable area
                          "mask": any("Mask" in str(x) for x in ly[1:]),
                          "mask_margin": float(mm[1]) if mm else 0.0})
        fps[str(ref)] = {"layer": str(layer), "x": float(at[1]), "y": float(at[2]), "rot": rot,
                         "x_dev": round(float(at[1]) - OX, 4), "y_dev": round(OY - float(at[2]), 4), "pads": plist}
    return fps


def write_pads(boards, path):
    """boards: {name: .kicad_pcb path}. Writes pads.json and returns a summary."""
    res = {name: pads_of_board(pcb) for name, pcb in boards.items()}
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    json.dump(res, open(path, "w"), indent=1)
    return {"path": path, "footprints": sum(len(v) for v in res.values()),
            "pads": sum(len(f["pads"]) for v in res.values() for f in v.values())}


def pads(out, boards):
    """pads.json for the boards of a spec build: <out>/export/pads.json (format: see pads_of_board)."""
    return write_pads({b: _paths(out, b)[2] for b in boards}, os.path.join(out, "export", "pads.json"))


def textures(out, bname, px_per_mm=80):
    """Layer masks for physically based board materials in Blender (white = layer present)."""
    cli, rsvg = kicad_env.kicad_cli(), kicad_env.rsvg_convert()
    if not rsvg:
        return {"skipped": "rsvg-convert not found"}
    _, _, pcb = _paths(out, bname)
    td = os.path.join(out, "export", "tex")
    os.makedirs(td, exist_ok=True)
    files = []
    for side in "FB":
        for key, layer in (("cu", "%s.Cu"), ("mask", "%s.Mask"), ("silk", "%s.SilkS")):
            svg = os.path.join(td, "%s_%s_%s.svg" % (bname, side, key))
            run([cli, "pcb", "export", "svg", "--mode-single", "--black-and-white", "--exclude-drawing-sheet",
                 "--page-size-mode", "2", "--drill-shape-opt", "2" if key == "cu" else "0",
                 "-l", layer % side, "-o", svg, pcb])
            head = open(svg).read(2000)
            w = float(re.search(r'width="([\d.]+)mm"', head).group(1))
            h = float(re.search(r'height="([\d.]+)mm"', head).group(1))
            png = svg[:-4] + ".png"
            run([rsvg, "-b", "white", "-w", str(int(w * px_per_mm)), "-h", str(int(h * px_per_mm)), "-o", png, svg])
            os.remove(svg)
            files.append(png)
    return {"files": files, "note": "black = layer present on white; invert in the shader"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--board", action="append")
    ap.add_argument("--out")
    ap.add_argument("--what", default="drc,3d,fab,render,pads")
    a = ap.parse_args()
    s = specmod.load(a.spec)
    out = os.path.abspath(a.out or s["_dir"])
    boards = a.board or list(s["boards"])
    resolved = json.load(open(os.path.join(out, "resolved.json")))
    what = a.what.split(",")
    summary = {}
    for bn in boards:
        r = summary.setdefault(bn, {})
        if "erc" in what:
            r["erc"] = erc(out, bn)
        if "drc" in what:
            r["drc"] = drc(out, bn)
        if "3d" in what or "step" in what:
            r["3d"] = three_d(out, bn, step="step" in what)
        if "fab" in what:
            r["fab"] = fab(s, out, bn, resolved[bn])
        if "render" in what:
            r["render"] = render(out, bn)
        if "textures" in what:
            r["textures"] = textures(out, bn)
    if "pads" in what:
        summary["pads"] = pads(out, boards)
    print(json.dumps(summary, indent=1))
    print("export: done (%s)" % ", ".join(what))


if __name__ == "__main__":
    main()
