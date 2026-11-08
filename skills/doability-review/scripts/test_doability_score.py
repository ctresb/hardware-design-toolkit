#!/usr/bin/env python3
"""Tests for doability_score.py (stdlib only): python3 test_doability_score.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "doability_score.py")
ALL = ["parts", "electrical", "power", "pcb", "mechanical", "compliance", "cost", "schedule", "claims"]
BP = {k: True for k in ["routed_board", "drc_erc_zero", "fab_files", "bom_in_stock", "enclosure_step",
                        "assembly_validated", "test_plan"]}
PROD = {"measurements_done": True, "quotes_received": True, "certifications_planned": True}
CHECK = {"id": "V-001", "what": "Average current, recording", "method": "10 min recording, firmware release build",
         "instrument": "power profiler (≥100 kHz sampling)", "pass_criteria": "≤ 1.5 mA average"}


def run(data, *extra):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "f.json")
        out = os.path.join(d, "r.json")
        json.dump(data, open(p, "w"))
        r = subprocess.run([sys.executable, SCRIPT, p, "--quiet", "--json", out, *extra],
                           capture_output=True, text=True)
        res = json.load(open(out)) if os.path.exists(out) else None
        return r.returncode, res, r.stdout + r.stderr


def base(**kw):
    d = dict(reviewed_areas=ALL, build_package=dict(BP), production={}, prototype_checks=[CHECK], findings=[])
    d.update(kw)
    return d


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def fixable_finding_starts_loop():
    f = dict(id="F-1", area="pcb", severity="major", status="open", title="trace too thin",
             owner="pcb-engineer", fix="widen VBAT to 0.3 mm", auto_fixable=True)
    code, r, _ = run(base(findings=[f]))
    assert code == 3 and r["overall"] == "NOT READY" and "fix loop" in r["next"], (code, r)
    assert r["fixes"]["pcb-engineer"][0]["id"] == "F-1"
    assert [a["status"] for a in r["areas"] if a["area"] == "pcb"] == ["FIX"]


@case
def leftover_fix_after_last_round_blocks():
    f = dict(id="F-1", area="pcb", severity="major", status="open", title="trace too thin",
             owner="pcb-engineer", fix="widen VBAT", auto_fixable=True)
    code, r, _ = run(base(findings=[f], round=3))
    assert code == 2 and r["overall"] == "NOT READY" and r["blockers"][0]["id"] == "F-1", (code, r)


@case
def user_blocker():
    f = dict(id="F-2", area="power", severity="critical", status="open", title="cell capacity unknown",
             owner="battery-and-power", fix="size the cell from a vendor quote", auto_fixable=False,
             blocker="quote", action="Send the RFQ in hw/cost/rfq.md to two cell vendors")
    code, r, _ = run(base(findings=[f]))
    assert code == 2 and r["overall"] == "NOT READY", (code, r)
    assert r["blockers"][0]["type"] == "quote"


@case
def ready_prototype():
    f = dict(id="F-3", area="power", severity="major", status="open", title="runtime not measured",
             owner="battery-and-power", fix="measure on the prototype", auto_fixable=False, prototype_check="V-001")
    code, r, _ = run(base(findings=[f]))
    assert code == 0 and r["overall"] == "READY TO BUILD (prototype)", (code, r)


@case
def ready_production():
    code, r, _ = run(base(production=dict(PROD)))
    assert code == 0 and r["overall"] == "READY TO BUILD (production)", (code, r)


@case
def missing_build_package_item():
    bp = dict(BP, routed_board=False)
    code, r, _ = run(base(build_package=bp))
    assert code == 2 and any("routed" in b["title"].lower() for b in r["blockers"]), (code, r)


@case
def not_reviewed_area_blocks():
    code, r, _ = run(base(reviewed_areas=ALL[:-1]))
    assert code == 2 and r["areas"][-1]["status"] == "NOT-REVIEWED", (code, r)


@case
def fixed_findings_without_review_stay_not_reviewed():
    # the PoC bug: an area whose findings were all fixed showed GO although nobody reviewed it
    fs = [dict(id="M1", area="mechanical", severity="major", status="fixed")]
    rest = [a for a in ALL if a != "mechanical"]
    code, r, _ = run(base(reviewed_areas=rest, findings=fs))
    st = {x["area"]: x["status"] for x in r["areas"]}
    assert code == 2 and st["mechanical"] == "NOT-REVIEWED" and r["overall"] == "NOT READY", (code, st)


@case
def input_errors():
    bad = base(prototype_checks=[{"id": "V-9", "what": "x"}],
               findings=[dict(id="X", area="foo", severity="major", status="open")])
    code, r, out = run(bad)
    assert code == 1 and "auto_fixable" in out and "pass_criteria" in out and "area 'foo'" in out, (code, out)


@case
def fixed_and_accepted_do_not_block():
    fs = [dict(id="A", area="pcb", severity="critical", status="fixed"),
          dict(id="B", area="cost", severity="major", status="accepted", decision="D-002")]
    code, r, _ = run(base(findings=fs, production=dict(PROD)))
    assert code == 0 and r["overall"] == "READY TO BUILD (production)", (code, r)


if __name__ == "__main__":
    bad = 0
    for c in CASES:
        try:
            c()
            print("ok  ", c.__name__)
        except AssertionError as ex:
            bad += 1
            print("FAIL", c.__name__, ex)
    print(f"test_doability_score: {len(CASES) - bad}/{len(CASES)} passed")
    sys.exit(1 if bad else 0)
