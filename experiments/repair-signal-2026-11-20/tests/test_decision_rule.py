"""Boundaries of the registered decision rule in analyze.py (PREREG.md, "What counts for and against the claim")."""
import unittest

import _path  # noqa: F401
import analyze


def arms(*rates):
    return {a: {"pass_rate": r} for a, r in zip("ABCD", rates)}


def prim(first, second, p=0.5, p_rev=0.5, pairs=100):
    return {"pairs": pairs, "first_only": first, "second_only": second, "p_pass_sign": p, "p_reverse": p_rev}


MID = arms(0.3, 0.4, 0.5, 0.6)


class Boundaries(unittest.TestCase):
    def test_floor_is_inclusive_at_five_percent(self):
        self.assertEqual(analyze.decide(arms(0.05, 0.05, 0.05, 0.05), prim(8, 4)), "floor_or_ceiling")
        self.assertNotEqual(analyze.decide(arms(0.05, 0.05, 0.05, 0.06), prim(8, 4)), "floor_or_ceiling")

    def test_ceiling_is_inclusive_at_ninety_five_percent(self):
        self.assertEqual(analyze.decide(arms(0.95, 0.95, 0.95, 0.95), prim(8, 4)), "floor_or_ceiling")
        self.assertNotEqual(analyze.decide(arms(0.95, 0.95, 0.95, 0.94), prim(8, 4)), "floor_or_ceiling")

    def test_ten_discordant_pairs_are_enough_nine_are_not(self):
        self.assertEqual(analyze.decide(MID, prim(5, 4)), "too_few_discordant_pairs")
        self.assertNotEqual(analyze.decide(MID, prim(6, 4)), "too_few_discordant_pairs")

    def test_threshold_decides_supports(self):
        self.assertEqual(analyze.decide(MID, prim(9, 2, p=analyze.ALPHA)), "supports")
        self.assertNotEqual(analyze.decide(MID, prim(9, 2, p=analyze.ALPHA + 1e-9)), "supports")

    def test_a_tie_in_discordant_pairs_is_against_one_more_win_is_inconclusive(self):
        self.assertEqual(analyze.decide(MID, prim(6, 6, p=0.6, p_rev=0.6)), "against")
        self.assertEqual(analyze.decide(MID, prim(7, 6, p=0.4, p_rev=0.8)), "inconclusive")

    def test_reverse_threshold_decides_against(self):
        self.assertEqual(analyze.decide(MID, prim(3, 12, p=0.99, p_rev=analyze.ALPHA)), "against")
        self.assertEqual(analyze.decide(MID, prim(8, 5, p=0.3, p_rev=analyze.ALPHA)), "against")

    def test_overall(self):
        self.assertEqual(analyze.overall({"S": "against", "M": "against"}), "against")
        self.assertEqual(analyze.overall({"S": "against", "M": "inconclusive"}), "not_decided")
        self.assertEqual(analyze.overall({"S": "against", "M": "supports"}), "mixed")
        self.assertEqual(analyze.overall({"S": "supports", "M": "inconclusive"}), "supports")
        self.assertEqual(analyze.overall({"S": "floor_or_ceiling", "M": "floor_or_ceiling"}), "not_decided")


if __name__ == "__main__":
    unittest.main()
