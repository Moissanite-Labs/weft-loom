import json
import os
import tempfile
import unittest
from fractions import Fraction
from unittest import mock

import _setup  # noqa: F401
import episodes as E
import evaluate as V
import latch
import ratchet as RT
import receipts
import reference_policies as RP

CAP = 96
DEFAULT_DECISIONS = V.DECISIONS_PATH
IDS = ["dec", "dec-1", "dec-2", "dec-9", "arm-dec", "d", "two"]


class SignTestTests(unittest.TestCase):
    def test_exact_p_values(self):
        self.assertEqual(RT.sign_test_p(7, 0), Fraction(1, 128))
        self.assertEqual(RT.sign_test_p(0, 0), Fraction(1))
        self.assertEqual(RT.sign_test_p(5, 5), Fraction(638, 1024))
        self.assertEqual(RT.sign_test_p(0, 4), Fraction(1))
        self.assertEqual(RT.sign_test_p(3, 1), Fraction(5, 16))

    def test_discordant(self):
        self.assertEqual(RT.discordant("PFXP", "PPFF"), (1, 1))
        with self.assertRaises(RT.RatchetRefused):
            RT.discordant("PP", "P")

    def test_paired_counts_by_test(self):
        first, second = "PPFXPFXP", "PFPPXFFX"
        self.assertEqual(RT.paired_counts(first, second, "pass"), (3, 2))
        # stratum: drop every position where either broke the format
        self.assertEqual(RT.paired_counts(first, second, "stratum"), (1, 1))
        self.assertEqual(RT.paired_counts("PPPF", "PFFF", "stratum"), (2, 0))
        # format: "first only" is an episode where first stayed in format and second broke it
        self.assertEqual(RT.paired_counts("PFPF", "XXPF", "format"), (2, 0))
        self.assertEqual(RT.paired_counts("XXPF", "PFPF", "format"), (0, 2))
        self.assertEqual(RT.paired_counts("XPFX", "PFXX", "format"), (1, 1))
        with self.assertRaises(RT.RatchetRefused):
            RT.paired_counts("PP", "P", "pass")
        with self.assertRaises(RT.RatchetRefused):
            RT.paired_counts("PP", "PP", "nope")


class RatchetBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h1 = E.build_set("heldout1", {"S": 30, "M": 30})
        cls.h1b = E.build_set("heldout1", {"S": 31, "M": 30})
        cls.h2 = E.build_set("heldout2", {"S": 15, "M": 15})

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        registry = os.path.join(d, "decisions.json")
        with open(registry, "w") as fh:
            json.dump({"decisions": IDS}, fh)
        patch = mock.patch.object(V, "DECISIONS_PATH", registry)
        patch.start()
        self.addCleanup(patch.stop)
        self.registry = registry
        self.rt = RT.Ratchet(os.path.join(d, "r.jsonl"), os.path.join(d, "l.jsonl"), os.path.join(d, "lock.json"), CAP)
        self.rt.lock_harness()
        self.base = self.rec(V.evaluate_arm(RP.unchanged, self.h1, "C", CAP, "adapter:base"))
        self.good = self.rec(V.evaluate_arm(RP.oracle, self.h1, "C", CAP, "adapter:good"))

    def rec(self, result):
        """Records a result in the chain, as every result must be before a decision."""
        self.rt.record(result, "run", {"cap": CAP})
        return result

    def ev(self, policy, epset, arm, cap, descriptor):
        return self.rec(V.evaluate_arm(policy, epset, arm, cap, descriptor))

    def tearDown(self):
        self.tmp.cleanup()

    def new_ratchet(self, name):
        d = self.tmp.name
        return RT.Ratchet(os.path.join(d, name + "-r.jsonl"), os.path.join(d, name + "-l.jsonl"),
                          os.path.join(d, name + "-lock.json"), CAP)


class RatchetTests(RatchetBase):
    def test_accepts_a_clear_improvement(self):
        d = self.rt.decide("dec", self.base, self.good)
        self.assertTrue(d["accepted"])
        self.assertLessEqual(d["p"], self.rt.alpha)
        last = receipts.bodies(self.rt.receipts_path)[-1]
        self.assertEqual((last["kind"], last["accepted"]), ("decision", 1))
        self.assertEqual(Fraction(last["p_num"], last["p_den"]), d["p"])

    def test_rejects_a_candidate_that_is_not_better(self):
        d = self.rt.decide("dec", self.good, self.base)
        self.assertFalse(d["accepted"])

    def test_rejects_a_gain_that_is_not_significant(self):
        weak = self.ev(lambda v: RP.recompute(v) if v.instance.seed % 29 == 0 else v.attempt_text,
                       self.h1, "C", CAP, "adapter:weak")
        d = self.rt.decide("dec", self.base, weak)
        self.assertGreater(weak.passed, self.base.passed)
        self.assertFalse(d["accepted"])

    def test_gate_identical_descriptor(self):
        again = self.ev(RP.oracle, self.h1, "C", CAP, "adapter:base")
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.decide("dec", self.base, again)
        self.assertIn("identical", str(cm.exception))

    def test_gate_identical_replies(self):
        same = self.ev(RP.unchanged, self.h1, "C", CAP, "adapter:renamed")
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.decide("dec", self.base, same)
        self.assertIn("identical", str(cm.exception))

    def test_gate_same_cap(self):
        other = self.ev(RP.oracle, self.h1, "C", CAP - 1, "adapter:other-cap")
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.decide("dec", self.base, other)
        self.assertIn("cap", str(cm.exception))
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", other, self.good)

    def test_gate_same_episodes_and_arm(self):
        same_size_other_episodes = E.build_set("heldout1", {"S": 60})
        self.assertEqual(len(same_size_other_episodes), len(self.h1))
        other_set = self.ev(RP.recompute, same_size_other_episodes, "C", CAP, "adapter:x")
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.decide("dec", self.base, other_set)
        self.assertIn("same episodes", str(cm.exception))
        other_arm = self.ev(RP.recompute, self.h1, "B", CAP, "adapter:y")
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.decide("dec", self.base, other_arm)
        self.assertIn("different arms", str(cm.exception))

    def other_harness_result(self, policy, descriptor):
        """A recorded result from a different harness, by changing the harness
        and its lock together. Returns (result, patch): decisions must be made
        inside the patch, where the changed harness is the current one."""
        h2 = dict(V.harness_hashes(), evaluate_py="2" * 64)
        patch = mock.patch.object(V, "harness_hashes", lambda: h2)
        with open(self.rt.lock_path, "w") as fh:
            json.dump(h2, fh)
        with patch:
            result = self.ev(policy, self.h1, "C", CAP, descriptor)
        return result, patch

    def test_gate_same_harness_for_both_results(self):
        other, patch = self.other_harness_result(RP.oracle, "adapter:z")
        self.assertNotEqual(other.harness, self.base.harness)
        with patch:
            with self.assertRaises(RT.RatchetRefused) as cm:
                self.rt.decide("dec", self.base, other)
            self.assertIn("harness", str(cm.exception))

    def test_gate_harness_lock_missing_or_changed(self):
        os.remove(self.rt.lock_path)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", self.base, self.good)
        with open(self.rt.lock_path, "w") as fh:
            json.dump({"evaluate_py": "0" * 64}, fh)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", self.base, self.good)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.record(self.base, "run", {})
        with self.assertRaises(RT.RatchetRefused):
            self.rt.lock_harness()

    def test_result_from_another_harness_is_refused_at_record(self):
        forged = V.evaluate_arm(RP.unchanged, self.h1, "C", CAP, "adapter:forged")
        forged.harness = dict(forged.harness, evaluate_py="1" * 64)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.record(forged, "run", {})

    def test_gate_chain_is_verified_before_a_decision(self):
        self.rt.record(self.base, "run", {"a": 1})
        with open(self.rt.receipts_path, "r") as fh:
            text = fh.read()
        with open(self.rt.receipts_path, "w") as fh:
            fh.write(text.replace('"passed":0', '"passed":1', 1))
        with self.assertRaises(receipts.ReceiptError):
            self.rt.decide("dec", self.base, self.good)

    def test_record_stores_config_hash_and_no_floats(self):
        self.rt.record(self.base, "run-1", {"cap": CAP})
        body = receipts.bodies(self.rt.receipts_path)[-1]
        self.assertEqual(body["config_sha256"], V.canonical_sha256({"cap": CAP}))
        self.assertEqual(body["run_id"], "run-1")
        self.assertEqual(body["harness"], self.base.harness)

    def test_compare_arms_across_arms(self):
        c = self.ev(RP.oracle, self.h1, "C", CAP, "adapter:c")
        b = self.ev(RP.oracle, self.h1, "B", CAP, "adapter:b")
        d = self.rt.compare_arms("cmp", c, b)
        self.assertTrue(d["first_better"])
        self.assertEqual(d["second_only"], 0)
        back = self.rt.compare_arms("cmp", b, c)
        self.assertFalse(back["first_better"])
        body = receipts.bodies(self.rt.receipts_path)[-1]
        self.assertEqual((body["kind"], body["first_arm"], body["second_arm"]), ("arm_comparison", "B", "C"))

    def test_compare_arms_ties_are_not_refused(self):
        a = self.ev(RP.recompute, self.h1, "A", CAP, "adapter:a")
        b = self.ev(RP.recompute, self.h1, "B", CAP, "adapter:b")
        d = self.rt.compare_arms("tie", a, b)
        self.assertEqual((d["first_only"], d["second_only"], d["first_better"]), (0, 0, False))

    def test_compare_arms_gates(self):
        c = self.ev(RP.oracle, self.h1, "C", CAP, "adapter:c")
        low = self.ev(RP.oracle, self.h1, "B", CAP - 1, "adapter:low")
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.compare_arms("g", c, low)
        self.assertIn("cap", str(cm.exception))
        other = self.ev(RP.oracle, E.build_set("heldout1", {"S": 60}), "B", CAP, "adapter:o")
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.compare_arms("g", c, other)
        self.assertIn("same episodes", str(cm.exception))
        b, patch = self.other_harness_result(RP.oracle, "adapter:b3")
        with patch:
            with self.assertRaises(RT.RatchetRefused) as cm:
                self.rt.compare_arms("g", c, b)
            self.assertIn("harness", str(cm.exception))
        os.remove(self.rt.lock_path)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.compare_arms("g", c, c)

    def test_arm_comparison_on_the_second_set_is_touched_once(self):
        args = ("arm-dec", self.h2, RP.oracle, "C", "adapter:c", RP.oracle, "B", "adapter:b", {"cap": CAP})
        self.assertTrue(self.rt.confirm_arms_second_set(*args)["first_better"])
        with self.assertRaises(latch.LatchRefused):
            self.rt.confirm_arms_second_set(*args)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.confirm_arms_second_set("x", self.h1, *args[2:])

    def test_second_set_is_touched_once_per_decision(self):
        args = ("dec-1", self.h2, RP.unchanged, RP.oracle, "C", "adapter:base", "adapter:good", {"cap": CAP})
        d = self.rt.confirm_second_set(*args)
        self.assertTrue(d["accepted"])
        with self.assertRaises(latch.LatchRefused):
            self.rt.confirm_second_set(*args)
        self.assertEqual(self.rt.latch.touched(), ["dec-1"])
        # a different registered decision has its own touch
        args2 = ("dec-2",) + args[1:]
        self.assertTrue(self.rt.confirm_second_set(*args2)["accepted"])

    def test_latch_touch_survives_a_crash_in_evaluation(self):
        def boom(view):
            raise RuntimeError("crash")
        with self.assertRaises(RuntimeError):
            self.rt.confirm_second_set("dec-9", self.h2, boom, RP.oracle, "C", "a", "b", {})
        with self.assertRaises(latch.LatchRefused):
            self.rt.confirm_second_set("dec-9", self.h2, RP.unchanged, RP.oracle, "C", "a", "b", {})

    def test_confirm_refuses_the_wrong_set_and_a_blank_id(self):
        with self.assertRaises(RT.RatchetRefused):
            self.rt.confirm_second_set("d", self.h1, RP.unchanged, RP.oracle, "C", "a", "b", {})
        with self.assertRaises(latch.LatchRefused):
            self.rt.confirm_second_set("", self.h2, RP.unchanged, RP.oracle, "C", "a", "b", {})

    def test_latch_file_is_append_only_lines(self):
        t = self.rt.latch.touch("dec-1", [("C", "a")])
        self.assertTrue(latch.token_is_valid(t))
        self.rt.latch.touch("dec-2", [("C", "a"), ("B", "b")])
        with open(self.rt.latch.path) as fh:
            rows = [json.loads(x) for x in fh]
        self.assertEqual([r["decision_id"] for r in rows], ["dec-1", "dec-2"])
        self.assertEqual(rows[1]["uses"], [["C", "a"], ["B", "b"]])

    def test_an_unregistered_decision_id_cannot_buy_a_look(self):
        for bad in ("d2", "dec ", "DEC", "dec-1 ", "other"):
            with self.assertRaises(latch.LatchRefused, msg=bad):
                self.rt.latch.touch(bad, [("C", "a")])
        self.assertEqual(self.rt.latch.touched(), [])
        self.rt.latch.touch("dec-1", [("C", "a")])
        with self.assertRaises(latch.LatchRefused):
            self.rt.latch.touch("dec-1 ", [("C", "a")])
        with self.assertRaises(latch.LatchRefused):
            self.rt.confirm_second_set("not-registered", self.h2, RP.unchanged, RP.oracle, "C", "a", "b", {})

    def test_the_default_registry_is_the_hashed_decisions_file(self):
        with mock.patch.object(V, "DECISIONS_PATH", DEFAULT_DECISIONS):
            rt = self.new_ratchet("r2")
            self.assertEqual(rt.latch.registered, frozenset({"primary-c-vs-b-seed0-confirm"}))
            self.assertIn("decisions_json", V.harness_hashes())

    def test_touch_needs_distinct_pairs_of_strings(self):
        for uses in ([], [("C", "a"), ("C", "a")], [("C",)], [("C", "")], [("C", 5)], [("", "a")]):
            with self.assertRaises(latch.LatchRefused, msg=str(uses)):
                self.rt.latch.touch("dec-1", uses)
        self.assertEqual(self.rt.latch.touched(), [])

    def test_a_token_is_single_use_and_bound_to_arm_and_descriptor(self):
        token = self.rt.latch.touch("dec-1", [("C", "a"), ("B", "b")])
        with self.assertRaises(V.EvalRefused):
            V.evaluate_arm(RP.unchanged, self.h2, "C", CAP, "other", token)      # another descriptor
        with self.assertRaises(V.EvalRefused):
            V.evaluate_arm(RP.unchanged, self.h2, "A", CAP, "a", token)          # another arm
        self.assertEqual(token.remaining, {("C", "a"), ("B", "b")})
        V.evaluate_arm(RP.unchanged, self.h2, "C", CAP, "a", token)
        with self.assertRaises(V.EvalRefused):
            V.evaluate_arm(RP.unchanged, self.h2, "C", CAP, "a", token)          # the same pair twice
        V.evaluate_arm(RP.unchanged, self.h2, "B", CAP, "b", token)
        self.assertEqual(token.remaining, set())

    def test_spend_refuses_a_forged_token(self):
        with self.assertRaises(latch.LatchRefused):
            latch.spend(latch.LatchToken("dec-1", [("C", "a")]), "C", "a", frozenset(IDS))

    def test_registry_file_is_read_strictly(self):
        p = os.path.join(self.tmp.name, "reg.json")
        for raw in ("not json", "[]", "{}", '{"decisions": []}', '{"decisions": "x"}', '{"decisions": [1]}',
                    '{"decisions": [""]}', '{"decisions": ["a", "a"]}'):
            with open(p, "w") as fh:
                fh.write(raw)
            with self.assertRaises(latch.LatchRefused, msg=raw):
                latch.load_registry(p)
        with self.assertRaises(latch.LatchRefused):
            latch.load_registry(os.path.join(self.tmp.name, "missing.json"))
        with open(p, "w") as fh:
            fh.write('{"decisions": ["a", "b"]}')
        self.assertEqual(latch.load_registry(p), frozenset({"a", "b"}))

    def test_second_set_results_records_every_evaluation_after_one_touch(self):
        got = self.rt.second_set_results("dec-1", self.h2, [
            ("x", RP.unchanged, "C", "m:x"), ("y", RP.oracle, "C", "m:y"), ("z", RP.oracle, "E", "m:y")], {"cap": CAP})
        self.assertEqual(set(got), {"x", "y", "z"})
        self.assertEqual(self.rt.latch.touched(), ["dec-1"])
        kinds = [b for b in receipts.bodies(self.rt.receipts_path) if b.get("set_kind") == "heldout2"]
        self.assertEqual(len(kinds), 3)
        with self.assertRaises(latch.LatchRefused):
            self.rt.second_set_results("dec-1", self.h2, [("x", RP.unchanged, "C", "m:x")], {})
        with self.assertRaises(RT.RatchetRefused):
            self.rt.second_set_results("dec-2", self.h1, [("x", RP.unchanged, "C", "m:x")], {})

    def test_the_stratum_and_format_comparisons_are_recorded_with_their_test(self):
        c = self.ev(RP.oracle, self.h1, "C", CAP, "adapter:c")
        v = self.ev(RP.verbose, self.h1, "B", CAP, "adapter:v")
        d = self.rt.compare_arms("fmt", c, v, "format")
        self.assertTrue(d["first_better"])                    # c stays in format where v always breaks it
        self.assertEqual(receipts.bodies(self.rt.receipts_path)[-1]["test"], "format")
        d = self.rt.compare_arms("fmt", v, c, "format")
        self.assertFalse(d["first_better"])
        d = self.rt.compare_arms("str", c, v, "stratum")      # v broke the format everywhere: no episode in the stratum
        self.assertEqual((d["first_only"], d["second_only"], d["first_better"]), (0, 0, False))
        self.assertEqual(receipts.bodies(self.rt.receipts_path)[-1]["test"], "stratum")
        self.assertEqual(receipts.bodies(self.rt.receipts_path)[-1]["second_descriptor"], "adapter:v")
        with self.assertRaises(RT.RatchetRefused):
            self.rt.compare_arms("x", c, v, "nope")

    def test_a_result_that_was_never_recorded_is_refused(self):
        stranger = V.evaluate_arm(RP.recompute, self.h1, "C", CAP, "adapter:stranger")
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.decide("dec", self.base, stranger)
        self.assertIn("receipt chain", str(cm.exception))
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", stranger, self.good)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.compare_arms("dec", stranger, self.good)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.compare_arms("dec", self.good, stranger)

    def test_edited_counts_are_caught_by_the_recount(self):
        cand = V.evaluate_arm(RP.recompute, self.h1, "C", CAP, "adapter:edit")
        self.rec(cand)
        cand.passed = 999
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.decide("dec", self.base, cand)
        self.assertIn("counts", str(cm.exception))
        cand.passed = cand.outcomes.count("P")
        cand.failed += 1
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", self.base, cand)
        cand.failed -= 1
        cand.format_broken += 1
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", self.base, cand)
        cand.format_broken -= 1
        cand.n += 1
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", self.base, cand)
        cand.n -= 1
        self.assertTrue(self.rt.decide("dec", self.base, cand)["accepted"])

    def test_an_outcome_string_with_other_letters_is_refused(self):
        cand = V.evaluate_arm(RP.recompute, self.h1, "C", CAP, "adapter:letters")
        self.rec(cand)
        cand.outcomes = "Q" * cand.n
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", self.base, cand)
        cand.outcomes = ""
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", self.base, cand)
        cand.outcomes = None
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", self.base, cand)

    def test_a_result_with_changed_replies_does_not_match_its_receipt(self):
        cand = V.evaluate_arm(RP.recompute, self.h1, "C", CAP, "adapter:swap")
        self.rec(cand)
        cand.replies_sha256 = "f" * 64
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", self.base, cand)


class ReplyAndChainTests(RatchetBase):
    """The raw replies are kept and rescored, a touch is a receipt in the chain, and the chain head is pinned."""

    def test_the_result_keeps_its_replies_episode_ids_and_cut_flags(self):
        r = self.base
        self.assertEqual(len(r.texts), r.n)
        self.assertEqual(r.episode_ids, [ep.id for ep in self.h1.episodes])
        self.assertEqual(r.cuts, "0" * r.n)
        self.assertEqual(V.canonical_sha256(r.texts), r.replies_sha256)

    def stored(self):
        with open(self.rt.replies_path) as fh:
            return [json.loads(x) for x in fh]

    def test_record_stores_the_raw_replies_once_and_names_them_in_the_receipt(self):
        rows = self.stored()
        self.assertEqual(len(rows), 2)                       # base and good
        n = len(rows)
        self.rt.record(self.base, "run", {"cap": CAP})       # the same replies again: stored once
        self.assertEqual(len(self.stored()), n)
        body = [b for b in receipts.bodies(self.rt.receipts_path) if b.get("kind") == "eval"][0]
        self.assertEqual(body["replies_entry_sha256"], rows[0]["sha256"])
        self.assertEqual(V.canonical_sha256(rows[0]["entry"]), rows[0]["sha256"])
        self.assertEqual(rows[0]["entry"]["texts"], self.base.texts)

    def test_edited_counts_are_refused_at_record(self):
        r = V.evaluate_arm(RP.oracle, self.h1, "C", CAP, "adapter:counts")
        r.passed += 1
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.record(r, "run", {})
        self.assertIn("counts", str(cm.exception))

    def test_a_measurement_after_a_rewritten_last_receipt_is_refused(self):
        self.rt.measure({"kind": "pilot", "x": 1})
        self.rewrite_last_line_of("kind", "pilot")
        with self.assertRaises(receipts.ReceiptError):
            self.rt.measure({"kind": "pilot", "x": 2})

    def rewrite_last_line_of(self, key, value):
        with open(self.rt.receipts_path, "rb") as fh:
            lines = fh.read().split(b"\n")[:-1]
        rec = json.loads(lines[-1])
        rec["body"][key] = value + "-x"
        rec["self"] = receipts._self_hash(rec["seq"], rec["prev"], rec["body"])
        lines[-1] = receipts._canon(rec).encode()
        with open(self.rt.receipts_path, "wb") as fh:
            fh.write(b"\n".join(lines) + b"\n")

    def test_a_result_no_evaluation_produced_is_refused_at_record(self):
        fake = V.evaluate_arm(RP.unchanged, self.h1, "C", CAP, "adapter:invented")
        fake.outcomes = "P" * fake.n
        fake.passed, fake.failed = fake.n, 0
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.record(fake, "run", {})
        self.assertIn("rescored", str(cm.exception))

    def test_replies_that_do_not_hash_to_the_result_are_refused_at_record(self):
        r = V.evaluate_arm(RP.oracle, self.h1, "C", CAP, "adapter:swapped")
        r.replies_sha256 = "e" * 64
        with self.assertRaises(RT.RatchetRefused):
            self.rt.record(r, "run", {})

    def test_replies_that_name_other_episodes_are_refused_at_record(self):
        r = V.evaluate_arm(RP.oracle, self.h1, "C", CAP, "adapter:ids")
        r.episode_ids = r.episode_ids[1:] + r.episode_ids[:1]
        with self.assertRaises(RT.RatchetRefused):
            self.rt.record(r, "run", {})
        r.episode_ids = ["nonsense"] * r.n
        with self.assertRaises(RT.RatchetRefused):
            self.rt.record(r, "run", {})

    def test_an_edited_replies_file_stops_a_decision(self):
        with open(self.rt.replies_path) as fh:
            text = fh.read()
        with open(self.rt.replies_path, "w") as fh:
            fh.write(text.replace("x0 = ", "x0 = 9", 1))
        with self.assertRaises(RT.RatchetRefused) as cm:
            self.rt.decide("dec", self.base, self.good)
        self.assertIn("raw replies", str(cm.exception))

    def test_a_missing_replies_file_stops_a_decision(self):
        os.remove(self.rt.replies_path)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", self.base, self.good)

    def test_a_decision_rescores_the_stored_replies(self):
        # a receipt and replies file that agree with each other but whose replies give other outcomes than the result
        liar = V.evaluate_arm(RP.unchanged, self.h1, "C", CAP, "adapter:liar")
        self.rec(liar)
        liar.outcomes = "P" * liar.n
        liar.passed, liar.failed = liar.n, 0
        # the receipt body no longer matches the lying result, so it is refused as unrecorded
        with self.assertRaises(RT.RatchetRefused):
            self.rt.decide("dec", self.base, liar)

    def test_a_cut_reply_is_scored_as_a_format_break_and_rescored_so(self):
        r = V.evaluate_arm(lambda v: (RP.recompute(v), 3, True), self.h1, "C", CAP, "adapter:cut")
        self.assertEqual(r.outcomes, "X" * r.n)
        self.assertEqual(r.cuts, "1" * r.n)
        self.rec(r)
        self.assertEqual(self.rt.compare_arms("cut", self.good, r, "format")["first_only"], r.n)

    def test_a_touch_is_a_receipt_in_the_chain(self):
        self.rt.latch.touch("dec-1", [("C", "a")])
        touches = [b for b in receipts.bodies(self.rt.receipts_path) if b.get("kind") == "touch"]
        self.assertEqual(touches, [{"kind": "touch", "decision_id": "dec-1", "uses": [["C", "a"]]}])

    def test_a_new_latch_path_does_not_buy_a_second_touch(self):
        self.rt.latch.touch("dec-1", [("C", "a")])
        again = latch.Latch(os.path.join(self.tmp.name, "other-latch.jsonl"), self.rt.receipts_path, self.registry)
        with self.assertRaises(latch.LatchRefused):
            again.touch("dec-1", [("C", "a")])
        self.assertEqual(again.touched(), ["dec-1"])

    def test_a_deleted_latch_file_does_not_buy_a_second_touch(self):
        self.rt.latch.touch("dec-1", [("C", "a")])
        os.remove(self.rt.latch.path)
        with self.assertRaises(latch.LatchRefused):
            self.rt.latch.touch("dec-1", [("C", "a")])
        self.assertEqual(self.rt.latch.touched(), ["dec-1"])

    def test_a_touch_in_the_latch_file_alone_still_counts(self):
        with open(self.rt.latch.path, "w") as fh:
            fh.write(json.dumps({"decision_id": "dec-1", "uses": [["C", "a"]]}) + "\n")
        with self.assertRaises(latch.LatchRefused):
            self.rt.latch.touch("dec-1", [("C", "a")])

    def test_a_latch_with_its_own_registry_cannot_issue_a_token_that_evaluate_accepts(self):
        own = os.path.join(self.tmp.name, "own.json")
        with open(own, "w") as fh:
            json.dump({"decisions": ["sneaky"]}, fh)
        sneaky = latch.Latch(os.path.join(self.tmp.name, "sneaky-l.jsonl"), os.path.join(self.tmp.name, "sneaky-r.jsonl"), own)
        token = sneaky.touch("sneaky", [("C", "a")])
        with self.assertRaises(V.EvalRefused) as cm:
            V.evaluate_arm(RP.unchanged, self.h2, "C", CAP, "a", token)
        self.assertIn("registry", str(cm.exception))
        self.assertEqual(token.remaining, {("C", "a")})

    def test_the_registry_is_part_of_the_locked_harness(self):
        self.assertEqual(V.harness_files()["decisions_json"], self.registry)
        with open(self.registry, "w") as fh:
            json.dump({"decisions": IDS + ["more"]}, fh)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.check_lock()

    def rewrite_last_line(self):
        with open(self.rt.receipts_path, "rb") as fh:
            lines = fh.read().split(b"\n")[:-1]
        rec = json.loads(lines[-1])
        rec["body"]["decision_id"] = "rewritten"
        rec["self"] = receipts._self_hash(rec["seq"], rec["prev"], rec["body"])
        lines[-1] = receipts._canon(rec).encode()
        with open(self.rt.receipts_path, "wb") as fh:
            fh.write(b"\n".join(lines) + b"\n")

    def test_a_rewritten_last_receipt_is_caught_by_the_head_this_ratchet_wrote(self):
        self.rt.decide("dec", self.base, self.good)
        self.rewrite_last_line()
        receipts.verify(self.rt.receipts_path)               # the file alone cannot tell
        with self.assertRaises(receipts.ReceiptError):
            self.rt._bodies()                                # reading the chain is pinned too, not only appending
        with self.assertRaises(receipts.ReceiptError):
            self.rt.decide("dec-1", self.base, self.good)
        with self.assertRaises(receipts.ReceiptError):
            self.rt.compare_arms("x", self.base, self.good)

    def test_a_rewritten_last_receipt_cannot_be_covered_by_a_touch(self):
        self.rt.decide("dec", self.base, self.good)
        self.rewrite_last_line()
        with self.assertRaises(receipts.ReceiptError):
            self.rt.second_set_results("dec-1", self.h2, [("x", RP.unchanged, "C", "m:x")], {})

    def test_a_new_process_can_be_given_the_pinned_head(self):
        head = self.rt.decide("dec", self.base, self.good)["head"]
        again = RT.Ratchet(self.rt.receipts_path, self.rt.latch.path, self.rt.lock_path, CAP, head=head)
        again.compare_arms("x", self.base, self.good)
        wrong = RT.Ratchet(self.rt.receipts_path, self.rt.latch.path, self.rt.lock_path, CAP, head="0" * 64)
        with self.assertRaises(receipts.ReceiptError):
            wrong.compare_arms("x", self.base, self.good)

    def test_compare_arms_reports_the_pass_counts_and_size(self):
        d = self.rt.compare_arms("c", self.good, self.base)
        self.assertEqual((d["first_passed"], d["second_passed"], d["n"]), (self.good.passed, self.base.passed, self.base.n))

    def test_a_measurement_is_appended_as_a_receipt(self):
        self.rt.measure({"kind": "pilot", "x": 1})
        self.assertEqual(receipts.bodies(self.rt.receipts_path)[-1], {"kind": "pilot", "x": 1})
        with self.assertRaises(receipts.ReceiptError):
            self.rt.measure({"kind": "pilot", "x": 1.5})


if __name__ == "__main__":
    unittest.main()
