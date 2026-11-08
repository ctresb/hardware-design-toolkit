#!/usr/bin/env python3
"""Check that every part's supply range contains the rail it is connected to.

This file is the single implementation of rail checking in the toolkit. `specs-engineer/scripts/bom_check.py`
and `electronics-researcher/scripts/bom_merge.py` import it; do not copy its logic elsewhere.

Inputs (CONVENTIONS.md §5):
  hw/bom.csv           `supply_rail_v` holds a rail NAME from rails.json (`VSYS`, `1V8`). A part on several
                       rails lists them as `VSYS|1V8`, matched in order to the `vdd`, `vdd2`, `vdd3`… tokens of
                       `key_specs` (`vdd=2.5-5.5; vdd2=1.65-1.95; i2c=0x2C`). A plain number (`1.8`) is accepted
                       as a fallback and treated as ±5 %, with a warning.
  hw/power/rails.json  {"<RAIL>": {"min": V, "max": V, "max_ma": mA}}  or  {"<RAIL>": {"nom": V, "tol": V, "max_ma": mA}}
                       `tol` is in volts: {"nom": 1.8, "tol": 0.05} spans 1.75–1.85 V.

A part fails when the rail's full range is not inside the part's vdd range.
Standard library only.

usage: check_rails.py hw/bom.csv hw/power/rails.json
"""
import argparse
import csv
import json
import re
import sys

NO_RAIL = {"", "-", "none", "passive", "n/a", "na"}
LITERAL_TOL = 0.05          # fraction applied to a plain-number rail


def parse_range(v):
    """'1.7-3.6', '1.71–3.6 V' or '1.8' -> (lo, hi); None if not a voltage."""
    v = (v or "").replace("–", "-").replace("—", "-").replace("V", "").replace("v", "").strip()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)$", v)
    if m:
        return float(m.group(1)), float(m.group(2))
    try:
        x = float(v)
        return x, x
    except ValueError:
        return None


def parse_specs(s):
    """'vdd=1.7-3.6; i2c=0x2C' -> {'vdd': '1.7-3.6', 'i2c': '0x2C'} (keys lower-case)."""
    out = {}
    for tok in (s or "").split(";"):
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out


def rail_names(value):
    """'VSYS|1V8' -> ['VSYS', '1V8']; '' / '-' / 'passive' -> []."""
    if (value or "").strip().lower() in NO_RAIL:
        return []
    return [n.strip() for n in value.split("|") if n.strip()]


def rail_span(name, rails):
    """(lo, hi, max_ma, defined) for a rail name, or for a plain voltage (defined=False); None if unknown."""
    if name in rails:
        r = rails[name]
        if "min" in r and "max" in r:
            return float(r["min"]), float(r["max"]), r.get("max_ma"), True
        if "nom" in r:
            nom, tol = float(r["nom"]), float(r.get("tol", 0.0))
            return nom - tol, nom + tol, r.get("max_ma"), True
        raise ValueError(f"rail {name}: give min+max or nom+tol")
    rr = parse_range(name)
    if rr and rr[0] == rr[1]:
        x = rr[0]
        return x * (1 - LITERAL_TOL), x * (1 + LITERAL_TOL), None, False
    return None


def check_row(row, rails):
    """Check one BOM row. Returns a list of (level, message) with level 'error' | 'warning' | 'skip'."""
    out = []
    specs = parse_specs(row.get("key_specs"))
    for k, name in enumerate(rail_names(row.get("supply_rail_v", ""))):
        key = "vdd" if k == 0 else f"vdd{k + 1}"
        span = rail_span(name, rails)
        if span is None:
            out.append(("error" if rails else "warning", f"rail '{name}' is not defined in rails.json"))
            continue
        lo, hi, _max_ma, defined = span
        if not defined:
            out.append(("warning", f"rail '{name}' is a plain voltage, not a rail name from rails.json "
                                   f"(assumed ±{LITERAL_TOL:.0%})"))
        if key not in specs:
            out.append(("skip", f"no {key}= token in key_specs for rail {name}"))
            continue
        pr = parse_range(specs[key])
        if pr is None:
            out.append(("error", f"cannot parse {key} '{specs[key]}'"))
        elif lo < pr[0] - 1e-9 or hi > pr[1] + 1e-9:
            out.append(("error", f"rail {name} spans {lo:.2f}–{hi:.2f} V but {key} accepts {pr[0]:.2f}–{pr[1]:.2f} V"))
    return out


def load_rails(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bom")
    ap.add_argument("rails")
    a = ap.parse_args()
    try:
        rails = load_rails(a.rails)
        rows = list(csv.DictReader(open(a.bom, newline="", encoding="utf-8")))
    except (OSError, ValueError) as e:
        print(f"check_rails: {e}", file=sys.stderr)
        return 2
    ok = bad = skipped = 0
    for row in rows:
        ref = row.get("ref", "?")
        res = check_row(row, rails)
        for level, msg in res:
            tag = {"error": "FAIL", "warning": "WARN", "skip": "SKIP"}[level]
            print(f"{tag}: {ref} ({row.get('mpn', '')}): {msg}")
        bad += sum(1 for lv, _ in res if lv == "error")
        skipped += sum(1 for lv, _ in res if lv == "skip")
        n_rails = len(rail_names(row.get("supply_rail_v", "")))
        ok += max(0, n_rails - sum(1 for lv, _ in res if lv in ("error", "skip")))
    print(f"SUMMARY {ok} supply checks passed, {bad} failed, {skipped} not checkable")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
