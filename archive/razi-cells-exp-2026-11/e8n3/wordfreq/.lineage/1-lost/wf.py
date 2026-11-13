import sys
from collections import Counter

def main():
    data = sys.stdin.buffer.read().lower()
    counts = Counter(data.split())
    top10 = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:10]
    for w, c in top10:
        print(f"{w.decode('utf-8', 'replace')} {c}")

if __name__ == '__main__':
    main()
