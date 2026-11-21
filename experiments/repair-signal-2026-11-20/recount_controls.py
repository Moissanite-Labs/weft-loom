"""Must-fail controls for recount.py. Each corrupts the committed tier S log in one way and expects a refusal.

Kept outside tests/ so the registered harness suite stays exactly as it was at the registered commit.
Usage: python3 -I -B recount_controls.py

The last class compares recount.py's reply reader with the harness parser on generated replies. That is the one
place where the harness is imported, and only to compare.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import recount  # noqa: E402

LOG = os.path.join(HERE, "results", "Qwen3.8-27B-AD-Q4_K_M-S.jsonl")


def load():
    with open(LOG, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def run(rows):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "log.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("".join(json.dumps(r) + "\n" for r in rows))
        return recount.recount(path)


class RecountControls(unittest.TestCase):
    def refused(self, rows, phrase):
        with self.assertRaises(SystemExit) as caught, contextlib.redirect_stderr(io.StringIO()):
            run(rows)
        self.assertIn("RECOUNT_FAIL", str(caught.exception))
        self.assertIn(phrase, str(caught.exception))

    def first(self, rows, test):
        return next(k for k, r in enumerate(rows) if test(r))

    def test_clean_log_matches_registered_counts(self):
        out = run(load())["registered_counts"]
        self.assertEqual(out["solved_of_100"], {"A": 65, "B": 75, "C": 69, "D": 77})
        self.assertEqual((out["primary_C_vs_B"]["first_only"], out["primary_C_vs_B"]["second_only"]), (7, 13))
        self.assertEqual(out["first_reply_identical_in_all_four_arms"], 100)

    def test_flipped_verdict_is_refused(self):
        rows = load()
        k = self.first(rows, lambda r: r["type"] == "round" and r["verdict"] == "fail" and r["round"] == 4)
        rows[k]["verdict"] = "pass"
        self.refused(rows, "verdict fail here, pass in the log")

    def test_forged_passing_reply_is_refused(self):
        rows = load()
        k = self.first(rows, lambda r: r["type"] == "round" and r["verdict"] == "pass")
        lines = rows[k]["reply"].split("\n")
        lines[0] = "x0 = 999999"
        rows[k]["reply"] = "\n".join(lines)
        self.refused(rows, "violations differ")

    def test_edited_violation_is_refused(self):
        rows = load()
        k = self.first(rows, lambda r: r["type"] == "round" and r["verdict"] == "fail" and r["violations"])
        rows[k]["violations"] = rows[k]["violations"][1:]
        self.refused(rows, "violations differ")

    def test_readable_reply_marked_unreadable_is_refused(self):
        rows = load()
        k = self.first(rows, lambda r: r["type"] == "round" and r["verdict"] == "fail")
        rows[k]["parse_error"] = "made up"
        self.refused(rows, "readable here but not by the harness")

    def test_dropped_unit_is_refused(self):
        rows = load()
        k = self.first(rows, lambda r: r["type"] == "unit" and r["arm"] == "C")
        del rows[k]
        self.refused(rows, "400 distinct units")

    def test_forged_unit_line_is_refused(self):
        rows = load()
        k = self.first(rows, lambda r: r["type"] == "unit" and not r["passed"])
        rows[k]["passed"], rows[k]["pass_round"] = True, 4
        self.refused(rows, "unit line")

    def test_swapped_feedback_is_refused(self):
        rows = load()
        k = self.first(rows, lambda r: r["type"] == "round" and r["round"] == 2 and r["arm"] == "C")
        rows[k]["prompt"] = "Verdict: FAILED.\nReply with a corrected assignment, one line per variable, and nothing else."
        self.refused(rows, "was not sent the feedback")


class PinnedOutput(unittest.TestCase):
    """Every number recount.py prints for the committed logs of both models, pinned in recount_golden.json."""

    MODELS = ("Qwen3.8-27B-AD-Q4_K_M", "gemma-4-E4B-it-Q8_0")

    def golden(self):
        with open(os.path.join(HERE, "recount_golden.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def test_full_output_matches_golden(self):
        golden = self.golden()
        for model in self.MODELS:
            for tier in ("S", "M"):
                got = recount.recount(os.path.join(HERE, "results", "%s-%s.jsonl" % (model, tier)))
                got.pop("file")
                self.assertEqual(json.loads(json.dumps(got)), golden[model][tier], (model, tier))

    def test_golden_matches_the_committed_recount_files(self):
        golden = self.golden()
        for model in self.MODELS:
            with open(os.path.join(HERE, "results", "%s-recount.txt" % model), encoding="utf-8") as fh:
                committed = json.load(fh)
            for entry, tier in zip(committed, ("S", "M")):
                entry.pop("file")
                self.assertEqual(entry, golden[model][tier], (model, tier))


class ReadLineControls(unittest.TestCase):
    """Each line breaks one guard of recount.read_line, so a copy without that guard accepts it or crashes."""

    def test_wrong_separator_is_unreadable(self):
        for line in ["x0 : 3", "x0 - 3", "x0 < 3", "x0 3", "x0", "x0 =", "x0 = -"]:
            self.assertIsNone(recount.read_line(line), line)

    def test_closing_assignment_of_exactly_n_lines_with_a_stray_fence(self):
        self.assertEqual(recount.closing_assignment("x0 = 1\nx1 = 2\n```", 2), {0: 1, 1: 2})
        self.assertIsNone(recount.closing_assignment("x0 = 1\n```", 2))

    def test_dangling_slash_is_unreadable(self):
        for line in ["x0 = 3/", "x0 = 3/ 4", "x0 = 3/x"]:
            self.assertIsNone(recount.read_line(line), line)


class ParserAgreement(unittest.TestCase):
    """recount.py's reply reader and the harness's parser are written separately. They must accept the same replies."""

    PIECES = ["x0 = 1", "x1 = -3/2", "x2 = 0", "x3 = 7/4", "x0=1", "x1 =\t2", "x00 = 1", "x4 = 1", "x1 = 1/0", "x1 = 1.5",
              "x1 = +1", "x2 = 1234567890123", "x2 = 123456789012", "x3 = 1/1234567890123", "x1 = \u0663", "", "  ",
              "```", "```text", "Here is the answer:", "x1 = 2 ", "x1 = 2/3/4", "x = 1", "x1 = -", "X1 = 1", "x1 == 1", "x1 = 1 # ok", "x1 : 1", "x1 - 1", "x1 = 1/"]

    def test_same_verdict_and_values_on_generated_replies(self):
        import random
        import rsig
        rng = random.Random(20261121)
        replies = ["x0 = 1\nx1 = 2\nx2 = 3\nx3 = 4", "```\nx0 = 1\nx1 = 2\nx2 = 3\nx3 = 4\n```", "```\n```", "", "```",
                   "x0 = 1\n\nx1 = 2\nx2 = 3\nx3 = 4\n", "```py\nx0 = 1\nx1 = 2\nx2 = 3\nx3 = 4```", "x3 = 4\nx2 = 3\nx1 = 2\nx0 = 1",
                   "x0 = 1\nx1 = 2\nx2 = 3\nx3 = 4\nx3 = 4", "```\nx0 = 1\n```\nx1 = 2\nx2 = 3\nx3 = 4\n```"]
        for _ in range(3000):
            replies.append(rng.choice(["\n", "\n", "\r\n", " \n"]).join(rng.choice(self.PIECES) for _ in range(rng.randint(1, 6))))
        for _ in range(6000):
            lines = ["x%d%s=%s%s" % (i, rng.choice(["", " ", "\t", "  "]), rng.choice(["", " ", "\t"]),
                                     rng.choice(["0", "-3", "7/2", "-11/6", "123456789012", "5/1"])) for i in range(4)]
            rng.shuffle(lines)
            for _ in range(rng.choice([0, 0, 0, 1, 1, 2])):
                at = rng.randrange(len(lines) + 1)
                if rng.random() < 0.5 and at < len(lines):
                    lines[at] = rng.choice(self.PIECES)
                else:
                    lines.insert(at, rng.choice(self.PIECES))
            text = rng.choice(["\n", "\n", "\n", "\r\n"]).join(lines)
            if rng.random() < 0.25:
                text = "```" + rng.choice(["", "text", "py3"]) + "\n" + text + rng.choice(["\n", ""]) + "```"
            replies.append(rng.choice(["", "", " ", "\n"]) + text + rng.choice(["", "", "\n", " "]))
        readable = 0
        for reply in replies:
            theirs, _ = rsig.parse_candidate(reply, 4)
            ours = recount.read_reply(reply, 4)
            self.assertEqual(theirs is None, ours is None, repr(reply))
            if theirs is not None:
                readable += 1
                self.assertEqual(theirs, [ours[i] for i in range(4)], repr(reply))
        self.assertGreater(readable, 1000)
        self.assertGreater(len(replies) - readable, 1000)

    def test_same_verdict_on_every_logged_reply(self):
        import rsig
        for r in load():
            if r["type"] != "round":
                continue
            theirs, _ = rsig.parse_candidate(r["reply"], 4)
            self.assertEqual(theirs is None, recount.read_reply(r["reply"], 4) is None)


if __name__ == "__main__":
    unittest.main()
