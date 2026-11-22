import unittest
from fractions import Fraction

import _setup  # noqa: F401
import episodes as E
import evaluate
import reference_policies as RP


class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = E.build_set("heldout1", {"S": 40, "M": 40})
        cls.r = {(n, a): evaluate.evaluate_arm(p, cls.s, a, 96, n)
                 for n, p in RP.POLICIES.items() for a in E.ARMS}

    def test_unchanged_scores_zero(self):
        for a in E.ARMS:
            self.assertEqual(self.r[("unchanged", a)].passed, 0)

    def test_recompute_ties_across_arms_and_scores(self):
        outs = {self.r[("recompute", a)].outcomes for a in E.ARMS}
        self.assertEqual(len(outs), 1)
        self.assertEqual(self.r[("recompute", "A")].passed, len(self.s))

    def test_oracle_separates_c_from_the_rest(self):
        c = self.r[("oracle", "C")].passed
        for a in "ABN":
            self.assertGreater(c, 3 * self.r[("oracle", a)].passed + 10)
        # amounts that are true for another puzzle are still positive and about as large,
        # so the oracle, which checks its proposals against the public constraints, passes
        # some by chance; C is clearly higher
        self.assertGreater(c, self.r[("oracle", "E")].passed + 10)
        self.assertEqual(self.r[("oracle", "A")].passed, 0)
        self.assertEqual(self.r[("oracle", "B")].passed, 0)
        self.assertEqual(self.r[("oracle", "N")].passed, 0)

    def test_blind_is_hurt_by_e_and_n(self):
        c = self.r[("blind", "C")].passed
        self.assertGreater(c, 0)
        self.assertGreater(c, 2 * self.r[("blind", "E")].passed)
        self.assertEqual(self.r[("blind", "N")].passed, 0)

    def test_verbose_breaks_the_format_not_the_repair(self):
        for a in E.ARMS:
            r = self.r[("verbose", a)]
            self.assertEqual((r.format_broken, r.failed, r.passed), (len(self.s), 0, 0))

    def test_policies_read_amounts_only_from_the_feedback(self):
        ep = self.s.episodes[0]
        for arm in "AB":
            v = E.View(ep, arm)
            self.assertTrue(all(x[4] is None for x in RP.read_feedback(v.feedback)))
        v = E.View(ep, "C")
        self.assertTrue(all(x[4] is not None and x[4] > 0 for x in RP.read_feedback(v.feedback)))

    def test_solve_satisfies_every_constraint(self):
        for ep in self.s.episodes:
            d = RP.solve(ep.public_instance())
            self.assertEqual(E.rsig().check(ep.instance, d), [])


if __name__ == "__main__":
    unittest.main()
