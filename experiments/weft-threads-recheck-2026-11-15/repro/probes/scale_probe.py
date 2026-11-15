"""Width scale probe: E13 splice at M1=M2=384 (~160k params, 13x), 6 seeds, A4 only.

Pass bar unchanged (>=5/6 joint). Question: does the mechanism survive when the
graft is a far smaller fraction of the host and retraction systems grow?
"""
import importlib.util
import json
import sys
from pathlib import Path
import time

import numpy as np

spec = importlib.util.spec_from_file_location("big", str(Path(__file__).resolve().parents[3] / "weft-threads-2026-11-15" / "probes" / "e13_lab_big.py"))
lab = importlib.util.module_from_spec(spec)
sys.modules["big"] = lab
spec.loader.exec_module(lab)

env = lab.FiveSkillEnvironment(world_seed=20261112)
passes, novs, nats, times = [], [], [], []
n_params = None
for seed in range(6):
    t0 = time.time()
    rng_h = np.random.default_rng(1000 + seed)
    rng_d = np.random.default_rng(2000 + seed)
    rng_ev = np.random.default_rng(8000 + seed)
    host = lab.init_organism(rng_h)
    n_params = int(host.flat_params().size)
    lab.train_organism_adam(host, env, [0, 1], rng_h, steps=280)
    donor = lab.init_organism(rng_d)
    lab.train_organism_adam(donor, env, [0, 1, 2], rng_d, steps=290)
    donor = lab.scramble_organism_hidden_gauge(donor, rng_d)
    pkt = lab.extract_neural_plasmid_from_donor(donor, skill_idx=2, probe_seed=777001 + seed)
    Xk, _ = env.sample_batch(rng_ev, [0, 1], n_per_skill=80, shifted=False)
    Xs, _ = env.sample_batch(rng_ev, [2], n_per_skill=256, shifted=False)
    Xn, Yn = env.sample_batch(rng_ev, [0, 1], n_per_skill=200, shifted=True)
    Xv, Yv = env.sample_batch(rng_ev, [2], n_per_skill=250, shifted=True)
    base = lab.eval_skill_r2(host, Xn, Yn)
    dref = lab.eval_skill_r2(donor, Xv, Yv)
    org, meta = lab.splice_gfpt_neural_plasmid(host, pkt, Xk, Xs, geodesic_retraction_steps=4, lateral_shunting=True)
    nat = lab.eval_skill_r2(org, Xn, Yn)
    nov = lab.eval_skill_r2(org, Xv, Yv)
    p = int(nat >= base - 0.025 and nov >= 0.70)
    passes.append(p); novs.append(round(nov, 4)); nats.append(round(nat, 4))
    times.append(round(time.time() - t0, 1))
    print(f"seed {seed} pass={p} novel={nov:.4f} donor={dref:.4f} native={nat:.4f} base={base:.4f} drift_factor={meta['drift_reduction_factor']:.2f} wire={len(pkt.raw_bytes)}B t={times[-1]}s", flush=True)

out = {"params": n_params, "passes": f"{sum(passes)}/6", "novel": novs, "native": nats, "sec_per_seed": times}
print(json.dumps(out))
with open(str(Path(__file__).resolve().parents[1] / "out" / "scale-results.json"), "w") as fh:
    json.dump(out, fh, indent=1)
