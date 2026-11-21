"""Pathwise check of S2 in the actual float32 training code (sampled implementation check).
Train a model and its image under a group element side by side; compare the trained
weights after mapping back. Sign flips should agree bitwise or to rounding; permutations
to float rounding (reduction order changes)."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np, torch
import nets, train_all


def _opt(name, default):
    """Folder option from the command line (for example --out DIR), with the record's layout as default."""
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument(name, default=default)
    known, rest = ap.parse_known_args()
    sys.argv[1:] = rest
    return getattr(known, name.lstrip("-").replace("-", "_"))

torch.set_num_threads(4)
P = nets.init_params([777001, 777002], "gated", 128)
rng = np.random.default_rng(31337)
# image of model 0 under a random hidden signed permutation (stored as model index 2 and 3 copies)
Q = train_all.signed_perm(P, rng)
both = {k: torch.cat([P[k], Q[k]]).clone() for k in P}
# sign-only element for model 1 (no permutation): flip units with a fixed pattern
e = torch.from_numpy(np.random.default_rng(5).choice([-1.0, 1.0], size=128).astype(np.float32))
for l in range(2):
    both["U%d" % l][1] = P["U%d" % l][1] * e[:, None]
    both["D%d" % l][1] = P["D%d" % l][1] * e[None, :]
    both["U%d" % l][3] = P["U%d" % l][1].clone(); both["D%d" % l][3] = P["D%d" % l][1].clone(); both["G%d" % l][3] = P["G%d" % l][1].clone()
for k in ("E1", "E2", "W", "gf", "g0", "g1"):
    both[k][3] = P[k][1].clone()
# now: model0 = P0, model2 = g.P0 (signed perm), model1 = e.P1 (signs only), model3 = P1
data = nets.stream(0, 0, 2000)
nets.train(both, data, "gated", "silu")
probe = torch.from_numpy(nets.probe_set())
with torch.no_grad():
    lg = nets.forward(both, probe[:, 0], probe[:, 1], "gated", nets.act_fn("silu"))
res = {"max_logit_diff_signed_perm_pair": float((lg[0] - lg[2]).abs().max()),
       "max_logit_diff_sign_only_pair": float((lg[1] - lg[3]).abs().max()),
       "max_weight_diff_sign_only_U0": float((both["U0"][1] - both["U0"][3] * e[:, None]).abs().max()),
       "max_weight_diff_sign_only_D1": float((both["D1"][1] - both["D1"][3] * e[None, :]).abs().max()),
       "logit_scale": float(lg.abs().mean())}
res["seeds"] = {"init": [777001, 777002], "group_element_rng": 31337, "sign_pattern_rng": 5, "stream": [0, 0], "steps": 2000}
print(json.dumps(res, indent=1))
with open(os.path.join(_opt("--out", os.path.join(HERE, "..", "out")), "equivariance_float.json"), "w") as f:
    json.dump(res, f, indent=1, sort_keys=True)
