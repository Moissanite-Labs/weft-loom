import unittest
from itertools import product

import _path  # noqa: F401
import stats


class Stats(unittest.TestCase):
    def test_sign_test_known_values(self):
        self.assertEqual(stats.sign_test(0, 0), 1.0)
        self.assertEqual(stats.sign_test(5, 0), 1 / 32)
        self.assertEqual(stats.sign_test(0, 5), 1.0)
        self.assertAlmostEqual(stats.sign_test(8, 2), 56 / 1024)
        self.assertAlmostEqual(stats.sign_test(5, 5, "two-sided"), 1.0)
        self.assertAlmostEqual(stats.sign_test(9, 1, "two-sided"), 2 * 11 / 1024)
        with self.assertRaises(ValueError):
            stats.sign_test(1, 1, "less")

    def test_signflip_matches_brute_force(self):
        for diffs in ([1, 2, 3], [3, -1, 0, 2], [-2, -2], [], [0, 0], [1, 1, 1, -1]):
            d = [x for x in diffs if x]
            obs = sum(diffs)
            n = sum(1 for s in product((1, -1), repeat=len(d)) if sum(a * b for a, b in zip(s, map(abs, d))) >= obs)
            self.assertAlmostEqual(stats.signflip_test(diffs), n / 2 ** len(d))

    def test_signflip_direction(self):
        self.assertLess(stats.signflip_test([2, 3, 1, 2, 4]), 0.05)
        self.assertEqual(stats.signflip_test([-2, -3, -1, -2, -4]), 1.0)


if __name__ == "__main__":
    unittest.main()
