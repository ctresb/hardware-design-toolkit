#!/usr/bin/env python3
"""Final verdict, area statuses and fix list for a doability review.

Reads hw/doability/findings.json (format in the doability-review SKILL.md) and computes:

  per area : GO | FIX | BLOCKED | NOT-REVIEWED
             GO      = listed in reviewed_areas and no open blocking finding. Fixed findings alone never
                       make an area GO: the whole area must have been reviewed.
             FIX     = an open finding the toolkit can fix on its own (auto_fixable: true)
             BLOCKED = an open critical/major finding that needs the user or the physical world
  overall  : READY TO BUILD (production) | READY TO BUILD (prototype) | NOT READY
             READY TO BUILD (prototype): no FIX, BLOCKED or NOT-REVIEWED area; every build-package item done;
                 every "verify on the prototype" check has a method, an instrument and a pass criterion.
             READY TO BUILD (production): the same, plus every production item done and no open finding
                 that waits for a prototype measurement.
             NOT READY: anything else, with the exact blockers listed.

Fix loop: while fixable findings remain and round < max rounds (default 3), the result is NOT READY with
"next: fix loop" and exit code 3. hardware-engineer hands the fix list to the owner skills and runs the
review again with round + 1. After the last round, fixable critical/major findings left over become blockers.

Exit codes: 0 READY TO BUILD (either level), 3 fix loop must continue, 2 NOT READY (blocked), 1 input error.

Outputs (CONVENTIONS.md §4): --json hw/doability/score.json is the canonical machine-readable verdict. Its key
`overall` is the one overall-verdict key that build-package and product-presentation read. It also carries
`areas`, `blockers`, `fixes`, `build_package`, `production` and `prototype_checks` (the "verify on the
prototype" list: what, method, instrument, pass_criteria), so readers need only this file.

Example:
  python3 doability_score.py hw/doability/findings.json --json hw/doability/score.json \
      --md hw/doability/score.md --fixes hw/doability/fixes.json
"""
import argparse
import json
import sys

AREAS = ["parts", "electrical", "power", "pcb", "mechanical", "compliance", "cost", "schedule", "claims"]
LABELS = {"parts": "Parts", "electrical": "Electrical", "power": "Power and battery", "pcb": "PCB",
          "mechanical": "Mechanical", "compliance": "Compliance", "cost": "Cost", "schedule": "Schedule",
          "claims": "Claims vs reality"}
SEVERITIES = ["critical", "major", "minor", "info"]
STATUSES = ["open", "fixed", "accepted"]
BLOCKER_TYPES = ["decision", "quote", "measurement", "purchase", "external"]
BUILD_PACKAGE = {
    "routed_board": "Boards routed (no unrouted nets)",
    "drc_erc_zero": "DRC and ERC with 0 violations, schematic parity",
    "fab_files": "Fab files: Gerbers, drill, pick-and-place, assembly drawing",
    "bom_in_stock": "BOM in stock at the chosen assembler (or consigned parts bought)",
    "enclosure_step": "Enclosure STEP, ready for a print, machining or molding quote",
    "assembly_validated": "Assembly validator: 0 interpenetrations; tolerance study done",
    "test_plan": "Bring-up and test plan written",
}
PRODUCTION = {
    "measurements_done": "Prototype measurements done and passed",
    "quotes_received": "Quotes received for every NRE and recurring cost line",
    "certifications_planned": "Certifications planned with lab, cost and dates",
}
CHECK_FIELDS = ["what", "method", "instrument", "pass_criteria"]


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as ex:
        raise SystemExit(f"error: cannot read {path}: {ex}")
    if isinstance(data, list):
        data = {"findings": data}
    for k, v in (("findings", []), ("prototype_checks", []), ("build_package", {}), ("production", {})):
        data.setdefault(k, v)
    errors = []
    check_ids = {c.get("id") for c in data["prototype_checks"]}
    for i, f in enumerate(data["findings"]):
        fid = f.get("id", f"#{i + 1}")
        if f.get("area") not in AREAS:
            errors.append(f"{fid}: area '{f.get('area')}' not in {AREAS}")
        if f.get("severity") not in SEVERITIES:
            errors.append(f"{fid}: severity '{f.get('severity')}' not in {SEVERITIES}")
        f.setdefault("status", "open")
        if f["status"] not in STATUSES:
            errors.append(f"{fid}: status '{f['status']}' not in {STATUSES}")
        if f["status"] == "accepted" and not f.get("decision"):
            errors.append(f"{fid}: status 'accepted' needs 'decision' (an entry such as D-004 in hw/decisions.md)")
        if f["status"] != "open" or f.get("severity") == "info":
            continue
        for k in ("owner", "fix"):
            if not f.get(k):
                errors.append(f"{fid}: open finding without '{k}'")
        if not isinstance(f.get("auto_fixable"), bool):
            errors.append(f"{fid}: 'auto_fixable' must be true or false")
        if f.get("prototype_check") and f["prototype_check"] not in check_ids:
            errors.append(f"{fid}: prototype_check '{f['prototype_check']}' is not in prototype_checks")
        if (f.get("auto_fixable") is False and not f.get("prototype_check")
                and f.get("severity") in ("critical", "major")):
            if f.get("blocker") not in BLOCKER_TYPES:
                errors.append(f"{fid}: non-fixable finding needs 'blocker' in {BLOCKER_TYPES}")
            if not f.get("action"):
                errors.append(f"{fid}: non-fixable finding needs 'action' (the exact step for the user)")
    for i, c in enumerate(data["prototype_checks"]):
        for k in ["id"] + CHECK_FIELDS:
            if not c.get(k):
                errors.append(f"prototype check {c.get('id', '#' + str(i + 1))}: missing '{k}'")
    for k in list(data["build_package"]) + list(data["production"]):
        if k not in BUILD_PACKAGE and k not in PRODUCTION:
            errors.append(f"unknown build-package or production item '{k}'")
    return data, errors


def evaluate(data, max_rounds):
    rnd = int(data.get("round", 1))
    last_round = rnd >= max_rounds
    reviewed = set(data.get("reviewed_areas", []))
    open_ = [f for f in data["findings"] if f["status"] == "open" and f["severity"] != "info"]
    # a finding that waits for a prototype measurement does not block the prototype level
    proto_wait = [f for f in open_ if f.get("prototype_check") and not f.get("auto_fixable")]
    active = [f for f in open_ if f not in proto_wait]
    fixable = [f for f in active if f.get("auto_fixable")]
    hard = [f for f in active if not f.get("auto_fixable") and f["severity"] in ("critical", "major")]
    soft = [f for f in active if not f.get("auto_fixable") and f["severity"] == "minor"]
    if last_round and fixable:          # fixes the toolkit could not land in the last round become blockers
        hard += [dict(f, blocker="external", action=f"Auto-fix failed after {rnd} rounds: {f['fix']}")
                 for f in fixable if f["severity"] in ("critical", "major")]
        soft += [f for f in fixable if f["severity"] == "minor"]
        fixable = []
    hard_areas = {f["area"] for f in hard}
    fix_areas = {f["area"] for f in fixable}
    rows = []
    for a in AREAS:
        n = {s: sum(1 for f in open_ if f["area"] == a and f["severity"] == s) for s in SEVERITIES}
        # open problems always show; GO needs an explicit review of the whole area, because fixed findings
        # alone do not prove that the rest of the area was checked
        if a in hard_areas:
            st = "BLOCKED"
        elif a in fix_areas:
            st = "FIX"
        elif a in reviewed:
            st = "GO"
        else:
            st = "NOT-REVIEWED"
        rows.append(dict(area=a, status=st, **n))
    statuses = {r["status"] for r in rows}
    missing_bp = [k for k in BUILD_PACKAGE if not data["build_package"].get(k)]
    missing_prod = [k for k in PRODUCTION if not data["production"].get(k)]
    if fixable:
        overall = "NOT READY"
        nxt = f"fix loop: apply {len(fixable)} fix(es), then run review round {rnd + 1} of {max_rounds}"
    elif statuses & {"BLOCKED", "NOT-REVIEWED"} or missing_bp:
        overall, nxt = "NOT READY", "resolve the blockers listed below"
    elif missing_prod or proto_wait:
        overall, nxt = "READY TO BUILD (prototype)", "build the prototype and run the 'Verify on the prototype' list"
    else:
        overall, nxt = "READY TO BUILD (production)", "release to production"
    blockers = [dict(id=f.get("id"), area=f["area"], type=f.get("blocker"), title=f.get("title", ""),
                     action=f.get("action", ""), owner=f.get("owner", "")) for f in hard]
    blockers += [dict(id=None, area=None, type="external", title=BUILD_PACKAGE[k],
                      action=f"Complete the build-package item: {BUILD_PACKAGE[k]}", owner="hardware-engineer")
                 for k in missing_bp]
    blockers += [dict(id=None, area=r["area"], type="external", title=f"{LABELS[r['area']]} not reviewed",
                      action="Review this area, or list it in reviewed_areas if it was checked with no findings",
                      owner="doability-review") for r in rows if r["status"] == "NOT-REVIEWED"]
    fixes = {}
    for f in fixable:
        fixes.setdefault(f["owner"], []).append(dict(id=f.get("id"), severity=f["severity"],
                                                     title=f.get("title", ""), fix=f["fix"]))
    return dict(round=rnd, max_rounds=max_rounds, overall=overall, next=nxt, areas=rows, blockers=blockers,
                fixes=fixes, minor_open=[f.get("id") for f in soft],
                waiting_on_prototype=[f.get("id") for f in proto_wait],
                missing_build_package=missing_bp, missing_production=missing_prod,
                build_package=data["build_package"], production=data["production"],
                prototype_checks=data["prototype_checks"], maturity=data.get("maturity"),
                project=data.get("project"), date=data.get("date"))


def markdown(data, r):
    out = []
    for k, lab in (("project", "Project"), ("date", "Date")):
        if data.get(k):
            out.append(f"**{lab}:** {data[k]}  ")
    out.append(f"**Review round:** {r['round']} of {r['max_rounds']}  ")
    out.append(f"**Final verdict:** {r['overall']}  ")
    out.append(f"**Next:** {r['next']}")
    out += ["", "| Area | Status | Critical | Major | Minor |", "|---|---|---|---|---|"]
    for a in r["areas"]:
        out.append(f"| {LABELS[a['area']]} | {a['status']} | {a['critical']} | {a['major']} | {a['minor']} |")
    out += ["", "Counts are open findings. GO: nothing open blocks the area. FIX: the toolkit fixes it in the loop. "
            "BLOCKED: needs the user or the physical world.", "", "### Build package", ""]
    out += [f"- [{'x' if data['build_package'].get(k) else ' '}] {lab}" for k, lab in BUILD_PACKAGE.items()]
    out += ["", "### Production readiness", ""]
    out += [f"- [{'x' if data['production'].get(k) else ' '}] {lab}" for k, lab in PRODUCTION.items()]
    if r["fixes"]:
        out += ["", "### Fix list for this round", ""]
        for owner, lst in r["fixes"].items():
            out += [f"- **{f['id']}** → `{owner}` ({f['severity']}): {f['fix']}" for f in lst]
    if r["blockers"]:
        out += ["", "### Blockers (need the user or the physical world)", ""]
        for b in r["blockers"]:
            tag = f"**{b['id']}** " if b["id"] else ""
            out.append(f"- {tag}[{b['type']}] {b['title']} → {b['action']}")
    if data["prototype_checks"]:
        out += ["", "### Verify on the prototype", "", "| ID | What | Method | Instrument | Pass criteria |",
                "|---|---|---|---|---|"]
        out += [f"| {c['id']} | {c['what']} | {c['method']} | {c['instrument']} | {c['pass_criteria']} |"
                for c in data["prototype_checks"]]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("findings", help="path to findings.json")
    ap.add_argument("--md", help="write the Markdown snippet to this file")
    ap.add_argument("--json", help="write the computed result as JSON to this file")
    ap.add_argument("--fixes", help="write the fix list, grouped by owner skill, to this JSON file")
    ap.add_argument("--max-rounds", type=int, default=3, help="fix-loop rounds before fixable findings block (3)")
    ap.add_argument("--quiet", action="store_true", help="only print the summary line")
    a = ap.parse_args()
    data, errors = load(a.findings)
    if errors:
        for e in errors:
            print("error:", e, file=sys.stderr)
        print(f"doability_score: {len(errors)} input error(s) in {a.findings}")
        return 1
    r = evaluate(data, a.max_rounds)
    md = markdown(data, r)
    for path, payload in ((a.md, md), (a.json, json.dumps(r, indent=1)), (a.fixes, json.dumps(r["fixes"], indent=1))):
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(payload)
    if not a.quiet:
        print(md)
    nfix = sum(len(v) for v in r["fixes"].values())
    print(f"doability_score: {r['overall']} (round {r['round']}/{r['max_rounds']}); {nfix} fix(es), "
          f"{len(r['blockers'])} blocker(s), {len(data['prototype_checks'])} prototype check(s)")
    if r["overall"].startswith("READY"):
        return 0
    return 3 if r["fixes"] else 2


if __name__ == "__main__":
    sys.exit(main())
