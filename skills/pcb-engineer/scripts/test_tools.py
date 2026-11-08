#!/usr/bin/env python3
"""Light regression tests for pcb-engineer helpers (system Python, no KiCad needed, about 10 s):

  - outline union rounds polygon corners (convex and concave), not only rect corners;
  - kicad_env reads the Java version a jar needs from its Main-Class, not from a bundled old library;
  - route.py builds the right Freerouting command for 1.x (xvfb on headless Linux) and 2.x.
"""
import io
import math
import os
import struct
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_env  # noqa: E402
import outline as outl  # noqa: E402

fails = 0


def check(name, cond, detail=""):
    global fails
    fails += not cond
    print(("ok   " if cond else "FAIL ") + name + (": " + detail if detail else ""))


# 1. union fillet rounds polygon corners
p = outl.build({"type": "union", "fillet": 1.0, "shapes": [{"polygon": [[-10, -10], [10, -10], [10, 10], [-10, 10]]},
                                                            {"rect": [8, -2, 14, 2]}]})
gap = min(math.hypot(x - 10, y - 10) for x, y in p)          # sharp corner: 0; radius 1: 0.414
check("union rounds convex polygon corners", 0.3 < gap < 0.6, "%.3f mm from the sharp corner" % gap)
L = outl.build({"type": "union", "fillet": 1.0, "shapes": [{"polygon": [[0, 0], [10, 0], [10, 4], [4, 4], [4, 10], [0, 10]]}]})
inner = min(math.hypot(x - 4, y - 4) for x, y in L)           # concave corner rounded: the outline leaves (4, 4)
check("union rounds concave polygon corners", inner > 0.2, "%.3f mm from the inner corner" % inner)


# 2. jar Java requirement from the Main-Class
def fake_jar(path, main_major, lib_major):
    def cls(major):
        return b"\xca\xfe\xba\xbe" + struct.pack(">HH", 0, major) + b"\x00" * 8
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nMain-Class: app.Main\n")
        z.writestr("com/old/Lib.class", cls(lib_major))
        z.writestr("app/Main.class", cls(main_major))


with tempfile.TemporaryDirectory() as d:
    j = os.path.join(d, "freerouting-2.5.0.jar")
    fake_jar(j, 69, 46)
    check("jar needs Java 25 (Main-Class 69, bundled lib 46)", kicad_env.jar_java_required(j) == 25,
          str(kicad_env.jar_java_required(j)))
    check("version from the jar name", kicad_env.freerouting_version(j) == "2.5.0")

# 3. route command per version (route.py imports pcbnew: test the helper with a stub)
sys.modules.setdefault("pcbnew", type(sys)("pcbnew"))
import route  # noqa: E402
c2 = route.route_cmd("java", "/x/freerouting-2.5.0.jar", "a.dsn", "a.ses", 60)
check("2.x command is headless", "--gui.enabled=false" in c2 and "-Djava.awt.headless=true" in c2)
if sys.platform.startswith("linux") and not os.environ.get("DISPLAY") and not __import__("shutil").which("xvfb-run"):
    try:
        route.route_cmd("java", "/x/freerouting-1.9.0.jar", "a.dsn", "a.ses", 60)
        check("1.x without a display asks for xvfb", False)
    except RuntimeError:
        check("1.x without a display asks for xvfb", True)
else:
    c1 = route.route_cmd("java", "/x/freerouting-1.9.0.jar", "a.dsn", "a.ses", 60)
    check("1.x command has no 2.x-only flags", "--gui.enabled=false" not in c1)

print("test_tools: %d failed" % fails)
sys.exit(1 if fails else 0)
