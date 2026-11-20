# Inkling 2 Mini — local setup for the owner's agents

Agent-facing package so a local coding agent can install and run Thinking Machines' **Inkling 2 Mini** (looped MoE transformer, Apache-2.0) on:

1. **Primary:** MacBook Pro **M1 Max, 64 GB** unified memory (macOS, Metal).
2. **Secondary:** ASUS Zenbook **RTX 3080 Laptop (8 GB VRAM), 32 GB RAM, WSL2 Ubuntu**, llama.cpp CUDA with MoE expert CPU offload.

The 32 GB Mac branch was **dropped** (owner, 2026-11-20 4:26 PM CT). Do not invent a Q4 path for that machine.

Everything lives under **`~/inkling2-mini`** (`INKLING_INSTALL_DIR` overrides it). Scripts are idempotent POSIX bash, log under `$INSTALL_DIR/logs`, and write results under `$INSTALL_DIR/results`. If anything fails: **STOP and report to the owner** with the log. Do not improvise another model, quant, or llama.cpp build. The only documented retry on the pin is the **optional** Unsloth `UD-Q4_K_XL` when `WANT_Q4=1`. ggml-org files are **not** an automatic fallback.

---

## Facts table

Every concrete number below is either **CONFIRMED** against a primary source opened while writing this package or against `/workspace/handoffs/inkling2mini-facts.md` (revised 16:29 CT, 2026-11-20), or marked **UNVERIFIED**. Conflicts are called out, not silently picked.

| Fact | Value | Source | Status |
|------|-------|--------|--------|
| Model | Inkling 2 Mini, Apache-2.0, looped MoE, multimodal | [TML blog](https://thinkingmachines.ai/news/inkling-2-mini), [Unsloth guide](https://unsloth.ai/docs/models/inkling-2-mini), [HF card](https://huggingface.co/thinkingmachines/Inkling-2-Mini) | CONFIRMED |
| Parameter count | Unsloth / TML blog / facts file: **26.4B** total, **5.4B** effective active with 3 loop passes. The TML card embedded in the Unsloth GGUF README also says **26.2B**, **3.4B** active (plus ~1.0B per extra pass → 5.4B). | [Unsloth guide](https://unsloth.ai/docs/models/inkling-2-mini), [TML blog](https://thinkingmachines.ai/news/inkling-2-mini), [HF GGUF README](https://huggingface.co/unsloth/Inkling-2-Mini-GGUF) | **CONFLICT** (26.4B vs 26.2B / 3.4B). Package uses “26.4B MoE, 5.4B effective active” as the public wording and records the card’s 26.2B/3.4B next to it. |
| Loop schedule | 24 physical layers; layers 6–17 run 3×; 48 layer visits/token; each pass keeps its own KV | [config.json](https://huggingface.co/thinkingmachines/Inkling-2-Mini/raw/main/config.json), [HF blog](https://huggingface.co/blog/inkling2mini), [ggml-org README](https://huggingface.co/ggml-org/Inkling-2-Mini-GGUF) | CONFIRMED |
| Max context | **1,048,576** (`text_config.model_max_length` / card “up to 1M”) | [config.json](https://huggingface.co/thinkingmachines/Inkling-2-Mini/raw/main/config.json), [HF card](https://huggingface.co/thinkingmachines/Inkling-2-Mini) | CONFIRMED |
| Default ctx | **32768** | [Unsloth llama.cpp example](https://unsloth.ai/docs/models/inkling-2-mini) | CONFIRMED |
| Long-ctx profile | **131072**, opt-in (`INKLING_CTX_PROFILE=long`), load-checked, not the default | facts file derivation; not in the Unsloth example | **UNVERIFIED** at runtime |
| Sampling | `--temp 1.0 --top-p 1.0 --top-k 0 --min-p 0.0`, `--jinja` | [Unsloth guide](https://unsloth.ai/docs/models/inkling-2-mini) | CONFIRMED |
| Repeat penalty / thinking flags | not listed in the Inkling llama.cpp guide | Unsloth guide, HF card (reasoning effort is described, not as a llama.cpp flag we verified) | **UNVERIFIED** |
| Heads / KV | 24 attention heads, **8** KV heads, head_dim **128**, sliding window **1024** on 20 local layers | [config.json](https://huggingface.co/thinkingmachines/Inkling-2-Mini/raw/main/config.json) | CONFIRMED |
| Primary GGUF repo | `unsloth/Inkling-2-Mini-GGUF` | [Unsloth post](https://x.com/UnslothAI/status/2123873656069877899), [guide](https://unsloth.ai/docs/models/inkling-2-mini), [HF tree](https://huggingface.co/api/models/unsloth/Inkling-2-Mini-GGUF/tree/main) | CONFIRMED |
| Mac default weights | `Inkling-2-Mini-UD-Q8_K_XL.gguf`, **22,867,451,616** bytes (**21.30 GiB**), SHA-256 `dfb04bf37bee457f98800989dedf93ec442ede8636dbea9433992f1e527e9a41`. GGUF arch **`inkling2`** (pin-compatible). | [HF tree API](https://huggingface.co/api/models/unsloth/Inkling-2-Mini-GGUF/tree/main), facts file, proof header peek | CONFIRMED |
| Optional 4-bit (fast iteration, off by default) | `Inkling-2-Mini-UD-Q4_K_XL.gguf`, **17,629,759,456** bytes (**16.42 GiB**), SHA-256 `e62d463c135ffe283df8d94b279a96ca145ac128b52ce854478613045bf4de15`. Arch **`inkling2`**. Set `WANT_Q4=1` or `INKLING_WANT_Q4=1` to download; `INKLING_USE_Q4=1` / `INKLING_QUANT=ud-q4` to serve it after its load gate PASSes. | facts file §1.1, HF tree API, proof (size + SHA + arch) | CONFIRMED |
| ggml-org Q8_0 / BF16 / IQ4_NL | `Inkling-2-Mini-Q8_0.gguf` **27,820,099,264** B (25.91 GiB) SHA `d57542f8aea5d7639beba5fc4ae7f584754916f63ac5d5a69328c27f652f45da`; BF16 **52,226,509,504** B (48.64 GiB) SHA `7074c9762e6769a608c7b23960a7fd2444880b1174a3910149749f6d01389aec`; IQ4_NL **17,627,940,768** B SHA `cbdf3fa9dc50a4124977980f37da4f1fa764b0cfe800d275cd43d26ce2a81af4`. All three declare arch **`inkling2_loop`**. **Not an automatic fallback.** They need the opt-in upstream build at `29b52d39` (UNVERIFIED). BF16 is also **not** the default on memory grounds. | HF tree; Q8_0 arch: proof range-read; BF16 and IQ4_NL arch: this session, HTTP Range 8 MiB, `general.architecture` at offset 64 | CONFIRMED files/SHAs/arch; load on upstream **UNVERIFIED** |
| Unsloth mmproj-F16 | `mmproj-F16.gguf`, 639,348,160 bytes, SHA-256 `3bff75ffeb2d6e0371ba7bd42e30d26a7d98aea681fa44b03b5a20891cfa2c5f` | HF tree, Unsloth guide (~639 MB) | CONFIRMED |
| Download CLI | `hf download` (current `huggingface_hub` CLI) | Unsloth guide | CONFIRMED |
| Pinned llama.cpp | Unsloth fork release **`b12568-mix-8eebad4`**. Upstream “is not in llama.cpp yet” was the guide wording the same day; see conflict row. | [Unsloth guide](https://unsloth.ai/docs/models/inkling-2-mini), [release](https://github.com/unslothai/llama.cpp/releases/tag/b12568-mix-8eebad4) | CONFIRMED pin |
| macOS prebuilt | `llama-b12568-mix-8eebad4-bin-macos-arm64.tar.gz`, 13,005,617 bytes, SHA-256 `65e6e3b1d0b98e95d3229301eabda9d1a139eac9d96e5f3be63eafd4ee0dd311`; extract with `--strip-components=1` | [Release API](https://api.github.com/repos/unslothai/llama.cpp/releases/tags/b12568-mix-8eebad4), `llama-prebuilt-sha256.json` | CONFIRMED |
| WSL CUDA 12 prebuilt | `app-b12568-mix-8eebad4-linux-x64-cuda12-portable.tar.gz`, 469,831,891 bytes, SHA-256 `e6d6c965e1cd05a510b5594c5682fa535dfb1604574ee1e359d4126b19387e96`; extract **without** strip | same | CONFIRMED |
| Windows CUDA 12 zip (native, not the WSL script path) | `app-b12568-mix-8eebad4-windows-x64-cuda12-portable.zip`, 465,700,911 bytes, SHA-256 `721c45b86606201a233ad94f32aec4edff0abfd33a3d310b93bda28044f39baa` | same | CONFIRMED |
| Source-build tarball | `llama.cpp-source-b12568-mix-8eebad4.tar.gz`, SHA-256 `f9582f91fd09caac41389575ea4221ae515095068c5ac8222f0a3beb04c768c2`, `source_commit` `b9b9c0345715dc76ff8f874de3529b8a51251ee9` | same sha256 manifest | CONFIRMED |
| Git tag vs source commit | GitHub tag `b12568-mix-8eebad4` object SHA `d20fe00659286081a3e96efd800c3706a88155ea` **differs** from the prebuilt `source_commit` above. Prefer the **release source tarball**, not `git checkout` of the tag alone. | GitHub git refs API vs sha256 manifest | CONFIRMED discrepancy |
| Metal | Enabled by default on macOS; `-DGGML_CUDA=OFF` for a Mac source build; runtime `-ngl 0` disables GPU | [build.md](https://raw.githubusercontent.com/ggml-org/llama.cpp/master/docs/build.md) | CONFIRMED |
| Full offload flag | `--n-gpu-layers 99` / `-ngl 99` | Unsloth serve example | CONFIRMED |
| Homebrew `llama.cpp` | **v1.0.0**, tag `v1.0.0-b12359-b1b770d`, revision `b1b770d90d94cad9e9ea5b993bdbc383a522fb28` | [formula JSON](https://formulae.brew.sh/api/formula/llama.cpp.json) | CONFIRMED |
| Homebrew usable for Mini? | **No, not today.** `b12359` predates PR #32694. Do not `brew install llama.cpp` for this package. Future route only once brew’s version is **≥ the first upstream tag that contains #32694**. | formula JSON + PR API | CONFIRMED (not sufficient now) |
| PR **#32694** “Inkling 2 Mini” (pcuenca) | **Merged** 2026-11-20T22:01:08Z (4:01 PM CT), merge commit `29b52d398b294509746ec0a3f28948a3107c0213`, `inkling2_loop` support for ggml-org GGUFs | [PR API](https://api.github.com/repos/ggml-org/llama.cpp/pulls/32694) | CONFIRMED |
| PR **#32695** “model: Inkling-2-Mini - looped arch” (danielhanchen) | Still **open, draft, not merged** as of 2026-11-20 4:30 PM CT | [PR API](https://api.github.com/repos/ggml-org/llama.cpp/pulls/32695) | CONFIRMED |
| First upstream **release tag** containing #32694 | **None yet** as of 4:49 PM CT. Latest tags checked: **b12596** (2026-11-20T22:43:55Z) and **b12591** (22:30Z), both still **behind** `29b52d39`. `master` has the merge. | [releases API](https://api.github.com/repos/ggml-org/llama.cpp/releases), proof (b12596/b12591), this session | CONFIRMED (no tag yet) |
| GGUF arch vs this pin | Pinned `b12568-mix-8eebad4` source only knows **`inkling2`** (Unsloth UD files). ggml-org files declare **`inkling2_loop`** and **cannot load on the pin**. | proof pre-revision notes on zip `ca19cb81`; this session’s range peeks | CONFIRMED |
| Unsloth UD `blk.24` report | The same UD-Q8_K_XL SHA was reported to fail with `tensor 'blk.24.attn_q.weight' not found` (`inkling2.block_count = 48`, physical `blk.0–23`). That failure was on **older** binaries (`b12540-mix-c4017f9` and similar), **not** this pin. The load gate still runs, because this pin has not been execution-tested on the owner’s Mac in this package. | [comment](https://github.com/ggml-org/llama.cpp/pull/32695#issuecomment-7051202749), proof notes | CONFIRMED for those older binaries; load on `b12568-mix-8eebad4` still **UNVERIFIED** until `35-loadcheck.sh` runs |
| Caches | `HF_HOME`, `HUGGINGFACE_HUB_CACHE`, `LLAMA_CACHE`, and `PIP_CACHE_DIR` are pointed under `$INSTALL_DIR/cache` | package policy (proof L5) | CONFIRMED in `lib.sh` |
| Zenbook quant | `Inkling-2-Mini-UD-IQ2_XXS.gguf`, 8,486,236,352 bytes (**7.90 GiB**), SHA-256 `4fe958f73a667d8082f911a4347e52bc34696a7816cf3d5b9f7c8a81d5c5ceaa` | HF tree | CONFIRMED file; **UNVERIFIED** as tested on the 3080 |
| Zenbook ctx | `8192` in the facts-file synthesis | facts file; Unsloth only says “reduce ctx if memory limited” | **UNVERIFIED** optimal value |
| MoE CPU offload flags | `-ot/--override-tensor`, `-cmoe/--cpu-moe`, `-ncmoe/--n-cpu-moe N` exist in llama.cpp CLI (and in the pinned tag’s `arg.cpp`). Pattern `-ot ".ffn_.*_exps.=CPU"` is from a general Unsloth MoE tutorial, **not** the Inkling guide. | [cli README](https://github.com/ggml-org/llama.cpp/blob/HEAD/tools/cli/README.md), pinned `common/arg.cpp`, [Cogito tutorial](https://unsloth.ai/docs/models/tutorials/cogito-v2-how-to-run-locally) | Flags CONFIRMED; Inkling-on-3080 combo **UNVERIFIED** |
| `--n-cpu-moe` layer index vs looped 24/48 | unknown | — | **UNVERIFIED** |
| `/health` | `GET /health` and `/v1/health`; ready body `{"status": "ok" }` | [llama.cpp server README (upstream HEAD)](https://github.com/ggml-org/llama.cpp/blob/HEAD/tools/server/README.md) | CONFIRMED on upstream docs; presence in this exact prebuilt **not separately tested** |
| llama-bench | `-pg 512,128` (pp512 + tg128) | [llama-bench README](https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md) | CONFIRMED flag; whether `llama-bench` is inside the macOS/CUDA prebuilt **UNVERIFIED** until install |
| MLX | Only in **mlx-lm PR #2086** (open draft). PyPI **v0.32.2** lacks Inkling. Pin commit **`0c4c99192230f1943dd468d297f0b8a64ae7b7c2`** (PR head, repo `jundot/mlx-lm`). 4-bit: `mlx-community/Inkling-2-Mini-4bit` (~17.31 GiB, 4 shards, SHAs in `config.env`). Native `thinkingmachines/Inkling-2-Mini` weights (HF lfs, this session): `model-00001-of-00001.safetensors` 19,526,019,168 B SHA `65e60f51aa1284d4fb022584908c315270334d991828bb774af60584523539d1`; `mtp.safetensors` 635,801,416 B SHA `7c3b651317f01f73bcf4e1dceba66ef8b7e1a1eac6bc171e882e690a4b10a1d2`; `tokenizer.json` 26,178,678 B SHA `7f332727f9a3f093dd452a39cc978e6757627e5dad1b0673aa4e75174f236dd6`. | [PR #2086](https://github.com/ml-explore/mlx-lm/pull/2086), [community README](https://huggingface.co/mlx-community/Inkling-2-Mini-4bit), HF tree API, `mlx-native-sha256.txt` | CONFIRMED as experimental / unmerged; native SHAs CONFIRMED from HF lfs.oid |
| Speed / VRAM use on either machine | not measured in this package | — | **UNVERIFIED** until 50-bench.sh runs on the machine |
| `iogpu.wired_limit_mb` | raises the Metal wired cap; **does not add RAM**; requires **sudo** | [MLX set_wired_limit doc](https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.set_wired_limit.html) | CONFIRMED as a sysctl; example values are third-party only — **owner decision**, never applied by these scripts |
| Facts file at write time | `/workspace/handoffs/inkling2mini-facts.md` **existed** (revised 16:29 CT). Tooling file `/workspace/handoffs/inkling-tooling.md` existed (16:29 CT). | — | CONFIRMED |

### Conflict resolution: PR #32694 vs #32695

The facts file summary still said “looped Mini in upstream is draft PR **#32695**, not merged.” The tooling file said upstream **merged** `inkling2_loop` in PR **#32694**. Both PRs were opened on the API:

- **#32694** is a different PR (author pcuenca, title “Inkling 2 Mini”). It **merged** into `ggml-org/llama.cpp` at **2026-11-20T22:01:08Z** (4:01 PM CT), commit `29b52d398b294509746ec0a3f28948a3107c0213`.
- **#32695** (author danielhanchen / Unsloth, title “model: Inkling-2-Mini - looped arch”) remains an **open draft**.

There is **no release tag yet** that contains #32694 (latest checked at 4:49 PM CT: `b12596` / `b12591`, both behind `29b52d39`). Homebrew is still **v1.0.0 / b12359**. Unsloth’s guide line “not in upstream llama.cpp yet” is **stale relative to `master`**, and **still true of every tagged release and of Homebrew**.

**Package choice (per nizam):** keep **Unsloth `b12568-mix-8eebad4` as the pinned primary**. Document upstream `master` / the first future tag that contains `29b52d39` as a **CITED alternative**, not as this package’s pin. Do not use brew llama.cpp until brew is ≥ that future tag.

### Why UD-Q8_K_XL is the default — and why ggml-org Q8_0 is not a fallback on this pin

**Primary remains Unsloth `UD-Q8_K_XL`.** It is the Unsloth “full precision / lossless” GGUF, the documented path with this exact pin, arch **`inkling2`**, 21.30 GiB, and it fits 64 GB at the recommended 32k context under the estimates below.

The `blk.24.attn_q.weight` failure in [PR #32695 comment](https://github.com/ggml-org/llama.cpp/pull/32695#issuecomment-7051202749) used this same UD-Q8_K_XL SHA, but on **older** binaries (`b12540-mix-c4017f9` and similar), **not** `b12568-mix-8eebad4`. That pin’s source only implements **`inkling2`**, which is what the Unsloth UD files declare. ggml-org `Q8_0`, `BF16`, and `IQ4_NL` declare **`inkling2_loop`** and **cannot load on the pin**. This was found in grk-proof’s pre-revision notes on zip `ca19cb81`; BF16/IQ4_NL headers were re-checked this session with an HTTP range read.

`20-download.sh` therefore checks the file’s arch **before any download**. `35-loadcheck.sh` still runs before smoke/serve (this pin has not been execution-tested here). If **UD-Q8_K_XL** fails the load gate:

1. If `WANT_Q4=1` (or `INKLING_QUANT=ud-q4`) and `UD-Q4_K_XL` is present and verified, **try that** (same `inkling2` family).
2. Otherwise **STOP and report**. There is **no** automatic ggml-org fallback.
3. Offer an **opt-in, never automatic, UNVERIFIED** path: `INKLING_INSTALL_MODE=upstream` to build ggml-org llama.cpp from commit `29b52d398b294509746ec0a3f28948a3107c0213` (PR #32694 merge) for `inkling2_loop` files. If cmake / a C++ compiler / (WSL) CUDA toolkit are missing: **STOP and ask** the owner. The source tarball SHA is not in the facts file. If `UPSTREAM_SOURCE_SHA256` is set, it is required. If it is empty, the first opt-in fetch is **trust-on-first-use**: the script records the SHA-256 under `$INSTALL_DIR/results/upstream-source-sha256.txt` (UNVERIFIED) and later fetches must match. Independently confirm that hash; do not invent one.

If optional Q4 fails but Q8 passed: report the Q4 failure and **continue with 8-bit**. Do not stop the whole setup.

**SPECULATION (do not act on it):** a `block_count` of 48 on a file that only stores `blk.0–23` may be metadata written for unrolled depth (24 unique blocks, looped to 48 visits). The agent must not “fix” GGUFs or loaders on that hypothesis.

### 64 GB quality vs memory (ESTIMATE)

CITED inputs: 8 KV heads, head_dim 128, 48 visits with their own KV, local window 1024 on 20 physical layers, 4 global physical layers → 8 global visits under 3 passes (derivation of the hybrid layout is **UNVERIFIED** against llama.cpp’s actual cache). KV dtype assumed f16 (**UNVERIFIED**). Per-visit K+V per token: `2 × 8 × 128 × 2 = 4096` bytes.

At **128k** (`--ctx-size 131072`):

- Hybrid (8 global × 128k + 40 local × 1024) = 4,462,739,456 B ≈ **4.156 GiB** KV (**UNVERIFIED** which formula llama.cpp uses).
- Naive (48 visits × full 128k) ≈ **24.0 GiB** KV (**UNVERIFIED**).

At Unsloth’s default **32k**, **do not scale the local term** (the 1024-token window stays 1024). Rechecked (proof L2, and again here): `8 × 32768 × 4096 + 40 × 1024 × 4096 = 1,241,513,984` bytes = **1.156 GiB** hybrid. Naive at 32k is **6.0 GiB** (that one does scale). Same caveats, **ESTIMATE**.

| Weights | Disk | + hybrid KV @ 32k | + hybrid KV @ 128k | + mmproj-F16 (0.60 GiB) @ 128k |
|---------|------|-------------------|--------------------|-------------------------------|
| UD-Q8_K_XL | 21.30 | 22.46 | 25.46 | 26.06 |
| UD-Q4_K_XL | 16.42 | 17.58 | 20.58 | 21.18 |
| ggml Q8_0 (upstream only) | 25.91 | 27.07 | 30.07 | 30.67 |
| ggml BF16 (upstream only) | 48.64 | 49.80 | 52.80 | 53.40 |

Figures are **GiB, ESTIMATE**, weights CITED, KV **UNVERIFIED**. Q8 and Q4 **fit 64 GB unified RAM** on this arithmetic if the hybrid formula is right and the OS/compute overhead is modest. **BF16 is not the default** and **will not load on the pin** (`inkling2_loop`). Even with the upstream build, ~49.80 GiB + OS and Metal compute buffers can brush the GPU **working set**. Naive-KV BF16 (~48.64+24) would **not** fit. Scripts refuse ggml-org files unless `INKLING_INSTALL_MODE=upstream`, and still will not download BF16 unless `INKLING_QUANT=bf16` and `INKLING_I_ACCEPT_BF16_RISK=1`. `iogpu.wired_limit_mb` is documented only as an **owner decision** (needs sudo). These scripts never set it. Both Q8+Q4 on disk: 21.30+16.42 = **37.72 GiB**, plus the 8 GiB headroom and the llama tarball.

---

## Layout

```
this package/          (copy it onto the Mac or into WSL)
  README.md
  config.env           # repo ids, filenames, SHA-256s, ctx, sampling
  lib.sh
  00-preflight.sh
  10-install.sh
  20-download.sh
  30-verify.sh
  35-loadcheck.sh      # mandatory load gate
  40-smoke.sh
  50-bench.sh
  serve.sh
  run-all.sh
  60-mlx-setup.sh      # optional, experimental, Mac only
  mlx-generate.sh

~/inkling2-mini/       # INSTALL_DIR (created at run time)
  logs/  results/  models/  downloads/  venv/  llama.cpp/
```

---

## How to run (Mac, default)

From this directory, on the owner's Mac:

```bash
export INKLING_INSTALL_DIR="${INKLING_INSTALL_DIR:-$HOME/inkling2-mini}"
./run-all.sh
./serve.sh
```

Or step by step: `00-preflight.sh` → `10-install.sh` → `20-download.sh` → `30-verify.sh` → `35-loadcheck.sh` → `40-smoke.sh` → `50-bench.sh` → `serve.sh`.

Dry-run (prints commands, downloads nothing):

```bash
INKLING_DRY_RUN=1 INKLING_INSTALL_DIR=/tmp/inkling2-mini-dry ./00-preflight.sh
```

Text-only is the default until weight-space work is done (owner, 4:46 PM CT). `serve.sh` / smoke / the load gate do **not** pass `--mmproj` unless `INKLING_USE_VISION=1`, and they clear a stale `active-mmproj.txt` when switching quants or when vision is off. When vision is on, `35-loadcheck.sh` also passes `--mmproj` so the projector is load-checked with the GGUF. When vision is off, the mmproj path is not load-checked (and is not used). The vision path remains **UNVERIFIED** on the owner's machines until that opt-in gate actually runs there.

Optional 4-bit for faster iteration (off by default):

```bash
WANT_Q4=1 ./20-download.sh    # or INKLING_WANT_Q4=1; also set in config.env
INKLING_USE_Q4=1 ./serve.sh   # only after 30-verify.sh and 35-loadcheck.sh PASS for Q4
```

If the Q4 load gate fails, the 8-bit default is left in place.

Long context (UNVERIFIED): `INKLING_CTX_PROFILE=long` before `35-loadcheck.sh`. The gate tries 131072 and, if it OOMs or fails, keeps 32768 and records `long_context=FAIL`. Do not raise ctx toward 1,048,576 without a new owner decision.

---

## How to run (Zenbook / WSL2, secondary)

Same scripts. Preflight expects WSL + `nvidia-smi` (driver from **Windows**, not apt). Default weights: **UD-IQ2_XXS**, ctx **8192** (UNVERIFIED), `-ngl 99 -ot ".ffn_.*_exps.=CPU"`. Speed and VRAM split are **UNVERIFIED** until measured.

If **UD-IQ2_XXS** fails to load, **STOP** and report. Do not silently switch to ggml-org Q8_0 (wrong arch on this pin) or to IQ1_S. `UD-IQ1_S` (7.23 GiB) is a **documented** tighter-VRAM option in the facts file, but it is an owner decision, not an automatic fallback. Optional `UD-Q4_K_XL` is **not recommended** on 8 GB VRAM (16.42 GiB file; preflight warns).

A Windows-native unzip command for the CUDA 12 portable zip is in the facts file if someone is not using WSL; these bash scripts target WSL.

---

## Install details

**Preferred:** download the Unsloth **prebuilt** for the platform into `$INSTALL_DIR/llama.cpp` and verify its SHA-256 (tarball download is resumable: `curl -C -`). Then create `$INSTALL_DIR/venv` and `pip install -U huggingface_hub` **inside the venv** (existing `python3` on the Mac or WSL; Homebrew is **not** required if Python is already present). Never system-wide pip. Hugging Face and llama.cpp caches are kept under `$INSTALL_DIR/cache` (`HF_HOME`, `LLAMA_CACHE`, `PIP_CACHE_DIR`).

**Source fallback (same pin):** `INKLING_INSTALL_MODE=source` uses the **release source tarball** (`llama.cpp-source-b12568-mix-8eebad4.tar.gz`), not a guessed git checkout. Mac: Metal (default). WSL: `-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86` (3080 / 3080 Ti compute 8.6 is cited in build.md; **3080 Laptop** specifically is **UNVERIFIED** on the NVIDIA page we opened). Source builds on WSL need `cmake`, a compiler, and a CUDA toolkit — **apt/toolkit installs require sudo and the owner's ok**. Prefer the prebuilt.

**Opt-in upstream (UNVERIFIED, never automatic):** `INKLING_INSTALL_MODE=upstream` builds ggml-org llama.cpp at commit `29b52d398b294509746ec0a3f28948a3107c0213` into `$INSTALL_DIR/llama.cpp-upstream`, for `inkling2_loop` files only. If build tools are missing, the script **STOPs and asks**. The source tarball SHA is **not** in the facts file. Set `UPSTREAM_SOURCE_SHA256` to a hash the owner has confirmed, or leave it empty for **trust-on-first-use**: the first fetch records the SHA-256 in `$INSTALL_DIR/results/upstream-source-sha256.txt` (UNVERIFIED) and later fetches must match. Independently confirm that hash. Do not invent one.

**Do not** `brew install llama.cpp` for this model. If brew llama.cpp is already present, leave it alone and do not use it.

`--host 127.0.0.1 --port 8080`. OpenAI-compatible `POST /v1/chat/completions`. Health: `GET /health`.

```bash
curl -sS http://127.0.0.1:8080/health
curl -sS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"inkling-2-mini","messages":[{"role":"user","content":"Hello"}],"temperature":1.0,"top_p":1.0}'
```

Smoke: `/health` must return ok. Architecture grep looks for `inkling2` / `inkling2_loop`. Arithmetic property: the string **`391`** (`17 * 23`). The completion probe uses **temp 0** as a package policy so the check is less noisy; recommended **chat** sampling remains temp 1.0. Do not treat a missing `391` as a license to swap models.

---

## Optional MLX (Mac, experimental)

Inkling is **not** in released mlx-lm (**v0.32.2**). Support is **only** in open draft [PR #2086](https://github.com/ml-explore/mlx-lm/pull/2086). This package will install from the PR head **pinned to** `0c4c99192230f1943dd468d297f0b8a64ae7b7c2` (`jundot/mlx-lm`) inside `$INSTALL_DIR/venv`, and will download `mlx-community/Inkling-2-Mini-4bit` (SHAs in `config.env`). Native `thinkingmachines/Inkling-2-Mini` is available via `INKLING_MLX_WEIGHTS=native`; `60-mlx-setup.sh` downloads it under `$INSTALL_DIR/mlx-models` and verifies the LFS SHA-256s in `config.env` / `mlx-native-sha256.txt`.

This route is **off** until the owner agrees:

```bash
INKLING_ENABLE_MLX=1 ./60-mlx-setup.sh
INKLING_ENABLE_MLX=1 ./mlx-generate.sh "The secret to baking a good cake is" 128
```

If `MLX_LM_COMMIT` were a `<UNVERIFIED: …>` placeholder, the script would refuse. It is filled in from the PR API. The route remains experimental until mlx-lm merges and releases.

---

## Guardrails

- **Mac:** Homebrew installs only where a missing tool is documented (e.g. `python`). No other system changes. **No sudo.**
- **WSL:** apt / CUDA toolkit / `build-essential` / `cmake` / `python3-venv` only if unavoidable, only for a **source** build or a missing Python, and only with the **owner's ok** (they need sudo). The default prebuilt path should not need apt besides an already-present `python3`, `curl`, and `tar`.
- Everything the scripts write is under `INSTALL_DIR` except brew (Mac) or those documented apt exceptions (WSL, not default).
- No sudo in the scripts. `iogpu.wired_limit_mb` is not applied.
- No alternate models, quants, or llama.cpp builds except: (1) optional Unsloth `UD-Q4_K_XL` when `WANT_Q4=1`, used as a load-gate retry only if Q8 fails and Q4 is enabled; (2) an explicit owner-set `INKLING_QUANT` for Unsloth UD files (`ud-q8`, `ud-q4`, `iq2`); (3) `INKLING_INSTALL_MODE=upstream` **only** when the owner opts in for `inkling2_loop` files (`ggml-q8` / `bf16` / `iq4`). Never download or serve an unverified SHA.
- Load and smoke gates are non-interactive (`-st`, stdin from `/dev/null`, a timeout via `timeout` / `gtimeout` / a bash fallback) and must see a non-zero `offloaded N/N layers` GPU count.
- If a step fails: **STOP**, keep the log, report to the owner. Do not keep trying variants.

---

## Troubleshooting

**OOM / Metal “insufficient memory”.** Lower `--ctx-size` (stay at 32768 or below unless the long profile already passed). Do not automatically switch quants. BF16 is the first thing *not* to use here. `iogpu.wired_limit_mb` may raise the Metal wired cap on 64 GB; it needs **sudo**, does not add RAM, and is an **owner decision**. These scripts will not set it. Third-party examples (e.g. ~55296 MiB leaving ~10 GB for the OS) are **not** Apple official.

**`tensor 'blk.24.attn_q.weight' not found`.** Reported on **older** Unsloth binaries (`b12540` etc.) for this same UD-Q8_K_XL SHA, not demonstrated on `b12568-mix-8eebad4`. Stay on the pin. If the load gate fails, try enabled `UD-Q4_K_XL` or STOP. Do **not** fetch ggml-org Q8_0 for the pin.

**`unknown model architecture` / `inkling2_loop`.** The file is a ggml-org GGUF. The pin cannot load it. Stop. If the owner wants those files, use the opt-in upstream build at `29b52d39` (UNVERIFIED) after they approve any missing build tools, and either set `UPSTREAM_SOURCE_SHA256` or accept trust-on-first-use recording of the tarball hash.

**Metal / `GGML_METAL` errors.** Confirm macOS version in the preflight log, confirm `-ngl 99`, try a lower `-ngl` only as a diagnostic to report, not as a new default. Confirm the binary is the Unsloth macOS arm64 prebuilt, not brew.

**WSL: nvidia-smi missing or wrong GPU memory.** Fix the **Windows** driver and WSL GPU passthrough. Do not apt-install a driver in WSL. If `/proc/meminfo` shows far less than 32 GB, inspect `.wslconfig` with the owner (do not edit it yourself).

**CUDA “out of memory” on the 3080.** Keep experts on CPU (`-ot ".ffn_.*_exps.=CPU"`), keep ctx at 8192 or lower, stay on IQ2_XXS. `--cpu-moe` is an equivalent high-level flag if you need to name it in a report. Do not jump to Q4/Q8 on 8 GB VRAM without the owner.

---

## Environment variables

| Variable | Meaning |
|----------|---------|
| `INKLING_INSTALL_DIR` | Install root (default `~/inkling2-mini`) |
| `INKLING_DRY_RUN=1` | Print commands; do not download the model or write a real install |
| `INKLING_QUANT` | `auto` (default), `ud-q8`, `ud-q4`, `iq2`. `ggml-q8` / `bf16` / `iq4` only with `INKLING_INSTALL_MODE=upstream` |
| `INKLING_WANT_Q4=1` / `WANT_Q4=1` | Also download and load-check optional `UD-Q4_K_XL` (off by default) |
| `INKLING_USE_Q4=1` | Serve/smoke/bench the Q4 file (requires its load gate PASS) |
| `INKLING_I_ACCEPT_BF16_RISK=1` | Required if `INKLING_QUANT=bf16` (and the upstream runtime) |
| `INKLING_USE_VISION=1` | Also download/use the F16 (or ggml Q8) mmproj; default is text-only |
| `INKLING_INSTALL_MODE` | `prebuilt` (default), `source` (same pin), or `upstream` (opt-in, UNVERIFIED, `29b52d39`) |
| `UPSTREAM_SOURCE_SHA256` | Optional pin for the opt-in upstream tarball. If unset, the first fetch records the SHA (trust-on-first-use, UNVERIFIED) under `results/`; later fetches must match |
| `INKLING_CTX_PROFILE=long` | Opt-in 131072 on the Mac (UNVERIFIED) |
| `INKLING_ENABLE_MLX=1` | Enable experimental MLX scripts |
| `INKLING_MLX_WEIGHTS` | `4bit` (default) or `native` (SHA-checked) |
| `INKLING_SERVE_BG=1` | `serve.sh` backgrounds the server |
| `INKLING_LLAMA=upstream` | Use the upstream binary tree if it was already built |

---

## Changelog

- **2026-11-20 5:08 PM CT** — Incorporates **grk-proof’s review** of zip `2de8e7b6`. MEDIUM: `35-loadcheck.sh` clears stale loadcheck status at start and writes `status=STOP` (with a reason) on `require_gpu_offload` and every `die` path, so `serve.sh` refuses after a failed re-gate; `run_with_timeout` saves and restores the caller’s errexit state and kills/reaps the watcher sleep (and leftover children). LOW: optional Q4 offload failure marks Q4 `STOP` and continues with 8-bit; smoke fails on a CLI timeout or non-zero exit even if an offload line was printed; removed the vacuous `GPU` device-string warning; load-check `--mmproj` when `INKLING_USE_VISION=1` (otherwise documented as not checked); upstream tarball SHA is trust-on-first-use and recorded on first fetch; `preflight PASSED` is logged once. Stub-binary regressions in `tests/`.

- **2026-11-20 4:46 PM CT** — Owner: optional Unsloth `UD-Q4_K_XL` second download (`WANT_Q4=1`, off by default); 8-bit stays the default; Q4 load-gate failure reports and continues with 8-bit; serve/smoke/bench can select 4-bit; default serve is text-only until weight-space work is done.
- **2026-11-20, same revision, after 4:49 PM CT** — Incorporates **grk-proof’s pre-revision review** of zip `ca19cb81` (`ca19cb81da5f5bf3e6a2f40d7e0b9b1bdcc5389125a770f0e38b6ab2374f7ce2`). HIGH: pre-download arch check; removed automatic ggml-org Q8_0 fallback (arch `inkling2_loop` cannot load on this pin); Q8 fail retries enabled Q4 only, else STOP and offer opt-in upstream build at `29b52d39` (UNVERIFIED, never automatic, stop-and-ask if tools or the tarball SHA are missing); README load-risk story corrected (the `blk.24` failure was on older builds; BF16/IQ4_NL also need the upstream build). MEDIUM: non-interactive load/smoke (`-st`, `/dev/null`, timeout/`gtimeout`/bash fallback); per-SHA verified markers and serve refuses unverified files; both gates assert a non-zero GPU offload; stale `active-mmproj.txt` is cleared on quant switch / text-only. LOW: shellcheck SC1090; hybrid KV @32k corrected to **1.156 GiB**; Homebrew not required unless used; resumable llama tarball (`curl -C -`); HF/llama/pip caches under `~/inkling2-mini`; SHA checks for MLX native weights.

## Sources opened for this package

Unsloth guide and its Markdown; Unsloth and Thinking Machines X posts (`2123873656069877899`, `2123871643797995872`); HF tree APIs for `unsloth/Inkling-2-Mini-GGUF`, `ggml-org/Inkling-2-Mini-GGUF`, `mlx-community/Inkling-2-Mini-4bit`, and `thinkingmachines/Inkling-2-Mini` (native LFS SHAs); `thinkingmachines/Inkling-2-Mini` card and `config.json`; [HF blog](https://huggingface.co/blog/inkling2mini); [TML blog](https://thinkingmachines.ai/news/inkling-2-mini); Unsloth llama.cpp release `b12568-mix-8eebad4` and `llama-prebuilt-sha256.json`; ggml-org PRs #32694 and #32695; mlx-lm PR #2086; Homebrew `llama.cpp` formula JSON; llama.cpp `docs/build.md`, server README, llama-bench README, and the pinned fork’s `common/arg.cpp` / CLI README. HTTP Range peeks of ggml-org BF16 and IQ4_NL. Plus `/workspace/handoffs/inkling2mini-facts.md`, `inkling-tooling.md`, and grk-proof’s pre-revision notes on zip `ca19cb81`.
