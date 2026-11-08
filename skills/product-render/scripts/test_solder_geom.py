"""Unit tests for solder_geom (run: python3 test_solder_geom.py)."""
import sys
import unittest

sys.path.insert(0, __import__("os").path.dirname(__file__))
import solder_geom as G  # noqa: E402


class T(unittest.TestCase):
    def test_select(self):
        refs = ["U1", "U2", "C1", "C12", "Q1", "J1"]
        self.assertEqual(G.select_refs(refs), refs)
        self.assertEqual(G.select_refs(refs, only=["C*"]), ["C1", "C12"])
        self.assertEqual(G.select_refs(refs, exclude=["Q1", "u2"]), ["U1", "C1", "C12", "J1"])
        self.assertEqual(G.select_refs(refs, only=["C*", "U*"], exclude=["C12"]), ["U1", "U2", "C1"])

    def test_wettable(self):
        self.assertTrue(G.pad_wettable({"n": "1", "cu": True}))
        self.assertFalse(G.pad_wettable({"n": "1", "cu": False}))
        self.assertFalse(G.pad_wettable({"n": "3", "cu": True, "mask": False}))      # no mask opening
        self.assertFalse(G.pad_wettable({"n": "MP1", "cu": True}, "J1"))
        self.assertTrue(G.pad_wettable({"n": "MP1", "cu": True}, "U1"))

    def test_inset(self):
        q = G.inset_pad({"w": 0.50, "h": 0.40}, 0.03)
        self.assertAlmostEqual(q["w"], 0.44)
        self.assertAlmostEqual(q["h"], 0.34)
        q = G.inset_pad({"w": 0.08, "h": 0.40}, 0.03)
        self.assertAlmostEqual(q["w"], G.MIN_PAD)
        q = G.inset_pad({"w": 0.50, "h": 0.40, "mask_margin": -0.02}, 0.03)       # mask overlaps copper
        self.assertAlmostEqual(q["w"], 0.40)
        q = G.inset_pad({"w": 0.50, "h": 0.40, "mask_margin": 0.05}, 0.0)         # positive margin: no change
        self.assertAlmostEqual(q["w"], 0.50)


if __name__ == "__main__":
    unittest.main(verbosity=1)
