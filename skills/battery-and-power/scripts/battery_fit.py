#!/usr/bin/env python3
"""Fit a realistic pouch cell into the space a product has for it, and estimate its capacity honestly.

A real pouch cell is a straight-edged rectangle, or at most a simple stepped shape. Its sealed border
holds no charge. It swells over its life, and its thickness has a tolerance. A cell is never a free-form
blob that fills whatever space is left. This script:

  1. reads the pocket outline: a rectangle, a JSON polygon or an SVG path; the pocket height is given;
  2. insets the pocket by the wall clearance;
  3. searches rotations for the largest straight-edged rectangle, optionally plus one step;
  4. derives the cell thickness from the height, the z clearance, the thickness tolerance and the
     swelling allowance;
  5. estimates capacity two ways and keeps the more conservative bound of each:
       A. envelope volume x envelope energy density for the cell class;
       B. active volume, inside the seals, x active-stack energy density;
  6. writes an SVG (pocket, cell, active area, tab side) and a JSON with every number and its basis.

Every density is an [estimate]; replace it with a vendor quote. Standard library only.

examples:
  battery_fit.py --rect 22 20 --height 3.6
  battery_fit.py --svg pocket.svg --height 3.6 --stepped --svg-out hw/power/battery.svg --json hw/power/battery.json
  battery_fit.py --polygon pocket.json --height 4.0 --chem pouch-hv --angle 0
"""
import argparse
import json
import math
import re
import sys

# Energy density (Wh/L) by cell class. [estimate] ranges. Basis: published capacity and dimensions of
# small catalog pouch cells (envelope), and typical stacked/wound electrode density inside the seal (active).
# Small cells sit at the bottom of the range, because seals and tabs take a larger share of the volume.
CHEM = {
    "pouch-small": dict(env=(180, 320), act=(420, 560), vnom=3.7, note="catalog LiPo pouch, envelope < 1.5 cm3"),
    "pouch": dict(env=(300, 430), act=(450, 600), vnom=3.7, note="catalog LiPo pouch, 1.5-15 cm3"),
    "pouch-hv": dict(env=(330, 480), act=(500, 660), vnom=3.85, note="4.35-4.45 V high-voltage pouch, custom or premium"),
    "stacked-custom": dict(env=(350, 500), act=(520, 680), vnom=3.85, note="custom stacked electrode cell, MOQ applies"),
}


# ------------------------------------------------------------------ geometry input
def parse_svg(path, scale=None):
    txt = open(path).read()
    if scale is None:
        m_w = re.search(r'<svg[^>]*\swidth="([\d.]+)mm"', txt)
        m_vb = re.search(r'viewBox="([-\d.eE ,]+)"', txt)
        if m_w and m_vb:
            vb = [float(v) for v in re.split(r"[ ,]+", m_vb.group(1).strip())]
            scale = float(m_w.group(1)) / vb[2]
        else:
            scale = 1.0
            print("WARNING: SVG has no width in mm + viewBox; assuming 1 unit = 1 mm (use --svg-scale)")
    polys = []
    for pts in re.findall(r'<polygon[^>]*\spoints="([^"]+)"', txt):
        v = [float(x) for x in re.split(r"[ ,]+", pts.strip())]
        polys.append([(v[i], v[i + 1]) for i in range(0, len(v) - 1, 2)])
    for d in re.findall(r'<path[^>]*\sd="([^"]+)"', txt):
        polys.extend(parse_path(d))
    if not polys:
        raise SystemExit("no <path> or <polygon> found in the SVG")
    polys = [[(x * scale, -y * scale) for x, y in p] for p in polys if len(p) >= 3]   # SVG y down -> mm y up
    polys.sort(key=lambda p: -abs(area(p)))
    if len(polys) > 1:
        print(f"NOTE: {len(polys)} outlines in the SVG; using the largest as the pocket (holes are ignored)")
    return polys[0], scale


def parse_path(d):
    toks = re.findall(r"[MmLlHhVvCcSsQqTtZzAa]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", d)
    i, cmd = 0, None
    cur = (0.0, 0.0)
    start = cur
    subs, pts = [], []
    last_ctrl = None

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    def cubic(p0, p1, p2, p3, n=16):
        for k in range(1, n + 1):
            t = k / n
            a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            pts.append((a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1]))

    while i < len(toks):
        if re.fullmatch(r"[A-Za-z]", toks[i]):
            cmd = toks[i]; i += 1
            if cmd in "Zz":
                if pts:
                    subs.append(pts)
                pts = []
                cur = start
                continue
        if cmd is None:
            raise SystemExit("bad path data")
        rel = cmd.islower()
        C = cmd.upper()
        ox, oy = cur if rel else (0.0, 0.0)
        if C == "A":
            raise SystemExit("SVG arcs (A) are not supported: convert the outline to paths/polygons first")
        if C == "M":
            if pts:
                subs.append(pts)
            cur = (ox + num(), oy + num()); start = cur; pts = [cur]
            cmd = "l" if rel else "L"
            last_ctrl = None
        elif C == "L":
            cur = (ox + num(), oy + num()); pts.append(cur); last_ctrl = None
        elif C == "H":
            cur = ((ox if rel else 0) + num(), cur[1]); pts.append(cur); last_ctrl = None
        elif C == "V":
            cur = (cur[0], (oy if rel else 0) + num()); pts.append(cur); last_ctrl = None
        elif C in "CS":
            if C == "C":
                p1 = (ox + num(), oy + num())
            else:
                p1 = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) if last_ctrl else cur
            p2 = (ox + num(), oy + num()); p3 = (ox + num(), oy + num())
            cubic(cur, p1, p2, p3); last_ctrl = p2; cur = p3
        elif C in "QT":
            if C == "Q":
                q = (ox + num(), oy + num())
            else:
                q = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) if last_ctrl else cur
            p3 = (ox + num(), oy + num())
            p1 = (cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1]))
            p2 = (p3[0] + 2 / 3 * (q[0] - p3[0]), p3[1] + 2 / 3 * (q[1] - p3[1]))
            cubic(cur, p1, p2, p3); last_ctrl = q; cur = p3
    if pts:
        subs.append(pts)
    return subs


def area(p):
    return 0.5 * sum(p[k][0] * p[(k + 1) % len(p)][1] - p[(k + 1) % len(p)][0] * p[k][1] for k in range(len(p)))


def rot(p, ang):
    c, s = math.cos(ang), math.sin(ang)
    return [(x * c - y * s, x * s + y * c) for x, y in p]


# ------------------------------------------------------------------ raster (scanline intervals)
def row_intervals(poly, y):
    xs = []
    n = len(poly)
    for k in range(n):
        (x0, y0), (x1, y1) = poly[k], poly[(k + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    xs.sort()
    return [(xs[k], xs[k + 1]) for k in range(0, len(xs) - 1, 2)]


def intersect(A, B):
    out, i, j = [], 0, 0
    while i < len(A) and j < len(B):
        lo, hi = max(A[i][0], B[j][0]), min(A[i][1], B[j][1])
        if hi > lo:
            out.append((lo, hi))
        if A[i][1] < B[j][1]:
            i += 1
        else:
            j += 1
    return out


def raster(poly, h, clear):
    """Boolean grid of cell centers that are at least `clear` inside the polygon."""
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    x0, y0 = min(xs), min(ys)
    nx = int((max(xs) - x0) / h) + 1
    ny = int((max(ys) - y0) / h) + 1
    rows = [row_intervals(poly, y0 + (j + 0.5) * h) for j in range(ny)]
    k = int(math.ceil(clear / h))
    grid = []
    for j in range(ny):
        surv = None
        for dy in range(-k, k + 1):
            jj = j + dy
            m = math.sqrt(max(clear * clear - (dy * h) ** 2, 0.0))
            iv = [(a + m, b - m) for a, b in rows[jj] if b - a > 2 * m] if 0 <= jj < ny else []
            surv = iv if surv is None else intersect(surv, iv)
            if not surv:
                break
        line = bytearray(nx)
        for a, b in surv or []:
            i0 = max(0, int(math.ceil((a - x0) / h - 0.5)))
            i1 = min(nx - 1, int(math.floor((b - x0) / h - 0.5)))
            for i in range(i0, i1 + 1):
                line[i] = 1
        grid.append(line)
    return grid, x0, y0, nx, ny


def largest_rect(grid, nx, ny):
    """Maximal all-free rectangle (histogram method). Returns (area_cells, c0, c1, r0, r1)."""
    hgt = [0] * nx
    best = (0, 0, -1, 0, -1)
    for j in range(ny):
        row = grid[j]
        for i in range(nx):
            hgt[i] = hgt[i] + 1 if row[i] else 0
        st = []
        for i in range(nx + 1):
            hh = hgt[i] if i < nx else 0
            s = i
            while st and st[-1][1] >= hh:
                s, sh = st.pop()
                w = i - s
                # usable size counts cell centers: (n-1) spans; rank by real span area
                a = max(w - 1, 0) * max(sh - 1, 0)
                if a > best[0]:
                    best = (a, s, i - 1, j - sh + 1, j)
            st.append((s, hh))
    return best


def hist_rect(runs):
    """Largest rectangle under a histogram of run lengths. Returns (area, i0, i1, depth)."""
    best = (0, 0, -1, 0)
    st = []
    for i in range(len(runs) + 1):
        hh = runs[i] if i < len(runs) else 0
        s = i
        while st and st[-1][1] >= hh:
            s, sh = st.pop()
            a = max(i - s - 1, 0) * sh
            if a > best[0]:
                best = (a, s, i - 1, sh)
        st.append((s, hh))
    return best


def step_extension(grid, nx, ny, R, h, min_w, min_d):
    """Best rectangle attached to one side of R = (c0, c1, r0, r1), inside the free grid."""
    c0, c1, r0, r1 = R
    cands = []

    def run(i, j, di, dj):
        n = 0
        while 0 <= i < nx and 0 <= j < ny and grid[j][i]:
            n += 1; i += di; j += dj
        return n
    sides = {
        "+y": ([run(i, r1 + 1, 0, 1) for i in range(c0, c1 + 1)], c0),
        "-y": ([run(i, r0 - 1, 0, -1) for i in range(c0, c1 + 1)], c0),
        "+x": ([run(c1 + 1, j, 1, 0) for j in range(r0, r1 + 1)], r0),
        "-x": ([run(c0 - 1, j, -1, 0) for j in range(r0, r1 + 1)], r0),
    }
    for side, (runs, base) in sides.items():
        a, i0, i1, d = hist_rect(runs)
        w, dep = (i1 - i0) * h, d * h
        if w >= min_w and dep >= min_d:
            cands.append((w * dep, side, base + i0, base + i1, d))
    return max(cands) if cands else None


def fit(poly, h, clear, angles, stepped, min_w, min_d):
    best = None
    for ang in angles:
        P = rot(poly, -math.radians(ang))
        grid, x0, y0, nx, ny = raster(P, h, clear)
        a, c0, c1, r0, r1 = largest_rect(grid, nx, ny)
        if c1 < c0:
            continue
        W, L = (c1 - c0) * h, (r1 - r0) * h
        ext = step_extension(grid, nx, ny, (c0, c1, r0, r1), h, min_w, min_d) if stepped else None
        tot = W * L + (ext[0] if ext else 0)
        if best is None or tot > best["area_total"]:
            best = dict(angle=ang, h=h, x0=x0, y0=y0, rect=(c0, c1, r0, r1), W=W, L=L, ext=ext, area_total=tot)
    return best


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--rect", nargs=2, type=float, metavar=("W", "L"), help="rectangular pocket, mm")
    g.add_argument("--polygon", help='JSON file: {"pocket": [[x, y], ...]} in mm (optional "height_mm")')
    g.add_argument("--svg", help="SVG with the pocket outline (<path> or <polygon>)")
    ap.add_argument("--svg-scale", type=float, help="mm per SVG unit (default: from width in mm + viewBox, else 1)")
    ap.add_argument("--height", type=float, help="pocket height available for the cell, mm")
    ap.add_argument("--clearance", type=float, default=0.25, help="xy gap cell-to-wall, mm (default 0.25)")
    ap.add_argument("--z-clearance", type=float, default=0.10, help="z gap kept free, mm (default 0.10)")
    ap.add_argument("--thick-tol", type=float, default=0.10, help="cell thickness tolerance (+), mm (default 0.10)")
    ap.add_argument("--swell", type=float, default=0.08, help="end-of-life swelling allowance, fraction of thickness (default 0.08)")
    ap.add_argument("--tab-seal", type=float, default=2.5, help="seal + tab zone on the tab side, mm (default 2.5)")
    ap.add_argument("--side-seal", type=float, default=1.0, help="folded side seal, mm (default 1.0)")
    ap.add_argument("--bottom-seal", type=float, default=1.0, help="seal opposite the tabs, mm (default 1.0)")
    ap.add_argument("--pcm", type=float, default=0.0, help="extra length for a protection board on the tab side, mm")
    ap.add_argument("--corner-radius", type=float, default=0.5, help="cell corner radius, mm (default 0.5)")
    ap.add_argument("--chem", choices=list(CHEM) + ["auto"], default="auto", help="cell class (default auto by volume)")
    ap.add_argument("--density", nargs=2, type=float, metavar=("LO", "HI"), help="override envelope Wh/L range")
    ap.add_argument("--vnom", type=float, help="nominal voltage (default from class)")
    ap.add_argument("--claimed-mah", type=float, help="capacity the design currently claims; checked against the fit")
    ap.add_argument("--stepped", action="store_true", help="allow one step (L/T shape); custom cells only")
    ap.add_argument("--min-step-width", type=float, default=5.0, help="minimum width of a step, mm")
    ap.add_argument("--min-step-depth", type=float, default=2.0, help="minimum depth of a step, mm")
    ap.add_argument("--angle", type=float, help="fix the cell rotation (deg) instead of searching")
    ap.add_argument("--res", type=float, default=0.05, help="final grid resolution, mm (default 0.05)")
    ap.add_argument("--svg-out", help="write a top-view SVG of pocket and cell")
    ap.add_argument("--json", help="write results JSON (e.g. hw/power/battery.json)")
    a = ap.parse_args()

    height = a.height
    if a.rect:
        W0, L0 = a.rect
        poly = [(-W0 / 2, -L0 / 2), (W0 / 2, -L0 / 2), (W0 / 2, L0 / 2), (-W0 / 2, L0 / 2)]
        src = f"rect {W0} x {L0} mm"
    elif a.polygon:
        d = json.load(open(a.polygon))
        poly = [tuple(p) for p in d["pocket"]]
        height = height or d.get("height_mm")
        src = a.polygon
    else:
        poly, sc = parse_svg(a.svg, a.svg_scale)
        src = f"{a.svg} (scale {sc:.4g} mm/unit)"
    if not height:
        raise SystemExit("--height is required (or height_mm in the polygon JSON)")
    if area(poly) < 0:
        poly = poly[::-1]
    A_pocket = area(poly)

    # rotation search: coarse, then fine around the best, then final resolution
    if a.angle is not None:
        best = fit(poly, a.res, a.clearance, [a.angle], a.stepped, a.min_step_width, a.min_step_depth)
    else:
        coarse = fit(poly, 0.2, a.clearance, range(0, 180, 3), a.stepped, a.min_step_width, a.min_step_depth)
        fine = fit(poly, 0.1, a.clearance, [coarse["angle"] + d * 0.5 for d in range(-6, 7)], a.stepped,
                   a.min_step_width, a.min_step_depth)
        best = fit(poly, a.res, a.clearance, [fine["angle"]], a.stepped, a.min_step_width, a.min_step_depth)
        # a cell square to the product's axes is easier to draw, place and tolerance: keep it unless a
        # rotated cell is clearly (> 3 %) larger
        aligned = fit(poly, a.res, a.clearance, [0.0], a.stepped, a.min_step_width, a.min_step_depth)
        if aligned and best and best["area_total"] <= 1.03 * aligned["area_total"]:
            best = aligned
    if best is None:
        raise SystemExit("no cell fits in this pocket with these clearances")

    W, L = best["W"], best["L"]
    # tab side: put tabs on the side that loses the least active area
    tabz = a.tab_seal + a.pcm
    opt1 = max(W - 2 * a.side_seal, 0) * max(L - tabz - a.bottom_seal, 0)   # tabs on a W edge (+/-y)
    opt2 = max(L - 2 * a.side_seal, 0) * max(W - tabz - a.bottom_seal, 0)   # tabs on an L edge (+/-x)
    act_main, tab_axis = (opt1, "y") if opt1 >= opt2 else (opt2, "x")
    ext = best["ext"]
    act_ext = 0.0
    ext_dims = None
    if ext:
        _, side, i0, i1, dcells = ext
        ew, ed = (i1 - i0) * best["h"], dcells * best["h"]
        act_ext = max(ew - 2 * a.side_seal, 0) * max(ed - a.bottom_seal, 0)
        ext_dims = dict(side=side, width_mm=round(ew, 2), depth_mm=round(ed, 2))
    corner_loss = (4 - math.pi) * a.corner_radius ** 2 * (4 if ext else 1)
    A_cell = W * L + (ext[0] if ext else 0) - corner_loss
    A_act = act_main + act_ext
    T = (height - a.z_clearance - a.thick_tol) / (1 + a.swell)
    if T <= 0.3:
        raise SystemExit(f"cell thickness would be {T:.2f} mm: the pocket is too shallow for a pouch cell")
    V_env = A_cell * T / 1000.0       # cm3 = mL
    V_act = A_act * T / 1000.0
    chem = a.chem if a.chem != "auto" else ("pouch-small" if V_env < 1.5 else "pouch")
    C = dict(CHEM[chem])
    if a.density:
        C["env"] = tuple(a.density)
    vnom = a.vnom or C["vnom"]

    def mah(vol_ml, dens):
        return vol_ml / 1000.0 * dens / vnom * 1000.0

    A_lo, A_hi = mah(V_env, C["env"][0]), mah(V_env, C["env"][1])
    B_lo, B_hi = mah(V_act, C["act"][0]), mah(V_act, C["act"][1])
    lo, hi = min(A_lo, B_lo), min(A_hi, B_hi)
    seal_frac = 1 - A_act / A_cell if A_cell > 0 else 1
    fill = A_cell / A_pocket

    notes = []
    if seal_frac > 0.30:
        notes.append(f"seals and tabs take {seal_frac:.0%} of the outline: small cells lose a large share to their border")
    if ext:
        notes.append("stepped outline: custom cell only (tooling + MOQ); a plain rectangle is cheaper and faster")
    if a.claimed_mah:
        if a.claimed_mah > hi:
            notes.append(f"CLAIM {a.claimed_mah:.0f} mAh is ABOVE the realistic range {lo:.0f}-{hi:.0f} mAh: "
                         "not doable without a vendor quote proving it")
        elif a.claimed_mah > (lo + hi) / 2:
            notes.append(f"claim {a.claimed_mah:.0f} mAh is in the optimistic half of {lo:.0f}-{hi:.0f} mAh: plan on the low end")
    notes.append("densities are [estimate]; confirm with 2-3 cell vendors (drawing + capacity + MOQ + tooling + UN38.3)")

    print(f"Pocket: {src}, area {A_pocket:.1f} mm2, height {height} mm")
    print(f"Cell outline: {W:.2f} x {L:.2f} mm at {best['angle']:.1f} deg" +
          (f" + step {ext_dims['width_mm']} x {ext_dims['depth_mm']} mm on {ext_dims['side']}" if ext else "") +
          f"; area {A_cell:.1f} mm2 ({fill:.0%} of pocket); tabs on a {'W' if tab_axis == 'y' else 'L'} edge")
    print(f"Thickness: {T:.2f} mm nominal max (height {height} - z clear {a.z_clearance} - tol {a.thick_tol}, "
          f"/ (1 + swell {a.swell:.0%}))")
    print(f"Volume: envelope {V_env * 1000:.0f} mm3, active {V_act * 1000:.0f} mm3 (seals/tabs {seal_frac:.0%})")
    print(f"Class {chem} ({C['note']}), {vnom} V: A envelope {A_lo:.0f}-{A_hi:.0f} mAh, B active {B_lo:.0f}-{B_hi:.0f} mAh")
    for n in notes:
        print("NOTE:", n)
    print(f"SUMMARY realistic capacity {lo:.0f}-{hi:.0f} mAh [estimate], cell {W:.1f} x {L:.1f} x {T:.2f} mm")

    # outline polygon(s) back in pocket coordinates
    h, x0, y0 = best["h"], best["x0"], best["y0"]
    c0, c1, r0, r1 = best["rect"]
    cx = lambda i: x0 + (i + 0.5) * h
    cy = lambda j: y0 + (j + 0.5) * h
    ang = math.radians(best["angle"])
    main_r = [(cx(c0), cy(r0)), (cx(c1), cy(r0)), (cx(c1), cy(r1)), (cx(c0), cy(r1))]
    ext_r = None
    if ext:
        _, side, i0, i1, dcl = ext
        if side == "+y":
            ext_r = [(cx(i0), cy(r1)), (cx(i1), cy(r1)), (cx(i1), cy(r1) + dcl * h), (cx(i0), cy(r1) + dcl * h)]
        elif side == "-y":
            ext_r = [(cx(i0), cy(r0) - dcl * h), (cx(i1), cy(r0) - dcl * h), (cx(i1), cy(r0)), (cx(i0), cy(r0))]
        elif side == "+x":
            ext_r = [(cx(c1), cy(i0)), (cx(c1) + dcl * h, cy(i0)), (cx(c1) + dcl * h, cy(i1)), (cx(c1), cy(i1))]
        else:
            ext_r = [(cx(c0) - dcl * h, cy(i0)), (cx(c0), cy(i0)), (cx(c0), cy(i1)), (cx(c0) - dcl * h, cy(i1))]
    # active area of the main rectangle (tab zone on the side chosen above)
    (ax0, ay0), (ax1, ay1) = main_r[0], main_r[2]
    if tab_axis == "y":
        act_r = [(ax0 + a.side_seal, ay0 + a.bottom_seal), (ax1 - a.side_seal, ay0 + a.bottom_seal),
                 (ax1 - a.side_seal, ay1 - tabz), (ax0 + a.side_seal, ay1 - tabz)]
        tab_line = [(ax0 + a.side_seal, ay1 - 0.3), (ax1 - a.side_seal, ay1 - 0.3)]
    else:
        act_r = [(ax0 + a.bottom_seal, ay0 + a.side_seal), (ax1 - tabz, ay0 + a.side_seal),
                 (ax1 - tabz, ay1 - a.side_seal), (ax0 + a.bottom_seal, ay1 - a.side_seal)]
        tab_line = [(ax1 - 0.3, ay0 + a.side_seal), (ax1 - 0.3, ay1 - a.side_seal)]
    act_ext_r = None
    if ext_r:
        (ex0, ey0), (ex1, ey1) = ext_r[0], ext_r[2]
        s_, b_ = a.side_seal, a.bottom_seal
        # the step joins the main cell on one side; its far side has a seal, its two flanks have side seals
        act_ext_r = {"+y": [(ex0 + s_, ey0), (ex1 - s_, ey0), (ex1 - s_, ey1 - b_), (ex0 + s_, ey1 - b_)],
                     "-y": [(ex0 + s_, ey0 + b_), (ex1 - s_, ey0 + b_), (ex1 - s_, ey1), (ex0 + s_, ey1)],
                     "+x": [(ex0, ey0 + s_), (ex1 - b_, ey0 + s_), (ex1 - b_, ey1 - s_), (ex0, ey1 - s_)],
                     "-x": [(ex0 + b_, ey0 + s_), (ex1, ey0 + s_), (ex1, ey1 - s_), (ex0 + b_, ey1 - s_)]}[ext[1]]
    back = lambda pts: rot(pts, ang)
    out_main, out_ext, out_act, out_tab = back(main_r), back(ext_r) if ext_r else None, back(act_r), back(tab_line)
    out_act_ext = back(act_ext_r) if act_ext_r else None

    result = dict(pocket_source=src, pocket_area_mm2=round(A_pocket, 2), height_mm=height,
                  cell=dict(outline_mm=[[round(x, 3), round(y, 3)] for x, y in out_main],
                            step_outline_mm=[[round(x, 3), round(y, 3)] for x, y in out_ext] if out_ext else None,
                            width_mm=round(W, 2), length_mm=round(L, 2), step=ext_dims, angle_deg=best["angle"],
                            thickness_mm=round(T, 3), area_mm2=round(A_cell, 2), fill_of_pocket=round(fill, 3),
                            tab_edge="W" if tab_axis == "y" else "L"),
                  volume_mm3=dict(envelope=round(V_env * 1000, 1), active=round(V_act * 1000, 1)),
                  seal_fraction=round(seal_frac, 3), chem=chem, vnom=vnom,
                  density_whl=dict(envelope=C["env"], active=C["act"], evidence="[estimate: cell-class range; replace with vendor quote]"),
                  capacity_mah=dict(low=round(lo, 1), high=round(hi, 1), method_A=[round(A_lo, 1), round(A_hi, 1)],
                                    method_B=[round(B_lo, 1), round(B_hi, 1)], evidence="[estimate]"),
                  params=dict(clearance=a.clearance, z_clearance=a.z_clearance, thick_tol=a.thick_tol, swell=a.swell,
                              tab_seal=a.tab_seal, side_seal=a.side_seal, bottom_seal=a.bottom_seal, pcm=a.pcm,
                              corner_radius=a.corner_radius),
                  claimed_mah=a.claimed_mah, notes=notes)
    if a.json:
        json.dump(result, open(a.json, "w"), indent=1)
    if a.svg_out:
        write_svg(a.svg_out, poly, out_main, out_ext, out_act, out_tab, result, out_act_ext)
    return 1 if (a.claimed_mah and a.claimed_mah > hi) else 0


def write_svg(path, pocket, cell, ext, act, tab, r, act_ext=None):
    pts = pocket + cell + (ext or [])
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    pad = 0.12 * max(max(xs) - min(xs), max(ys) - min(ys)) + 2
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    W, H = x1 - x0, y1 - y0
    S = 600.0 / max(W, H)                       # px per mm
    head = 64
    X = lambda x: (x - x0) * S
    Y = lambda y: head + (y1 - y) * S           # mm y up -> SVG y down
    P = lambda poly: " ".join(f"{X(x):.2f},{Y(y):.2f}" for x, y in poly)
    c = r["cell"]; cap = r["capacity_mah"]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * S:.0f}" height="{H * S + head + 48:.0f}" '
         f'viewBox="0 0 {W * S:.0f} {H * S + head + 48:.0f}" font-family="Helvetica Neue, Helvetica, Arial, sans-serif">',
         f'<rect width="100%" height="100%" fill="#fbfbfa"/>',
         f'<text x="16" y="26" font-size="17" font-weight="600" fill="#151515">Cell {c["width_mm"]} × {c["length_mm"]} × '
         f'{c["thickness_mm"]:.2f} mm' + (f' + step {c["step"]["width_mm"]} × {c["step"]["depth_mm"]} mm' if c["step"] else "")
         + f' · {cap["low"]:.0f}–{cap["high"]:.0f} mAh (estimate)</text>',
         f'<text x="16" y="48" font-size="12" fill="#666">Fill {c["fill_of_pocket"]:.0%} of pocket · seals/tabs '
         f'{r["seal_fraction"]:.0%} of outline · class {r["chem"]} · tabs on {c["tab_edge"]} edge</text>',
         f'<polygon points="{P(pocket)}" fill="none" stroke="#151515" stroke-width="1.6"/>',
         f'<polygon points="{P(cell)}" fill="#e3e6ea" stroke="#3d4a5c" stroke-width="1.2"/>']
    if ext:
        o.append(f'<polygon points="{P(ext)}" fill="#e3e6ea" stroke="#3d4a5c" stroke-width="1.2"/>')
    o.append(f'<polygon points="{P(act)}" fill="#b9c3cf" stroke="none"/>')
    if act_ext:
        o.append(f'<polygon points="{P(act_ext)}" fill="#b9c3cf" stroke="none"/>')
    o.append(f'<polyline points="{P(tab)}" fill="none" stroke="#d0402b" stroke-width="3" stroke-linecap="round"/>')
    # 5 mm scale bar, then the legend on its own line
    sb = 5 * S
    yb = head + H * S + 14
    o.append(f'<line x1="16" y1="{yb}" x2="{16 + sb:.1f}" y2="{yb}" stroke="#151515" stroke-width="2"/>')
    o.append(f'<text x="{22 + sb:.1f}" y="{yb + 4}" font-size="12" fill="#151515">5 mm</text>')
    xx, yl = 16.0, yb + 22
    for col, lab, line in (("#151515", "pocket", True), ("#e3e6ea", "cell outline incl. seals", False),
                           ("#b9c3cf", "active area", False), ("#d0402b", "tab edge", True)):
        if line:
            o.append(f'<line x1="{xx:.0f}" y1="{yl - 3}" x2="{xx + 14:.0f}" y2="{yl - 3}" stroke="{col}" stroke-width="2.4"/>')
        else:
            o.append(f'<rect x="{xx:.0f}" y="{yl - 8}" width="14" height="10" fill="{col}" stroke="#3d4a5c" stroke-width="0.6"/>')
        o.append(f'<text x="{xx + 20:.0f}" y="{yl + 1}" font-size="11" fill="#444">{lab}</text>')
        xx += 20 + 6.2 * len(lab) + 18
    o.append("</svg>")
    open(path, "w").write("\n".join(o))


if __name__ == "__main__":
    sys.exit(main())
