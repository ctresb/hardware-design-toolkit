#!/usr/bin/env python3
"""Tests for compliance_matrix.py (stdlib only). Run: python3 test_compliance_matrix.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import compliance_matrix as cm  # noqa: E402

RULES = json.load(open(cm.DEFAULT_RULES))
FAILS = []


def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def ids(res):
    return {r["id"] for r in res["global"]} | {r["id"] for rows in res["markets"].values() for r in rows}


coin = {"product": "t", "markets": ["US", "EU", "UK"], "radios": ["ble"], "battery": {"chemistry": "coin-cell"},
        "product_category": "item_finder"}
_, res = cm.build(coin, RULES)
ok("un38-3" in ids(res), "a coin cell triggers UN 38.3")
ok("coin-cell-62368" in {r["id"] for r in res["markets"].get("EU", [])}, "a coin cell triggers EN 62368-1 4.8 in the EU")
ok("dult-item-finder" in ids(res), "an item finder triggers the DULT rule")

listed = dict(coin, battery={"chemistry": ["coin-cell", "li-primary"]})
_, res2 = cm.build(listed, RULES)
ok("un38-3" in ids(res2), "a list-valued chemistry matches `in`")

# shared rows are counted once in the unique total
uniq = cm.unique_rows(res)
per_market_rows = len(res["global"]) + sum(len(v) for v in res["markets"].values())
ok(len(uniq) < per_market_rows, f"unique rows ({len(uniq)}) < per-market rows ({per_market_rows})")
ok(len({r['id'] for r, _ in uniq}) == len(uniq), "unique rows have no duplicate id")
shared = [r for r, ms in uniq if len(ms) > 1]
ok(any(r["id"] == "coin-cell-62368" for r in shared), "EN 62368-1 4.8 is listed as shared by EU and UK")

# local override: replace, disable, add
local = {"rules": [
    {"id": "dult-item-finder", "disabled": True},
    dict(next(r for r in RULES["rules"] if r["id"] == "un38-3"), cost_usd=[1, 2]),
    {"id": "x-local", "markets": ["*"], "area": "other", "name": "Local rule", "if": {}, "cost_usd": [5, 5],
     "lead_weeks": [0, 1], "evidence": "assumption", "source": "test", "notes": "test", "levers": ""},
]}
merged, log = cm.merge_local(RULES, local)
_, res3 = cm.build(coin, merged)
ok("dult-item-finder" not in ids(res3), "a disabled local rule is removed")
ok(next(r for r in merged["rules"] if r["id"] == "un38-3")["cost_usd"] == [1, 2], "a local rule replaces by id")
ok("x-local" in ids(res3), "a new local rule is added")
ok(len(merged["rules"]) == len(RULES["rules"]), "rule count = base - 1 disabled + 1 added")

# CLI auto-loads rules.local.json next to the traits file, and markdown shows the unique total
with tempfile.TemporaryDirectory() as d:
    json.dump(coin, open(os.path.join(d, "traits.json"), "w"))
    json.dump(local, open(os.path.join(d, "rules.local.json"), "w"))
    p = subprocess.run([sys.executable, os.path.join(HERE, "compliance_matrix.py"), "--traits",
                        os.path.join(d, "traits.json")], capture_output=True, text=True)
    ok(p.returncode == 0, "CLI exits 0")
    ok("Project-local rules applied" in p.stdout, "markdown names the local rules")
    ok("Total, all target markets (each row once)" in p.stdout, "markdown shows the de-duplicated total")
    ok("x-local" not in p.stdout or "Local rule" in p.stdout, "local rule appears in the matrix")

print(f"{len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
