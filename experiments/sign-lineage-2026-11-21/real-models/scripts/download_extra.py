"""Post hoc extra downloads (weights only, for the weight-space sign statistic). Same rules as download.py.
Run: python -I download_extra.py <folder> <repo>..."""
import json, os, sys
ROOT = sys.argv[1]
os.environ["HF_HOME"] = os.path.join(ROOT, "hf", "home")
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
from huggingface_hub import snapshot_download, HfApi
PAT = ["config.json", "*.safetensors", "*.safetensors.index.json"]
rec_path = os.path.join(ROOT, "data", "downloads.json")
rec = json.load(open(rec_path))
for repo in sys.argv[2:]:
    name = repo.replace("/", "__")
    info = HfApi().model_info(repo, token=False)
    snapshot_download(repo_id=repo, local_dir=os.path.join(ROOT, "hf", "models", name), allow_patterns=PAT, token=False)
    rec[name] = {"repo": repo, "revision": "main", "sha": info.sha, "post_hoc": True}
    print(name, info.sha, flush=True)
json.dump(rec, open(rec_path, "w"), indent=1, sort_keys=True)
