"""Advocate pass: N6 and Unlock 1A on all 42 layers of Gemma 4 E4B.

Inputs (read only): argv[1] g4e4 page (sha256 f1340b4f..., equal to the sibling's pinned copy),
argv[2] siliquant output-budget results.jsonl (per-layer clip:5@ffn_down#L rows).
Per-layer statistics use exact integers (group out-weights in thousandths, as the sibling defines
them, rebuilt here independently). Spearman rho is exact (Fraction) on ranks with average ties.
Its null is sampled by seeded permutations. Must-fail control: the same pipeline on a seeded
shuffle of the layer labels. No bare assert.
"""
import base64
import json
import os
import random
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adv_page as pg  # noqa: E402


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [Fraction(0)] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = Fraction(i + j + 2, 2)
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    ma = sum(ra) / n
    mb = sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = sum((x - ma) ** 2 for x in ra)
    db = sum((y - mb) ** 2 for y in rb)
    return num, da, db  # rho = num / sqrt(da*db); sign and square are exact


def rho_float(a, b):
    num, da, db = spearman(a, b)
    return float(num) / (float(da) * float(db)) ** 0.5


def perm_p(a, b, seeds, draws):
    obs = rho_float(a, b)
    out = []
    for sd in seeds:
        rng = random.Random(sd)
        bb = list(b)
        ge = 0
        for _ in range(draws):
            rng.shuffle(bb)
            if rho_float(a, bb) >= obs:
                ge += 1
        out.append((sd, ge, draws))
    return obs, out


def main(page, results):
    d = pg.load_data(page)
    ids = pg.group_ids(d)
    W, L = int(d["width"]), int(d["layers"])
    fam = d["structures"]["familyOf"]
    info = d["structures"]["info"]
    share = base64.b64decode(d["share"])
    if len(share) != 3 * int(d["n"]):
        print("share length mismatch")
        return 1
    g_out = [sum(int(round(w * 1000)) for _k, w in g.get("out", [])) for g in info]
    g_in = [sum(int(round(w * 1000)) for _k, w in g.get("in", [])) for g in info]
    per = []
    for lay in range(L):
        o = i_ = dk = ps = ms = cs = 0
        for c in range(W):
            x = lay * W + c
            g = ids[x]
            ps += share[3 * x]
            ms += share[3 * x + 1]
            cs += share[3 * x + 2]
            if g == 65535:
                dk += 1
                continue
            if fam[g] < 0:
                dk += 1
            o += g_out[g]
            i_ += g_in[g]
        per.append({"layer": lay, "out": o, "in": i_, "dark": dk, "p": ps, "m": ms, "c": cs})
    by_out = sorted(per, key=lambda r: (-r["out"], r["layer"]))
    print("top-6 layers by mean group out-weight (x1e5):",
          [(r["layer"], (r["out"] * 100) // W) for r in by_out[:6]])
    l10, l9 = per[10]["out"], per[9]["out"]
    print("L10 vs L9 margin: %s = %.4f%%" % (Fraction(l10 - l9, l9), 100 * float(Fraction(l10 - l9, l9))))
    first = [r["layer"] for r in per if r["c"] > r["p"]]
    print("layers with code share > prose share:", first)
    darks = [Fraction(r["dark"], W) for r in per]
    print("per-layer no-family share: min %.4f (L%d) max %.4f (L%d)" % (
        float(min(darks)), darks.index(min(darks)), float(max(darks)), darks.index(max(darks))))
    # How many of a layer's neurons sit in groups whose members are mostly in other layers?
    gl = {}
    for x, g in enumerate(ids):
        if g != 65535:
            gl.setdefault(g, {}).setdefault(x // W, 0)
            gl[g][x // W] += 1
    own10 = sum(cnt for g, layers in gl.items() for lay, cnt in layers.items()
                if lay == 10 and max(layers, key=lambda k: (layers[k], -k)) == 10)
    print("L10 neurons whose group's modal layer is L10: %d of %d" % (own10, W))

    kl = {}
    with open(results, encoding="utf-8") as fh:
        lines = fh.readlines()
    for line in lines:
        r = json.loads(line)
        v = r.get("variant", "")
        if v.startswith("clip:5@ffn_down#") and ":" not in v[len("clip:5@ffn_down#"):] \
                and "," not in v and r.get("layers") and len(r["layers"]) == 1:
            kl[r["layers"][0]] = Fraction(str(r["kl_mean"]))
    if sorted(kl) != list(range(L)):
        print("missing layers in KL:", sorted(set(range(L)) - set(kl)))
        return 1
    kls = [kl[i] for i in range(L)]
    krank = sorted(range(L), key=lambda i: -kls[i])
    print("KL rank (1 = largest) of the top-5 mean_out layers:",
          [(r["layer"], krank.index(r["layer"]) + 1) for r in by_out[:5]])
    print("L9 %s, L12 %s, L13 %s" % (float(kl[9]), float(kl[12]), float(kl[13])))
    outs = [r["out"] for r in per]
    ins = [r["in"] for r in per]
    seeds = (101, 20262, 777)
    for name, a, b in (
        ("mean_out vs KL, 42 layers", outs, kls),
        ("mean_out vs KL, 41 layers without L10", outs[:10] + outs[11:], kls[:10] + kls[11:]),
        ("mean_in vs KL, 42 layers (comparator)", ins, kls),
        ("no-family share vs KL, 42 layers (comparator)", [float(x) for x in darks], kls),
    ):
        num, da, db = spearman(a, b)
        obs, res = perm_p(a, b, seeds, 3000)
        print("%-48s rho = %+.4f (sign exact: %s); one-sided perm P(rho>=obs): %s" % (
            name, obs, "+" if num > 0 else ("-" if num < 0 else "0"),
            ", ".join("seed %d %d/%d" % r for r in res)))
    rng = random.Random(4242)
    sh = list(outs)
    rng.shuffle(sh)
    obs, res = perm_p(sh, kls, (5,), 3000)
    print("control, shuffled mean_out vs KL: rho = %+.4f; perm %d/%d" % (obs, res[0][1], res[0][2]))
    # Does L10 stand out on mean_out the way it does on KL?
    srt = sorted(outs, reverse=True)
    print("mean_out top-1/top-2 ratio %.4f; KL top-1/top-2 ratio %.2f" % (
        srt[0] / srt[1], float(sorted(kls, reverse=True)[0] / sorted(kls, reverse=True)[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
