"""Join renders into one contact sheet (compare variants side by side before a full render).

    blender -b --python contact_sheet.py -- out.png a.png b.png c.png [--height 700] [--cols 3] [--labels]

Runs in Blender (uses its image loader and numpy), so it needs no extra Python packages.
"""
import argparse
import os
import sys

import bpy
import numpy as np


def load(path, height):
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(im)
    s = height / h
    nw = max(1, int(round(w * s)))
    ys = (np.arange(height) / s).astype(int).clip(0, h - 1)
    xs = (np.arange(nw) / s).astype(int).clip(0, w - 1)
    return px[ys][:, xs]


def main(argv):
    ap = argparse.ArgumentParser(prog="contact_sheet.py")
    ap.add_argument("out")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--height", type=int, default=700)
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--gap", type=int, default=12)
    ap.add_argument("--bg", type=float, default=0.08, help="background grey (0–1, linear)")
    a = ap.parse_args(argv)
    ims = [load(p, a.height) for p in a.images if os.path.exists(p)]
    if not ims:
        print("SHEET no images found")
        return 1
    rows = [ims[i:i + a.cols] for i in range(0, len(ims), a.cols)]
    W = max(sum(i.shape[1] for i in r) + a.gap * (len(r) + 1) for r in rows)
    H = len(rows) * (a.height + a.gap) + a.gap
    sheet = np.full((H, W, 4), a.bg, dtype=np.float32)
    sheet[..., 3] = 1
    y = a.gap
    for r in reversed(rows):                       # Blender images start at the bottom row
        x = a.gap
        for im in r:
            sheet[y:y + a.height, x:x + im.shape[1]] = im
            x += im.shape[1] + a.gap
        y += a.height + a.gap
    out = bpy.data.images.new("sheet", W, H, alpha=True)
    out.pixels[:] = sheet.ravel()
    out.filepath_raw = os.path.abspath(a.out)
    out.file_format = "PNG"
    out.save()
    print(f"SHEET {len(ims)} images -> {a.out} ({W}×{H})")
    return 0


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    rc = main(argv)
    if bpy.app.background:
        sys.exit(rc)
