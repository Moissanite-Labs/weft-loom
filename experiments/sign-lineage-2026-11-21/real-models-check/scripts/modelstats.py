"""Per-model trace moments (second checker, numpy only, shares no code with real-models/scripts).

For each unit: float64 mean, population sd, sign of the third central moment, sign of the mean,
count of words with a positive value. Writes out/models/<key>.npz (mu, sd per unit in global order)
and out/models/<key>.json (counts). Exact p-values are computed later by exact.py.

Usage: python -I modelstats.py <trace_dir> <key> <out_dir>
"""
import sys, os, glob, json
import numpy as np


def main():
    tdir, key, odir = sys.argv[1], sys.argv[2], sys.argv[3]
    files = sorted(glob.glob(os.path.join(tdir, "L*.npy")))
    if not files:
        raise SystemExit("no layer files in " + tdir)
    mus, sds, widths = [], [], []
    n_skew_pos = n_skew_neg = n_skew_zero = 0
    n_mean_pos = n_mean_neg = 0
    n_gt90 = 0
    zero_var = 0
    per_layer = []
    max_abs = 0.0
    any_nonfinite = False
    T = None
    for f in files:
        a = np.load(f, mmap_mode="r")
        if a.dtype != np.float16:
            raise SystemExit("unexpected dtype %s in %s" % (a.dtype, f))
        if T is None:
            T = a.shape[0]
        elif a.shape[0] != T:
            raise SystemExit("T mismatch")
        x = np.asarray(a, dtype=np.float64)
        if not np.all(np.isfinite(x)):
            any_nonfinite = True
        max_abs = max(max_abs, float(np.abs(x).max()))
        mu = x.mean(axis=0)
        d = x - mu
        var = (d * d).mean(axis=0)
        m3 = (d * d * d).mean(axis=0)
        sd = np.sqrt(var)
        zv = int((var == 0).sum())
        zero_var += zv
        sp = int((m3 > 0).sum()); sn = int((m3 < 0).sum()); sz = int((m3 == 0).sum())
        n_skew_pos += sp; n_skew_neg += sn; n_skew_zero += sz
        n_mean_pos += int((mu > 0).sum()); n_mean_neg += int((mu < 0).sum())
        pos_words = (x > 0).sum(axis=0)
        g90 = int((pos_words * 10 > 9 * T).sum())
        n_gt90 += g90
        per_layer.append({"layer": len(widths), "h": int(x.shape[1]), "skew_pos": sp, "skew_nonzero": sp + sn,
                          "zero_var": zv})
        mus.append(mu); sds.append(sd); widths.append(int(x.shape[1]))
        del x, d
    mu = np.concatenate(mus); sd = np.concatenate(sds)
    os.makedirs(odir, exist_ok=True)
    np.savez(os.path.join(odir, key + ".npz"), mu=mu, sd=sd, widths=np.array(widths))
    out = {"key": key, "trace_dir": tdir, "T": T, "layers": len(widths), "widths": widths,
           "units": int(sum(widths)), "zero_var": zero_var, "skew_pos": n_skew_pos, "skew_neg": n_skew_neg,
           "skew_zero": n_skew_zero, "mean_pos": n_mean_pos, "mean_neg": n_mean_neg,
           "pos_on_gt90pct_words": n_gt90, "max_abs_value": max_abs, "nonfinite": any_nonfinite,
           "per_layer": per_layer}
    with open(os.path.join(odir, key + ".json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(key, "units", out["units"], "skew+", n_skew_pos, "/", n_skew_pos + n_skew_neg, "mean+", n_mean_pos,
          "gt90", n_gt90, "zerovar", zero_var, "maxabs", max_abs)


if __name__ == "__main__":
    main()
