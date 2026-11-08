#!/usr/bin/env python3
"""Export the SMD pads of KiCad boards to pads.json, the input of solder.py. Standard library only.

    python3 kicad_pads.py hw/pcb/main/main.kicad_pcb hw/pcb/flex/flex.kicad_pcb -o hw/pcb/export/pads.json

pcb-engineer owns pads.json and writes it during its export (`export.py --what pads`). Use this wrapper only
for a board that was not built by pcb-engineer. It calls the same exporter
(pcb-engineer/scripts/export.py: pads_of_board), so the format is identical. Board names in the JSON are the
file stems ("main", "flex").
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "pcb-engineer", "scripts"))
try:
    import export  # noqa: E402  (pcb-engineer's exporter)
except ImportError:
    sys.exit("kicad_pads: needs pcb-engineer/scripts/export.py (install the whole Hardware Design Toolkit)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("boards", nargs="+", help=".kicad_pcb files")
    ap.add_argument("-o", "--out", required=True, help="output pads.json")
    a = ap.parse_args()
    missing = [b for b in a.boards if not os.path.exists(b)]
    if missing:
        print("kicad_pads: not found: " + ", ".join(missing), file=sys.stderr)
        return 2
    r = export.write_pads({os.path.splitext(os.path.basename(b))[0]: b for b in a.boards}, a.out)
    print(f"kicad_pads: {r['footprints']} footprints, {r['pads']} SMD pads -> {r['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
