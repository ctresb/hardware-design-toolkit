"""Release gate: fails unless every board is ready to order with no further changes.

    python3 release_check.py hw/pcb/board.json [--out hw/pcb] [--board main]

Checks, per board, on the files on disk (it does not regenerate anything):
  routed        DRC report has 0 unconnected items and the board has tracks
  drc           0 errors, 0 schematic-parity issues, warnings only of allowed types (silkscreen cosmetics)
  erc           0 errors, warnings only PWR_FLAG pin-type notes
  fresh         drc.json and the fab zip are newer than the .kicad_pcb (the checks ran on this board)
  placement     no failed part, no fixed-part collision
  gerbers       zip has every copper layer of the stack-up, both masks, paste, outline, PTH and NPTH drill
  bom/cpl       both exist; the CPL lists exactly the populated BOM parts; every BOM line has an assembler
                part number (lcsc) or is marked consigned, and an MPN or LCSC number
  notes         stackup.md and order.md exist; impedance notes exist for every impedance net class
  panel         board meets the assembler's minimum size, or a panel is planned (fab service or KiKit files)
  fiducials     >= 2 fiducials per assembled side on the board, or fiducials on the panel rails
  footprints    every generated footprint cites its land-pattern source in its description
Writes <out>/release-check.json. Exit 0 = ready to order, 1 = not ready (the list says why).
"""
import argparse
import csv
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sexp  # noqa: E402
import spec as specmod  # noqa: E402

ALLOWED_DRC_WARNINGS = {"silk_overlap", "silk_over_copper", "silk_edge_clearance", "text_height", "text_thickness"}


def check_board(spec, out, bname):
    b = spec["boards"][bname]
    fails, notes = [], []
    d = os.path.join(out, bname)
    pcb = os.path.join(d, bname + ".kicad_pcb")
    fd = os.path.join(out, "fab", bname)

    def need(path, what):
        if not os.path.exists(path):
            fails.append("%s missing (%s)" % (what, os.path.relpath(path, out)))
            return False
        return True

    if not need(pcb, "board"):
        return fails, notes
    allowed = ALLOWED_DRC_WARNINGS | set(b.get("release", {}).get("allow_drc_warnings", []))

    # DRC / routing
    if need(os.path.join(d, "drc.json"), "DRC report"):
        js = json.load(open(os.path.join(d, "drc.json")))
        errs = [v for v in js.get("violations", []) if v.get("severity") == "error"]
        warns = [v for v in js.get("violations", []) if v.get("severity") != "error" and v.get("type") not in allowed]
        if errs:
            fails.append("DRC: %d errors (%s)" % (len(errs), ", ".join(sorted({v["type"] for v in errs}))))
        if warns:
            fails.append("DRC: %d warnings not allowed (%s)" % (len(warns), ", ".join(sorted({v["type"] for v in warns}))))
        if js.get("schematic_parity"):
            fails.append("DRC: %d schematic parity issues" % len(js["schematic_parity"]))
        if js.get("unconnected_items"):
            fails.append("not routed: %d unconnected items" % len(js["unconnected_items"]))
        if os.path.getmtime(os.path.join(d, "drc.json")) + 5 < os.path.getmtime(pcb):
            fails.append("DRC report is older than the board: run DRC again")
    root = sexp.load(pcb)
    if not any(isinstance(x, list) and x and x[0] in ("segment", "arc") for x in root):
        fails.append("board has no tracks")

    # ERC
    if need(os.path.join(d, "erc.json"), "ERC report"):
        js = json.load(open(os.path.join(d, "erc.json")))
        viol = [v for s in js.get("sheets", []) for v in s.get("violations", [])]
        errs = [v for v in viol if v.get("severity") == "error"]
        warns = [v for v in viol if v.get("severity") != "error" and not (
            v.get("type") == "pin_to_pin" and any("#FLG" in i.get("description", "") for i in v.get("items", [])))]
        if errs:
            fails.append("ERC: %d errors" % len(errs))
        if warns:
            fails.append("ERC: %d warnings (%s)" % (len(warns), ", ".join(sorted({v["type"] for v in warns}))))

    parts = {p["ref"]: p for p in b["parts"]}

    # placement
    if need(os.path.join(d, "placement-report.json"), "placement report"):
        rep = json.load(open(os.path.join(d, "placement-report.json")))
        if rep.get("failed") or rep.get("fixed_collisions"):
            fails.append("placement: failed %s, fixed collisions %s" % (rep.get("failed"), list(rep.get("fixed_collisions", {}))))

    # gerbers
    st = specmod.stackup(b)
    zp = os.path.join(fd, "%s_gerbers.zip" % bname)
    if need(zp, "Gerber zip"):
        if os.path.getmtime(zp) + 5 < os.path.getmtime(pcb):
            fails.append("Gerber zip is older than the board: export fab outputs again")
        names = [n.lower() for n in zipfile.ZipFile(zp).namelist()]
        cu = ["f_cu"] + ["in%d_cu" % i for i in range(1, st["layers"] - 1)] + (["b_cu"] if st["layers"] > 1 else [])
        want = cu + ["f_mask", "b_mask", "f_paste", "edge_cuts"]
        miss = [w for w in want if not any(w in n for n in names)]
        if not any("npth" in n for n in names) or not any(n.endswith(".drl") and "npth" not in n for n in names):
            miss.append("PTH and NPTH drill files")
        if miss:
            fails.append("Gerber zip lacks: %s" % ", ".join(miss))

    # BOM / CPL
    populated = {p["ref"] for p in b["parts"] if not p["dnp"] and p.get("in_bom", True)}
    bom, cpl = os.path.join(fd, "%s_bom.csv" % bname), os.path.join(fd, "%s_cpl.csv" % bname)
    if need(bom, "BOM") and need(cpl, "CPL"):
        rows = list(csv.DictReader(open(bom)))
        bom_refs = {r.strip() for row in rows for r in row["Designator"].split(",") if r.strip()}
        cpl_refs = {row["Designator"] for row in csv.DictReader(open(cpl))}
        if bom_refs != populated:
            fails.append("BOM refs differ from populated parts: missing %s, extra %s" % (
                sorted(populated - bom_refs), sorted(bom_refs - populated)))
        if cpl_refs != bom_refs:
            fails.append("CPL refs differ from BOM: missing %s, extra %s" % (sorted(bom_refs - cpl_refs), sorted(cpl_refs - bom_refs)))
        no_src = sorted(r for r in populated if not parts[r].get("lcsc") and not parts[r].get("consign"))
        if no_src:
            fails.append("no assembler part number (lcsc) and not consigned: %s" % ", ".join(no_src))
        no_pn = sorted(r for r in populated if not parts[r].get("mpn") and not parts[r].get("lcsc"))
        if no_pn:
            fails.append("no MPN or LCSC number: %s" % ", ".join(no_pn))

    # notes
    if need(os.path.join(fd, "stackup.md"), "stack-up notes"):
        s = open(os.path.join(fd, "stackup.md")).read()
        for cname, c in b["netclasses"].items():
            if c.get("impedance") and cname not in s:
                fails.append("stackup.md has no impedance line for net class %s" % cname)
    need(os.path.join(fd, "order.md"), "order notes")

    # panel
    pp_path = os.path.join(fd, "panel-plan.json")
    if need(pp_path, "panel plan"):
        pp = json.load(open(pp_path))
        if pp["needed"] and pp["mode"] == "none":
            fails.append("board %.1f × %.1f mm is below the assembler minimum and no panel is planned" % tuple(pp["board"]))
        if pp["mode"] != "none" and not pp.get("meets_min", True):
            fails.append("panel %.1f × %.1f mm is still below the assembler minimum" % tuple(pp["panel"]))
        if pp["mode"] == "kikit" and not os.path.exists(os.path.join(fd, "panel", bname + "_panel.kicad_pcb")):
            fails.append("KiKit panel not generated: run %s" % pp.get("command", "kikit panelize"))
        rails_fid = pp["mode"] != "none" and pp.get("fiducials", "rails") == "rails"
    else:
        rails_fid = False

    # fiducials
    if not rails_fid:
        for side in sorted({parts[r]["side"] for r in populated} if populated else []):
            n = sum(1 for p in b["parts"] if p.get("fiducial") and p["side"] == side)
            if n < 2:
                fails.append("side %s: %d fiducials on the board (need >= 2, or fiducials on panel rails)" % (side, n))

    # generated footprints cite a source
    for name, f in spec["footprints"].items():
        dsc = f.get("description", "").lower()
        if not any(k in dsc for k in ("datasheet", "figure", "fig.", "land pattern", "drawing", "app note")):
            fails.append("footprint %s: description does not cite its land-pattern source" % name)
    return fails, notes


def _ellipk_agm(k: float) -> float:
    """Complete elliptic integral of the first kind K(k) via arithmetic-geometric mean."""
    import math
    k = max(0.0, min(1.0 - 1e-12, float(k)))
    a, g = 1.0, math.sqrt(max(1e-15, 1.0 - k * k))
    for _ in range(25):
        a, g = 0.5 * (a + g), math.sqrt(a * g)
        if abs(a - g) < 1e-15:
            break
    return math.pi / (2.0 * a)


def cpwg_impedance_ohm(w_mm: float, s_mm: float, h_mm: float, er: float = 4.4) -> float:
    """Closed-form grounded coplanar waveguide (CPWG) characteristic impedance Z0 in ohms."""
    import math
    a = float(w_mm) / 2.0
    b = a + float(s_mm)
    h = float(h_mm)
    k = a / b
    kp = math.sqrt(max(1e-12, 1.0 - k * k))
    k1 = math.tanh(math.pi * a / (2.0 * h)) / math.tanh(math.pi * b / (2.0 * h))
    k1p = math.sqrt(max(1e-12, 1.0 - k1 * k1))
    ratio_k = _ellipk_agm(k) / _ellipk_agm(kp)
    ratio_k1 = _ellipk_agm(k1) / _ellipk_agm(k1p)
    q_tilde = ratio_k1 / ratio_k
    er_eff = (1.0 + float(er) * q_tilde) / (1.0 + q_tilde)
    z0 = (60.0 * math.pi / math.sqrt(er_eff)) / (ratio_k + ratio_k1)
    return round(z0, 2)


def check_thermal_rise(t_amb_c: float, p_diss_w: float, r_theta_ja_c_per_w: float, t_j_max_c: float = 125.0) -> dict:
    """Compute junction temperature Tj = Tamb + P_diss * R_theta_JA and verify margin."""
    delta_t = float(p_diss_w) * float(r_theta_ja_c_per_w)
    t_j = float(t_amb_c) + delta_t
    margin = float(t_j_max_c) - t_j
    return {
        "delta_t_c": round(delta_t, 2),
        "t_j_c": round(t_j, 2),
        "margin_c": round(margin, 2),
        "ok": t_j <= float(t_j_max_c),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out")
    ap.add_argument("--board", action="append")
    a = ap.parse_args()
    s = specmod.load(a.spec)
    out = os.path.abspath(a.out or s["_dir"])
    res, total = {}, 0
    for bn in a.board or s["boards"]:
        fails, _ = check_board(s, out, bn)
        res[bn] = {"ready": not fails, "failures": fails}
        total += len(fails)
        print("%s: %s" % (bn, "READY TO ORDER" if not fails else "NOT READY"))
        for f in fails:
            print("  - " + f)
    json.dump(res, open(os.path.join(out, "release-check.json"), "w"), indent=1)
    print("release_check: %s (%d problems) -> %s" % ("ready" if not total else "NOT READY", total, os.path.join(out, "release-check.json")))
    sys.exit(0 if not total else 1)


if __name__ == "__main__":
    main()
