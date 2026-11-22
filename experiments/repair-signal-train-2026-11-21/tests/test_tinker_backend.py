import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction

import _setup  # noqa: F401
import codec as C
import episodes as E
import evaluate as V
import fakes
import tinker_backend as T


PID = "plan-fingerprint-1"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "approvals.json")
        self.plan = {"train": 100000, "prefill": 10000, "sample": 10000}   # $0.08 + $0.0015 + $0.005

    def approve(self, run_id="run-1", ceiling="1.00", raw=None, plan="test", plan_id=PID):
        row = {"run_id": run_id, "ceiling_usd": ceiling, "plan": plan, "plan_id": plan_id}
        with open(self.path, "w") as fh:
            fh.write(raw if raw is not None else json.dumps({"approvals": [row]}))

    def run_(self, run_id="run-1", plan=None, service=None):
        run = T.TinkerRun(run_id, self.path, self.plan if plan is None else plan, "test", PID,
                          service or fakes.FakeService(), fakes.FakeTypes)
        self.addCleanup(run.close)
        return run


class ApprovalTests(Base):
    def test_unapproved_run_id_refused(self):
        self.approve("other")
        with self.assertRaises(T.ApprovalError):
            self.run_()

    def test_missing_and_broken_files_refused(self):
        with self.assertRaises(T.ApprovalError):
            self.run_()
        for raw in ("not json", "[]", "{}", '{"approvals": 3}', '{"approvals": [{"run_id": "run-1"}]}'):
            self.approve(raw=raw)
            with self.assertRaises(T.ApprovalError, msg=raw):
                self.run_()

    def test_ceiling_must_be_a_positive_exact_string(self):
        plan = '"plan": "test", "plan_id": "%s"' % PID           # everything else in the row is right
        for raw in ('{"approvals": [{"run_id": "run-1", "ceiling_usd": 1.5, %s}]}',
                    '{"approvals": [{"run_id": "run-1", "ceiling_usd": 5, %s}]}',
                    '{"approvals": [{"run_id": "run-1", "ceiling_usd": "0", %s}]}',
                    '{"approvals": [{"run_id": "run-1", "ceiling_usd": "-1", %s}]}',
                    '{"approvals": [{"run_id": "run-1", "ceiling_usd": "abc", %s}]}',
                    '{"approvals": [{"run_id": "run-1", "ceiling_usd": "1/0", %s}]}'):
            raw = raw % plan
            self.approve(raw=raw)
            with self.assertRaises(T.ApprovalError, msg=raw):
                self.run_()
        self.approve(raw='{"approvals": [{"run_id": "run-1", "ceiling_usd": "1", %s}]}' % plan)
        self.run_()

    def test_exact_run_id_match_only(self):
        self.approve("run-1")
        for rid in ("run-10", "RUN-1", "run-1 ", ""):
            with self.assertRaises(T.ApprovalError):
                self.run_(rid)
        self.assertEqual(T.load_approval(self.path, "run-1").ceiling, Fraction(1))

    def test_refused_before_any_client_is_made(self):
        self.approve("other")
        svc = fakes.FakeService()
        with self.assertRaises(T.ApprovalError):
            self.run_(service=svc)
        self.assertEqual(svc.created, [])


class BudgetTests(Base):
    def test_planned_cost_is_exact(self):
        self.assertEqual(T.planned_cost(self.plan), Fraction(100000 * 3, 4 * 10**6) + Fraction(10000 * 3, 20 * 10**6)
                         + Fraction(10000, 2 * 10**6))
        self.assertEqual(T.cost_usd("train", 1000000), Fraction(3, 4))
        self.assertEqual(T.cost_usd("sample", 1000000), Fraction(1, 2))
        self.assertEqual(T.cost_usd("prefill", 1000000), Fraction(3, 20))

    def test_budget_over_or_equal_to_ceiling_refused(self):
        cost = T.planned_cost(self.plan)
        self.approve(ceiling=str(cost))                 # equal: refused
        with self.assertRaises(T.BudgetError):
            self.run_()
        self.approve(ceiling=str(cost - Fraction(1, 10**6)))
        with self.assertRaises(T.BudgetError):
            self.run_()
        self.approve(ceiling=str(cost + Fraction(1, 10**6)))
        self.assertEqual(self.run_().budget, cost)

    def test_a_plan_must_name_all_three_kinds_with_positive_counts(self):
        self.approve(ceiling="5.00")
        good = {"train": 10, "prefill": 10, "sample": 10}
        T.require_plan(good)
        for bad in ({}, {"train": 10}, {"train": 10, "prefill": 10}, dict(good, extra=5), dict(good, sample=0),
                    dict(good, train=-4), dict(good, prefill=1.5), dict(good, sample=True), dict(good, train="9"),
                    [("train", 1)]):
            with self.assertRaises(T.BudgetError, msg=str(bad)):
                T.require_plan(bad)
            with self.assertRaises(T.BudgetError, msg=str(bad)):
                self.run_(plan=bad)

    def test_no_plan_at_all_is_refused(self):
        with self.assertRaises(T.BudgetError):
            T.require_plan(None)

    def test_an_empty_plan_no_longer_starts_a_run(self):
        self.approve(ceiling="0.01")
        with self.assertRaises(T.BudgetError):
            self.run_(plan={})

    def test_settle_refunds_or_counts_in_full(self):
        m = T.Meter(Fraction(1))
        m.reserve("sample", 100)
        m.settle("sample", 100, 30)
        self.assertEqual((m.tokens["sample"], m.spent), (30, Fraction(30, 2 * 10**6)))
        m.settle("sample", 30, 30)
        self.assertEqual((m.tokens["sample"], m.spent), (30, Fraction(30, 2 * 10**6)))

    def test_the_first_overrun_stops_the_run_after_counting_it_in_full(self):
        m = T.Meter(Fraction(1))                           # far below the ceiling
        m.reserve("sample", 30)
        with self.assertRaises(T.BudgetStop):
            m.settle("sample", 30, 500)                    # a server that ignored max_tokens
        self.assertEqual((m.tokens["sample"], m.spent), (500, Fraction(500, 2 * 10**6)))
        m = T.Meter(Fraction(1, 10**6))                   # room for under 2 sampled tokens
        m.reserve("sample", 1)
        with self.assertRaises(T.BudgetStop):
            m.settle("sample", 1, 10)
        self.assertEqual(m.tokens["sample"], 10)

    def test_bad_token_counts_refused(self):
        for bad in (-1, 1.5, True):
            with self.assertRaises(T.BudgetError):
                T.cost_usd("train", bad)
        with self.assertRaises(T.BudgetError):
            T.cost_usd("rent", 1)

    def test_training_counts_tokens_and_stops_before_the_ceiling(self):
        self.approve(ceiling="0.0900")                                  # budget is 0.0864
        svc = fakes.FakeService()
        run = self.run_(service=svc)
        run.start_arm("C")
        mk = lambda n: fakes.FakeDatum(fakes.FakeModelInput(range(n - 1)), {})   # a datum of n tokens drops one
        run.train_step("C", [mk(40000), mk(40000)], 1e-3)               # 80000 tokens = $0.06
        self.assertEqual(run.meter.tokens["train"], 80000)
        self.assertEqual(run.meter.spent, Fraction(80000 * 3, 4 * 10**6))
        client = svc.clients[0]
        n_calls = len(client.calls)
        with self.assertRaises(T.BudgetStop):
            run.train_step("C", [mk(40000)], 1e-3)                      # would reach 0.09
        self.assertEqual(len(client.calls), n_calls)                    # nothing was sent
        self.assertLess(run.meter.spent, run.meter.ceiling)

    def test_a_call_that_lands_exactly_on_the_ceiling_is_refused(self):
        m = T.Meter(Fraction(3, 4))
        with self.assertRaises(T.BudgetStop):
            m.reserve("train", 1000000)
        m.reserve("train", 999999)
        self.assertLess(m.spent, m.ceiling)


class RunTests(Base):
    def setUp(self):
        super().setUp()
        self.approve(ceiling="5.00")
        self.svc = fakes.FakeService()
        self.run = self.run_(service=self.svc)

    def test_lora_settings_and_model_id_are_passed(self):
        self.run.start_arm("C", rank=16, seed=3, train_mlp=True, train_attn=False, train_unembed=False)
        kw = self.svc.created[0]
        self.assertEqual(kw["base_model"], "thinkingmachines/Inkling-2-Mini")
        self.assertEqual((kw["rank"], kw["seed"], kw["train_mlp"], kw["train_attn"], kw["train_unembed"]),
                         (16, 3, True, False, False))

    def test_default_settings(self):
        self.run.start_arm("C")
        self.assertEqual(self.svc.created[0]["rank"], 8)

    def test_the_training_client_and_the_base_sampler_are_the_results_of_the_library_futures(self):
        base = fakes.FakeSampler()
        svc = fakes.FakeService(base=base)
        self.approve("run-2", ceiling="5.00")
        self.run.close()                                  # setUp's run holds the lock
        run = self.run_("run-2", service=svc)
        self.assertIs(run.base_sampler(), base)
        run.start_arm("C")
        self.assertIs(run.clients["C"], svc.clients[0])

    def test_one_training_client_per_label(self):
        self.run.start_arm("C")
        with self.assertRaises(T.BackendError):
            self.run.start_arm("C")

    def test_step_is_forward_backward_then_optim_step(self):
        self.run.start_arm("C")
        d = T.make_datum(fakes.FakeTypes, [1, 2, 3], [4, 5])
        self.assertEqual(d.model_input.tokens, [1, 2, 3, 4])
        self.assertEqual(d.loss_fn_inputs["weights"], [0, 0, 1, 1])
        self.assertEqual(d.loss_fn_inputs["target_tokens"], [2, 3, 4, 5])
        self.run.train_step("C", [d, d], 2e-4)
        self.assertEqual([c[0] for c in self.svc.clients[0].calls], ["forward_backward", "optim_step"])
        self.assertEqual(self.svc.clients[0].calls[0][1:], (2, "cross_entropy"))
        self.assertEqual(self.run.meter.tokens["train"], 10)           # 2 datums of 5 tokens: the shift drops one each

    def test_at_most_one_checkpoint_per_arm(self):
        self.run.start_arm("C")
        self.run.start_arm("B")
        self.run.checkpoint_sampler("C")
        with self.assertRaises(T.BackendError):
            self.run.checkpoint_sampler("C")
        self.run.checkpoint_sampler("B")
        self.assertEqual([c.saved for c in self.svc.clients], [1, 1])

    def codec(self):
        return C.Codec(fakes.FakeTokenizer())

    def encode(self, text):
        return self.codec().target_ids(text)               # the reply and the end marker (the opening is in the prompt)

    def test_sampling_counts_prompt_and_returned_tokens_and_obeys_the_cap(self):
        sampler = fakes.FakeSampler(reply_tokens=[ord("a")] * 500)
        s = E.build_set("heldout1", {"S": 1})
        resp = T.TinkerResponder(self.run, sampler, self.codec(), 7)
        text, n, was_cut = resp(E.View(s.episodes[0], "C"))
        self.assertEqual((text, n, was_cut), ("a" * 7, 7, True))      # cut at the cap: reported, so it counts as a format break
        self.assertEqual(resp.stats, {"calls": 1, "accepted": 1, "new_block": 0, "cut": 1})
        self.assertEqual(sampler.calls[0][2], 8)                       # the cap plus the end marker
        self.assertEqual(self.run.meter.tokens["sample"], 8)           # counted as returned
        self.assertEqual(self.run.meter.tokens["prefill"], sampler.calls[0][0])
        self.assertGreater(sampler.calls[0][0], 50)

    def test_an_overrun_stops_the_run_at_once_and_keeps_the_returned_ids(self):
        sampler = fakes.FakeSampler(reply_tokens=[ord("a")] * 500, overrun=True)
        s = E.build_set("heldout1", {"S": 1})
        resp = T.TinkerResponder(self.run, sampler, self.codec(), 7)
        with self.assertRaises(T.BudgetStop):
            resp(E.View(s.episodes[0], "C"))
        self.assertEqual(self.run.meter.tokens["sample"], 500)         # counted as returned
        self.assertEqual((resp.reached, resp.last_returned), (True, [[ord("a")] * 500]))
        self.assertEqual(resp.stats["calls"], 0)

    def test_the_returned_ids_are_kept_whole_and_reset_for_each_call(self):
        ids = self.encode("x0 = 1") + [ord("z")] * 5              # reply, end marker, then ids after it
        sampler = fakes.FakeSampler(reply_tokens=ids)
        s = E.build_set("heldout1", {"S": 1})
        resp = T.TinkerResponder(self.run, sampler, self.codec(), 96)
        self.assertEqual((resp.reached, resp.last_returned), (False, None))
        resp(E.View(s.episodes[0], "C"))
        self.assertEqual((resp.reached, resp.last_returned), (True, [ids]))
        sampler.reply_tokens = [1, 2]
        resp(E.View(s.episodes[0], "C"))
        self.assertEqual(resp.last_returned, [[1, 2]])
        self.run.meter.spent = self.run.meter.ceiling - Fraction(1, 10**9)   # the next call stops before the service
        with self.assertRaises(T.BudgetStop):
            resp(E.View(s.episodes[0], "C"))
        self.assertEqual((resp.reached, resp.last_returned), (False, None))   # nothing is left from the call before

    def test_a_call_that_stops_before_the_service_is_reached_says_so(self):
        s = E.build_set("heldout1", {"S": 1})
        self.run.meter.spent = self.run.meter.ceiling - Fraction(1, 10**9)     # no room for the call
        resp = T.TinkerResponder(self.run, fakes.FakeSampler(), self.codec(), 96)
        with self.assertRaises(T.BudgetStop):
            resp(E.View(s.episodes[0], "C"))
        self.assertEqual((resp.reached, resp.last_returned), (False, None))

    def test_a_service_error_after_the_request_was_made_is_reached_without_ids(self):
        class Boom:
            def sample(self, *a, **kw):
                raise RuntimeError("down")
        s = E.build_set("heldout1", {"S": 1})
        resp = T.TinkerResponder(self.run, Boom(), self.codec(), 96)
        with self.assertRaises(T.BackendError):
            resp(E.View(s.episodes[0], "C"))
        self.assertEqual((resp.reached, resp.last_returned), (True, None))

    def test_the_prompt_carries_special_ids_and_sampling_stops_on_the_end_marker(self):
        sampler = fakes.FakeSampler(reply_tokens=self.encode("x0 = 1"))
        s = E.build_set("heldout1", {"S": 1})
        T.TinkerResponder(self.run, sampler, self.codec(), 96)(E.View(s.episodes[0], "C"))
        ids = sampler.prompts[0]
        c = self.codec()
        self.assertEqual(ids[:2], [c.role["system"], c.content])
        self.assertEqual(ids[-2:], [c.role["assistant"], c.content])   # the forced opening of the model's turn
        self.assertEqual(ids[-3], c.end)                               # the last user message ends before it
        self.assertEqual(ids.count(c.end), 4)                          # system, user, model, user
        self.assertEqual(sampler.stops[0], [c.end, c.eos])
        self.assertEqual(ids, c.prompt_ids(E.View(s.episodes[0], "C").messages))

    def test_the_reply_is_cut_at_the_end_marker(self):
        sampler = fakes.FakeSampler(reply_tokens=self.encode("x0 = 1") + [ord("z")] * 5)         # reply, end, junk
        s = E.build_set("heldout1", {"S": 1})
        resp = T.TinkerResponder(self.run, sampler, self.codec(), 96)
        text, n, was_cut = resp(E.View(s.episodes[0], "C"))
        self.assertEqual((text, n, was_cut), ("x0 = 1", 6, False))
        self.assertEqual(resp.stats, {"calls": 1, "accepted": 1, "new_block": 0, "cut": 0})

    def test_a_reply_that_opens_a_new_block_is_counted_and_cannot_parse(self):
        c = self.codec()
        s = E.build_set("heldout1", {"S": 1})
        for block in ([c.thinking], [c.role["assistant"], c.content], [c.content]):
            sampler = fakes.FakeSampler(reply_tokens=block + self.encode("x0 = 1\nx1 = 2\nx2 = 3\nx3 = 4"))
            resp = T.TinkerResponder(self.run, sampler, c, 96)
            text, n, was_cut = resp(E.View(s.episodes[0], "C"))
            self.assertEqual(resp.stats, {"calls": 1, "accepted": 1, "new_block": 1, "cut": 0})
            self.assertTrue(text.startswith("<|"))
            self.assertEqual(V.outcome_of(V.ep_mod.rsig(), s.episodes[0], text, was_cut), "X")

    def test_a_marker_after_the_end_marker_is_not_a_new_block(self):
        c = self.codec()
        sampler = fakes.FakeSampler(reply_tokens=[ord("a"), c.end, c.thinking])
        s = E.build_set("heldout1", {"S": 1})
        resp = T.TinkerResponder(self.run, sampler, c, 96)
        resp(E.View(s.episodes[0], "C"))
        self.assertEqual(resp.stats["new_block"], 0)

    def test_a_response_with_other_than_one_sequence_is_refused(self):
        class Two(fakes.FakeSampler):
            def sample(self, prompt, num_samples, sampling_params):
                fut = super().sample(prompt, num_samples, sampling_params)
                fut._value.sequences = fut._value.sequences * 2
                return fut
        s = E.build_set("heldout1", {"S": 1})
        with self.assertRaises(T.BackendError):
            T.TinkerResponder(self.run, Two(), self.codec(), 96)(E.View(s.episodes[0], "C"))

    def test_sampling_reserves_the_cap_and_stops_before_the_ceiling(self):
        self.approve(ceiling="0.0866")
        self.run.close()                                  # setUp's run holds the lock
        os.remove(self.path + ".spend.jsonl")             # a fresh ledger: setUp already started this run id
        run = self.run_(service=fakes.FakeService())
        run.meter.spent = Fraction(8659, 100000)        # almost at the ceiling
        sampler = fakes.FakeSampler()
        with self.assertRaises(T.BudgetStop):
            T.TinkerResponder(run, sampler, self.codec(), 96)(E.View(E.build_set("heldout1", {"S": 1}).episodes[0], "C"))
        self.assertEqual(sampler.calls, [])

    def test_responder_works_inside_the_evaluation_harness(self):
        sampler = fakes.FakeSampler(reply_tokens=self.encode("x0 = 0\nx1 = 0\nx2 = 0\nx3 = 0"))
        s = E.build_set("heldout1", {"S": 3})
        r = V.evaluate_arm(T.TinkerResponder(self.run, sampler, self.codec(), 96), s, "C", 96, "tinker-fake")
        self.assertEqual((r.n, r.format_broken), (3, 0))
        self.assertEqual(self.run.meter.tokens["prefill"], sum(c[0] for c in sampler.calls))
        self.assertEqual(self.run.meter.tokens["sample"], 3 * 28)      # 3 x (27 characters, the end marker)

    def test_base_sampler_is_not_a_checkpoint(self):
        self.run.base_sampler()
        self.assertEqual(self.run.checkpoints, {})


class LedgerTests(Base):
    """The spend ceiling holds across processes: the ledger is written before each call."""

    def setUp(self):
        super().setUp()
        self.approve(ceiling="1.00")
        self.ledger = self.path + ".spend.jsonl"

    def start(self, hold=False, **kw):
        """A run on the ledger. Unless hold is true its lock is dropped at once, as if that
        process had ended, so that the next start is not turned away. Its meter still works."""
        kw.setdefault("service", fakes.FakeService())
        plan_id = kw.pop("plan_id", PID)
        run = T.TinkerRun("run-1", self.path, kw.pop("plan", self.plan), "test", plan_id, kw.pop("service"),
                          fakes.FakeTypes, **kw)
        self.addCleanup(run.close)
        if not hold:
            run.close()
        return run

    def lines(self):
        with open(self.ledger) as fh:
            return [json.loads(x) for x in fh]

    def raw(self):
        with open(self.ledger) as fh:
            return fh.read()

    def test_a_start_and_each_reservation_and_refund_are_written(self):
        run = self.start()
        run.meter.reserve("sample", 100)
        run.meter.settle("sample", 100, 30)
        run.meter.reserve("train", 7)
        self.assertEqual(self.lines(), [
            {"ev": "start", "plan_id": PID, "run_id": "run-1"},
            {"ev": "reserve", "kind": "sample", "run_id": "run-1", "tokens": 100},
            {"ev": "adjust", "kind": "sample", "run_id": "run-1", "tokens": -70},
            {"ev": "reserve", "kind": "train", "run_id": "run-1", "tokens": 7}])
        spent, tokens, starts, plan_id = T.Ledger(self.ledger, "run-1").replay()
        self.assertEqual((spent, tokens["sample"], tokens["train"], starts, plan_id),
                         (run.meter.spent, 30, 7, 1, PID))

    def test_an_overrun_is_written_as_extra_tokens(self):
        run = self.start()
        run.meter.reserve("sample", 10)
        with self.assertRaises(T.BudgetStop):
            run.meter.settle("sample", 10, 25)
        self.assertEqual(self.lines()[-1]["tokens"], 15)
        self.assertEqual(T.Ledger(self.ledger, "run-1").replay()[1]["sample"], 25)

    def test_the_reservation_is_on_disk_before_the_service_is_called(self):
        seen = []
        outer = self

        class Spy(fakes.FakeTrainingClient):
            def forward_backward(self, data, loss_fn):
                seen.append([r["ev"] for r in outer.lines()])
                return super().forward_backward(data, loss_fn)
        svc = fakes.FakeService()
        svc.create_lora_training_client = lambda **kw: svc.clients.append(Spy()) or fakes.FakeFuture(svc.clients[-1])
        run = self.start(service=svc)
        run.start_arm("C")
        run.train_step("C", [T.make_datum(fakes.FakeTypes, [1, 2, 3], [4])], 1e-3)
        self.assertEqual(seen, [["start", "reserve"]])

    def test_a_second_process_counts_what_the_first_spent(self):
        first = self.start()
        first.meter.reserve("train", 1000000)                 # $0.75
        second = self.start(resume=True, plan={"train": 10, "prefill": 10, "sample": 10})
        self.assertEqual(second.meter.spent, Fraction(3, 4))
        self.assertEqual(second.meter.tokens["train"], 1000000)
        with self.assertRaises(T.BudgetStop):                 # $0.75 + $0.30 would pass the $1.00 ceiling
            second.meter.reserve("train", 400000)
        second.meter.reserve("train", 300000)                 # $0.225 more: $0.975 in all
        self.assertEqual(T.Ledger(self.ledger, "run-1").replay()[0], Fraction(975, 1000))

    def test_three_restarts_cannot_spend_more_than_the_ceiling_in_all(self):
        small = {"train": 10, "prefill": 10, "sample": 10}
        total = Fraction(0)
        for i in range(3):
            run = self.start(resume=i > 0, plan=small)
            try:
                for _ in range(100):
                    run.meter.reserve("train", 100000)        # $0.075 a call
            except T.BudgetStop:
                pass
            total = run.meter.spent
        self.assertLess(total, Fraction(1))
        self.assertEqual(T.Ledger(self.ledger, "run-1").replay()[0], total)

    def test_a_run_id_that_already_started_needs_resume(self):
        self.start()
        with self.assertRaises(T.ApprovalError):
            self.start()
        self.start(resume=True)

    def test_a_resumed_run_must_be_the_same_plan(self):
        self.start()
        self.approve(plan_id="other")                         # the owner now approves another plan for this id
        with self.assertRaises(T.ApprovalError) as cm:        # the approval agrees, the ledger does not
            self.start(plan_id="other", resume=True)
        self.assertIn("different plan", str(cm.exception))
        with self.assertRaises(T.ApprovalError):              # the plan given is not the approved one
            self.start(resume=True)

    def test_the_whole_plan_must_fit_under_what_is_left(self):
        first = self.start()
        first.meter.reserve("train", 1200000)                 # $0.90 of the $1.00
        with self.assertRaises(T.BudgetError):                # the plan costs $0.0864 and only $0.10 is left: fits
            self.start(resume=True, plan={"train": 200000, "prefill": 10, "sample": 10})
        self.start(resume=True)                  # the default plan costs $0.0864: fits

    def test_a_start_that_is_refused_writes_nothing(self):
        self.start()
        before = self.raw()
        with self.assertRaises(T.ApprovalError):               # no resume
            self.start()
        with self.assertRaises(T.ApprovalError):               # not the approved plan
            self.start(plan_id="q", resume=True)
        self.approve(plan_id="q")
        with self.assertRaises(T.ApprovalError):               # approved, but not the plan that started
            self.start(plan_id="q", resume=True)
        self.assertEqual(self.raw(), before)

    def test_other_run_ids_in_the_same_ledger_are_not_counted(self):
        self.approve(ceiling="1.00")
        other = T.Ledger(self.ledger, "elsewhere")
        other.append({"ev": "reserve", "kind": "train", "tokens": 1000000})
        run = self.start()
        self.assertEqual(run.meter.spent, 0)

    def test_a_damaged_ledger_refuses_the_run(self):
        good = json.dumps({"ev": "start", "plan_id": PID, "run_id": "run-1"}) + "\n"
        row = lambda **kw: json.dumps(dict({"run_id": "run-1", "ev": "reserve", "kind": "train", "tokens": 5}, **kw)) + "\n"
        for raw in (good + '{"run_id": "run-1"', "not json\n", "[]\n", '{"run_id": 5, "ev": "start"}\n',
                    '{"run_id": "run-1", "ev": 5}\n', row(ev="refund"), row(kind="rent"), row(tokens=1.5),
                    row(tokens=True), row(tokens=-5), row(ev="adjust", tokens=-5), row(tokens="5"),
                    row() + row(tokens=-5), good.rstrip() [:-1] + ', "x": 1.5}\n'):
            with open(self.ledger, "w") as fh:
                fh.write(raw)
            with self.assertRaises(T.BudgetError, msg=raw):
                self.start(resume=True)

    def test_every_ledger_line_is_flushed_to_disk(self):
        import unittest.mock as mock
        run = self.start()
        with mock.patch("os.fsync") as sync:
            run.meter.reserve("train", 5)
            run.meter.settle("sample", 0, 0)
            run.meter.reserve("sample", 5)
            with self.assertRaises(T.BudgetStop):
                run.meter.settle("sample", 5, 9)
        self.assertEqual(sync.call_count, 4)

    def test_a_ledger_that_cannot_be_written_stops_before_any_call(self):
        run = self.start()
        run.meter.ledger.path = os.path.join(self.tmp.name, "no-such-dir", "x.jsonl")
        with self.assertRaises(T.BudgetStop):
            run.meter.reserve("train", 5)
        self.assertEqual(run.meter.spent, 0)
        import unittest.mock as mock
        with mock.patch("os.open", side_effect=OSError("denied")):      # the run lock cannot be opened
            with self.assertRaises(T.BudgetStop):
                self.start()

    def test_require_room_counts_what_is_spent(self):
        run = self.start()
        run.meter.reserve("train", 1000000)                   # $0.75
        run.meter.require_room({"train": 100000, "prefill": 1, "sample": 1})            # $0.075: fits under $1.00
        with self.assertRaises(T.BudgetStop):
            run.meter.require_room({"train": 400000, "prefill": 1, "sample": 1})        # $0.30: does not
        with self.assertRaises(T.BudgetStop):
            run.meter.require_room({"train": 0, "prefill": 0, "sample": 500000})        # exactly $0.25: reaches the ceiling
        run.meter.require_room({"train": 0, "prefill": 0, "sample": 499999})

    def test_a_crashed_process_leaves_its_spend_in_the_ledger(self):
        code = ("import os, sys\n"
                "sys.path.insert(0, %r)\n"
                "import fakes, tinker_backend as T\n"
                "run = T.TinkerRun('run-1', %r, {'train': 100000, 'prefill': 10000, 'sample': 10000}, 'test', %r, "
                "fakes.FakeService(), fakes.FakeTypes)\n"
                "run.meter.reserve('train', 1000000)\n"
                "os._exit(7)\n") % (_setup.LOOP, self.path, PID)
        r = subprocess.run([sys.executable, "-I", "-B", "-c", code], capture_output=True, text=True)
        self.assertEqual(r.returncode, 7, r.stderr)
        run = self.start(resume=True)
        self.assertEqual(run.meter.spent, Fraction(3, 4))             # the dead process's reservation counts
        with self.assertRaises(T.ApprovalError):
            self.start()                                   # and a plain restart is refused


class LockTests(Base):
    """One live process per ledger, and a run only for the plan its approval names."""

    def setUp(self):
        super().setUp()
        self.approve(ceiling="1.00")

    def start(self, **kw):
        return T.TinkerRun("run-1", self.path, self.plan, "test", kw.pop("plan_id", PID), fakes.FakeService(),
                           fakes.FakeTypes, **kw)

    def test_a_second_holder_of_the_ledger_is_refused_until_the_first_closes(self):
        first = self.start()
        with self.assertRaises(T.ApprovalError) as cm:
            self.start(resume=True)
        self.assertIn("another process", str(cm.exception))
        first.close()
        second = self.start(resume=True)
        second.close()

    def test_close_can_be_repeated_and_a_context_manager_closes(self):
        with self.start() as run:
            self.assertIsNotNone(run.lock_fd)
        self.assertIsNone(run.lock_fd)
        run.close()
        with self.start(resume=True):
            pass

    def test_a_start_that_is_refused_does_not_keep_the_lock(self):
        self.start().close()
        with self.assertRaises(T.ApprovalError):               # no resume
            self.start()
        with self.assertRaises(T.BudgetError):                 # the plan does not fit
            self.start(resume=True).close()
            T.TinkerRun("run-1", self.path, {"train": 10**9, "prefill": 1, "sample": 1}, "test", PID,
                        fakes.FakeService(), fakes.FakeTypes, resume=True)
        self.start(resume=True).close()                        # nothing is left locked

    def test_two_real_processes_cannot_spend_past_the_ceiling_together(self):
        """A process that holds the run, and a second one started meanwhile on the same run id."""
        holder = ("import sys, time\n"
                  "sys.path.insert(0, %r)\n"
                  "import fakes, tinker_backend as T\n"
                  "run = T.TinkerRun('run-1', %r, {'train': 100000, 'prefill': 10000, 'sample': 10000}, 'test', %r, "
                  "fakes.FakeService(), fakes.FakeTypes)\n"
                  "print('held', flush=True)\n"
                  "sys.stdin.readline()\n") % (_setup.LOOP, self.path, PID)
        other = ("import sys\n"
                 "sys.path.insert(0, %r)\n"
                 "import fakes, tinker_backend as T\n"
                 "try:\n"
                 "    T.TinkerRun('run-1', %r, {'train': 10, 'prefill': 10, 'sample': 10}, 'test', %r, "
                 "fakes.FakeService(), fakes.FakeTypes, resume=True)\n"
                 "except T.ApprovalError as exc:\n"
                 "    print('refused:', exc)\n"
                 "    sys.exit(5)\n") % (_setup.LOOP, self.path, PID)
        p = subprocess.Popen([sys.executable, "-I", "-B", "-c", holder], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             text=True)
        try:
            self.assertEqual(p.stdout.readline().strip(), "held")
            r = subprocess.run([sys.executable, "-I", "-B", "-c", other], capture_output=True, text=True)
            self.assertEqual((r.returncode, "another process" in r.stdout), (5, True), r.stdout + r.stderr)
        finally:
            p.communicate("\n", timeout=30)
        self.start(resume=True).close()                         # the holder has ended: its lock is gone

    def test_the_ledger_is_beside_the_approvals_file_and_cannot_be_named(self):
        import inspect
        self.assertNotIn("ledger_path", inspect.signature(T.TinkerRun.__init__).parameters)
        run = self.start()
        run.close()
        self.assertTrue(os.path.exists(self.path + ".spend.jsonl"))
        self.assertTrue(os.path.exists(self.path + ".spend.jsonl.lock"))

    def test_an_approval_names_its_plan_and_a_run_for_another_plan_is_refused(self):
        with self.assertRaises(T.ApprovalError):               # other fingerprint
            self.start(plan_id="not-the-approved-plan")
        with self.assertRaises(T.ApprovalError):               # other plan name
            T.TinkerRun("run-1", self.path, self.plan, "other-name", PID, fakes.FakeService(), fakes.FakeTypes)
        self.start().close()

    def test_an_approval_without_a_plan_is_refused(self):
        """Each row is refused for what it lacks: the plan name and fingerprint given match the row."""
        ok = {"run_id": "run-1", "ceiling_usd": "1.00", "plan": "test", "plan_id": PID}
        cases = [({k: v for k, v in ok.items() if k != "plan"}, None, PID),
                 ({k: v for k, v in ok.items() if k != "plan_id"}, "test", None),
                 (dict(ok, plan=""), "", PID), (dict(ok, plan_id=""), "test", ""),
                 (dict(ok, plan=5), 5, PID), (dict(ok, plan_id=5), "test", 5)]
        for row, plan_name, plan_id in cases:
            self.approve(raw=json.dumps({"approvals": [row]}))
            with self.assertRaises(T.ApprovalError, msg=str(row)) as cm:
                T.TinkerRun("run-1", self.path, self.plan, plan_name, plan_id, fakes.FakeService(), fakes.FakeTypes)
            self.assertIn("must name its plan", str(cm.exception))
        self.approve(raw=json.dumps({"approvals": [ok]}))
        self.start().close()

    def test_load_approval_returns_ceiling_plan_and_fingerprint(self):
        got = T.load_approval(self.path, "run-1")
        self.assertEqual((got.ceiling, got.plan, got.plan_id), (Fraction(1), "test", PID))


class SecretTests(Base):
    KEY = "tml-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef"

    def test_redact(self):
        self.assertNotIn("tml-ABC", T.redact("bad key " + self.KEY))
        self.assertNotIn("A" * 40, T.redact("x " + "A" * 40))
        self.assertNotIn("sekrit", T.redact("api_key=sekrit and more"))
        self.assertNotIn("sekrit", T.redact("API-KEY: sekrit"))

    def test_service_errors_are_redacted_and_nothing_is_printed(self):
        import contextlib
        import io
        self.approve(ceiling="5.00")
        svc = fakes.FakeService(fail_with=RuntimeError("auth failed for " + self.KEY))
        run = self.run_(service=svc)
        run.start_arm("C")
        d = T.make_datum(fakes.FakeTypes, [1, 2], [3])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            with self.assertRaises(T.BackendError) as cm:
                run.train_step("C", [d], 1e-3)
        self.assertNotIn("ABCDEFGH", str(cm.exception))
        self.assertIn("REDACTED", str(cm.exception))
        self.assertEqual(buf.getvalue(), "")
        self.assertTrue(cm.exception.__suppress_context__)
        self.assertIsNone(cm.exception.__cause__)

    def test_a_registered_key_is_removed_whole_before_the_pattern_and_the_cut(self):
        key = "tml-PLANTED+k3y/0123456789abc=def"                      # holds characters the pattern does not match
        self.addCleanup(T.set_secret_values, [])
        T.set_secret_values([key])
        self.assertNotIn("k3y", T.redact("auth failed for key %s please retry" % key))
        self.assertNotIn("0123456789abc", T.redact("x" * 380 + key))   # a key that straddles the 400 cut
        T.set_secret_values([])
        self.assertIn("k3y", T.redact("auth failed for key %s" % key))   # the control: unregistered, it leaks
        T.set_secret_values([key, key + "+more", "", None])
        self.assertEqual(T.redact(key + "+more"), "[REDACTED]")        # the longest value first

    def test_a_registered_key_does_not_leak_through_the_guard_path(self):
        key = "tml-PLANTED+k3y/0123456789abc=def"
        self.addCleanup(T.set_secret_values, [])
        T.set_secret_values([key])
        self.approve(ceiling="5.00")
        svc = fakes.FakeService(fail_with=RuntimeError("auth failed for key %s please retry" % key))
        run = self.run_(service=svc)
        run.start_arm("C")
        d = T.make_datum(fakes.FakeTypes, [1, 2], [3])
        with self.assertRaises(T.BackendError) as cm:
            run.train_step("C", [d], 1e-3)
        self.assertNotIn("k3y", str(cm.exception))
        self.assertNotIn("0123456789abc", str(cm.exception))
        self.assertIn("please retry", str(cm.exception))

    def test_source_never_reads_environment_or_key_files(self):
        with open(T.__file__.replace(".pyc", ".py"), "r", encoding="utf-8") as fh:
            src = fh.read()
        code = "\n".join(ln for ln in src.split("\n") if not ln.lstrip().startswith("#"))
        for word in ("environ", "getenv", "tinker_key", "textutil", "print("):
            self.assertNotIn(word, code)
        # the approvals file, the lock file, and the spend ledger twice (read it, append to it)
        self.assertEqual(len(re.findall(r"\bopen\(", code)), 4)


if __name__ == "__main__":
    unittest.main()
