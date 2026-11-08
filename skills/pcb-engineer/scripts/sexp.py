"""Minimal reader/writer for KiCad S-expression files (.kicad_sym, .kicad_mod, .kicad_sch, .kicad_pcb, .net).

Pure Python 3.9+ (runs in KiCad's bundled Python and in the system Python).
Strings that must be quoted on output are `Q` instances; everything else is written bare.
"""
import re

_TOK = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


class Q(str):
    """A string that is written between double quotes."""


def parse(text):
    stack, cur = [], []
    pos = 0
    while True:
        m = _TOK.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done, cur = cur, stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(Q(m.group(3).replace('\\"', '"').replace("\\\\", "\\")))
        else:
            cur.append(m.group(4))
    return cur[0] if len(cur) == 1 else cur


def load(path):
    with open(path, encoding="utf-8") as f:
        return parse(f.read())


def dump(node, indent=0):
    if isinstance(node, list):
        if all(not isinstance(x, list) for x in node):
            return "(" + " ".join(dump(x) for x in node) + ")"
        out = "(" + " ".join(dump(x) for x in node if not isinstance(x, list))
        for x in node:
            if isinstance(x, list):
                out += "\n" + "\t" * (indent + 1) + dump(x, indent + 1)
        return out + "\n" + "\t" * indent + ")"
    if isinstance(node, Q):
        return '"' + node.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(node, bool):
        return "yes" if node else "no"
    if isinstance(node, float):
        if node == int(node):
            return str(int(node))
        return ("%.6f" % node).rstrip("0").rstrip(".")
    return str(node)


def save(path, node):
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump(node) + "\n")


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def first(node, key, default=None):
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return default


def netlist(path):
    """{net_name: [(ref, pin, pinfunction)]} from a KiCad `kicadsexpr` netlist."""
    root = load(path)
    out = {}
    for net in find(first(root, "nets", []), "net"):
        name = first(net, "name")[1]
        nodes = []
        for nd in find(net, "node"):
            pf = first(nd, "pinfunction")
            nodes.append((first(nd, "ref")[1], first(nd, "pin")[1], pf[1] if pf else ""))
        out[name] = nodes
    return out
