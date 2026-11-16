#!/usr/bin/env python3
"""Tests for budget_curve.SearchTrace checkpoint and crossing accounting."""
import unittest

import numpy as np

import budget_curve
from test_cbc import native_row


class Zero:
    def predict(self, X):
        return np.zeros((len(X), 8))


class FirstColumn:
    def predict(self, X):
        return np.repeat(np.asarray(X)[:, :1], 8, axis=1)


class TestSearchTrace(unittest.TestCase):
    def test_checkpoint_and_crossing_rows(self):
        old = budget_curve.CHECKPOINTS
        budget_curve.CHECKPOINTS = [2, 3, 4]
        try:
            trace = budget_curve.SearchTrace(Zero(), FirstColumn(), tau=1.0, max_budget=10)
            X = np.tile(native_row(), (3, 1))
            X[:, 0] = [0.25, 2.0, 0.5]
            done = trace.consider(X)
        finally:
            budget_curve.CHECKPOINTS = old

        self.assertTrue(done)
        self.assertEqual(trace.evaluated, 2)
        self.assertEqual(trace.crossing_row, 2)
        self.assertEqual(trace.checkpoints, [{"rows": 2, "best_change": 2.0}])
        self.assertEqual(trace.best_x[0], 2.0)

    def test_checkpoints_are_monotonic_without_crossing(self):
        old = budget_curve.CHECKPOINTS
        budget_curve.CHECKPOINTS = [2, 4]
        try:
            trace = budget_curve.SearchTrace(Zero(), FirstColumn(), tau=10.0, max_budget=10)
            X = np.tile(native_row(), (4, 1))
            X[:, 0] = [0.25, 0.5, 0.4, 0.75]
            done = trace.consider(X)
        finally:
            budget_curve.CHECKPOINTS = old

        self.assertFalse(done)
        self.assertEqual(trace.evaluated, 4)
        self.assertEqual(
            trace.checkpoints,
            [{"rows": 2, "best_change": 0.5}, {"rows": 4, "best_change": 0.75}],
        )


if __name__ == "__main__":
    unittest.main()
