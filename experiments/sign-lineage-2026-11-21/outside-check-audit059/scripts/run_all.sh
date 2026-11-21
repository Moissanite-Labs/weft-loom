#!/bin/bash
# Run every checker under the three interpreter modes and print output hashes.
#
# Usage: run_all.sh Q08_PAGE INDEX_PAGE GEMMA_PAGE WEM_DIR SILIQUANT_RESULTS
#   Q08_PAGE           your saved copy of https://qwen-neuron-map.pages.dev model page for Qwen3.5-0.8B (index.html)
#   INDEX_PAGE         your saved copy of the site's index page
#   GEMMA_PAGE         your saved copy of the site's Gemma 4 E4B model page
#   WEM_DIR            files from the public alphaxiv/weight-edit-minimization repository at commit 768d7340:
#                      frozen_weights_manifest.json, base_l15_down_proj_f32.npy, base_l19_down_proj_f32.npy,
#                      factors_layer15.npz, factors_layer19.npz
#   SILIQUANT_RESULTS  experiments/output-budget-gemma-e4b-2026-11-17/results.jsonl of Moissanite-Labs/siliquant
# The site states no license, so its pages are not included here. The page hashes the checks expect are in CHECK.md.
set -u
Q=$1; IX=$2; G=$3; W=$4; R=$5
cd "$(dirname "$0")/.." || exit 1
for tag in IB IOB IBW; do
  case $tag in
    IB) fl=(-I -B);; IOB) fl=(-I -O -B);; IBW) fl=(-I -B -W error);;
  esac
  python3 "${fl[@]}" scripts/adv_q08_join.py "$Q" "$W" > out/q08_$tag.txt 2>&1; echo "q08 $tag rc=$?"
  python3 "${fl[@]}" scripts/adv_q08_layers.py "$Q" "$W" > out/q08layers_$tag.txt 2>&1; echo "layers $tag rc=$?"
  python3 "${fl[@]}" scripts/adv_family_scan.py "$Q" "$W/frozen_weights_manifest.json" > out/famscan_$tag.txt 2>&1; echo "famscan $tag rc=$?"
  python3 "${fl[@]}" scripts/adv_index_kinds.py "$IX" > out/index_kinds_$tag.txt 2>&1; echo "kinds $tag rc=$?"
  python3 "${fl[@]}" scripts/adv_gemma.py "$G" "$R" > out/gemma_$tag.txt 2>&1; echo "gemma $tag rc=$?"
  python3 "${fl[@]}" scripts/adv_z2.py > out/z2_$tag.txt 2>&1; echo "z2 $tag rc=$?"
  python3 "${fl[@]}" scripts/adv_extra.py "$W" > out/extra_$tag.txt 2>&1; echo "extra $tag rc=$?"
done
cd out
for b in q08 q08layers famscan index_kinds gemma z2 extra; do
  for tag in IB IOB IBW; do printf '%s %s\n' "$(shasum -a 256 ${b}_$tag.txt | cut -c1-16)" "${b}_$tag.txt"; done
done
