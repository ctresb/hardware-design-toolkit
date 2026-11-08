"""Orthographic views of the assembled product (front, top, side) with overall dimensions, hidden edges
dashed, a small isometric view in the free quadrant, and an ISO 7200-style title block.

usage:
  blender -b assembly.blend --python ortho_views.py -- config.json out/prefix [--themes print]

Uses the same config as blueprint.py (groups/items are ignored; explode offsets are not applied).
Writes <prefix>_ortho_<theme>.svg (+ .pdf/.png if rsvg-convert is installed). Tested with Blender 5.2.
"""
import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drawing_core as dc  # noqa: E402
import line_clean as LC  # noqa: E402

X_, Y_, Z_ = np.eye(3)
VIEWS = {  # D (target -> camera), R (right on paper), U (up on paper)
    "front": (-Y_, X_, Z_),
    "top": (Z_, X_, Y_),
    "right": (X_, Y_, Z_),
    "left": (-X_, -Y_, Z_),
}


def bbox2d(segs2d):
    pts = [p for v in segs2d.values() for s in v for p in (s[:2], s[2:])]
    a = np.array(pts)
    return a.min(0), a.max(0)


def dim_line(sh, x1, y1, x2, y2, value, side, dec, off=7.0):
    """Overall dimension between two points (horizontal or vertical) with extension lines and arrows."""
    ink = sh.t["ink"]
    horiz = abs(y2 - y1) < abs(x2 - x1)
    if horiz:
        yd = (max(y1, y2) + off) if side == "below" else (min(y1, y2) - off)
        for x, y in ((x1, y1), (x2, y2)):
            sh.o.append(f'<line x1="{x:.2f}" y1="{y + (1 if yd > y else -1):.2f}" x2="{x:.2f}" '
                        f'y2="{yd + (1.5 if yd > y else -1.5):.2f}" stroke="{ink}" stroke-width="0.18"/>')
        a, b = (x1, yd), (x2, yd)
        tx, ty, rot = (x1 + x2) / 2, yd - 1.2, 0
    else:
        xd = (min(x1, x2) - off) if side == "left" else (max(x1, x2) + off)
        for x, y in ((x1, y1), (x2, y2)):
            sh.o.append(f'<line x1="{x + (1 if xd > x else -1):.2f}" y1="{y:.2f}" '
                        f'x2="{xd + (1.5 if xd > x else -1.5):.2f}" y2="{y:.2f}" stroke="{ink}" stroke-width="0.18"/>')
        a, b = (xd, y1), (xd, y2)
        tx, ty, rot = xd - 1.2, (y1 + y2) / 2, -90
    sh.o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" stroke="{ink}" stroke-width="0.18"/>')
    v = np.array(b) - np.array(a)
    L = np.linalg.norm(v)
    if L > 1e-6:
        u = v / L
        n = np.array([-u[1], u[0]])
        for p, d in ((np.array(a), u), (np.array(b), -u)):
            q1 = p + d * 2.2 + n * 0.55
            q2 = p + d * 2.2 - n * 0.55
            sh.o.append(f'<path d="M{p[0]:.2f} {p[1]:.2f}L{q1[0]:.2f} {q1[1]:.2f}L{q2[0]:.2f} {q2[1]:.2f}Z" fill="{ink}"/>')
    sh.o.append(f'<text x="{tx:.2f}" y="{ty:.2f}" font-size="2.6" fill="{ink}" text-anchor="middle" '
                f'transform="rotate({rot} {tx:.2f} {ty:.2f})">{dc.num(value, dec)}</text>')


def main():
    ap = argparse.ArgumentParser(prog="ortho_views.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("out_prefix")
    ap.add_argument("--themes", default=None, help="comma list (default: config 'ortho_themes', else 'themes')")
    a = ap.parse_args(dc.script_args())
    t0 = time.time()
    cfg = dc.load_config(a.config)
    inc = cfg.get("ortho_include")
    if inc:                                                   # draw only these groups (e.g. the exterior parts)
        cfg["groups"] = [g for g in cfg["groups"] if g.get("name") in inc]
        if not cfg["groups"]:
            raise SystemExit(f"ortho_include {inc} matches no group name in the config")
    themes = a.themes.split(",") if a.themes else (cfg.get("ortho_themes") or cfg["themes"])
    lab, dec = cfg["labels"], cfg["decimal"]
    scene = dc.Scene3D(cfg, explode=False)
    side = "right" if cfg["projection"] == "third" else "left"
    views = {}
    for name in ("front", "top", side):
        D, R, U = VIEWS[name]
        segs = scene.feature_edges(D, hidden=cfg["hidden_lines"])
        s2 = dc.project(segs, R, U)
        # drop edges seen end-on (zero length on paper)
        s2 = {k: [s for s in v if abs(s[2] - s[0]) + abs(s[3] - s[1]) > 1e-4] for k, v in s2.items()}
        views[name] = (s2, *bbox2d(s2))
    vD, vR, vU = dc.view_basis(cfg["view"]["azimuth_deg"], cfg["view"]["elevation_deg"])
    iso = dc.project(scene.feature_edges(vD, hidden=False), vR, vU)
    iso_lo, iso_hi = bbox2d(iso)

    made = []
    lc = cfg.get("line_clean") or {}
    removed = 0
    for th in themes:
        sh = dc.Sheet(cfg, th)
        fw, fh = views["front"][2] - views["front"][1]
        tw_, th_ = views["top"][2] - views["top"][1]
        sw, shh = views[side][2] - views[side][1]
        gap = 26.0
        area_w, area_h = sh.W - 40, sh.H - 20 - 55
        fit = min((area_w - 3 * gap) / (fw + sw), (area_h - 2 * gap) / (fh + th_))
        sc = dc.standard_scale(sh.phys(fit)) * sh.W / sh.pw if cfg["standard_scale"] else fit
        block_w = (fw + sw) * sc + gap
        block_h = (fh + th_) * sc + gap
        x0 = 20 + (area_w - block_w) / 2
        y0 = 20 + (area_h - block_h) / 2
        if cfg["projection"] == "third":
            pos = {"top": (x0, y0), "front": (x0, y0 + th_ * sc + gap), side: (x0 + fw * sc + gap, y0 + th_ * sc + gap)}
            iso_box = (x0 + fw * sc + gap, y0, sw * sc, th_ * sc)
        else:
            pos = {"front": (x0, y0), "top": (x0, y0 + fh * sc + gap), side: (x0 + fw * sc + gap, y0)}
            iso_box = (x0 + fw * sc + gap, y0 + fh * sc + gap, sw * sc, th_ * sc)
        for name, (px, py) in pos.items():
            s2, lo, hi = views[name]
            if lc.get("enabled", True):                       # seam ticks and dots: tolerance in paper mm
                k = (sh.W / sh.pw) / sc
                s2, nrm = LC.clean(s2, tol=lc.get("tol_mm", 0.3) * k, maxlen=lc.get("maxlen_mm", 2.0) * k)
                removed += nrm
            sh.lines(s2, lambda x, lo=lo, px=px: px + (x - lo[0]) * sc, lambda y, lo=lo, py=py: py + (y - lo[1]) * sc,
                     ident=f"-{name}")
            w, h = (hi - lo) * sc
            label = lab["front"] if name == "front" else lab["top"] if name == "top" else lab[name]
            sh.text(px + w / 2, py + h + (17 if name in ("front", side) else 6), label, 2.8, fill=sh.t["ink2"],
                    weight="600", anchor="middle")
            if name == "front":
                dim_line(sh, px, py + h, px + w, py + h, hi[0] - lo[0], "below", dec)
                dim_line(sh, px, py, px, py + h, hi[1] - lo[1], "left", dec)
            elif name == side:
                dim_line(sh, px, py + h, px + w, py + h, hi[0] - lo[0], "below", dec)
        # isometric thumbnail in the free quadrant, at its own scale
        bx, by, bw, bh = iso_box
        bw, bh = max(bw, 40), max(bh, 30)
        isz = iso_hi - iso_lo
        s_iso = min(bw / isz[0], (bh - 6) / isz[1]) * 0.9
        ix = bx + (bw - isz[0] * s_iso) / 2 - iso_lo[0] * s_iso
        iy = by + (bh - 6 - isz[1] * s_iso) / 2 - iso_lo[1] * s_iso
        sh.lines(iso, lambda x: ix + x * s_iso, lambda y: iy + y * s_iso, ident="-iso")
        sh.text(bx + bw / 2, by + bh + 2, lab["iso"], 2.4, fill=sh.t["ink2"], weight="600", anchor="middle")

        ti = cfg["title"]
        size = " × ".join(dc.num(x, dec) for x in scene.size0) + " mm"
        cells = [(lab["size"], ti.get("overall_size") or size),
                 (lab["scale"], dc.scale_label(sh.phys(sc), dec) + f" ({cfg['sheet']})"),
                 (lab["units"], ti.get("units", "mm")),
                 (lab["revision"], ti.get("revision", "A")),
                 (lab["date"], ti.get("date") if ti.get("date") not in (None, "auto") else dc.today()),
                 (lab["sheet"], ti.get("ortho_sheet", ti.get("sheet", "1/1")))]
        sh.title_block(cells, ti.get("product", "Product"), lab[cfg["projection"]] + " · overall dimensions")
        sh.footer(cfg["footer"].replace("Hidden lines removed.", "Hidden edges dashed.") if cfg["hidden_lines"] else cfg["footer"])
        made += dc.write_outputs(sh.svg(), f"{a.out_prefix}_ortho_{th}.svg")
    print(f"ORTHO ok: {len(scene.meshes)} meshes, {scene.nrays} rays, size {size}, scale {dc.scale_label(sh.phys(sc))}, "
          f"{removed} seam ticks removed, {time.time() - t0:.1f} s -> {', '.join(os.path.basename(m) for m in made)}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code not in (0, None):
            print(f"ORTHO failed: {e}")
            sys.stdout.flush()
            os._exit(e.code if isinstance(e.code, int) else 1)
        raise
