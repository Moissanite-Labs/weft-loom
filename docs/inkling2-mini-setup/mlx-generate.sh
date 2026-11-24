#!/usr/bin/env bash
# Experimental mlx-lm generate wrapper. Requires 60-mlx-setup.sh.
set -euo pipefail
# shellcheck source=lib.sh
_sdir=$(dirname -- "$0")
_sdir=$(cd -- "$_sdir" && pwd)
. "$_sdir/lib.sh"
load_config
init_paths

if [ "${INKLING_ENABLE_MLX:-0}" != "1" ]; then
  die "Set INKLING_ENABLE_MLX=1 and run 60-mlx-setup.sh first. This route is experimental (mlx-lm PR #2086, unmerged)."
fi

PROMPT=${1:-The secret to baking a good cake is}
MAXTOK=${2:-128}

if is_dry_run; then
  printf 'DRY-RUN: mlx_lm.generate --model <mlx-community/Inkling-2-Mini-4bit or native> -p %q -m %s\n' "$PROMPT" "$MAXTOK"
  exit 0
fi

[ -x "$VENV_DIR/bin/python" ] || die "venv missing"
repo=$(cat "$RESULTS_DIR/mlx-repo.txt" 2>/dev/null || echo "$MLX_REPO_4BIT")
if [ -f "$RESULTS_DIR/mlx-weights-dir.txt" ]; then
  repo=$(cat "$RESULTS_DIR/mlx-weights-dir.txt")
fi

# PR #2086 verification command used mlx_lm.generate (CITED).
if [ -x "$VENV_DIR/bin/mlx_lm.generate" ]; then
  exec "$VENV_DIR/bin/mlx_lm.generate" --model "$repo" -p "$PROMPT" -m "$MAXTOK"
else
  exec "$VENV_DIR/bin/python" -m mlx_lm generate --model "$repo" -p "$PROMPT" -m "$MAXTOK"
fi
