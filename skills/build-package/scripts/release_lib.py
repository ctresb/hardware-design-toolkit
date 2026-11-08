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


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


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
