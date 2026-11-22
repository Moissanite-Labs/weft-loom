"""Command line runner for the pilot (PREREG.md, "After the pilot").

    python3 pilot_cli.py --run-id ID --print-approval-row [--window N]
    python3 pilot_cli.py --approvals PATH --run-id ID --out DIR [--fake] [--window N]

--window N is the number of sampling calls in flight at once (default 8, a choice
of the proposal this branch holds, not approved). The window is part of the plan
fingerprint, so the approval row names it. A window above 1 adds one evaluation
to the pilot: the untrained model sampled one call at a time on the same puzzles,
whose replies must equal the windowed ones. A window of 1 is the plan of the
first pilot.

--print-approval-row prints the one JSON row the owner puts in the approvals
file for this run id and the pilot plan, with the pilot ceiling, and stops.

The real mode takes the service key only from the environment variable the
client library reads. It never opens a key file, never prints the variable, and
passes every exception text through the backend's redact function before the
text is printed or written. The runner registers the variable's value with the
backend first, so redact removes the key's own value, whatever characters it
holds, before the pattern and the 400-character cut apply, including for errors
raised inside a service call.
It refuses to start unless the variable is set and non-empty, so the library
cannot fall back to a stored credentials file.

Before the first service call it prints the planned cost and the ceiling. The
service object is made inside driver.start_run only after the approval, the
plan, the ceiling and the lock have all been checked.

--out must be a new or empty directory. It receives:
  pilot-result.json   integers and strings only: measurements, gates, counts by
                      outcome, tokens and exact dollars spent by kind (from the
                      spend ledger), time totals in nanoseconds with their counts
                      (the sampling time is the wall-clock time of the evaluations
                      as wholes, see driver.run_pilot)
  replies.jsonl       one line per call that reached the service, written as each
                      reply is handed back: the decoded reply, and the ids and their
                      count exactly as the service returned them. A call that raised
                      after the service was reached has a row with status
                      "raised" and an empty outcome. With a window, a call that was
                      in flight when another failed has a row with status "drained"
                      and the ids it returned (or none), and its model
  receipts.jsonl      the chain of receipts (with its stored replies and lock)
  pilot-summary.md    a short table a person can read
On any error after the run has started the same files are written with what
exists, the result says "incomplete" with the redacted error, and the exit
status is 1. Refusals before the run starts exit with status 2, write no file
and make no --out directory (it is made only after the run has started).
SIGINT, SIGTERM and SIGHUP are treated alike: the run is written as incomplete
with the error "interrupted". A finished pilot exits 0, whether the gates give a go or a no-go.

--fake runs the same code path against fakes.py (no key, no network).

The pilot evaluates on training-range seeds only. The runner builds the
expected evaluation set itself, refuses a plan that is not the pilot or that
holds a second set, and refuses any reply request that is not the next episode
of that training-range set.
"""
import contextlib
import json
import os
import signal
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost  # noqa: E402
import driver  # noqa: E402
import episodes as ep_mod  # noqa: E402
import evaluate  # noqa: E402
import fakes  # noqa: E402
import ratchet as ratchet_mod  # noqa: E402
import receipts  # noqa: E402
import tinker_backend  # noqa: E402

KEY_VAR = "TINKER_API_KEY"
PILOT_CEILING = Fraction(1, 2)                  # the pilot's registered ceiling in dollars (PREREG.md, Spend)
FULL_EXAMPLES, FULL_SEEDS = 2048, 2             # the full plan the time projection is made for
PILOT_WINDOW = cost.PROPOSED_WINDOW             # the window of the proposed pilot (a choice, not approved)
MODEL_ORDER = ("base", "adapter")               # the order run_pilot samples its models in with a window of 1
WINDOWED_ORDER = ("base", "base-sequential", "adapter")     # and with a window above 1


def model_order(plan):
    return WINDOWED_ORDER if plan.window > 1 else MODEL_ORDER
EXIT_OK, EXIT_ERROR, EXIT_REFUSED = 0, 1, 2


class PilotCliError(Exception):
    pass


def scrub(exc, env):
    """Text of an exception that is safe to print or store: the key variable's own
    value removed, then the backend's redact (which also removes the values main
    registered, before the pattern and the length cut)."""
    text = "%s: %s" % (type(exc).__name__, exc)
    key = env.get(KEY_VAR, "")
    if key:
        text = text.replace(key, "[REDACTED]")
    return tinker_backend.redact(text)


class TokenizerCounter:
    """cost.plan_counts counter that counts with a tokenizer's encode_ordinary."""
    source = "tokenizer"

    def __init__(self, tok):
        self.tok = tok

    def count(self, texts):
        return [len(self.tok.encode_ordinary(t)) for t in texts]


# ------------------------------------------------------------------ raw replies

class ReplyLog:
    """Appends one JSON line per sampled reply, flushed to the file as it arrives."""

    def __init__(self, path):
        self.fh = open(path, "x", encoding="utf-8")
        self.count = 0

    def write(self, row):
        self.fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        self.fh.flush()
        self.count += 1

    def close(self):
        self.fh.close()


class Recording:
    """Wraps a TinkerResponder. Each request must be the next episode of the
    expected training-range evaluation set, in text C; the reply is logged
    with its model, tier, seed and outcome."""

    def __init__(self, inner, expected, model, log):
        self.inner, self.expected, self.model, self.log = inner, expected, model, log
        self.i = 0
        self.outcomes = []

    @property
    def stats(self):
        return self.inner.stats

    def finish(self):
        """Settles the calls the inner responder still has in flight, and logs the
        replies of those that were paid for and not handed back."""
        try:
            driver.settled(self.inner)
        finally:
            self._write_orphans()

    def _write_orphans(self):
        for o in getattr(self.inner, "orphans", []):
            if 0 <= o["index"] < len(self.expected.episodes):
                ep = self.expected.episodes[o["index"]]
                self.log.write({"model": self.model, "episode_id": ep.id, "tier": ep.tier, "seed": ep.seed, "arm": "C",
                                "status": "drained", "reply": "", "tokens": 0, "cut": 0, "outcome": "",
                                "returned": o["returned"],
                                "returned_tokens": sum(len(q) for q in o["returned"]) if o["returned"] else 0})
        if hasattr(self.inner, "orphans"):
            self.inner.orphans = []

    def __call__(self, view):
        if self.i >= len(self.expected.episodes):
            raise PilotCliError("more reply requests than the pilot's evaluation episodes")
        ep = self.expected.episodes[self.i]
        want = ep_mod.View(ep, "C")
        if view.arm != "C" or view.messages != want.messages:
            raise PilotCliError("a reply was requested for something other than the next pilot evaluation episode")
        try:
            text, count, was_cut = self.inner(view)
        except BaseException:
            if getattr(self.inner, "reached", False):       # paid for, so it is evidence
                self._write(ep, "raised", "", 0, 0, "")
            raise
        self.i += 1
        outcome = evaluate.outcome_of(ep_mod.rsig(), ep, text, was_cut)
        self.outcomes.append(outcome)
        self._write(ep, "ok", text, count, 1 if was_cut else 0, outcome)
        return text, count, was_cut

    def _write(self, ep, status, text, count, cut, outcome):
        got = getattr(self.inner, "last_returned", None)     # the ids exactly as the service returned them
        self.log.write({"model": self.model, "episode_id": ep.id, "tier": ep.tier, "seed": ep.seed, "arm": "C",
                        "status": status, "reply": text, "tokens": count, "cut": cut, "outcome": outcome,
                        "returned": got, "returned_tokens": sum(len(q) for q in got) if got else 0})


@contextlib.contextmanager
def recording(plan, log):
    """Makes driver.responder return a Recording for each of the pilot's two models."""
    if plan.name != "pilot" or plan.eval2_counts:
        raise PilotCliError("the runner runs the pilot plan only, with no second evaluation set")
    expected = ep_mod.build_set("train", plan.eval1_counts, plan.eval1_offset)
    if expected.kind != "train":
        raise PilotCliError("the pilot's evaluation set is not a training-range set")
    original, made = driver.responder, []

    order = model_order(plan)

    def make(run, sampler, codec, cap, views=None, window=1):
        if len(made) >= len(order):
            raise PilotCliError("the pilot made more than %d sampling evaluations" % len(order))
        rec = Recording(original(run, sampler, codec, cap, views, window), expected, order[len(made)], log)
        made.append(rec)
        return rec
    driver.responder = make
    try:
        yield made
    finally:
        driver.responder = original


# ------------------------------------------------------------------ output files

def true_false(b):
    return "true" if b else "false"


def spend_from_ledger(approvals_path, run_id):
    """Tokens and exact dollars by kind, replayed from the spend ledger."""
    spent, tokens, _starts, _plan = tinker_backend.Ledger(approvals_path + ".spend.jsonl", run_id).replay()
    by_kind = {k: {"tokens": tokens[k], "usd": str(tinker_backend.cost_usd(k, tokens[k]))} for k in sorted(tokens)}
    return {"by_kind": by_kind, "total_usd": str(spent)}


def counts_by_outcome(outcomes):
    return {k: outcomes.count(k) for k in ("P", "F", "X")}


def build_result(run_id, plan_id, ceiling, planned, mode, spend, error, got, rows_logged):
    res = {"status": "incomplete" if error else "complete", "error": error, "run_id": run_id, "plan": "pilot",
           "plan_id": plan_id, "mode": mode, "ceiling_usd": str(ceiling), "planned_cost_usd": str(planned),
           "spend": spend, "replies_logged": rows_logged}
    if got is not None:
        m = got["measurements"]
        res["measurements"] = {k: m[k] for k in sorted(m)}
        res["gates"] = {k: true_false(v) for k, v in sorted(got["gates"].items())}
        res["go"] = true_false(got["gates"]["go"])
        res["outcomes"] = {name: counts_by_outcome(got["results"][name].outcomes) for name in WINDOWED_ORDER if name in got["results"]}
        res["timing"] = {"sampling_calls": m["calls"], "sampling_ns_total": m["sample_ns"],
                         "train_steps": m["steps"], "train_ns_total": m["train_ns"]}
    return res


def summary_text(res):
    lines = ["# Pilot summary", "", "Run %s, status %s." % (res["run_id"], res["status"])]
    if res["error"]:
        lines += ["", "Error (redacted): %s" % res["error"]]
    if "gates" in res:
        lines += ["", "| Gate | Result |", "|---|---|"]
        lines += ["| %s | %s |" % (k, v) for k, v in res["gates"].items()]
        lines += ["", "| Model | Passed | Failed the check | Broke the format |", "|---|---|---|---|"]
        for name in WINDOWED_ORDER:
            if name in res["outcomes"]:
                o = res["outcomes"][name]
                lines.append("| %s | %d | %d | %d |" % (name, o["P"], o["F"], o["X"]))
        t = res["timing"]
        lines += ["", "Sampling: %d calls, %d ns of wall-clock time over the evaluations as wholes, window %d. "
                  "Training: %d steps, %d ns in total."
                  % (t["sampling_calls"], t["sampling_ns_total"], res["measurements"]["window"], t["train_steps"],
                     t["train_ns_total"])]
        m = res["measurements"]
        if "window_check_calls" in m:
            lines += ["", "Window check: %d replies of the untrained model sampled one call at a time, %d differ from "
                      "the windowed replies." % (m["window_check_calls"], m["window_check_differing"])]
    lines += ["", "| Spend | Tokens | Dollars |", "|---|---|---|"]
    for kind, row in res["spend"]["by_kind"].items():
        lines.append("| %s | %d | %s |" % (kind, row["tokens"], row["usd"]))
    lines += ["", "Total spent: %s dollars, ceiling %s, planned %s." % (
        res["spend"]["total_usd"], res["ceiling_usd"], res["planned_cost_usd"]), ""]
    return "\n".join(lines)


def write_outputs(out, res):
    receipts.check_plain(res, "pilot-result")          # integers and strings only
    with open(os.path.join(out, "pilot-result.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, sort_keys=True, indent=1)
        fh.write("\n")
    with open(os.path.join(out, "pilot-summary.md"), "w", encoding="utf-8") as fh:
        fh.write(summary_text(res))


# ------------------------------------------------------------------ the run

def fake_service(plan, codec):
    """A fake service for --fake: the base model repeats the failed attempt, the adapter repairs 60 of 100."""
    ev = ep_mod.build_set("train", plan.eval1_counts, plan.eval1_offset)
    fails = [ep_mod.render(ep, "A").attempt_text for ep in ev.episodes]
    wins = [ep_mod.render(ep, "A").target_text for ep in ev.episodes]
    mixed = [wins[i] if i < 60 else fails[i] for i in range(len(fails))]
    adapter = fakes.ScriptedSampler(mixed, codec.target_ids)
    return fakes.FakeService(checkpoint_samplers=[adapter], base=fakes.ScriptedSampler(fails, codec.target_ids))


@contextlib.contextmanager
def fake_backend(plan, codec):
    """For --fake: the backend's factories for the service and its types return fakes."""
    saved = tinker_backend._real_service, tinker_backend._real_types
    tinker_backend._real_service = lambda: fake_service(plan, codec)
    tinker_backend._real_types = lambda: fakes.FakeTypes
    try:
        yield
    finally:
        tinker_backend._real_service, tinker_backend._real_types = saved


def parse_args(argv):
    opts = {"approvals": None, "run_id": None, "out": None, "fake": False, "print_row": False, "window": PILOT_WINDOW}
    flags = {"--approvals": "approvals", "--run-id": "run_id", "--out": "out", "--window": "window"}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--window" and i + 1 < len(argv):
            if not argv[i + 1].isascii() or not argv[i + 1].isdigit():
                raise PilotCliError("--window must be a whole number")
            try:
                opts["window"] = tinker_backend.check_window(int(argv[i + 1]))
            except tinker_backend.BackendError as exc:
                raise PilotCliError(str(exc))
            i += 2
        elif a in flags and i + 1 < len(argv):
            opts[flags[a]] = argv[i + 1]
            i += 2
        elif a == "--fake":
            opts["fake"] = True
            i += 1
        elif a == "--print-approval-row":
            opts["print_row"] = True
            i += 1
        else:
            raise PilotCliError("unknown or incomplete option %r" % (a,))
    return opts


def prepare(opts, env, cap, out_msg):
    """Everything before the run starts. Returns (plan, codec, counter, approval). Refuses by raising."""
    if not opts["approvals"] or not opts["run_id"] or not opts["out"]:
        raise PilotCliError("--approvals, --run-id and --out are all required")
    out = opts["out"]
    if os.path.exists(out) and (not os.path.isdir(out) or os.listdir(out)):
        raise PilotCliError("--out must be a new or empty directory")
    if not opts["fake"] and not env.get(KEY_VAR):
        raise PilotCliError("the environment variable %s must be set and non-empty" % KEY_VAR)
    plan = cost.pilot_plan(cap, opts["window"])
    approval = tinker_backend.load_approval(opts["approvals"], opts["run_id"])
    if approval.ceiling > PILOT_CEILING:
        raise PilotCliError("the approved ceiling %s is above the pilot's registered ceiling %s" % (
            approval.ceiling, PILOT_CEILING))
    # the fake tokenizer meters one token per character, so the fake plan counts that too
    tok = fakes.FakeTokenizer() if opts["fake"] else tinker_backend.real_tokenizer()
    counter = TokenizerCounter(tok)
    codec = driver.check_codec(tok)
    totals, _items = cost.plan_counts(plan, counter)
    planned = tinker_backend.planned_cost(totals)
    out_msg("planned cost %s dollars (about %s, token counts from the %s), ceiling %s dollars"
            % (planned, cost.usd_text(planned), counter.source, approval.ceiling))
    return plan, codec, counter, approval, planned


def _interrupt(signum, _frame):
    raise KeyboardInterrupt()


def main(argv=None, env=None):
    """Registers the key's value with the backend's redact and turns SIGTERM and SIGHUP into the same
    interrupt as SIGINT for the length of the run, then runs the pilot."""
    env = os.environ if env is None else env
    tinker_backend.set_secret_values([env.get(KEY_VAR, "")])
    old = {}
    for sig in (signal.SIGTERM, signal.SIGHUP):
        try:
            old[sig] = signal.signal(sig, _interrupt)
        except ValueError:                  # not the main thread: the handlers cannot be set
            pass
    try:
        return _main(argv, env)
    finally:
        for sig, handler in old.items():
            signal.signal(sig, handler)
        tinker_backend.set_secret_values([])


def _main(argv, env):
    argv = sys.argv[1:] if argv is None else list(argv)
    out_msg = print
    try:
        opts = parse_args(argv)
        cap = evaluate.DEFAULT_CAP
        if opts["print_row"]:
            if not opts["run_id"]:
                raise PilotCliError("--run-id is required")
            print(json.dumps(driver.approval_row(opts["run_id"], "0.50", cost.pilot_plan(cap, opts["window"])), sort_keys=True))
            return EXIT_OK
        plan, codec, counter, approval, planned = prepare(opts, env, cap, out_msg)
        big = cost.full_plan(FULL_EXAMPLES, FULL_SEEDS, cap, window=opts["window"])
    except (PilotCliError, tinker_backend.ApprovalError, tinker_backend.BudgetError, tinker_backend.BudgetStop,
            driver.DriverError, OSError) as exc:
        print("refused: %s" % scrub(exc, env), file=sys.stderr)
        return EXIT_REFUSED
    out, run_id = opts["out"], opts["run_id"]
    plan_id = driver.plan_fingerprint(plan)
    mode = "fake" if opts["fake"] else "real"
    got, made, error, log = None, [], "", None
    try:
        # --fake only swaps the two factories that build the service and its types, so the order of the
        # approval, plan, ceiling and lock checks before the service is made is the real order
        with fake_backend(plan, codec) if opts["fake"] else contextlib.nullcontext():
            run = driver.start_run(run_id, opts["approvals"], plan, counter)
    except (Exception,) as exc:             # nothing was spent: the run did not start
        print("refused: %s" % scrub(exc, env), file=sys.stderr)
        return EXIT_REFUSED
    try:
        os.makedirs(out, exist_ok=True)     # only now: a refusal above leaves no directory behind
    except OSError as exc:
        run.close()
        print("refused: %s" % scrub(exc, env), file=sys.stderr)
        return EXIT_REFUSED
    try:
        with run:
            rt = ratchet_mod.Ratchet(os.path.join(out, "receipts.jsonl"), os.path.join(out, "latch.jsonl"),
                                     os.path.join(out, "lock.json"), cap)
            log = ReplyLog(os.path.join(out, "replies.jsonl"))
            with recording(plan, log) as made:
                got = driver.run_pilot(run, rt, codec, run_id, plan, {"cap": cap, "plan_id": plan_id, "mode": mode},
                                       big)
                for rec, name in zip(made, model_order(plan)):
                    if "".join(rec.outcomes) != got["results"][name].outcomes:
                        raise PilotCliError("the logged replies of the %s model do not give its recorded outcomes" % name)
    except (Exception, KeyboardInterrupt) as exc:
        error = scrub(exc, env) if not isinstance(exc, KeyboardInterrupt) else "interrupted"
        got = None
    finally:
        if log is not None:
            log.close()
    try:
        spend = spend_from_ledger(opts["approvals"], run_id)
    except (Exception,) as exc:
        spend = {"by_kind": {}, "total_usd": "0"}
        error = error or "the spend ledger could not be read: %s" % scrub(exc, env)
    res = build_result(run_id, plan_id, approval.ceiling, planned, mode, spend, error, got,
                       log.count if log is not None else 0)
    write_outputs(out, res)
    if error:
        print("pilot incomplete: %s" % error, file=sys.stderr)
        return EXIT_ERROR
    print("pilot complete: go=%s, spent %s dollars, results in %s" % (res["go"], spend["total_usd"],
                                                                      os.path.join(out, "pilot-result.json")))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
