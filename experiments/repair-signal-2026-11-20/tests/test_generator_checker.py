import unittest
from fractions import Fraction as F

import _path  # noqa: F401
import rsig

TINY = rsig.Instance(2, [
    rsig.Constraint("c0", 0, 1, 1),
    rsig.Constraint("c1", 1, 0, 1),
    rsig.Constraint("goal", 1, 0, F(-1, 2)),
])


class Checker(unittest.TestCase):
    def test_known_answer_pass(self):
        self.assertEqual(rsig.check(TINY, [F(1), F(0)]), [])

    def test_known_answer_goal_violation(self):
        v = rsig.check(TINY, [F(0), F(0)])
        self.assertEqual(v, [rsig.Violation("goal", 1, 0, F(-1, 2), F(1, 2))])

    def test_known_answer_signed_exact_excess(self):
        v = rsig.check(TINY, [F(5, 2), F(0)])
        self.assertEqual(v, [rsig.Violation("c0", 0, 1, F(1), F(3, 2))])

    def test_boundary_is_a_pass(self):
        self.assertEqual(rsig.check(TINY, [F(1), F(0)]), [])  # c0 tight
        self.assertEqual(rsig.check(TINY, [F(1, 2), F(0)]), [])  # goal tight

    def test_exactness_no_float_rounding(self):
        # 1/3 + 1/3 + 1/3 style sums stay exact
        inst = rsig.Instance(2, [rsig.Constraint("c0", 0, 1, F(1, 3)), rsig.Constraint("goal", 1, 0, F(-1, 3))])
        self.assertEqual(rsig.check(inst, [F(1, 3), F(0)]), [])
        v = rsig.check(inst, [F(1, 3) + F(1, 10 ** 30), F(0)])
        self.assertEqual(v[0].excess, F(1, 10 ** 30))

    def test_rejects_floats_and_wrong_length(self):
        with self.assertRaises(TypeError):
            rsig.check(TINY, [0.5, 0.0])
        with self.assertRaises(TypeError):
            rsig.check(TINY, [True, F(0)])
        with self.assertRaises(ValueError):
            rsig.check(TINY, [F(0)])

    def test_label_free(self):
        # planted point absent: checker still works
        self.assertIsNone(TINY.planted)
        self.assertEqual(len(rsig.check(TINY, [F(0), F(0)])), 1)

    def test_all_violations_listed_in_order(self):
        def got(c):
            return [(x.cid, x.excess) for x in rsig.check(TINY, c)]
        self.assertEqual(got([F(9), F(-9)]), [("c0", F(17))])
        self.assertEqual(got([F(-9), F(9)]), [("c1", F(17)), ("goal", F(37, 2))])
        self.assertEqual(got([F(0), F(5)]), [("c1", F(4)), ("goal", F(11, 2))])
        self.assertEqual(got([F(0), F(0)]), [("goal", F(1, 2))])
        self.assertEqual(got([F(0), F(-3)]), [("c0", F(2))])
        self.assertEqual(got([F(5), F(5)]), [("goal", F(1, 2))])


class Generator(unittest.TestCase):
    def suite(self):
        for tier, kw in rsig.TIERS.items():
            for seed in range(150):
                yield rsig.make_instance(seed, tier=tier, **kw)

    def test_planted_point_is_feasible(self):
        for inst in self.suite():
            self.assertEqual(rsig.check(inst, list(inst.planted)), [], inst.seed)

    def test_zero_answer_always_fails_on_goal(self):
        for inst in self.suite():
            v = rsig.check(inst, [F(0)] * inst.n)
            self.assertIn("goal", [x.cid for x in v], inst.seed)

    def test_goal_lower_bound_positive_and_last(self):
        for inst in self.suite():
            g = inst.constraints[-1]
            self.assertEqual(g.cid, "goal")
            self.assertLess(g.c, 0)

    def test_some_constraints_are_tight_at_the_planted_point(self):
        tight = sum(1 for inst in self.suite() for c in inst.constraints[:-1]
                    if inst.planted[c.u] - inst.planted[c.w] == c.c)
        self.assertGreater(tight, 50)

    def test_denominators_bounded_and_exact(self):
        for tier, kw in rsig.TIERS.items():
            for seed in range(100):
                inst = rsig.make_instance(seed, tier=tier, **kw)
                for c in inst.constraints:
                    self.assertIsInstance(c.c, F)
                    self.assertEqual(kw["den"] % c.c.denominator, 0)

    def test_deterministic_and_seed_sensitive(self):
        a = rsig.make_instance(5, **rsig.TIERS["S"])
        b = rsig.make_instance(5, **rsig.TIERS["S"])
        c = rsig.make_instance(6, **rsig.TIERS["S"])
        self.assertEqual(a.sha256(), b.sha256())
        self.assertNotEqual(a.sha256(), c.sha256())

    def test_known_answer_instance_hash(self):
        # pins the generator stream so a silent change to it is caught
        self.assertEqual(rsig.make_instance(1, **rsig.TIERS["S"]).sha256(),
                         "ce6a7dbbab8488c4649d701e8c5453e65f97efa9cb2619dfb4cc4dcbddc5ee6f")

    def test_sizes(self):
        inst = rsig.make_instance(3, n=6, extra=5, den=6, span=6)
        self.assertEqual(inst.n, 6)
        self.assertEqual(len(inst.constraints), 6 + 5 + 1)
        self.assertEqual(len({(c.u, c.w) for c in inst.constraints[:-1]}), 11)

    def test_cycle_makes_every_variable_constrained(self):
        for inst in self.suite():
            nodes = {c.u for c in inst.constraints} | {c.w for c in inst.constraints}
            self.assertEqual(nodes, set(range(inst.n)))


if __name__ == "__main__":
    unittest.main()
