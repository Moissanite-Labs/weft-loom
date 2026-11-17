#!/usr/bin/env python3
"""A distance built on persistence, put to the closure rule (CL-8 of the flow note).

For a weight matrix, make a graph with one vertex per row and one per column
and one link per weight, of size |w|. Take a maximum spanning tree of it and
sort the sizes of its links, largest first. Biases are left out. For two cells
of the same host, subtract the two sorted lists layer by layer. Two distances
follow:

    largest gap = the largest absolute difference, over all layers
    summed gap  = the root of the sum of squares of all differences

The largest gap is at most the largest change of any |w|, so at most the
Frobenius length of the move. Reordering rows or columns changes neither gap.
The program tests those facts at start: the tree against full enumeration of
spanning trees on tiny graphs, the bound on random pairs, and the reordering.

It then rebuilds the passing fine-tune of each MLP host of the calibration
record, as closure_quant.py does, and checks it against the recorded row. It
computes both gaps between each host and its fine-tune.

The breaking move is made by the program pga of the calibration record, which
is deterministic for a seed. The program rebuilds it at its recorded length,
as closure_balls.py does, and checks its length, its change on the held-out
inputs and its drop in the native score against the recorded row. Then it
computes both gaps of the breaking move exactly. If the rebuild did not match
the record, the program would say so and skip the second sector.

Sector 1 is closed on a host if the fine-tune's largest gap is above the
length of the breaking move, which is an upper bound on its largest gap.
Sector 2 is closed on a host if the fine-tune's summed gap is above the
breaking move's summed gap. Lower bounds are rounded down and upper bounds up
in the table. The plan predicted at least 8 hosts for sector 1 and at least
10 for sector 2.

Needs NumPy. Usage, from the root of a checkout:
  python3 notes/prototypes/closure-register/closure_persist.py > notes/prototypes/closure-register/closure_persist.out
It also writes closure_persist.json beside itself, which check_closures.py reads.
"""
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from closure_balls import CAL, load_calib  # noqa: E402

BAR = 0.025                 # the native retention bar of the record
PREDICT_LARGEST = 8         # hosts the plan predicted for sector 1
PREDICT_SUMMED = 10         # hosts the plan predicted for sector 2
DIGITS = 4


def down(x):
    f = 10.0 ** DIGITS
    return math.floor(x * f) / f


def up(x):
    f = 10.0 ** DIGITS
    return math.ceil(x * f) / f


def tree_sizes(W):
    """Sorted sizes (largest first) of the links of a maximum spanning tree of the layer's graph."""
    m, n = W.shape
    parent = list(range(m + n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    order = np.argsort(-np.abs(W), axis=None, kind="stable")
    sizes = []
    for k in order:
        i, j = divmod(int(k), n)
        a, b = find(i), find(m + j)
        if a != b:
            parent[a] = b
            sizes.append(abs(float(W[i, j])))
            if len(sizes) == m + n - 1:
                break
    return np.array(sizes)


def layers(c, vec):
    W1, b1, W2, b2, W3, b3 = c.split(vec)
    return [W1, W2, W3]


def gaps_between(mats_a, mats_b):
    """(largest gap, summed gap) between two cells of the same host, given their weight matrices."""
    big, sq = 0.0, 0.0
    for A, B in zip(mats_a, mats_b):
        d = tree_sizes(A) - tree_sizes(B)
        big = max(big, float(np.max(np.abs(d))))
        sq += float(np.sum(d ** 2))
    return big, math.sqrt(sq)


def is_tree(edges, m, n):
    parent = list(range(m + n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i, j in edges:
        a, b = find(i), find(m + j)
        if a == b:
            return False
        parent[a] = b
    return True


def selftest():
    rng = np.random.default_rng(20261117)
    # 1. The tree against full enumeration of spanning trees.
    for m, n in ((2, 2), (2, 3), (3, 3)):
        cells = list(itertools.product(range(m), range(n)))
        for trial in range(30):
            W = rng.normal(size=(m, n))
            if trial % 5 == 0:
                W = np.round(W)          # ties
            best, best_sizes = -1.0, None
            for combo in itertools.combinations(cells, m + n - 1):
                if is_tree(combo, m, n):
                    sizes = sorted((abs(W[i, j]) for i, j in combo), reverse=True)
                    if sum(sizes) > best + 1e-12:
                        best, best_sizes = sum(sizes), sizes
            if not np.allclose(tree_sizes(W), best_sizes, atol=1e-12):
                raise SystemExit(f"FAIL: tree sizes differ from enumeration on a {m}x{n} matrix")
    # 2. The largest gap is at most the largest entrywise change of |W|.
    for _ in range(300):
        m, n = rng.integers(2, 9, size=2)
        A = rng.normal(size=(m, n))
        B = A + rng.normal(size=(m, n)) * rng.choice([0.01, 0.1, 1.0])
        big = float(np.max(np.abs(tree_sizes(A) - tree_sizes(B))))
        if big > float(np.max(np.abs(np.abs(A) - np.abs(B)))) + 1e-12:
            raise SystemExit("FAIL: the largest gap exceeds the largest entrywise change of |W|")
    # 3. Reordering rows or columns of one matrix changes neither gap.
    for _ in range(50):
        m, n = rng.integers(2, 9, size=2)
        A = rng.normal(size=(m, n))
        B = rng.normal(size=(m, n))
        Bp = B[rng.permutation(m)][:, rng.permutation(n)]
        g1, s1 = gaps_between([A], [B])
        g2, s2 = gaps_between([A], [Bp])
        if abs(g1 - g2) > 1e-12 or abs(s1 - s2) > 1e-12:
            raise SystemExit("FAIL: a gap changed when rows or columns were reordered")
    print("Self-test passed: tree against enumeration (2x2, 2x3, 3x3), largest gap against entrywise change (300 pairs), reordering (50 pairs).")


def main():
    selftest()
    c = load_calib()
    e13 = c.load_e13()
    res = json.loads((CAL / "results.json").read_text())
    recorded = {h["summary"]["seed"]: h for h in res["hosts"]}
    per_host = {ph["seed"]: ph for ph in res["analysis"]["per_host"]}
    saved = {"bar": BAR, "predict_largest": PREDICT_LARGEST, "predict_summed": PREDICT_SUMMED, "hosts": []}
    rows = []
    for seed in sorted(recorded):
        env = e13.FiveSkillEnvironment(world_seed=c.WORLD0 + seed)
        rng_h = np.random.default_rng(c.HOST0 + seed)
        host = e13.init_organism(rng_h)
        e13.train_organism_adam(host, env, [0, 1], rng_h, steps=280)
        w0 = c.flat_org(host)
        rng_ho = np.random.default_rng(c.HELD0 + seed)
        X_ho, _ = env.sample_batch(rng_ho, [0, 1], 1024, shifted=False)
        X_sh, Y_sh = env.sample_batch(rng_ho, [0, 1], 1024, shifted=True)
        Yho0 = c.forward(w0, X_ho)
        base_r2 = c.r2_e13(w0, X_sh, Y_sh)
        M0 = layers(c, w0)

        ft_org = c.to_org(e13, w0)
        e13.train_organism_adam(ft_org, env, [0, 1, 2], np.random.default_rng(c.DIR0 + 11 + seed), steps=120)
        wf = c.flat_org(ft_org)
        r_ft = float(np.linalg.norm(wf - w0))
        row = next(x for x in recorded[seed]["rows"] if x["natural"] and x["class"] == "finetune_joint")
        held = c.rms_change(wf, w0, X_ho, Yho0)
        if abs(r_ft - row["r"]) > 1e-9 * row["r"] or abs(held - row["held"]) > 1e-9 * max(1.0, row["held"]):
            raise SystemExit(f"FAIL: rebuilt fine-tune of host {seed} has length {r_ft} and change {held}. The record has {row['r']} and {row['held']}")
        ft_big, ft_sum = gaps_between(layers(c, wf), M0)

        h = {"seed": seed, "finetune_r": r_ft, "finetune_largest_gap": ft_big, "finetune_summed_gap": ft_sum,
             "finetune_passes": bool(row["drop"] <= BAR and row["novel_r2_after"] >= 0.70)}
        brk = per_host[seed]["H6_r_break_adv"]
        h["break_r"] = brk
        h["break_rebuilt"] = False
        h["break_why_not"] = None
        if brk is None:
            h["break_why_not"] = "the record holds no breaking move for this host"
        else:
            env.sample_batch(np.random.default_rng(c.FIT0 + seed), [0, 1], 128, shifted=False)
            X_att, _ = env.sample_batch(np.random.default_rng(c.ATT0 + seed), [0, 1], 128, shifted=False)
            J_att = c.jacobian(w0, X_att)
            _, U_a = np.linalg.eigh(J_att @ J_att.T / (X_att.shape[0] * c.D_OUT))
            top_att = c.unit(J_att.T @ U_a[:, -1])
            d = c.pga(w0, X_att, brk, top_att, steps=80)
            wb = w0 + d
            rb = float(np.linalg.norm(d))
            hb = c.rms_change(wb, w0, X_ho, Yho0)
            dropb = base_r2 - c.r2_e13(wb, X_sh, Y_sh)
            rec = next(x for x in recorded[seed]["rows"] if x["class"] == "adv" and not x["natural"] and abs(x["r"] - brk) < 1e-12)
            ok = (abs(rb - brk) <= 1e-9 * max(1.0, brk) and abs(hb - rec["held"]) <= 1e-9 * max(1.0, rec["held"])
                  and abs(dropb - rec["drop"]) <= 1e-9 * max(1.0, abs(rec["drop"])))
            if ok:
                bb, bs = gaps_between(layers(c, wb), M0)
                h.update(break_rebuilt=True, break_held=hb, break_drop=dropb, break_largest_gap=bb, break_summed_gap=bs,
                         break_breaks=bool(dropb > BAR))
                if bb > rb * (1 + 1e-12):
                    raise SystemExit(f"FAIL: the largest gap of the breaking move on host {seed} exceeds its length")
            else:
                h["break_why_not"] = f"the rebuilt move gives length {rb}, change {hb}, drop {dropb}. The record has {rec['held']} and {rec['drop']}"
        h["closed_largest"] = bool(h["finetune_passes"] and brk is not None and h["finetune_largest_gap"] > brk)
        h["closed_summed"] = (bool(h["finetune_passes"] and h["break_breaks"] and h["finetune_summed_gap"] > h["break_summed_gap"])
                              if h["break_rebuilt"] else None)
        rows.append(h)
        saved["hosts"].append(h)

    rebuilt = all(h["break_rebuilt"] for h in rows)
    print("\nHost | fine-tune length | fine-tune largest gap (lower) | fine-tune summed gap (lower) | breaking length (upper) | "
          "breaking largest gap (upper) | breaking summed gap (upper) | sector 1 | sector 2")
    for h in rows:
        if h["break_rebuilt"]:
            bl, bs = f"{up(h['break_largest_gap']):.{DIGITS}f}", f"{up(h['break_summed_gap']):.{DIGITS}f}"
        else:
            bl = bs = "not rebuilt"
        c2 = "closed" if h["closed_summed"] else ("not closed" if h["closed_summed"] is False else "skipped")
        print(f"{h['seed']:>4} | {h['finetune_r']:>16.{DIGITS}f} | {down(h['finetune_largest_gap']):>29.{DIGITS}f} | {down(h['finetune_summed_gap']):>28.{DIGITS}f} | "
              f"{up(h['break_r']):>23.{DIGITS}f} | {bl:>28} | {bs:>27} | {'closed' if h['closed_largest'] else 'not closed':<10} | {c2}")
    n1 = sum(h["closed_largest"] for h in rows)
    print(f"\nSector 1 (largest gap): closed on {n1} of {len(rows)} hosts. Plan predicted at least {PREDICT_LARGEST}: {'holds' if n1 >= PREDICT_LARGEST else 'fails'}.")
    if rebuilt:
        n2 = sum(bool(h["closed_summed"]) for h in rows)
        print(f"Sector 2 (summed gap): closed on {n2} of {len(rows)} hosts. Plan predicted at least {PREDICT_SUMMED}: {'holds' if n2 >= PREDICT_SUMMED else 'fails'}.")
        print("The breaking move was rebuilt on every host and matches its recorded length, change and drop.")
    else:
        n2 = None
        why = sorted({h["break_why_not"] for h in rows if not h["break_rebuilt"]})
        print("Sector 2 (summed gap): skipped. The breaking move could not be rebuilt on every host: " + " ".join(why))
    saved["closed_largest"], saved["closed_summed"] = n1, n2
    (HERE / "closure_persist.json").write_text(json.dumps(saved, indent=1) + "\n")


if __name__ == "__main__":
    main()
