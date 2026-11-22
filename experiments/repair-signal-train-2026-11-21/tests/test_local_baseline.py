import json
import os
import subprocess
import sys
import tempfile
import unittest

import _setup  # noqa: F401

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(HERE, "local-baseline")


def read(name):
    with open(os.path.join(HERE, name), "r", encoding="utf-8") as fh:
        return fh.read()


def run_check(path):
    return subprocess.run([sys.executable, "-I", "-B", os.path.join(BASE, "check_seeds.py"), path],
                          capture_output=True, text=True)


class LocalBaselineTests(unittest.TestCase):
    """The committed local baseline is pilot-seed data, and the plan quotes it exactly."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(BASE, "summary.json"), "r", encoding="utf-8") as fh:
            cls.summary = json.load(fh)
        cls.prereg = read("PREREG.md")

    def test_every_line_has_a_pilot_evaluation_seed(self):
        got = run_check(os.path.join(BASE, "results.jsonl"))
        self.assertEqual(got.returncode, 0, got.stdout + got.stderr)
        self.assertIn("560 lines, 100 distinct (tier, seed) pairs, 0 outside the pilot evaluation ranges", got.stdout)

    def test_the_seed_check_refuses_a_seed_outside_the_pilot_ranges(self):
        for tier, seed in (("S", 400000), ("S", 310050), ("S", 309999), ("M", 360050), ("M", 310000), ("X", 310000),
                           ("S", "310000"), ("S", True), ("S", None)):
            with tempfile.TemporaryDirectory() as tmp:
                path = os.path.join(tmp, "results.jsonl")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(json.dumps({"tier": tier, "seed": seed, "mode": "F", "text": "A", "outcome": "failed"}) + "\n")
                self.assertEqual(run_check(path).returncode, 1, (tier, seed))

    def test_the_seed_check_accepts_the_range_ends_and_refuses_an_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "results.jsonl")
            with open(path, "w", encoding="utf-8") as fh:
                for tier, seed in (("S", 310000), ("S", 310049), ("M", 360000), ("M", 360049)):
                    fh.write(json.dumps({"tier": tier, "seed": seed}) + "\n")
            self.assertEqual(run_check(path).returncode, 0)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("")
            self.assertEqual(run_check(path).returncode, 1)

    def test_the_seed_check_refuses_a_summary_that_disagrees_with_the_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("results.jsonl", "summary.json"):
                with open(os.path.join(BASE, name), "r", encoding="utf-8") as fh:
                    text = fh.read()
                if name == "summary.json":
                    data = json.loads(text)
                    data["F"]["A_S"]["passed"] += 1
                    text = json.dumps(data)
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                    fh.write(text)
            got = run_check(os.path.join(tmp, "results.jsonl"))
            self.assertEqual(got.returncode, 1)
            self.assertIn("summary.json cell F A_S", got.stdout)

    def test_the_plan_table_is_the_summary(self):
        for text in "ABCEN":
            cells = [self.summary["F"]["%s_%s" % (text, tier)] for tier in "SM"]
            self.assertEqual([c["n"] for c in cells], [50, 50])
            row = "| %s | %d | %d | %d, %d | %d, %d |" % (
                text, cells[0]["passed"], cells[1]["passed"], cells[0]["format_breaks"], cells[1]["format_breaks"],
                cells[0]["cut_by_cap"], cells[1]["cut_by_cap"])
            self.assertIn(row, self.prereg)

    def test_the_paired_count_and_the_reasoning_line_are_the_summary(self):
        p = self.summary["paired"]["F_both"]
        self.assertEqual((p["episodes"], p["only_C_passed"], p["only_B_passed"], p["both_passed"], p["neither_passed"]),
                         (100, 4, 4, 24, 68))
        self.assertIn("only C passed %d, only B passed %d, both passed %d and neither passed %d" % (
            p["only_C_passed"], p["only_B_passed"], p["both_passed"], p["neither_passed"]), self.prereg)
        R = self.summary["R"]
        self.assertEqual((R["B_S"]["passed"], R["C_S"]["passed"], R["B_M"]["passed"], R["C_M"]["passed"],
                          R["B_M"]["no_answer"], R["C_M"]["no_answer"]), (15, 15, 5, 4, 8, 10))
        self.assertEqual((R["B_S"]["median_generated_tokens"], R["C_S"]["median_generated_tokens"]), (773, 751))
        for needle in ("passed 15 of 15 in tier S", "a median of 773 (B) and 751 (C)", "5 of 15 (B) and 4 of 15 (C)",
                       "8 (B) and 10 (C)"):
            self.assertIn(needle, self.prereg)

    def test_the_capped_rates_are_away_from_the_floor_and_ceiling_as_the_plan_says(self):
        rates = [self.summary["F"]["%s_%s" % (t, k)]["passed"] for t in "BCEN" for k in "SM"]
        self.assertEqual((min(rates), max(rates)), (7, 21))        # 14 and 42 percent of 50
        self.assertIn("between 14 and 42 percent", self.prereg)
        self.assertEqual(self.summary["F"]["A_M"]["passed"], 0)

    def test_the_committed_files_carry_no_local_paths(self):
        for name in sorted(os.listdir(BASE)):
            if name == "__pycache__":
                continue
            with open(os.path.join(BASE, name), "r", encoding="utf-8") as fh:
                text = fh.read()
            for needle in ("/Users/", "/home/", "/Volumes/", "/private/", "/tmp/"):
                self.assertNotIn(needle, text, (name, needle))


if __name__ == "__main__":
    unittest.main()
