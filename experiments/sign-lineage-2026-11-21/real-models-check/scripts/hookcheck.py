"""Step 3 and step 4 of the verification (torch, own hook code; second checker).

Step 3: SmolLM2-135M on three corpus chunks. Own word -> token alignment from the saved word spans. Per layer:
  * a forward hook on model.layers[i].mlp captures the MLP input x;
  * a forward pre-hook on model.layers[i].mlp.down_proj captures the down projection input;
  * an independent float64 recomputation silu(W_gate x) * (W_up x) from the weights.
  Compared: down_proj input vs float64 product (is the hooked value the product?); saved float16 trace rows vs
  the down_proj input at the aligned tokens.
Step 4: own laundered SmolLM2-135M-Instruct (signperm npz, seed 5150): logits vs the Instruct model; laundered
  down_proj input vs signed-permuted Instruct down_proj input; vs signed-permuted saved Instruct trace.

Usage: python -I hookcheck.py <device cpu|mps> <out.json>
"""
import os, sys, json, time
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

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
CHUNKS = [0, 40, 99]


def align(tok, text, spans):
    enc = tok(text, return_offsets_mapping=True)
    ids = enc["input_ids"]
    offs = enc["offset_mapping"]
    nspecial = sum(1 for (a, b) in offs if a == b)
    pos = []
    for (ws, we) in spans:
        c = we - 1
        hit = [t for t, (a, b) in enumerate(offs) if a < b and a <= c < b]
        if not hit:
            raise SystemExit("no token for char %d" % c)
        pos.append(hit[-1])
    return ids, pos, nspecial


def capture(model, ids, device):
    layers = model.model.layers
    store = {"x": {}, "d": {}}
    hs = []
    for i, L in enumerate(layers):
        hs.append(L.mlp.register_forward_hook(lambda m, inp, out, i=i: store["x"].__setitem__(i, inp[0].detach()[0].float().cpu())))
        hs.append(L.mlp.down_proj.register_forward_pre_hook(lambda m, inp, i=i: store["d"].__setitem__(i, inp[0].detach()[0].float().cpu())))
    with torch.no_grad():
        out = model(torch.tensor([ids], device=device))
    for h in hs:
        h.remove()
    return store, out.logits[0].float().cpu()


def main():
    device, outp = sys.argv[1], sys.argv[2]
    corpus = json.load(open(os.path.join(RM, "data/corpus.json")))
    res = {"device": device, "chunks": CHUNKS, "torch": torch.__version__}
    # ---- step 3
    mdir = os.path.join(RM, "hf/models/HuggingFaceTB__SmolLM2-135M")
    tok = AutoTokenizer.from_pretrained(mdir)
    model = AutoModelForCausalLM.from_pretrained(mdir, dtype=torch.float32).to(device).eval()
    nl = len(model.model.layers)
    names = [n for n, _ in model.named_modules() if n.endswith("mlp.down_proj")]
    res["down_proj_module_names_first_last"] = [names[0], names[-1], len(names)]
    res["down_proj_in_features"] = int(model.model.layers[0].mlp.down_proj.in_features)
    res["act"] = model.config.hidden_act
    s3 = []
    for c in CHUNKS:
        ch = corpus["chunks"][c]
        ids, pos, nspecial = align(tok, ch["text"], ch["words"])
        store, _ = capture(model, ids, device)
        rows = np.arange(200 * c, 200 * c + 200)
        worst_prod = 0.0; worst_saved = 0.0; worst_saved_rel = 0.0; eq16 = 0; tot = 0; worst_unit_rel = 0.0; min_corr = 1.0
        for i in range(nl):
            mlp = model.model.layers[i].mlp
            x = store["x"][i].double()
            Wg = mlp.gate_proj.weight.detach().cpu().double(); Wu = mlp.up_proj.weight.detach().cpu().double()
            g = x @ Wg.T
            prod = (g * torch.sigmoid(g)) * (x @ Wu.T)
            d = store["d"][i].double()
            worst_prod = max(worst_prod, float((d - prod).abs().max() / prod.abs().max()))
            saved = np.load(os.path.join(RM, "traces/s135/L%02d.npy" % i), mmap_mode="r")[rows].astype(np.float64)
            mine = d.numpy()[pos]
            diff = np.abs(saved - mine)
            worst_saved = max(worst_saved, float(diff.max()))
            # float16 spacing at each value: relative 2^-11 of the value (round-to-nearest gives <= half spacing)
            rel = diff / np.maximum(np.abs(mine), 6.1e-5)
            worst_saved_rel = max(worst_saved_rel, float(rel.max()))
            eq16 += int((mine.astype(np.float16) == np.asarray(saved, dtype=np.float16)).sum())
            # difference relative to each unit's largest |value| on these 200 words, and per-unit correlation
            unit_scale = np.maximum(np.abs(mine).max(axis=0), 1e-30)
            worst_unit_rel = max(worst_unit_rel, float((diff.max(axis=0) / unit_scale).max()))
            a = saved - saved.mean(0); b = mine - mine.mean(0)
            den = np.sqrt((a * a).sum(0) * (b * b).sum(0))
            ok = den > 0
            min_corr = min(min_corr, float(((a * b).sum(0)[ok] / den[ok]).min()))
            tot += mine.size
        s3.append({"chunk": c, "part": ch["part"], "tokens": len(ids), "special_tokens": nspecial,
                   "max_rel_diff_downproj_input_vs_float64_product": worst_prod,
                   "max_abs_diff_saved_vs_mine": worst_saved, "max_rel_diff_saved_vs_mine": worst_saved_rel,
                   "float16_identical": [eq16, tot],
                   "max_diff_over_unit_max_abs": worst_unit_rel, "min_unit_corr_saved_vs_mine": min_corr})
        print("step3", s3[-1], flush=True)
    res["step3"] = s3
    del model
    # ---- step 4
    idir = os.path.join(RM, "hf/models/HuggingFaceTB__SmolLM2-135M-Instruct")
    tok = AutoTokenizer.from_pretrained(idir)
    ref = AutoModelForCausalLM.from_pretrained(idir, dtype=torch.float32).to(device).eval()
    lau = AutoModelForCausalLM.from_pretrained(idir, dtype=torch.float32).to(device).eval()
    sp = np.load(os.path.join(ROOT, "out/laund/signperm_5150.npz"))
    perm, sign = sp["perm"], sp["sign"]
    h = int(sp["width"])
    with torch.no_grad():
        for i, L in enumerate(lau.model.layers):
            p = torch.tensor(perm[i * h:(i + 1) * h] - i * h, device=device)
            s = torch.tensor(sign[i * h:(i + 1) * h], dtype=torch.float32, device=device)
            L.mlp.gate_proj.weight.copy_(L.mlp.gate_proj.weight[p])
            L.mlp.up_proj.weight.copy_(L.mlp.up_proj.weight[p] * s[:, None])
            L.mlp.down_proj.weight.copy_(L.mlp.down_proj.weight[:, p] * s[None, :])
    # weights really changed and are a signed permutation
    w_changed = float((lau.model.layers[0].mlp.up_proj.weight - ref.model.layers[0].mlp.up_proj.weight).abs().max())
    s4 = []
    for c in CHUNKS:
        ch = corpus["chunks"][c]
        ids, pos, _ = align(tok, ch["text"], ch["words"])
        st_r, lg_r = capture(ref, ids, device)
        st_l, lg_l = capture(lau, ids, device)
        rows = np.arange(200 * c, 200 * c + 200)
        worst_tr = 0.0; worst_saved = 0.0; scale = 0.0
        for i in range(len(ref.model.layers)):
            p = perm[i * h:(i + 1) * h] - i * h
            s = sign[i * h:(i + 1) * h]
            dr = st_r["d"][i].numpy(); dl = st_l["d"][i].numpy()
            expect = dr[:, p] * s[None, :]
            worst_tr = max(worst_tr, float(np.abs(dl - expect).max()))
            scale = max(scale, float(np.abs(dr).max()))
            saved = np.load(os.path.join(RM, "traces/s135i/L%02d.npy" % i), mmap_mode="r")[rows].astype(np.float64)
            worst_saved = max(worst_saved, float(np.abs(dl[pos] - saved[:, p] * s[None, :]).max()))
        s4.append({"chunk": c, "max_abs_logit_diff": float((lg_l - lg_r).abs().max()),
                   "max_abs_logit": float(lg_r.abs().max()),
                   "max_abs_trace_diff_vs_signed_perm_of_ref": worst_tr, "trace_scale": scale,
                   "max_abs_diff_vs_signed_perm_of_saved_instruct_trace": worst_saved})
        print("step4", s4[-1], flush=True)
    res["step4"] = {"seed": int(sp["seed"]), "weights_changed_max": w_changed, "chunks": s4}
    with open(outp, "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
