#!/usr/bin/env bash
# Download the platform's primary GGUF into INSTALL_DIR/models.
# Arch is checked against the current runtime BEFORE any download.
# ggml-org inkling2_loop files are refused on the Unsloth pin.
# Optional UD-Q4_K_XL is a second Unsloth download when WANT_Q4=1.
# Does not download the model in dry-run mode.
set -euo pipefail
# shellcheck source=lib.sh
_sdir=$(dirname -- "$0")
_sdir=$(cd -- "$_sdir" && pwd)
. "$_sdir/lib.sh"
load_config
init_paths
detect_platform
require_confirmed_platform

LOG="$LOG_DIR/download.log"
quant=${INKLING_QUANT:-auto}

repo=""
file=""
sha=""
bytes=0
mmproj=""
mmproj_sha=""

pick_auto() {
  if [ "$INKLING_PLATFORM" = "macos-arm64" ]; then
    repo=$HF_REPO_UNSLOTH
    file=$UNSLOTH_Q8_FILE
    sha=$UNSLOTH_Q8_SHA256
    bytes=$UNSLOTH_Q8_BYTES
    mmproj=$UNSLOTH_MMPROJ_FILE
    mmproj_sha=$UNSLOTH_MMPROJ_SHA256
  else
    repo=$HF_REPO_UNSLOTH
    file=$UNSLOTH_IQ2_FILE
    sha=$UNSLOTH_IQ2_SHA256
    bytes=$UNSLOTH_IQ2_BYTES
    mmproj=$UNSLOTH_MMPROJ_FILE
    mmproj_sha=$UNSLOTH_MMPROJ_SHA256
  fi
}

case "$quant" in
  auto|ud-q4) pick_auto ;;
  ud-q8)
    repo=$HF_REPO_UNSLOTH; file=$UNSLOTH_Q8_FILE; sha=$UNSLOTH_Q8_SHA256; bytes=$UNSLOTH_Q8_BYTES
    mmproj=$UNSLOTH_MMPROJ_FILE; mmproj_sha=$UNSLOTH_MMPROJ_SHA256
    ;;
  ggml-q8)
    repo=$HF_REPO_GGML; file=$GGML_Q8_FILE; sha=$GGML_Q8_SHA256; bytes=$GGML_Q8_BYTES
    mmproj=$GGML_MMPROJ_Q8_FILE; mmproj_sha=$GGML_MMPROJ_Q8_SHA256
    ;;
  bf16)
    repo=$HF_REPO_GGML; file=$GGML_BF16_FILE; sha=$GGML_BF16_SHA256; bytes=$GGML_BF16_BYTES
    mmproj=$GGML_MMPROJ_Q8_FILE; mmproj_sha=$GGML_MMPROJ_Q8_SHA256
    log_to "$LOG" "WARN: BF16 is optional, NOT the default, and its header is inkling2_loop (needs the opt-in upstream build). See README."
    ;;
  iq4)
    repo=$HF_REPO_GGML; file=$GGML_IQ4_FILE; sha=$GGML_IQ4_SHA256; bytes=$GGML_IQ4_BYTES
    mmproj=$GGML_MMPROJ_Q8_FILE; mmproj_sha=$GGML_MMPROJ_Q8_SHA256
    ;;
  iq2)
    repo=$HF_REPO_UNSLOTH; file=$UNSLOTH_IQ2_FILE; sha=$UNSLOTH_IQ2_SHA256; bytes=$UNSLOTH_IQ2_BYTES
    mmproj=$UNSLOTH_MMPROJ_FILE; mmproj_sha=$UNSLOTH_MMPROJ_SHA256
    ;;
  *)
    die "unknown INKLING_QUANT=$quant"
    ;;
esac

# Arch gate BEFORE any download (proof HIGH). Uses the known-header table
# (Unsloth UD = inkling2; ggml-org Q8_0/BF16/IQ4_NL = inkling2_loop).
assert_arch_supported_on_current_runtime "$file"
if want_q4 || [ "$quant" = "ud-q4" ]; then
  assert_arch_supported_on_current_runtime "$UNSLOTH_Q4_FILE"
fi

if [ "$quant" = "bf16" ] && [ "${INKLING_I_ACCEPT_BF16_RISK:-0}" != "1" ]; then
  die "BF16 (~$(bytes_to_gib "$GGML_BF16_BYTES") GiB) is not the default. Its GGUF arch is inkling2_loop, so it also needs INKLING_INSTALL_MODE=upstream (UNVERIFIED). On 64 GB it may exceed a comfortable Metal working set with long context (ESTIMATE; see README). Set INKLING_I_ACCEPT_BF16_RISK=1 only if the owner explicitly wants this file after the upstream build is in place. iogpu.wired_limit_mb is an owner decision (sudo)."
fi

log_to "$LOG" "download plan repo=$repo file=$file arch=$(known_gguf_arch "$file") bytes=$bytes sha=$sha vision=$(want_vision && echo 1 || echo 0) want_q4=$(want_q4 && echo 1 || echo 0)"

if is_dry_run; then
  printf 'DRY-RUN: would refuse any file whose arch is not supported on the current runtime (pin=%s supports inkling2 only; inkling2_loop needs INKLING_INSTALL_MODE=upstream)\n' "$LLAMA_RELEASE_TAG"
  printf 'DRY-RUN: would download %s %s -> %s (%s bytes, arch %s)\n' "$repo" "$file" "$MODELS_DIR/$file" "$bytes" "$(known_gguf_arch "$file")"
  if want_q4 || [ "$quant" = "ud-q4" ]; then
    printf 'DRY-RUN: would also download optional Q4 %s %s -> %s (%s bytes, sha %s, arch %s)\n' \
      "$HF_REPO_UNSLOTH" "$UNSLOTH_Q4_FILE" "$MODELS_DIR/$UNSLOTH_Q4_FILE" "$UNSLOTH_Q4_BYTES" "$UNSLOTH_Q4_SHA256" "$(known_gguf_arch "$UNSLOTH_Q4_FILE")"
  else
    printf 'DRY-RUN: WANT_Q4=0; not downloading optional UD-Q4_K_XL\n'
  fi
  if want_vision; then
    printf 'DRY-RUN: would also download opt-in mmproj %s %s\n' "$repo" "$mmproj"
  else
    printf 'DRY-RUN: text-only default (INKLING_USE_VISION not set); omitting mmproj; would clear stale active-mmproj.txt\n'
  fi
  exit 0
fi

[ -x "$VENV_DIR/bin/python" ] || die "venv missing. Run 10-install.sh first."

# Clear stale verify/loadcheck/mmproj state when the primary file changes.
prev=""
if [ -f "$RESULTS_DIR/active-file.txt" ]; then
  prev=$(cat "$RESULTS_DIR/active-file.txt")
fi
if [ "$prev" != "$file" ]; then
  log_to "$LOG" "primary file changing from '${prev:-none}' to $file; clearing stale verify/loadcheck/mmproj markers"
  clear_stale_gate_state
fi
if ! want_vision; then
  rm -f "$RESULTS_DIR/active-mmproj.txt" "$RESULTS_DIR/active-mmproj-sha256.txt"
fi

hf_download() {
  local r=$1 f=$2
  if [ -x "$VENV_DIR/bin/hf" ]; then
    HF_HOME="$HF_HOME" "$VENV_DIR/bin/hf" download "$r" "$f" --local-dir "$MODELS_DIR"
  else
    HF_HOME="$HF_HOME" "$VENV_DIR/bin/python" -c "
import sys
from huggingface_hub import hf_hub_download
hf_hub_download(repo_id=sys.argv[1], filename=sys.argv[2], local_dir=sys.argv[3])
" "$r" "$f" "$MODELS_DIR"
  fi
}

# huggingface_hub current CLI is `hf download` (CITED: Unsloth guide).
hf_download "$repo" "$file"
if want_vision; then
  hf_download "$repo" "$mmproj"
fi

[ -f "$MODELS_DIR/$file" ] || die "download finished but $MODELS_DIR/$file is missing. STOP and report."
printf '%s\n' "$repo" >"$RESULTS_DIR/active-repo.txt"
printf '%s\n' "$file" >"$RESULTS_DIR/active-file.txt"
printf '%s\n' "$sha" >"$RESULTS_DIR/active-sha256.txt"
printf '%s\n' "$bytes" >"$RESULTS_DIR/active-bytes.txt"
# A new download is not yet SHA-verified for this SHA; 30-verify.sh must run.
rm -f "$RESULTS_DIR/verify-status.txt" "$RESULTS_DIR/loadcheck-status.txt"
if want_vision; then
  printf '%s\n' "$mmproj" >"$RESULTS_DIR/active-mmproj.txt"
  printf '%s\n' "$mmproj_sha" >"$RESULTS_DIR/active-mmproj-sha256.txt"
else
  rm -f "$RESULTS_DIR/active-mmproj.txt" "$RESULTS_DIR/active-mmproj-sha256.txt"
fi
if want_q4 || [ "$quant" = "ud-q4" ]; then
  log_to "$LOG" "optional Q4 download $HF_REPO_UNSLOTH $UNSLOTH_Q4_FILE"
  hf_download "$HF_REPO_UNSLOTH" "$UNSLOTH_Q4_FILE"
  [ -f "$MODELS_DIR/$UNSLOTH_Q4_FILE" ] || die "Q4 download finished but $MODELS_DIR/$UNSLOTH_Q4_FILE is missing. Report and retry; the 8-bit default was already recorded."
  printf '%s\n' "$HF_REPO_UNSLOTH" >"$RESULTS_DIR/q4-repo.txt"
  printf '%s\n' "$UNSLOTH_Q4_FILE" >"$RESULTS_DIR/q4-file.txt"
  printf '%s\n' "$UNSLOTH_Q4_SHA256" >"$RESULTS_DIR/q4-sha256.txt"
  printf '%s\n' "$UNSLOTH_Q4_BYTES" >"$RESULTS_DIR/q4-bytes.txt"
  rm -f "$RESULTS_DIR/q4-loadcheck-status.txt"
  # Drop a previous verified marker only if we re-downloaded; 30-verify rewrites it.
  log_to "$LOG" "optional Q4 recorded $MODELS_DIR/$UNSLOTH_Q4_FILE"
else
  log_to "$LOG" "WANT_Q4=0; skipping optional UD-Q4_K_XL download"
fi

log_to "$LOG" "download PASSED file=$MODELS_DIR/$file"
