"""E13 hardening bundle (loom issue 6 kill tests).

Arms, same pass bar as the suite (native drop <= 0.025, novel R2 >= 0.70, shifted sets):
  A4-shared   : original design, one world seed 20261112 (sanity vs certificate)
  A4-worlds   : 12 distinct world seeds
  shunt sweep : strengths 0, -0.6, -1.2, -2.4, -4.8 on the shared world
  random slots: random dormant slots instead of lowest-Fisher, shared world
  trivial-MoE : external oracle router, plasmid alone when gate channel 2 fires
Preregistered reading (written before this run, 2026-11-15):
  worlds PASS >= 10/12 keeps the claim; <= 6/12 kills generality.
  If trivial-MoE matches A4, internal splicing adds packaging value only.
  If random slots match Fisher slots, Fisher selection is not load-bearing.
Run: python3 hardening.py
"""
import importlib.util
import json
import sys

import numpy as np

spec = importlib.util.spec_from_file_location("lab", "/Users/kethuda/Work/coordination/weft-threads/probes/e13_lab.py")
lab = importlib.util.module_from_spec(spec)
sys.modules["lab"] = lab
spec.loader.exec_module(lab)

RET, NOV = 0.025, 0.70


def build(env, seed):
    rng_h = np.random.default_rng(1000 + seed)
    rng_d = np.random.default_rng(2000 + seed)
    rng_ev = np.random.default_rng(8000 + seed)
    host = lab.init_organism(rng_h)
    lab.train_organism_adam(host, env, [0, 1], rng_h, steps=280)
    donor = lab.init_organism(rng_d)
    lab.train_organism_adam(donor, env, [0, 1, 2], rng_d, steps=290)
    donor = lab.scramble_organism_hidden_gauge(donor, rng_d)
    pkt = lab.extract_neural_plasmid_from_donor(donor, skill_idx=2, probe_seed=777001 + seed)
    X_keep, _ = env.sample_batch(rng_ev, [0, 1], n_per_skill=80, shifted=False)
    X_synth, _ = env.sample_batch(rng_ev, [2], n_per_skill=256, shifted=False)
    Xn, Yn = env.sample_batch(rng_ev, [0, 1], n_per_skill=200, shifted=True)
    Xv, Yv = env.sample_batch(rng_ev, [2], n_per_skill=250, shifted=True)
    base = lab.eval_skill_r2(host, Xn, Yn)
    return host, donor, pkt, X_keep, X_synth, (Xn, Yn, Xv, Yv), base


def joint(org, ev, base):
    Xn, Yn, Xv, Yv = ev
    nat = lab.eval_skill_r2(org, Xn, Yn)
    nov = lab.eval_skill_r2(org, Xv, Yv)
    return int(nat >= base - RET and nov >= NOV), nat, nov


def splice(host, pkt, Xk, Xs, **kw):
    org, _ = lab.splice_gfpt_neural_plasmid(
        host, pkt, Xk, Xs, geodesic_retraction_steps=4, lateral_shunting=True, **kw
    )
    return org


def trivial_moe_r2(host, pkt, X, Y):
    gate = X[:, 16 + 2]
    y_host = host.predict(X)
    y_plas = lab.eval_neural_plasmid(pkt, X)
    pick = (gate > 1.1)[:, None]
    pred = np.where(pick, y_plas, y_host)
    mse = float(np.mean((pred - Y) ** 2))
    return 1.0 - mse / (float(np.mean(Y ** 2)) + 1e-12)


res = {k: [] for k in ["A4_shared", "A4_worlds", "rand_slots", "trivial_moe"]}
novs = {k: [] for k in res}
sweep = {s: [] for s in [0.0, -0.6, -1.2, -2.4, -4.8]}
sweep_nov = {s: [] for s in sweep}

env_shared = lab.FiveSkillEnvironment(world_seed=20261112)
for seed in range(12):
    host, donor, pkt, Xk, Xs, ev, base = build(env_shared, seed)
    p, _, nov = joint(splice(host, pkt, Xk, Xs), ev, base)
    res["A4_shared"].append(p); novs["A4_shared"].append(nov)
    p, _, nov = joint(splice(host, pkt, Xk, Xs, slot_mode="random", slot_seed=seed), ev, base)
    res["rand_slots"].append(p); novs["rand_slots"].append(nov)
    for st in sweep:
        p, _, nov = joint(splice(host, pkt, Xk, Xs, shunt_strength=st), ev, base)
        sweep[st].append(p); sweep_nov[st].append(nov)
    Xn, Yn, Xv, Yv = ev
    nat = trivial_moe_r2(host, pkt, Xn, Yn)
    nov = trivial_moe_r2(host, pkt, Xv, Yv)
    res["trivial_moe"].append(int(nat >= base - RET and nov >= NOV)); novs["trivial_moe"].append(nov)
    print(f"shared seed {seed} done", flush=True)

for seed in range(12):
    env = lab.FiveSkillEnvironment(world_seed=20261112 + (seed + 1) * 7919)
    host, donor, pkt, Xk, Xs, ev, base = build(env, seed)
    p, _, nov = joint(splice(host, pkt, Xk, Xs), ev, base)
    res["A4_worlds"].append(p); novs["A4_worlds"].append(nov)
    print(f"world seed {seed} done pass={p} novel={nov:.4f}", flush=True)

out = {"passes": {k: f"{sum(v)}/12" for k, v in res.items()},
       "novel_mean": {k: round(float(np.mean(v)), 4) for k, v in novs.items()},
       "shunt_sweep_passes": {str(k): f"{sum(v)}/12" for k, v in sweep.items()},
       "shunt_sweep_novel": {str(k): round(float(np.mean(v)), 4) for k, v in sweep_nov.items()},
       "per_seed": res}
print(json.dumps(out, indent=1))
with open("/Users/kethuda/Work/coordination/weft-threads/probes/hardening-results.json", "w") as f:
    json.dump(out, f, indent=1)
