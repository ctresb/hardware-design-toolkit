"""Build the project's own KiCad library from the spec, and resolve every pin to a net.

- Symbols: copied from KiCad's standard libraries (or a vendor .kicad_sym listed in "sym_libs"), with `extends`
  resolved; or generated from a pin table in "symbols".
- Footprints: copied from KiCad's standard .pretty libraries (or "fp_libs"); or generated from a pad table in
  "footprints", with a simple VRML body so the 3D export has the right envelope.
- Cross-checks: every symbol pin must exist as a footprint pad; every pin must have a net, an explicit null
  (no connect) or `nc_rest`. Pins can be keyed by number or by pin name (a name maps to all pins with it).

Writes <out>/lib/<library>.kicad_sym, <out>/lib/<library>.pretty/, <out>/lib/3d/, <out>/resolved.json.
Pure Python 3.9+.
"""
import argparse
import copy
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_env  # noqa: E402
import sexp  # noqa: E402
import spec as specmod  # noqa: E402
from sexp import Q  # noqa: E402
from stepbox import write_step_box  # noqa: E402

FMT = 20250114          # file format version written (KiCad 9/10 read it)
SILK = {"F.SilkS", "B.SilkS"}


class LibError(RuntimeError):
    pass


# ---------------------------------------------------------------- symbols

_sym_cache = {}


def _sym_file(spec, lib):
    if lib in spec["sym_libs"]:
        return os.path.join(spec["_dir"], spec["sym_libs"][lib])
    d = kicad_env.symbol_dir()
    if not d:
        raise LibError("KiCad symbol directory not found (set KICAD_SYMBOL_DIR)")
    return os.path.join(d, lib + ".kicad_sym")


def _lib_symbols(path):
    if path not in _sym_cache:
        if not os.path.exists(path):
            raise LibError("symbol library not found: %s" % path)
        root = sexp.load(path)
        _sym_cache[path] = {s[1]: s for s in sexp.find(root, "symbol")}
    return _sym_cache[path]


def _resolve_symbol(path, name, new_name):
    syms = _lib_symbols(path)
    if name not in syms:
        raise LibError("symbol %s not in %s" % (name, os.path.basename(path)))
    s = syms[name]
    ext = sexp.first(s, "extends")
    if ext:
        base = _resolve_symbol(path, ext[1], new_name)
        own = {p[1]: p for p in sexp.find(s, "property")}
        out = []
        for item in base:
            if isinstance(item, list) and item and item[0] == "property" and item[1] in own:
                out.append(copy.deepcopy(own.pop(item[1])))
            else:
                out.append(item)
        # derived-only properties go right after the last property
        idx = max(i for i, x in enumerate(out) if isinstance(x, list) and x and x[0] == "property") + 1
        for p in own.values():
            out.insert(idx, copy.deepcopy(p))
            idx += 1
        return out
    s = copy.deepcopy(s)
    old = s[1]
    s[1] = Q(new_name)
    for u in sexp.find(s, "symbol"):
        u[1] = Q(new_name + u[1][len(old):])
    return s


def _set_prop(sym, key, value):
    for p in sexp.find(sym, "property"):
        if p[1] == key:
            p[2] = Q(value)
            return
    idx = max(i for i, x in enumerate(sym) if isinstance(x, list) and x and x[0] == "property") + 1
    sym.insert(idx, ["property", Q(key), Q(value), ["at", 0, 0, 0], ["effects", ["font", ["size", 1.27, 1.27]], ["hide", "yes"]]])


def _font(size=1.27):
    return ["effects", ["font", ["size", size, size]]]


def _prop(name, value, x=0.0, y=0.0, hide=False):
    eff = _font()
    if hide:
        eff.append(["hide", "yes"])
    return ["property", Q(name), Q(value), ["at", x, y, 0], eff]


def generate_symbol(name, d):
    """d: {"ref": "U", "description": "...", "datasheet": "...", "pins": [[num, name, type, side], ...]}
    side is L, R, T or B; type is a KiCad electrical type (input, output, bidirectional, power_in, power_out,
    passive, tri_state, open_collector, no_connect, ...)."""
    pins = [tuple(p) for p in d["pins"]]
    for p in pins:
        if len(p) != 4 or p[3] not in "LRTB":
            raise LibError("symbol %s: pin rows are [number, name, type, side L|R|T|B]: %r" % (name, p))
    side = {s: [p for p in pins if p[3] == s] for s in "LRTB"}
    rows = max(len(side["L"]), len(side["R"]), 1)
    cols = max(len(side["T"]), len(side["B"]), 1)
    w = round(max(15.24, 2.54 * (cols + 3)) / 2.54) * 2.54
    h = round(2.54 * (rows + 1) / 2.54) * 2.54
    x0, y0 = -w / 2, h / 2
    body = [["rectangle", ["start", x0, y0], ["end", -x0, -y0],
             ["stroke", ["width", 0.254], ["type", "default"]], ["fill", ["type", "background"]]]]

    def pin(p, x, y, rot):
        num, nm, typ, _ = p
        return ["pin", typ, "line", ["at", round(x, 4), round(y, 4), rot], ["length", 2.54],
                ["name", Q(nm), _font()], ["number", Q(num), _font()]]

    pl = []
    for i, p in enumerate(side["L"]):
        pl.append(pin(p, x0 - 2.54, y0 - 2.54 * (i + 1), 0))
    for i, p in enumerate(side["R"]):
        pl.append(pin(p, -x0 + 2.54, y0 - 2.54 * (i + 1), 180))
    for i, p in enumerate(side["T"]):
        pl.append(pin(p, -2.54 * (len(side["T"]) - 1) / 2 + 2.54 * i, y0 + 2.54, 270))
    for i, p in enumerate(side["B"]):
        pl.append(pin(p, -2.54 * (len(side["B"]) - 1) / 2 + 2.54 * i, -y0 - 2.54, 90))
    return ["symbol", Q(name), ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
            _prop("Reference", d.get("ref", "U"), x0, y0 + 1.5), _prop("Value", name, x0, -y0 - 1.5),
            _prop("Footprint", "", hide=True), _prop("Datasheet", d.get("datasheet", ""), hide=True),
            _prop("Description", d.get("description", ""), hide=True),
            ["symbol", Q("%s_0_1" % name)] + body, ["symbol", Q("%s_1_1" % name)] + pl]


def symbol_pins(sym):
    """[(number, name, type, unit, x, y, rot)] of a symbol (symbol coordinates, y up). Unit 0 = all units."""
    out, seen = [], set()
    for u in sexp.find(sym, "symbol"):
        m = re.search(r"_(\d+)_(\d+)$", u[1])
        unit = int(m.group(1)) if m else 1
        for p in sexp.find(u, "pin"):
            at = sexp.first(p, "at")
            num = sexp.first(p, "number")[1]
            key = (num, unit)
            if key in seen:
                continue
            seen.add(key)
            out.append((num, sexp.first(p, "name")[1], p[1], unit, float(at[1]), float(at[2]),
                        float(at[3]) if len(at) > 3 else 0.0))
    return out


# ---------------------------------------------------------------- footprints

def _fp_file(spec, lib, name):
    if lib in spec["fp_libs"]:
        return os.path.join(spec["_dir"], spec["fp_libs"][lib], name + ".kicad_mod")
    d = kicad_env.footprint_dir()
    if not d:
        raise LibError("KiCad footprint directory not found (set KICAD_FOOTPRINT_DIR)")
    return os.path.join(d, lib + ".pretty", name + ".kicad_mod")


def _rect(layer, x0, y0, x1, y1, w=0.05):
    return ["fp_rect", ["start", x0, y0], ["end", x1, y1], ["stroke", ["width", w], ["type", "solid"]],
            ["fill", "no"], ["layer", Q(layer)]]


def generate_footprint(name, d):
    """d: {"description": "...", "pads": [{"n": "1", "x": 0, "y": 0, "w": 0.3, "h": 0.6, "shape": "roundrect",
    "type": "smd"|"thru"|"npth", "drill": 0.3, "paste": true, "mask_margin": 0.0, "paste_margin": 0.0}],
    "courtyard": [x0, y0, x1, y1] (default: pads + 0.15), "body": {"w": .., "l": .., "h": .., "color": [r,g,b]}}
    Coordinates in mm, KiCad footprint frame (+y down), pin 1 where the datasheet's land pattern puts it."""
    pads = d["pads"]
    node = ["footprint", Q(name), ["version", FMT], ["generator", Q("hdt_pcb")], ["layer", Q("F.Cu")],
            ["descr", Q(d.get("description", ""))], ["attr", "smd" if all(p.get("type", "smd") == "smd" for p in pads) else "through_hole"]]
    xs, ys = [], []
    for p in pads:
        typ = p.get("type", "smd")
        shape = p.get("shape", "roundrect")
        w, h = float(p["w"]), float(p.get("h", p["w"]))
        x, y = float(p["x"]), float(p["y"])
        xs += [x - w / 2, x + w / 2]
        ys += [y - h / 2, y + h / 2]
        if typ == "smd":
            layers = [Q("F.Cu"), Q("F.Mask")] + ([Q("F.Paste")] if p.get("paste", True) else [])
            pad = ["pad", Q(str(p["n"])), "smd", shape, ["at", x, y] + ([float(p["a"])] if p.get("a") else []),
                   ["size", w, h], ["layers"] + layers]
        elif typ == "thru":
            pad = ["pad", Q(str(p["n"])), "thru_hole", shape, ["at", x, y], ["size", w, h],
                   ["drill", float(p["drill"])], ["layers", Q("*.Cu"), Q("*.Mask")]]
        else:
            pad = ["pad", Q(""), "np_thru_hole", "circle", ["at", x, y], ["size", w, w],
                   ["drill", float(p.get("drill", w))], ["layers", Q("*.Cu"), Q("*.Mask")]]
        if shape == "roundrect":
            pad.append(["roundrect_rratio", p.get("rratio", 0.25)])
        if "mask_margin" in p:
            pad.append(["solder_mask_margin", float(p["mask_margin"])])
        if "paste_margin" in p:
            pad.append(["solder_paste_margin", float(p["paste_margin"])])
        node.append(pad)
    cy = d.get("courtyard") or [round(min(xs) - 0.15, 3), round(min(ys) - 0.15, 3),
                                round(max(xs) + 0.15, 3), round(max(ys) + 0.15, 3)]
    b = d.get("body")
    if b:
        bx, by = b["w"] / 2, b["l"] / 2
        node.append(_rect("F.Fab", -bx, -by, bx, by, 0.05))
        cy = [min(cy[0], -bx - 0.1), min(cy[1], -by - 0.1), max(cy[2], bx + 0.1), max(cy[3], by + 0.1)]
    node.append(_rect("F.CrtYd", *cy, w=0.05))
    node.insert(5, ["property", Q("Reference"), Q("REF**"), ["at", 0, cy[1] - 0.6, 0], ["layer", Q("F.Fab")],
                    ["effects", ["font", ["size", 0.4, 0.4], ["thickness", 0.06]]]])
    node.insert(6, ["property", Q("Value"), Q(name), ["at", 0, cy[3] + 0.6, 0], ["layer", Q("F.Fab")], ["hide", "yes"],
                    ["effects", ["font", ["size", 0.4, 0.4], ["thickness", 0.06]]]])
    node.append(["embedded_fonts", "no"])
    return node


def footprint_pads(fp):
    """{pad number} of a footprint node (empty numbers = mechanical, ignored)."""
    out = set()
    for p in sexp.find(fp, "pad"):
        if p[1] and p[2] != "np_thru_hole":
            out.add(str(p[1]))
    return out


def write_vrml(path, w, l, h, color=(0.1, 0.1, 0.11)):
    """Simple box body. KiCad's VRML unit is 0.1 inch (1 unit = 2.54 mm)."""
    u = 1 / 2.54
    r, g, b = color
    with open(path, "w") as f:
        f.write("#VRML V2.0 utf8\nTransform { translation 0 0 %.5f children [ Shape { appearance Appearance { "
                "material Material { diffuseColor %s %s %s specularColor 0.2 0.2 0.2 shininess 0.3 } } "
                "geometry Box { size %.5f %.5f %.5f } } ] }\n" % (h / 2 * u, r, g, b, w * u, l * u, h * u))


def _set_model(fp, model, offset=(0, 0, 0), rotate=(0, 0, 0), scale=(1, 1, 1)):
    for m in sexp.find(fp, "model"):
        fp.remove(m)
    node = ["model", Q(model), ["offset", ["xyz"] + list(offset)], ["scale", ["xyz"] + list(scale)],
            ["rotate", ["xyz"] + list(rotate)]]
    idx = next((i for i, x in enumerate(fp) if isinstance(x, list) and x and x[0] == "embedded_fonts"), len(fp))
    fp.insert(idx, node)


def _silk_to_fab(fp):
    keep = []
    for item in fp:
        if isinstance(item, list) and item and item[0] in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly", "fp_text"):
            ly = sexp.first(item, "layer")
            if ly and ly[1] in SILK:
                continue
        if isinstance(item, list) and item and item[0] == "property" and item[1] == "Reference":
            ly = sexp.first(item, "layer")
            if ly:
                ly[1] = Q("F.Fab")
        keep.append(item)
    return keep


# ---------------------------------------------------------------- main build

def build(spec, out):
    lib = spec["library"]
    libdir = os.path.join(out, "lib")
    pretty = os.path.join(libdir, lib + ".pretty")
    d3 = os.path.join(libdir, "3d")
    for d in (libdir, pretty, d3):
        os.makedirs(d, exist_ok=True)
    silk = spec.get("footprint_silk", "keep")
    models = spec.get("models", {})

    sym_nodes, sym_src, fp_nodes = {}, {}, {}
    errors, warnings = [], []

    def want_symbol(ref_id):
        libn, name = specmod.lib_name(ref_id)
        src = (libn, name)
        local = name
        if local in sym_src and sym_src[local] != src:
            local = "%s_%s" % (libn, name)
        if local in sym_nodes:
            return local
        if libn is None:
            if name not in spec["symbols"]:
                raise LibError("symbol %s is neither Lib:Name nor defined in spec.symbols" % name)
            node = generate_symbol(name, spec["symbols"][name])
        else:
            node = _resolve_symbol(_sym_file(spec, libn), name, local)
        sym_nodes[local], sym_src[local] = node, src
        return local

    def want_fp(ref_id):
        libn, name = specmod.lib_name(ref_id)
        if name in fp_nodes:
            return name
        if libn is None:
            if name not in spec["footprints"]:
                raise LibError("footprint %s is neither Lib:Name nor defined in spec.footprints" % name)
            d = spec["footprints"][name]
            node = generate_footprint(name, d)
            if d.get("body"):
                b = d["body"]
                write_vrml(os.path.join(d3, name + ".wrl"), b["w"], b["l"], b["h"], tuple(b.get("color", (0.1, 0.1, 0.11))))
                write_step_box(os.path.join(d3, name + ".step"), b["w"], b["l"], b["h"], name)   # --subst-models
                _set_model(node, "${KIPRJMOD}/../lib/3d/%s.wrl" % name)
        else:
            path = _fp_file(spec, libn, name)
            if not os.path.exists(path):
                raise LibError("footprint not found: %s (%s)" % (ref_id, path))
            node = sexp.load(path)
            if silk == "fab":
                node = _silk_to_fab(node)
        if name in models:
            m = models[name]
            f = m["file"]
            if not f.startswith("$") and not os.path.isabs(f):
                f = os.path.relpath(os.path.join(spec["_dir"], f), os.path.join(out, "_board_"))
                f = "${KIPRJMOD}/" + f
            _set_model(node, f, m.get("offset", (0, 0, 0)), m.get("rotate", (0, 0, 0)), m.get("scale", (1, 1, 1)))
        fp_nodes[name] = node
        return name

    want_symbol("power:PWR_FLAG")
    resolved = {}
    for bname, b in spec["boards"].items():
        rb = resolved.setdefault(bname, {})
        for p in b["parts"]:
            try:
                sname = want_symbol(p["symbol"])
                fpid = p["footprint"] or next((x[2] for x in sexp.find(sym_nodes[sname], "property")
                                                if x[1] == "Footprint"), "")
                if not fpid:
                    raise LibError("no footprint given and the symbol has no default footprint")
                fname = want_fp(fpid)
            except LibError as e:
                errors.append("%s:%s %s" % (bname, p["ref"], e))
                continue
            spins = symbol_pins(sym_nodes[sname])
            nums = []
            for n in [x[0] for x in spins]:
                if n not in nums:
                    nums.append(n)
            by_name = {}
            for num, nm, typ, unit, *_ in spins:
                by_name.setdefault(nm, []).append(num)
            pin_net = {}
            for key, net in p["pins"].items():
                if key in nums:
                    pin_net[key] = net
                elif key in by_name:
                    for num in by_name[key]:
                        pin_net.setdefault(num, net)
                else:
                    errors.append("%s:%s pin %r is neither a pin number nor a pin name of %s" % (bname, p["ref"], key, sname))
            missing = [n for n in nums if n not in pin_net]
            if missing:
                if p["nc_rest"]:
                    for n in missing:
                        pin_net[n] = None
                else:
                    names = {num: nm for num, nm, *_ in spins}
                    errors.append("%s:%s pins without a net (set null for no-connect, or nc_rest): %s" % (
                        bname, p["ref"], ", ".join("%s(%s)" % (n, names[n]) for n in missing)))
            pads = footprint_pads(fp_nodes[fname])
            no_pad = [n for n in nums if n not in pads]
            if no_pad:
                errors.append("%s:%s symbol pins with no footprint pad in %s: %s" % (bname, p["ref"], fname, no_pad))
            extra = sorted(pads - set(nums))
            if extra:
                warnings.append("%s:%s footprint pads not in the symbol (left unconnected): %s" % (bname, p["ref"], extra))
            types = {num: typ for num, nm, typ, *_ in spins}
            rb[p["ref"]] = {"symbol": sname, "footprint": fname, "pins": pin_net, "types": types,
                            "units": sorted({x[3] for x in spins if x[3] > 0}) or [1]}

    # write the libraries
    for name, node in fp_nodes.items():
        sexp.save(os.path.join(pretty, name + ".kicad_mod"), node)
    symlib = ["kicad_symbol_lib", ["version", FMT], ["generator", Q("hdt_pcb")], ["generator_version", Q("1.0")]]
    symlib += list(sym_nodes.values())
    sexp.save(os.path.join(libdir, lib + ".kicad_sym"), symlib)
    with open(os.path.join(out, "resolved.json"), "w") as f:
        json.dump(resolved, f, indent=1)
    return {"symbols": len(sym_nodes), "footprints": len(fp_nodes), "errors": errors, "warnings": warnings}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="board.json")
    ap.add_argument("--out", help="output folder (default: the spec's folder)")
    a = ap.parse_args()
    s = specmod.load(a.spec)
    out = os.path.abspath(a.out or s["_dir"])
    r = build(s, out)
    for w in r["warnings"]:
        print("warning:", w)
    for e in r["errors"]:
        print("ERROR:", e)
    print("libgen: %d symbols, %d footprints, %d errors, %d warnings" % (r["symbols"], r["footprints"], len(r["errors"]), len(r["warnings"])))
    sys.exit(1 if r["errors"] else 0)


if __name__ == "__main__":
    main()
