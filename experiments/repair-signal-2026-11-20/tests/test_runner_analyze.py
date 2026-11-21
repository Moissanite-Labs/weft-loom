import json
import os
import tempfile
import unittest
from fractions import Fraction as F

import _path  # noqa: F401
import analyze
import rsig
import runner
import selftest

INSTS = rsig.make_suite(9100, 12, "S")


def unit(model="m", arm="C", inst=1, tier="S", passed=True, rnd=2, k=4):
    return {"type": "unit", "model": model, "arm": arm, "instance": inst, "tier": tier, "k": k,
            "passed": passed, "pass_round": rnd if passed else None, "rounds_used": rnd if passed else k,
            "stagnant": 0, "transitions": 1, "unparsable_rounds": 0, "instance_sha256": "x"}


class Mocks(unittest.TestCase):
    def test_unknown_mock_kind_is_refused(self):
        with self.assertRaises(ValueError):
            runner.mock_chat("folow")

    def test_follow_first_answer_is_zeros_then_moves_by_excess(self):
        inst = INSTS[0]
        chat = runner.mock_chat("follow")
        msgs = [{"role": "user", "content": rsig.initial_prompt(inst)}]
        r1 = chat(msgs)
        self.assertEqual(r1, "\n".join("x%d = 0" % i for i in range(inst.n)))
        cand, _ = rsig.parse_candidate(r1, inst.n)
        v = rsig.check(inst, cand)
        self.assertTrue(v)
        msgs += [{"role": "assistant", "content": r1}, {"role": "user", "content": rsig.feedback("C", v)}]
        c2, _ = rsig.parse_candidate(chat(msgs), inst.n)
        self.assertEqual(c2[v[0].u], -v[0].excess)
        msgs[-1] = {"role": "user", "content": rsig.feedback("D", v)}
        c3, _ = rsig.parse_candidate(chat(msgs), inst.n)
        self.assertEqual(c3[v[0].u], v[0].excess)

    def test_ignore_mock_solution_is_feasible(self):
        for inst in INSTS:
            first = rsig.initial_prompt(inst)
            sol = runner._solve_prompt(first, inst.n)
            self.assertEqual(rsig.check(inst, sol), [], inst.seed)

    def test_ignore_mock_answers_zeros_until_its_round_and_then_the_solution(self):
        chat = runner.mock_chat("ignore")
        for inst in INSTS[:6]:
            first = rsig.initial_prompt(inst)
            at = 2 + int(runner.sha(first), 16) % 4
            zeros = "\n".join("x%d = 0" % i for i in range(inst.n))
            solved = "\n".join("x%d = %s" % (i, v) for i, v in enumerate(runner._solve_prompt(first, inst.n)))
            for rnd in range(1, 7):
                msgs = [{"role": "user", "content": first}]
                for _ in range(rnd - 1):
                    msgs += [{"role": "assistant", "content": "a"}, {"role": "user", "content": "b"}]
                self.assertEqual(chat(msgs), zeros if rnd < at else solved, (inst.seed, rnd, at))

    def test_garbage_is_unparsable_in_every_arm(self):
        for arm in "ABCD":
            _, u = runner.run_unit(runner.mock_chat("garbage"), INSTS[0], arm, 3, "g")
            self.assertEqual((u["passed"], u["unparsable_rounds"], u["rounds_used"]), (False, 3, 3))


class RunUnit(unittest.TestCase):
    def test_round_limit_and_pass_round(self):
        rounds, u = runner.run_unit(runner.mock_chat("follow"), INSTS[0], "C", 4, "m")
        self.assertLessEqual(len(rounds), 4)
        if u["passed"]:
            self.assertEqual(rounds[-1]["verdict"], "pass")
            self.assertEqual(u["pass_round"], len(rounds))
        _, u1 = runner.run_unit(runner.mock_chat("follow"), INSTS[0], "A", 1, "m")
        self.assertEqual(u1["rounds_used"], 1)
        self.assertFalse(u1["passed"])

    def test_hashes_match_content(self):
        rounds, _ = runner.run_unit(runner.mock_chat("follow"), INSTS[1], "B", 3, "m")
        for r in rounds:
            self.assertEqual(r["reply_sha256"], runner.sha(r["reply"]))

    def test_repeat_counter(self):
        calls = []

        def stuck(messages):
            calls.append(1)
            return "\n".join("x%d = 0" % i for i in range(INSTS[0].n))
        _, u = runner.run_unit(stuck, INSTS[0], "B", 4, "m")
        self.assertEqual((u["stagnant"], u["transitions"]), (3, 3))

    def test_verdict_comes_from_the_checker_not_the_reply(self):
        def liar(messages):
            return "\n".join("x%d = 0" % i for i in range(INSTS[0].n))
        _, u = runner.run_unit(liar, INSTS[0], "C", 2, "m")
        self.assertFalse(u["passed"])


class Resume(unittest.TestCase):
    def test_same_seed_other_tier_is_a_separate_unit(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.jsonl")
            chat = runner.mock_chat("follow")
            a = [rsig.make_instance(5, tier="S", **rsig.TIERS["S"])]
            b = [rsig.make_instance(5, tier="M", **rsig.TIERS["M"])]
            self.assertEqual(runner.run_experiment(chat, "m", ["C"], a, 3, p), 1)
            self.assertEqual(runner.run_experiment(chat, "m", ["C"], b, 3, p), 1)
            self.assertEqual(runner.run_experiment(chat, "m", ["C"], a, 3, p), 0)

    def test_changed_instance_under_same_key_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.jsonl")
            chat = runner.mock_chat("follow")
            inst = rsig.make_instance(5, tier="S", **rsig.TIERS["S"])
            runner.run_experiment(chat, "m", ["C"], [inst], 3, p)
            other = rsig.make_instance(5, tier="S", n=4, extra=3, den=2, span=4)
            with self.assertRaises(RuntimeError):
                runner.run_experiment(chat, "m", ["C"], [other], 3, p)

    def test_torn_line_does_not_eat_the_next_record(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.jsonl")
            with open(p, "w") as f:
                f.write('{"type": "round", "tor')
            runner.run_experiment(runner.mock_chat("follow"), "m", ["C"], INSTS[:1], 3, p)
            recs = runner.read_log(p)
            self.assertEqual(recs[0]["round"], 1)
            self.assertEqual(recs[-1]["type"], "unit")


class Analysis(unittest.TestCase):
    def by(self, spec):
        # spec: arm -> list of passed flags
        return analyze.table([unit(arm=a, inst=i, passed=p) for a, fl in spec.items() for i, p in enumerate(fl)])["m", "S"]

    def test_counts_are_paired_on_instances(self):
        by = self.by({"C": [1, 1, 1, 0, 0], "B": [1, 0, 0, 1, 0]})
        c = analyze.compare(by, "C", "B", 4)
        self.assertEqual((c["pairs"], c["first_only"], c["second_only"]), (5, 2, 1))

    def test_only_instances_present_in_both_arms_are_paired(self):
        by = self.by({"C": [1, 1, 1, 1, 1], "B": [0, 0, 1]})
        c = analyze.compare(by, "C", "B", 4)
        self.assertEqual((c["pairs"], c["first_only"], c["second_only"]), (3, 2, 0))

    def test_verdicts(self):
        n = 30
        sup = analyze.summarize([unit(arm="C", inst=i, passed=True) for i in range(n)]
                                + [unit(arm="B", inst=i, passed=i < 10) for i in range(n)], 4)["m"]
        self.assertEqual(sup["tiers"]["S"]["verdict"], "supports")
        self.assertEqual(sup["overall"], "supports")
        rev = analyze.summarize([unit(arm="C", inst=i, passed=i < 10) for i in range(n)]
                                + [unit(arm="B", inst=i, passed=True) for i in range(n)], 4)["m"]
        self.assertEqual(rev["tiers"]["S"]["verdict"], "against")
        tie = analyze.summarize([unit(arm=a, inst=i, passed=i % 2 == 0) for a in "BC" for i in range(n)], 4)["m"]
        self.assertEqual(tie["tiers"]["S"]["verdict"], "too_few_discordant_pairs")  # identical arms
        ceil = analyze.summarize([unit(arm=a, inst=i, passed=True) for a in "BC" for i in range(n)], 4)["m"]
        self.assertEqual(ceil["tiers"]["S"]["verdict"], "floor_or_ceiling")
        few = analyze.summarize([unit(arm="C", inst=i, passed=i < 20) for i in range(n)]
                                + [unit(arm="B", inst=i, passed=i < 15) for i in range(n)], 4)["m"]
        self.assertEqual(few["tiers"]["S"]["verdict"], "too_few_discordant_pairs")

    def test_models_and_tiers_are_not_pooled(self):
        us = [unit(model="m1", arm=a, inst=1, tier=t) for a in "BC" for t in "SM"] + \
             [unit(model="m2", arm="C", inst=1)]
        s = analyze.summarize(us, 4)
        self.assertEqual(sorted(s), ["m1", "m2"])
        self.assertEqual(sorted(s["m1"]["tiers"]), ["M", "S"])
        self.assertEqual(s["m1"]["tiers"]["S"]["arms"]["C"]["n"], 1)


class Cli(unittest.TestCase):
    def test_runner_then_analyze_on_two_logs(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as d:
            logs = []
            for tier, seed in (("S", 100000), ("M", 200000)):
                p = os.path.join(d, tier + ".jsonl")
                logs.append(p)
                runner.main(["--mock", "follow", "--model", "m", "--tier", tier, "--base-seed", str(seed),
                             "--count", "3", "--k", "4", "--log", p])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                analyze.main(logs + ["--k", "4"])
            out = json.loads(buf.getvalue())
            self.assertEqual(sorted(out["m"]["tiers"]), ["M", "S"])
            self.assertEqual(out["m"]["tiers"]["S"]["arms"]["C"]["n"], 3)


class Selftest(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            r = selftest.run_selftest(tmpdir=d)
        self.assertIn("ignore_mock", r)


if __name__ == "__main__":
    unittest.main()
