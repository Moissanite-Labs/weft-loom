"""Exact token counts and dollar cost for the planned runs.

Counting: with the real tokenizer if tml_renderers can be imported, either in
this interpreter or in the interpreter named by --venv-python (run as a small
worker, nothing leaves the machine). Otherwise by the documented rule in
evaluate.PIECE (one piece per digit, per run of letters, per other mark).

Chat markers are special tokens and are not run through the tokenizer. Their
counts come from codec.py, which builds the ids the paid path sends: each
message adds MARKERS_PER_MESSAGE tokens (role, content marker, end), the
system line is one more message, and a reply (the training target and what the
model writes) adds REPLY_OVERHEAD tokens: its turn opening and its end marker. tests/test_layout_real.py checks these counts against
the tml_renderers renderer, id for id, when that package can be imported.

Cost: tokens times the published price per million, as exact fractions.
Training bills every token of the prompt and the target (forward and backward).
Evaluation bills prefill for each prompt and, as an upper bound, `cap` plus
REPLY_OVERHEAD sampled tokens per episode.

    python3 cost.py [--venv-python PATH] [--examples N] [--seeds K] [--cap C]
"""
import json
import os
import subprocess
import sys

if __name__ == "__main__" and "--token-worker" in sys.argv:
    # Self-contained worker: reads a JSON list of strings, prints a JSON list of counts.
    from tml_renderers import renderers
    _tk = renderers.Inkling2().tokenizer
    _tk = _tk() if callable(_tk) else _tk
    print(json.dumps([len(_tk.encode_ordinary(t)) for t in json.load(sys.stdin)]))
    sys.exit(0)

from fractions import Fraction  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codec  # noqa: E402
import episodes as ep_mod  # noqa: E402
import evaluate  # noqa: E402
import tinker_backend  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


class Counter:
    """Counts tokens of many strings at once. .source says how."""

    def __init__(self, venv_python=None, rule_only=False):
        self.source = "rule"
        self._real = None
        if rule_only:
            return
        try:
            from tml_renderers import renderers
            tk = renderers.Inkling2().tokenizer
            tk = tk() if callable(tk) else tk
            self._real = lambda texts: [len(tk.encode_ordinary(t)) for t in texts]
            self.source = "tokenizer"
        except ImportError:
            if venv_python:
                self._real = self._worker(venv_python)
                if self._real is not None:
                    self.source = "tokenizer"

    def _worker(self, venv_python):
        def run(texts):
            proc = subprocess.run([venv_python, "-I", "-B", os.path.join(HERE, "cost.py"), "--token-worker"],
                                  input=json.dumps(texts), capture_output=True, text=True, check=True)
            return json.loads(proc.stdout)
        try:
            probe = run(["x0 = 1"])
            if not (len(probe) == 1 and probe[0] >= 1):
                return None
        except (OSError, subprocess.CalledProcessError, ValueError):
            return None
        return run

    def count(self, texts):
        texts = list(texts)
        if self._real is not None:
            return self._real(texts)
        return [evaluate.count_pieces(t) for t in texts]


class Eval:
    """One evaluation line of a plan: a text arm on a held-out set, for `runs`
    model runs (the untrained model once, or one adapter per training seed)."""

    def __init__(self, label, text_arm, set_key, runs):
        self.label, self.text_arm, self.set_key, self.runs = label, text_arm, set_key, runs


class Plan:
    def __init__(self, name, arms, train_counts, seeds, epochs, eval1_counts, eval2_counts, cap, evals,
                 train_offset=0, eval1_offset=0):
        self.name, self.arms = name, tuple(arms)
        self.train_counts, self.seeds, self.epochs = dict(train_counts), seeds, epochs
        self.eval1_counts, self.eval2_counts, self.cap = dict(eval1_counts), dict(eval2_counts), cap
        self.evals = tuple(evals)
        self.train_offset, self.eval1_offset = train_offset, eval1_offset


# The pilot's training episodes sit 2000 seeds above the full plan's (which use
# the first 1024 of each tier), and its evaluation episodes 10000 above, so the
# pilot shares no episode with the full run.
PILOT_TRAIN_OFFSET = 2000
PILOT_EVAL_OFFSET = 10000
HELDOUT_PER_TIER = 500       # a choice: 1000 episodes per held-out set, see PREREG.md


def pilot_plan(cap):
    evals = [Eval("base model, text C", "C", "e1", 1), Eval("adapter C, text C", "C", "e1", 1)]
    return Plan("pilot", ("C",), {"S": 128, "M": 128}, 1, 1, {"S": 50, "M": 50}, {}, cap, evals,
                PILOT_TRAIN_OFFSET, PILOT_EVAL_OFFSET)


def full_plan(examples, seeds, cap, heldout_per_tier=HELDOUT_PER_TIER):
    half = examples // 2
    evals = [Eval("base model, text %s" % a, a, "e1", 1) for a in ep_mod.ARMS]
    evals += [Eval("adapter %s, text %s" % (a, a), a, "e1", seeds) for a in ep_mod.TRAIN_ARMS]
    evals += [Eval("adapter C, text %s (control)" % a, a, "e1", seeds) for a in ("B", "E", "N")]
    # second set: training seed 0 only, the four evaluations of the registered decision
    evals += [Eval("adapter C, text C", "C", "e2", 1), Eval("adapter B, text B", "B", "e2", 1),
              Eval("adapter C, text E (control)", "E", "e2", 1), Eval("adapter C, text N (control)", "N", "e2", 1)]
    return Plan("full", ep_mod.TRAIN_ARMS, {"S": half, "M": half}, seeds, 1,
                {"S": heldout_per_tier, "M": heldout_per_tier}, {"S": heldout_per_tier, "M": heldout_per_tier},
                cap, evals)


def _strings_for(epset, arm):
    out = []
    for ep in epset.episodes:
        r = ep_mod.render(ep, arm)
        out.append(([m["content"] for m in r.messages], r.target_text))
    return out


def _tokens(counter, epset, arm):
    """Per-episode (prompt_tokens, target_tokens), counted in one batch."""
    rows = _strings_for(epset, arm)
    flat = [codec.SYSTEM_LINE]
    for msgs, tgt in rows:
        flat += msgs + [tgt]
    uniq = sorted(set(flat))
    got = dict(zip(uniq, counter.count(uniq)))
    sys_tokens = got[codec.SYSTEM_LINE] + codec.MARKERS_PER_MESSAGE
    out = []
    for msgs, tgt in rows:
        prompt = sys_tokens + sum(got[m] + codec.MARKERS_PER_MESSAGE for m in msgs)
        out.append((prompt, got[tgt] + codec.REPLY_OVERHEAD))
    return out


def plan_counts(plan, counter):
    """Token totals per price kind, plus the items that make them up."""
    train = ep_mod.build_set("train", plan.train_counts, plan.train_offset)
    sets = {"e1": ep_mod.build_set("train" if plan.name == "pilot" else "heldout1", plan.eval1_counts,
                                   plan.eval1_offset)}
    if plan.eval2_counts and any(e.set_key == "e2" for e in plan.evals):
        sets["e2"] = ep_mod.build_set("heldout2", plan.eval2_counts)
    items = []
    train_total = prefill_total = sample_total = 0
    for arm in plan.arms:
        tr = _tokens(counter, train, arm)
        per_run = sum(p + t for p, t in tr) * plan.epochs
        n = per_run * plan.seeds
        train_total += n
        items.append(("train %s: %d examples x %d epoch x %d seed" % (arm, len(tr), plan.epochs, plan.seeds), "train", n, "count"))
    for e in plan.evals:
        ev = _tokens(counter, sets[e.set_key], e.text_arm)
        pf = sum(p for p, _ in ev) * e.runs
        sm = (plan.cap + codec.REPLY_OVERHEAD) * len(ev) * e.runs
        prefill_total += pf
        sample_total += sm
        items.append(("eval prefill %s on %s x%d" % (e.label, e.set_key, e.runs), "prefill", pf, "count"))
        items.append(("eval sample %s (cap %d, upper bound)" % (e.label, plan.cap), "sample", sm, "bound"))
    return {"train": train_total, "prefill": prefill_total, "sample": sample_total}, items


def usd_text(x, places=4):
    """Exact fraction rounded half up to `places` decimals, with integer math only."""
    scale = 10 ** places
    q = (x * scale * 2 + 1) // 2
    return "%d.%0*d" % (q // scale, places, q % scale)


def table(plan, counter):
    totals, items = plan_counts(plan, counter)
    rows = []
    for label, kind, n, how in items:
        price = tinker_backend.PRICES_PER_MILLION[kind]
        rows.append((label, kind, n, price, tinker_backend.cost_usd(kind, n)))
    total = sum((r[4] for r in rows), Fraction(0))
    lines = ["Plan %s (token source: %s)" % (plan.name, counter.source),
             "%-52s %-8s %12s %8s %14s" % ("item", "kind", "tokens", "$/M", "dollars")]
    for label, kind, n, price, c in rows:
        lines.append("%-52s %-8s %12d %8s %14s" % (label, kind, n, usd_text(price, 3), usd_text(c)))
    lines.append("%-52s %-8s %12d %8s %14s" % ("TOTAL", "", sum(totals.values()), "", usd_text(total)))
    lines.append("exact total: %s dollars" % total)
    return totals, total, lines


def main(argv):
    def opt(name, default):
        return argv[argv.index(name) + 1] if name in argv else default
    cap = int(opt("--cap", evaluate.DEFAULT_CAP))
    examples, seeds = int(opt("--examples", 2048)), int(opt("--seeds", 2))
    counter = Counter(opt("--venv-python", None))
    for plan in (pilot_plan(cap), full_plan(examples, seeds, cap)):
        _totals, _total, lines = table(plan, counter)
        print("\n".join(lines))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
