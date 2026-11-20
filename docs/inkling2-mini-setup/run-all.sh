#!/usr/bin/env bash
# Run the documented sequence: preflight, install, download, verify, load
# gate, smoke, bench. Stops on the first failure. Does not start the server.
set -euo pipefail
# shellcheck source=lib.sh
_sdir=$(dirname -- "$0")
_sdir=$(cd -- "$_sdir" && pwd)
. "$_sdir/lib.sh"
load_config
init_paths

_sdir=$(dirname -- "$0")
DIR=$(cd -- "$_sdir" && pwd)
for s in 00-preflight.sh 10-install.sh 20-download.sh 30-verify.sh 35-loadcheck.sh 40-smoke.sh 50-bench.sh; do
  log "===== $s ====="
  "$DIR/$s"
done
log "all steps PASSED. Start the server with: $DIR/serve.sh"
