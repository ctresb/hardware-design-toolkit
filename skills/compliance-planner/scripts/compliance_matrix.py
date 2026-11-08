#!/usr/bin/env python3
"""Build a certification matrix from product traits. PLANNING AID, NOT LEGAL ADVICE.

Reads a traits JSON (see templates/traits.example.json) and the rules in references/rules.json, then writes,
per target market, the certifications and obligations that likely apply, with cost and lead-time ranges,
evidence level and design levers.

Project-local rules: if hw/compliance/rules.local.json exists next to the traits file (or --local-rules
names a file), its rules are merged over the toolkit rules by `id`: a rule with a known id replaces it,
a rule with `"disabled": true` removes it, and a new id is added. Use it for project-specific findings;
propose generic ones upstream.

Examples:
  python3 compliance_matrix.py --traits hw/compliance/traits.json --out hw/compliance/matrix.md
  python3 compliance_matrix.py --traits traits.json --format json
  python3 compliance_matrix.py --traits traits.json --show-skipped
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RULES = os.path.join(HERE, "..", "references", "rules.json")
MARKET_NAMES = {
    "US": "United States", "CA": "Canada", "EU": "European Union", "UK": "United Kingdom", "BR": "Brazil",
    "JP": "Japan", "KR": "South Korea", "CN": "China", "AU": "Australia / New Zealand", "IN": "India",
}
# traits the rules derive when the user leaves them out
DERIVED = {
    "has_digital_electronics": True,
    "has_firmware": True,
    "consumer_product": True,
}


def get(traits, path):
    cur = traits
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def check(traits, cond):
    v = get(traits, cond["trait"])
    op, ref = cond["op"], cond.get("value")
    if op == "truthy":
        return bool(v)
    if op == "falsy":
        return not v
    if op == "eq":
        return (v if v is not None else ([] if isinstance(ref, list) else None)) == ref
    if op == "ne":
        return v is not None and v != ref
    if op == "in":
        if isinstance(v, list):                       # a list-valued trait matches if any value is listed
            return bool(set(v) & set(ref))
        return v in ref
    if op == "intersects":
        return bool(set(v or []) & set(ref))
    if op == "contains":
        return ref in (v or [])
    if op == "gte":
        return v is not None and v >= ref
    if op == "lte":
        return v is not None and v <= ref
    raise ValueError(f"unknown op {op!r} in rule condition {cond}")


def applies(traits, rule):
    block = rule.get("if", {})
    if "all" in block and not all(check(traits, c) for c in block["all"]):
        return False
    if "any" in block and not any(check(traits, c) for c in block["any"]):
        return False
    if "none" in block and any(check(traits, c) for c in block["none"]):
        return False
    return True


def rng(a, unit=""):
    if not a or (a[0] == 0 and a[1] == 0):
        return "—"
    lo, hi = a
    f = (lambda x: f"{x:,.0f}") if unit == "$" else (lambda x: f"{x:g}")
    return f"{unit}{f(lo)}–{f(hi)}" if lo != hi else f"{unit}{f(lo)}"


def build(traits, rules):
    t = dict(DERIVED)
    t.update(traits)
    markets = t.get("markets", [])
    out = {"markets": {}, "global": [], "skipped": []}
    for r in rules["rules"]:
        ms = r["markets"]
        hit = applies(t, r)
        if "*" in ms:
            (out["global"] if hit else out["skipped"]).append(r)
            continue
        targets = [m for m in ms if m in markets]
        if not targets:
            continue
        if not hit:
            out["skipped"].append(r)
            continue
        for m in targets:
            out["markets"].setdefault(m, []).append(r)
    return t, out


def merge_local(rules, local):
    """Merge a project-local rules file over the toolkit rules, by id. Returns (rules, change log)."""
    out = dict(rules)
    by_id = {r["id"]: r for r in rules["rules"]}
    order = [r["id"] for r in rules["rules"]]
    log = []
    for r in local.get("rules", []):
        rid = r["id"]
        if r.get("disabled"):
            if rid in by_id:
                del by_id[rid]
                order.remove(rid)
                log.append(f"disabled {rid}")
            continue
        if rid in by_id and by_id[rid] == r:
            continue                                   # identical copy of the toolkit rule: nothing to report
        log.append(("replaced " if rid in by_id else "added ") + rid)
        if rid not in by_id:
            order.append(rid)
        by_id[rid] = r
    out["rules"] = [by_id[i] for i in order]
    return out, log


def unique_rows(res):
    """Every applicable rule once, with the target markets it serves."""
    seen = {}
    for r in res["global"]:
        seen.setdefault(r["id"], (r, ["*"]))
    for m, rows in res["markets"].items():
        for r in rows:
            seen.setdefault(r["id"], (r, []))[1].append(m)
    return list(seen.values())


def totals(rows):
    lo = sum(r["cost_usd"][0] for r in rows if r.get("cost_usd"))
    hi = sum(r["cost_usd"][1] for r in rows if r.get("cost_usd"))
    lead = max((r["lead_weeks"][1] for r in rows if r.get("lead_weeks")), default=0)
    return lo, hi, lead


def table(rows):
    s = ["| Requirement | Area | Cost (USD) | Lead time (weeks) | Evidence | Notes | Design levers |",
         "|---|---|---|---|---|---|---|"]
    for r in rows:
        clean = lambda x: (x or "").replace("|", "/").replace("\n", " ")
        s.append(f"| {clean(r['name'])} | {r['area']} | {rng(r.get('cost_usd'), '$')} | {rng(r.get('lead_weeks'))} | "
                 f"{r['evidence']} | {clean(r['notes'])} | {clean(r.get('levers')) or '—'} |")
    return "\n".join(s)


def markdown(traits, res, rules, show_skipped):
    L = [f"# Certification matrix — {traits.get('product', 'product')}", "",
         f"> {rules['disclaimer']} Rules file checked {rules['checked']}. "
         f"{rules['fx_note']}", ""]
    if rules.get("local_rules"):
        L += [f"> Project-local rules applied ({os.path.basename(rules['local_rules']['file'])}): "
              f"{', '.join(rules['local_rules']['changes']) or 'none'}.", ""]
    radios = ", ".join(traits.get("radios", [])) or "none"
    bat = get(traits, "battery.chemistry") or "none"
    L += [f"Traits: markets {', '.join(traits.get('markets', []))}; radios {radios}; "
          f"module pre-certified: {'yes' if traits.get('radio_module_precertified') else 'no'}; battery {bat}; "
          f"body-worn: {'yes' if traits.get('body_worn') else 'no'}.", ""]
    blocking = [r for rows in res["markets"].values() for r in rows if "BLOCKING" in r["notes"]] + \
               [r for r in res["global"] if "CRITICAL PATH" in r["notes"] or "DESIGN RISK" in r["notes"]]
    risks = [r for rows in res["markets"].values() for r in rows if "DESIGN RISK" in r["notes"]]
    flagged = {r["id"]: r for r in blocking + risks}
    if flagged:
        L += ["## Read first", ""]
        for r in flagged.values():
            tag = "BLOCKING" if "BLOCKING" in r["notes"] else ("DESIGN RISK" if "DESIGN RISK" in r["notes"] else "CRITICAL PATH")
            L.append(f"- **{tag}:** {r['name']}.")
        L.append("")
    L += ["## Summary", "", "| Scope | Rows | Cost range (USD) | Longest single lead time (weeks) |", "|---|---|---|---|"]
    glo, ghi, glead = totals(res["global"])
    L.append(f"| All markets | {len(res['global'])} | {rng((glo, ghi), '$')} | {glead} |")
    for m, rows in res["markets"].items():
        lo, hi, lead = totals(rows)
        L.append(f"| {MARKET_NAMES.get(m, m)} | {len(rows)} | {rng((lo, hi), '$')} | {lead} |")
    uniq = unique_rows(res)
    ulo, uhi, ulead = totals([r for r, _ in uniq])
    shared = [r for r, ms in uniq if len(ms) > 1]
    L.append(f"| **Total, all target markets (each row once)** | {len(uniq)} | {rng((ulo, uhi), '$')} | {ulead} |")
    L += ["", "A market's row lists everything that market requires, so a requirement shared by several markets "
          f"appears in each of them ({len(shared)} shared: {', '.join(r['id'] for r in shared) or 'none'}). "
          "The bold total counts each requirement once; do not add the market rows. Tests in one lab session can "
          "overlap, so the real total is often lower; the high end is a budget ceiling, not a quote.", ""]
    L += ["## All markets", "", table(res["global"]), ""]
    for m, rows in res["markets"].items():
        L += [f"## {MARKET_NAMES.get(m, m)} ({m})", "", table(rows), ""]
    if show_skipped and res["skipped"]:
        L += ["## Checked and not triggered", ""]
        L += [f"- {r['name']} ({', '.join(r['markets'])})" for r in res["skipped"]]
        L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--traits", required=True, help="product traits JSON")
    ap.add_argument("--rules", default=DEFAULT_RULES, help="rules JSON (default: references/rules.json)")
    ap.add_argument("--local-rules", help="project-local rules merged by id (default: rules.local.json next to "
                    "the traits file, if present)")
    ap.add_argument("--format", choices=("md", "json"), default="md")
    ap.add_argument("--out", help="output file (default: stdout)")
    ap.add_argument("--show-skipped", action="store_true", help="list rules that were checked but do not apply")
    a = ap.parse_args()
    try:
        traits = json.load(open(a.traits))
        rules = json.load(open(a.rules))
        local_path = a.local_rules or os.path.join(os.path.dirname(os.path.abspath(a.traits)), "rules.local.json")
        local = json.load(open(local_path)) if (a.local_rules or os.path.exists(local_path)) else None
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if local:
        rules, log = merge_local(rules, local)
        rules["local_rules"] = {"file": local_path, "changes": log}
        print(f"local rules {local_path}: {', '.join(log) or 'no changes'}", file=sys.stderr)
    unknown = [m for m in traits.get("markets", []) if m not in MARKET_NAMES]
    if unknown:
        print(f"warning: no rules for markets {unknown}; research them by hand", file=sys.stderr)
    t, res = build(traits, rules)
    if a.format == "json":
        text = json.dumps({"disclaimer": rules["disclaimer"], "checked": rules["checked"],
                           "global": [r["id"] for r in res["global"]],
                           "markets": {m: [r["id"] for r in rows] for m, rows in res["markets"].items()},
                           "skipped": [r["id"] for r in res["skipped"]],
                           "total_unique": dict(zip(("cost_low_usd", "cost_high_usd", "longest_lead_weeks"),
                                                    totals([r for r, _ in unique_rows(res)]))),
                           "local_rules": rules.get("local_rules")}, indent=1)
    else:
        text = markdown(t, res, rules, a.show_skipped)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        open(a.out, "w").write(text + "\n")
    else:
        print(text)
    n = len(res["global"]) + sum(len(v) for v in res["markets"].values())
    print(f"compliance_matrix: {n} rows for {len(res['markets'])} markets + global "
          f"({len(res['skipped'])} rules not triggered)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
