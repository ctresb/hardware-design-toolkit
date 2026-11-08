#!/usr/bin/env python3
"""Turn a stages JSON into a dated roadmap: Markdown table + SVG timeline.

Each stage has a duration range in weeks [best, worst] and finish-to-start dependencies (optional lag, which
may be negative for overlap). The script schedules the best case and the worst case, finds the critical path
on the worst case, and back-schedules long-lead purchases ("order by" dates).

Examples:
  python3 roadmap.py --stages hw/roadmap/stages.json --md hw/roadmap/schedule.md --svg hw/roadmap/timeline.svg
  python3 roadmap.py --stages templates/stages.example.json            # Markdown to stdout
"""
import argparse
import datetime as dt
import json
import os
import sys
from html import escape


def load(path):
    d = json.load(open(path))
    ids = [s["id"] for s in d["stages"]]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate stage ids")
    known = {"id", "name", "weeks", "depends_on", "lag_weeks", "start_week", "gate", "deliverable", "detail",
             "evidence", "notes", "owner", "critical"}
    for s in d["stages"]:
        extra = set(s) - known - {k for k in s if k.startswith("_")}
        if extra:
            hint = " (use depends_on)" if extra & {"after", "deps", "requires"} else ""
            raise ValueError(f"stage {s['id']}: unknown key(s) {sorted(extra)}{hint}")
        for p in s.get("depends_on", []):
            if p not in ids:
                raise ValueError(f"stage {s['id']} depends on unknown stage {p}")
        lo, hi = s["weeks"]
        if lo > hi or lo < 0:
            raise ValueError(f"stage {s['id']}: weeks must be [best, worst] with 0 <= best <= worst")
    return d


def topo(stages):
    by = {s["id"]: s for s in stages}
    seen, order, temp = set(), [], set()

    def visit(i):
        if i in seen:
            return
        if i in temp:
            raise ValueError(f"dependency cycle at {i}")
        temp.add(i)
        for p in by[i].get("depends_on", []):
            visit(p)
        temp.discard(i)
        seen.add(i)
        order.append(by[i])
    for s in stages:
        visit(s["id"])
    return order


def schedule(stages, k):
    """k = 0 best, 1 worst. Returns {id: (start_week, end_week, driver)}."""
    res = {}
    for s in topo(stages):
        start, driver = s.get("start_week", 0.0), None
        for p in s.get("depends_on", []):
            t = res[p][1] + s.get("lag_weeks", 0.0)
            if t >= start:
                start, driver = t, p
        res[s["id"]] = (start, start + s["weeks"][k], driver)
    return res


def critical_path(stages, sch):
    end_id = max(sch, key=lambda i: sch[i][1])
    path, cur = [], end_id
    while cur:
        path.append(cur)
        cur = sch[cur][2]
    return list(reversed(path))


def wdate(start, w):
    return start + dt.timedelta(days=round(w * 7))


def fmt(d):
    return d.strftime("%Y-%m-%d")


def mon(d):
    return d.strftime("%b %Y")


def markdown(d, best, worst, crit, start, longlead):
    L = [f"# Roadmap — {d.get('project', 'product')}", "",
         f"Start {fmt(start)}. Durations are `[estimate]` unless a stage says otherwise. "
         f"Best case uses the short end of every range, worst case the long end.", ""]
    end_b = max(v[1] for v in best.values())
    end_w = max(v[1] for v in worst.values())
    L += [f"**Finish:** {mon(wdate(start, end_b))} (best) to {mon(wdate(start, end_w))} (worst), "
          f"{end_b:.0f}–{end_w:.0f} weeks.", "",
          "**Critical path (worst case):** " + " → ".join(f"{i}" for i in crit) + ".", ""]
    L += ["| Stage | Weeks | Start (best → worst) | End (best → worst) | Exit gate | Critical |",
          "|---|---|---|---|---|---|"]
    for s in topo(d["stages"]):
        b, w = best[s["id"]], worst[s["id"]]
        lo, hi = s["weeks"]
        wk = f"{lo:g}" if lo == hi else f"{lo:g}–{hi:g}"
        gate = (s.get("gate") or "—").replace("|", "/")
        L.append(f"| **{s['id']}** {s['name']} | {wk} | {fmt(wdate(start, b[0]))} → {fmt(wdate(start, w[0]))} | "
                 f"{fmt(wdate(start, b[1]))} → {fmt(wdate(start, w[1]))} | {gate} | {'yes' if s['id'] in crit else ''} |")
    if d.get("milestones"):
        L += ["", "## Milestones", "", "| Milestone | After | Date (best → worst) |", "|---|---|---|"]
        for m in d["milestones"]:
            b, w = best[m["after"]][1], worst[m["after"]][1]
            L.append(f"| {m['name']} | {m['after']} | {fmt(wdate(start, b))} → {fmt(wdate(start, w))} |")
    if longlead:
        L += ["", "## Long-lead purchases", "",
              "Order date = start of the stage that needs the part (best case) minus the factory lead time. A part "
              "whose order date has passed but that is in stock now (`stock.on_hand` ≥ `qty_needed`) is a "
              "buy-now item, not a late one.", "",
              "| Item | Lead time (weeks) | Needed by | Order by | Status |", "|---|---|---|---|---|"]
        for it in longlead:
            L.append(f"| {it['item']} | {it['lead_weeks']:g} | {it['needed_by']} ({fmt(it['need_date'])}) | "
                     f"{fmt(it['order_by'])} | {it['status']} |")
    return "\n".join(L)


def tw(text, size):
    """Approximate rendered width of text in a Helvetica-like font."""
    return len(text) * size * 0.52


def wrap(text, width, size, max_lines=2):
    """Split text into lines that fit `width` px, breaking only between words. If it still does not fit in
    `max_lines`, the last line ends with an ellipsis after a whole word, never mid-word."""
    words, lines, cur = text.split(), [], ""
    for wd in words:
        cand = (cur + " " + wd).strip()
        if tw(cand, size) <= width or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        last = lines[max_lines - 1].split()
        rest = lines[max_lines:]
        while last and tw(" ".join(last) + " …", size) > width:
            last.pop()
        lines = lines[:max_lines - 1] + [(" ".join(last) + " …") if last else "…"]
        del rest
    return lines


def svg(d, best, worst, crit, start):
    order = topo(d["stages"])
    ms = d.get("milestones", [])
    end_w = max(v[1] for v in worst.values())
    left, right, top, row = 250, 30, 76, 30
    weeks = max(4.0, end_w)
    W = 1120
    px = (W - left - right) / weeks
    lanes_needed = 1
    H = 0  # set after the rows are laid out
    ink, mute, grid, acc, tint = "#111111", "#6b6b6b", "#e6e6e6", "#d9472b", "#cfcfcf"
    legend = "solid = best case · light = range to worst case · red = critical path"
    ly = 30 if 24 + tw(d.get("project", "Roadmap"), 16) * 1.05 + 24 < W - right - tw(legend, 11) else 50
    if ly == 50:
        top += 14                                   # legend on its own line: move the plot down
    halo = 'paint-order="stroke" stroke="#ffffff" stroke-width="4" stroke-linejoin="round"'
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="0" viewBox="0 0 {W} 0" '
         f'font-family="-apple-system, Helvetica Neue, Helvetica, Arial, sans-serif">',
         '<rect/>',
         f'<text x="24" y="30" font-size="16" font-weight="600" fill="{ink}">{escape(d.get("project", "Roadmap"))}</text>']
    o.append(f'<text x="{W - right}" y="{ly}" font-size="11" fill="{mute}" text-anchor="end">{legend}</text>')
    # month grid; the start date gets its own label at the left edge
    o.append(f'<text x="{left:.1f}" y="{top - 14}" font-size="10" font-weight="600" fill="{ink}">{start.strftime("%d %b %Y")}</text>')
    m = dt.date(start.year, start.month, 1)
    while True:
        wk = (m - start).days / 7
        if wk > weeks:
            break
        if wk >= 0:
            x = left + wk * px
            o.append(f'<line x1="{x:.1f}" y1="{top - 10}" x2="{x:.1f}" y2="__GRID_END__" stroke="{grid}" stroke-width="1"/>')
            if (m.month in (1, 4, 7, 10) or weeks < 40) and wk * px > 70:
                lab = m.strftime("%b") + (m.strftime(" %Y") if m.month == 1 or wk == 0 else "")
                o.append(f'<text x="{x + 3:.1f}" y="{top - 14}" font-size="10" fill="{mute}" {halo}>{lab}</text>')
        m = dt.date(m.year + (m.month // 12), m.month % 12 + 1, 1)
    ys = []
    y = top
    for s in order:
        lines = wrap(s["name"], left - 24 - 16 - tw(s["id"], 12) - 8, 12)
        h = row if len(lines) == 1 else row + 14
        ys.append((y, h, lines))
        y += h
    for (y, h, lines), s in zip(ys, order):
        b, w = best[s["id"]], worst[s["id"]]
        c = acc if s["id"] in crit else ink
        idw = tw(s["id"], 12) + 8
        ty = y + h / 2 + 4 - (len(lines) - 1) * 7
        o.append(f'<text x="24" y="{ty:.1f}" font-size="12" fill="{ink}"><title>{escape(s["name"])}</title>'
                 f'<tspan font-weight="600">{escape(s["id"])}</tspan>'
                 f'<tspan x="{24 + idw:.1f}">{escape(lines[0])}</tspan>'
                 + "".join(f'<tspan x="{24 + idw:.1f}" dy="14">{escape(ln)}</tspan>' for ln in lines[1:]) + '</text>')
        x0, x1 = left + b[0] * px, left + w[1] * px
        by = y + h / 2 - 7
        o.append(f'<rect x="{x0:.1f}" y="{by:.1f}" width="{max(2, x1 - x0):.1f}" height="14" rx="3" fill="{tint}" opacity="0.6"/>')
        o.append(f'<rect x="{x0:.1f}" y="{by:.1f}" width="{max(2, (b[1] - b[0]) * px):.1f}" height="14" rx="3" fill="{c}"/>')
    y_end = (ys[-1][0] + ys[-1][1]) if ys else top
    lane_rows = []
    if ms:
        xs = {id(mm): left + best[mm["after"]][1] * px for mm in ms}
        # lane 0 shares its row with every diamond: a label there must not cover another milestone's diamond
        lanes = [[(x - 7, x + 7) for x in xs.values()]]
        for mm in sorted(ms, key=lambda m_: best[m_["after"]][1]):
            x = xs[id(mm)]
            wlab = tw(mm["name"], 10)
            anchor_end = x + 9 + wlab > W - right
            span = (x - 9 - wlab, x - 7) if anchor_end else (x + 7, x + 9 + wlab)
            own = (x - 7, x + 7)
            for k, occ in enumerate(lanes):
                if all(span[1] + 8 <= a or span[0] - 8 >= b for a, b in occ if (a, b) != own):
                    occ.append(span)
                    break
            else:
                lanes.append([span])
                k = len(lanes) - 1
            lane_rows.append((mm, x, k, anchor_end))
        lanes_needed = max(1, len(lanes))
    H = y_end + (row + 14 * (lanes_needed - 1) if ms else 0) + 40
    o[0] = o[0].replace(f'height="0" viewBox="0 0 {W} 0"', f'height="{H:.0f}" viewBox="0 0 {W} {H:.0f}"')
    o[1] = f'<rect width="{W}" height="{H:.0f}" fill="#ffffff"/>'
    o = [ln.replace('y2="__GRID_END__"', f'y2="{H - 30:.0f}"') for ln in o]
    if ms:
        y = y_end
        o.append(f'<text x="24" y="{y + 19}" font-size="12" fill="{mute}">Milestones</text>')
        for mm, x, k, anchor_end in lane_rows:
            o.append(f'<path d="M{x:.1f} {y + 8} l6 7 l-6 7 l-6 -7 z" fill="{acc}"><title>{escape(mm["name"])}</title></path>')
            tx, anc = (x - 9, ' text-anchor="end"') if anchor_end else (x + 9, "")
            o.append(f'<text x="{tx:.1f}" y="{y + 19 + k * 14}" font-size="10" fill="{ink}"{anc} {halo}>{escape(mm["name"])}</text>')
    o.append('</svg>')
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stages", required=True, help="stages JSON (see templates/stages.example.json)")
    ap.add_argument("--start", help="override the start date (YYYY-MM-DD)")
    ap.add_argument("--md", help="write the Markdown table here (default: stdout)")
    ap.add_argument("--svg", help="write the SVG timeline here")
    a = ap.parse_args()
    try:
        d = load(a.stages)
        start = dt.date.fromisoformat(a.start or d["start"])
        best, worst = schedule(d["stages"], 0), schedule(d["stages"], 1)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    crit = critical_path(d["stages"], worst)
    today = dt.date.today()
    longlead = []
    for it in d.get("long_lead", []):
        need = wdate(start, best[it["needed_by"]][0])
        order_by = need - dt.timedelta(weeks=it["lead_weeks"])
        st = it.get("stock") or {}
        have, qty = st.get("on_hand"), it.get("qty_needed")
        in_stock = bool(have) and (qty is None or have >= qty)
        if order_by < today and in_stock:
            src = f"{have:,} @ {st.get('source', 'distributor')} {st.get('date', '')}".rstrip()
            buy = f"buy {qty:,} now" if qty else "buy now"
            status = f"in stock ({src}): {buy}; the factory lead time would be late"
        elif order_by < today:
            short = f" (stock {have:,} < {qty:,} needed)" if have and qty else ""
            status = f"LATE by {(today - order_by).days / 7:.0f} wk{short}: order now"
        elif order_by < start:
            status = "order before the project starts"
        else:
            status = "ok"
        longlead.append(dict(it, need_date=need, order_by=order_by, status=status))
    text = markdown(d, best, worst, crit, start, longlead)
    if a.md:
        os.makedirs(os.path.dirname(os.path.abspath(a.md)), exist_ok=True)
        open(a.md, "w").write(text + "\n")
    else:
        print(text)
    if a.svg:
        os.makedirs(os.path.dirname(os.path.abspath(a.svg)), exist_ok=True)
        open(a.svg, "w").write(svg(d, best, worst, crit, start))
    end_b = max(v[1] for v in best.values())
    end_w = max(v[1] for v in worst.values())
    n_late = sum(1 for x in longlead if x["status"].startswith("LATE"))
    n_buy = sum(1 for x in longlead if x["status"].startswith("in stock"))
    print(f"roadmap: {len(d['stages'])} stages, {end_b:.0f}–{end_w:.0f} weeks, critical path {'→'.join(crit)}, "
          f"{n_late} long-lead item(s) late, {n_buy} to buy from stock now", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
