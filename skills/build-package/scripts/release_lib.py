"""Shared helpers for assemble_release.py and release_check.py (standard library only)."""
import csv
import datetime as dt
import fnmatch
import hashlib
import json
import pathlib
import re

PLACEHOLDER_MPN = re.compile(r"(\?|TBD|TODO|XXX|placeholder|^-$|^$)", re.I)
REF_RANGE = re.compile(r"^([A-Za-z_]+)(\d+)\s*[-–]\s*(?:\1)?(\d+)$")
ASSEMBLER_FILES = {
    "jlcpcb": {"bom": "{board}_bom_jlcpcb.csv", "cpl": "{board}_cpl_jlcpcb.csv"},
    "pcbway": {"bom": "{board}_bom_pcbway.csv", "cpl": "{board}_cpl_pcbway.csv"},
    "generic": {"bom": "{board}_bom.csv", "cpl": "{board}_cpl.csv"},
}


def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def natural(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def expand_refs(text):
    """'C1, C2-C4 R7' -> ['C1','C2','C3','C4','R7']."""
    out = []
    for tok in re.split(r"[,\s;]+", (text or "").strip()):
        if not tok:
            continue
        m = REF_RANGE.match(tok)
        if m:
            p, a, b = m.group(1), int(m.group(2)), int(m.group(3))
            out += [f"{p}{i}" for i in range(a, b + 1)]
        else:
            out.append(tok)
    return out


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _sanitize_csv_cell(val):
    if isinstance(val, str) and val and val[0] in ("=", "+", "@", "\t", "\r"):
        return "'" + val
    if isinstance(val, str) and len(val) > 1 and val[0] == "-" and not re.match(r"^-[0-9.]", val):
        return "'" + val
    return val


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows([[_sanitize_csv_cell(c) for c in r] for r in rows])


def lcsc_of(row):
    """LCSC number from an 'lcsc' column, an 'LCSC:C123' token in distributors, or 'lcsc=C123' in key_specs."""
    for k in ("lcsc", "LCSC", "LCSC Part #"):
        v = (row.get(k) or "").strip()
        if re.fullmatch(r"C\d{3,}", v):
            return v
    for field in ("distributors", "key_specs", "notes"):
        m = re.search(r"\bLCSC\s*[:=]\s*(C\d{3,})", row.get(field) or "", re.I)
        if m:
            return m.group(1).upper()
    return ""


def bom_by_ref(bom_rows):
    """Map each reference designator to its hw/bom.csv row."""
    out = {}
    for r in bom_rows:
        for ref in expand_refs(r.get("ref", "")):
            out[ref] = r
    return out


def is_passive(ref, prefixes):
    m = re.match(r"[A-Za-z]+", ref)
    return bool(m) and m.group(0).upper() in {p.upper() for p in prefixes}


def order_qty(per_unit, build_qty, attrition, passive):
    """Units to buy for one build: per-unit × build size, plus attrition (percent, then a minimum extra)."""
    base = per_unit * build_qty
    extra = max(base * attrition.get("default_pct", 5) / 100.0,
                attrition.get("passive_min_extra", 10) if passive else attrition.get("min_extra", 1))
    q = base + extra
    return int(q) if q == int(q) else int(q) + 1


def parse_date(s):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", s or "")
    return dt.date.fromisoformat(m.group(1)) if m else None


def parse_stock(s):
    """First integer in a stock snapshot like '12,400 @ LCSC 2026-11-08' -> 12400; None if absent."""
    m = re.search(r"(\d[\d,.\s]*)", (s or "").split("@")[0])
    if not m:
        return None
    digits = re.sub(r"[^\d]", "", m.group(1))
    return int(digits) if digits else None


def rotation_offset(footprint, offsets):
    for pat, deg in (offsets or {}).items():
        if fnmatch.fnmatch(footprint, pat):
            return float(deg)
    return 0.0


def doability_verdict(path):
    """Overall verdict string from doability output (JSON with a verdict field, or Markdown text)."""
    p = pathlib.Path(path)
    if not p.exists():
        return None
    text = p.read_text(encoding="utf-8")
    if p.suffix == ".json":
        try:
            d = json.loads(text)
        except json.JSONDecodeError:
            d = None
        if isinstance(d, dict):
            for k in ("overall", "overall_verdict", "verdict", "status", "level"):   # `overall`: doability score.json
                v = d.get(k)
                if isinstance(v, dict):
                    v = v.get("verdict") or v.get("status") or v.get("level")
                if isinstance(v, str) and v.strip():
                    return v.strip()
    m = re.search(r"(READY TO BUILD\s*\((?:prototype|production)\)|NOT READY)", text, re.I)
    return m.group(1) if m else None


def verify_list_from_doability(path):
    """'Verify on the prototype' items: `prototype_checks` of doability score.json (canonical), or legacy keys."""
    try:
        d = load_json(path)
    except Exception:
        return []
    for k in ("prototype_checks", "verify_on_prototype", "verify"):
        v = d.get(k) if isinstance(d, dict) else None
        if isinstance(v, list):
            return v
    return []


def extract_mcu_pins(netlist_text, mcu):
    pins = []
    for chunk in re.split(r"\(net\s+\(code", netlist_text)[1:]:
        m = re.search(r'\(name\s+"([^"]*)"', chunk)
        net = m.group(1) if m else ""
        for nm in re.finditer(r'\(node\s+\(ref\s+"?([^")\s]+)"?\)\s+\(pin\s+"?([^")\s]+)"?\)(?:\s+\(pinfunction\s+"([^"]*)"\))?', chunk):
            if nm.group(1) == mcu:
                pins.append({"pin": nm.group(2), "function": nm.group(3) or "", "net": net.lstrip("/")})
    pins.sort(key=lambda d: natural(d["pin"]))
    return pins


def format_pins_header(mcu, pins):
    h = [f"/* Pin map of {mcu}, generated from the schematic netlist. Do not edit; regenerate. */", "#pragma once", ""]
    net_counts = {}
    for d in pins:
        if d["net"].startswith("unconnected") or not d["net"]:
            continue
        ident = re.sub(r"[^A-Za-z0-9]+", "_", d["net"]).strip("_").upper()
        net_counts[ident] = net_counts.get(ident, 0) + 1
    for d in pins:
        if d["net"].startswith("unconnected") or not d["net"]:
            continue
        ident = re.sub(r"[^A-Za-z0-9]+", "_", d["net"]).strip("_").upper()
        macro_name = f"PIN_{ident}_{d['pin'].upper()}" if net_counts[ident] > 1 else f"PIN_{ident}"
        fun = re.sub(r"[^A-Za-z0-9_.]+", "_", d["function"])
        h.append(f"#define {macro_name:<28} \"{fun or d['pin']}\"  /* pad {d['pin']} */")
    return "\n".join(h) + "\n"


def format_order_markdown(cfg):
    steps = cfg.get("order_steps", [])
    n = cfg.get("build_qty", 1)
    lo = sum((s.get("cost_usd") or [0, 0])[0] for s in steps)
    hi = sum((s.get("cost_usd") or [0, 0])[-1] for s in steps)
    out = [f"# Order · {cfg.get('product', '')} rev {cfg.get('rev')} · build of {n}", "",
           f"Total: USD {lo:,.0f}–{hi:,.0f} [estimate, sources per step]. Steps that do not depend on each other "
           "can run in parallel; the lead times are per step.", "",
           "**WARNING** Ordering spends money. Confirm the release check passed (`checks/release-check.json`) "
           "and the stock dates are current before each step.", ""]
    for i, s in enumerate(steps, 1):
        c, t = s.get("cost_usd"), s.get("lead_time_days")
        out += [f"## {i}. {s.get('title', '')}", "",
                f"- **Where:** {s.get('where', '')}",
                f"- **Upload:** " + (", ".join(f"`{u}`" for u in s.get("upload", [])) or "nothing"),
                f"- **Options:** {s.get('options', '')}",
                f"- **Cost:** " + (f"USD {c[0]:,.0f}–{c[-1]:,.0f}" if c else "MISSING"),
                f"- **Lead time:** " + (f"{t[0]}–{t[-1]} days" if t else "MISSING"),
                f"- **Receiver:** {s.get('receiver', '')}",
                f"- **Source:** {s.get('source', '')}", ""]
    return "\n".join(out)
