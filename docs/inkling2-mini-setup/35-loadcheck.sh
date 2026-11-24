#!/usr/bin/env bash
# LOAD GATE. Must pass before smoke or serve.
# Loads the active GGUF with the pinned fork at a minimal context for a few
# tokens, non-interactively (-st, stdin /dev/null, timeout).
# If Unsloth UD-Q8_K_XL fails: try UD-Q4_K_XL only if WANT_Q4=1 and it was
# verified. ggml-org Q8_0 is NOT an automatic fallback (inkling2_loop cannot
# load on b12568-mix-8eebad4). If neither UD file loads: STOP and report.
# Optional Q4 is also load-checked when enabled; a Q4-only failure is
# reported and does not stop the 8-bit setup.
set -euo pipefail
# shellcheck source=lib.sh
_sdir=$(dirname -- "$0")
_sdir=$(cd -- "$_sdir" && pwd)
. "$_sdir/lib.sh"
load_config
init_paths
detect_platform
require_confirmed_platform

LOG="$LOG_DIR/loadcheck.log"
STAMP=$(date '+%Y%m%d-%H%M%S')
RAW="$LOG_DIR/loadcheck-$STAMP.log"
STATUS_FILE="$RESULTS_DIR/loadcheck-status.txt"
PROFILE=${INKLING_CTX_PROFILE:-default} # default | long
TIMEOUT_SECS=${LOAD_TIMEOUT:-300}

# write_status_to <file> PASS|FAIL|STOP reason...
write_status_to() {
  local dest=$1 st=$2
  shift 2
  if ! is_dry_run; then
    mkdir -p "$RESULTS_DIR"
    {
      printf 'status=%s\n' "$st"
      printf 'time=%s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
      printf 'file=%s\n' "${ACTIVE_FILE:-}"
      printf 'sha256=%s\n' "${ACTIVE_SHA:-}"
      printf 'repo=%s\n' "${ACTIVE_REPO:-}"
      printf 'profile=%s\n' "$PROFILE"
      printf 'reason=%s\n' "$*"
      printf 'log=%s\n' "${CURRENT_LOG:-$RAW}"
    } >"$dest"
  fi
  log_to "$LOG" "loadcheck $st: $*"
}

# Record status=STOP on any die() from this gate (including lib.sh helpers).
inkling_on_die() {
  if is_dry_run; then
    return 0
  fi
  if [ -n "${STATUS_FILE:-}" ]; then
    write_status_to "$STATUS_FILE" STOP "${1:-unspecified failure}"
  fi
}

looks_like_load_failure() {
  local f=$1
  [ -f "$f" ] || return 1
  grep -Eiq \
    "error loading model|failed to load|wrong number of tensors|unknown model architecture|tensor 'blk\.24|check_tensor_dims: tensor .* not found|failed to load model|error while loading" \
    "$f"
}

try_load() {
  local model=$1
  local ctx=$2
  local this_log=$3
  local bin=""
  local extra=()
  local ngl=$N_GPU_LAYERS
  local rc=1

  CURRENT_LOG=$this_log

  if is_dry_run; then
    printf 'DRY-RUN: would load %q with ctx=%s ngl=%s -st </dev/null timeout=%ss, then assert GPU offload\n' \
      "$model" "$ctx" "$ngl" "$TIMEOUT_SECS"
    if [ "$INKLING_PLATFORM" = "wsl-cuda" ] || [ "$INKLING_PLATFORM" = "linux-cuda" ]; then
      printf 'DRY-RUN: would add -ot %q\n' "$ZENBOOK_OVERRIDE_TENSOR"
    fi
    return 0
  fi

  if bin=$(find_llama_bin llama-cli); then
    extra=(--ctx-size "$ctx" -n 1 -p "Hi" -st --no-display-prompt --verbose
      --temp 0 --top-p 1.0 --top-k 0 --min-p 0.0 -ngl "$ngl")
    if [ "$INKLING_PLATFORM" = "wsl-cuda" ] || [ "$INKLING_PLATFORM" = "linux-cuda" ]; then
      extra+=(-ot "$ZENBOOK_OVERRIDE_TENSOR")
    fi
    if want_vision && [ -f "$RESULTS_DIR/active-mmproj.txt" ]; then
      extra+=(--mmproj "$MODELS_DIR/$(cat "$RESULTS_DIR/active-mmproj.txt")")
    fi
    set +e
    run_with_timeout "$TIMEOUT_SECS" "$bin" -m "$model" "${extra[@]}" </dev/null >"$this_log" 2>&1
    rc=$?
    set -e
  elif bin=$(find_llama_bin llama-server); then
    extra=(--model "$model" --ctx-size "$ctx" -ngl "$ngl" --verbose --host 127.0.0.1 --port "$PORT" --parallel 1)
    if [ "$INKLING_PLATFORM" = "wsl-cuda" ] || [ "$INKLING_PLATFORM" = "linux-cuda" ]; then
      extra+=(-ot "$ZENBOOK_OVERRIDE_TENSOR")
    fi
    if want_vision && [ -f "$RESULTS_DIR/active-mmproj.txt" ]; then
      extra+=(--mmproj "$MODELS_DIR/$(cat "$RESULTS_DIR/active-mmproj.txt")")
    fi
    set +e
    run_with_timeout "$TIMEOUT_SECS" "$bin" "${extra[@]}" </dev/null >"$this_log" 2>&1 &
    pid=$!
    i=0
    rc=1
    while [ "$i" -lt "$TIMEOUT_SECS" ]; do
      if ! kill -0 "$pid" 2>/dev/null; then
        wait "$pid"
        rc=$?
        break
      fi
      if curl -fsS --max-time 2 "http://127.0.0.1:$PORT/health" >>"$this_log" 2>&1; then
        rc=0
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
        break
      fi
      i=$((i + 1))
      sleep 1
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
      rc=1
    fi
    set -e
  else
    die "neither llama-cli nor llama-server found under $LLAMA_DIR. Run 10-install.sh first."
  fi

  if looks_like_load_failure "$this_log"; then
    return 1
  fi
  if [ "${rc:-1}" -ne 0 ]; then
    return 1
  fi
  if ! gpu_offload_ok "$this_log"; then
    return 1
  fi
  return 0
}

require_file_verified() {
  local path=$1 sha=$2
  if is_dry_run; then
    printf 'DRY-RUN: would require verified marker + SHA %s for %q\n' "$sha" "$path"
    return 0
  fi
  if [ ! -f "$RESULTS_DIR/verify-status.txt" ] && [ ! -f "$(verified_marker_path "$sha")" ]; then
    die "no verification record for $path. Run 30-verify.sh first."
  fi
  require_verified_sha "$path" "$sha"
}

if is_dry_run; then
  printf 'DRY-RUN: load gate would use ctx=%s (loadcheck) then optional profile=%s, -st, stdin /dev/null, timeout=%ss, GPU-offload assert\n' \
    "$CTX_SIZE_LOADCHECK" "$PROFILE" "$TIMEOUT_SECS"
  if want_vision; then
    printf 'DRY-RUN: INKLING_USE_VISION=1; would also pass --mmproj to the load gate (vision path is otherwise UNVERIFIED)\n'
  else
    printf 'DRY-RUN: text-only; mmproj is not load-checked (and is not passed to llama-cli/server)\n'
  fi
  printf 'DRY-RUN: primary is the Unsloth UD file for this platform (inkling2). ggml-org Q8_0/BF16/IQ4_NL are inkling2_loop and are NOT an automatic fallback on %s.\n' "$LLAMA_RELEASE_TAG"
  if want_q4 || [ "${INKLING_QUANT:-}" = "ud-q4" ]; then
    printf 'DRY-RUN: WANT_Q4=1; would also SHA-verify and load-check %s. If Q4 fails, report and keep the 8-bit default (do not stop the setup).\n' "$UNSLOTH_Q4_FILE"
    printf 'DRY-RUN: if the primary Unsloth UD file fails the gate, would try UD-Q4_K_XL (enabled) before stopping.\n'
  else
    printf 'DRY-RUN: WANT_Q4=0; if the primary Unsloth UD file fails, STOP (no Q8_0 fallback). Opt-in upstream build at %s is never automatic.\n' "$UPSTREAM_LOOP_MERGE_COMMIT"
  fi
  exit 0
fi

# A failed re-gate must not leave a stale status=PASS (proof M1).
rm -f "$STATUS_FILE" "$RESULTS_DIR/q4-loadcheck-status.txt"

[ -f "$RESULTS_DIR/active-file.txt" ] || die "no active model. Run 20-download.sh and 30-verify.sh first."
ACTIVE_REPO=$(cat "$RESULTS_DIR/active-repo.txt")
ACTIVE_FILE=$(cat "$RESULTS_DIR/active-file.txt")
ACTIVE_SHA=$(cat "$RESULTS_DIR/active-sha256.txt")
MODEL_PATH="$MODELS_DIR/$ACTIVE_FILE"
[ -f "$MODEL_PATH" ] || die "model missing: $MODEL_PATH"
assert_arch_supported_on_current_runtime "$ACTIVE_FILE"
require_file_verified "$MODEL_PATH" "$ACTIVE_SHA"

ctx=$CTX_SIZE_LOADCHECK
attempt_log="$RAW"
primary_ok=0
if try_load "$MODEL_PATH" "$ctx" "$attempt_log"; then
  write_status_to "$STATUS_FILE" PASS "loaded $ACTIVE_FILE at ctx=$ctx"
  primary_ok=1
else
  # No automatic ggml-org Q8_0 fallback (inkling2_loop ≠ pinned inkling2).
  # If optional Q4 is enabled, try that Unsloth UD file (same arch family).
  if [ "$ACTIVE_FILE" = "$UNSLOTH_Q8_FILE" ] && { want_q4 || [ "${INKLING_QUANT:-}" = "ud-q4" ]; } && [ -f "$MODELS_DIR/$UNSLOTH_Q4_FILE" ]; then
    log_to "$LOG" "primary $ACTIVE_FILE failed the load gate; trying enabled UD-Q4_K_XL (same inkling2 arch). ggml-org Q8_0 is not used."
    require_file_verified "$MODELS_DIR/$UNSLOTH_Q4_FILE" "$UNSLOTH_Q4_SHA256"
    attempt_q4="$LOG_DIR/loadcheck-q4-fallback-$STAMP.log"
    if try_load "$MODELS_DIR/$UNSLOTH_Q4_FILE" "$ctx" "$attempt_q4"; then
      ACTIVE_FILE=$UNSLOTH_Q4_FILE
      ACTIVE_SHA=$UNSLOTH_Q4_SHA256
      ACTIVE_REPO=$HF_REPO_UNSLOTH
      MODEL_PATH="$MODELS_DIR/$UNSLOTH_Q4_FILE"
      printf '%s\n' "$ACTIVE_REPO" >"$RESULTS_DIR/active-repo.txt"
      printf '%s\n' "$ACTIVE_FILE" >"$RESULTS_DIR/active-file.txt"
      printf '%s\n' "$ACTIVE_SHA" >"$RESULTS_DIR/active-sha256.txt"
      printf '%s\n' "$UNSLOTH_Q4_BYTES" >"$RESULTS_DIR/active-bytes.txt"
      write_status_to "$STATUS_FILE" PASS "primary UD-Q8_K_XL failed; enabled UD-Q4_K_XL loaded at ctx=$ctx"
      write_status_to "$RESULTS_DIR/q4-loadcheck-status.txt" PASS "loaded $UNSLOTH_Q4_FILE as fallback after Q8 failure"
      primary_ok=1
    else
      write_status_to "$STATUS_FILE" STOP "UD-Q8_K_XL failed and enabled UD-Q4_K_XL also failed on $LLAMA_RELEASE_TAG. No automatic ggml-org fallback (inkling2_loop). STOP. Opt-in UNVERIFIED path: INKLING_INSTALL_MODE=upstream at commit $UPSTREAM_LOOP_MERGE_COMMIT. Logs: $attempt_log $attempt_q4"
      die "LOAD GATE STOP: Unsloth UD-Q8_K_XL failed to load, and the enabled UD-Q4_K_XL also failed, on $LLAMA_RELEASE_TAG. ggml-org Q8_0/BF16 are inkling2_loop and cannot load on this pin — they are not used automatically. If the owner wants those files, ask before building upstream llama.cpp at $UPSTREAM_LOOP_MERGE_COMMIT (PR #32694; UNVERIFIED). Logs: $LOG $attempt_log $attempt_q4"
    fi
  else
    write_status_to "$STATUS_FILE" STOP "load failed for $ACTIVE_FILE on $LLAMA_RELEASE_TAG. No automatic fallback. WANT_Q4 was not enabled or Q4 was not downloaded. STOP. Opt-in UNVERIFIED path for inkling2_loop GGUFs: INKLING_INSTALL_MODE=upstream at $UPSTREAM_LOOP_MERGE_COMMIT."
    die "LOAD GATE STOP: $ACTIVE_FILE failed to load on $LLAMA_RELEASE_TAG. There is no automatic ggml-org Q8_0 fallback (that file is inkling2_loop; this pin only runs inkling2 / Unsloth UD). To also have a 4-bit retry, set WANT_Q4=1, re-run 20-download.sh / 30-verify.sh / 35-loadcheck.sh. For ggml-org files, ask the owner about an opt-in upstream build at $UPSTREAM_LOOP_MERGE_COMMIT (UNVERIFIED). Log: $attempt_log"
  fi
fi

# Optional Q4 load-check when Q8 already passed (fast-iteration add-on).
if [ "$primary_ok" -eq 1 ] && { want_q4 || [ "${INKLING_QUANT:-}" = "ud-q4" ]; } && [ "$ACTIVE_FILE" != "$UNSLOTH_Q4_FILE" ]; then
  if [ ! -f "$MODELS_DIR/$UNSLOTH_Q4_FILE" ]; then
    log_to "$LOG" "WANT_Q4=1 but $UNSLOTH_Q4_FILE is missing; reporting Q4 FAIL and continuing with the 8-bit default"
    write_status_to "$RESULTS_DIR/q4-loadcheck-status.txt" FAIL "Q4 file missing; 8-bit default unchanged"
  else
    assert_arch_supported_on_current_runtime "$UNSLOTH_Q4_FILE"
    require_file_verified "$MODELS_DIR/$UNSLOTH_Q4_FILE" "$UNSLOTH_Q4_SHA256"
    q4log="$LOG_DIR/loadcheck-q4-$STAMP.log"
    if try_load "$MODELS_DIR/$UNSLOTH_Q4_FILE" "$ctx" "$q4log"; then
      write_status_to "$RESULTS_DIR/q4-loadcheck-status.txt" PASS "loaded optional $UNSLOTH_Q4_FILE at ctx=$ctx"
      log_to "$LOG" "optional Q4 loadcheck PASSED (8-bit remains the default unless INKLING_USE_Q4=1)"
    else
      write_status_to "$RESULTS_DIR/q4-loadcheck-status.txt" STOP "optional $UNSLOTH_Q4_FILE failed the load or offload check; continuing with the 8-bit default. log=$q4log"
      log_to "$LOG" "optional Q4 loadcheck STOP (load or offload failed); 8-bit default is still PASS. See $q4log. Not stopping the setup."
    fi
  fi
fi

# Optional long-context profile (UNVERIFIED). Only after the minimal load passed.
if [ "$PROFILE" = "long" ]; then
  if [ "$INKLING_PLATFORM" != "macos-arm64" ]; then
    die "INKLING_CTX_PROFILE=long is a Mac 64 GB opt-in only (UNVERIFIED). Zenbook stays at CTX_SIZE_ZENBOOK. STOP."
  fi
  long_log="$LOG_DIR/loadcheck-long-$STAMP.log"
  log_to "$LOG" "long-context opt-in: trying ctx=$CTX_SIZE_LONG (UNVERIFIED). Watching for OOM / load failure."
  if try_load "$MODEL_PATH" "$CTX_SIZE_LONG" "$long_log"; then
    printf '%s\n' "$CTX_SIZE_LONG" >"$RESULTS_DIR/active-ctx.txt"
    log_to "$LOG" "long-context loadcheck PASSED at ctx=$CTX_SIZE_LONG (runtime still UNVERIFIED at this length)"
  else
    printf '%s\n' "$CTX_SIZE_DEFAULT" >"$RESULTS_DIR/active-ctx.txt"
    log_to "$LOG" "long-context loadcheck FAILED or ran out of memory. Keeping default ctx=$CTX_SIZE_DEFAULT. See $long_log"
    printf 'long_context=FAIL\n' >>"$STATUS_FILE"
  fi
else
  if [ "$INKLING_PLATFORM" = "macos-arm64" ]; then
    printf '%s\n' "$CTX_SIZE_DEFAULT" >"$RESULTS_DIR/active-ctx.txt"
  else
    printf '%s\n' "$CTX_SIZE_ZENBOOK" >"$RESULTS_DIR/active-ctx.txt"
  fi
fi

log "loadcheck PASSED (see $STATUS_FILE)"
