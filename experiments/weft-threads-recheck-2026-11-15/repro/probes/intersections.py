"""Intersections on the E13 harness (2026-11-15).

B) Gate as splice admission (T1 x T3 x calibration): benign vs harmful grafts.
   Admission rules compared: none, Frobenius R=120 / R=10, behavior drift on X_keep.
   Harmful packets: shuffled readout rows, gate column moved to a native skill,
   random-noise packet. Preregistered reading: Frobenius cannot separate harmful
   from benign (same slots overwritten); behavior drift can. Separation measured
   by AUROC of each score, harmful = positive.
C) Router with no oracle (T3 x T4 sense idea): plasmid receptor row may not read
   the gate column. A logistic router on z only (fit at splice time on keep/synth
   batches) drives the receptor. PASS >= 9/12 joint; FAIL <= 5/12.
Run: python3 intersections.py
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
    return host, pkt, X_keep, X_synth, (Xn, Yn, Xv, Yv), base


def joint(org, ev, base):
    Xn, Yn, Xv, Yv = ev
    nat = lab.eval_skill_r2(org, Xn, Yn)
    nov = lab.eval_skill_r2(org, Xv, Yv)
    return int(nat >= base - RET and nov >= NOV), nat, nov


def splice(host, pkt, Xk, Xs):
    org, meta = lab.splice_gfpt_neural_plasmid(
        host, pkt, Xk, Xs, geodesic_retraction_steps=4, lateral_shunting=True
    )
    return org, meta


def auroc(pos, neg):
    pos, neg = np.asarray(pos), np.asarray(neg)
    wins = sum(float(np.mean(p > neg) + 0.5 * np.mean(p == neg)) for p in pos)
    return round(float(wins / len(pos)), 4)


def pkt_copy(pkt, **over):
    q = copy.copy(pkt)
    for f in ["W1_p", "b1_p", "W2_p", "b2_p", "W3_p"]:
        setattr(q, f, getattr(pkt, f).copy())
    for k, v in over.items():
        setattr(q, k, v)
    return q


env = lab.FiveSkillEnvironment(world_seed=20261112)
frob, drift, held, novc, harm_nat_drop = {"benign": [], "harm": []}, {"benign": [], "harm": []}, {"benign": [], "harm": []}, {"benign": [], "harm": []}, []
benign_pass, harm_pass_if_admitted = [], []
router_pass, router_nov, router_acc = [], [], []

for seed in range(12):
    host, pkt, Xk, Xs, ev, base = build(env, seed)
    y_keep = host.predict(Xk)
    w0 = host.flat_params()

    Xn0 = ev[0]
    y_shift_host = host.predict(Xn0)
    Xv0 = ev[2]
    def score(org):
        d_f = float(np.linalg.norm(org.flat_params() - w0))
        d_b = float(np.sqrt(np.mean((org.predict(Xk) - y_keep) ** 2)))
        d_h = float(np.sqrt(np.mean((org.predict(Xn0) - y_shift_host) ** 2)))
        return d_f, d_b, d_h

    org, _ = splice(host, pkt, Xk, Xs)
    f, b, h = score(org)
    frob["benign"].append(f); drift["benign"].append(b); held["benign"].append(h)
    novc["benign"].append(float(np.sqrt(np.mean((org.predict(Xv0) - lab.eval_neural_plasmid(pkt, Xv0)) ** 2))))
    benign_pass.append(joint(org, ev, base)[0])

    rng = np.random.default_rng(500 + seed)
    harms = []
    q = pkt_copy(pkt); q.W3_p = q.W3_p[rng.permutation(q.W3_p.shape[0]), :]; harms.append(q)
    q = pkt_copy(pkt); q.W1_p[0, 16 + 2] = 0.0; q.W1_p[0, 16 + 0] = 2.0; harms.append(q)
    q = pkt_copy(pkt)
    for fld in ["W1_p", "W2_p", "W3_p"]:
        cur = getattr(q, fld)
        setattr(q, fld, rng.normal(0, float(np.std(cur)) + 1e-9, size=cur.shape))
    harms.append(q)
    for q in harms:
        org_h, _ = splice(host, q, Xk, Xs)
        f, b, h = score(org_h)
        frob["harm"].append(f); drift["harm"].append(b); held["harm"].append(h)
        novc["harm"].append(float(np.sqrt(np.mean((org_h.predict(Xv0) - lab.eval_neural_plasmid(q, Xv0)) ** 2))))
        p, nat, _ = joint(org_h, ev, base)
        harm_pass_if_admitted.append(p)
        harm_nat_drop.append(round(base - nat, 4))

    # C: z-only logistic router into receptor row 0, gate weight removed
    Z = np.vstack([Xk[:, :16], Xs[:, :16]])
    ylab = np.array([0] * len(Xk) + [1] * len(Xs), dtype=float)
    mu, sd = Z.mean(0), Z.std(0) + 1e-9
    Zs = (Z - mu) / sd
    w = np.zeros(16); bb = 0.0
    for _ in range(300):
        zlin = Zs @ w + bb
        pr = 1 / (1 + np.exp(-zlin))
        g = pr - ylab
        w -= 0.5 * (Zs.T @ g) / len(Zs)
        bb -= 0.5 * float(np.mean(g))
    acc = float(np.mean(((Zs @ w + bb) > 0) == (ylab > 0.5)))
    router_acc.append(round(acc, 4))
    q = pkt_copy(pkt)
    a = 2.0
    q.W1_p[0, :16] += a * (w / sd)
    q.b1_p[0] += a * (bb - float(np.sum(w * mu / sd)))
    q.W1_p[0, 16 + 2] = 0.0
    org_r, _ = splice(host, q, Xk, Xs)
    p, _, nov = joint(org_r, ev, base)
    router_pass.append(p); router_nov.append(round(nov, 4))
    print(f"seed {seed} benign_drift={drift['benign'][-1]:.5f} router_acc={acc:.3f} router_pass={p}", flush=True)

out = {
    "B_frobenius": {"benign_mean": round(float(np.mean(frob["benign"])), 3),
                    "harm_mean": round(float(np.mean(frob["harm"])), 3),
                    "auroc_harm_gt_benign": auroc(frob["harm"], frob["benign"]),
                    "accept_at_R120": f"{sum(d <= 120 for d in frob['benign'] + frob['harm'])}/{len(frob['benign']) + len(frob['harm'])}",
                    "accept_at_R10": f"{sum(d <= 10 for d in frob['benign'] + frob['harm'])}/{len(frob['benign']) + len(frob['harm'])}"},
    "B_behavior_drift": {"benign_mean": round(float(np.mean(drift["benign"])), 5),
                         "harm_mean": round(float(np.mean(drift["harm"])), 5),
                         "benign_max": round(float(np.max(drift["benign"])), 5),
                         "harm_min": round(float(np.min(drift["harm"])), 5),
                         "auroc_harm_gt_benign": auroc(drift["harm"], drift["benign"])},
    "B_heldout_drift": {"benign_mean": round(float(np.mean(held["benign"])), 5),
                         "harm_mean": round(float(np.mean(held["harm"])), 5),
                         "benign_max": round(float(np.max(held["benign"])), 5),
                         "harm_min": round(float(np.min(held["harm"])), 5),
                         "auroc_harm_gt_benign": auroc(held["harm"], held["benign"]),
                         "rule_at_benign_max_x1p5": {"benign_accept": f"{sum(d <= 1.5*float(np.max(held['benign'])) for d in held['benign'])}/12",
                                                     "harm_reject": f"{sum(d > 1.5*float(np.max(held['benign'])) for d in held['harm'])}/36"}},
    "B_novel_consistency": {"benign_mean": round(float(np.mean(novc["benign"])), 5),
                         "harm_mean": round(float(np.mean(novc["harm"])), 5),
                         "benign_max": round(float(np.max(novc["benign"])), 5),
                         "harm_min": round(float(np.min(novc["harm"])), 5),
                         "auroc_harm_gt_benign": auroc(novc["harm"], novc["benign"])},
    "B_two_sided_rule": {"native_thr": round(1.5 * float(np.max(held["benign"])), 5),
                         "novel_thr": round(1.5 * float(np.max(novc["benign"])), 5),
                         "benign_accept": f"{sum(1 for i in range(12) if held['benign'][i] <= 1.5*float(np.max(held['benign'])) and novc['benign'][i] <= 1.5*float(np.max(novc['benign'])))}/12",
                         "harm_reject": f"{sum(1 for i in range(36) if held['harm'][i] > 1.5*float(np.max(held['benign'])) or novc['harm'][i] > 1.5*float(np.max(novc['benign'])))}/36"},
    "B_outcomes": {"benign_pass": f"{sum(benign_pass)}/12",
                   "harm_joint_pass_if_admitted": f"{sum(harm_pass_if_admitted)}/36",
                   "harm_native_drop_mean": round(float(np.mean(harm_nat_drop)), 4)},
    "C_router": {"pass": f"{sum(router_pass)}/12", "novel_mean": round(float(np.mean(router_nov)), 4),
                 "fit_acc_mean": round(float(np.mean(router_acc)), 4), "per_seed": router_pass},
}
print(json.dumps(out, indent=1))
with open(str(Path(__file__).resolve().parents[1] / "out" / "intersections-results.json"), "w") as fh:
    json.dump(out, fh, indent=1)
