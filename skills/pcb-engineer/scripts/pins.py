"""Print the pins of a KiCad symbol and the pads of a footprint, to fill a part's "pins" in board.json.

    python3 pins.py MCU_Nordic:nRF52832-QFxx
    python3 pins.py Battery_Management:MCP73831-2-OT --footprint Package_TO_SOT_SMD:SOT-23-5
    python3 pins.py --search "LIS2"            (symbol names containing the text, all standard libraries)

Pure Python 3.9+.
"""
import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_env  # noqa: E402
import libgen  # noqa: E402
import sexp  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol", nargs="?", help="Lib:Name")
    ap.add_argument("--footprint", help="Lib:Name")
    ap.add_argument("--search", help="find symbols whose name contains this text")
    ap.add_argument("--search-footprint", help="find footprints whose name contains this text")
    a = ap.parse_args()
    if a.search:
        pat = re.compile(r'\(symbol "([^"]*%s[^"]*)"' % re.escape(a.search), re.I)
        for f in sorted(glob.glob(os.path.join(kicad_env.symbol_dir(), "*.kicad_sym"))):
            hits = sorted({m for m in pat.findall(open(f, encoding="utf-8").read()) if not re.search(r"_\d+_\d+$", m)})
            for h in hits:
                print("%s:%s" % (os.path.basename(f)[:-10], h))
        return
    if a.search_footprint:
        for d in sorted(glob.glob(os.path.join(kicad_env.footprint_dir(), "*.pretty"))):
            for f in sorted(os.listdir(d)):
                if a.search_footprint.lower() in f.lower():
                    print("%s:%s" % (os.path.basename(d)[:-7], f[:-10]))
        return
    if a.symbol:
        if ":" not in a.symbol:
            sys.exit("pins: give the symbol as Lib:Name (find it with --search %s)" % a.symbol)
        lib, name = a.symbol.split(":", 1)
        path = os.path.join(kicad_env.symbol_dir() or "", lib + ".kicad_sym")
        if not os.path.exists(path):
            sys.exit("pins: no symbol library %r in %s (find it with --search %s)" % (lib, kicad_env.symbol_dir(), name))
        try:
            sym = libgen._resolve_symbol(path, name, name)
        except Exception as ex:
            sys.exit("pins: symbol %s not found in %s (%s); find it with --search %s" % (name, lib, ex, name))
        if sym is None:
            sys.exit("pins: symbol %s not found in %s; find it with --search %s" % (name, lib, name))
        fp_prop = next((p[2] for p in sexp.find(sym, "property") if p[1] == "Footprint"), "")
        print("symbol %s  (default footprint: %s)" % (a.symbol, fp_prop or "none"))
        print("%-6s %-22s %-14s %s" % ("number", "name", "type", "unit"))
        for num, nm, typ, unit, *_ in sorted(libgen.symbol_pins(sym), key=lambda p: (p[3], [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", p[0])])):
            print("%-6s %-22s %-14s %s" % (num, nm, typ, unit))
    if a.footprint:
        if ":" not in a.footprint:
            sys.exit("pins: give the footprint as Lib:Name (find it with --search-footprint %s)" % a.footprint)
        lib, name = a.footprint.split(":", 1)
        fpath = os.path.join(kicad_env.footprint_dir() or "", lib + ".pretty", name + ".kicad_mod")
        if not os.path.exists(fpath):
            sys.exit("pins: footprint %s not found (%s); find it with --search-footprint %s" % (a.footprint, fpath, name))
        fp = sexp.load(fpath)
        print("footprint %s" % a.footprint)
        for p in sexp.find(fp, "pad"):
            at, sz = sexp.first(p, "at"), sexp.first(p, "size")
            print("  pad %-5s %-12s %-9s at (%s, %s) size %s x %s" % (p[1] or '""', p[2], p[3], at[1], at[2], sz[1], sz[2]))
        print("pads:", ", ".join(sorted(libgen.footprint_pads(fp), key=lambda x: (len(x), x))))


if __name__ == "__main__":
    main()
