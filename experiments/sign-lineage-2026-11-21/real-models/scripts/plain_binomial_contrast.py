"""Post hoc, written for the published record: what the plain binomial would say where it does not apply.

For the pairs whose source side has no sign freedom (Pythia, Falcon-H1 Tiny) and whose target is SmolLM2-135M,
the valid exact law is the cluster law (out/stats/<pair>.json, field "p_two"). This prints, next to it, the
two-sided p-value that Binomial(m, 1/2) would give for the same count. Pure Python, exact integer arithmetic.

Run: python3 -I -B plain_binomial_contrast.py [--root <real-models folder>]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exactlaw as X  # noqa: E402


def show(p):
    """Two significant digits of a Fraction in (0, 1], computed exactly enough for display."""
    from fractions import Fraction
    p = Fraction(p)
    e = 0
    while p < 1:
        p *= 10
        e -= 1
    return "%.2fe%d" % (float(p), e)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(here))
    a = ap.parse_args()
    for name in ["py__s135", "falcon__s135"]:
        with open(os.path.join(a.root, "out", "stats", name + ".json")) as fh:
            st = json.load(fh)
        for tau in ["tau_0", "tau_0.3", "tau_0.5"]:
            r = st["ab"][tau]
            k, m = r["share"]["num"], r["share"]["den"]
            b = X.binom_test(m, k)
            print("%s %s share %d/%d | valid law: %s p_two %s | plain binomial p_two %s" % (
                name, tau, k, m, st["ab"]["law"], r["p_two"], show(b["p_two"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
