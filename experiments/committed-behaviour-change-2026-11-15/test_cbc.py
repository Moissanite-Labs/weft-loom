#!/usr/bin/env python3
"""Unit tests for cbc.py: hashing, domain, probe order, dispute verdicts."""
import unittest

import numpy as np

import cbc


class Tiny:
    """Smallest organism stand-in: named tensors plus a predict method."""

    def __init__(self, scale=1.0):
        rng = np.random.default_rng(0)
        self.W1 = rng.normal(size=(4, 24)) * scale
        self.b1 = np.zeros(4)
        self.W2 = rng.normal(size=(4, 4))
        self.b2 = np.zeros(4)
        self.W3 = rng.normal(size=(8, 4))
        self.b3 = np.zeros(8)

    def predict(self, X):
        h = np.tanh(X @ self.W1.T + self.b1)
        h = np.tanh(h @ self.W2.T + self.b2)
        return h @ self.W3.T + self.b3


def native_row():
    x = np.zeros(24)
    x[16] = 2.4
    return x


SPEC = {"grid": [-6.0, -3.0, 0.0, 3.0, 6.0], "budget_rows": 5000, "n_bases": 4,
        "n_random": 200, "hill_step": 1.0}


class TestCbc(unittest.TestCase):
    def test_root_depends_on_shape_not_only_bytes(self):
        a = {"W": np.arange(6, dtype=np.float64).reshape(2, 3)}
        b = {"W": np.arange(6, dtype=np.float64).reshape(3, 2)}
        self.assertNotEqual(cbc.weight_root(a), cbc.weight_root(b))

    def test_root_independent_of_dict_order(self):
        a = {"W1": np.ones((2, 2)), "b1": np.zeros(2)}
        b = {"b1": np.zeros(2), "W1": np.ones((2, 2))}
        self.assertEqual(cbc.weight_root(a), cbc.weight_root(b))

    def test_probe_seed_changes_with_candidate(self):
        f0, f1, f1b = Tiny(1.0), Tiny(1.1), Tiny(1.2)
        c1 = cbc.make_claim(cbc.weight_root(f0), cbc.weight_root(f1), "0.5", "t", SPEC)
        c2 = cbc.make_claim(cbc.weight_root(f0), cbc.weight_root(f1b), "0.5", "t", SPEC)
        self.assertNotEqual(cbc.probe_seed(c1), cbc.probe_seed(c2))

    def test_domain(self):
        self.assertTrue(cbc.in_domain(native_row()))
        novel = native_row()
        novel[16], novel[18] = 0.0, 2.4
        self.assertFalse(cbc.in_domain(novel))
        far = native_row()
        far[:16] = 6.0
        self.assertFalse(cbc.in_domain(far))

    def test_dispute_verdicts(self):
        f0, f1 = Tiny(1.0), Tiny(3.0)
        claim = cbc.make_claim(cbc.weight_root(f0), cbc.weight_root(f1), "0.01", "t", SPEC)
        x = native_row()
        x[0] = 3.0
        v = cbc.verify_dispute(claim, f0, f1, x)
        self.assertTrue(v["refuted"], v)
        same = cbc.make_claim(cbc.weight_root(f0), cbc.weight_root(f0), "0.01", "t", SPEC)
        self.assertFalse(cbc.verify_dispute(same, f0, f0, x)["refuted"])
        out = native_row()
        out[0] = 9.0
        self.assertEqual(cbc.verify_dispute(claim, f0, f1, out)["reason"], "outside_domain")
        self.assertEqual(cbc.verify_dispute(claim, f1, f0, x)["reason"], "weight_root_mismatch")

    def test_search_finds_large_change(self):
        f0, f1 = Tiny(1.0), Tiny(3.0)
        claim = cbc.make_claim(cbc.weight_root(f0), cbc.weight_root(f1), "0.01", "t", SPEC)
        rng = np.random.default_rng(cbc.probe_seed(claim))
        bases = np.tile(native_row(), (4, 1)) + rng.normal(0, 0.1, size=(4, 24))
        bases[:, 16] = 2.4
        r = cbc.search_refutation(claim, f0, f1, bases, rng)
        self.assertTrue(r["refuted"], r)
        self.assertLessEqual(r["rows_evaluated"], SPEC["budget_rows"])


if __name__ == "__main__":
    unittest.main()
