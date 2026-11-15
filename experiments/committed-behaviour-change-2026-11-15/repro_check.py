#!/usr/bin/env python3
"""Phase 0 check: the E13 route rebuilds bit-identically from seeds alone.

Builds one admission pair twice in this process and prints the CBC weight
roots of the host and the benign splice for each build. Run the script twice
and diff the outputs for the cross-process reading. Same machine only;
cross-host replay is Experiment A.

Usage: python3 repro_check.py [pair_index]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cbc  # noqa: E402
import expb  # noqa: E402

adm = expb.adm


def main():
    i = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    for trial in (1, 2):
        P = adm.build_pair(i, None)
        org_b, _ = adm.splice(P, P["pkt"])
        print(f"trial {trial} host_root {cbc.weight_root(P['host'])}")
        print(f"trial {trial} benign_root {cbc.weight_root(org_b)}")


if __name__ == "__main__":
    main()
