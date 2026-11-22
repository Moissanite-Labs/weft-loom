"""The paid-run driver: training, evaluation and the registered comparisons.

It ties the pieces together in the order the preregistration states, and is
tested end to end against fakes.py. Nothing in this file calls the service by
itself: it works through a tinker_backend.TinkerRun, whose construction needs an
approval for the run id and a budget under the ceiling. start_run builds that
run with the plan computed from cost.py for this configuration.

Every prompt that is sampled from, for the untrained model and every adapter,
ends with the forced opening of the model's turn (codec.Codec.prompt_ids), so
the cap of reply tokens counts answer tokens only, for every arm alike.

Order of a registered run (run_registered):
  1. the untrained model on held-out set 1, every text (exploratory baseline)
  2. for each training seed and each arm A, B, C: train 64 steps, save the one
     checkpoint, evaluate on held-out set 1 with the arm's own text. The
     adapter trained on C is also evaluated on the texts B, E and N, on the
     same episodes (the test-time controls).
  3. the paired comparisons on held-out set 1, for each seed
  4. only if both seeds pass every set 1 condition, the one touch of
     held-out set 2 for the registered decision, then the same comparisons
     on it for seed 0. Otherwise set 2 is never touched.

The decision rule (support needs every item, each at alpha, so no alpha split):
  1. C beats B on pass rate, all episodes, for both seeds on set 1
  2. the same on the stratum where neither adapter broke the format, both seeds
  3. B does not beat C on staying in the format at alpha, both seeds (a no-harm
     gate, not a test of equivalence)
  4. items 1 to 3 on set 2 for seed 0
Before an item 1 or 2 test counts, the comparison must be testable: at least
GATES.min_discordant discordant episodes, and neither adapter at or under
GATES.rate_low or at or over GATES.rate_high on pass rate. A comparison that is
not testable gives the verdict "cannot_test", not "not_supported". Item 3 has
no testability condition and is read first in judge(): a format harm gives
"not_supported" whether or not items 1 and 2 could be tested. The text E
and N controls (the C adapter on other texts) are read, never decided on: they
do not change the verdict (see control_readings).

A run is tied to one plan, and the plan is the one the owner approved: each row
of the approvals file names a plan and its fingerprint, TinkerRun refuses a
different plan, and start_run is the only place that counts a plan's tokens
(it marks the run with the fingerprint it counted). run_registered runs only the
full plan and run_pilot only the pilot plan, and each refuses a run that was
not counted for the plan given. The full run does not check that a pilot gave a
go: the go is the owner's call before the full run is approved (PREREG.md,
"After the pilot"). Before the one touch of set 2,
the remaining ceiling must cover the four set-2 evaluations at their upper bounds.
"""
import hashlib
import random
import time
from collections import namedtuple
from fractions import Fraction

import codec as codec_mod
import cost
import episodes as ep_mod
import evaluate
import power
import tinker_backend

BATCH_SIZE = 32                     # choice
LEARNING_RATE = 1e-3                # choice, not tuned
LORA_RANK = 8                       # choice
DECISION_ID = "primary-c-vs-b-seed0-confirm"
CONTROL_TEXTS = ("B", "E", "N")     # shown to the adapter trained on C


Gates = namedtuple("Gates", "min_discordant rate_low rate_high")
# choice (PREREG.md): at least 10 discordant episodes, and a pass rate over
# 5 percent and under 95 percent for both adapters, or the set cannot test the claim
GATES = Gates(power.MIN_DISCORDANT, Fraction(1, 20), Fraction(19, 20))

# Pilot gates (choices, PREREG.md). The pilot passes only if all hold.
PILOT_MAX_NEW_BLOCK = Fraction(1, 20)        # replies that open a new block of their own, among all sampled replies
PILOT_MAX_FORMAT_BREAK = Fraction(1, 5)      # adapter format breaks, text C
PILOT_RATE_LOW, PILOT_RATE_HIGH = Fraction(1, 20), Fraction(19, 20)    # adapter pass rate must be testable
PILOT_MAX_HOURS = 12                         # projected sampling plus training time of the full plan
NS_PER_HOUR = 3600 * 10**9


class DriverError(Exception):
    pass


def plan_fingerprint(plan):
    """A hash of everything that defines a plan, so a run id can be tied to one plan."""
    return evaluate.canonical_sha256({
        "name": plan.name, "arms": list(plan.arms), "train_counts": plan.train_counts, "seeds": plan.seeds,
        "epochs": plan.epochs, "eval1_counts": plan.eval1_counts, "eval2_counts": plan.eval2_counts,
        "cap": plan.cap, "train_offset": plan.train_offset, "eval1_offset": plan.eval1_offset,
        "evals": [[e.label, e.text_arm, e.set_key, e.runs] for e in plan.evals]})


def approval_row(run_id, ceiling, plan):
    """The approvals-file row the owner writes for a run id, naming the plan it approves."""
    return {"run_id": run_id, "ceiling_usd": ceiling, "plan": plan.name, "plan_id": plan_fingerprint(plan)}


def start_run(run_id, approvals_path, plan, counter, service=None, types_mod=None, resume=False):
    """A TinkerRun whose planned token counts come from cost.py for this plan.
    The approval for the run id must name this plan and its fingerprint. The
    run is marked with the fingerprint of the plan that was counted."""
    totals, _items = cost.plan_counts(plan, counter)
    fingerprint = plan_fingerprint(plan)
    run = tinker_backend.TinkerRun(run_id, approvals_path, totals, plan.name, fingerprint, service, types_mod, resume)
    run.counted_plan = fingerprint
    return run


def require_plan_run(run, plan, name):
    """Refuses a run that was not started for this plan, a plan of another
    kind, or a run whose token counts did not come from start_run for this plan."""
    if plan.name != name:
        raise DriverError("this function runs the %s plan, not %r" % (name, plan.name))
    fingerprint = plan_fingerprint(plan)
    if run.plan_id != fingerprint:
        raise DriverError("the run was started for a different plan than the one given")
    if getattr(run, "counted_plan", None) != fingerprint:
        raise DriverError("the run's token counts were not made by start_run for this plan")


def shuffled_order(n, seed, label):
    digest = hashlib.sha256(("order/%s/%d" % (label, seed)).encode()).digest()
    order = list(range(n))
    random.Random(int.from_bytes(digest[:8], "big")).shuffle(order)
    return order


def train_arm(run, label, codec, trainset, text_arm, seed, batch_size=BATCH_SIZE, learning_rate=LEARNING_RATE,
              rank=LORA_RANK, step_ns=None, clock=time.perf_counter_ns):
    """One epoch on the arm's own text, loss on the target tokens only.
    Returns the number of steps. If step_ns is a list, the nanoseconds of each
    training step (the call, not the building of the datums) are appended to it."""
    n = len(trainset)
    if n < 1 or n % batch_size != 0:
        raise DriverError("%d training examples do not fill whole batches of %d" % (n, batch_size))
    run.start_arm(label, rank=rank, seed=seed)
    order = shuffled_order(n, seed, label)
    steps = 0
    for start in range(0, n, batch_size):
        datums = []
        for i in order[start:start + batch_size]:
            r = ep_mod.render(trainset.episodes[i], text_arm)
            prompt_ids, target_ids = codec.train_ids(r.messages, r.target_text)
            datums.append(tinker_backend.make_datum(run.types, prompt_ids, target_ids))
        t0 = clock()
        run.train_step(label, datums, learning_rate)
        if step_ns is not None:
            step_ns.append(clock() - t0)
        steps += 1
    return steps


def responder(run, sampler, codec, cap):
    return tinker_backend.TinkerResponder(run, sampler, codec, cap)


def evaluate_recorded(ratchet, run, sampler, codec, epset, text_arm, descriptor, run_id, config):
    """Evaluate one model on one set with one text, and record the receipt."""
    result = evaluate.evaluate_arm(responder(run, sampler, codec, ratchet.cap), epset, text_arm, ratchet.cap,
                                   descriptor)
    ratchet.record(result, run_id, config)
    return result


def adapter_name(arm, seed):
    return "adapter:%s:seed%d" % (arm, seed)


def compare_all(ratchet, tag, c_own, b_own, controls):
    """The paired comparisons for one seed on one set. controls maps a text
    name (B, E, N) to the C adapter's result on that text. Returns a dict of
    comparison results by name."""
    out = {
        "pass": ratchet.compare_arms("%s-pass" % tag, c_own, b_own, "pass"),
        "stratum": ratchet.compare_arms("%s-stratum" % tag, c_own, b_own, "stratum"),
        # B first: a win for B here means C breaks the format more often
        "format_harm": ratchet.compare_arms("%s-format" % tag, b_own, c_own, "format"),
    }
    for text, res in sorted(controls.items()):
        out["control_%s" % text] = ratchet.compare_arms("%s-control-%s" % (tag, text), c_own, res, "pass")
    return out


def testable(cmp_, gates=None):
    """Whether a pass or stratum comparison can test the claim: enough
    discordant episodes, and neither adapter at the floor or the ceiling."""
    g = GATES if gates is None else gates
    if cmp_["first_only"] + cmp_["second_only"] < g.min_discordant:
        return False
    for passed in (cmp_["first_passed"], cmp_["second_passed"]):
        rate = Fraction(passed, cmp_["n"])
        if rate <= g.rate_low or rate >= g.rate_high:
            return False
    return True


def judge(cmp_, gates=None):
    """The verdict for one seed on one set: ("support" | "not_supported" |
    "cannot_test", reason). Item 3 first: it has no testability condition, so
    a format harm is "not_supported" even when items 1 or 2 cannot be tested.
    Then items 1 and 2 (each must be testable, then win)."""
    if cmp_["format_harm"]["first_better"]:
        return "not_supported", "C breaks the format more often than B"
    for name, label in (("pass", "all episodes"), ("stratum", "the format stratum")):
        if not testable(cmp_[name], gates):
            return "cannot_test", "the comparison on %s has too few discordant episodes or an adapter at the floor or ceiling" % label
        if not cmp_[name]["first_better"]:
            return "not_supported", "C does not beat B on %s" % label
    return "support", "every item holds"


def conditions_met(cmp_):
    return judge(cmp_)[0] == "support"


def overall_verdict(verdicts):
    """Support needs every verdict to be support. Else not_supported if any
    testable item failed, else cannot_test."""
    if all(v == "support" for v in verdicts):
        return "support"
    if any(v == "not_supported" for v in verdicts):
        return "not_supported"
    return "cannot_test"


def control_readings(cmp_):
    """Interpretive only, never part of the verdict: for each control text (B, E, N),
    whether the C adapter beat itself-on-that-text at alpha on the same episodes."""
    return {name[len("control_"):]: res["first_better"] for name, res in sorted(cmp_.items())
            if name.startswith("control_")}


def set2_bound(plan, codec, h2):
    """Upper bound, in plan tokens, of the four set-2 evaluations of the registered decision:
    prefill for every prompt, and the full cap plus the end marker sampled per reply."""
    prefill = 0
    for text in ("C", "B", "E", "N"):
        prefill += sum(len(codec.prompt_ids(ep_mod.render(ep, text).messages)) for ep in h2.episodes)
    return {"train": 0, "prefill": prefill, "sample": 4 * len(h2) * (plan.cap + codec_mod.REPLY_OVERHEAD)}


def run_registered(run, ratchet, codec, run_id, plan, config, decision_id=DECISION_ID):
    """The whole registered run. Returns a summary dict with every result."""
    require_plan_run(run, plan, "full")
    train = ep_mod.build_set("train", plan.train_counts, plan.train_offset)
    h1 = ep_mod.build_set("heldout1", plan.eval1_counts, plan.eval1_offset)
    h2 = ep_mod.build_set("heldout2", plan.eval2_counts)
    cap = ratchet.cap
    ratchet.lock_harness()
    summary = {"base": {}, "own": {}, "controls": {}, "set1": {}, "set2": None, "steps": {}, "support": False,
               "verdict": None, "verdicts": {}, "reasons": {}, "interpretive": {}}
    base = run.base_sampler()
    for arm in ep_mod.ARMS:
        summary["base"][arm] = evaluate_recorded(ratchet, run, base, codec, h1, arm, "base-model", run_id, config)
    samplers = {}
    for seed in range(plan.seeds):
        for arm in plan.arms:
            label = "%s-s%d" % (arm, seed)
            summary["steps"][label] = train_arm(run, label, codec, train, arm, seed)
            samplers[(arm, seed)] = run.checkpoint_sampler(label)
            name = adapter_name(arm, seed)
            summary["own"][(arm, seed)] = evaluate_recorded(
                ratchet, run, samplers[(arm, seed)], codec, h1, arm, name, run_id, config)
        for text in CONTROL_TEXTS:
            summary["controls"][(text, seed)] = evaluate_recorded(
                ratchet, run, samplers[("C", seed)], codec, h1, text, adapter_name("C", seed), run_id, config)
    for seed in range(plan.seeds):
        controls = {t: summary["controls"][(t, seed)] for t in ("E", "N")}
        controls["B"] = summary["controls"][("B", seed)]
        summary["set1"][seed] = compare_all(ratchet, "set1-seed%d" % seed,
                                            summary["own"][("C", seed)], summary["own"][("B", seed)], controls)
    judged = {seed: judge(summary["set1"][seed]) for seed in range(plan.seeds)}
    summary["verdicts"]["set1"] = {seed: v for seed, (v, _why) in judged.items()}
    summary["reasons"]["set1"] = {seed: why for seed, (_v, why) in judged.items()}
    summary["interpretive"]["set1"] = {seed: control_readings(summary["set1"][seed]) for seed in range(plan.seeds)}
    if not all(v == "support" for v in summary["verdicts"]["set1"].values()):
        summary["verdict"] = overall_verdict(list(summary["verdicts"]["set1"].values()))
        return summary                       # the second set stays untouched
    # the one touch must not be lost to a BudgetStop part way through
    run.meter.require_room(set2_bound(plan, codec, h2))
    c0, b0 = adapter_name("C", 0), adapter_name("B", 0)
    entries = [("C", responder(run, samplers[("C", 0)], codec, cap), "C", c0),
               ("B", responder(run, samplers[("B", 0)], codec, cap), "B", b0),
               ("E", responder(run, samplers[("C", 0)], codec, cap), "E", c0),
               ("N", responder(run, samplers[("C", 0)], codec, cap), "N", c0)]
    got = ratchet.second_set_results(decision_id, h2, entries, config)
    summary["set2"] = compare_all(ratchet, "set2-seed0", got["C"], got["B"], {"E": got["E"], "N": got["N"]})
    v2, why2 = judge(summary["set2"])
    summary["verdicts"]["set2"], summary["reasons"]["set2"] = v2, why2
    summary["interpretive"]["set2"] = control_readings(summary["set2"])
    summary["verdict"] = overall_verdict(list(summary["verdicts"]["set1"].values()) + [v2])
    summary["support"] = summary["verdict"] == "support"
    return summary


# ------------------------------------------------------------------ pilot

class TimedResponder:
    """Wraps a responder and records the nanoseconds of each call."""

    def __init__(self, inner, clock=time.perf_counter_ns):
        self.inner, self.clock, self.call_ns = inner, clock, []

    def __call__(self, view):
        t0 = self.clock()
        out = self.inner(view)
        self.call_ns.append(self.clock() - t0)
        return out


def plan_calls(plan):
    """(sampling calls, training steps) of a plan, from its evaluation lines and sizes."""
    sizes = {"e1": sum(plan.eval1_counts.values()), "e2": sum(plan.eval2_counts.values())}
    calls = sum(sizes[e.set_key] * e.runs for e in plan.evals)
    steps = sum(sum(plan.train_counts.values()) // BATCH_SIZE * plan.epochs * plan.seeds for _arm in plan.arms)
    return calls, steps


def pilot_verdict(m, full_calls, full_steps):
    """The pilot's gates as exact comparisons. m holds integers from run_pilot:
    adapter n, passed, format_broken; accepted, new_block and calls (sampling), sample_ns
    and train_ns totals with steps. Returns {gate: bool, ..., "go": bool}."""
    n = m["adapter_n"]
    rate = Fraction(m["adapter_passed"], n)
    projected = Fraction(m["sample_ns"], m["calls"]) * full_calls + Fraction(m["train_ns"], m["steps"]) * full_steps
    gates = {
        "forced_opening_accepted": m["accepted"] == m["calls"],
        "no_new_block_in_replies": Fraction(m["new_block"], m["calls"]) <= PILOT_MAX_NEW_BLOCK,
        "format_breaks_low": Fraction(m["adapter_format_broken"], n) <= PILOT_MAX_FORMAT_BREAK,
        "adapter_pass_rate_testable": PILOT_RATE_LOW < rate < PILOT_RATE_HIGH,
        "projected_time_ok": projected <= PILOT_MAX_HOURS * NS_PER_HOUR,
    }
    gates["go"] = all(gates.values())
    return gates


def run_pilot(run, ratchet, codec, run_id, plan, config, full_plan, clock=time.perf_counter_ns):
    """The pilot: the base model and one adapter trained on text C, both on the
    pilot's evaluation episodes (training-range seeds) in text C. It measures
    what the pilot gates on, writes the measurements as a receipt, and returns
    them with the gate results. Nothing in it touches held-out sets."""
    require_plan_run(run, plan, "pilot")
    train = ep_mod.build_set("train", plan.train_counts, plan.train_offset)
    ev = ep_mod.build_set("train", plan.eval1_counts, plan.eval1_offset)
    ratchet.lock_harness()
    out = {}

    def evaluate_timed(sampler, descriptor):
        inner = responder(run, sampler, codec, ratchet.cap)
        timed = TimedResponder(inner, clock)
        result = evaluate.evaluate_arm(timed, ev, "C", ratchet.cap, descriptor)
        ratchet.record(result, run_id, config)
        return result, timed.call_ns, inner.stats

    out["base"] = evaluate_timed(run.base_sampler(), "pilot:base-model")
    step_ns = []
    steps = train_arm(run, "C-pilot", codec, train, "C", 0, step_ns=step_ns, clock=clock)
    out["adapter"] = evaluate_timed(run.checkpoint_sampler("C-pilot"), "pilot:adapter:C")
    result, call_ns, stats = out["adapter"]
    base_result, base_ns, base_stats = out["base"]
    m = {"adapter_n": result.n, "adapter_passed": result.passed, "adapter_format_broken": result.format_broken,
         "base_passed": base_result.passed, "base_format_broken": base_result.format_broken,
         "accepted": stats["accepted"] + base_stats["accepted"],
         "new_block": stats["new_block"] + base_stats["new_block"],
         "calls": stats["calls"] + base_stats["calls"], "sample_ns": sum(call_ns) + sum(base_ns),
         "train_ns": sum(step_ns), "steps": steps}
    full_calls, full_steps = plan_calls(full_plan)
    gates = pilot_verdict(m, full_calls, full_steps)
    ratchet.measure({"kind": "pilot", "run_id": run_id, "go": 1 if gates["go"] else 0, **m})
    return {"measurements": m, "gates": gates, "results": {k: v[0] for k, v in out.items()}}


def check_codec(tok):
    """A codec for a tokenizer, refusing a tokenizer whose markers are not distinct special ids."""
    try:
        return codec_mod.Codec(tok)
    except codec_mod.CodecError as exc:
        raise DriverError("the tokenizer does not fit the chat layout: %s" % exc)
