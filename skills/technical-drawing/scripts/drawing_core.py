"""Shared engine for the technical-drawing scripts (runs inside headless Blender).

Geometry: evaluated meshes -> one reference frame in millimetres -> feature edges (silhouette, boundary,
crease) with vertices merged by position -> visibility by ray casting along each edge -> 2D projection.
Sheet: SVG helpers for frame, title block, wrapped tables, and PDF/PNG export through rsvg-convert.

Tested with Blender 5.2 (also expected to work on 4.2+). Uses only bpy, mathutils and numpy.
"""
import datetime
import json
import math
import os
import shutil
import subprocess
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

# ------------------------------------------------------------------------------------------------ config
SHEETS = {  # paper size in mm (landscape)
    "A4": (297.0, 210.0), "A3": (420.0, 297.0), "A2": (594.0, 420.0),
    "LETTER": (279.4, 215.9), "TABLOID": (431.8, 279.4),
}
VW = 420.0  # every sheet is laid out in a 420-unit-wide virtual space, then scaled to the paper

THEMES = {
    "blueprint": dict(bg="#123a6b", ink="#eaf2ff", ink2="#b9cdee", grid="#1b4a83", accent="#ffd36a"),
    "print": dict(bg="#ffffff", ink="#111111", ink2="#4a4a4a", grid=None, accent="#d0402b"),
}

DEFAULTS = {
    "frame_object": None,          # object whose local frame is the drawing frame (None = world)
    "root": None,                  # only meshes under this object (None = whole scene)
    "mm_per_unit": None,           # None = from scene unit scale (scale_length * 1000)
    "skip_prefixes": ["Solder", "Marking", "Label", "Light", "Fiber"],
    "unit_ignore_prefixes": ["Node", "=>", "Root", "Scene"],
    "groups": [],                  # [{"name", "offset_mm", "fine", "match": {...}}]
    "explode_axis": "z",
    "items": [],                   # [{"id", "name", "spec", "qty", "envelope", "fine", "match": {...}}]
    "view": {"azimuth_deg": 35.0, "elevation_deg": 24.0},
    "sheet": "A3",
    "themes": ["blueprint", "print"],
    "font": "Inter, Helvetica Neue, Helvetica, Arial, sans-serif",
    "decimal": ".",
    "crease_deg": 35.0,
    "edge_sample": None,           # mm between visibility rays (None = model diagonal / 400)
    "standard_scale": True,        # snap to ISO 5455 scales (10:1, 5:1, 2:1, 1:1, 1:2 ...)
    "hidden_lines": False,         # ortho views: draw hidden edges dashed (clutters assemblies; use for parts)
    "projection": "third",         # ortho views: "third" (US) or "first" (ISO E)
    "title": {},
    "footer": "Hidden lines removed. Electronic parts shown as manufacturer 3D envelopes. "
              "Reference dimensions in mm; general tolerances ISO 2768-f unless stated.",
    "labels": {},
    "ortho_include": None,         # ortho views: group names to draw (None = all groups; e.g. only exterior parts)
    "ortho_themes": None,          # ortho views: themes (None = "themes")
    "line_clean": {"enabled": True, "tol_mm": 0.3, "maxlen_mm": 2.0},   # ortho: remove seam ticks (paper mm)
}
LABELS = {
    "bom": "BILL OF MATERIALS", "item": "Item", "description": "Description", "spec": "Specification",
    "qty": "Qty", "size": "Overall size", "scale": "Scale", "units": "Units", "revision": "Revision",
    "date": "Date", "sheet": "Sheet", "envelope": "envelope", "envelope_each": "envelope (each)",
    "envelopes": "envelopes", "front": "FRONT", "top": "TOP", "right": "RIGHT SIDE", "left": "LEFT SIDE",
    "iso": "ISOMETRIC (NOT TO SCALE)", "third": "Third-angle projection", "first": "First-angle projection",
}


def script_args():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def load_config(path):
    cfg = json.loads(json.dumps(DEFAULTS))
    if path:
        with open(path) as f:
            user = json.load(f)
        for k, v in user.items():
            if k in ("view", "title", "labels") and isinstance(v, dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    lab = dict(LABELS)
    lab.update(cfg["labels"])
    cfg["labels"] = lab
    cfg["sheet"] = cfg["sheet"].upper()
    if cfg["sheet"] not in SHEETS:
        raise SystemExit(f"unknown sheet {cfg['sheet']}; use one of {sorted(SHEETS)}")
    return cfg


# ------------------------------------------------------------------------------------------------ matching
def base(name):
    return name.split(".")[0]


class Matcher:
    """Rule = {"all": true} or any of names / prefixes / collections / ancestors (OR)."""

    def __init__(self):
        self.cols = {}
        for c in bpy.data.collections:
            for o in c.all_objects:
                self.cols.setdefault(o.name, set()).add(c.name)

    def match(self, o, rule):
        if not rule:
            return False
        if rule.get("all"):
            return True
        if base(o.name) in rule.get("names", ()):
            return True
        if any(o.name.startswith(p) for p in rule.get("prefixes", ())):
            return True
        if self.cols.get(o.name, set()) & set(rule.get("collections", ())):
            return True
        anc = set(rule.get("ancestors", ()))
        a = o
        while anc and a is not None:
            if base(a.name) in anc:
                return True
            a = a.parent
        return False

    def first(self, o, rules):
        for r in rules:
            if self.match(o, r.get("match")):
                return r
        return None


# ------------------------------------------------------------------------------------------------ geometry
def frame_inverse(cfg):
    name = cfg.get("frame_object")
    if not name:
        return Matrix.Identity(4)
    ob = bpy.data.objects.get(name)
    if ob is None:
        raise SystemExit(f"frame_object '{name}' not found")
    bpy.context.view_layer.update()
    return ob.matrix_world.inverted()


def mm_per_unit(cfg):
    if cfg.get("mm_per_unit"):
        return float(cfg["mm_per_unit"])
    us = bpy.context.scene.unit_settings
    return (us.scale_length if us.system != 'NONE' else 1.0) * 1000.0


def candidate_objects(cfg):
    root = bpy.data.objects.get(cfg["root"]) if cfg.get("root") else None
    if cfg.get("root") and root is None:
        raise SystemExit(f"root '{cfg['root']}' not found")
    pool = root.children_recursive if root else bpy.context.scene.objects
    out = []
    for o in pool:
        if o.type != 'MESH' or o.hide_render:
            continue
        if any(c.hide_render for c in o.users_collection):
            continue
        if any(o.name.startswith(p) for p in cfg["skip_prefixes"]):
            continue
        out.append(o)
    return out


def _edges(W, lt, ls_, lv, qtol):
    """Unique edges after merging vertices by position (fixes 'hatched' outlines on split-normal meshes)."""
    q = np.round(W / qtol).astype(np.int64)
    _, uid = np.unique(q, axis=0, return_inverse=True)
    uid = uid.ravel()
    nxt = np.arange(len(lv)) + 1
    nxt[ls_ + lt - 1] = ls_
    lp = np.repeat(np.arange(len(lt)), lt)
    a, b = uid[lv], uid[lv[nxt]]
    ok = a != b
    lo, hi = np.minimum(a, b)[ok], np.maximum(a, b)[ok]
    key = lo * (int(uid.max()) + 1) + hi
    uk, inv = np.unique(key, return_inverse=True)
    inv = inv.ravel()
    ne = len(uk)
    ed = np.zeros((ne, 2), np.int64)
    ed[inv, 0] = lv[ok]
    ed[inv, 1] = lv[nxt][ok]
    lpo = lp[ok]
    order = np.argsort(inv, kind="stable")
    invs, lps = inv[order], lpo[order]
    cnt = np.bincount(invs, minlength=ne)
    start = np.r_[0, np.cumsum(cnt)[:-1]]
    f0 = lps[start]
    f1 = np.where(cnt >= 2, lps[np.minimum(start + 1, len(lps) - 1)], -1)
    return ed, cnt, f0, f1


class Scene3D:
    """All drawable meshes in one frame (mm), with groups, items, explode offsets and a BVH."""

    def __init__(self, cfg, explode=True):
        self.cfg = cfg
        M_inv = frame_inverse(cfg)
        k = mm_per_unit(cfg)
        mt = Matcher()
        self.matcher = mt
        ax = "xyz".index(cfg.get("explode_axis", "z").lower())
        dg = bpy.context.evaluated_depsgraph_get()
        raw = []
        for o in candidate_objects(cfg):
            g = mt.first(o, cfg["groups"]) if cfg["groups"] else {"name": "all", "offset_mm": 0.0}
            if g is None:
                continue
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            try:
                if not len(me.polygons):
                    continue
                nv, npo = len(me.vertices), len(me.polygons)
                co = np.empty(nv * 3)
                me.vertices.foreach_get("co", co)
                M = np.array(M_inv @ ev.matrix_world)
                W = (co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]) * k
                pn = np.empty(npo * 3)
                me.polygons.foreach_get("normal", pn)
                Nm = np.linalg.inv(M[:3, :3]).T
                pn = pn.reshape(-1, 3) @ Nm.T
                pn /= np.maximum(np.linalg.norm(pn, axis=1, keepdims=True), 1e-12)
                lt = np.empty(npo, np.int64)
                me.polygons.foreach_get("loop_total", lt)
                ls_ = np.empty(npo, np.int64)
                me.polygons.foreach_get("loop_start", ls_)
                lv = np.empty(len(me.loops), np.int64)
                me.loops.foreach_get("vertex_index", lv)
                me.calc_loop_triangles()
                tri = np.empty(len(me.loop_triangles) * 3, np.int64)
                me.loop_triangles.foreach_get("vertices", tri)
            finally:
                ev.to_mesh_clear()
            off = np.zeros(3)
            if explode:
                off[ax] = float(g.get("offset_mm", 0.0))
            it = mt.first(o, cfg["items"])
            raw.append(dict(o=o, W0=W, W=W + off, off=off, pn=pn, lt=lt, ls=ls_, lv=lv, tri=tri.reshape(-1, 3),
                            group=g.get("name"), item=it["id"] if it else None,
                            fine=bool((it or {}).get("fine", g.get("fine", False)))))
        if not raw:
            raise SystemExit("no meshes matched: check root / groups / skip_prefixes in the config")
        allW = np.concatenate([m["W"] for m in raw])
        allW0 = np.concatenate([m["W0"] for m in raw])
        self.lo, self.hi = allW.min(0), allW.max(0)
        self.size0 = allW0.max(0) - allW0.min(0)           # assembled overall size (mm)
        self.diag = float(np.linalg.norm(self.hi - self.lo))
        qtol = max(self.diag * 2e-6, 1e-5)
        for m in raw:
            m["ed"], m["cnt"], m["f0"], m["f1"] = _edges(m["W"], m["lt"], m["ls"], m["lv"], qtol)
        self.meshes = raw
        V, T, base_i = [], [], 0
        for m in raw:
            V.append(m["W"])
            T.append(m["tri"] + base_i)
            base_i += len(m["W"])
        V, T = np.concatenate(V), np.concatenate(T)
        self.bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
        self.step = float(cfg.get("edge_sample") or self.diag / 400.0)
        self.eps = self.diag * 1.5e-4
        self.nrays = 0

    def visible(self, p, D, nrm=None):
        o = p + D * self.eps + (nrm * self.eps if nrm is not None else 0.0)
        self.nrays += 1
        return self.bvh.ray_cast(Vector(o.tolist()), Vector(D.tolist()), self.diag * 4)[0] is None

    def feature_edges(self, D, hidden=False):
        """Visible (and optionally hidden) 3D segments seen from direction D (target -> camera).
        Returns dict class -> list of (a, b) 3D points; classes contour/detail/fine/hidden."""
        D = np.asarray(D, float) / np.linalg.norm(D)
        cc = math.cos(math.radians(self.cfg["crease_deg"]))
        out = {"contour": [], "detail": [], "fine": [], "hidden": []}
        for m in self.meshes:
            W, pn, ed, cnt, f0, f1 = m["W"], m["pn"], m["ed"], m["cnt"], m["f0"], m["f1"]
            f1m = np.maximum(f1, 0)
            face = pn @ D
            fa = face[f0]
            fb = np.where(f1 >= 0, face[f1m], 0.0)
            boundary, two = cnt == 1, cnt == 2
            # silhouette = front-facing next to not-front-facing; a face seen exactly edge-on (axis views)
            # counts as not front-facing, otherwise outlines of boxes in front/top/side views vanish
            sil = two & ((fa > 1e-6) != (fb > 1e-6))
            crease = two & ((pn[f0] * pn[f1m]).sum(1) < cc)
            front = (fa > -1e-3) | (two & (fb > -1e-3))
            feat = boundary | sil | crease | (cnt > 2)
            keep = feat if hidden else feat & front
            contour = sil | boundary | (cnt > 2)
            nr = pn[f0] + np.where(two[:, None], pn[f1m], 0.0)
            nr /= np.maximum(np.linalg.norm(nr, axis=1, keepdims=True), 1e-9)
            for e in np.nonzero(keep)[0]:
                a, b = W[ed[e, 0]], W[ed[e, 1]]
                L = float(np.linalg.norm(b - a))
                if L < 1e-6:
                    continue
                ns = min(40, max(2, int(math.ceil(L / self.step)) + 1))
                ts = np.linspace(0.0, 1.0, ns)
                vis = [self.visible(a + (b - a) * t, D, nr[e]) for t in ts]
                cls = "fine" if m["fine"] else ("contour" if contour[e] else "detail")
                for want, target in ((True, cls), (False, "hidden")):
                    if not want and not hidden:
                        continue
                    run = None
                    for i, (t, v) in enumerate(zip(ts, vis)):
                        on = v == want
                        if on and run is None:
                            run = t
                        if run is not None and (not on or i == ns - 1):
                            tend = t if on else t - (ts[1] - ts[0]) * 0.5
                            if tend > run:
                                out[target].append((a + (b - a) * run, a + (b - a) * tend))
                            run = None
        return out


def view_basis(az_deg, el_deg):
    """Orthographic camera: D (target -> camera), right R, up U."""
    az, el = math.radians(az_deg), math.radians(el_deg)
    D = np.array([math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az), math.sin(el)])
    up = np.array([0.0, 0.0, 1.0]) if abs(D[2]) < 0.999 else np.array([0.0, 1.0, 0.0])
    R = np.cross(-D, up)
    R /= np.linalg.norm(R)
    U = np.cross(R, -D)
    return D, R, U


def project(segs, R, U):
    """3D segments -> 2D (x right, y down) in mm."""
    return {k: [(a @ R, -(a @ U), b @ R, -(b @ U)) for a, b in v] for k, v in segs.items()}


def standard_scale(fit):
    """Largest ISO 5455 scale not above the fitted one (virtual units per mm handled by caller)."""
    for s in (100, 50, 20, 10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005, 0.002, 0.001):
        if s <= fit:
            return s
    return fit


def scale_label(s, dec="."):
    def f(x):
        t = f"{x:.0f}" if abs(x - round(x)) < 1e-6 else f"{x:.1f}"
        return t.replace(".", dec)
    return f"{f(s)}:1" if s >= 1 else f"1:{f(1 / s)}"


# ------------------------------------------------------------------------------------------------ svg
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def num(x, dec):
    return f"{x:.1f}".replace(".", dec)


def wrap(s, n):
    out, line = [], ""
    for w in str(s).split():
        if line and len(line) + len(w) + 1 > n:
            out.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    out.append(line)
    return out


def chars_fit(width, font, bold=False):
    return max(4, int((width - 2.4) / (font * (0.6 if bold else 0.54))))


class Sheet:
    def __init__(self, cfg, theme):
        self.cfg = cfg
        self.t = THEMES[theme]
        self.pw, self.ph = SHEETS[cfg["sheet"]]
        self.W, self.H = VW, VW * self.ph / self.pw
        self.o = []
        t = self.t
        self.o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.pw}mm" height="{self.ph}mm" '
                      f'viewBox="0 0 {self.W:.2f} {self.H:.2f}" font-family="{esc(cfg["font"])}">')
        self.o.append(f'<rect width="{self.W:.2f}" height="{self.H:.2f}" fill="{t["bg"]}"/>')
        if t["grid"]:
            g = "".join(f'<line x1="{x}" y1="8" x2="{x}" y2="{self.H - 8:.2f}"/>' for x in range(10, int(self.W) - 7, 10))
            g += "".join(f'<line x1="8" y1="{y}" x2="{self.W - 8:.2f}" y2="{y}"/>' for y in range(10, int(self.H) - 7, 10))
            self.o.append(f'<g stroke="{t["grid"]}" stroke-width="0.12">{g}</g>')
        self.o.append(f'<rect x="8" y="8" width="{self.W - 16:.2f}" height="{self.H - 16:.2f}" fill="none" '
                      f'stroke="{t["ink"]}" stroke-width="0.6"/>')

    def phys(self, s_virtual_per_mm):
        """Virtual units per model mm -> paper mm per model mm."""
        return s_virtual_per_mm * self.pw / self.W

    def lines(self, segs2d, X, Y, ident=""):
        widths = {"hidden": 0.16, "fine": 0.14, "detail": 0.22, "contour": 0.42}
        for cls in ("hidden", "fine", "detail", "contour"):
            ss = segs2d.get(cls) or []
            if not ss:
                continue
            d = "".join(f"M{X(a):.2f} {Y(b):.2f}L{X(c):.2f} {Y(e):.2f}" for a, b, c, e in ss)
            dash = ' stroke-dasharray="1.1 0.7"' if cls == "hidden" else ""
            col = self.t["ink2"] if cls == "hidden" else self.t["ink"]
            self.o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{widths[cls]}" '
                          f'stroke-linecap="round" stroke-linejoin="round"{dash} id="lines-{cls}{ident}"/>')

    def text(self, x, y, s, size, fill=None, weight=None, anchor=None):
        w = f' font-weight="{weight}"' if weight else ""
        a = f' text-anchor="{anchor}"' if anchor else ""
        self.o.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size:.2f}" fill="{fill or self.t["ink"]}"{w}{a}>'
                      f'{esc(s)}</text>')

    def title_block(self, cells, product, subtitle):
        """Bottom-right block, 116 x 31 virtual units. cells: 6 (label, value) pairs."""
        t, ink, ink2 = self.t, self.t["ink"], self.t["ink2"]
        bw, bh = 116.0, 31.0
        bx, by = self.W - 12 - bw, self.H - 12 - bh
        self.o.append(f'<rect x="{bx:.2f}" y="{by:.2f}" width="{bw}" height="{bh}" fill="{t["bg"]}" '
                      f'stroke="{ink}" stroke-width="0.4"/>')
        for yy in (by + 12, by + 21.5):
            self.o.append(f'<line x1="{bx:.2f}" y1="{yy:.2f}" x2="{bx + bw:.2f}" y2="{yy:.2f}" stroke="{ink}" stroke-width="0.2"/>')
        for xx in (bx + bw / 3, bx + 2 * bw / 3):
            self.o.append(f'<line x1="{xx:.2f}" y1="{by + 12:.2f}" x2="{xx:.2f}" y2="{by + bh:.2f}" stroke="{ink}" stroke-width="0.2"/>')
        fs = 5.0
        while fs > 3.0 and len(product) * fs * 0.66 > bw - 6:          # bold glyphs are ~0.66 em wide
            fs -= 0.2
        self.text(bx + 3, by + 6.2, product, fs, weight="700")
        if subtitle:
            self.text(bx + 3, by + 10.2, subtitle[:int((bw - 6) / (2.6 * 0.54))], 2.6, fill=ink2)
        for i, (k, v) in enumerate(cells[:6]):
            cx = bx + 3 + (i % 3) * bw / 3
            cy = by + 15.6 + (i // 3) * 9.5
            self.text(cx, cy, k, 2.1, fill=ink2)
            vs = 2.9
            while vs > 1.6 and len(str(v)) * vs * 0.64 > bw / 3 - 4:   # semibold digits and "×" ~0.64 em
                vs -= 0.1
            self.text(cx, cy + 3.6, v, vs, weight="600")
        return bx, by

    def footer(self, s):
        if s:
            self.text(14, self.H - 11.5, s, 2.2, fill=self.t["ink2"])

    def svg(self):
        return "\n".join(self.o + ["</svg>"])


def write_outputs(svg_text, path_svg, png_width_px=4961):
    """Write SVG; also PDF and PNG when rsvg-convert is installed (optional)."""
    os.makedirs(os.path.dirname(os.path.abspath(path_svg)), exist_ok=True)
    with open(path_svg, "w", encoding="utf-8") as f:
        f.write(svg_text)
    made = [path_svg]
    rs = shutil.which("rsvg-convert")
    if rs:
        stem = path_svg[:-4] if path_svg.endswith(".svg") else path_svg
        for args, out in ((["-f", "pdf"], stem + ".pdf"), (["-f", "png", "-w", str(png_width_px)], stem + ".png")):
            r = subprocess.run([rs, *args, "-o", out, path_svg], capture_output=True, text=True)
            if r.returncode == 0:
                made.append(out)
            else:
                print("rsvg-convert failed:", r.stderr.strip()[:200])
    return made


def today():
    return datetime.date.today().isoformat()
