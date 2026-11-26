#!/usr/bin/env python3
"""Assertion-free R5 control & synthetic-trajectory tests for probe_s1_repair_signal_two_channel.py."""

from __future__ import annotations

import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path

STUDY_DIR = Path(__file__).resolve().parent
if str(STUDY_DIR) not in sys.path:
    sys.path.insert(0, str(STUDY_DIR))

import probe_s1_repair_signal_two_channel as p1


class ProbeS1ControlsTest(unittest.TestCase):
    def test_01_exact_binomial_known_answers_and_r3_rejections(self) -> None:
        self.assertEqual(p1.exact_binom_one_sided_ge(15, 18), Fraction(247, 65536))
        self.assertEqual(p1.exact_binom_two_sided(15, 18), Fraction(247, 32768))
        self.assertEqual(p1.exact_binom_one_sided_ge(11, 14), Fraction(235, 8192))
        self.assertEqual(p1.exact_binom_two_sided(11, 14), Fraction(235, 4096))
        self.assertEqual(p1.exact_binom_one_sided_ge(3, 5), Fraction(1, 2))
        self.assertEqual(p1.exact_binom_two_sided(3, 5), Fraction(1, 1))
        self.assertEqual(p1.exact_binom_one_sided_ge(0, 0), Fraction(1, 1))
        self.assertEqual(p1.exact_binom_two_sided(0, 0), Fraction(1, 1))

        r3 = p1.r3_negative_controls()
        self.assertTrue(r3["all_r3_rejected"])
        for bad in ((True, 5), (1, False)):
            with self.assertRaises(TypeError):
                p1.exact_binom_two_sided(*bad)
        for bad in ((6, 5), (0, -1), (-1, 5)):
            with self.assertRaises(ValueError):
                p1.exact_binom_two_sided(*bad)

    def test_02_synthetic_trajectory_controls(self) -> None:
        ctrl = p1.synthetic_mediation_controls()
        self.assertTrue(ctrl["all_synthetic_controls_passed"])
        self.assertEqual(ctrl["identical_arms_discordant"], 0)
        self.assertEqual(ctrl["constant_compute_escapes"], 0)
        self.assertEqual(ctrl["constant_compute_crossover_diff"], 0)
        self.assertEqual(ctrl["planted_10_vs_0_exact_p"], "1/1024")

        # Synthetic compute-budget crossover control: C solves fast (3s), D escapes (80s) then solves in R3.
        c_fast = [
            [{"seconds": 3.0, "parse_error": None, "verdict": "pass"}]
            if i < 6
            else [{"seconds": 3.0, "parse_error": None, "verdict": "fail"}]
            for i in range(10)
        ]
        d_esc = [
            [
                {"seconds": 3.0, "parse_error": None, "verdict": "fail"},
                {"seconds": 80.0, "parse_error": "format", "verdict": "fail"},
                {"seconds": 3.0, "parse_error": None, "verdict": "pass"},
            ]
            if i < 8
            else [{"seconds": 3.0, "parse_error": None, "verdict": "fail"}]
            for i in range(10)
        ]
        cross = p1.evaluate_paired_trajectories(c_fast, d_esc, budget_s=30.0)
        self.assertEqual(cross["budget_test_C_vs_D"]["x_only"], 6)
        self.assertEqual(cross["budget_test_C_vs_D"]["y_only"], 0)
        self.assertEqual(cross["unbounded_test_C_vs_D"]["x_only"], 0)
        self.assertEqual(cross["unbounded_test_C_vs_D"]["y_only"], 2)
        self.assertEqual(cross["D_escaped_ever"], 8)

    def test_03_committed_results_reconcile_pr38_check_md(self) -> None:
        res = json.loads((STUDY_DIR / "probe_s1_repair_signal_results.json").read_text(encoding="utf-8"))
        ts = res["tier_S"]
        tm = res["tier_M"]

        # Exact stratum-rate non-reversal proof (no Simpson's paradox).
        sr = ts["stratum_rate_check_no_simpson_paradox"]
        self.assertFalse(sr["simpson_paradox_holds"])
        self.assertEqual(sr["C_minus_D_rate_no_escape_exact"], "-16/2881")
        self.assertEqual(sr["C_minus_D_rate_after_escape_exact"], "-1/14")
        self.assertEqual(sr["C_minus_D_rate_overall_exact"], "-2/25")

        # Observed never-escaper principal stratum (66 instances on Tier S).
        ps = ts["observed_principal_stratum_never_escaped_CD"]
        self.assertEqual(ps["n_never_escaped_in_either_C_or_D"], 66)
        self.assertEqual(ps["C_solved"], 44)
        self.assertEqual(ps["D_solved"], 43)
        self.assertEqual(ps["exact_paired_sign_test_C_vs_D"]["p_x_gt_y_exact_frac"], "1/2")

        # Shared both-readable R1-fail -> R2 L1 stats vs per-arm readable rates.
        l1_s = ts["shared_both_readable_R1fail_R2_L1_CD"]
        self.assertEqual(l1_s["per_arm_C_readable_denom"], 65)
        self.assertEqual(l1_s["per_arm_D_readable_denom"], 45)
        self.assertEqual(l1_s["per_arm_C_readable_improved_frac"], "44/65")
        self.assertEqual(l1_s["per_arm_D_readable_improved_frac"], "2/3")
        self.assertEqual(l1_s["shared_both_readable_n"], 45)
        self.assertEqual(l1_s["shared_C_improved"], 30)
        self.assertEqual(l1_s["shared_D_improved"], 30)
        self.assertEqual(l1_s["strict_C_lt_D_vs_D_lt_C"]["x_only"], 3)
        self.assertEqual(l1_s["strict_C_lt_D_vs_D_lt_C"]["y_only"], 4)

        l1_m = tm["shared_both_readable_R1fail_R2_L1_CD"]
        self.assertEqual(l1_m["shared_both_readable_n"], 69)
        self.assertEqual(l1_m["shared_C_improved"], 29)
        self.assertEqual(l1_m["shared_D_improved"], 21)
        self.assertEqual(l1_m["strict_C_lt_D_vs_D_lt_C"]["x_only"], 13)
        self.assertEqual(l1_m["strict_C_lt_D_vs_D_lt_C"]["y_only"], 6)


if __name__ == "__main__":
    unittest.main()
