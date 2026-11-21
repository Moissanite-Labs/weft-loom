"""Capture per-word MLP traces (PLAN.txt b, c) for one model key, save float16 per layer.

Run: HF_HUB_OFFLINE=1 python -I capture.py <real-models folder> <key>
Keys: s135 s135i s360 s135L py py_s1 py_s2 py_1k py_8k py_32k falcon q08 q2
s135L builds the laundered copy of s135i (seed 777) and also checks its logits against s135i.
"""
import json
import os
import re
import sys
import time

ROOT = sys.argv[1]
KEY = sys.argv[2]
os.environ["HF_HOME"] = os.path.join(ROOT, "hf", "home")
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
import numpy as np  # noqa: E402
import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

M = os.path.join(ROOT, "hf", "models")
REG = {
    "s135": "HuggingFaceTB__SmolLM2-135M",
    "s135i": "HuggingFaceTB__SmolLM2-135M-Instruct",
    "s360": "HuggingFaceTB__SmolLM2-360M",
    "s135L": "HuggingFaceTB__SmolLM2-135M-Instruct",
    "py": "EleutherAI__pythia-160m",
    "py_s1": "EleutherAI__pythia-160m-seed1",
    "py_s2": "EleutherAI__pythia-160m-seed2",
    "py_1k": "EleutherAI__pythia-160m@step1000",
    "py_8k": "EleutherAI__pythia-160m@step8000",
    "py_32k": "EleutherAI__pythia-160m@step32000",
    "falcon": "tiiuae__Falcon-H1-Tiny-R-0.6B",
    "q08": "Qwen__Qwen3.5-0.8B",
    "q2": "Qwen__Qwen3.5-2B",
}
PATTERNS = [r"layers\.(\d+)\.mlp\.down_proj$", r"layers\.(\d+)\.mlp\.dense_4h_to_h$",
            r"layers\.(\d+)\.feed_forward\.down_proj$"]


def word_token_index(offsets, words):
    """For each word span (a, b): the last token whose span contains character b-1."""
    idx = []
    for a, b in words:
        c = b - 1
        hit = -1
        for t, (s, e) in enumerate(offsets):
            if e > s and s <= c < e:
                hit = t
        if hit < 0:
            raise SystemExit("word end not in any token span: %r" % ((a, b),))
        idx.append(hit)
    return idx


def find_down_modules(model):
    found = {}
    for name, mod in model.named_modules():
        if "visual" in name or "vision" in name:
            continue
        for p in PATTERNS:
            mm = re.search(p, name)
            if mm:
                found[int(mm.group(1))] = (name, mod)
    L = len(found)
    if sorted(found) != list(range(L)):
        raise SystemExit("layer indices not contiguous")
    return [found[i] for i in range(L)]


def launder(model, seed=777):
    g = torch.Generator().manual_seed(seed)
    info = []
    with torch.no_grad():
        for name, mod in find_down_modules(model):
            mlp_name = name.rsplit(".", 1)[0]
            mlp = model.get_submodule(mlp_name)
            h = mlp.down_proj.weight.shape[1]
            perm = torch.randperm(h, generator=g)
            sign = (torch.randint(0, 2, (h,), generator=g) * 2 - 1).to(mlp.up_proj.weight.dtype)
            mlp.gate_proj.weight.copy_(mlp.gate_proj.weight[perm])
            mlp.up_proj.weight.copy_(mlp.up_proj.weight[perm] * sign[:, None])
            mlp.down_proj.weight.copy_(mlp.down_proj.weight[:, perm] * sign[None, :])
            for lin in (mlp.gate_proj, mlp.up_proj):
                if lin.bias is not None:
                    raise SystemExit("unexpected bias")
            info.append({"layer": mlp_name, "h": h, "n_flipped": int((sign < 0).sum()),
                         "perm_head": perm[:5].tolist()})
    return info


def main():
    t0 = time.time()
    corpus = json.load(open(os.path.join(ROOT, "data", "corpus.json")))
    chunks = corpus["chunks"]
    path = os.path.join(M, REG[KEY])
    tok = AutoTokenizer.from_pretrained(path)
    if not tok.is_fast:
        raise SystemExit("tokenizer is not fast")
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = AutoModelForCausalLM.from_pretrained(path, dtype=torch.float32)
    model.eval()
    meta = {"key": KEY, "dir": REG[KEY], "class": type(model).__name__, "device": device}
    ref = None
    if KEY == "s135L":
        ref = AutoModelForCausalLM.from_pretrained(path, dtype=torch.float32).eval().to(device)
        meta["launder"] = launder(model)
    model.to(device)
    mods = find_down_modules(model)
    meta["modules"] = [n for n, _ in mods]
    L = len(mods)
    h = mods[0][1].weight.shape[1]
    T = sum(len(c["words"]) for c in chunks)
    store = [np.zeros((T, h), dtype=np.float32) for _ in range(L)]
    gate_store = None
    cur = {}
    hooks = []

    def mk(li):
        def pre(mod, args):
            cur[li] = args[0][0].detach()
        return pre

    for li, (n, mod) in enumerate(mods):
        hooks.append(mod.register_forward_pre_hook(mk(li)))
    if KEY == "falcon":
        gate_store = [np.zeros((T, h), dtype=np.float32) for _ in range(L)]
        gcur = {}

        def mkg(li, mlp):
            def fwd(mod, args, out):
                gcur[li] = mlp.act_fn(out[0] * mlp.gate_multiplier).detach()
            return fwd

        for li, (n, mod) in enumerate(mods):
            mlp = model.get_submodule(n.rsplit(".", 1)[0])
            hooks.append(mlp.gate_proj.register_forward_hook(mkg(li, mlp)))
        meta["mlp_multipliers"] = list(model.config.mlp_multipliers)
    pos = 0
    n_tokens = 0
    collisions = 0
    specials = []
    max_abs = 0.0
    logit_diff = 0.0
    logit_max = 0.0
    with torch.no_grad():
        for ci, ch in enumerate(chunks):
            enc = tok(ch["text"], return_offsets_mapping=True)
            ids = enc["input_ids"]
            offs = enc["offset_mapping"]
            sp = tok(ch["text"], add_special_tokens=False)["input_ids"]
            specials.append(len(ids) - len(sp))
            widx = word_token_index(offs, ch["words"])
            collisions += len(widx) - len(set(widx))
            n_tokens += len(ids)
            x = torch.tensor([ids], device=device)
            out = model(input_ids=x)
            if ref is not None:
                r = ref(input_ids=x).logits
                logit_diff = max(logit_diff, float((out.logits - r).abs().max()))
                logit_max = max(logit_max, float(r.abs().max()))
            wi = torch.tensor(widx, device=device)
            n = len(widx)
            for li in range(L):
                v = cur[li].index_select(0, wi).float().cpu().numpy()
                store[li][pos:pos + n] = v
                if gate_store is not None:
                    gate_store[li][pos:pos + n] = gcur[li].index_select(0, wi).float().cpu().numpy()
            pos += n
    if pos != T:
        raise SystemExit("position count")
    for hk in hooks:
        hk.remove()
    outdir = os.path.join(ROOT, "traces", KEY)
    os.makedirs(outdir, exist_ok=True)
    f32_layers = []
    for li in range(L):
        a = store[li]
        ma = float(np.abs(a).max())
        max_abs = max(max_abs, ma)
        if ma > 65000:
            np.save(os.path.join(outdir, "L%02d.npy" % li), a)
            f32_layers.append(li)
        else:
            np.save(os.path.join(outdir, "L%02d.npy" % li), a.astype(np.float16))
    if gate_store is not None:
        gd = os.path.join(ROOT, "traces", KEY + "_gate")
        os.makedirs(gd, exist_ok=True)
        for li in range(L):
            np.save(os.path.join(gd, "L%02d.npy" % li), gate_store[li].astype(np.float16))
    meta.update({"layers": L, "h": h, "T": T, "n_tokens": n_tokens, "word_token_collisions": collisions,
                 "special_tokens_added": sorted(set(specials)), "max_abs_value": max_abs,
                 "float32_layers": f32_layers, "seconds": round(time.time() - t0, 1),
                 "torch": torch.__version__})
    if ref is not None:
        meta["laundered_max_abs_logit_diff"] = logit_diff
        meta["reference_max_abs_logit"] = logit_max
    json.dump(meta, open(os.path.join(outdir, "meta.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in meta.items() if k not in ("modules", "launder")}))


if __name__ == "__main__":
    main()
