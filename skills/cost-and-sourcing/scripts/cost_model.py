#!/usr/bin/env python3
"""Cost per unit at each production tier, with one-time costs (NRE) kept separate.

Reads the canonical BOM (hw/bom.csv) and a manufacturing JSON (see
templates/manufacturing.example.json and references/manufacturing-json.md). Writes:

  <out>/model.json   every number, per tier, low and high, with its evidence tag
  <out>/cost.md      the tables a person reads. Only the block between
                     <!-- cost_model:begin --> and <!-- cost_model:end --> is regenerated;
                     text you write outside the markers is kept on every re-run.
  <out>/cost.svg     optional (--svg): cost per unit by tier, log scale, with the conclusion
                     in the title and the target per tier (manufacturing.json "targets")

Every value can be a number or a [low, high] range. Every line keeps its evidence tag
(verified / estimate / assumption), and the report states how much of each total
rests on verified figures.

Standard library only.

usage:
  python3 cost_model.py --bom hw/bom.csv --mfg hw/cost/manufacturing.json --out hw/cost [--svg]
"""
import argparse
import csv
import json
import math
import os
import re
import sys

BREAKS = (1, 10, 100, 1000, 10000)
PRICE_COLS = {1: "price_1", 10: "price_10", 100: "price_100", 1000: "price_1k", 10000: "price_10k"}
EVIDENCE = ("verified", "estimate", "assumption")


# ---------------------------------------------------------------- small helpers
def rng(v):
    """Number, '1.2', '1.1-1.4', [1.1, 1.4] or None -> (low, high) or None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return (float(v), float(v))
    if isinstance(v, (list, tuple)):
        if len(v) != 2:
            raise ValueError(f"range must have 2 values: {v}")
        return (float(v[0]), float(v[1]))
    s = str(v).strip().replace("$", "").replace(",", "")
    if not s or s.lower() in ("na", "n/a", "-", "?", "none"):
        return None
    m = re.fullmatch(r"([0-9.]+)\s*(?:-|–|to)\s*([0-9.]+)", s)
    if m:
        return (float(m.group(1)), float(m.group(2)))
    return (float(s), float(s))


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, k):
    if isinstance(k, tuple):
        return (a[0] * k[0], a[1] * k[1])
    return (a[0] * k, a[1] * k)


ZERO = (0.0, 0.0)


def evidence_of(tag):
    t = (tag or "").strip().lower()
    for e in EVIDENCE:
        if t.startswith(e):
            return e
    return "assumption"            # untagged numbers are treated as assumptions


def per_tier(spec, tier):
    """Value of an item at a tier. spec: a value, or {"1": v, "100": v, ...} (step: the nearest
    defined tier at or below; else the lowest defined)."""
    if not isinstance(spec, dict):
        return rng(spec)
    pts = sorted((int(k), v) for k, v in spec.items())
    below = [v for k, v in pts if k <= tier]
    v = below[-1] if below else pts[0][1]
    return rng(v)


def fmt(r, money=True):
    if r is None:
        return "—"
    lo, hi = r
    def one(x):
        if x >= 1000:
            s = f"{x / 1000:,.1f}k".replace(".0k", "k")
        elif x >= 100:
            s = f"{x:,.0f}"
        elif x >= 10:
            s = f"{x:,.1f}"
        else:
            s = f"{x:,.2f}"
        return ("$" if money else "") + s
    if abs(hi - lo) < 1e-9 * max(1, abs(hi)):
        return one(lo)
    return f"{one(lo)}–{one(hi).lstrip('$')}"


def target_at(mfg, tier):
    """Recurring (FOB) unit-cost target at exactly this tier, from manufacturing.json
    "targets": {"unit_cost": {"1000": 12, "10000": 8}}; None when the tier has no target."""
    tg = (mfg.get("targets") or {}).get("unit_cost") or {}
    v = tg.get(str(tier), tg.get(tier))
    return float(v) if v is not None else None


def verdict(rec, target):
    """met: the whole range is at or under the target; not met: the whole range is over it;
    not proven: the target sits inside the range (the estimates decide)."""
    if target is None:
        return None
    if rec[1] <= target:
        return "met"
    if rec[0] > target:
        return "not met"
    return "not proven"


# ---------------------------------------------------------------- BOM
def load_bom(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]
    need = {"ref", "qty", "mpn"}
    missing = need - set(rows[0].keys() if rows else [])
    if missing:
        raise SystemExit(f"BOM {path}: missing columns {sorted(missing)}")
    return rows


def part_price(row, nparts, moq_over):
    """Unit price for buying nparts of this line. Uses the highest price break <= nparts.
    Returns (price_range, break_used, note)."""
    mpn = (row.get("mpn") or "").strip()
    if mpn in moq_over:
        o = moq_over[mpn]
        moq = int(o.get("moq", 1))
        p = rng(o.get("price"))
        if nparts < moq:
            # below MOQ: buy paid samples (only for small lots) or pay for the whole MOQ; take the cheaper
            whole = mul(p, moq / max(nparts, 1))
            sp = rng(o.get("sample_price"))
            if sp is not None and nparts <= int(o.get("sample_max", 50)) and sum(sp) <= sum(whole):
                return sp, "sample", f"below MOQ {moq}: paid samples"
            return whole, f"MOQ {moq}", f"below MOQ {moq}: whole MOQ paid"
        return p, f"MOQ {moq}", ""
    avail = [(b, rng(row.get(PRICE_COLS[b]))) for b in BREAKS]
    avail = [(b, p) for b, p in avail if p is not None]
    if not avail:
        return None, None, "no price"
    below = [(b, p) for b, p in avail if b <= nparts]
    if below:
        b, p = below[-1]
        return p, b, ""
    b, p = avail[0]
    return p, b, f"only a {b}+ break is known"


def bom_cost(rows, units, attr, moq_over):
    """Electronics BOM cost for one order of `units` devices, per device."""
    total = ZERO
    lines = []
    for r in rows:
        qty = float(r.get("qty") or 0)
        if qty <= 0:
            continue
        ref = (r.get("ref") or "").strip()
        prefix = re.match(r"[A-Za-z]*", ref).group(0).upper()
        rule = attr.get("by_ref_prefix", {}).get(prefix, {})
        pct = float(rule.get("pct", attr.get("default_pct", 0)))
        extra = int(rule.get("min_extra", attr.get("min_extra", 0)))
        need = qty * units
        buy = need + max(math.ceil(need * pct / 100.0), extra if need else 0)
        p, brk, note = part_price(r, int(buy), moq_over)
        if p is None:
            lines.append(dict(ref=ref, mpn=r.get("mpn"), buy=buy, price=None, per_device=None,
                              evidence=evidence_of(r.get("evidence")), note="NO PRICE"))
            continue
        line_total = mul(p, buy)
        per_dev = mul(line_total, 1.0 / units)
        total = add(total, per_dev)
        lines.append(dict(ref=ref, mpn=r.get("mpn"), function=r.get("function", ""), buy=buy, break_used=brk,
                          price=p, per_device=per_dev, evidence=evidence_of(r.get("evidence")), note=note))
    return total, lines


# ---------------------------------------------------------------- PCBA tariff (e.g. a published quick-turn price list)
def tier_price(table, n):
    """table: [[upper_bound, price], ...] ascending; returns the price for count n."""
    for ub, p in table:
        if n <= ub:
            return float(p)
    return float(table[-1][1])


def pcba_fees(boards, tariff, units):
    """Per-order (batch) fee and per-board variable fee for every board, computed from the tariff.
    Returns (batch_total, variable_per_device, detail)."""
    batch = 0.0
    var = 0.0
    detail = []
    for b in boards:
        n = int(units * b.get("per_device", 1))
        sides = int(b.get("sides", 1))
        flex = bool(b.get("flex", False))
        setup = tariff["setup"][str(sides)]
        stencil = tariff["stencil"][str(sides)]
        loading = tariff["loading_per_part_type"] * b["unique_parts"]
        fx_count = tier_price(tariff["fixtures_count"], n)
        fixtures = fx_count * (tariff["fixture_flex"] if flex else tariff["fixture_rigid"])
        handling = tariff.get("handling_per_order", 0.0)
        joints_total = b["joints"] * n
        per_joint = tier_price(tariff["per_joint"], joints_total)
        xray_total = b.get("xray_parts", 0) * n
        xray_each = tier_price(tariff["xray_per_component"], xray_total) if xray_total else 0.0
        single = 0.0 if b.get("panelized", True) else tariff.get("single_board_surcharge", 0.0)
        bb = setup + stencil + loading + fixtures + handling
        vv = b["joints"] * per_joint + b.get("xray_parts", 0) * xray_each + single
        batch += bb
        var += vv * b.get("per_device", 1)
        detail.append(dict(board=b["name"], boards=n, batch_fee=round(bb, 2), variable_per_board=round(vv, 4),
                           fixtures=fx_count, per_joint=per_joint, xray_each=xray_each))
    return batch, var, detail


# ---------------------------------------------------------------- model
def applies(item, tier):
    lo = item.get("from_tier", 0)
    hi = item.get("to_tier", 10 ** 12)
    return lo <= tier <= hi


def run(bom_path, mfg):
    rows = load_bom(bom_path) if bom_path else []
    tiers = [int(t) for t in mfg.get("tiers", BREAKS)]
    attr = mfg.get("bom", {}).get("attrition", {})
    moq_over = mfg.get("bom", {}).get("moq_overrides", {})
    yield_loss = mfg.get("yield_loss_pct", {})
    landed = mfg.get("landed", {})
    out = dict(project=mfg.get("project", ""), currency=mfg.get("currency", "USD"), date=mfg.get("date", ""),
               tiers=[], warnings=[])
    for t in tiers:
        cats = {}                                   # category -> (lo, hi)
        ev = {e: ZERO for e in EVIDENCE}            # how much of the recurring cost rests on each evidence kind
        drivers = []
        # electronics
        if rows:
            b, lines = bom_cost(rows, t, attr, moq_over)
            cats["electronics (BOM)"] = b
            for ln in lines:
                if ln["per_device"] is None:
                    out["warnings"].append(f"tier {t}: {ln['ref']} {ln['mpn']} has no price")
                    continue
                ev[ln["evidence"]] = add(ev[ln["evidence"]], ln["per_device"])
                drivers.append((ln["per_device"][1], f"{ln['ref']} {ln['mpn']}", ln["per_device"], ln["evidence"]))
        # PCBA from a published tariff
        batch_fees = []
        if mfg.get("pcba"):
            pb, pv, pdet = pcba_fees(mfg["pcba"]["boards"], mfg["pcba"]["tariff"], t)
            e = evidence_of(mfg["pcba"].get("evidence"))
            cats["PCBA (variable)"] = add(cats.get("PCBA (variable)", ZERO), (pv, pv))
            ev[e] = add(ev[e], (pv, pv))
            drivers.append((pv, "PCBA variable fee", (pv, pv), e))
            batch_fees.append(dict(name="PCBA setup, stencil, loading, fixtures, handling", value=(pb, pb),
                                   evidence=e, detail=pdet))
        # other recurring lines
        for it in mfg.get("recurring", []):
            if not applies(it, t):
                continue
            v = per_tier(it["value"], t)
            if v is None:
                continue
            v = mul(v, float(it.get("qty", 1)))
            c = it.get("category", "other")
            cats[c] = add(cats.get(c, ZERO), v)
            e = evidence_of(it.get("evidence"))
            ev[e] = add(ev[e], v)
            drivers.append((v[1], it["name"], v, e))
        # per-order (batch) costs: repeat on every order, spread over that order
        for it in mfg.get("per_order", []):
            if applies(it, t):
                v = per_tier(it["value"], t)
                if v is not None:
                    batch_fees.append(dict(name=it["name"], value=v, evidence=evidence_of(it.get("evidence"))))
        batch_total = ZERO
        for bf in batch_fees:
            batch_total = add(batch_total, bf["value"])
        batch_per_unit = mul(batch_total, 1.0 / t)
        for bf in batch_fees:
            v = mul(bf["value"], 1.0 / t)
            ev[bf["evidence"]] = add(ev[bf["evidence"]], v)
            drivers.append((v[1], bf["name"] + " (per order)", v, bf["evidence"]))
        # recurring before yield
        rec = ZERO
        for v in cats.values():
            rec = add(rec, v)
        # yield loss: a scrapped unit still costs its parts and labor (not the per-order fees)
        yl = per_tier(yield_loss, t) if yield_loss else None
        if yl:
            k = (1.0 / (1 - yl[0] / 100.0), 1.0 / (1 - yl[1] / 100.0))
            loss = (rec[0] * (k[0] - 1), rec[1] * (k[1] - 1))
            rec = add(rec, loss)
            cats["yield loss"] = loss
        rec = add(rec, batch_per_unit)
        # one-time costs
        nre_items = []
        nre = ZERO
        for it in mfg.get("nre", []):
            if not applies(it, t):
                continue
            v = rng(it["value"])
            nre = add(nre, v)
            nre_items.append(dict(name=it["name"], value=v, evidence=evidence_of(it.get("evidence")),
                                  group=it.get("group", "other")))
        nre_unit = mul(nre, 1.0 / t)
        total = add(rec, nre_unit)
        # landed cost per destination: duty/tax multiplier on the recurring (imported) value
        dest = []
        for d in landed.get("destinations", []):
            m = rng(d["multiplier"])
            fr = per_tier(d.get("freight_per_unit", 0), t) or ZERO
            landed_rec = mul(add(rec, fr), m)
            v = add(landed_rec, nre_unit)
            row = dict(name=d["name"], multiplier=m, freight_per_unit=fr, per_unit=v, recurring_per_unit=landed_rec,
                       evidence=evidence_of(d.get("evidence")), note=d.get("note", ""))
            fxc = d.get("fx")
            if fxc:
                rate = rng(landed.get("fx", {}).get(fxc, {}).get("rate"))
                if rate:
                    row["local"] = dict(currency=fxc, per_unit=mul(v, rate), recurring_per_unit=mul(landed_rec, rate))
            dest.append(row)
        drivers.sort(reverse=True, key=lambda x: (x[2][0] + x[2][1]) / 2)
        rec_mid = (rec[0] + rec[1]) / 2 or 1
        top = [dict(name=n, per_unit=v, share=round(((v[0] + v[1]) / 2) / rec_mid, 3), evidence=e)
               for _, n, v, e in drivers[:6]]
        verified_share = ((ev["verified"][0] + ev["verified"][1]) / 2) / rec_mid
        target = target_at(mfg, t)
        out["tiers"].append(dict(
            target=target, target_verdict=verdict(rec, target),
            units=t, categories=cats, batch_fees=batch_fees, batch_per_unit=batch_per_unit,
            recurring=rec, nre_items=nre_items, nre=nre, nre_per_unit=nre_unit, total=total,
            landed=dest, top_drivers=top, evidence_split={k: v for k, v in ev.items()},
            verified_share=round(verified_share, 3)))
    out["warnings"] = sorted(set(out["warnings"]))
    return out


# ---------------------------------------------------------------- outputs
def write_md(m, path):
    T = m["tiers"]
    hdr = "| Item (per unit, " + m["currency"] + ") | " + " | ".join(f"{t['units']:,}" for t in T) + " |"
    sep = "|---|" + "---:|" * len(T)
    cats = []
    for t in T:
        for c in t["categories"]:
            if c not in cats:
                cats.append(c)
    L = [f"# Cost model{(' — ' + m['project']) if m['project'] else ''}", ""]
    if m["date"]:
        L += [f"Prices as of {m['date']}. Ranges are low–high. Every line keeps its evidence tag in `model.json`.", ""]
    L += ["## Cost per unit by order size", "", hdr, sep]
    for c in cats:
        L.append(f"| {c} | " + " | ".join(fmt(t["categories"].get(c)) for t in T) + " |")
    L.append("| per-order fees, spread over the order | " + " | ".join(fmt(t["batch_per_unit"]) for t in T) + " |")
    L.append("| **Recurring (FOB, before duties)** | " + " | ".join(f"**{fmt(t['recurring'])}**" for t in T) + " |")
    L.append("| One-time costs (NRE) in this plan | " + " | ".join(fmt(t["nre"]) for t in T) + " |")
    L.append("| NRE spread per unit | " + " | ".join(fmt(t["nre_per_unit"]) for t in T) + " |")
    L.append("| **Total per unit (recurring + NRE)** | " + " | ".join(f"**{fmt(t['total'])}**" for t in T) + " |")
    dests = []
    for t in T:
        for d in t["landed"]:
            if d["name"] not in dests:
                dests.append(d["name"])
    if any(t.get("target") is not None for t in T):
        L.append("| Target, recurring | " + " | ".join(
            (f"{fmt((t['target'], t['target']))} · {t['target_verdict']}" if t.get("target") is not None else "—")
            for t in T) + " |")
    for dn in dests:
        for key, label in (("recurring_per_unit", "recurring"), ("per_unit", "incl. NRE")):
            cells = []
            for t in T:
                d = next((x for x in t["landed"] if x["name"] == dn), None)
                if not d:
                    cells.append("—"); continue
                txt = fmt(d[key])
                if d.get("local"):
                    txt += f" ({d['local']['currency']} {fmt(d['local'][key], money=False)})"
                cells.append(txt)
            L.append(f"| Landed in {dn}, {label} | " + " | ".join(cells) + " |")
    L.append("| Share of recurring cost resting on verified figures | " +
             " | ".join(f"{t['verified_share'] * 100:.0f}%" for t in T) + " |")
    L += ["", "How to read it: recurring cost is what one more unit costs at that order size. NRE is paid once "
          "(tooling, fixtures, certifications) and is shown spread over the order. Landed cost applies the "
          "destination's duty and tax multiplier to the recurring cost and adds freight; the 'incl. NRE' row also "
          "adds the NRE spread per unit.", ""]
    # NRE list (union over tiers, first tier where it appears)
    L += ["## One-time costs (NRE)", "", "| Item | Group | From order size | Cost | Evidence |", "|---|---|---:|---:|---|"]
    seen = set()
    for t in T:
        for it in t["nre_items"]:
            if it["name"] in seen:
                continue
            seen.add(it["name"])
            L.append(f"| {it['name']} | {it['group']} | {t['units']:,} | {fmt(it['value'])} | {it['evidence']} |")
    L += ["", "## What drives the cost", ""]
    for t in T:
        if t["units"] not in (T[0]["units"], 1000, 10000) and t is not T[-1]:
            continue
        L.append(f"**{t['units']:,} unit{'s' if t['units'] != 1 else ''}:** " + "; ".join(
            f"{d['name']} {fmt(d['per_unit'])} ({d['share'] * 100:.0f}%, {d['evidence']})" for d in t["top_drivers"][:4]))
        L.append("")
    if m["warnings"]:
        L += ["## Warnings", ""] + [f"- {w}" for w in m["warnings"]] + [""]
    write_block(path, "\n".join(L).rstrip() + "\n")


BEGIN, END = "<!-- cost_model:begin -->", "<!-- cost_model:end -->"


def write_block(path, block):
    """Write the generated tables between markers, keeping everything a person wrote around them.
    A file without markers that this script generated before is replaced; any other existing file
    keeps its text and gets the block appended once."""
    new = f"{BEGIN}\n<!-- generated by cost_model.py; edit outside the markers -->\n{block}{END}\n"
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    if BEGIN in old and END in old:
        head, rest = old.split(BEGIN, 1)
        tail = rest.split(END, 1)[1].lstrip("\n")
        text = head + new + (("\n" + tail) if tail else "")
    elif not old.strip() or "How to read it: recurring cost is what one more unit costs" in old:
        text = new
    else:
        text = old.rstrip() + "\n\n" + new
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _tw(text, size):
    """Approximate rendered width of a label (Inter/Helvetica digits and $ are ~0.6 em)."""
    return len(text) * size * 0.6


def money(x):
    """Target-style money: no decimals for whole numbers ($12, not $12.0)."""
    return f"${x:,.0f}" if abs(x - round(x)) < 1e-9 else fmt((x, x))


def _join(units):
    u = [f"{n:,}" for n in units]
    return u[0] if len(u) == 1 else ", ".join(u[:-1]) + " and " + u[-1]


def conclusion(m):
    """One sentence that states what the chart shows, for the chart title."""
    T = m["tiers"]
    tg = [t for t in T if t.get("target") is not None]
    if tg:
        groups = {}
        for t in tg:
            groups.setdefault(t["target_verdict"], []).append(t["units"])
        phrase = {"met": "met", "not met": "missed", "not proven": "not proven yet"}
        if len(groups) == 1:
            v, units = next(iter(groups.items()))
            tail = ": the estimates decide" if v == "not proven" else ""
            return f"Unit-cost target {phrase[v]} at {_join(units)} units{tail}"
        return "Unit-cost target " + ", ".join(f"{phrase[v]} at {_join(u)} units" for v, u in groups.items())
    last = T[-1]
    return (f"One more unit costs {fmt(T[0]['recurring'])} at {T[0]['units']:,} and "
            f"{fmt(last['recurring'])} at {last['units']:,} units")


def write_svg(m, path):
    """Horizontal range bars on a log axis: recurring range and total range per order size, value labels on
    every bar, the target per tier in a column outside the plot. Text never crosses a mark: labels carry a
    halo in the page colour and move left of the bar when they would leave the plot.
    Light and dark surfaces via prefers-color-scheme; per-mark <title> tooltips."""
    T = m["tiers"]
    has_target = any(t.get("target") is not None for t in T)
    W, rowh, top, left = 900, 48, 96, 104
    tcol = 150 if has_target else 0                      # target column, outside the plot area
    plot_r = W - 32 - tcol
    H = top + rowh * len(T) + 70
    vals = [v for t in T for v in (t["recurring"][0], t["total"][1]) if v > 0]
    vals += [t["target"] for t in T if t.get("target")]
    lo = 10 ** math.floor(math.log10(min(vals)))
    hi = 10 ** math.ceil(math.log10(max(vals)))

    def X(v):
        return left + (math.log10(max(v, lo)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * (plot_r - left)
    C_REC, C_TOT, C_TGT = "#3a72c0", "#d9542b", "#1d1f23"
    title = conclusion(m)
    tsize = 16
    while _tw(title, tsize) > W - left - 24 and tsize > 12:
        tsize -= 1
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'font-family="Inter, Helvetica Neue, Arial, sans-serif" role="img" '
         f'aria-label="Cost per unit by order size. {title}">',
         '<style>.bg{fill:#fcfcfb}.t1{fill:#1d1f23}.t2{fill:#5b6170}.grid{stroke:#e6e6e3}.tg{stroke:#1d1f23}'
         '.halo{paint-order:stroke;stroke:#fcfcfb;stroke-width:4px;stroke-linejoin:round}'
         '@media (prefers-color-scheme: dark){.bg{fill:#1a1a19}.t1{fill:#ededeb}.t2{fill:#a2a6ae}'
         '.grid{stroke:#2e2e2c}.tg{stroke:#ededeb}.halo{stroke:#1a1a19}}'
         '</style>',
         f'<rect class="bg" width="{W}" height="{H}"/>',
         f'<text class="t1" x="{left}" y="30" font-size="{tsize}" font-weight="600">{title}</text>',
         f'<text class="t2" x="{left}" y="52" font-size="12">Cost per unit by order size, {m["currency"]}, '
         f'log scale. Each bar is the low–high range{"; the black mark is the recurring (FOB) target" if has_target else ""}.</text>']
    if has_target:
        o.append(f'<text class="t2" x="{plot_r + 24}" y="{top - 14}" font-size="11" font-weight="600">TARGET</text>')
    # grid, ticks below the plot
    k = lo
    while k <= hi * 1.0001:
        x = X(k)
        o.append(f'<line class="grid" x1="{x:.1f}" y1="{top - 8}" x2="{x:.1f}" y2="{top + rowh * len(T)}" stroke-width="1"/>')
        lab = f"${k / 1000:g}k" if k >= 1000 else f"${k:g}"
        o.append(f'<text class="t2" x="{x:.1f}" y="{top + rowh * len(T) + 18}" font-size="11" text-anchor="middle">{lab}</text>')
        k *= 10
    fs = 11
    for i, t in enumerate(T):
        y = top + i * rowh
        o.append(f'<text class="t1" x="{left - 14}" y="{y + 24}" font-size="12" text-anchor="end">'
                 f'{t["units"]:,} unit{"s" if t["units"] != 1 else ""}</text>')
        tgt = t.get("target")
        if tgt is not None:
            o.append(f'<text class="t1" x="{plot_r + 24}" y="{y + 18}" font-size="12" font-weight="600">'
                     f'{money(tgt)}</text>')
            o.append(f'<text class="t2" x="{plot_r + 24}" y="{y + 34}" font-size="11">{t["target_verdict"]}</text>')
        for j, (key, col, name) in enumerate((("recurring", C_REC, "Recurring"), ("total", C_TOT, "Total incl. NRE"))):
            a, b = t[key]
            x0, x1 = X(a), X(b)
            if x1 - x0 < 6:
                x0, x1 = (x0 + x1) / 2 - 3, (x0 + x1) / 2 + 3
            yy = y + 6 + j * 18
            o.append(f'<rect x="{x0:.1f}" y="{yy}" width="{x1 - x0:.1f}" height="12" rx="4" fill="{col}">'
                     f'<title>{t["units"]:,} units · {name}: {fmt(t[key])}</title></rect>')
            if j == 0 and tgt is not None:                 # target marker on the recurring bar only
                xt = X(tgt)
                o.append(f'<line class="tg halo" x1="{xt:.1f}" y1="{yy - 4}" x2="{xt:.1f}" y2="{yy + 16}" '
                         f'stroke-width="2" stroke-linecap="round"><title>Target {money(tgt)}</title></line>')
                o.append(f'<line class="tg" x1="{xt:.1f}" y1="{yy - 4}" x2="{xt:.1f}" y2="{yy + 16}" '
                         f'stroke-width="2" stroke-linecap="round"/>')
            lab = fmt(t[key])
            w = _tw(lab, fs)
            if j == 0 and tgt is not None and x1 - 1 <= X(tgt) <= x1 + 8 + w:
                x1 = max(x1, X(tgt) + 2)                   # start the label after the target marker
            if x1 + 8 + w <= plot_r:                       # right of the bar
                o.append(f'<text class="t2 halo" x="{x1 + 8:.1f}" y="{yy + 10}" font-size="{fs}">{lab}</text>')
            elif x0 - 8 - w >= left:                       # left of the bar
                o.append(f'<text class="t2 halo" x="{x0 - 8:.1f}" y="{yy + 10}" font-size="{fs}" '
                         f'text-anchor="end">{lab}</text>')
            else:                                          # inside the bar
                o.append(f'<text x="{x0 + 6:.1f}" y="{yy + 10}" font-size="{fs}" fill="#ffffff">{lab}</text>')
    ly = H - 22
    o.append(f'<rect x="{left}" y="{ly - 10}" width="12" height="12" rx="3" fill="{C_REC}"/>'
             f'<text class="t1" x="{left + 18}" y="{ly}" font-size="12">Recurring (one more unit)</text>')
    x2 = left + 18 + _tw("Recurring (one more unit)", 12) + 28
    o.append(f'<rect x="{x2:.0f}" y="{ly - 10}" width="12" height="12" rx="3" fill="{C_TOT}"/>'
             f'<text class="t1" x="{x2 + 18:.0f}" y="{ly}" font-size="12">Total, with one-time costs spread over the order</text>')
    if has_target:
        x3 = x2 + 18 + _tw("Total, with one-time costs spread over the order", 12) + 28
        o.append(f'<line class="tg" x1="{x3:.0f}" y1="{ly - 12}" x2="{x3:.0f}" y2="{ly + 2}" stroke-width="2" '
                 f'stroke-linecap="round"/><text class="t1" x="{x3 + 10:.0f}" y="{ly}" font-size="12">'
                 f'Target (recurring)</text>')
    o.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(o) + "\n")


def jsonable(x):
    if isinstance(x, tuple):
        return [round(x[0], 4), round(x[1], 4)]
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items()}
    if isinstance(x, list):
        return [jsonable(v) for v in x]
    return x


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bom", help="canonical BOM CSV (hw/bom.csv)")
    ap.add_argument("--mfg", required=True, help="manufacturing JSON (see templates/manufacturing.example.json)")
    ap.add_argument("--out", required=True, help="output folder (hw/cost)")
    ap.add_argument("--svg", action="store_true", help="also write cost.svg")
    a = ap.parse_args()
    with open(a.mfg, encoding="utf-8") as f:
        mfg = json.load(f)
    bom = a.bom or mfg.get("bom", {}).get("path")
    if bom and not os.path.isabs(bom) and not os.path.exists(bom):
        cand = os.path.join(os.path.dirname(os.path.abspath(a.mfg)), bom)
        bom = cand if os.path.exists(cand) else bom
    try:
        m = run(bom, mfg)
    except (KeyError, ValueError) as ex:
        print(f"cost_model: error in input: {ex!r}", file=sys.stderr)
        return 2
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "model.json"), "w", encoding="utf-8") as f:
        json.dump(jsonable(m), f, indent=1, ensure_ascii=False)
    write_md(m, os.path.join(a.out, "cost.md"))
    if a.svg:
        write_svg(m, os.path.join(a.out, "cost.svg"))
    t1k = next((t for t in m["tiers"] if t["units"] == 1000), m["tiers"][-1])
    print(f"cost_model: {len(m['tiers'])} tiers; at {t1k['units']:,} units recurring {fmt(t1k['recurring'])}, "
          f"total {fmt(t1k['total'])}; {len(m['warnings'])} warnings -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
