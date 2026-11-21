"""Check that the loaded model's layer-0 and last-layer down_proj weights equal the safetensors file (no random init).
Run: HF_HUB_OFFLINE=1 python -I check_load.py <folder> <model dir>..."""
import os, re, sys
os.environ["HF_HUB_OFFLINE"] = "1"
import torch
from safetensors import safe_open
from transformers import AutoModelForCausalLM
ROOT = sys.argv[1]
for name in sys.argv[2:]:
    d = os.path.join(ROOT, "hf", "models", name)
    m = AutoModelForCausalLM.from_pretrained(d, dtype=torch.float32)
    keys = {}
    for f in os.listdir(d):
        if f.endswith(".safetensors"):
            with safe_open(os.path.join(d, f), "pt") as fh:
                for k in fh.keys():
                    mm = re.search(r"layers\.(\d+)\.(mlp|feed_forward)\.(down_proj|dense_4h_to_h)\.weight$", k)
                    if mm and "visual" not in k and "mtp" not in k:
                        keys[int(mm.group(1))] = (os.path.join(d, f), k)
    ok = True
    mods = {int(re.search(r"layers\.(\d+)\.", n).group(1)): mod for n, mod in m.named_modules()
            if re.search(r"layers\.\d+\.(mlp|feed_forward)\.(down_proj|dense_4h_to_h)$", n) and "visual" not in n}
    for L in (0, max(keys)):
        f, k = keys[L]
        with safe_open(f, "pt") as fh:
            w = fh.get_tensor(k).float()
        ok &= bool(torch.equal(w, mods[L].weight.detach()))
    print(name, "layers in file", len(keys), "layers in model", len(mods), "weights equal", ok)
