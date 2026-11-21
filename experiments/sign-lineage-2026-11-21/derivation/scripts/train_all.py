"""Train every network for Statement S5. Sampled evidence. Seeds fixed here.

Usage (venv torch):  python -I train_all.py <experiment>
Experiments: null_h128 null_h64 null_h256 null_otherorder plain_relu plain_gelu plain_tanh
             descend siblings planted
Each writes ../runs/<name>*.npz and appends a line to ../runs/train_log.jsonl.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import torch  # noqa: E402
import nets  # noqa: E402


def _opt(name, default):
    """Folder option from the command line (for example --out DIR), with the record's layout as default."""
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument(name, default=default)
    known, rest = ap.parse_known_args()
    sys.argv[1:] = rest
    return getattr(known, name.lstrip("-").replace("-", "_"))


RUNS = _opt("--runs", os.path.join(HERE, "..", "runs"))
STEPS = 2000
torch.set_num_threads(8)

# name: (block, act, width, init seeds, teacher, stream)
BASE = {
    "null_h128": ("gated", "silu", 128, range(100000, 100400), 0, 0),
    "null_h64": ("gated", "silu", 64, range(110000, 110100), 0, 0),
    "null_h256": ("gated", "silu", 256, range(120000, 120100), 0, 0),
    "null_otherorder": ("gated", "silu", 128, range(130000, 130100), 0, 1),
    "plain_relu": ("plain", "relu", 128, range(140000, 140200), 0, 0),
    "plain_gelu": ("plain", "gelu", 128, range(150000, 150200), 0, 0),
    "plain_tanh": ("plain", "tanh", 128, range(160000, 160100), 0, 0),
    # siblings: same init as null_h128 models 0..39, different data order
    "siblings": ("gated", "silu", 128, range(100000, 100040), 0, 1),
}


def log(rec):
    os.makedirs(RUNS, exist_ok=True)
    with open(os.path.join(RUNS, "train_log.jsonl"), "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")


def run_base(name, chunk=100):
    block, act, h, seeds, teacher, strm = BASE[name]
    seeds = list(seeds)
    data = nets.stream(teacher, strm, STEPS)
    parts, losses = [], []
    t0 = time.time()
    for c in range(0, len(seeds), chunk):
        P = nets.init_params(seeds[c:c + chunk], block, h)
        loss, _ = nets.train(P, data, block, act)
        parts.append({k: v.numpy() for k, v in P.items()})
        losses.append(loss)
        print(name, "chunk", c, "mean final nll", float(loss.mean()), "elapsed", round(time.time() - t0, 1), flush=True)
    P = {k: torch.tensor(np.concatenate([p[k] for p in parts])) for k in parts[0]}
    meta = {"name": name, "block": block, "act": act, "h": h, "seeds": [seeds[0], seeds[-1]],
            "teacher": teacher, "stream": strm, "steps": STEPS, "lr": 3e-3, "wd": 0.01}
    nets.save(os.path.join(RUNS, name + ".npz"), P, meta)
    loss = np.concatenate(losses)
    log({**meta, "final_nll_mean": float(loss.mean()), "final_nll_min": float(loss.min()),
         "final_nll_max": float(loss.max()), "seconds": round(time.time() - t0, 1)})


def subset(P, idx):
    return {k: v[idx].clone() for k, v in P.items()}


def run_descend():
    """B = A continued for 30, 300, 3000 steps; same task (teacher 0, new stream 2)
    and different task (teacher 1, stream 3). Fresh AdamW. A = null_h128 models 0..39."""
    A, meta = nets.load(os.path.join(RUNS, "null_h128.npz"))
    for task, (teacher, strm) in {"same": (0, 2), "diff": (1, 3)}.items():
        P = subset(A, list(range(40)))
        data = nets.stream(teacher, strm, 3000)
        t0 = time.time()
        loss, snaps = nets.train(P, data, "gated", "silu", snap_at=(30, 300, 3000))
        for k, S in snaps.items():
            nets.save(os.path.join(RUNS, "descend_%s_%d.npz" % (task, k)), S,
                      {"from": "null_h128[0:40]", "task": task, "teacher": teacher, "stream": strm, "steps": k})
        log({"name": "descend_" + task, "teacher": teacher, "stream": strm, "snaps": [30, 300, 3000],
             "final_nll_mean": float(loss.mean()), "seconds": round(time.time() - t0, 1)})


def signed_perm(P, rng, L=nets.N_LAYERS, residual=False):
    """Apply a uniformly random element of the hidden-unit group (per block) and,
    if residual=True, also of the residual-coordinate signed-permutation group."""
    Q = {k: v.clone() for k, v in P.items()}
    M = Q["E1"].shape[0]
    for m in range(M):
        for l in range(L):
            h = Q["U%d" % l].shape[1]
            p = torch.from_numpy(rng.permutation(h))
            e = torch.from_numpy(rng.choice([-1.0, 1.0], size=h).astype(np.float32))
            Q["U%d" % l][m] = Q["U%d" % l][m][p] * e[:, None]
            if "G%d" % l in Q:
                Q["G%d" % l][m] = Q["G%d" % l][m][p]
            Q["D%d" % l][m] = Q["D%d" % l][m][:, p] * e[None, :]
        if residual:
            d = Q["E1"].shape[2]
            p = torch.from_numpy(rng.permutation(d))
            e = torch.from_numpy(rng.choice([-1.0, 1.0], size=d).astype(np.float32))
            for k in ("E1", "E2", "W"):
                Q[k][m] = Q[k][m][:, p] * e[None, :]
            Q["gf"][m] = Q["gf"][m][p]
            for l in range(L):
                Q["g%d" % l][m] = Q["g%d" % l][m][p]
                for k in ("G%d" % l, "U%d" % l):
                    if k in Q:
                        Q[k][m] = Q[k][m][:, p] * e[None, :]
                Q["D%d" % l][m] = Q["D%d" % l][m][p, :] * e[:, None]
    return Q


def run_planted():
    """A = null_h128 models 40..79. B = random group element applied to A, then
    (a) nothing, (b) 300 steps same task, (c) 3000 steps different task.
    Variant 'full' also randomises the residual basis."""
    A, meta = nets.load(os.path.join(RUNS, "null_h128.npz"))
    A = subset(A, list(range(40, 80)))
    probe = nets.probe_set()
    t = torch.from_numpy(probe)
    for variant, residual, seed in (("hidden", False, 424242), ("full", True, 535353)):
        rng = np.random.default_rng(seed)
        B0 = signed_perm(A, rng, residual=residual)
        with torch.no_grad():
            la = nets.forward(A, t[:, 0], t[:, 1], "gated", nets.act_fn("silu"))
            lb = nets.forward(B0, t[:, 0], t[:, 1], "gated", nets.act_fn("silu"))
        err = float((la - lb).abs().max())
        nets.save(os.path.join(RUNS, "planted_%s_0.npz" % variant), B0, {"variant": variant, "seed": seed, "steps": 0})
        P = {k: v.clone() for k, v in B0.items()}
        loss, snaps = nets.train(P, nets.stream(0, 4, 300), "gated", "silu", snap_at=(300,))
        nets.save(os.path.join(RUNS, "planted_%s_same300.npz" % variant), snaps[300], {"variant": variant, "steps": 300})
        P = {k: v.clone() for k, v in B0.items()}
        loss2, snaps = nets.train(P, nets.stream(1, 5, 3000), "gated", "silu", snap_at=(3000,))
        nets.save(os.path.join(RUNS, "planted_%s_diff3000.npz" % variant), snaps[3000], {"variant": variant, "steps": 3000})
        log({"name": "planted_" + variant, "seed": seed, "max_abs_logit_change_after_group_element": err,
             "nll_same300": float(loss.mean()), "nll_diff3000": float(loss2.mean())})
        print(variant, "function change", err, flush=True)


if __name__ == "__main__":
    name = sys.argv[1]
    if name in BASE:
        run_base(name)
    elif name == "descend":
        run_descend()
    elif name == "planted":
        run_planted()
    else:
        raise SystemExit("unknown experiment " + name)
