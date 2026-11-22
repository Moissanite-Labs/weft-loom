import unittest
from fractions import Fraction

import _setup  # noqa: F401
import episodes as E


class SeedTests(unittest.TestCase):
    def setUp(self):
        self.base, self.span, self.off = dict(E.KIND_BASE), E.KIND_SPAN, dict(E.TIER_OFFSET)

    def tearDown(self):
        E.KIND_BASE.clear()
        E.KIND_BASE.update(self.base)
        E.KIND_SPAN = self.span
        E.TIER_OFFSET.clear()
        E.TIER_OFFSET.update(self.off)

    def test_default_ranges(self):
        self.assertEqual(E.seed_span("train", "S", 10), (300000, 300009))
        self.assertEqual(E.seed_span("heldout1", "M", 10), (450000, 450009))
        self.assertEqual(E.seed_span("heldout2", "S", 1), (500000, 500000))

    def test_registered_overlap_refused(self):
        E.KIND_BASE["train"] = 100050
        with self.assertRaises(E.SeedRangeError) as cm:
            E.seed_span("train", "S", 10)
        self.assertIn("registered", str(cm.exception))

    def test_registered_overlap_refused_second_range(self):
        E.KIND_BASE["train"] = 200099
        with self.assertRaises(E.SeedRangeError) as cm:
            E.seed_span("train", "S", 5)
        self.assertIn("registered", str(cm.exception))

    def test_other_kind_overlap_refused(self):
        E.KIND_BASE["heldout1"] = 300010
        with self.assertRaises(E.SeedRangeError) as cm:
            E.seed_span("heldout1", "S", 10)
        self.assertIn("overlap the train", str(cm.exception))

    def test_leaving_the_kind_range_refused(self):
        E.KIND_SPAN = 1000
        with self.assertRaises(E.SeedRangeError) as cm:
            E.seed_span("train", "M", 10)
        self.assertIn("leave", str(cm.exception))

    def test_offset_moves_the_span_and_stays_in_its_tier(self):
        self.assertEqual(E.seed_span("train", "S", 10, 10000), (310000, 310009))
        self.assertEqual(E.seed_span("train", "M", 10, 10000), (360000, 360009))
        with self.assertRaises(E.SeedRangeError):
            E.seed_span("train", "S", 10, E.MAX_PER_TIER - 5)      # would run into the M seeds
        with self.assertRaises(E.SeedRangeError):
            E.seed_span("train", "M", 10, E.MAX_PER_TIER - 5)
        for bad in (-1, True, 1.5):
            with self.assertRaises(E.SeedRangeError):
                E.seed_span("train", "S", 10, bad)
        a = E.build_set("train", {"S": 3}, 10000)
        self.assertEqual([ep.seed for ep in a.episodes], [310000, 310001, 310002])
        self.assertNotEqual(a.sha256(), E.build_set("train", {"S": 3}).sha256())

    def test_check_seed_accepts_only_the_seeds_a_kind_and_tier_own(self):
        E.check_seed("train", "S", 300000)
        E.check_seed("heldout2", "M", 550199)
        for args in (("train", "S", 100000), ("train", "S", 200050), ("train", "S", 299999),
                     ("train", "S", -1), ("train", "S", 300000 + 0.5), ("train", "S", Fraction(300000)),
                     ("train", "S", 350000), ("heldout1", "S", 300000), ("heldout1", "M", 400000),
                     ("heldout2", "S", 500000 + E.MAX_PER_TIER), ("train", "S", 300000.0), ("train", "S", True),
                     ("nope", "S", 300000), ("train", "Z", 300000)):
            with self.assertRaises(E.SeedRangeError, msg=str(args)):
                E.check_seed(*args)

    def test_build_episode_refuses_a_seed_outside_its_range(self):
        for args in (("train", "S", 100000), ("heldout1", "S", 200099), ("train", "S", 400000),
                     ("heldout2", "M", 500000), ("train", "S", 50)):
            with self.assertRaises(E.SeedRangeError, msg=str(args)):
                E.build_episode(*args)

    def test_bad_arguments_refused(self):
        for args in (("nope", "S", 1), ("train", "Z", 1), ("train", "S", 0), ("train", "S", E.MAX_PER_TIER + 1),
                     ("train", "S", True), ("train", "S", 2.0)):
            with self.assertRaises(E.SeedRangeError, msg=str(args)):
                E.seed_span(*args)

    def test_built_sets_are_disjoint_from_each_other_and_the_registered_ranges(self):
        seen = set()
        for kind in E.KIND_BASE:
            s = E.build_set(kind, {"S": 5, "M": 5})
            seeds = {ep.seed for ep in s.episodes}
            self.assertFalse(seeds & seen)
            seen |= seeds
            for lo, hi in E.REGISTERED_RANGES:
                self.assertFalse(any(lo <= x <= hi for x in seeds))


class AttemptTests(unittest.TestCase):
    def test_every_attempt_fails_and_every_target_passes(self):
        R = E.rsig()
        s = E.build_set("train", {"S": 30, "M": 30})
        for ep in s.episodes:
            self.assertTrue(ep.violations())
            self.assertEqual(R.check(ep.instance, list(ep.target)), [])

    def test_perturbation_is_recorded_and_uses_the_generator_denominator(self):
        R = E.rsig()
        s = E.build_set("train", {"S": 30, "M": 30})
        for ep in s.episodes:
            self.assertIn(len(ep.perturbation), (1, 2))
            den = R.TIERS[ep.tier]["den"]
            planted = list(ep.instance.planted)
            moved = list(planted)
            for v, step in ep.perturbation:
                self.assertEqual((step * den).denominator, 1)
                self.assertNotEqual(step, 0)
                moved[v] += step
            self.assertEqual(tuple(moved), ep.attempt)

    def test_attempt_that_still_passes_is_rejected(self):
        calls = []

        def draw(tries, inst):
            calls.append(tries)
            return [(0, Fraction(0))] if tries == 1 else [(0, Fraction(3, 1))]
        ep = E.build_episode("train", "S", 300000, _draw=draw)
        self.assertEqual(ep.tries, 2)
        self.assertTrue(ep.violations())

    def test_a_planted_point_that_fails_the_checker_is_an_error(self):
        from unittest import mock
        R = E.rsig()
        bad = [R.Violation("c0", 0, 1, Fraction(0), Fraction(1))]
        with mock.patch.object(R, "check", lambda inst, cand: bad):
            with self.assertRaises(E.EpisodeError):
                E.build_episode("train", "S", 300000)

    def test_render_refuses_an_attempt_that_passes(self):
        ep = E.build_episode("train", "S", 300000)
        passing = E.Episode(ep.kind, ep.tier, ep.seed, ep.instance, ep.target, (), 1, ep.target)
        with self.assertRaises(E.EpisodeError):
            E.render(passing, "C")

    def test_no_failing_attempt_is_an_error(self):
        with self.assertRaises(E.EpisodeError):
            E.build_episode("train", "S", 300000, _draw=lambda t, i: [(0, Fraction(0))])

    def test_target_rules_and_the_target_is_the_same_in_every_arm(self):
        s = E.build_set("train", {"S": 40, "M": 40})
        rules = {ep.target_rule for ep in s.episodes}
        self.assertEqual(rules, {"max-excess", "search", "planted"})
        for ep in s.episodes:
            for arm in E.ARMS:
                self.assertEqual(E.render(ep, arm).target_text, E.render(ep, "A").target_text)
            if ep.target_rule == "planted":
                self.assertEqual(ep.target, tuple(ep.instance.planted))
            else:
                self.assertEqual(sum(1 for a, b in zip(ep.target, ep.attempt) if a != b) <= 2, True)
        self.assertGreater(sum(1 for ep in s.episodes if ep.target_rule != "planted"), len(s) * 0.8)

    def test_same_seed_same_episode(self):
        a = E.build_episode("train", "S", 300007)
        b = E.build_episode("train", "S", 300007)
        self.assertEqual(a.sha256(), b.sha256())
        self.assertNotEqual(a.sha256(), E.build_episode("train", "S", 300008).sha256())


class CanonicalRepairTests(unittest.TestCase):
    def setUp(self):
        self.R = E.rsig()

    def inst(self, n, cons, planted):
        return self.R.Instance(n, [self.R.Constraint(*c) for c in cons], planted=[Fraction(x) for x in planted])

    def fx(self, values):
        return [Fraction(x) for x in values]

    def test_shared_first_named_variable_is_lowered_by_the_largest_excess(self):
        inst = self.inst(3, [("c0", 0, 1, 0), ("c1", 0, 2, 0)], [0, 1, 2])
        got, rule = E.canonical_repair(self.R, inst, self.fx([5, 1, 2]))
        self.assertEqual((got, rule), (self.fx([1, 1, 2]), "max-excess"))

    def test_shared_second_named_variable_is_raised(self):
        inst = self.inst(3, [("c0", 1, 0, 0), ("c1", 2, 0, 0)], [2, 1, 1])
        got, rule = E.canonical_repair(self.R, inst, self.fx([-3, 1, 0]))
        self.assertEqual((got, rule), (self.fx([1, 1, 0]), "max-excess"))

    def test_a_single_violation_lowers_the_first_named_variable_not_the_lower_index(self):
        inst = self.inst(2, [("c0", 1, 0, 1)], [0, 1])
        got, rule = E.canonical_repair(self.R, inst, self.fx([0, 3]))
        self.assertEqual((got, rule), (self.fx([0, 1]), "max-excess"))

    def test_a_variable_with_two_roles_is_skipped_and_the_search_decides(self):
        # x0 is first named in c0 and second named in c1: moving it cannot fix both
        inst = self.inst(3, [("c0", 0, 1, 0), ("c1", 2, 0, 0)], [0, 0, 0])
        got, rule = E.canonical_repair(self.R, inst, self.fx([1, 0, 2]))
        self.assertEqual(rule, "search")
        self.assertEqual(self.R.check(inst, got), [])
        self.assertEqual(sum(1 for a, b in zip(got, [1, 0, 2]) if a != b), 2)

    def test_the_largest_excess_can_fail_and_the_search_takes_over(self):
        # lowering x0 by the largest excess (4) breaks c2 (x3 - x0 <= -1), a constraint that was fine
        inst = self.inst(4, [("c0", 0, 1, 0), ("c1", 0, 2, 0), ("c2", 3, 0, -1)], [2, 2, 2, 1])
        start = self.fx([5, 1, 2, 2])
        got, rule = E.canonical_repair(self.R, inst, start)
        self.assertEqual(rule, "search")
        self.assertEqual(self.R.check(inst, got), [])
        self.assertEqual(got, self.fx([5, 5, 5, 2]))

    def test_three_separate_violations_fall_back_to_the_planted_point(self):
        inst = self.inst(6, [("c0", 0, 1, 0), ("c1", 2, 3, 0), ("c2", 4, 5, 0)], [0] * 6)
        got, rule = E.canonical_repair(self.R, inst, self.fx([1, 0, 1, 0, 1, 0]))
        self.assertEqual((got, rule), (self.fx([0] * 6), "planted"))

    def test_a_passing_attempt_has_nothing_to_repair(self):
        inst = self.inst(2, [("c0", 0, 1, 0)], [0, 0])
        with self.assertRaises(E.EpisodeError):
            E.canonical_repair(self.R, inst, self.fx([0, 0]))

    def test_search_order_is_by_total_size_then_count_then_variable(self):
        moves = [(0, Fraction(-1)), (1, Fraction(1)), (2, Fraction(-3))]
        want = [((0, Fraction(-1)),), ((1, Fraction(1)),), ((0, Fraction(-1)), (1, Fraction(1))),
                ((2, Fraction(-3)),), ((0, Fraction(-1)), (2, Fraction(-3))), ((1, Fraction(1)), (2, Fraction(-3)))]
        self.assertEqual(E.search_order(moves), want)
        # a single move and a pair of the same total size: the single comes first
        tie = [(0, Fraction(-2)), (1, Fraction(1)), (2, Fraction(1))]
        got = E.search_order(tie)
        self.assertEqual(got[:2], [((1, Fraction(1)),), ((2, Fraction(1)),)])
        self.assertLess(got.index(((0, Fraction(-2)),)), got.index(((1, Fraction(1)), (2, Fraction(1)))))
        # two moves on one variable never form a pair
        same = [(0, Fraction(-1)), (0, Fraction(-3))]
        self.assertEqual(E.search_order(same), [((0, Fraction(-1)),), ((0, Fraction(-3)),)])
        self.assertEqual(E.search_order([]), [])

    def test_search_prefers_the_smaller_total_move(self):
        # two variables moved: fixing needs both; the cheaper pair is chosen
        inst = self.inst(4, [("c0", 0, 1, 0), ("c1", 2, 3, 0)], [0, 0, 0, 0])
        got, rule = E.canonical_repair(self.R, inst, self.fx([1, 0, 3, 0]))
        self.assertEqual(rule, "search")
        self.assertEqual(got, self.fx([0, 0, 0, 0]))


class ArmTests(unittest.TestCase):
    def setUp(self):
        self.R = E.rsig()
        self.eps = E.build_set("train", {"S": 20, "M": 20}).episodes

    def test_a_and_b_use_rsig_text(self):
        for ep in self.eps:
            v = ep.violations()
            self.assertEqual(E.render(ep, "A").messages[-1]["content"], self.R.feedback_A(v))
            self.assertEqual(E.render(ep, "B").messages[-1]["content"], self.R.feedback_B(v))

    def test_first_two_messages_identical_across_arms(self):
        for ep in self.eps[:10]:
            first = [E.render(ep, a).messages[:2] for a in E.ARMS]
            self.assertTrue(all(f == first[0] for f in first))

    def test_c_e_n_have_one_neutral_label_and_no_defining_sentence(self):
        for ep in self.eps:
            for arm in "CEN":
                text = E.render(ep, arm).messages[-1]["content"]
                low = text.lower()
                for word in ("excess", "left side", "minus", "bound.", "signed"):
                    self.assertNotIn(word, low)
                lines = text.split("\n")
                self.assertEqual(lines[0], "Verdict: FAILED. Violated constraints:")
                self.assertEqual(lines[-1], self.R.REPLY_TAIL)
                for ln in lines[1:-1]:
                    self.assertRegex(ln, r"^- \S+: x\d+ - x\d+ <= -?\d+(/\d+)? \(s [+-]?\d+(/\d+)?\)$")

    def test_every_true_amount_is_positive_so_n_is_c_relabelled(self):
        s = E.build_set("train", {"S": 60, "M": 60})
        for ep in s.episodes:
            c = E.render(ep, "C").messages[-1]["content"]
            n = E.render(ep, "N").messages[-1]["content"]
            self.assertNotIn("(s -", c)
            self.assertEqual(c.replace("(s +", "(s -"), n)

    def test_only_the_numbers_differ_between_c_e_n(self):
        import re
        for ep in self.eps:
            texts = {a: E.render(ep, a).messages[-1]["content"] for a in "CEN"}
            stripped = {a: re.sub(r"\(s [^)]*\)", "(s)", t) for a, t in texts.items()}
            self.assertEqual(stripped["C"], stripped["E"])
            self.assertEqual(stripped["C"], stripped["N"])

    def test_n_is_c_with_signs_flipped(self):
        for ep in self.eps:
            v = ep.violations()
            c = E.amounts_for("C", v, ep.seed, ep.tier)
            n = E.amounts_for("N", v, ep.seed, ep.tier)
            self.assertEqual(c, [x.excess for x in v])
            self.assertEqual(n, [-x for x in c])
            self.assertTrue(all(x > 0 for x in c))

    def test_e_has_the_same_count_looks_like_c_and_ignores_the_truth(self):
        s = E.build_set("train", {"S": 150, "M": 150})
        same_all = 0
        tot_c = tot_e = n = 0
        for ep in s.episodes:
            v = ep.violations()
            e = E.amounts_for("E", v, ep.seed, ep.tier)
            self.assertEqual(len(e), len(v))
            self.assertTrue(all(x > 0 for x in e))             # positive, as C's always are
            fake = [self.R.Violation("x", 0, 1, Fraction(0), Fraction(99)) for _ in v]
            self.assertEqual(e, E.amounts_for("E", fake, ep.seed, ep.tier))
            same_all += 1 if e == [x.excess for x in v] else 0
            tot_c += sum(x.excess for x in v)
            tot_e += sum(e)
            n += len(v)
        self.assertLess(same_all, len(s) // 8)                 # chance coincidences only
        self.assertLess(abs(tot_e - tot_c) / n, Fraction(1, 4))   # the same size on average

    def test_e_amounts_come_from_decoy_puzzles_outside_every_range(self):
        for tier in E.TIERS:
            lo = E.DECOY_BASE + E.TIER_OFFSET[tier]
            for kind, base in E.KIND_BASE.items():
                self.assertFalse(base <= lo <= base + E.KIND_SPAN - 1 or base <= lo + E.DECOY_POOL <= base + E.KIND_SPAN)
            for r_lo, r_hi in E.REGISTERED_RANGES:
                self.assertFalse(r_lo <= lo <= r_hi)
            pool = E.decoy_pool(tier)
            self.assertEqual(sum(len(v) for v in pool.values()), E.DECOY_POOL)
            for count, rows in pool.items():
                self.assertTrue(all(len(r) == count and all(x > 0 for x in r) for r in rows))

    def test_e_exists_for_every_violation_count_in_the_planned_sets(self):
        for kind, counts in (("train", {"S": 1024, "M": 1024}), ("heldout1", {"S": 500, "M": 500}),
                             ("heldout2", {"S": 500, "M": 500})):
            for ep in E.build_set(kind, counts).episodes:
                E.render(ep, "E")

    def test_e_without_a_decoy_for_the_count_is_an_error(self):
        v = [self.R.Violation("x", 0, 1, Fraction(0), Fraction(1)) for _ in range(40)]
        with self.assertRaises(E.EpisodeError):
            E.amounts_for("E", v, 1, "S")

    def test_unknown_arm_refused(self):
        with self.assertRaises(E.EpisodeError):
            E.feedback_text("Z", self.eps[0].violations(), 1, "S")

    def test_view_hides_the_planted_point(self):
        v = E.View(self.eps[0], "C")
        self.assertIsNone(v.instance.planted)
        self.assertFalse(hasattr(v, "target"))

    def test_train_arms_are_a_b_c_and_e_n_are_test_time_texts(self):
        self.assertEqual(E.TRAIN_ARMS, ("A", "B", "C"))
        self.assertEqual(set(E.ARMS) - set(E.TRAIN_ARMS), {"E", "N"})


if __name__ == "__main__":
    unittest.main()
