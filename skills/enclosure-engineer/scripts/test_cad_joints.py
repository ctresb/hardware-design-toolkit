#!/usr/bin/env python3
"""Regression tests for cad_enclosure.py joints, doors and keep-out checks. Run with cad_python (build123d):

    "$CAD_PY" test_cad_joints.py            builds 6 variants in a temp folder, about 10 s

Cases: adhesive lip (example), captive screws + flat gasket, round door with screws, round door with twist lugs,
a twist lid on a non-circular outline (must be refused with a clear message), and a keep-out that touches
nothing (must not crash).
"""
import copy
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "..", "templates")


def run(spec, tmp):
    p = os.path.join(tmp, spec["name"] + ".json")
    json.dump(spec, open(p, "w"))
    r = subprocess.run([sys.executable, os.path.join(HERE, "cad_enclosure.py"), p, "--out", os.path.join(tmp, "out"),
                        "--formats", "glb"], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    base = json.load(open(os.path.join(TPL, "enclosure.example.json")))
    screws = json.load(open(os.path.join(TPL, "enclosure.screws.example.json")))
    door = json.load(open(os.path.join(TPL, "enclosure.door.example.json")))
    twist = copy.deepcopy(door)
    twist["name"] = "t-door-twist"
    twist["lid"]["door"]["retention"] = "twist"
    twist["lid"]["door"].pop("screws", None)
    bad = copy.deepcopy(base)
    bad["name"], bad["lid"]["joint"] = "t-bad-twist", "twist"
    far = copy.deepcopy(base)
    far["name"] = "t-far-keepout"
    far["keepouts"].append({"name": "Far", "center": [0, 0, 6], "size": [1, 1, 1]})
    cases = [(base, 0, "DFM PASS"), (screws, 0, "captive"), (door, 0, "battery door"), (twist, 0, "DFM PASS"),
             (bad, 2, "needs a circle outline"), (far, 0, "DFM PASS")]
    fails = 0
    with tempfile.TemporaryDirectory() as tmp:
        for spec, code, text in cases:
            rc, out = run(spec, tmp)
            dfm = os.path.join(tmp, "out", spec["name"] + "_dfm.json")
            notes = json.load(open(dfm))["notes"] if os.path.exists(dfm) else []
            ok = rc == code and (text in out or any(text in n for n in notes))
            fails += not ok
            print(("ok   " if ok else "FAIL ") + spec["name"] + ": exit %d (want %d)" % (rc, code))
            if not ok:
                print(out[-1500:])
    print("test_cad_joints: %d/%d passed" % (len(cases) - fails, len(cases)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
