#!/usr/bin/env python3
"""Gate-metric calibration study, second architecture: a small transformer.

Same question and same measurements as calib.py, on a different kind of model,
as weft-loom issue 7 asks. The model is a two-layer, two-head transformer
(width 32, 18,205 weights) written in this file. It reads three tokens
(task, a, b) and predicts one of 23 classes at the last position.

  native tasks   max(a, b) and floor((a + b) / 2)
  novel task     |a - b|

The input space is finite, so the host is trained on all 1,058 native inputs.
The fit probes (96), the attacker's inputs (96) and the held-out inputs (866)
are disjoint parts of it.

Behaviour is the centred logit vector at the last position (logits minus their
mean over classes, which removes the shift that leaves probabilities alone).
The behaviour change is its RMS difference. The drop score is the fall in
accuracy on the held-out native inputs; the bar is 0.025.

Usage:
  python3 calib_tf.py --seeds 900 901 --out pilot_tf.json
  python3 calib_tf.py --seeds 0 1 2 3 4 5 6 7 8 9 10 11 --out results_tf.json

Needs NumPy and CPU PyTorch. Every internal check stops the run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.func import functional_call, jacrev, vmap

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calib import analyse, fail, row_basis, unit  # noqa: E402

torch.set_default_dtype(torch.float64)
torch.set_num_threads(4)

M = 23                    # number classes and operand range
VOCAB = M + 3             # operands plus three task tokens
D, HEADS, HID, LAYERS = 32, 2, 64, 2
DROP_MAX = 0.025
LR = 1e-3
SEED0 = 61_000_000
RADII = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 0.1, 0.3, 1.0, 3.0]
R_LOC, R_BLIND = 1e-3, 1e-2


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.ln1 = nn.LayerNorm(D)
        self.qkv = nn.Linear(D, 3 * D)
        self.proj = nn.Linear(D, D)
        self.ln2 = nn.LayerNorm(D)
        self.fc1 = nn.Linear(D, HID)
        self.fc2 = nn.Linear(HID, D)

    def forward(self, x):
        b, t, _ = x.shape
        q, k, v = self.qkv(self.ln1(x)).reshape(b, t, 3, HEADS, D // HEADS).permute(2, 0, 3, 1, 4)
        att = torch.softmax(q @ k.transpose(-1, -2) / math.sqrt(D // HEADS), dim=-1)
        x = x + self.proj((att @ v).transpose(1, 2).reshape(b, t, D))
        return x + self.fc2(F.gelu(self.fc1(self.ln2(x))))


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.emb = nn.Embedding(VOCAB, D)
        self.pos = nn.Parameter(torch.zeros(3, D))
        self.blocks = nn.ModuleList([Block() for _ in range(LAYERS)])
        self.lnf = nn.LayerNorm(D)
        self.out = nn.Linear(D, M)

    def forward(self, tok):
        x = self.emb(tok) + self.pos
        for blk in self.blocks:
            x = blk(x)
        z = self.out(self.lnf(x[:, -1]))
        return z - z.mean(dim=-1, keepdim=True)


def target(task, a, b):
    if task == 0:
        return max(a, b)
    if task == 1:
        return (a + b) // 2
    return abs(a - b)


def all_inputs(tasks):
    rows, ys = [], []
    for t in tasks:
        for a in range(M):
            for b in range(M):
                rows.append([M + t, a, b])
                ys.append(target(t, a, b))
    return torch.tensor(rows), torch.tensor(ys)


def names_shapes(net):
    return [(n, tuple(p.shape)) for n, p in net.named_parameters()]


def get_flat(net):
    return torch.cat([p.detach().reshape(-1) for p in net.parameters()]).numpy().copy()


def set_flat(net, vec):
    i = 0
    with torch.no_grad():
        for p in net.parameters():
            n = p.numel()
            p.copy_(torch.from_numpy(vec[i:i + n]).reshape(p.shape))
            i += n


def as_dict(net, vec_t):
    out, i = {}, 0
    for n, p in net.named_parameters():
        k = p.numel()
        out[n] = vec_t[i:i + k].reshape(p.shape)
        i += k
    return out


def run_host(seed, quick=False):
    t0 = time.time()
    torch.manual_seed(SEED0 + seed)
    rng = np.random.default_rng(SEED0 + 1_000_000 + seed)
    net = Net()
    P = sum(p.numel() for p in net.parameters())
    w_init = get_flat(net)

    # The input space is finite (2 * 23 * 23 native inputs), so the host is
    # trained on all of it. The fit probes, the attacker's inputs and the
    # held-out inputs are three disjoint parts of it: "held-out" means unseen by
    # the predictor, which is what the question is about.
    Xn, Yn = all_inputs([0, 1])
    perm = rng.permutation(len(Xn))
    fit, att, held = perm[:96], perm[96:192], perm[192:]
    Xv, Yv = all_inputs([2])

    def train(model, X, Y, steps, gen):
        opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
        for _ in range(steps):
            idx = torch.from_numpy(gen.integers(0, len(X), size=128))
            loss = F.cross_entropy(model(X[idx]), Y[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()

    train(net, Xn, Yn, 3000, rng)
    w0 = get_flat(net)

    def logits(vec, X):
        set_flat(net, vec)
        with torch.no_grad():
            return net(X).numpy()

    def acc(vec, X, Y):
        return float((logits(vec, X).argmax(axis=1) == Y.numpy()).mean())

    base_acc = acc(w0, Xn[held], Yn[held])
    if base_acc < 0.99:
        fail(f"seed {seed}: host reaches only {base_acc:.3f} on the native inputs")

    X_fit, X_att, X_ho = Xn[fit], Xn[att], Xn[held]
    Lfit0, Lho0 = logits(w0, X_fit), logits(w0, X_ho)
    nd = X_fit.shape[0] * M

    # Jacobian of the centred logits on the fit probes.
    w0_t = torch.from_numpy(w0)

    def f_single(vec_t, tok):
        return functional_call(net, as_dict(net, vec_t), (tok[None, :],))[0]

    def jac(X):
        parts = []
        for i in range(0, X.shape[0], 32):
            parts.append(vmap(jacrev(f_single), in_dims=(None, 0))(w0_t, X[i:i + 32]).reshape(-1, P))
        return torch.cat(parts).numpy()

    set_flat(net, w0)
    J = jac(X_fit)
    rng_d = np.random.default_rng(SEED0 + 2_000_000 + seed)
    for _ in range(3):
        u = unit(rng_d.normal(size=P))
        eps = 1e-5
        fd = (logits(w0 + eps * u, X_fit) - logits(w0 - eps * u, X_fit)).ravel() / (2 * eps)
        an = J @ u
        if float(np.max(np.abs(fd - an))) > 1e-5 * (1.0 + float(np.max(np.abs(an)))):
            fail("Jacobian disagrees with central differences")

    evals, U = np.linalg.eigh(J @ J.T / nd)
    evals = np.clip(evals[::-1], 0.0, None)
    U = U[:, ::-1]
    lam_max, trace = float(evals[0]), float(evals.sum())
    top = unit(J.T @ U[:, 0])
    Q = row_basis(J)

    def change(vec, X, L0):
        return float(np.sqrt(np.mean((logits(vec, X) - L0) ** 2)))

    def kl(vec, X, L0):
        la = torch.log_softmax(torch.from_numpy(L0), dim=-1)
        lb = torch.log_softmax(torch.from_numpy(logits(vec, X)), dim=-1)
        return float((la.exp() * (la - lb)).sum(dim=-1).mean())

    def grad_of(vec, X, fn):
        set_flat(net, vec)
        net.zero_grad()
        fn(net(X)).backward()
        return torch.cat([p.grad.reshape(-1) for p in net.parameters()]).numpy().copy()

    rows = []

    def record(cls, d, natural=False, r_nom=None):
        r = float(np.linalg.norm(d))
        if r_nom is not None and abs(r - r_nom) > 1e-9 * max(1.0, r_nom):
            fail(f"move of class {cls} has norm {r}, expected {r_nom}")
        w = w0 + d
        row = {
            "class": cls, "natural": bool(natural), "r": r if r_nom is None else float(r_nom),
            "fisher": float(np.linalg.norm(J @ d) / math.sqrt(nd)),
            "probe": change(w, X_fit, Lfit0),
            "held": change(w, X_ho, Lho0),
            "held_kl": kl(w, X_ho, Lho0),
            "drop": base_acc - acc(w, X_ho, Yn[held]),
        }
        rows.append(row)
        return row

    dirs = {}
    for k in range(5):
        dirs[f"rand{k}"] = unit(rng_d.normal(size=P))
    dirs["top"] = top
    for k in range(3):
        v = rng_d.normal(size=P)
        dirs[f"null{k}"] = unit(v - Q @ (Q.T @ v))
    Yt = Yn[att]
    g_nat = grad_of(w0, Xn[att], lambda z: F.cross_entropy(z, Yt))
    dirs["grad_native"] = unit(-g_nat)
    g_nov = grad_of(w0, Xv, lambda z: F.cross_entropy(z, Yv))
    dirs["grad_novel"] = unit(-g_nov)
    dirs["adam_novel"] = unit(-np.sign(g_nov))
    # Readout flip: negate the last linear layer, which negates every logit.
    flip, i = np.zeros(P), 0
    for n, p in net.named_parameters():
        k = p.numel()
        if n.startswith("out."):
            flip[i:i + k] = -w0[i:i + k]
        i += k
    dirs["flip"] = unit(flip)

    radii = RADII if not quick else [1e-3, 1e-2, 0.1]
    for name, u in dirs.items():
        cls = name.rstrip("0123456789") if name[:4] in ("rand", "null") else name
        for r in radii:
            record(cls, r * u, r_nom=r)

    # Natural moves.
    set_flat(net, w0)
    pnet = Net()
    pnet.load_state_dict(net.state_dict())
    with torch.no_grad():
        for blk in pnet.blocks:
            pm = torch.from_numpy(rng_d.permutation(HID))
            blk.fc1.weight.copy_(blk.fc1.weight[pm])
            blk.fc1.bias.copy_(blk.fc1.bias[pm])
            blk.fc2.weight.copy_(blk.fc2.weight[:, pm])
    record("perm", get_flat(pnet) - w0, natural=True)
    record("flip", 2.0 * flip, natural=True)
    record("to_init", w_init - w0, natural=True)
    record("one_step", -LR * g_nov / (np.abs(g_nov) + 1e-8), natural=True)
    fnet = Net()
    fnet.load_state_dict(net.state_dict())
    Xj = torch.cat([Xn, Xv])
    Yj = torch.cat([Yn, Yv])
    train(fnet, Xj, Yj, 2000, np.random.default_rng(SEED0 + 3_000_000 + seed))
    wf = get_flat(fnet)
    ft = record("finetune_joint", wf - w0, natural=True)
    ft["novel_acc_after"] = acc(wf, Xv, Yv)
    ft["joint_pass"] = bool(ft["drop"] <= DROP_MAX and ft["novel_acc_after"] >= 0.70)

    # Adversaries inside the ball.
    Latt0_t = torch.from_numpy(logits(w0, X_att))
    Lfit0_t = torch.from_numpy(Lfit0)

    def pga(r, start, steps, proj=None, mu=0.0):
        d = r * unit(start)
        best_d, best_v = d.copy(), -1.0
        for k in range(steps):
            set_flat(net, w0 + d)
            net.zero_grad()
            val = ((net(X_att) - Latt0_t) ** 2).mean()
            if mu > 0.0:
                val = val - mu * ((net(X_fit) - Lfit0_t) ** 2).mean()
            val.backward()
            g = torch.cat([p.grad.reshape(-1) for p in net.parameters()]).numpy().copy()
            if float(val.detach()) > best_v:
                best_v, best_d = float(val.detach()), d.copy()
            if proj is not None:
                g = g - proj @ (proj.T @ g)
            gn = float(np.linalg.norm(g))
            if gn < 1e-300:
                break
            eta = 0.25 * r * (0.5 * (1.0 + math.cos(math.pi * k / steps)) + 0.05)
            d = d + eta * g / gn
            if proj is not None:
                d = d - proj @ (proj.T @ d)
            d = r * unit(d)
        set_flat(net, w0 + d)
        with torch.no_grad():
            val = float(((net(X_att) - Latt0_t) ** 2).mean())
            if mu > 0.0:
                val -= mu * float(((net(X_fit) - Lfit0_t) ** 2).mean())
        return d if val > best_v else best_d

    set_flat(net, w0)
    J_att = jac(X_att)
    ev_a, U_a = np.linalg.eigh(J_att @ J_att.T / (X_att.shape[0] * M))
    top_att = unit(J_att.T @ U_a[:, -1])
    null_start = unit(top_att - Q @ (Q.T @ top_att))
    for r in radii:
        record("adv", pga(r, top_att, 30 if quick else 80), r_nom=r)
        record("adv_blind", pga(r, null_start, 30 if quick else 80, proj=Q, mu=100.0), r_nom=r)
    set_flat(net, w0)

    def r_break(cls):
        hit = [x["r"] for x in rows if x["class"] == cls and not x["natural"] and x["drop"] > DROP_MAX]
        return min(hit) if hit else None

    summary = {
        "seed": seed,
        "drop_metric": "accuracy on the held-out native inputs, bar 0.025",
        "n_weights": P,
        "weight_norm": float(np.linalg.norm(w0)),
        "base_held_acc": base_acc,
        "output_rms_held": float(np.sqrt(np.mean(Lho0 ** 2))),
        "lam_max": lam_max,
        "sqrt_lam_max": math.sqrt(lam_max),
        "sqrt_mean_lam": math.sqrt(trace / P),
        "anisotropy": math.sqrt(lam_max * P / trace),
        "rank_fit": int(Q.shape[1]),
        "effective_rank": float(trace / lam_max),
        "r_break": {c: r_break(c) for c in ["adv", "top", "grad_native", "grad_novel", "adam_novel", "rand", "flip", "null", "adv_blind"]},
        "seconds": time.time() - t0,
    }
    return {"summary": summary, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    hosts = []
    for s in a.seeds:
        h = run_host(s, quick=a.quick)
        hosts.append(h)
        sm = h["summary"]
        print(f"seed {s}: weights={sm['n_weights']} |w|={sm['weight_norm']:.2f} acc={sm['base_held_acc']:.3f} "
              f"sqrt(lam_max)={sm['sqrt_lam_max']:.3f} anisotropy={sm['anisotropy']:.1f} "
              f"r_break(adv)={sm['r_break']['adv']} [{sm['seconds']:.0f}s]", flush=True)
    res = {
        "program_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "numpy": np.__version__, "torch": torch.__version__, "python": sys.version.split()[0],
        "seeds": a.seeds, "quick": bool(a.quick), "hosts": hosts,
    }
    if not a.quick:
        res["analysis"] = analyse(hosts, r_loc=R_LOC, r_blind=R_BLIND, shipped_radius=None)
        print(json.dumps(res["analysis"]["tests"], indent=1))
    Path(a.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
