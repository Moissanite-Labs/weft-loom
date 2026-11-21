"""Corpus checks (pure Python): hashes, 100 chunks x 200 words, word spans equal str.split() of each chunk,
parts 33/34/33, chunk text found verbatim in its source file (which chunks are not one substring), CR characters.

Usage: python3 -I corpus_check.py [--real-models DIR] --sources GUTENBERG TEXTWRAP FRACTIONS GATE_CONTRACTS INERTIA
The five source files are given in the order of data/corpus_meta.json (see real-models/scripts/build_corpus.py).
"""
import json, hashlib, os, sys

# --real-models DIR: the first run's folder (traces/, hf/, data/, out/). Default: ../../real-models next to this
# folder in the published record. The option is removed from sys.argv before the positional arguments are read.
import argparse as _argparse
_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--real-models", default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "real-models"))
_known, _rest = _ap.parse_known_args()
sys.argv = sys.argv[:1] + _rest
RM = _known.real_models


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


c = json.load(open(os.path.join(RM, "data/corpus.json")))
meta = json.load(open(os.path.join(RM, "data/corpus_meta.json")))
out = {"corpus_json_sha256": sha(os.path.join(RM, "data/corpus.json")),
       "corpus_txt_sha256": sha(os.path.join(RM, "data/corpus.txt"))}
srcs = {}
_sp = _argparse.ArgumentParser()
_sp.add_argument("--sources", nargs=5, required=True)
_paths = _sp.parse_args().sources
for s, p in zip(meta["sources"], _paths):
    ok = os.path.exists(p) and sha(p) == s["sha256"]
    out.setdefault("source_hash_ok", []).append([os.path.basename(p), ok])
    if os.path.exists(p):
        srcs[s["part"]] = srcs.get(s["part"], "") + "\x00" + open(p, encoding="utf-8", newline="").read()
bad_spans = 0; nw = 0; parts = {}; not_substring = []; cr = 0
for i, ch in enumerate(c["chunks"]):
    t = ch["text"]; w = ch["words"]
    parts[ch["part"]] = parts.get(ch["part"], 0) + 1
    nw += len(w)
    if [t[a:b] for a, b in w] != t.split() or len(w) != 200:
        bad_spans += 1
    if t not in srcs.get(ch["part"], ""):
        not_substring.append(i)
    cr += t.count("\r")
out.update({"chunks": len(c["chunks"]), "words": nw, "chunks_with_bad_spans": bad_spans, "parts": parts,
            "chunks_not_a_verbatim_substring_of_their_part_sources": not_substring, "carriage_returns": cr})
txt = open(os.path.join(RM, "data/corpus.txt"), encoding="utf-8", newline="").read()
out["corpus_txt_split_words"] = len(txt.split())
out["corpus_txt_equals_join"] = txt == "\n\n".join(ch["text"] for ch in c["chunks"])
print(json.dumps(out, indent=1))
json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out/corpus_check.json"), "w"), indent=1)
