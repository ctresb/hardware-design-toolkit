#!/usr/bin/env python3
"""Tests for roadmap.py (stdlib only). Run: python3 test_roadmap.py"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import roadmap as rm  # noqa: E402

FAILS = []


def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


# wrapping never cuts a word
name = "Dev-kit current measurement on the vendor LaunchPad with a power profiler"
lines = rm.wrap(name, 180, 12)
words = set(name.split())
ok(len(lines) <= 2, "wrap gives at most 2 lines")
ok(all(w in words or w == "…" for ln in lines for w in ln.split()), "wrap breaks only between words")
ok(lines[-1].endswith("…"), "an over-long name ends with an ellipsis after a whole word")
ok(rm.wrap("Short", 180, 12) == ["Short"], "a short name stays on one line")

today = dt.date.today()
stages = {
    "project": "Test",
    "start": today.isoformat(),
    "stages": [
        {"id": "A", "name": name, "weeks": [2, 4]},
        {"id": "B", "name": "JLCPCB assembly of the first ten boards", "weeks": [3, 5], "depends_on": ["A"]},
        {"id": "C", "name": "Build", "weeks": [4, 6], "depends_on": ["B"]},
    ],
    "milestones": [{"name": "Engineering freeze and ready-to-build review", "after": "A"},
                   {"name": "First boards", "after": "B"}, {"name": "Launch", "after": "C"}],
    "long_lead": [
        {"item": "SoC", "lead_weeks": 26, "needed_by": "B", "qty_needed": 130,
         "stock": {"on_hand": 9278, "source": "LCSC", "date": today.isoformat()}},
        {"item": "Holder", "lead_weeks": 26, "needed_by": "B", "qty_needed": 130,
         "stock": {"on_hand": 12, "source": "LCSC", "date": today.isoformat()}},
        {"item": "Crystal", "lead_weeks": 26, "needed_by": "B"},
    ],
}
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "stages.json")
    json.dump(stages, open(p, "w"))
    r = subprocess.run([sys.executable, os.path.join(HERE, "roadmap.py"), "--stages", p, "--md",
                        os.path.join(d, "s.md"), "--svg", os.path.join(d, "t.svg")], capture_output=True, text=True)
    ok(r.returncode == 0, "roadmap runs")
    md = open(os.path.join(d, "s.md")).read()
    row = lambda item: next(ln for ln in md.splitlines() if ln.startswith(f"| {item} |"))
    ok("in stock" in row("SoC") and "LATE" not in row("SoC"), "a passed order date with stock is buy-now, not late")
    ok("LATE" in row("Holder") and "12 < 130" in row("Holder"), "too little stock is still late, with the shortfall")
    ok("LATE" in row("Crystal"), "no stock data keeps the late flag")
    ok("1 to buy from stock now" in r.stderr and "2 long-lead item(s) late" in r.stderr, "summary counts both kinds")
    svg = open(os.path.join(d, "t.svg")).read()
    H = float(re.search(r'viewBox="0 0 [0-9.]+ ([0-9.]+)"', svg).group(1))
    ok(H > 100, "SVG height is set after layout")
    ok("__GRID_END__" not in svg, "grid placeholders are replaced")
    tspans = re.findall(r"<tspan[^>]*>([^<]+)</tspan>", svg)
    ok(all(all(w in words or w in ("A", "B", "C", "…") or w in "JLCPCB assembly of the first ten boards Build".split()
               for w in t.split()) for t in tspans), "stage labels contain only whole words")
    # milestone labels in one lane do not overlap
    ms = [(float(x), float(y), anc, txt) for x, y, anc, txt in
          re.findall(r'<text x="([0-9.]+)" y="([0-9.]+)" font-size="10" fill="#111111"( text-anchor="end")? '
                     r'paint-order[^>]*>([^<]+)</text>', svg)]
    spans = {}
    for x, y, anc, txt in ms:
        w = rm.tw(txt, 10)
        spans.setdefault(y, []).append((x - w, x) if anc else (x, x + w))
    overlap = any(a[1] > b[0] for lane in spans.values() for a, b in zip(sorted(lane), sorted(lane)[1:]))
    ok(len(ms) == 3 and not overlap, "milestone labels are placed in lanes without overlap")
    diamonds = [float(x) for x in re.findall(r'<path d="M([0-9.]+) ', svg)]
    lane0 = min(spans) if spans else None
    covers = any(a < dx + 6 and b > dx - 6 and not (abs(a - 9 - dx) < 1 or abs(b + 9 - dx) < 1 or abs(a - 7 - dx) < 1)
                 for a, b in spans.get(lane0, []) for dx in diamonds)
    ok(not covers, "no lane-0 label covers another milestone's diamond")

print(f"{len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
