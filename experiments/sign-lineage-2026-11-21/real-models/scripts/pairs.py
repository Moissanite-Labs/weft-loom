"""Match every unit of A to its closest unit of B by |corr| (and B to A), PLAN.txt section (d).

Run: python -I pairs.py <folder> <keyA> <keyB> [--shuffle SEED] [--check64 N] [--name NAME]
Float32 screen on MPS keeps the top 8 |r| per row and per column; the candidates within 2e-3 of the screened maximum
are recomputed in float64 from the float16 traces; rows whose 8th screened value is still within the margin are
recomputed in full in float64. Ties (within 1e-12 of the float64 maximum) are broken at random (PCG64 20261121).
Output: out/pairs/<name>.npz with, per direction, the kept source ids, matched target ids and float64 r.
"""
import json
import os
import sys
import time

import numpy as np
import torch

ROOT = sys.argv[1]
KA, KB = sys.argv[2], sys.argv[3]
args = sys.argv[4:]
SHUF = None
CHECK64 = 0
NAME = KA + "__" + KB
i = 0
while i < len(args):
    if args[i] == "--shuffle":
        SHUF = int(args[i + 1]); i += 2
    elif args[i] == "--check64":
        CHECK64 = int(args[i + 1]); i += 2
    elif args[i] == "--name":
        NAME = args[i + 1]; i += 2
    else:
        raise SystemExit("bad arg " + args[i])
MARGIN = 2e-3
TIE = 1e-12
TOPK = 8
DEV = "mps"
RNG = np.random.Generator(np.random.PCG64(20261121))


def load(key, shuffle=None):
    d = os.path.join(ROOT, "traces", key)
    meta = json.load(open(os.path.join(d, "meta.json"))) if os.path.exists(os.path.join(d, "meta.json")) else {}
    files = sorted(f for f in os.listdir(d) if f.startswith("L") and f.endswith(".npy"))
    X = []  # (N, T) float16, units as rows
    layer, index = [], []
    for li, f in enumerate(files):
        a = np.load(os.path.join(d, f))
        if shuffle is not None:
            perm = np.random.Generator(np.random.PCG64(shuffle)).permutation(a.shape[0])
            a = a[perm]
        X.append(np.ascontiguousarray(a.T))
        layer.append(np.full(a.shape[1], li, dtype=np.int32))
        index.append(np.arange(a.shape[1], dtype=np.int32))
    X = np.concatenate(X, 0)
    layer = np.concatenate(layer)
    index = np.concatenate(index)
    T = X.shape[1]
    mu = np.empty(X.shape[0]); sd = np.empty(X.shape[0])
    for s in range(0, X.shape[0], 4096):
        b = X[s:s + 4096].astype(np.float64)
        mu[s:s + 4096] = b.mean(1)
        sd[s:s + 4096] = np.sqrt(((b - b.mean(1, keepdims=True)) ** 2).mean(1))
    live = np.flatnonzero(sd > 0)
    return {"X": X, "mu": mu, "sd": sd, "live": live, "layer": layer, "index": index, "T": T, "meta": meta,
            "layers": len(files), "widths": [int((layer == l).sum()) for l in range(len(files))]}


def z32(D, ids):
    b = D["X"][ids].astype(np.float64)
    b = (b - D["mu"][ids, None]) / D["sd"][ids, None]
    return torch.from_numpy(b.astype(np.float32))


def r64_pairs(A, B, ia, ib):
    """float64 correlation for each pair (ia[k], ib[k])."""
    out = np.empty(len(ia))
    T = A["T"]
    for s in range(0, len(ia), 2048):
        a = A["X"][ia[s:s + 2048]].astype(np.float64) - A["mu"][ia[s:s + 2048], None]
        b = B["X"][ib[s:s + 2048]].astype(np.float64) - B["mu"][ib[s:s + 2048], None]
        out[s:s + 2048] = (a * b).sum(1) / (T * A["sd"][ia[s:s + 2048]] * B["sd"][ib[s:s + 2048]])
    return out


def full_rows64(A, B, rows):
    """Full float64 argmax |r| for the A live rows `rows` (positions in A live) over all B live units.
    Ties within TIE: uniform choice (reservoir). Returns (positions in B live, r64, n_tied_rows)."""
    k = len(rows)
    best = np.full(k, -1.0); bi = np.zeros(k, dtype=np.int64); br = np.zeros(k); cnt = np.zeros(k, dtype=np.int64)
    for s0 in range(0, k, 4096):
        ids = A["live"][rows[s0:s0 + 4096]]
        a = (A["X"][ids].astype(np.float64) - A["mu"][ids, None]) / A["sd"][ids, None]
        for s in range(0, len(B["live"]), 8192):
            bid = B["live"][s:s + 8192]
            b = (B["X"][bid].astype(np.float64) - B["mu"][bid, None]) / B["sd"][bid, None]
            R = a @ b.T / A["T"]
            AR = np.abs(R)
            for q in range(a.shape[0]):
                g = s0 + q
                m = AR[q].max()
                if m > best[g] + TIE:
                    best[g] = m; cnt[g] = 0
                if m >= best[g] - TIE:
                    for j in np.flatnonzero(AR[q] >= best[g] - TIE):
                        cnt[g] += 1
                        if cnt[g] == 1 or RNG.random() < 1.0 / cnt[g]:
                            bi[g] = s + j; br[g] = R[q, j]
                    best[g] = max(best[g], m)
    return bi, br, int((cnt > 1).sum())


def screen(A, B):
    """Top-K |r32| per A row and per B column. Returns (rowv, rowi, colv, coli) with indices into live arrays."""
    na, nb = len(A["live"]), len(B["live"])
    T = A["T"]
    ZB = []
    for s in range(0, nb, 16384):
        ZB.append(z32(B, B["live"][s:s + 16384]).to(DEV))  # (cols, T)
    rowv = torch.full((na, TOPK), -1.0); rowi = torch.zeros((na, TOPK), dtype=torch.long)
    colv = torch.full((nb, TOPK), -1.0, device=DEV); coli = torch.zeros((nb, TOPK), dtype=torch.long, device=DEV)
    for s in range(0, na, 4096):
        za = z32(A, A["live"][s:s + 4096]).to(DEV)
        rv = None; ri = None
        off = 0
        for zb in ZB:
            R = (za @ zb.T).abs_() / T  # (rows, cols)
            v, ix = R.topk(TOPK, dim=1)
            ix = ix + off
            if rv is None:
                rv, ri = v, ix
            else:
                cv = torch.cat([rv, v], 1); ci = torch.cat([ri, ix], 1)
                rv, p = cv.topk(TOPK, dim=1); ri = ci.gather(1, p)
            cvv, cix = R.topk(min(TOPK, R.shape[0]), dim=0)  # (k, cols)
            cvv = cvv.T; cix = cix.T + s
            sl = slice(off, off + R.shape[1])
            mv = torch.cat([colv[sl], cvv], 1); mi = torch.cat([coli[sl], cix], 1)
            nv, p = mv.topk(TOPK, dim=1)
            colv[sl] = nv; coli[sl] = mi.gather(1, p)
            off += R.shape[1]
        rowv[s:s + 4096] = rv.cpu(); rowi[s:s + 4096] = ri.cpu()
    return rowv.numpy(), rowi.numpy(), colv.cpu().numpy(), coli.cpu().numpy()


def resolve(A, B, v32, i32, tag):
    """For each A live row: float64 argmax |r| over candidates. Returns (src ids, tgt ids, r64, stats)."""
    na = len(A["live"])
    best = v32[:, 0]
    cand_ok = v32 >= (best[:, None] - MARGIN)
    full_rows = np.flatnonzero(cand_ok[:, -1])  # 8th still within margin: recompute full row
    ia = np.repeat(np.arange(na), TOPK)
    ib = i32.reshape(-1)
    keep = cand_ok.reshape(-1)
    r = np.full(na * TOPK, np.nan)
    r[keep] = r64_pairs(A, B, A["live"][ia[keep]], B["live"][ib[keep]])
    r = r.reshape(na, TOPK)
    ar = np.where(np.isnan(r), -1.0, np.abs(r))
    tgt = np.empty(na, dtype=np.int64); rr = np.empty(na)
    ties = 0
    maxdiff = 0.0
    for k in range(na):
        m = ar[k].max()
        tied = np.flatnonzero(ar[k] >= m - TIE)
        j = tied[0] if len(tied) == 1 else RNG.choice(tied)
        ties += len(tied) > 1
        tgt[k] = i32[k, j]; rr[k] = r[k, j]
    if len(full_rows):
        fb, fr, fties = full_rows64(A, B, full_rows)
        tgt[full_rows] = fb; rr[full_rows] = fr
        ties += fties
    # screen accuracy on candidates
    with np.errstate(invalid="ignore"):
        d = np.abs(np.where(np.isnan(r), 0, np.abs(r)) - np.where(np.isnan(r), 0, v32))
    maxdiff = float(d.max())
    return A["live"], B["live"][tgt], rr, {"ties": int(ties), "full_rows": int(len(full_rows)),
                                           "max_abs_r32_minus_r64_on_candidates": maxdiff}



def main():
    t0 = time.time()
    A = load(KA)
    B = load(KB, SHUF) if KB != KA or SHUF is not None else A
    rowv, rowi, colv, coli = screen(A, B)
    t1 = time.time()
    sa, ta, ra, sta = resolve(A, B, rowv, rowi, "ab")
    sb, tb, rb, stb = resolve(B, A, colv, coli, "ba")
    out = {"name": NAME, "A": KA, "B": KB, "shuffle": SHUF, "T": A["T"],
           "A_layers": A["layers"], "B_layers": B["layers"], "A_widths": A["widths"], "B_widths": B["widths"],
           "A_dropped_zero_var": int(len(A["X"]) - len(A["live"])),
           "B_dropped_zero_var": int(len(B["X"]) - len(B["live"])),
           "ab": sta, "ba": stb, "screen_seconds": round(t1 - t0, 1)}
    if CHECK64:
        # full float64 rows for the first CHECK64 live A units: compare matches
        rows = np.arange(min(CHECK64, len(A["live"])))
        fb, fr, _ = full_rows64(A, B, rows)
        agree = int((B["live"][fb] == ta[rows]).sum())
        worst = float(np.abs(np.abs(fr) - np.abs(ra[rows])).max())
        out["check64"] = {"rows": int(min(CHECK64, len(A["live"]))), "agree": int(agree),
                          "max_abs_diff_best_abs_r": worst}
    d = os.path.join(ROOT, "out", "pairs")
    os.makedirs(d, exist_ok=True)
    np.savez(os.path.join(d, NAME + ".npz"),
             ab_src=sa, ab_tgt=ta, ab_r=ra, ba_src=sb, ba_tgt=tb, ba_r=rb,
             A_layer=A["layer"], A_index=A["index"], B_layer=B["layer"], B_index=B["index"])
    out["seconds"] = round(time.time() - t0, 1)
    json.dump(out, open(os.path.join(d, NAME + ".json"), "w"), indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
