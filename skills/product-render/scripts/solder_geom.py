"""Pure-Python helpers for solder.py (no bpy), so the pad logic can be unit-tested anywhere.

- Which components get fillets: `select_refs` (glob lists, per-part enable).
- Which pads can carry solder: `pad_wettable` (copper, a solder-mask opening, not a mounting tab).
- Where the contact line sits: `inset_pad` pulls the fillet edge inside the copper so it never meets a
  zero-margin solder-mask wall (a 0.03 mm inset hides the clash and is invisible in any render).
"""
import fnmatch

EDGE_INSET = 0.03       # mm, default contact-line inset from the copper edge
MIN_PAD = 0.05          # mm, smallest pad side kept after the inset


def _match(ref, patterns):
    return any(fnmatch.fnmatchcase(ref, p) or fnmatch.fnmatchcase(ref.upper(), p.upper()) for p in patterns)


def select_refs(refs, only=None, exclude=None):
    """refs: iterable of reference designators. only/exclude: glob lists ('U*', 'C1?', 'Q1').
    Returns the refs to solder, in input order."""
    out = []
    for r in refs:
        if only and not _match(r, only):
            continue
        if exclude and _match(r, exclude):
            continue
        out.append(r)
    return out


def pad_wettable(p, ref=""):
    """True when solder can wet this pad: it has copper, its solder-mask opening is not explicitly absent
    (`"mask": false` in pads.json), and it is not a connector mounting tab (MP*)."""
    if not p.get("cu", True):
        return False
    if p.get("mask") is False:
        return False
    if ref.upper().startswith(("J", "CN")) and str(p.get("n", "")).upper().startswith("MP"):
        return False
    return True


def inset_pad(p, d=EDGE_INSET):
    """Copy of pad p with w and h reduced by 2·d (never below MIN_PAD). Also reduces by the pad's own
    `mask_margin` when it is negative (mask overlapping the copper: the opening is smaller than the pad)."""
    q = dict(p)
    mm = p.get("mask_margin")
    extra = -mm if isinstance(mm, (int, float)) and mm < 0 else 0.0
    q["w"] = max(MIN_PAD, p["w"] - 2 * (d + extra))
    q["h"] = max(MIN_PAD, p["h"] - 2 * (d + extra))
    return q
