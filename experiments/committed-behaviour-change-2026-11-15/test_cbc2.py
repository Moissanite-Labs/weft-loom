#!/usr/bin/env python3
"""Unit tests for cbc2.py: float32 roots, recorded decisions, domain guard."""
import unittest

import numpy as np

import cbc2
from test_cbc import Tiny, native_row

SPEC = {"grid": [0.0], "budget_rows": 10, "n_bases": 1, "n_random": 0, "hill_step": 1.0}
DEC = {"slot_m1": [1, 2], "slot_m2": [3, 4]}


class TestCbc2(unittest.TestCase):
    def test_f32_root_ignores_float64_low_bits(self):
        a, b = Tiny(1.0), Tiny(1.0)
        b.W1 = b.W1 + 1e-12  # below float32 resolution at this scale
        self.assertEqual(cbc2.f32_root(a), cbc2.f32_root(b))

    def test_f32_root_sees_real_change(self):
        a, b = Tiny(1.0), Tiny(1.0)
        b.W1 = b.W1 + 1e-3
        self.assertNotEqual(cbc2.f32_root(a), cbc2.f32_root(b))

    def test_claim_id_binds_decisions_and_packet(self):
        f0, f1 = Tiny(1.0), Tiny(1.1)
        c1 = cbc2.make_claim_v2(f0, f1, "0.5", "t", SPEC, "a" * 64, DEC)
        c2 = cbc2.make_claim_v2(f0, f1, "0.5", "t", SPEC, "a" * 64, {"slot_m1": [9], "slot_m2": [3, 4]})
        c3 = cbc2.make_claim_v2(f0, f1, "0.5", "t", SPEC, "b" * 64, DEC)
        self.assertNotEqual(c1["id"], c2["id"])
        self.assertNotEqual(c1["id"], c3["id"])
        self.assertNotEqual(cbc2.probe_seed_v2(c1), cbc2.probe_seed_v2(c2))

    def test_guard(self):
        self.assertEqual(cbc2.guard(native_row()), "in_domain")
        far = native_row()
        far[:16] = 6.0
        self.assertEqual(cbc2.guard(far), "out_of_domain")

    def test_dispute_v2(self):
        f0, f1 = Tiny(1.0), Tiny(3.0)
        claim = cbc2.make_claim_v2(f0, f1, "0.01", "t", SPEC, "a" * 64, DEC)
        x = native_row()
        x[0] = 3.0
        self.assertTrue(cbc2.verify_dispute_v2(claim, f0, f1, x)["refuted"])
        same = cbc2.make_claim_v2(f0, f0, "0.01", "t", SPEC, "a" * 64, DEC)
        self.assertFalse(cbc2.verify_dispute_v2(same, f0, f0, x)["refuted"])
        out = native_row()
        out[:16] = 6.0
        self.assertEqual(cbc2.verify_dispute_v2(claim, f0, f1, out)["reason"], "outside_domain")


if __name__ == "__main__":
    unittest.main()
