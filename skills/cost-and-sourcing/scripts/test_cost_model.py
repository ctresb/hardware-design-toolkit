#!/usr/bin/env python3
"""Tests for cost_model.py (stdlib only). Run: python3 test_cost_model.py"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cost_model as cm  # noqa: E402

EX = os.path.join(HERE, "..", "templates", "manufacturing.example.json")
FAILS = []


def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def run(mfg_path, out):
    return subprocess.run([sys.executable, os.path.join(HERE, "cost_model.py"), "--mfg", mfg_path, "--out", out,
                           "--svg"], capture_output=True, text=True)


ok(cm.verdict((5, 9), 10) == "met", "verdict met when the whole range is under the target")
ok(cm.verdict((11, 14), 10) == "not met", "verdict not met when the whole range is over")
ok(cm.verdict((8, 14), 10) == "not proven", "verdict not proven when the target is inside the range")
ok(cm.money(12.0) == "$12", "whole-number targets print without decimals")

with tempfile.TemporaryDirectory() as d:
    p = run(EX, d)
    ok(p.returncode == 0, "example runs")
    md = os.path.join(d, "cost.md")
    text = open(md).read()
    ok(cm.BEGIN in text and cm.END in text, "cost.md has generated-block markers")
    ok("Target, recurring" in text, "cost.md shows the target row")
    ok(", recurring |" in text and ", incl. NRE |" in text, "landed cost is shown recurring and incl. NRE")
    m = json.load(open(os.path.join(d, "model.json")))
    t = next(x for x in m["tiers"] if x["units"] == 1000)
    ok(all("recurring_per_unit" in x for x in t["landed"]), "model.json has landed recurring per unit")
    ok(all(x["recurring_per_unit"][1] <= x["per_unit"][1] for x in t["landed"]), "landed recurring <= incl. NRE")

    # hand-written text outside the markers survives a re-run
    open(md, "w").write("# My cost notes\n\nKeep me.\n\n" + text + "\n## After\n\nKeep me too.\n")
    run(EX, d)
    t2 = open(md).read()
    ok("Keep me." in t2 and "Keep me too." in t2, "text outside the markers is kept")
    ok(t2.count(cm.BEGIN) == 1, "exactly one generated block after a re-run")

    # a hand-written file without markers is kept and gets the block appended once
    open(md, "w").write("# Narrative only\n\nMy analysis.\n")
    run(EX, d)
    run(EX, d)
    t3 = open(md).read()
    ok(t3.startswith("# Narrative only") and t3.count(cm.BEGIN) == 1, "unmarked narrative kept, block appended once")

    # chart: conclusion title, labels inside the canvas, every bar labeled
    svg = open(os.path.join(d, "cost.svg")).read()
    W = float(re.search(r'viewBox="0 0 ([0-9.]+)', svg).group(1))
    title = re.search(r'font-weight="600">([^<]+)</text>', svg).group(1)
    ok("target" in title.lower() or "costs" in title.lower(), f"title states a conclusion: {title!r}")
    labels = re.findall(r'<text class="t2 halo" x="([0-9.]+)"[^>]*?(text-anchor="end")?[^>]*>(\$[^<]+)</text>', svg)
    inside = re.findall(r'fill="#ffffff">(\$[^<]+)</text>', svg)
    ok(len(labels) + len(inside) == 2 * len(m["tiers"]), "every bar has a value label")
    in_canvas = all((float(x) - (len(s) * 11 * 0.6 if anchor else 0)) >= 0 and
                    (float(x) + (0 if anchor else len(s) * 11 * 0.6)) <= W for x, anchor, s in labels)
    ok(in_canvas, "value labels stay inside the canvas")

    # labels move left of the bar when the right side has no room
    big = json.load(open(EX))
    big["targets"] = {"unit_cost": {"1": 5000}}
    bp = os.path.join(d, "big.json")
    json.dump(big, open(bp, "w"))
    if "bom" in big and isinstance(big["bom"], dict) and big["bom"].get("path"):
        big["bom"]["path"] = os.path.join(os.path.dirname(os.path.abspath(EX)), big["bom"]["path"])
        json.dump(big, open(bp, "w"))
    d2 = os.path.join(d, "big")
    p = run(bp, d2)
    ok(p.returncode == 0, "runs with a target at qty 1")

print(f"{len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
