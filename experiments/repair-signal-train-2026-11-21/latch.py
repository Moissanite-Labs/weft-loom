"""One-touch latch for the second held-out set.

The second held-out set may be evaluated once per registered decision.

- A decision id must be in the registry (decisions.json, hashed into the
  harness lock and into every receipt). An id that is not registered is
  refused, so a new id cannot buy a new look.
- The touch is recorded as a receipt in the hash chain (receipts.py) and as one
  JSON line in the latch file. A second touch for the same decision id is
  refused before any evaluation starts if either record holds one, so a new
  latch path or a deleted latch file does not buy a second touch while the
  chain is the same. The chain receipt is written first, so a crash after the
  touch still counts as a touch. Limit: a new receipt chain and a new latch
  file together are a new experiment, and nothing in the files can tell.
- The registry is read from the hashed decisions.json (evaluate.DECISIONS_PATH)
  and evaluate_arm checks the token's decision id against that same registry,
  so a Latch cannot issue a token for an id that the locked registry lacks.
- A touch names the evaluations it covers, as (arm, descriptor) pairs. The
  token it returns is spent one pair at a time: an evaluation outside the list,
  or the same pair a second time, is refused.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import receipts  # noqa: E402


class LatchRefused(Exception):
    pass


class LatchToken:
    """Proof that Latch.touch ran. evaluate.py accepts only tokens that this
    module issued, and only for the (arm, descriptor) pairs they were issued for."""

    def __init__(self, decision_id, uses=()):
        self.decision_id = decision_id
        self.remaining = set(uses)


_ISSUED = []


def token_is_valid(token):
    return any(token is t for t in _ISSUED)


def spend(token, arm, descriptor, registry):
    """Uses up one evaluation of the token. Refused for a forged token, a
    decision id that the registry lacks, a pair the token does not cover and a
    pair already used."""
    if not token_is_valid(token):
        raise LatchRefused("the token was not issued by Latch.touch")
    if token.decision_id not in registry:
        raise LatchRefused("the token's decision id is not in the registry")
    pair = (arm, descriptor)
    if pair not in token.remaining:
        raise LatchRefused("the token does not cover this evaluation, or it was already used")
    token.remaining.discard(pair)


def load_registry(path):
    """The set of registered decision ids from a registry file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        raise LatchRefused("the decision registry cannot be read")
    rows = data.get("decisions") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows or not all(isinstance(x, str) and x for x in rows):
        raise LatchRefused("the decision registry needs a non-empty list of decision ids")
    if len(set(rows)) != len(rows):
        raise LatchRefused("the decision registry lists an id twice")
    return frozenset(rows)


class Latch:
    def __init__(self, path, receipts_path, registry_path):
        """path: the latch file. receipts_path: the hash chain that also holds
        each touch. registry_path: the file of decision ids."""
        self.path = path
        self.receipts_path = receipts_path
        self.registered = load_registry(registry_path)
        self.head = None        # chain head to expect (a Ratchet sets it), then the head after this latch's receipt

    def touched(self):
        out = [b["decision_id"] for b in receipts.bodies(self.receipts_path) if b.get("kind") == "touch"]
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        out.append(json.loads(line)["decision_id"])
        return sorted(set(out))

    def touch(self, decision_id, uses):
        """uses: the (arm, descriptor) pairs this decision may evaluate."""
        if not isinstance(decision_id, str) or decision_id not in self.registered:
            raise LatchRefused("decision id %r is not in the registry" % (decision_id,))
        pairs = [tuple(u) for u in uses]
        if not pairs or len(set(pairs)) != len(pairs):
            raise LatchRefused("a touch needs a non-empty list of distinct (arm, descriptor) pairs")
        if not all(len(p) == 2 and all(isinstance(x, str) and x for x in p) for p in pairs):
            raise LatchRefused("each use is a pair of non-empty strings")
        if decision_id in self.touched():
            raise LatchRefused("the second held-out set was already touched for " + decision_id)
        self.head = receipts.append(self.receipts_path, {"kind": "touch", "decision_id": decision_id,
                                                         "uses": [list(p) for p in pairs]}, self.head)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"decision_id": decision_id, "uses": [list(p) for p in pairs]}, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        token = LatchToken(decision_id, pairs)
        _ISSUED.append(token)
        return token
