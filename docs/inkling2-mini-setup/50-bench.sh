#!/usr/bin/env bash
# Short tok/s benchmark with llama-bench (pp512 / tg128). Results are
# measurements, not claims — mark any later summary UNVERIFIED until the
# owner runs this on the target machine.
set -euo pipefail
# shellcheck source=lib.sh
_sdir=$(dirname -- "$0")
_sdir=$(cd -- "$_sdir" && pwd)
. "$_sdir/lib.sh"
load_config
init_paths
detect_platform
require_confirmed_platform

STAMP=$(date '+%Y%m%d-%H%M%S')
OUT="$RESULTS_DIR/bench-$STAMP.txt"
LOG="$LOG_DIR/bench.log"

if is_dry_run; then
  printf 'DRY-RUN: would require a verified SHA and loadcheck PASS for the resolved model (INKLING_USE_Q4 selects Q4)\n'
  printf 'DRY-RUN: would run llama-bench -m <resolved-gguf> -pg 512,128 with platform offload flags\n'
  printf 'DRY-RUN: would write %q plus machine info\n' "$OUT"
  exit 0
fi

[ -f "$RESULTS_DIR/loadcheck-status.txt" ] || die "run 35-loadcheck.sh first"
grep -q '^status=PASS$' "$RESULTS_DIR/loadcheck-status.txt" \
  || die "loadcheck did not PASS. STOP."

resolve_runtime_model
assert_arch_supported_on_current_runtime "$RUNTIME_FILE"
MODEL="$RUNTIME_MODEL"
[ -f "$MODEL" ] || die "model missing: $MODEL"

bench=$(find_llama_bin llama-bench) || die "llama-bench not found in the pinned build. STOP and report; do not invent an alternate benchmark."

{
  echo "inkling2-mini llama-bench"
  echo "timestamp=$(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "platform=$INKLING_PLATFORM"
  echo "model=$MODEL"
  echo "llama_release=$LLAMA_RELEASE_TAG"
  echo "hostname=$(hostname 2>/dev/null || true)"
  echo "uname=$(uname -a)"
  if [ "$INKLING_PLATFORM" = "macos-arm64" ] && command -v sysctl >/dev/null 2>&1; then
    echo "chip=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || true)"
    echo "hw.memsize=$(sysctl -n hw.memsize 2>/dev/null || true)"
    echo "macos=$(sw_vers -productVersion 2>/dev/null || true)"
  fi
  if command -v nvidia-smi >/dev/null 2>&1; then
    echo "gpu=$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || true)"
  fi
  echo "--- llama-bench ---"
} >"$OUT"

extra=(-m "$MODEL" -pg "512,128" -ngl "$N_GPU_LAYERS")
if [ "$INKLING_PLATFORM" = "wsl-cuda" ] || [ "$INKLING_PLATFORM" = "linux-cuda" ]; then
  extra+=(-ot "$ZENBOOK_OVERRIDE_TENSOR")
fi

set +e
"$bench" "${extra[@]}" >>"$OUT" 2>&1
rc=$?
set -e
echo "exit=$rc" >>"$OUT"
if [ "$rc" -ne 0 ]; then
  cat "$OUT" >>"$LOG"
  die "llama-bench failed (exit $rc). See $OUT. STOP and report."
fi
cp "$OUT" "$RESULTS_DIR/bench-latest.txt"
log_to "$LOG" "bench PASSED $OUT"
log "bench PASSED ($OUT). Treat tok/s as a raw measurement, not a published claim."
