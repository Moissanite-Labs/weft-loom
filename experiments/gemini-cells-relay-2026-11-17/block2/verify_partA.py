#!/usr/bin/env python3
"""Checks of part A's rows that the planned analysis does not make. Not preregistered; it
reads the same rows as block2/analyze_a.py and changes nothing.

    python3 -I -B block2/verify_partA.py block2/partA/assay2-partA-*.jsonl > block2/verify_partA.out

1. Each assay ran the harness it names: its builder hash equals the archived final harness
   of that run and slot, or the seed's hash for seed rows. (The four shards unpacked the
   archives at the same moment; one shard crashed on that race before any model call, and
   this check shows that no running shard read a half-unpacked harness.)
2. Every planned row is present exactly once, and no secret repeats.
3. Model errors, refused calls and reruns, by row kind, and the rows that had a usage-limit
   rerun anywhere (the account ran out of allowance for a while during the run; the
   frozen code waits, probes, and reruns the cut episode or build from the start).
4. Spend by the rows' own counts, against the ledger total if given.
"""
import glob
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import run  # noqa: E402
from referee import relay  # noqa: E402
from referee.bench import tree_hash  # noqa: E402


def main(argv):
    ledger = None
    if argv[:1] == ["--ledger"]:
        ledger, argv = json.loads(Path(argv[1]).read_text()), argv[2:]
    rows = [json.loads(line) for pattern in argv for path in sorted(glob.glob(pattern)) for line in open(path)]
    rows = [r for r in rows if r.get("kind") == "assay2"]
    seed_h = tree_hash(relay.SEED_DIR)
    final = {}
    for d in sorted((HERE / "results" / "runs").iterdir()):
        end = [json.loads(line) for line in open(d / "log.jsonl") if '"kind": "end"' in line][-1]
        for slot, h in end["harness"].items():
            final[(d.name, slot)] = h
    wrong = [r for r in rows if r["builder_harness"] != (seed_h if r["run"] is None else final.get((r["run"], r["slot"])))]
    planned = Counter(run.assay2_plan(sorted({k[0] for k in final}), ["A", "B"], 3, 12, "partA"))
    have = Counter((r["rep"], r["run"], r["slot"]) for r in rows)
    missing = sorted(set(planned) - set(have), key=str)
    extra = sorted(set(have) - set(planned), key=str)
    doubled = sorted((k for k, n in have.items() if n > 1), key=str)
    secrets = Counter(r["secret"] for r in rows)
    print(f"rows: {len(rows)} of {sum(planned.values())} planned")
    print(f"1. builder harness differs from the archived one: {len(wrong)}"
          + "".join(f"\n   {r['run']} {r['slot']} rep {r['rep']}" for r in wrong))
    print(f"2. missing {len(missing)}, not planned {len(extra)}, present more than once {len(doubled)},"
          f" repeated secrets {sum(1 for n in secrets.values() if n > 1)}")
    for k in missing[:20]:
        print(f"   missing: {k}")
    errors = Counter()
    for r in rows:
        errors["build model errors"] += r.get("build_model_errors") or 0
        errors["boot model errors"] += (r.get("boot") or {}).get("model_errors") or 0
        for key in ("inc_report", "cand_report", "base_report"):
            rep = r.get(key) or {}
            errors[f"{key.split('_')[0]} benchmark model errors"] += rep.get("model_errors") or 0
            errors[f"{key.split('_')[0]} episode reruns"] += sum(e.get("reruns") or 0 for e in rep.get("episodes", []))
            errors[f"{key.split('_')[0]} episode usage-limit reruns"] += sum(e.get("limit_reruns") or 0 for e in rep.get("episodes", []))
            errors[f"{key.split('_')[0]} episode timeouts"] += sum(1 for e in rep.get("episodes", []) if e.get("timed_out"))
        errors["build reruns"] += r.get("build_reruns") or 0
        errors["build usage-limit reruns"] += r.get("build_limit_reruns") or 0
        errors["build timeouts"] += 1 if r.get("build_timed_out") else 0
        errors["boot usage-limit reruns"] += (r.get("boot") or {}).get("limit_reruns") or 0
    print("3. " + ", ".join(f"{k} {v}" for k, v in sorted(errors.items())))
    hit = [r for r in rows if r.get("build_limit_reruns") or (r.get("boot") or {}).get("limit_reruns")
           or any(e.get("limit_reruns") for key in ("inc_report", "cand_report", "base_report")
                  for e in (r.get(key) or {}).get("episodes", []))]
    print(f"   rows with a usage-limit rerun anywhere: {len(hit)}"
          + "".join(f"\n   {r['run']} {r['slot']} rep {r['rep']}: {r.get('outcome')}" for r in hit))
    outcomes = Counter(r.get("outcome") for r in rows)
    print("   outcomes: " + ", ".join(f"{k} {v}" for k, v in sorted(outcomes.items(), key=str)))
    usd = sum(r.get("usd") or 0 for r in rows)
    print(f"4. spend by the rows' own counts: {usd:.3f} dollars"
          + (f"; ledger: {ledger['usd']:.3f} dollars over {ledger.get('calls')} calls" if ledger else ""))
    return 1 if wrong or extra or doubled else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
