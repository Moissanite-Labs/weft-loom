"""Test of the first agent's explanation for Falcon (post hoc claim): the sign of <gate_i, up_i> is not a fair
coin in Falcon-H1 Tiny, and this is what makes its product traces skew positive.

Own safetensors reader (8-byte little-endian header length, JSON header, raw little-endian data; BF16 converted
by shifting into the high half of a float32). numpy only; exact binomial p-values from exact.py.

Per model: count of units with <gate_i, up_i> > 0. For Falcon-H1-Tiny-R-0.6B also: per-unit agreement between
sign <gate_i, up_i> and the sign of the third central moment of the saved trace; and whether the MLP tensors of the
R model and the pre-GRPO model are byte-identical.
"""
import sys, os, json, struct, re
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exact  # noqa: E402

# --real-models DIR: the first run's folder (traces/, hf/, data/, out/). Default: ../../real-models next to this
# folder in the published record. The option is removed from sys.argv before the positional arguments are read.
import argparse as _argparse
_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--real-models", default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "real-models"))
_known, _rest = _ap.parse_known_args()
sys.argv = sys.argv[:1] + _rest
RM = _known.real_models
HF = os.path.join(RM, "hf", "models")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ST:
    def __init__(self, path):
        self.f = open(path, "rb")
        n = struct.unpack("<Q", self.f.read(8))[0]
        self.h = json.loads(self.f.read(n))
        self.base = 8 + n

    def raw(self, k):
        e = self.h[k]
        a, b = e["data_offsets"]
        self.f.seek(self.base + a)
        return self.f.read(b - a)

    def get(self, k):
        e = self.h[k]
        buf = self.raw(k)
        if e["dtype"] == "BF16":
            u = np.frombuffer(buf, dtype="<u2").astype(np.uint32) << 16
            x = u.view(np.float32)
        elif e["dtype"] == "F32":
            x = np.frombuffer(buf, dtype="<f4")
        elif e["dtype"] == "F16":
            x = np.frombuffer(buf, dtype="<f2").astype(np.float32)
        else:
            raise SystemExit("dtype " + e["dtype"])
        return x.reshape(e["shape"]).astype(np.float64)


def files(d):
    p = os.path.join(HF, d)
    return [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.endswith(".safetensors")]


def mlp_keys(st):
    pat = re.compile(r"^(?!.*visual)(?!.*mtp)(.*layers\.(\d+)\.(?:mlp|feed_forward))\.gate_proj\.weight$")
    out = []
    for k in st.h:
        m = pat.match(k)
        if m:
            out.append((int(m.group(2)), m.group(1)))
    return sorted(out)


def gate_up_signs(d):
    signs = []
    for path in files(d):
        st = ST(path)
        for L, pre in mlp_keys(st):
            g = st.get(pre + ".gate_proj.weight"); u = st.get(pre + ".up_proj.weight")
            signs.append((L, np.sign((g * u).sum(axis=1))))
    signs.sort(key=lambda t: t[0])
    return np.concatenate([s for _, s in signs]), len(signs)


def main():
    res = {}
    models = ["tiiuae__Falcon-H1-Tiny-R-0.6B", "tiiuae__Falcon-H1-Tiny-R-0.6B-pre-GRPO",
              "tiiuae__Falcon-H1-Tiny-90M-Base", "HuggingFaceTB__SmolLM2-135M", "HuggingFaceTB__SmolLM2-135M-Instruct",
              "HuggingFaceTB__SmolLM2-360M", "Qwen__Qwen3.5-0.8B", "Qwen__Qwen3.5-2B"]
    sgn = {}
    for d in models:
        s, nl = gate_up_signs(d)
        sgn[d] = s
        pos = int((s > 0).sum()); nz = int((s != 0).sum())
        p = exact.binom_two_sided(nz, pos)
        res[d] = {"layers": nl, "units": int(len(s)), "positive": pos, "nonzero": nz, "p_two": exact.fmt(p)}
        print(d, res[d], flush=True)
    # R vs pre-GRPO: byte identity of every MLP tensor, and of all tensors
    a = ST(files("tiiuae__Falcon-H1-Tiny-R-0.6B")[0]); b = ST(files("tiiuae__Falcon-H1-Tiny-R-0.6B-pre-GRPO")[0])
    same_mlp = diff_mlp = same_all = diff_all = 0
    diff_names = []
    for k in sorted(a.h):
        if k == "__metadata__" or k not in b.h:
            continue
        eq = a.raw(k) == b.raw(k)
        is_mlp = "feed_forward" in k
        if eq:
            same_all += 1; same_mlp += is_mlp
        else:
            diff_all += 1; diff_mlp += is_mlp
            if len(diff_names) < 8:
                diff_names.append(k)
    res["R_vs_preGRPO"] = {"tensors_identical": same_all, "tensors_different": diff_all, "mlp_identical": same_mlp,
                           "mlp_different": diff_mlp, "first_different": diff_names,
                           "only_in_R": sorted(set(a.h) - set(b.h))[:5], "only_in_pre": sorted(set(b.h) - set(a.h))[:5]}
    print(res["R_vs_preGRPO"], flush=True)
    # agreement of weight sign with trace skew sign (Falcon R, saved traces), per unit
    s = sgn["tiiuae__Falcon-H1-Tiny-R-0.6B"]
    m3s = []
    for L in range(44):
        x = np.load(os.path.join(RM, "traces/falcon/L%02d.npy" % L)).astype(np.float64)
        d = x - x.mean(0)
        m3s.append(np.sign((d ** 3).mean(0)))
    m3 = np.concatenate(m3s)
    tab = {"w+_skew+": int(((s > 0) & (m3 > 0)).sum()), "w+_skew-": int(((s > 0) & (m3 < 0)).sum()),
           "w-_skew+": int(((s < 0) & (m3 > 0)).sum()), "w-_skew-": int(((s < 0) & (m3 < 0)).sum())}
    agree = tab["w+_skew+"] + tab["w-_skew-"]
    res["falcon_weight_sign_vs_trace_skew"] = dict(tab, agree=agree, units=int(len(s)))
    print(res["falcon_weight_sign_vs_trace_skew"])
    json.dump(res, open(os.path.join(ROOT, "out/weights_check.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
