#!/usr/bin/env python3
"""Lint a hardware BOM (hw/bom.csv) against the toolkit conventions.

Checks
  errors   : missing columns, empty MPN, placeholder MPN, missing/invalid max size, invalid qty,
             evidence not tagged, price breaks that rise with quantity, part supply range that does not
             contain its rail, duplicate I2C address on one bus, single-part peak above the rail limit
  warnings : no packaging suffix detected, no alternatives, risky lifecycle, verified row without
             source_date, sum of peaks above the rail limit, rail not defined, IC without vdd range

key_specs holds `key=value` tokens separated by `;`, for example `vdd=1.7-3.6; i2c=0x2C; bus=I2C0`.
supply_rail_v holds a rail NAME defined in the rails JSON (`VSYS`, or `VSYS|1V8` for a part on two rails, matched
to vdd, vdd2). A plain voltage such as `1.8` is accepted with a warning. Rail logic is imported from
battery-and-power/scripts/check_rails.py, the single implementation.

Rails JSON:
  {"VSYS": {"min": 3.0, "max": 4.4, "max_ma": 125},
   "1V8":  {"nom": 1.8, "tol": 0.05, "max_ma": 100}}
  `tol` is in volts (1.8 ± 0.05 V). `max_ma` is optional.

Usage
  python3 bom_check.py hw/bom.csv --rails hw/power/rails.json [--json report.json] [--strict]

Exit code: 0 = no errors (warnings allowed unless --strict), 1 = errors, 2 = cannot read input.
"""
import argparse
import csv
import json
import os
import re
import sys

REQUIRED = ["ref", "qty", "function", "manufacturer", "mpn", "lcsc", "package", "size_max_mm", "lifecycle",
            "key_specs", "supply_rail_v", "typ_current_ma", "peak_current_ma", "distributors",
            "price_1", "price_10", "price_100", "price_1k", "price_10k", "lead_time_wk",
            "stock_snapshot", "alternatives", "evidence", "source_date", "notes"]
PRICE_COLS = ["price_1", "price_10", "price_100", "price_1k", "price_10k"]
EVIDENCE = {"verified", "estimate", "assumption"}
RISKY_LIFECYCLE = ["early sampling", "sampling", "preview", "engineering sample", "nrnd",
                   "not recommended", "not for new", "last time", "ltb", "eol", "end of life",
                   "obsolete", "discontinued", "special order"]
PLACEHOLDER = re.compile(r"(\?|\*|\bTBD\b|\bTBC\b|xxx|\.\.\.|…)", re.I)
# common packaging/reel endings: -R, -R7, TR, /TR, -T, R18, (51), #PBF, -ND is a distributor code (bad)
PACK_SUFFIX = re.compile(r"(-?T&?R\b|/TR\b|-R\d*\b|R\d{1,3}$|TR$|-T\d*$|\(\d+\)$|#PBF$|-RL\d*$|"
                         r"-REEL\d*$|-TP$|-Z$|E$|IR$|T$|R$)", re.I)
IC_FUNCS = re.compile(r"\b(soc|mcu|pmic|charger|driver|ic|sensor|accel|imu|mic|memory|nand|nor|flash|"
                      r"controller|codec|regulator|ldo|buck|gauge|rtc)\b", re.I)
SIZE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*$")


# Rail logic lives in one place: battery-and-power/scripts/check_rails.py (owner of hw/power/rails.json).
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "battery-and-power", "scripts"))
try:
    from check_rails import (  # noqa: E402
        parse_range, parse_specs, rail_names, rail_span, check_row,
        check_bus_vio_compatibility, check_ldo_dropout,
    )
except ImportError:  # pragma: no cover
    sys.exit("bom_check: needs battery-and-power/scripts/check_rails.py next to this skill "
             "(install the whole Hardware Design Toolkit)")


def num(s):
    s = (s or "").strip().replace("$", "").replace(",", "")
    if not s or s in {"-", "—", "n/a", "na"}:
        return None
    try:
        return float(s)
    except ValueError:
        return "bad"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bom", help="path to bom.csv")
    ap.add_argument("--rails", help="rails JSON (see above)")
    ap.add_argument("--json", help="write the findings as JSON to this path")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    a = ap.parse_args()

    try:
        with open(a.bom, newline="", encoding="utf-8-sig") as f:
            rd = csv.DictReader(f)
            cols = [c.strip() for c in (rd.fieldnames or [])]
            rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in rd]
    except OSError as e:
        print(f"bom_check: cannot read {a.bom}: {e}", file=sys.stderr)
        return 2
    rails = {}
    if a.rails:
        try:
            rails = json.load(open(a.rails, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"bom_check: cannot read rails {a.rails}: {e}", file=sys.stderr)
            return 2

    errs, warns = [], []

    def E(ref, msg): errs.append({"ref": ref, "msg": msg})
    def W(ref, msg): warns.append({"ref": ref, "msg": msg})

    missing = [c for c in REQUIRED if c not in cols]
    if missing:
        E("-", "missing columns: " + ", ".join(missing))
    extra = [c for c in cols if c not in REQUIRED]
    if extra:
        W("-", "unknown columns (ignored): " + ", ".join(extra))

    i2c = {}            # (bus, addr) -> [refs]
    rail_peaks = {}     # rail -> [(ref, peak)]
    seen_refs = set()
    for i, r in enumerate(rows, start=2):
        ref = r.get("ref") or f"row{i}"
        if ref in seen_refs:
            E(ref, "duplicate ref")
        seen_refs.add(ref)
        func = r.get("function", "")
        mpn = r.get("mpn", "")
        q = num(r.get("qty"))
        if q in (None, "bad") or q <= 0 or q != int(q):
            E(ref, f"qty must be a positive integer (got '{r.get('qty', '')}')")
        if not mpn:
            E(ref, "empty mpn")
        elif PLACEHOLDER.search(mpn):
            E(ref, f"placeholder in mpn '{mpn}'")
        elif mpn.upper().endswith("-ND"):
            E(ref, f"'{mpn}' looks like a distributor part number, not the manufacturer's")
        elif not PACK_SUFFIX.search(mpn.replace(" ", "")) and "suffix ok" not in r.get("notes", "").lower():
            W(ref, f"no packaging suffix detected in '{mpn}' (add it, or write 'suffix ok' in notes)")
        sz = r.get("size_max_mm", "")
        m = SIZE.match(sz)
        if not m:
            E(ref, f"size_max_mm must be LxWxH in mm from the datasheet maximums (got '{sz}')")
        ev = r.get("evidence", "").lower()
        if ev not in EVIDENCE:
            E(ref, f"evidence must be one of {sorted(EVIDENCE)} (got '{r.get('evidence', '')}')")
        if ev == "verified" and not r.get("source_date"):
            W(ref, "verified row without source_date")
        lc = r.get("lifecycle", "").lower()
        if not lc:
            W(ref, "lifecycle empty")
        elif any(k in lc for k in RISKY_LIFECYCLE):
            W(ref, f"risky lifecycle '{r.get('lifecycle')}': needs a logged decision and a fallback part")
        if not r.get("alternatives"):
            W(ref, "no alternatives listed")
        # prices must not rise with quantity
        prev = None
        for c in PRICE_COLS:
            p = num(r.get(c))
            if p == "bad":
                E(ref, f"{c} is not a number ('{r.get(c)}')")
                continue
            if p is None:
                continue
            if prev is not None and p > prev[1] + 1e-9:
                E(ref, f"{c} ({p}) is higher than {prev[0]} ({prev[1]})")
            prev = (c, p)
        specs = parse_specs(r.get("key_specs"))
        rail_field = r.get("supply_rail_v", "")
        peak = num(r.get("peak_current_ma"))
        names = rail_names(rail_field)
        for level, msg in check_row(r, rails):
            if level == "error":
                E(ref, msg)
            elif level == "warning":
                W(ref, msg)
            elif level == "skip" and IC_FUNCS.search(func):
                W(ref, f"IC on a rail without a supply range: {msg}")
        if names and isinstance(peak, float):
            qn = q if isinstance(q, float) else 1
            for k_idx, rname in enumerate(names):
                pk_key = "peak_ma_vdd" if k_idx == 0 else f"peak_ma_vdd{k_idx + 1}"
                r_peak = num(specs.get(pk_key)) if pk_key in specs else (peak if k_idx == 0 else None)
                if not isinstance(r_peak, float):
                    continue
                span = rail_span(rname, rails)
                rail_peaks.setdefault(rname, []).append((ref, r_peak * qn))
                if span and span[2] is not None and r_peak > float(span[2]):
                    E(ref, f"peak {r_peak} mA exceeds rail {rname} limit {span[2]} mA")
        if "i2c" in specs:
            bus = specs.get("bus", "I2C")
            for addr in re.split(r"[,/ ]+", specs["i2c"]):
                if addr:
                    try:
                        key = (bus, int(addr, 16) if addr.lower().startswith("0x") else int(addr))
                    except ValueError:
                        E(ref, f"cannot parse i2c address '{addr}'")
                        continue
                    i2c.setdefault(key, []).append(ref)

    for (bus, addr), refs in sorted(i2c.items()):
        if len(refs) > 1:
            E(",".join(refs), f"I2C address 0x{addr:02X} used twice on {bus}")
    for refs_str, msg in check_bus_vio_compatibility(rows, rails):
        E(refs_str, msg)
    for rname, msg in check_ldo_dropout(rails):
        E(rname, msg)
    for rail, lst in rail_peaks.items():
        span = rail_span(rail, rails)
        if span and span[2] is not None:
            tot = sum(p for _, p in lst)
            if tot > float(span[2]):
                W(rail, f"sum of peaks on {rail} is {tot:.0f} mA, above its {span[2]} mA limit "
                        f"(fine only if these peaks never coincide; show it in architecture.md)")

    for e in errs:
        print(f"ERROR   {e['ref']}: {e['msg']}")
    for w in warns:
        print(f"WARNING {w['ref']}: {w['msg']}")
    if a.json:
        json.dump({"errors": errs, "warnings": warns, "rows": len(rows)}, open(a.json, "w"), indent=1)
    fail = bool(errs) or (a.strict and bool(warns))
    print(f"bom_check: {len(rows)} rows, {len(errs)} errors, {len(warns)} warnings -> {'FAIL' if fail else 'OK'}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
