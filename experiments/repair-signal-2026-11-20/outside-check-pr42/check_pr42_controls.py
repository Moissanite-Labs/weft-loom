"""Must-fail controls for check_pr42.py. Each builds a small synthetic log and expects the script to refuse it, or to
report no difference where none exists, or to report a difference where one was planted.

The output has no timings, so it is the same under every interpreter mode.
Usage: python3 -I -B check_pr42_controls.py
"""
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # python3 -I drops the script directory
import check_pr42 as chk  # noqa: E402

PROMPT = ("Find rational numbers x0 to x1 that satisfy every constraint below.\n"
          "c0: x1 - x0 <= 1\n"
          "goal: x0 - x1 <= -1\n"
          "Reply with exactly one line per variable.")


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def rnd(arm, inst, number, verdict="fail", error=None, secs=3.0, reply="x0 = 0\nx1 = 0", excess=("1",)):
    return {"type": "round", "arm": arm, "instance": inst, "round": number, "prompt": PROMPT, "reply": reply,
            "reply_sha256": sha(reply), "verdict": verdict, "parse_error": error, "seconds": secs,
            "violations": [{"cid": "goal", "excess": e} for e in excess] if verdict == "fail" else []}


def write(rows):
    d = tempfile.mkdtemp(prefix="pr42-ctl-")
    path = os.path.join(d, "log.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("".join(json.dumps(r) + "\n" for r in rows))
    return path


def log(per_arm, instances=range(10)):
    """per_arm maps an arm to a function (instance) -> list of round rows."""
    rows = []
    for arm in chk.ARMS:
        for inst in instances:
            rows += per_arm[arm](inst)
    return rows


def same(arm):
    def make(inst):
        return [rnd(arm, inst, 1), rnd(arm, inst, 2, verdict="pass", reply="x0 = 0\nx1 = 1", secs=4.0)]
    return make


def tier(rows):
    return chk.Tier(chk.load_log(write(rows)))


def captured(fn, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        fn(*args)
    return out.getvalue()


class Arithmetic(unittest.TestCase):
    def test_tail_values(self):
        self.assertEqual(chk.tail(3, 5), Fraction(1, 2))
        self.assertEqual(chk.tail(0, 4), Fraction(1))
        self.assertEqual(chk.tail(15, 18), Fraction(247, 65536))

    def test_two_sided(self):
        self.assertEqual(chk.two_sided(15, 3), Fraction(247, 32768))
        self.assertEqual(chk.two_sided(3, 15), Fraction(247, 32768))
        self.assertEqual(chk.two_sided(0, 0), Fraction(1))
        self.assertEqual(chk.two_sided(5, 5), Fraction(1))

    def test_holm_adjusts_in_order_and_never_lowers(self):
        out = chk.holm({"a": Fraction(1, 100), "b": Fraction(1, 100), "c": Fraction(1)})
        self.assertEqual(out, {"a": Fraction(3, 100), "b": Fraction(3, 100), "c": Fraction(1)})
        out = chk.holm({"a": Fraction(1, 100), "b": Fraction(2, 100)})
        self.assertEqual(out["b"], Fraction(2, 100))

    def test_seconds_are_exact(self):
        self.assertEqual(chk.seconds({"seconds": 0.1}), Fraction(1, 10))

    def test_quantile_picks_the_ranked_element(self):
        self.assertEqual(chk.quantile([5, 1, 3, 2, 4, 6, 7, 8, 9, 10], 1, 2), 6)
        self.assertIsNone(chk.quantile([], 1, 2))


class Loading(unittest.TestCase):
    def good(self):
        return log({a: same(a) for a in chk.ARMS})

    def refused(self, rows, phrase):
        with self.assertRaises(chk.CheckError) as caught:
            chk.load_log(write(rows))
        self.assertIn(phrase, str(caught.exception))

    def test_clean_log_loads(self):
        self.assertEqual(sorted(chk.load_log(write(self.good()))), list(chk.ARMS))

    def test_missing_arm_is_refused(self):
        self.refused([r for r in self.good() if r["arm"] != "D"], "arms found")

    def test_arms_over_different_instances_are_refused(self):
        self.refused([r for r in self.good() if not (r["arm"] == "C" and r["instance"] == 3)], "same instances")

    def test_duplicate_round_is_refused(self):
        rows = self.good()
        self.refused(rows + [rows[0]], "duplicate round")

    def test_round_gap_is_refused(self):
        self.refused([r for r in self.good() if not (r["arm"] == "B" and r["instance"] == 2 and r["round"] == 1)], "not 1..n")

    def test_line_that_is_not_json_is_refused(self):
        path = write(self.good())
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("{torn\n")
        with self.assertRaises(chk.CheckError):
            chk.load_log(path)

    def test_missing_file_is_refused(self):
        with self.assertRaises(chk.CheckError):
            chk.load_log(os.path.join(tempfile.mkdtemp(prefix="pr42-ctl-"), "none.jsonl"))

    def test_prompt_without_constraints_is_refused(self):
        with self.assertRaises(chk.CheckError):
            chk.instance_of([{"prompt": "Find numbers x0 to x1."}])


class NoDifference(unittest.TestCase):
    """Two arms that are identical must give no discordant pairs, whatever the statistic."""

    def test_identical_arms_have_no_discordant_pairs(self):
        t = tier(log({a: same(a) for a in chk.ARMS}))
        ids = t.ids
        for name in ("pass4", "pure", "r2esc", "r2pass", "esc"):
            self.assertEqual(chk.pair(t.flag("C", name), t.flag("D", name), ids), (0, 0), name)
        for limit in chk.WINDOWS:
            self.assertEqual(chk.pair(t.within("C", limit), t.within("D", limit), ids), (0, 0), limit)
        self.assertEqual(chk.pair(t.late("C"), t.late("D"), ids), (0, 0))
        self.assertEqual(chk.pair(t.any_format_r2("C"), t.any_format_r2("D"), ids), (0, 0))

    def test_report_on_identical_arms_says_no_reversal_and_no_gap(self):
        t = tier(log({a: same(a) for a in chk.ARMS}))
        text = captured(chk.section_split, "synthetic", t)
        self.assertIn("reversal (the same non-zero direction in both strata and the opposite one overall): no", text)
        text = captured(chk.section_pairs, "synthetic", t)
        self.assertIn("C only 0, D only 0", text)
        self.assertNotIn("C only 1", text)


class PlantedDifference(unittest.TestCase):
    def test_a_planted_gap_is_found(self):
        def never(arm):
            return lambda inst: [rnd(arm, inst, 1), rnd(arm, inst, 2, secs=4.0)]
        per = {a: same(a) for a in chk.ARMS}
        per["C"] = never("C")
        t = tier(log(per))
        self.assertEqual(chk.pair(t.flag("D", "pass4"), t.flag("C", "pass4"), t.ids), (10, 0))
        self.assertEqual(chk.tail(10, 10), Fraction(1, 1024))

    def test_unreadable_round_is_counted_as_an_escape_and_a_late_pass(self):
        def escape(arm):
            return lambda inst: [rnd(arm, inst, 1), rnd(arm, inst, 2, verdict="unparsable", error="x", secs=60.0, reply="thinking"),
                                 rnd(arm, inst, 3, verdict="pass", reply="x0 = 0\nx1 = 1", secs=3.0)]
        per = {a: same(a) for a in chk.ARMS}
        per["D"] = escape("D")
        t = tier(log(per))
        self.assertEqual(chk.pair(t.flag("D", "r2esc"), t.flag("C", "r2esc"), t.ids), (10, 0))
        self.assertEqual(chk.pair(t.late("D"), t.late("C"), t.ids), (10, 0))
        self.assertEqual(chk.pair(t.flag("C", "pure"), t.flag("D", "pure"), t.ids), (10, 0))
        self.assertEqual(chk.pair(t.flag("C", "pass4"), t.flag("D", "pass4"), t.ids), (0, 0))

    def test_budget_edge_is_inclusive(self):
        def timed(secs):
            return lambda arm: (lambda inst: [rnd(arm, inst, 1, secs=secs / 2), rnd(arm, inst, 2, verdict="pass", secs=secs / 2)])
        per = {a: timed(30.0)(a) for a in chk.ARMS}
        per["D"] = timed(30.5)("D")
        t = tier(log(per))
        self.assertEqual(sum(t.within("C", 30).values()), 10)
        self.assertEqual(sum(t.within("D", 30).values()), 0)

    def test_pairing_drops_instances_whose_round_one_differs(self):
        per = {a: same(a) for a in chk.ARMS}
        per["A"] = lambda inst: [rnd("A", inst, 1, reply="x0 = 9\nx1 = 9" if inst < 3 else "x0 = 0\nx1 = 0"),
                                 rnd("A", inst, 2, verdict="pass", reply="x0 = 0\nx1 = 1", secs=4.0)]
        t = tier(log(per))
        keep, dropped = chk.paired_ids(t.units, "A", "C")
        self.assertEqual((len(keep), dropped), (7, 3))


class Reading(unittest.TestCase):
    def setUp(self):
        self.t = tier(log({a: same(a) for a in chk.ARMS}))

    def test_lenient_takes_the_last_value_written(self):
        self.assertEqual(self.t.lenient(0, "x0 = 5, no\nx0 = 0\nx1 = 3/2"), {0: Fraction(0), 1: Fraction(3, 2)})

    def test_lenient_accepts_a_satisfying_answer_inside_prose(self):
        self.assertTrue(self.t.lenient_ok(0, "Thinking... so the answer is\nx0 = 0\nx1 = 1.0"))

    def test_lenient_refuses_a_missing_variable(self):
        self.assertFalse(self.t.lenient_ok(0, "x0 = 0"))

    def test_lenient_refuses_a_variable_outside_the_instance(self):
        self.assertFalse(self.t.lenient_ok(0, "x0 = 0\nx1 = 2\nx2 = 1"))

    def test_lenient_skips_a_zero_denominator(self):
        self.assertFalse(self.t.lenient_ok(0, "x0 = 0\nx1 = 1/0"))

    def test_lenient_refuses_an_answer_that_breaks_a_constraint(self):
        self.assertFalse(self.t.lenient_ok(0, "x0 = 0\nx1 = 1/2"))

    def test_lenient_ignores_inequalities(self):
        self.assertFalse(self.t.lenient_ok(0, "x1 - x0 <= 1\nx0 - x1 <= -1"))

    def test_boundary_answer_is_satisfying(self):
        self.assertTrue(self.t.lenient_ok(0, "x0 = 0\nx1 = 1"))

    def test_reply_kinds(self):
        self.assertEqual(chk.reply_kind("x0 = 1.5\nx1 = 2"), "decimal")
        self.assertEqual(chk.reply_kind("x0 = 1\nx1 = 2"), "other answer")
        self.assertEqual(chk.reply_kind("```\nx0 = 1.5\nx1 = 2\n```"), "decimal")
        self.assertEqual(chk.reply_kind("So x0 = 1.5"), "prose")
        self.assertEqual(chk.reply_kind(""), "prose")

    def test_excess_sum_is_exact(self):
        row = {"violations": [{"excess": "1/3"}, {"excess": "1/6"}]}
        self.assertEqual(chk.excess_sum(row), Fraction(1, 2))


def main():
    out = io.StringIO()
    result = unittest.TextTestRunner(stream=out, verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    bad = result.failures + result.errors
    print("controls run: %d, failed: %d" % (result.testsRun, len(bad)))
    for case, trace in bad:
        print("FAILED %s" % case.id())
        print(trace)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
