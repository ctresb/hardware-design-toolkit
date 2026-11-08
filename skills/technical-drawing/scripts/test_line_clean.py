"""Unit tests for line_clean (run: python3 test_line_clean.py)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import line_clean as LC  # noqa: E402


class T(unittest.TestCase):
    def test_tick_on_line_removed(self):
        segs = {"contour": [(0, 0, 10, 0), (4.0, 0.05, 4.4, 0.05)], "detail": []}
        out, n = LC.clean(segs, tol=0.1, maxlen=1.0)
        self.assertEqual(n, 1)
        self.assertEqual(out["contour"], [(0, 0, 10, 0)])

    def test_arc_kept(self):
        import math
        arc = [(math.cos(a / 10), math.sin(a / 10), math.cos((a + 1) / 10), math.sin((a + 1) / 10)) for a in range(10)]
        segs = {"contour": arc + [(5, 5, 15, 5)]}
        out, n = LC.clean(segs, tol=0.1, maxlen=0.5)
        self.assertEqual(n, 0)
        self.assertEqual(len(out["contour"]), 11)

    def test_parallel_far_kept(self):
        segs = {"contour": [(0, 0, 10, 0), (4, 0.5, 4.4, 0.5)]}
        out, n = LC.clean(segs, tol=0.1, maxlen=1.0)
        self.assertEqual(n, 0)

    def test_long_duplicate_kept(self):
        segs = {"contour": [(0, 0, 10, 0)], "detail": [(0, 0.02, 9.9, 0.02)]}
        out, n = LC.clean(segs, tol=0.1, maxlen=1.0)       # longer than maxlen: not a tick
        self.assertEqual(n, 0)

    def test_dot_removed_across_classes(self):
        segs = {"contour": [(0, 0, 10, 0)], "detail": [(3, 0.03, 3.02, 0.03)]}
        out, n = LC.clean(segs, tol=0.1, maxlen=1.0)
        self.assertEqual(n, 1)
        self.assertEqual(out["detail"], [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
