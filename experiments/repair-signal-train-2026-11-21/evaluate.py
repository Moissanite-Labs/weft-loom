"""The locked evaluation.

Fixed seeds (episode sets), the exact checker (vendored rsig), one answer per
episode, one cap on reply tokens (the same in every arm), one reply grammar.

Reply grammar (anything else breaks the format):

    reply   := [fence] line { newline line } [fence]
    fence   := "```" [letters] newline ... newline "```"    (at most one pair, around everything)
    line    := "x" INDEX blanks "=" blanks number            (blank lines are ignored)
    INDEX   := 0 to n-1 with no leading zero, each variable exactly once
    number  := [SIGN] DIGITS                 an integer
             | [SIGN] DIGITS "." DIGITS      a decimal, read as an exact fraction
             | [SIGN] DIGITS "/" DIGITS      a fraction, denominator not zero
    SIGN    := "-" | "+"                     the texts for C, E and N show amounts with "+",
                                             so a leading "+" is not a format break
    DIGITS  := 1 to 12 ASCII digits (a decimal has 1 to 12 digits after the point)

Decimals and fractions are read as exact rationals (fractions.Fraction). A
reply that breaks the grammar is its own outcome (X), not a failed repair (F).

Token cap: a responder may report its own token count (a server that enforced
max_tokens). If it does not, the harness counts pieces with PIECE and cuts the
reply at the cap. PIECE gives one piece per digit, per run of letters and per
other mark, which is close to how digits tokenize in the real tokenizer.

A reply that was cut at the cap, by the responder (a third item in its answer)
or by the harness, is a format break (X), even if the cut text still parses: a
cut can land inside the last number and leave a different but valid value. The
raw replies and the cut flags stay in the result, so a decision can rescore
them (see rescore and Ratchet.record).
"""
import hashlib
import json
import os
import re
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import episodes as ep_mod  # noqa: E402
import latch as latch_mod  # noqa: E402
import vendor_loader  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
# The registry of decision ids. It is hashed into the harness lock, and the
# latch and evaluate_arm both read it from here. Tests and the dry run point it
# at their own file; a real run leaves it at the file shipped here.
DECISIONS_PATH = os.path.join(HERE, "decisions.json")
DEFAULT_CAP = 96            # a choice, not a measurement
PIECE = re.compile(r"[0-9]|[A-Za-z]+|[^\sA-Za-z0-9]", re.ASCII)

_LINE = re.compile(r"x(0|[1-9][0-9]{0,2})[ \t]*=[ \t]*([+-]?[0-9]{1,12}(?:\.[0-9]{1,12}|/[0-9]{1,12})?)", re.ASCII)
_FENCE = re.compile(r"```[A-Za-z]*\n(.*?)\n?```", re.S)


class EvalRefused(Exception):
    pass


def parse_reply(text, n):
    """Returns (list of Fraction, None) or (None, reason)."""
    body = text.strip()
    m = _FENCE.fullmatch(body)
    if m:
        body = m.group(1)
    if not body.strip():
        return None, "empty reply"
    vals = {}
    for ln, raw in enumerate(body.split("\n"), 1):
        line = raw.strip()
        if not line:
            continue
        g = _LINE.fullmatch(line)
        if not g:
            return None, "line %d breaks the grammar" % ln
        idx = int(g.group(1))
        if idx >= n:
            return None, "line %d names an unknown variable" % ln
        if idx in vals:
            return None, "variable x%d appears twice" % idx
        num = g.group(2)
        if "/" in num and int(num.split("/")[1]) == 0:
            return None, "line %d has a zero denominator" % ln
        vals[idx] = Fraction(num)
    for i in range(n):
        if i not in vals:
            return None, "variable x%d is missing" % i
    return [vals[i] for i in range(n)], None


def count_pieces(text):
    return len(PIECE.findall(text))


def cut_to_cap(text, cap):
    """Keep the first cap pieces of text. Returns (text, was_cut)."""
    n = 0
    for m in PIECE.finditer(text):
        n += 1
        if n > cap:
            return text[:m.start()], True
    return text, False


def harness_files():
    return {"evaluate_py": os.path.join(HERE, "evaluate.py"),
            "episodes_py": os.path.join(HERE, "episodes.py"),
            "vendor_loader_py": os.path.join(HERE, "vendor_loader.py"),
            "rsig_py": os.path.join(vendor_loader.DEFAULT_VENDOR, "rsig.py"),
            "decisions_json": DECISIONS_PATH}


def harness_hashes():
    vendor_loader.load_rsig()   # refuses if the pin does not hold
    return {k: vendor_loader.sha256_file(p) for k, p in harness_files().items()}


def canonical_sha256(obj):
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


class EvalResult:
    """All counts are integers. rate is passed over n, kept as two integers.
    episode_ids, texts and cuts hold what the model wrote, episode by episode
    (cuts is a string of 0 and 1), so the outcomes can be rescored."""

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def rate(self):
        return Fraction(self.passed, self.n)

    def body(self):
        keys = ("arm", "descriptor", "set_kind", "set_sha256", "cap", "n", "passed", "failed",
                "format_broken", "capped", "outcomes", "replies_sha256")
        out = {k: getattr(self, k) for k in keys}
        out["rate_num"], out["rate_den"] = self.passed, self.n
        out["harness"] = dict(self.harness)
        out["descriptor_sha256"] = hashlib.sha256(self.descriptor.encode()).hexdigest()
        return out

    def replies_entry(self):
        """What is stored so that the outcomes can be rescored from the replies."""
        return {"set_sha256": self.set_sha256, "arm": self.arm, "descriptor": self.descriptor,
                "episode_ids": list(self.episode_ids), "texts": list(self.texts), "cuts": self.cuts}


def outcome_of(R, ep, text, was_cut):
    """P passes the exact checker, F parses and fails it, X breaks the grammar or was cut at the cap."""
    if was_cut:
        return "X"
    cand, _why = parse_reply(text, ep.instance.n)
    if cand is None:
        return "X"
    return "F" if R.check(ep.instance, cand) else "P"


_REBUILT = {}


def rebuild_set(ids):
    """The episode set named by episode ids such as heldout1-S-400000, rebuilt from the seeds."""
    key = tuple(ids)
    if key not in _REBUILT:
        eps, counts = [], {}
        for eid in ids:
            parts = eid.split("-") if isinstance(eid, str) else []
            if len(parts) != 3 or not parts[2].isdigit() or parts[0] not in ep_mod.KIND_BASE:
                raise EvalRefused("episode id %r cannot be rebuilt" % (eid,))
            try:
                ep = ep_mod.build_episode(parts[0], parts[1], int(parts[2]))
            except ep_mod.EpisodeError as exc:
                raise EvalRefused("episode %s: %s" % (eid, exc))
            eps.append(ep)
            counts[ep.tier] = counts.get(ep.tier, 0) + 1
        if not eps or len({ep.kind for ep in eps}) != 1:
            raise EvalRefused("the episode ids must name one non-empty set")
        _REBUILT[key] = ep_mod.EpisodeSet(eps[0].kind, counts, eps)
    return _REBUILT[key]


def rescore(entry):
    """The outcome string for stored replies, recomputed with the exact checker
    on episodes rebuilt from their seeds. Refused if the set does not match."""
    ids, texts, cuts = entry["episode_ids"], entry["texts"], entry["cuts"]
    if not (len(ids) == len(texts) == len(cuts)) or any(c not in "01" for c in cuts):
        raise EvalRefused("the stored replies do not line up with their episodes")
    epset = rebuild_set(ids)
    if epset.sha256() != entry["set_sha256"]:
        raise EvalRefused("the rebuilt episodes differ from the set that was evaluated")
    R = ep_mod.rsig()
    return "".join(outcome_of(R, ep, t, c == "1") for ep, t, c in zip(epset.episodes, texts, cuts))


def evaluate_arm(responder, epset, arm, cap=DEFAULT_CAP, descriptor="unnamed", latch_token=None):
    """One answer per episode. responder(view) returns a reply text, or a pair
    (text, completion_tokens or None). Outcomes: P passes the exact checker,
    F parsed but fails it, X broke the reply grammar."""
    if arm not in ep_mod.ARMS:
        raise EvalRefused("unknown arm %r" % (arm,))
    if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:
        raise EvalRefused("cap must be a positive integer")
    if epset.kind not in ep_mod.KIND_BASE:
        raise EvalRefused("unknown episode set kind %r" % (epset.kind,))
    for ep in epset.episodes:
        if ep.kind != epset.kind:
            raise EvalRefused("episode %s does not belong to a %s set" % (ep.id, epset.kind))
        try:
            ep_mod.check_seed(ep.kind, ep.tier, ep.seed)
        except ep_mod.SeedRangeError as exc:
            raise EvalRefused("episode %s: %s" % (ep.id, exc))
    if epset.kind == "heldout2":
        try:
            latch_mod.spend(latch_token, arm, descriptor, latch_mod.load_registry(DECISIONS_PATH))
        except latch_mod.LatchRefused as exc:
            raise EvalRefused("the second held-out set needs a latch token for this evaluation: %s" % exc)
    hashes = harness_hashes()
    R = ep_mod.rsig()
    outcomes, replies, cuts, capped = [], [], [], 0
    for ep in epset.episodes:
        got = responder(ep_mod.View(ep, arm))
        if isinstance(got, tuple):
            text, ntok = got[0], got[1]
            was_cut = len(got) > 2 and bool(got[2])
        else:
            text, ntok, was_cut = got, None, False
        if not isinstance(text, str):
            raise EvalRefused("responder must return text")
        if ntok is None:
            text, harness_cut = cut_to_cap(text, cap)
            was_cut = was_cut or harness_cut
            capped += 1 if was_cut else 0
        elif ntok > cap:
            raise EvalRefused("responder reported %d tokens, over the cap %d" % (ntok, cap))
        elif ntok == cap:
            capped += 1
        replies.append(text)
        cuts.append("1" if was_cut else "0")
        outcomes.append(outcome_of(R, ep, text, was_cut))
    s = "".join(outcomes)
    return EvalResult(
        arm=arm, descriptor=descriptor, set_kind=epset.kind, set_sha256=epset.sha256(), cap=cap,
        n=len(s), passed=s.count("P"), failed=s.count("F"), format_broken=s.count("X"), capped=capped,
        outcomes=s, replies_sha256=canonical_sha256(replies), harness=hashes,
        episode_ids=[ep.id for ep in epset.episodes], texts=replies, cuts="".join(cuts))
