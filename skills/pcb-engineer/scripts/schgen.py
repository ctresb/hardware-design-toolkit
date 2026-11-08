"""Generate one KiCad schematic per board from the spec (after libgen.py).

Every pin gets a global label with its net name, so the schematic is correct by construction and easy to
regenerate. Parts are laid out in titled blocks ("groups" in the spec). Nets that are driven only by
connectors or batteries get a PWR_FLAG (auto: any net with a power_in pin and no power_out pin).

Writes <out>/<board>/<board>.kicad_sch, .kicad_pro (if missing), sym-lib-table, fp-lib-table.
Pure Python 3.9+. Do not edit the generated schematic by hand: change the spec and regenerate.
"""
import argparse
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sexp  # noqa: E402
import spec as specmod  # noqa: E402
from libgen import symbol_pins  # noqa: E402
from sexp import Q  # noqa: E402

NS = uuid.UUID("3b8f6c1e-5d2a-4c7b-9e10-7a6b5c4d3e2f")


def uid(*parts):
    return Q(str(uuid.uuid5(NS, "/".join(str(p) for p in parts))))


def snap(v):
    return round(round(v / 1.27) * 1.27, 4)


def label(net, x, y, rot, key):
    just = {0: "left", 180: "right", 90: "left", 270: "right"}[int(rot) % 360]
    return ["global_label", Q(net), ["shape", "passive"], ["at", x, y, rot], ["fields_autoplaced", "yes"],
            ["effects", ["font", ["size", 1.0, 1.0]], ["justify", just]], ["uuid", uid(key)],
            ["property", Q("Intersheetrefs"), Q("${INTERSHEET_REFS}"), ["at", x, y, 0],
             ["effects", ["font", ["size", 1.0, 1.0]], ["hide", "yes"]]]]


def instance(board, project, ref, value, lib, sym_name, fp_name, part, unit, x, y, root_uuid, pins):
    props = [("Reference", ref, x, y - 2), ("Value", value, x, y + 2),
             ("Footprint", "%s:%s" % (lib, fp_name) if fp_name else "", x, y), ("Datasheet", "", x, y),
             ("Description", part.get("description", ""), x, y), ("MPN", part.get("mpn", ""), x, y),
             ("Manufacturer", part.get("manufacturer", ""), x, y), ("LCSC", part.get("lcsc", ""), x, y)]
    node = ["symbol", ["lib_id", Q("%s:%s" % (lib, sym_name))], ["at", x, y, 0], ["unit", unit],
            ["exclude_from_sim", "no"], ["in_bom", "yes" if part.get("in_bom", True) else "no"],
            ["on_board", "yes" if part.get("on_board", True) else "no"],
            ["dnp", "yes" if part.get("dnp") else "no"], ["uuid", uid(board, ref, unit)]]
    for i, (k, v, px, py) in enumerate(props):
        eff = ["effects", ["font", ["size", 1.0, 1.0]]]
        if i >= 2:
            eff.append(["hide", "yes"])
        node.append(["property", Q(k), Q(v), ["at", px, py, 0], eff])
    for num in pins:
        node.append(["pin", Q(num), ["uuid", uid(board, ref, "pin", num)]])
    node.append(["instances", ["project", Q(project), ["path", Q("/" + root_uuid), ["reference", Q(ref)], ["unit", unit]]]])
    return node


def build(spec, out, bname):
    b = spec["boards"][bname]
    lib = spec["library"]
    resolved = json.load(open(os.path.join(out, "resolved.json")))[bname]
    symlib = sexp.load(os.path.join(out, "lib", lib + ".kicad_sym"))
    syms = {s[1]: s for s in sexp.find(symlib, "symbol")}
    parts = {p["ref"]: p for p in b["parts"]}
    root_uuid = str(uuid.uuid5(NS, bname))

    used = sorted({resolved[r]["symbol"] for r in resolved} | {"PWR_FLAG"})
    lib_symbols = []
    for name in used:
        s = sexp.parse(sexp.dump(syms[name]))
        s[1] = Q("%s:%s" % (lib, name))
        lib_symbols.append(s)

    items, labels, ncs = [], [], []
    y_cursor = 30.0
    for g in b["groups"]:
        items.append(["text", Q(g["title"]), ["exclude_from_sim", "no"], ["at", 20, y_cursor - 8, 0],
                      ["effects", ["font", ["size", 2.5, 2.5], ["bold", "yes"]], ["justify", "left"]],
                      ["uuid", uid(bname, "title", g["title"])]])
        x_cursor, row_h = 30.0, 0.0
        for ref in g["refs"]:
            if ref not in resolved:
                continue
            part, rp = parts[ref], resolved[ref]
            spins = symbol_pins(syms[rp["symbol"]])
            for unit in rp["units"]:
                upins = [p for p in spins if p[3] == unit or (p[3] == 0 and unit == rp["units"][0])]
                xs = [p[4] for p in upins] or [0]
                ys = [p[5] for p in upins] or [0]
                w, h = (max(xs) - min(xs)) + 30, (max(ys) - min(ys)) + 14
                if x_cursor + w > 560:
                    x_cursor, y_cursor = 30.0, y_cursor + row_h
                    row_h = 0.0
                sx, sy = snap(x_cursor - min(xs) + 12), snap(y_cursor + max(ys) + 6)
                pin_nums = []
                done = set()
                for num, nm, typ, u, px, py, rot in upins:
                    if num not in pin_nums:
                        pin_nums.append(num)
                    wx, wy = round(sx + px, 4), round(sy - py, 4)
                    if (wx, wy) in done:
                        continue
                    done.add((wx, wy))
                    net = rp["pins"].get(num)
                    if net is None:
                        ncs.append(["no_connect", ["at", wx, wy], ["uuid", uid(bname, ref, "nc", num, unit)]])
                    else:
                        lrot = {0: 180, 180: 0, 270: 90, 90: 270}[int(rot) % 360]
                        labels.append(label(net, wx, wy, lrot, "%s/%s/%s/%s" % (bname, ref, num, unit)))
                items.append(instance(bname, bname, ref, part["value"], lib, rp["symbol"], rp["footprint"], part,
                                      unit, sx, sy, root_uuid, pin_nums))
                x_cursor += w
                row_h = max(row_h, h)
        y_cursor += row_h + 20

    # power flags
    if b["pwr_flags"] == "auto":
        drive, need = set(), set()
        for ref, rp in resolved.items():
            for num, net in rp["pins"].items():
                if not net:
                    continue
                t = rp["types"].get(num)
                if t == "power_out":
                    drive.add(net)
                elif t == "power_in":
                    need.add(net)
        flags = sorted(need - drive)
    else:
        flags = list(b["pwr_flags"])
    fx, fy = 30.48, snap(y_cursor)
    flag_sym = syms["PWR_FLAG"]
    for i, net in enumerate(flags):
        ref = "#FLG%02d" % (i + 1)
        node = instance(bname, bname, ref, "PWR_FLAG", lib, "PWR_FLAG", "", {"in_bom": False, "on_board": False},
                        1, fx, fy, root_uuid, [p[0] for p in symbol_pins(flag_sym)])
        items.append(node)
        labels.append(label(net, fx, fy, 90, "%s/flag/%s" % (bname, net)))
        fx += 15.24

    sch = ["kicad_sch", ["version", 20250114], ["generator", Q("eeschema")], ["generator_version", Q("10.0")],
           ["uuid", Q(root_uuid)], ["paper", Q("A1")],
           ["title_block", ["title", Q(b["title"])], ["company", Q(spec.get("company", ""))], ["rev", Q(b["rev"])],
            ["comment", 1, Q("Generated from %s by schgen.py; edit the spec, not this file" % os.path.basename(spec["_path"]))]],
           ["lib_symbols"] + lib_symbols] + items + labels + ncs + [
        ["sheet_instances", ["path", Q("/"), ["page", Q("1")]]], ["embedded_fonts", "no"]]
    d = os.path.join(out, bname)
    os.makedirs(d, exist_ok=True)
    sexp.save(os.path.join(d, bname + ".kicad_sch"), sch)
    with open(os.path.join(d, "sym-lib-table"), "w") as f:
        f.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/../lib/%s.kicad_sym")(options "")(descr "project"))\n)\n' % (lib, lib))
    with open(os.path.join(d, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/../lib/%s.pretty")(options "")(descr "project"))\n)\n' % (lib, lib))
    pro = os.path.join(d, bname + ".kicad_pro")
    if not os.path.exists(pro):
        with open(pro, "w") as f:
            json.dump({"meta": {"filename": bname + ".kicad_pro", "version": 3}}, f, indent=2)
    return {"parts": len(resolved), "labels": len(labels), "no_connects": len(ncs), "pwr_flags": flags}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out", help="output folder (default: the spec's folder)")
    ap.add_argument("--board", action="append", help="board name (default: all)")
    a = ap.parse_args()
    s = specmod.load(a.spec)
    out = os.path.abspath(a.out or s["_dir"])
    for bname in a.board or s["boards"]:
        r = build(s, out, bname)
        print("schgen: %s: %d parts, %d labels, %d no-connects, PWR_FLAG on %s" % (
            bname, r["parts"], r["labels"], r["no_connects"], ", ".join(r["pwr_flags"]) or "none"))


if __name__ == "__main__":
    main()
