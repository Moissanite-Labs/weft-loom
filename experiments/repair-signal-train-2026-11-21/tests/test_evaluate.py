import unittest
from fractions import Fraction

import _setup  # noqa: F401
import episodes as E
import evaluate as V
import latch
import receipts
import reference_policies as RP


class GrammarTests(unittest.TestCase):
    def ok(self, text, n, want):
        got, why = V.parse_reply(text, n)
        self.assertIsNone(why, why)
        self.assertEqual(got, want)

    def bad(self, text, n):
        got, why = V.parse_reply(text, n)
        self.assertIsNone(got)
        self.assertTrue(why)

    def test_integers_fractions_and_decimals_are_exact(self):
        self.ok("x0 = 3/2\nx1 = -2\nx2 = 1.25\nx3 = -0.1", 4,
                [Fraction(3, 2), Fraction(-2), Fraction(5, 4), Fraction(-1, 10)])

    def test_a_leading_plus_is_read_like_the_texts_show_it(self):
        self.ok("x0 = +3/2\nx1 = +2\nx2 = +1.25", 3, [Fraction(3, 2), Fraction(2), Fraction(5, 4)])

    def test_fraction_not_reduced_is_read_exactly(self):
        self.ok("x0 = 6/4\nx1 = 0", 2, [Fraction(3, 2), Fraction(0)])

    def test_fence_and_blank_lines_and_spacing(self):
        self.ok("```text\nx0=1\n\nx1 =\t2\n```", 2, [Fraction(1), Fraction(2)])

    def test_order_is_free(self):
        self.ok("x1 = 2\nx0 = 1", 2, [Fraction(1), Fraction(2)])

    def test_format_breaks(self):
        for text in ("", "   ", "x0 = 1", "x0 = 1\nx0 = 2\nx1 = 3", "x0 = 1\nx1 = 2\nx2 = 3",
                     "Here you go:\nx0 = 1\nx1 = 2", "x0 = 1\nx1 = 2 ok", "x0 = 1/0\nx1 = 2",
                     "x0 = 1e3\nx1 = 2", "x0 = ++1\nx1 = 2", "x0 = +-1\nx1 = 2", "x0 = +\nx1 = 2", "x00 = 1\nx1 = 2", "x0 = .5\nx1 = 2",
                     "x0 = 1.\nx1 = 2", "x0 = 1234567890123\nx1 = 2", "x0 = 1\nx1 = 2\n```", "x0 = 1/2/3\nx1 = 2",
                     "X0 = 1\nx1 = 2", "x0 = 1.0000000000001\nx1 = 2"):
            self.bad(text, 2)

    def test_empty_reply_is_reported_as_empty(self):
        self.assertEqual(V.parse_reply("", 2), (None, "empty reply"))
        self.assertEqual(V.parse_reply("```\n```", 2), (None, "empty reply"))

    def test_unknown_variable(self):
        self.bad("x0 = 1\nx5 = 2", 2)


class CapTests(unittest.TestCase):
    def test_pieces(self):
        self.assertEqual(V.count_pieces("x0 = -12/5"), 8)   # x 0 = - 1 2 / 5 is 8 pieces with "x" as a letter run
        self.assertEqual(V.count_pieces(""), 0)

    def test_cut_to_cap(self):
        text, cut = V.cut_to_cap("x0 = 1\nx1 = 2", 100)
        self.assertEqual((text, cut), ("x0 = 1\nx1 = 2", False))
        text, cut = V.cut_to_cap("x0 = 1\nx1 = 2", 4)
        self.assertTrue(cut)
        self.assertEqual(V.count_pieces(text), 4)

    def test_cap_cuts_a_long_reply_and_it_counts_as_format_break(self):
        s = E.build_set("heldout1", {"S": 10})
        r = V.evaluate_arm(RP.verbose, s, "C", 96, "v")
        self.assertEqual((r.format_broken, r.passed, r.failed, r.capped), (10, 0, 0, 10))

    def test_tight_cap_breaks_a_good_answer_equally_in_every_arm(self):
        s = E.build_set("heldout1", {"S": 10})
        outs = {a: V.evaluate_arm(RP.recompute, s, a, 5, "r").outcomes for a in E.ARMS}
        self.assertEqual(set(outs.values()), {"X" * 10})

    def test_reported_tokens_over_the_cap_refused(self):
        s = E.build_set("heldout1", {"S": 2})
        with self.assertRaises(V.EvalRefused):
            V.evaluate_arm(lambda v: (v.attempt_text, 97), s, "C", 96, "x")

    def test_reported_tokens_at_the_cap_count_as_capped(self):
        s = E.build_set("heldout1", {"S": 2})
        r = V.evaluate_arm(lambda v: (RP.recompute(v), 96), s, "C", 96, "x")
        self.assertEqual((r.capped, r.passed), (2, 2))

    def test_bad_cap_refused(self):
        s = E.build_set("heldout1", {"S": 2})
        for cap in (0, -1, True, 1.5):
            with self.assertRaises(V.EvalRefused):
                V.evaluate_arm(RP.unchanged, s, "C", cap, "x")


class EvaluateTests(unittest.TestCase):
    def test_outcomes_are_three_kinds(self):
        s = E.build_set("heldout1", {"S": 6})
        seq = iter(["", "x0 = 0\nx1 = 0\nx2 = 0\nx3 = 0", None])

        def responder(view):
            t = next(seq, None)
            return RP.recompute(view) if t is None else t
        r = V.evaluate_arm(responder, s, "B", 96, "mix")
        self.assertEqual(r.outcomes[:2], "XF")
        self.assertEqual((r.n, r.passed + r.failed + r.format_broken), (6, 6))

    def test_decimal_answers_are_scored_as_rationals(self):
        s = E.build_set("heldout1", {"S": 30})

        def dec(view):
            return "\n".join("x%d = %s" % (i, _dec(v)) for i, v in enumerate(RP.solve(view.instance)))
        r = V.evaluate_arm(dec, s, "A", 96, "dec")
        self.assertEqual(r.format_broken, 0)
        # the solution has halves, so a decimal answer is exact and passes
        self.assertGreater(r.passed, 0)

    def test_result_body_is_float_free_and_carries_hashes(self):
        s = E.build_set("heldout1", {"S": 4})
        r = V.evaluate_arm(RP.recompute, s, "C", 96, "r")
        body = r.body()
        receipts.check_plain(body)
        self.assertEqual(body["harness"], V.harness_hashes())
        self.assertEqual(set(body["harness"]),
                         {"evaluate_py", "episodes_py", "vendor_loader_py", "rsig_py", "decisions_json"})
        self.assertEqual(body["set_sha256"], s.sha256())
        self.assertEqual((body["rate_num"], body["rate_den"]), (4, 4))
        self.assertEqual(len(body["replies_sha256"]), 64)

    def test_evaluate_py_hash_is_its_source_hash(self):
        import hashlib
        with open(V.harness_files()["evaluate_py"], "rb") as fh:
            self.assertEqual(V.harness_hashes()["evaluate_py"], hashlib.sha256(fh.read()).hexdigest())

    def test_second_set_needs_a_valid_latch_token(self):
        s2 = E.build_set("heldout2", {"S": 2})
        with self.assertRaises(V.EvalRefused):
            V.evaluate_arm(RP.unchanged, s2, "C", 96, "x")
        with self.assertRaises(V.EvalRefused):
            V.evaluate_arm(RP.unchanged, s2, "C", 96, "x", latch_token=latch.LatchToken("forged"))

    def relabelled(self, kind, tier, seed, base):
        ep = E.build_episode("train", "S", 300000)
        return E.Episode(kind, tier, seed, ep.instance, ep.attempt, ep.perturbation, 1, ep.target, ep.target_rule)

    def test_second_set_episodes_cannot_pass_as_the_first_set(self):
        h2 = E.build_set("heldout2", {"S": 3})
        wrapped = E.EpisodeSet("heldout1", {"S": 3}, h2.episodes)         # kinds say heldout2
        with self.assertRaises(V.EvalRefused) as cm:
            V.evaluate_arm(RP.unchanged, wrapped, "C", 96, "x")
        self.assertIn("does not belong", str(cm.exception))

    def test_relabelled_episodes_with_seeds_outside_the_range_are_refused(self):
        for kind, tier, seed in (("heldout1", "S", 500000), ("heldout1", "S", 100000), ("train", "S", 100050),
                                 ("train", "S", 200099), ("heldout1", "M", 400000), ("train", "S", 299999)):
            ep = self.relabelled(kind, tier, seed, None)
            with self.assertRaises(V.EvalRefused, msg=str((kind, tier, seed))):
                V.evaluate_arm(RP.unchanged, E.EpisodeSet(kind, {tier: 1}, [ep]), "C", 96, "x")

    def test_unknown_set_kind_is_refused(self):
        ep = self.relabelled("zzz", "S", 400000, None)
        with self.assertRaises(V.EvalRefused):
            V.evaluate_arm(RP.unchanged, E.EpisodeSet("zzz", {"S": 1}, [ep]), "C", 96, "x")

    def test_an_empty_set_of_an_unknown_kind_is_refused_too(self):
        with self.assertRaises(V.EvalRefused):
            V.evaluate_arm(RP.unchanged, E.EpisodeSet("zzz", {}, []), "C", 96, "x")

    def test_an_episode_inside_its_range_passes_the_seed_check(self):
        ep = self.relabelled("heldout1", "S", 400000, None)
        r = V.evaluate_arm(RP.unchanged, E.EpisodeSet("heldout1", {"S": 1}, [ep]), "C", 96, "x")
        self.assertEqual(r.n, 1)

    def test_unknown_arm_and_non_text_refused(self):
        s = E.build_set("heldout1", {"S": 2})
        with self.assertRaises(V.EvalRefused):
            V.evaluate_arm(RP.unchanged, s, "D", 96, "x")
        with self.assertRaises(V.EvalRefused):
            V.evaluate_arm(lambda v: 5, s, "C", 96, "x")

    def test_the_checker_is_the_judge(self):
        s = E.build_set("heldout1", {"S": 10})
        r = V.evaluate_arm(lambda v: v.attempt_text, s, "C", 96, "same")
        self.assertEqual(r.passed, 0)
        r = V.evaluate_arm(RP.recompute, s, "C", 96, "ok")
        self.assertEqual(r.passed, 10)


class CutAndRescoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = E.build_set("heldout1", {"S": 6, "M": 4})

    def test_a_reply_cut_by_the_harness_is_a_format_break_even_if_the_cut_text_parses(self):
        def last_value_two_digits(view):
            n = view.instance.n
            return "\n".join("x%d = %s" % (i, "12" if i == n - 1 else "0") for i in range(n))
        full = V.evaluate_arm(last_value_two_digits, self.s, "C", 96, "full")
        self.assertEqual(full.format_broken, 0)                    # the text parses when it is not cut
        one = E.EpisodeSet("heldout1", {"S": 1}, self.s.episodes[:1])
        text = last_value_two_digits(E.View(one.episodes[0], "C"))
        cap = V.count_pieces(text) - 1
        cut, was_cut = V.cut_to_cap(text, cap)
        self.assertTrue(was_cut)
        self.assertIsNotNone(V.parse_reply(cut, one.episodes[0].instance.n)[0])   # the cut text is still valid
        r = V.evaluate_arm(last_value_two_digits, one, "C", cap, "cut")
        self.assertEqual((r.outcomes, r.cuts, r.capped), ("X", "1", 1))

    def test_a_responder_can_report_that_it_cut_the_reply(self):
        r = V.evaluate_arm(lambda v: (RP.recompute(v), 5, True), self.s, "C", 96, "x")
        self.assertEqual((r.outcomes, r.cuts), ("X" * 10, "1" * 10))
        self.assertEqual(r.capped, 0)                              # 5 tokens is under the cap: the cut flag alone decides
        r = V.evaluate_arm(lambda v: (RP.recompute(v), 5, False), self.s, "C", 96, "x")
        self.assertEqual((r.passed, r.cuts), (10, "0" * 10))
        r = V.evaluate_arm(lambda v: (RP.recompute(v), 5), self.s, "C", 96, "x")
        self.assertEqual((r.passed, r.cuts), (10, "0" * 10))

    def test_a_cut_flag_with_no_token_count_also_counts_as_capped(self):
        r = V.evaluate_arm(lambda v: (RP.recompute(v), None, True), self.s, "C", 96, "x")
        self.assertEqual((r.outcomes, r.capped), ("X" * 10, 10))

    def test_rescore_gives_the_same_outcomes_as_the_evaluation(self):
        r = V.evaluate_arm(lambda v: RP.recompute(v) if v.instance.seed % 2 else v.attempt_text, self.s, "C", 96, "mix")
        self.assertEqual(V.rescore(r.replies_entry()), r.outcomes)
        self.assertIn("P", r.outcomes)
        self.assertIn("F", r.outcomes)

    def test_rescore_counts_a_cut_flag_as_a_break(self):
        r = V.evaluate_arm(RP.recompute, self.s, "C", 96, "ok")
        entry = r.replies_entry()
        entry["cuts"] = "1" + entry["cuts"][1:]
        self.assertEqual(V.rescore(entry), "X" + r.outcomes[1:])

    def test_rescore_refuses_replies_that_do_not_line_up(self):
        r = V.evaluate_arm(RP.recompute, self.s, "C", 96, "ok")
        bad = [dict(r.replies_entry(), texts=r.texts[:-1]), dict(r.replies_entry(), cuts=r.cuts[:-1]),
               dict(r.replies_entry(), cuts="2" * r.n), dict(r.replies_entry(), set_sha256="0" * 64),
               dict(r.replies_entry(), episode_ids=r.episode_ids[::-1])]
        for entry in bad:
            with self.assertRaises(V.EvalRefused):
                V.rescore(entry)

    def test_rebuild_set_gives_the_same_set(self):
        again = V.rebuild_set([ep.id for ep in self.s.episodes])
        self.assertEqual(again.sha256(), self.s.sha256())
        self.assertEqual(again.counts, {"S": 6, "M": 4})
        self.assertIs(V.rebuild_set([ep.id for ep in self.s.episodes]), again)      # cached

    def test_rebuild_set_refuses_what_it_cannot_rebuild(self):
        for ids in ([], ["heldout1-S"], ["heldout1-S-4x"], ["nokind-S-400000"], ["heldout1-S-400000-1"], [5],
                    ["heldout1-S-100000"], ["heldout1-S-400000", "heldout2-S-500000"], ["heldout1-Q-400000"],
                    ["heldout1-S--5"]):
            with self.assertRaises(V.EvalRefused, msg=str(ids)):
                V.rebuild_set(ids)


def _dec(v):
    # exact decimal text for a fraction whose denominator divides 6 only when it is a half or whole
    if v.denominator == 1:
        return str(v.numerator)
    if v.denominator == 2:
        sign = "-" if v < 0 else ""
        a = abs(v)
        return "%s%d.5" % (sign, a.numerator // a.denominator)
    return str(v)


if __name__ == "__main__":
    unittest.main()
