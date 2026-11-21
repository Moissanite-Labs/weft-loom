"""Episodes: a puzzle from a seed, a failed attempt, a feedback message, nothing else.

The target is one canonical repair, the same in every arm (see
canonical_repair): the shared variable moved by the largest true excess, else
the smallest passing one- or two-variable move, else the planted solution. The
exact checker accepts it. Failed attempts are synthetic: the planted solution
with one or two variables moved by random rational steps (the generator's own
denominator), kept only if the exact checker rejects the result.

Texts (what follows a failed attempt):
  A  verdict only (rsig's text)
  B  which constraints failed and where (rsig's text)
  C  B plus an exact amount per listed constraint, neutral label "s"
  E  as C, but the amounts belong to another puzzle with the same number of
     violations (so only the pairing with the truth is broken)
  N  as C, but every amount has its sign flipped

Only violated constraints are listed, so every true amount is positive: text N
is text C with "+" changed to "-". For that reason N and E are test-time
controls. They are shown to an adapter trained on C and are not trained on:
an adapter trained on N would only relabel C (see the preregistration).

rsig's own text for C has a sentence that defines the sign ("The excess is the
left side minus the bound."). A text for N that flips the numbers would then
contradict that sentence. So C, E and N use the texts written here: one neutral
label, no sentence that defines its sign, so only the numbers differ.
"""
import hashlib
import json
import os
import random
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vendor_loader  # noqa: E402

ARMS = ("A", "B", "C", "E", "N")
TRAIN_ARMS = ("A", "B", "C")    # adapters are trained on these texts only; E and N are test-time controls
TIERS = ("S", "M")

# Ranges already used by the finished experiment. Never reused here.
REGISTERED_RANGES = ((100000, 100099), (200000, 200099))
# Each kind owns 100000 seeds. Within a kind, tier S starts at the base and
# tier M starts 50000 above it, so no tier shares a seed with another.
KIND_BASE = {"train": 300000, "heldout1": 400000, "heldout2": 500000}
KIND_SPAN = 100000
TIER_OFFSET = {"S": 0, "M": 50000}
MAX_PER_TIER = 50000
MAX_ATTEMPT_TRIES = 64
# Puzzles whose amounts feed text E. Outside every kind range and the registered ranges.
DECOY_BASE = 700000
DECOY_POOL = 5000


class EpisodeError(Exception):
    pass


class SeedRangeError(EpisodeError):
    pass


def rsig():
    return vendor_loader.load_rsig()


# ------------------------------------------------------------------ seeds

def _overlaps(a_lo, a_hi, b_lo, b_hi):
    return a_lo <= b_hi and b_lo <= a_hi


def _require_known(kind, tier):
    if kind not in KIND_BASE:
        raise SeedRangeError("unknown kind %r" % (kind,))
    if tier not in TIER_OFFSET:
        raise SeedRangeError("unknown tier %r" % (tier,))


def seed_span(kind, tier, count, offset=0):
    """Inclusive (lo, hi) of the seeds for one tier of one kind, starting
    `offset` above the tier's first seed. Refuses any overlap with the
    registered ranges or with another kind's seeds."""
    _require_known(kind, tier)
    if not isinstance(count, int) or isinstance(count, bool) or count < 1 or count > MAX_PER_TIER:
        raise SeedRangeError("count must be an integer from 1 to %d" % MAX_PER_TIER)
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise SeedRangeError("offset must be a non-negative integer")
    lo = KIND_BASE[kind] + TIER_OFFSET[tier] + offset
    hi = lo + count - 1
    for r_lo, r_hi in REGISTERED_RANGES:
        if _overlaps(lo, hi, r_lo, r_hi):
            raise SeedRangeError("seeds %d-%d overlap the registered range %d-%d" % (lo, hi, r_lo, r_hi))
    for other, base in KIND_BASE.items():
        if other != kind and _overlaps(lo, hi, base, base + KIND_SPAN - 1):
            raise SeedRangeError("seeds %d-%d overlap the %s seeds" % (lo, hi, other))
    if hi > KIND_BASE[kind] + TIER_OFFSET[tier] + MAX_PER_TIER - 1:
        raise SeedRangeError("seeds %d-%d leave the %s tier range" % (lo, hi, tier))
    if lo < KIND_BASE[kind] or hi > KIND_BASE[kind] + KIND_SPAN - 1:
        raise SeedRangeError("seeds %d-%d leave the %s range" % (lo, hi, kind))
    return lo, hi


def check_seed(kind, tier, seed):
    """Refuses a seed that is not inside the range its kind and tier own, or
    that sits in a registered range."""
    _require_known(kind, tier)
    # a seed that is not an integer, or lies below the range, gives an offset
    # that seed_span refuses
    seed_span(kind, tier, 1, seed - (KIND_BASE[kind] + TIER_OFFSET[tier]))


# --------------------------------------------------------------- episodes

def _int_rng(*parts):
    digest = hashlib.sha256("/".join(str(p) for p in parts).encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _public(R, inst):
    """The instance without the planted point: what a model or policy may see."""
    return R.Instance(inst.n, inst.constraints, planted=None, seed=inst.seed, tier=inst.tier)


def _lines(values):
    return "\n".join("x%d = %s" % (i, v) for i, v in enumerate(values))


class Episode:
    def __init__(self, kind, tier, seed, instance, attempt, perturbation, tries, target, target_rule="planted"):
        self.kind, self.tier, self.seed = kind, tier, seed
        self.target_rule = target_rule
        self.instance = instance          # carries the planted point: builder side only
        self.attempt = tuple(attempt)
        self.perturbation = tuple(perturbation)
        self.tries = tries
        self.target = tuple(target)

    @property
    def id(self):
        return "%s-%s-%d" % (self.kind, self.tier, self.seed)

    def public_instance(self):
        return _public(rsig(), self.instance)

    def violations(self):
        return rsig().check(self.instance, list(self.attempt))

    def to_dict(self):
        return {"id": self.id, "instance": self.instance.to_dict(),
                "attempt": [str(x) for x in self.attempt],
                "perturbation": [[v, str(s)] for v, s in self.perturbation],
                "tries": self.tries, "target": [str(x) for x in self.target],
                "target_rule": self.target_rule}

    def sha256(self):
        blob = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()


def make_attempt(R, inst, tier, seed, _draw=None):
    """Planted solution with one or two variables moved by rational steps.
    Returns (attempt, perturbation, tries). _draw is a test hook that replaces
    the random choice of (variable, step) pairs."""
    den = R.TIERS[tier]["den"]
    planted = list(inst.planted)
    rng = _int_rng("attempt", tier, seed)
    for tries in range(1, MAX_ATTEMPT_TRIES + 1):
        if _draw is not None:
            moves = _draw(tries, inst)
        else:
            k = rng.choice((1, 2))
            moves = [(v, Fraction(rng.choice((-1, 1)) * rng.randint(1, 3 * den), den))
                     for v in rng.sample(range(inst.n), k)]
        attempt = list(planted)
        for v, step in moves:
            attempt[v] = attempt[v] + step
        if not R.check(inst, attempt):
            continue
        return attempt, [(v, s) for v, s in moves], tries
    raise EpisodeError("no failing attempt found for seed %d" % seed)


def search_order(moves):
    """The one- and two-variable move sets the search tries, smallest total
    size first, then fewer variables, then by variable and step. A pair never
    moves one variable twice."""
    tries = [(m,) for m in moves]
    tries += [(a, b) for i, a in enumerate(moves) for b in moves[i + 1:] if a[0] != b[0]]
    tries.sort(key=lambda t: (sum(abs(d) for _v, d in t), len(t), [(v, d) for v, d in t]))
    return tries


def canonical_repair(R, inst, attempt):
    """The one repair used as the training target in every arm. Returns
    (values, rule). Rules in order:
      max-excess  a variable shared by all violated constraints, moved the
                  right way by the largest true excess, if the exact checker
                  accepts the result. A variable that is the first named (u)
                  in every violated constraint comes before one that is the
                  second named (w), then the lower index, so a text that lists
                  "x1 - x3" has the target lower x1
      search      else the passing one- or two-variable move, with each step
                  one of the true excesses, that has the smallest total size
      planted     else the planted solution (always accepted)
    The max-excess rule is exact when one variable was moved. It is partial
    when two were. The checker decides every step."""
    vios = R.check(inst, list(attempt))
    if not vios:
        raise EpisodeError("the attempt passes: nothing to repair")
    top = max(v.excess for v in vios)
    shared = set.intersection(*[{v.u, v.w} for v in vios])
    roles = {var: {"u" if v.u == var else "w" for v in vios} for var in shared}
    order = sorted((var for var in shared if len(roles[var]) == 1), key=lambda var: (roles[var] == {"w"}, var))
    for var in order:
        cand = list(attempt)
        cand[var] = cand[var] + (-top if roles[var] == {"u"} else top)
        if not R.check(inst, cand):
            return cand, "max-excess"
    moves = sorted({(var, delta) for v in vios for var, delta in ((v.u, -v.excess), (v.w, v.excess))},
                   key=lambda m: (abs(m[1]), m[0], m[1]))
    for move in search_order(moves):
        cand = list(attempt)
        for var, delta in move:
            cand[var] = cand[var] + delta
        if not R.check(inst, cand):
            return cand, "search"
    return list(inst.planted), "planted"


def build_episode(kind, tier, seed, _draw=None):
    check_seed(kind, tier, seed)
    R = rsig()
    inst = R.make_instance(seed, tier=tier, **R.TIERS[tier])
    if R.check(inst, list(inst.planted)):
        raise EpisodeError("planted point fails the checker for seed %d" % seed)
    attempt, pert, tries = make_attempt(R, inst, tier, seed, _draw)
    target, rule = canonical_repair(R, inst, attempt)
    return Episode(kind, tier, seed, inst, attempt, pert, tries, target, rule)


class EpisodeSet:
    def __init__(self, kind, counts, episodes):
        self.kind = kind
        self.counts = dict(counts)
        self.episodes = tuple(episodes)

    def __len__(self):
        return len(self.episodes)

    def sha256(self):
        h = hashlib.sha256()
        h.update(json.dumps({"kind": self.kind, "counts": self.counts}, sort_keys=True).encode())
        for ep in self.episodes:
            h.update(ep.sha256().encode())
        return h.hexdigest()


def build_set(kind, counts, offset=0):
    """counts maps tier to the number of episodes, e.g. {"S": 50, "M": 50}.
    offset starts each tier that many seeds above its first seed, so a pilot
    can use training-range seeds that the training sample does not use."""
    if not counts:
        raise SeedRangeError("no tiers given")
    episodes = []
    for tier in sorted(counts):
        lo, hi = seed_span(kind, tier, counts[tier], offset)
        episodes += [build_episode(kind, tier, s) for s in range(lo, hi + 1)]
    return EpisodeSet(kind, counts, episodes)


# ----------------------------------------------------------- feedback text

_POOLS = {}


def decoy_pool(tier):
    """Excess lists of failed attempts at decoy puzzles, by number of violations.
    Text E shows one of these, so its numbers look like C's (all positive, the
    same sizes) and only their pairing with this puzzle is wrong."""
    R = rsig()
    key = (tier, vendor_loader.rsig_sha256())
    if key not in _POOLS:
        pool = {}
        lo = DECOY_BASE + TIER_OFFSET[tier]
        for s in range(lo, lo + DECOY_POOL):
            inst = R.make_instance(s, tier=tier, **R.TIERS[tier])
            attempt, _pert, _tries = make_attempt(R, inst, tier, s)
            vios = R.check(inst, attempt)
            pool.setdefault(len(vios), []).append(tuple(v.excess for v in vios))
        _POOLS[key] = pool
    return _POOLS[key]


def amounts_for(arm, vios, seed, tier):
    """The numbers shown next to each violated constraint, or None for A and B."""
    if arm in ("A", "B"):
        return None
    if arm == "C":
        return [v.excess for v in vios]
    if arm == "N":
        return [-v.excess for v in vios]
    if arm == "E":
        # The true amounts of a decoy puzzle with the same number of violations,
        # picked from the seed and the count alone: unrelated to this puzzle's truth.
        pool = decoy_pool(tier).get(len(vios))
        if not pool:
            raise EpisodeError("no decoy amounts for %d violations" % len(vios))
        return list(_int_rng("noise", tier, seed).choice(pool))
    raise EpisodeError("unknown arm %r" % (arm,))


def feedback_text(arm, vios, seed, tier):
    R = rsig()
    if arm == "A":
        return R.feedback_A(vios)
    if arm == "B":
        return R.feedback_B(vios)
    amts = amounts_for(arm, vios, seed, tier)
    lines = ["Verdict: FAILED. Violated constraints:"]
    for v, a in zip(vios, amts):
        lines.append("- %s: x%d - x%d <= %s (s %s)" % (v.cid, v.u, v.w, v.c, R.signed(a)))
    lines.append(R.REPLY_TAIL)
    return "\n".join(lines)


class Rendered:
    def __init__(self, messages, attempt_text, target_text):
        self.messages = messages
        self.attempt_text = attempt_text
        self.target_text = target_text


def render(ep, arm):
    R = rsig()
    vios = ep.violations()
    if not vios:
        raise EpisodeError("episode %s has an attempt that passes" % ep.id)
    attempt_text = _lines(ep.attempt)
    messages = [
        {"role": "user", "content": R.initial_prompt(ep.public_instance())},
        {"role": "assistant", "content": attempt_text},
        {"role": "user", "content": feedback_text(arm, vios, ep.seed, ep.tier)},
    ]
    return Rendered(messages, attempt_text, _lines(ep.target))


class View:
    """Everything a responder may see. No planted point, no target."""

    def __init__(self, ep, arm):
        r = render(ep, arm)
        self.arm = arm
        self.tier = ep.tier
        self.instance = ep.public_instance()
        self.attempt = ep.attempt
        self.messages = r.messages
        self.feedback = r.messages[-1]["content"]
        self.attempt_text = r.attempt_text
