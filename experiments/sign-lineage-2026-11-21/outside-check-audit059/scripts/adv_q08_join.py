"""Advocate pass: recount the q08 x weight-edit join and test N2, N3 and the column-order point.

Inputs (all read only, untrusted data):
  argv[1] q08 page (your saved copy, sha256 1292ab48..., equal to the copy the other team pinned)
  argv[2] dir with frozen_weights_manifest.json, base_l{15,19}_down_proj_f32.npy, factors_layer{15,19}.npz
Labels and counts are integers; tails are exact (two routes, adv_exact). Kurtosis uses float64
on the exact float32 weights (stated as float). Permutation nulls are sampled with fixed seeds.
No bare assert. Exit 1 on any internal disagreement.
"""
import json
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adv_exact as ex  # noqa: E402
import adv_page as pg  # noqa: E402

BAD = []


def need(cond, msg):
    if not cond:
        BAD.append(msg)
        print("DISAGREE:", msg)


def load_npy(path):
    arr = np.load(path, allow_pickle=False)
    return np.asarray(arr, dtype=np.float32)


def kurt_cols(W):
    """Uncentred per-column kurtosis rows*sum(w^4)/sum(w^2)^2 (the sibling's definition),
    and the centred one, both float64."""
    X = W.astype(np.float64)
    r = X.shape[0]
    s2 = (X * X).sum(axis=0)
    s4 = (X ** 4).sum(axis=0)
    unc = r * s4 / (s2 * s2)
    Xc = X - X.mean(axis=0, keepdims=True)
    c2 = (Xc * Xc).sum(axis=0)
    c4 = (Xc ** 4).sum(axis=0)
    cen = r * c4 / (c2 * c2)
    return unc, cen


def strat_null(stat, blocks, sel, seeds, draws):
    """Null: random column sets with the selection's count in each block. Returns per seed
    (exceed, draws) for mean(stat) >= observed."""
    obs = float(np.mean(stat[sel]))
    by_block = {}
    for c in range(len(stat)):
        by_block.setdefault(blocks[c], []).append(c)
    need_n = {}
    for c in sel:
        need_n[blocks[c]] = need_n.get(blocks[c], 0) + 1
    res = []
    for sd in seeds:
        rng = random.Random(sd)
        exceed = 0
        for _ in range(draws):
            pick = []
            for b, k in need_n.items():
                pick.extend(rng.sample(by_block[b], k))
            if float(np.mean(stat[pick])) >= obs:
                exceed += 1
        res.append((sd, exceed, draws))
    return obs, res


def main(page, wdir):
    data = pg.load_data(page)
    ids = pg.group_ids(data)
    fam = pg.family_of_neuron(data, ids)
    kind = pg.kind_of_neuron(data, ids)
    W = int(data["width"])
    L = int(data["layers"])
    print("page:", data["title"], "width", W, "layers", L)
    fams = data["structures"]["families"]
    adj = [i for i, f in enumerate(fams) if f["title"].startswith("Adjacent brackets")]
    regs = data["structures"]["regions"]
    eqk = [i for i, r in enumerate(regs) if r["name"] == "Equations, numbers and units"]
    need(len(adj) == 1 and len(eqk) == 1, "family/kind lookup not unique")
    adj, eqk = adj[0], eqk[0]
    print("family", adj, repr(fams[adj]["title"]), "| kind", eqk, repr(regs[eqk]["name"]))

    with open(os.path.join(wdir, "frozen_weights_manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    top_lo_total = 0
    for layer in (15, 19):
        sel = sorted(int(x) for x in man[str(layer)]["selected_neurons"])
        need(len(set(sel)) == 64, "selection size L%d" % layer)
        base = layer * W
        lab = fam[base:base + W]
        kd = kind[base:base + W]
        print("\n=== L%d ===" % layer)
        n_lo = sum(1 for c in sel if c < 512)
        print("selected in col<512: %d/64 (exact tail vs 512/3584: %s)" % (
            n_lo, ex.sci(ex.tail_checked(W, 512, 64, n_lo))))
        rows = [
            ("Adjacent brackets, all", [c for c in range(W)], sel, lambda c: lab[c] == adj),
            ("Adjacent brackets, col<512", list(range(512)), [c for c in sel if c < 512], lambda c: lab[c] == adj),
            ("Adjacent brackets, col>=512", list(range(512, W)), [c for c in sel if c >= 512], lambda c: lab[c] == adj),
            ("Kind Equations, all", [c for c in range(W)], sel, lambda c: kd[c] == eqk),
            ("Kind Equations, col<512", list(range(512)), [c for c in sel if c < 512], lambda c: kd[c] == eqk),
            ("Kind Equations, col>=512", list(range(512, W)), [c for c in sel if c >= 512], lambda c: kd[c] == eqk),
        ]
        strata = {}
        for name, pop, s, hit in rows:
            N = len(pop)
            K = sum(1 for c in pop if hit(c))
            n = len(s)
            k = sum(1 for c in s if hit(c))
            p = ex.tail_checked(N, K, n, k)
            print("%-28s obs %2d/%2d  bg %3d/%4d  expected %.3f  exact P(X>=obs) = %s" % (
                name, k, n, K, N, n * K / N, ex.sci(p)))
            strata[name] = (N, K, n, k)
        for fam_name in ("Adjacent brackets", "Kind Equations"):
            a = strata[fam_name + ", col<512"]
            b = strata[fam_name + ", col>=512"]
            ps = ex.stratified_upper_tail([a[:3], b[:3]], a[3] + b[3])
            print("%s stratified (2 blocks) exact P(X1+X2>=%d) = %s" % (fam_name, a[3] + b[3], ex.sci(ps)))
        dark_bg = sum(1 for c in range(W) if lab[c] < 0)
        dark_sel = sum(1 for c in sel if lab[c] < 0)
        print("no-family: %d/64 vs %d/%d; P(X<=obs)=%s, P(X>=obs)=%s" % (
            dark_sel, dark_bg, W, ex.sci(ex.lower_tail(W, dark_bg, 64, dark_sel)),
            ex.sci(ex.tail_checked(W, dark_bg, 64, dark_sel))))

        Wt = load_npy(os.path.join(wdir, "base_l%d_down_proj_f32.npy" % layer))
        need(Wt.shape == (1024, W), "weight shape L%d" % layer)
        linf = np.abs(Wt).max(axis=0)  # exact on float32 values
        order = sorted(range(W), key=lambda c: (-float(linf[c]), c))
        top20 = order[:20]
        tie = float(linf[order[19]]) == float(linf[order[20]])
        k_lo = sum(1 for c in top20 if c < 512)
        top_lo_total += k_lo
        print("top-20 L_inf columns in col<512: %d/20 (tie at rank 20/21: %s)" % (k_lo, tie))
        for kk in (10, 40, 100):
            tk = order[:kk]
            print("  robustness: top-%d L_inf in col<512: %d/%d (exact tail %s)" % (
                kk, sum(1 for c in tk if c < 512), kk,
                ex.sci(ex.tail_checked(W, 512, kk, sum(1 for c in tk if c < 512)))))
        rowmax = int(np.argmax(np.abs(Wt).max(axis=1)))
        print("row with the largest |entry|:", rowmax)

        unc, cen = kurt_cols(Wt)
        selm = np.zeros(W, dtype=bool)
        selm[sel] = True
        lo = np.arange(W) < 512
        print("uncentred kurtosis mean: selected %.3f vs non-selected %.3f (sibling: 10.44/4.03, 12.18/3.45)" % (
            unc[selm].mean(), unc[~selm].mean()))
        for nm, blk in (("col<512", lo), ("col>=512", ~lo)):
            print("  within %-8s: selected %.3f (n=%d) vs non-selected %.3f (n=%d); centred %.3f vs %.3f" % (
                nm, unc[selm & blk].mean(), int((selm & blk).sum()), unc[~selm & blk].mean(),
                int((~selm & blk).sum()), cen[selm & blk].mean(), cen[~selm & blk].mean()))
        print("  block means, all columns: col<512 %.3f, col>=512 %.3f" % (unc[lo].mean(), unc[~lo].mean()))
        # Column-block matched null for the mean kurtosis of the selection.
        blocks = [0 if c < 512 else 1 for c in range(W)]
        obs, res = strat_null(unc, blocks, sel, seeds=(11, 2027, 90001), draws=4000)
        print("  block-matched null (mean uncentred kurtosis >= %.3f): %s" % (
            obs, ", ".join("seed %d: %d/%d" % r for r in res)))
        # Must-fail control: a random 64-set with the same block counts, run through the same null.
        rng = random.Random(555 + layer)
        fake = rng.sample(range(512), n_lo) + rng.sample(range(512, W), 64 - n_lo)
        fobs, fres = strat_null(unc, blocks, fake, seeds=(12,), draws=4000)
        print("  control (random block-matched 64-set as 'selected'): mean %.3f, exceed %d/%d" % (
            fobs, fres[0][1], fres[0][2]))
        # Second confounder: the selection score is c_j * dact_j with c = u @ W0. Match on |c| decile too.
        u = np.load(os.path.join(wdir, "factors_layer%d.npz" % layer), allow_pickle=False)["u"].astype(np.float64)
        u = u / np.linalg.norm(u)
        cvec = u @ Wt.astype(np.float64)
        dec = np.argsort(np.argsort(np.abs(cvec)))  # rank 0..W-1
        dec = (dec * 10) // W
        blocks2 = [blocks[c] * 10 + int(dec[c]) for c in range(W)]
        obs2, res2 = strat_null(unc, blocks2, sel, seeds=(13, 4049), draws=4000)
        print("  block x |c|-decile matched null (>= %.3f): %s" % (obs2, ", ".join("seed %d: %d/%d" % r for r in res2)))
        top_u = sorted(range(len(u)), key=lambda i: (-abs(u[i]), i))[:5]
        print("  |u| top-5 residual dims:", sorted(top_u), "| selected |c| deciles:",
              np.bincount(dec[sel], minlength=10).tolist())
    p40 = ex.tail_checked(2 * W, 1024, 40, top_lo_total)
    print("\npooled top-20 L_inf in col<512: %d/40 vs 1024/7168, exact P(X>=%d) = %s" % (
        top_lo_total, top_lo_total, ex.sci(p40)))
    print("21/21 sign test two-sided:", ex.binom_two_sided_half(21, 21))
    if BAD:
        print("FAILED:", BAD)
        return 1
    print("DONE: both exact routes agree on every tail")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
