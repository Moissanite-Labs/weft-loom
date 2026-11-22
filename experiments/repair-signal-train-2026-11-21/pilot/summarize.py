"""Reads the committed files of the pilot run and prints what they say.

    python3 -I -B pilot/summarize.py [--dir FOLDER]

FOLDER defaults to the pilot-2026-11-22-a folder beside this script. The script
reads only the files in that folder and the record's own committed data and
code. It calls no service and needs no key. Standard library only, exact
arithmetic (fractions.Fraction) throughout.

It prints, for the run: outcomes by model and tier, the paired counts between
the adapter and the untrained model on the same puzzles with the exact sign
test, the time per sampling call and per training step with the projected time
of the full plan, each pilot gate recomputed from the measurements, tokens and
dollars by kind against the plan, and the sampled tokens against their upper
bound.

It also rescores every logged reply on its own: the puzzle is rebuilt from its
tier and seed with the record's episode builder, the saved reply text is parsed
with the record's grammar, and the exact checker decides. The result must equal
the recorded outcome in all 200 rows.

Exit status: 0 when every check agrees, 1 when a check finds a mismatch (the
report is still printed), 2 when the files are refused (a seed outside the
pilot evaluation ranges, a missing file, a malformed row).
"""
import hashlib
import json
import os
import sys
from fractions import Fraction
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD = os.path.dirname(HERE)
sys.path.insert(0, RECORD)
import cost  # noqa: E402
import driver  # noqa: E402
import episodes as ep_mod  # noqa: E402
import evaluate  # noqa: E402
import pilot_cli  # noqa: E402
import receipts  # noqa: E402
import tinker_backend  # noqa: E402

DEFAULT_DIR = os.path.join(HERE, "pilot-2026-11-22-a")
MODELS = ("base", "adapter")
ROW_KEYS = {"arm", "cut", "episode_id", "model", "outcome", "reply", "returned", "returned_tokens", "seed",
            "status", "tier", "tokens"}
FILES = ("APPROVAL-NOTE.md", "approval-row.json", "console-output.txt", "lock.json", "pilot-result.json",
         "pilot-summary.md", "receipts.jsonl", "receipts.jsonl.replies.jsonl", "replies.jsonl",
         "spend-ledger.jsonl")
SUMS = "SHA256SUMS"


class SummaryError(Exception):
    """The files are refused: nothing is reported from them."""


class Report:
    def __init__(self):
        self.lines, self.problems = [], []

    def add(self, text=""):
        self.lines.append(text)

    def problem(self, text):
        self.problems.append(text)
        self.lines.append("PROBLEM: " + text)


# ------------------------------------------------------------------ small helpers

def dec(x, places):
    """An exact fraction rounded half up to `places` decimals, with integer arithmetic."""
    x = Fraction(x)
    scale = 10 ** places
    q = (x * scale * 2 + 1) // 2
    return "%d.%0*d" % (q // scale, places, q % scale)


def frac_text(x):
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else "%d/%d" % (x.numerator, x.denominator)


def sign_one_sided(wins, losses):
    """Exact P(X >= wins) for X ~ Bin(wins + losses, 1/2)."""
    n = wins + losses
    return Fraction(sum(comb(n, k) for k in range(wins, n + 1)), 2 ** n)


def sign_two_sided(wins, losses):
    """Exact two-sided p: twice the smaller tail, at most 1."""
    return min(Fraction(1), 2 * min(sign_one_sided(wins, losses), sign_one_sided(losses, wins)))


def read_text(folder, name):
    path = os.path.join(folder, name)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        raise SummaryError("the file %s cannot be read" % name)


def read_json_lines(folder, name):
    out = []
    for n, raw in enumerate(read_text(folder, name).split("\n"), 1):
        if not raw.strip():
            continue
        try:
            out.append(json.loads(raw))
        except ValueError:
            raise SummaryError("%s line %d is not JSON" % (name, n))
    return out


def pilot_ranges():
    """Inclusive seed ranges of the pilot evaluation set, by tier, from the record's own plan."""
    plan = cost.pilot_plan(evaluate.DEFAULT_CAP)
    return plan, {tier: ep_mod.seed_span("train", tier, count, plan.eval1_offset)
                  for tier, count in sorted(plan.eval1_counts.items())}


# ------------------------------------------------------------------ files and hashes

def check_hashes(folder, rep):
    text = read_text(folder, SUMS)
    listed = {}
    for ln in text.split("\n"):
        if not ln.strip():
            continue
        parts = ln.split("  ", 1)
        if len(parts) != 2:
            raise SummaryError("a line of %s is malformed" % SUMS)
        listed[parts[1]] = parts[0]
    if sorted(listed) != sorted(FILES):
        raise SummaryError("%s does not list exactly the pilot files" % SUMS)
    bad = []
    for name in FILES:
        try:
            with open(os.path.join(folder, name), "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()
        except OSError:
            raise SummaryError("the file %s cannot be read" % name)
        if got != listed[name]:
            bad.append(name)
    rep.add("files listed in %s: %d, hash mismatches: %d" % (SUMS, len(FILES), len(bad)))
    for name in bad:
        rep.problem("%s does not match its SHA-256 in %s" % (name, SUMS))


# ------------------------------------------------------------------ rows

def load_rows(folder):
    """The logged replies, refused unless every row is well formed, inside the pilot evaluation
    ranges, and the rows cover each pilot puzzle once for each of the two models."""
    plan, ranges = pilot_ranges()
    rows = read_json_lines(folder, "replies.jsonl")
    seen = {}
    for n, row in enumerate(rows, 1):
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            raise SummaryError("row %d does not have the fields of a logged reply" % n)
        tier, seed = row["tier"], row["seed"]
        if tier not in ranges:
            raise SummaryError("row %d names tier %r, which the pilot does not use" % (n, tier))
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise SummaryError("row %d: the seed is not an integer" % n)
        lo, hi = ranges[tier]
        if not lo <= seed <= hi:
            raise SummaryError("row %d: seed %d of tier %s is outside the pilot evaluation range %d to %d"
                               % (n, seed, tier, lo, hi))
        if row["episode_id"] != "train-%s-%d" % (tier, seed):
            raise SummaryError("row %d: the episode id does not match the tier and seed" % n)
        if row["model"] not in MODELS:
            raise SummaryError("row %d names model %r" % (n, row["model"]))
        if row["arm"] != "C" or row["status"] != "ok":
            raise SummaryError("row %d is not a completed call on text C" % n)
        if row["outcome"] not in ("P", "F", "X") or row["cut"] not in (0, 1) or isinstance(row["cut"], bool):
            raise SummaryError("row %d has an outcome or cut flag that is not allowed" % n)
        if not isinstance(row["reply"], str):
            raise SummaryError("row %d: the reply is not text" % n)
        got = row["returned"]
        if isinstance(got, list) and all(isinstance(q, list) for q in got):
            if row["returned_tokens"] != sum(len(q) for q in got):
                raise SummaryError("row %d: returned_tokens does not match the returned ids" % n)
        else:
            raise SummaryError("row %d: the returned ids are not a list of sequences" % n)
        key = (row["model"], tier, seed)
        if key in seen:
            raise SummaryError("row %d repeats the puzzle %s %d for the %s model" % (n, tier, seed, row["model"]))
        seen[key] = row
    for model in MODELS:
        for tier, (lo, hi) in ranges.items():
            missing = [s for s in range(lo, hi + 1) if (model, tier, s) not in seen]
            if missing:
                raise SummaryError("the %s model has no row for %d puzzles of tier %s" % (model, len(missing), tier))
    return rows, seen


def rescore_row(R, ep, row):
    """The outcome of one logged reply: P passes the exact checker, F parses and fails it, X cut or off grammar."""
    if row["cut"] == 1:
        return "X"
    cand, _why = evaluate.parse_reply(row["reply"], ep.instance.n)
    if cand is None:
        return "X"
    return "F" if R.check(ep.instance, cand) else "P"


def rescore_all(seen):
    """{(model, tier, seed): (recorded, rescored)} with each puzzle rebuilt from its tier and seed."""
    R = ep_mod.rsig()
    built, got = {}, {}
    for key in sorted(seen):
        _model, tier, seed = key
        if (tier, seed) not in built:
            built[(tier, seed)] = ep_mod.build_episode("train", tier, seed)
        row = seen[key]
        got[key] = (row["outcome"], rescore_row(R, built[(tier, seed)], row))
    return got


# ------------------------------------------------------------------ sections

def outcomes_section(rep, scored, ranges):
    rep.add("== Outcomes, rescored from the replies ==")
    rep.add("model    tier    n    P    F    X   pass rate")
    for model in MODELS:
        tot = {"P": 0, "F": 0, "X": 0}
        for tier in sorted(ranges):
            c = {k: sum(1 for (m, t, _s), (_r, got) in scored.items() if m == model and t == tier and got == k)
                 for k in tot}
            for k in tot:
                tot[k] += c[k]
            n = sum(c.values())
            rep.add("%-8s %-4s %4d %4d %4d %4d   %s" % (model, tier, n, c["P"], c["F"], c["X"], "%d/%d" % (c["P"], n)))
        n = sum(tot.values())
        rep.add("%-8s %-4s %4d %4d %4d %4d   %s" % (model, "all", n, tot["P"], tot["F"], tot["X"], "%d/%d" % (tot["P"], n)))
    rep.add()


def pairs_section(rep, scored, ranges):
    rep.add("== Paired counts, adapter against the untrained model on the same puzzles ==")
    rep.add("tier    both pass    adapter only    base only    neither")
    totals = [0, 0, 0, 0]
    for tier in sorted(ranges):
        lo, hi = ranges[tier]
        c = [0, 0, 0, 0]
        for seed in range(lo, hi + 1):
            b = scored[("base", tier, seed)][1] == "P"
            a = scored[("adapter", tier, seed)][1] == "P"
            c[0 if (a and b) else 1 if a else 2 if b else 3] += 1
        totals = [x + y for x, y in zip(totals, c)]
        rep.add("%-6s %9d %15d %12d %10d" % (tier, c[0], c[1], c[2], c[3]))
    rep.add("%-6s %9d %15d %12d %10d" % ("all", totals[0], totals[1], totals[2], totals[3]))
    both, a_only, b_only, neither = totals
    n = a_only + b_only
    one, two = sign_one_sided(a_only, b_only), sign_two_sided(a_only, b_only)
    rep.add("discordant pairs: %d (adapter only %d, base only %d)" % (n, a_only, b_only))
    rep.add("exact sign test, one-sided (adapter above base): p = %s = %s" % (frac_text(one), dec(one, 6)))
    rep.add("exact sign test, two-sided: p = %s = %s" % (frac_text(two), dec(two, 6)))
    rep.add("exploratory: these 100 puzzles are training-range seeds, and the pilot is not part of any registered result")
    rep.add()
    return totals


def timing_section(rep, res, full_calls, full_steps):
    meas = res["measurements"]
    calls, steps = meas["calls"], meas["steps"]
    per_call = Fraction(meas["sample_ns"], calls * 10 ** 9)
    per_step = Fraction(meas["train_ns"], steps * 10 ** 9)
    projected = full_calls * per_call + full_steps * per_step
    hours = projected / 3600
    rep.add("== Time ==")
    rep.add("sampling: %d ns over %d calls, sent one at a time" % (meas["sample_ns"], calls))
    rep.add("seconds per sampling call: %s = %s" % (frac_text(per_call), dec(per_call, 3)))
    rep.add("training: %d ns over %d steps" % (meas["train_ns"], steps))
    rep.add("seconds per training step: %s = %s" % (frac_text(per_step), dec(per_step, 3)))
    rep.add("the full plan has %d sampling calls and %d training steps (driver.plan_calls on the plan of pilot_cli)"
            % (full_calls, full_steps))
    rep.add("sampling part: %s s = %s hours" % (frac_text(full_calls * per_call), dec(full_calls * per_call / 3600, 3)))
    rep.add("training part: %s s = %s hours" % (frac_text(full_steps * per_step), dec(full_steps * per_step / 3600, 3)))
    rep.add("projected time of the full plan: %s hours = %s hours, the gate allows %d" % (frac_text(hours), dec(hours, 3), driver.PILOT_MAX_HOURS))
    rep.add()


def gates_section(rep, res, scored, rows, full_calls, full_steps):
    meas = res["measurements"]
    base = [v for (m, _t, _s), v in scored.items() if m == "base"]
    adapter = [v for (m, _t, _s), v in scored.items() if m == "adapter"]
    m = {"adapter_n": len(adapter), "adapter_passed": sum(1 for _r, g in adapter if g == "P"),
         "adapter_format_broken": sum(1 for _r, g in adapter if g == "X"),
         "base_passed": sum(1 for _r, g in base if g == "P"),
         "base_format_broken": sum(1 for _r, g in base if g == "X"),
         "accepted": sum(1 for r in rows if len(r["returned"]) == 1),
         "new_block": sum(1 for r in rows if "<|" in r["reply"]),
         "calls": len(rows), "sample_ns": meas["sample_ns"], "train_ns": meas["train_ns"], "steps": meas["steps"]}
    for key in sorted(m):
        if meas.get(key) != m[key]:
            rep.problem("measurement %s: recorded %r, recomputed %r" % (key, meas.get(key), m[key]))
    verdict = driver.pilot_verdict(m, full_calls, full_steps)
    projected_h = (Fraction(m["sample_ns"], m["calls"]) * full_calls + Fraction(m["train_ns"], m["steps"]) * full_steps) / driver.NS_PER_HOUR
    rate = Fraction(m["adapter_passed"], m["adapter_n"])
    rep.add("== Pilot gates, recomputed ==")
    rep.add("%-28s %-9s %s" % ("gate", "result", "recorded"))
    lines = [
        ("forced_opening_accepted", "accepted %d of %d calls (rule: all)" % (m["accepted"], m["calls"])),
        ("no_new_block_in_replies", "new blocks %d of %d (rule: at most %s)" % (m["new_block"], m["calls"], frac_text(driver.PILOT_MAX_NEW_BLOCK))),
        ("format_breaks_low", "adapter breaks %d of %d (rule: at most %s)" % (m["adapter_format_broken"], m["adapter_n"], frac_text(driver.PILOT_MAX_FORMAT_BREAK))),
        ("adapter_pass_rate_testable", "adapter pass rate %s (rule: above %s, below %s)" % (frac_text(rate), frac_text(driver.PILOT_RATE_LOW), frac_text(driver.PILOT_RATE_HIGH))),
        ("projected_time_ok", "projected %s hours (rule: at most %d)" % (dec(projected_h, 3), driver.PILOT_MAX_HOURS)),
    ]
    for name, what in lines:
        got = "true" if verdict[name] else "false"
        rep.add("%-28s %-9s %s" % (name, got, res["gates"].get(name)))
        rep.add("    %s" % what)
        if res["gates"].get(name) != got:
            rep.problem("gate %s: recorded %r, recomputed %r" % (name, res["gates"].get(name), got))
    go = "true" if verdict["go"] else "false"
    rep.add("%-28s %-9s %s" % ("go", go, res["gates"].get("go")))
    if res["gates"].get("go") != go or res["go"] != go:
        rep.problem("go: recorded %r and %r, recomputed %r" % (res["gates"].get("go"), res["go"], go))
    rep.add()
    return m


def parse_plan_tokens(folder_record, name, source):
    """Planned pilot tokens by kind from a committed output of cost.py."""
    path = os.path.join(folder_record, "data", name)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        raise SummaryError("the committed plan file data/%s cannot be read" % name)
    head = "Plan pilot (token source: %s)" % source
    block = text.split(head + "\n", 1)
    if len(block) != 2:
        raise SummaryError("data/%s has no pilot plan for the %s count" % (name, source))
    kinds = {k: 0 for k in ("train", "prefill", "sample")}
    exact = None
    for ln in block[1].split("\n"):
        if not ln.strip():
            break
        parts = ln.split()
        if ln.startswith("exact total:"):
            exact = Fraction(parts[2])
        elif len(parts) >= 5 and parts[-4] in kinds:
            kinds[parts[-4]] += int(parts[-3])
    if exact is None:
        raise SummaryError("data/%s gives no exact total for the pilot plan" % name)
    return kinds, exact


def spend_section(rep, folder, res, rows, rowsum_tokens):
    ledger_path = os.path.join(folder, "spend-ledger.jsonl")
    run_id = res["run_id"]
    spent, tokens, starts, plan_id = tinker_backend.Ledger(ledger_path, run_id).replay()
    if starts != 1:
        rep.problem("the ledger holds %d starts of the run" % starts)
    if plan_id != res["plan_id"]:
        rep.problem("the ledger's plan id differs from the result file's")
    reserved = {k: 0 for k in tinker_backend.PRICES_PER_MILLION}
    refunded = {k: 0 for k in tinker_backend.PRICES_PER_MILLION}
    for row in read_json_lines(folder, "spend-ledger.jsonl"):
        if row.get("run_id") != run_id:
            continue
        if row.get("ev") == "reserve":
            reserved[row["kind"]] += row["tokens"]
        elif row.get("ev") == "adjust":
            refunded[row["kind"]] += row["tokens"]
    plan_rule, rule_exact = parse_plan_tokens(RECORD, "cost-rule.txt", "rule")
    plan_tok, tok_exact = parse_plan_tokens(RECORD, "cost-tokenizer.txt", "tokenizer")
    rep.add("== Spend, from the ledger ==")
    rep.add("%-15s %9s %9s %9s %18s" % ("kind", "rule plan", "tok. plan", "ledger", "dollars (exact)"))
    total = Fraction(0)
    for kind in sorted(tokens):
        dollars = tinker_backend.cost_usd(kind, tokens[kind])
        total += dollars
        rep.add("%-15s %9s %9s %9d %18s" % (kind, plan_rule.get(kind, "-"), plan_tok.get(kind, "-"), tokens[kind], frac_text(dollars)))
    rep.add("%-15s %9d %9d %9d %18s" % ("tokens in all", sum(plan_rule.values()), sum(plan_tok.values()), sum(tokens.values()), ""))
    rep.add("total spent: %s dollars = %s, ceiling %s, planned (tokenizer) %s = %s, planned (rule) %s = %s"
            % (frac_text(total), dec(total, 4), res["ceiling_usd"], frac_text(tok_exact), dec(tok_exact, 4),
               frac_text(rule_exact), dec(rule_exact, 4)))
    if frac_text(total) != res["spend"]["total_usd"] or frac_text(tok_exact) != res["planned_cost_usd"]:
        rep.problem("the total spent or the planned cost differs from the result file")
    for kind in sorted(tokens):
        got = res["spend"]["by_kind"].get(kind)
        if got is None or got["tokens"] != tokens[kind] or got["usd"] != frac_text(tinker_backend.cost_usd(kind, tokens[kind])):
            rep.problem("spend of kind %s differs between the ledger and the result file" % kind)
    bound = reserved["sample"]
    rep.add("sampled tokens: %d returned, upper bound %d (the cap plus the end marker for each of %d calls), %s of the bound"
            % (tokens["sample"], bound, len(rows), dec(Fraction(tokens["sample"], bound), 3)))
    rep.add("the ledger reserved %d sample tokens and refunded %d" % (reserved["sample"], -refunded["sample"]))
    rep.add("the token ids returned in replies.jsonl add up to %d" % rowsum_tokens)
    if tokens["sample"] > bound:
        rep.problem("sampled tokens are above their upper bound")
    if rowsum_tokens != tokens["sample"]:
        rep.problem("the returned ids in replies.jsonl do not add up to the sampled tokens of the ledger")
    rep.add("the service's own bill has not been compared with this ledger")
    rep.add()


def run_section(rep, folder, res):
    rep.add("== The run ==")
    rep.add("run id %s, plan %s, mode %s, status %s" % (res["run_id"], res["plan"], res["mode"], res["status"]))
    if res["status"] != "complete" or res["error"] != "" or res["mode"] != "real":
        rep.problem("the result file is not a complete real run")
    plan = cost.pilot_plan(evaluate.DEFAULT_CAP)
    fingerprint = driver.plan_fingerprint(plan)
    row = json.loads(read_text(folder, "approval-row.json"))
    want = driver.approval_row(res["run_id"], "0.50", plan)
    rep.add("plan id in the result file equals the fingerprint of the record's pilot plan: %s" % ("yes" if res["plan_id"] == fingerprint else "no"))
    rep.add("approval row equals the row the record prints for this run id: %s" % ("yes" if row == want else "no"))
    if res["plan_id"] != fingerprint:
        rep.problem("the plan id of the run is not the fingerprint of the record's pilot plan")
    if row != want:
        rep.problem("the approval row differs from the row the record prints")
    lock = json.loads(read_text(folder, "lock.json"))
    same = lock == evaluate.harness_hashes()
    rep.add("harness lock of the run equals the hashes of the record's harness files: %s" % ("yes" if same else "no"))
    if not same:
        rep.problem("the harness lock of the run differs from the record's harness files")
    count, head = receipts.verify(os.path.join(folder, "receipts.jsonl"))
    rep.add("receipt chain verifies: %d receipts, head %s" % (count, head))
    rep.add()


def store_check(folder, rep, seen):
    """The replies stored beside the receipts equal the logged replies, model by model."""
    entries = read_json_lines(folder, "receipts.jsonl.replies.jsonl")
    ok = 0
    for e in entries:
        entry = e.get("entry", e)
        model = "base" if entry.get("descriptor") == "pilot:base-model" else "adapter"
        ids = entry.get("episode_ids", [])
        for eid, text in zip(ids, entry.get("texts", [])):
            _kind, tier, seed = eid.split("-")
            if seen[(model, tier, int(seed))]["reply"] == text:
                ok += 1
            else:
                rep.problem("stored reply of %s %s differs from replies.jsonl" % (model, eid))
    rep.add("replies stored beside the receipts that equal the logged replies: %d" % ok)
    if ok != len(seen):
        rep.problem("the stored replies cover %d of %d logged replies" % (ok, len(seen)))


# ------------------------------------------------------------------ main

def build_report(folder):
    rep = Report()
    _plan, ranges = pilot_ranges()
    check_hashes(folder, rep)
    rows, seen = load_rows(folder)
    res = json.loads(read_text(folder, "pilot-result.json"))
    rep.add()
    run_section(rep, folder, res)
    scored = rescore_all(seen)
    bad = [(k, r, g) for k, (r, g) in sorted(scored.items()) if r != g]
    outcomes_section(rep, scored, ranges)
    rep.add("== Rescoring, one reply at a time ==")
    rep.add("each puzzle is rebuilt from its tier and seed, the reply text is parsed with the record's grammar and checked exactly")
    rep.add("rows rescored: %d, rows whose recorded outcome equals the rescored outcome: %d" % (len(scored), len(scored) - len(bad)))
    for (model, tier, seed), r, g in bad:
        rep.problem("MISMATCH %s %s %d: recorded %s, rescored %s" % (model, tier, seed, r, g))
    for model in MODELS:
        s = "".join(scored[(model, t, sd)][1] for t in sorted(ranges) for sd in range(ranges[t][0], ranges[t][1] + 1))
        rep.add("outcome string of the %s model: %d characters, P %d F %d X %d" % (model, len(s), s.count("P"), s.count("F"), s.count("X")))
    store_check(folder, rep, seen)
    rep.add()
    for model in MODELS:
        got = res["outcomes"][model]
        have = {k: sum(1 for (m, _t, _s), (_r, g) in scored.items() if m == model and g == k) for k in "PFX"}
        if got != have:
            rep.problem("the outcome counts of the %s model in the result file differ from the rescored counts" % model)
    pairs_section(rep, scored, ranges)
    full_calls, full_steps = driver.plan_calls(cost.full_plan(pilot_cli.FULL_EXAMPLES, pilot_cli.FULL_SEEDS, evaluate.DEFAULT_CAP))
    timing_section(rep, res, full_calls, full_steps)
    gates_section(rep, res, scored, rows, full_calls, full_steps)
    spend_section(rep, folder, res, rows, sum(r["returned_tokens"] for r in rows))
    rep.add("== Verdict of this script ==")
    rep.add("problems found: %d" % len(rep.problems))
    return rep


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    folder = DEFAULT_DIR
    if argv:
        if len(argv) == 2 and argv[0] == "--dir":
            folder = argv[1]
        else:
            print("usage: summarize.py [--dir FOLDER]", file=sys.stderr)
            return 2
    try:
        rep = build_report(folder)
    except (SummaryError, receipts.ReceiptError, KeyError, ValueError, TypeError) as exc:
        print("refused: %s" % (exc,), file=sys.stderr)
        return 2
    print("\n".join(rep.lines))
    return 1 if rep.problems else 0


if __name__ == "__main__":
    sys.exit(main())
