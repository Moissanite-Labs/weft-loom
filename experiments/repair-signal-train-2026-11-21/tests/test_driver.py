import json
import os
import tempfile
import unittest
from fractions import Fraction
from unittest import mock

import _setup  # noqa: F401
import codec as C
import cost
import driver as D
import episodes as E
import evaluate as V
import fakes
import ratchet as RT
import receipts
import reference_policies as RP
import tinker_backend as T

CAP = 96
DECISION = "dec-driver"


def texts(epset, kind):
    out = []
    for ep in epset.episodes:
        r = E.render(ep, "A")
        out.append(r.target_text if kind == "target" else r.attempt_text)
    return out


class Fixture(unittest.TestCase):
    """A small registered run: 2 seeds x arms A, B, C, 64 training examples,
    10 + 10 episodes per held-out set."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = self.tmp.name
        registry = os.path.join(self.dir, "decisions.json")
        with open(registry, "w") as fh:
            json.dump({"decisions": [DECISION]}, fh)
        patch = mock.patch.object(V, "DECISIONS_PATH", registry)
        patch.start()
        self.addCleanup(patch.stop)
        self.codec = C.Codec(fakes.FakeTokenizer())
        self.plan = cost.full_plan(64, 2, CAP, heldout_per_tier=10)
        self.h1 = E.build_set("heldout1", self.plan.eval1_counts)
        self.h2 = E.build_set("heldout2", self.plan.eval2_counts)
        self.fail1, self.fail2 = texts(self.h1, "attempt"), texts(self.h2, "attempt")
        self.win1, self.win2 = texts(self.h1, "target"), texts(self.h2, "target")

    def mixed(self, win, fail, wins):
        return [win[i] if i in wins else fail[i] for i in range(len(win))]

    def scripts(self, c_wins, b_wins):
        c = self.mixed(self.win1, self.fail1, c_wins) * 1
        c = c + self.fail1 * 3 + self.mixed(self.win2, self.fail2, c_wins) + self.fail2 * 2
        b = self.mixed(self.win1, self.fail1, b_wins) + self.mixed(self.win2, self.fail2, b_wins)
        return c, b

    def approvals(self, run_id="run-d", ceiling="5.00", plan=None):
        path = os.path.join(self.dir, "approvals.json")
        with open(path, "w") as fh:
            json.dump({"approvals": [D.approval_row(run_id, ceiling, self.plan if plan is None else plan)]}, fh)
        return path

    def start_run(self, *args, **kw):
        """D.start_run, then the run's lock is dropped at once, as if its process had ended: a
        test may start the same run id again. The run's meter still works."""
        run = D.start_run(*args, **kw)
        run.close()
        return run

    def service(self, c_replies, b_replies=None, a_replies=None, base=None):
        """c_replies: the C adapter's scripted texts for seed 0 and seed 1 (same list)."""
        enc = self.codec.target_ids
        samplers = []
        for _seed in range(2):
            for arm in ("A", "B", "C"):
                texts_ = {"A": a_replies, "B": b_replies, "C": c_replies}[arm] or self.fail1 + self.fail2
                samplers.append(fakes.ScriptedSampler(texts_, enc))
        return fakes.FakeService(checkpoint_samplers=samplers, base=fakes.ScriptedSampler(base or self.fail1, enc)), samplers

    def ratchet(self, name="d"):
        sub = os.path.join(self.dir, name)
        os.makedirs(sub, exist_ok=True)
        return RT.Ratchet(os.path.join(sub, "r.jsonl"), os.path.join(sub, "l.jsonl"), os.path.join(sub, "lock.json"),
                          CAP)

    def run_registered(self, svc, run_id="run-d", ratchet=None):
        counter = cost.Counter(rule_only=True)
        run = self.start_run(run_id, self.approvals(run_id), self.plan, counter, svc, fakes.FakeTypes)
        rt = ratchet or self.ratchet()
        summary = D.run_registered(run, rt, self.codec, run_id, self.plan, {"cap": CAP}, DECISION)
        return summary, run, rt


class TrainArmTests(Fixture):
    def test_batches_steps_and_loss_only_on_the_target(self):
        svc = fakes.FakeService()
        run = self.start_run("run-d", self.approvals(), self.plan, cost.Counter(rule_only=True), svc, fakes.FakeTypes)
        train = E.build_set("train", {"S": 32, "M": 32})
        steps = D.train_arm(run, "C-s0", self.codec, train, "C", 0)
        self.assertEqual(steps, 2)
        self.assertEqual(svc.created[0]["rank"], 8)
        self.assertEqual([c[:2] for c in svc.clients[0].calls], [("forward_backward", 32), ("optim_step", 1e-3)] * 2)

    def test_datums_are_built_from_the_codec_ids_with_the_arms_own_text(self):
        seen = []

        class Spy(fakes.FakeTrainingClient):
            def forward_backward(self, data, loss_fn):
                seen.extend(data)
                return super().forward_backward(data, loss_fn)
        svc = fakes.FakeService()
        svc.create_lora_training_client = lambda **kw: svc.clients.append(Spy()) or fakes.FakeFuture(svc.clients[-1])
        run = self.start_run("run-d", self.approvals(), self.plan, cost.Counter(rule_only=True), svc, fakes.FakeTypes)
        train = E.build_set("train", {"S": 32})
        D.train_arm(run, "B-s0", self.codec, train, "B", 0)
        self.assertEqual(len(seen), 32)
        by_text = {}
        for ep in train.episodes:
            r = E.render(ep, "B")
            p, t = self.codec.train_ids(r.messages, r.target_text)
            by_text[tuple((p + t)[1:])] = (len(p), len(t))
        for d in seen:
            key = tuple(d.loss_fn_inputs["target_tokens"])
            n_prompt, n_target = by_text[key]
            w = d.loss_fn_inputs["weights"]
            self.assertEqual(sum(w), n_target)
            self.assertEqual(w[-n_target:], [1] * n_target)
            self.assertEqual(sum(w[:n_prompt - 1]), 0)

    def test_the_first_batch_follows_the_shuffled_order(self):
        seen = []

        class Spy(fakes.FakeTrainingClient):
            def forward_backward(self, data, loss_fn):
                seen.append([tuple(d.loss_fn_inputs["target_tokens"]) for d in data])
                return super().forward_backward(data, loss_fn)
        svc = fakes.FakeService()
        svc.create_lora_training_client = lambda **kw: svc.clients.append(Spy()) or fakes.FakeFuture(svc.clients[-1])
        run = self.start_run("run-d", self.approvals(), self.plan, cost.Counter(rule_only=True), svc, fakes.FakeTypes)
        train = E.build_set("train", {"S": 32, "M": 32})
        D.train_arm(run, "C-s0", self.codec, train, "C", 0)
        order = D.shuffled_order(64, 0, "C-s0")
        want = []
        for i in order[:32]:
            r = E.render(train.episodes[i], "C")
            p, t = self.codec.train_ids(r.messages, r.target_text)
            want.append(tuple((p + t)[1:]))
        self.assertEqual(seen[0], want)
        self.assertEqual(len(seen), 2)

    def test_the_order_is_shuffled_by_seed_and_label_and_every_example_is_used_once(self):
        a = D.shuffled_order(64, 0, "C-s0")
        self.assertEqual(sorted(a), list(range(64)))
        self.assertEqual(a, D.shuffled_order(64, 0, "C-s0"))
        self.assertNotEqual(a, D.shuffled_order(64, 1, "C-s0"))
        self.assertNotEqual(a, D.shuffled_order(64, 0, "B-s0"))
        self.assertNotEqual(a, list(range(64)))

    def test_partial_batches_are_refused(self):
        svc = fakes.FakeService()
        run = self.start_run("run-d", self.approvals(), self.plan, cost.Counter(rule_only=True), svc, fakes.FakeTypes)
        for n in (0, 33):
            train = E.EpisodeSet("train", {}, E.build_set("train", {"S": 40}).episodes[:n])
            with self.assertRaises(D.DriverError):
                D.train_arm(run, "C-s%d" % n, self.codec, train, "C", 0)
        self.assertEqual(svc.created, [])

    def test_training_stops_at_the_ceiling_before_the_call(self):
        svc = fakes.FakeService()
        run = self.start_run("run-d", self.approvals(ceiling="5.00"), self.plan, cost.Counter(rule_only=True), svc,
                          fakes.FakeTypes)
        run.meter.spent = run.meter.ceiling - Fraction(1, 10**6)
        with self.assertRaises(T.BudgetStop):
            D.train_arm(run, "C-s0", self.codec, E.build_set("train", {"S": 32}), "C", 0)
        self.assertEqual(svc.clients[0].calls, [])


class StartRunTests(Fixture):
    def test_the_plan_is_computed_from_cost_for_this_configuration(self):
        run = self.start_run("run-d", self.approvals(), self.plan, cost.Counter(rule_only=True), fakes.FakeService(),
                          fakes.FakeTypes)
        totals, _ = cost.plan_counts(self.plan, cost.Counter(rule_only=True))
        self.assertEqual(run.budget, T.planned_cost(totals))
        self.assertEqual(set(totals), {"train", "prefill", "sample"})

    def test_a_ceiling_below_the_plan_refuses_to_start(self):
        with self.assertRaises(T.BudgetError):
            self.start_run("run-d", self.approvals(ceiling="0.01"), self.plan, cost.Counter(rule_only=True),
                        fakes.FakeService(), fakes.FakeTypes)

    def test_an_unapproved_run_id_refuses_to_start(self):
        with self.assertRaises(T.ApprovalError):
            self.start_run("other", self.approvals("run-d"), self.plan, cost.Counter(rule_only=True),
                        fakes.FakeService(), fakes.FakeTypes)

    def test_a_tokenizer_that_does_not_fit_is_refused(self):
        class Bad(fakes.FakeTokenizer):
            def encode_special(self, name):
                return 5
        with self.assertRaises(D.DriverError):
            D.check_codec(Bad())
        self.assertIsInstance(D.check_codec(fakes.FakeTokenizer()), C.Codec)


class RegisteredRunTests(Fixture):
    """The alpha logic of the decision rule on small synthetic sets. The sets
    are 20 episodes and the scripts are extreme, so the testability gates of
    the preregistration (judge, GATES) are relaxed here and tested on their own
    in GateTests with their real values."""

    def setUp(self):
        super().setUp()
        relaxed = D.Gates(0, Fraction(-1), Fraction(2))
        patch = mock.patch.object(D, "GATES", relaxed)
        patch.start()
        self.addCleanup(patch.stop)

    def c_good(self):
        return self.win1 + self.fail1 * 3 + self.win2 + self.fail2 * 2     # own, B, E, N on set 1; own, E, N on set 2

    def test_a_gain_for_c_goes_through_set_1_then_set_2_once(self):
        svc, samplers = self.service(self.c_good())
        summary, run, rt = self.run_registered(svc)
        self.assertEqual(len(svc.clients), 6)
        self.assertEqual(set(summary["steps"]), {"A-s0", "B-s0", "C-s0", "A-s1", "B-s1", "C-s1"})
        self.assertEqual(set(summary["steps"].values()), {2})
        for seed in (0, 1):
            cmp_ = summary["set1"][seed]
            self.assertTrue(D.conditions_met(cmp_))
            self.assertEqual(cmp_["pass"]["first_only"], 20)
            self.assertEqual(cmp_["format_harm"]["first_better"], False)
            self.assertTrue(cmp_["control_E"]["first_better"] and cmp_["control_N"]["first_better"])
        self.assertTrue(summary["support"])
        self.assertEqual(rt.latch.touched(), [DECISION])
        self.assertTrue(D.conditions_met(summary["set2"]))
        self.assertLess(run.meter.spent, run.meter.ceiling)
        receipts.verify(rt.receipts_path)

    def test_a_windowed_registered_run_records_what_the_sequential_one_records(self):
        base_plan = self.plan
        got = {}
        for window in (1, 4):
            self.plan = cost.full_plan(64, 2, CAP, heldout_per_tier=10, window=window)
            svc, samplers = self.service(self.c_good())
            summary, run, rt = self.run_registered(svc, run_id="run-w%d" % window, ratchet=self.ratchet("w%d" % window))
            keys = ("arm", "descriptor", "n", "passed", "failed", "format_broken", "outcomes", "replies_sha256", "set_sha256")
            raw = [{k: body[k] for k in keys} for body in receipts.bodies(rt.receipts_path) if body.get("kind") == "eval"]
            got[window] = (summary, raw, [s_.prompts for s_ in samplers], run.meter.tokens)
        self.plan = base_plan
        (s1, raw1, prompts1, tokens1), (s4, raw4, prompts4, tokens4) = got[1], got[4]
        self.assertGreater(len(raw1), 10)
        self.assertEqual(raw4, raw1)                                         # every evaluation receipt: replies, outcomes and counts
        self.assertEqual(prompts4, prompts1)                                 # the same prompts, in the same order, per sampler
        self.assertEqual(tokens4, tokens1)
        self.assertEqual((s4["verdict"], s4["support"], s4["steps"]), (s1["verdict"], s1["support"], s1["steps"]))
        for key in s1["own"]:
            self.assertEqual(s4["own"][key].replies_sha256, s1["own"][key].replies_sha256)
        self.assertTrue(s4["support"])

    def test_every_evaluation_of_a_registered_run_is_made_at_the_plans_window(self):
        windows = []
        real = D.responder

        def spy(run, sampler, codec, cap, views=None, window=1):
            windows.append((len(views) if views is not None else None, window))
            return real(run, sampler, codec, cap, views, window)
        self.plan = cost.full_plan(64, 2, CAP, heldout_per_tier=10, window=3)
        svc, _ = self.service(self.c_good())
        with mock.patch.object(D, "responder", spy):
            summary, run, rt = self.run_registered(svc)
        # 3 base texts of 5 (A, B, C, E, N): 5 + 2 seeds x (3 own + 3 controls) at 20 episodes, then 4 on set 2
        self.assertEqual(len(windows), 5 + 2 * 6 + 4)
        self.assertEqual({w for _n, w in windows}, {3})
        self.assertTrue(all(n == 20 for n, _w in windows))

    def test_the_second_set_responders_are_settled_when_the_touch_stops_early(self):
        made = []
        real = D.responder

        def spy(run, sampler, codec, cap, views=None, window=1):
            made.append(real(run, sampler, codec, cap, views, window))
            return made[-1]

        def stop_midway(self_, decision_id, epset2, entries, config, models=None):
            entries[0][1](D.epset_views(epset2, "C")[0])           # one reply asked for, with the window open
            self.assertGreater(len(entries[0][1].pending), 0)
            raise RuntimeError("the touch stops here")
        self.plan = cost.full_plan(64, 2, CAP, heldout_per_tier=10, window=4)
        svc, _ = self.service(self.c_good())
        with mock.patch.object(D, "responder", spy), mock.patch.object(RT.Ratchet, "second_set_results", stop_midway):
            with self.assertRaises(RuntimeError):
                self.run_registered(svc)
        last_four = made[-4:]
        self.assertEqual([len(r.pending) for r in last_four], [0, 0, 0, 0])
        self.assertTrue(all(r.stopped for r in last_four))

    def test_every_sampled_prompt_uses_special_ids_and_stops_on_the_end_marker(self):
        svc, samplers = self.service(self.c_good())
        self.run_registered(svc)
        for smp in samplers + [svc.base]:
            self.assertTrue(smp.prompts)
            for p, stop in zip(smp.prompts, smp.stops):
                self.assertEqual(p[:2], [self.codec.role["system"], self.codec.content])
                self.assertEqual(p[-2:], [self.codec.role["assistant"], self.codec.content])   # the forced opening, every arm
                self.assertEqual(p[-3], self.codec.end)
                self.assertEqual(stop, [self.codec.end, self.codec.eos])

    def test_the_first_set_evaluations_are_the_registered_ones(self):
        svc, samplers = self.service(self.c_good())
        summary, run, rt = self.run_registered(svc)
        self.assertEqual(set(summary["base"]), set(E.ARMS))
        self.assertEqual(set(summary["own"]), {(a, s) for a in "ABC" for s in (0, 1)})
        self.assertEqual(set(summary["controls"]), {(t, s) for t in "BEN" for s in (0, 1)})
        self.assertEqual(summary["controls"][("E", 0)].arm, "E")
        self.assertEqual(summary["controls"][("E", 0)].descriptor, D.adapter_name("C", 0))
        # the three evaluations of the C adapter on set 1 plus its own text: four calls over the set
        self.assertEqual(len(samplers[2].prompts), 4 * 20 + 3 * 20)    # set 1 four times, set 2 three times
        self.assertEqual(len(samplers[5].prompts), 4 * 20)             # seed 1 never touches set 2
        self.assertEqual(len(samplers[1].prompts), 20 + 20)            # B seed 0: own text, and the set 2 own text

    def test_one_checkpoint_per_adapter_and_no_other_checkpoint(self):
        svc, _ = self.service(self.c_good())
        summary, run, rt = self.run_registered(svc)
        self.assertEqual(run.checkpoints, {"%s-s%d" % (a, s): 1 for a in "ABC" for s in (0, 1)})
        self.assertEqual([c.saved for c in svc.clients], [1] * 6)

    def test_no_gain_means_no_support_and_set_2_is_never_touched(self):
        svc, _ = self.service(self.fail1 + self.fail2)
        summary, run, rt = self.run_registered(svc)
        self.assertFalse(summary["support"])
        self.assertIsNone(summary["set2"])
        self.assertEqual(rt.latch.touched(), [])
        self.assertFalse(os.path.exists(rt.latch.path))
        heldout2 = [b for b in receipts.bodies(rt.receipts_path) if b.get("set_kind") == "heldout2"]
        self.assertEqual(heldout2, [])

    def test_a_gain_in_one_seed_only_is_not_enough(self):
        svc, samplers = self.service(self.fail1 + self.fail2)
        svc.checkpoint_samplers[2] = fakes.ScriptedSampler(self.c_good(), self.codec.target_ids)   # C seed 0 only
        summary, run, rt = self.run_registered(svc)
        self.assertTrue(D.conditions_met(summary["set1"][0]))
        self.assertFalse(D.conditions_met(summary["set1"][1]))
        self.assertFalse(summary["support"])
        self.assertEqual(rt.latch.touched(), [])

    def test_a_win_that_buys_itself_with_format_breaks_is_not_support(self):
        # C repairs 7 episodes, breaks the format on 8 and fails the other 5; B fails all 20 in the format.
        # The pass test and the stratum test both see C win, the format gate sees harm.
        script = self.win1[:7] + ["not an answer"] * 8 + self.fail1[15:] + self.win2 + self.fail2 * 2
        svc, _ = self.service(script)
        summary, run, rt = self.run_registered(svc)
        for seed in (0, 1):
            c = summary["own"][("C", seed)]
            self.assertEqual((c.passed, c.format_broken), (7, 8))
            cmp_ = summary["set1"][seed]
            self.assertTrue(cmp_["pass"]["first_better"])
            self.assertTrue(cmp_["stratum"]["first_better"])
            self.assertTrue(cmp_["format_harm"]["first_better"])
            self.assertFalse(D.conditions_met(cmp_))
        self.assertFalse(summary["support"])
        self.assertEqual(rt.latch.touched(), [])

    def test_a_win_over_all_episodes_that_the_stratum_does_not_show_is_not_support(self):
        # C passes 7 episodes where B broke the format: the pass test sees 7 to 0, the stratum sees none
        broken = "not an answer"
        svc, _ = self.service(self.win1[:7] + self.fail1[7:] + self.fail2 * 3,
                              b_replies=[broken] * 7 + self.fail1[7:] + self.fail2)
        summary, run, rt = self.run_registered(svc)
        for seed in (0, 1):
            cmp_ = summary["set1"][seed]
            self.assertTrue(cmp_["pass"]["first_better"])
            self.assertFalse(cmp_["stratum"]["first_better"])
            self.assertFalse(cmp_["format_harm"]["first_better"])
            self.assertFalse(D.conditions_met(cmp_))
        self.assertFalse(summary["support"])
        self.assertEqual(rt.latch.touched(), [])

    def test_a_win_in_the_stratum_that_all_episodes_do_not_show_is_not_support(self):
        # C wins 6 episodes in the format; B wins 6 where C broke the format; B alone broke once
        broken = "not an answer"
        c = self.win1[:6] + [broken] * 6 + self.fail1[12:] + self.fail1 * 3 + self.fail2 * 3
        b = self.fail1[:6] + self.win1[6:12] + [broken] + self.fail1[13:] + self.fail2
        svc, _ = self.service(c, b_replies=b)
        summary, run, rt = self.run_registered(svc)
        for seed in (0, 1):
            cmp_ = summary["set1"][seed]
            self.assertEqual((cmp_["pass"]["first_only"], cmp_["pass"]["second_only"]), (6, 6))
            self.assertFalse(cmp_["pass"]["first_better"])
            self.assertTrue(cmp_["stratum"]["first_better"])
            self.assertFalse(cmp_["format_harm"]["first_better"])
            self.assertFalse(D.conditions_met(cmp_))
        self.assertFalse(summary["support"])
        self.assertEqual(rt.latch.touched(), [])

    def test_equal_wins_in_both_directions_are_not_support(self):
        # C repairs episodes 0 to 6 and B repairs episodes 7 to 13: 7 each way, no difference
        svc, _ = self.service(self.win1[:7] + self.fail1[7:] + self.fail2 * 3,
                              b_replies=self.fail1[:7] + self.win1[7:14] + self.fail1[14:] + self.fail2)
        summary, run, rt = self.run_registered(svc)
        for seed in (0, 1):
            cmp_ = summary["set1"][seed]
            self.assertEqual((cmp_["pass"]["first_only"], cmp_["pass"]["second_only"]), (7, 7))
            self.assertFalse(cmp_["pass"]["first_better"])
        self.assertFalse(summary["support"])

    def test_a_set_1_win_that_set_2_does_not_confirm_is_not_support(self):
        script = self.win1 + self.fail1 * 3 + self.fail2 * 3            # C is no better than B on set 2
        svc, _ = self.service(script)
        summary, run, rt = self.run_registered(svc)
        self.assertTrue(all(D.conditions_met(summary["set1"][s]) for s in (0, 1)))
        self.assertEqual(rt.latch.touched(), [DECISION])
        self.assertFalse(summary["support"])
        self.assertFalse(D.conditions_met(summary["set2"]))

    def test_the_meter_counts_every_phase(self):
        svc, _ = self.service(self.c_good())
        summary, run, rt = self.run_registered(svc)
        self.assertGreater(run.meter.tokens["train"], 0)
        self.assertGreater(run.meter.tokens["prefill"], 0)
        self.assertGreater(run.meter.tokens["sample"], 0)

    def test_the_run_stops_at_the_ceiling_with_nothing_decided(self):
        svc, _ = self.service(self.c_good())
        counter = cost.Counter(rule_only=True)
        run = self.start_run("run-d", self.approvals(ceiling="5.00"), self.plan, counter, svc, fakes.FakeTypes)
        run.meter.ceiling = Fraction(1, 100)
        rt = self.ratchet()
        with self.assertRaises(T.BudgetStop):
            D.run_registered(run, rt, self.codec, "run-d", self.plan, {"cap": CAP}, DECISION)
        self.assertEqual(rt.latch.touched(), [])
        self.assertFalse([b for b in receipts.bodies(rt.receipts_path) if b.get("kind") == "arm_comparison"])


def scripted(pattern):
    """A responder that gives, episode by episode, a passing answer (P), the failed attempt (F) or junk (X)."""
    calls = []

    def respond(view):
        i = len(calls)
        calls.append(i)
        ch = pattern[i % len(pattern)]
        return {"P": RP.recompute, "F": lambda v: v.attempt_text, "X": lambda v: "no answer"}[ch](view)
    return respond


def side(first_only, second_only, first_passed, second_passed, n=100, better=None):
    p = RT.sign_test_p(first_only, second_only)
    return {"first_only": first_only, "second_only": second_only, "first_passed": first_passed,
            "second_passed": second_passed, "n": n,
            "first_better": (first_only > second_only and p <= Fraction(1, 40)) if better is None else better}


def cmp_of(pass_, stratum, fmt_better=False):
    return {"pass": pass_, "stratum": stratum, "format_harm": {"first_better": fmt_better}}


class GateTests(Fixture):
    """The testability gates of the preregistration, with their real values."""

    def test_the_gates_are_the_preregistered_ones(self):
        self.assertEqual(D.GATES, D.Gates(10, Fraction(1, 20), Fraction(19, 20)))

    def test_at_least_ten_discordant_episodes_are_needed(self):
        self.assertFalse(D.testable(side(9, 0, 40, 31)))
        self.assertTrue(D.testable(side(10, 0, 40, 30)))
        self.assertFalse(D.testable(side(4, 5, 40, 41)))
        self.assertTrue(D.testable(side(5, 5, 40, 40)))

    def test_an_adapter_at_five_percent_or_below_or_at_ninety_five_or_above_cannot_test(self):
        self.assertFalse(D.testable(side(20, 0, 25, 5)))        # second adapter at exactly 5 percent
        self.assertTrue(D.testable(side(20, 0, 26, 6)))
        self.assertFalse(D.testable(side(20, 0, 5, 0)))
        self.assertFalse(D.testable(side(20, 0, 95, 75)))       # first adapter at exactly 95 percent
        self.assertTrue(D.testable(side(20, 0, 94, 74)))
        self.assertFalse(D.testable(side(20, 0, 50, 95)))
        self.assertTrue(D.testable(side(20, 0, 50, 94)))
        self.assertFalse(D.testable(side(20, 0, 99, 79)))

    def test_testable_takes_gates_as_an_argument(self):
        relaxed = D.Gates(0, Fraction(-1), Fraction(2))
        self.assertTrue(D.testable(side(1, 0, 100, 0), relaxed))
        self.assertFalse(D.testable(side(1, 0, 100, 0)))

    def good(self):
        return side(30, 0, 60, 30)

    def test_judge_support_needs_every_item(self):
        self.assertEqual(D.judge(cmp_of(self.good(), self.good())), ("support", "every item holds"))
        self.assertTrue(D.conditions_met(cmp_of(self.good(), self.good())))

    def test_judge_each_item_can_fail_in_its_own_way(self):
        tie = side(20, 20, 50, 50)
        self.assertEqual(D.judge(cmp_of(tie, self.good()))[0], "not_supported")
        self.assertIn("all episodes", D.judge(cmp_of(tie, self.good()))[1])
        self.assertEqual(D.judge(cmp_of(self.good(), tie))[0], "not_supported")
        self.assertIn("stratum", D.judge(cmp_of(self.good(), tie))[1])
        verdict, why = D.judge(cmp_of(self.good(), self.good(), fmt_better=True))
        self.assertEqual(verdict, "not_supported")
        self.assertIn("format", why)
        self.assertFalse(D.conditions_met(cmp_of(self.good(), self.good(), fmt_better=True)))

    def test_judge_cannot_test_comes_before_a_verdict_on_that_item(self):
        few = side(7, 0, 40, 33)
        self.assertEqual(D.judge(cmp_of(few, self.good()))[0], "cannot_test")
        self.assertEqual(D.judge(cmp_of(self.good(), few))[0], "cannot_test")
        self.assertIn("stratum", D.judge(cmp_of(self.good(), few))[1])
        self.assertFalse(D.conditions_met(cmp_of(few, few)))

    def test_a_format_harm_is_not_supported_even_when_item_1_or_2_cannot_be_tested(self):
        few = side(7, 0, 40, 33)
        for first, second in ((few, self.good()), (self.good(), few), (few, few)):
            verdict, why = D.judge(cmp_of(first, second, fmt_better=True))
            self.assertEqual(verdict, "not_supported")
            self.assertIn("format", why)
        self.assertEqual(D.judge(cmp_of(few, self.good(), fmt_better=False))[0], "cannot_test")
        self.assertEqual(D.overall_verdict([D.judge(cmp_of(few, few, fmt_better=True))[0]]), "not_supported")

    def test_a_lost_pass_test_is_not_supported_even_if_the_stratum_cannot_be_tested(self):
        self.assertEqual(D.judge(cmp_of(side(20, 20, 50, 50), side(2, 0, 50, 48)))[0], "not_supported")

    def test_judge_takes_gates_as_an_argument(self):
        relaxed = D.Gates(0, Fraction(-1), Fraction(2))
        self.assertEqual(D.judge(cmp_of(side(7, 0, 40, 33), side(7, 0, 40, 33)), relaxed)[0], "support")

    def test_overall_verdict(self):
        self.assertEqual(D.overall_verdict(["support", "support", "support"]), "support")
        self.assertEqual(D.overall_verdict(["support", "not_supported"]), "not_supported")
        self.assertEqual(D.overall_verdict(["cannot_test", "not_supported"]), "not_supported")
        self.assertEqual(D.overall_verdict(["support", "cannot_test"]), "cannot_test")
        self.assertEqual(D.overall_verdict(["cannot_test", "cannot_test"]), "cannot_test")

    def test_control_readings_are_read_from_the_control_comparisons_only(self):
        cmp_ = cmp_of(self.good(), self.good())
        cmp_.update({"control_B": {"first_better": True}, "control_E": {"first_better": False},
                     "control_N": {"first_better": True}})
        self.assertEqual(D.control_readings(cmp_), {"B": True, "E": False, "N": True})
        self.assertEqual(D.control_readings(cmp_of(self.good(), self.good())), {})

    def run_compare(self, c_pattern, b_pattern, e_pattern="F"):
        h1 = E.build_set("heldout1", {"S": 50, "M": 50})
        rt = self.ratchet("gate")
        rt.lock_harness()
        out = {}
        for key, arm, pattern in (("c", "C", c_pattern), ("b", "B", b_pattern), ("e", "E", e_pattern)):
            out[key] = V.evaluate_arm(scripted(pattern), h1, arm, CAP, "adapter:" + key)
            rt.record(out[key], "run", {})
        return D.compare_all(rt, "t", out["c"], out["b"], {"E": out["e"]}), out

    def pattern(self, c_only, b_only, both, c_junk=0, b_junk=0):
        """Per-episode outcomes for C and B as two strings of length 100."""
        c = b = ""
        c += "P" * c_only + "X" * c_junk
        b += "F" * c_only + "F" * c_junk
        c += "F" * b_only
        b += "P" * b_only
        c += "P" * both
        b += "P" * both
        pad = 100 - len(c)
        return c + "F" * pad, b + "F" * pad

    def test_synthetic_results_from_the_reviewers_cases(self):
        # (name, C outcomes, B outcomes, expected verdict)
        P, F, X = "P", "F", "X"
        cases = [
            ("clear support", P * 60 + F * 40, P * 30 + F * 70, "support"),
            ("seven discordant, all for C", P * 40 + F * 60, P * 33 + F * 67, "cannot_test"),
            ("C 98 percent, B 85 percent", P * 98 + F * 2, P * 85 + F * 15, "cannot_test"),
            ("tie", P * 20 + F * 20 + P * 10 + F * 50, F * 20 + P * 20 + P * 10 + F * 50, "not_supported"),
            ("a win over all episodes that the stratum does not show",
             P * 40 + F * 10 + P * 10 + F * 40, X * 40 + P * 10 + P * 10 + F * 40, "not_supported"),
            ("stratum cannot be tested", P * 25 + F * 65 + P * 10, X * 25 + F * 65 + P * 10, "cannot_test"),
            ("format harm", P * 30 + X * 20 + P * 10 + F * 40, F * 50 + P * 10 + F * 40, "not_supported"),
        ]
        for name, c, b, want in cases:
            self.assertEqual((len(c), len(b)), (100, 100), name)
            got, _ = self.run_compare(c, b)
            self.assertEqual(D.judge(got)[0], want, name)

    def test_c_on_e_as_good_as_c_on_c_does_not_change_the_verdict(self):
        got, out = self.run_compare("P" * 60 + "F" * 40, "P" * 30 + "F" * 70, e_pattern="P" * 60 + "F" * 40)
        self.assertEqual(got["control_E"]["first_only"], 0)
        self.assertEqual(D.judge(got)[0], "support")
        self.assertEqual(D.control_readings(got), {"E": False})


class PlanTests(Fixture):
    def test_the_fingerprint_is_stable_and_changes_with_every_field(self):
        base = cost.full_plan(64, 2, CAP, heldout_per_tier=10)
        self.assertEqual(D.plan_fingerprint(base), D.plan_fingerprint(cost.full_plan(64, 2, CAP, heldout_per_tier=10)))
        self.assertEqual(len(D.plan_fingerprint(base)), 64)
        seen = {D.plan_fingerprint(base)}
        for other in (cost.full_plan(64, 1, CAP, heldout_per_tier=10), cost.full_plan(64, 2, CAP - 1, heldout_per_tier=10),
                      cost.full_plan(128, 2, CAP, heldout_per_tier=10), cost.full_plan(64, 2, CAP, heldout_per_tier=11),
                      cost.pilot_plan(CAP), cost.full_plan(64, 2, CAP, heldout_per_tier=10, window=2)):
            seen.add(D.plan_fingerprint(other))
        self.assertEqual(len(seen), 7)
        for field, value in (("window", 3), ("name", "x"), ("arms", ("A",)), ("train_counts", {"S": 1}), ("epochs", 2),
                             ("eval2_counts", {"S": 1}), ("train_offset", 1), ("eval1_offset", 1),
                             ("evals", base.evals[:1]), ("eval1_counts", {"S": 3})):
            p = cost.full_plan(64, 2, CAP, heldout_per_tier=10)
            setattr(p, field, value)
            self.assertNotEqual(D.plan_fingerprint(p), D.plan_fingerprint(base), field)

    def test_start_run_ties_the_run_to_its_plan_and_writes_it_in_the_ledger(self):
        run = self.start_run("run-d", self.approvals(), self.plan, cost.Counter(rule_only=True), fakes.FakeService(),
                          fakes.FakeTypes)
        self.assertEqual(run.plan_id, D.plan_fingerprint(self.plan))
        with open(self.dir + "/approvals.json.spend.jsonl") as fh:
            self.assertEqual(json.loads(fh.readline()), {"ev": "start", "plan_id": run.plan_id, "run_id": "run-d"})

    def test_start_run_restart_needs_resume_and_the_same_plan(self):
        counter = cost.Counter(rule_only=True)
        other = cost.full_plan(64, 2, CAP, heldout_per_tier=11)
        self.start_run("run-d", self.approvals(), self.plan, counter, fakes.FakeService(), fakes.FakeTypes)
        with self.assertRaises(T.ApprovalError):
            self.start_run("run-d", self.approvals(), self.plan, counter, fakes.FakeService(), fakes.FakeTypes)
        with self.assertRaises(T.ApprovalError) as cm:           # approved for the other plan, but not the plan that started
            self.start_run("run-d", self.approvals(plan=other), other, counter, fakes.FakeService(), fakes.FakeTypes,
                           resume=True)
        self.assertIn("different plan", str(cm.exception))
        run = self.start_run("run-d", self.approvals(), self.plan, counter, fakes.FakeService(), fakes.FakeTypes,
                             resume=True)
        self.assertEqual(run.plan_id, D.plan_fingerprint(self.plan))

    def test_start_run_cannot_name_a_ledger(self):
        import inspect
        self.assertNotIn("ledger_path", inspect.signature(D.start_run).parameters)
        self.start_run("run-d", self.approvals(), self.plan, cost.Counter(rule_only=True), fakes.FakeService(),
                       fakes.FakeTypes)
        self.assertTrue(os.path.exists(self.dir + "/approvals.json.spend.jsonl"))

    def test_the_approval_row_names_the_plan_and_its_fingerprint(self):
        row = D.approval_row("run-d", "5.00", self.plan)
        self.assertEqual(row, {"run_id": "run-d", "ceiling_usd": "5.00", "plan": "full",
                               "plan_id": D.plan_fingerprint(self.plan)})

    def test_an_id_approved_for_the_pilot_cannot_start_the_full_plan_and_the_reverse(self):
        counter = cost.Counter(rule_only=True)
        pilot = cost.pilot_plan(CAP)
        full = cost.full_plan(2048, 2, CAP)
        with self.assertRaises(T.ApprovalError):
            self.start_run("pilot-2", self.approvals("pilot-2", ceiling="12.00", plan=pilot), full, counter,
                           fakes.FakeService(), fakes.FakeTypes)
        with self.assertRaises(T.ApprovalError):
            self.start_run("full-1", self.approvals("full-1", ceiling="12.00", plan=full), pilot, counter,
                           fakes.FakeService(), fakes.FakeTypes)
        self.assertFalse(os.path.exists(self.dir + "/approvals.json.spend.jsonl"))     # nothing was started
        self.start_run("pilot-2", self.approvals("pilot-2", ceiling="12.00", plan=pilot), pilot, counter,
                       fakes.FakeService(), fakes.FakeTypes)

    def test_a_run_built_by_hand_with_the_full_plans_fingerprint_is_not_accepted(self):
        full = cost.full_plan(64, 2, CAP, heldout_per_tier=10)
        run = T.TinkerRun("run-d", self.approvals(plan=full), {"train": 1, "prefill": 1, "sample": 1}, full.name,
                          D.plan_fingerprint(full), fakes.FakeService(), fakes.FakeTypes)
        run.close()
        self.assertIsNone(getattr(run, "counted_plan", None))
        with self.assertRaises(D.DriverError) as cm:
            D.require_plan_run(run, full, "full")
        self.assertIn("start_run", str(cm.exception))
        with self.assertRaises(D.DriverError):
            D.run_registered(run, self.ratchet(), self.codec, "run-d", full, {"cap": CAP}, DECISION)
        self.assertEqual(run.meter.spent, 0)

    def test_a_run_whose_plan_id_differs_from_the_plan_given_is_refused_even_if_marked(self):
        other = cost.full_plan(64, 2, CAP, heldout_per_tier=11)
        run = self.start_run("run-d", self.approvals(), self.plan, cost.Counter(rule_only=True), fakes.FakeService(),
                             fakes.FakeTypes)
        run.counted_plan = D.plan_fingerprint(other)          # marked for the other plan, started for this one
        with self.assertRaises(D.DriverError) as cm:
            D.require_plan_run(run, other, "full")
        self.assertIn("different plan", str(cm.exception))

    def test_start_run_marks_the_run_with_the_plan_it_counted(self):
        run = self.start_run("run-d", self.approvals(), self.plan, cost.Counter(rule_only=True), fakes.FakeService(),
                             fakes.FakeTypes)
        self.assertEqual(run.counted_plan, D.plan_fingerprint(self.plan))
        D.require_plan_run(run, self.plan, "full")

    def test_a_live_run_holds_the_lock_and_a_second_start_is_refused(self):
        counter = cost.Counter(rule_only=True)
        first = D.start_run("run-d", self.approvals(), self.plan, counter, fakes.FakeService(), fakes.FakeTypes)
        self.addCleanup(first.close)
        with self.assertRaises(T.ApprovalError) as cm:
            D.start_run("run-d", self.approvals(), self.plan, counter, fakes.FakeService(), fakes.FakeTypes,
                        resume=True)
        self.assertIn("another process", str(cm.exception))

    def test_run_registered_refuses_a_run_started_for_another_plan(self):
        svc, _ = self.service(self.fail1 + self.fail2)
        small = cost.full_plan(64, 2, CAP, heldout_per_tier=5)
        run = self.start_run("run-d", self.approvals(plan=small), small, cost.Counter(rule_only=True), svc, fakes.FakeTypes)
        rt = self.ratchet()
        with self.assertRaises(D.DriverError):
            D.run_registered(run, rt, self.codec, "run-d", self.plan, {"cap": CAP}, DECISION)
        self.assertEqual(svc.clients, [])
        self.assertEqual(run.meter.spent, 0)

    def test_run_registered_refuses_the_pilot_plan_before_any_spend(self):
        svc = fakes.FakeService()
        pilot = cost.pilot_plan(CAP)
        run = self.start_run("run-d", self.approvals(plan=pilot), pilot, cost.Counter(rule_only=True), svc, fakes.FakeTypes)
        with self.assertRaises(D.DriverError) as cm:
            D.run_registered(run, self.ratchet(), self.codec, "run-d", pilot, {"cap": CAP}, DECISION)
        self.assertIn("full", str(cm.exception))
        self.assertEqual((svc.clients, run.meter.spent), ([], 0))

    def test_run_pilot_refuses_the_full_plan_and_another_plans_run(self):
        svc = fakes.FakeService()
        counter = cost.Counter(rule_only=True)
        run = self.start_run("run-d", self.approvals(), self.plan, counter, svc, fakes.FakeTypes)
        with self.assertRaises(D.DriverError):
            D.run_pilot(run, self.ratchet(), self.codec, "run-d", self.plan, {}, self.plan)
        pilot = cost.pilot_plan(CAP)
        with self.assertRaises(D.DriverError):
            D.run_pilot(run, self.ratchet(), self.codec, "run-d", pilot, {}, self.plan)    # run was started for the full plan
        self.assertEqual((svc.clients, run.meter.spent), ([], 0))

    def test_the_full_plan_calls_and_steps(self):
        self.assertEqual(D.plan_calls(cost.full_plan(2048, 2, CAP)), (21000, 384))
        self.assertEqual(D.plan_calls(cost.pilot_plan(CAP)), (200, 8))
        self.assertEqual(D.plan_calls(self.plan), (5 * 20 + 6 * 20 + 6 * 20 + 4 * 20, 3 * 2 * 2))

    def test_the_first_held_out_set_starts_at_the_plans_offset(self):
        plan = cost.full_plan(64, 2, CAP, heldout_per_tier=10)
        plan.eval1_offset = 3
        h1 = E.build_set("heldout1", plan.eval1_counts, 3)
        fails = texts(h1, "attempt")
        enc = self.codec.target_ids
        samplers = [fakes.ScriptedSampler(fails, enc) for _ in range(6)]
        svc = fakes.FakeService(checkpoint_samplers=samplers, base=fakes.ScriptedSampler(fails, enc))
        run = self.start_run("run-d", self.approvals(plan=plan), plan, cost.Counter(rule_only=True), svc, fakes.FakeTypes)
        summary = D.run_registered(run, self.ratchet(), self.codec, "run-d", plan, {"cap": CAP}, DECISION)
        ids = summary["base"]["A"].episode_ids
        self.assertEqual((ids[0], ids[10]), ("heldout1-M-450003", "heldout1-S-400003"))
        self.assertEqual(summary["base"]["A"].set_sha256, h1.sha256())

    def test_the_set_2_bound_covers_four_evaluations_at_the_cap(self):
        h2 = E.build_set("heldout2", {"S": 3, "M": 2})
        bound = D.set2_bound(self.plan, self.codec, h2)
        want = sum(len(self.codec.prompt_ids(E.render(ep, t).messages)) for ep in h2.episodes for t in "CBEN")
        self.assertEqual(bound, {"train": 0, "prefill": want, "sample": 4 * 5 * (CAP + C.REPLY_OVERHEAD)})

    def test_the_remaining_ceiling_must_cover_set_2_before_the_one_touch(self):
        c, b = self.scripts(set(range(15)), {3, 4})
        svc, _ = self.service(c, b_replies=b)
        with mock.patch.object(D, "GATES", D.Gates(0, Fraction(-1), Fraction(2))):
            summary, run, rt = self.run_registered(svc)
            self.assertEqual(summary["verdict"], "support")
            total = run.meter.spent
            self.assertEqual(rt.latch.touched(), [DECISION])
            svc2, _ = self.service(c, b_replies=b)
            counter = cost.Counter(rule_only=True)
            run2 = self.start_run("run-d2", self.approvals("run-d2"), self.plan, counter, svc2, fakes.FakeTypes)
            run2.meter.ceiling = total                  # the set-2 evaluations would reach it
            rt2 = self.ratchet("two")
            with self.assertRaises(T.BudgetStop):
                D.run_registered(run2, rt2, self.codec, "run-d2", self.plan, {"cap": CAP}, DECISION)
            self.assertEqual(rt2.latch.touched(), [])         # the one touch was not spent
            self.assertFalse([b for b in receipts.bodies(rt2.receipts_path) if b.get("set_kind") == "heldout2"])


class VerdictTests(Fixture):
    """run_registered with the real gates, on sets where the rates sit inside them."""

    def test_a_clear_gain_with_rates_inside_the_gates_is_support(self):
        c, b = self.scripts(set(range(16)), {0, 18})          # C 16 of 20 (80 percent), B 2 of 20 (10 percent)
        svc, _ = self.service(c, b_replies=b)
        summary, run, rt = self.run_registered(svc)
        self.assertEqual(summary["verdict"], "support")
        self.assertTrue(summary["support"])
        self.assertEqual(summary["verdicts"], {"set1": {0: "support", 1: "support"}, "set2": "support"})
        self.assertEqual(summary["reasons"]["set2"], "every item holds")
        self.assertEqual(set(summary["interpretive"]), {"set1", "set2"})
        self.assertEqual(summary["interpretive"]["set2"], {"E": True, "N": True})
        self.assertEqual(rt.latch.touched(), [DECISION])

    def test_a_perfect_c_cannot_test_and_the_second_set_is_not_touched(self):
        svc, _ = self.service(self.win1 + self.fail1 * 3 + self.win2 + self.fail2 * 2)
        summary, run, rt = self.run_registered(svc)
        self.assertEqual(summary["verdict"], "cannot_test")
        self.assertFalse(summary["support"])
        self.assertEqual(summary["verdicts"], {"set1": {0: "cannot_test", 1: "cannot_test"}})
        self.assertIsNone(summary["set2"])
        self.assertEqual(rt.latch.touched(), [])

    def test_no_gain_at_all_cannot_test(self):
        svc, _ = self.service(self.fail1 + self.fail2)
        summary, run, rt = self.run_registered(svc)
        self.assertEqual(summary["verdict"], "cannot_test")
        self.assertEqual(summary["interpretive"]["set1"][0], {"B": False, "E": False, "N": False})

    def test_set_1_not_supported_wins_over_cannot_test_and_is_reported(self):
        c, b = self.scripts(set(range(10)), set(range(10, 20)))   # 10 each way, 50 percent each
        svc, _ = self.service(c, b_replies=b)
        summary, run, rt = self.run_registered(svc)
        self.assertEqual(summary["verdicts"]["set1"], {0: "not_supported", 1: "not_supported"})
        self.assertEqual(summary["verdict"], "not_supported")
        self.assertEqual(summary["reasons"]["set1"][0], "C does not beat B on all episodes")

    def test_a_set_2_that_does_not_confirm_is_reported_with_its_own_verdict(self):
        c, b = self.scripts(set(range(16)), {0, 18})
        c = c[:len(c) - 40] + self.fail2 * 2          # C no better than B on set 2 (set 2: own, E, N all failing)
        c = self.mixed(self.win1, self.fail1, set(range(16))) + self.fail1 * 3 + self.fail2 * 3
        svc, _ = self.service(c, b_replies=b)
        summary, run, rt = self.run_registered(svc)
        self.assertEqual(summary["verdicts"]["set1"], {0: "support", 1: "support"})
        self.assertEqual(summary["verdicts"]["set2"], "cannot_test")      # nobody passes: both at the floor
        self.assertEqual(summary["verdict"], "cannot_test")
        self.assertFalse(summary["support"])
        self.assertEqual(rt.latch.touched(), [DECISION])


class PilotTests(Fixture):
    def setUp(self):
        super().setUp()
        self.pilot = cost.pilot_plan(CAP)
        self.eval = E.build_set("train", self.pilot.eval1_counts, self.pilot.eval1_offset)
        self.fails, self.win = texts(self.eval, "attempt"), texts(self.eval, "target")

    def clock(self):
        t = iter(range(0, 10**9, 1000))
        return lambda: next(t)

    def start(self, svc):
        run = self.start_run("pilot-1", self.approvals("pilot-1", plan=self.pilot), self.pilot, cost.Counter(rule_only=True), svc,
                          fakes.FakeTypes)
        return run

    def service_for(self, adapter_texts, base_texts=None):
        enc = self.codec.target_ids
        sampler = fakes.ScriptedSampler(adapter_texts, enc)
        return fakes.FakeService(checkpoint_samplers=[sampler], base=fakes.ScriptedSampler(base_texts or self.fails, enc)), sampler

    def run_it(self, adapter_texts, base_texts=None):
        svc, sampler = self.service_for(adapter_texts, base_texts)
        run = self.start(svc)
        rt = self.ratchet("pilot")
        out = D.run_pilot(run, rt, self.codec, "pilot-1", self.pilot, {"cap": CAP}, cost.full_plan(2048, 2, CAP),
                          clock=self.clock())
        return out, run, rt, svc, sampler

    def test_the_pilot_measures_what_it_gates_on_and_writes_a_receipt(self):
        adapter = self.win[:60] + self.fails[60:]
        out, run, rt, svc, sampler = self.run_it(adapter)
        m = out["measurements"]
        self.assertEqual((m["adapter_n"], m["adapter_passed"], m["adapter_format_broken"]), (100, 60, 0))
        self.assertEqual((m["base_passed"], m["base_format_broken"]), (0, 0))
        self.assertEqual((m["calls"], m["accepted"], m["new_block"], m["steps"]), (200, 200, 0, 8))
        # the clock ticks 1000 on every reading: an evaluation reads it twice for itself and twice for each of its
        # 100 calls, so its wall-clock time is 201 ticks and the waits of its calls are 100 ticks
        self.assertEqual((m["sample_ns"], m["call_wait_ns"], m["train_ns"]), (2 * 201 * 1000, 200 * 1000, 8 * 1000))
        self.assertEqual(m["window"], 1)
        self.assertNotIn("window_check_calls", m)
        self.assertTrue(out["gates"]["go"])
        body = receipts.bodies(rt.receipts_path)[-1]
        self.assertEqual(body, dict({"kind": "pilot", "run_id": "pilot-1", "go": 1}, **m))
        self.assertEqual(sum(c.saved for c in svc.clients), 1)

    def test_the_pilot_uses_the_pilots_training_range_seeds_and_never_a_held_out_set(self):
        out, run, rt, svc, sampler = self.run_it(self.win[:60] + self.fails[60:])
        self.assertEqual((out["results"]["adapter"].set_kind, out["results"]["adapter"].arm, out["results"]["base"].arm),
                         ("train", "C", "C"))
        self.assertEqual(out["results"]["adapter"].episode_ids[0], "train-M-360000")
        self.assertEqual(out["results"]["adapter"].episode_ids[50], "train-S-310000")
        self.assertEqual(out["results"]["base"].set_sha256, self.eval.sha256())
        self.assertEqual(rt.latch.touched(), [])
        self.assertFalse([b for b in receipts.bodies(rt.receipts_path) if str(b.get("set_kind", "")).startswith("heldout")])
        self.assertEqual(svc.created[0]["rank"], 8)
        self.assertEqual(len(sampler.prompts), 100)

    def test_the_pilot_trains_on_its_own_training_range_seeds(self):
        seen = []

        class Spy(fakes.FakeTrainingClient):
            def forward_backward(self, data, loss_fn):
                seen.extend(tuple(d.loss_fn_inputs["target_tokens"]) for d in data)
                return super().forward_backward(data, loss_fn)
        svc, _sampler = self.service_for(self.win[:60] + self.fails[60:])
        svc.create_lora_training_client = lambda **kw: svc.clients.append(Spy(sampler=_sampler)) or fakes.FakeFuture(svc.clients[-1])
        run = self.start(svc)
        D.run_pilot(run, self.ratchet("pilot"), self.codec, "pilot-1", self.pilot, {"cap": CAP},
                    cost.full_plan(2048, 2, CAP), clock=self.clock())
        want = set()
        for ep in E.build_set("train", self.pilot.train_counts, self.pilot.train_offset).episodes:
            r = E.render(ep, "C")
            p, t = self.codec.train_ids(r.messages, r.target_text)
            want.add(tuple((p + t)[1:]))
        self.assertEqual(len(seen), 256)
        self.assertEqual(set(seen), want)
        self.assertEqual(len(want), 256)

    def test_a_pilot_whose_adapter_passes_everything_is_not_a_go(self):
        out, *_ = self.run_it(self.win)
        self.assertFalse(out["gates"]["adapter_pass_rate_testable"])
        self.assertFalse(out["gates"]["go"])

    def test_a_pilot_whose_adapter_breaks_the_format_is_not_a_go(self):
        out, *_ = self.run_it(["no answer"] * 30 + self.win[30:70] + self.fails[70:])
        self.assertEqual(out["measurements"]["adapter_format_broken"], 30)
        self.assertFalse(out["gates"]["format_breaks_low"])
        self.assertFalse(out["gates"]["go"])

    def good_m(self):
        return {"adapter_n": 100, "adapter_passed": 60, "adapter_format_broken": 0, "accepted": 200, "new_block": 0, "calls": 200,
                "sample_ns": 200 * 10**9, "train_ns": 8 * 10**9, "steps": 8}

    def test_the_pilot_gates_at_their_boundaries(self):
        ok = D.pilot_verdict(self.good_m(), 21000, 384)
        self.assertTrue(ok["go"])
        self.assertEqual(set(ok), {"forced_opening_accepted", "no_new_block_in_replies", "format_breaks_low", "adapter_pass_rate_testable",
                                   "projected_time_ok", "go"})
        for field, value, gate in (("accepted", 199, "forced_opening_accepted"), ("new_block", 11, "no_new_block_in_replies"),
                                   ("adapter_format_broken", 21, "format_breaks_low"),
                                   ("adapter_passed", 5, "adapter_pass_rate_testable"),
                                   ("adapter_passed", 95, "adapter_pass_rate_testable")):
            got = D.pilot_verdict(dict(self.good_m(), **{field: value}), 21000, 384)
            self.assertFalse(got[gate], (field, value))
            self.assertFalse(got["go"])
        for field, value, gate in (("accepted", 200, "forced_opening_accepted"), ("new_block", 10, "no_new_block_in_replies"),
                                   ("adapter_format_broken", 20, "format_breaks_low"),
                                   ("adapter_passed", 6, "adapter_pass_rate_testable"),
                                   ("adapter_passed", 94, "adapter_pass_rate_testable")):
            self.assertTrue(D.pilot_verdict(dict(self.good_m(), **{field: value}), 21000, 384)[gate], (field, value))

    def test_the_projected_time_is_calls_and_steps_scaled_to_the_full_plan(self):
        m = dict(self.good_m(), sample_ns=200 * 2 * 10**9, train_ns=8 * 10**9)        # 2 s a call, 1 s a step
        # 21000 calls x 2 s + 384 steps x 1 s = 42384 s = 11.77 hours: under the 12 hours
        self.assertTrue(D.pilot_verdict(m, 21000, 384)["projected_time_ok"])
        self.assertFalse(D.pilot_verdict(m, 21000, 4000)["projected_time_ok"])         # +3616 s: over
        edge = dict(self.good_m(), sample_ns=12 * 3600 * 10**9 * 200 // 20000, train_ns=0)     # exactly 12 hours
        self.assertTrue(D.pilot_verdict(edge, 20000, 384)["projected_time_ok"])
        self.assertFalse(D.pilot_verdict(dict(edge, sample_ns=edge["sample_ns"] + 1), 20000, 384)["projected_time_ok"])


class WindowedPilotTests(Fixture):
    """The pilot of the proposal: a window above 1, timed as whole evaluations, with the window check."""

    def setUp(self):
        super().setUp()
        self.pilot = cost.pilot_plan(CAP, 8)
        self.eval = E.build_set("train", self.pilot.eval1_counts, self.pilot.eval1_offset)
        self.fails, self.win = texts(self.eval, "attempt"), texts(self.eval, "target")

    def clock(self):
        t = iter(range(0, 10**9, 1000))
        return lambda: next(t)

    def run_it(self, base_texts, adapter_texts=None, plan=None):
        plan = plan or self.pilot
        enc = self.codec.target_ids
        adapter = fakes.ScriptedSampler(adapter_texts or (self.win[:60] + self.fails[60:]), enc)
        svc = fakes.FakeService(checkpoint_samplers=[adapter], base=fakes.ScriptedSampler(base_texts, enc))
        run = self.start_run("pilot-w", self.approvals("pilot-w", plan=plan), plan, cost.Counter(rule_only=True), svc,
                             fakes.FakeTypes)
        rt = self.ratchet("pilot")
        out = D.run_pilot(run, rt, self.codec, "pilot-w", plan, {"cap": CAP}, cost.full_plan(2048, 2, CAP, window=8),
                          clock=self.clock())
        return out, run, rt, svc

    def test_the_window_check_samples_the_base_model_again_one_call_at_a_time_and_the_replies_agree(self):
        out, run, rt, svc = self.run_it(self.fails)
        m = out["measurements"]
        self.assertEqual((m["window"], m["window_check_calls"], m["window_check_differing"]), (8, 100, 0))
        self.assertTrue(out["gates"]["windowed_replies_equal"])
        self.assertTrue(out["gates"]["go"])
        self.assertEqual(set(out["results"]), {"base", "base-sequential", "adapter"})
        a, b = out["results"]["base"], out["results"]["base-sequential"]
        self.assertEqual((a.texts, a.cuts, a.outcomes), (b.texts, b.cuts, b.outcomes))
        self.assertEqual((a.descriptor, b.descriptor), ("pilot:base-model", "pilot:base-model-sequential"))
        self.assertEqual(m["calls"], 200)                  # the two measured evaluations only, not the check
        bodies = receipts.bodies(rt.receipts_path)
        self.assertEqual([x.get("descriptor") for x in bodies if x["kind"] == "eval"],
                         ["pilot:base-model", "pilot:base-model-sequential", "pilot:adapter:C"])
        self.assertEqual(bodies[-1], dict({"kind": "pilot", "run_id": "pilot-w", "go": 1}, **m))

    def test_replies_that_differ_between_the_two_ways_are_counted_and_are_not_a_go(self):
        # the second evaluation of the base model sees other replies than the first on every puzzle
        out, *_ = self.run_it(self.fails + self.win)
        m = out["measurements"]
        self.assertEqual((m["window_check_calls"], m["window_check_differing"]), (100, 100))
        self.assertFalse(out["gates"]["windowed_replies_equal"])
        self.assertFalse(out["gates"]["go"])
        self.assertTrue(out["gates"]["forced_opening_accepted"])

    def test_one_differing_reply_is_enough_to_fail_the_check(self):
        other = list(self.fails)
        other[41] = self.win[41]
        out, *_ = self.run_it(self.fails + other)
        self.assertEqual(out["measurements"]["window_check_differing"], 1)
        self.assertFalse(out["gates"]["windowed_replies_equal"])

    def test_a_difference_in_the_cut_flag_alone_fails_the_check(self):
        # the same text after the cut, but one reply was cut at the cap and the other was not
        exact = ("x0 = 1\n" * 20)[:CAP]             # exactly the cap in pieces (one per character with the fake tokenizer)
        first = list(self.fails)
        first[7] = exact
        second = list(first)
        second[7] = exact + "x"                      # one piece over the cap: cut back to the same text
        out, *_ = self.run_it(first + second)
        a, b = out["results"]["base"], out["results"]["base-sequential"]
        self.assertEqual(a.texts, b.texts)
        self.assertNotEqual(a.cuts, b.cuts)
        self.assertEqual(out["measurements"]["window_check_differing"], 1)
        self.assertFalse(out["gates"]["windowed_replies_equal"])

    def test_the_measured_evaluations_use_the_window_and_the_check_sends_one_call_at_a_time(self):
        seen = []
        enc = self.codec.target_ids

        class Spy(fakes.WindowSampler):
            def sample(spy, *a, **kw):
                seen.append(spy.outstanding)
                return super().sample(*a, **kw)
        mapping = {}
        for v, text in zip(D.epset_views(self.eval, "C"), self.fails):
            mapping[tuple(self.codec.prompt_ids(v.messages))] = enc(text)
        base = Spy(reply_for=lambda toks: mapping[tuple(toks)])
        mixed = self.win[:60] + self.fails[60:]
        amap = {}
        for v, text in zip(D.epset_views(self.eval, "C"), mixed):
            amap[tuple(self.codec.prompt_ids(v.messages))] = enc(text)
        adapter = fakes.WindowSampler(reply_for=lambda toks: amap[tuple(toks)])
        svc = fakes.FakeService(checkpoint_samplers=[adapter], base=base)
        run = self.start_run("pilot-w", self.approvals("pilot-w", plan=self.pilot), self.pilot,
                             cost.Counter(rule_only=True), svc, fakes.FakeTypes)
        D.run_pilot(run, self.ratchet("pilot"), self.codec, "pilot-w", self.pilot, {"cap": CAP},
                    cost.full_plan(2048, 2, CAP, window=8), clock=self.clock())
        self.assertEqual(len(seen), 200)
        self.assertEqual(max(seen[:100]), 7)                  # the windowed evaluation: 8 in flight at the eighth send
        self.assertEqual(max(seen[100:]), 0)                  # the check: each call is sent after the one before is back
        self.assertEqual(base.max_in_flight, 8)
        self.assertEqual((len(adapter.calls), adapter.max_in_flight), (100, 8))       # the adapter too is sampled at the window

    def test_replies_of_other_puzzles_or_another_length_are_all_different(self):
        class R:
            def __init__(self, ids, texts, cuts):
                self.episode_ids, self.texts, self.cuts = ids, texts, cuts
        a = R(["e1", "e2", "e3"], ["a", "b", "c"], "000")
        self.assertEqual(D.differing_replies(a, R(["e1", "e2", "e3"], ["a", "b", "c"], "000")), 0)
        self.assertEqual(D.differing_replies(a, R(["e1", "e2", "e3"], ["a", "x", "c"], "000")), 1)
        self.assertEqual(D.differing_replies(a, R(["e1", "e2", "e3"], ["a", "b", "c"], "010")), 1)
        self.assertEqual(D.differing_replies(a, R(["e1", "e2", "e9"], ["a", "b", "c"], "000")), 3)      # another puzzle
        self.assertEqual(D.differing_replies(a, R(["e1", "e2"], ["a", "b"], "00")), 3)

    def test_the_time_is_the_wall_clock_of_each_evaluation_as_a_whole(self):
        out, *_ = self.run_it(self.fails)
        m = out["measurements"]
        # every clock reading is 1000 ns on: an evaluation reads the clock twice for itself and twice for each of its
        # 100 calls. Its wall-clock time is 201 readings' worth, and the check is not part of the sampling time.
        self.assertEqual(m["sample_ns"], 2 * 201 * 1000)
        self.assertEqual(m["window_check_ns"], 201 * 1000)
        self.assertEqual(m["call_wait_ns"], 200 * 1000)
        self.assertNotEqual(m["sample_ns"], m["call_wait_ns"])
        self.assertEqual(m["train_ns"], 8 * 1000)
        edge = D.pilot_verdict(dict(m, sample_ns=12 * 3600 * 10**9 * 200 // 21000, train_ns=0), 21000, 384)
        self.assertTrue(edge["projected_time_ok"])

    def test_the_projection_divides_the_whole_evaluation_time_by_its_calls(self):
        m = {"adapter_n": 100, "adapter_passed": 60, "adapter_format_broken": 0, "accepted": 200, "new_block": 0,
             "calls": 200, "sample_ns": 200 * 10**9, "train_ns": 8 * 10**9, "steps": 8,
             "window_check_calls": 100, "window_check_differing": 0}
        got = D.pilot_verdict(m, 21000, 384)
        self.assertTrue(got["windowed_replies_equal"])
        self.assertEqual(set(got), {"forced_opening_accepted", "no_new_block_in_replies", "format_breaks_low",
                                    "adapter_pass_rate_testable", "projected_time_ok", "windowed_replies_equal", "go"})
        self.assertTrue(got["projected_time_ok"])                                  # 1 s a call: 21000 s plus 384 s
        slower = D.pilot_verdict(dict(m, sample_ns=200 * 2 * 10**9), 21000, 384)
        self.assertTrue(slower["projected_time_ok"])                               # 2 s a call: 11.77 hours
        self.assertFalse(D.pilot_verdict(dict(m, sample_ns=200 * 3 * 10**9), 21000, 384)["projected_time_ok"])
        for field, value in (("window_check_calls", 99), ("window_check_differing", 1)):
            bad = D.pilot_verdict(dict(m, **{field: value}), 21000, 384)
            self.assertFalse(bad["windowed_replies_equal"], field)
            self.assertFalse(bad["go"], field)

    def test_a_window_of_one_has_no_window_check_and_no_such_gate(self):
        plan = cost.pilot_plan(CAP, 1)
        out, run, rt, svc = self.run_it(self.fails, plan=plan)
        self.assertNotIn("windowed_replies_equal", out["gates"])
        self.assertEqual(set(out["results"]), {"base", "adapter"})
        self.assertEqual(out["measurements"]["window"], 1)

    def test_the_pilot_plan_refuses_to_run_under_another_window(self):
        enc = self.codec.target_ids
        svc = fakes.FakeService(base=fakes.ScriptedSampler(self.fails, enc))
        approvals = self.approvals("pilot-w", plan=cost.pilot_plan(CAP, 8))
        with self.assertRaises(T.ApprovalError):
            self.start_run("pilot-w", approvals, cost.pilot_plan(CAP, 4), cost.Counter(rule_only=True), svc, fakes.FakeTypes)


class TimingTests(Fixture):
    def test_train_arm_records_each_step_time(self):
        svc = fakes.FakeService()
        run = self.start_run("run-d", self.approvals(), self.plan, cost.Counter(rule_only=True), svc, fakes.FakeTypes)
        ticks = iter(range(0, 10**9, 7))
        steps = []
        D.train_arm(run, "C-s0", self.codec, E.build_set("train", {"S": 32, "M": 32}), "C", 0, step_ns=steps,
                    clock=lambda: next(ticks))
        self.assertEqual(steps, [7, 7])

    def test_train_arm_without_a_list_records_nothing(self):
        svc = fakes.FakeService()
        run = self.start_run("run-d", self.approvals(), self.plan, cost.Counter(rule_only=True), svc, fakes.FakeTypes)
        self.assertEqual(D.train_arm(run, "C-s0", self.codec, E.build_set("train", {"S": 32}), "C", 0), 1)

    def test_a_timed_responder_passes_the_reply_through_and_records_each_call(self):
        ticks = iter([0, 5, 100, 130])
        timed = D.TimedResponder(lambda view: ("x0 = 1", 3), clock=lambda: next(ticks))
        self.assertEqual(timed(None), ("x0 = 1", 3))
        self.assertEqual(timed(None), ("x0 = 1", 3))
        self.assertEqual(timed.call_ns, [5, 30])


if __name__ == "__main__":
    unittest.main()
