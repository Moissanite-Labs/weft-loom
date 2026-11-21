"""Download config, tokenizer and safetensors files for the planned models into this folder.

Run: HF_HOME=<folder>/hf/home python -I download.py <folder> [group...]
No token is sent. Nothing downloaded is executed.
"""
import json
import os
import sys

ROOT = sys.argv[1]
os.environ["HF_HOME"] = os.path.join(ROOT, "hf", "home")
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
from huggingface_hub import snapshot_download, HfApi  # noqa: E402

MODELS = {
    "1": [("HuggingFaceTB/SmolLM2-135M", None), ("HuggingFaceTB/SmolLM2-135M-Instruct", None),
          ("HuggingFaceTB/SmolLM2-360M", None)],
    "2": [("EleutherAI/pythia-160m", None), ("EleutherAI/pythia-160m-seed1", None),
          ("EleutherAI/pythia-160m-seed2", None), ("EleutherAI/pythia-160m", "step1000"),
          ("EleutherAI/pythia-160m", "step8000"), ("EleutherAI/pythia-160m", "step32000")],
    "3": [("tiiuae/Falcon-H1-Tiny-R-0.6B", None)],
    "5": [("Qwen/Qwen3.5-0.8B", None), ("Qwen/Qwen3.5-2B", None)],
}
PATTERNS = ["config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json",
            "special_tokens_map.json", "vocab.json", "merges.txt", "*.safetensors", "*.safetensors.index.json"]


def local_name(repo, rev):
    return repo.replace("/", "__") + ("@" + rev if rev else "")


def main():
    groups = sys.argv[2:] or ["1", "2", "3"]
    api = HfApi()
    rec_path = os.path.join(ROOT, "data", "downloads.json")
    rec = json.load(open(rec_path)) if os.path.exists(rec_path) else {}
    for g in groups:
        for repo, rev in MODELS[g]:
            name = local_name(repo, rev)
            d = os.path.join(ROOT, "hf", "models", name)
            info = api.model_info(repo, revision=rev or "main", token=False)
            p = snapshot_download(repo_id=repo, revision=rev or "main", local_dir=d, allow_patterns=PATTERNS,
                                  token=False)
            files = sorted(os.listdir(p))
            rec[name] = {"repo": repo, "revision": rev or "main", "sha": info.sha, "files": files}
            print(name, info.sha, files, flush=True)
            json.dump(rec, open(rec_path, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
