"""Board outlines as polygons (mm, device frame: origin at the board center, +x right, +y up, CCW).

Outline spec forms (in board.json, key "outline"):
  {"type": "circle", "r": 10}                                   optional "x", "y", "n" (segments)
  {"type": "rounded_rect", "w": 20, "h": 14, "r": 2}
  {"type": "polygon", "points": [[x, y], ...]}
  {"type": "svg", "file": "outline.svg", "size": 19.2}          first <path>, scaled so its larger side = size mm,
                                                                 centered; or "scale": mm per SVG unit
  {"type": "union", "fillet": 0.6, "shapes": [{"circle": [x, y, r]}, {"rect": [x0, y0, x1, y1]}, ...]}
       smooth union (no sharp inner corners; flex boards tear at sharp corners)
Any form accepts "inset": d (mm, shrink inward) and "scale": k (uniform scale after building).

Pure Python 3.9+.
"""
import math
import os
import re


# ---------------------------------------------------------------- geometry helpers

def area(poly):
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))


def ccw(poly):
    return poly if area(poly) > 0 else poly[::-1]


def inside(poly, x, y):
    c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def edge_dist(poly, x, y):
    best = 1e9
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x1 - x0, y1 - y0
        t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy or 1e-12)))
        best = min(best, math.hypot(x - x0 - t * dx, y - y0 - t * dy))
    return best


def signed_dist(poly, x, y):
    d = edge_dist(poly, x, y)
    return -d if inside(poly, x, y) else d


def bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def resample(pts, n):
    """n points evenly spaced along the closed polyline."""
    acc = [0.0]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        acc.append(acc[-1] + math.dist(a, b))
    total, out, j = acc[-1], [], 0
    for k in range(n):
        s = total * k / n
        while acc[j + 1] < s:
            j += 1
        a, b = pts[j], pts[(j + 1) % len(pts)]
        f = (s - acc[j]) / ((acc[j + 1] - acc[j]) or 1e-12)
        out.append((a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])))
    return out


def simplify(pts, tol=0.01):
    """Ramer-Douglas-Peucker on a closed loop."""
    if len(pts) < 4:
        return pts

    def rdp(p):
        if len(p) < 3:
            return p
        a, b = p[0], p[-1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1e-12
        dmax, idx = 0.0, 0
        for i in range(1, len(p) - 1):
            d = abs(dy * (p[i][0] - a[0]) - dx * (p[i][1] - a[1])) / n
            if d > dmax:
                dmax, idx = d, i
        if dmax > tol:
            return rdp(p[:idx + 1])[:-1] + rdp(p[idx:])
        return [a, b]

    half = len(pts) // 2
    return rdp(pts[:half + 1])[:-1] + rdp(pts[half:] + [pts[0]])[:-1]


def contour(f, x0, y0, x1, y1, step=0.05):
    """Marching squares: the longest closed loop of f(x, y) = 0 (f < 0 inside)."""
    nx, ny = int((x1 - x0) / step) + 2, int((y1 - y0) / step) + 2
    g = [[f(x0 + i * step, y0 + j * step) for j in range(ny)] for i in range(nx)]
    segs = {}

    def interp(i0, j0, i1, j1):
        a, b = g[i0][j0], g[i1][j1]
        t = a / (a - b)
        return (round(x0 + (i0 + t * (i1 - i0)) * step, 5), round(y0 + (j0 + t * (j1 - j0)) * step, 5))

    for i in range(nx - 1):
        for j in range(ny - 1):
            c = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            ins = [g[a][b] < 0 for a, b in c]
            pts = []
            for e in range(4):
                (a0, b0), (a1, b1) = c[e], c[(e + 1) % 4]
                if ins[e] != ins[(e + 1) % 4]:
                    pts.append(interp(a0, b0, a1, b1))
            pairs = [(pts[0], pts[1])] if len(pts) == 2 else ([(pts[0], pts[1]), (pts[2], pts[3])] if len(pts) == 4 else [])
            for p, q in pairs:
                segs.setdefault(p, []).append(q)
                segs.setdefault(q, []).append(p)
    loops, seen = [], set()
    for start in segs:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [p for p in segs[cur] if p != prev and p not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        loops.append(loop)
    if not loops:
        raise ValueError("outline: empty contour")
    return ccw(simplify(max(loops, key=len), 0.005))


def offset(poly, d, step=None):
    """Inset (d > 0) or outset (d < 0) a polygon via its signed distance field."""
    x0, y0, x1, y1 = bbox(poly)
    m = abs(d) + 0.5
    span = max(x1 - x0, y1 - y0)
    step = step or max(0.03, span / 300)
    return contour(lambda x, y: signed_dist(poly, x, y) + d, x0 - m, y0 - m, x1 + m, y1 + m, step)


# ---------------------------------------------------------------- SVG path import

_NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_CMD = re.compile(r"([MmLlHhVvCcSsQqTtZzAa])([^MmLlHhVvCcSsQqTtZzAa]*)")


def svg_path_points(d, per_curve=24):
    """Sample an SVG path `d` (M L H V C S Q T Z, absolute or relative; arcs approximated by lines)."""
    pts, cur, start, prev_c = [], (0.0, 0.0), (0.0, 0.0), None
    for cmd, args in _CMD.findall(d):
        v = [float(x) for x in _NUM.findall(args)]
        rel = cmd.islower()
        c = cmd.upper()

        def P(x, y):
            return (cur[0] + x, cur[1] + y) if rel else (x, y)

        if c == "Z":
            cur = start
            prev_c = None
            continue
        if c == "M":
            for i in range(0, len(v), 2):
                cur = P(v[i], v[i + 1])
                if i == 0:
                    start = cur
                pts.append(cur)
            prev_c = None
        elif c == "L" or c == "T":
            for i in range(0, len(v), 2):
                cur = P(v[i], v[i + 1])
                pts.append(cur)
            prev_c = None
        elif c == "H":
            for x in v:
                cur = (cur[0] + x if rel else x, cur[1])
                pts.append(cur)
        elif c == "V":
            for y in v:
                cur = (cur[0], cur[1] + y if rel else y)
                pts.append(cur)
        elif c in ("C", "S", "Q"):
            n = {"C": 6, "S": 4, "Q": 4}[c]
            for i in range(0, len(v), n):
                p0 = cur
                if c == "C":
                    p1, p2, p3 = P(v[i], v[i + 1]), P(v[i + 2], v[i + 3]), P(v[i + 4], v[i + 5])
                elif c == "S":
                    p1 = (2 * p0[0] - prev_c[0], 2 * p0[1] - prev_c[1]) if prev_c else p0
                    p2, p3 = P(v[i], v[i + 1]), P(v[i + 2], v[i + 3])
                else:
                    q, p3 = P(v[i], v[i + 1]), P(v[i + 2], v[i + 3])
                    p1 = (p0[0] + 2 / 3 * (q[0] - p0[0]), p0[1] + 2 / 3 * (q[1] - p0[1]))
                    p2 = (p3[0] + 2 / 3 * (q[0] - p3[0]), p3[1] + 2 / 3 * (q[1] - p3[1]))
                for k in range(1, per_curve + 1):
                    t = k / per_curve
                    u = 1 - t
                    pts.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                                u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
                prev_c, cur = p2, p3
        elif c == "A":
            for i in range(0, len(v), 7):
                cur = P(v[i + 5], v[i + 6])
                pts.append(cur)
    # drop duplicates
    out = []
    for p in pts:
        if not out or math.dist(p, out[-1]) > 1e-9:
            out.append(p)
    if len(out) > 1 and math.dist(out[0], out[-1]) < 1e-9:
        out.pop()
    return out


def from_svg(path, size=None, scale=None, path_index=0):
    text = open(path, encoding="utf-8").read()
    ds = re.findall(r'<path[^>]*?\sd="([^"]+)"', text, re.S)
    if not ds:
        raise ValueError("%s: no <path d=...>" % path)
    pts = svg_path_points(ds[path_index])
    x0, y0, x1, y1 = bbox(pts)
    k = scale if scale else (size / max(x1 - x0, y1 - y0) if size else 1.0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return ccw([((x - cx) * k, (cy - y) * k) for x, y in pts])      # SVG y is down


# ---------------------------------------------------------------- shapes

def circle(r, x=0.0, y=0.0, n=96):
    return [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rounded_rect(w, h, r, n=12):
    r = min(r, w / 2, h / 2)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _sd_shape(s, x, y, fillet):
    if "circle" in s:
        cx, cy, r = s["circle"]
        return math.hypot(x - cx, y - cy) - r
    if "rect" in s:
        x0, y0, x1, y1 = s["rect"]
        r = min(fillet, (x1 - x0) / 2, (y1 - y0) / 2)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hx, hy = (x1 - x0) / 2 - r, (y1 - y0) / 2 - r
        qx, qy = abs(x - cx) - hx, abs(y - cy) - hy
        return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - r
    if "polygon" in s:
        return signed_dist([tuple(p) for p in s["polygon"]], x, y)
    raise ValueError("union shape must be circle, rect or polygon: %r" % s)


def _smin(a, b, k):
    if k <= 0:
        return min(a, b)
    h = max(k - abs(a - b), 0) / k
    return min(a, b) - h * h * k * 0.25


def round_corners(poly, r):
    """Round every corner of a polygon with radius r: closing (outset, inset) rounds the concave corners,
    opening (inset, outset) rounds the convex ones."""
    if r <= 0:
        return poly
    p = offset(offset(poly, -r), r)
    return offset(offset(p, r), -r)


def union(shapes, fillet=0.6, step=0.05):
    # rects carry their own corner radius in _sd_shape; polygons are rounded once here, so every corner of the
    # union is rounded, not only rect corners and joins
    shapes = [({"polygon": round_corners(ccw([tuple(map(float, q)) for q in s["polygon"]]), fillet)}
               if "polygon" in s and fillet > 0 else s) for s in shapes]

    def f(x, y):
        d = None
        for s in shapes:
            v = _sd_shape(s, x, y, fillet)
            d = v if d is None else _smin(d, v, fillet)
        return d

    xs, ys = [], []
    for s in shapes:
        if "circle" in s:
            cx, cy, r = s["circle"]
            xs += [cx - r, cx + r]
            ys += [cy - r, cy + r]
        elif "rect" in s:
            xs += [s["rect"][0], s["rect"][2]]
            ys += [s["rect"][1], s["rect"][3]]
        else:
            xs += [p[0] for p in s["polygon"]]
            ys += [p[1] for p in s["polygon"]]
    m = fillet + 0.5
    return contour(f, min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m, step)


def build(spec, base_dir="."):
    t = spec.get("type")
    if t == "circle":
        poly = circle(spec["r"], spec.get("x", 0.0), spec.get("y", 0.0), spec.get("n", 96))
    elif t == "rounded_rect":
        poly = rounded_rect(spec["w"], spec["h"], spec.get("r", 0.0))
    elif t == "polygon":
        poly = ccw([tuple(map(float, p)) for p in spec["points"]])
    elif t == "svg":
        poly = from_svg(os.path.join(base_dir, spec["file"]), spec.get("size"), spec.get("svg_scale"),
                        spec.get("path_index", 0))
        if spec.get("n"):
            poly = resample(poly, spec["n"])
    elif t == "union":
        poly = union(spec["shapes"], spec.get("fillet", 0.6), spec.get("step", 0.05))
    else:
        raise ValueError("unknown outline type %r" % t)
    if spec.get("scale"):
        k = float(spec["scale"])
        poly = [(x * k, y * k) for x, y in poly]
    if spec.get("inset"):
        poly = offset(poly, float(spec["inset"]))
    return ccw(poly)


def shape_polygon(s, n=48):
    if "circle" in s:
        cx, cy, r = s["circle"]
        return circle(r, cx, cy, n)
    if "rect" in s:
        x0, y0, x1, y1 = s["rect"]
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [tuple(p) for p in s["polygon"]]


def bbox_polys(polys):
    xs = [x for p in polys for x, _ in p]
    ys = [y for p in polys for _, y in p]
    return min(xs), min(ys), max(xs), max(ys)


def move_polys(polys, dx, dy):
    return [[(x + dx, y + dy) for x, y in p] for p in polys]


def seg_dist(a, b, c, d):
    """Distance between segments ab and cd (0 if they cross)."""
    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])

    d1, d2, d3, d4 = cross(c, d, a), cross(c, d, b), cross(a, b, c), cross(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0

    def pd(p, q, r):
        dx, dy = r[0] - q[0], r[1] - q[1]
        t = max(0.0, min(1.0, ((p[0] - q[0]) * dx + (p[1] - q[1]) * dy) / (dx * dx + dy * dy or 1e-12)))
        return math.hypot(p[0] - q[0] - t * dx, p[1] - q[1] - t * dy)

    return min(pd(a, c, d), pd(b, c, d), pd(c, a, b), pd(d, a, b))


def poly_gap(A, B):
    """0 if polygons A and B overlap (or touch), else the distance between them."""
    if any(inside(B, *pt) for pt in A) or any(inside(A, *pt) for pt in B):
        return 0.0
    best = 1e9
    for a, b in zip(A, A[1:] + A[:1]):
        for c, d in zip(B, B[1:] + B[:1]):
            best = min(best, seg_dist(a, b, c, d))
            if best == 0.0:
                return 0.0
    return best


def polys_overlap(PA, PB, gap=0.0):
    ax0, ay0, ax1, ay1 = bbox_polys(PA)
    bx0, by0, bx1, by1 = bbox_polys(PB)
    if not (ax0 < bx1 + gap and bx0 < ax1 + gap and ay0 < by1 + gap and by0 < ay1 + gap):
        return False
    return any(poly_gap(a, b) < max(gap, 1e-9) for a in PA for b in PB)


def shape_hits_polys(s, polys):
    if "circle" in s:
        cx, cy, r = s["circle"]
        return any(inside(p, cx, cy) or edge_dist(p, cx, cy) < r for p in polys)
    return polys_overlap([shape_polygon(s)], polys)


def shape_hits_rect(s, rect):
    x0, y0, x1, y1 = rect
    return shape_hits_polys(s, [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]])


def inside_outline(polys, poly, margin):
    for p in polys:
        for x, y in p:
            if not inside(poly, x, y) or edge_dist(poly, x, y) < margin:
                return False
        if any(inside(p, x, y) for x, y in poly):
            return False
    return True


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Print an outline polygon built from a JSON outline spec.")
    ap.add_argument("spec", help='JSON string or file, e.g. \'{"type": "circle", "r": 10}\'')
    a = ap.parse_args()
    s = json.load(open(a.spec)) if os.path.exists(a.spec) else json.loads(a.spec)
    p = build(s, os.path.dirname(os.path.abspath(a.spec)) if os.path.exists(a.spec) else ".")
    x0, y0, x1, y1 = bbox(p)
    print(json.dumps([[round(x, 4), round(y, 4)] for x, y in p]))
    print("outline: %d points, %.2f x %.2f mm, area %.1f mm2" % (len(p), x1 - x0, y1 - y0, area(p)))
