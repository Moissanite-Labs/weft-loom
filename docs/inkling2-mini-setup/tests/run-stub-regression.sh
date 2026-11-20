#!/usr/bin/env bash
# Stub-binary regressions for proof M1 and M2 (zip 2de8e7b6).
# Run from anywhere: tests/run-stub-regression.sh
# Exercises 35-loadcheck.sh / 40-smoke.sh / serve.sh with fake llama-cli
# and llama-server, both with GNU timeout on PATH and with it hidden
# (macOS-like bash fallback).
set -euo pipefail

SELF=$(cd -- "$(dirname -- "$0")" && pwd)
PKG=$(cd -- "$SELF/.." && pwd)
STAMP=$(date '+%Y%m%d-%H%M%S')
ROOT=$(mktemp -d "${TMPDIR:-/tmp}/inkling-stubtest-$STAMP-XXXX")
trap 'rm -rf "$ROOT"' EXIT

fails=0
passes=0
logf="$ROOT/test-output.txt"

say() { printf '%s\n' "$*" | tee -a "$logf"; }

fail() {
  say "FAIL: $*"
  fails=$((fails + 1))
}

pass() {
  say "PASS: $*"
  passes=$((passes + 1))
}

# Build a PATH prefix that includes common tools, optionally omitting timeout/gtimeout.
build_toolpath() {
  local include_timeout=$1
  local dir=$2
  mkdir -p "$dir"
  local c w
  for c in bash sh cat printf echo mkdir rm mv cp ln chmod date grep sed awk tr wc \
           cut head tail tee sleep kill ps pkill pgrep sha256sum shasum uname env \
           hostname curl python3 mktemp sort uniq xargs basename dirname pwd true false \
           which getent lsof ss; do
    w=$(command -v "$c" 2>/dev/null) || continue
    ln -sf "$w" "$dir/$c"
  done
  if [ "$include_timeout" = 1 ]; then
    for c in timeout gtimeout; do
      w=$(command -v "$c" 2>/dev/null) || continue
      ln -sf "$w" "$dir/$c"
    done
  fi
}

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

setup_install() {
  local inst=$1
  mkdir -p "$inst/llama.cpp" "$inst/models" "$inst/results/verified" "$inst/logs" "$inst/downloads"
  printf 'tiny-inkling-ud-q8-stub\n' >"$inst/models/Inkling-2-Mini-UD-Q8_K_XL.gguf"
  printf 'tiny-inkling-ud-q4-stub\n' >"$inst/models/Inkling-2-Mini-UD-Q4_K_XL.gguf"
  local q8sha q4sha q8b q4b
  q8sha=$(sha256_file "$inst/models/Inkling-2-Mini-UD-Q8_K_XL.gguf")
  q4sha=$(sha256_file "$inst/models/Inkling-2-Mini-UD-Q4_K_XL.gguf")
  q8b=$(wc -c <"$inst/models/Inkling-2-Mini-UD-Q8_K_XL.gguf" | tr -d ' ')
  q4b=$(wc -c <"$inst/models/Inkling-2-Mini-UD-Q4_K_XL.gguf" | tr -d ' ')

  # Patch only the SHA/size lines so arch names and other facts stay intact.
  sed \
    -e "s/^UNSLOTH_Q8_SHA256=.*/UNSLOTH_Q8_SHA256=$q8sha/" \
    -e "s/^UNSLOTH_Q8_BYTES=.*/UNSLOTH_Q8_BYTES=$q8b/" \
    -e "s/^UNSLOTH_Q4_SHA256=.*/UNSLOTH_Q4_SHA256=$q4sha/" \
    -e "s/^UNSLOTH_Q4_BYTES=.*/UNSLOTH_Q4_BYTES=$q4b/" \
    "$PKG/config.env" >"$inst/config.env"

  printf '%s\n' "unsloth/Inkling-2-Mini-GGUF" >"$inst/results/active-repo.txt"
  printf '%s\n' "Inkling-2-Mini-UD-Q8_K_XL.gguf" >"$inst/results/active-file.txt"
  printf '%s\n' "$q8sha" >"$inst/results/active-sha256.txt"
  printf '%s\n' "$q8b" >"$inst/results/active-bytes.txt"
  printf '%s\n' "32768" >"$inst/results/active-ctx.txt"
  {
    printf 'status=PASS\n'
    printf 'file=Inkling-2-Mini-UD-Q8_K_XL.gguf\n'
    printf 'sha256=%s\n' "$q8sha"
  } >"$inst/results/verify-status.txt"
  {
    printf 'file=Inkling-2-Mini-UD-Q8_K_XL.gguf\n'
    printf 'sha256=%s\n' "$q8sha"
    printf 'path=%s\n' "$inst/models/Inkling-2-Mini-UD-Q8_K_XL.gguf"
  } >"$inst/results/verified/$q8sha"
  {
    printf 'file=Inkling-2-Mini-UD-Q4_K_XL.gguf\n'
    printf 'sha256=%s\n' "$q4sha"
    printf 'path=%s\n' "$inst/models/Inkling-2-Mini-UD-Q4_K_XL.gguf"
  } >"$inst/results/verified/$q4sha"
  printf '%s\n' "unsloth/Inkling-2-Mini-GGUF" >"$inst/results/q4-repo.txt"
  printf '%s\n' "Inkling-2-Mini-UD-Q4_K_XL.gguf" >"$inst/results/q4-file.txt"
  printf '%s\n' "$q4sha" >"$inst/results/q4-sha256.txt"
  printf '%s\n' "$q4b" >"$inst/results/q4-bytes.txt"
}

install_stubs() {
  local inst=$1
  local mode=$2
  mkdir -p "$inst/llama.cpp"
  printf '%s\n' "$mode" >"$inst/llama.cpp/cli.mode"
  cat >"$inst/llama.cpp/llama-cli" << 'STUB'
#!/usr/bin/env bash
mode=$(cat "$(dirname "$0")/cli.mode" 2>/dev/null || echo ok)
printf 'stub llama-cli mode=%s\n' "$mode" >&2
case "$mode" in
  ok)
    printf 'llama_model_loader: loaded meta\n'
    printf 'offloaded 49/49 layers to GPU\n'
    exit 0
    ;;
  nooff)
    printf 'llama_model_loader: loaded meta\n'
    exit 0
    ;;
  zero)
    printf 'llama_model_loader: loaded meta\n'
    printf 'offloaded 0/49 layers to GPU\n'
    exit 0
    ;;
  exit3)
    printf 'llama_model_loader: loaded meta\n'
    printf 'offloaded 49/49 layers to GPU\n'
    exit 3
    ;;
  q4nooff)
    # Primary Q8 (filename contains Q8) offloads; Q4 does not.
    case " $* " in
      *Q4*)
        printf 'llama_model_loader: loaded meta\n'
        exit 0
        ;;
      *)
        printf 'llama_model_loader: loaded meta\n'
        printf 'offloaded 49/49 layers to GPU\n'
        exit 0
        ;;
    esac
    ;;
  hang)
    sleep 1000
    exit 0
    ;;
  *)
    printf 'unknown stub mode %s\n' "$mode" >&2
    exit 99
    ;;
esac
STUB
  chmod +x "$inst/llama.cpp/llama-cli"

  cat >"$inst/llama.cpp/llama-server" << 'STUB'
#!/usr/bin/env bash
log=$(dirname "$0")/server.log
printf 'FAKE llama-server started:' >>"$log"
printf ' %s' "$@" >>"$log"
printf '\n' >>"$log"
for a in "$@"; do
  if [ "$a" = "--version" ]; then
    printf 'stub-llama-server 0\n'
    exit 0
  fi
done
printf 'offloaded 49/49 layers to GPU\n' >&2
# Stay up briefly so a mistaken serve.sh start is observable.
sleep 2
exit 0
STUB
  chmod +x "$inst/llama.cpp/llama-server"
}

set_cli_mode() {
  printf '%s\n' "$2" >"$1/llama.cpp/cli.mode"
  rm -f "$1/llama.cpp/server.log" "$1/results/server.pid"
}

run_env() {
  # run_env INST TOOLPATH cmd...
  local inst=$1 toolpath=$2
  shift 2
  env -i \
    PATH="$toolpath" \
    HOME="$inst/home" \
    USER="${USER:-test}" \
    TERM="${TERM:-dumb}" \
    LANG=C \
    INKLING_INSTALL_DIR="$inst" \
    INKLING_CONFIG="$inst/config.env" \
    INKLING_TEST_PLATFORM=wsl-cuda \
    INKLING_DRY_RUN=0 \
    INKLING_USE_VISION=0 \
    INKLING_WANT_Q4="${INKLING_WANT_Q4:-0}" \
    INKLING_USE_Q4="${INKLING_USE_Q4:-0}" \
    INKLING_SERVE_BG="${INKLING_SERVE_BG:-0}" \
    INKLING_CTX_PROFILE=default \
    "$@"
}

# --- M2 unit: bash fallback must not kill a set +e caller ---
unit_timeout_fallback() {
  local label=$1 toolpath=$2
  say "--- unit: run_with_timeout exit 3 ($label) ---"
  local out rc helper
  helper="$ROOT/unit-timeout.sh"
  cat >"$helper" << 'EOS'
set -euo pipefail
# shellcheck source=../lib.sh
. "$INKLING_LIB"
set +e
run_with_timeout 5 bash -c "exit 3"
rc=$?
echo "reached after call, rc=$rc"
exit 0
EOS
  set +e
  out=$(
    env -i PATH="$toolpath" HOME="$ROOT/home" LANG=C       INKLING_LIB="$PKG/lib.sh" bash "$helper" 2>&1
  )
  rc=$?
  set -e
  printf '%s\n' "$out" | tee -a "$logf"
  if [ "$rc" -eq 0 ] && printf '%s\n' "$out" | grep -q 'reached after call, rc=3'; then
    pass "$label run_with_timeout exit 3 reached the caller with rc=3"
  else
    fail "$label run_with_timeout exit 3 did not reach the caller cleanly (script rc=$rc)"
  fi
}

# --- M1: stale PASS must not survive a failed re-gate ---
case_m1() {
  local label=$1 toolpath=$2 failmode=$3
  local inst="$ROOT/m1-$failmode-$label"
  mkdir -p "$inst/home"
  setup_install "$inst"
  install_stubs "$inst" ok
  say "--- M1 prior PASS then $failmode re-gate ($label) ---"

  set +e
  run_env "$inst" "$toolpath" "$PKG/35-loadcheck.sh" >"$inst/first.log" 2>&1
  local rc1=$?
  set -e
  if [ "$rc1" -ne 0 ] || ! grep -q '^status=PASS$' "$inst/results/loadcheck-status.txt"; then
    fail "$label first loadcheck did not PASS (rc=$rc1). Log:"
    tee -a "$logf" < "$inst/first.log"
    return 0
  fi
  say "  first gate PASS (as required before the re-run)"

  set_cli_mode "$inst" "$failmode"
  set +e
  run_env "$inst" "$toolpath" "$PKG/35-loadcheck.sh" >"$inst/second.log" 2>&1
  local rc2=$?
  set -e
  printf '  second gate rc=%s\n' "$rc2" | tee -a "$logf"
  if [ "$rc2" -eq 0 ]; then
    fail "$label second loadcheck ($failmode) unexpectedly passed"
  else
    pass "$label second loadcheck ($failmode) exited non-zero"
  fi
  if [ -f "$inst/results/loadcheck-status.txt" ] && grep -q '^status=PASS$' "$inst/results/loadcheck-status.txt"; then
    fail "$label stale status=PASS survived the failed re-gate"
    tee -a "$logf" < "$inst/results/loadcheck-status.txt"
  elif [ -f "$inst/results/loadcheck-status.txt" ] && grep -q '^status=STOP$' "$inst/results/loadcheck-status.txt"; then
    pass "$label loadcheck-status.txt is status=STOP after the failed re-gate"
  else
    fail "$label expected status=STOP after the failed re-gate; got:"
    tee -a "$logf" < "$inst/results/loadcheck-status.txt" 2>/dev/null || say "  (missing status file)"
  fi

  set +e
  INKLING_SERVE_BG=1 run_env "$inst" "$toolpath" "$PKG/serve.sh" >"$inst/serve.log" 2>&1
  local rcs=$?
  set -e
  # If a server was mistakenly started, stop it.
  if [ -f "$inst/results/server.pid" ]; then
    kill "$(cat "$inst/results/server.pid")" 2>/dev/null || true
  fi
  if [ "$rcs" -eq 0 ]; then
    fail "$label serve.sh started after the failed re-gate (rc=0)"
    tee -a "$logf" < "$inst/serve.log"
  elif grep -q 'FAKE llama-server started' "$inst/llama.cpp/server.log" 2>/dev/null || grep -q 'FAKE llama-server started' "$inst/serve.log"; then
    fail "$label serve.sh launched llama-server after the failed re-gate"
  elif grep -Eqi 'loadcheck did not PASS|run 35-loadcheck.sh first' "$inst/serve.log"; then
    pass "$label serve.sh refused after the failed re-gate"
  else
    fail "$label serve.sh exited $rcs but without a loadcheck refusal message"
    tee -a "$logf" < "$inst/serve.log"
  fi
}

# --- M2 / L3: cli exit 3 must produce a normal smoke failure report ---
case_m2() {
  local label=$1 toolpath=$2
  local inst="$ROOT/m2-exit3-$label"
  mkdir -p "$inst/home"
  setup_install "$inst"
  install_stubs "$inst" ok
  say "--- M2 / L3 smoke on llama-cli exit 3 ($label) ---"

  set +e
  run_env "$inst" "$toolpath" "$PKG/35-loadcheck.sh" >"$inst/gate.log" 2>&1
  local rcg=$?
  set -e
  if [ "$rcg" -ne 0 ]; then
    fail "$label precondition loadcheck failed"
    tee -a "$logf" < "$inst/gate.log"
    return 0
  fi
  set_cli_mode "$inst" exit3
  set +e
  run_env "$inst" "$toolpath" "$PKG/40-smoke.sh" >"$inst/smoke.log" 2>&1
  local rcs=$?
  set -e
  printf '  smoke script rc=%s\n' "$rcs" | tee -a "$logf"
  cat "$inst/smoke.log" >>"$logf"

  if [ "$rcs" -eq 3 ]; then
    fail "$label smoke exited 3 silently (errexit leaked from run_with_timeout)"
  elif [ "$rcs" -eq 0 ]; then
    fail "$label smoke unexpectedly passed with cli exit 3"
  else
    pass "$label smoke exited non-zero (rc=$rcs), not a leaked 3"
  fi
  if grep -q 'smoke FAILED' "$inst/smoke.log"; then
    pass "$label smoke printed the normal 'smoke FAILED' report"
  else
    fail "$label smoke did not print 'smoke FAILED'"
  fi
  local status
  status=""
  for f in "$inst/results"/smoke-*.txt; do
    if [ -f "$f" ]; then
      status=$f
      break
    fi
  done
  if [ -n "$status" ] && grep -q 'cli_load=FAIL rc=3' "$status"; then
    pass "$label smoke status records cli_load=FAIL rc=3"
  elif [ -n "$status" ]; then
    fail "$label smoke status exists but lacks cli_load=FAIL rc=3:"
    tee -a "$logf" < "$status"
  else
    fail "$label no smoke-*.txt result file was written"
  fi
}

# --- L2 extra: optional Q4 offload fail must not abort an 8-bit PASS ---
case_l2() {
  local label=$1 toolpath=$2
  local inst="$ROOT/l2-q4nooff-$label"
  mkdir -p "$inst/home"
  setup_install "$inst"
  install_stubs "$inst" q4nooff
  say "--- L2 optional Q4 offload fail continues with 8-bit ($label) ---"
  set +e
  INKLING_WANT_Q4=1 run_env "$inst" "$toolpath" "$PKG/35-loadcheck.sh" >"$inst/gate.log" 2>&1
  local rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    fail "$label loadcheck aborted on optional Q4 offload failure (rc=$rc)"
    tee -a "$logf" < "$inst/gate.log"
  else
    pass "$label loadcheck continued after optional Q4 offload failure"
  fi
  if [ -f "$inst/results/loadcheck-status.txt" ] && grep -q '^status=PASS$' "$inst/results/loadcheck-status.txt"; then
    pass "$label primary 8-bit status remains PASS"
  else
    fail "$label primary 8-bit status was not PASS"
    tee -a "$logf" < "$inst/results/loadcheck-status.txt" 2>/dev/null || true
  fi
  if [ -f "$inst/results/q4-loadcheck-status.txt" ] && grep -q '^status=STOP$' "$inst/results/q4-loadcheck-status.txt"; then
    pass "$label q4-loadcheck-status.txt is status=STOP"
  else
    fail "$label expected q4-loadcheck-status.txt status=STOP"
    tee -a "$logf" < "$inst/results/q4-loadcheck-status.txt" 2>/dev/null || true
  fi
}

WITH="$ROOT/path-with-timeout"
WITHOUT="$ROOT/path-without-timeout"
build_toolpath 1 "$WITH"
build_toolpath 0 "$WITHOUT"

if [ -x "$WITH/timeout" ]; then
  say "GNU timeout is available; will run both PATH modes."
else
  say "WARN: no GNU timeout on this host; the 'with timeout' PATH will also use the bash fallback."
fi
if [ -x "$WITHOUT/timeout" ] || [ -x "$WITHOUT/gtimeout" ]; then
  fail "path-without-timeout still contains timeout/gtimeout"
fi

say "PKG=$PKG"
say "ROOT=$ROOT"
say ""

unit_timeout_fallback with-timeout "$WITH"
unit_timeout_fallback without-timeout "$WITHOUT"

case_m1 with-timeout "$WITH" nooff
case_m1 without-timeout "$WITHOUT" nooff
case_m1 with-timeout "$WITH" zero
case_m1 without-timeout "$WITHOUT" zero

case_m2 with-timeout "$WITH"
case_m2 without-timeout "$WITHOUT"

case_l2 with-timeout "$WITH"
case_l2 without-timeout "$WITHOUT"

say ""
say "Summary: $passes passed, $fails failed"
say "Full log: $logf"
if [ "$fails" -ne 0 ]; then
  exit 1
fi
exit 0
