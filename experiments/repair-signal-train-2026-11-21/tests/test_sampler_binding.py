"""Which adapter is evaluated: an evaluation is recorded only for a sampler this
run issued after training that arm, under that arm's own training receipt."""
import hashlib
import json
import os
import unittest
from fractions import Fraction
from unittest import mock

import _setup  # noqa: F401
import cost
import driver as D
import episodes as E
import evaluate as V
import fakes
import ratchet as RT
import receipts
import tinker_backend as T

import test_driver as TD

CAP = TD.CAP


class NoHandle:
    """A sampler object with no get_sampler_handle."""


class BrokenHandle(fakes.FakeSampler):
    def get_sampler_handle(self):
        raise RuntimeError("no session")


class EmptyHandle(fakes.FakeSampler):
    def get_sampler_handle(self):
        return ""


class SharedHandle(fakes.FakeSampler):
    def __init__(self, handle):
        super().__init__()
        self.handle = handle


class BackendBindingTests(unittest.TestCase):
    def run_with(self, svc):
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "approvals.json")
        with open(path, "w") as fh:
            json.dump({"approvals": [{"run_id": "r", "ceiling_usd": "5.00", "plan": "test", "plan_id": "p"}]}, fh)
        run = T.TinkerRun("r", path, {"train": 1000, "prefill": 1000, "sample": 1000}, "test", "p", svc, fakes.FakeTypes)
        self.addCleanup(run.close)
        return run

    def trained(self, run, label, steps=1):
        run.start_arm(label)
        d = T.make_datum(fakes.FakeTypes, [1, 2, 3], [4, 5])
        for _ in range(steps):
            run.train_step(label, [d], 1e-3)

    def test_an_adapter_binding_gives_label_steps_source_and_the_hash_of_the_handle(self):
        sampler = fakes.FakeSampler()
        run = self.run_with(fakes.FakeService(checkpoint_samplers=[sampler]))
        self.trained(run, "C-s0", steps=3)
        got = run.checkpoint_sampler("C-s0")
        self.assertIs(got, sampler)
        self.assertEqual(run.binding(sampler), {
            "model": "adapter", "label": "C-s0", "steps": 3, "sampler_source": "handle",
            "sampler_id": hashlib.sha256(sampler.handle.encode()).hexdigest()})

    def test_the_base_sampler_is_untrained_and_repeating_the_call_gives_the_same_object(self):
        base = fakes.FakeSampler()
        run = self.run_with(fakes.FakeService(base=base))
        self.assertIs(run.base_sampler(), base)
        self.assertIs(run.base_sampler(), base)
        self.assertEqual(run.binding(base), {"model": "untrained"})
        self.assertEqual(len(run.issued), 1)

    def test_a_sampler_the_run_did_not_issue_is_refused(self):
        run = self.run_with(fakes.FakeService())
        with self.assertRaises(T.BackendError):
            run.binding(fakes.FakeSampler())

    def test_a_sampler_that_looks_equal_but_is_another_object_is_refused(self):
        a = SharedHandle("same")
        run = self.run_with(fakes.FakeService(checkpoint_samplers=[a]))
        self.trained(run, "C-s0")
        run.checkpoint_sampler("C-s0")
        with self.assertRaises(T.BackendError):
            run.binding(SharedHandle("same"))

    def test_a_checkpoint_that_is_a_sampler_already_issued_is_refused(self):
        same = EmptyHandle()                  # no handle: only the object tells the two apart
        run = self.run_with(fakes.FakeService(checkpoint_samplers=[same, same]))
        self.trained(run, "B-s0")
        self.trained(run, "C-s0")
        run.checkpoint_sampler("B-s0")
        with self.assertRaises(T.BackendError):
            run.checkpoint_sampler("C-s0")

    def test_two_checkpoints_with_the_same_handle_are_refused(self):
        run = self.run_with(fakes.FakeService(checkpoint_samplers=[SharedHandle("h"), SharedHandle("h")]))
        self.trained(run, "B-s0")
        self.trained(run, "C-s0")
        run.checkpoint_sampler("B-s0")
        with self.assertRaises(T.BackendError):
            run.checkpoint_sampler("C-s0")

    def test_a_base_sampler_that_is_a_checkpoint_is_refused(self):
        same = fakes.FakeSampler()
        run = self.run_with(fakes.FakeService(checkpoint_samplers=[same], base=same))
        self.trained(run, "C-s0")
        run.checkpoint_sampler("C-s0")
        with self.assertRaises(T.BackendError):
            run.base_sampler()

    def test_a_base_sampler_with_the_handle_of_a_checkpoint_is_refused(self):
        run = self.run_with(fakes.FakeService(checkpoint_samplers=[SharedHandle("h")], base=SharedHandle("h")))
        self.trained(run, "C-s0")
        run.checkpoint_sampler("C-s0")
        with self.assertRaises(T.BackendError):
            run.base_sampler()

    def test_no_handle_gives_source_object_and_an_empty_id(self):
        for sampler in (NoHandle(), BrokenHandle(), EmptyHandle()):
            self.assertEqual(T.sampler_identifier(sampler), ("object", ""), type(sampler).__name__)

    def test_a_handle_is_hashed_and_never_kept(self):
        got = T.sampler_identifier(SharedHandle("abc"))
        self.assertEqual(got, ("handle", hashlib.sha256(b"abc").hexdigest()))

    def test_a_handle_that_is_not_a_string_counts_as_none(self):
        s = fakes.FakeSampler()
        s.get_sampler_handle = lambda: 7
        self.assertEqual(T.sampler_identifier(s), ("object", ""))

    def test_steps_are_counted_after_each_completed_step(self):
        run = self.run_with(fakes.FakeService())
        self.trained(run, "C-s0", steps=2)
        self.assertEqual(run.steps, {"C-s0": 2})


class Bound(TD.Fixture):
    def setUp(self):
        super().setUp()
        enc = self.codec.target_ids
        self.samplers = [fakes.ScriptedSampler(self.fail1, enc) for _ in range(4)]
        self.base = fakes.ScriptedSampler(self.fail1, enc)
        self.svc = fakes.FakeService(checkpoint_samplers=self.samplers, base=self.base)
        self.run = self.start_run("run-b", self.approvals("run-b"), self.plan, cost.Counter(rule_only=True),
                                  self.svc, fakes.FakeTypes)
        self.rt = self.ratchet("b")
        self.rt.lock_harness()
        self.train = E.build_set("train", {"S": 32, "M": 32})
        self.ev = E.build_set("heldout1", {"M": 3})
        self.config = {"cap": CAP}

    def train_arm_(self, arm, seed):
        label = "%s-s%d" % (arm, seed)
        return D.train_and_save(self.run, self.rt, self.codec, self.train, arm, seed, label,
                                D.adapter_name(arm, seed), "run-b")[0]

    def evaluate(self, sampler, descriptor, text="C"):
        return D.evaluate_recorded(self.rt, self.run, sampler, self.codec, self.ev, text, descriptor, "run-b",
                                   self.config)

    def evals(self):
        return [b for b in receipts.bodies(self.rt.receipts_path) if b["kind"] == "eval"]

    def trains(self):
        return [b for b in receipts.bodies(self.rt.receipts_path) if b["kind"] == "train"]

    def calls(self):
        return sum(len(s.calls) for s in self.samplers) + len(self.base.calls)


class TrainingReceiptTests(Bound):
    def test_training_writes_one_receipt_with_the_checkpoints_identity(self):
        sampler = self.train_arm_("C", 0)
        (t,) = self.trains()
        self.assertEqual((t["label"], t["arm"], t["seed"], t["descriptor"], t["steps"], t["run_id"]),
                         ("C-s0", "C", 0, "adapter:C:seed0", 2, "run-b"))
        self.assertEqual((t["sampler_source"], t["sampler_id"]),
                         ("handle", hashlib.sha256(sampler.handle.encode()).hexdigest()))

    def test_a_second_receipt_for_the_same_label_or_descriptor_is_refused(self):
        self.train_arm_("C", 0)
        info = {"label": "C-s0", "arm": "C", "seed": 0, "descriptor": "other", "steps": 2,
                "sampler_source": "object", "sampler_id": ""}
        with self.assertRaises(RT.RatchetRefused):
            self.rt.record_training("run-b", info)
        info.update(label="other", descriptor="adapter:C:seed0")
        with self.assertRaises(RT.RatchetRefused):
            self.rt.record_training("run-b", info)

    def test_a_malformed_receipt_is_refused(self):
        good = {"label": "C-s0", "arm": "C", "seed": 0, "descriptor": "d", "steps": 2,
                "sampler_source": "handle", "sampler_id": "ab"}
        bad = [dict(good, sampler_source="path", sampler_id=""),          # unknown source, consistent with its id
               dict(good, steps=0), dict(good, steps=True), dict(good, seed="0"), dict(good, label=""),
               dict(good, descriptor=""), dict(good, sampler_source="path"),
               dict(good, sampler_source="object"),            # an id goes with the source handle only
               dict(good, sampler_id=""), {k: v for k, v in good.items() if k != "arm"}, dict(good, extra="x"),
               "not a dict"]
        for info in bad:
            with self.assertRaises(RT.RatchetRefused, msg=repr(info)):
                self.rt.record_training("run-b", info)
        self.assertEqual(self.trains(), [])

    def test_the_loop_and_the_run_must_agree_on_the_step_count(self):
        real = D.train_arm

        def lying(*a, **kw):
            return real(*a, **kw) + 3
        with mock.patch.object(D, "train_arm", lying):
            with self.assertRaises(D.DriverError):
                D.train_and_save(self.run, self.rt, self.codec, self.train, "C", 0, "C-s0", "adapter:C:seed0", "run-b")
        self.assertEqual(self.trains(), [])

    def test_no_training_receipt_is_written_when_training_did_not_finish(self):
        run_ = self.run
        original = run_.train_step
        calls = []

        def boom(label, datums, lr):
            calls.append(1)
            if len(calls) == 2:
                raise T.BackendError("stop")
            return original(label, datums, lr)
        run_.train_step = boom
        with self.assertRaises(T.BackendError):
            self.train_arm_("C", 0)
        self.assertEqual(self.trains(), [])


class EvaluationBindingTests(Bound):
    def test_an_adapter_evaluation_names_its_adapter_and_the_training_receipt(self):
        sampler = self.train_arm_("C", 0)
        self.evaluate(sampler, "adapter:C:seed0")
        (e,) = self.evals()
        (t,) = self.trains()
        self.assertEqual(e["model"], "adapter")
        self.assertEqual((e["adapter_label"], e["adapter_steps"]), ("C-s0", 2))
        self.assertEqual((e["sampler_source"], e["sampler_id"]), (t["sampler_source"], t["sampler_id"]))
        self.assertEqual(e["train_receipt_sha256"], V.canonical_sha256(t))

    def test_the_untrained_model_is_marked_untrained(self):
        self.evaluate(self.run.base_sampler(), "base-model")
        (e,) = self.evals()
        self.assertEqual(e["model"], "untrained")
        self.assertNotIn("train_receipt_sha256", e)

    def test_a_sampler_of_another_arm_is_refused_before_any_call(self):
        self.train_arm_("B", 0)
        c = self.train_arm_("C", 0)
        before = self.calls()
        b_sampler = self.run.issued[0]["sampler"]
        self.assertIsNot(b_sampler, c)
        with self.assertRaises(RT.RatchetRefused):
            self.evaluate(b_sampler, "adapter:C:seed0")
        self.assertEqual(self.calls(), before)
        self.assertEqual(self.evals(), [])

    def test_a_sampler_of_another_seed_is_refused_before_any_call(self):
        s0 = self.train_arm_("C", 0)
        s1 = self.train_arm_("C", 1)
        before = self.calls()
        for sampler, name in ((s0, "adapter:C:seed1"), (s1, "adapter:C:seed0")):
            with self.assertRaises(RT.RatchetRefused):
                self.evaluate(sampler, name)
        self.assertEqual(self.calls(), before)
        self.assertEqual(self.evals(), [])

    def test_a_sampler_with_no_training_receipt_is_refused(self):
        self.run.start_arm("C-s0")
        d = T.make_datum(fakes.FakeTypes, [1, 2, 3], [4, 5])
        self.run.train_step("C-s0", [d], 1e-3)
        sampler = self.run.checkpoint_sampler("C-s0")           # saved, never recorded by the driver
        before = self.calls()
        with self.assertRaises(RT.RatchetRefused):
            self.evaluate(sampler, "adapter:C:seed0")
        self.assertEqual(self.calls(), before)
        self.assertEqual(self.evals(), [])

    def test_a_sampler_the_run_did_not_issue_is_refused(self):
        self.train_arm_("C", 0)
        stranger = fakes.ScriptedSampler(self.fail1, self.codec.target_ids)
        with self.assertRaises(T.BackendError):
            self.evaluate(stranger, "adapter:C:seed0")
        self.assertEqual(stranger.calls, [])

    def test_the_base_sampler_cannot_stand_for_an_adapter(self):
        self.train_arm_("C", 0)
        base = self.run.base_sampler()
        before = self.calls()
        with self.assertRaises(RT.RatchetRefused):
            self.evaluate(base, "adapter:C:seed0")
        self.assertEqual(self.calls(), before)

    def test_an_adapter_cannot_be_recorded_as_the_untrained_model(self):
        # the run knows the sampler is an adapter, so a binding saying untrained cannot come from it,
        # and a hand-made one is refused by the descriptor
        self.train_arm_("C", 0)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.require_model({"model": "untrained"}, "adapter:C:seed0")
        with self.assertRaises(RT.RatchetRefused):
            self.rt.require_model({"model": "untrained", "label": "C-s0"}, "base-model")
        self.assertEqual(self.rt.require_model({"model": "untrained"}, "base-model"), {"model": "untrained"})

    def test_a_binding_that_differs_from_the_receipt_in_any_field_is_refused(self):
        sampler = self.train_arm_("C", 0)
        good = self.run.binding(sampler)
        self.assertEqual(self.rt.require_model(good, "adapter:C:seed0")["adapter_label"], "C-s0")
        for key, value in (("label", "B-s0"), ("steps", 1), ("sampler_id", "0" * 64), ("sampler_source", "object")):
            with self.assertRaises(RT.RatchetRefused, msg=key):
                self.rt.require_model(dict(good, **{key: value}), "adapter:C:seed0")
        with self.assertRaises(RT.RatchetRefused):
            self.rt.require_model({k: v for k, v in good.items() if k != "steps"}, "adapter:C:seed0")
        with self.assertRaises(RT.RatchetRefused):
            self.rt.require_model(dict(good, extra="x"), "adapter:C:seed0")
        with self.assertRaises(RT.RatchetRefused):
            self.rt.require_model(dict(good, model="other"), "adapter:C:seed0")
        with self.assertRaises(RT.RatchetRefused):
            self.rt.require_model("adapter", "adapter:C:seed0")

    def test_an_unknown_descriptor_is_refused_for_an_adapter(self):
        sampler = self.train_arm_("C", 0)
        with self.assertRaises(RT.RatchetRefused):
            self.rt.require_model(self.run.binding(sampler), "adapter:C:seed9")

    def test_the_recording_itself_refuses_a_wrong_model_even_after_the_calls(self):
        # the ratchet's record is the second line of defence, without the driver's pre-check
        b = self.train_arm_("B", 0)
        self.train_arm_("C", 0)
        from evaluate import evaluate_arm
        result = evaluate_arm(D.responder(self.run, b, self.codec, CAP), self.ev, "C", CAP, "adapter:C:seed0")
        with self.assertRaises(RT.RatchetRefused):
            self.rt.record(result, "run-b", self.config, self.run.binding(b))
        self.assertEqual(self.evals(), [])

    def test_a_policy_evaluation_is_refused_once_the_chain_holds_a_training_receipt(self):
        result = V.evaluate_arm(lambda view: "x0 = 0", self.ev, "C", CAP, "policy:x")
        self.rt.record(result, "run-b", self.config)                    # before any training: a stand-in policy
        self.assertEqual(self.evals()[0]["model"], "policy")
        self.train_arm_("C", 0)
        again = V.evaluate_arm(lambda view: "x0 = 1", self.ev, "C", CAP, "policy:y")
        with self.assertRaises(RT.RatchetRefused):
            self.rt.record(again, "run-b", self.config)
        self.assertEqual(len(self.evals()), 1)

    def test_a_chain_without_training_still_records_policies_as_policies(self):
        self.assertEqual(self.rt.require_model(None, "policy:x"), {"model": "policy"})

    def test_control_texts_on_the_c_adapter_are_bound_to_the_same_adapter(self):
        sampler = self.train_arm_("C", 0)
        for text in ("B", "E", "N"):
            self.evaluate(sampler, "adapter:C:seed0", text)
        self.assertEqual(len({e["train_receipt_sha256"] for e in self.evals()}), 1)


class SecondSetBindingTests(Bound):
    def setUp(self):
        super().setUp()
        self.c = self.train_arm_("C", 0)
        self.b = self.train_arm_("B", 0)
        self.h2s = E.build_set("heldout2", {"M": 2})

    def entries(self, c_sampler, b_sampler):
        rsp = lambda s: D.responder(self.run, s, self.codec, CAP)
        return [("C", rsp(c_sampler), "C", "adapter:C:seed0"), ("B", rsp(b_sampler), "B", "adapter:B:seed0")]

    def models(self, c_sampler, b_sampler):
        return {"C": self.run.binding(c_sampler), "B": self.run.binding(b_sampler)}

    def test_a_wrong_sampler_is_refused_before_the_latch_is_touched(self):
        before = self.calls()
        with self.assertRaises(RT.RatchetRefused):
            self.rt.second_set_results("dec-driver", self.h2s, self.entries(self.b, self.b),
                                       self.config, self.models(self.b, self.b))
        self.assertEqual(self.rt.latch.touched(), [])
        self.assertEqual(self.calls(), before)

    def test_no_models_at_all_is_refused_before_the_latch_is_touched(self):
        with self.assertRaises(RT.RatchetRefused):
            self.rt.second_set_results("dec-driver", self.h2s, self.entries(self.c, self.b), self.config)
        self.assertEqual(self.rt.latch.touched(), [])

    def test_the_right_samplers_are_recorded_with_their_models(self):
        got = self.rt.second_set_results("dec-driver", self.h2s, self.entries(self.c, self.b), self.config,
                                         self.models(self.c, self.b))
        self.assertEqual(sorted(got), ["B", "C"])
        e = [b for b in self.evals() if b["set_kind"] == "heldout2"]
        self.assertEqual(sorted(x["adapter_label"] for x in e), ["B-s0", "C-s0"])


class RegisteredAndPilotRunTests(TD.Fixture):
    def setUp(self):
        super().setUp()
        patch = mock.patch.object(D, "GATES", D.Gates(0, Fraction(-1), Fraction(2)))
        patch.start()
        self.addCleanup(patch.stop)

    def test_every_evaluation_of_a_registered_run_is_bound_to_one_training_receipt(self):
        svc, _samplers = self.service(self.win1 + self.fail1 * 3 + self.win2 + self.fail2 * 2)
        summary, run, rt = self.run_registered(svc)
        self.assertTrue(summary["support"])                        # set 2 was reached: the models were named there
        self.assertEqual(rt.latch.touched(), [TD.DECISION])
        bodies = receipts.bodies(rt.receipts_path)
        trains = [b for b in bodies if b["kind"] == "train"]
        evals = [b for b in bodies if b["kind"] == "eval"]
        self.assertEqual(sorted(t["label"] for t in trains), ["A-s0", "A-s1", "B-s0", "B-s1", "C-s0", "C-s1"])
        self.assertEqual(len({t["sampler_id"] for t in trains}), 6)
        by_hash = {V.canonical_sha256(t): t for t in trains}
        for e in evals:
            if e["model"] == "untrained":
                self.assertEqual(e["descriptor"], "base-model")
            else:
                self.assertEqual(e["model"], "adapter")
                self.assertEqual(by_hash[e["train_receipt_sha256"]]["descriptor"], e["descriptor"])
        self.assertEqual(sum(1 for e in evals if e["model"] == "untrained"), 5)
        self.assertEqual(sum(1 for e in evals if e["model"] == "adapter"), 16)

    def test_the_pilot_checks_its_model_before_it_samples(self):
        plan = cost.pilot_plan(CAP)
        ev = E.build_set("train", plan.eval1_counts, plan.eval1_offset)
        fails = [E.render(ep, "A").attempt_text for ep in ev.episodes]
        base = fakes.ScriptedSampler(fails, self.codec.target_ids)
        svc = fakes.FakeService(checkpoint_samplers=[fakes.ScriptedSampler(fails, self.codec.target_ids)], base=base)
        run = self.start_run("pilot-c", self.approvals("pilot-c", plan=plan), plan, cost.Counter(rule_only=True), svc,
                             fakes.FakeTypes)
        rt = self.ratchet("pilot-c")
        with mock.patch.object(rt, "require_model", side_effect=RT.RatchetRefused("refused")):
            with self.assertRaises(RT.RatchetRefused):
                D.run_pilot(run, rt, self.codec, "pilot-c", plan, {"cap": CAP}, cost.full_plan(2048, 2, CAP))
        self.assertEqual(base.calls, [])

    def test_the_pilot_binds_its_adapter_evaluation(self):
        plan = cost.pilot_plan(CAP)
        big = cost.full_plan(2048, 2, CAP)
        ev = E.build_set("train", plan.eval1_counts, plan.eval1_offset)
        fails = [E.render(ep, "A").attempt_text for ep in ev.episodes]
        enc = self.codec.target_ids
        sampler = fakes.ScriptedSampler(fails, enc)
        svc = fakes.FakeService(checkpoint_samplers=[sampler], base=fakes.ScriptedSampler(fails, enc))
        counter = cost.Counter(rule_only=True)
        approvals = self.approvals("pilot-b", plan=plan)
        run = self.start_run("pilot-b", approvals, plan, counter, svc, fakes.FakeTypes)
        rt = self.ratchet("pilot")
        out = D.run_pilot(run, rt, self.codec, "pilot-b", plan, {"cap": CAP}, big)
        self.assertEqual(sorted(out["results"]), ["adapter", "base"])
        bodies = receipts.bodies(rt.receipts_path)
        self.assertEqual([b["kind"] for b in bodies], ["eval", "train", "eval", "pilot"])
        self.assertEqual(bodies[0]["model"], "untrained")
        self.assertEqual(bodies[1]["descriptor"], "pilot:adapter:C")
        self.assertEqual(bodies[2]["model"], "adapter")
        self.assertEqual(bodies[2]["train_receipt_sha256"], V.canonical_sha256(bodies[1]))


if __name__ == "__main__":
    unittest.main()
