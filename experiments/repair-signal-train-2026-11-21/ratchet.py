"""The rule that accepts a new adapter as better.

Five gates, from the method's rules for any automated improvement loop:
  1. The evaluation harness is locked by hash (harness.lock.json).
  2. Receipts are chained and float-free (receipts.py verifies the chain).
     A result is only decided on if it is in that chain: an "eval" receipt with
     the same replies, episode set, harness and descriptor must exist, and the
     raw replies stored beside the chain (receipts path + ".replies.jsonl",
     named by hash in the receipt) are rescored with the exact checker on
     episodes rebuilt from their seeds. Counts must match the rescored
     outcomes. The chain is verified against the head this Ratchet last wrote,
     so a rewritten last receipt is refused within a process; pass head= to
     carry a head kept elsewhere into a new process.
  3. A candidate identical to the baseline is rejected. Identity means the same
     descriptor (adapter id and configuration) or the same replies on every
     episode.
  4. The second held-out set is touched once per registered decision. The
     decision id must be in the registry (decisions.json), each touch is a
     receipt in the chain and a line in the latch file, a second touch is
     refused if either holds one, and the token covers only the evaluations
     named at the touch, once each.
  5. Every comparison is at the same compute cap, the cap this ratchet was
     created with.

The exact checker stays outside the model and is the only judge. This module
never scores anything itself: it reads the outcome strings that evaluate.py
produced with the checker.

Acceptance on one set: the candidate passes strictly more episodes than the
baseline, and the exact one-sided paired sign test (on episodes where exactly
one of them passes) has p at most alpha. A decision needs the first held-out
set and then, once, the second.
"""
import json
import os
import sys
from fractions import Fraction
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluate  # noqa: E402
import latch as latch_mod  # noqa: E402
import receipts  # noqa: E402

DEFAULT_ALPHA = Fraction(1, 40)   # a choice


class RatchetRefused(Exception):
    pass


def sign_test_p(cand_only, base_only):
    """Exact one-sided binomial sign test: P(X >= cand_only), X ~ Bin(n, 1/2)."""
    n = cand_only + base_only
    if n == 0:
        return Fraction(1)
    return Fraction(sum(comb(n, k) for k in range(cand_only, n + 1)), 2 ** n)


def discordant(base_outcomes, cand_outcomes):
    if len(base_outcomes) != len(cand_outcomes):
        raise RatchetRefused("outcome strings differ in length")
    cand_only = sum(1 for b, c in zip(base_outcomes, cand_outcomes) if c == "P" and b != "P")
    base_only = sum(1 for b, c in zip(base_outcomes, cand_outcomes) if b == "P" and c != "P")
    return cand_only, base_only


TESTS = ("pass", "stratum", "format")


def paired_counts(first_outcomes, second_outcomes, test="pass"):
    """(first_only, second_only) on the same episodes, for one paired test.
      pass     first passes where second does not, and the reverse
      stratum  the same, on the episodes where neither broke the reply format
      format   first stays in the format where second breaks it, and the
               reverse (so a significant win for `first` means `second` breaks
               the format more often)"""
    if test not in TESTS:
        raise RatchetRefused("unknown test %r" % (test,))
    if len(first_outcomes) != len(second_outcomes):
        raise RatchetRefused("outcome strings differ in length")
    pairs = list(zip(first_outcomes, second_outcomes))
    if test == "stratum":
        pairs = [(a, b) for a, b in pairs if a != "X" and b != "X"]
    hit = (lambda o: o != "X") if test == "format" else (lambda o: o == "P")
    first_only = sum(1 for a, b in pairs if hit(a) and not hit(b))
    second_only = sum(1 for a, b in pairs if hit(b) and not hit(a))
    return first_only, second_only


class Ratchet:
    def __init__(self, receipts_path, latch_path, lock_path, cap, alpha=DEFAULT_ALPHA, head=None):
        """The decision ids the latch accepts come from decisions.json
        (evaluate.DECISIONS_PATH), which is hashed into the lock. head: the
        chain head kept elsewhere, if this is a new process on an old chain."""
        self.receipts_path = receipts_path
        self.latch = latch_mod.Latch(latch_path, receipts_path, evaluate.DECISIONS_PATH)
        self.lock_path = lock_path
        self.cap = cap
        self.alpha = Fraction(alpha)
        self.head = head
        self._scored = set()

    @property
    def replies_path(self):
        return self.receipts_path + ".replies.jsonl"

    def _append(self, body):
        self.head = receipts.append(self.receipts_path, body, self.head)
        return self.head

    def _bodies(self):
        return receipts.bodies(self.receipts_path, self.head)

    def measure(self, body):
        """Appends a measurement receipt (integers and strings only), such as the pilot's."""
        return self._append(body)

    def _store_replies(self, result):
        """Appends the raw replies of a result, once per distinct entry, and returns the entry's hash."""
        entry = result.replies_entry()
        key = evaluate.canonical_sha256(entry)
        if key not in self._stored_replies():
            line = json.dumps({"sha256": key, "entry": entry}, sort_keys=True, separators=(",", ":")) + "\n"
            with open(self.replies_path, "a", encoding="utf-8") as fh:
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())
        return key

    def _stored_replies(self):
        out = {}
        if os.path.exists(self.replies_path):
            with open(self.replies_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        row = json.loads(line)
                        out[row["sha256"]] = row["entry"]
        return out

    # gate 1
    def lock_harness(self):
        current = evaluate.harness_hashes()
        if os.path.exists(self.lock_path):
            with open(self.lock_path, "r", encoding="utf-8") as fh:
                if json.load(fh) != current:
                    raise RatchetRefused("a lock exists and differs from the harness")
            return current
        with open(self.lock_path, "w", encoding="utf-8") as fh:
            json.dump(current, fh, sort_keys=True, indent=1)
            fh.write("\n")
        return current

    def check_lock(self):
        if not os.path.exists(self.lock_path):
            raise RatchetRefused("the harness is not locked")
        with open(self.lock_path, "r", encoding="utf-8") as fh:
            locked = json.load(fh)
        if evaluate.harness_hashes() != locked:
            raise RatchetRefused("the evaluation harness differs from its locked hashes")
        return locked

    # gate 2
    def record(self, result, run_id, config):
        """Append the evaluation receipt. The config dict is hashed into it. The
        raw replies are stored first and rescored: a result whose replies do
        not give its outcomes is refused."""
        locked = self.check_lock()
        if result.harness != locked:
            raise RatchetRefused("the result was produced by a different harness than the lock")
        self._recount(result)
        self._rescored(result.replies_entry(), result)
        body = result.body()
        body.update({"kind": "eval", "run_id": run_id, "config_sha256": evaluate.canonical_sha256(config),
                     "replies_entry_sha256": self._store_replies(result)})
        return self._append(body)

    def _rescored(self, entry, r):
        """Refuses unless the replies in entry, rescored, give r's outcomes and replies hash."""
        key = (evaluate.canonical_sha256(entry), r.outcomes)
        if key in self._scored:
            return
        try:
            again = evaluate.rescore(entry)
        except evaluate.EvalRefused as exc:
            raise RatchetRefused("the replies cannot be rescored: %s" % exc)
        if again != r.outcomes:
            raise RatchetRefused("the replies, rescored with the exact checker, differ from the result's outcomes")
        if evaluate.canonical_sha256(entry["texts"]) != r.replies_sha256:
            raise RatchetRefused("the stored replies differ from the result's replies hash")
        self._scored.add(key)

    def _recount(self, r):
        """Passes, failures and format breaks recounted from the outcome string."""
        s = r.outcomes
        if not isinstance(s, str) or not s or any(ch not in "PFX" for ch in s):
            raise RatchetRefused("the outcome string holds something other than P, F and X")
        if (r.n, r.passed, r.failed, r.format_broken) != (len(s), s.count("P"), s.count("F"), s.count("X")):
            raise RatchetRefused("the counts of a result differ from its outcome string")

    def _require_recorded(self, results):
        """Every result must match an eval receipt in the verified chain."""
        recorded = [b for b in self._bodies() if b.get("kind") == "eval"]
        stored = self._stored_replies()
        for r in results:
            self._recount(r)
            want = r.body()
            matches = [b for b in recorded if all(b.get(k) == v for k, v in want.items())]
            if not matches:
                raise RatchetRefused("a result is not in the receipt chain: record it before deciding")
            entry = stored.get(matches[0].get("replies_entry_sha256"))
            if entry is None or evaluate.canonical_sha256(entry) != matches[0]["replies_entry_sha256"]:
                raise RatchetRefused("the raw replies of a result are missing or were edited")
            self._rescored(entry, r)

    def _gates(self, base, cand):
        self.check_lock()
        self._require_recorded((base, cand))
        for r in (base, cand):
            if r.cap != self.cap:
                raise RatchetRefused("cap %d differs from the ratchet cap %d" % (r.cap, self.cap))
        if base.set_kind != cand.set_kind or base.set_sha256 != cand.set_sha256:
            raise RatchetRefused("baseline and candidate were not evaluated on the same episodes")
        if base.arm != cand.arm:
            raise RatchetRefused("baseline and candidate were evaluated in different arms")
        if base.harness != cand.harness:
            raise RatchetRefused("baseline and candidate came from different harnesses")
        if base.descriptor == cand.descriptor or base.replies_sha256 == cand.replies_sha256:
            raise RatchetRefused("the candidate is identical to the baseline")

    def decide(self, decision_id, base, cand):
        """Gates, then the sign test on one set. Appends a decision receipt."""
        self._gates(base, cand)
        cand_only, base_only = discordant(base.outcomes, cand.outcomes)
        p = sign_test_p(cand_only, base_only)
        accepted = cand.passed > base.passed and p <= self.alpha
        body = {"kind": "decision", "decision_id": decision_id, "set_kind": cand.set_kind,
                "accepted": 1 if accepted else 0, "cand_only": cand_only, "base_only": base_only,
                "p_num": p.numerator, "p_den": p.denominator,
                "alpha_num": self.alpha.numerator, "alpha_den": self.alpha.denominator,
                "cap": self.cap, "base_replies_sha256": base.replies_sha256,
                "cand_replies_sha256": cand.replies_sha256}
        head = self._append(body)
        return {"accepted": accepted, "cand_only": cand_only, "base_only": base_only, "p": p, "head": head}

    # comparison of two arms (C against B): same episodes, same cap, locked harness
    def compare_arms(self, decision_id, first, second, test="pass"):
        """Exact one-sided paired sign test that `first` beats `second` on the
        same episodes, for results from different texts or arms (for example
        the adapter trained on C against the adapter trained on B). `test` is
        pass, stratum or format (see paired_counts). Same gates 1, 2 and 5.
        Identical replies are a tie here, not a refusal."""
        self.check_lock()
        self._require_recorded((first, second))
        for r in (first, second):
            if r.cap != self.cap:
                raise RatchetRefused("cap %d differs from the ratchet cap %d" % (r.cap, self.cap))
        if first.set_kind != second.set_kind or first.set_sha256 != second.set_sha256:
            raise RatchetRefused("the two results were not evaluated on the same episodes")
        if first.harness != second.harness:
            raise RatchetRefused("the two results came from different harnesses")
        first_only, second_only = paired_counts(first.outcomes, second.outcomes, test)
        p = sign_test_p(first_only, second_only)
        body = {"kind": "arm_comparison", "test": test, "decision_id": decision_id, "set_kind": first.set_kind,
                "first_arm": first.arm, "second_arm": second.arm, "first_descriptor": first.descriptor,
                "second_descriptor": second.descriptor, "first_only": first_only,
                "second_only": second_only, "p_num": p.numerator, "p_den": p.denominator,
                "first_passed": first.passed, "second_passed": second.passed, "n": first.n, "cap": self.cap,
                "first_format_broken": first.format_broken, "second_format_broken": second.format_broken}
        head = self._append(body)
        return {"first_only": first_only, "second_only": second_only, "p": p, "head": head,
                "first_passed": first.passed, "second_passed": second.passed, "n": first.n,
                "first_better": first_only > second_only and p <= self.alpha}

    def second_set_results(self, decision_id, epset2, entries, config):
        """The one touch of the second held-out set for a registered decision.
        entries is a list of (key, responder, arm, descriptor). The latch is
        touched first, for exactly those (arm, descriptor) pairs. Every result
        is recorded. Returns {key: result}."""
        if epset2.kind != "heldout2":
            raise RatchetRefused("this is not the second held-out set")
        self.check_lock()
        self.latch.head = self.head
        token = self.latch.touch(decision_id, [(arm, desc) for _key, _resp, arm, desc in entries])
        self.head = self.latch.head
        out = {}
        for key, responder, arm, desc in entries:
            out[key] = evaluate.evaluate_arm(responder, epset2, arm, self.cap, desc, token)
        for key, _resp, _arm, _desc in entries:
            self.record(out[key], decision_id, config)
        return out

    def confirm_arms_second_set(self, decision_id, epset2, first_responder, first_arm, first_descriptor,
                                second_responder, second_arm, second_descriptor, config):
        """The same one-touch rule for a comparison of two results."""
        got = self.second_set_results(decision_id, epset2, [
            ("first", first_responder, first_arm, first_descriptor),
            ("second", second_responder, second_arm, second_descriptor)], config)
        return self.compare_arms(decision_id, got["first"], got["second"])

    # gate 4
    def confirm_second_set(self, decision_id, epset2, base_responder, cand_responder, arm,
                           base_descriptor, cand_descriptor, config):
        """Touches the latch (refused the second time for this decision id),
        evaluates both on the second held-out set, decides, records."""
        got = self.second_set_results(decision_id, epset2, [
            ("base", base_responder, arm, base_descriptor),
            ("cand", cand_responder, arm, cand_descriptor)], config)
        return self.decide(decision_id, got["base"], got["cand"])
