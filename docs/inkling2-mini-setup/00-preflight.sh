#!/usr/bin/env bash
# Preflight checks. Read-only except for INSTALL_DIR/logs when not dry-run.
set -euo pipefail
# shellcheck source=lib.sh
_sdir=$(dirname -- "$0")
_sdir=$(cd -- "$_sdir" && pwd)
. "$_sdir/lib.sh"
load_config
init_paths
detect_platform
require_confirmed_platform

LOG="$LOG_DIR/preflight.log"
if ! is_dry_run; then
  mkdir -p "$LOG_DIR"
fi

fail=0
note() { log_to "$LOG" "$*"; }
warn() { log_to "$LOG" "WARN: $*"; }
bad()  { log_to "$LOG" "FAIL: $*"; fail=1; }

note "preflight start"
note "platform=$INKLING_PLATFORM os=$INKLING_OS arch=$INKLING_ARCH wsl=$INKLING_IS_WSL"
note "INSTALL_DIR=$INSTALL_DIR (override with INKLING_INSTALL_DIR)"
note "dry_run=${INKLING_DRY_RUN:-0}"

# --- macOS ---
if [ "$INKLING_PLATFORM" = "macos-arm64" ]; then
  if command -v sw_vers >/dev/null 2>&1; then
    note "macOS product=$(sw_vers -productName 2>/dev/null || true) version=$(sw_vers -productVersion 2>/dev/null || true) build=$(sw_vers -buildVersion 2>/dev/null || true)"
  else
    bad "sw_vers not found; cannot read macOS version"
  fi

  chip="unknown"
  if command -v sysctl >/dev/null 2>&1; then
    chip=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || sysctl -n hw.model 2>/dev/null || echo unknown)
  fi
  note "chip=$chip"
  case "$chip" in
    *M1*Max*)
      note "chip matches expected M1 Max"
      ;;
    *)
      warn "expected Apple M1 Max; got '$chip'. Continuing only if RAM and arch checks pass. Do not invent a different build."
      ;;
  esac

  if command -v sysctl >/dev/null 2>&1; then
    mem=$(sysctl -n hw.memsize)
    mem_gib=$(bytes_to_gib "$mem")
    note "hw.memsize=$mem bytes (~${mem_gib} GiB)"
    # 64 GB class: accept 60–68 GiB. 32 GB branch was dropped.
    awk -v m="$mem" 'BEGIN { exit !((m >= 60*1024*1024*1024) && (m <= 68*1024*1024*1024)) }' || {
      if awk -v m="$mem" 'BEGIN { exit !(m < 48*1024*1024*1024) }'; then
        bad "this package is for the owner's 64 GB M1 Max. Detected ~${mem_gib} GiB. The 32 GB branch was dropped. STOP and report to the owner."
      else
        bad "unified RAM ~${mem_gib} GiB is not the expected 64 GB class. STOP and report to the owner."
      fi
    }
  else
    bad "sysctl not found; cannot read hw.memsize"
  fi

  if command -v xcode-select >/dev/null 2>&1 && xcode-select -p >/dev/null 2>&1; then
    note "Xcode CLT path=$(xcode-select -p)"
  else
    bad "Xcode Command Line Tools not found (xcode-select -p failed). Install CLT, then re-run. Do not improvise."
  fi

  if command -v brew >/dev/null 2>&1; then
    note "homebrew=$(command -v brew) version=$(brew --version 2>/dev/null | head -n1 || true)"
  else
    if command -v python3 >/dev/null 2>&1; then
      note "Homebrew not found; python3 is present ($(command -v python3)), so Homebrew is not required for the default prebuilt path. This package does not install Homebrew and does not install official brew llama.cpp (that formula cannot run looped Mini yet)."
    else
      bad "python3 not found and Homebrew is not installed. On the Mac, install Python (Homebrew is one documented route: brew install python — owner decision). This package does not install Homebrew itself and does not install official brew llama.cpp."
    fi
  fi
fi

# --- WSL2 / NVIDIA ---
if [ "$INKLING_PLATFORM" = "wsl-cuda" ] || [ "$INKLING_PLATFORM" = "linux-cuda" ]; then
  if [ -r /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    note "linux_os=${PRETTY_NAME:-$NAME $VERSION_ID}"
  fi
  if [ -r /proc/meminfo ]; then
    mem_kb=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
    mem=$((mem_kb * 1024))
    note "MemTotal=$mem bytes (~$(bytes_to_gib "$mem") GiB). If this looks far below 32 GB, check Windows .wslconfig memory=. Do not change .wslconfig without the owner's ok."
  fi
  if command -v nvidia-smi >/dev/null 2>&1; then
    note "nvidia-smi=$(command -v nvidia-smi)"
    if is_dry_run; then
      note "DRY-RUN: would run nvidia-smi"
    else
      nvidia-smi >>"$LOG" 2>&1 || bad "nvidia-smi failed. The NVIDIA driver comes from Windows; fix that first. Do not invent a CPU-only path."
      # Record a short GPU line if present.
      nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null | while IFS= read -r line; do
        note "gpu=$line"
      done || true
    fi
  else
    bad "nvidia-smi not found. On WSL2 the driver is installed on Windows. STOP and report. Do not apt-install a driver inside WSL."
  fi
fi

# --- disk space vs chosen quant ---
# Default file by platform. BF16 is opt-in only.
quant=${INKLING_QUANT:-auto}
vision=${INKLING_USE_VISION:-0}
need=$DISK_HEADROOM_BYTES
case "$quant" in
  auto)
    if [ "$INKLING_PLATFORM" = "macos-arm64" ]; then
      need=$((need + UNSLOTH_Q8_BYTES))
      note "planned primary weights: $UNSLOTH_Q8_FILE ($(bytes_to_gib "$UNSLOTH_Q8_BYTES") GiB, arch inkling2). ggml-org Q8_0 is inkling2_loop and is NOT an automatic fallback on $LLAMA_RELEASE_TAG."
    else
      need=$((need + UNSLOTH_IQ2_BYTES))
      note "planned primary weights: $UNSLOTH_IQ2_FILE ($(bytes_to_gib "$UNSLOTH_IQ2_BYTES") GiB) for 8 GB VRAM."
    fi
    ;;
  ud-q8)
    need=$((need + UNSLOTH_Q8_BYTES))
    ;;
  ud-q4)
    # 8-bit (or IQ2 on Zenbook) stays the default; Q4 bytes are added below.
    if [ "$INKLING_PLATFORM" = "macos-arm64" ]; then
      need=$((need + UNSLOTH_Q8_BYTES))
    else
      need=$((need + UNSLOTH_IQ2_BYTES))
    fi
    ;;
  ggml-q8)
    need=$((need + GGML_Q8_BYTES))
    if ! using_upstream; then
      bad "INKLING_QUANT=ggml-q8 is inkling2_loop and cannot load on pinned $LLAMA_RELEASE_TAG. Opt-in UNVERIFIED path: INKLING_INSTALL_MODE=upstream at $UPSTREAM_LOOP_MERGE_COMMIT."
    fi
    ;;
  bf16)
    need=$((need + GGML_BF16_BYTES))
    warn "BF16 is optional and NOT the default. Its header is inkling2_loop, so it needs the opt-in upstream build. On 64 GB it may hit Metal working-set limits with long context (ESTIMATE; see README). iogpu.wired_limit_mb is an owner decision (requires sudo)."
    if ! using_upstream; then
      bad "INKLING_QUANT=bf16 is inkling2_loop and cannot load on pinned $LLAMA_RELEASE_TAG. Opt-in UNVERIFIED path: INKLING_INSTALL_MODE=upstream."
    fi
    if [ "$INKLING_PLATFORM" = "wsl-cuda" ] || [ "$INKLING_PLATFORM" = "linux-cuda" ]; then
      bad "BF16 (~$(bytes_to_gib "$GGML_BF16_BYTES") GiB) is not a Zenbook path (8 GB VRAM)."
    fi
    ;;
  iq4)
    need=$((need + GGML_IQ4_BYTES))
    if ! using_upstream; then
      bad "INKLING_QUANT=iq4 is inkling2_loop and cannot load on pinned $LLAMA_RELEASE_TAG."
    fi
    ;;
  iq2)
    need=$((need + UNSLOTH_IQ2_BYTES))
    ;;
  *)
    bad "unknown INKLING_QUANT=$quant (allowed: auto, ud-q8, ud-q4, iq2, and inkling2_loop files ggml-q8/bf16/iq4 only with INKLING_INSTALL_MODE=upstream). Set WANT_Q4=1 to download the optional 4-bit."
    ;;
esac
if [ "$vision" = "1" ]; then
  need=$((need + UNSLOTH_MMPROJ_BYTES))
  note "vision projector included (+$(bytes_to_gib "$UNSLOTH_MMPROJ_BYTES") GiB) — opt-in only; default is text-only"
fi
if want_q4 || [ "$quant" = "ud-q4" ]; then
  need=$((need + UNSLOTH_Q4_BYTES))
  note "optional Q4 also requested: $UNSLOTH_Q4_FILE ($(bytes_to_gib "$UNSLOTH_Q4_BYTES") GiB). 8-bit stays the default runtime model."
  if [ "$INKLING_PLATFORM" = "wsl-cuda" ] || [ "$INKLING_PLATFORM" = "linux-cuda" ]; then
    warn "UD-Q4_K_XL is 16.42 GiB (Unsloth 4-bit class 17–18 GB). On 8 GB VRAM it is not the recommended Zenbook quant (that is UD-IQ2_XXS). Optional for fast iteration only."
  fi
fi
# llama.cpp tarball
if [ "$INKLING_PLATFORM" = "macos-arm64" ]; then
  need=$((need + LLAMA_MAC_ASSET_BYTES))
else
  need=$((need + LLAMA_LINUX_CUDA12_ASSET_BYTES))
fi

# df target: INSTALL_DIR if it exists, else HOME or /
df_target=$INSTALL_DIR
if [ ! -d "$df_target" ]; then
  df_target=${HOME:-/}
fi
if is_dry_run && [ ! -d "$df_target" ]; then
  note "DRY-RUN: would check free disk at $df_target vs need=$need (~$(bytes_to_gib "$need") GiB including $(bytes_to_gib "$DISK_HEADROOM_BYTES") GiB package-policy headroom)"
else
  free=$(free_disk_bytes "$df_target")
  note "free_disk=$free bytes (~$(bytes_to_gib "$free") GiB) at $df_target; need ~$(bytes_to_gib "$need") GiB"
  if [ "$free" -lt "$need" ]; then
    bad "not enough free disk (have ~$(bytes_to_gib "$free") GiB, need ~$(bytes_to_gib "$need") GiB including headroom). STOP and report."
  fi
fi

# --- port-in-use (warn only) ---
if command -v lsof >/dev/null 2>&1; then
  if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    warn "port $PORT appears to be in use. serve.sh / smoke will fail to bind $HOST:$PORT until it is free."
  fi
elif command -v ss >/dev/null 2>&1; then
  if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
    warn "port $PORT appears to be in use. serve.sh / smoke will fail to bind $HOST:$PORT until it is free."
  fi
fi

# --- tools ---
for cmd in curl tar awk; do
  if command -v "$cmd" >/dev/null 2>&1; then
    note "found $cmd=$(command -v "$cmd")"
  else
    bad "missing command: $cmd"
  fi
done
if command -v shasum >/dev/null 2>&1; then
  note "found shasum=$(command -v shasum)"
elif command -v sha256sum >/dev/null 2>&1; then
  note "found sha256sum=$(command -v sha256sum)"
else
  bad "need shasum (macOS) or sha256sum (Linux)"
fi
if command -v python3 >/dev/null 2>&1; then
  note "python3=$(command -v python3) version=$(python3 --version 2>&1)"
else
  if [ "$INKLING_PLATFORM" = "macos-arm64" ]; then
    bad "python3 not found. On the Mac, install Python via Homebrew (brew install python) — a documented Homebrew install, not a system change. Then re-run."
  else
    bad "python3 not found. On WSL, installing python3 / python3-venv / python3-pip via apt needs sudo and the owner's ok. STOP and report."
  fi
fi

if [ "$fail" -ne 0 ]; then
  if is_dry_run; then
    note "preflight recorded FAIL items above, but INKLING_DRY_RUN=1 so this is not a hard stop (this host is not the owner's Mac or Zenbook)"
    log "preflight DRY-RUN finished with recorded issues"
    exit 0
  fi
  note "preflight FAILED"
  die "preflight failed. See ${LOG:-the log above}. STOP and report to the owner. Do not improvise."
fi
note "preflight PASSED"
