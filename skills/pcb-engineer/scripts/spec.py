"""Load and normalize a board spec (board.json). Pure Python 3.9+ (also imported by KiCad's Python).

The spec is the single source of truth for parts, footprints, nets and placement.
See ../references/spec-format.md for every field.
"""
import json
import os

# 2-pin shortcuts: kind -> (symbol, footprint pattern by size)
SIZES = {"0201": "0603", "0402": "1005", "0603": "1608", "0805": "2012", "1206": "3216"}
SHORTCUTS = {
    "R": ("Device:R_Small", "Resistor_SMD:R_{s}_{m}Metric"),
    "C": ("Device:C_Small", "Capacitor_SMD:C_{s}_{m}Metric"),
    "L": ("Device:L_Small", "Inductor_SMD:L_{s}_{m}Metric"),
    "FB": ("Device:FerriteBead_Small", "Inductor_SMD:L_{s}_{m}Metric"),
    "LED": ("Device:LED_Small", "LED_SMD:LED_{s}_{m}Metric"),       # pin 1 = K (cathode), pin 2 = A
    "D": ("Device:D_Small", "Diode_SMD:D_{s}_{m}Metric"),            # pin 1 = K, pin 2 = A
    "TP": ("Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.0mm"),
}

STACKUPS = {
    # name: (copper layers, thickness mm). Dielectrics are split to match the total; replace them with the
    # fab's published stack-up (e.g. JLCPCB's JLC04061H-xxxx) before ordering impedance-controlled boards.
    "2L-1.6": (2, 1.6), "2L-1.0": (2, 1.0), "2L-0.8": (2, 0.8), "2L-0.6": (2, 0.6),
    "4L-1.6": (4, 1.6), "4L-1.0": (4, 1.0), "4L-0.8": (4, 0.8), "4L-0.6": (4, 0.6),
    "6L-1.6": (6, 1.6), "6L-0.8": (6, 0.8),
    "2L-flex-0.11": (2, 0.11), "2L-flex-0.13": (2, 0.13), "1L-flex-0.07": (1, 0.07),
}

DEFAULT_RULES = {  # standard (non-HDI) capability of large prototype fabs; check references/fab-capabilities.md
    "min_clearance": 0.1, "min_track_width": 0.1, "min_via_diameter": 0.4,
    "min_through_hole_diameter": 0.2, "min_via_annular_width": 0.1, "min_hole_to_hole": 0.25,
    "min_copper_edge_clearance": 0.2, "min_hole_clearance": 0.2, "min_silk_clearance": 0.0,
    "min_text_height": 0.6, "min_text_thickness": 0.1,
}


class SpecError(ValueError):
    pass


def stackup(board):
    s = board.get("stackup", "2L-1.6")
    if isinstance(s, dict):
        return s
    if s not in STACKUPS:
        raise SpecError("unknown stackup preset %r (known: %s)" % (s, ", ".join(STACKUPS)))
    n, t = STACKUPS[s]
    flex = "flex" in s
    mask_t = 0.025 if flex else 0.01
    cu_out, cu_in = (0.018, 0.018) if flex else (0.035, 0.0175)
    mat = "Polyimide" if flex else "FR4"
    layers = [("F.Mask", "Top Solder Mask", mask_t, "Polyimide" if flex else None)]
    coppers = ["F.Cu"] + ["In%d.Cu" % i for i in range(1, n - 1)] + (["B.Cu"] if n > 1 else [])
    cu_total = sum(cu_out if c in ("F.Cu", "B.Cu") else cu_in for c in coppers)
    n_diel = max(len(coppers) - 1, 0)
    diel_total = t - cu_total - 2 * mask_t
    if n_diel and diel_total <= 0:
        raise SpecError("stackup %s: thickness too small for its layers" % s)
    # outer prepregs thin, central core takes the rest (typical 4/6-layer build)
    diel = []
    if n_diel == 1:
        diel = [("core", diel_total)]
    elif n_diel >= 2:
        pp = min(0.1, diel_total / (n_diel + 1))      # outer prepregs; the middle layers take the rest
        k = n_diel - 2
        mid = [("core" if i % 2 == 0 else "prepreg", (diel_total - 2 * pp) / k) for i in range(k)] if k else []
        diel = [("prepreg", pp)] + mid + [("prepreg", pp)]
    for i, c in enumerate(coppers):
        layers.append((c, "copper", cu_out if c in ("F.Cu", "B.Cu") else cu_in, None))
        if i < n_diel:
            layers.append(("dielectric %d" % (i + 1), diel[i][0], round(diel[i][1], 4), mat))
    if n > 1:
        layers.append(("B.Mask", "Bottom Solder Mask", mask_t, "Polyimide" if flex else None))
    return {"layers": n, "thickness": t, "flex": flex,
            "finish": board.get("finish", "ENIG"),
            "mask_color": board.get("mask_color", "#C47A1EE6" if flex else "Green"),
            "stack": layers}


def _expand_part(p):
    p = dict(p)
    kind = p.pop("kind", None)
    if kind:
        if kind not in SHORTCUTS:
            raise SpecError("%s: unknown kind %r" % (p.get("ref"), kind))
        sym, fp = SHORTCUTS[kind]
        size = p.pop("size", "0402")
        p.setdefault("symbol", sym)
        if kind != "TP":
            if size not in SIZES:
                raise SpecError("%s: size %r not in %s" % (p["ref"], size, list(SIZES)))
            p.setdefault("footprint", fp.format(s=size, m=SIZES[size]))
        else:
            p.setdefault("footprint", fp)
        nets = p.pop("nets", None)
        if nets is not None:
            if isinstance(nets, str):
                nets = [nets]
            p["pins"] = {str(i + 1): n for i, n in enumerate(nets)}
        if kind == "TP":
            p.setdefault("value", "TP_" + (nets[0] if nets else p["ref"]))
            p.setdefault("in_bom", False)
    for k in ("ref", "symbol"):
        if not p.get(k):
            raise SpecError("part %r: missing %r" % (p.get("ref"), k))
    p.setdefault("footprint", "")        # empty: libgen uses the symbol's default Footprint property
    p.setdefault("value", p["ref"])
    p["pins"] = {str(k): v for k, v in (p.get("pins") or {}).items()}
    p.setdefault("x", 0.0)
    p.setdefault("y", 0.0)
    p.setdefault("rot", 0.0)
    p.setdefault("side", "F")
    if p["side"] not in ("F", "B"):
        raise SpecError("%s: side must be F or B" % p["ref"])
    p.setdefault("fixed", False)
    p.setdefault("dnp", False)
    p.setdefault("in_bom", not p["dnp"])
    p.setdefault("mpn", "")
    p.setdefault("lcsc", "")
    p.setdefault("manufacturer", "")
    p.setdefault("description", "")
    p.setdefault("nc_rest", False)
    p.setdefault("allow_overlap", [])
    p.setdefault("consign", False)      # true: no assembler part number; the part is shipped to the assembler
    return p


def load(path):
    path = os.path.abspath(path)
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    spec["_path"] = path
    spec["_dir"] = os.path.dirname(path)
    spec.setdefault("project", os.path.splitext(os.path.basename(path))[0])
    spec.setdefault("library", "project")
    spec.setdefault("symbols", {})
    spec.setdefault("footprints", {})
    spec.setdefault("sym_libs", {})      # extra symbol libraries: {"nickname": "path/to/lib.kicad_sym"}
    spec.setdefault("fp_libs", {})       # extra footprint libraries: {"nickname": "path/to/lib.pretty"}
    fab = {"name": "jlcpcb", "assembly": "standard", "min_assembly": [70.0, 70.0], "quantity": 10}
    fab.update(spec.get("fab", {}))
    spec["fab"] = fab
    boards = spec.get("boards")
    if not boards:
        raise SpecError("spec has no boards")
    for name, b in boards.items():
        if "outline" not in b:
            raise SpecError("board %s: missing outline" % name)
        b.setdefault("title", name)
        b.setdefault("rev", "A")
        b.setdefault("edge_margin", 0.2)
        b.setdefault("silkscreen", "keep")
        b.setdefault("planes", [])
        b.setdefault("keepouts", [])
        b.setdefault("exclusive", [])
        b.setdefault("texts", [])
        b.setdefault("pwr_flags", "auto")
        b.setdefault("netclasses", {})
        rules = dict(DEFAULT_RULES)
        rules.update(b.get("rules", {}))
        b["rules"] = rules
        fids = []
        for i, f in enumerate(b.get("fiducials", [])):
            fids.append({"ref": "FID%d" % (i + 1), "symbol": "Mechanical:Fiducial",
                         "footprint": f.get("footprint", "Fiducial:Fiducial_1mm_Mask2mm"), "value": "Fiducial",
                         "pins": {}, "x": f["x"], "y": f["y"], "side": f.get("side", "F"), "fixed": True,
                         "in_bom": False, "fiducial": True})
        b.setdefault("panel", {"mode": "none"})
        parts = [_expand_part(p) for p in b.get("parts", []) + fids]
        refs = [p["ref"] for p in parts]
        dup = sorted({r for r in refs if refs.count(r) > 1})
        if dup:
            raise SpecError("board %s: duplicate refs %s" % (name, dup))
        b["parts"] = parts
        b.setdefault("groups", [{"title": b["title"], "refs": refs}])
        listed = {r for g in b["groups"] for r in g["refs"]}
        rest = [r for r in refs if r not in listed]
        if rest:
            b["groups"].append({"title": "Other", "refs": rest})
    return spec


def lib_name(ref_id):
    """'Device:C_Small' -> ('Device', 'C_Small'); 'MyPart' -> (None, 'MyPart')."""
    if ":" in ref_id:
        lib, name = ref_id.split(":", 1)
        return lib, name
    return None, ref_id


def local_name(ref_id):
    """Name of a symbol/footprint inside the project library."""
    return lib_name(ref_id)[1]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Validate and summarize a board spec.")
    ap.add_argument("spec")
    a = ap.parse_args()
    s = load(a.spec)
    for n, b in s["boards"].items():
        nets = sorted({v for p in b["parts"] for v in p["pins"].values() if v})
        print("%s: %d parts, %d nets, stackup %s" % (n, len(b["parts"]), len(nets), b.get("stackup", "2L-1.6")))
    print("spec: ok")
