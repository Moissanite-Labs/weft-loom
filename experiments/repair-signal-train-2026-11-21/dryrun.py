"""Runs the whole loop end to end with reference policies in place of the model.

Build episodes, "train" (a no-op), evaluate every policy in every arm, write
receipts, apply the ratchet, show the refusals, print the score table. Exits 1
if any expected behaviour is missing. No network, no key, no model, no spend.

    python3 dryrun.py [--out DIR] [--record PATH_TO_ORIGINAL_RSIG]
"""
import json
import os
import shutil
import sys
import tempfile
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codec as codec_mod  # noqa: E402
import cost  # noqa: E402
import driver  # noqa: E402
import episodes as ep_mod  # noqa: E402
import evaluate  # noqa: E402
import fakes  # noqa: E402
import latch as latch_mod  # noqa: E402
import ratchet as ratchet_mod  # noqa: E402
import receipts  # noqa: E402
import reference_policies as rp  # noqa: E402
import tinker_backend  # noqa: E402
import vendor_loader  # noqa: E402

CAP = evaluate.DEFAULT_CAP
CHECKS = []


def check(name, ok):
    CHECKS.append((name, bool(ok)))
    print("CHECK %-62s %s" % (name, "PASS" if ok else "FAIL"))


def refused(exc_type, fn):
    try:
        fn()
    except exc_type:
        return True
    return False


def cell(r):
    return "%d/%d x%d" % (r.passed, r.n, r.format_broken)


def _texts(epset, kind):
    out = []
    for ep in epset.episodes:
        r = ep_mod.render(ep, "A")
        out.append(r.target_text if kind == "target" else r.attempt_text)
    return out


def _mixed(win, fail, wins):
    """Per episode: the passing text where the index is in wins, else the failed attempt."""
    return [win[i] if i in wins else fail[i] for i in range(len(win))]


def driver_scenario(out, decision_id, c_good):
    """A registered run against fakes. c_good: the adapter trained on C repairs
    16 of 20 episodes on each held-out set and the adapter trained on B repairs
    2 of 20 (both inside the testability gates); every other model repeats the
    failed attempt."""
    fakes_codec = codec_mod.Codec(fakes.FakeTokenizer())
    enc = fakes_codec.target_ids
    plan = cost.full_plan(64, 2, CAP, heldout_per_tier=10)
    h1 = ep_mod.build_set("heldout1", plan.eval1_counts)
    h2 = ep_mod.build_set("heldout2", plan.eval2_counts)
    fail1, fail2 = _texts(h1, "attempt"), _texts(h2, "attempt")
    win1, win2 = _texts(h1, "target"), _texts(h2, "target")
    c_wins, b_wins = {i for i in range(20) if i % 5}, {0, 10}
    samplers = []
    for _seed in range(plan.seeds):
        for arm in plan.arms:
            if arm == "C" and c_good:
                # own, then texts B, E, N on set 1; set 2: own, E, N
                texts = _mixed(win1, fail1, c_wins) + fail1 * 3 + _mixed(win2, fail2, c_wins) + fail2 * 2
            elif arm == "B" and c_good:
                texts = _mixed(win1, fail1, b_wins) + _mixed(win2, fail2, b_wins)
            else:
                texts = fail1 + fail1 * 3 + fail2 * 3 if arm == "C" else fail1 + fail2
            samplers.append(fakes.ScriptedSampler(texts, enc))
    svc = fakes.FakeService(checkpoint_samplers=samplers, base=fakes.ScriptedSampler(fail1, enc))
    appr = os.path.join(out, "approvals-driver.json")
    with open(appr, "w", encoding="utf-8") as fh:
        json.dump({"approvals": [{"run_id": "driver-" + decision_id, "ceiling_usd": "5.00"}]}, fh)
    counter = cost.Counter(rule_only=True)
    run_ = driver.start_run("driver-" + decision_id, appr, plan, counter, svc, fakes.FakeTypes)
    sub = os.path.join(out, decision_id)
    os.makedirs(sub, exist_ok=True)
    rt = ratchet_mod.Ratchet(os.path.join(sub, "receipts.jsonl"), os.path.join(sub, "latch.jsonl"),
                             os.path.join(sub, "lock.json"), CAP)
    config = {"cap": CAP, "scenario": decision_id}
    summary = driver.run_registered(run_, rt, fakes_codec, "driver-" + decision_id, plan, config, decision_id)
    return summary, run_, rt, svc


def driver_checks(out):
    summary, run_, rt, svc = driver_scenario(out, "dryrun-driver-good", True)
    check("driver: 2 seeds x 3 arms trained, 2 steps each", len(svc.clients) == 6 and set(summary["steps"].values()) == {2})
    check("driver: C beat B in both seeds, so the second set was touched once and support holds",
          summary["support"] and summary["verdict"] == "support" and rt.latch.touched() == ["dryrun-driver-good"])
    check("driver: the verdict is support on set 1 for both seeds and on set 2",
          summary["verdicts"] == {"set1": {0: "support", 1: "support"}, "set2": "support"})
    check("driver: the controls (C adapter on texts E and N) score below C",
          all(summary["set1"][s]["control_E"]["second_only"] == 0 and summary["set1"][s]["control_E"]["first_better"]
              for s in range(2)))
    check("driver: the meter stayed under the ceiling", run_.meter.spent < run_.meter.ceiling)
    check("driver: every sampled prompt carries special role ids",
          all(1000 in p and 1010 in p and 1004 in p for smp in svc.checkpoint_samplers for p in smp.prompts[:3]))
    summary2, _run2, rt2, _svc2 = driver_scenario(out, "dryrun-driver-flat", False)
    check("driver: no gain means no support and the second set is never touched",
          (not summary2["support"]) and summary2["set2"] is None and rt2.latch.touched() == [])
    check("driver: no gain at all is reported as cannot_test, not as not_supported",
          summary2["verdict"] == "cannot_test")
    check("driver: a run refuses a plan other than the one it was started for",
          refused(driver.DriverError, lambda: driver.run_registered(
              run_, rt, codec_mod.Codec(fakes.FakeTokenizer()), "driver-dryrun-driver-good",
              cost.full_plan(64, 2, CAP, heldout_per_tier=11), {"cap": CAP}, "dryrun-driver-good")))
    pilot_checks(out)


def pilot_checks(out):
    """The pilot against fakes, with a fake clock: measurements, gates and no held-out set."""
    codec = codec_mod.Codec(fakes.FakeTokenizer())
    pilot, big = cost.pilot_plan(CAP), cost.full_plan(2048, 2, CAP)
    ev = ep_mod.build_set("train", pilot.eval1_counts, pilot.eval1_offset)
    fails, wins = _texts(ev, "attempt"), _texts(ev, "target")
    sampler = fakes.ScriptedSampler(_mixed(wins, fails, set(range(60))), codec.target_ids)
    svc = fakes.FakeService(checkpoint_samplers=[sampler], base=fakes.ScriptedSampler(fails, codec.target_ids))
    appr = os.path.join(out, "approvals-pilot.json")
    with open(appr, "w", encoding="utf-8") as fh:
        json.dump({"approvals": [{"run_id": "pilot-dry", "ceiling_usd": "0.50"}]}, fh)
    run_ = driver.start_run("pilot-dry", appr, pilot, cost.Counter(rule_only=True), svc, fakes.FakeTypes)
    sub = os.path.join(out, "pilot")
    os.makedirs(sub, exist_ok=True)
    rt = ratchet_mod.Ratchet(os.path.join(sub, "receipts.jsonl"), os.path.join(sub, "latch.jsonl"),
                             os.path.join(sub, "lock.json"), CAP)
    ticks = iter(range(0, 10**12, 1000))
    got = driver.run_pilot(run_, rt, codec, "pilot-dry", pilot, {"cap": CAP}, big, clock=lambda: next(ticks))
    m = got["measurements"]
    print("pilot measurements: %s" % json.dumps(m, sort_keys=True))
    check("pilot: measures calls, steps, accepted forced openings, new blocks and format breaks, and every gate holds",
          got["gates"]["go"] and (m["calls"], m["steps"], m["accepted"], m["new_block"], m["adapter_format_broken"])
          == (200, 8, 200, 0, 0))
    opening = codec.opening_ids()
    check("pilot: every prompt sampled from, base model and adapter, ends with the forced opening of the model's turn",
          all(p[-2:] == opening for smp in (sampler, svc.base) for p in smp.prompts) and len(sampler.prompts) == 100
          and len(svc.base.prompts) == 100)
    check("pilot: evaluates on training-range seeds only and never touches a held-out set",
          got["results"]["adapter"].set_kind == "train" and rt.latch.touched() == []
          and not [b for b in receipts.bodies(rt.receipts_path) if str(b.get("set_kind", "")).startswith("heldout")])
    check("pilot: its measurements are a receipt in the chain",
          receipts.bodies(rt.receipts_path)[-1].get("kind") == "pilot")
    check("pilot: a run started for the full plan cannot run the pilot",
          refused(driver.DriverError, lambda: driver.run_pilot(
              driver.start_run("pilot-dry2", _approve(out, "pilot-dry2"), big, cost.Counter(rule_only=True),
                               fakes.FakeService(), fakes.FakeTypes),
              rt, codec, "pilot-dry2", pilot, {}, big)))


def _approve(out, run_id):
    path = os.path.join(out, "approvals-%s.json" % run_id)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"approvals": [{"run_id": run_id, "ceiling_usd": "50.00"}]}, fh)
    return path


def run(out, record):
    # the registry the latch and evaluate read: the dry run uses its own ids, and the lock covers this file
    registry = os.path.join(out, "decisions.json")
    with open(registry, "w", encoding="utf-8") as fh:
        json.dump({"decisions": ["dryrun-dec-1", "dryrun-driver-good", "dryrun-driver-flat"]}, fh)
    saved, evaluate.DECISIONS_PATH = evaluate.DECISIONS_PATH, registry
    try:
        return _run(out, record)
    finally:
        evaluate.DECISIONS_PATH = saved


def _run(out, record):
    # 1. the vendored copy
    print("vendored rsig sha256 %s" % vendor_loader.rsig_sha256())
    if record:
        same = vendor_loader.sha256_file(record) == vendor_loader.sha256_file(
            os.path.join(vendor_loader.DEFAULT_VENDOR, "rsig.py"))
        check("vendored rsig is byte-identical to the experiment record", same)

    # 2. episodes
    train = ep_mod.build_set("train", {"S": 20, "M": 20})
    h1 = ep_mod.build_set("heldout1", {"S": 100, "M": 100})
    h2 = ep_mod.build_set("heldout2", {"S": 100, "M": 100})
    print("episodes: train %d, heldout1 %d, heldout2 %d" % (len(train), len(h1), len(h2)))
    print("set hashes: train %s heldout1 %s heldout2 %s" % (train.sha256()[:16], h1.sha256()[:16], h2.sha256()[:16]))
    check("every attempt fails the exact checker", all(ep.violations() for s in (train, h1, h2) for ep in s.episodes))
    check("every target passes the exact checker",
          all(not ep_mod.rsig().check(ep.instance, list(ep.target)) for ep in train.episodes))

    # 3. "train": a no-op for reference policies
    print("train: no-op (reference policies have no weights)")

    # 4. evaluate and record
    rt = ratchet_mod.Ratchet(os.path.join(out, "receipts.jsonl"), os.path.join(out, "latch.jsonl"),
                             os.path.join(out, "harness.lock.json"), CAP)
    rt.lock_harness()
    config = {"cap": CAP, "arms": list(ep_mod.ARMS), "heldout1": h1.counts, "heldout2": h2.counts,
              "train": train.counts, "run": "dryrun-1"}
    results = {}
    for name, pol in rp.POLICIES.items():
        for arm in ep_mod.ARMS:
            r = evaluate.evaluate_arm(pol, h1, arm, CAP, "policy:" + name)
            rt.record(r, "dryrun-1", config)
            results[(name, arm)] = r
    print()
    print("Score table, held-out set 1, cap %d pieces, cell = passed/n and format breaks (x)" % CAP)
    print("%-10s" % "policy" + "".join("%-16s" % a for a in ep_mod.ARMS))
    for name in rp.POLICIES:
        print("%-10s" % name + "".join("%-16s" % cell(results[(name, a)]) for a in ep_mod.ARMS))
    print()

    # 5. what the table must show
    o = {a: results[("oracle", a)] for a in ep_mod.ARMS}
    for other in ("A", "B", "E", "N"):
        cmp_ = rt.compare_arms("dryrun-arms-%s" % other, o["C"], o[other])
        check("oracle: C beats %s (exact sign test, p <= 1/1000)" % other,
              cmp_["first_better"] and cmp_["p"] <= Fraction(1, 1000))
    rc = [results[("recompute", a)].outcomes for a in ep_mod.ARMS]
    check("recompute: identical outcomes in every arm (arms can tie)", len(set(rc)) == 1 and "P" in rc[0])
    check("unchanged: scores zero in every arm", all(results[("unchanged", a)].passed == 0 for a in ep_mod.ARMS))
    check("blind: hurt by E and N relative to C",
          all(results[("blind", "C")].passed > results[("blind", a)].passed for a in ("E", "N")))
    check("verbose: every reply breaks the format, counted apart from failures",
          all(results[("verbose", a)].format_broken == results[("verbose", a)].n for a in ep_mod.ARMS))

    # 6. the ratchet
    print()
    base, cand = results[("unchanged", "C")], results[("oracle", "C")]
    d = rt.decide("dryrun-dec-0", base, cand)
    check("ratchet accepts the oracle over unchanged on held-out 1 (exact p)", d["accepted"] and d["p"] < Fraction(1, 1000))
    d2 = rt.confirm_second_set("dryrun-dec-1", h2, rp.unchanged, rp.oracle, "C", "policy:unchanged", "policy:oracle", config)
    check("second set touched once, decision confirmed", d2["accepted"])
    check("latch refuses a second touch of the second set for that decision",
          refused(latch_mod.LatchRefused,
                  lambda: rt.confirm_second_set("dryrun-dec-1", h2, rp.unchanged, rp.oracle, "C",
                                                "policy:unchanged", "policy:oracle", config)))
    os.remove(rt.latch.path)
    check("a deleted latch file does not buy a second touch: the chain holds the touch",
          refused(latch_mod.LatchRefused,
                  lambda: rt.confirm_second_set("dryrun-dec-1", h2, rp.unchanged, rp.oracle, "C",
                                                "policy:unchanged", "policy:oracle", config)))
    check("evaluation of the second set without a latch token is refused",
          refused(evaluate.EvalRefused, lambda: evaluate.evaluate_arm(rp.oracle, h2, "C", CAP, "x")))
    same = evaluate.evaluate_arm(rp.unchanged, h1, "C", CAP, "policy:unchanged-copy")
    rt.record(same, "dryrun-1", config)
    check("ratchet rejects a candidate identical to the baseline",
          refused(ratchet_mod.RatchetRefused, lambda: rt.decide("dryrun-dec-2", base, same)))
    other_cap = evaluate.evaluate_arm(rp.oracle, h1, "C", CAP - 1, "policy:oracle-cap")
    rt.record(other_cap, "dryrun-1", config)
    check("ratchet refuses a comparison at a different compute cap",
          refused(ratchet_mod.RatchetRefused, lambda: rt.decide("dryrun-dec-3", base, other_cap)))
    unrecorded = evaluate.evaluate_arm(rp.recompute, h1, "C", CAP, "policy:never-recorded")
    check("ratchet refuses a result that is not in the receipt chain",
          refused(ratchet_mod.RatchetRefused, lambda: rt.decide("dryrun-dec-4", base, unrecorded)))
    check("the latch refuses a decision id that is not registered",
          refused(latch_mod.LatchRefused, lambda: rt.latch.touch("dryrun-unregistered", [("C", "x")])))

    # 6b. the paid-run driver, end to end against the fake client
    driver_checks(out)

    # 7. receipts
    n, head = receipts.verify(rt.receipts_path)
    print("receipts: %d, chain head %s" % (n, head))
    check("receipt chain verifies", n > 0)
    tampered = os.path.join(out, "tampered.jsonl")
    with open(rt.receipts_path, "r", encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    lines[2] = lines[2].replace('"passed":0', '"passed":1', 1)
    with open(tampered, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    check("an edited receipt fails verification", refused(receipts.ReceiptError, lambda: receipts.verify(tampered)))

    # 8. a changed rsig hash refuses to run
    bad = os.path.join(out, "vendor-bad")
    shutil.copytree(vendor_loader.DEFAULT_VENDOR, bad)
    with open(os.path.join(bad, "rsig.py"), "ab") as fh:
        fh.write(b"\n# edited\n")
    check("a changed rsig hash refuses to run", refused(vendor_loader.VendorError, lambda: vendor_loader.load_rsig(bad)))

    # 9. the paid backend, with a fake client
    appr = os.path.join(out, "approvals.json")
    with open(appr, "w", encoding="utf-8") as fh:
        json.dump({"approvals": [{"run_id": "some-other-run", "ceiling_usd": "10.00"}]}, fh)
    plan = {"train": 1000000, "prefill": 100000, "sample": 100000}
    check("the paid backend refuses an unapproved run id",
          refused(tinker_backend.ApprovalError,
                  lambda: tinker_backend.TinkerRun("dryrun-1", appr, plan, fakes.FakeService(), fakes.FakeTypes)))
    with open(appr, "w", encoding="utf-8") as fh:
        json.dump({"approvals": [{"run_id": "dryrun-1", "ceiling_usd": "0.50"}]}, fh)
    check("the paid backend refuses a budget at or over the ceiling",
          refused(tinker_backend.BudgetError,
                  lambda: tinker_backend.TinkerRun("dryrun-1", appr, plan, fakes.FakeService(), fakes.FakeTypes)))
    ok = tinker_backend.TinkerRun("dryrun-1", appr, {"train": 1000, "prefill": 1000, "sample": 1000},
                                  fakes.FakeService(), fakes.FakeTypes)
    check("the paid backend starts with approval and a budget under the ceiling", ok.budget < ok.meter.ceiling)
    ok.meter.reserve("train", 100000)
    small = {"train": 1000, "prefill": 1000, "sample": 1000}
    check("the paid backend refuses a restart of a started run id unless resume is given",
          refused(tinker_backend.ApprovalError,
                  lambda: tinker_backend.TinkerRun("dryrun-1", appr, small, fakes.FakeService(), fakes.FakeTypes)))
    again = tinker_backend.TinkerRun("dryrun-1", appr, small, fakes.FakeService(), fakes.FakeTypes, resume=True)
    check("a resumed run counts the spend already in the ledger", again.meter.spent == ok.meter.spent > 0)

    bad_checks = [n for n, good in CHECKS if not good]
    print()
    print("%d checks, %d failed" % (len(CHECKS), len(bad_checks)))
    return 1 if bad_checks else 0


def main(argv):
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    record = argv[argv.index("--record") + 1] if "--record" in argv else None
    if out:
        os.makedirs(out, exist_ok=True)
        return run(out, record)
    with tempfile.TemporaryDirectory() as tmp:
        return run(tmp, record)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
