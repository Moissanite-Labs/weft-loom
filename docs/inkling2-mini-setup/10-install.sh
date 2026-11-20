#!/usr/bin/env bash
# Install the pinned Unsloth llama.cpp prebuilt into INSTALL_DIR, plus a
# local Python venv with huggingface_hub. Source build is a fallback only.
set -euo pipefail
# shellcheck source=lib.sh
_sdir=$(dirname -- "$0")
_sdir=$(cd -- "$_sdir" && pwd)
. "$_sdir/lib.sh"
load_config
init_paths
detect_platform
require_confirmed_platform

LOG="$LOG_DIR/install.log"
MODE=${INKLING_INSTALL_MODE:-prebuilt} # prebuilt | source | upstream

case "$MODE" in
  prebuilt|source|upstream) ;;
  *) die "INKLING_INSTALL_MODE must be prebuilt, source, or upstream (got $MODE)" ;;
esac

log_to "$LOG" "install start mode=$MODE platform=$INKLING_PLATFORM"

# Official Homebrew llama.cpp (v1.0.0 / b12359) cannot run looped Mini yet.
# Do not brew install llama.cpp. See README facts table.
if command -v brew >/dev/null 2>&1 && ! is_dry_run; then
  if brew list llama.cpp >/dev/null 2>&1; then
    log_to "$LOG" "WARN: Homebrew llama.cpp is installed. This package will not use it. The formula is v1.0.0 / b12359, which predates upstream PR #32694 and does not load looped Mini. Leaving it untouched."
  fi
fi

asset=""
sha=""
strip=0
url_base="https://github.com/unslothai/llama.cpp/releases/download/${LLAMA_RELEASE_TAG}"

case "$INKLING_PLATFORM" in
  macos-arm64)
    asset=$LLAMA_MAC_ASSET
    sha=$LLAMA_MAC_ASSET_SHA256
    strip=$LLAMA_MAC_STRIP_COMPONENTS
    ;;
  wsl-cuda|linux-cuda)
    asset=$LLAMA_LINUX_CUDA12_ASSET
    sha=$LLAMA_LINUX_CUDA12_ASSET_SHA256
    strip=$LLAMA_LINUX_STRIP_COMPONENTS
    ;;
  *)
    if is_dry_run; then
      asset=$LLAMA_LINUX_CUDA12_ASSET
      sha=$LLAMA_LINUX_CUDA12_ASSET_SHA256
      strip=$LLAMA_LINUX_STRIP_COMPONENTS
      log_to "$LOG" "DRY-RUN: pretending linux cuda asset for unsupported platform"
    else
      die "no prebuilt asset mapped for platform $INKLING_PLATFORM"
    fi
    ;;
esac

download_and_verify() {
  local name=$1 url=$2 expected=$3 dest=$4
  if [ -f "$dest" ]; then
    log_to "$LOG" "already present: $dest — verifying SHA-256"
    if is_dry_run; then
      log_to "$LOG" "DRY-RUN: would verify $dest"
      return 0
    fi
    if [ "$(sha256_of "$dest")" = "$expected" ]; then
      log_to "$LOG" "SHA-256 already OK for $name"
      return 0
    fi
    log_to "$LOG" "existing file has the wrong SHA-256; re-downloading $name"
    rm -f "$dest"
  fi
  log_to "$LOG" "downloading $url (resumable)"
  if is_dry_run; then
    printf 'DRY-RUN: curl -L --retry 3 -C - -o %q %q\n' "$dest" "$url"
    return 0
  fi
  # -C - resumes a partial tarball. A completed file that then fails --fail
  # with HTTP 416 is retried as a fresh download.
  if ! curl -L --retry 3 -C - -o "$dest" "$url"; then
    log_to "$LOG" "resumable curl failed (possibly HTTP 416 on a complete file); retrying without resume"
    rm -f "$dest"
    curl -L --fail --retry 3 -o "$dest" "$url"
  fi
  verify_sha256 "$dest" "$expected"
}

install_upstream() {
  # Opt-in only, never automatic. Builds ggml-org llama.cpp at the #32694
  # merge so inkling2_loop GGUFs can load. UNVERIFIED until the load gate
  # passes on the owner's machine. The tarball SHA is not in the facts file.
  # If UPSTREAM_SOURCE_SHA256 is set, it is required. Otherwise this is
  # trust-on-first-use: the first successful fetch records the SHA under
  # $RESULTS_DIR and later fetches must match. Independently confirm it.
  local url dest src build cmake_args missing expected recorded got
  url="https://github.com/ggml-org/llama.cpp/archive/${UPSTREAM_LOOP_MERGE_COMMIT}.tar.gz"
  dest="$DOWNLOADS_DIR/llama.cpp-upstream-${UPSTREAM_LOOP_MERGE_COMMIT}.tar.gz"
  recorded="$RESULTS_DIR/upstream-source-sha256.txt"
  log_to "$LOG" "UPSTREAM MODE (opt-in, UNVERIFIED): build ggml-org llama.cpp at $UPSTREAM_LOOP_MERGE_COMMIT (PR #$UPSTREAM_LOOP_PR merge) into $UPSTREAM_DIR. This is for inkling2_loop files only. The Unsloth pin remains the default path."
  missing=""
  for cmd in cmake curl tar; do
    command -v "$cmd" >/dev/null 2>&1 || missing="$missing $cmd"
  done
  if ! command -v c++ >/dev/null 2>&1 && ! command -v clang++ >/dev/null 2>&1 && ! command -v g++ >/dev/null 2>&1; then
    missing="$missing C++ compiler"
  fi
  if [ -n "$missing" ]; then
    die "INKLING_INSTALL_MODE=upstream needs build tools that are missing:$missing. STOP and ask the owner before installing compilers / cmake / (WSL) CUDA toolkit (apt and sudo need the owner's ok). This path is never automatic."
  fi
  expected=${UPSTREAM_SOURCE_SHA256:-}
  if [ -z "$expected" ] && [ -f "$recorded" ]; then
    expected=$(cat "$recorded")
    log_to "$LOG" "using previously recorded trust-on-first-use SHA-256 from $recorded"
  fi
  if is_dry_run; then
    if [ -n "$expected" ]; then
      printf 'DRY-RUN: would curl -L --retry 3 -C - -o %q %q, verify SHA-256 %s, cmake-build into %q (UNVERIFIED)\n' "$dest" "$url" "$expected" "$UPSTREAM_DIR"
    else
      printf 'DRY-RUN: UPSTREAM_SOURCE_SHA256 unset; would download %q, record its SHA-256 in %q (trust-on-first-use, UNVERIFIED), then cmake-build into %q. Later fetches must match the recorded hash. Independently confirm it.\n' "$url" "$recorded" "$UPSTREAM_DIR"
    fi
    return 0
  fi
  if [ -n "$expected" ]; then
    download_and_verify "llama.cpp-upstream-${UPSTREAM_LOOP_MERGE_COMMIT}.tar.gz" "$url" "$expected" "$dest"
    mkdir -p "$RESULTS_DIR"
    printf '%s\n' "$expected" >"$recorded"
  else
    log_to "$LOG" "UPSTREAM_SOURCE_SHA256 is empty (not in the facts file). Trust-on-first-use: downloading $url and recording its SHA-256. UNVERIFIED. Confirm the hash independently."
    if [ -f "$dest" ]; then
      log_to "$LOG" "already present: $dest — will hash it"
    else
      if ! curl -L --retry 3 -C - -o "$dest" "$url"; then
        log_to "$LOG" "resumable curl failed; retrying without resume"
        rm -f "$dest"
        curl -L --fail --retry 3 -o "$dest" "$url"
      fi
    fi
    [ -f "$dest" ] || die "upstream tarball missing after download: $dest"
    got=$(sha256_of "$dest")
    mkdir -p "$RESULTS_DIR"
    printf '%s\n' "$got" >"$recorded"
    log_to "$LOG" "trust-on-first-use: recorded SHA-256 $got in $recorded. Later runs will require this hash. This is UNVERIFIED; the owner should confirm it (for example by comparing to a second fetch or a published digest). Do not invent a hash."
  fi
  src="$INSTALL_DIR/src/llama.cpp-upstream-src"
  mkdir -p "$src" "$UPSTREAM_DIR"
  tar -xzf "$dest" -C "$src" --strip-components=1
  build="$src/build"
  cmake_args=(-B "$build" -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF)
  if [ "$INKLING_PLATFORM" = "macos-arm64" ]; then
    cmake_args+=(-DGGML_CUDA=OFF)
  else
    if ! command -v nvcc >/dev/null 2>&1; then
      die "upstream source build on WSL needs the CUDA toolkit (nvcc). That install requires sudo and the owner's ok. STOP and ask."
    fi
    cmake_args+=(-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86)
  fi
  cmake "${cmake_args[@]}" -S "$src"
  cmake --build "$build" --config Release -j --target llama-cli llama-server llama-bench
  find "$build/bin" -maxdepth 1 -type f -name 'llama-*' -exec cp -f {} "$UPSTREAM_DIR/" \;
  log_to "$LOG" "upstream build copied to $UPSTREAM_DIR (UNVERIFIED until 35-loadcheck.sh passes)"
}

if [ "$MODE" = "upstream" ]; then
  install_upstream
elif [ "$MODE" = "prebuilt" ]; then
  tarball="$DOWNLOADS_DIR/$asset"
  download_and_verify "$asset" "$url_base/$asset" "$sha" "$tarball"
  if is_dry_run; then
    printf 'DRY-RUN: mkdir -p %q && tar -xzf %q -C %q --strip-components=%s\n' "$LLAMA_DIR" "$tarball" "$LLAMA_DIR" "$strip"
  else
    mkdir -p "$LLAMA_DIR"
    # Idempotent extract into LLAMA_DIR.
    if [ "$strip" -gt 0 ]; then
      tar -xzf "$tarball" -C "$LLAMA_DIR" --strip-components="$strip"
    else
      tar -xzf "$tarball" -C "$LLAMA_DIR"
    fi
  fi
else
  # Source fallback: official release source tarball (NOT git checkout of the
  # tag alone — the GitHub tag object SHA and the prebuilt source_commit differ;
  # see README). Building upstream ggml-org master is a future alternative
  # after a tagged release contains PR #32694; it is not this package's pin.
  tarball="$DOWNLOADS_DIR/$LLAMA_SOURCE_ASSET"
  download_and_verify "$LLAMA_SOURCE_ASSET" "$url_base/$LLAMA_SOURCE_ASSET" "$LLAMA_SOURCE_ASSET_SHA256" "$tarball"
  src="$INSTALL_DIR/src/llama.cpp-src"
  if is_dry_run; then
    printf 'DRY-RUN: extract source to %q and cmake build into %q\n' "$src" "$LLAMA_DIR"
  else
    mkdir -p "$src"
    tar -xzf "$tarball" -C "$src" --strip-components=1
    build="$src/build"
    cmake_args=(-B "$build" -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF)
    if [ "$INKLING_PLATFORM" = "macos-arm64" ]; then
      # Metal is default on macOS (CITED: ggml-org docs/build.md).
      cmake_args+=(-DGGML_CUDA=OFF)
    else
      # Apt/CUDA toolkit installs need sudo and the owner's ok.
      if ! command -v cmake >/dev/null 2>&1 || ! command -v nvcc >/dev/null 2>&1; then
        die "source build on WSL needs cmake and the CUDA toolkit. Those apt/toolkit installs require sudo and the owner's ok. STOP and report. Preferred path: INKLING_INSTALL_MODE=prebuilt (default)."
      fi
      cmake_args+=(-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86)
    fi
    cmake "${cmake_args[@]}" -S "$src"
    cmake --build "$build" --config Release -j --target llama-cli llama-server llama-bench
    mkdir -p "$LLAMA_DIR"
    # Copy built binaries next to any bundled libs if present.
    find "$build/bin" -maxdepth 1 -type f -name 'llama-*' -exec cp -f {} "$LLAMA_DIR/" \;
  fi
fi

if is_dry_run; then
  printf 'DRY-RUN: would run llama-server --version from %q (or %q if upstream)\n' "$LLAMA_DIR" "$UPSTREAM_DIR"
else
  server=$(find_llama_bin llama-server) || die "llama-server not found under $LLAMA_DIR or $UPSTREAM_DIR after install. STOP and report. Log: $LOG"
  log_to "$LOG" "llama-server=$server"
  "$server" --version >>"$LOG" 2>&1 || die "llama-server --version failed. STOP and report. Log: $LOG"
  # Best-effort: record version text. Do not invent a required string.
  "$server" --version || true
fi

# Local venv for huggingface_hub (not system pip).
if is_dry_run; then
  printf 'DRY-RUN: python3 -m venv %q && %q/bin/pip install -U pip huggingface_hub\n' "$VENV_DIR" "$VENV_DIR"
else
  if [ ! -x "$VENV_DIR/bin/python" ]; then
    python3 -m venv "$VENV_DIR"
  fi
  # pip install is idempotent enough with -U.
  "$VENV_DIR/bin/python" -m pip install -U pip huggingface_hub
  if [ -x "$VENV_DIR/bin/hf" ]; then
    log_to "$LOG" "hf CLI: $VENV_DIR/bin/hf"
  elif "$VENV_DIR/bin/python" -c 'import huggingface_hub' 2>/dev/null; then
    log_to "$LOG" "huggingface_hub imported; hf entrypoint missing — 20-download.sh will use python -m huggingface_hub"
  else
    die "huggingface_hub install did not work. STOP and report. Log: $LOG"
  fi
fi

log_to "$LOG" "install PASSED"
