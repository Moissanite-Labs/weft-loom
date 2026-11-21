"""All-layer argmax |corr| matching between two trace sets, both directions (second checker, numpy only).

Independent of real-models/scripts. Route:
  * z = (x - mu) / sd per unit, mu and sd in float64 from out/models/<key>.npz (modelstats.py).
  * float32 screen: C = zA zB^T / T in row blocks (Accelerate BLAS).
  * rows (A -> B): candidates are targets with |c32| >= rowmax32 - DELTA; each candidate recomputed in float64
    from the float16 traces; match = argmax |r64|; ties = within 1e-12 of the row max.
  * columns (B -> A): running top-K per column; if the K-th kept value is within DELTA of the max the column is
    recomputed in full in float64; otherwise the kept candidates within DELTA are recomputed in float64.
  * screen check: the first CHECK_ROWS source rows are recomputed against all targets in float64 and the largest
    |r32 - r64| over all entries is recorded, plus agreement of the argmax.

Optional transforms of B (applied to the float16 traces, exact):
  --shuffle SEED          permute the word axis of B with numpy.random.default_rng(SEED).permutation(T)
  --signperm FILE.npz     B unit k := sign[k] * B unit perm[k] (global order), the laundered relabelling

Usage: python -I matchpair.py A_dir A_key B_dir B_key out_name [--shuffle S] [--signperm F] [--block N]
Writes out/pairs/<out_name>.npz with per-unit match index and r64 for both directions, and a json meta.
"""
import sys, os, glob, json, time
import numpy as np

DELTA = 2e-3
K = 8
TIE = 1e-12
CHECK_ROWS = 256
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_traces(tdir):
    files = sorted(glob.glob(os.path.join(tdir, "L*.npy")))
    parts, widths = [], []
    for f in files:
        a = np.load(f, mmap_mode="r")
        parts.append(np.ascontiguousarray(np.asarray(a).T))  # (h, T) float16
        widths.append(a.shape[1])
    return np.concatenate(parts, axis=0), widths


def std64(raw16, mu, sd, idx):
    x = raw16[idx].astype(np.float64)
    x -= mu[idx][:, None]
    x /= sd[idx][:, None]
    return x


def main():
    args = sys.argv[1:]
    a_dir, a_key, b_dir, b_key, name = args[:5]
    opts = args[5:]
    shuffle = None; signperm = None; block = 1024; b_stats_key = b_key
    i = 0
    while i < len(opts):
        if opts[i] == "--shuffle":
            shuffle = int(opts[i + 1]); i += 2
        elif opts[i] == "--signperm":
            signperm = opts[i + 1]; i += 2
        elif opts[i] == "--block":
            block = int(opts[i + 1]); i += 2
        else:
            raise SystemExit("bad option " + opts[i])
    t0 = time.time()
    A16, wa = load_traces(a_dir)
    B16, wb = load_traces(b_dir)
    T = A16.shape[1]
    sa = np.load(os.path.join(ROOT, "out/models", a_key + ".npz"))
    sb = np.load(os.path.join(ROOT, "out/models", b_stats_key + ".npz"))
    muA, sdA = sa["mu"], sa["sd"]
    muB, sdB = sb["mu"], sb["sd"]
    if shuffle is not None:
        perm_t = np.random.default_rng(shuffle).permutation(T)
        B16 = np.ascontiguousarray(B16[:, perm_t])  # moments unchanged
    if signperm is not None:
        sp = np.load(signperm)
        perm, sign = sp["perm"], sp["sign"]
        B16 = B16[perm]
        B16 *= sign.astype(np.float16)[:, None]  # exact in float16
        muB = muB[perm] * sign
        sdB = sdB[perm]
    nA, nB = A16.shape[0], B16.shape[0]
    keepA = sdA > 0
    keepB = sdB > 0
    if not keepA.all() or not keepB.all():
        raise SystemExit("zero-variance units present; not handled in this checker")
    # float32 standardized target
    ZB = np.empty((nB, T), dtype=np.float32)
    for s in range(0, nB, 8192):
        e = min(nB, s + 8192)
        ZB[s:e] = std64(B16, muB, sdB, np.arange(s, e)).astype(np.float32)
    t_load = time.time() - t0

    row_m = np.full(nA, -1, dtype=np.int64)
    row_r = np.zeros(nA, dtype=np.float64)
    row_ties = 0
    row_full = 0
    col_tv = np.full((K, nB), -1.0, dtype=np.float32)
    col_ti = np.full((K, nB), -1, dtype=np.int64)
    invT = np.float32(1.0 / T)
    check = {}
    for s in range(0, nA, block):
        e = min(nA, s + block)
        idx = np.arange(s, e)
        zA64 = std64(A16, muA, sdA, idx)
        C = (zA64.astype(np.float32) @ ZB.T) * invT
        np.abs(C, out=C)
        if s == 0:
            nchk = min(CHECK_ROWS, e - s)
            maxerr = 0.0; agree = 0
            best64 = np.full(nchk, -1.0); arg64 = np.zeros(nchk, dtype=np.int64)
            for cs in range(0, nB, 8192):
                ce = min(nB, cs + 8192)
                zb = std64(B16, muB, sdB, np.arange(cs, ce))
                R = np.abs(zA64[:nchk] @ zb.T) / T
                maxerr = max(maxerr, float(np.abs(R - C[:nchk, cs:ce].astype(np.float64)).max()))
                am = R.argmax(axis=1)
                v = R[np.arange(nchk), am]
                upd = v > best64
                best64[upd] = v[upd]; arg64[upd] = am[upd] + cs
            check = {"rows": nchk, "max_abs_r32_minus_r64_all_entries": maxerr, "arg64": arg64}
        # rows
        rmax = C.max(axis=1)
        cand = C >= (rmax - DELTA)[:, None]
        counts = cand.sum(axis=1)
        many = np.nonzero(counts > 64)[0]
        ri, cj = np.nonzero(cand)
        sel = counts[ri] <= 64
        ri, cj = ri[sel], cj[sel]
        r64 = np.empty(len(ri))
        for q in range(0, len(ri), 4096):
            qe = min(len(ri), q + 4096)
            zb = std64(B16, muB, sdB, cj[q:qe])
            r64[q:qe] = np.einsum("ij,ij->i", zA64[ri[q:qe]], zb) / T
        # group by row
        order = np.lexsort((-np.abs(r64), ri))
        ri, cj, r64 = ri[order], cj[order], r64[order]
        first = np.ones(len(ri), dtype=bool)
        first[1:] = ri[1:] != ri[:-1]
        starts = np.nonzero(first)[0]
        best_abs = np.abs(r64[starts])
        row_best = np.repeat(best_abs, np.diff(np.append(starts, len(ri))))
        tied = np.abs(r64) >= row_best - TIE
        ntied = np.add.reduceat(tied.astype(np.int64), starts)
        row_ties += int((ntied > 1).sum())
        row_m[s + ri[starts]] = cj[starts]
        row_r[s + ri[starts]] = r64[starts]
        if len(many):
            row_full += len(many)
            zm = zA64[many]
            bv = np.full(len(many), -1.0); bj = np.zeros(len(many), dtype=np.int64); bsv = np.zeros(len(many))
            nt = np.zeros(len(many), dtype=np.int64)
            for cs in range(0, nB, 8192):
                ce = min(nB, cs + 8192)
                zb = std64(B16, muB, sdB, np.arange(cs, ce))
                R = zm @ zb.T / T
                aR = np.abs(R)
                am = aR.argmax(axis=1)
                v = aR[np.arange(len(many)), am]
                upd = v > bv
                bv[upd] = v[upd]; bj[upd] = am[upd] + cs; bsv[upd] = R[np.arange(len(many)), am][upd]
            # tie count in full rows: recount
            for cs in range(0, nB, 8192):
                ce = min(nB, cs + 8192)
                zb = std64(B16, muB, sdB, np.arange(cs, ce))
                aR = np.abs(zm @ zb.T / T)
                nt += (aR >= (bv - TIE)[:, None]).sum(axis=1)
            row_ties += int((nt > 1).sum())
            row_m[s + many] = bj
            row_r[s + many] = bsv
        # columns: merge top-K
        kk = min(K, e - s)
        part = np.argpartition(-C, kk - 1, axis=0)[:kk]
        pv = np.take_along_axis(C, part, axis=0)
        allv = np.concatenate([col_tv, pv], axis=0)
        alli = np.concatenate([col_ti, part + s], axis=0)
        top = np.argpartition(-allv, K - 1, axis=0)[:K]
        col_tv = np.take_along_axis(allv, top, axis=0)
        col_ti = np.take_along_axis(alli, top, axis=0)
        del C, cand
    # columns finalize
    cmax = col_tv.max(axis=0)
    cmin = col_tv.min(axis=0)
    full_cols = np.nonzero(cmin >= cmax - DELTA)[0]
    col_m = np.full(nB, -1, dtype=np.int64)
    col_r = np.zeros(nB)
    col_ties = 0
    mask = (col_tv >= (cmax - DELTA)[None, :])
    mask[:, full_cols] = False
    kk_, jj = np.nonzero(mask)
    ii = col_ti[kk_, jj]
    r64c = np.empty(len(ii))
    for q in range(0, len(ii), 4096):
        qe = min(len(ii), q + 4096)
        za = std64(A16, muA, sdA, ii[q:qe])
        zb = std64(B16, muB, sdB, jj[q:qe])
        r64c[q:qe] = np.einsum("ij,ij->i", za, zb) / T
    order = np.lexsort((-np.abs(r64c), jj))
    jj, ii, r64c = jj[order], ii[order], r64c[order]
    if len(jj):
        first = np.ones(len(jj), dtype=bool); first[1:] = jj[1:] != jj[:-1]
        starts = np.nonzero(first)[0]
        best_abs = np.abs(r64c[starts])
        rb = np.repeat(best_abs, np.diff(np.append(starts, len(jj))))
        ntied = np.add.reduceat((np.abs(r64c) >= rb - TIE).astype(np.int64), starts)
        col_ties += int((ntied > 1).sum())
        col_m[jj[starts]] = ii[starts]
        col_r[jj[starts]] = r64c[starts]
    if len(full_cols):
        zbf = std64(B16, muB, sdB, full_cols)
        bv = np.full(len(full_cols), -1.0); bi = np.zeros(len(full_cols), dtype=np.int64)
        bsv = np.zeros(len(full_cols))
        for cs in range(0, nA, 8192):
            ce = min(nA, cs + 8192)
            za = std64(A16, muA, sdA, np.arange(cs, ce))
            R = zbf @ za.T / T
            aR = np.abs(R)
            am = aR.argmax(axis=1)
            v = aR[np.arange(len(full_cols)), am]
            upd = v > bv
            bv[upd] = v[upd]; bi[upd] = am[upd] + cs; bsv[upd] = R[np.arange(len(full_cols)), am][upd]
        col_m[full_cols] = bi
        col_r[full_cols] = bsv
    if (row_m < 0).any() or (col_m < 0).any():
        raise SystemExit("unmatched unit")
    chk_arg_agree = int((check["arg64"] == row_m[:check["rows"]]).sum())
    meta = {"name": name, "A": a_key, "B": b_key, "A_dir": a_dir, "B_dir": b_dir, "shuffle": shuffle,
            "signperm": signperm, "T": int(T), "A_widths": [int(w) for w in wa], "B_widths": [int(w) for w in wb],
            "delta": DELTA, "K": K, "row_ties": row_ties, "row_full_recompute": row_full,
            "col_ties": col_ties, "col_full_recompute": int(len(full_cols)),
            "screen_check_rows": check["rows"],
            "screen_check_max_abs_r32_minus_r64_all_entries": check["max_abs_r32_minus_r64_all_entries"],
            "screen_check_argmax_agree": chk_arg_agree,
            "seconds_load": round(t_load, 1), "seconds": round(time.time() - t0, 1)}
    os.makedirs(os.path.join(ROOT, "out/pairs"), exist_ok=True)
    np.savez(os.path.join(ROOT, "out/pairs", name + ".npz"), ab_m=row_m, ab_r=row_r, ba_m=col_m, ba_r=col_r,
             A_widths=np.array(wa), B_widths=np.array(wb))
    with open(os.path.join(ROOT, "out/pairs", name + ".json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
