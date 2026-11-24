#!/usr/bin/env bash
# Start llama-server (OpenAI-compatible) bound to 127.0.0.1.
# Requires loadcheck PASS and a verified SHA for the active INKLING_QUANT.
# Text-only by default: --mmproj only when INKLING_USE_VISION=1.
# Does not daemonize unless INKLING_SERVE_BG=1.
set -euo pipefail
# shellcheck source=lib.sh
_sdir=$(dirname -- "$0")
_sdir=$(cd -- "$_sdir" && pwd)
. "$_sdir/lib.sh"
load_config
init_paths
detect_platform
require_confirmed_platform

LOG="$LOG_DIR/serve.log"

if is_dry_run; then
  printf 'DRY-RUN: would refuse any file whose SHA is not in results/verified/<sha> for the active INKLING_QUANT\n'
  printf 'DRY-RUN: llama-server --model <resolved active or Q4 if INKLING_USE_Q4=1> --jinja --ctx-size <active-or-default> -ngl %s --temp %s --top-p %s --top-k %s --min-p %s --host %s --port %s\n' \
    "$N_GPU_LAYERS" "$TEMP" "$TOP_P" "$TOP_K" "$MIN_P" "$HOST" "$PORT"
  if want_vision; then
    printf 'DRY-RUN: INKLING_USE_VISION=1; would add --mmproj if recorded\n'
  else
    printf 'DRY-RUN: text-only default; would not pass --mmproj (and would ignore a stale active-mmproj.txt)\n'
  fi
  printf 'DRY-RUN: curl example:\n'
  printf '  curl -sS http://%s:%s/health\n' "$HOST" "$PORT"
  printf '  curl -sS http://%s:%s/v1/chat/completions -H Content-Type: application/json -d {...}\n' "$HOST" "$PORT"
  exit 0
fi

[ -f "$RESULTS_DIR/loadcheck-status.txt" ] || die "run 35-loadcheck.sh first"
grep -q '^status=PASS$' "$RESULTS_DIR/loadcheck-status.txt" \
  || die "loadcheck did not PASS. STOP."

resolve_runtime_model
assert_arch_supported_on_current_runtime "$RUNTIME_FILE"
CTX=$(cat "$RESULTS_DIR/active-ctx.txt" 2>/dev/null || echo "$CTX_SIZE_DEFAULT")
server=$(find_llama_bin llama-server) || die "llama-server not found"

args=(--model "$RUNTIME_MODEL" --jinja --ctx-size "$CTX" --n-gpu-layers "$N_GPU_LAYERS" --parallel "$PARALLEL"
  --temp "$TEMP" --top-p "$TOP_P" --top-k "$TOP_K" --min-p "$MIN_P"
  --host "$HOST" --port "$PORT")
if want_vision && [ -f "$RESULTS_DIR/active-mmproj.txt" ]; then
  args+=(--mmproj "$MODELS_DIR/$(cat "$RESULTS_DIR/active-mmproj.txt")")
elif [ -f "$RESULTS_DIR/active-mmproj.txt" ]; then
  log_to "$LOG" "ignoring stale active-mmproj.txt (text-only default; set INKLING_USE_VISION=1 to use it)"
fi
if [ "$INKLING_PLATFORM" = "wsl-cuda" ] || [ "$INKLING_PLATFORM" = "linux-cuda" ]; then
  args+=(-ot "$ZENBOOK_OVERRIDE_TENSOR")
fi

log_to "$LOG" "starting: $server ${args[*]} (file=$RUNTIME_FILE sha=$RUNTIME_SHA kind=$RUNTIME_KIND)"
log "Open http://$HOST:$PORT  health: curl -sS http://$HOST:$PORT/health"
log "Chat example:"
log "curl -sS http://$HOST:$PORT/v1/chat/completions -H 'Content-Type: application/json' -d '{\"model\":\"inkling-2-mini\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}],\"temperature\":1.0,\"top_p\":1.0}'"

if [ "${INKLING_SERVE_BG:-0}" = "1" ]; then
  "$server" "${args[@]}" >>"$LOG" 2>&1 &
  echo $! >"$RESULTS_DIR/server.pid"
  log "server pid $(cat "$RESULTS_DIR/server.pid")"
else
  exec "$server" "${args[@]}"
fi
