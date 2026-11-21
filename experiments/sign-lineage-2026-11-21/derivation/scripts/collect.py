"""Assemble ../RESULTS.json from the exact outputs and the sampled analysis files."""
import glob
import json
import os
import subprocess
import sys


def _opt(name, default):
    """Folder option from the command line (for example --out DIR), with the record's layout as default."""
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument(name, default=default)
    known, rest = ap.parse_known_args()
    sys.argv[1:] = rest
    return getattr(known, name.lstrip("-").replace("-", "_"))


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = _opt("--root", os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "out")


def run_exact(script):
    r = subprocess.run([sys.executable, "-I", "-B", os.path.join(HERE, script)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("exact script failed: " + script + "\n" + r.stdout + r.stderr)
    return r.stdout


def main():
    res = {"date": "2026-11-21", "folder": "derivation",
           "evidence_kinds": {"exact": "S1, S2 (rational), S3, S4, site sentence",
                              "sampled": "S5 (trained networks; seeds in train_all.py and runs/train_log.jsonl)",
                              "anchor": "S1.2 public code lines in transformers 5.22.2",
                              "third_party": "site numbers as quoted in ../site_claims.json, taken on trust"}}
    res["exact"] = {
        "exact_null_selftest": json.loads(run_exact("exact_null.py").splitlines()[0]),
        "independent_checker": json.loads(run_exact("check_independent.py")),
        "symmetry_equivariance": json.loads(run_exact("symmetry_exact.py")),
        "site_sentence": json.loads(run_exact("site_sentence.py")),
    }
    sampled = {}
    for f in sorted(glob.glob(os.path.join(OUT, "analysis_*.json"))):
        with open(f) as fh:
            d = json.load(fh)
        for k, v in d.items():
            if k == "diagnostics_per_model_layer":
                if v:
                    sampled.setdefault(k, {}).update(v)
            else:
                sampled[k] = v
    res["sampled"] = sampled
    eq = os.path.join(OUT, "equivariance_float.json")
    if os.path.exists(eq):
        with open(eq) as fh:
            res["sampled_implementation_check"] = json.load(fh)
    log = os.path.join(ROOT, "runs", "train_log.jsonl")
    with open(log) as fh:
        res["training_log"] = [json.loads(x) for x in fh if x.strip()]
    with open(os.path.join(ROOT, "RESULTS.json"), "w", newline="\n") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    print("wrote RESULTS.json with", len(sampled), "sampled entries")


if __name__ == "__main__":
    main()
