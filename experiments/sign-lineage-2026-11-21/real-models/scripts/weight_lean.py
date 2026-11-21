"""Exploratory, post hoc (not in PLAN.txt): a weight-space odd statistic for gated blocks.
For each hidden unit i, the sign of <gate_i, up_i> (rows of gate_proj and up_proj). Flipping unit i flips up_i only,
so under the per-unit sign null this sign is a fair coin: the count of positive signs is Binomial(h, 1/2) exactly
(given the orbit). Also the sign of the up_proj row sum and of the down_proj column sum.

Run: python -I weight_lean.py <folder> <model dir name> [...]

Fix made for publication: the first version keyed MLP tensors by layer number only, so in Qwen3.5 the
multi-token-prediction head (`mtp.layers.0.mlp`) overwrote decoder layer 0. Tensors are now keyed by their full
module prefix, and only decoder layers are counted. The `mtp.` head and any vision tower are left out and listed
under "skipped_prefixes". The old counts for Qwen3.5-0.8B and -2B were 42954/86016 and 73735/147456. The fixed
counts are 42974/86016 and 73680/147456. Falcon-H1 and SmolLM2 counts are unchanged by the fix.
"""
import json
import os
import re
import sys

import torch
from safetensors.torch import load_file

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exactlaw as X  # noqa: E402
from stats import flog10  # noqa: E402

ROOT = sys.argv[1]


def main():
    out = {}
    for name in sys.argv[2:]:
        d = os.path.join(ROOT, "hf", "models", name)
        W = {}
        for f in sorted(os.listdir(d)):
            if f.endswith(".safetensors"):
                W.update(load_file(os.path.join(d, f)))
        layers = {}
        skipped = set()
        for k in W:
            m = re.search(r"^(.*layers\.(\d+))\.(mlp|feed_forward)\.(gate_proj|up_proj|down_proj)\.weight$", k)
            if not m:
                continue
            prefix = m.group(1)
            if prefix.startswith("mtp.") or "visual" in prefix:
                skipped.add(prefix)
                continue
            layers.setdefault((prefix, int(m.group(2))), {})[m.group(4)] = W[k].float()
        stems = {p.rsplit("layers.", 1)[0] for p, _ in layers}
        if len(stems) != 1:
            raise SystemExit("more than one decoder stack in %s: %s" % (name, sorted(stems)))
        pos_gu = tot = pos_up = pos_dn = 0
        per = []
        for key in sorted(layers, key=lambda t: t[1]):
            L = key[1]
            g, u, dn = layers[key]["gate_proj"], layers[key]["up_proj"], layers[key]["down_proj"]
            ip = (g * u).sum(1)
            a = int((ip > 0).sum()); n = int((ip != 0).sum())
            pos_gu += a; tot += n
            pos_up += int((u.sum(1) > 0).sum()); pos_dn += int((dn.sum(0) > 0).sum())
            per.append({"layer": L, "gate_up_inner_positive": a, "units": n})
        b = X.binom_test(tot, pos_gu)
        out[name] = {"gate_up_inner_positive": {"num": pos_gu, "den": tot}, "p_two": flog10(b["p_two"]),
                     "up_rowsum_positive": {"num": pos_up, "den": tot},
                     "down_colsum_positive": {"num": pos_dn, "den": tot}, "per_layer": per,
                     "skipped_prefixes": sorted(skipped)}
        print(name, out[name]["gate_up_inner_positive"], out[name]["p_two"], out[name]["up_rowsum_positive"],
              out[name]["down_colsum_positive"])
    os.makedirs(os.path.join(ROOT, "out", "weights"), exist_ok=True)
    with open(os.path.join(ROOT, "out", "weights", "weight_lean.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
