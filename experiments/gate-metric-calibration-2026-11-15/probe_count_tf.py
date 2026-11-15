#!/usr/bin/env python3
"""Why the probe check missed its mark on three transformer hosts (exploratory).

In the confirmatory run the change measured on 96 probes was within 1.25 of
the change on held-out inputs for every move class except the adversary that
searches on its own inputs, where it was off by up to 1.71 on hosts 4, 5 and 7.

This program rebuilds a host with the seed and code of calib_tf.py, finds the
same kind of adversarial move at the local radius, and then asks how the
ratio (change on the rest) / (change on the probes) spreads when the probe
set is redrawn 200 times at each of several sizes. It also reports how
concentrated the move is: the share of its squared change carried by the
5 percent of inputs it changes most.

Usage: python3 probe_count_tf.py --seeds 4 5 7 0 1 2 --out probe_count_tf.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.func import functional_call, jacrev, vmap

import calib_tf as T
from calib import unit

SIZES = [24, 48, 96, 192, 384]
R = T.R_LOC


def run(seed):
    torch.manual_seed(T.SEED0 + seed)
    rng = np.random.default_rng(T.SEED0 + 1_000_000 + seed)
    net = T.Net()
    P = sum(p.numel() for p in net.parameters())
    Xn, Yn = T.all_inputs([0, 1])
    perm = rng.permutation(len(Xn))
    att = perm[96:192]
    rest = np.concatenate([perm[:96], perm[192:]])      # everything the attacker did not use
    opt = torch.optim.AdamW(net.parameters(), lr=T.LR, weight_decay=0.01)
    for _ in range(3000):
        idx = torch.from_numpy(rng.integers(0, len(Xn), size=128))
        loss = F.cross_entropy(net(Xn[idx]), Yn[idx])
        opt.zero_grad()
        loss.backward()
        opt.step()
    w0 = T.get_flat(net)
    w0_t = torch.from_numpy(w0)

    def logits(vec, X):
        T.set_flat(net, vec)
        with torch.no_grad():
            return net(X).numpy()

    def f_single(vec_t, tok):
        return functional_call(net, T.as_dict(net, vec_t), (tok[None, :],))[0]

    X_att = Xn[att]
    parts = [vmap(jacrev(f_single), in_dims=(None, 0))(w0_t, X_att[i:i + 32]).reshape(-1, P) for i in range(0, 96, 32)]
    J_att = torch.cat(parts).numpy()
    ev, U = np.linalg.eigh(J_att @ J_att.T)
    d = R * unit(J_att.T @ U[:, -1])
    Latt0 = torch.from_numpy(logits(w0, X_att))
    for k in range(80):                                   # the same search as calib_tf.py
        T.set_flat(net, w0 + d)
        net.zero_grad()
        val = ((net(X_att) - Latt0) ** 2).mean()
        val.backward()
        g = torch.cat([p.grad.reshape(-1) for p in net.parameters()]).numpy().copy()
        eta = 0.25 * R * (0.5 * (1.0 + math.cos(math.pi * k / 80)) + 0.05)
        d = R * unit(d + eta * g / np.linalg.norm(g))

    per_input = np.mean((logits(w0 + d, Xn[rest]) - logits(w0, Xn[rest])) ** 2, axis=1)   # squared change per input
    order = np.sort(per_input)[::-1]
    top5 = float(order[: max(1, len(order) // 20)].sum() / order.sum())
    draw = np.random.default_rng(T.SEED0 + 9_000_000 + seed)
    rows = []
    for n in SIZES:
        ratios = []
        for _ in range(200):
            pick = draw.permutation(len(rest))
            probe, other = per_input[pick[:n]], per_input[pick[n:]]
            ratios.append(math.sqrt(other.mean() / probe.mean()))
        q = np.quantile(ratios, [0.025, 0.5, 0.975])
        rows.append({"n_probes": n, "ratio_2p5": float(q[0]), "ratio_median": float(q[1]), "ratio_97p5": float(q[2]),
                     "share_outside_1p25": float(np.mean([(r < 0.8) or (r > 1.25) for r in ratios]))})
    return {"seed": seed, "inputs_available": int(len(rest)), "top5_percent_share_of_squared_change": top5, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    hosts = [run(s) for s in a.seeds]
    Path(a.out).write_text(json.dumps({"radius": R, "sizes": SIZES, "hosts": hosts}, indent=1, sort_keys=True) + "\n")
    print("| Host | Share of squared change on the top 5% of inputs | " + " | ".join(f"n = {n}" for n in SIZES) + " |")
    print("|---|---|" + "---|" * len(SIZES))
    for h in hosts:
        cells = " | ".join(f"{r['ratio_2p5']:.2f} to {r['ratio_97p5']:.2f}" for r in h["rows"])
        print(f"| {h['seed']} | {h['top5_percent_share_of_squared_change']:.2f} | {cells} |")
    print("\nCells: the 2.5th to 97.5th percentile of (change on the rest) / (change on the probes) over 200 probe draws.")


if __name__ == "__main__":
    main()
