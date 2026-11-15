import json, math, os, struct, sys, importlib.util
from collections import defaultdict
from pathlib import Path
import torch
def _weft():
    a = sys.argv
    w = a[a.index("--weft") + 1] if "--weft" in a and a.index("--weft") + 1 < len(a) else os.environ.get("WEFT_CHECKOUT")
    if not w:
        raise SystemExit("give the weft software checkout with --weft PATH or the WEFT_CHECKOUT environment variable")
    return Path(w)
INV = (_weft() / "weft" / "runtime" / "invariants" / "invariants.py").resolve()
spec = importlib.util.spec_from_file_location("inv", INV); inv = importlib.util.module_from_spec(spec); spec.loader.exec_module(inv)
S = {"Inf": math.inf, "-Inf": -math.inf, "NaN": math.nan}
dec = lambda x: (S[x] if x in S else float(x)) if isinstance(x, str) else x
def fb(u): return struct.unpack("<f", struct.pack("<I", u))[0]
def f32(x):
    try: return struct.unpack("<f", struct.pack("<f", x))[0]
    except OverflowError: return math.inf if x > 0 else -math.inf
cases = [json.loads(l) for l in open("cases.jsonl")]
js = {}
for l in open("js_out.jsonl"):
    d = json.loads(l); js[d["id"]] = d
cres = {}
for l in open("c_out.txt"):
    i, ok, bud, dist, before = l.split(); cres[int(i)] = dict(acc=bool(int(ok)), bud=fb(int(bud)), dist=fb(int(dist)), before=fb(int(before)))
def same(a, b):
    if isinstance(a, str): a = dec(a)
    if isinstance(b, str): b = dec(b)
    a = float(a); b = float(b)
    if a != a and b != b: return True
    return a == b
def close(a, b, rel=1e-9):
    a = dec(a) if isinstance(a, str) else a; b = dec(b) if isinstance(b, str) else b
    if a != a and b != b: return True
    if math.isinf(a) or math.isinf(b): return a == b
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-300)

# python results
pyres = {}; pytens = {}
for c in cases:
    base = [dec(x) for x in c["base"]]; cand = [dec(x) for x in c["cand"]]
    r, b, co = dec(c["r"]), dec(c["b"]), dec(c["c"])
    try:
        ok, dist, rem, reason = inv.verify_weight_update_safety_ex(base, cand, r, b, co, c["mask"])
        pyres[c["id"]] = dict(acc=ok, dist=dist, rem=rem, reason=reason)
    except Exception as e:
        pyres[c["id"]] = dict(acc=None, exc=repr(e)[:80], reason="EXCEPTION")
    if c["mask"] is None and len(base) == len(cand) and len(base) > 0 and c["c_ok"]:
        try:
            ok, dist, rem, reason = inv.verify_weight_update_safety_ex(torch.tensor(base, dtype=torch.float32), torch.tensor(cand, dtype=torch.float32), r, b, co)
            pytens[c["id"]] = dict(acc=ok, dist=dist, rem=rem, reason=reason)
        except Exception as e:
            pytens[c["id"]] = dict(acc=None, exc=repr(e)[:80], reason="EXCEPTION")

groups = defaultdict(list)  # (pair, kind, cls) -> [ids]
def rec(pair, kind, c): groups[(pair, kind, c["cls"])].append(c["id"])
tot = defaultdict(int)
for c in cases:
    i = c["id"]; p = pyres[i]; j = js[i]; cr = cres.get(i); t = pytens.get(i)
    if p["acc"] is None: rec("py", "python_raises", c)
    if "skip" not in j:
        tot["py_vs_js"] += 1
        if p["acc"] != j["acc"]: rec("py|js", "accept", c)
        if p["reason"] != j["reason"]: rec("py|js", "reason", c)
        if not same(p.get("rem", math.nan), j["rem"]): rec("py|js", "remaining", c)
        if p["acc"] is not None and not close(p["dist"], j["dist"], 1e-9) and not (p["dist"]==math.inf and j["dist"]=="Inf"): rec("py|js", "distance", c)
    if cr is not None:
        tot["py_vs_c"] += 1
        if "skip" not in j: tot["js_vs_c"] += 1
        if p["acc"] != cr["acc"]: rec("py|c", "accept", c)
        if "skip" not in j and j["acc"] != cr["acc"]: rec("js|c", "accept", c)
        if cr["acc"] != (cr["bud"] == cr["before"]) and False: pass
        if not cr["acc"] and not same(cr["bud"], cr["before"]): rec("c", "debits_budget_on_rejected_call", c)
        if cr["acc"] and p["acc"]:
            if not same(f32(p["rem"]), cr["bud"]): rec("py|c", "remaining_accepted_beyond_f32_round", c)
            elif not same(p["rem"], cr["bud"]): rec("py|c", "remaining_accepted_f32_rounding_only", c)
        if (not cr["acc"]) and (not p["acc"] if p["acc"] is not None else False):
            # python's reported remaining on reject vs C's budget after call
            if not same(f32(p["rem"]) if math.isfinite(p["rem"]) else p["rem"], cr["bud"]): rec("py|c", "remaining_on_reject_field_vs_c_budget", c)
    if t is not None:
        tot["pyList_vs_pyTensor"] += 1
        if p["acc"] != t["acc"]: rec("pyList|pyTensor", "accept", c)
        if p["reason"] != t["reason"]: rec("pyList|pyTensor", "reason", c)
cmap = {c["id"]: c for c in cases}
def summ(i):
    c = cmap[i]
    sh = lambda a: (a[:3] + ["..."] + a[-1:]) if len(a) > 6 else a
    s = f'id={i} base={sh(c["base"])} cand={sh(c["cand"])} r={c["r"]} budget={c["b"]} cost={c["c"]}'
    if c["mask"] is not None: s += f' mask={sh(c["mask"])}'
    s += f' | py={ {k: v for k, v in pyres[i].items()} } js={js[i]}'
    if i in cres: s += f' c={cres[i]}'
    if i in pytens: s += f' pytensor={pytens[i]}'
    return s
print("TOTAL cases", len(cases), dict(tot), "c_ok cases", len(cres), "mask cases", sum(1 for c in cases if c["mask"] is not None))
for k in sorted(groups):
    ids = groups[k]
    print(f"\n[{k[0]}] {k[1]} class={k[2]} count={len(ids)}\n   e.g. {summ(ids[0])}")

# ---- second pass: detail breakdowns
import collections
def show(title, pred, n=2):
    ids = [c["id"] for c in cases if pred(c)]
    print(f"\n### {title}: {len(ids)}")
    for i in ids[:n]: print("   ", summ(i)[:900])
    return ids
print("\n\n######## DETAIL")
# py|js remaining by (python reason, relation)
cnt = collections.Counter()
ex = {}
for c in cases:
    i = c["id"]; j = js[i]; p = pyres[i]
    if "skip" in j: continue
    if not same(p.get("rem", math.nan), j["rem"]):
        k = (p["reason"], "cost<=0" if dec(c["c"]) <= 0 else ("budget<=0" if dec(c["b"]) <= 0 else "other"))
        cnt[k] += 1; ex.setdefault(k, i)
print("py|js remaining mismatch by (reason, trigger):")
for k, v in cnt.items(): print("  ", k, v, "\n      ", summ(ex[k])[:600])
# py|c remaining on reject
cnt = collections.Counter(); ex = {}
for c in cases:
    i = c["id"]; cr = cres.get(i); p = pyres[i]
    if cr is None or cr["acc"] or p["acc"]: continue
    pr = p["rem"]; pr32 = f32(pr) if math.isfinite(pr) else pr
    if not same(pr32, cr["bud"]):
        rel = "C budget unchanged, py field=b-c" if same(cr["bud"], cr["before"]) else "C debited, py field differs"
        k = (p["reason"], rel); cnt[k] += 1; ex.setdefault(k, i)
print("\npy|c remaining-on-reject mismatch by (py reason, relation):")
for k, v in cnt.items(): print("  ", k, v, "\n      ", summ(ex[k])[:700])
# which rejected-call classes does C debit, by py reason
cnt = collections.Counter(); ex={}
for c in cases:
    i = c["id"]; cr = cres.get(i); p = pyres[i]
    if cr is None or cr["acc"]: continue
    k = (p["reason"], "C debits" if not same(cr["bud"], cr["before"]) else "C leaves budget")
    cnt[k] += 1; ex.setdefault(k, i)
print("\nC rejected calls by python reason and whether C changed *budget:")
for k in sorted(cnt): print("  ", k, cnt[k])
# python reports b-c on reject (py field != b) while never mutating: by reason
cnt = collections.Counter()
for c in cases:
    p = pyres[c["id"]]
    if p["acc"] is False and not same(p["rem"], dec(c["b"])): cnt[p["reason"]] += 1
print("\nPython/rejected calls whose reported remaining_budget != input budget, by reason:", dict(cnt))
# C accept / py reject etc
cnt = collections.Counter(); ex={}
for c in cases:
    i = c["id"]; cr = cres.get(i); p = pyres[i]
    if cr is None: continue
    if p["acc"] != cr["acc"]:
        k = ("C accepts, py rejects" if cr["acc"] else "C rejects, py accepts", c["cls"]); cnt[k]+=1; ex.setdefault(k,i)
print("\naccept disagreements py|c:", dict(cnt))
for k,i in ex.items(): print("  ", k, summ(i)[:800])
# zeno
cnt = collections.Counter(); ex={}
for c in cases:
    i = c["id"]; cr = cres.get(i); p = pyres[i]
    if cr and cr["acc"] and p["acc"] and not same(f32(p["rem"]), cr["bud"]):
        k = "c budget < f32(py rem) (C stricter: monotone nextafter)" if cr["bud"] < f32(p["rem"]) else "c budget > py"
        cnt[(c["cls"], k)] += 1; ex.setdefault((c["cls"], k), i)
print("\nbeyond-f32-round remaining on accept:", dict(cnt))
for k,i in ex.items(): print("  ", k, summ(i)[:800])
# tensor direction
cnt = collections.Counter(); ex = {}
for c in cases:
    i = c["id"]
    if i not in pytens: continue
    p = pyres[i]; t = pytens[i]
    if p["acc"] != t["acc"]:
        k = ("tensor ACCEPTS, list rejects" if t["acc"] else "tensor REJECTS, list accepts", c["cls"]); cnt[k] += 1; ex.setdefault(k, i)
print("\npyList|pyTensor accept disagreements:", dict(cnt))
for k, i in ex.items(): print("  ", k, summ(i)[:900])
# true-distance check for tensor false accepts: exact fsum distance vs r
bad = 0; tot_fa = 0; worst = 0
for c in cases:
    i = c["id"]
    if i in pytens and pytens[i]["acc"] and not pyres[i]["acc"] and pyres[i]["reason"] == "baseline_distance_exceeded":
        tot_fa += 1
        b_ = [dec(x) for x in c["base"]]; c_ = [dec(x) for x in c["cand"]]
        d = math.sqrt(math.fsum((x - y) ** 2 for x, y in zip(b_, c_)))
        if d > dec(c["r"]): bad += 1; worst = max(worst, d / dec(c["r"]) - 1 if dec(c["r"]) > 0 else 0)
print(f"\ntensor false accepts where exact (fsum) distance > r: {bad} of {tot_fa}; worst relative excess {worst:.3e}")
# py vs c & py vs js long case direction with exact distance
for c in cases:
    if c["cls"].startswith("long_65536") and cres.get(c["id"]) and pyres[c["id"]]["acc"] != cres[c["id"]]["acc"]:
        b_ = [dec(x) for x in c["base"]]; c_ = [dec(x) for x in c["cand"]]
        d = math.sqrt(math.fsum((x - y) ** 2 for x, y in zip(b_, c_)))
        print("long case", c["id"], "exact dist", repr(d), "r", c["r"], "py dist", pyres[c["id"]]["dist"], "c acc", cres[c["id"]]["acc"])
