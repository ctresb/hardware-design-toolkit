#!/usr/bin/env python3
"""Self-test of assemble_release.py and release_check.py on the test fixture in templates/example/.

One passing case, then one mutation per gate check. Each mutation must fail with the expected check.
Usage: selftest.py [--keep]
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
FIXTURE = HERE.parent / "templates" / "example" / "hw"
TODAY = "2026-11-10"


def build_fixture(root):
    hw = root / "hw"
    shutil.copytree(FIXTURE, hw)
    with zipfile.ZipFile(hw / "pcb/fab/main/main_gerbers.zip", "w") as z:
        for n in ("main-F_Cu.gbr", "main-B_Cu.gbr", "main-Edge_Cuts.gbr", "main.drl"):
            z.writestr(n, "test fixture, not a real Gerber\n")
    (hw / "mech/cad/shell.step").write_text("ISO-10303-21;\nHEADER;\n/* test fixture stub */\nENDSEC;\nEND-ISO-10303-21;\n")
    (hw / "mech/cad/shell.stl").write_text("solid shell\nendsolid shell\n")
    (hw / "drawings").mkdir(parents=True, exist_ok=True)
    (hw / "drawings/blueprint.pdf").write_bytes(b"%PDF-1.4\n% test fixture stub\n")
    time.sleep(0.01)
    later = time.time() + 5
    os.utime(hw / "validation/assembly.json", (later, later))     # validator newer than the CAD
    return hw


def run(hw, today=TODAY):
    a = subprocess.run([sys.executable, HERE / "assemble_release.py", hw, "--force"], capture_output=True, text=True)
    if a.returncode:
        return a.returncode, a.stdout + a.stderr, None
    c = subprocess.run([sys.executable, HERE / "release_check.py", hw / "release/A", "--hw", hw, "--today", today],
                       capture_output=True, text=True)
    res = json.loads((hw / "release/A/checks/release-check.json").read_text())
    return c.returncode, c.stdout + c.stderr, res


def mut_drc(hw):
    d = json.loads((hw / "pcb/main/drc.json").read_text())
    d["violations"] = [{"type": "clearance", "severity": "error", "description": "test"}]
    (hw / "pcb/main/drc.json").write_text(json.dumps(d))


def mut_unrouted(hw):
    p = hw / "pcb/main/main.kicad_pcb"
    p.write_text("\n".join(l for l in p.read_text().splitlines() if "(segment" not in l))


def mut_step(hw):
    (hw / "mech/cad/shell.step").unlink()


def mut_old_validator(hw):
    later = time.time() + 60
    os.utime(hw / "mech/cad/shell.step", (later, later))


def mut_verdict(hw):
    (hw / "doability/score.json").write_text(json.dumps({"overall": "NOT READY"}))


def mut_placeholder(hw):
    p = hw / "release/src/assembly-guide.md"
    p.write_text(p.read_text() + "\n- **QC:** <criterion>\n")


def mut_order(hw):
    p = hw / "release/release.json"
    c = json.loads(p.read_text())
    c["order_steps"][0].pop("cost_usd")
    p.write_text(json.dumps(c))


def mut_lcsc(hw):
    """D1 loses its LCSC number: both the `lcsc` column (canonical) and any legacy LCSC: token."""
    import csv
    p = hw / "bom.csv"
    rows = list(csv.DictReader(p.open(newline="")))
    for r in rows:
        if r["ref"] == "D1":
            r["lcsc"] = "-"
            r["distributors"] = r["distributors"].replace("LCSC:C900004", "Mouser")
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def mut_stock(hw):
    p = hw / "bom.csv"
    p.write_text(p.read_text().replace("8000 @ LCSC", "5 @ LCSC"))


CASES = [
    ("DRC error", mut_drc, "drc", TODAY),
    ("unrouted board", mut_unrouted, "routing", TODAY),
    ("stale stock dates", None, "stock", "2026-12-31"),
    ("missing STEP", mut_step, "mech", TODAY),
    ("validator older than CAD", mut_old_validator, "validation", TODAY),
    ("doability not ready", mut_verdict, "doability", TODAY),
    ("placeholder in a document", mut_placeholder, "docs", TODAY),
    ("order step without cost", mut_order, "order", TODAY),
    ("LED without LCSC and not consigned", mut_lcsc, "assembly", TODAY),
    ("stock below build size", mut_stock, "stock", TODAY),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keep", action="store_true", help="keep the temporary folders")
    a = ap.parse_args()
    base = pathlib.Path(tempfile.mkdtemp(prefix="build-package-selftest-"))
    bad = 0
    hw = build_fixture(base / "pass")
    code, out, res = run(hw)
    ok = code == 0 and res and res["status"].startswith("READY TO BUILD")
    print(f"{'PASS' if ok else 'FAIL'}  clean fixture → {res['status'] if res else out.strip()[:200]}")
    if not ok:
        print(out)
        bad += 1
    else:
        man = json.loads((hw / "release/A/MANIFEST.json").read_text())
        cpl = (hw / "release/A/assembly/main/main_cpl_jlcpcb.csv").read_text().splitlines()
        pins = json.loads((hw / "release/A/firmware/pins.json").read_text())
        rot_ok = any(l.startswith("U1,") and l.endswith(",90") for l in cpl)
        print(f"      {len(man['files'])} files in manifest; U1 rotation offset applied: {rot_ok}; "
              f"pins mapped: {len(pins['pins'])}")
        bad += 0 if rot_ok and len(pins["pins"]) == 3 else 1
        # hand edit after assembly must fail the manifest check
        (hw / "release/A/ORDER.md").write_text("edited by hand\n")
        c = subprocess.run([sys.executable, HERE / "release_check.py", hw / "release/A", "--hw", hw, "--today", TODAY],
                           capture_output=True, text=True)
        r = json.loads((hw / "release/A/checks/release-check.json").read_text())
        hit = any(i["check"] == "manifest" for i in r["items"] if i["level"] == "fail")
        print(f"{'PASS' if c.returncode == 1 and hit else 'FAIL'}  hand-edited release file → manifest failure")
        bad += 0 if c.returncode == 1 and hit else 1
    for i, (name, mut, check, today) in enumerate(CASES):
        hw = build_fixture(base / f"case{i}")
        if mut:
            mut(hw)
        code, out, res = run(hw, today)
        fails = [x for x in (res or {}).get("items", []) if x["level"] == "fail"]
        hit = any(x["check"] == check for x in fails)
        ok = code == 1 and hit
        first = next((x["message"] for x in fails if x["check"] == check), out.strip()[:160])
        print(f"{'PASS' if ok else 'FAIL'}  {name} → {check}: {first}")
        bad += 0 if ok else 1
    if not a.keep:
        shutil.rmtree(base)
    else:
        print("kept", base)
    print(f"selftest: {len(CASES) + 2 - bad}/{len(CASES) + 2} cases as expected")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
