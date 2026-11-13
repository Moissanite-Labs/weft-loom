import sys
from collections import Counter

def main():
    table = bytes(i if 97 <= i <= 122 else (i + 32 if 65 <= i <= 90 else 32) for i in range(256))
    words = sys.stdin.buffer.read().translate(table).split()
    if not words:
        return
    counts = Counter(words)
    # Get top candidates using most_common(50) or nsmallest
    # Since ties are broken alphabetically, (-count, word) is exact.
    # Optimization: find the 10th highest count threshold using most_common(10)
    mc = counts.most_common(10)
    min_c = mc[-1][1]
    candidates = [(-c, w) for w, c in counts.items() if c >= min_c]
    candidates.sort()
    out = "\n".join(f"{w.decode('ascii')} {-neg_c}" for neg_c, w in candidates[:10]) + "\n"
    sys.stdout.write(out)

if __name__ == "__main__":
    main()
