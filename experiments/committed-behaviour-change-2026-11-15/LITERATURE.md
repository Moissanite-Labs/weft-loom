# Prior-art search for the two novelty stakes

Run 2026-11-15 against the arXiv API only. Script: `lit_search.py`. Output: `lit-search.out`. Ten queries, titles only read. Absence here is absence in this search.

## Stake 1: a bound on change between two model versions, refuted by one input

Nearest found: opML (optimistic machine learning on blockchain) and one TEE-rollup successor. Both prove that a single inference was computed correctly. Neither bounds the change between two versions of a model. The query for model-update verification with a bound returned two papers, neither about version-to-version behaviour bounds.

No equivalent to the CBC claim was found in this search. The stake survives this search. It has not survived a systematic review, and venues outside arXiv were not searched.

## Stake 2: a skill packet between independently trained networks

Nearest found: model fusion via neuron transplantation, and ARM (role-conditioned neuron transplantation). Both transplant between related models where units correspond. The independently-trained query returned one fingerprint-detection protocol, not a transfer method. Queries for weight-space skill transfer returned nothing.

The distillation-into-dormant-units route still reads as different from transplantation in this search. Whether it beats an outside router is Experiment C, not a literature question.

## Supporting pieces

Commit-reveal over a test set: no hits under that phrasing. Bit-exact training reproducibility: no hits under that phrasing. Both are phrase-sensitive and should be re-queried under the names those fields actually use before any sentence outside this record relies on them.

## Disclosure

Searched and written by an AI agent session with human oversight.
