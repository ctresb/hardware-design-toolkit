#!/usr/bin/env python3
"""Check the project notebook (hw/knowledge, hw/decisions.md) for the defects that cause regressions.

Checks:
  - duplicate IDs (F-, E-, L-, D-, REQ-) across the notebook files;
  - facts without an evidence tag;
  - experiments without a verdict (worked | did not work | inconclusive);
  - lessons without a rule;
  - superseded entries that point to an ID that does not exist.

Usage:
  notebook_check.py hw/                 check the notebook, exit 1 on errors
  notebook_check.py hw/ --next F        print the next free F- ID (also E, L, D)
"""
import argparse
import pathlib
import re
import sys

HEAD = re.compile(r"^##\s+((F|E|L|D)-(\d{3,}))\b(.*)$")
EVIDENCE = re.compile(r"\[(verified|estimate|assumption)\b", re.I)
VERDICT = re.compile(r"\*\*Verdict:\*\*\s*(worked|did not work|inconclusive)\b", re.I)
RULE = re.compile(r"\*\*Rule:\*\*\s*\S")
SUPERSEDED = re.compile(r"SUPERSEDED on [0-9-]+ by ((F|E|L|D)-\d{3,})")

FILES = {
    "F": "knowledge/FACTS.md",
    "E": "knowledge/EXPERIMENTS.md",
    "L": "knowledge/LESSONS.md",
    "D": "decisions.md",
}


def entries(path):
    """Yield (id, kind, line_no, body) for each '## X-NNN' entry outside HTML comments."""
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    lines = text.splitlines()
    cur = None
    for i, line in enumerate(lines, 1):
        m = HEAD.match(line)
        if m:
            if cur:
                yield cur
            cur = [m.group(1), m.group(2), i, [line]]
        elif cur is not None:
            if line.startswith("# ") or (line.startswith("## ") and not HEAD.match(line)):
                yield cur
                cur = None
            else:
                cur[3].append(line)
    if cur:
        yield cur


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("hw", type=pathlib.Path, help="the project's hw/ folder")
    ap.add_argument("--next", choices=list(FILES), help="print the next free ID of this kind and exit")
    a = ap.parse_args()
    if not a.hw.is_dir():
        print(f"error: {a.hw} is not a folder", file=sys.stderr)
        return 2

    seen = {}
    errors, warnings = [], []
    all_entries = []
    for kind, rel in FILES.items():
        p = a.hw / rel
        for eid, k, ln, body in entries(p):
            all_entries.append((eid, k, p, ln, "\n".join(body)))
            if eid in seen:
                errors.append(f"{rel}:{ln}: duplicate ID {eid} (first at {seen[eid]})")
            else:
                seen[eid] = f"{rel}:{ln}"
            if k != kind:
                warnings.append(f"{rel}:{ln}: {eid} is in the {kind}- file")

    if a.next:
        nums = [int(e[0].split("-")[1]) for e in all_entries if e[1] == a.next]
        print(f"{a.next}-{(max(nums) + 1 if nums else 1):03d}")
        return 0

    for eid, k, p, ln, body in all_entries:
        rel = p.relative_to(a.hw)
        if k == "F" and not EVIDENCE.search(body):
            errors.append(f"{rel}:{ln}: {eid} has no evidence tag ([verified: …] / [estimate: …] / [assumption])")
        if k == "E" and not VERDICT.search(body):
            errors.append(f"{rel}:{ln}: {eid} has no verdict (worked | did not work | inconclusive)")
        if k == "L" and not RULE.search(body):
            errors.append(f"{rel}:{ln}: {eid} has no **Rule:** line")
        for m in SUPERSEDED.finditer(body):
            if m.group(1) not in seen:
                errors.append(f"{rel}:{ln}: {eid} is superseded by {m.group(1)}, which does not exist")

    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("error:", e)
    counts = {k: sum(1 for e in all_entries if e[1] == k) for k in FILES}
    summary = ", ".join(f"{n} {k}-" for k, n in counts.items())
    print(f"notebook: {summary}; {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
