#!/usr/bin/env bash
# SHA-256 check of the active GGUF (and optional Q4 / mmproj).
# Writes a per-file verified marker keyed by the SHA so serve.sh can refuse
# an unverified file, including after a quant switch.
set -euo pipefail
# shellcheck source=lib.sh
_sdir=$(dirname -- "$0")
_sdir=$(cd -- "$_sdir" && pwd)
. "$_sdir/lib.sh"
load_config
init_paths

LOG="$LOG_DIR/verify.log"

verify_one() {
  local path=$1 sha=$2 expected_bytes=${3:-}
  local got_bytes
  [ -f "$path" ] || die "file missing: $path"
  if [ -n "$expected_bytes" ]; then
    got_bytes=$(wc -c <"$path" | tr -d ' ')
    if [ "$got_bytes" != "$expected_bytes" ]; then
      die "size mismatch for $path: expected $expected_bytes bytes, got $got_bytes. STOP and report."
    fi
  fi
  verify_sha256 "$path" "$sha"
  mark_verified "$path" "$sha"
}

if is_dry_run; then
  if [ -f "$RESULTS_DIR/active-file.txt" ]; then
    file=$(cat "$RESULTS_DIR/active-file.txt")
    sha=$(cat "$RESULTS_DIR/active-sha256.txt")
    printf 'DRY-RUN: would shasum -a 256 %q and compare to %s, then write verified/%s\n' "$MODELS_DIR/$file" "$sha" "$sha"
  else
    printf 'DRY-RUN: would verify the file recorded by 20-download.sh and write a per-SHA verified marker\n'
  fi
  if want_q4 || [ "${INKLING_QUANT:-}" = "ud-q4" ]; then
    printf 'DRY-RUN: would also verify optional Q4 %s (%s bytes, sha %s)\n' \
      "$UNSLOTH_Q4_FILE" "$UNSLOTH_Q4_BYTES" "$UNSLOTH_Q4_SHA256"
  fi
  exit 0
fi

[ -f "$RESULTS_DIR/active-file.txt" ] || die "no active file recorded. Run 20-download.sh first."
file=$(cat "$RESULTS_DIR/active-file.txt")
sha=$(cat "$RESULTS_DIR/active-sha256.txt")
path="$MODELS_DIR/$file"
expected_bytes=$(cat "$RESULTS_DIR/active-bytes.txt")
verify_one "$path" "$sha" "$expected_bytes"

if want_q4 || [ "${INKLING_QUANT:-}" = "ud-q4" ] || [ -f "$RESULTS_DIR/q4-file.txt" ]; then
  if [ -f "$MODELS_DIR/${UNSLOTH_Q4_FILE}" ]; then
    q4_bytes=${UNSLOTH_Q4_BYTES}
    if [ -f "$RESULTS_DIR/q4-bytes.txt" ]; then
      q4_bytes=$(cat "$RESULTS_DIR/q4-bytes.txt")
    fi
    verify_one "$MODELS_DIR/$UNSLOTH_Q4_FILE" "$UNSLOTH_Q4_SHA256" "$q4_bytes"
    log_to "$LOG" "Q4 verify PASSED $UNSLOTH_Q4_FILE"
  elif want_q4 || [ "${INKLING_QUANT:-}" = "ud-q4" ]; then
    die "WANT_Q4/INKLING_QUANT requested Q4 but $MODELS_DIR/$UNSLOTH_Q4_FILE is missing. Re-run 20-download.sh."
  fi
fi

if [ -f "$RESULTS_DIR/active-mmproj.txt" ]; then
  if want_vision; then
    mp=$(cat "$RESULTS_DIR/active-mmproj.txt")
    mpsha=$(cat "$RESULTS_DIR/active-mmproj-sha256.txt")
    verify_one "$MODELS_DIR/$mp" "$mpsha"
  else
    log_to "$LOG" "INKLING_USE_VISION is off; ignoring and clearing stale active-mmproj.txt"
    rm -f "$RESULTS_DIR/active-mmproj.txt" "$RESULTS_DIR/active-mmproj-sha256.txt"
  fi
fi

{
  printf 'status=PASS\n'
  printf 'time=%s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'file=%s\n' "$file"
  printf 'sha256=%s\n' "$sha"
} >"$RESULTS_DIR/verify-status.txt"
log_to "$LOG" "verify PASSED $file"
