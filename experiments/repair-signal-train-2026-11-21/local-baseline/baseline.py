"""Untrained Inkling 2 Mini (Q8_0, local llama.cpp) on the pilot evaluation episodes.

Exploratory, free, local only. Run:

    python3 -I -B baseline.py sanity|main|summary|controls \
        --llama-server PATH_TO_llama-server --model PATH_TO_GGUF [--record DIR] [--out DIR] [--port N]

--record is the record folder that holds codec.py, episodes.py and evaluate.py
(default: the folder above this one). --out is where results.jsonl, server.log
and summary.json go (default: this folder). `summary` rebuilds summary.json
from results.jsonl and `controls` runs the offline control only. Neither starts
a server. Only pilot evaluation seeds are allowed: tier S 310000-310049, tier M
360000-360049. Anything else is refused in code.
"""
import json
import os
import statistics
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def option(name, default=None):
    argv = sys.argv
    if name in argv and argv.index(name) + 1 < len(argv):
        return argv[argv.index(name) + 1]
    return default


RECORD = os.path.abspath(option("--record", os.path.dirname(HERE)))
OUT = os.path.abspath(option("--out", HERE))
sys.path.insert(0, RECORD)
import codec as codec_mod  # noqa: E402
import episodes as ep_mod  # noqa: E402
import evaluate  # noqa: E402

BIN = option("--llama-server")
MODEL = option("--model")
PORT = int(option("--port", "8092"))
BASE = "http://127.0.0.1:%d" % PORT
RESULTS = os.path.join(OUT, "results.jsonl")

PILOT = {"S": (310000, 310049), "M": (360000, 360049)}
TEXTS = ("A", "B", "C", "E", "N")
CAP = 96
R_MAX = 2000
R_BUDGET_S = 70 * 60

MARK = {"sys": "<|message_system|>", "user": "<|message_user|>", "model": "<|message_model|>",
        "text": "<|content_text|>", "end": "<|end_message|>", "eos": "<|content_model_end_sampling|>",
        "think": "<|content_thinking|>"}
ROLE = {"system": MARK["sys"], "user": MARK["user"], "assistant": MARK["model"]}


def guard(tier, seed):
    if tier not in PILOT or not isinstance(seed, int) or not (PILOT[tier][0] <= seed <= PILOT[tier][1]):
        raise SystemExit("REFUSED: seed %r tier %r is outside the pilot evaluation ranges" % (seed, tier))


def build(tier, seed):
    guard(tier, seed)
    return ep_mod.build_episode("train", tier, seed)


# ------------------------------------------------------------- http / server
def post(path, body, timeout=600):
    req = urllib.request.Request(BASE + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def port_busy():
    out = subprocess.run(["lsof", "-nP", "-iTCP:%d" % PORT], capture_output=True, text=True).stdout
    return bool(out.strip())


def other_servers():
    out = subprocess.run(["pgrep", "-fl", "llama-server"], capture_output=True, text=True).stdout
    return [l for l in out.splitlines() if l.strip() and "pgrep" not in l]


class Server:
    def __enter__(self):
        if port_busy():
            raise SystemExit("port %d is busy" % PORT)
        if other_servers():
            raise SystemExit("another llama-server runs: %s" % other_servers())
        if not BIN or not MODEL:
            raise SystemExit("--llama-server and --model are required to start the server")
        self.log = open(os.path.join(OUT, "server.log"), "w")
        self.p = subprocess.Popen([BIN, "-m", MODEL, "--host", "127.0.0.1", "--port", str(PORT), "-ngl", "all",
                                   "-c", "8192", "-np", "1"], stdout=self.log, stderr=subprocess.STDOUT)
        for _ in range(240):
            if self.p.poll() is not None:
                raise SystemExit("server exited early")
            try:
                with urllib.request.urlopen(BASE + "/health", timeout=2) as r:
                    if b'"ok"' in r.read():
                        return self
            except Exception:
                pass
            time.sleep(2)
        raise SystemExit("server not ready")

    def __exit__(self, *a):
        self.p.terminate()
        try:
            self.p.wait(30)
        except Exception:
            self.p.kill()
            self.p.wait()
        self.log.close()
        time.sleep(1)
        print("port %d free at end: %s" % (PORT, not port_busy()), flush=True)


# ------------------------------------------------------------------ prompt
def tokenize(text, special):
    return post("/tokenize", {"content": text, "parse_special": special, "add_special": False})["tokens"]


def forced_prompt(messages):
    """The prompt of mode F: the messages, then the model's turn opened for an answer."""
    return prompt_text(messages) + MARK["model"] + MARK["text"]


def prompt_text(messages):
    s = ROLE["system"] + MARK["text"] + codec_mod.SYSTEM_LINE + MARK["end"]
    for m in messages:
        s += ROLE[m["role"]] + MARK["text"] + m["content"] + MARK["end"]
    return s


def check_markers():
    ids = {}
    for k, m in MARK.items():
        one = tokenize(m, True)
        many = tokenize(m, False)
        if len(one) != 1 or len(many) == 1:
            raise SystemExit("marker %s is not one special token: %r vs %r" % (m, one, many))
        ids[k] = one[0]
    return ids


class ServerTok:
    """Tokenizer shim so the record's Codec can be compared with my text layout."""
    def __init__(self, ids):
        self.names = {"message_system": ids["sys"], "message_user": ids["user"], "message_model": ids["model"],
                      "content_text": ids["text"], "end_message": ids["end"],
                      "content_model_end_sampling": ids["eos"], "content_thinking": ids["think"]}

    def encode_special(self, name):
        return self.names[name]

    def encode_ordinary(self, text):
        return tokenize(text, False)

    def decode(self, ids):
        return post("/detokenize", {"tokens": list(ids)})["content"]


def check_layout(ids):
    """The forced-answer text layout == the record's Codec prompt ids, and ordinary text contains no marker id."""
    cod = codec_mod.Codec(ServerTok(ids))
    n = 0
    for tier, seed in (("S", 310000), ("M", 360000), ("S", 310007)):
        ep = build(tier, seed)
        for arm in TEXTS:
            msgs = ep_mod.render(ep, arm).messages
            got = tokenize(forced_prompt(msgs), True)
            want = cod.prompt_ids(msgs)
            if got != want:
                raise SystemExit("layout differs from codec.py for %s %s" % (ep.id, arm))
            body = [t for t in got if t not in ids.values()]
            if len(got) - len(body) != 3 * (len(msgs) + 1) + codec_mod.OPENING_TOKENS:
                raise SystemExit("unexpected marker count")
            n += 1
    return n


# --------------------------------------------------------------- generation
def stream_generate(prompt, n_predict, stop_fn):
    """Stream tokens (greedy). stop_fn(tokens) -> True ends the call client-side.
    Returns (tokens, finish, seconds)."""
    body = {"prompt": prompt, "n_predict": n_predict, "temperature": 0, "top_k": 1, "stream": True,
            "return_tokens": True, "cache_prompt": True}
    req = urllib.request.Request(BASE + "/completion", json.dumps(body).encode(), {"Content-Type": "application/json"})
    toks, finish = [], "length"
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=900) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            d = json.loads(line[5:])
            toks += d.get("tokens") or []
            if d.get("stop"):
                finish = d.get("stop_type") or "stop"
                break
            if stop_fn(toks):
                finish = "client_stop"
                break
    return toks, finish, time.perf_counter() - t0


def detok(ids):
    return post("/detokenize", {"tokens": list(ids)})["content"] if ids else ""


def label(R, ep, text, was_cut):
    if was_cut:
        return "cut"
    o = evaluate.outcome_of(R, ep, text, False)
    return {"P": "passed", "F": "failed", "X": "format_break"}[o]


def run_F(ids, ep, arm):
    R = ep_mod.rsig()
    msgs = ep_mod.render(ep, arm).messages
    prompt = forced_prompt(msgs)
    stops = (ids["end"], ids["eos"])
    # the end marker does not count against the cap (as in codec.reply), so allow cap+1 tokens
    toks, finish, secs = stream_generate(prompt, CAP + 1, lambda t: any(x in stops for x in t))
    reply_ids = []
    stopped = False
    for x in toks:
        if x in stops:
            stopped = True
            break
        reply_ids.append(x)
    was_cut = (not stopped) or len(reply_ids) > CAP
    text = detok(reply_ids[:CAP])
    why = "end_marker" if stopped and len(reply_ids) <= CAP else "cap"
    return {"reply": text, "gen_tokens": len(reply_ids), "stop": why if finish != "eos" else "eos_marker",
            "seconds": round(secs, 3), "outcome": label(R, ep, text, was_cut)}, prompt


def run_R(ids, ep, arm):
    R = ep_mod.rsig()
    msgs = ep_mod.render(ep, arm).messages
    prompt = prompt_text(msgs)

    def done(t):
        # an answer block has opened and closed, or sampling ended
        if ids["eos"] in t:
            return True
        return answer_span(t, ids) is not None and answer_span(t, ids)[1]

    toks, finish, secs = stream_generate(prompt, R_MAX, done)
    span = answer_span(toks, ids)
    if span is None:
        out, text = "no_answer", ""
        stop = "eos_marker" if ids["eos"] in toks else "cap"
    else:
        a_ids, closed = span
        text = detok(a_ids)
        if closed:
            out = label(R, ep, text, False)
            stop = "answer_closed"
        else:
            out, stop = "cut", "cap"
    think = []
    for i, x in enumerate(toks):
        if x == ids["think"]:
            think = toks[i + 1:]
            break
    return {"reply": text, "gen_tokens": len(toks), "stop": stop, "seconds": round(secs, 3), "outcome": out,
            "thinking_tokens": len(think)}, prompt


def answer_span(toks, ids):
    """(answer ids, closed) for the first content_text block, or None."""
    for i, x in enumerate(toks):
        if x == ids["text"]:
            body = []
            for y in toks[i + 1:]:
                if y in (ids["end"], ids["eos"]):
                    return body, True
                body.append(y)
            return body, False
    return None


# -------------------------------------------------------------------- main
def controls():
    R = ep_mod.rsig()
    ok_t = ok_a = 0
    for i in range(20):
        tier, seed = ("S", 310000 + i) if i < 10 else ("M", 360000 + i - 10)
        ep = build(tier, seed)
        ok_t += evaluate.outcome_of(R, ep, ep_mod._lines(ep.target), False) == "P"
        ok_a += evaluate.outcome_of(R, ep, ep_mod._lines(ep.attempt), False) == "P"
    print("control: canonical repair passes %d/20 (need 20); failed attempt passes %d/20 (need 0)" % (ok_t, ok_a), flush=True)
    if ok_t != 20 or ok_a != 0:
        raise SystemExit("control failed")
    return ok_t, ok_a


def sanity(ids):
    for i in range(5):
        ep = build("S", 310000 + i)
        arm = TEXTS[i]
        row, prompt = run_F(ids, ep, arm)
        print("=== %s text %s | prompt tail:\n...%s" % (ep.id, arm, prompt[-420:]), flush=True)
        print("--- reply %r | %s" % (row["reply"], {k: row[k] for k in ("gen_tokens", "stop", "seconds", "outcome")}), flush=True)


def load_done():
    done = {}
    if os.path.exists(RESULTS):
        for l in open(RESULTS):
            r = json.loads(l)
            done[(r["mode"], r["text"], r["tier"], r["seed"])] = r
    return done


def main_run(ids):
    done = load_done()
    out = open(RESULTS, "a")

    def emit(mode, arm, tier, seed, row):
        rec = {"text": arm, "tier": tier, "seed": seed, "mode": mode, **row}
        out.write(json.dumps(rec) + "\n")
        out.flush()
        done[(mode, arm, tier, seed)] = rec

    k = 0
    for tier in ("S", "M"):
        lo = PILOT[tier][0]
        for seed in range(lo, lo + 50):
            ep = build(tier, seed)
            for arm in TEXTS:
                if ("F", arm, tier, seed) in done:
                    continue
                row, _ = run_F(ids, ep, arm)
                emit("F", arm, tier, seed, row)
                k += 1
                if k % 25 == 0:
                    print("F %d calls, last %.1fs" % (k, row["seconds"]), flush=True)
    print("mode F done", flush=True)
    t0 = time.perf_counter()
    k = 0
    for i in range(20):
        for tier in ("S", "M"):
            seed = PILOT[tier][0] + i
            ep = build(tier, seed)
            for arm in ("B", "C"):
                if ("R", arm, tier, seed) in done:
                    continue
                if time.perf_counter() - t0 > R_BUDGET_S:
                    print("mode R stopped at the 70 minute budget", flush=True)
                    return
                row, _ = run_R(ids, ep, arm)
                emit("R", arm, tier, seed, row)
                k += 1
                if k % 5 == 0:
                    print("R %d calls, elapsed %.0fs" % (k, time.perf_counter() - t0), flush=True)
    print("mode R done", flush=True)


def summarize():
    rows = [json.loads(l) for l in open(RESULTS)]
    S = {"integers_only": "1", "note": "exploratory; Q8_0 local; greedy; pilot seeds; one run", "F": {}, "R": {}, "paired": {}, "seconds_per_call_ms": {}}
    for mode in ("F", "R"):
        for arm in TEXTS:
            for tier in ("S", "M"):
                rs = [r for r in rows if r["mode"] == mode and r["text"] == arm and r["tier"] == tier]
                if not rs:
                    continue
                c = lambda o: sum(r["outcome"] == o for r in rs)
                e = {"n": len(rs), "passed": c("passed"), "failed": c("failed"), "format_breaks": c("format_break"),
                     "cut_by_cap": c("cut"), "no_answer": c("no_answer"),
                     "median_generated_tokens": int(statistics.median(r["gen_tokens"] for r in rs))}
                S[mode]["%s_%s" % (arm, tier)] = e
    for mode in ("F", "R"):
        rs = [r for r in rows if r["mode"] == mode]
        if rs:
            S["seconds_per_call_ms"][mode + "_mean"] = int(1000 * sum(r["seconds"] for r in rs) / len(rs))
            S["seconds_per_call_ms"][mode + "_median"] = int(1000 * statistics.median(r["seconds"] for r in rs))
            S["seconds_per_call_ms"][mode + "_calls"] = len(rs)
        p = {(r["text"], r["tier"], r["seed"]): r["outcome"] == "passed" for r in rs}
        for tier in ("S", "M", "both"):
            keys = sorted({(t, s) for (a, t, s) in p if a == "C" and (tier == "both" or t == tier)})
            keys = [k for k in keys if ("B",) + k in p]
            S["paired"]["%s_%s" % (mode, tier)] = {
                "episodes": len(keys),
                "both_passed": sum(p[("C",) + k] and p[("B",) + k] for k in keys),
                "only_C_passed": sum(p[("C",) + k] and not p[("B",) + k] for k in keys),
                "only_B_passed": sum(p[("B",) + k] and not p[("C",) + k] for k in keys),
                "neither_passed": sum(not p[("C",) + k] and not p[("B",) + k] for k in keys)}
    json.dump(S, open(os.path.join(OUT, "summary.json"), "w"), indent=1, sort_keys=True)
    print(json.dumps(S, indent=1, sort_keys=True))


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "sanity"
    if what == "summary":
        summarize()
        raise SystemExit(0)
    controls()
    if what == "controls":
        raise SystemExit(0)
    with Server():
        ids = check_markers()
        print("markers are single tokens:", ids, flush=True)
        print("layout equals codec.py ids on %d prompts" % check_layout(ids), flush=True)
        if what == "sanity":
            sanity(ids)
        elif what == "main":
            try:
                main_run(ids)
            finally:
                summarize()
