"""Packet-vs-donor agreement as admission check (third side).

Score: RMS(packet(X_fresh_novel) - donor(X_fresh_novel)), donor queried only at
admission time. Benign packets were distilled from the donor, so agreement is
tight by construction. Question: do shuffled-readout and noise packets separate?
"""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("lab", str(Path(__file__).resolve().parents[3] / "weft-threads-2026-11-15" / "probes" / "e13_lab.py"))
lab = importlib.util.module_from_spec(spec)
sys.modules["lab"] = lab
spec.loader.exec_module(lab)


def auroc(pos, neg):
    pos, neg = np.asarray(pos), np.asarray(neg)
    return round(float(np.mean([np.mean(p > neg) + 0.5 * np.mean(p == neg) for p in pos])), 4)


def pkt_copy(pkt):
    q = copy.copy(pkt)
    for f in ["W1_p", "b1_p", "W2_p", "b2_p", "W3_p"]:
        setattr(q, f, getattr(pkt, f).copy())
    return q


env = lab.FiveSkillEnvironment(world_seed=20261112)
ben, har = [], []
for seed in range(12):
    rng_d = np.random.default_rng(2000 + seed)
    rng_ev = np.random.default_rng(8000 + seed)
    donor = lab.init_organism(rng_d)
    lab.train_organism_adam(donor, env, [0, 1, 2], rng_d, steps=290)
    donor = lab.scramble_organism_hidden_gauge(donor, rng_d)
    pkt = lab.extract_neural_plasmid_from_donor(donor, skill_idx=2, probe_seed=777001 + seed)
    Xv, _ = env.sample_batch(rng_ev, [2], n_per_skill=250, shifted=True)
    yd = donor.predict(Xv)

    def agree(q):
        return float(np.sqrt(np.mean((lab.eval_neural_plasmid(q, Xv) - yd) ** 2)))

    ben.append(agree(pkt))
    rng = np.random.default_rng(500 + seed)
    q = pkt_copy(pkt); q.W3_p = q.W3_p[rng.permutation(q.W3_p.shape[0]), :]; har.append(agree(q))
    q = pkt_copy(pkt)
    for fld in ["W1_p", "W2_p", "W3_p"]:
        cur = getattr(q, fld)
        setattr(q, fld, rng.normal(0, float(np.std(cur)) + 1e-9, size=cur.shape))
    har.append(agree(q))
    print(f"seed {seed} benign={ben[-1]:.4f}", flush=True)

thr = 1.5 * max(ben)
out = {"benign_mean": round(float(np.mean(ben)), 4), "benign_max": round(float(max(ben)), 4),
       "harm_mean": round(float(np.mean(har)), 4), "harm_min": round(float(min(har)), 4),
       "auroc": auroc(har, ben),
       "rule_1p5x_benign_max": {"benign_accept": f"{sum(d <= thr for d in ben)}/12",
                                "harm_reject": f"{sum(d > thr for d in har)}/24"}}
print(json.dumps(out, indent=1))
with open(str(Path(__file__).resolve().parents[1] / "out" / "donor-agreement-results.json"), "w") as fh:
    json.dump(out, fh, indent=1)
