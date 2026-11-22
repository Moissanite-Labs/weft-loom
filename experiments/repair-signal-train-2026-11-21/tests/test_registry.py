import contextlib
import hashlib
import io
import os
import re
import sys
import unittest
from fractions import Fraction

import _setup  # noqa: F401
import driver
import latch
import power


def read(name):
    with open(os.path.join(_setup.LOOP, name), "rb") as fh:
        return fh.read()


class RegistryTests(unittest.TestCase):
    def test_the_drivers_decision_is_registered(self):
        self.assertIn(driver.DECISION_ID, latch.load_registry(os.path.join(_setup.LOOP, "decisions.json")))

    def test_the_registry_is_exactly_the_one_registered_decision(self):
        self.assertEqual(latch.load_registry(os.path.join(_setup.LOOP, "decisions.json")),
                         frozenset({"primary-c-vs-b-seed0-confirm"}))


class PreregConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read("PREREG.md").decode("utf-8")

    def test_the_prereg_names_the_registry_hash_and_the_decision_id(self):
        self.assertIn(hashlib.sha256(read("decisions.json")).hexdigest(), self.text)
        self.assertIn(driver.DECISION_ID, self.text)

    def test_the_prereg_states_the_driver_choices(self):
        self.assertIn("Batch %d" % driver.BATCH_SIZE, self.text)
        self.assertIn("LoRA rank %d" % driver.LORA_RANK, self.text)
        self.assertIn("1e-3", self.text)

    def test_a_power_row_in_the_prereg_is_the_exact_value(self):
        w = power.power(1000, 15 + 4, 15 - 4, 200)
        single = "%.4f" % (w.numerator / w.denominator)
        rule = power.rule_power(w)
        both = "%.4f" % (rule.numerator / rule.denominator)
        self.assertIn("| 15%% | 4 points | %s | %s |" % (single, both), self.text)

    def test_the_prereg_does_not_call_the_amount_signed_or_train_on_n(self):
        low = self.text.lower()
        self.assertNotIn("signed amount", low)
        self.assertIn("n is not trained", low)
        self.assertIn("test-time controls", low)

    def test_the_pilot_seeds_in_the_prereg_are_the_cost_plan_seeds(self):
        import cost
        p = cost.pilot_plan(96)
        self.assertEqual(p.train_offset, 2000)
        self.assertEqual(p.eval1_offset, 10000)
        for needle in ("302000 to 302127", "352000 to 352127", "310000 to 310049", "360000 to 360049"):
            self.assertIn(needle, self.text)


class PreregMatchesCodeTests(unittest.TestCase):
    """The plan's choices and numbers are the ones the code uses."""

    @classmethod
    def setUpClass(cls):
        cls.text = read("PREREG.md").decode("utf-8")

    def test_the_gates_in_the_prereg_are_the_ones_in_the_driver(self):
        g = driver.GATES
        self.assertEqual((g.min_discordant, g.rate_low, g.rate_high), (10, Fraction(1, 20), Fraction(19, 20)))
        for needle in ("at least 10 discordant", "5 percent or fewer, or 95 percent or more", "`cannot_test`", "`not_supported`",
                       "`support`", "`GATES`"):
            self.assertIn(needle, self.text)

    def test_the_pilot_gates_in_the_prereg_are_the_ones_in_the_driver(self):
        self.assertEqual((driver.PILOT_MAX_NEW_BLOCK, driver.PILOT_MAX_FORMAT_BREAK, driver.PILOT_RATE_LOW,
                          driver.PILOT_RATE_HIGH, driver.PILOT_MAX_HOURS),
                         (Fraction(1, 20), Fraction(1, 5), Fraction(1, 20), Fraction(19, 20), 12))
        for needle in ("every one of the 200 calls", "at most 5 percent of the 200 sampled replies", "20 percent or fewer of its 100 replies",
                       "above 5 percent and below 95 percent", "at most 12 hours", "21,000 calls", "384 steps"):
            self.assertIn(needle, self.text)
        self.assertEqual(driver.plan_calls(__import__("cost").full_plan(2048, 2, 96)), (21000, 384))

    def test_the_decision_procedure_in_the_prereg_reads_item_3_first_like_judge(self):
        import tinker_backend
        i3 = self.text.index("1. Item 3 first: if C breaks the format more often at 1/40, `not_supported`.")
        i1 = self.text.index("2. Item 1. Not testable gives `cannot_test`.")
        i2 = self.text.index("3. Item 2 the same way.")
        self.assertLess(i3, i1)
        self.assertLess(i1, i2)
        self.assertIn("a format harm gives `not_supported` even when item 1 or item 2 could not be tested", self.text)
        with open(driver.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertLess(src.index('cmp_["format_harm"]["first_better"]'), src.index("for name, label in"))
        self.assertIn("## After the pilot", self.text)
        for needle in ("The go is the owner's call, and the code does not enforce it",
                       "The full run must not start after a no-go", "new pilot run id",
                       "exclusive lock (`flock`", "a run cannot name another one",
                       "names the plan it approves, by name and by the fingerprint of the plan",
                       "loses the extra tokens of that one overrun"):
            self.assertIn(needle, self.text)
        self.assertTrue(hasattr(tinker_backend, "acquire_lock"))

    def test_the_marked_choices_are_the_ones_in_the_code(self):
        import codec
        import tinker_backend
        self.assertIn("temperature 0.0", self.text)
        with open(tinker_backend.__file__, encoding="utf-8") as fh:
            self.assertIn("temperature=0.0", fh.read())
        self.assertIn("`%s`" % codec.SYSTEM_LINE, self.text)
        self.assertIn(codec.END_NAME, self.text)
        self.assertIn(codec.EOS_NAME, self.text)
        for needle in ("(choice, the tie-break)", "lower variable index first, then the more negative step"):
            self.assertIn(needle, self.text)

    def test_the_text_e_floor_in_the_prereg_is_what_the_script_prints(self):
        sys.path.insert(0, os.path.join(_setup.LOOP, "checks"))
        try:
            import e_floor
        finally:
            sys.path.pop(0)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(e_floor.main(), 0)
        out = buf.getvalue()
        for key, val in (("e_mechanical", 207), ("e_lookahead", 264), ("true_mechanical", 574), ("true_lookahead", 691),
                         ("same_in_order", 53), ("same_multiset", 58), ("same_max", 95), ("amounts_same", 190)):
            self.assertRegex(out, r"%s +%d\n" % (key, val))
        for needle in ("207 of 1000", "264 of 1000", "574 of 1000", "691 of 1000", "116 of 420", "71 of 362", "19 of 166",
                       "1 of 39", "53 episodes", "190 match"):
            self.assertIn(needle, self.text)

    def test_the_rule2_tie_counts_in_the_prereg_are_what_the_script_prints(self):
        sys.path.insert(0, os.path.join(_setup.LOOP, "checks"))
        try:
            import rule2_ties
        finally:
            sys.path.pop(0)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(rule2_ties.main(), 0)
        rows = {ln.split()[0] + (" " + ln.split()[1] if ln.split()[1] in ("1", "2") else ""): ln.split()
                for ln in buf.getvalue().splitlines()[1:]}
        self.assertEqual([rows[k][-3:] for k in ("training", "held-out 1", "held-out 2")],
                         [["491", "159", "159"], ["259", "90", "90"], ["244", "73", "73"]])
        for needle in ("159 of the 491", "90 of 259", "73 of 244"):
            self.assertIn(needle, self.text)

    def test_the_target_counts_in_the_prereg_are_what_the_script_prints(self):
        sys.path.insert(0, os.path.join(_setup.LOOP, "checks"))
        try:
            import targets
        finally:
            sys.path.pop(0)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(targets.main(), 0)
        out = buf.getvalue()
        for pattern in (r"train_rule_max-excess +1450\n", r"train_rule_search +491\n", r"train_rule_planted +107\n",
                        r"mean_amount_C 1\.4115\n", r"mean_amount_E 1\.4657\n",
                        r"moved_1 total 440 +max-excess 440 +search 0 +planted 0\n",
                        r"moved_2 total 560 +max-excess 251 +search 259 +planted 50\n",
                        r"one_subtraction_per_violation 476 of 1000\n"):
            self.assertRegex(out, pattern)
        for needle in ("1450, 491 and 107 of 2048", "1.466 against 1.412", "440 of 440 episodes", "251 of 560",
                       "259 more, and 50 need the planted point", "476 of 1000"):
            self.assertIn(needle, self.text)

    def test_the_minimal_effects_in_the_prereg_are_the_exact_ones(self):
        self.assertIn("4.5 points at 15 percent discordant, 5.5 points at 25 percent and 6.5 points at 35 percent", self.text)
        for share, halves in ((15, 9), (25, 11), (35, 13)):
            self.assertGreaterEqual(power.rule_power_at(1000, share, halves), power.TARGET)
            self.assertLess(power.rule_power_at(1000, share, halves - 1), power.TARGET)


if __name__ == "__main__":
    unittest.main()
