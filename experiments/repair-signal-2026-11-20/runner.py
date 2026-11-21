"""Runner: any OpenAI-compatible chat endpoint, or a deterministic mock.

Writes one JSON line per round and one per finished unit (model, arm,
instance). A unit is written in one append, so an interrupted run loses at
most the unit in flight, and a rerun with the same log skips finished units.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from fractions import Fraction

import rsig


def sha(obj):
    blob = obj if isinstance(obj, str) else json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


# ------------------------------------------------------------------ clients

def http_chat(base_url, model, max_tokens=512, timeout=300, retries=3):
    """Returns chat(messages) -> reply text. Temperature is fixed at 0."""
    url = base_url.rstrip("/") + "/chat/completions"
    key = os.environ.get("RSIG_API_KEY")

    def chat(messages):
        body = json.dumps({"model": model, "messages": messages, "temperature": 0,
                           "seed": 0, "max_tokens": max_tokens, "stream": False}).encode()
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = "Bearer " + key
        last = None
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, data=body, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    data = json.loads(r.read().decode())
                return data["choices"][0]["message"].get("content") or ""
            except Exception as e:  # network or shape errors
                last = e
                time.sleep(1 + attempt)
        raise RuntimeError("chat request failed: %r" % (last,))

    return chat


_VIOL = re.compile(r"^- (c[0-9]+|goal): x([0-9]+) - x([0-9]+) <= (\S+?)(?: \(excess ([+-]?[0-9/]+)\))?$")
_CON = re.compile(r"^(c[0-9]+|goal): x([0-9]+) - x([0-9]+) <= (-?[0-9/]+)$")
MOCK_KINDS = ("follow", "magnitude", "ignore", "garbage")


def _solve_prompt(first, n):
    """Bellman-Ford on the constraints printed in the first message. Used
    only by the 'ignore' mock, which then answers by round number alone."""
    edges = []
    for line in first.split("\n"):
        m = _CON.match(line)
        if m:
            edges.append((int(m.group(2)), int(m.group(3)), Fraction(m.group(4))))
    d = [Fraction(0)] * n  # v(u) <= v(w) + c : relax d[u] = min(d[u], d[w] + c)
    for _ in range(n + 1):
        for u, w, c in edges:
            if d[w] + c < d[u]:
                d[u] = d[w] + c
    return d


def mock_chat(kind="follow"):
    """Deterministic stand-ins for a model. They read only the messages.
    All start from all zeros.
    follow:    after feedback, moves xU of each reported violation down by
               the printed excess when one is shown (so a flipped sign moves
               the wrong way), else by a fixed step of 1. With no constraint
               named it nudges one variable chosen by a hash of the chat.
    magnitude: as follow, but uses only the size of the printed excess and
               always moves down, so the sign carries no information.
    ignore:    ignores all feedback. It answers zeros until a round fixed by
               a hash of the first message alone, then answers a solution
               it finds from the constraint list. Same reply in every arm.
    garbage:   never gives a readable answer."""
    if kind not in MOCK_KINDS:
        raise ValueError(kind)

    def chat(messages):
        first = messages[0]["content"]
        n = int(re.search(r"x0 to x([0-9]+)", first).group(1)) + 1
        zeros = "\n".join("x%d = 0" % i for i in range(n))
        rnd = (len(messages) + 1) // 2
        if kind == "garbage":
            return "I think the answer is probably zero."
        if kind == "ignore":
            at = 2 + int(sha(first), 16) % 4
            if rnd < at:
                return zeros
            return "\n".join("x%d = %s" % (i, v) for i, v in enumerate(_solve_prompt(first, n)))
        if len(messages) == 1:
            return zeros
        prev, _ = rsig.parse_candidate(messages[-2]["content"], n)
        if prev is None:
            prev = [Fraction(0)] * n
        new = list(prev)
        viols = []
        for line in messages[-1]["content"].split("\n"):
            m = _VIOL.match(line)
            if m:
                viols.append(m.groups())
        if viols:
            for _cid, u, _w, _c, ex in viols:
                step = Fraction(ex) if ex is not None else Fraction(1)
                if kind == "magnitude":
                    step = abs(step)
                new[int(u)] = prev[int(u)] - step
        else:
            h = int(sha(messages), 16)
            new[h % n] += 1 if (h >> 8) & 1 else -1
        return "\n".join("x%d = %s" % (i, new[i]) for i in range(n))

    return chat


# --------------------------------------------------------------- run a unit

def run_unit(chat, instance, arm, k, model):
    messages = [{"role": "user", "content": rsig.initial_prompt(instance)}]
    rounds, keys, passed_at = [], [], None
    for r in range(1, k + 1):
        t0 = time.time()
        reply = chat(messages)
        secs = round(time.time() - t0, 3)
        cand, err = rsig.parse_candidate(reply, instance.n)
        vios = []
        if err is not None:
            verdict, fb = "unparsable", rsig.feedback_unparsed(err)
            key = "RAW:" + sha(reply)
        else:
            vios = rsig.check(instance, cand)
            key = rsig.canon(cand)
            if vios:
                verdict, fb = "fail", rsig.feedback(arm, vios)
            else:
                verdict, fb = "pass", None
        keys.append(key)
        rounds.append({
            "type": "round", "model": model, "arm": arm, "instance": instance.seed,
            "tier": instance.tier, "round": r,
            "chat_sha256": sha(messages), "prompt": messages[-1]["content"],
            "reply": reply, "reply_sha256": sha(reply), "verdict": verdict,
            "parse_error": err,
            "violations": [{"cid": v.cid, "excess": str(v.excess)} for v in vios],
            "feedback": fb, "seconds": secs})
        if verdict == "pass":
            passed_at = r
            break
        messages = messages + [{"role": "assistant", "content": reply},
                               {"role": "user", "content": fb}]
    stagnant = sum(1 for i in range(1, len(keys)) if keys[i] == keys[i - 1])
    unit = {"type": "unit", "model": model, "arm": arm, "instance": instance.seed,
            "tier": instance.tier, "instance_sha256": instance.sha256(), "k": k,
            "passed": passed_at is not None, "pass_round": passed_at,
            "rounds_used": len(rounds), "stagnant": stagnant,
            "transitions": max(0, len(keys) - 1),
            "unparsable_rounds": sum(1 for x in rounds if x["verdict"] == "unparsable")}
    return rounds, unit


def read_log(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass  # torn last line from an interrupted write
    return out


def run_experiment(chat, model, arms, instances, k, log_path, stop_after=None):
    """Resumes from log_path. stop_after: stop after that many new units
    (used by the self-test to simulate an interruption)."""
    done = {}
    for rec in read_log(log_path):
        if rec.get("type") == "unit":
            done[(rec["model"], rec["arm"], rec["tier"], rec["instance"], rec["k"])] = rec["instance_sha256"]
    new = 0
    for inst in instances:
        for arm in arms:
            key = (model, arm, inst.tier, inst.seed, k)
            if key in done:
                if done[key] != inst.sha256():
                    raise RuntimeError("log holds a different instance for seed %s" % inst.seed)
                continue
            if stop_after is not None and new >= stop_after:
                return new
            rounds, unit = run_unit(chat, inst, arm, k, model)
            blob = "".join(json.dumps(x, sort_keys=True) + "\n" for x in rounds + [unit])
            with open(log_path, "a+") as f:
                f.seek(0, os.SEEK_END)
                if f.tell() > 0:
                    f.seek(f.tell() - 1)
                    if f.read(1) != "\n":  # torn last line: start a fresh one
                        f.write("\n")
                f.write(blob)
                f.flush()
                os.fsync(f.fileno())
            new += 1
    return new


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", help="base URL of an OpenAI-compatible server, e.g. http://127.0.0.1:8080/v1")
    ap.add_argument("--model", required=True, help="model name sent to the server (label only with --mock)")
    ap.add_argument("--mock", choices=list(MOCK_KINDS), help="use the deterministic mock, no network")
    ap.add_argument("--arms", default="A,B,C,D")
    ap.add_argument("--tier", default="S", choices=sorted(rsig.TIERS))
    ap.add_argument("--base-seed", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--log", required=True)
    a = ap.parse_args(argv)
    if a.mock:
        chat = mock_chat(a.mock)
    elif a.url:
        chat = http_chat(a.url, a.model, a.max_tokens)
    else:
        ap.error("give --url or --mock")
    arms = a.arms.split(",")
    for x in arms:
        if x not in rsig.ARMS:
            ap.error("unknown arm " + x)
    n = run_experiment(chat, a.model, arms, rsig.make_suite(a.base_seed, a.count, a.tier), a.k, a.log)
    print("new units written: %d" % n)


if __name__ == "__main__":
    main()
