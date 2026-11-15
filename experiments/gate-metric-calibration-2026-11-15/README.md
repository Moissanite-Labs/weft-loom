# Gate-metric calibration: which distance predicts behaviour change?

## Question

The Weft gate accepts a weight update when it stays within a fixed distance of a saved baseline. Does that distance, or any other distance, predict how much the model's behaviour changes? This is the study that [issue 7](https://github.com/Moissanite-Labs/weft-loom/issues/7) asks for.

## Status

`design`

This commit holds the derivation, the preregistration, the two programs and the pilot. The confirmatory run has not been made. The status changes when its results are committed.

## Preregistration

[PREREG.md](PREREG.md), committed and pushed before the confirmatory run. It lists the predictions, the pass rule and the one change of design made after the pilot. [THEORY.md](THEORY.md) holds the derivations the predictions come from.

## How to rerun

Needs Python 3.12 with NumPy, and CPU PyTorch for the transformer. Run from this folder inside a weft-loom checkout. `calib.py` imports the E13 record beside it.

```
python3 calib.py --seeds 900 901 --out pilot.json
python3 calib_tf.py --seeds 900 901 --out pilot_tf.json
```

The pilot ran on one Apple Silicon Mac, macOS, Python 3.12.15, NumPy 2.5.4, PyTorch 2.15.0. One MLP host takes about 90 seconds and one transformer host about four minutes.

## Results

None yet. `pilot/` holds the output of the two pilot hosts per architecture. Pilot numbers set the design and are not results.

## Limits

See "What this cannot show" in the preregistration.

## Disclosure

Written and run by an AI agent session with human oversight.

> Automated posting by agentic team with human oversight.
