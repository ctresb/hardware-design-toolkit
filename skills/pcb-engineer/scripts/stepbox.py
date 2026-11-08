"""Write a box as a minimal AP214 STEP solid (mm). Used for the bodies of generated footprints, next to the VRML
of the same name, so `kicad-cli pcb export step --subst-models` can include them. Pure Python 3.9+.

    python3 stepbox.py out.step 2.0 1.6 0.6
"""
import sys


def write_step_box(path, w, l, h, name="body"):
    x0, x1, y0, y1, z0, z1 = -w / 2, w / 2, -l / 2, l / 2, 0.0, h
    P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    # faces as vertex loops, counter-clockwise seen from outside; with the outward normal
    F = [((0, 3, 2, 1), (0, 0, -1)), ((4, 5, 6, 7), (0, 0, 1)), ((0, 1, 5, 4), (0, -1, 0)),
         ((1, 2, 6, 5), (1, 0, 0)), ((2, 3, 7, 6), (0, 1, 0)), ((3, 0, 4, 7), (-1, 0, 0))]
    lines, n = [], [0]

    def e(s):
        n[0] += 1
        lines.append("#%d=%s;" % (n[0], s))
        return n[0]

    def f(v):
        return "%.6f" % v

    ac = e("APPLICATION_CONTEXT('automotive design')")
    e("APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#%d)" % ac)
    pc = e("PRODUCT_CONTEXT('',#%d,'mechanical')" % ac)
    pr = e("PRODUCT('%s','%s','',(#%d))" % (name, name, pc))
    pdf = e("PRODUCT_DEFINITION_FORMATION('','',#%d)" % pr)
    pdc = e("PRODUCT_DEFINITION_CONTEXT('part definition',#%d,'design')" % ac)
    pd = e("PRODUCT_DEFINITION('design','',#%d,#%d)" % (pdf, pdc))
    pds = e("PRODUCT_DEFINITION_SHAPE('','',#%d)" % pd)
    lu = e("(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.))")
    au = e("(NAMED_UNIT(*)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.))")
    su = e("(NAMED_UNIT(*)SI_UNIT($,.STERADIAN.)SOLID_ANGLE_UNIT())")
    um = e("UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-07),#%d,'distance_accuracy_value','confusion accuracy')" % lu)
    ctx = e("(GEOMETRIC_REPRESENTATION_CONTEXT(3)GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#%d))"
            "GLOBAL_UNIT_ASSIGNED_CONTEXT((#%d,#%d,#%d))REPRESENTATION_CONTEXT('Context','3D'))" % (um, lu, au, su))
    o = e("CARTESIAN_POINT('',(0.,0.,0.))")
    dz = e("DIRECTION('',(0.,0.,1.))")
    dx = e("DIRECTION('',(1.,0.,0.))")
    ax = e("AXIS2_PLACEMENT_3D('',#%d,#%d,#%d)" % (o, dz, dx))
    cp = [e("CARTESIAN_POINT('',(%s,%s,%s))" % tuple(map(f, p))) for p in P]
    vp = [e("VERTEX_POINT('',#%d)" % c) for c in cp]
    edges = {}

    def edge(i, j):
        key = (min(i, j), max(i, j))
        if key not in edges:
            a, b = key
            d = [P[b][k] - P[a][k] for k in range(3)]
            ln = sum(x * x for x in d) ** 0.5
            di = e("DIRECTION('',(%s,%s,%s))" % tuple(f(x / ln) for x in d))
            vec = e("VECTOR('',#%d,%s)" % (di, f(ln)))
            line = e("LINE('',#%d,#%d)" % (cp[a], vec))
            edges[key] = e("EDGE_CURVE('',#%d,#%d,#%d,.T.)" % (vp[a], vp[b], line))
        return edges[key], (i, j) == (min(i, j), max(i, j))

    faces = []
    for loop, nrm in F:
        oes = []
        for k in range(4):
            i, j = loop[k], loop[(k + 1) % 4]
            ec, same = edge(i, j)
            oes.append(e("ORIENTED_EDGE('',*,*,#%d,%s)" % (ec, ".T." if same else ".F.")))
        el = e("EDGE_LOOP('',(%s))" % ",".join("#%d" % x for x in oes))
        fb = e("FACE_OUTER_BOUND('',#%d,.T.)" % el)
        pn = e("DIRECTION('',(%s,%s,%s))" % tuple(f(x) for x in nrm))
        ref = (1.0, 0.0, 0.0) if abs(nrm[0]) < 0.5 else (0.0, 1.0, 0.0)
        rd = e("DIRECTION('',(%s,%s,%s))" % tuple(f(x) for x in ref))
        pa = e("AXIS2_PLACEMENT_3D('',#%d,#%d,#%d)" % (cp[loop[0]], pn, rd))
        pl = e("PLANE('',#%d)" % pa)
        faces.append(e("ADVANCED_FACE('',(#%d),#%d,.T.)" % (fb, pl)))
    sh = e("CLOSED_SHELL('',(%s))" % ",".join("#%d" % x for x in faces))
    so = e("MANIFOLD_SOLID_BREP('%s',#%d)" % (name, sh))
    rep = e("ADVANCED_BREP_SHAPE_REPRESENTATION('',(#%d,#%d),#%d)" % (ax, so, ctx))
    e("SHAPE_DEFINITION_REPRESENTATION(#%d,#%d)" % (pds, rep))
    with open(path, "w") as fh:
        fh.write("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('box'),'2;1');\n"
                 "FILE_NAME('%s','2026-01-01T00:00:00',(''),(''),'hdt_pcb','hdt_pcb','');\n"
                 "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\nENDSEC;\nDATA;\n" % name)
        fh.write("\n".join(lines))
        fh.write("\nENDSEC;\nEND-ISO-10303-21;\n")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    write_step_box(sys.argv[1], *map(float, sys.argv[2:5]))
    print("stepbox: wrote", sys.argv[1])
