import unittest
from fractions import Fraction as F

import _path  # noqa: F401
import rsig

TINY = rsig.Instance(2, [rsig.Constraint("c0", 0, 1, 1), rsig.Constraint("goal", 1, 0, F(-1, 2))])
V = [rsig.Violation("c0", 0, 1, F(1), F(3, 2)), rsig.Violation("goal", 1, 0, F(-1, 2), F(1, 2))]


class Parser(unittest.TestCase):
    def ok(self, text, n=2):
        c, e = rsig.parse_candidate(text, n)
        self.assertIsNone(e, e)
        return c

    def bad(self, text, n=2):
        c, e = rsig.parse_candidate(text, n)
        self.assertIsNone(c)
        self.assertTrue(e)

    def test_plain_and_fenced(self):
        self.assertEqual(self.ok("x0 = 3/2\nx1 = -2"), [F(3, 2), F(-2)])
        self.assertEqual(self.ok("```\nx0 = 1\nx1 = 0\n```"), [F(1), F(0)])
        self.assertEqual(self.ok("```text\nx1 = 0\nx0 = 1\n```\n"), [F(1), F(0)])
        self.assertEqual(self.ok("x0=1\nx1 = 2/4"), [F(1), F(1, 2)])

    def test_rejects_prose_decimals_and_oddities(self):
        for t in ["", "  \n", "Sure! x0 = 1\nx1 = 2", "x0 = 0.5\nx1 = 1", "x0 = 1\nx1 = 1\nx2 = 1",
                  "x0 = 1", "x0 = 1\nx0 = 2\nx1 = 1", "x0 = 1/0\nx1 = 1", "x0 = +1\nx1 = 1",
                  "x00 = 1\nx1 = 1", "x0 = 1 \nx1 = 1 and more", "x0 = 1e3\nx1 = 1", "X0 = 1\nx1 = 1",
                  "x0 = 1\nx1 = 1\n```", "x0 = 1/2/3\nx1 = 1", "x0 = 1234567890123\nx1 = 1",
                  "x0 = ١\nx1 = 1", "x0 = 1\n\nthanks\nx1 = 1"]:
            with self.subTest(t=t):
                self.bad(t)

    def test_exact_value_survives(self):
        self.assertEqual(self.ok("x0 = 1/3\nx1 = 0")[0] * 3, 1)

    def test_roundtrip_with_checker(self):
        c = self.ok("x0 = 1\nx1 = 0")
        self.assertEqual(rsig.check(TINY, c), [])


class Prompts(unittest.TestCase):
    def test_initial_prompt_states_instance_and_gap(self):
        p = rsig.initial_prompt(TINY)
        self.assertIn("c0: x0 - x1 <= 1", p)
        self.assertIn("goal: x1 - x0 <= -1/2", p)
        self.assertIn("x0 - x1 at least 1/2", p)
        self.assertNotIn("planted", p)

    def test_arm_texts(self):
        a, b, c, d = (rsig.feedback(x, V) for x in "ABCD")
        self.assertNotIn("c0", a)
        for t in (b, c, d):
            self.assertIn("c0: x0 - x1 <= 1", t)
            self.assertIn("goal: x1 - x0 <= -1/2", t)
        self.assertNotIn("excess", b)
        self.assertNotIn("excess", a)
        self.assertIn("(excess +3/2)", c)
        self.assertIn("(excess +1/2)", c)
        self.assertIn("(excess -3/2)", d)
        self.assertIn("(excess -1/2)", d)

    def test_c_and_d_differ_only_in_the_sign(self):
        c, d = rsig.feedback("C", V), rsig.feedback("D", V)
        self.assertNotEqual(c, d)
        self.assertEqual(c.replace("+", "#"), d.replace("-3/2", "#3/2").replace("-1/2", "#1/2")
                         .replace("<= #1/2", "<= -1/2"))

    def test_b_is_c_without_the_amount(self):
        import re
        c = rsig.feedback("C", V)
        c = re.sub(r" \(excess [^)]*\)", "", c).replace(rsig.EXCESS_NOTE + "\n", "")
        self.assertEqual(c, rsig.feedback("B", V))

    def test_unparsed_feedback_is_the_same_for_every_arm_and_leaks_nothing(self):
        t = rsig.feedback_unparsed("line 1 is not of the form 'x0 = 3/2'")
        self.assertNotIn("excess", t)
        self.assertNotIn("c0", t)

    def test_a_names_no_constraint(self):
        self.assertEqual(rsig.feedback("A", V), rsig.feedback("A", V[:1]))


if __name__ == "__main__":
    unittest.main()
