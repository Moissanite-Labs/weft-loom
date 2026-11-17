# Heddle prototype

A steering instrument for a small model, and the mathematics behind it. Supporting files for the design note
[`notes/heddle-steering-instrument.md`](../../heddle-steering-instrument.md). It is a prototype for an idea. It is not
part of the Weft runtime and nothing in weft depends on it.

The instrument is a page. It shows a network of 467 weights as a cloth: each point of the unit square is an input and
its three outputs are a colour, so the picture is the model's whole behaviour. You press treadles to change it, beat a
pick in, and read what was checked.

## Run it

```bash
python3 -m http.server 8000 --directory notes/prototypes/heddle
```

Open <http://localhost:8000>. No build step, no dependency, no network request. It needs a browser with ES modules.

## What is here

| File | What it holds |
|---|---|
| `heddle.py` | The reference implementation: host, Jacobian, shafts, treadles and tie-up, pins and shed, the gate port, the proved bound, weight roots, claims, fresh probes, dispute search, the hidden move, draft replay |
| `heddle.js` | The same mathematics for the browser and Node, plus `Loom`, one steering session |
| `ui.js`, `index.html` | The instrument. All checks are in `heddle.js`; these draw them |
| `make_vectors.py`, `vectors.json` | Values computed by the reference that the JavaScript must reproduce |
| `test_heddle.py`, `test_heddle.mjs` | The tests for each side |
| `make_sample_draft.mjs`, `sample-draft.json` | One recorded session, made by the JavaScript loom, replayed by the Python test |
| `replay_draft.py` | Checks a draft exported by the page, without the page |
| `vendor/`, `VENDORED.json` | weft's browser gate and its conformance vectors, copied unchanged and pinned by hash |

## Tests

```bash
python3 -m unittest discover -s notes/prototypes/heddle -p 'test_*.py'     # 27 tests
(cd notes/prototypes/heddle && node --test test_heddle.mjs)                # 13 tests
python3 notes/prototypes/heddle/replay_draft.py notes/prototypes/heddle/sample-draft.json
```

They need Python 3.12 or newer with NumPy, and Node 20 or newer. They are not run in this repository's CI. On
17 November 2026 they passed on one cloud container (Linux x86_64, Python 3.13.18, NumPy 2.5.3, Node 22.23.4).

## What is checked, and what is only stated

Checked by a test:

- **Same bits in both languages.** The generator, the initial weights, every weight root, claim id, event id and probe
  coordinate are equal bit for bit in Python and JavaScript.
- **The weight root is the CBC root.** `test_heddle.py` imports `cbc.py` from the committed-behaviour-change record and
  compares. A pick's roots are valid `w0_root` and `w1_root` fields of a CBC record.
- **The gate is weft's gate.** The page runs `site/assets/js/invariant-gate.js` from weft unchanged. The test fails if
  its hash changes, and runs it on weft's own vectors with the same five deferrals as weft's browser test.
- **A treadling is a weaving draft.** To first order, output change equals threading times tie-up times treadling, to
  `1e-10`.
- **Travel is behaviour.** One unit of travel along any shaft is a first-order output change of one unit.
- **Pins hold to first order**, and what reaches them is second order: halving a move quarters the leak.
- **The proved bound is never exceeded** (Theorem 1 of the calibration theory, slope 1 for tanh) on the moves tried.
- **A session replays.** A draft made in JavaScript rebuilds in Python to the same weight roots, gate verdicts and
  witnesses. A changed move, a reordered event, a snap whose witness does not refute, and a gesture too light for its
  tension are each caught.

Only stated, or true by construction:

- **The gesture.** A draft records the gesture the page saw. Nothing proves a person made it.
- **Admission is a sampled reading.** "No input found above the limit" is the result of a bounded search over 9,600
  inputs. A larger search could find one.
- **The display.** Colours are a fixed map of the three outputs, for the eye only. No check reads a colour.
- **The frame time on the page** is that browser on that machine. It is a reading, not a result.
- **The hidden move is first order.** It shows that room to hide exists. It is not the best an adversary could do.

The measurements made with this code are in the record
[`experiments/heddle-knob-range-2026-11-17/`](../../../experiments/heddle-knob-range-2026-11-17/).

## Vocabulary

Each word names one object in the code. The note gives the reasons for the choice.

| Word | What it is here |
|---|---|
| warp | the baseline weights, and whatever the pins hold still |
| shaft | a unit eigenvector of `G = J'J/(n m)` on the fit probes, with its eigenvalue |
| treadle | a named output pattern, tied to the shafts by least squares |
| tie-up | the matrix of those coefficients, shafts by treadles |
| heddle | a pinned input: its outputs must not move to first order |
| shed | the moves that pass the pins: the null space of the pins' Jacobian |
| pick | one committed move, with its weight root and its claim |
| snap | a move the gate accepted and one input refuted. The weights do not change |
| fell | the last committed weights |
| selvedge | the gate `‖w − w0‖ ≤ R` of weft's invariants |
| draft | the hash-chained record of a session |

## Licence and sources

Code here is under Apache-2.0, as the rest of this repository's code. The two files in `vendor/` come from
[Moissanite-Labs/weft](https://github.com/Moissanite-Labs/weft) at the commit in `VENDORED.json`, also Apache-2.0.

The four interaction ideas (a focus monitor, an attention lock, future vector steering, realtime re-generation) are
from [Spaceship IDE](https://github.com/chuanqisun/spaceship) by Chuanqi Sun (MIT licence), read at commit
`4ddd4d1061aa5f22113d5dd03462b3b3e5f506a6`. No code from it is used here.

## Disclosure

Written by an AI agent session (Claude) at the request of the repository owner. Not yet reviewed by a person.
