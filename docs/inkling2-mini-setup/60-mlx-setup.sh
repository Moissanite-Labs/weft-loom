#!/usr/bin/env bash
# Optional, experimental MLX route (macOS only).
# Inkling support is not in mlx-lm v0.32.2; it exists only in open draft
# PR #2086, pinned here to commit $MLX_LM_COMMIT. Scripts refuse to run
# if that SHA is a placeholder or if INKLING_ENABLE_MLX is not 1.
set -euo pipefail
# shellcheck source=lib.sh
_sdir=$(dirname -- "$0")
_sdir=$(cd -- "$_sdir" && pwd)
. "$_sdir/lib.sh"
load_config
init_paths
detect_platform

LOG="$LOG_DIR/mlx-setup.log"

if [ "${INKLING_ENABLE_MLX:-0}" != "1" ]; then
  die "MLX is optional and experimental. Set INKLING_ENABLE_MLX=1 after the owner agrees, then re-run. mlx-lm PR #2086 is an unmerged draft; PyPI v0.32.2 does not include Inkling."
fi

case "$MLX_LM_COMMIT" in
  *'<UNVERIFIED:'*|REPLACE_ME|"")
    die "MLX_LM_COMMIT is missing or a placeholder in config.env. Refusing to proceed."
    ;;
esac

if [ "$INKLING_PLATFORM" != "macos-arm64" ] && ! is_dry_run; then
  die "MLX is Apple Silicon only. This platform is $INKLING_PLATFORM."
fi

which_weights=${INKLING_MLX_WEIGHTS:-4bit} # 4bit | native

if is_dry_run; then
  printf 'DRY-RUN: %q/bin/pip install -U git+%s@%s\n' "$VENV_DIR" "$MLX_LM_GIT_URL" "$MLX_LM_COMMIT"
  if [ "$which_weights" = "4bit" ]; then
    printf 'DRY-RUN: would download %s (4 shards, ~17.31 GiB) and verify SHA-256s\n' "$MLX_REPO_4BIT"
  else
    printf 'DRY-RUN: would download native checkpoint %s and verify SHA-256 of %s, %s, and %s (HF lfs.oid)\n' \
      "$MLX_REPO_NATIVE" "$MLX_NATIVE_WEIGHT" "$MLX_NATIVE_MTP" "$MLX_NATIVE_TOKENIZER"
  fi
  exit 0
fi

[ -x "$VENV_DIR/bin/python" ] || die "venv missing. Run 10-install.sh first."
log_to "$LOG" "installing mlx-lm from $MLX_LM_GIT_URL @$MLX_LM_COMMIT (PR #$MLX_LM_PR, experimental)"
"$VENV_DIR/bin/python" -m pip install -U "git+${MLX_LM_GIT_URL}@${MLX_LM_COMMIT}"

# Confirm the pin is what got installed, as far as git metadata allows.
"$VENV_DIR/bin/python" -c "import mlx_lm,sys; print('mlx_lm', getattr(mlx_lm,'__file__', '?'))"

if [ "$which_weights" = "4bit" ]; then
  dest="$INSTALL_DIR/mlx-models/Inkling-2-Mini-4bit"
  mkdir -p "$dest"
  if [ -x "$VENV_DIR/bin/hf" ]; then
    HF_HOME="$HF_HOME" "$VENV_DIR/bin/hf" download "$MLX_REPO_4BIT" --local-dir "$dest"
  else
    "$VENV_DIR/bin/python" -c "
from huggingface_hub import snapshot_download
import sys
snapshot_download(repo_id=sys.argv[1], local_dir=sys.argv[2])
" "$MLX_REPO_4BIT" "$dest"
  fi
  verify_sha256 "$dest/$MLX_4BIT_SHARD1" "$MLX_4BIT_SHARD1_SHA256"
  verify_sha256 "$dest/$MLX_4BIT_SHARD2" "$MLX_4BIT_SHARD2_SHA256"
  verify_sha256 "$dest/$MLX_4BIT_SHARD3" "$MLX_4BIT_SHARD3_SHA256"
  verify_sha256 "$dest/$MLX_4BIT_SHARD4" "$MLX_4BIT_SHARD4_SHA256"
  printf '%s\n' "$dest" >"$RESULTS_DIR/mlx-weights-dir.txt"
  printf '%s\n' "$MLX_REPO_4BIT" >"$RESULTS_DIR/mlx-repo.txt"
else
  dest="$INSTALL_DIR/mlx-models/Inkling-2-Mini"
  mkdir -p "$dest"
  if [ -x "$VENV_DIR/bin/hf" ]; then
    HF_HOME="$HF_HOME" "$VENV_DIR/bin/hf" download "$MLX_REPO_NATIVE" --local-dir "$dest"
  else
    HF_HOME="$HF_HOME" "$VENV_DIR/bin/python" -c "
from huggingface_hub import snapshot_download
import sys
snapshot_download(repo_id=sys.argv[1], local_dir=sys.argv[2])
" "$MLX_REPO_NATIVE" "$dest"
  fi
  verify_sha256 "$dest/$MLX_NATIVE_WEIGHT" "$MLX_NATIVE_WEIGHT_SHA256"
  verify_sha256 "$dest/$MLX_NATIVE_MTP" "$MLX_NATIVE_MTP_SHA256"
  verify_sha256 "$dest/$MLX_NATIVE_TOKENIZER" "$MLX_NATIVE_TOKENIZER_SHA256"
  printf '%s\n' "$dest" >"$RESULTS_DIR/mlx-weights-dir.txt"
  printf '%s\n' "$MLX_REPO_NATIVE" >"$RESULTS_DIR/mlx-repo.txt"
  log_to "$LOG" "native weights verified under $dest"
fi

log_to "$LOG" "mlx setup PASSED (experimental)"
log "mlx setup PASSED (experimental). Use ./mlx-generate.sh"
