"""Windowed sampling: the window is respected, replies do not depend on the window or on the order
the service answers in, a window of 1 is the sequential path, and the ledger holds a reservation for
every call in flight whatever goes wrong."""
import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction

import _setup  # noqa: F401
import codec as C
import cost
import driver as D
import episodes as E
import evaluate as V
import fakes
import ratchet as RT
import tinker_backend as T

CAP = 96
PID = "plan-fingerprint-window"
LIMIT = CAP + 1                       # the reply and the end marker: what a call reserves for sampling
PLAN_TOKENS = {"train": 100000, "prefill": 10000, "sample": 10000}

LATENCIES = {
    "constant": lambda i: 5,
    "later answers first": lambda i: 1000 - i,
    "scrambled": lambda i: (i * 7) % 5 * 10 + i,
}


def setup_codec_and_views(n_per_tier=6):
    codec = C.Codec(fakes.FakeTokenizer())
    epset = E.build_set("train", {"S": n_per_tier, "M": n_per_tier})
    views = D.epset_views(epset, "C")
    replies = {}
    for i, ep in enumerate(epset.episodes):
        r = E.render(ep, "A")
        text = r.target_text if i % 2 == 0 else r.attempt_text
        replies[tuple(codec.prompt_ids(views[i].messages))] = codec.target_ids(text)
    return codec, epset, views, replies


class Env:
    """A fresh approvals file, ledger and run on a fake service whose one sampler is the given one."""

    def __init__(self, case, sampler, ceiling="5.00", plan_tokens=None):
        self.tmp = tempfile.TemporaryDirectory()
        case.addCleanup(self.tmp.cleanup)
        self.dir = self.tmp.name
        self.approvals = os.path.join(self.dir, "approvals.json")
        with open(self.approvals, "w") as fh:
            json.dump({"approvals": [{"run_id": "run-w", "ceiling_usd": ceiling, "plan": "test", "plan_id": PID}]}, fh)
        self.sampler = sampler
        self.run = T.TinkerRun("run-w", self.approvals, plan_tokens or PLAN_TOKENS, "test", PID,
                               fakes.FakeService(base=sampler), fakes.FakeTypes)
        case.addCleanup(self.run.close)
        self.ledger_path = self.approvals + ".spend.jsonl"

    def rows(self):
        with open(self.ledger_path, "rb") as fh:
            return [json.loads(line) for line in fh.read().split(b"\n")[:-1]]

    def count(self, ev, kind):
        return sum(1 for r in self.rows() if r["ev"] == ev and r["kind"] == kind and r["run_id"] == "run-w")

    def tokens(self):
        return T.Ledger(self.ledger_path, "run-w").replay()[1]


def drive(resp, views, upto=None):
    out = []
    for v in views[:upto]:
        out.append(resp(v))
    return out


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.codec, self.epset, self.views, self.replies = setup_codec_and_views()
        self.n = len(self.views)
        self.reply_for = lambda toks: self.replies[tuple(toks)]
        self.ids = [self.codec.prompt_ids(v.messages) for v in self.views]
        self.actual = [len(self.replies[tuple(i)]) for i in self.ids]

    def sampler(self, **kw):
        return fakes.WindowSampler(reply_for=self.reply_for, **kw)

    def responder(self, env, window, cap=CAP):
        return T.WindowedResponder(env.run, env.sampler, self.codec, cap, self.views, window)

    # ---------------------------------------------------------------- the window and the order

    def test_the_window_is_respected_and_replies_do_not_depend_on_the_window_or_on_the_order_of_answers(self):
        baseline = None
        for window in (1, 2, 3, 5, 12, 20):
            for name, latency in LATENCIES.items():
                env = Env(self, self.sampler(latency=latency))
                resp = self.responder(env, window)
                got = drive(resp, self.views)
                label = (window, name)
                self.assertLessEqual(env.sampler.max_in_flight, window, label)
                self.assertEqual(env.sampler.max_in_flight, min(window, self.n), label)
                self.assertEqual(resp.max_in_flight, env.sampler.max_in_flight, label)
                self.assertEqual(env.sampler.prompts, self.ids, label)          # sent in episode order
                self.assertEqual(env.sampler.outstanding, 0, label)
                if baseline is None:
                    baseline = (got, env.tokens(), env.run.meter.spent)
                self.assertEqual(got, baseline[0], label)                       # the replies
                self.assertEqual(env.tokens(), baseline[1], label)              # and what they cost
                self.assertEqual(env.run.meter.spent, baseline[2], label)

    def test_a_window_above_one_really_is_answered_out_of_order(self):
        env = Env(self, self.sampler(latency=LATENCIES["later answers first"]))
        drive(self.responder(env, 5), self.views, 1)
        self.assertEqual(env.sampler.answered_order, [4, 3, 2, 1, 0])
        got_order = []
        env2 = Env(self, self.sampler(latency=LATENCIES["later answers first"]))
        resp = self.responder(env2, 5)
        for v in self.views:
            resp(v)
            got_order.append(resp.delivered - 1)
        self.assertEqual(got_order, list(range(self.n)))                        # but handed back in order

    def test_replies_come_back_in_episode_order_even_when_the_service_answers_in_reverse(self):
        env = Env(self, self.sampler(latency=LATENCIES["later answers first"]))
        got = drive(self.responder(env, 4), self.views)
        want = [self.codec.reply(self.replies[tuple(i)], CAP) for i in self.ids]
        self.assertEqual(got, want)

    # ---------------------------------------------------------------- a window of 1 is the sequential path

    def evaluation(self, windowed, window=1, sampler_kw=None):
        sampler = self.sampler(**(sampler_kw or {}))
        env = Env(self, sampler)
        rt = RT.Ratchet(os.path.join(env.dir, "r.jsonl"), os.path.join(env.dir, "l.jsonl"),
                        os.path.join(env.dir, "lock.json"), CAP)
        rt.lock_harness()
        base = env.run.base_sampler()
        if windowed:
            result = D.evaluate_recorded(rt, env.run, base, self.codec, self.epset, "C", "pilot:base-model", "run-w",
                                         {"cap": CAP}, window)
        else:
            model = env.run.binding(base)
            rt.require_model(model, "pilot:base-model")
            result = V.evaluate_arm(D.responder(env.run, base, self.codec, CAP), self.epset, "C", CAP,
                                    "pilot:base-model")
            rt.record(result, "run-w", {"cap": CAP}, model)
        with open(rt.receipts_path, "rb") as fh:
            raw = fh.read()
        return env.rows(), raw, result, sampler

    def test_a_window_of_one_reproduces_the_sequential_path_row_for_row(self):
        for kw in (None, {"latency": LATENCIES["later answers first"]}):
            seq_rows, seq_receipts, seq, seq_sampler = self.evaluation(False, sampler_kw=kw)
            win_rows, win_receipts, win, win_sampler = self.evaluation(True, 1, kw)
            self.assertEqual(win_rows, seq_rows)                    # every ledger row, in order
            self.assertEqual(win_receipts, seq_receipts)            # the receipt chain, byte for byte
            self.assertEqual((win.texts, win.cuts, win.outcomes, win.replies_sha256),
                             (seq.texts, seq.cuts, seq.outcomes, seq.replies_sha256))
            self.assertEqual((win_sampler.calls, win_sampler.prompts, win_sampler.stops),
                             (seq_sampler.calls, seq_sampler.prompts, seq_sampler.stops))
            self.assertGreater(len(seq_rows), 3 * self.n)

    def test_the_responders_stats_and_last_reply_of_a_window_of_one_are_the_sequential_ones(self):
        seq_env = Env(self, self.sampler())
        seq = T.TinkerResponder(seq_env.run, seq_env.sampler, self.codec, CAP)
        win_env = Env(self, self.sampler())
        win = self.responder(win_env, 1)
        for v in self.views:
            self.assertEqual(win(v), seq(v))
            self.assertEqual((win.last_returned, win.reached), (seq.last_returned, seq.reached))
        self.assertEqual(win.stats, seq.stats)
        self.assertEqual(win_env.rows(), seq_env.rows())

    def test_what_an_evaluation_records_does_not_depend_on_the_window_or_the_answer_order(self):
        base = self.evaluation(True, 1)
        for window in (2, 3, 8, 12):
            for name, latency in LATENCIES.items():
                rows, raw, result, sampler = self.evaluation(True, window, {"latency": latency})
                label = (window, name)
                self.assertEqual((result.texts, result.cuts, result.outcomes, result.replies_sha256),
                                 (base[2].texts, base[2].cuts, base[2].outcomes, base[2].replies_sha256), label)
                self.assertEqual(raw, base[1], label)
                self.assertEqual(sampler.max_in_flight, min(window, self.n))      # the driver's window is used
                self.assertEqual(sorted(r["tokens"] for r in rows if r["ev"] == "reserve"),
                                 sorted(r["tokens"] for r in base[0] if r["ev"] == "reserve"))

    # ---------------------------------------------------------------- every call is reserved before it is sent

    def test_every_call_in_flight_has_its_reservation_in_the_ledger_when_it_is_sent(self):
        seen = []

        class Spy(fakes.WindowSampler):
            def sample(spy, prompt, *a, **kw):
                rows = env.rows()
                reserves = sum(1 for r in rows if r["ev"] == "reserve" and r["kind"] == "sample")
                adjusts = sum(1 for r in rows if r["ev"] == "adjust" and r["kind"] == "sample")
                pre = sum(1 for r in rows if r["ev"] == "reserve" and r["kind"] == "prefill")
                seen.append((reserves, adjusts, pre, spy.outstanding, len(spy.calls)))
                return super().sample(prompt, *a, **kw)
        env = Env(self, Spy(reply_for=self.reply_for, latency=LATENCIES["later answers first"]))
        drive(self.responder(env, 4), self.views)
        self.assertEqual(len(seen), self.n)
        for k, (reserves, adjusts, pre, outstanding, calls) in enumerate(seen):
            self.assertEqual((reserves, pre, calls), (k + 1, k + 1, k), k)       # this call is reserved before it is sent
            self.assertEqual(reserves - adjusts, outstanding + 1, k)             # one open reservation per call in flight
        self.assertEqual(env.count("reserve", "sample"), env.count("adjust", "sample"))

    def test_the_ceiling_check_counts_every_reservation_in_flight(self):
        costs = [T.cost_usd("prefill", len(ids)) + T.cost_usd("sample", LIMIT) for ids in self.ids]
        ceiling = sum(costs[:3]) + T.cost_usd("prefill", len(self.ids[3])) / 2    # room for 3 calls in flight, not 4
        env = Env(self, self.sampler(), ceiling=str(ceiling), plan_tokens={"train": 1, "prefill": 1, "sample": 1})
        resp = self.responder(env, 8)
        with self.assertRaises(T.BudgetStop) as cm:
            resp(self.views[0])
        self.assertIn("would reach the ceiling", str(cm.exception))
        self.assertEqual(len(env.sampler.calls), 3)                              # three were sent, the fourth never
        self.assertEqual(env.sampler.outstanding, 0)                             # and all three were awaited
        tokens = env.tokens()
        self.assertEqual(tokens["prefill"], sum(len(ids) for ids in self.ids[:3]))
        self.assertEqual(tokens["sample"], sum(self.actual[:3]))                  # settled to what they used
        self.assertEqual(env.count("reserve", "sample"), env.count("adjust", "sample"))
        self.assertLess(env.run.meter.spent, Fraction(ceiling))

    # ---------------------------------------------------------------- failures in the middle of a window

    def test_a_failure_in_the_middle_of_a_window_settles_the_calls_already_sent_before_it_is_raised(self):
        env = Env(self, self.sampler(fail_result=[3]))
        resp = self.responder(env, 6)
        got = []
        with self.assertRaises(T.BackendError) as cm:
            for v in self.views:
                got.append(resp(v))
        self.assertEqual(len(got), 3)
        self.assertIn("fake service: the call failed", str(cm.exception))
        # the window refills as replies are handed back, so when call 3 failed, calls 0 to 8 had been sent
        self.assertEqual(len(env.sampler.calls), 9)
        self.assertEqual(env.sampler.outstanding, 0)                             # and every one was awaited
        self.assertEqual((env.count("reserve", "sample"), env.count("adjust", "sample")), (9, 8))
        want = sum(self.actual[i] for i in range(9) if i != 3) + LIMIT           # the failed call keeps its full reservation
        self.assertEqual(env.tokens()["sample"], want)
        self.assertEqual([o["index"] for o in resp.orphans], [4, 5, 6, 7, 8])
        self.assertEqual((resp.last_returned, resp.reached), (None, True))
        self.assertEqual(resp.stats["calls"], 3)
        with self.assertRaises(T.BackendError):                                  # a stopped responder sends nothing more
            resp(self.views[3])
        self.assertEqual(len(env.sampler.calls), 9)

    def test_a_send_that_fails_in_the_middle_of_a_window_settles_the_calls_already_sent(self):
        env = Env(self, self.sampler(fail_send=[4]))
        resp = self.responder(env, 8)
        with self.assertRaises(T.BackendError):
            resp(self.views[0])
        self.assertEqual(len(env.sampler.calls), 4)
        self.assertEqual(env.sampler.outstanding, 0)
        self.assertEqual((env.count("reserve", "sample"), env.count("adjust", "sample")), (5, 4))
        self.assertEqual(env.tokens()["sample"], sum(self.actual[:4]) + LIMIT)   # the unsent call stays reserved
        self.assertEqual(env.count("reserve", "prefill"), 5)
        # the head (call 0) came back whole and was not handed back because the look-ahead send failed:
        # it is an orphan, paid for, and is not reported as a call that raised
        self.assertEqual(sorted(o["index"] for o in resp.orphans), [0, 1, 2, 3])
        self.assertEqual([o["returned"] for o in resp.orphans if o["index"] == 0], [[self.replies[tuple(self.ids[0])]]])
        self.assertEqual((resp.last_returned, resp.reached), (None, False))
        self.assertEqual(resp.failed_send, 4)                                    # the send that failed has no reply to log

    def test_a_head_whose_own_call_failed_stays_a_failed_call_when_a_look_ahead_send_fails_too(self):
        env = Env(self, self.sampler(fail_result=[1], fail_send=[4]))
        resp = self.responder(env, 4)
        with self.assertRaises(T.BackendError) as cm:
            drive(resp, self.views)
        self.assertIn("could not be sent", str(cm.exception))                     # the error that stopped the run, first
        self.assertEqual(resp.failed_send, 4)
        self.assertEqual(sorted(o["index"] for o in resp.orphans), [2, 3])         # the head is not an orphan: it raised
        self.assertEqual((resp.last_returned, resp.reached), (None, True))
        self.assertEqual(env.sampler.outstanding, 0)

    def test_a_head_that_came_back_oversize_stays_a_failed_call_when_a_look_ahead_send_fails_too(self):
        env = Env(self, self.sampler(oversize=[1], fail_send=[4]))
        resp = self.responder(env, 4)
        with self.assertRaises(T.BackendError) as cm:
            drive(resp, self.views)
        self.assertIn("could not be sent", str(cm.exception))
        self.assertEqual(sorted(o["index"] for o in resp.orphans), [2, 3])
        padded = self.replies[tuple(self.ids[1])] + [7] * (LIMIT + 1 - self.actual[1])
        self.assertEqual((resp.last_returned, resp.reached), ([padded], True))      # its ids were paid for, and kept
        self.assertEqual(env.tokens()["sample"], self.actual[0] + (LIMIT + 1) + self.actual[2] + self.actual[3] + LIMIT)   # the unsent call 4 keeps its limit

    def test_a_head_whose_own_send_failed_is_not_also_a_failed_look_ahead(self):
        env = Env(self, self.sampler(fail_send=[0]))
        resp = self.responder(env, 4)
        with self.assertRaises(T.BackendError):
            resp(self.views[0])
        self.assertIsNone(resp.failed_send)
        self.assertEqual((resp.last_returned, resp.reached, resp.orphans), (None, True, []))

    def test_a_reply_over_its_limit_stops_the_run_after_the_calls_in_flight_are_settled(self):
        for window in (1, 4, 8):
            for bad in (0, 2, 7):
                env = Env(self, self.sampler(oversize=[bad]))
                resp = self.responder(env, window)
                label = (window, bad)
                got = []
                with self.assertRaises(T.BudgetStop) as cm:
                    for v in self.views:
                        got.append(resp(v))
                self.assertIn("more than the", str(cm.exception), label)
                self.assertEqual(len(got), bad, label)
                sent = len(env.sampler.calls)
                self.assertEqual(sent, min(self.n, bad + window), label)          # nothing is sent after the bad reply is read
                self.assertEqual(env.sampler.outstanding, 0, label)               # everything sent was awaited
                self.assertEqual((env.count("reserve", "sample"), env.count("adjust", "sample")), (sent, sent), label)
                actual = [LIMIT + 1 if i == bad else self.actual[i] for i in range(sent)]
                self.assertEqual(env.tokens()["sample"], sum(actual), label)      # the excess is counted in full
                self.assertEqual(env.run.meter.tokens["sample"], sum(actual), label)

    def test_the_first_error_is_the_one_raised_when_calls_in_flight_fail_too(self):
        env = Env(self, self.sampler(fail_result=[2], oversize=[4]))
        resp = self.responder(env, 6)
        with self.assertRaises(T.BackendError) as cm:                              # not the BudgetStop of call 4
            drive(resp, self.views)
        self.assertIn("the call failed", str(cm.exception))
        self.assertEqual(env.sampler.outstanding, 0)
        self.assertEqual(env.tokens()["sample"], sum(self.actual[i] for i in (0, 1, 3, 5, 6, 7)) + LIMIT + LIMIT + 1)

    def test_a_responder_that_stops_leaves_no_call_pending(self):
        for fail in ({"fail_result": [3]}, {"oversize": [3]}, {"fail_send": [5]}):
            env = Env(self, self.sampler(**fail))
            resp = self.responder(env, 4)
            with self.assertRaises((T.BackendError, T.BudgetStop)):
                drive(resp, self.views)
            self.assertEqual((len(resp.pending), resp.stopped, env.sampler.outstanding), (0, True, 0), fail)

    def test_an_answer_with_two_sequences_for_one_sample_is_refused_and_the_window_is_settled(self):
        # replies of 2 ids, so that both sequences together stay under the limit of 97
        env = Env(self, fakes.WindowSampler(reply_for=lambda toks: [1, 2], two_sequences=[1]))
        resp = self.responder(env, 4)
        with self.assertRaises(T.BackendError) as cm:
            drive(resp, self.views)
        self.assertIn("returned 2 sequences", str(cm.exception))
        self.assertEqual(env.sampler.outstanding, 0)
        self.assertEqual(resp.stats["calls"], 1)
        # every returned token is billed: call 1 held two sequences of 2 ids, and the other calls 2 ids each
        self.assertEqual(env.tokens()["sample"], 2 * 5 + 2)

    def test_two_sequences_that_together_pass_the_limit_are_counted_in_full_whether_or_not_each_does(self):
        # a normal reply of the puzzle (about 54 ids) twice is over the limit of 97 though each sequence is under it
        for window in (1, 4):
            env = Env(self, self.sampler(two_sequences=[1]))
            resp = self.responder(env, window)
            with self.assertRaises(T.BudgetStop):
                drive(resp, self.views)
            sent = len(env.sampler.calls)
            want = sum(self.actual[i] * (2 if i == 1 else 1) for i in range(sent))
            self.assertEqual(env.tokens()["sample"], want, window)                  # the ledger holds every returned token
            self.assertEqual((env.count("reserve", "sample"), env.count("adjust", "sample")), (sent, sent), window)
            self.assertEqual(env.sampler.outstanding, 0, window)

    def test_the_sequential_responder_settles_a_wrong_sequence_count_against_every_returned_token(self):
        for toks, error in (([1, 2], T.BackendError), ([5] * 60, T.BudgetStop)):
            sampler = fakes.FakeSampler(reply_tokens=toks)
            orig = sampler.sample

            def two(*a, _orig=orig, **kw):
                fut = _orig(*a, **kw)
                fut._value.sequences = fut._value.sequences * 2
                return fut
            sampler.sample = two
            env = Env(self, sampler)
            with self.assertRaises(error):
                T.TinkerResponder(env.run, sampler, self.codec, CAP)(self.views[0])
            self.assertEqual(env.tokens()["sample"], 2 * len(toks))                  # not one limit held and one sequence counted

    def test_the_stats_of_a_window_count_new_blocks_and_cut_replies_as_the_sequential_responder_does(self):
        replies = dict(self.replies)
        marker = self.codec.thinking
        replies[tuple(self.ids[2])] = [ord("x"), marker, ord("y")] + self.codec.target_ids("z")        # opens a block of its own
        replies[tuple(self.ids[4])] = [ord("a")] * (CAP + 1) + [self.codec.end]                         # longer than the cap
        reply_for = lambda toks: replies[tuple(toks)]
        seq_env = Env(self, fakes.WindowSampler(reply_for=reply_for))
        seq = T.TinkerResponder(seq_env.run, seq_env.sampler, self.codec, CAP)
        win_env = Env(self, fakes.WindowSampler(reply_for=reply_for, latency=LATENCIES["later answers first"]))
        win = self.responder(win_env, 5)
        for v in self.views:
            self.assertEqual(win(v), seq(v))
        self.assertEqual(win.stats, seq.stats)
        self.assertEqual(win.stats, {"calls": self.n, "accepted": self.n, "new_block": 1, "cut": 1})

    # ---------------------------------------------------------------- the asked-for views, and finishing

    def test_a_view_that_is_not_the_next_planned_episode_is_refused_and_the_calls_in_flight_are_settled(self):
        env = Env(self, self.sampler())
        resp = self.responder(env, 5)
        resp(self.views[0])
        resp(self.views[1])
        with self.assertRaises(T.BackendError) as cm:
            resp(self.views[5])
        self.assertIn("not the next planned episode", str(cm.exception))
        self.assertEqual(env.sampler.outstanding, 0)
        self.assertEqual(env.count("reserve", "sample"), env.count("adjust", "sample"))
        env2 = Env(self, self.sampler())
        resp2 = self.responder(env2, 5)
        with self.assertRaises(T.BackendError):
            resp2(self.views[1])
        self.assertEqual(env2.sampler.calls, [])                                  # refused before anything was sent

    def test_a_view_of_another_text_is_refused(self):
        env = Env(self, self.sampler())
        resp = self.responder(env, 3)
        other = D.epset_views(self.epset, "B")[0]
        with self.assertRaises(T.BackendError):
            resp(other)
        self.assertEqual(env.sampler.calls, [])

    def test_more_replies_than_episodes_are_refused(self):
        env = Env(self, self.sampler())
        resp = self.responder(env, 3)
        drive(resp, self.views)
        with self.assertRaises(T.BackendError):
            resp(self.views[0])
        self.assertEqual(len(env.sampler.calls), self.n)

    def test_finish_settles_the_calls_still_in_flight_and_stops_the_responder(self):
        env = Env(self, self.sampler())
        resp = self.responder(env, 5)
        drive(resp, self.views, 2)
        self.assertEqual(env.sampler.outstanding, 4)                             # the window refills at the next request
        self.assertEqual(env.count("reserve", "sample") - env.count("adjust", "sample"), 4)
        resp.finish()
        self.assertEqual(env.sampler.outstanding, 0)
        self.assertEqual(env.count("reserve", "sample"), env.count("adjust", "sample"))
        with self.assertRaises(T.BackendError):
            resp(self.views[2])
        resp.finish()                                                            # a second finish does nothing

    def test_finish_raises_an_oversize_reply_that_was_still_in_flight(self):
        env = Env(self, self.sampler(oversize=[3]))
        resp = self.responder(env, 5)
        drive(resp, self.views, 2)
        with self.assertRaises(T.BudgetStop):
            resp.finish()
        self.assertEqual(env.sampler.outstanding, 0)

    def test_the_driver_settles_the_calls_in_flight_when_an_evaluation_stops_early(self):
        sampler = self.sampler()
        env = Env(self, sampler)
        rt = RT.Ratchet(os.path.join(env.dir, "r.jsonl"), os.path.join(env.dir, "l.jsonl"),
                        os.path.join(env.dir, "lock.json"), CAP)
        rt.lock_harness()
        base = env.run.base_sampler()
        real = V.evaluate_arm

        def stop_after_two(resp, *a, **kw):
            resp(self.views[0])
            resp(self.views[1])
            raise RuntimeError("the evaluation stops here")
        V.evaluate_arm = stop_after_two
        self.addCleanup(setattr, V, "evaluate_arm", real)
        with self.assertRaises(RuntimeError):
            D.evaluate_recorded(rt, env.run, base, self.codec, self.epset, "C", "pilot:base-model", "run-w", {}, 6)
        self.assertEqual(sampler.outstanding, 0)
        self.assertEqual(env.count("reserve", "sample"), env.count("adjust", "sample"))

    def evaluation_with_a_ratchet(self, env, sampler):
        rt = RT.Ratchet(os.path.join(env.dir, "r.jsonl"), os.path.join(env.dir, "l.jsonl"),
                        os.path.join(env.dir, "lock.json"), CAP)
        rt.lock_harness()
        return rt, env.run.base_sampler()

    def test_an_interrupt_waits_for_the_calls_in_flight_and_settles_them(self):
        sampler = self.sampler()
        env = Env(self, sampler)
        rt, base = self.evaluation_with_a_ratchet(env, sampler)
        real = V.evaluate_arm

        def interrupted(resp, *a, **kw):
            resp(self.views[0])
            resp(self.views[1])
            raise KeyboardInterrupt()
        V.evaluate_arm = interrupted
        self.addCleanup(setattr, V, "evaluate_arm", real)
        with self.assertRaises(KeyboardInterrupt):
            D.evaluate_recorded(rt, env.run, base, self.codec, self.epset, "C", "pilot:base-model", "run-w", {}, 6)
        self.assertEqual(sampler.outstanding, 0)                                  # the calls in flight were awaited
        sent = len(sampler.calls)
        self.assertGreater(sent, 2)
        self.assertEqual((env.count("reserve", "sample"), env.count("adjust", "sample")), (sent, sent))
        self.assertEqual(env.tokens()["sample"], sum(self.actual[:sent]))        # and settled to what they used

    def test_an_oversize_reply_found_while_draining_replaces_the_interrupt(self):
        sampler = self.sampler(oversize=[4])
        env = Env(self, sampler)
        rt, base = self.evaluation_with_a_ratchet(env, sampler)
        real = V.evaluate_arm

        def interrupted(resp, *a, **kw):
            resp(self.views[0])
            raise KeyboardInterrupt()
        V.evaluate_arm = interrupted
        self.addCleanup(setattr, V, "evaluate_arm", real)
        with self.assertRaises(T.BudgetStop):
            D.evaluate_recorded(rt, env.run, base, self.codec, self.epset, "C", "pilot:base-model", "run-w", {}, 6)
        self.assertEqual(sampler.outstanding, 0)

    def test_a_second_interrupt_during_the_wait_leaves_the_calls_not_yet_settled_at_their_full_reservation(self):
        class Impatient(fakes.WindowSampler):
            def sample(self, *a, **kw):
                fut = super().sample(*a, **kw)
                if fut.index == 3:                                                # the second interrupt arrives here
                    def stop(timeout=None):
                        raise KeyboardInterrupt()
                    fut.result = stop
                return fut
        sampler = Impatient(reply_for=self.reply_for)
        env = Env(self, sampler)
        resp = self.responder(env, 6)
        drive(resp, self.views, 1)
        with self.assertRaises(KeyboardInterrupt):
            resp.finish()
        # calls 1 and 2 were settled; call 3 and the calls after it keep their full limit: an upper bound
        sent = len(sampler.calls)
        self.assertEqual(sent, 6)
        unsettled = env.count("reserve", "sample") - env.count("adjust", "sample")
        self.assertEqual(unsettled, sent - 3)
        self.assertEqual(env.tokens()["sample"], sum(self.actual[:3]) + (sent - 3) * LIMIT)

    def test_with_every_reply_oversize_the_overshoot_is_the_excess_of_every_call_in_flight(self):
        # each reply is over its limit by 1 id, so with a window of W the first oversize reply is read while up to W calls are
        # in flight, and every one of them comes back oversize before the run stops
        for window in (1, 2, 4, 8):
            env = Env(self, self.sampler(oversize=range(self.n)))
            resp = self.responder(env, window)
            with self.assertRaises(T.BudgetStop):
                drive(resp, self.views)
            sent = len(env.sampler.calls)
            self.assertEqual(sent, window, window)
            reserved = sent * LIMIT
            self.assertEqual(env.tokens()["sample"] - reserved, sent, window)         # the excess is the sum over the window
            self.assertEqual(env.run.meter.tokens["sample"], env.tokens()["sample"], window)
            self.assertEqual(env.sampler.outstanding, 0, window)

    def test_the_window_must_be_a_whole_number_from_one_to_the_largest(self):
        for bad in (0, -1, T.MAX_WINDOW + 1, True, 2.0, "8", None):
            with self.assertRaises(T.BackendError, msg=repr(bad)):
                T.check_window(bad)
        for good in (1, 8, T.MAX_WINDOW):
            self.assertEqual(T.check_window(good), good)
        env = Env(self, self.sampler())
        with self.assertRaises(T.BackendError):
            T.WindowedResponder(env.run, env.sampler, self.codec, CAP, self.views, 0)

    def test_the_driver_responder_without_views_is_the_sequential_one(self):
        env = Env(self, self.sampler())
        self.assertIs(type(D.responder(env.run, env.sampler, self.codec, CAP)), T.TinkerResponder)
        self.assertIs(type(D.responder(env.run, env.sampler, self.codec, CAP, self.views, 3)), T.WindowedResponder)


class KilledWithCallsInFlightTests(unittest.TestCase):
    def test_a_killed_process_leaves_every_reservation_and_a_restart_counts_them_as_spent(self):
        codec, _epset, views, _replies = setup_codec_and_views()
        window = 4
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        approvals = os.path.join(tmp.name, "approvals.json")
        with open(approvals, "w") as fh:
            json.dump({"approvals": [{"run_id": "run-k", "ceiling_usd": "5.00", "plan": "test", "plan_id": PID}]}, fh)
        child = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_window_child.py")
        cmd = [sys.executable, "-I", "-B"] + ["-O"] * sys.flags.optimize
        for w in sys.warnoptions:
            cmd += ["-W", w]
        proc = subprocess.Popen(cmd + [child, approvals, "run-k", str(window), PID], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
        try:
            line = proc.stdout.readline()
            self.assertEqual(line.strip(), "WAITING %d" % window, proc.stderr.read() if proc.poll() is not None else "")
            os.kill(proc.pid, signal.SIGKILL)
            proc.wait(timeout=30)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=30)
            proc.stdout.close()
            proc.stderr.close()
        self.assertEqual(proc.returncode, -signal.SIGKILL)
        ledger = T.Ledger(approvals + ".spend.jsonl", "run-k")
        spent, tokens, starts, plan_id = ledger.replay()
        want_prefill = sum(len(codec.prompt_ids(v.messages)) for v in views[:window])
        self.assertEqual((starts, plan_id), (1, PID))
        self.assertEqual(tokens, {"train": 0, "prefill": want_prefill, "sample": window * LIMIT, "cached_prefill": 0})
        with open(approvals + ".spend.jsonl", "rb") as fh:
            rows = [json.loads(x) for x in fh.read().split(b"\n")[:-1]]
        self.assertEqual([r["ev"] for r in rows], ["start"] + ["reserve"] * (2 * window))   # nothing settled, nothing lost
        want = T.cost_usd("prefill", want_prefill) + T.cost_usd("sample", window * LIMIT)
        self.assertEqual(spent, want)
        # the lock died with the process, so a restart can start, and it counts the calls in flight as spent
        run = T.TinkerRun("run-k", approvals, PLAN_TOKENS, "test", PID, fakes.FakeService(), fakes.FakeTypes, resume=True)
        self.addCleanup(run.close)
        self.assertEqual(run.meter.spent, want)
        self.assertEqual(run.meter.tokens["sample"], window * LIMIT)
        with self.assertRaises(T.ApprovalError):                                  # and without resume it is refused
            T.TinkerRun("run-k", approvals, PLAN_TOKENS, "test", PID, fakes.FakeService(), fakes.FakeTypes)


class RetryTests(unittest.TestCase):
    def make(self, **kw):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "approvals.json")
        with open(path, "w") as fh:
            json.dump({"approvals": [{"run_id": "run-w", "ceiling_usd": "5.00", "plan": "test", "plan_id": PID}]}, fh)
        svc = fakes.FakeService(base=fakes.FakeSampler(), checkpoint_samplers=[fakes.FakeSampler()])
        run = T.TinkerRun("run-w", path, PLAN_TOKENS, "test", PID, svc, fakes.FakeTypes, **kw)
        self.addCleanup(run.close)
        return run, svc

    def test_the_library_retries_stay_as_they_are_unless_the_run_switches_them_off(self):
        run, svc = self.make()
        run.start_arm("a")
        run.base_sampler()
        run.checkpoint_sampler("a")
        self.assertEqual((svc.retry_configs, svc.clients[0].retry_configs), ([None], [None]))

    def test_a_run_without_sample_retries_builds_both_kinds_of_sampling_client_with_the_retry_loop_off(self):
        run, svc = self.make(sample_retries=False)
        run.start_arm("a")
        run.base_sampler()
        run.checkpoint_sampler("a")
        got = svc.retry_configs + svc.clients[0].retry_configs
        self.assertEqual(len(got), 2)
        for cfg in got:
            self.assertIs(cfg.enable_retry_logic, False)

    @unittest.skipUnless(__import__("importlib").util.find_spec("tinker"), "needs the service library")
    def test_the_real_library_config_with_the_retry_loop_off_survives_the_clients_own_rewrite(self):
        import dataclasses
        cfg = T.no_retry_config(object())                  # an object without RetryConfig: the library's is used
        self.assertIs(cfg.enable_retry_logic, False)
        self.assertIs(dataclasses.replace(cfg, max_connections=None).enable_retry_logic, False)
        self.assertIs(dataclasses.replace(cfg, max_connections=7, enable_stuck_detection=False).enable_retry_logic, False)


class FakeFidelityTests(unittest.TestCase):
    def test_the_fake_sample_returns_a_pending_future_and_records_what_is_in_flight(self):
        s = fakes.WindowSampler(reply_for=lambda toks: [9, 9])
        types = fakes.FakeTypes
        futs = [s.sample(prompt=types.ModelInput.from_ints(tokens=[i]), num_samples=1,
                         sampling_params=types.SamplingParams(max_tokens=5, temperature=0.0, stop=[1]))
                for i in range(4)]
        self.assertEqual((s.outstanding, s.max_in_flight, s.answered_order), (4, 4, []))
        futs[0].result()
        self.assertEqual((s.outstanding, s.answered_order), (3, [3, 2, 1, 0]))
        futs[2].result(timeout=1)
        self.assertEqual((s.outstanding, s.max_in_flight), (2, 4))
        self.assertEqual(futs[1].result().sequences[0].tokens, [9, 9])

    def test_the_fake_fails_sends_and_results_and_oversize_replies_where_it_is_told_to(self):
        s = fakes.WindowSampler(fail_send=[1], fail_result=[0], oversize=[1])
        types = fakes.FakeTypes
        mk = lambda: s.sample(prompt=types.ModelInput.from_ints(tokens=[1, 2]), num_samples=1,
                              sampling_params=types.SamplingParams(max_tokens=5))
        f0 = mk()
        with self.assertRaises(RuntimeError):
            mk()                                                                   # the second send fails, no call is made
        self.assertEqual(len(s.calls), 1)
        f1 = mk()                                                                  # the third send is the call numbered 1
        with self.assertRaises(RuntimeError):
            f0.result()
        self.assertEqual(len(f1.result().sequences[0].tokens), 6)                  # one more than max_tokens


class PlanFingerprintTests(unittest.TestCase):
    LEGACY = "588a6b6c0082ae7a1b898dade6d4ec713ead807eceeef967a4e927e341c57aa0"      # the first pilot's plan_id

    def test_the_window_is_part_of_the_plan_fingerprint(self):
        prints = {w: D.plan_fingerprint(cost.pilot_plan(CAP, w)) for w in (1, 2, 8)}
        self.assertEqual(len(set(prints.values())), 3)
        full = {w: D.plan_fingerprint(cost.full_plan(2048, 2, CAP, window=w)) for w in (1, 2, 8)}
        self.assertEqual(len(set(full.values())), 3)
        plan = cost.full_plan(64, 2, CAP, heldout_per_tier=10, window=4)
        before = D.plan_fingerprint(plan)
        plan.window = 5
        self.assertNotEqual(D.plan_fingerprint(plan), before)

    def test_a_window_of_one_keeps_the_fingerprint_of_the_plan_the_first_pilot_ran_under(self):
        self.assertEqual(D.plan_fingerprint(cost.pilot_plan(CAP)), self.LEGACY)
        self.assertEqual(D.plan_fingerprint(cost.pilot_plan(CAP, 1)), self.LEGACY)
        self.assertNotEqual(D.plan_fingerprint(cost.pilot_plan(CAP, cost.PROPOSED_WINDOW)), self.LEGACY)

    def test_the_proposed_window_is_eight_and_a_plan_refuses_a_bad_window(self):
        self.assertEqual(cost.PROPOSED_WINDOW, 8)
        self.assertEqual(cost.pilot_plan(CAP).window, 1)
        self.assertEqual(cost.pilot_plan(CAP, 8).window, 8)
        for bad in (0, 65, True, "8"):
            with self.assertRaises(T.BackendError):
                cost.pilot_plan(CAP, bad)
            with self.assertRaises(T.BackendError):
                cost.full_plan(2048, 2, CAP, window=bad)

    def test_an_approval_for_one_window_is_refused_for_another(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "approvals.json")
        eight, one = cost.pilot_plan(CAP, 8), cost.pilot_plan(CAP, 1)
        with open(path, "w") as fh:
            json.dump({"approvals": [D.approval_row("pilot-w", "0.50", eight)]}, fh)
        counter = cost.Counter(rule_only=True)
        with self.assertRaises(T.ApprovalError):
            D.start_run("pilot-w", path, one, counter, fakes.FakeService(), fakes.FakeTypes)
        run = D.start_run("pilot-w", path, eight, counter, fakes.FakeService(), fakes.FakeTypes)
        run.close()


class CostTests(unittest.TestCase):
    def test_the_window_changes_no_token_count_and_the_pilot_check_is_counted(self):
        counter = cost.Counter(rule_only=True)
        full1, _ = cost.plan_counts(cost.full_plan(2048, 2, CAP), counter)
        full8, _ = cost.plan_counts(cost.full_plan(2048, 2, CAP, window=8), counter)
        self.assertEqual(full1, full8)
        p1, items1 = cost.plan_counts(cost.pilot_plan(CAP), counter)
        p8, items8 = cost.plan_counts(cost.pilot_plan(CAP, 8), counter)
        self.assertEqual(len(items8), len(items1) + 2)                           # the check adds a prefill and a sample line
        self.assertEqual(p8["train"], p1["train"])
        self.assertGreater(p8["prefill"], p1["prefill"])
        self.assertGreater(p8["sample"], p1["sample"])
        # the check is the base model on the same 100 puzzles again, so it costs what that evaluation costs
        base_prefill = [n for label, kind, n, _ in items1 if label.startswith("eval prefill base model")][0]
        base_sample = [n for label, kind, n, _ in items1 if label.startswith("eval sample base model")][0]
        self.assertEqual((p8["prefill"] - p1["prefill"], p8["sample"] - p1["sample"]), (base_prefill, base_sample))

    def test_the_proposed_pilot_costs_more_than_the_first_one_and_stays_under_its_ceiling(self):
        counter = cost.Counter(rule_only=True)
        t1, _ = cost.plan_counts(cost.pilot_plan(CAP), counter)
        t8, _ = cost.plan_counts(cost.pilot_plan(CAP, 8), counter)
        c1, c8 = T.planned_cost(t1), T.planned_cost(t8)
        self.assertGreater(c8, c1)
        self.assertLess(c8, Fraction(1, 2))


if __name__ == "__main__":
    unittest.main()
