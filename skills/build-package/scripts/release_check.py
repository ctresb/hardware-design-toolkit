#!/usr/bin/env python3
"""READY TO BUILD gate for a release folder made by assemble_release.py.

Fails (exit 1) with a list of problems, each with the skill that owns the fix, when:
  - a required file is missing or MANIFEST.json does not match the files;
  - a Gerber zip is not a zip, or has no copper layer or no drill file;
  - DRC or ERC reports errors, unconnected items or schematic-parity issues; a report is missing;
  - a board is unrouted (no tracks in the .kicad_pcb);
  - BOM refs and CPL refs differ; a BOM line has no orderable MPN, no LCSC number and is not consigned,
    a lifecycle that cannot be bought, too little stock for the build, or a stock date older than the limit;
  - an enclosure part has no STEP (or no STL when it is printed);
  - the assembly validator report is missing, failing, or older than the CAD;
  - the doability verdict is not READY TO BUILD for the release target;
  - an ORDER.md step has no cost or no lead time;
  - a document still has placeholders (<…>, TBD, TODO); the test plan has no pass threshold.
Writes checks/release-check.json and the status line of README.md.

Usage:
  release_check.py hw/release/A/ --hw hw/ [--today 2026-11-08] [--json]
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import release_lib as L  # noqa: E402

PLACEHOLDER = re.compile(
    r"<(?!/?(?:br|sup|sub|b|i|em|strong|img|a|p|div|span|kbd|code|details|summary)\b)[a-z][a-z0-9 _/.-]{1,40}>"
    r"|\bTBD\b|\bTODO\b|\?\?\?", re.I)
THRESHOLD = re.compile(r"(≤|≥|<=|>=|<\s*\d|>\s*\d|±|pass\s*:)", re.I)
BAD_LIFECYCLE = {"prototype": ("eol", "obsolete", "discontinued", "last time buy"),
                 "production": ("eol", "obsolete", "discontinued", "last time buy", "nrnd", "not recommended",
                                "sampling", "preview", "early")}
PRINTED = ("sla", "fdm", "mjf", "sls", "polyjet", "print", "3d")


class Gate:
    def __init__(self):
        self.items = []

    def fail(self, check, msg, owner):
        self.items.append({"level": "fail", "check": check, "message": msg, "owner": owner})

    def warn(self, check, msg, owner):
        self.items.append({"level": "warn", "check": check, "message": msg, "owner": owner})

    @property
    def failed(self):
        return [i for i in self.items if i["level"] == "fail"]


def kicad_counts(report):
    """(errors, warnings, unconnected, parity) from a kicad-cli DRC or ERC JSON report."""
    viol = list(report.get("violations", []))
    for sh in report.get("sheets", []):
        viol += sh.get("violations", [])
    err = sum(1 for v in viol if v.get("severity", "error") == "error")
    wrn = sum(1 for v in viol if v.get("severity") == "warning")
    return err, wrn, len(report.get("unconnected_items", [])), len(report.get("schematic_parity", []))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("release", type=pathlib.Path, help="hw/release/<rev>/")
    ap.add_argument("--hw", type=pathlib.Path, help="the project's hw/ folder (default: two levels up)")
    ap.add_argument("--today", help="date for stock-age checks (YYYY-MM-DD, default today)")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    a = ap.parse_args()
    rel = a.release.resolve()
    hw = (a.hw or rel.parent.parent).resolve()
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    g = Gate()

    cfg_p = rel / "release.json"
    if not cfg_p.exists():
        print(f"error: {cfg_p} missing; run assemble_release.py first", file=sys.stderr)
        return 2
    cfg = L.load_json(cfg_p)
    target = cfg.get("target", "prototype")
    n = int(cfg.get("build_qty", 1))
    max_age = int(cfg.get("stock_max_age_days", 14))
    assembler = cfg.get("assembler", {}).get("name", "generic")
    consigned = set(cfg.get("assembler", {}).get("consigned_refs", []))
    files = L.ASSEMBLER_FILES.get(assembler, L.ASSEMBLER_FILES["generic"])

    # 1. structure and manifest
    for req in ("README.md", "ORDER.md", "MANIFEST.json", "battery/battery.md", "assembly-guide/assembly-guide.md",
                "test/test-plan.md", "test/verify-on-prototype.md"):
        if not (rel / req).exists():
            owner = {"test/verify-on-prototype.md": "doability-review"}.get(req, "build-package")
            g.fail("structure", f"missing {req}", owner)
    man_p = rel / "MANIFEST.json"
    if man_p.exists():
        man = L.load_json(man_p)
        listed = {f["path"]: f for f in man.get("files", [])}
        for p, f in listed.items():
            fp = rel / p
            if p == "README.md":
                continue                       # the gate writes its status line
            if not fp.exists():
                g.fail("manifest", f"{p} listed in MANIFEST.json but missing", "build-package")
            elif L.sha256(fp) != f["sha256"]:
                g.fail("manifest", f"{p} changed after assembly (edit the stage file and re-assemble)", "build-package")
        for fp in rel.rglob("*"):
            r = fp.relative_to(rel).as_posix()
            if fp.is_file() and r not in listed and r not in ("MANIFEST.json",) and not r.startswith(
                    ("checks/release-check", "checks/pre-order")):
                g.fail("manifest", f"{r} is not in MANIFEST.json (added by hand?)", "build-package")

    # 2. boards: fab files, DRC/ERC, routing, BOM/CPL consistency
    bom_rows = L.read_csv(hw / "bom.csv") if (hw / "bom.csv").exists() else []
    if not bom_rows:
        g.fail("bom", "hw/bom.csv missing or empty", "specs-engineer")
    bom_ref = L.bom_by_ref(bom_rows)
    placed_all = set()
    for b in cfg.get("boards", []):
        name = b["name"]
        gz = rel / f"fab/{name}/{name}_gerbers.zip"
        if not gz.exists():
            g.fail("fab", f"{name}: no Gerber zip", "pcb-engineer")
        else:
            try:
                names = [x.lower() for x in zipfile.ZipFile(gz).namelist()]
                cu = any(re.search(r"(\.gtl|\.gbl|\.g\d+|f_cu|b_cu|in\d+_cu)", x) for x in names)
                drl = any(re.search(r"(\.drl|\.xln|drill)", x) for x in names)
                if not cu:
                    g.fail("fab", f"{name}: Gerber zip has no copper layer", "pcb-engineer")
                if not drl:
                    g.fail("fab", f"{name}: Gerber zip has no drill file", "pcb-engineer")
            except zipfile.BadZipFile:
                g.fail("fab", f"{name}: {gz.name} is not a valid zip", "pcb-engineer")
        for k in ("drc", "erc"):
            rp = rel / f"checks/{name}_{k}.json"
            if not rp.exists():
                g.fail(k, f"{name}: no {k.upper()} report", "pcb-engineer")
                continue
            try:
                e, w, u, par = kicad_counts(L.load_json(rp))
            except (json.JSONDecodeError, AttributeError):
                g.fail(k, f"{name}: {k.upper()} report is not valid kicad-cli JSON", "pcb-engineer")
                continue
            if e:
                g.fail(k, f"{name}: {k.upper()} has {e} errors", "pcb-engineer")
            if w:
                (g.fail if cfg.get("warnings_fail") else g.warn)(k, f"{name}: {k.upper()} has {w} warnings", "pcb-engineer")
            if u:
                g.fail(k, f"{name}: {u} unconnected items (board not fully routed)", "pcb-engineer")
            if par:
                g.fail(k, f"{name}: {par} schematic-parity issues", "pcb-engineer")
        pcb = hw / b.get("kicad_pcb", f"pcb/{name}/{name}.kicad_pcb")
        if not pcb.exists():
            g.fail("routing", f"{name}: {pcb.relative_to(hw)} not found", "pcb-engineer")
        else:
            txt = pcb.read_text(encoding="utf-8", errors="replace")
            if not re.search(r"\(\s*(segment|arc)\s", txt):
                g.fail("routing", f"{name}: the board has no tracks (unrouted)", "pcb-engineer")
        cpl_p = rel / f"assembly/{name}/" / files["cpl"].format(board=name)
        bomj_p = rel / f"assembly/{name}/" / files["bom"].format(board=name)
        if not cpl_p.exists() or not bomj_p.exists():
            g.fail("assembly", f"{name}: assembler BOM or CPL missing", "pcb-engineer")
            continue
        cpl_refs = {r.get("Designator") for r in L.read_csv(cpl_p)}
        bom_refs, bom_lines = set(), L.read_csv(bomj_p)
        for r in bom_lines:
            refs = set(L.expand_refs(r.get("Designator", "")))
            bom_refs |= refs
            lc = (r.get("LCSC Part #") or r.get("JLCPCB Part #") or r.get("LCSC") or "").strip()
            if assembler == "jlcpcb" and not lc and not (refs & consigned):
                g.fail("assembly", f"{name}: {','.join(sorted(refs, key=L.natural))} has no LCSC part and is not consigned",
                       "electronics-researcher")
        if cpl_refs != bom_refs:
            only_c = sorted(cpl_refs - bom_refs, key=L.natural)
            only_b = sorted(bom_refs - cpl_refs, key=L.natural)
            g.fail("assembly", f"{name}: CPL and BOM refs differ (CPL only: {only_c or '—'}; BOM only: {only_b or '—'})",
                   "pcb-engineer")
        missing = sorted((r for r in cpl_refs if r not in bom_ref), key=L.natural)
        if missing:
            g.fail("bom", f"{name}: placed refs not in hw/bom.csv: {', '.join(missing)}", "specs-engineer")
        placed_all |= cpl_refs

    # 3. hw/bom.csv lines: orderable, lifecycle, stock, freshness
    for r in bom_rows:
        refs = L.expand_refs(r.get("ref", ""))
        tag = r.get("ref", "?")
        mpn = (r.get("mpn") or "").strip()
        if L.PLACEHOLDER_MPN.search(mpn):
            g.fail("bom", f"{tag}: MPN '{mpn}' is not an orderable part number", "electronics-researcher")
        lc = (r.get("lifecycle") or "").lower()
        if any(b in lc for b in BAD_LIFECYCLE[target]):
            g.fail("bom", f"{tag}: lifecycle '{r.get('lifecycle')}' cannot be used for a {target} build", "specs-engineer")
        elif target == "prototype" and any(b in lc for b in ("sampling", "preview", "early", "nrnd")):
            g.warn("bom", f"{tag}: lifecycle '{r.get('lifecycle')}' — fine for a prototype, not for production",
                   "specs-engineer")
        d = L.parse_date(r.get("source_date")) or L.parse_date(r.get("stock_snapshot"))
        if not d:
            g.fail("stock", f"{tag}: no stock/price check date", "electronics-researcher")
        elif (today - d).days > max_age:
            g.fail("stock", f"{tag}: stock checked {d} ({(today - d).days} days ago, limit {max_age})", "electronics-researcher")
        stock = L.parse_stock(r.get("stock_snapshot"))
        need = float(r.get("qty") or len(refs) or 1) * n
        if stock is None:
            g.fail("stock", f"{tag}: no stock snapshot", "electronics-researcher")
        elif stock < need:
            g.fail("stock", f"{tag}: stock {stock} < {need:g} needed for {n} units", "electronics-researcher")
        if refs and not any(x in placed_all for x in refs) and not (rel / "purchasing/digikey.csv").exists():
            g.fail("purchasing", f"{tag}: not placed by the assembler and no purchase cart exists", "build-package")

    # 4. mechanics
    for part in cfg.get("enclosure_parts", []):
        sp = rel / f"mech/{part['name']}.step"
        if not sp.exists():
            g.fail("mech", f"{part['name']}: no STEP", "enclosure-engineer")
        elif not sp.read_bytes()[:64].lstrip().startswith(b"ISO-10303-21"):
            g.fail("mech", f"{part['name']}: {sp.name} is not a STEP file", "enclosure-engineer")
        if any(k in (part.get("process", "").lower()) for k in PRINTED) and not (rel / f"mech/{part['name']}.stl").exists():
            g.fail("mech", f"{part['name']}: printed part without STL", "enclosure-engineer")
    if cfg.get("enclosure_parts") and not (rel / "mech/print-settings.md").exists() and any(
            any(k in p.get("process", "").lower() for k in PRINTED) for p in cfg["enclosure_parts"]):
        g.fail("mech", "printed parts but no mech/print-settings.md", "build-package")

    # 5. validator: passing and newer than the CAD
    vp = rel / "checks/validator.json"
    if not vp.exists():
        g.fail("validation", "no assembly validator report", "enclosure-engineer")
    else:
        v = L.load_json(vp)
        if not v.get("ok") or v.get("n_interpenetrations", 0):
            g.fail("validation", f"assembly validator fails ({v.get('n_interpenetrations', '?')} interpenetrations)",
                   "enclosure-engineer")
        src_v = hw / cfg.get("validator", "validation/assembly.json")
        cad = [hw / c for c in cfg.get("cad_sources", [])] + [hw / p["step"] for p in cfg.get("enclosure_parts", []) if p.get("step")]
        newer = [c for c in cad if c.exists() and src_v.exists() and c.stat().st_mtime > src_v.stat().st_mtime + 1]
        if newer:
            g.fail("validation", "validator report is older than " + ", ".join(c.relative_to(hw).as_posix() for c in newer),
                   "enclosure-engineer")

    # 6. doability verdict
    dp = next(iter(sorted(rel.glob("checks/doability.*"))), None)
    verdict = L.doability_verdict(dp) if dp else None
    want = f"READY TO BUILD ({target})"
    ok_levels = [want] + (["READY TO BUILD (production)"] if target == "prototype" else [])
    if not verdict:
        g.fail("doability", "no doability verdict", "doability-review")
    elif verdict.upper() not in [x.upper() for x in ok_levels]:
        g.fail("doability", f"doability verdict is '{verdict}', needs '{want}'", "doability-review")

    # 7. order steps
    steps = cfg.get("order_steps", [])
    if not steps:
        g.fail("order", "no order steps", "build-package")
    for i, s in enumerate(steps, 1):
        if not s.get("cost_usd"):
            g.fail("order", f"step {i} '{s.get('title', '')}' has no cost", "cost-and-sourcing")
        if not s.get("lead_time_days"):
            g.fail("order", f"step {i} '{s.get('title', '')}' has no lead time", "cost-and-sourcing")
        for u in s.get("upload", []):
            if not (rel / u).exists():
                g.fail("order", f"step {i} uploads {u}, which is not in the release", "build-package")

    # 8. documents: no placeholders, thresholds in the test plan
    for md in rel.rglob("*.md"):
        r = md.relative_to(rel).as_posix()
        if r == "README.md" or r.startswith("checks/"):
            continue
        for ln, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            m = PLACEHOLDER.search(line)
            if m:
                g.fail("docs", f"{r}:{ln}: placeholder '{m.group(0)}'", "build-package")
                break
    tp = rel / "test/test-plan.md"
    if tp.exists() and not THRESHOLD.search(tp.read_text(encoding="utf-8")):
        g.fail("docs", "test/test-plan.md has no pass thresholds (≤, ≥, ±)", "battery-and-power")

    # result
    ok = not g.failed
    status = f"READY TO BUILD ({target})" if ok else "NOT READY"
    res = {"release": cfg.get("rev"), "target": target, "status": status, "checked": today.isoformat(),
           "failures": len(g.failed), "warnings": len(g.items) - len(g.failed), "items": g.items}
    (rel / "checks").mkdir(exist_ok=True)
    (rel / "checks/release-check.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    rd = rel / "README.md"
    if rd.exists():
        t = rd.read_text(encoding="utf-8")
        line = f"Status: {status} · checked {today.isoformat()} · {len(g.failed)} failures (checks/release-check.json)"
        t = re.sub(r"^Status:.*$", line, t, count=1, flags=re.M)
        rd.write_text(t, encoding="utf-8")
    if a.json:
        print(json.dumps(res, indent=1, ensure_ascii=False))
    else:
        for i in g.items:
            print(f"{i['level'].upper():4}  [{i['check']}] {i['message']}  → {i['owner']}")
        print(f"release {cfg.get('rev')}: {status} ({len(g.failed)} failures, {res['warnings']} warnings)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
