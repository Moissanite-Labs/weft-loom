#!/usr/bin/env bash
# Smoke test. Requires a PASS from 35-loadcheck.sh.
# Hard gates: model already loaded once, /health returns ok, log mentions
# an inkling architecture if present. Arithmetic (17*23 contains 391) is a
# property check; it uses temp 0 as a package-policy probe, not Unsloth's
# recommended chat sampling (which is stochastic at temp 1.0).
set -euo pipefail
# shellcheck source=lib.sh
_sdir=$(dirname -- "$0")
_sdir=$(cd -- "$_sdir" && pwd)
. "$_sdir/lib.sh"
load_config
init_paths
detect_platform
require_confirmed_platform

LOG="$LOG_DIR/smoke.log"
STAMP=$(date '+%Y%m%d-%H%M%S')
STATUS="$RESULTS_DIR/smoke-$STAMP.txt"

TIMEOUT_SECS=${SMOKE_TIMEOUT:-300}

if is_dry_run; then
  printf 'DRY-RUN: would require loadcheck PASS and a verified SHA for the resolved model (INKLING_USE_Q4 / INKLING_QUANT=ud-q4 selects Q4)\n'
  printf 'DRY-RUN: would run llama-cli with -st, stdin /dev/null, timeout=%ss, then assert GPU offload\n' "$TIMEOUT_SECS"
  printf 'DRY-RUN: llama-cli property check: prompt 17*23, output contains 391 (temp 0 package policy)\n'
  printf 'DRY-RUN: llama-server /health -> {"status": "ok"}\n'
  printf 'DRY-RUN: /v1/chat/completions curl example\n'
  printf 'DRY-RUN: text-only unless INKLING_USE_VISION=1; would not invent expected full model text\n'
  exit 0
fi

[ -f "$RESULTS_DIR/loadcheck-status.txt" ] || die "run 35-loadcheck.sh first"
grep -q '^status=PASS$' "$RESULTS_DIR/loadcheck-status.txt" \
  || die "loadcheck did not PASS. STOP. See $RESULTS_DIR/loadcheck-status.txt"

resolve_runtime_model
assert_arch_supported_on_current_runtime "$RUNTIME_FILE"
MODEL="$RUNTIME_MODEL"
CTX=$(cat "$RESULTS_DIR/active-ctx.txt" 2>/dev/null || echo "$CTX_SIZE_DEFAULT")
[ -f "$MODEL" ] || die "model missing: $MODEL"

fail=0
{
  echo "smoke start $STAMP"
  echo "model=$MODEL"
  echo "ctx=$CTX"
} >"$STATUS"

cli_ok=0
if bin=$(find_llama_bin llama-cli); then
  cli_log="$LOG_DIR/smoke-cli-$STAMP.log"
  extra=(--ctx-size "$CTX" -n 32 -p "17 * 23 = " -st --no-display-prompt --verbose --temp 0 --top-p 1.0 --top-k 0 --min-p 0.0 -ngl "$N_GPU_LAYERS")
  if [ "$INKLING_PLATFORM" = "wsl-cuda" ] || [ "$INKLING_PLATFORM" = "linux-cuda" ]; then
    extra+=(-ot "$ZENBOOK_OVERRIDE_TENSOR")
  fi
  set +e
  run_with_timeout "$TIMEOUT_SECS" "$bin" -m "$MODEL" "${extra[@]}" </dev/null >"$cli_log" 2>&1
  rc=$?
  set -e
  if grep -Eiq "error loading model|failed to load|tensor 'blk\.24" "$cli_log" || [ "$rc" -ne 0 ]; then
    echo "cli_load=FAIL rc=$rc" >>"$STATUS"
    fail=1
  else
    echo "cli_load=OK rc=$rc" >>"$STATUS"
  fi
  set +e
  gpu_offload_ok "$cli_log"
  off_rc=$?
  set -e
  if [ "$off_rc" -ne 0 ]; then
    echo "cli_offload=FAIL" >>"$STATUS"
    fail=1
  else
    echo "cli_offload=PASS" >>"$STATUS"
  fi
  if grep -F "391" "$cli_log" >/dev/null 2>&1; then
    echo "arithmetic_property=PASS (output contains 391)" >>"$STATUS"
    cli_ok=1
  else
    echo "arithmetic_property=MISS (no '391' at temp 0; not a setup failure by itself if the model loaded)" >>"$STATUS"
  fi
else
  echo "llama-cli absent; skipping completion property check" >>"$STATUS"
fi

server=$(find_llama_bin llama-server) || die "llama-server not found"
srv_log="$LOG_DIR/smoke-server-$STAMP.log"
extra=(--model "$MODEL" --jinja --ctx-size "$CTX" --n-gpu-layers "$N_GPU_LAYERS" --parallel "$PARALLEL"
  --temp "$TEMP" --top-p "$TOP_P" --top-k "$TOP_K" --min-p "$MIN_P"
  --verbose --host "$HOST" --port "$PORT")
if want_vision && [ -f "$RESULTS_DIR/active-mmproj.txt" ]; then
  extra+=(--mmproj "$MODELS_DIR/$(cat "$RESULTS_DIR/active-mmproj.txt")")
fi
if [ "$INKLING_PLATFORM" = "wsl-cuda" ] || [ "$INKLING_PLATFORM" = "linux-cuda" ]; then
  extra+=(-ot "$ZENBOOK_OVERRIDE_TENSOR")
fi

set +e
"$server" "${extra[@]}" >"$srv_log" 2>&1 &
pid=$!
set -e
cleanup() {
  if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT

health_ok=0
i=0
while [ "$i" -lt 180 ]; do
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "server_died_early" >>"$STATUS"
    fail=1
    break
  fi
  if body=$(curl -fsS "http://$HOST:$PORT/health" 2>/dev/null); then
    echo "health_body=$body" >>"$STATUS"
    if printf '%s' "$body" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"'; then
      health_ok=1
      echo "health=PASS" >>"$STATUS"
      break
    fi
  fi
  i=$((i + 1))
  sleep 1
done
if [ "$health_ok" -ne 1 ]; then
  echo "health=FAIL" >>"$STATUS"
  fail=1
else
  if gpu_offload_ok "$srv_log"; then
    echo "server_offload=PASS" >>"$STATUS"
  else
    echo "server_offload=FAIL" >>"$STATUS"
    fail=1
  fi
fi

arch_files=("$srv_log")
if [ -n "${cli_log:-}" ] && [ -f "${cli_log:-}" ]; then
  arch_files+=("$cli_log")
fi
if grep -Eiq "inkling2_loop|general.architecture[[:space:]=]+inkling2|arch[[:space:]=]+inkling2" "${arch_files[@]}"; then
  echo "arch=recognized inkling2/inkling2_loop" >>"$STATUS"
else
  echo "arch=not grepped (not a hard fail if health passed; record the log)" >>"$STATUS"
fi

# One chat-completions request (property check, recommended sampling).
if [ "$health_ok" -eq 1 ]; then
  chat_log="$LOG_DIR/smoke-chat-$STAMP.json"
  set +e
  curl -sS "http://$HOST:$PORT/v1/chat/completions" \
    -H 'Content-Type: application/json' \
    -d "{\"model\":\"inkling-2-mini\",\"messages\":[{\"role\":\"user\",\"content\":\"What is 17 times 23? Reply with the number.\"}],\"temperature\":0}" \
    >"$chat_log"
  chat_rc=$?
  set -e
  echo "chat_curl_rc=$chat_rc" >>"$STATUS"
  if grep -F "391" "$chat_log" >/dev/null 2>&1; then
    echo "chat_arithmetic_property=PASS" >>"$STATUS"
    cli_ok=1
  else
    echo "chat_arithmetic_property=MISS" >>"$STATUS"
  fi
fi

cleanup
trap - EXIT

if [ "$fail" -ne 0 ]; then
  cat "$STATUS" >>"$LOG"
  die "smoke FAILED. See $STATUS and $LOG. STOP and report to the owner."
fi
echo "smoke=PASS arithmetic_seen=$cli_ok" >>"$STATUS"
cat "$STATUS" >>"$LOG"
log "smoke PASSED ($STATUS)"
