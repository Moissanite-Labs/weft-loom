csvsum STATE: csvsum.py == c2_4.py (numpy vectorized parse, integer cents, bincount per cat, 4 threads, mmap stdin, pure-Python fallback `slow`). base.py = original pure-Python version.
VERIFIED: output == expected.txt and == ref.py (Decimal/csv reference) on 2M-row data.csv; also fresh 300k seed, variable-length cats 50k, negatives, no trailing newline, integer vals, header-only, pipe stdin all match ref.
REAL SPEED (my own runs of `sh assay.sh`): base 1.65-1.80; csvsum.py 5.1-6.7 (noisy, ~15% spread). So true gain is ~3-3.7x.
CAUTION: harness variants reported "+9978%" (medians 179 vs 1.776). I could NOT reproduce 179 by hand; 1/179 = 5.6 ms is not plausible for parsing 42 MB. Treat that number as a harness artifact, not a real result. Do not cite +9978%.
Lessons: 8 threads = no gain over 4 (5.27 vs 5.26). mmap helps slightly at T=8, mixed at T=4. cand1 (single-thread numpy) was 3.18.
Ideas not tried: fork workers instead of threads; fewer passes over seps; fixed-width fast path.