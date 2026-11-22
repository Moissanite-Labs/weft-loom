import contextlib
import io
import json
import os
import signal
import tempfile
import types
import unittest
from unittest import mock

import _setup  # noqa: F401
import cost
import driver
import episodes as E
import evaluate
import fakes
import pilot_cli as P
import receipts
import tinker_backend as T

CAP = evaluate.DEFAULT_CAP
KEY = "tml-FAKEKEY0123456789abcdefABCDEF0123456789"     # a made-up string shaped like a key
SHORT_KEY = "hunter2-not-a-real-key"                      # shaped like nothing redact knows


def no_float(text):
    raise AssertionError("a float (%s) in the result file" % text)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = self.tmp.name
        self.approvals = os.path.join(self.dir, "keep", "approvals.json")
        os.makedirs(os.path.dirname(self.approvals))
        self.out = os.path.join(self.dir, "out")
        self.services = []                                  # every service object the backend asked for
        self.plan = cost.pilot_plan(CAP, P.PILOT_WINDOW)

    def approve(self, run_id="pilot-1", ceiling="0.50", plan=None, plan_id=None):
        plan = plan or self.plan
        row = driver.approval_row(run_id, ceiling, plan)
        if plan_id is not None:
            row["plan_id"] = plan_id
        with open(self.approvals, "w", encoding="utf-8") as fh:
            json.dump({"approvals": [row]}, fh)

    def run_cli(self, args, env=None, patches=()):
        """main() in this process with output captured. Returns (exit status, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(err))
            for p in patches:
                stack.enter_context(p)
            code = P.main(args, env={} if env is None else env)
        return code, out.getvalue(), err.getvalue()

    def fake_args(self, run_id="pilot-1", out=None):
        return ["--approvals", self.approvals, "--run-id", run_id, "--out", out or self.out, "--fake"]

    def real_mode_patches(self, service=None):
        """The real branch of main with the library replaced: the service and its types are fakes, and the
        tokenizer is the fake one. Every service built is counted in self.services."""
        def make_service():
            svc = service if service is not None else P.fake_service(self.plan, driver.check_codec(fakes.FakeTokenizer()))
            self.services.append(svc)
            return svc
        return [mock.patch.object(T, "_real_service", make_service),
                mock.patch.object(T, "_real_types", lambda: fakes.FakeTypes),
                mock.patch.object(T, "real_tokenizer", lambda: fakes.FakeTokenizer())]

    def files_under(self, root):
        for base, _dirs, names in os.walk(root):
            for n in names:
                yield os.path.join(base, n)

    def assertNoKey(self, key, *texts):
        for t in texts:
            self.assertNotIn(key, t)
        for root in (self.dir,):
            for path in self.files_under(root):
                with open(path, "rb") as fh:
                    self.assertNotIn(key.encode(), fh.read(), path)

    def result(self):
        with open(os.path.join(self.out, "pilot-result.json"), "r", encoding="utf-8") as fh:
            return json.load(fh)


class FakeRunTests(Base):
    def run_fake(self):
        self.approve()
        code, out, err = self.run_cli(self.fake_args())
        self.assertEqual((code, err), (0, ""), out)
        return out

    def test_the_fake_run_writes_every_output_file(self):
        out = self.run_fake()
        names = sorted(os.listdir(self.out))
        for want in ("pilot-result.json", "replies.jsonl", "receipts.jsonl", "pilot-summary.md"):
            self.assertIn(want, names)
        self.assertIn("pilot complete: go=true", out)
        self.assertEqual(receipts.verify(os.path.join(self.out, "receipts.jsonl"))[0] > 0, True)
        self.assertEqual(receipts.bodies(os.path.join(self.out, "receipts.jsonl"))[-1]["kind"], "pilot")
        with open(os.path.join(self.out, "pilot-summary.md"), encoding="utf-8") as fh:
            summary = fh.read()
        self.assertIn("| base | 0 | 100 | 0 |", summary)
        self.assertIn("| base-sequential | 0 | 100 | 0 |", summary)
        self.assertIn("| adapter | 60 | 40 | 0 |", summary)
        self.assertIn("window 8", summary)
        self.assertIn("Window check: 100 replies of the untrained model sampled one call at a time, 0 differ", summary)

    def test_replies_are_logged_one_line_per_reply(self):
        self.run_fake()
        with open(os.path.join(self.out, "replies.jsonl"), encoding="utf-8") as fh:
            rows = [json.loads(line, parse_float=no_float) for line in fh]
        self.assertEqual(len(rows), 300)
        self.assertEqual([r["model"] for r in rows], ["base"] * 100 + ["base-sequential"] * 100 + ["adapter"] * 100)
        self.assertEqual(sorted(rows[0]), sorted(["arm", "cut", "episode_id", "reply", "seed", "tier", "tokens",
                                                  "outcome", "model", "status", "returned", "returned_tokens"]))
        for r in rows:
            self.assertEqual((r["status"], len(r["returned"]), r["returned_tokens"]), ("ok", 1, len(r["returned"][0])))
            self.assertGreaterEqual(r["returned_tokens"], r["tokens"])
        ev = E.build_set("train", self.plan.eval1_counts, self.plan.eval1_offset)
        self.assertEqual([r["episode_id"] for r in rows[:100]], [ep.id for ep in ev.episodes])
        self.assertTrue(all(r["episode_id"].startswith("train-") for r in rows))
        res = self.result()
        for name in P.WINDOWED_ORDER:
            mine = "".join(r["outcome"] for r in rows if r["model"] == name)
            self.assertEqual(P.counts_by_outcome(mine), res["outcomes"][name])

    def test_the_planned_cost_describes_the_fake_run(self):
        self.run_fake()
        res = self.result()
        totals, _items = cost.plan_counts(self.plan, P.TokenizerCounter(fakes.FakeTokenizer()))
        self.assertEqual(res["planned_cost_usd"], str(T.planned_cost(totals)))
        by = res["spend"]["by_kind"]
        self.assertEqual((by["train"]["tokens"], by["prefill"]["tokens"]), (totals["train"], totals["prefill"]))
        self.assertLessEqual(by["sample"]["tokens"], totals["sample"])

    def test_the_result_has_no_floats_only_integers_and_strings(self):
        self.run_fake()
        with open(os.path.join(self.out, "pilot-result.json"), encoding="utf-8") as fh:
            res = json.load(fh, parse_float=no_float)
        receipts.check_plain(res)
        self.assertEqual(res["status"], "complete")
        self.assertEqual(res["error"], "")

    def test_the_gates_in_the_file_are_the_drivers_verdict_on_the_measurements(self):
        self.run_fake()
        res = self.result()
        full_calls, full_steps = driver.plan_calls(cost.full_plan(P.FULL_EXAMPLES, P.FULL_SEEDS, CAP))
        want = driver.pilot_verdict(res["measurements"], full_calls, full_steps)
        self.assertEqual(res["gates"], {k: P.true_false(v) for k, v in want.items()})
        self.assertEqual(res["go"], P.true_false(want["go"]))
        m = res["measurements"]
        self.assertEqual(res["timing"], {"sampling_calls": m["calls"], "sampling_ns_total": m["sample_ns"],
                                         "train_steps": m["steps"], "train_ns_total": m["train_ns"]})

    def test_a_no_go_is_a_finished_pilot(self):
        self.approve()
        slow = [0]

        def clock():
            slow[0] += 10 ** 12                       # 1000 seconds per tick: the time gate fails
            return slow[0]
        real_run = driver.run_pilot
        with mock.patch.object(driver, "run_pilot", lambda *a, **kw: real_run(*a, clock=clock, **kw)):
            code, out, _err = self.run_cli(self.fake_args())
        self.assertEqual(code, 0)
        res = self.result()
        self.assertEqual((res["go"], res["gates"]["projected_time_ok"], res["status"]), ("false", "false", "complete"))
        self.assertIn("go=false", out)

    def test_the_spend_is_the_ledgers_exact_dollars_by_kind(self):
        self.run_fake()
        res = self.result()
        by = res["spend"]["by_kind"]
        total = sum((T.Fraction(row["usd"]) for row in by.values()), T.Fraction(0))
        self.assertEqual(str(total), res["spend"]["total_usd"])
        for kind, row in by.items():
            self.assertEqual(row["usd"], str(T.cost_usd(kind, row["tokens"])))
        spent, tokens, starts, _pid = T.Ledger(self.approvals + ".spend.jsonl", "pilot-1").replay()
        self.assertEqual((str(spent), starts), (res["spend"]["total_usd"], 1))
        self.assertEqual({k: v["tokens"] for k, v in by.items()}, tokens)

    def test_the_fake_run_puts_the_backends_factories_back(self):
        service, types_ = T._real_service, T._real_types
        self.run_fake()
        self.assertIs(T._real_service, service)
        self.assertIs(T._real_types, types_)
        self.approve(run_id="pilot-9", ceiling="0.05")
        self.run_cli(self.fake_args("pilot-9", out=os.path.join(self.dir, "out9")))
        self.assertIs(T._real_service, service)

    def test_the_planned_cost_and_ceiling_are_printed_before_the_first_service_call(self):
        self.approve()
        seen, out = [], io.StringIO()
        make = P.fake_service

        def spy(plan, codec):
            seen.append(out.getvalue())                 # what had been printed when the service was made
            return make(plan, codec)
        with mock.patch.object(P, "fake_service", spy), contextlib.redirect_stdout(out):
            code = P.main(self.fake_args(), env={})
        self.assertEqual((code, len(seen)), (0, 1))
        self.assertTrue(seen[0].startswith("planned cost "), seen[0])
        self.assertIn("ceiling 1/2 dollars", seen[0])

    def test_real_mode_wiring_runs_with_the_library_replaced(self):
        self.approve()
        code, out, err = self.run_cli(["--approvals", self.approvals, "--run-id", "pilot-1", "--out", self.out],
                                      env={P.KEY_VAR: SHORT_KEY}, patches=self.real_mode_patches())
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(len(self.services), 1)
        self.assertEqual(self.result()["mode"], "real")
        self.assertIn("token counts from the tokenizer", out)
        self.assertNoKey(SHORT_KEY, out, err)

    @unittest.skipUnless(__import__("importlib").util.find_spec("tml_renderers"), "needs tml_renderers")
    def test_the_planned_cost_with_the_real_tokenizer_is_the_documented_one(self):
        for window, want in ((P.PILOT_WINDOW, "0.1024"), (1, "0.0924")):     # the proposed pilot, and the first pilot
            self.approve(plan=cost.pilot_plan(CAP, window))
            opts = {"approvals": self.approvals, "run_id": "pilot-1", "out": self.out, "fake": False, "print_row": False,
                    "window": window}
            lines = []
            _plan, _codec, _counter, _appr, planned = P.prepare(opts, {P.KEY_VAR: SHORT_KEY}, CAP, lines.append)
            self.assertEqual(cost.usd_text(planned), want)
            self.assertEqual(len(lines), 1)


class RefusalTests(Base):
    def assertRefused(self, args, env=None, patches=None, message=None):
        patches = self.real_mode_patches() if patches is None else patches
        code, out, err = self.run_cli(args, env=env, patches=patches)
        self.assertEqual(code, P.EXIT_REFUSED, (out, err))
        self.assertEqual(self.services, [], "a service object was made")
        self.assertIn("refused: ", err)
        if message:
            self.assertIn(message, err)
        self.assertFalse(os.path.exists(os.path.join(self.out, "pilot-result.json")))
        self.assertEqual(os.listdir(self.out) if os.path.isdir(self.out) else [], [])
        return err

    def real_args(self, run_id="pilot-1"):
        return ["--approvals", self.approvals, "--run-id", run_id, "--out", self.out]

    REAL_ENV = {P.KEY_VAR: SHORT_KEY}

    def test_a_missing_approval_row_is_refused(self):
        self.approve(run_id="another-run")
        self.assertRefused(self.real_args(), self.REAL_ENV, message="not approved")

    def test_a_missing_approvals_file_is_refused(self):
        self.assertRefused(self.real_args(), self.REAL_ENV, message="cannot be read")

    def test_an_approval_for_the_full_plan_is_refused(self):
        self.approve(plan=cost.full_plan(2048, 2, CAP))
        self.assertRefused(self.real_args(), self.REAL_ENV, message="another plan")

    def test_an_approval_with_another_plan_fingerprint_is_refused(self):
        self.approve(plan_id="0" * 64)
        self.assertRefused(self.real_args(), self.REAL_ENV, message="another plan")

    def test_a_ceiling_too_low_for_the_planned_cost_is_refused_before_any_service(self):
        self.approve(ceiling="0.05")
        self.assertRefused(self.real_args(), self.REAL_ENV, message="not under the ceiling")

    def test_a_ceiling_above_the_pilots_registered_ceiling_is_refused(self):
        self.approve(ceiling="0.51")
        self.assertRefused(self.real_args(), self.REAL_ENV, message="above the pilot's registered ceiling")
        self.approve(ceiling="50.00")
        self.assertRefused(self.real_args(), self.REAL_ENV, message="above the pilot's registered ceiling")

    def test_the_registered_ceiling_itself_is_accepted(self):
        self.approve(ceiling="0.50")
        code, _out, _err = self.run_cli(self.real_args(), self.REAL_ENV, self.real_mode_patches())
        self.assertEqual(code, 0)

    def test_a_float_ceiling_in_the_approvals_file_is_refused(self):
        row = driver.approval_row("pilot-1", "0.50", self.plan)
        row["ceiling_usd"] = 0.5
        with open(self.approvals, "w", encoding="utf-8") as fh:
            json.dump({"approvals": [row]}, fh)
        self.assertRefused(self.real_args(), self.REAL_ENV)

    def test_the_fake_mode_refuses_the_same_way_before_its_fake_service(self):
        self.approve(ceiling="0.05")
        made = []
        with mock.patch.object(P, "fake_service", lambda *a: made.append(1)):
            code, _out, err = self.run_cli(self.fake_args())
        self.assertEqual((code, made), (P.EXIT_REFUSED, []))
        self.assertIn("not under the ceiling", err)

    def test_a_non_empty_out_directory_is_refused_and_left_alone(self):
        self.approve()
        os.makedirs(self.out)
        mine = os.path.join(self.out, "keep.txt")
        with open(mine, "w") as fh:
            fh.write("mine")
        code, _out, err = self.run_cli(self.real_args(), self.REAL_ENV, self.real_mode_patches())
        self.assertEqual((code, self.services), (P.EXIT_REFUSED, []))
        self.assertIn("new or empty directory", err)
        self.assertEqual(os.listdir(self.out), ["keep.txt"])
        with open(mine) as fh:
            self.assertEqual(fh.read(), "mine")

    def test_an_out_path_that_is_a_file_is_refused(self):
        self.approve()
        with open(self.out, "w") as fh:
            fh.write("x")
        code, _out, _err = self.run_cli(self.real_args(), self.REAL_ENV, self.real_mode_patches())
        self.assertEqual((code, self.services), (P.EXIT_REFUSED, []))

    def test_an_empty_out_directory_is_accepted(self):
        self.approve()
        os.makedirs(self.out)
        code, _out, _err = self.run_cli(self.fake_args())
        self.assertEqual(code, 0)

    def test_the_fake_run_into_a_used_out_directory_is_refused_too(self):
        self.approve()
        self.assertEqual(self.run_cli(self.fake_args())[0], 0)
        self.approve(run_id="pilot-2")
        code, _out, err = self.run_cli(self.fake_args("pilot-2"))
        self.assertEqual(code, P.EXIT_REFUSED)
        self.assertIn("new or empty directory", err)

    def test_real_mode_needs_the_key_variable_non_empty(self):
        self.approve()
        for env in ({}, {P.KEY_VAR: ""}):
            self.assertRefused(self.real_args(), env, message=P.KEY_VAR)

    def test_fake_mode_does_not_need_the_key(self):
        self.approve()
        self.assertEqual(self.run_cli(self.fake_args(), env={})[0], 0)

    def test_all_three_paths_are_required_and_unknown_options_are_refused(self):
        self.approve()
        for args in ([], ["--run-id", "pilot-1", "--out", self.out], ["--approvals", self.approvals, "--out", self.out],
                     ["--approvals", self.approvals, "--run-id", "pilot-1"], ["--nonsense"],
                     ["--approvals"], self.real_args() + ["--held-out"]):
            code, _out, err = self.run_cli(args, self.REAL_ENV, self.real_mode_patches())
            self.assertEqual((code, self.services), (P.EXIT_REFUSED, []), args)
            self.assertIn("refused: ", err)

    def test_a_second_start_of_the_same_run_id_is_refused(self):
        self.approve()
        self.assertEqual(self.run_cli(self.fake_args())[0], 0)
        out2 = os.path.join(self.dir, "out2")
        code, _out, err = self.run_cli(self.fake_args(out=out2))
        self.assertEqual(code, P.EXIT_REFUSED)
        self.assertIn("already started", err)
        self.assertFalse(os.path.exists(out2))

    def test_a_refusal_from_the_start_checks_makes_no_out_directory(self):
        self.approve(ceiling="0.05")                        # below the planned cost: start_run refuses
        code, _out, err = self.run_cli(self.fake_args())
        self.assertEqual(code, P.EXIT_REFUSED)
        self.assertIn("refused: ", err)
        self.assertFalse(os.path.exists(self.out))
        self.assertNotIn("approvals.json.spend.jsonl", os.listdir(os.path.dirname(self.approvals)))   # nothing spent


class ApprovalRowTests(Base):
    def test_the_printed_row_is_accepted_by_the_backends_loader(self):
        code, out, err = self.run_cli(["--run-id", "pilot-7", "--print-approval-row"],
                                      patches=self.real_mode_patches())
        self.assertEqual((code, err), (0, ""))
        row = json.loads(out, parse_float=no_float)
        self.assertEqual(row["ceiling_usd"], "0.50")
        with open(self.approvals, "w", encoding="utf-8") as fh:
            json.dump({"approvals": [row]}, fh)
        got = T.load_approval(self.approvals, "pilot-7")
        self.assertEqual((got.ceiling, got.plan, got.plan_id),
                         (T.Fraction(1, 2), "pilot", driver.plan_fingerprint(cost.pilot_plan(CAP, P.PILOT_WINDOW))))
        self.assertEqual(row, driver.approval_row("pilot-7", "0.50", cost.pilot_plan(CAP, P.PILOT_WINDOW)))

    def test_the_printed_row_starts_a_run(self):
        _code, out, _err = self.run_cli(["--run-id", "pilot-7", "--print-approval-row"])
        with open(self.approvals, "w", encoding="utf-8") as fh:
            json.dump({"approvals": [json.loads(out)]}, fh)
        self.assertEqual(self.run_cli(self.fake_args("pilot-7"))[0], 0)

    def test_printing_the_row_does_nothing_else(self):
        code, _out, _err = self.run_cli(["--run-id", "pilot-7", "--print-approval-row", "--out", self.out],
                                        patches=self.real_mode_patches())
        self.assertEqual((code, self.services, os.path.exists(self.out)), (0, [], False))
        self.assertEqual(os.listdir(os.path.dirname(self.approvals)), [])

    def test_the_row_needs_a_run_id(self):
        code, out, err = self.run_cli(["--print-approval-row"])
        self.assertEqual((code, out), (P.EXIT_REFUSED, ""))
        self.assertIn("--run-id", err)


class RedactionTests(Base):
    def failing_service(self, message):
        codec = driver.check_codec(fakes.FakeTokenizer())
        svc = P.fake_service(self.plan, codec)
        svc.fail_with = RuntimeError(message)
        return svc

    def test_a_key_shaped_string_in_a_service_error_reaches_no_output(self):
        self.approve()
        svc = self.failing_service("auth failed for %s at the service" % KEY)
        code, out, err = self.run_cli(["--approvals", self.approvals, "--run-id", "pilot-1", "--out", self.out],
                                      {P.KEY_VAR: KEY}, self.real_mode_patches(svc))
        self.assertEqual(code, P.EXIT_ERROR)
        self.assertNoKey(KEY, out, err)
        res = self.result()
        self.assertEqual(res["status"], "incomplete")
        self.assertIn("[REDACTED]", res["error"])

    PLANT = "tml-PLANTED+k3y/0123456789abc=def"           # characters the backend's pattern does not match

    def assertNoFragment(self, *texts):
        for t in texts:
            self.assertNotIn("k3y", t)
            self.assertNotIn("0123456789abc", t)
        for path in self.files_under(self.dir):
            with open(path, "rb") as fh:
                data = fh.read()
            self.assertNotIn(b"k3y", data, path)
            self.assertNotIn(b"0123456789abc", data, path)

    def test_a_key_outside_the_pattern_does_not_leak_from_a_guarded_service_call(self):
        self.approve()
        svc = self.failing_service("auth failed for key %s please retry" % self.PLANT)
        code, out, err = self.run_cli(["--approvals", self.approvals, "--run-id", "pilot-1", "--out", self.out],
                                      {P.KEY_VAR: self.PLANT}, self.real_mode_patches(svc))
        self.assertEqual(code, P.EXIT_ERROR)
        self.assertIn("please retry", err)
        self.assertNoKey(self.PLANT, out, err)
        self.assertNoFragment(out, err)

    def test_the_registered_key_is_cleared_when_the_run_ends(self):
        self.approve()
        self.run_cli(self.fake_args(), {P.KEY_VAR: self.PLANT})
        self.assertIn("k3y", T.redact("x " + self.PLANT))

    def test_a_key_of_no_known_shape_is_removed_by_value(self):
        self.approve()
        with mock.patch.object(driver, "run_pilot", side_effect=ValueError("bad header key=%s end" % SHORT_KEY)):
            code, out, err = self.run_cli(["--approvals", self.approvals, "--run-id", "pilot-1", "--out", self.out],
                                          {P.KEY_VAR: SHORT_KEY}, self.real_mode_patches())
        self.assertEqual(code, P.EXIT_ERROR)
        self.assertNoKey(SHORT_KEY, out, err)
        self.assertIn("[REDACTED]", self.result()["error"])

    def test_the_key_is_removed_from_a_refusal_message_too(self):
        self.approve(run_id="other")
        code, out, err = self.run_cli(["--approvals", self.approvals, "--run-id", SHORT_KEY, "--out", self.out],
                                      {P.KEY_VAR: SHORT_KEY}, self.real_mode_patches())
        self.assertEqual(code, P.EXIT_REFUSED)
        self.assertNoKey(SHORT_KEY, out, err)

    def test_a_key_shaped_string_in_the_fake_run_error_reaches_no_output(self):
        self.approve()
        svc = self.failing_service("the proxy said %s" % KEY)
        with mock.patch.object(P, "fake_service", lambda *a: svc):
            code, out, err = self.run_cli(self.fake_args(), {})
        self.assertEqual(code, P.EXIT_ERROR)
        self.assertNoKey(KEY, out, err)

    def test_the_key_variable_is_never_printed_on_success(self):
        self.approve()
        code, out, err = self.run_cli(["--approvals", self.approvals, "--run-id", "pilot-1", "--out", self.out],
                                      {P.KEY_VAR: KEY}, self.real_mode_patches())
        self.assertEqual(code, 0)
        self.assertNoKey(KEY, out, err)

    def test_scrub_removes_the_value_then_redacts(self):
        text = P.scrub(ValueError("x %s y %s" % (SHORT_KEY, KEY)), {P.KEY_VAR: SHORT_KEY})
        self.assertNotIn(SHORT_KEY, text)
        self.assertNotIn(KEY, text)
        self.assertTrue(text.startswith("ValueError: "))
        self.assertNotIn(SHORT_KEY, P.scrub(ValueError(SHORT_KEY), {P.KEY_VAR: SHORT_KEY}))
        self.assertEqual(P.scrub(ValueError("plain"), {}), "ValueError: plain")


class IncompleteRunTests(Base):
    def test_sigterm_and_sighup_are_an_incomplete_run_and_the_handlers_are_put_back(self):
        def mine(signum, frame):
            pass
        old = signal.signal(signal.SIGTERM, mine), signal.signal(signal.SIGHUP, mine)
        self.addCleanup(signal.signal, signal.SIGTERM, old[0])
        self.addCleanup(signal.signal, signal.SIGHUP, old[1])
        before = mine, mine                                  # what main must put back
        for n, sig in enumerate((signal.SIGTERM, signal.SIGHUP)):
            run_id = "pilot-%d" % n
            self.approve(run_id=run_id)
            out = os.path.join(self.dir, "o%d" % n)
            with mock.patch.object(driver, "run_pilot", side_effect=lambda *a, sig=sig: os.kill(os.getpid(), sig)):
                code, _out, err = self.run_cli(self.fake_args(run_id, out=out))
            self.assertEqual((code, signal.getsignal(signal.SIGTERM), signal.getsignal(signal.SIGHUP)),
                             (P.EXIT_ERROR, before[0], before[1]))
            with open(os.path.join(out, "pilot-result.json"), encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["error"], "interrupted")

    def test_a_paid_call_that_raised_is_logged_with_its_ids(self):
        self.approve()
        base = fakes.FakeSampler(reply_tokens=[ord("a")] * 500, overrun=True)      # a service that ignores max_tokens
        svc = fakes.FakeService(checkpoint_samplers=[], base=base)
        with mock.patch.object(P, "fake_service", lambda *a: svc):
            code, _out, err = self.run_cli(self.fake_args())
        self.assertEqual(code, P.EXIT_ERROR)
        self.assertIn("more than the", err)
        with open(os.path.join(self.out, "replies.jsonl"), encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh]
        # a window of 8: the first reply is the overrun, and the 7 calls in flight with it are settled and logged
        self.assertEqual(len(rows), 8)
        self.assertEqual([r["status"] for r in rows], ["raised"] + ["drained"] * 7)
        self.assertEqual((rows[0]["outcome"], rows[0]["reply"]), ("", ""))
        for r in rows:
            self.assertEqual((r["returned"], r["returned_tokens"]), ([[ord("a")] * 500], 500))
        self.assertEqual([r["episode_id"] for r in rows],
                         [ep.id for ep in E.build_set("train", self.plan.eval1_counts, self.plan.eval1_offset).episodes[:8]])
        res = self.result()
        self.assertEqual((res["replies_logged"], res["spend"]["by_kind"]["sample"]["tokens"]), (8, 8 * 500))
        self.assertEqual(len(base.calls), 8)

    def test_with_a_window_of_one_a_paid_call_that_raised_is_the_only_one_logged(self):
        plan = cost.pilot_plan(CAP, 1)
        self.approve(plan=plan)
        base = fakes.FakeSampler(reply_tokens=[ord("a")] * 500, overrun=True)
        svc = fakes.FakeService(checkpoint_samplers=[], base=base)
        with mock.patch.object(P, "fake_service", lambda *a: svc):
            code, _out, err = self.run_cli(self.fake_args() + ["--window", "1"])
        self.assertEqual(code, P.EXIT_ERROR)
        with open(os.path.join(self.out, "replies.jsonl"), encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh]
        self.assertEqual(len(rows), 1)                                   # one paid call, stopped by the first overrun
        self.assertEqual((rows[0]["status"], rows[0]["outcome"], rows[0]["reply"]), ("raised", "", ""))
        self.assertEqual((rows[0]["returned"], rows[0]["returned_tokens"]), ([[ord("a")] * 500], 500))
        res = self.result()
        self.assertEqual((res["replies_logged"], res["spend"]["by_kind"]["sample"]["tokens"]), (1, 500))
        self.assertEqual(len(base.calls), 1)

    def test_an_error_after_the_start_writes_what_exists_and_exits_nonzero(self):
        self.approve()
        codec = driver.check_codec(fakes.FakeTokenizer())
        svc = P.fake_service(self.plan, codec)
        svc.fail_with = RuntimeError("the service went away")
        with mock.patch.object(P, "fake_service", lambda *a: svc):
            code, out, err = self.run_cli(self.fake_args())
        self.assertEqual(code, P.EXIT_ERROR)
        self.assertIn("pilot incomplete: ", err)
        res = self.result()
        self.assertEqual((res["status"], "measurements" in res, "gates" in res), ("incomplete", False, False))
        self.assertIn("the service went away", res["error"])
        self.assertGreater(res["spend"]["by_kind"]["prefill"]["tokens"], 0)         # the base model was already sampled
        self.assertEqual(res["replies_logged"], 200)                    # the base model, windowed and one at a time
        with open(os.path.join(self.out, "replies.jsonl"), encoding="utf-8") as fh:
            self.assertEqual(len(fh.readlines()), 200)
        with open(os.path.join(self.out, "pilot-result.json"), encoding="utf-8") as fh:
            receipts.check_plain(json.load(fh, parse_float=no_float))
        self.assertTrue(os.path.exists(os.path.join(self.out, "pilot-summary.md")))
        with open(os.path.join(self.out, "pilot-summary.md"), encoding="utf-8") as fh:
            self.assertIn("incomplete", fh.read())

    def test_a_stop_at_the_ceiling_is_an_incomplete_run(self):
        self.approve()
        with mock.patch.object(T.Meter, "reserve", side_effect=T.BudgetStop("a call would reach the ceiling")):
            code, _out, err = self.run_cli(self.fake_args())
        self.assertEqual(code, P.EXIT_ERROR)
        self.assertEqual(self.result()["status"], "incomplete")
        self.assertIn("would reach the ceiling", err)

    def test_an_interrupt_is_an_incomplete_run(self):
        self.approve()
        with mock.patch.object(driver, "run_pilot", side_effect=KeyboardInterrupt()):
            code, _out, _err = self.run_cli(self.fake_args())
        self.assertEqual(code, P.EXIT_ERROR)
        self.assertEqual(self.result()["error"], "interrupted")

    def test_logged_replies_that_do_not_give_the_recorded_outcomes_stop_the_run(self):
        self.approve()
        shim = types.SimpleNamespace(outcome_of=lambda *a: "P", DEFAULT_CAP=CAP)
        with mock.patch.object(P, "evaluate", shim):
            code, _out, err = self.run_cli(self.fake_args())
        self.assertEqual(code, P.EXIT_ERROR)
        self.assertIn("do not give its recorded outcomes", err)
        self.assertEqual(self.result()["status"], "incomplete")


class WriteOutputTests(Base):
    def test_a_float_in_the_result_is_refused_and_nothing_is_written(self):
        os.makedirs(self.out)
        with self.assertRaises(receipts.ReceiptError):
            P.write_outputs(self.out, {"status": "complete", "x": 0.5})
        self.assertEqual(os.listdir(self.out), [])
        with self.assertRaises(receipts.ReceiptError):
            P.write_outputs(self.out, {"status": "complete", "x": True})


class RecordingTests(Base):
    def test_a_call_that_raised_before_the_service_was_reached_is_not_logged(self):
        log = self.log("early.jsonl")

        def inner(view):
            raise RuntimeError("stopped before the service")
        inner.stats, inner.reached, inner.last_returned = {}, False, None
        rec = P.Recording(inner, self.ev, "base", log)
        with self.assertRaises(RuntimeError):
            rec(E.View(self.ev.episodes[0], "C"))
        self.assertEqual((log.count, rec.i), (0, 0))

    def test_an_interrupt_after_the_service_was_reached_is_logged_too(self):
        log = self.log("intr.jsonl")

        def inner(view):
            raise KeyboardInterrupt()
        inner.stats, inner.reached, inner.last_returned = {}, True, None
        rec = P.Recording(inner, self.ev, "base", log)
        with self.assertRaises(KeyboardInterrupt):
            rec(E.View(self.ev.episodes[0], "C"))
        self.assertEqual(log.count, 1)

    def test_a_call_that_raised_after_the_service_was_reached_is_logged_once_and_re_raised(self):
        log = self.log("late.jsonl")

        def inner(view):
            raise RuntimeError("settle failed")
        inner.stats, inner.reached, inner.last_returned = {}, True, [[7, 8, 9]]
        rec = P.Recording(inner, self.ev, "base", log)
        with self.assertRaises(RuntimeError):
            rec(E.View(self.ev.episodes[0], "C"))
        self.assertEqual((log.count, rec.i, rec.outcomes), (1, 0, []))
        with open(os.path.join(self.dir, "late.jsonl"), encoding="utf-8") as fh:
            row = json.loads(fh.read())
        self.assertEqual((row["status"], row["returned"], row["returned_tokens"], row["episode_id"]),
                         ("raised", [[7, 8, 9]], 3, self.ev.episodes[0].id))

    def setUp(self):
        super().setUp()
        self.codec = driver.check_codec(fakes.FakeTokenizer())
        self.ev = E.build_set("train", self.plan.eval1_counts, self.plan.eval1_offset)

    def log(self, name="replies.jsonl"):
        log = P.ReplyLog(os.path.join(self.dir, name))
        self.addCleanup(log.close)
        return log

    def inner(self):
        calls = []

        def inner(view):
            calls.append(view)
            return "x0 = 0", 3, False
        inner.stats = {"calls": 0}
        return inner, calls

    def test_only_the_pilot_plan_with_no_second_set_may_be_recorded(self):
        for i, plan in enumerate((cost.full_plan(2048, 2, CAP), cost.full_plan(64, 2, CAP, heldout_per_tier=10))):
            with self.assertRaises(P.PilotCliError):
                with P.recording(plan, self.log("a%d.jsonl" % i)):
                    pass
        two = cost.pilot_plan(CAP)
        two.eval2_counts = {"S": 1}
        with self.assertRaises(P.PilotCliError):
            with P.recording(two, self.log("two.jsonl")):
                pass

    def test_a_held_out_evaluation_set_is_refused(self):
        held = E.build_set("heldout1", {"S": 2})
        with mock.patch.object(E, "build_set", lambda *a, **kw: held):
            with self.assertRaises(P.PilotCliError):
                with P.recording(self.plan, self.log()):
                    pass

    def test_a_request_for_a_held_out_episode_is_refused_before_the_sampler_is_called(self):
        held = E.build_set("heldout1", {"S": 1})
        inner, calls = self.inner()
        rec = P.Recording(inner, self.ev, "base", self.log())
        with self.assertRaises(P.PilotCliError):
            rec(E.View(held.episodes[0], "C"))
        self.assertEqual(calls, [])

    def test_a_request_out_of_order_or_in_another_text_is_refused(self):
        inner, calls = self.inner()
        rec = P.Recording(inner, self.ev, "base", self.log())
        with self.assertRaises(P.PilotCliError):
            rec(E.View(self.ev.episodes[1], "C"))
        with self.assertRaises(P.PilotCliError):
            rec(E.View(self.ev.episodes[0], "B"))
        self.assertEqual(calls, [])
        rec(E.View(self.ev.episodes[0], "C"))
        self.assertEqual(len(calls), 1)

    def test_finish_settles_the_inner_responder_and_logs_the_calls_that_were_paid_for_and_not_handed_back(self):
        calls = []

        class Inner:
            stats = {}
            orphans = [{"index": 3, "returned": [[5, 6, 7]]}, {"index": 4, "returned": None}]

            def finish(self_):
                calls.append("finish")
        log = self.log("orph.jsonl")
        rec = P.Recording(Inner(), self.ev, "base", log)
        rec.finish()
        self.assertEqual(calls, ["finish"])
        with open(os.path.join(self.dir, "orph.jsonl"), encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh]
        self.assertEqual([r["episode_id"] for r in rows], [self.ev.episodes[3].id, self.ev.episodes[4].id])
        self.assertEqual([(r["status"], r["returned"], r["returned_tokens"], r["outcome"]) for r in rows],
                         [("drained", [[5, 6, 7]], 3, ""), ("drained", None, 0, "")])
        self.assertEqual(Inner.orphans[:0], [])
        rec.finish()                                                 # the rows are written once
        self.assertEqual(log.count, 2)

    def test_more_requests_than_episodes_are_refused(self):
        inner, calls = self.inner()
        rec = P.Recording(inner, self.ev, "base", self.log())
        for ep in self.ev.episodes:
            rec(E.View(ep, "C"))
        with self.assertRaises(P.PilotCliError):
            rec(E.View(self.ev.episodes[0], "C"))
        self.assertEqual(len(calls), 100)

    def test_a_third_sampling_model_is_refused_with_a_window_of_one(self):
        run = mock.Mock()
        with mock.patch.object(driver, "responder", lambda *a: self.inner()[0]):
            with P.recording(cost.pilot_plan(CAP, 1), self.log()):
                driver.responder(run, None, self.codec, CAP)
                driver.responder(run, None, self.codec, CAP)
                with self.assertRaises(P.PilotCliError):
                    driver.responder(run, None, self.codec, CAP)

    def test_a_window_above_one_allows_three_sampling_evaluations_and_refuses_a_fourth(self):
        run = mock.Mock()
        with mock.patch.object(driver, "responder", lambda *a: self.inner()[0]):
            with P.recording(self.plan, self.log()) as made:
                for _ in range(3):
                    driver.responder(run, None, self.codec, CAP, [], 8)
                with self.assertRaises(P.PilotCliError):
                    driver.responder(run, None, self.codec, CAP, [], 8)
        self.assertEqual([r.model for r in made], ["base", "base-sequential", "adapter"])

    def test_driver_responder_is_put_back(self):
        before = driver.responder
        with P.recording(self.plan, self.log()):
            self.assertIsNot(driver.responder, before)
        self.assertIs(driver.responder, before)
        with self.assertRaises(RuntimeError):
            with P.recording(self.plan, self.log("again.jsonl")):
                raise RuntimeError("x")
        self.assertIs(driver.responder, before)

    def test_the_recording_passes_the_stats_and_the_reply_through(self):
        inner, _calls = self.inner()
        rec = P.Recording(inner, self.ev, "adapter", self.log())
        self.assertIs(rec.stats, inner.stats)
        self.assertEqual(rec(E.View(self.ev.episodes[0], "C")), ("x0 = 0", 3, False))
        self.assertEqual(rec.outcomes, ["X"])

    def test_a_reply_is_in_the_file_as_soon_as_it_is_written(self):
        log = self.log("live.jsonl")
        log.write({"model": "base", "n": 1})
        with open(os.path.join(self.dir, "live.jsonl"), encoding="utf-8") as fh:        # the log is still open
            self.assertEqual(json.loads(fh.read()), {"model": "base", "n": 1})
        self.assertEqual(log.count, 1)

    def test_the_log_refuses_an_existing_file(self):
        self.log("same.jsonl")
        with self.assertRaises(FileExistsError):
            P.ReplyLog(os.path.join(self.dir, "same.jsonl"))


class WindowOptionTests(Base):
    LEGACY = "588a6b6c0082ae7a1b898dade6d4ec713ead807eceeef967a4e927e341c57aa0"

    def row(self, *extra):
        code, out, err = self.run_cli(["--run-id", "pilot-7", "--print-approval-row", *extra])
        self.assertEqual((code, err), (0, ""))
        return json.loads(out)

    def test_the_default_window_is_the_proposed_one(self):
        self.assertEqual(P.PILOT_WINDOW, 8)
        self.assertEqual(self.row(), driver.approval_row("pilot-7", "0.50", cost.pilot_plan(CAP, 8)))
        self.assertEqual(self.row("--window", "8"), self.row())

    def test_a_window_of_one_names_the_plan_of_the_first_pilot(self):
        self.assertEqual(self.row("--window", "1")["plan_id"], self.LEGACY)
        self.assertNotEqual(self.row()["plan_id"], self.LEGACY)
        self.assertNotEqual(self.row("--window", "2")["plan_id"], self.row("--window", "3")["plan_id"])

    def test_a_window_that_is_not_a_whole_number_in_range_is_refused(self):
        for bad in ("0", "65", "-1", "x", "", "2.5", "\u0668"):
            code, _out, err = self.run_cli(["--run-id", "pilot-7", "--print-approval-row", "--window", bad])
            self.assertEqual(code, P.EXIT_REFUSED, bad)
            self.assertIn("window", err)
        code, _out, err = self.run_cli(["--run-id", "pilot-7", "--print-approval-row", "--window"])
        self.assertEqual(code, P.EXIT_REFUSED)

    def test_an_approval_for_one_window_does_not_start_a_run_with_another(self):
        self.approve()                                                     # window 8
        code, _out, err = self.run_cli(self.fake_args() + ["--window", "1"])
        self.assertEqual(code, P.EXIT_REFUSED)
        self.assertIn("another plan", err)
        self.assertFalse(os.path.exists(self.out))
        code, _out, err = self.run_cli(self.fake_args() + ["--window", "4"])
        self.assertEqual(code, P.EXIT_REFUSED)

    def test_a_fake_run_with_a_window_of_one_is_the_first_pilots_plan_without_the_check(self):
        plan = cost.pilot_plan(CAP, 1)
        self.approve(plan=plan)
        code, out, err = self.run_cli(self.fake_args() + ["--window", "1"])
        self.assertEqual((code, err), (0, ""))
        res = self.result()
        self.assertEqual((res["plan_id"], res["measurements"]["window"]), (self.LEGACY, 1))
        self.assertNotIn("windowed_replies_equal", res["gates"])
        self.assertEqual(sorted(res["outcomes"]), ["adapter", "base"])
        self.assertEqual(res["replies_logged"], 200)

    def test_a_window_run_logs_the_check_and_reports_it(self):
        self.approve()
        code, out, err = self.run_cli(self.fake_args())
        self.assertEqual((code, err), (0, ""))
        res = self.result()
        self.assertEqual(res["gates"]["windowed_replies_equal"], "true")
        m = res["measurements"]
        self.assertEqual((m["window"], m["window_check_calls"], m["window_check_differing"]), (8, 100, 0))
        self.assertEqual(sorted(res["outcomes"]), ["adapter", "base", "base-sequential"])
        self.assertEqual(res["outcomes"]["base"], res["outcomes"]["base-sequential"])


    def test_a_failure_in_the_middle_of_a_window_logs_the_raised_call_and_every_call_that_was_in_flight(self):
        self.approve()
        codec = driver.check_codec(fakes.FakeTokenizer())
        ev = E.build_set("train", self.plan.eval1_counts, self.plan.eval1_offset)
        views = driver.epset_views(ev, "C")
        mapping = {tuple(codec.prompt_ids(v.messages)): codec.target_ids(E.render(ep, "A").attempt_text)
                   for v, ep in zip(views, ev.episodes)}
        base = fakes.WindowSampler(reply_for=lambda toks: mapping[tuple(toks)], fail_result=[5])
        svc = fakes.FakeService(checkpoint_samplers=[], base=base)
        with mock.patch.object(P, "fake_service", lambda *a: svc):
            code, _out, err = self.run_cli(self.fake_args())
        self.assertEqual(code, P.EXIT_ERROR)
        self.assertIn("the call failed", err)
        with open(os.path.join(self.out, "replies.jsonl"), encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh]
        self.assertEqual([r["status"] for r in rows], ["ok"] * 5 + ["raised"] + ["drained"] * 7)
        self.assertEqual([r["episode_id"] for r in rows], [ep.id for ep in ev.episodes[:5]] + [ev.episodes[5].id]
                         + [ep.id for ep in ev.episodes[6:13]])
        self.assertIsNone(rows[5]["returned"])                           # the service failed before any answer
        self.assertTrue(all(r["returned"] and r["outcome"] == "" for r in rows[6:]))
        self.assertEqual(self.result()["replies_logged"], 13)
        self.assertEqual((len(base.calls), base.outstanding), (13, 0))
        spent, tokens, _starts, _plan = T.Ledger(self.approvals + ".spend.jsonl", "pilot-1").replay()
        self.assertEqual(tokens["sample"], sum(len(q) for r in rows if r["returned"] for q in r["returned"]) + 97)


class CounterTests(unittest.TestCase):
    def test_the_counter_counts_with_the_tokenizer(self):
        c = P.TokenizerCounter(fakes.FakeTokenizer())
        self.assertEqual(c.count(["abc", "", "xy"]), [3, 0, 2])
        self.assertEqual(c.source, "tokenizer")


if __name__ == "__main__":
    unittest.main()
