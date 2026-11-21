import itertools
import unittest
from fractions import Fraction
from math import factorial

import _setup  # noqa: F401
import power as P
import ratchet as RT


def brute(n, p_num, q_num, den):
    """Enumerate every (first-only, second-only) pair with the multinomial law."""
    r_num = den - p_num - q_num
    total = Fraction(0)
    for a, b in itertools.product(range(n + 1), repeat=2):
        if a + b > n:
            continue
        d = a + b
        if d < 10 or not a > b:
            continue
        if RT.sign_test_p(a, b) > Fraction(1, 40):
            continue
        coef = factorial(n) // (factorial(a) * factorial(b) * factorial(n - d))
        total += Fraction(coef * p_num ** a * q_num ** b * r_num ** (n - d), den ** n)
    return total


class PowerTests(unittest.TestCase):
    def test_threshold_agrees_with_the_ratchets_sign_test(self):
        for d in range(0, 45):
            want = None
            if d >= P.MIN_DISCORDANT:
                for a in range(0, d + 1):
                    if a > d - a and RT.sign_test_p(a, d - a) <= Fraction(1, 40):
                        want = a
                        break
            self.assertEqual(P.min_wins(d), want, d)

    def test_threshold_values(self):
        self.assertIsNone(P.min_wins(9))
        self.assertIsNone(P.min_wins(10, Fraction(1, 2000)))
        self.assertEqual(P.min_wins(10), 9)       # 9 of 10: p = 11/1024 <= 1/40; 8 of 10: 56/1024 > 1/40
        self.assertEqual(P.min_wins(20), 15)
        self.assertEqual(P.min_wins(10, Fraction(1, 2)), 6)

    def test_power_equals_a_brute_force_enumeration(self):
        for n, p, q, den in ((12, 30, 10, 100), (15, 20, 5, 100), (14, 1, 1, 4), (10, 1, 0, 2), (16, 25, 20, 100)):
            self.assertEqual(P.power(n, p, q, den), brute(n, p, q, den), (n, p, q, den))

    def test_certain_and_impossible_cases(self):
        self.assertEqual(P.power(40, 10, 0, 10), Fraction(1))             # the first always wins
        self.assertEqual(P.power(40, 0, 10, 10), Fraction(0))             # the second always wins
        self.assertEqual(P.power(40, 0, 0, 10), Fraction(0))              # never a discordant episode
        self.assertEqual(P.power(9, 10, 0, 10), Fraction(0))              # at most 9 discordant episodes: never enough
        self.assertLessEqual(P.power(60, 15, 15, 100), Fraction(1, 40))   # no effect: the size of the test

    def test_power_grows_with_the_effect_and_with_n(self):
        weak = P.power(100, 12, 8, 100)
        strong = P.power(100, 16, 4, 100)
        self.assertLess(weak, strong)
        self.assertLess(P.power(60, 16, 4, 100), P.power(120, 16, 4, 100))

    def test_the_minimum_is_ten_discordant(self):
        self.assertEqual(P.MIN_DISCORDANT, 10)
        self.assertEqual(P.power(10, 10, 0, 10), Fraction(1))       # all 10 discordant, all for the first
        self.assertIsNone(P.min_wins(P.MIN_DISCORDANT - 1))
        self.assertEqual(P.min_wins(P.MIN_DISCORDANT), 9)

    def test_bad_arguments(self):
        for args in ((10, 60, 60, 100), (10, -1, 5, 10), (0, 1, 1, 10), (10, 1, 1, 0)):
            with self.assertRaises(P.PowerError, msg=str(args)):
                P.power(*args)

    def test_table_and_rule_power(self):
        rows = P.table(30, discordant_shares=(20,), effects=(5, 10, 30))
        self.assertEqual([(d, e) for d, e, _ in rows], [(20, 5), (20, 10)])      # an effect above the share is skipped
        self.assertEqual(rows[0][2], P.power(30, 25, 15, 200))
        self.assertEqual(P.rule_power(Fraction(1, 2)), Fraction(1, 8))


class MinimalEffectTests(unittest.TestCase):
    def test_rule_power_at_is_the_cube_of_the_single_power_with_the_stated_shares(self):
        # 15 percent discordant, a net effect of 4 points (8 half points): p = 19/200, q = 11/200
        self.assertEqual(P.rule_power_at(30, 15, 8), P.rule_power(P.power(30, 19, 11, 200)))
        self.assertEqual(P.rule_power_at(30, 15, 9), P.rule_power(P.power(30, 39, 21, 400)))

    def test_the_bisection_finds_the_first_effect_that_reaches_the_target(self):
        for n, share in ((60, 25), (80, 35), (100, 30)):
            h = P.min_effect_halves(n, share)
            self.assertIsNotNone(h)
            scan = next(x for x in range(1, 2 * share + 1) if P.rule_power_at(n, share, x) >= P.TARGET)
            self.assertEqual(h, scan)
            self.assertGreaterEqual(P.rule_power_at(n, share, h), P.TARGET)
            if h > 1:
                self.assertLess(P.rule_power_at(n, share, h - 1), P.TARGET)

    def test_a_power_exactly_at_the_target_reaches_it(self):
        exact = P.rule_power_at(60, 25, 5)
        self.assertEqual(P.min_effect_halves(60, 25, exact), 5)

    def test_no_effect_up_to_the_share_can_be_enough_for_a_small_set(self):
        self.assertIsNone(P.min_effect_halves(20, 15))

    def test_the_target_can_be_changed(self):
        low = P.min_effect_halves(60, 25, Fraction(1, 5))
        self.assertLess(low, P.min_effect_halves(60, 25))

    def test_effect_text(self):
        self.assertEqual([P.halves_text(h) for h in (1, 2, 8, 11)], ["0.5", "1.0", "4.0", "5.5"])


if __name__ == "__main__":
    unittest.main()
