#!/usr/bin/env python3
"""Merge part dossiers (hw/parts/*.md front matter) into the canonical BOM (hw/bom.csv).

Each dossier starts with a block of `key: value` lines between `---` lines (see the
electronics-researcher SKILL.md for the key list). The script fills the researcher-owned
BOM columns and matches BOM rows to dossiers by MPN, alias, or a truncated MPN prefix.
It refuses to overwrite a different value silently (notes are merged, never replaced, even with
--overwrite), and it checks the evidence, the dates,
the lifecycle, the price breaks and the rail voltage against the supply range.

`supply_rail_v` is a rail NAME from hw/power/rails.json (CONVENTIONS.md §5). The name is resolved through
rails.json with battery-and-power/scripts/check_rails.py, the toolkit's single rail implementation. A plain
voltage (`1.8`, `3.0-3.6`) is accepted as a fallback. For a part on several rails (`VSYS|1V8`), the first
rail is checked against the dossier's `supply_range_v`. rails.json defaults to <bom folder>/power/rails.json.

Exit code: 0 = clean (warnings allowed), 1 = errors or conflicts, 2 = bad input.
Standard library only.
"""
import argparse
import csv
import datetime as dt
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "battery-and-power", "scripts"))
try:
    from check_rails import rail_names, rail_span  # noqa: E402
except ImportError:  # pragma: no cover
    sys.exit("bom_merge: needs battery-and-power/scripts/check_rails.py (install the whole Hardware Design Toolkit)")

BOM_COLUMNS = [
    "ref", "qty", "function", "manufacturer", "mpn", "lcsc", "package", "size_max_mm", "lifecycle",
    "key_specs", "supply_rail_v", "typ_current_ma", "peak_current_ma", "distributors",
    "price_1", "price_10", "price_100", "price_1k", "price_10k", "lead_time_wk",
    "stock_snapshot", "alternatives", "evidence", "source_date", "notes",
]
DOSSIER_KEYS = [
    "mpn", "aliases", "manufacturer", "lcsc", "function", "package", "size_max_mm", "supply_range_v",
    "io_range_v", "typ_current_ma", "peak_current_ma", "lifecycle", "lifecycle_distributor",
    "key_specs", "distributors", "price_1", "price_10", "price_100", "price_1k", "price_10k",
    "lead_time_wk", "stock_snapshot", "alternatives", "evidence", "source_date", "notes",
]
OPTIONAL_KEYS = {"aliases", "lcsc", "io_range_v", "lifecycle_distributor", "notes", "price_10k"}
# BOM columns filled from the dossier (same name). `function` only fills an empty cell.
RESEARCHER_COLUMNS = [
    "manufacturer", "lcsc", "package", "size_max_mm", "lifecycle", "key_specs", "typ_current_ma",
    "peak_current_ma", "distributors", "price_1", "price_10", "price_100", "price_1k",
    "price_10k", "lead_time_wk", "stock_snapshot", "alternatives", "evidence", "source_date",
    "notes",
]
GATE_COLUMNS = ["mpn", "size_max_mm", "lifecycle", "price_1", "price_1k", "evidence", "source_date"]
NUMERIC = {"typ_current_ma", "peak_current_ma", "price_1", "price_10", "price_100", "price_1k",
           "price_10k", "lead_time_wk"}
PRICE_KEYS = ["price_1", "price_10", "price_100", "price_1k", "price_10k"]
LIFECYCLES = {"production", "preview", "sampling", "nrnd", "eol", "obsolete"}
RISKY_LIFECYCLES = {"preview", "sampling", "nrnd", "eol", "obsolete"}
EVIDENCE = {"verified", "estimate", "assumption"}
SIZE_RE = re.compile(r"^\d+(\.\d+)?x\d+(\.\d+)?x\d+(\.\d+)?$")
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def norm_mpn(s):
    return re.sub(r"\s+", "", s or "").upper()


def unknown(v):
    return v is None or v.strip() in ("", "-")


def to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_range(v):
    """'1.7-1.95' -> (1.7, 1.95); '3.3' -> (3.3, 3.3); text around numbers is ignored."""
    nums = [float(x) for x in NUM_RE.findall(v.replace("–", "-").replace(" - ", " ").replace("-", " "))]
    if not nums:
        return None
    return (min(nums), max(nums))


def same(a, b):
    fa, fb = to_float(a), to_float(b)
    if fa is not None and fb is not None:
        return abs(fa - fb) <= 1e-9 + 1e-6 * max(abs(fa), abs(fb))
    return " ".join(a.split()) == " ".join(b.split())


def read_dossier(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "no front matter (file must start with '---')"
    data = {}
    for i, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return data, None
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            return None, f"line {i}: expected 'key: value'"
        k, v = line.split(":", 1)
        data[k.strip()] = v.strip()
    return None, "front matter not closed with '---'"


class Report:
    def __init__(self):
        self.errors, self.warnings, self.changes = [], [], []

    def err(self, where, msg):
        self.errors.append(f"**{where}**: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"**{where}**: {msg}")

    def change(self, where, msg):
        self.changes.append(f"**{where}**: {msg}")

    def markdown(self, summary):
        out = ["# BOM merge report", "", summary, ""]
        for title, items in (("Errors and conflicts", self.errors), ("Warnings", self.warnings),
                             ("Changes written", self.changes)):
            out += [f"## {title} ({len(items)})", ""]
            out += [f"- {x}" for x in items] or ["- none"]
            out.append("")
        return "\n".join(out)


def check_dossier(name, d, rep, today, max_age):
    for k in DOSSIER_KEYS:
        if k not in d and k not in OPTIONAL_KEYS:
            rep.err(name, f"missing key `{k}` (use `-` for unknown)")
    for k in d:
        if k not in DOSSIER_KEYS:
            rep.warn(name, f"unknown key `{k}` ignored")
    ev = d.get("evidence", "-")
    if ev not in EVIDENCE:
        rep.err(name, f"evidence `{ev}` must be one of {sorted(EVIDENCE)}")
    lc = d.get("lifecycle", "-")
    if lc not in LIFECYCLES:
        rep.err(name, f"lifecycle `{lc}` must be one of {sorted(LIFECYCLES)} (the maker's status)")
    elif lc in RISKY_LIFECYCLES:
        rep.warn(name, f"lifecycle is `{lc}`: needs a plan B or the maker's written production date")
    lcd = d.get("lifecycle_distributor", "-")
    if not unknown(lcd) and lc in LIFECYCLES:
        dl = lcd.lower()
        active = dl.startswith("active") or "new product" in dl
        if (active and lc in RISKY_LIFECYCLES) or (not active and dl != lc):
            rep.warn(name, f"distributor says `{lcd}`, maker says `{lc}`: the maker's status wins")
    sd = d.get("source_date", "-")
    try:
        age = (today - dt.date.fromisoformat(sd)).days
        if age > max_age:
            rep.warn(name, f"source_date {sd} is {age} days old (limit {max_age}): re-check price and stock")
        if age < 0:
            rep.err(name, f"source_date {sd} is in the future")
    except ValueError:
        rep.err(name, f"source_date `{sd}` is not an ISO date (YYYY-MM-DD)")
    sz = d.get("size_max_mm", "-")
    if not unknown(sz) and not SIZE_RE.match(sz.replace(" ", "").lower()):
        rep.err(name, f"size_max_mm `{sz}` must be LxWxH in mm, e.g. 5.1x5.1x0.95")
    for k in NUMERIC:
        v = d.get(k, "-")
        if not unknown(v) and (to_float(v) is None or to_float(v) < 0):
            rep.err(name, f"`{k}` = `{v}` must be a non-negative number or `-`")
    prices = [(k, to_float(d.get(k))) for k in PRICE_KEYS if to_float(d.get(k)) is not None]
    for (k1, p1), (k2, p2) in zip(prices, prices[1:]):
        if p2 > p1 * 1.001:
            rep.warn(name, f"{k2} ({p2}) is above {k1} ({p1}): price breaks should not rise with quantity")
    t, p = to_float(d.get("typ_current_ma")), to_float(d.get("peak_current_ma"))
    if t is not None and p is not None and p < t:
        rep.err(name, f"peak_current_ma {p} is below typ_current_ma {t}")
    sr = d.get("supply_range_v", "-")
    if not unknown(sr) and parse_range(sr) is None:
        rep.err(name, f"supply_range_v `{sr}` must be `min-max` in volts")


def merge_notes(cur, new):
    """Keep the BOM note and append each dossier note segment ("; "-separated) that is not already there."""
    def segs(t):
        return [x.strip() for x in re.split(r"\s*;\s*", t or "") if x.strip()]
    out = segs(cur)
    seen = {re.sub(r"\s+", " ", x).lower() for x in out}
    for x in segs(new):
        k = re.sub(r"\s+", " ", x).lower()
        if k not in seen:
            out.append(x)
            seen.add(k)
    return "; ".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bom", required=True, help="path to hw/bom.csv")
    ap.add_argument("--parts", required=True, help="folder with <MPN>.md dossiers")
    ap.add_argument("--report", help="write a Markdown report here")
    ap.add_argument("--rails", help="rails JSON (default: <bom folder>/power/rails.json)")
    ap.add_argument("--create", action="store_true", help="create the BOM if it does not exist")
    ap.add_argument("--append-missing", action="store_true",
                    help="add a BOM row for each dossier that matches no row (ref/qty left empty)")
    ap.add_argument("--overwrite", action="store_true",
                    help="dossier values replace different BOM values in researcher columns (logged)")
    ap.add_argument("--max-age-days", type=int, default=90, help="warn when source_date is older (default 90)")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD), for tests")
    ap.add_argument("--dry-run", action="store_true", help="do not write the BOM")
    a = ap.parse_args(argv)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    rep = Report()
    rails_path = a.rails or os.path.join(os.path.dirname(os.path.abspath(a.bom)), "power", "rails.json")
    rails = {}
    if os.path.exists(rails_path):
        try:
            import json
            rails = json.load(open(rails_path, encoding="utf-8"))
        except ValueError as e:
            print(f"bom_merge: cannot read {rails_path}: {e}", file=sys.stderr)
            return 2

    # ---- BOM
    if os.path.exists(a.bom):
        with open(a.bom, newline="", encoding="utf-8") as f:
            rd = csv.DictReader(f)
            header = rd.fieldnames or []
            rows = list(rd)
        missing_cols = [c for c in BOM_COLUMNS if c not in header]
        if missing_cols:
            rep.warn("bom.csv", f"added missing columns: {', '.join(missing_cols)}")
        extra = [c for c in header if c not in BOM_COLUMNS]
        header = BOM_COLUMNS + extra
        for r in rows:
            for c in header:
                r[c] = (r.get(c) or "").strip()
    elif a.create:
        header, rows = list(BOM_COLUMNS), []
    else:
        print(f"bom_merge: {a.bom} not found (use --create)", file=sys.stderr)
        return 2

    # ---- dossiers
    if not os.path.isdir(a.parts):
        print(f"bom_merge: {a.parts} is not a folder", file=sys.stderr)
        return 2
    dossiers = []
    for fn in sorted(os.listdir(a.parts)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        d, problem = read_dossier(os.path.join(a.parts, fn))
        if problem:
            rep.err(fn, problem)
            continue
        if unknown(d.get("mpn")):
            rep.err(fn, "no `mpn`")
            continue
        check_dossier(d["mpn"], d, rep, today, a.max_age_days)
        dossiers.append(d)

    by_key = {}
    for d in dossiers:
        keys = {norm_mpn(d["mpn"])}
        if not unknown(d.get("aliases")):
            keys |= {norm_mpn(x) for x in d["aliases"].split(";") if x.strip()}
        for k in keys:
            if k in by_key and by_key[k] is not d:
                rep.err(d["mpn"], f"MPN/alias `{k}` also claimed by {by_key[k]['mpn']}")
            by_key[k] = d

    # ---- match and fill
    used = set()
    for r in rows:
        where = f"BOM {r.get('ref') or '?'} ({r.get('mpn') or 'no MPN'})"
        m = norm_mpn(r.get("mpn"))
        d = by_key.get(m) if m else None
        if d is None and m:
            cands = {id(x): x for x in dossiers if norm_mpn(x["mpn"]).startswith(m)}
            if len(cands) == 1:
                d = next(iter(cands.values()))
                rep.warn(where, f"truncated MPN: matched dossier `{d['mpn']}`")
            elif len(cands) > 1:
                rep.err(where, "truncated MPN matches several dossiers: " +
                        ", ".join(sorted(x["mpn"] for x in cands.values())))
        if d is None:
            rep.warn(where, "no dossier yet")
            continue
        used.add(id(d))
        if r.get("mpn") != d["mpn"]:
            rep.change(where, f"mpn `{r.get('mpn')}` -> `{d['mpn']}` (full orderable number)")
            r["mpn"] = d["mpn"]
        cols = list(RESEARCHER_COLUMNS) + ["function"]
        for c in cols:
            v = d.get(c, "-")
            if unknown(v):
                continue
            cur = r.get(c, "")
            if unknown(cur):
                r[c] = v
                rep.change(where, f"{c} = `{v}`")
            elif c == "notes":
                merged = merge_notes(cur, v)           # notes are merged, never overwritten
                if merged != cur:
                    rep.change(where, f"notes += `{merged[len(cur):].lstrip('; ')}`")
                    r[c] = merged
            elif not same(cur, v):
                if c == "function":
                    continue                           # the BOM owner's wording wins
                if a.overwrite:
                    rep.change(where, f"{c}: `{cur}` -> `{v}` (overwrite)")
                    r[c] = v
                else:
                    rep.err(where, f"conflict in `{c}`: BOM has `{cur}`, dossier has `{v}` "
                                   "(fix one, or rerun with --overwrite)")
        rail = r.get("supply_rail_v", "")
        sr = d.get("supply_range_v", "-")
        if not unknown(rail) and not unknown(sr):
            names = rail_names(rail)
            span = rail_span(names[0], rails) if names else None
            if span is None:
                rr = parse_range(rail)                  # legacy text such as "VSYS 3.0-3.6"
                span = (rr[0], rr[1], None, False) if rr else None
            rng = parse_range(sr)
            if span is None:
                rep.warn(where, f"supply_rail_v `{rail}` is not in rails.json and has no voltage to check")
            elif rng and (span[0] < rng[0] - 1e-9 or span[1] > rng[1] + 1e-9):
                rep.err(where, f"rail {names[0] if names else rail} spans {span[0]:.2f}-{span[1]:.2f} V, "
                               f"outside the supply range {sr} V")
            elif not span[3] and rails:
                rep.warn(where, f"supply_rail_v `{rail}` is a voltage, not a rail name from rails.json")
        elif unknown(rail):
            rep.warn(where, "supply_rail_v empty: rail not checked against the supply range")

    for d in dossiers:
        if id(d) in used:
            continue
        if a.append_missing:
            r = {c: "" for c in header}
            r["mpn"] = d["mpn"]
            for c in RESEARCHER_COLUMNS + ["function"]:
                if not unknown(d.get(c)):
                    r[c] = d[c]
            rows.append(r)
            rep.change(d["mpn"], "appended as a new BOM row (ref and qty empty)")
        else:
            rep.warn(d["mpn"], "dossier matches no BOM row (use --append-missing to add it)")

    # ---- gate
    for r in rows:
        where = f"BOM {r.get('ref') or '?'} ({r.get('mpn') or 'no MPN'})"
        gaps = [c for c in GATE_COLUMNS if unknown(r.get(c))]
        if gaps:
            rep.err(where, "gate fields missing: " + ", ".join(gaps))

    if not a.dry_run:
        tmp = a.bom + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            for r in rows:
                w.writerow({c: r.get(c, "") for c in header})
        os.replace(tmp, a.bom)

    summary = (f"bom_merge: {len(rows)} BOM rows, {len(dossiers)} dossiers, {len(rep.errors)} errors, "
               f"{len(rep.warnings)} warnings, {len(rep.changes)} changes"
               + (" (dry run)" if a.dry_run else ""))
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(rep.markdown(summary))
    for x in rep.errors:
        print("ERROR", x.replace("**", ""))
    for x in rep.warnings:
        print("WARN ", x.replace("**", ""))
    print(summary)
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
