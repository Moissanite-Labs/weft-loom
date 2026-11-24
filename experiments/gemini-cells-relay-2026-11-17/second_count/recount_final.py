#!/usr/bin/env python3
"""The second reader's count, pointed at the runs the planned tables use.

`recount.py` is kept as the second reader wrote it: it reads replicates 0 to 2 from the run
root of the day, with the exam re-sit of the run that was later excluded. This wrapper,
added by the lead, changes only where it looks and which replicates it reads: the packed
logs in `../results/runs`, replicates 0, 1 and 4. The counting code is untouched, so its
header line still names the old set.

    python3 second_count/recount_final.py > second_count/recount_final.out
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import recount  # noqa: E402

recount.RUNS = str(HERE.parent / "results" / "runs")
recount.SEED_EXAM = str(HERE.parent / "results" / "seed_exam.json")
recount.REPS = ("-r0", "-r1", "-r4")
recount.RESIT = {}
print("RUN SET FOR THIS OUTPUT: replicates 0, 1 and 4 from results/runs (the header below is the program's own)\n")
recount.main()
