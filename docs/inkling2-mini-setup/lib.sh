# shellcheck shell=bash
# Shared helpers for the Inkling 2 Mini setup scripts.
# Source this from the same directory as config.env.

set -euo pipefail

if [ -z "${INKLING_LIB_SOURCED:-}" ]; then
  INKLING_LIB_SOURCED=1
else
  return 0
fi

_sdir=$(dirname -- "${BASH_SOURCE[0]}")
SCRIPT_DIR=$(cd -- "$_sdir" && pwd)
CONFIG_FILE=${INKLING_CONFIG:-"$SCRIPT_DIR/config.env"}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  # Optional hook (used by 35-loadcheck.sh to record status=STOP before exit).
  if [ "${INKLING_IN_DIE:-0}" != 1 ]; then
    INKLING_IN_DIE=1
    if [ "$(type -t inkling_on_die 2>/dev/null)" = "function" ]; then
      inkling_on_die "$*" || true
    fi
  fi
  exit 1
}

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

log_to() {
  # log_to <logfile> <message...>
  local f=$1
  shift
  local line
  line="$(date '+%Y-%m-%d %H:%M:%S') $*"
  printf '%s\n' "$line"
  if [ -n "${f:-}" ] && [ "${INKLING_DRY_RUN:-0}" != "1" ]; then
    mkdir -p "$(dirname -- "$f")"
    printf '%s\n' "$line" >>"$f"
  fi
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

is_dry_run() {
  [ "${INKLING_DRY_RUN:-0}" = "1" ]
}

refuse_placeholders() {
  local file=${1:-$CONFIG_FILE}
  [ -f "$file" ] || die "config file not found: $file"
  # Only check assigned values, not comments.
  if grep -E '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=' "$file" \
    | grep -vE '^[[:space:]]*#' \
    | grep -E '<UNVERIFIED:|REPLACE_ME|TODO_SHA|CHANGEME' >/dev/null 2>&1; then
    printf 'ERROR: %s contains an UNVERIFIED placeholder in an assigned value. Refusing to proceed.\n' "$file" >&2
    grep -nE '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=.*(<UNVERIFIED:|REPLACE_ME|TODO_SHA|CHANGEME)' "$file" >&2 || true
    exit 1
  fi
}

load_config() {
  [ -f "$CONFIG_FILE" ] || die "config file not found: $CONFIG_FILE"
  refuse_placeholders "$CONFIG_FILE"
  # Do not `set -a`: that would export TEMP/HOST/PORT into pip, hf, and
  # Python (TEMP is Python's tempfile directory). Scripts read these vars
  # in-process after sourcing.
  # shellcheck source=config.env
  . "$CONFIG_FILE"
}

want_q4() {
  # Env INKLING_WANT_Q4 overrides config.env WANT_Q4 (default 0).
  local v=${INKLING_WANT_Q4:-${WANT_Q4:-0}}
  [ "$v" = "1" ]
}

want_vision() {
  # Vision / mmproj is opt-in only (owner 2026-11-20 4:46 PM CT).
  [ "${INKLING_USE_VISION:-0}" = "1" ]
}

want_runtime_q4() {
  [ "${INKLING_USE_Q4:-0}" = "1" ] || [ "${INKLING_QUANT:-}" = "ud-q4" ]
}

# Sets RUNTIME_FILE, RUNTIME_MODEL, RUNTIME_KIND, RUNTIME_SHA for serve / smoke / bench.
resolve_runtime_model() {
  if want_runtime_q4; then
    if [ ! -f "$RESULTS_DIR/q4-loadcheck-status.txt" ] || ! grep -q '^status=PASS$' "$RESULTS_DIR/q4-loadcheck-status.txt"; then
      die "4-bit was requested (INKLING_USE_Q4=1 or INKLING_QUANT=ud-q4) but UD-Q4_K_XL did not PASS the load gate. See $RESULTS_DIR/q4-loadcheck-status.txt. Unset those flags to use the 8-bit default. This does not change the 8-bit install."
    fi
    RUNTIME_FILE=$(cat "$RESULTS_DIR/q4-file.txt")
    RUNTIME_SHA=$(cat "$RESULTS_DIR/q4-sha256.txt")
    RUNTIME_MODEL="$MODELS_DIR/$RUNTIME_FILE"
    RUNTIME_KIND=ud-q4
  else
    [ -f "$RESULTS_DIR/active-file.txt" ] || die "no active model recorded. Run 20-download.sh and 35-loadcheck.sh first."
    RUNTIME_FILE=$(cat "$RESULTS_DIR/active-file.txt")
    RUNTIME_SHA=$(cat "$RESULTS_DIR/active-sha256.txt")
    RUNTIME_MODEL="$MODELS_DIR/$RUNTIME_FILE"
    RUNTIME_KIND=primary
    if [ -f "$RESULTS_DIR/loadcheck-status.txt" ]; then
      lc_file=$(awk -F= '/^file=/{print $2; exit}' "$RESULTS_DIR/loadcheck-status.txt")
      if [ -n "$lc_file" ] && [ "$lc_file" != "$RUNTIME_FILE" ]; then
        die "loadcheck-status.txt is for file=$lc_file but active-file.txt is $RUNTIME_FILE. Re-run 30-verify.sh and 35-loadcheck.sh for the current quant. Refusing to serve an unchecked file."
      fi
    fi
  fi
  [ -f "$RUNTIME_MODEL" ] || die "model missing: $RUNTIME_MODEL"
  export RUNTIME_FILE RUNTIME_MODEL RUNTIME_KIND RUNTIME_SHA
  require_verified_sha "$RUNTIME_MODEL" "$RUNTIME_SHA"
}

using_upstream() {
  [ "${INKLING_LLAMA:-}" = "upstream" ] || [ "${INKLING_INSTALL_MODE:-}" = "upstream" ]
}

# Known GGUF architectures. Unsloth UD headers: inkling2 (proof + this package).
# ggml-org Q8_0, BF16, IQ4_NL headers: inkling2_loop (Q8_0: proof range-read;
# BF16 and IQ4_NL: this session, HTTP range, general.architecture at offset 64).
known_gguf_arch() {
  local file=$1
  case "$file" in
    Inkling-2-Mini-UD-*.gguf) printf '%s\n' inkling2 ;;
    Inkling-2-Mini-Q8_0.gguf|Inkling-2-Mini-BF16.gguf|Inkling-2-Mini-IQ4_NL.gguf) printf '%s\n' inkling2_loop ;;
    *) printf '%s\n' unknown ;;
  esac
}

assert_arch_supported_on_current_runtime() {
  local file=$1
  local arch
  arch=$(known_gguf_arch "$file")
  if [ "$arch" = "inkling2" ]; then
    return 0
  fi
  if [ "$arch" = "inkling2_loop" ]; then
    if using_upstream; then
      log "arch inkling2_loop for $file: allowed only because INKLING_INSTALL_MODE/INKLING_LLAMA=upstream (build at $UPSTREAM_LOOP_MERGE_COMMIT). Loadability UNVERIFIED until the load gate passes."
      return 0
    fi
    die "Refusing $file: its GGUF architecture is inkling2_loop. The pinned Unsloth build $LLAMA_RELEASE_TAG only has runtime support for inkling2 (Unsloth UD files). ggml-org Q8_0/BF16/IQ4_NL cannot load on that pin. This is not an automatic fallback. Opt-in (never automatic, UNVERIFIED): INKLING_INSTALL_MODE=upstream to build ggml-org llama.cpp from commit $UPSTREAM_LOOP_MERGE_COMMIT (PR #32694 merge). If build tools are missing, STOP and ask the owner. See README."
  fi
  die "unknown GGUF architecture for $file; refusing to download or run it."
}

verified_marker_path() {
  printf '%s\n' "$RESULTS_DIR/verified/$1"
}

mark_verified() {
  local file=$1 sha=$2
  local dir="$RESULTS_DIR/verified"
  mkdir -p "$dir"
  {
    printf 'file=%s\n' "$(basename -- "$file")"
    printf 'sha256=%s\n' "$sha"
    printf 'path=%s\n' "$file"
    printf 'verified_at=%s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  } >"$dir/$sha"
}

require_verified_sha() {
  local file=$1 expected=$2
  local marker got
  [ -n "$expected" ] || die "empty expected SHA-256 for $file"
  case "$expected" in
    *'<UNVERIFIED:'*|REPLACE_ME|TODO_SHA|CHANGEME)
      die "expected SHA-256 for $file is a placeholder; refusing"
      ;;
  esac
  [ -f "$file" ] || die "file missing for verified-SHA check: $file"
  marker=$(verified_marker_path "$expected")
  got=$(sha256_of "$file")
  if [ "$got" != "$expected" ]; then
    die "SHA-256 of $file ($got) does not match the expected value for this quant ($expected). Refusing to serve or test an unverified file. Re-run 30-verify.sh."
  fi
  if [ ! -f "$marker" ]; then
    # Quant switch or first use after a fresh verify: re-verify and write the marker.
    log "no verified marker for $expected; re-verifying $file"
    verify_sha256 "$file" "$expected"
    mark_verified "$file" "$expected"
  fi
}

clear_stale_gate_state() {
  # Call when the primary or selected quant changes.
  rm -f "$RESULTS_DIR/verify-status.txt" "$RESULTS_DIR/loadcheck-status.txt"
  if ! want_vision; then
    rm -f "$RESULTS_DIR/active-mmproj.txt" "$RESULTS_DIR/active-mmproj-sha256.txt"
  fi
}

gpu_offload_ok() {
  # Return 0 if the log shows a non-zero GPU layer offload. Print the reason to stderr on fail.
  # This is a proxy (INFO "offloaded N/M layers to GPU"); a partial N/M (WSL -ot) is allowed, 0/M is not.
  local logf=$1
  local line n
  if [ ! -f "$logf" ]; then
    printf 'ERROR: offload check: log missing: %s\n' "$logf" >&2
    return 1
  fi
  line=$(grep -Ei "offloaded[[:space:]]+[0-9]+/[0-9]+[[:space:]]+layers" "$logf" | tail -n 1 || true)
  if [ -z "$line" ]; then
    printf 'ERROR: could not confirm GPU offload: no offloaded N/N layers line in %s. A CPU-only fallback must not pass this gate.\n' "$logf" >&2
    return 1
  fi
  n=$(printf '%s\n' "$line" | sed -n 's/.*[Oo]ffloaded[[:space:]]*\([0-9][0-9]*\)\/[0-9][0-9]*[[:space:]]*layers.*/\1/p')
  if [ -z "$n" ] || [ "$n" -eq 0 ]; then
    printf 'ERROR: GPU offload count is 0 in: %s  (log %s)\n' "$line" "$logf" >&2
    return 1
  fi
  log "GPU offload confirmed: $line"
  return 0
}

require_gpu_offload() {
  if gpu_offload_ok "$1"; then
    return 0
  fi
  if [ -n "${RESULTS_DIR:-}" ]; then
    _inkling_write_gate_stop "GPU offload was not confirmed in $1"
  fi
  die "GPU offload was not confirmed in $1. Re-run with a Metal (Mac) or CUDA (WSL) build and -ngl ${N_GPU_LAYERS:-99}. STOP and report."
}

# Best-effort write of loadcheck status=STOP (used by require_gpu_offload and die hook).
_inkling_write_gate_stop() {
  local dest=${STATUS_FILE:-${RESULTS_DIR:-}/loadcheck-status.txt}
  [ -n "${RESULTS_DIR:-}" ] || return 0
  mkdir -p "$RESULTS_DIR" 2>/dev/null || true
  {
    printf 'status=STOP\n'
    printf 'time=%s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
    printf 'file=%s\n' "${ACTIVE_FILE:-}"
    printf 'sha256=%s\n' "${ACTIVE_SHA:-}"
    printf 'reason=%s\n' "$*"
  } >"$dest" 2>/dev/null || true
}

# Kill pid and its descendants (watcher sleeps, hung-stub children). Bash 3.2 compatible.
_inkling_kill_tree() {
  local sig=TERM
  local target kids k
  if [ "${1:-}" = "-9" ] || [ "${1:-}" = "-KILL" ]; then
    sig=KILL
    shift
  fi
  target=${1:-}
  [ -n "$target" ] || return 0
  kids=$(ps -o pid= -o ppid= 2>/dev/null | awk -v p="$target" '$2 == p {print $1}') || true
  for k in $kids; do
    _inkling_kill_tree "-$sig" "$k"
  done
  if command -v pkill >/dev/null 2>&1; then
    pkill -"$sig" -P "$target" 2>/dev/null || true
  fi
  kill -"$sig" "$target" 2>/dev/null || true
}

# Portable timeout: GNU timeout, brew gtimeout, or a bash fallback (macOS).
# Restores the caller's errexit state. Returns the child's exit code. Reaps the
# watcher (and its sleep) so a timed-out or fast-finishing command leaves no orphans.
run_with_timeout() {
  local secs=$1
  local rc=0 pid watcher
  local restore_e=0
  shift
  case $- in
    *e*) restore_e=1 ;;
  esac
  set +e
  if command -v timeout >/dev/null 2>&1; then
    timeout -k 15 "$secs" "$@"
    rc=$?
    [ "$restore_e" -eq 1 ] && set -e
    return "$rc"
  fi
  if command -v gtimeout >/dev/null 2>&1; then
    gtimeout -k 15 "$secs" "$@"
    rc=$?
    [ "$restore_e" -eq 1 ] && set -e
    return "$rc"
  fi
  "$@" &
  pid=$!
  (
    sleep "$secs"
    _inkling_kill_tree "$pid"
    sleep 10
    _inkling_kill_tree -9 "$pid"
  ) &
  watcher=$!
  wait "$pid"
  rc=$?
  # Reap the watcher and its sleep so neither outlives the call (proof L1).
  _inkling_kill_tree "$watcher"
  wait "$watcher" 2>/dev/null || true
  # Leftover children of a timed-out command (e.g. a hang stub's sleep).
  _inkling_kill_tree "$pid"
  wait "$pid" 2>/dev/null || true
  [ "$restore_e" -eq 1 ] && set -e
  return "$rc"
}

# Must be called after load_config.

init_paths() {
  INSTALL_DIR=${INKLING_INSTALL_DIR:-"${HOME}/inkling2-mini"}
  LOG_DIR="$INSTALL_DIR/logs"
  RESULTS_DIR="$INSTALL_DIR/results"
  MODELS_DIR="$INSTALL_DIR/models"
  VENV_DIR="$INSTALL_DIR/venv"
  LLAMA_DIR="$INSTALL_DIR/llama.cpp"
  UPSTREAM_DIR="$INSTALL_DIR/llama.cpp-upstream"
  DOWNLOADS_DIR="$INSTALL_DIR/downloads"
  CACHE_DIR="$INSTALL_DIR/cache"
  # Keep caches inside INSTALL_DIR (proof L5).
  export HF_HOME="$CACHE_DIR/hf"
  export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
  export LLAMA_CACHE="$CACHE_DIR/llama"
  export PIP_CACHE_DIR="$CACHE_DIR/pip"
  export INSTALL_DIR LOG_DIR RESULTS_DIR MODELS_DIR VENV_DIR LLAMA_DIR UPSTREAM_DIR DOWNLOADS_DIR CACHE_DIR
  if ! is_dry_run; then
    mkdir -p "$INSTALL_DIR" "$LOG_DIR" "$RESULTS_DIR" "$MODELS_DIR" "$DOWNLOADS_DIR" \
      "$HF_HOME" "$LLAMA_CACHE" "$PIP_CACHE_DIR" "$RESULTS_DIR/verified"
  fi
}

run() {
  # Run a command, or print it in dry-run mode.
  if is_dry_run; then
    printf 'DRY-RUN:'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  "$@"
}

# Like run, but records the command in a log file when not dry-run.
run_logged() {
  local logfile=$1
  shift
  if is_dry_run; then
    printf 'DRY-RUN:'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  mkdir -p "$(dirname -- "$logfile")"
  {
    printf '+ '
    printf '%q ' "$@"
    printf '\n'
  } >>"$logfile"
  "$@" >>"$logfile" 2>&1
}

detect_platform() {
  # Sets: INKLING_OS INKLING_ARCH INKLING_PLATFORM INKLING_IS_WSL
  # INKLING_PLATFORM is one of: macos-arm64, wsl-cuda, linux-cuda, unsupported
  # INKLING_TEST_PLATFORM is a test-only hook (tests/run-stub-regression.sh).
  if [ -n "${INKLING_TEST_PLATFORM:-}" ]; then
    case "$INKLING_TEST_PLATFORM" in
      macos-arm64|wsl-cuda|linux-cuda)
        INKLING_OS=$(uname -s)
        INKLING_ARCH=$(uname -m)
        INKLING_PLATFORM=$INKLING_TEST_PLATFORM
        INKLING_IS_WSL=0
        if [ "$INKLING_TEST_PLATFORM" = "wsl-cuda" ]; then
          INKLING_IS_WSL=1
        fi
        return 0
        ;;
      *)
        die "INKLING_TEST_PLATFORM=$INKLING_TEST_PLATFORM is not a known platform (test hook)"
        ;;
    esac
  fi
  INKLING_OS=$(uname -s)
  INKLING_ARCH=$(uname -m)
  INKLING_IS_WSL=0
  INKLING_PLATFORM=unsupported
  if [ -r /proc/version ] && grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
    INKLING_IS_WSL=1
  fi
  case "$INKLING_OS:$INKLING_ARCH" in
    Darwin:arm64|Darwin:aarch64)
      INKLING_PLATFORM=macos-arm64
      ;;
    Linux:x86_64)
      if [ "$INKLING_IS_WSL" = "1" ]; then
        INKLING_PLATFORM=wsl-cuda
      else
        INKLING_PLATFORM=linux-cuda
      fi
      ;;
    *)
      INKLING_PLATFORM=unsupported
      ;;
  esac
}

find_llama_bin() {
  # find_llama_bin llama-server
  local name=$1
  local p roots r
  roots="$LLAMA_DIR"
  if using_upstream; then
    roots="$UPSTREAM_DIR $LLAMA_DIR"
  fi
  for r in $roots; do
    for p in "$r/$name" "$r/bin/$name"; do
      if [ -x "$p" ]; then
        printf '%s\n' "$p"
        return 0
      fi
    done
  done
  if [ -x "$INSTALL_DIR/bin/$name" ]; then
    printf '%s\n' "$INSTALL_DIR/bin/$name"
    return 0
  fi
  return 1
}


sha256_of() {
  # Print SHA-256 of a file (macOS shasum or Linux sha256sum).
  local f=$1
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$f" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$f" | awk '{print $1}'
  else
    die "neither shasum nor sha256sum is available"
  fi
}

verify_sha256() {
  local file=$1
  local expected=$2
  local got
  [ -f "$file" ] || die "file not found for SHA-256 check: $file"
  [ -n "$expected" ] || die "empty expected SHA-256 for $file"
  case "$expected" in
    *'<UNVERIFIED:'*|REPLACE_ME|TODO_SHA|CHANGEME)
      die "expected SHA-256 for $file is a placeholder; refusing to proceed"
      ;;
  esac
  got=$(sha256_of "$file")
  if [ "$got" != "$expected" ]; then
    die "SHA-256 mismatch for $file
  expected: $expected
  got:      $got
STOP and report to the owner. Do not ignore this."
  fi
  log "SHA-256 OK: $(basename -- "$file") $got"
}

bytes_to_gib() {
  # Integer-ish GiB with 2 decimals via awk.
  awk -v b="$1" 'BEGIN { printf "%.2f", b / 1073741824 }'
}

free_disk_bytes() {
  local path=$1
  # POSIX-ish: df -k on both macOS and Linux. Use 1024-byte blocks.
  df -k "$path" | awk 'NR==2 { print $4 * 1024 }'
}

memsize_bytes_macos() {
  sysctl -n hw.memsize
}

require_confirmed_platform() {
  detect_platform
  case "$INKLING_PLATFORM" in
    macos-arm64|wsl-cuda)
      return 0
      ;;
    linux-cuda)
      # Native Linux CUDA is not a documented owner target. Dry-run may proceed.
      if is_dry_run; then
        log "platform=$INKLING_PLATFORM (not an owner target; dry-run continues)"
        return 0
      fi
      die "native Linux (non-WSL) is not a documented target for this package. STOP and report to the owner. Detected: $INKLING_OS $INKLING_ARCH"
      ;;
    *)
      if is_dry_run; then
        log "platform=$INKLING_PLATFORM (unsupported; dry-run continues)"
        return 0
      fi
      die "unsupported platform $INKLING_OS/$INKLING_ARCH. This package supports macOS arm64 (M1 Max, 64 GB) and WSL2 + NVIDIA CUDA (Zenbook). STOP and report."
      ;;
  esac
}
