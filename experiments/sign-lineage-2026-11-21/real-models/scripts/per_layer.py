"""Per-layer same-position and same-layer counts for one pair direction a->b (tau 0 and 0.3).
Run: python -I per_layer.py <folder> <pair name>"""
import json, os, sys
import numpy as np
ROOT, NAME = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(ROOT, "out", "pairs", NAME + ".npz"))
src, tgt, r = z["ab_src"], z["ab_tgt"], z["ab_r"]
Al, Ai, Bl, Bi = z["A_layer"], z["A_index"], z["B_layer"], z["B_index"]
out = []
for L in range(int(Al.max()) + 1):
    row = {"layer": L}
    for name, tau in (("0", 0.0), ("0.3", 0.3)):
        k = (Al[src] == L) & (r != 0) & (np.abs(r) >= tau)
        row["kept_" + name] = int(k.sum())
        row["same_layer_" + name] = int((k & (Bl[tgt] == L)).sum())
        if Bl.max() == Al.max():
            row["same_position_" + name] = int((k & (Bl[tgt] == L) & (Bi[tgt] == Ai[src])).sum())
        row["positive_" + name] = int((k & (r > 0)).sum())
        row["mean_abs_r_" + name] = round(float(np.abs(r[k]).mean()), 4) if k.any() else None
    out.append(row)
os.makedirs(os.path.join(ROOT, "out", "per_layer"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "out", "per_layer", NAME + ".json"), "w"), indent=1)
for row in out:
    print(row)
