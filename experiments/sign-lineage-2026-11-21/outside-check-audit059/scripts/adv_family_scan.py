"""Advocate pass: is "Adjacent brackets" the most enriched family among all families, per layer,
and what does a family-wide multiplicity correction do to its tail? (S1 / positive point 1)

argv[1] q08 page, argv[2] frozen_weights_manifest.json. Exact tails (adv_exact, two routes).
No bare assert.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adv_exact as ex  # noqa: E402
import adv_page as pg  # noqa: E402


def main(page, manifest):
    d = pg.load_data(page)
    ids = pg.group_ids(d)
    fam = pg.family_of_neuron(d, ids)
    W = int(d["width"])
    titles = [f["title"] for f in d["structures"]["families"]]
    with open(manifest, encoding="utf-8") as fh:
        man = json.load(fh)
    for layer in (15, 19):
        sel = [int(x) for x in man[str(layer)]["selected_neurons"]]
        lab = fam[layer * W:(layer + 1) * W]
        present = sorted({f for f in lab if f >= 0})
        rows = []
        for f in present:
            K = sum(1 for x in lab if x == f)
            k = sum(1 for c in sel if lab[c] == f)
            if k == 0:
                continue
            rows.append((ex.tail_checked(W, K, 64, k), f, k, K))
        rows.sort()
        m = len(present)
        print("L%d: %d families present in the layer; families hit by the selection: %d" % (layer, m, len(rows)))
        for p, f, k, K in rows[:5]:
            print("   %-45s %2d/64 vs %3d/%d  exact tail %s  x%d families = %s" % (
                titles[f][:45], k, K, W, ex.sci(p), m, ex.sci(min(1, p * m))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
