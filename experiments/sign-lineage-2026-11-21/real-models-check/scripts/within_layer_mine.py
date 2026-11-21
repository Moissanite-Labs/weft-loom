"""Within-layer matching (post hoc check of the first agent's P4 explanation). numpy only.

Each source unit of layer L is matched to argmax |r| over target units of layer L only. float64 throughout
(3072 x 3072 per layer). Counts same position F and records per layer the n_j multiset for the exact null.
Usage: python -I within_layer_mine.py A_key B_key name
"""
import sys, os, json
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


def main():
    a, b, name = sys.argv[1:4]
    nl = len([f for f in os.listdir(os.path.join(RM, "traces", a)) if f.startswith("L")])
    F = 0; tot = 0; pos = 0; ties = 0
    layers = []
    for L in range(nl):
        za = z(np.load(os.path.join(RM, "traces/%s/L%02d.npy" % (a, L))))
        zb = z(np.load(os.path.join(RM, "traces/%s/L%02d.npy" % (b, L))))
        R = za.T @ zb / za.shape[0]
        aR = np.abs(R)
        m = aR.argmax(1)
        best = aR[np.arange(len(m)), m]
        ties += int(((aR >= (best - 1e-12)[:, None]).sum(1) > 1).sum())
        r = R[np.arange(len(m)), m]
        F += int((m == np.arange(len(m))).sum())
        tot += len(m); pos += int((r > 0).sum())
        nj = np.bincount(m, minlength=zb.shape[1]); nj = nj[nj > 0]
        u, c = np.unique(nj, return_counts=True)
        layers.append({"N": int(zb.shape[1]), "n_hist": {str(int(x)): int(y) for x, y in zip(u, c)}})
    out = {"name": name, "A": a, "B": b, "same_position": F, "units": tot, "positive": pos, "ties": ties,
           "layers": layers}
    json.dump(out, open(os.path.join(ROOT, "out/within_" + name + ".json"), "w"), indent=1)
    print(name, "F", F, "/", tot, "pos", pos, "ties", ties)


if __name__ == "__main__":
    main()
