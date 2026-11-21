import unittest

import _path  # noqa: F401
import rsig
import selftest


class SelftestNeed(unittest.TestCase):
    """selftest.need is what makes selftest.py exit nonzero. A copy that never raised would leave it green."""

    def test_false_condition_raises_with_the_message(self):
        with self.assertRaises(selftest.SelfTestFailure) as cm:
            selftest.need(False, "boom")
        self.assertEqual(str(cm.exception), "boom")

    def test_true_condition_passes(self):
        self.assertIsNone(selftest.need(True, "unused"))


class ConstraintEquality(unittest.TestCase):
    def test_equal_and_unequal_constraints(self):
        a = rsig.Constraint("c0", 0, 1, 2)
        self.assertEqual(a, rsig.Constraint("c0", 0, 1, 2))
        for other in (rsig.Constraint("c1", 0, 1, 2), rsig.Constraint("c0", 1, 1, 2),
                      rsig.Constraint("c0", 0, 2, 2), rsig.Constraint("c0", 0, 1, 3)):
            self.assertNotEqual(a, other)
