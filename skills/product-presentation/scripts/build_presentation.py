#!/usr/bin/env python3
"""Build the product presentation (one self-contained HTML deck) from a project's hw/ folder.

Reads whatever exists and skips a slide when its input is missing:

  hw/brief.md                       name, idea, users and use, environment, body       (product-discovery)
  hw/architecture.svg|png|md        diagram; a Mermaid flowchart in architecture.md is drawn natively
  hw/bom.csv                        components table                                   (specs-engineer)
  hw/power/budget.json              runtime per scenario, peak checks                  (battery-and-power)
  hw/doability/score.json           verdict (`overall`), areas, blockers, prototype checks (doability-review)
  hw/doability/findings.json        findings
  hw/release/*/checks/release-check.json  build package checklist                      (build-package)
  hw/doability/review.md            "Must be measured or quoted" list for next steps (fallback report.md)
  hw/cost/model.json                cost per unit by tier, NRE, landed cost             (cost-and-sourcing)
  hw/compliance/matrix.md           certification summary                               (compliance-planner)
  hw/roadmap/schedule.md            stages, dates, gates, milestones; else timeline.svg  (prototype-roadmap)
  hw/renders/*                      one slide per image; renders/captions.json          (product-render)
  hw/drawings/*                     one slide per drawing                               (technical-drawing)
  hw/presentation/deck.json         optional overrides (see SKILL.md)

Writes hw/presentation/index.html. Images are inlined when they total less than --inline-limit MB,
otherwise copied to hw/presentation/assets/. Standard library only.

Examples:
  python3 build_presentation.py hw
  python3 build_presentation.py hw --pdf                  # also hw/presentation/presentation.pdf (needs Chrome/Chromium/Edge)
  python3 build_presentation.py hw --png /tmp/slides      # one PNG per slide, for visual review
"""
import argparse
import base64
import csv
import datetime as dt
import glob
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif")
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
        ".svg": "image/svg+xml", ".gif": "image/gif"}
E = html.escape
# canonical file name stems, in slide order (hero is the cover); other names follow alphabetically
RENDER_ORDER = ["hero", "desk", "hand", "dark", "exploded", "lineup", "blueprint", "architecture"]


# ------------------------------------------------------------------ small helpers
def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def load_json(path):
    t = read(path)
    if t is None:
        return None
    try:
        return json.loads(t)
    except json.JSONDecodeError as ex:
        print(f"warning: {path}: {ex}", file=sys.stderr)
        return None


def first(*paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


def rng(v):
    """number | [lo, hi] | None -> (lo, hi) or None"""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return (float(v), float(v))
    if isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
        return (float(v[0]), float(v[1]))
    return None


def money(x):
    if x is None:
        return "—"
    if abs(x) >= 100:
        return f"${x:,.0f}"
    if abs(x) >= 0.995 or x == 0:
        return f"${x:,.2f}"
    return f"${x:.3f}".rstrip("0") if x < 0.1 else f"${x:.2f}"


def money_r(v):
    r = rng(v)
    if r is None:
        return "—"
    lo, hi = r
    if abs(hi - lo) < 1e-9 * max(1, abs(hi)):
        return money(lo)
    a, b = money(lo), money(hi)
    return f"{a}–{b[1:]}"


def num_r(v, unit="", digits=0):
    r = rng(v)
    if r is None:
        return "—"
    f = f"{{:,.{digits}f}}"
    s = f.format(r[0]) if r[0] == r[1] else f"{f.format(r[0])}–{f.format(r[1])}"
    return s + (f" {unit}" if unit else "")


TIME_UNITS = [("h", 1.0), ("days", 24.0), ("months", 730.0), ("years", 8760.0)]


def time_unit(max_h):
    """display unit for a set of runtimes: hours < 2 days, days < 2 months, months < 2 years, else years"""
    if max_h < 48:
        return TIME_UNITS[0]
    if max_h < 1460:
        return TIME_UNITS[1]
    if max_h < 17520:
        return TIME_UNITS[2]
    return TIME_UNITS[3]


def human_hours(h):
    """runtime in the unit a person thinks in"""
    if h is None:
        return "—"
    if h < 48:
        return f"{h:.0f} h" if h >= 10 else f"{h:.1f} h"
    d = h / 24
    if d < 60:
        return f"{d:.0f} days"
    m = h / 730.0
    if m < 24:
        return f"{m:.0f} months" if m >= 10 else f"{m:.1f} months"
    return f"{h / 8760:.1f} years"


def norm_ev(s):
    s = (s or "").strip().strip("[]").lower()
    for k in ("verified", "estimate", "assumption"):
        if s.startswith(k):
            return k
    return "estimate" if s else ""


EV_LABEL = {"verified": "verified", "estimate": "est.", "assumption": "assumed"}


def ev_tag(ev, title=""):
    k = norm_ev(ev)
    if not k:
        return ""
    t = f' title="{E(title)}"' if title else ""
    return f'<span class="ev ev-{k}"{t}>{EV_LABEL[k]}</span>'


def split_unit(v):
    """'28 × 28 × 6.5 mm' -> ('28 × 28 × 6.5', 'mm'); '15 months' -> ('15', 'months'); '$7.14–10.43' -> (v, '')"""
    m = re.match(r"^(.*?\d[\d.,]*)\s+([A-Za-zµ°%][\w%°µ/·.]*(?:\s[A-Za-z]+)?)$", v.strip())
    return (m.group(1), m.group(2)) if m else (v, "")


def with_pill(text_html, pill):
    """keep the evidence pill on the same line as the last word of its label"""
    if not pill:
        return text_html
    head, _, last = text_html.rpartition(" ")
    return (head + " " if head else "") + f"<span class='nowrap'>{last}&nbsp;{pill}</span>"


def inline_md(s):
    """escape, then **bold**, *em*, `code`, [text](http...)"""
    s = E(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md_tables(text):
    """all pipe tables in a Markdown text -> [(header, rows)]"""
    out, cur = [], []
    for line in (text or "").splitlines() + [""]:
        if line.strip().startswith("|"):
            cur.append(line.strip())
            continue
        if len(cur) >= 2 and re.match(r"^\|?\s*:?-{2,}", cur[1].replace("|", "", 1).strip() or "--"):
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in cur]
            out.append((cells[0], cells[2:]))
        cur = []
    return out


def md_sections(text):
    """'## n. Title' sections -> {normalized title: body}"""
    secs, name, buf = {}, None, []
    for line in (text or "").splitlines():
        m = re.match(r"^##\s+(?:\d+\.\s*)?(.+?)\s*$", line)
        if m:
            if name:
                secs[name] = "\n".join(buf).strip()
            name, buf = m.group(1).strip().lower(), []
        elif name:
            buf.append(line)
    if name:
        secs[name] = "\n".join(buf).strip()
    return secs


def sec(secs, *keys):
    for k in keys:
        for n, b in secs.items():
            if n.startswith(k):
                return b
    return ""


def paragraphs(body):
    """plain paragraphs only (no lists, tables, quotes)"""
    ps, cur = [], []
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith(("|", "-", "*", ">", "#", "```")) or re.match(r"^\d+\.\s", s):
            if cur:
                ps.append(" ".join(cur))
                cur = []
            continue
        cur.append(s)
    if cur:
        ps.append(" ".join(cur))
    return ps


def bullets(body):
    """'- **Label:** value' bullets -> [(label, value)]"""
    out = []
    for line in body.splitlines():
        m = re.match(r"^\s*[-*]\s+\*\*(.+?):?\*\*:?\s*(.*)$", line)
        if m:
            out.append((m.group(1).rstrip(":"), m.group(2)))
    return out


# ------------------------------------------------------------------ inputs
class Project:
    def __init__(self, hw):
        self.hw = hw
        self.deck = load_json(os.path.join(hw, "presentation", "deck.json")) or {}
        self.brief = read(os.path.join(hw, "brief.md")) or ""
        self.secs = md_sections(self.brief)
        m = re.search(r"^#\s+(?:Product brief:\s*)?(.+)$", self.brief, re.M)
        self.name = self.deck.get("title") or (m.group(1).strip() if m else "Product")
        mm = re.search(r"\*\*Date:\*\*\s*([0-9-]{8,10})", self.brief)
        self.date = self.deck.get("date") or (mm.group(1) if mm else dt.date.today().isoformat())
        self.bom = self._bom()
        self.power = load_json(first(os.path.join(hw, "power", "budget.json"), os.path.join(hw, "power", "results.json")))
        self.findings = load_json(os.path.join(hw, "doability", "findings.json"))
        self.score = load_json(os.path.join(hw, "doability", "score.json"))
        self.report = read(first(os.path.join(hw, "doability", "review.md"), os.path.join(hw, "doability", "report.md")) or "") or ""
        rels = sorted(glob.glob(os.path.join(hw, "release", "*", "checks", "release-check.json")), key=os.path.getmtime)
        self.release = load_json(rels[-1]) if rels else None      # build-package gate result (latest release)
        self.timeline_svg = first(os.path.join(hw, "roadmap", "timeline.svg"))
        self.cost = load_json(os.path.join(hw, "cost", "model.json"))
        self.compliance = read(first(os.path.join(hw, "compliance", "matrix.md"), os.path.join(hw, "compliance.md")) or "")
        self.schedule = read(first(os.path.join(hw, "roadmap", "schedule.md"), os.path.join(hw, "roadmap.md")) or "")
        self.arch_img = first(*[os.path.join(hw, f"architecture{x}") for x in (".svg", ".png", ".jpg")],
                              *[os.path.join(hw, "drawings", f"architecture{x}") for x in (".svg", ".png")])
        self.arch_md = read(os.path.join(hw, "architecture.md")) or ""
        self.renders = self._images("renders")
        self.drawings = [p for p in self._images("drawings") if os.path.splitext(os.path.basename(p))[0] != "architecture"]
        self.captions = {}
        for d in ("renders", "drawings"):
            self.captions.update(load_json(os.path.join(hw, d, "captions.json")) or {})
        self.captions.update(self.deck.get("captions", {}))
        self.maturity = (self.findings or {}).get("maturity") or self.deck.get("maturity")

    def _bom(self):
        p = os.path.join(self.hw, "bom.csv")
        if not os.path.exists(p):
            return []
        with open(p, newline="", encoding="utf-8") as f:
            return [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]

    def _images(self, sub):
        """One image per file name stem. Renders: a raster (the real render) beats an SVG placeholder of the same
        name. Drawings: the SVG (vector) beats a raster export. Canonical names come first, in RENDER_ORDER."""
        files = sorted(p for p in glob.glob(os.path.join(self.hw, sub, "*")) if p.lower().endswith(IMG_EXT))
        want_svg = sub == "drawings"
        best = {}
        for p in files:
            stem = os.path.splitext(os.path.basename(p))[0]
            cur = best.get(stem)
            if cur is None:
                best[stem] = p
                continue
            p_svg, c_svg = p.lower().endswith(".svg"), cur.lower().endswith(".svg")
            if p_svg != c_svg:
                if p_svg == want_svg:
                    best[stem] = p
            elif os.path.getsize(p) > os.path.getsize(cur):
                best[stem] = p
        rank = lambda s: (RENDER_ORDER.index(s) if s in RENDER_ORDER else len(RENDER_ORDER), s)
        return [best[k] for k in sorted(best, key=rank)]


# ------------------------------------------------------------------ images
def img_size(path):
    """(w, h) of a PNG, JPEG or SVG without dependencies; None if unknown."""
    try:
        with open(path, "rb") as f:
            head = f.read(64 * 1024)
    except OSError:
        return None
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        import struct
        return struct.unpack(">II", head[16:24])
    if head[:2] == b"\xff\xd8":
        import struct
        i = 2
        while i < len(head) - 9:
            if head[i] != 0xFF:
                i += 1
                continue
            mk, ln = head[i + 1], struct.unpack(">H", head[i + 2:i + 4])[0]
            if mk in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", head[i + 5:i + 9])
                return (w, h)
            i += 2 + ln
        return None
    m = re.search(rb'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)"', head)
    return (float(m.group(1)), float(m.group(2))) if m else None


def first_sentences(text, limit=320):
    """the opening of a paragraph, cut at a sentence end before `limit` characters"""
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    cut = [m.end() for m in re.finditer(r"[.!?](?=\s)", text[:limit])]
    return text[:cut[-1]] if cut else text[:limit].rsplit(" ", 1)[0] + "…"


class Images:
    def __init__(self, out_dir, inline):
        self.out_dir, self.inline, self.copied = out_dir, inline, 0

    def src(self, path):
        ext = os.path.splitext(path)[1].lower()
        if self.inline:
            with open(path, "rb") as f:
                return f"data:{MIME[ext]};base64," + base64.b64encode(f.read()).decode()
        dst_dir = os.path.join(self.out_dir, "assets")
        os.makedirs(dst_dir, exist_ok=True)
        name = os.path.basename(os.path.dirname(path)) + "-" + os.path.basename(path)
        shutil.copy2(path, os.path.join(dst_dir, name))
        self.copied += 1
        return "assets/" + name


# ------------------------------------------------------------------ charts (inline SVG, themed by CSS variables)
def text_w(t, size):
    """approximate rendered width of a label (sans, tabular digits): conservative so placement errs on space"""
    narrow = sum(1 for c in t if c in "il.,:;|!'·1 ")
    return size * (0.6 * (len(t) - narrow) + 0.32 * narrow)


def nice_ticks(vmax, steps, max_ticks=6):
    """0 .. >= vmax in one of the allowed round steps, at most max_ticks intervals"""
    for st in steps:
        n = math.ceil(vmax / st - 1e-9)
        if n <= max_ticks:
            return [round(i * st, 9) for i in range(n + 1)]
    st = steps[-1]
    while math.ceil(vmax / st) > max_ticks:
        st *= 2
    return [round(i * st, 9) for i in range(math.ceil(vmax / st - 1e-9) + 1)]


STEPS = {"h": [1, 2, 4, 6, 12, 24], "days": [1, 2, 5, 7, 10, 14, 30], "months": [1, 2, 3, 6, 12],
         "years": [0.5, 1, 2, 5, 10], "": [1, 2, 2.5, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000]}


def hbar_chart(rows, ticks, fmt_tick, axis_unit="", log=False, target=None, target_label="",
               legend=None, width=1000, label_w=150, row_h=46, font=16):
    """Horizontal bars with collision-free labels. One axis, one unit, round ticks.

    rows: dicts with label, lo, hi, text (value label), tip, emph (True = series color, False = muted),
          track (draw a thin track from the axis start to lo; for ranges on a linear axis).
    Value labels: right of the mark; if that crosses the target line or the plot edge, right of the target line;
    else inside the mark; else right with a knockout halo. Every label carries a halo in the page color, so
    gridlines never cut through text."""
    top = 46 if target is not None else 14
    pad_r = 24
    plot_x0, plot_x1 = label_w, width - pad_r
    if log:
        e0, e1 = math.log10(ticks[0]), math.log10(ticks[-1])
        X = lambda v: plot_x0 + (math.log10(max(v, ticks[0])) - e0) / (e1 - e0) * (plot_x1 - plot_x0)
    else:
        X = lambda v: plot_x0 + v / ticks[-1] * (plot_x1 - plot_x0)
    # reserve room on the right for the longest label that may sit past the last tick
    need = max(text_w(r["text"], font) for r in rows) + 18
    longest_end = max(X(r["hi"]) for r in rows)
    if longest_end + need > plot_x1:
        shrink = (longest_end + need - plot_x1)
        plot_x1 -= shrink
        if log:
            X = lambda v: plot_x0 + (math.log10(max(v, ticks[0])) - e0) / (e1 - e0) * (plot_x1 - plot_x0)
        else:
            X = lambda v: plot_x0 + v / ticks[-1] * (plot_x1 - plot_x0)
    y_axis = top + len(rows) * row_h
    leg_h = 34 if legend else 0
    h = y_axis + 34 + leg_h
    o = [f'<svg class="chart" viewBox="0 0 {width} {h}" width="100%" role="img" style="--fs:{font}px">']
    for i, t in enumerate(ticks):
        tx = X(t)
        o.append(f'<line class="grid" x1="{tx:.1f}" y1="{top - 6}" x2="{tx:.1f}" y2="{y_axis}"/>')
        lab = fmt_tick(t) + (f" {axis_unit}" if axis_unit and i == len(ticks) - 1 else "")
        anchor = "end" if i == len(ticks) - 1 and tx + text_w(lab, 13) / 2 > width - 4 else "middle"
        o.append(f'<text class="tick" x="{tx:.1f}" y="{y_axis + 22}" text-anchor="{anchor}">{E(lab)}</text>')
    o.append(f'<line class="axis" x1="{plot_x0}" y1="{y_axis}" x2="{X(ticks[-1]):.1f}" y2="{y_axis}"/>')
    tx_t = None
    if target is not None:
        tx_t = X(target)
        o.append(f'<line class="target" x1="{tx_t:.1f}" y1="{top - 14}" x2="{tx_t:.1f}" y2="{y_axis}"/>')
        tw = text_w(target_label, 14)
        anchor = "middle"
        if tx_t + tw / 2 > width - 4:
            anchor = "end"
        elif tx_t - tw / 2 < 4:
            anchor = "start"
        o.append(f'<text class="target-label" x="{tx_t:.1f}" y="{top - 22}" text-anchor="{anchor}">{E(target_label)}</text>')
    for i, r in enumerate(rows):
        yc = top + i * row_h + row_h / 2
        o.append(f'<text class="cat" x="{label_w - 16}" y="{yc + 5.5:.1f}" text-anchor="end">{E(r["label"])}</text>')
        x0 = X(r["lo"]) if (log or r["lo"] != r["hi"]) else plot_x0
        x1 = max(X(r["hi"]), x0 + 4)
        cls = "bar" if r.get("emph", True) else "bar bar-muted"
        g = [f'<g class="mark" tabindex="0" data-tip="{E(r.get("tip", r["text"]))}">',
             f'<rect class="hit" x="{plot_x0}" y="{yc - row_h / 2 + 2:.1f}" width="{width - plot_x0}" height="{row_h - 4}"/>']
        if r.get("track") and x0 > plot_x0 + 1:
            g.append(f'<rect class="{cls} track" x="{plot_x0}" y="{yc - 2:.1f}" width="{x0 - plot_x0 - 2:.1f}" height="4" rx="2"/>')
        g.append(f'<rect class="{cls}" x="{x0:.1f}" y="{yc - 8:.1f}" width="{x1 - x0:.1f}" height="16" rx="4"/>')
        # label placement
        w = text_w(r["text"], font)
        def clear(a, b):
            return (tx_t is None or not (a - 6 <= tx_t <= b + 6)) and b <= width - 4
        lx, anchor, inside = x1 + 10, "start", False
        if not clear(lx, lx + w):
            if tx_t is not None and tx_t > x1 and clear(tx_t + 10, tx_t + 10 + w):
                lx = tx_t + 10
            elif x1 - x0 >= w + 20:
                lx, anchor, inside = x1 - 10, "end", True
        g.append(f'<text class="val{" val-in" if inside else ""}" x="{lx:.1f}" y="{yc + 5.5:.1f}" text-anchor="{anchor}">{E(r["text"])}</text>')
        g.append("</g>")
        o.append("".join(g))
    if legend:
        lx = plot_x0
        ly = h - 12
        for name, emph in legend:
            o.append(f'<rect class="{"bar" if emph else "bar bar-muted"}" x="{lx}" y="{ly - 10}" width="16" height="10" rx="3"/>'
                     f'<text class="legend-t" x="{lx + 24}" y="{ly}">{E(name)}</text>')
            lx += 24 + text_w(name, 14) + 30
    o.append("</svg>")
    return "".join(o)


def chart_collisions(svg):
    """Layout check for the charts this script draws: text boxes against each other, against the target line
    and against bars (a label inside its own bar is allowed), and against the chart edges. Returns problems."""
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    if not vb:
        return []
    W, H = float(vb.group(1)), float(vb.group(2))
    fs = float((re.search(r"--fs:([\d.]+)px", svg) or [0, 16])[1])
    size = {"tick": 13, "target-label": 14, "legend-t": 14, "edge-label": 13}
    boxes = []
    for m in re.finditer(r'<text class="([\w -]+)" x="([-\d.]+)" y="([-\d.]+)"(?: text-anchor="(\w+)")?[^>]*>([^<]*)</text>', svg):
        cls, x, y, anc, t = m.group(1), float(m.group(2)), float(m.group(3)), m.group(4) or "start", html.unescape(m.group(5))
        k = cls.split()[0]
        if k == "node-label":
            continue
        f = size.get(k, fs)
        w = text_w(t, f)
        x0 = x - w if anc == "end" else x - w / 2 if anc == "middle" else x
        boxes.append((cls, t, x0, y - 0.75 * f, x0 + w, y + 0.22 * f))
    rects = [(float(a), float(b), float(a) + float(c), float(b) + float(d), k) for k, a, b, c, d in
             re.findall(r'<rect class="(bar[\w -]*)" x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"', svg)]
    targets = [(float(x), min(float(y1), float(y2)), max(float(y1), float(y2))) for x, y1, y2 in
               re.findall(r'<line class="target" x1="([-\d.]+)" y1="([-\d.]+)" x2="[-\d.]+" y2="([-\d.]+)"', svg)]
    out = []
    for i, (c, t, a, b, cc, d) in enumerate(boxes):
        if a < -1 or cc > W + 1 or b < -1 or d > H + 1:
            out.append(f"'{t}' leaves the chart area")
        if "target-label" not in c:
            for tx, ty0, ty1 in targets:
                if a - 2 <= tx <= cc + 2 and b < ty1 and d > ty0:
                    out.append(f"'{t}' crosses the target line")
        for (ra, rb, rc, rd, k) in rects:
            ov = min(cc, rc) - max(a, ra) > 1 and min(d, rd) - max(b, rb) > 1
            if ov and not ("val-in" in c and a >= ra - 1 and cc <= rc + 1):
                out.append(f"'{t}' overlaps a bar")
                break
        for (c2, t2, a2, b2, cc2, d2) in boxes[i + 1:]:
            if min(cc, cc2) - max(a, a2) > 1 and min(d, d2) - max(b, b2) > 1:
                out.append(f"'{t}' overlaps '{t2}'")
    return out


def _clean_label(t):
    t = (t or "").strip().strip('"').strip()
    return [x.strip() for x in re.split(r"<br\s*/?>|\\n", t) if x.strip()]


def parse_mermaid(text):
    """flowchart/graph subset: nodes A, A[..], A(..), A((..)), A{..}, A[".."]; edges -->, ---, -.->, ==>,
    with labels as -- x --> or -->|x|; chains A --> B --> C. Labels keep <br/> line breaks."""
    m = re.search(r"```mermaid\s*\n(.*?)```", text or "", re.S)
    if not m or not re.search(r"^\s*(flowchart|graph)\s", m.group(1), re.M):
        return None
    nodes, order, edges = {}, [], []
    node_re = r'\s*([A-Za-z0-9_]+)\s*(\(\(.*?\)\)|\[\[.*?\]\]|\[.*?\]|\(.*?\)|\{.*?\})?\s*'
    link_re = r'(--\s*"?[^-|>]+?"?\s*-->|-->\s*\|[^|]*\||---\s*\|[^|]*\||-\.->|-->|==>|---)'
    for line in m.group(1).splitlines()[1:]:
        line = line.strip()
        if not line or line.startswith(("%%", "classDef", "class ", "style ", "subgraph", "end", "linkStyle")):
            continue
        parts = re.split(link_re, line)
        prev, label, undirected = None, None, False
        for k, p in enumerate(parts):
            if k % 2 == 1:
                lm = re.match(r'--\s*"?(.+?)"?\s*-->', p) or re.search(r'\|\s*"?(.*?)"?\s*\|', p)
                label = lm.group(1) if lm else None
                undirected = p.startswith("---")
                continue
            nm = re.match(node_re, p)
            if not nm or not nm.group(1):
                prev = None
                continue
            nid, shape = nm.group(1), nm.group(2)
            if nid not in nodes:
                nodes[nid] = {"label": [nid], "round": False}
                order.append(nid)
            if shape:
                inner = shape[2:-2] if shape[:2] in ("((", "[[") else shape[1:-1]
                nodes[nid]["label"] = _clean_label(inner) or [nid]
                nodes[nid]["round"] = shape.startswith("((")
            if prev:
                el = None
                if label:
                    el = [w for x in _clean_label(label) for w in re.split(r",\s*", x) if w]
                edges.append((prev, nid, el, undirected))
            prev, label, undirected = nid, None, False
    return (nodes, order, edges) if edges else None


def _wrap_lines(lines, maxc=24):
    out = []
    for ln in lines:
        words, cur = ln.split(" "), ""
        for w in words:
            if cur and len(cur) + 1 + len(w) > maxc:
                out.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            out.append(cur)
    return out


def flow_svg(graph, width=1280):
    """Left-to-right layered layout. Directed edges set the columns; undirected (---) edges attach a node to
    its partner's column. Boxes are sized from their measured text, column gaps from the edge labels, and the
    nodes in each column are ordered by the position of their neighbours to limit crossings."""
    nodes, order, edges = graph
    FS, LH, PADX, PADY = 15, 19, 14, 11
    directed = [(a, b) for a, b, _l, u in edges if not u]
    attach = {}
    for a, b, _l, u in edges:
        if u:
            has_a = any(a in e for e in directed)
            has_b = any(b in e for e in directed)
            child, host = (a, b) if (has_b and not has_a) or (not has_a and not has_b) else (b, a)
            if not any(child in e for e in directed):
                attach[child] = host
    rank = {n: 0 for n in order}
    for _ in range(len(order)):
        changed = False
        for a, b in directed:
            if rank[b] < rank[a] + 1 and rank[a] + 1 < len(order):
                rank[b] = rank[a] + 1
                changed = True
        if not changed:
            break
    # sources that only feed one node sit just before it (a button next to the chip, not in column 0)
    for n in order:
        outs = [b for a, b in directed if a == n]
        ins = [a for a, b in directed if b == n]
        if not ins and outs and n not in attach:
            rank[n] = max(0, min(rank[b] for b in outs) - 1)
    for c, h in attach.items():
        rank[c] = rank.get(h, 0)
    lab = {n: _wrap_lines(nodes[n]["label"]) for n in order}
    size = {n: (max(text_w(t, FS) for t in lab[n]) + 2 * PADX, len(lab[n]) * LH + 2 * PADY) for n in order}
    cols = {}
    for n in order:
        cols.setdefault(rank[n], []).append(n)
    keys = sorted(cols)
    # order within columns: barycentre of already-placed neighbours, attached nodes right after their host
    idx = {}
    for ci, c in enumerate(keys):
        ns = [n for n in cols[c] if n not in attach]
        def bary(n):
            nb = [idx[a] for a, b in directed if b == n and a in idx] + [idx[b] for a, b in directed if a == n and b in idx]
            return sum(nb) / len(nb) if nb else 0
        if ci:
            ns.sort(key=bary)
        out = []
        for n in ns:
            out.append(n)
            out += [a for a in cols[c] if attach.get(a) == n]
        out += [n for n in cols[c] if n not in out]
        cols[c] = out
        for i, n in enumerate(out):
            idx[n] = i - (len(out) - 1) / 2
    colw = {c: max(size[n][0] for n in cols[c]) for c in keys}
    gaps = {}
    for a, b, l, u in edges:
        if l and not u and rank[b] > rank[a]:
            w = max(text_w(t, 13) for t in l) + 28
            gaps[rank[a]] = max(gaps.get(rank[a], 0), w)
    GY = 22
    colh = {c: sum(size[n][1] for n in cols[c]) + GY * (len(cols[c]) - 1) for c in keys}
    height = int(max(colh.values()) + 40)
    x, colx = 20, {}
    for i, c in enumerate(keys):
        colx[c] = x
        x += colw[c] + (max(56, gaps.get(c, 0)) if i < len(keys) - 1 else 0)
    width = int(x + 20)
    pos = {}
    for c in keys:
        y = (height - colh[c]) / 2
        for n in cols[c]:
            w, h = size[n]
            pos[n] = (colx[c] + (colw[c] - w) / 2, y, w, h)
            y += h + GY
    o = [f'<svg class="chart flow" viewBox="0 0 {width} {height}" width="100%" role="img" style="--fs:{FS}px">',
         '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         '<path d="M0 0 L10 5 L0 10 z" class="arrow"/></marker></defs>']
    labels = []
    for a, b, l, u in edges:
        ax, ay, aw, ah = pos[a]
        bx, by, bw, bh = pos[b]
        if rank[a] == rank[b]:                           # same column (attachment): short vertical link
            top, bot = (pos[a], pos[b]) if ay < by else (pos[b], pos[a])
            xm = top[0] + top[2] / 2
            d = f"M{xm:.1f} {top[1] + top[3]:.1f} L{xm:.1f} {bot[1]:.1f}"
            o.append(f'<path class="edge edge-u" d="{d}"/>')
            continue
        if bx < ax:
            a, b = b, a
            ax, ay, aw, ah, bx, by, bw, bh = bx, by, bw, bh, ax, ay, aw, ah
        x1, y1, x2, y2 = ax + aw, ay + ah / 2, bx, by + bh / 2
        mx = (x1 + x2) / 2
        d = f"M{x1:.1f} {y1:.1f} C{mx:.1f} {y1:.1f} {mx:.1f} {y2:.1f} {x2 - 2:.1f} {y2:.1f}"
        mk = '' if u else ' marker-end="url(#ah)"'
        o.append(f'<path class="edge{" edge-u" if u else ""}" d="{d}"{mk}/>')
        if l:
            labels.append((x2 - 10, y2, l))
    for n in order:
        x, y, w, h = pos[n]
        rx = min(h / 2, 22) if nodes[n]["round"] else 10
        o.append(f'<rect class="node{" hub" if nodes[n]["round"] else ""}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}"/>')
        t0 = y + PADY + LH * 0.72
        for i, t in enumerate(lab[n]):
            cls = "node-label" if i == 0 else "node-label node-sub"
            o.append(f'<text class="{cls}" x="{x + w / 2:.1f}" y="{t0 + i * LH:.1f}" text-anchor="middle">{E(t)}</text>')
    for x1, y1, l in labels:                              # edge labels last, with a halo, left-aligned at the source
        for i, t in enumerate(l):
            yy = y1 - 7 - (len(l) - 1 - i) * 15
            o.append(f'<text class="edge-label" x="{x1:.1f}" y="{yy:.1f}" text-anchor="end">{E(t)}</text>')
    o.append("</svg>")
    return "".join(o)


# ------------------------------------------------------------------ slides
STATUS = {
    "GO": ("good", "✓", "Go"),
    "GO-WITH-CHANGES": ("warn", "!", "Go with changes"),
    "NO-GO": ("bad", "✕", "No-go"),
    "NOT-REVIEWED": ("none", "–", "Not reviewed"),
}
SEV = {"critical": ("bad", "✕", "Critical"), "major": ("warn", "!", "Major"),
       "minor": ("none", "·", "Minor"), "info": ("none", "·", "Info")}
OVERALL = {"READY TO BUILD (prototype)": ("good", "✓", "Ready to build · prototype"),
           "READY TO BUILD (production)": ("good", "✓", "Ready to build · production"),
           "NOT READY": ("bad", "✕", "Not ready to build")}
LEGACY_OVERALL = {"GO": "READY TO BUILD (prototype)", "GO-WITH-CHANGES": "NOT READY", "NO-GO": "NOT READY"}
AREA_STATUS = {"GO": ("good", "✓", "Go"), "FIX": ("warn", "!", "Fix"), "BLOCKED": ("bad", "✕", "Blocked"),
               "NOT-REVIEWED": ("none", "–", "Not reviewed")}
LEGACY_AREA = {"GO-WITH-CHANGES": "FIX", "NO-GO": "BLOCKED"}
# build-package release_check.py check ids -> build package checklist labels
RELEASE_CHECKS = [("routing", "Routed boards"), ("drc", "DRC and ERC at 0"), ("assembly", "Fab and assembly files"),
                  ("stock", "BOM in stock"), ("mech", "Enclosure STEP"), ("validation", "Assembly validated"),
                  ("docs", "Assembly guide and test plan"), ("order", "Order steps with cost and lead time")]
# doability-review build_package keys (doability_score.py BUILD_PACKAGE)
DOABILITY_PKG = {"routed_board": "Routed boards", "drc_erc_zero": "DRC and ERC at 0", "fab_files": "Fab files",
                 "bom_in_stock": "BOM in stock", "enclosure_step": "Enclosure STEP",
                 "assembly_validated": "Assembly validated", "test_plan": "Test plan"}
PKG_STATUS = {"done": ("good", "✓", "Done"), "partial": ("warn", "!", "Partial"), "missing": ("none", "–", "Missing")}
AREA_LABEL = {"parts": "Parts", "electrical": "Electrical", "power": "Power and battery", "pcb": "PCB",
              "mechanical": "Mechanical", "compliance": "Compliance", "cost": "Cost", "schedule": "Schedule",
              "claims": "Claims vs reality"}


def chip(kind_icon_label):
    k, i, l = kind_icon_label
    return f'<span class="chip chip-{k}"><span class="chip-i" aria-hidden="true">{i}</span>{E(l)}</span>'


def label_cells(h):
    """add data-label (header text) to every td so narrow screens can stack rows into cards"""
    def one(t):
        heads = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<th[^>]*>(.*?)</th>", t, re.S)]
        def row(m):
            i = [0]
            def cell(c):
                lab = heads[i[0]] if i[0] < len(heads) else ""
                i[0] += 1
                return f'<td data-label="{E(lab)}"' + c.group(1)
            return re.sub(r"<td((?:\s[^>]*)?>)", cell, m.group(0))
        return re.sub(r"<tr>(?:(?!</tr>).)*<td.*?</tr>", row, t, flags=re.S)
    return re.sub(r"<table.*?</table>", lambda m: one(m.group(0)), h, flags=re.S)


class Deck:
    def __init__(self, P, imgs):
        self.P, self.imgs, self.slides = P, imgs, []

    def add(self, sid, body, cls=""):
        if body:
            self.slides.append((sid, label_cells(body), cls))

    # -- cover
    def cover(self):
        P = self.P
        hero = self.P.deck.get("hero")
        hero = os.path.join(P.hw, hero) if hero else (P.renders[0] if P.renders else None)
        meta = [E(P.date)]
        if P.maturity:
            meta.append(E(P.maturity))
        fit = (P.deck.get("hero_fit") or "").lower()
        wh = img_size(hero) if hero else None
        crop = fit != "contain" and bool(wh and wh[1] > 1.15 * wh[0])
        img = (f'<img class="cover-img{" cover-crop" if crop else ""}" src="{self.imgs.src(hero)}" alt="{E(P.name)}">'
               if hero else "")
        self.add("cover", f'<div class="cover{"" if hero else " cover-solo"}"><div class="cover-text"><h1>{E(P.name)}</h1>'
                          f'<p class="meta">Design review · {" · ".join(meta)}</p></div>{img}</div>', "slide-cover")

    def idea(self):
        ps = paragraphs(sec(self.P.secs, "idea", "the idea", "summary"))
        if ps:
            self.add("idea", '<div class="statement">' + "".join(f"<p>{inline_md(p)}</p>" for p in ps[:2]) + "</div>")

    def use(self):
        items = bullets(sec(self.P.secs, "users", "use", "who"))
        env = md_tables(sec(self.P.secs, "environment"))
        if not items and not env:
            return
        h = "<h2>Who uses it, where and how</h2><div class='cols'>"
        if items:
            h += "<dl class='facts'>" + "".join(f"<dt>{E(k)}</dt><dd>{inline_md(v)}</dd>" for k, v in items) + "</dl>"
        if env:
            hdr, rows = env[0]
            rows = [r for r in rows if len(r) >= 3 and r[1].strip()]
            if rows:
                h += ("<table class='t t-compact'><thead><tr><th>Condition</th><th>Expected</th><th>Design answer</th></tr></thead><tbody>" +
                      "".join(f"<tr><td>{inline_md(r[0])}</td><td>{inline_md(r[1])}</td><td>{inline_md(r[2])}</td></tr>" for r in rows) +
                      "</tbody></table>")
        self.add("use", h + "</div>")

    def highlights(self):
        P = self.P
        tiles = list(P.deck.get("highlights", []))
        if not tiles:
            body = dict(bullets(sec(P.secs, "body")))
            size = body.get("Size target", "")
            size = re.split(r"\s+·\s+|\*\*", size)[0].strip()
            size = re.sub(r"\s*\((must|should|nice|nice to have|target|goal)\)\s*", " ", size, flags=re.I).strip()
            if size:
                tiles.append({"value": size, "label": "Size target"})
            if P.power:
                base = next((s for s in P.power.get("scenarios", []) if s.get("scenario") == "baseline"), None)
                if base and base.get("runtime_new_h"):
                    tiles.append({"value": human_hours(base["runtime_new_h"]), "label": "Battery life, baseline estimate",
                                  "evidence": "estimate" if not (P.power.get("measured_avg_ma") or {}) else "verified"})
            if P.cost:
                t = next((t for t in P.cost.get("tiers", []) if t.get("units") == 1000), None)
                if t:
                    tiles.append({"value": money_r(t["recurring"]), "label": "Unit cost at 1,000 units, before one-time costs",
                                  "evidence": "verified" if t.get("verified_share", 0) > 0.9 else "estimate"})
        if not tiles:
            return
        def tile(t):
            num, unit = split_unit(str(t["value"]))
            v = f"<span class='num'>{E(num)}</span>" + (f" <span class='unit'>{E(unit)}</span>" if unit else "")
            return (f"<div class='tile'><div class='tile-v' data-fit>{v}</div>"
                    f"<div class='tile-l'>{with_pill(E(t['label']), ev_tag(t.get('evidence')))}</div></div>")
        h = "<div class='tiles'>" + "".join(tile(t) for t in tiles[:4]) + "</div>"
        self.add("highlights", h)

    def images(self, paths, kind):
        for p in paths:
            base = os.path.basename(p)
            cap = self.P.captions.get(base) or self.P.captions.get(os.path.splitext(base)[0], "")
            dark = re.search(r"(dark|night|led|noite|escuro)", base, re.I)
            cls = "slide-image" + (" slide-dark" if dark else "") + (" slide-drawing" if kind == "drawing" else "")
            wh = img_size(p)
            portrait = bool(wh and wh[1] > 1.15 * wh[0])
            if portrait:
                cls += " slide-portrait"
            fig = (f'<figure{" class=fig-portrait" if portrait else ""}><img src="{self.imgs.src(p)}" alt="{E(cap or base)}" loading="lazy">'
                   + (f"<figcaption>{inline_md(cap)}</figcaption>" if cap else "") + "</figure>")
            self.add(f"{kind}-{os.path.splitext(base)[0]}", fig, cls)

    def architecture(self):
        P = self.P
        paras = paragraphs(re.sub(r"```.*?```", "", P.arch_md, flags=re.S))
        meta = re.compile(r"^\W*(issue|status|date|inputs?|owner|code|applicability|verification|revision|sources?)\b", re.I)
        paras = [x for x in paras if not meta.match(x) and len(x) > 40]
        note = first_sentences(P.deck.get("architecture_note") or (paras[0] if paras else ""))
        if P.arch_img:
            art = f'<img class="diagram" src="{self.imgs.src(P.arch_img)}" alt="Architecture">'
        else:
            g = parse_mermaid(P.arch_md)
            if not g:
                return
            art = flow_svg(g)
        self.add("architecture", f"<h2>What is inside</h2><div class='diagram-wrap'>{art}</div>" +
                 (f"<p class='note'>{inline_md(note)}</p>" if note else ""))

    def components(self):
        rows = self.P.bom
        if not rows:
            return
        per = int(self.P.deck.get("components_per_slide", 5))
        pages = [rows[i:i + per] for i in range(0, len(rows), per)]
        for n, page in enumerate(pages):
            trs = []
            for r in page:
                mpn = (r.get("mpn") or "").strip()
                maker = (r.get("manufacturer") or "").strip()
                pkg = (r.get("package") or "").strip()
                qty = (r.get("qty") or "1").strip()
                prices = []
                for k in ("price_1", "price_100", "price_1k"):
                    try:
                        prices.append(money(float(r.get(k) or "")))
                    except ValueError:
                        prices.append("—")
                where = buy_links(r.get("distributors") or "", mpn, r.get("lcsc") or "",
                                  fake=mpn.upper().startswith("EXAMPLE"))
                alts_all = [a.strip() for a in re.split(r";", r.get("alternatives") or "") if a.strip()]
                # the table shows the part numbers only; the reasons stay in the dossier
                short = [re.sub(r"\s*[\(\[].*$", "", a).strip() or a for a in alts_all]
                alts = [a if len(a) <= 40 else a[:38].rsplit(" ", 1)[0] + "…" for a in short[:2]]
                if len(alts_all) > 2:
                    alts.append(f"+{len(alts_all) - 2} more in the dossier")
                trs.append(
                    f"<tr><td><strong>{E(r.get('function') or '')}</strong><span class='sub'>{E(r.get('ref') or '')}"
                    f"{' × ' + E(qty) if qty not in ('', '1') else ''}</span></td>"
                    f"<td>{E(mpn)}<span class='sub'>{E(maker)}{' · ' + E(pkg) if pkg else ''}</span></td>"
                    + "".join(f"<td class='n'>{p}</td>" for p in prices) +
                    f"<td class='buy'>{where or '—'}</td><td class='alts'>{'<br>'.join(E(a) for a in alts) or '—'}</td>"
                    f"<td>{ev_tag(r.get('evidence'), r.get('evidence') or '')}</td></tr>")
            title = "Components" + (f" <span class='count'>{n + 1}/{len(pages)}</span>" if len(pages) > 1 else "")
            date = next((r.get("source_date") for r in rows if r.get("source_date")), "")
            self.add(f"components-{n + 1}",
                     f"<h2>{title}</h2><table class='t t-bom'><thead><tr><th>Function</th><th>Part</th>"
                     "<th class='n'>1 pc</th><th class='n'>100</th><th class='n'>1k</th><th>Where to buy</th>"
                     "<th>Alternatives</th><th></th></tr></thead><tbody>" + "".join(trs) + "</tbody></table>"
                     + (f"<p class='note'>Unit prices in USD, checked {E(date)}.</p>" if date else ""))

    def power(self):
        pw = self.P.power
        if not pw or not pw.get("scenarios"):
            return
        target = pw.get("target_runtime_h")
        bat = pw.get("battery", {})
        scen = [s for s in pw["scenarios"] if s.get("runtime_new_h")]
        if not scen:
            return
        top_h = max([s["runtime_new_h"] for s in scen] + [target or 0])
        uname, uh = time_unit(top_h)
        ticks = nice_ticks(top_h / uh, STEPS[uname])
        def span(lo, hi):
            d = 0 if hi >= 10 else 1
            return f"{hi:.{d}f} {uname}" if abs(hi - lo) < 0.05 * hi else f"{lo:.{d}f}–{hi:.{d}f} {uname}"
        rows = []
        for s in scen:
            new, eol = s["runtime_new_h"], s.get("runtime_eol_h") or s["runtime_new_h"]
            meets = target is None or eol >= target
            rows.append(dict(label=s["scenario"].capitalize(), lo=eol / uh, hi=new / uh, text=span(eol / uh, new / uh),
                             emph=meets, track=True,
                             tip=f"{s['scenario'].capitalize()}: {human_hours(new)} with a new cell, {human_hours(eol)} at end of life, "
                                 f"{s['avg_ma']:g} mA average" + ("" if target is None else (" · meets target" if meets else " · below target"))))
        legend = [("Meets the target at end of life", True), ("Below the target", False)] if target else None
        chart = hbar_chart(rows, ticks, lambda v: f"{v:g}", axis_unit=uname, target=target / uh if target else None,
                           target_label=f"Target · {human_hours(target)}" if target else "", legend=legend)
        base = next((s for s in scen if s.get("scenario") == "baseline"), scen[0])
        cap = f"{bat['rated_mah']:g} mAh cell" if bat.get("rated_mah") else "one cell"
        bl, bh = (base.get("runtime_eol_h") or base["runtime_new_h"]) / uh, base["runtime_new_h"] / uh
        title = f"{base['scenario'].capitalize()} lasts {span(bl, bh)} on a {cap}"
        sub = []
        if bat.get("nominal_v"):
            sub.append(f"{bat['nominal_v']:g} V")
        if bat.get("usable_fraction"):
            sub.append(f"{bat['usable_fraction']:.0%} usable")
        sub.append("range: end of life to new cell")
        sub.append("measured on hardware" if pw.get("measured_avg_ma") else "not measured yet")
        checks = "".join(
            f"<li>{chip(('good', '✓', 'Within limit') if L['ok'] else ('bad', '✕', 'Exceeds limit'))}"
            f"<span>{E(L['name'])}: worst-case {L['worst_peak_ma']:g} mA against {L['max_ma']:g} mA</span></li>"
            for L in pw.get("limits", []))
        self.add("power", f"<h2>{E(title)}</h2><p class='lede'>{E(' · '.join(sub))} "
                          f"{ev_tag('verified' if pw.get('measured_avg_ma') else 'estimate')}</p>"
                          f"<div class='chart-wrap'>{chart}</div>" + (f"<ul class='checks'>{checks}</ul>" if checks else ""))

    def doability(self):
        F, S = self.P.findings or {}, self.P.score or {}
        if not F and not S:
            return
        fs = F.get("findings", [])
        overall = S.get("overall") or F.get("overall")           # canonical: score.json `overall`
        areas = [dict(a, verdict=a.get("verdict") or a.get("status")) for a in (S.get("areas") or F.get("areas") or [])]
        if not areas:
            for a in AREA_LABEL:
                op = [f for f in fs if f.get("area") == a and f.get("status", "open") == "open"]
                v = ("BLOCKED" if any(f.get("severity") == "critical" for f in op) else
                     "FIX" if any(f.get("severity") == "major" for f in op) else
                     "GO" if any(f.get("area") == a for f in fs) or a in F.get("reviewed_areas", []) else "NOT-REVIEWED")
                areas.append({"area": a, "verdict": v})
        areas = [dict(a, verdict=LEGACY_AREA.get(a.get("verdict"), a.get("verdict"))) for a in areas]
        overall = LEGACY_OVERALL.get(overall, overall)
        if not overall:
            vs = [a["verdict"] for a in areas]
            overall = "NOT READY" if ("BLOCKED" in vs or "FIX" in vs or "NOT-REVIEWED" in vs) else "READY TO BUILD (prototype)"
        st = OVERALL.get(overall, ("none", "–", overall.title()))
        grid = "".join(f"<div class='area'><span>{E(AREA_LABEL.get(a['area'], a['area']))}</span>"
                       f"{chip(AREA_STATUS.get(a['verdict'], AREA_STATUS['NOT-REVIEWED']))}</div>" for a in areas)
        sub = []
        if self.P.maturity:
            sub.append(f"Maturity: {E(self.P.maturity)}")
        if S.get("score") is not None:
            sub.append(f"score {S['score']}/100")
        pkg = self.build_package(F, S)
        pk = "".join(f"<li>{chip(PKG_STATUS.get(i.get('status'), PKG_STATUS['missing']))}<span>{E(i['item'])}"
                     + (f"<span class='sub'>{E(i['path'])}</span>" if i.get("path") else "") + "</span></li>" for i in pkg)
        blockers = S.get("blockers") or []
        if overall == "NOT READY" and blockers:
            low = ("<h3>Before building</h3><ol class='todo'>" + "".join(
                f"<li><strong>{inline_md(b.get('title', ''))}</strong><span>{inline_md(b.get('action', ''))}"
                + (f" <span class='owner'>{E(b.get('owner'))}</span>" if b.get("owner") else "") + "</span></li>"
                for b in blockers[:4]) + "</ol>"
                + (f"<p class='note'>{len(blockers) - 4} more in the review.</p>" if len(blockers) > 4 else ""))
        elif overall == "NOT READY":
            order = {"critical": 0, "major": 1}
            todo = sorted([f for f in fs if f.get("status", "open") == "open" and f.get("severity") in order],
                          key=lambda f: order[f["severity"]])
            low = ("<h3>Before building</h3><ol class='todo'>" + "".join(
                f"<li><strong>{inline_md(f.get('title', ''))}</strong><span>{inline_md(f.get('fix') or f.get('recommendation', ''))}"
                + (f" <span class='owner'>{E(f.get('owner'))}</span>" if f.get("owner") else "") + "</span></li>" for f in todo[:4])
                + "</ol>" + (f"<p class='note'>{len(todo) - 4} more in the open findings.</p>" if len(todo) > 4 else "")) if todo else ""
        else:
            ver = [dict(measurement=v.get("what") or v.get("measurement", ""),
                        method=" · ".join(x for x in (v.get("method", ""), v.get("instrument", "")) if x),
                        **{"pass": v.get("pass_criteria") or v.get("pass", "")})
                   for v in (S.get("prototype_checks") or F.get("prototype_checks")
                             or F.get("verify_on_prototype") or S.get("verify_on_prototype") or [])]
            low = ""
            self._verify = ver
            if ver:
                low = (f"<p class='note note-next'>{len(ver)} measurement{'s' if len(ver) != 1 else ''} on the first "
                       "prototype close the remaining estimates: next slide.</p>")
        head = (f"<div class='verdict verdict-{st[0]}'><span class='verdict-i' aria-hidden='true'>{st[1]}</span>"
                f"<span>{E(st[2])}</span></div>" + (f"<p class='lede lede-tight'>{' · '.join(sub)}</p>" if sub else ""))
        self.add("doability", f"{head}<div class='cols cols-even'><div><h3>By area</h3><div class='areas'>{grid}</div></div>"
                              f"<div><h3>Build package</h3><ul class='checks checks-tight'>{pk}</ul></div></div>{low}", "slide-dense")

    def verify(self):
        ver = getattr(self, "_verify", None) or []
        if not ver:
            return
        per = 6
        pages = [ver[i:i + per] for i in range(0, len(ver), per)]
        for n, page in enumerate(pages):
            title = "Prototype checks" + (f" <span class='count'>{n + 1}/{len(pages)}</span>" if len(pages) > 1 else "")
            rows = "".join(f"<tr><td><strong>{inline_md(v.get('measurement', ''))}</strong></td>"
                           f"<td>{inline_md(v.get('method', ''))}</td><td class='pass'>{inline_md(v.get('pass', ''))}</td></tr>"
                           for v in page)
            self.add(f"verify-{n + 1}", f"<h2>{title}</h2><p class='lede lede-tight'>Each check has a method and a pass "
                     "threshold. None of them blocks building the prototype.</p><table class='t t-compact t-verify'><thead><tr>"
                     "<th>Measurement</th><th>Method and instrument</th><th>Pass</th></tr></thead><tbody>" + rows +
                     "</tbody></table>")

    def build_package(self, F, S):
        """build-package's release check first, then the review's build_package, else what the workspace holds"""
        R = self.P.release
        if R:
            failed = {i["check"] for i in R.get("items", []) if i.get("level") == "fail"}
            warned = {i["check"] for i in R.get("items", []) if i.get("level") == "warn"}
            return [dict(item=lab, status="missing" if c in failed else "partial" if c in warned else "done",
                         path=f"release {R.get('release')}" if c not in failed else None) for c, lab in RELEASE_CHECKS]
        given = S.get("build_package") or F.get("build_package")
        if isinstance(given, dict):                             # doability_score.py: {key: true/false}
            return [dict(item=DOABILITY_PKG.get(k, k), status="done" if v else "missing") for k, v in given.items()]
        if given:
            return given
        hw = self.P.hw
        def g(*pats):
            for pat in pats:
                hits = sorted(glob.glob(os.path.join(hw, pat), recursive=True))
                if hits:
                    return os.path.relpath(hits[0], os.path.dirname(os.path.abspath(hw)))
            return None
        items = []
        fab = g("pcb/**/*gerber*.zip", "pcb/**/fab/*", "pcb/**/*gerber*")
        items.append(dict(item="Routed board and fab files", status="done" if fab else "missing", path=fab))
        rows = self.P.bom
        if rows:
            def stock(r):
                m = re.match(r"\s*([\d,]+)", r.get("stock_snapshot") or "")
                return int(m.group(1).replace(",", "")) if m else None
            st = [stock(r) for r in rows]
            status = "done" if all(x and x > 0 for x in st) else "partial" if any(x and x > 0 for x in st) else "missing"
            n_out = sum(1 for x in st if not x)
            items.append(dict(item="BOM in stock", status=status, path="hw/bom.csv" + (f" · {n_out} line(s) without stock" if n_out else "")))
        else:
            items.append(dict(item="BOM in stock", status="missing"))
        for name, pats in (("Enclosure STEP", ("mech/**/*.step", "mech/**/*.stp")),
                           ("Assembly guide", ("**/assembly*.md", "**/assembly*.pdf")),
                           ("Test plan", ("**/test*plan*.md", "**/test-plan*")),
                           ("Order steps", ("**/order*.md", "cost/rfq*.md"))):
            hit = g(*pats)
            items.append(dict(item=name, status="done" if hit else "missing", path=hit))
        return items

    def risks(self):
        F = self.P.findings
        if not F:
            return
        order = {"critical": 0, "major": 1, "minor": 2, "info": 3}
        op = sorted([f for f in F.get("findings", []) if f.get("status", "open") == "open"],
                    key=lambda f: order.get(f.get("severity"), 9))
        if not op:
            return
        trs = "".join(
            f"<tr><td>{chip(SEV.get(f.get('severity'), SEV['info']))}</td><td><strong>{inline_md(f.get('title', ''))}</strong>"
            f"<span class='sub'>{E(AREA_LABEL.get(f.get('area'), f.get('area', '')))}</span></td>"
            f"<td>{inline_md(f.get('recommendation', '') or '—')}</td><td class='sub-cell'>{E(f.get('owner', ''))}</td></tr>"
            for f in op[:8])
        fixed = [f for f in F.get("findings", []) if f.get("status") in ("fixed", "accepted")]
        note = f"<p class='note'>{len(fixed)} more finding{'s' if len(fixed) != 1 else ''} already fixed or accepted.</p>" if fixed else ""
        self.add("risks", "<h2>Open findings</h2><table class='t'><thead><tr><th>Severity</th><th>Finding</th>"
                          "<th>Change</th><th>Owner</th></tr></thead><tbody>" + trs + "</tbody></table>" + note)

    def cost(self):
        C = self.P.cost
        if not C or not C.get("tiers"):
            return
        tiers = C["tiers"]
        rows = [dict(label=f"{t['units']:,}", lo=t["recurring"][0], hi=t["recurring"][1], text=money_r(t["recurring"]),
                     tip=f"{t['units']:,} units: {money_r(t['recurring'])} per unit before one-time costs; {money_r(t['total'])} with them")
                for t in tiers]
        lo_all = min(r["lo"] for r in rows if r["lo"] > 0)
        hi_all = max(r["hi"] for r in rows)
        ticks = [10 ** e for e in range(math.floor(math.log10(lo_all)), math.ceil(math.log10(hi_all)) + 1)]
        if len(ticks) < 2:
            ticks.append(ticks[-1] * 10)
        chart = hbar_chart(rows, ticks, lambda v: f"${v:,.0f}" if v >= 1 else f"${v:g}", log=True,
                           width=1000, label_w=110, row_h=50)
        dest = tiers[0]["landed"][0]["name"] if tiers[0].get("landed") else None
        trs = "".join(
            f"<tr><td>{t['units']:,}</td><td class='n'>{money_r(t['recurring'])}</td><td class='n'>{money_r(t['nre_per_unit'])}</td>"
            f"<td class='n strong'>{money_r(t['total'])}</td>"
            + (f"<td class='n'>{money_r(t['landed'][0]['per_unit'])}</td>" if dest else "") + "</tr>"
            for t in tiers)
        tbl = ("<table class='t t-cost'><thead><tr><th>Units</th><th class='n'>Per unit</th><th class='n'>One-time, per unit</th>"
               "<th class='n'>Total per unit</th>" + (f"<th class='n'>Landed, {E(dest)}</th>" if dest else "") +
               "</tr></thead><tbody>" + trs + "</tbody></table>")
        k = next((t for t in tiers if t["units"] == 1000), tiers[-1])
        vs = k.get("verified_share")
        note = (f"Per unit, before one-time costs. Ranges are low–high, USD{', ' + E(C.get('date')) if C.get('date') else ''}. "
                "Logarithmic axis; units per order on the left. "
                + (f"{vs:.0%} of the {k['units']:,}-unit cost rests on verified prices." if vs is not None else ""))
        self.add("cost", f"<h2>{money_r(k['recurring'])} per unit at {k['units']:,} units</h2>"
                         f"<div class='chart-wrap'>{chart}</div><p class='note'>{note}</p>")
        self.add("cost-table", f"<h2>{money_r(k['total'])} per unit at {k['units']:,}, one-time costs included</h2>{tbl}"
                               + ("<p class='note'>Landed: duty, tax and freight to the destination, on top of the total.</p>" if dest else ""))

    def nre(self):
        C = self.P.cost
        if not C or not C.get("tiers"):
            return
        want = self.P.deck.get("nre_tier", 1000)
        t = next((t for t in C["tiers"] if t["units"] == want), C["tiers"][-1])
        items = t.get("nre_items", [])
        if not items:
            return
        items = sorted(items, key=lambda i: -(rng(i["value"]) or (0, 0))[1])
        trs = "".join(f"<tr><td>{E(i['name'])}</td><td class='sub-cell'>{E(i.get('group', ''))}</td>"
                      f"<td class='n'>{money_r(i['value'])}</td><td>{ev_tag(i.get('evidence'))}</td></tr>" for i in items)
        self.add("nre", f"<h2>{money_r(t['nre'])} one-time to reach {t['units']:,} units</h2>"
                        "<table class='t'><thead><tr><th>Item</th><th>Group</th><th class='n'>Cost</th><th></th></tr></thead>"
                        f"<tbody>{trs}</tbody></table>")

    def compliance(self):
        tabs = md_tables(self.P.compliance)
        summ = next(((h, r) for h, r in tabs if h and h[0].lower().startswith("scope")), None)
        if not summ:
            return
        h, rows = summ
        trs = "".join(f"<tr><td>{inline_md(r[0])}</td><td class='n'>{E(r[2] if len(r) > 2 else '')}</td>"
                      f"<td class='n'>{E(r[3] if len(r) > 3 else '')}</td></tr>" for r in rows)
        flags = re.findall(r"^-\s+\*\*(BLOCKING|DESIGN RISK|CRITICAL PATH):\*\*\s*(.+)$", self.P.compliance, re.M)
        fl = "".join(f"<li>{chip(('bad', '✕', 'Blocking') if k == 'BLOCKING' else ('warn', '!', k.capitalize()))}<span>{inline_md(v)}</span></li>"
                     for k, v in flags[:5])
        self.add("compliance", "<h2>Certifications</h2><div class='cols'><table class='t'><thead><tr><th>Market</th>"
                               "<th class='n'>Cost (USD)</th><th class='n'>Longest lead (weeks)</th></tr></thead><tbody>"
                               + trs + "</tbody></table>" + (f"<ul class='checks'>{fl}</ul>" if fl else "") + "</div>"
                               "<p class='note'>Planning ranges, not quotes. Confirm each row with an accredited lab before relying on it.</p>")

    def roadmap(self):
        tabs = md_tables(self.P.schedule)
        st = next(((h, r) for h, r in tabs if h and h[0].lower().startswith("stage")), None)
        if not st:
            if self.P.timeline_svg:                 # prototype-roadmap's own timeline, when schedule.md has no table
                svg = re.sub(r"<\?xml[^>]*>", "", read(self.P.timeline_svg) or "")
                self.add("roadmap", f"<h2>Roadmap</h2><div class='figure'>{svg}</div>")
            return
        h, rows = st
        def dates(cell):
            ds = re.findall(r"\d{4}-\d{2}-\d{2}", cell)
            return [dt.date.fromisoformat(d) for d in ds]
        items = []
        for r in rows:
            if len(r) < 5:
                continue
            s, e = dates(r[2]), dates(r[3])
            if len(s) < 2 or len(e) < 2:
                continue
            name = re.sub(r"\*\*(.+?)\*\*", r"\1", r[0]).strip()
            items.append(dict(name=name, sb=s[0], sw=s[1], eb=e[0], ew=e[1], gate=r[4], crit=(r[5].strip().lower() == "yes") if len(r) > 5 else False))
        if not items:
            return
        t0 = min(i["sb"] for i in items)
        t1 = max(i["ew"] for i in items)
        span = max(1, (t1 - t0).days)
        W, rh = 1280, 40
        lw = int(min(W * 0.4, max(text_w(i['name'], 16) for i in items) + 34))
        pw_ = W - lw - 30
        X = lambda d: lw + (d - t0).days / span * pw_
        H = len(items) * rh + 50
        o = [f'<svg class="chart" viewBox="0 0 {W} {H}" width="100%" role="img">']
        m = dt.date(t0.year, t0.month, 1)
        while m <= t1:
            if m >= t0:
                x = X(m)
                o.append(f'<line class="grid" x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{H - 30}"/>')
                if m.month in (1, 4, 7, 10):
                    lab = m.strftime("%b %Y")
                    anchor = "end" if x + text_w(lab, 13) > W - 4 else "start"
                    o.append(f'<text class="tick" x="{x + (4 if anchor == "start" else -4):.1f}" y="{H - 10}" text-anchor="{anchor}">{lab}</text>')
            m = dt.date(m.year + (m.month // 12), m.month % 12 + 1, 1)
        for k, i in enumerate(items):
            y = k * rh + 10
            o.append(f'<text class="cat" x="{lw - 14}" y="{y + 15}" text-anchor="end">{E(i["name"])}</text>')
            xb0, xb1, xw1 = X(i["sb"]), X(i["eb"]), X(i["ew"])
            cls = "bar" if i["crit"] else "bar bar-muted"
            tip = f"{i['name']}: {i['sb']} to {i['eb']} (best) · ends by {i['ew']} (worst) · gate: {i['gate']}"
            o.append(f'<g class="mark" tabindex="0" data-tip="{E(tip)}"><rect class="hit" x="{lw}" y="{y - 6}" width="{pw_}" height="{rh - 4}"/>'
                     f'<rect class="{cls} bar-range" x="{X(i["sw"]):.1f}" y="{y + 4}" width="{max(3, xw1 - X(i["sw"])):.1f}" height="12" rx="4"/>'
                     f'<rect class="{cls}" x="{xb0:.1f}" y="{y}" width="{max(4, xb1 - xb0):.1f}" height="20" rx="4"/></g>')
        o.append("</svg>")
        finish = re.search(r"\*\*Finish:\*\*\s*(.+)", self.P.schedule)
        miles = next(((hh, rr) for hh, rr in tabs if hh and hh[0].lower().startswith("milestone")), None)
        ml = ""
        if miles:
            ml = "<ul class='milestones'>" + "".join(f"<li><strong>{E(r[0])}</strong><span>{E(r[2] if len(r) > 2 else '')}</span></li>" for r in miles[1]) + "</ul>"
        legend = ("<div class='legend'><span><i class='key key-bar'></i>Critical path</span><span><i class='key key-muted'></i>Other stages</span>"
                  "<span><i class='key key-range'></i>Worst case</span></div>")
        title = "Roadmap" + (f": {inline_md(finish.group(1).split(',')[0].rstrip('.'))}" if finish else "")
        self.add("roadmap", f"<h2>{title}</h2>{legend}{''.join(o)}{ml}")

    def next_steps(self):
        steps = list(self.P.deck.get("next_steps", []))
        if not steps:
            body = ""
            for name, b in md_sections(self.P.report).items():
                if name.startswith(("must be measured", "next", "rfq")):
                    body = b
                    break
            steps = [re.sub(r"^\s*(?:[-*]|\d+\.)\s+(\[ \]\s*)?", "", l).strip() for l in body.splitlines()
                     if re.match(r"^\s*(?:[-*]|\d+\.)\s+", l)]
        if not steps:
            return
        self.add("next", "<h2>Next steps</h2><ol class='steps'>" + "".join(f"<li>{inline_md(s)}</li>" for s in steps[:8]) + "</ol>")

    def pending(self):
        """Honest state for inputs that do not exist yet. No placeholder art."""
        P = self.P
        miss = []
        if not P.renders:
            miss.append(("Product renders", "product-render", "hw/renders/hero.png, desk.png, dark.png, exploded.png, lineup.png"))
        if not P.drawings:
            miss.append(("Exploded technical drawing", "technical-drawing", "hw/drawings/blueprint.svg"))
        if not P.arch_img and not parse_mermaid(P.arch_md):
            miss.append(("Architecture diagram", "specs-engineer", "hw/architecture.md (Mermaid flowchart) or hw/architecture.svg"))
        if not P.bom:
            miss.append(("Components", "specs-engineer, electronics-researcher", "hw/bom.csv"))
        if not P.power:
            miss.append(("Battery life", "battery-and-power", "hw/power/budget.json"))
        if not P.findings and not P.score:
            miss.append(("Doability review", "doability-review", "hw/doability/findings.json"))
        if not P.cost:
            miss.append(("Cost per unit", "cost-and-sourcing", "hw/cost/model.json"))
        if not md_tables(P.compliance):
            miss.append(("Certifications", "compliance-planner", "hw/compliance/matrix.md"))
        if not md_tables(P.schedule):
            miss.append(("Roadmap", "prototype-roadmap", "hw/roadmap/schedule.md"))
        if not miss:
            return
        trs = "".join(f"<tr><td><strong>{E(a)}</strong></td><td>{E(b)}</td><td class='sub-cell'><code>{E(c)}</code></td></tr>" for a, b, c in miss)
        self.add("pending", "<h2>Not produced yet</h2><table class='t'><thead><tr><th>Part of this review</th><th>Produced by</th>"
                            "<th>Expected file</th></tr></thead><tbody>" + trs + "</tbody></table>")

    def sources(self):
        rows = self.P.bom
        counts = {"verified": 0, "estimate": 0, "assumption": 0}
        for r in rows:
            k = norm_ev(r.get("evidence"))
            if k:
                counts[k] += 1
        if not rows and not self.P.cost:
            return
        legend = ("<dl class='facts facts-legend'>"
                  f"<dt>{ev_tag('verified')}</dt><dd>Read from a named source in this review, with its date.</dd>"
                  f"<dt>{ev_tag('estimate')}</dt><dd>Calculated or inferred; the basis is stated next to the number.</dd>"
                  f"<dt>{ev_tag('assumption')}</dt><dd>Chosen for planning. A measurement or a quote must replace it.</dd></dl>")
        tally = ""
        if rows:
            tally = (f"<p class='lede'>Components: {counts['verified']} verified · {counts['estimate']} estimated · "
                     f"{counts['assumption']} assumed</p>")
        self.add("sources", f"<h2>How to read the numbers</h2>{tally}{legend}")


DIST_NAMES = {"digikey": "DigiKey", "mouser": "Mouser", "lcsc": "LCSC", "jlcpcb": "JLCPCB", "arrow": "Arrow",
              "farnell": "Farnell", "newark": "Newark", "tme": "TME", "octopart": "Octopart", "ti": "TI",
              "rs": "RS", "avnet": "Avnet", "future": "Future"}


def _dist_name(d):
    k = re.sub(r"[^a-z]", "", d.lower())
    return DIST_NAMES.get(k, d.strip()[:18])


def buy_links(field, mpn, lcsc="", fake=False):
    """'Name=URL; Name: URL; URL; Name' -> short link labels, never a raw URL. A JLCPCB basic/extended note
    becomes a small badge."""
    links, badge, seen = [], "", set()
    for d in re.split(r"[;|]", field):
        d = d.strip()
        if not d:
            continue
        url = None
        mm = re.match(r"^(.*?)\s*[=:]\s*(https?://\S+)$", d) or re.match(r"^(.*?)\s+(https?://\S+)$", d)
        if mm:
            name, url = mm.group(1).strip(), mm.group(2)
        elif d.lower().startswith("http"):
            url = d
            name = re.sub(r"^https?://(www\.)?([^/.]+).*", r"\2", d, flags=re.I)
        else:
            name = re.split(r"\s*[=:]\s*", d, maxsplit=1)[0]
            rest = d[len(name):]
            if re.search(r"\b(basic|extended|preferred)\b", d, re.I) and "jlc" in d.lower():
                kind = re.search(r"\b(basic|extended|preferred)\b", d, re.I).group(1).lower()
                badge = f"<span class='badge badge-{kind}' title='{E(d)}'>JLC {kind}</span>"
                continue
            if not fake and mpn:
                url = search_url(name, mpn)
        label = _dist_name(name or "link")
        if label.lower() in seen:
            continue
        seen.add(label.lower())
        links.append(f'<a href="{E(url)}">{E(label)}</a>' if url else E(label))
    if lcsc and lcsc.strip() not in ("", "-") and "lcsc" not in seen and not fake:
        links.append(f'<a href="https://www.lcsc.com/product-detail/{E(lcsc.strip())}.html">LCSC</a>')
    return " · ".join(links) + (f" {badge}" if badge else "")


def search_url(dist, mpn):
    d = dist.lower().replace("-", "").replace(" ", "")
    q = mpn.replace(" ", "+")
    return {"digikey": f"https://www.digikey.com/en/products/result?keywords={q}",
            "mouser": f"https://www.mouser.com/c/?q={q}",
            "lcsc": f"https://www.lcsc.com/search?q={q}",
            "octopart": f"https://octopart.com/search?q={q}",
            "arrow": f"https://www.arrow.com/en/products/search?q={q}",
            "farnell": f"https://www.farnell.com/search?st={q}",
            "newark": f"https://www.newark.com/search?st={q}",
            "tme": f"https://www.tme.eu/en/katalog/?search={q}"}.get(d)


# ------------------------------------------------------------------ page
CSS = r"""
:root{--paper:#F7F6F2;--surface:#FAFAF7;--ink:#15171A;--ink-2:#55595F;--muted:#8A8E95;--hair:#E2E0D9;--axis:#C9C6BD;
--accent:#FF6A13;--series:#E8590C;--series-muted:#C9C6BD;--good:#0ca30c;--warn:#fab219;--bad:#d03b3b;--none:#8A8E95;
--dark-bg:#0E0F11;--tip-bg:#15171A;--tip-ink:#F7F6F2;color-scheme:light}
:root[data-theme=dark]{--paper:#0E0F11;--surface:#141517;--ink:#F2F1EC;--ink-2:#B9BCC2;--muted:#8A8E95;--hair:#26282C;--axis:#3A3C40;
--series:#E8661C;--series-muted:#4A4C51;--tip-bg:#F2F1EC;--tip-ink:#15171A;color-scheme:dark}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--paper:#0E0F11;--surface:#141517;--ink:#F2F1EC;--ink-2:#B9BCC2;
--hair:#26282C;--axis:#3A3C40;--series:#E8661C;--series-muted:#4A4C51;--tip-bg:#F2F1EC;--tip-ink:#15171A;color-scheme:dark}}
*{box-sizing:border-box}html{scroll-snap-type:y mandatory}
body{margin:0;background:var(--paper);color:var(--ink);font:400 20px/1.45 "Inter",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
-webkit-font-smoothing:antialiased;font-feature-settings:"ss01","cv11"}
a{color:inherit;text-decoration:underline;text-decoration-color:var(--axis);text-underline-offset:3px}a:hover{text-decoration-color:var(--accent)}
.slide{position:relative;min-height:100vh;display:flex;align-items:center;padding:8vh 7vw 10vh;scroll-snap-align:start;overflow:hidden}
.frame{width:100%;max-width:1480px;margin:0 auto}
footer{position:absolute;left:7vw;right:7vw;bottom:4vh;display:flex;justify-content:space-between;font-size:14px;color:var(--muted);letter-spacing:.01em}
h1{font-size:clamp(56px,8vw,132px);line-height:.98;letter-spacing:-.035em;font-weight:650;margin:0}
h2{font-size:clamp(34px,3.6vw,60px);line-height:1.06;letter-spacing:-.025em;font-weight:620;margin:0 0 .9em;max-width:22ch}
h2 .count{color:var(--muted);font-weight:450}
.meta{color:var(--ink-2);font-size:20px;margin:1.4em 0 0}
.lede{color:var(--ink-2);font-size:22px;margin:-.6em 0 1.4em}
.note{color:var(--muted);font-size:15px;margin:1.6em 0 0;max-width:110ch}
.sub{display:block;color:var(--muted);font-size:14px;margin-top:2px}.sub-cell{color:var(--muted);font-size:15px}
.cover{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:5vw;align-items:center}
.cover-solo{grid-template-columns:1fr}.cover-img{width:100%;max-height:72vh;object-fit:contain;border-radius:22px}.cover-crop{aspect-ratio:4/5;height:min(78vh,820px);width:auto;max-width:100%;max-height:none;object-fit:cover;justify-self:center}.fig-portrait{display:grid;grid-template-columns:minmax(0,auto) minmax(260px,440px);justify-content:center;align-items:center;gap:56px;height:80vh}.fig-portrait img{height:80vh;width:auto;max-width:100%;justify-self:end}.fig-portrait figcaption{max-width:30ch;font-size:22px;line-height:1.4}.slide-drawing figure img{width:auto;max-width:100%;margin:0 auto}.t-verify{margin-top:28px}.t-verify td{vertical-align:top}.t-verify .pass{white-space:normal;color:var(--ink)}.note-next{margin-top:28px}
.statement p{font-size:clamp(34px,3.4vw,58px);line-height:1.15;letter-spacing:-.022em;font-weight:560;margin:0 0 .6em;max-width:24ch}
.statement p+p{color:var(--ink-2);font-weight:450}
.cols{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:4vw;align-items:start}
.cols-verdict{grid-template-columns:minmax(0,4fr) minmax(0,6fr);align-items:center}
.cols-cost{grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:center}
.facts{display:grid;grid-template-columns:max-content 1fr;gap:14px 28px;margin:0}
.facts dt{color:var(--muted);font-size:16px;padding-top:3px}.facts dd{margin:0}
.facts-legend{max-width:70ch;gap:20px 28px}.facts-legend dt{padding-top:1px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:48px clamp(32px,4vw,64px)}
.tile{min-width:0;border-top:1px solid var(--hair);padding-top:28px}
.tile-v{min-width:0;white-space:nowrap;overflow:hidden;font-size:clamp(36px,4vw,72px);font-weight:620;letter-spacing:-.03em;line-height:1.04;padding-bottom:.06em}
.tile-v .unit{font-size:.5em;font-weight:500;letter-spacing:-.01em;color:var(--ink-2)}
.tile-v.wrap{white-space:normal;overflow:visible}.tile-v.wrap .unit{display:block;margin-top:.25em}
.tile-l{color:var(--ink-2);font-size:18px;margin-top:16px;overflow-wrap:anywhere}
.nowrap{white-space:nowrap}.ev{vertical-align:.12em}
figure{margin:0;display:flex;flex-direction:column;gap:22px;height:78vh;justify-content:center}
figure img{width:100%;height:100%;min-height:0;object-fit:contain;border-radius:18px}
figcaption{font-size:22px;color:var(--ink-2);max-width:60ch}
.slide-dark{background:var(--dark-bg);--ink:#F2F1EC;--ink-2:#B9BCC2;color:var(--ink)}
.slide-drawing figure img{background:#fff;border-radius:6px}
.t{width:100%;border-collapse:collapse;font-size:17px}
.t th{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600;text-align:left;padding:0 14px 12px 0;border-bottom:1px solid var(--axis)}
.t code{font-size:.88em;color:var(--ink-2)}.t td{padding:14px 14px 14px 0;border-bottom:1px solid var(--hair);vertical-align:top}
.t .n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}.t .strong{font-weight:620}
.t-bom{font-size:15.5px;table-layout:fixed;width:100%}.t-bom td{overflow-wrap:anywhere}.t-bom td{padding:11px 12px 11px 0}.t-bom .alts{color:var(--ink-2);font-size:14px}
.t-compact td{font-size:16px}
.ev{display:inline-block;font-size:11.5px;letter-spacing:.04em;color:var(--muted);border:1px solid var(--hair);border-radius:99px;padding:0 7px;line-height:18px;vertical-align:2px;white-space:nowrap}
.ev-verified{color:var(--ink-2);border-color:var(--axis)}
.chip{display:inline-flex;align-items:center;gap:7px;font-size:14.5px;font-weight:560;white-space:nowrap}
.chip-i{display:inline-grid;place-items:center;width:20px;height:20px;border-radius:50%;font-size:12px;font-weight:800;color:#fff;background:var(--none)}
.chip-good .chip-i{background:var(--good)}.chip-warn .chip-i{background:var(--warn);color:#15171A}.chip-bad .chip-i{background:var(--bad)}
h3{font-size:14px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600;margin:0 0 10px}
.slide-dense .verdict{font-size:clamp(36px,3.6vw,60px)}.slide-dense h3{margin-top:26px}
.lede-tight{margin:.7em 0 0}.cols-even{grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:4vw}
.slide-dense .area{padding:9px 0;font-size:16px}.checks-tight{margin:0;gap:6px}.checks-tight li{font-size:16px;align-items:center}
.checks-tight .chip{min-width:96px}.checks .sub{display:inline;margin-left:10px}
.todo{margin:0;padding-left:1.2em;display:grid;gap:8px;font-size:16px;max-width:120ch}.todo span{display:block;color:var(--ink-2)}
.owner{display:inline!important;color:var(--muted);font-size:14px;margin-left:6px}
.verdict{display:flex;align-items:center;gap:22px;font-size:clamp(40px,4.4vw,74px);font-weight:640;letter-spacing:-.03em;line-height:1}
.verdict-i{display:grid;place-items:center;width:1.25em;height:1.25em;border-radius:50%;font-size:.62em;color:#fff;background:var(--none);flex:none}
.verdict-good .verdict-i{background:var(--good)}.verdict-warn .verdict-i{background:var(--warn);color:#15171A}.verdict-bad .verdict-i{background:var(--bad)}
.verdict+.lede{margin:1em 0 0}
.areas{display:grid;grid-template-columns:1fr 1fr;gap:0 40px}
.area{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:15px 0;border-bottom:1px solid var(--hair);font-size:18px}
.checks{list-style:none;padding:0;margin:28px 0 0;display:grid;gap:12px}.checks li{display:flex;gap:14px;align-items:baseline;font-size:17px}
.steps{margin:0;padding:0;list-style:none;counter-reset:s;display:grid;gap:18px;max-width:80ch}
.steps li{counter-increment:s;display:grid;grid-template-columns:48px 1fr;font-size:22px;padding-bottom:18px;border-bottom:1px solid var(--hair)}
.steps li::before{content:counter(s);color:var(--accent);font-weight:650;font-variant-numeric:tabular-nums}
.milestones{list-style:none;padding:0;margin:18px 0 0;display:flex;gap:48px;flex-wrap:wrap;font-size:17px}
.milestones span{display:block;color:var(--muted);font-size:15px;font-variant-numeric:tabular-nums}
.legend{display:flex;gap:28px;font-size:15px;color:var(--ink-2);margin:-1.2em 0 18px}
.key{display:inline-block;width:16px;height:10px;border-radius:3px;margin-right:8px;vertical-align:0}
.key-bar{background:var(--series)}.key-muted{background:var(--series-muted)}.key-range{background:var(--series);opacity:.35}
.diagram-wrap{width:100%}.diagram{width:100%;max-height:62vh;object-fit:contain}
.chart{display:block;overflow:visible}.chart-wrap{max-width:1100px}
.chart text{fill:var(--ink);font-size:var(--fs,16px);font-family:inherit;font-variant-numeric:tabular-nums}
.chart .tick{fill:var(--muted);font-size:13px}
.chart .cat{fill:var(--ink-2)}.chart .val{fill:var(--ink);font-weight:560}
.chart .val,.chart .tick,.chart .target-label{paint-order:stroke;stroke:var(--paper);stroke-width:6px;stroke-linejoin:round}
.chart .val-in{fill:#fff;stroke:none}
.chart .target-label{fill:var(--ink-2);font-size:14px;font-weight:600}
.chart .legend-t{fill:var(--ink-2);font-size:14px}
.chart .grid{stroke:var(--hair);stroke-width:1}.chart .axis{stroke:var(--axis);stroke-width:1}
.chart .target{stroke:var(--ink-2);stroke-width:1.5;stroke-dasharray:5 4}
.chart .bar{fill:var(--series)}.chart .bar-muted{fill:var(--series-muted)}.chart .track{opacity:.45}.chart .bar-range{opacity:.35}
.chart .hit{fill:transparent}.chart .mark{outline:none;cursor:default}
.chart .mark:hover .bar,.chart .mark:focus .bar{filter:brightness(1.12)}
.chart .mark:focus-visible .hit{stroke:var(--accent);stroke-width:1.5}
.flow .node{fill:var(--surface);stroke:var(--axis);stroke-width:1.2}.flow .node.hub{stroke:var(--accent)}
.flow .node-label{fill:var(--ink);font-weight:520}.flow .edge{fill:none;stroke:var(--axis);stroke-width:1.6}
.flow .arrow{fill:var(--axis)}.flow .edge-label{fill:var(--muted);font-size:13px;paint-order:stroke;stroke:var(--paper);stroke-width:4px;stroke-linejoin:round}.flow .node-label{font-size:15px}.flow .node-sub{fill:var(--ink-2);font-weight:400;font-size:13.5px}.flow .edge-u{stroke-dasharray:3 4}.t-bom .buy a{white-space:nowrap}.badge{display:inline-block;font-size:11.5px;line-height:1;padding:4px 7px;border-radius:999px;border:1px solid var(--hair);color:var(--muted);vertical-align:1px;white-space:nowrap;margin-left:4px}.badge-basic,.badge-preferred{color:var(--good,#2f8f4e);border-color:currentColor}
#tip{position:fixed;pointer-events:none;background:var(--tip-bg);color:var(--tip-ink);font-size:14px;line-height:1.35;padding:9px 12px;border-radius:8px;max-width:420px;opacity:0;transition:opacity .08s;z-index:9}
#theme{position:fixed;top:18px;right:20px;z-index:8;font:inherit;font-size:13px;color:var(--ink-2);background:transparent;border:1px solid var(--hair);border-radius:99px;padding:5px 12px;cursor:pointer}
#theme:hover{border-color:var(--axis)}
body.solo #theme{display:none}body.solo .slide{display:none}body.solo .slide.on{display:flex;min-height:100vh}
@page{size:1600px 900px;margin:0}
@media print{html{scroll-snap-type:none}#theme,#tip{display:none}.slide{height:900px;min-height:0;page-break-after:always;break-after:page;padding:64px 100px 80px}
figure{height:700px}footer{bottom:30px;left:100px;right:100px}body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
@media (max-width:1100px){.cols,.cols-cost,.cols-verdict,.cols-even{grid-template-columns:1fr;gap:40px}.cover{grid-template-columns:1fr;gap:40px}}
@media (max-width:900px){body{font-size:17px}.slide{padding:72px 24px 88px;align-items:flex-start}footer{left:24px;right:24px;bottom:28px}
.areas{grid-template-columns:1fr}figure{height:auto}figure img{height:auto;max-height:70vh}.fig-portrait{grid-template-columns:1fr;height:auto;gap:22px}.fig-portrait img{height:auto;max-height:70vh;width:100%;object-fit:contain;justify-self:center}.fig-portrait figcaption{max-width:none;font-size:17px}.cover-crop{height:auto;width:100%;max-height:70vh}
.t thead{display:none}.t,.t tbody,.t tr,.t td{display:block;width:100%}
.t tr{padding:14px 0;border-bottom:1px solid var(--hair)}.t td{border:0;padding:3px 0;text-align:left!important;white-space:normal!important}
.t td[data-label]:not([data-label=""])::before{content:attr(data-label);display:block;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-top:6px}
.t td:first-child::before{display:none!important}.facts{grid-template-columns:1fr;gap:4px}.facts dd{margin-bottom:12px}
.steps li{grid-template-columns:36px 1fr;font-size:19px}h2{max-width:none}.legend{flex-wrap:wrap;gap:12px 24px}
.milestones{gap:20px}.checks li{flex-wrap:wrap}.tile-v{font-size:clamp(34px,10vw,56px)}}
"""

JS = r"""
const fit=()=>document.querySelectorAll('[data-fit]').forEach(el=>{el.classList.remove('wrap');el.style.fontSize='';
let f=parseFloat(getComputedStyle(el).fontSize);const floor=Math.max(26,f*0.55);
while(el.scrollWidth>el.clientWidth+1&&f>floor){f-=1;el.style.fontSize=f+'px'}
if(el.scrollWidth>el.clientWidth+1)el.classList.add('wrap')});
fit();addEventListener('load',fit);addEventListener('resize',fit);document.fonts&&document.fonts.ready.then(fit);
(()=>{const root=document.documentElement,b=document.getElementById('theme');
const set=t=>{if(t)root.dataset.theme=t;else delete root.dataset.theme;b.textContent=(t||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'))==='dark'?'Light':'Dark'};
set(new URLSearchParams(location.search).get('theme')||root.dataset.theme);
b.onclick=()=>set((root.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'))==='dark'?'light':'dark');
const tip=document.getElementById('tip');
const show=(el,x,y)=>{tip.textContent=el.dataset.tip;tip.style.opacity=1;const r=tip.getBoundingClientRect();
tip.style.left=Math.min(innerWidth-r.width-12,x+14)+'px';tip.style.top=Math.max(8,y-r.height-12)+'px'};
document.querySelectorAll('[data-tip]').forEach(el=>{el.addEventListener('pointermove',e=>show(el,e.clientX,e.clientY));
el.addEventListener('pointerleave',()=>tip.style.opacity=0);el.addEventListener('focus',()=>{const r=el.getBoundingClientRect();show(el,r.left+r.width/2,r.top)});
el.addEventListener('blur',()=>tip.style.opacity=0)});
const slides=[...document.querySelectorAll('.slide')];const q=new URLSearchParams(location.search).get('slide');
if(q){document.body.classList.add('solo');(slides[+q-1]||slides[0]).classList.add('on')}
const cur=()=>{let best=0,d=1e9;slides.forEach((s,i)=>{const t=Math.abs(s.getBoundingClientRect().top);if(t<d){d=t;best=i}});return best};
addEventListener('keydown',e=>{if(e.target.closest('input,textarea'))return;let k=null;
if(['ArrowRight','ArrowDown','PageDown',' '].includes(e.key))k=1;if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key))k=-1;
if(k){e.preventDefault();const i=Math.max(0,Math.min(slides.length-1,cur()+k));slides[i].scrollIntoView({behavior:'smooth'})}})})();
"""


def page(P, deck, theme):
    n = len(deck.slides)
    secs = []
    for i, (sid, body, cls) in enumerate(deck.slides):
        foot = "" if sid == "cover" else f"<footer><span>{E(P.name)}</span><span>{i + 1} / {n}</span></footer>"
        secs.append(f'<section class="slide {cls}" id="{E(sid)}"><div class="frame">{body}</div>{foot}</section>')
    th = f' data-theme="{theme}"' if theme in ("light", "dark") else ""
    return (f'<!doctype html><html lang="en"{th}><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{E(P.name)} · design review</title><style>{CSS}</style></head><body>"
            f'<button id="theme" type="button" aria-label="Switch color theme">Dark</button><div id="tip" role="tooltip"></div>'
            + "".join(secs) + f"<script>{JS}</script></body></html>\n")


# ------------------------------------------------------------------ browser (optional PDF / PNG)
def run_browser(args, hw="."):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import layout_check
    b = layout_check.toolchain_browser(hw)
    if not b:
        print("warning: no Chrome/Chromium/Edge found; skipped (set CHROME or run toolchain-setup)", file=sys.stderr)
        return False
    return layout_check.headless(b, args, timeout=180).returncode == 0


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("hw", nargs="?", default="hw", help="project workspace folder (default: hw)")
    ap.add_argument("-o", "--out", help="output HTML (default: <hw>/presentation/index.html)")
    ap.add_argument("--theme", choices=("auto", "light", "dark"), default=None, help="initial theme (default: deck.json or auto)")
    ap.add_argument("--inline-limit", type=float, default=25.0, help="inline images when their total is below this many MB")
    ap.add_argument("--pdf", action="store_true", help="also print a PDF with a headless Chromium browser")
    ap.add_argument("--check", action="store_true", help="check every chart for overlapping text; exit 3 on a problem")
    ap.add_argument("--no-layout-check", action="store_true", help="skip the browser layout lint (scripts/layout_check.py)")
    ap.add_argument("--png", metavar="DIR", help="also write one PNG per slide (1600x900) for visual review")
    a = ap.parse_args()
    if not os.path.isdir(a.hw):
        print(f"error: {a.hw} is not a folder", file=sys.stderr)
        return 1
    P = Project(a.hw)
    out = a.out or os.path.join(a.hw, "presentation", "index.html")
    out_dir = os.path.dirname(os.path.abspath(out))
    os.makedirs(out_dir, exist_ok=True)
    pics = P.renders + P.drawings + ([P.arch_img] if P.arch_img else [])
    total_mb = sum(os.path.getsize(p) for p in pics) / 1e6
    imgs = Images(out_dir, inline=total_mb < a.inline_limit)
    D = Deck(P, imgs)
    order = P.deck.get("slides") or ["cover", "idea", "highlights", "use", "renders", "drawings", "architecture",
                                     "components", "power", "doability", "verify", "risks", "cost", "nre", "compliance",
                                     "roadmap", "next", "pending", "sources"]
    hero = P.deck.get("hero")
    gallery = [p for p in P.renders if not (hero and os.path.abspath(p) == os.path.abspath(os.path.join(a.hw, hero)))]
    if not hero and gallery:
        gallery = gallery[1:]                      # the first render is the cover
    steps = {"cover": D.cover, "idea": D.idea, "highlights": D.highlights, "use": D.use,
             "renders": lambda: D.images(gallery, "render"), "drawings": lambda: D.images(P.drawings, "drawing"),
             "architecture": D.architecture, "components": D.components, "power": D.power, "doability": D.doability, "verify": D.verify,
             "risks": D.risks, "cost": D.cost, "nre": D.nre, "compliance": D.compliance, "roadmap": D.roadmap,
             "next": D.next_steps, "pending": D.pending, "sources": D.sources}
    for s in order:
        if s in steps:
            steps[s]()
        else:
            print(f"warning: unknown slide '{s}' in deck.json", file=sys.stderr)
    theme = a.theme or P.deck.get("theme", "auto")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page(P, D, theme))
    problems = []
    for sid, body, _c in D.slides:
        for svg in re.findall(r"<svg class=\"chart.*?</svg>", body, re.S):
            problems += [f"{sid}: {p}" for p in chart_collisions(svg)]
    if a.check:
        for p in problems:
            print("LAYOUT:", p, file=sys.stderr)
    url = "file://" + os.path.abspath(out)
    extra = []
    if a.pdf:
        pdf = os.path.join(out_dir, "presentation.pdf")
        ok = run_browser(["--no-pdf-header-footer", f"--print-to-pdf={pdf}", url + ("?theme=light" if theme != "dark" else "")], a.hw)
        extra.append(f"PDF {'written' if ok and os.path.exists(pdf) else 'FAILED'}")
    if a.png:
        os.makedirs(a.png, exist_ok=True)
        okn = 0
        for i in range(1, len(D.slides) + 1):
            png = os.path.join(a.png, f"slide-{i:02d}.png")
            q = f"?slide={i}" + (f"&theme={theme}" if theme in ("light", "dark") else "")
            if run_browser(["--window-size=1600,900", f"--screenshot={png}", url + q], a.hw) and os.path.exists(png):
                okn += 1
        extra.append(f"{okn} PNG(s) in {a.png}")
    lint = None
    if not a.no_layout_check:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import layout_check
        lint = layout_check.run(out, shots="failing", quiet=False)
        if lint is not None:
            extra.append(f"layout check: {len(lint)} finding(s)")
    missing = [k for k, v in (("brief", P.brief), ("bom", P.bom), ("power", P.power), ("doability", P.findings),
                              ("cost", P.cost), ("compliance", P.compliance), ("roadmap", P.schedule),
                              ("renders", P.renders)) if not v]
    print(f"build_presentation: {len(D.slides)} slides -> {out}"
          + (f" ({imgs.copied} image(s) copied to assets/)" if imgs.copied else "")
          + (f"; missing inputs: {', '.join(missing)}" if missing else "")
          + ("; " + "; ".join(extra) if extra else "")
          + (f"; layout check: {len(problems)} problem(s)" if a.check else ""))
    if a.check and problems:
        return 3
    return 4 if lint else 0


if __name__ == "__main__":
    sys.exit(main())
