# Siliconcordat Cut, built bundle snapshot (2026-11-13)

Generated snapshot of `siliconcordat-cut/` as built by `scripts/build_siliconcordat_cut_bundle.py` with `SILICONCORDAT_CUT_HOST=production` on 2026-11-13. It is not source. The source and the build pipeline live in this repository (`siliconcordat-cut/`, `scripts/build_siliconcordat_cut_bundle.py`, `workers/siliconcordat-cut.mjs`, `wrangler.siliconcordat-cut*.jsonc`). `dist-cut/` is gitignored here so a fresh build does not dirty the tree.

Weft mirror inside it (`weft/` subtree) was built from the pinned `Moissanite-Labs/weft` commit recorded in `siliconcordat-cut/sources-manifest.json`.

To rebuild: `WEFT_REPO=/path/to/weft python3 scripts/build_siliconcordat_cut_bundle.py` (staging or production via `SILICONCORDAT_CUT_HOST`). Verification: `python3 scripts/verify_siliconcordat_cut_bundle.py`.
