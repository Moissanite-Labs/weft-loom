"""Independent re-run of S5 (own design, own code, fresh seeds).

Task: order-2 Markov language, V=40, transition rows ~ Dirichlet(0.2) (numpy seeds 31337 / 31338).
Net: two token embeddings summed (d=32), two residual blocks with RMSNorm, MLP gated
D(SiLU(G n) * (U n)) or plain D GELU(U n + b), h=128, RMSNorm + unembedding.
K networks are trained at once as batched tensors (independent params, shared data batches).
AdamW lr 3e-3 betas (0.9, 0.99) wd 0.01, batch 256, 1500 steps.
Probe: 4096 (a, b) pairs from a held-out generator; trace = input of D, pooled over both blocks.

Statistic: m(i) = argmax_j |corr(a_i, b_j)|, c_i = sign, N+ = #{c_i > 0}; tau = 0.
p-values: binomial and exact cluster law (my own integer convolution), one-sided upper and two-sided.

Usage: python -I sampled_refute.py <master_seed> <out.json>
"""
import json
import math
import sys
import time

import numpy as np
import torch
import torch.nn.functional as Fn

torch.set_num_threads(6)
V, DM, H, BATCH, STEPS = 40, 32, 128, 256, 1500


def make_task(seed):
    r = np.random.default_rng(seed)
    P = r.dirichlet(np.full(V, 0.2), size=(V, V))
    return torch.tensor(P, dtype=torch.float32)


def sample(P, n, gen):
    a = torch.randint(0, V, (n,), generator=gen)
    b = torch.randint(0, V, (n,), generator=gen)
    y = torch.multinomial(P[a, b], 1, generator=gen).squeeze(1)
    return a, b, y


def init_params(K, kind, gen, bias_mean=0.0, bias_sd=0.0):
    s = 0.02 if False else None
    p = {}
    p["E1"] = torch.randn(K, V, DM, generator=gen) * 0.5
    p["E2"] = torch.randn(K, V, DM, generator=gen) * 0.5
    for l in range(2):
        p[f"U{l}"] = torch.randn(K, DM, H, generator=gen) / math.sqrt(DM)
        if kind == "gated":
            p[f"G{l}"] = torch.randn(K, DM, H, generator=gen) / math.sqrt(DM)
        else:
            p[f"b{l}"] = bias_mean + bias_sd * torch.randn(K, 1, H, generator=gen)
        p[f"D{l}"] = torch.randn(K, H, DM, generator=gen) / math.sqrt(H) * 0.5
        p[f"g{l}"] = torch.ones(K, 1, DM)
    p["gf"] = torch.ones(K, 1, DM)
    p["W"] = torch.randn(K, DM, V, generator=gen) / math.sqrt(DM)
    return p


def rms(x, g):
    return x * torch.rsqrt((x * x).mean(-1, keepdim=True) + 1e-6) * g


def forward(p, kind, a, b, want_traces=False):
    K = p["E1"].shape[0]
    x = p["E1"][:, a, :] + p["E2"][:, b, :]          # K, n, d
    traces = []
    for l in range(2):
        n = rms(x, p[f"g{l}"])
        u = torch.bmm(n, p[f"U{l}"])
        if kind == "gated":
            hdn = Fn.silu(torch.bmm(n, p[f"G{l}"])) * u
        else:
            hdn = Fn.gelu(u + p[f"b{l}"])
        if want_traces:
            traces.append(hdn.detach())
        x = x + torch.bmm(hdn, p[f"D{l}"])
    logits = torch.bmm(rms(x, p["gf"]), p["W"])
    return logits, traces


def train(p, kind, P, steps, stream_seed):
    for v in p.values():
        v.requires_grad_(True)
    opt = torch.optim.AdamW(list(p.values()), lr=3e-3, betas=(0.9, 0.99), weight_decay=0.01)
    gen = torch.Generator().manual_seed(stream_seed)
    K = p["E1"].shape[0]
    for t in range(steps):
        a, b, y = sample(P, BATCH, gen)
        logits, _ = forward(p, kind, a, b)
        loss = Fn.cross_entropy(logits.reshape(-1, V), y.repeat(K), reduction="sum") / BATCH
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    for v in p.values():
        v.requires_grad_(False)
    return float(loss) / K


def traces_of(p, kind, probe):
    a, b = probe
    with torch.no_grad():
        _, tr = forward(p, kind, a, b, want_traces=True)
    return torch.cat(tr, dim=2).double()              # K, n, 2H


def zscore(t):
    t = t - t.mean(0, keepdim=True)
    sd = t.norm(dim=0, keepdim=True)
    return t / sd, sd.squeeze(0) > 1e-9


# ---------------------------------------------------------------- exact p-values (own)
def cluster_counts(abs_s):
    """integer weights of S = sum e_j |s_j|; returns dict S -> count, total 2^J"""
    dist = {0: 1}
    for a in abs_s:
        if a == 0:
            dist = {k: 2 * w for k, w in dist.items()}
            continue
        nd = {}
        for k, w in dist.items():
            nd[k + a] = nd.get(k + a, 0) + w
            nd[k - a] = nd.get(k - a, 0) + w
        dist = nd
    return dist


def pvals(m, nplus, abs_s):
    # binomial
    tot = 2 ** m
    up = sum(math.comb(m, k) for k in range(nplus, m + 1))
    lo = sum(math.comb(m, k) for k in range(0, nplus + 1))
    pb1 = up / tot
    pb2 = min(1.0, 2 * min(up, lo) / tot)
    dist = cluster_counts(abs_s)
    T = sum(dist.values())
    obsS = 2 * nplus - m
    upc = sum(w for k, w in dist.items() if k >= obsS)
    loc = sum(w for k, w in dist.items() if k <= obsS)
    pc1 = upc / T
    pc2 = min(1.0, 2 * min(upc, loc) / T)
    return pb1, pb2, pc1, pc2


def pair_stats(TA, TB, hA_block=H):
    """TA: n x mA z-scored, TB: n x mB z-scored (dead units removed beforehand)."""
    C = TA.T @ TB                                   # mA x mB correlations
    j = C.abs().argmax(dim=1)
    c = torch.sign(C[torch.arange(C.shape[0]), j])
    m = int((c != 0).sum())
    nplus = int((c > 0).sum())
    s = torch.zeros(C.shape[1], dtype=torch.long).index_add_(0, j, c.long())
    abs_s = [int(x) for x in s.abs() if x != 0]
    kappa = sum(x * x for x in abs_s) / m
    pb1, pb2, pc1, pc2 = pvals(m, nplus, abs_s)
    F = int((j == torch.arange(C.shape[0])).sum())   # same position (indices aligned when no dead units)
    inv = float(C.abs().max(dim=1).values.mean())
    return dict(m=m, share=nplus / m, kappa=kappa, pb1=pb1, pb2=pb2, pc1=pc1, pc2=pc2, F=F, inv=inv)


def lean(T):
    """T: n x units raw traces. counts of positive mean and positive third central moment."""
    mu = T.mean(0)
    c = T - mu
    sk = (c ** 3).mean(0)
    live = c.norm(dim=0) > 1e-9
    n = int(live.sum())
    kpos = int((mu[live] > 0).sum())
    kskew = int((sk[live] > 0).sum())

    def p2(k):
        lo = sum(math.comb(n, i) for i in range(0, k + 1))
        up = sum(math.comb(n, i) for i in range(k, n + 1))
        return min(1.0, 2 * min(lo, up) / 2 ** n)
    return dict(n=n, pos_mean=kpos, p_mean=p2(kpos), pos_skew=kskew, p_skew=p2(kskew))


def summarize(rows):
    sh = np.array([r["share"] for r in rows])
    m = np.array([r["m"] for r in rows])
    out = dict(pairs=len(rows), mean_share=float(sh.mean()), sd_share=float(sh.std(ddof=1)),
               binom_sd=float(np.mean(0.5 / np.sqrt(m))), min_share=float(sh.min()), max_share=float(sh.max()),
               median_kappa=float(np.median([r["kappa"] for r in rows])),
               mean_F=float(np.mean([r["F"] for r in rows])), mean_inv=float(np.mean([r["inv"] for r in rows])))
    for key in ("pb1", "pb2", "pc1", "pc2"):
        v = np.array([r[key] for r in rows])
        out[key + "_lt05_lt01"] = [int((v < 0.05).sum()), int((v < 0.01).sum())]
    return out


def all_traces(p, kind, probe):
    T = traces_of(p, kind, probe)
    return T


def pairs_between(TA_all, TB_all, idxA, idxB):
    rows = []
    for ia, ib in zip(idxA, idxB):
        za, la = zscore(TA_all[ia])
        zb, lb = zscore(TB_all[ib])
        if not (la.all() and lb.all()):
            za, zb = za[:, la], zb[:, lb]
        rows.append(pair_stats(za, zb))
    return rows


def main():
    seed = int(sys.argv[1])
    outp = sys.argv[2]
    t0 = time.time()
    P0, P1 = make_task(31337), make_task(31338)
    pg = torch.Generator().manual_seed(seed + 999)
    pa, pb, _ = sample(P0, 4096, pg)
    probe = (pa, pb)
    res = {"seed": seed}

    # gated null: 160 nets, independent inits, shared data stream
    g = torch.Generator().manual_seed(seed + 1)
    pg_ = init_params(160, "gated", g)
    res["loss_gated"] = train(pg_, "gated", P0, STEPS, stream_seed=seed + 2)
    TG = all_traces(pg_, "gated", probe)
    # plain GELU: 120 nets
    g = torch.Generator().manual_seed(seed + 3)
    pp = init_params(120, "plain", g)
    res["loss_gelu"] = train(pp, "plain", P0, STEPS, stream_seed=seed + 2)
    TP = all_traces(pp, "plain", probe)
    # sparse GELU: negative, spread biases (a plain one-sided block with sparse traces)
    g = torch.Generator().manual_seed(seed + 4)
    ps = init_params(60, "plain", g, bias_mean=-1.5, bias_sd=1.0)
    res["loss_gelu_sparse"] = train(ps, "plain", P0, STEPS, stream_seed=seed + 2)
    TS = all_traces(ps, "plain", probe)
    res["t_train"] = time.time() - t0

    res["gated_null"] = summarize(pairs_between(TG, TG, range(0, 80), range(80, 160)))
    res["gelu_null"] = summarize(pairs_between(TP, TP, range(0, 40), range(40, 80)))
    res["gelu_sparse_null"] = summarize(pairs_between(TS, TS, range(0, 30), range(30, 60)))
    # mixed: GELU source -> gated target, and gated source -> GELU target
    res["mixed_gelu_src_gated_tgt"] = summarize(pairs_between(TP, TG, range(80, 120), range(0, 40)))
    res["mixed_gated_src_gelu_tgt"] = summarize(pairs_between(TG, TP, range(40, 80), range(80, 120)))

    # lean diagnostics per block
    def lean_arm(T, nnets):
        out = dict(rej_mean_01=0, rej_skew_01=0, frac_pos_mean=[], frac_pos_skew=[], blocks=0)
        for k in range(nnets):
            for l in range(2):
                r = lean(T[k][:, l * H:(l + 1) * H])
                out["blocks"] += 1
                out["rej_mean_01"] += r["p_mean"] < 0.01
                out["rej_skew_01"] += r["p_skew"] < 0.01
                out["frac_pos_mean"].append(r["pos_mean"] / r["n"])
                out["frac_pos_skew"].append(r["pos_skew"] / r["n"])
        for key in ("frac_pos_mean", "frac_pos_skew"):
            v = np.array(out[key])
            out[key] = [float(v.min()), float(np.median(v)), float(v.max())]
        return out
    res["lean_gated"] = lean_arm(TG, 60)
    res["lean_gelu"] = lean_arm(TP, 60)
    res["lean_gelu_sparse"] = lean_arm(TS, 60)
    # shift counterexample: act' = GELU - c with D-bias b' = b + c*D.1 computes the same function;
    # its traces are GELU traces minus c. corr (hence the sign statistic) is shift-invariant,
    # the positive-mean lean count is not. c = median of the unit means of each block.
    TPs = TP.clone()
    for k in range(TPs.shape[0]):
        for l in range(2):
            blk = TPs[k][:, l * H:(l + 1) * H]
            TPs[k][:, l * H:(l + 1) * H] = blk - blk.mean(0).median()
    res["lean_gelu_shifted"] = lean_arm(TPs, 60)
    res["gelu_shifted_null"] = summarize(pairs_between(TPs, TPs, range(0, 40), range(40, 80)))

    # descendants: 30 gated parents continued on task 1 with a fresh optimiser
    desc = {k: v[:30].clone() for k, v in pg_.items()}
    res["loss_desc"] = train(desc, "gated", P1, STEPS, stream_seed=seed + 5)
    TD = all_traces(desc, "gated", probe)
    res["descendant_task1"] = summarize(pairs_between(TG, TD, range(0, 30), range(0, 30)))

    # planted relabelled descendant: random signed permutation per block, no training
    gperm = torch.Generator().manual_seed(seed + 6)
    TPl = TG[:30].clone()
    for k in range(30):
        for l in range(2):
            perm = torch.randperm(H, generator=gperm)
            sg = (torch.randint(0, 2, (H,), generator=gperm) * 2 - 1).double()
            TPl[k][:, l * H:(l + 1) * H] = TPl[k][:, l * H:(l + 1) * H][:, perm] * sg
    res["planted_relabelled"] = summarize(pairs_between(TG, TPl, range(0, 30), range(0, 30)))
    res["t_total"] = time.time() - t0
    json.dump(res, open(outp, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
