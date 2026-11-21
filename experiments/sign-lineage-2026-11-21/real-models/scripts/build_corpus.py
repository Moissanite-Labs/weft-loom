"""Build the 20,000-word corpus of PLAN.txt (a): 100 chunks of 200 words, prose / code / math.

The corpus text is not committed. Fetch the five source files yourself; the run stops if a file's
SHA-256 differs from the one below.

  prose  Arthur Conan Doyle, The Adventures of Sherlock Holmes, Project Gutenberg eBook 1661,
         file 1661-0.txt from https://gutenberg.pglaf.org/1/6/6/1661/1661-0.txt (public domain in the USA)
         sha256 b9c105a5c0cf9fcb37c7d0211658851ed56074519c9455d15e20f04c0c5a3174
  code   CPython 3.14.6 standard library, Lib/textwrap.py (PSF License)
         sha256 7f05d89c983f5aa8cefcff707a9cc561ed60c51fc8a68e2e3ab61cc6dfa84544
  code   CPython 3.14.6 standard library, Lib/fractions.py (PSF License)
         sha256 7a95f1c506c9ac4b2277df5f2bdd9d61cc67b520c45021a5a961939770221ef6
  math   docs/09-gate-contracts.md of github.com/siliconcordat/loom at commit 8cdfa396a38f (CC BY 4.0)
         sha256 5bf76eb94589b36946e4025a6b8116da9a8678304e28a6a058b022f6e7c2340a
  math   docs/10-exact-inertia-certificates.md of github.com/siliconcordat/loom at commit 64c797d30da1 (CC BY 4.0)
         sha256 93f007c5370065952a0729587c04e06dcd4c5bf68bee209ba34eea4ccf1d0f02

Run:
  python3 -I -B build_corpus.py --root <real-models folder> --gutenberg 1661-0.txt \
      --textwrap textwrap.py --fractions fractions.py \
      --gate-contracts 09-gate-contracts.md --inertia 10-exact-inertia-certificates.md

Writes <root>/data/corpus.json, corpus.txt and corpus_meta.json. The original run stored each source's local
path inside corpus.json, so its recorded hash (ae42fafa...) depends on where the files sat. This version stores
a source name instead and gives corpus.json the SHA-256 1174a9e572fb0f6507fee448e6b8ae381552a9cc4a08014aa900af510ee9307c,
with chunks identical to the original. The hash of corpus.txt,
67693619fea31dc309a9f5cb122b7f70358f5ede82c20748c4015d3dbd6b4629, depends only on the text and is the same in both.
"""
import argparse
import hashlib
import json
import os
import re
from collections import Counter

EXPECTED = {
    "gutenberg": "b9c105a5c0cf9fcb37c7d0211658851ed56074519c9455d15e20f04c0c5a3174",
    "textwrap": "7f05d89c983f5aa8cefcff707a9cc561ed60c51fc8a68e2e3ab61cc6dfa84544",
    "fractions": "7a95f1c506c9ac4b2277df5f2bdd9d61cc67b520c45021a5a961939770221ef6",
    "gate_contracts": "5bf76eb94589b36946e4025a6b8116da9a8678304e28a6a058b022f6e7c2340a",
    "inertia": "93f007c5370065952a0729587c04e06dcd4c5bf68bee209ba34eea4ccf1d0f02",
}
CHUNK = 200


def sha(b):
    return hashlib.sha256(b).hexdigest()


def parse():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.path.dirname(here), help="real-models folder (writes <root>/data)")
    ap.add_argument("--gutenberg", required=True)
    ap.add_argument("--textwrap", required=True)
    ap.add_argument("--fractions", required=True)
    ap.add_argument("--gate-contracts", required=True)
    ap.add_argument("--inertia", required=True)
    return ap.parse_args()


def main():
    a = parse()
    sources = [
        # (part, key, path, start marker or None, number of words)
        ("prose", "gutenberg", a.gutenberg, "To Sherlock Holmes she is always", 6600),
        ("code", "textwrap", a.textwrap, None, None),
        ("code", "fractions", a.fractions, None, 4587),
        ("math", "gate_contracts", a.gate_contracts, None, 3400),
        ("math", "inertia", a.inertia, None, 3200),
    ]
    records = []
    words_all = []  # (part, source index, text, start, end)
    for si, (part, key, path, marker, n) in enumerate(sources):
        with open(path, "rb") as fh:
            raw = fh.read()
        if sha(raw) != EXPECTED[key]:
            raise SystemExit("SHA-256 of %s is %s, expected %s" % (key, sha(raw), EXPECTED[key]))
        text = raw.decode("utf-8")
        if text.startswith("﻿"):
            text = text[1:]
        start = 0
        if marker is not None:
            start = text.index(marker)
        spans = [(m.start() + start, m.end() + start) for m in re.finditer(r"\S+", text[start:])]
        if n is None:
            n = len(spans)
        if len(spans) < n:
            raise SystemExit("not enough words in " + key)
        spans = spans[:n]
        records.append({"part": part, "source": key, "sha256": sha(raw), "words": n,
                        "first_word": text[spans[0][0]:spans[0][1]], "last_word": text[spans[-1][0]:spans[-1][1]]})
        for s0, s1 in spans:
            words_all.append((part, si, text, s0, s1))
    if len(words_all) != 20000:
        raise SystemExit("word count %d" % len(words_all))
    chunks = []
    for c in range(0, len(words_all), CHUNK):
        ws = words_all[c:c + CHUNK]
        parts = {w[0] for w in ws}
        srcs = {w[1] for w in ws}
        if len(parts) != 1:
            raise SystemExit("chunk straddles parts")
        if len(srcs) != 1:
            # a chunk may straddle two files of one part: join their pieces with a blank line
            offs = []
            cur = ""
            for s in sorted(srcs):
                sub = [w for w in ws if w[1] == s]
                t = sub[0][2]
                a0 = sub[0][3]
                seg = t[a0:sub[-1][4]]
                if cur:
                    cur += "\n\n"
                base = len(cur)
                offs += [(base + w[3] - a0, base + w[4] - a0) for w in sub]
                cur += seg
            chunks.append({"part": ws[0][0], "text": cur, "words": offs})
        else:
            t = ws[0][2]
            a0 = ws[0][3]
            chunks.append({"part": ws[0][0], "text": t[a0:ws[-1][4]],
                           "words": [(w[3] - a0, w[4] - a0) for w in ws]})
    # self-check: every word span is non-whitespace and words split exactly
    for ch in chunks:
        toks = ch["text"].split()
        if toks != [ch["text"][s0:s1] for s0, s1 in ch["words"]]:
            raise SystemExit("word spans do not match split()")
    ddir = os.path.join(a.root, "data")
    os.makedirs(ddir, exist_ok=True)
    jb = json.dumps({"sources": records, "chunks": chunks}, ensure_ascii=False, sort_keys=True).encode("utf-8")
    tb = "\n\n".join(ch["text"] for ch in chunks).encode("utf-8")
    with open(os.path.join(ddir, "corpus.json"), "wb") as fh:
        fh.write(jb)
    with open(os.path.join(ddir, "corpus.txt"), "wb") as fh:
        fh.write(tb)
    out = {"sources": records, "n_chunks": len(chunks), "chunks_per_part": dict(Counter(ch["part"] for ch in chunks)),
           "corpus_json_sha256": sha(jb), "corpus_txt_sha256": sha(tb),
           "n_words_corpus_txt_split": len(tb.decode("utf-8").split())}
    with open(os.path.join(ddir, "corpus_meta.json"), "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
