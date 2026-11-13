sortints.py state (verified, steps nearly exhausted):
- Path: read stdin bytes -> np.fromstring(data, int64, sep=' ') (warnings as errors -> fallback to pure Python int/sort) -> downcast to int32 if range fits -> arr.sort() -> tolist -> ('%d\n'*n % tuple(a)).encode() -> single write.
- Assay `python3 bench.py` (median of 5 runs/sec, checks expected.txt + empty + negatives/mixed whitespace). Baseline 2.3083 (np.array(split).astype + join(map(str))); now ~4.17-4.23.
- Profile for 1M ints: numpy import ~0.045s, fromstring 0.018s, sort32 0.017s (sort64 0.040s), tolist 0.011s, '%d\n' fmt 0.060s (join map str 0.090s, str(list).replace 0.073s). Formatting is the biggest remaining cost, then numpy import.
- Lessons: np.fromstring(sep=' ') is 10x faster than split+astype; '%d\n'*n % tuple is the fastest pure-Python formatter tried; int32 sort is 2x faster than int64.
- Big ints (> int64) and values near 2**62 go to the pure path and print correctly; non-integer tokens exit 1 with a traceback (not handled).
- Untried: vectorised numpy digit formatting to bytes, avoiding numpy import cost.