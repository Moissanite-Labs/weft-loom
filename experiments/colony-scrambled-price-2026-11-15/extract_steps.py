#!/usr/bin/env python3
"""Write the rows the counts need from the per-cell logs of the scrambled-price runs.

The per-cell logs hold shell output from the run machine, so they stay there.
This keeps, for every cell, the laws row, one row per paid step, one row per
act (its kind and the model it sets for the next step, no text), and the
downshift, bad-reply and death rows. It also lists the SHA-256 of each log.

Usage: python3 extract_steps.py [exp_folder]     (writes results/steps.jsonl and results/raw_logs.sha256)
"""
import glob
import hashlib
import json
import sys
from pathlib import Path

EXP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Work" / "razi-cells" / "exp"
OUT = Path(__file__).resolve().parent / "results"
rows, hashes = [], []
for path in sorted(glob.glob(str(EXP / "sc*" / "*" / "log.jsonl"))):
    run, kit = Path(path).parts[-3], Path(path).parts[-2]
    hashes.append(f"{hashlib.sha256(Path(path).read_bytes()).hexdigest()}  {run}/{kit}/log.jsonl")
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        r = {"run": run, "kit": kit, "t": d.get("t")}
        ev = d.get("event")
        if ev == "laws":
            r.update(kind="laws", price_show=d["price_show"], price_scramble=d.get("price_scramble", False), start=d["start"][0])
        elif "usage" in d and "model" in d:
            r.update(kind="step", step=d["step"], model=d["model"], charge=d["cost"], usd=(d["usage"] or {}).get("usd"))
        elif "act" in d:
            nxt = d["next"][0] if "next" in d else None
            r.update(kind="act", step=d["step"], do=d["act"].get("do"), model=d["model"], next=nxt)
        elif ev == "downshift":
            r.update(kind="downshift", frm=d["frm"], to=d["to"], e=d["e"])
        elif "bad_reply" in d:
            r.update(kind="bad_reply", step=d["step"])
        elif ev == "death":
            r.update(kind="death", why=d.get("why"), e=d.get("e"), age=d.get("age"))
        else:
            continue
        rows.append(r)
(OUT / "steps.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
(OUT / "raw_logs.sha256").write_text("\n".join(hashes) + "\n", encoding="utf-8")
print(f"{len(rows)} rows from {len(hashes)} cell logs")
