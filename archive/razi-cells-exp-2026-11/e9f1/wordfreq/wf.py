import os
import sys

def _fallback():
    from collections import Counter
    table = bytes(
        i + 32 if 65 <= i <= 90 else (i if 97 <= i <= 122 else 32)
        for i in range(256)
    )
    words = sys.stdin.buffer.read().translate(table).split()
    counts = Counter(words)
    candidates = counts.most_common(50)
    if len(candidates) >= 10:
        tenth_count = candidates[9][1]
        if len(candidates) == 50 and candidates[-1][1] == tenth_count:
            top10 = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:10]
        else:
            cutoff = [x for x in candidates if x[1] >= tenth_count]
            top10 = sorted(cutoff, key=lambda x: (-x[1], x[0]))[:10]
    else:
        top10 = sorted(candidates, key=lambda x: (-x[1], x[0]))[:10]
    for word, count in top10:
        print(f"{word.decode('ascii')} {count}")

def main():
    so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_wf.so")
    if os.path.exists(so_path):
        try:
            import ctypes
            lib = ctypes.CDLL(so_path)
            lib.run_stdin()
            return
        except Exception:
            pass
    _fallback()

if __name__ == '__main__':
    main()
