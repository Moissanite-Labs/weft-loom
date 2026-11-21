"""Is the first agent's laundered trace (traces/s135L) a signed permutation of the Instruct trace (traces/s135i)?
Per layer: float64 correlation of every s135L unit with every s135i unit of the same layer; best match, its sign,
bijectivity; compared with the flip counts and permutation heads recorded in traces/s135L/meta.json.
numpy only.
"""
import json, os, sys
import numpy as np

# --real-models DIR: the first run's folder (traces/, hf/, data/, out/). Default: ../../real-models next to this
# folder in the published record. The option is removed from sys.argv before the positional arguments are read.
import argparse as _argparse
_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--real-models", default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "real-models"))
_known, _rest = _ap.parse_known_args()
sys.argv = sys.argv[:1] + _rest
RM = _known.real_models
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def z(a):
    x = np.asarray(a, dtype=np.float64)
    x = x - x.mean(0)
    return x / x.std(0)


meta = json.load(open(os.path.join(RM, "traces/s135L/meta.json")))
out = []
for L in range(30):
    zl = z(np.load(os.path.join(RM, "traces/s135L/L%02d.npy" % L)))
    zi = z(np.load(os.path.join(RM, "traces/s135i/L%02d.npy" % L)))
    R = zl.T @ zi / zl.shape[0]
    am = np.abs(R).argmax(1)
    best = R[np.arange(R.shape[0]), am]
    m = meta["launder"][L]
    head = m["perm_head"]
    rec = {"layer": L, "min_abs_best_r": float(np.abs(best).min()), "bijective": bool(len(set(am.tolist())) == len(am)),
           "negated": int((best < 0).sum()), "meta_n_flipped": m["n_flipped"],
           "perm_head_mine": am[:5].tolist(), "perm_head_meta": head,
           "second_best_max": float(np.sort(np.abs(R), axis=1)[:, -2].max())}
    out.append(rec)
    print(rec, flush=True)
json.dump(out, open(os.path.join(ROOT, "out/laund/their_laundered_check.json"), "w"), indent=1)
ok = all(r["bijective"] and r["negated"] == r["meta_n_flipped"] and r["min_abs_best_r"] > 0.999 for r in out)
print("ALL_LAYERS_SIGNED_PERMUTATION", ok)
