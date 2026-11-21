"""Paid backend for thinkingmachines/Inkling-2-Mini on the Tinker service.

Adapted from the earlier smoke and training scripts (create a LoRA training
client, forward_backward then optim_step, sample for evaluation). Built and
unit-tested against a fake client only. Nothing here has been run against the
real service.

It refuses to start unless
  (a) an approvals file names this exact run id with a spend ceiling in dollars,
  (b) the planned token counts name all three price kinds with positive
      counts, and their cost at the published prices below is strictly less
      than that ceiling. driver.start_run computes the counts from cost.py for
      the run's configuration. TinkerRun checks their shape and size only.
It counts tokens as it goes and raises BudgetStop before a call that would
reach the ceiling. At most one checkpoint is saved per arm label. Sampled
tokens are counted as the service returned them, not as capped.

The spend is kept in an append-only ledger file (default: the approvals file
path plus ".spend.jsonl"). A reservation is written and fsynced before its
call, and any later refund or extra is written after it. A new process for the
same run id reads the ledger first and counts everything already spent against
the ceiling, so the ceiling holds across crashes and restarts. A run id that
has already started is refused unless the caller passes resume=True, and the
plan it was started with must be the same plan (plan_id). A restart runs the
plan again from the start, so the whole planned cost must fit under what is
left of the ceiling.

This module never reads, prints or stores a key. The service library finds its
own credentials when the real client is built. Errors are passed through
redact() before they leave this module.

Approvals file (JSON):
    {"approvals": [{"run_id": "RUN-ID", "ceiling_usd": "5.00"}]}
The ceiling is a string so that it is read as an exact fraction, never a float.
"""
import json
import os
import re
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codec as codec_mod  # noqa: E402

MODEL_ID = "thinkingmachines/Inkling-2-Mini"

# Dollars per million tokens at 64K context, from the published price table
# (fact sheet section H). Exact fractions.
PRICES_PER_MILLION = {
    "train": Fraction(3, 4),
    "prefill": Fraction(3, 20),
    "cached_prefill": Fraction(3, 200),
    "sample": Fraction(1, 2),
}
MILLION = 1000000


class ApprovalError(Exception):
    pass


class BudgetError(Exception):
    pass


class BudgetStop(Exception):
    pass


class BackendError(Exception):
    pass


_SECRETISH = re.compile(r"tml-[A-Za-z0-9_\-\.]+|[A-Za-z0-9_\-]{32,}|(?i:api[_-]?key)\s*[=:]\s*\S+")


def redact(text):
    return _SECRETISH.sub("[REDACTED]", str(text))[:400]


def cost_usd(kind, tokens):
    if kind not in PRICES_PER_MILLION:
        raise BudgetError("unknown price kind %r" % (kind,))
    if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0:
        raise BudgetError("token count must be a non-negative integer")
    return PRICES_PER_MILLION[kind] * tokens / MILLION


def planned_cost(plan_tokens):
    """plan_tokens maps price kinds to token counts. Returns exact dollars."""
    return sum((cost_usd(k, n) for k, n in plan_tokens.items()), Fraction(0))


PLAN_KINDS = ("train", "prefill", "sample")


def require_plan(plan_tokens):
    """A run plan names training, prefill and sampling, each above zero."""
    if not isinstance(plan_tokens, dict) or set(plan_tokens) != set(PLAN_KINDS):
        raise BudgetError("the plan must give token counts for exactly: %s" % ", ".join(PLAN_KINDS))
    for kind in PLAN_KINDS:
        n = plan_tokens[kind]
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise BudgetError("the %s count must be a positive integer" % kind)


def _refuse_float(text):
    raise ApprovalError("a float (%s) appears in the approvals file" % text)


def load_ceiling(approvals_path, run_id):
    """Exact ceiling in dollars for this run id, or ApprovalError."""
    try:
        with open(approvals_path, "r", encoding="utf-8") as fh:
            data = json.load(fh, parse_float=_refuse_float)
    except (OSError, ValueError):
        raise ApprovalError("the approvals file cannot be read")
    rows = data.get("approvals") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise ApprovalError("the approvals file has no approvals list")
    for row in rows:
        if isinstance(row, dict) and row.get("run_id") == run_id:
            raw = row.get("ceiling_usd")
            if not isinstance(raw, str):
                raise ApprovalError("ceiling_usd must be a string such as \"5.00\"")
            try:
                ceiling = Fraction(raw)
            except (ValueError, ZeroDivisionError):
                raise ApprovalError("ceiling_usd is not a number")
            if ceiling <= 0:
                raise ApprovalError("ceiling_usd must be above zero")
            return ceiling
    raise ApprovalError("run id %r is not approved" % (run_id,))


def _entry_cost(kind, tokens):
    """Dollars for a ledger entry, which may be negative (a refund)."""
    return PRICES_PER_MILLION[kind] * tokens / MILLION


class Ledger:
    """Append-only spend ledger for one run id, one JSON object per line.
    Lines of other run ids in the same file are skipped. Entries:
      start   a process began this run id under plan_id
      reserve tokens reserved before a call (written and fsynced first)
      adjust  signed token change after a call (a refund, or tokens over the reservation)"""

    def __init__(self, path, run_id):
        self.path, self.run_id = path, run_id

    def replay(self):
        """(spent, tokens by kind, number of starts, plan id of the first start)."""
        spent, tokens, starts, plan_id = Fraction(0), {k: 0 for k in PRICES_PER_MILLION}, 0, None
        if not os.path.exists(self.path):
            return spent, tokens, starts, plan_id
        with open(self.path, "rb") as fh:
            raw = fh.read()
        if raw and not raw.endswith(b"\n"):
            raise BudgetError("the spend ledger ends in a partial line: the owner must inspect it")
        for ln in raw.split(b"\n")[:-1]:
            try:
                row = json.loads(ln.decode("utf-8"), parse_float=_refuse_float)
            except (ValueError, ApprovalError):
                raise BudgetError("the spend ledger holds a line that is not valid JSON without floats")
            if not isinstance(row, dict) or not isinstance(row.get("run_id"), str) or not isinstance(row.get("ev"), str):
                raise BudgetError("the spend ledger holds a malformed line")
            if row["run_id"] != self.run_id:
                continue
            if row["ev"] == "start":
                if starts == 0:
                    plan_id = row.get("plan_id")
                starts += 1
                continue
            n = row.get("tokens")
            if row["ev"] not in ("reserve", "adjust") or row.get("kind") not in PRICES_PER_MILLION \
                    or not isinstance(n, int) or isinstance(n, bool) or (row["ev"] == "reserve" and n < 0):
                raise BudgetError("the spend ledger holds a malformed entry")
            tokens[row["kind"]] += n
            spent += _entry_cost(row["kind"], n)
            if tokens[row["kind"]] < 0:
                raise BudgetError("the spend ledger refunds more tokens than it reserved")
        return spent, tokens, starts, plan_id

    def append(self, row):
        row = dict(row, run_id=self.run_id)
        line = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            with open(self.path, "ab") as fh:
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())
        except OSError:
            raise BudgetStop("the spend ledger cannot be written, so no call is made")


class Meter:
    def __init__(self, ceiling, ledger=None, spent=Fraction(0), tokens=None):
        self.ceiling = Fraction(ceiling)
        self.spent = Fraction(spent)
        self.tokens = dict(tokens) if tokens is not None else {k: 0 for k in PRICES_PER_MILLION}
        self.ledger = ledger

    def _log(self, ev, kind, tokens):
        if self.ledger is not None:
            self.ledger.append({"ev": ev, "kind": kind, "tokens": tokens})

    def reserve(self, kind, tokens):
        """Counts the tokens, or raises BudgetStop before reaching the ceiling.
        With a ledger the reservation is on disk before this returns."""
        cost = cost_usd(kind, tokens)
        if self.spent + cost >= self.ceiling:
            raise BudgetStop("a call of %d %s tokens would reach the ceiling" % (tokens, kind))
        self._log("reserve", kind, tokens)
        self.spent += cost
        self.tokens[kind] += tokens

    def require_room(self, plan_tokens):
        """BudgetStop unless the whole of plan_tokens (an upper bound for some
        later calls) fits strictly under the ceiling, counting what is spent."""
        if self.spent + planned_cost(plan_tokens) >= self.ceiling:
            raise BudgetStop("the planned calls would reach the ceiling")

    def refund(self, kind, tokens):
        self._log("adjust", kind, -tokens)
        self.spent -= cost_usd(kind, tokens)
        self.tokens[kind] -= tokens

    def settle(self, kind, reserved, actual):
        """Replaces a reservation by what the service really used. More than
        reserved is counted in full, then the run stops if that reached the
        ceiling."""
        if actual <= reserved:
            self.refund(kind, reserved - actual)
            return
        extra = actual - reserved
        self._log("adjust", kind, extra)
        self.spent += cost_usd(kind, extra)
        self.tokens[kind] += extra
        if self.spent >= self.ceiling:
            raise BudgetStop("the service returned %d %s tokens, more than the %d reserved" % (actual, kind, reserved))


def _guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except (BudgetStop, BudgetError, ApprovalError):
        raise
    except Exception as exc:  # the service library raises many types
        raise BackendError("%s: %s" % (type(exc).__name__, redact(exc))) from None


def make_datum(types_mod, prompt_ids, target_ids):
    """Loss on the target tokens only, as in the earlier scripts."""
    t = list(prompt_ids) + list(target_ids)
    w = [0] * len(prompt_ids) + [1] * len(target_ids)
    return types_mod.Datum(model_input=types_mod.ModelInput.from_ints(tokens=t[:-1]),
                           loss_fn_inputs=dict(weights=w[1:], target_tokens=t[1:]))


class TinkerRun:
    def __init__(self, run_id, approvals_path, plan_tokens, service=None, types_mod=None, ledger_path=None,
                 plan_id=None, resume=False):
        ceiling = load_ceiling(approvals_path, run_id)              # (a)
        require_plan(plan_tokens)                                   # (b)
        budget = planned_cost(plan_tokens)
        ledger = Ledger(ledger_path if ledger_path is not None else approvals_path + ".spend.jsonl", run_id)
        spent, tokens, starts, first_plan = ledger.replay()
        if starts and not resume:
            raise ApprovalError("run id %r already started: a restart needs resume=True, and runs the plan "
                                "again from the start" % (run_id,))
        if starts and first_plan != plan_id:
            raise ApprovalError("run id %r was started under a different plan" % (run_id,))
        if not budget < ceiling - spent:
            raise BudgetError("planned cost %s is not under the ceiling %s less the %s already spent"
                              % (budget, ceiling, spent))
        self.run_id, self.budget, self.plan_id = run_id, budget, plan_id
        self.meter = Meter(ceiling, ledger, spent, tokens)
        self.service = service if service is not None else _real_service()
        self.types = types_mod if types_mod is not None else _real_types()
        ledger.append({"ev": "start", "plan_id": plan_id})
        self.clients = {}
        self.checkpoints = {}

    def start_arm(self, label, rank=8, seed=0, train_mlp=True, train_attn=True, train_unembed=True):
        if label in self.clients:
            raise BackendError("arm %r already has a training client" % (label,))
        self.clients[label] = _guard(
            self.service.create_lora_training_client, base_model=MODEL_ID, rank=rank, seed=seed,
            train_mlp=train_mlp, train_attn=train_attn, train_unembed=train_unembed)

    def train_step(self, label, datums, learning_rate):
        # a datum drops the last token of the sequence from its input, but the
        # service bills the whole sequence
        tokens = sum(d.model_input.length + 1 for d in datums)
        self.meter.reserve("train", tokens)
        client = self.clients[label]
        fb = _guard(client.forward_backward, datums, "cross_entropy")
        op = _guard(client.optim_step, self.types.AdamParams(learning_rate=learning_rate))
        _guard(fb.result)
        _guard(op.result)

    def checkpoint_sampler(self, label):
        """The one saved checkpoint of this arm, as a sampling client."""
        if self.checkpoints.get(label, 0) >= 1:
            raise BackendError("arm %r already saved its one checkpoint" % (label,))
        self.checkpoints[label] = self.checkpoints.get(label, 0) + 1
        return _guard(lambda: self.clients[label].save_weights_and_get_sampling_client().result())

    def base_sampler(self):
        return _guard(lambda: self.service.create_sampling_client(base_model=MODEL_ID))


class TinkerResponder:
    """Evaluation responder: samples one reply with at most `cap` reply tokens
    (plus the turn opening and the end marker), and counts prompt and returned
    tokens against the meter. codec is a codec.Codec: prompts carry real special tokens, and
    sampling stops on the end marker."""

    def __init__(self, run, sampler, codec, cap):
        self.run, self.sampler, self.codec, self.cap = run, sampler, codec, cap
        self.stats = {"calls": 0, "opening_seen": 0, "cut": 0}

    def __call__(self, view):
        ids = self.codec.prompt_ids(view.messages)
        limit = self.cap + codec_mod.REPLY_OVERHEAD    # the turn opening, the reply, the end marker
        meter = self.run.meter
        meter.reserve("prefill", len(ids))
        meter.reserve("sample", limit)                 # upper bound, settled below
        types = self.run.types
        resp = _guard(lambda: self.sampler.sample(
            prompt=types.ModelInput.from_ints(tokens=ids), num_samples=1,
            sampling_params=types.SamplingParams(max_tokens=limit, temperature=0.0,
                                                 stop=self.codec.stop_ids())).result())
        out = list(resp.sequences[0].tokens)
        meter.settle("sample", limit, len(out))        # counted as returned, even over the limit
        text, count, was_cut = self.codec.reply(out, self.cap)
        self.stats["calls"] += 1
        self.stats["opening_seen"] += 1 if self.codec.has_opening(out) else 0
        self.stats["cut"] += 1 if was_cut else 0
        return text, count, was_cut                    # a cut reply is a format break (evaluate.py)


def _real_service():
    import tinker  # only here; the library finds its own credentials
    return _guard(tinker.ServiceClient)


def _real_types():
    from tinker import types
    return types


def real_tokenizer():
    """The tokenizer carried by tml_renderers (unverified for Mini, see README).
    It has encode_ordinary, encode_special and decode, as codec.Codec needs."""
    from tml_renderers import renderers
    tk = renderers.Inkling2().tokenizer
    return tk() if callable(tk) else tk
