"""End-to-end self-test with the mock proposer. No model is run.

It shows three things. The harness detects a real difference between arms
(the mock uses an excess when it is shown one). It reports no difference when
two arms carry the same feedback. A run cut short and resumed gives the same
log as an uninterrupted run. It also drives the real HTTP client against a
local stub server.
"""
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python3 -I drops the script directory

import analyze  # noqa: E402
import rsig  # noqa: E402
import runner  # noqa: E402


class SelfTestFailure(Exception):
    pass


def need(cond, msg):
    if not cond:
        raise SelfTestFailure(msg)


def strip_time(path):
    out = []
    for r in runner.read_log(path):
        r = dict(r)
        r.pop("seconds", None)
        out.append(r)
    return out


def units_by_arm(path):
    return analyze.table(analyze.load_units(path))


def run_selftest(count=40, tier="S", k=4, base_seed=7000, tmpdir=None):
    tmp = tmpdir or tempfile.mkdtemp(prefix="rsig-selftest-")
    insts = rsig.make_suite(base_seed, count, tier)
    chat = runner.mock_chat("follow")
    report = {}

    # 1. a mock that uses the signed amount: C beats B, B beats D
    p1 = os.path.join(tmp, "arms.jsonl")
    runner.run_experiment(chat, "mock", list("ABCD"), insts, k, p1)
    s = analyze.summarize(analyze.load_units(p1), k)["mock"]["tiers"][tier]
    report["signed_mock"] = s
    cb = s["comparisons"]["primary_C_vs_B"]
    need(cb["p_pass_sign"] < 0.01, "C vs B not detected: %r" % cb)
    need(cb["second_only"] == 0 or cb["first_only"] > 5 * cb["second_only"], "C vs B direction")
    need(s["comparisons"]["check_C_vs_D"]["p_pass_sign"] < 0.01, "C vs D not detected")
    by = units_by_arm(p1)["mock", tier]
    bd = analyze.compare(by, "B", "D", k)
    need(bd["p_pass_sign"] < 0.01 and bd["first_only"] > bd["second_only"], "D does not lose to B: %r" % bd)
    need(s["arms"]["C"]["pass"] > s["arms"]["B"]["pass"] > s["arms"]["D"]["pass"], "arm order")
    need(s["verdict"] == "supports", "verdict %r" % s["verdict"])

    # 1b. a mock that ignores the feedback: all four arms tie exactly, and
    # the tie is not trivial (some units pass, some do not)
    p1b = os.path.join(tmp, "ignore.jsonl")
    runner.run_experiment(runner.mock_chat("ignore"), "mock-ignore", list("ABCD"), insts, k, p1b)
    by = units_by_arm(p1b)["mock-ignore", tier]
    for arm in "BCD":
        need(by[arm].keys() == by["A"].keys(), "ignore: instance sets differ")
        need(all(by[arm][i]["pass_round"] == by["A"][i]["pass_round"] for i in by["A"]),
             "ignore mock: arm %s differs from A" % arm)
    npass = sum(1 for u in by["A"].values() if u["passed"])
    need(0 < npass < count, "ignore mock tie is trivial: %d of %d pass" % (npass, count))
    ig = analyze.summarize(analyze.load_units(p1b), k)["mock-ignore"]["tiers"][tier]
    for name, c in ig["comparisons"].items():
        need(c["first_only"] == 0 and c["second_only"] == 0 and c["p_pass_sign"] == 1.0
             and c["p_rounds_signflip"] == 1.0, "ignore mock, %s: %r" % (name, c))
    need(ig["verdict"] == "too_few_discordant_pairs", "ignore verdict %r" % ig["verdict"])
    report["ignore_mock"] = {"passing_units_per_arm": npass, "of": count}

    # 1c. a mock that reads only the size of the excess: C and D tie exactly
    p1c = os.path.join(tmp, "magnitude.jsonl")
    runner.run_experiment(runner.mock_chat("magnitude"), "mock-mag", ["C", "D"], insts, k, p1c)
    by = units_by_arm(p1c)["mock-mag", tier]
    need(all(by["C"][i]["pass_round"] == by["D"][i]["pass_round"] for i in by["C"]),
         "magnitude mock: C and D differ")
    report["magnitude_mock"] = {"c_pass": sum(1 for u in by["C"].values() if u["passed"])}

    # 1d. round one is the same in every arm (the arms differ only after a failure)
    first = {}
    for r in runner.read_log(p1):
        if r["type"] == "round" and r["round"] == 1:
            first.setdefault(r["instance"], set()).add((r["chat_sha256"], r["reply_sha256"]))
    need(all(len(v) == 1 for v in first.values()), "round one differs between arms")

    # 2. identical arms report no difference
    rsig.ARMS["C2"] = rsig.feedback_C
    try:
        p2 = os.path.join(tmp, "same.jsonl")
        runner.run_experiment(chat, "mock", ["C", "C2"], insts, k, p2)
    finally:
        del rsig.ARMS["C2"]
    by = analyze.table(analyze.load_units(p2))["mock", tier]
    c = analyze.compare(by, "C", "C2", k, "greater")
    report["identical_arms"] = c
    need(c["first_only"] == 0 and c["second_only"] == 0, "identical arms disagree: %r" % c)
    need(c["p_pass_sign"] == 1.0 and c["p_rounds_signflip"] == 1.0, "identical arms gave p < 1")
    need(by["C"].keys() == by["C2"].keys() and
         all(by["C"][i]["pass_round"] == by["C2"][i]["pass_round"] for i in by["C"]), "identical arms differ")

    # 3. interrupted then resumed equals uninterrupted
    p3 = os.path.join(tmp, "resume.jsonl")
    n1 = runner.run_experiment(chat, "mock", list("ABCD"), insts, k, p3, stop_after=9)
    with open(p3, "a") as f:
        f.write('{"type": "round", "torn')  # torn write from a crash
    n2 = runner.run_experiment(chat, "mock", list("ABCD"), insts, k, p3)
    need(n1 == 9 and n1 + n2 == count * 4, "resume counts %d %d" % (n1, n2))
    need(strip_time(p3) == strip_time(p1), "resumed log differs from uninterrupted log")
    n3 = runner.run_experiment(chat, "mock", list("ABCD"), insts, k, p3)
    need(n3 == 0, "rerun on a finished log wrote units")
    report["resume"] = {"first_leg": n1, "second_leg": n2, "rerun_new_units": n3}

    # 4. the real HTTP client against a local stub
    seen = []
    mock = runner.mock_chat("follow")

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append((self.path, body["temperature"], body["model"]))
            reply = {"choices": [{"message": {"role": "assistant", "content": mock(body["messages"])}}]}
            data = json.dumps(reply).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        url = "http://127.0.0.1:%d/v1" % srv.server_address[1]
        p4 = os.path.join(tmp, "http.jsonl")
        runner.run_experiment(runner.http_chat(url, "stub-model"), "stub-model", ["C"], insts[:5], k, p4)
    finally:
        srv.shutdown()
        srv.server_close()
    need(seen and all(x[0] == "/v1/chat/completions" and x[1] == 0 and x[2] == "stub-model" for x in seen),
         "http request shape: %r" % seen[:2])
    direct = os.path.join(tmp, "direct.jsonl")
    runner.run_experiment(mock, "stub-model", ["C"], insts[:5], k, direct)
    need(strip_time(p4) == strip_time(direct), "http run differs from direct run")
    report["http"] = {"requests": len(seen)}
    return report


if __name__ == "__main__":
    print(json.dumps(run_selftest(), indent=1, sort_keys=True))
