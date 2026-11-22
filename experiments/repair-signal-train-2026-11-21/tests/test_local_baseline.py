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
        seen = 0
        for root, dirs, names in os.walk(BASE):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for name in sorted(names):
                with open(os.path.join(root, name), "r", encoding="utf-8") as fh:
                    text = fh.read()
                seen += 1
                for needle in ("/Users/", "/home/", "/Volumes/", "/private/", "/tmp/"):
                    self.assertNotIn(needle, text, (name, needle))
        self.assertGreaterEqual(seen, 12)

    def facts(self, *flags):
        return subprocess.run([sys.executable, "-I", *flags, os.path.join(BASE, "facts.py")],
                              capture_output=True, text=True)

    def test_facts_txt_is_what_facts_py_prints_in_every_mode(self):
        want = read("local-baseline/facts.txt")
        for flags in (("-B",), ("-O", "-B"), ("-B", "-W", "error")):
            got = self.facts(*flags)
            self.assertEqual((got.returncode, got.stdout, got.stderr), (0, want, ""), flags)

    def test_the_plans_local_numbers_are_the_ones_facts_prints(self):
        facts = read("local-baseline/facts.txt")
        for line in ("free-reasoning calls: 60", "free-reasoning calls with no thinking tokens: 0",
                     "free-reasoning fewest thinking tokens in one call: 531",
                     "free B tier M: 15 calls, passed 5, no answer 8, cut by the cap 2",
                     "free C tier M: 15 calls, passed 4, no answer 10, cut by the cap 1",
                     "mean milliseconds per call, forced answer: 3305",
                     "sampling calls of the full plan: 21000, training steps: 384",
                     "hours of sampling for the full plan at the local mean per call: 19.28 (4627/240)",
                     "that is above the 12 hour gate: yes",
                     "tries at a cap of 96 with an empty answer (smoke.out, then smoke2.out A to D): 5",
                     "calls of the two smoke runs that returned reasoning text: 7",
                     "one-line arithmetic question: 82 completion tokens, answer '7/4'",
                     "puzzle at a cap of 1500: 569 completion tokens, finished",
                     "local layout equals codec.py ids on 15 prompts"):
            self.assertIn(line + "\n", facts)
        for needle in ("at least 531 thinking tokens", "the 7 calls of the two smoke runs", "That is 67 calls",
                       "In 5 tries at a cap of 96 tokens", "answer in 82 tokens", "it wrote 569 tokens",
                       "on 15 prompts", "2 (B) and 1 (C) more calls were cut", "19.28 hours",
                       "4 episodes passed only with C and 4 only with B", "(UTC)"):
            self.assertIn(needle, self.prereg)
        for banned in ("does not use the amounts", "always opens a thinking block", "no switch turns"):
            self.assertNotIn(banned, self.prereg)
            self.assertNotIn(banned, read("README.md"))

    def test_facts_refuses_a_log_that_lacks_a_quoted_line(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(BASE, os.path.join(tmp, "local-baseline"), ignore=shutil.ignore_patterns("__pycache__"))
            for name in os.listdir(HERE):
                if name.endswith(".py") or name in ("vendor", "decisions.json"):
                    src = os.path.join(HERE, name)
                    (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, os.path.join(tmp, name))
            log = os.path.join(tmp, "local-baseline", "logs", "baseline-stdout.txt")
            with open(log, "w", encoding="utf-8") as fh:
                fh.write("nothing here\n")
            got = subprocess.run([sys.executable, "-I", "-B", os.path.join(tmp, "local-baseline", "facts.py")],
                                 capture_output=True, text=True)
            self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
            self.assertIn("PROBLEM", got.stdout)


if __name__ == "__main__":
    unittest.main()
