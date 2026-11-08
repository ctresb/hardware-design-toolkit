#!/usr/bin/env python3
"""Assemble the release package hw/release/<rev>/ from the outputs of every stage.

The release copies stage files (it never edits them) and generates:
  - assembler BOM and CPL (only when pcb-engineer did not export them), with rotation offsets
  - stock.md, consigned.csv, options.md per board
  - purchase carts (DigiKey, Mouser BOM-upload CSV) for parts the assembler does not supply, with attrition
  - mechanical BOM, firmware pin map (pins.json, pins.h) from the KiCad netlist
  - ORDER.md, README.md, MANIFEST.json (sha256 of every file and its source stage)

Usage:
  assemble_release.py hw/ --config hw/release/release.json [--force]
Then run release_check.py on the result.
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import release_lib as L  # noqa: E402

GENERATED = "generated"


class Release:
    def __init__(self, hw, cfg, out):
        self.hw, self.cfg, self.out = hw, cfg, out
        self.sources = {}          # release-relative path -> source (hw-relative path or "generated")
        self.notes = []            # things the user must know, printed at the end

    def src(self, rel):
        return self.hw / rel

    def copy(self, rel_src, rel_dst, stage):
        s = self.src(rel_src)
        if not s.exists():
            self.notes.append(f"missing input {rel_src} ({stage})")
            return False
        d = self.out / rel_dst
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
        self.sources[rel_dst] = f"{stage}: hw/{rel_src}"
        return True

    def write(self, rel_dst, text, stage=GENERATED):
        d = self.out / rel_dst
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(text, encoding="utf-8")
        self.sources[rel_dst] = stage

    def csv(self, rel_dst, header, rows, stage=GENERATED):
        L.write_csv(self.out / rel_dst, header, rows)
        self.sources[rel_dst] = stage


def find_one(folder, patterns):
    for pat in patterns:
        hits = sorted(folder.glob(pat)) if folder.exists() else []
        if hits:
            return hits[0]
    return None


def read_pos(path):
    """KiCad position file (kicad-cli pcb export pos --format csv) -> list of dicts."""
    rows = []
    for r in L.read_csv(path):
        rows.append({
            "ref": r.get("Ref") or r.get("Designator"),
            "val": r.get("Val") or r.get("Comment", ""),
            "fp": r.get("Package") or r.get("Footprint", ""),
            "x": float(r.get("PosX") or r.get("Mid X", "0").replace("mm", "")),
            "y": float(r.get("PosY") or r.get("Mid Y", "0").replace("mm", "")),
            "rot": float(r.get("Rot") or r.get("Rotation") or 0),
            "side": (r.get("Side") or r.get("Layer") or "top").lower(),
        })
    return rows


def board_assembly(rel, b, bom_ref, assembler, consigned):
    name = b["name"]
    fab_dir = rel.src(b.get("fab_dir", f"pcb/fab/{name}"))
    files = L.ASSEMBLER_FILES.get(assembler, L.ASSEMBLER_FILES["generic"])
    bom_dst = f"assembly/{name}/" + files["bom"].format(board=name)
    cpl_dst = f"assembly/{name}/" + files["cpl"].format(board=name)
    offsets = b.get("rotation_offsets") or {}

    # Fab: Gerber zip, IPC netlist, notes
    gz = find_one(fab_dir, [f"{name}*gerber*.zip", "*gerber*.zip", "*.zip"])
    if gz:
        rel.copy(gz.relative_to(rel.hw).as_posix(), f"fab/{name}/{name}_gerbers.zip", "pcb-engineer")
    else:
        rel.notes.append(f"{name}: no Gerber zip in {fab_dir.relative_to(rel.hw)}")
    ipc = find_one(fab_dir, ["*.ipc", "*.d356", "*ipc356*"])
    if ipc:
        rel.copy(ipc.relative_to(rel.hw).as_posix(), f"fab/{name}/{ipc.name}", "pcb-engineer")
    fn = b.get("fab_notes") or {}
    lines = [f"# Fab notes · {name}", "", "| Parameter | Value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in fn.items()]
    rel.write(f"fab/{name}/fab-notes.md", "\n".join(lines) + "\n", "build-package: release.json boards[].fab_notes")

    # Assembly: use pcb-engineer's BOM/CPL when present, else build them from the position file
    ex_bom = find_one(fab_dir, [f"{name}_bom.csv", "*_bom*.csv"])
    ex_cpl = find_one(fab_dir, [f"{name}_cpl.csv", "*_cpl*.csv"])
    placed = []
    if ex_cpl:
        cpl = L.read_csv(ex_cpl)
        rows = []
        for r in cpl:
            ref = r.get("Designator")
            fp = (bom_ref.get(ref) or {}).get("package", "")
            rot = (float(r.get("Rotation") or 0) + L.rotation_offset(fp, offsets)) % 360
            rows.append([ref, r.get("Mid X"), r.get("Mid Y"), r.get("Layer"), f"{rot:g}"])
            placed.append(ref)
        rel.csv(cpl_dst, ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"], rows,
                f"pcb-engineer: hw/{ex_cpl.relative_to(rel.hw).as_posix()} (+ rotation offsets)" if offsets
                else f"pcb-engineer: hw/{ex_cpl.relative_to(rel.hw).as_posix()}")
    else:
        pos_path = rel.src(b.get("pos", f"pcb/fab/{name}/{name}_pos.csv"))
        if not pos_path.exists():
            rel.notes.append(f"{name}: no CPL and no position file ({pos_path.relative_to(rel.hw)})")
            return []
        pos = read_pos(pos_path)
        rows = []
        for p in sorted(pos, key=lambda p: L.natural(p["ref"])):
            rot = (p["rot"] + L.rotation_offset(p["fp"], offsets)) % 360
            layer = "Bottom" if p["side"].startswith("b") else "Top"
            rows.append([p["ref"], f"{p['x']:.4f}mm", f"{p['y']:.4f}mm", layer, f"{rot:g}"])
            placed.append(p["ref"])
        rel.csv(cpl_dst, ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"], rows,
                f"generated from hw/{pos_path.relative_to(rel.hw).as_posix()}")

    if ex_bom:
        rel.copy(ex_bom.relative_to(rel.hw).as_posix(), bom_dst, "pcb-engineer")
    else:
        groups = {}
        for ref in placed:
            r = bom_ref.get(ref, {})
            key = (r.get("function", ""), r.get("package", ""), r.get("mpn", ""), L.lcsc_of(r))
            groups.setdefault(key, []).append(ref)
        rows = []
        for (func, pkg, mpn, lcsc), refs in sorted(groups.items(), key=lambda kv: L.natural(sorted(kv[1], key=L.natural)[0])):
            if any(x in consigned for x in refs):
                lcsc = ""
            rows.append([mpn or func, ",".join(sorted(refs, key=L.natural)), pkg, lcsc])
        rel.csv(bom_dst, ["Comment", "Designator", "Footprint", "LCSC Part #"], rows,
                "generated from hw/bom.csv + CPL")

    # stock, consigned, options
    st = [f"# Stock at order time · {name}", "",
          "Re-check every line on the assembler's site within the release's stock age limit before you pay.", "",
          "| Refs | MPN | LCSC | Stock snapshot | Checked | Lifecycle |", "|---|---|---|---|---|---|"]
    seen, cons_rows = set(), []
    for ref in sorted(placed, key=L.natural):
        r = bom_ref.get(ref)
        if not r or id(r) in seen:
            continue
        seen.add(id(r))
        refs_here = [x for x in L.expand_refs(r.get("ref", "")) if x in placed]
        lc = L.lcsc_of(r)
        st.append(f"| {', '.join(refs_here)} | `{r.get('mpn','')}` | {lc or '—'} | {r.get('stock_snapshot','') or '—'} | "
                  f"{r.get('source_date','') or '—'} | {r.get('lifecycle','') or '—'} |")
        if not lc or any(x in consigned for x in refs_here):
            cons_rows.append([",".join(refs_here), r.get("manufacturer", ""), r.get("mpn", ""), r.get("qty", "")])
    rel.write(f"assembly/{name}/stock.md", "\n".join(st) + "\n", "generated from hw/bom.csv")
    rel.csv(f"assembly/{name}/consigned.csv", ["Designator", "Manufacturer", "MPN", "Qty per board"], cons_rows,
            "generated from hw/bom.csv")
    opts = rel.cfg.get("assembler", {}).get("options", {})
    ol = [f"# Assembly order options · {name} · {assembler}", "", "| Option | Choose |", "|---|---|"]
    ol += [f"| {k} | {v} |" for k, v in opts.items()]
    if offsets:
        ol += ["", "Rotation offsets applied to the CPL (footprint pattern → degrees):", ""]
        ol += [f"- `{k}` → {v}°" for k, v in offsets.items()]
    ol += ["", "Check every polarized part in the assembler's 3D preview before you confirm the order."]
    rel.write(f"assembly/{name}/options.md", "\n".join(ol) + "\n", "build-package: release.json assembler")
    return placed


def purchasing(rel, bom_rows, placed_all, consigned):
    cfg, n = rel.cfg, int(rel.cfg.get("build_qty", 1))
    att = cfg.get("attrition", {})
    supplied_by_assembler = cfg.get("assembler", {}).get("name", "generic") in ("jlcpcb", "pcbway")
    dk, mo, summary = [], [], []
    for r in bom_rows:
        refs = L.expand_refs(r.get("ref", ""))
        on_board = [x for x in refs if x in placed_all]
        need_buy = (not on_board) or (not supplied_by_assembler) or (not L.lcsc_of(r)) or any(x in consigned for x in refs)
        if not need_buy:
            continue
        per_unit = float(r.get("qty") or len(refs) or 1)
        q = L.order_qty(per_unit, n, att, L.is_passive(refs[0] if refs else "", att.get("passive_prefixes", [])))
        ref_txt = ",".join(refs)
        dk.append([r.get("mpn", ""), r.get("manufacturer", ""), q, ref_txt])
        mo.append([r.get("mpn", ""), r.get("manufacturer", ""), q, ref_txt])
        why = "not placed by the assembler" if not on_board else ("consigned" if any(x in consigned for x in refs) else "no assembler part number")
        summary.append(f"| {ref_txt} | `{r.get('mpn','')}` | {per_unit:g} | {q} | {why} |")
    if dk:
        rel.csv("purchasing/digikey.csv", ["Manufacturer Part Number", "Manufacturer", "Quantity", "Customer Reference"], dk,
                "generated from hw/bom.csv")
        rel.csv("purchasing/mouser.csv", ["Mfr. Part Number", "Manufacturer", "Quantity", "Customer Part Number"], mo,
                "generated from hw/bom.csv")
    mech = cfg.get("mech_bom", [])
    mrows = []
    for m in mech:
        q = m.get("qty_per_unit", 1) * n * (1 + att.get("default_pct", 5) / 100.0)
        mrows.append([m.get("item", ""), m.get("vendor", ""), m.get("mpn", ""), f"{q:g}", m.get("unit", "pcs"), m.get("url", "")])
    if mrows:
        rel.csv("purchasing/mechanical.csv", ["Item", "Vendor", "MPN", "Quantity", "Unit", "URL"], mrows,
                "build-package: release.json mech_bom")
        rel.csv("mech/mech-bom.csv", ["Item", "Vendor", "MPN", "Quantity", "Unit", "URL"], mrows,
                "build-package: release.json mech_bom")
    txt = [f"# Purchasing · build of {n}", "",
           f"Attrition: {att.get('default_pct', 5)} % with at least {att.get('min_extra', 1)} extra per line "
           f"({att.get('passive_min_extra', 10)} for passives).", "",
           "Upload `digikey.csv` at digikey.com → BOM Manager, or `mouser.csv` at mouser.com → BOM Tool. "
           "Lines marked \"consigned\" go to the assembler: ship them with the assembler's consignment form before the "
           "order is released. Ship lithium cells to the final-assembly location, never to a fab that does not accept them.", "",
           "| Refs | MPN | Per unit | Order | Why |", "|---|---|---|---|---|"] + summary
    if mrows:
        txt += ["", "Mechanical parts: `mechanical.csv`."]
    rel.write("purchasing/purchasing.md", "\n".join(txt) + "\n")


def pin_map(rel, netlist_rel, mcu):
    p = rel.src(netlist_rel)
    if not p.exists():
        rel.notes.append(f"firmware: netlist {netlist_rel} not found; pin map skipped")
        return
    text = p.read_text(encoding="utf-8", errors="replace")
    pins = []
    for chunk in re.split(r"\(net\s+\(code", text)[1:]:
        m = re.search(r'\(name\s+"([^"]*)"', chunk)
        net = m.group(1) if m else ""
        for nm in re.finditer(r'\(node\s+\(ref\s+"?([^")\s]+)"?\)\s+\(pin\s+"?([^")\s]+)"?\)(?:\s+\(pinfunction\s+"([^"]*)"\))?', chunk):
            if nm.group(1) == mcu:
                pins.append({"pin": nm.group(2), "function": nm.group(3) or "", "net": net.lstrip("/")})
    pins.sort(key=lambda d: L.natural(d["pin"]))
    rel.write("firmware/pins.json", json.dumps({"mcu_ref": mcu, "pins": pins}, indent=1) + "\n", f"generated from hw/{netlist_rel}")
    h = [f"/* Pin map of {mcu}, generated from the schematic netlist. Do not edit; regenerate. */", "#pragma once", ""]
    for d in pins:
        if d["net"].startswith("unconnected") or not d["net"]:
            continue
        ident = re.sub(r"[^A-Za-z0-9]+", "_", d["net"]).strip("_").upper()
        fun = re.sub(r"[^A-Za-z0-9_.]+", "_", d["function"])
        h.append(f"#define PIN_{ident:<24} \"{fun or d['pin']}\"  /* pad {d['pin']} */")
    rel.write("firmware/pins.h", "\n".join(h) + "\n", f"generated from hw/{netlist_rel}")


def order_md(rel):
    cfg = rel.cfg
    steps = cfg.get("order_steps", [])
    n = cfg.get("build_qty", 1)
    lo = sum((s.get("cost_usd") or [0, 0])[0] for s in steps)
    hi = sum((s.get("cost_usd") or [0, 0])[-1] for s in steps)
    out = [f"# Order · {cfg.get('product', '')} rev {cfg.get('rev')} · build of {n}", "",
           f"Total: USD {lo:,.0f}–{hi:,.0f} [estimate, sources per step]. Steps that do not depend on each other "
           "can run in parallel; the lead times are per step.", "",
           "**WARNING** Ordering spends money. Confirm the release check passed (`checks/release-check.json`) "
           "and the stock dates are current before each step.", ""]
    for i, s in enumerate(steps, 1):
        c, t = s.get("cost_usd"), s.get("lead_time_days")
        out += [f"## {i}. {s.get('title', '')}", "",
                f"- **Where:** {s.get('where', '')}",
                f"- **Upload:** " + (", ".join(f"`{u}`" for u in s.get("upload", [])) or "nothing"),
                f"- **Options:** {s.get('options', '')}",
                f"- **Cost:** " + (f"USD {c[0]:,.0f}–{c[-1]:,.0f}" if c else "MISSING"),
                f"- **Lead time:** " + (f"{t[0]}–{t[-1]} days" if t else "MISSING"),
                f"- **Receiver:** {s.get('receiver', '')}",
                f"- **Source:** {s.get('source', '')}", ""]
    rel.write("ORDER.md", "\n".join(out), "build-package: release.json order_steps")


def readme(rel, boards):
    cfg = rel.cfg
    out = [f"# {cfg.get('product', '')} · release {cfg.get('rev')}", "",
           "Status: NOT CHECKED (run release_check.py)", "",
           f"Target level: READY TO BUILD ({cfg.get('target', 'prototype')}) · build size {cfg.get('build_qty', 1)} · "
           f"assembled {dt.date.today().isoformat()}", "",
           "| Folder | Content |", "|---|---|",
           "| `ORDER.md` | the order steps, with cost and lead time |",
           "| `fab/` | Gerbers and fab notes per board: " + ", ".join(boards) + " |",
           "| `assembly/` | assembler BOM, CPL, stock, consigned parts, order options |",
           "| `purchasing/` | carts for parts the assembler does not supply, mechanical parts |",
           "| `mech/` | enclosure STEP/STL, print settings, drawing, mechanical BOM |",
           "| `battery/` | the cell and its holder or the custom-cell spec |",
           "| `assembly-guide/` | final assembly steps with QC checks |",
           "| `test/` | bring-up and test plan, verify-on-prototype list |",
           "| `firmware/` | pin map from the schematic |",
           "| `checks/` | the reports the release gate used |",
           "| `MANIFEST.json` | sha256 of every file and its source |", ""]
    rel.write("README.md", "\n".join(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("hw", type=pathlib.Path, help="the project's hw/ folder")
    ap.add_argument("--config", type=pathlib.Path, help="release config (default hw/release/release.json)")
    ap.add_argument("--force", action="store_true", help="replace an existing release folder of the same revision")
    a = ap.parse_args()
    hw = a.hw.resolve()
    cfg_path = (a.config or hw / "release" / "release.json").resolve()
    if not cfg_path.exists():
        print(f"error: {cfg_path} not found (copy templates/release.example.json)", file=sys.stderr)
        return 2
    cfg = L.load_json(cfg_path)
    out = hw / "release" / str(cfg.get("rev", "A"))
    if out.exists():
        if not a.force:
            print(f"error: {out} exists; use --force to rebuild it", file=sys.stderr)
            return 2
        keep = out / "checks" / "pre-order.md"
        saved = keep.read_text(encoding="utf-8") if keep.exists() else None
        shutil.rmtree(out)
        if saved is not None:
            keep.parent.mkdir(parents=True, exist_ok=True)
            keep.write_text(saved, encoding="utf-8")
    out.mkdir(parents=True, exist_ok=True)
    rel = Release(hw, cfg, out)
    shutil.copy2(cfg_path, out / "release.json")
    rel.sources["release.json"] = "build-package: " + str(cfg_path.relative_to(hw) if cfg_path.is_relative_to(hw) else cfg_path)

    bom_path = hw / "bom.csv"
    bom_rows = L.read_csv(bom_path) if bom_path.exists() else []
    if not bom_rows:
        rel.notes.append("hw/bom.csv missing or empty")
    bom_ref = L.bom_by_ref(bom_rows)
    assembler = cfg.get("assembler", {}).get("name", "generic")
    consigned = set(cfg.get("assembler", {}).get("consigned_refs", []))

    placed_all = set()
    for b in cfg.get("boards", []):
        placed_all |= set(board_assembly(rel, b, bom_ref, assembler, consigned))
        for k in ("drc", "erc"):
            if b.get(k):
                rel.copy(b[k], f"checks/{b['name']}_{k}.json", "pcb-engineer")
    purchasing(rel, bom_rows, placed_all, consigned)

    for part in cfg.get("enclosure_parts", []):
        for k in ("step", "stl"):
            if part.get(k):
                rel.copy(part[k], f"mech/{part['name']}.{k}", "enclosure-engineer")
    if cfg.get("drawing"):
        rel.copy(cfg["drawing"], "mech/" + pathlib.Path(cfg["drawing"]).name, "technical-drawing")
    docs = cfg.get("docs", {})
    for key, dst, stage in (("print_settings", "mech/print-settings.md", "build-package"),
                            ("battery", "battery/battery.md", "build-package"),
                            ("assembly_guide", "assembly-guide/assembly-guide.md", "build-package"),
                            ("test_plan", "test/test-plan.md", "build-package")):
        if docs.get(key):
            rel.copy(docs[key], dst, stage)
    for img in docs.get("assembly_images", []):
        rel.copy(img, "assembly-guide/" + pathlib.Path(img).name, "technical-drawing / product-render")

    if cfg.get("validator"):
        rel.copy(cfg["validator"], "checks/validator.json", "enclosure-engineer")
    if cfg.get("doability"):
        rel.copy(cfg["doability"], "checks/doability" + pathlib.Path(cfg["doability"]).suffix, "doability-review")
    vop = cfg.get("verify_on_prototype")
    if vop and rel.src(vop).exists():
        rel.copy(vop, "test/verify-on-prototype.md", "doability-review")
    elif cfg.get("doability"):
        items = L.verify_list_from_doability(rel.src(cfg["doability"]))
        if items:
            lines = ["# Verify on the prototype", "",
                     "| Measurement | Method | Instrument | Pass threshold |", "|---|---|---|---|"]
            for it in items:
                if isinstance(it, dict):
                    lines.append(f"| {it.get('what', it.get('measurement', ''))} | {it.get('method', '')} | "
                                 f"{it.get('instrument', '')} | "
                                 f"{it.get('pass_criteria', it.get('pass', it.get('threshold', '')))} |")
                else:
                    lines.append(f"| {it} | | | |")
            rel.write("test/verify-on-prototype.md", "\n".join(lines) + "\n", "generated from doability-review findings")

    fw = cfg.get("firmware") or {}
    if fw.get("mcu_ref"):
        b = next((x for x in cfg.get("boards", []) if x["name"] == fw.get("board")), (cfg.get("boards") or [{}])[0])
        if b.get("netlist"):
            pin_map(rel, b["netlist"], fw["mcu_ref"])

    order_md(rel)
    readme(rel, [b["name"] for b in cfg.get("boards", [])])

    man = {"product": cfg.get("product"), "rev": cfg.get("rev"), "assembled": dt.datetime.now().isoformat(timespec="seconds"),
           "files": []}
    for f in sorted(out.rglob("*")):
        if f.is_file():
            r = f.relative_to(out).as_posix()
            if r in ("MANIFEST.json",) or r.startswith("checks/pre-order"):
                continue
            man["files"].append({"path": r, "sha256": L.sha256(f), "bytes": f.stat().st_size,
                                 "source": rel.sources.get(r, "unknown")})
    (out / "MANIFEST.json").write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")

    for n_ in rel.notes:
        print("note:", n_)
    print(f"release {cfg.get('rev')}: {len(man['files'])} files in {out} ({len(rel.notes)} notes); next: release_check.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
