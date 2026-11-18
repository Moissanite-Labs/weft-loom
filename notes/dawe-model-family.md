# DAWE model-family choice for a single 4090

Status: `idea`. Not adopted. Nothing here has been measured yet. The measurements will come from the DAWE
reproduction and from [E11c](../experiments/e11c-dawe-closed-form-edit-2026-11/PREREG.md).

**Question.** Which open model family should the DAWE closed-form edit work use on one RTX 4090 (24 GB)?

## Ranking

1. **Qwen 3.5 4B is the top pick.** DAWE itself used it, and its tied input/output embeddings are the edit target
   (the DAWE edit changed 2 tied-embedding rows). It runs at full bf16 in about 8 GB on a 4090 (an 8B in about
   16 GB), so no quantization is needed. Editing quantized weights is unreliable.
2. **Llama 3 8B is second, as the cross-family check.** It has the most weight-editing prior art (ROME, MEMIT) and
   the widest interpretability tool support.
3. **Gemma 2/3 is third.** Gemma Scope gives it the best ready-made inspection tooling, but the 9B is tight in 24 GB.
4. **Mistral 7B works, but its tooling is thinner.** DeepSeek's small distilled models are Qwen or Llama underneath,
   and its MoE models do not fit on one card.

## Open question

There is no solid data yet on how edits carry across harness format changes for any family. The DAWE reproduction
and E11c will measure that.

## Plan

Reproduce DAWE on Qwen 3.5 4B first, then repeat it on Llama 3 8B as the cross-family check.

## Source

From an owner call on 2026-11-18, plus a summary by qalam (an AI agent) from existing knowledge. This is not a
fresh literature review. Reference: [bandr-ai/dawe](https://github.com/bandr-ai/dawe).
