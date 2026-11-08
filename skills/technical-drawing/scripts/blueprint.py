"""Exploded isometric vector drawing for quotations: hidden-line-removed linework, numbered balloons,
bill of materials with per-unit envelopes, and an ISO 7200-style title block.

usage:
  blender -b assembly.blend --python blueprint.py -- config.json out/prefix [--themes blueprint,print]

Writes <prefix>_<theme>.svg (+ .pdf/.png if rsvg-convert is installed) and <prefix>_items.json.
Config format: see templates/blueprint.example.json and SKILL.md. Tested with Blender 5.2.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drawing_core as dc  # noqa: E402


def item_table(scene, cfg, R, U):
    """Anchor (visible point near the item centroid) and per-unit envelopes for every BOM item."""
    D = np.cross(R, U)                       # towards the camera
    items = {}
    ign = tuple(cfg["unit_ignore_prefixes"])
    root = cfg.get("root")
    for m in scene.meshes:
        it = m["item"]
        if it is None:
            continue
        d = items.setdefault(it, dict(pts=[], units={}))
        d["pts"].append(m["W"])
        # physical unit = nearest named empty above the mesh (a placed component), else the mesh itself
        u, a = m["o"], m["o"].parent
        while a is not None:
            if a.type == 'EMPTY' and a.name[:1].isalpha() and not a.name.startswith(ign) and a.name != root:
                u = a
                break
            a = a.parent
        d["units"].setdefault(u.name, []).append(m["W0"])
    for it, d in items.items():
        P = np.concatenate(d["pts"])
        c = P.mean(0)
        proj = np.c_[P @ R, -(P @ U)]
        cc = np.array([c @ R, -(c @ U)])
        idx = np.argsort(((proj - cc) ** 2).sum(1))[:600]
        anchor, hidden = proj[idx[0]], True
        rest = np.argsort(((proj - cc) ** 2).sum(1))[600::max(1, (len(P) - 600) // 4000)]
        for i in np.r_[idx, rest]:
            if scene.visible(P[i], D):
                anchor, hidden = proj[i], False
                break
        d["anchor"] = [float(anchor[0]), float(anchor[1])]
        d["hidden"] = hidden                                  # no point of the item is visible in this view
        dims = []
        for un, lst in d["units"].items():
            Q = np.concatenate(lst)
            e = Q.max(0) - Q.min(0)
            dims.append((float(np.prod(np.maximum(e, 1e-3))), un, sorted([round(float(x), 1) for x in e], reverse=True)))
        dims.sort(reverse=True)
        d["dim"] = dims[0][2]                                  # one unit (the largest), never the sum
        d["dims_all"] = {un: dm for _v, un, dm in dims}
        d["n_units"] = len(dims)
        Q = np.concatenate([x for lst in d["units"].values() for x in lst])
        d["dim_item"] = sorted([round(float(x), 1) for x in Q.max(0) - Q.min(0)], reverse=True)
        del d["pts"], d["units"]
    return items


def place_column(desired, lo, hi, gap):
    """1D placement that keeps the anchor order (so leaders do not cross) with a minimum gap."""
    n = len(desired)
    if not n:
        return []
    gap = min(gap, (hi - lo) / max(1, n - 1)) if n > 1 else gap
    y = [min(hi, max(lo, v)) for v in desired]
    for i in range(1, n):
        y[i] = max(y[i], y[i - 1] + gap)
    if y[-1] > hi:
        y[-1] = hi
        for i in range(n - 2, -1, -1):
            y[i] = min(y[i], y[i + 1] - gap)
    if y[0] < lo:
        y[0] = lo
        for i in range(1, n):
            y[i] = max(y[i], y[i - 1] + gap)
    return y


def _cross(p1, p2, q1, q2):
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return o(p1, p2, q1) * o(p1, p2, q2) < 0 and o(q1, q2, p1) * o(q1, q2, p2) < 0


def _near(p, a, b, r):
    """Point p within r of segment a-b (a leader running over another item's anchor dot)."""
    a, b, p = np.array(a), np.array(b), np.array(p)
    t = np.clip(np.dot(p - a, b - a) / max(np.dot(b - a, b - a), 1e-9), 0, 1)
    return np.linalg.norm(a + t * (b - a) - p) < r


def untangle(anchors, ys, kx):
    """Swap balloon slots while two leaders cross or a leader runs over another anchor."""
    ys = list(ys)
    for _ in range(60):
        changed = False
        for i in range(len(ys)):
            for j in range(i + 1, len(ys)):
                ai, aj = anchors[i], anchors[j]
                li, lj = (ai, (kx, ys[i])), (aj, (kx, ys[j]))
                bad = _cross(*li, *lj) or _near(aj, *li, 1.2) or _near(ai, *lj, 1.2)
                if bad:
                    sw_i, sw_j = (ai, (kx, ys[j])), (aj, (kx, ys[i]))
                    if not (_cross(*sw_i, *sw_j) or _near(aj, *sw_i, 1.2) or _near(ai, *sw_j, 1.2)):
                        ys[i], ys[j] = ys[j], ys[i]
                        changed = True
        if not changed:
            break
    return ys


def envelope_text(cfg, it_cfg, d):
    """envelope: "auto" (default), "item", "largest", "all" or false.
    auto = whole item when qty is 1 (one physical part, e.g. a PCBA), else the largest unit "(each)"."""
    lab, dec = cfg["labels"], cfg["decimal"]

    def fmt(dm):
        return " × ".join(dc.num(x, dec) for x in dm) + " mm"
    mode = it_cfg.get("envelope", "auto")
    if not d or mode is False:
        return ""
    single = str(it_cfg.get("qty", "1")).strip() in ("1", "")
    if mode == "auto":
        mode = "item" if single else "largest"
    if mode == "all":
        distinct = []
        for dm in d["dims_all"].values():
            if dm not in distinct:
                distinct.append(dm)
        if len(distinct) > 1:
            return f"; {lab['envelopes']} " + "; ".join(fmt(x) for x in distinct)
        mode = "largest"
    if mode == "item":
        return f"; {lab['envelope']} " + fmt(d["dim_item"])
    return f"; {lab['envelope'] if single and d['n_units'] == 1 else lab['envelope_each']} " + fmt(d["dim"])


def draw(cfg, scene, segs2d, items, theme):
    sh = dc.Sheet(cfg, theme)
    t, lab, dec = sh.t, cfg["labels"], cfg["decimal"]
    tw = 116.0
    tx = sh.W - 12 - tw
    AREA = (14.0, 22.0, tx - 24.0, sh.H - 35.0)
    allp = np.array([s[:2] for k in segs2d for s in segs2d[k]] + [s[2:] for k in segs2d for s in segs2d[k]])
    lo, hi = allp.min(0), allp.max(0)
    fit = min((AREA[2] - 40) / (hi[0] - lo[0]), (AREA[3] - 8) / (hi[1] - lo[1]))
    sc = fit
    if cfg["standard_scale"]:
        sc = dc.standard_scale(sh.phys(fit)) * sh.W / sh.pw
    ox = AREA[0] + (AREA[2] - (hi[0] - lo[0]) * sc) / 2 - lo[0] * sc
    oy = AREA[1] + (AREA[3] - (hi[1] - lo[1]) * sc) / 2 - lo[1] * sc

    def X(x):
        return ox + x * sc

    def Y(y):
        return oy + y * sc
    sh.lines(segs2d, X, Y)

    # balloons: left and right columns, ordered by anchor height so leaders do not cross
    mid = X((lo[0] + hi[0]) / 2)
    ks = sorted(items, key=lambda k: items[k]["anchor"][1])
    left = [k for k in ks if X(items[k]["anchor"][0]) < mid]
    right = [k for k in ks if k not in left]
    xl = max(22.0, X(lo[0]) - 14)
    xr = min(tx - 12.0, X(hi[0]) + 14)
    for lst, xb, side in ((left, xl, "L"), (right, xr, "R")):
        ys = place_column([Y(items[k]["anchor"][1]) for k in lst], 34.0, sh.H - 48.0, 11.0)
        kx = xb + (5 if side == "L" else -5)
        ys = untangle([(X(items[k]["anchor"][0]), Y(items[k]["anchor"][1])) for k in lst], ys, kx)
        for k, yb in zip(lst, ys):
            ax, ay = X(items[k]["anchor"][0]), Y(items[k]["anchor"][1])
            if items[k]["hidden"]:      # hidden item: hollow dot, dashed leader (ISO 128 hidden-feature look)
                sh.o.append(f'<circle cx="{ax:.2f}" cy="{ay:.2f}" r="0.8" fill="{t["bg"]}" stroke="{t["accent"]}" stroke-width="0.25"/>')
                dash = ' stroke-dasharray="1.2 0.8"'
            else:
                sh.o.append(f'<circle cx="{ax:.2f}" cy="{ay:.2f}" r="0.7" fill="{t["accent"]}"/>')
                dash = ""
            sh.o.append(f'<polyline points="{ax:.2f},{ay:.2f} {kx:.2f},{yb:.2f} {xb:.2f},{yb:.2f}" fill="none" '
                        f'stroke="{t["accent"]}" stroke-width="0.25"{dash}/>')
            cx = xb - 4.2 if side == "L" else xb + 4.2
            sh.o.append(f'<circle cx="{cx:.2f}" cy="{yb:.2f}" r="4.2" fill="{t["bg"]}" stroke="{t["accent"]}" '
                        f'stroke-width="0.35"/>')
            sh.text(cx, yb + 1.25, k, 3.6, weight="600", anchor="middle")

    # bill of materials (fonts shrink until the table fits above the title block)
    ty = 22.0
    bottom = sh.H - 12 - 31 - 6
    rows_cfg = sorted(cfg["items"], key=lambda r: r["id"])
    for f in np.linspace(1.0, 0.55, 19):
        fn, fs, lh = 2.35 * f, 2.15 * f, 2.9 * f
        cols = [(tx, 8), (tx + 8, 34), (tx + 42, 62), (tx + 104, 12)]
        rows = []
        for r in rows_cfg:
            spec = r.get("spec", "") + envelope_text(cfg, r, items.get(r["id"]))
            nl = dc.wrap(r.get("name", ""), dc.chars_fit(34, fn, True))
            sl = dc.wrap(spec.lstrip("; "), dc.chars_fit(62, fs))
            rows.append((r, nl, sl, max(len(nl), len(sl)) * lh + 2.2 * f))
        if ty + 6 + sum(x[3] for x in rows) <= bottom:
            break
    sh.text(tx, ty - 4, lab["bom"], 4.2, weight="700")
    sh.o.append(f'<rect x="{tx:.2f}" y="{ty}" width="{tw}" height="6" fill="none" stroke="{t["ink"]}" stroke-width="0.3"/>')
    for (cx, _cw), label in zip(cols, (lab["item"], lab["description"], lab["spec"], lab["qty"])):
        sh.text(cx + 1.2, ty + 4.2, label, 2.6, weight="700")
    y = ty + 6
    for r, nl, sl, rh in rows:
        sh.o.append(f'<rect x="{tx:.2f}" y="{y:.2f}" width="{tw}" height="{rh:.2f}" fill="none" stroke="{t["ink"]}" stroke-width="0.2"/>')
        sh.text(tx + 4, y + 3.6 * f + 0.4, r["id"], 2.6 * max(f, 0.8), weight="700", anchor="middle")
        for i, s in enumerate(nl):
            sh.text(tx + 9.2, y + 3.6 * f + 0.4 + i * lh, s, fn, weight="600")
        for i, s in enumerate(sl):
            sh.text(tx + 43.2, y + 3.6 * f + 0.4 + i * lh, s, fs, fill=t["ink2"])
        sh.text(tx + 110, y + 3.6 * f + 0.4, r.get("qty", "1"), 2.4 * max(f, 0.8), anchor="middle")
        y += rh
    for cx, _cw in cols[1:]:
        sh.o.append(f'<line x1="{cx:.2f}" y1="{ty}" x2="{cx:.2f}" y2="{y:.2f}" stroke="{t["ink"]}" stroke-width="0.2"/>')

    ti = cfg["title"]
    size = " × ".join(dc.num(x, dec) for x in scene.size0) + " mm"
    cells = [(lab["size"], ti.get("overall_size") or size),
             (lab["scale"], dc.scale_label(sh.phys(sc), dec) + f" ({cfg['sheet']})"),
             (lab["units"], ti.get("units", "mm")),
             (lab["revision"], ti.get("revision", "A")),
             (lab["date"], ti.get("date") if ti.get("date") not in (None, "auto") else dc.today()),
             (lab["sheet"], ti.get("sheet", "1/1"))]
    sh.title_block(cells, ti.get("product", "Product"), ti.get("subtitle", "Exploded isometric view · for quotation"))
    sh.footer(cfg["footer"])
    return sh.svg(), sh.phys(sc)


def main():
    ap = argparse.ArgumentParser(prog="blueprint.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("out_prefix")
    ap.add_argument("--themes", default=None, help="comma list: blueprint,print")
    a = ap.parse_args(dc.script_args())
    t0 = time.time()
    cfg = dc.load_config(a.config)
    themes = a.themes.split(",") if a.themes else cfg["themes"]
    scene = dc.Scene3D(cfg, explode=True)
    v = cfg["view"]
    D, R, U = dc.view_basis(v["azimuth_deg"], v["elevation_deg"])
    segs = scene.feature_edges(D, hidden=False)
    segs2d = dc.project(segs, R, U)
    items = item_table(scene, cfg, R, U)
    missing = [r["id"] for r in cfg["items"] if r["id"] not in items]
    hidden = sorted(k for k, d in items.items() if d["hidden"])
    made = []
    for th in themes:
        svg, s = draw(cfg, scene, segs2d, items, th)
        made += dc.write_outputs(svg, f"{a.out_prefix}_{th}.svg")
    with open(a.out_prefix + "_items.json", "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in sorted(items.items())}, f, ensure_ascii=False, indent=1)
    n = sum(len(x) for x in segs.values())
    print(f"BLUEPRINT ok: {len(scene.meshes)} meshes, {n} segments, {scene.nrays} rays, scale {dc.scale_label(s)}, "
          f"items {sorted(items)}" + (f", ITEMS WITHOUT GEOMETRY {missing}" if missing else "") +
          (f", hidden in this view (dashed leader; raise offsets or change view): {hidden}" if hidden else "") +
          f", {time.time() - t0:.1f} s -> {', '.join(os.path.basename(m) for m in made)}")
    if missing:
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code not in (0, None):
            print(f"BLUEPRINT failed: {e}")
            sys.stdout.flush()
            os._exit(e.code if isinstance(e.code, int) else 1)
        raise
