import sys, collections, heapq

TRANS = bytes(
    c + 32 if 65 <= c <= 90 else (c if 97 <= c <= 122 else 32)
    for c in range(256)
)

def main():
    words = sys.stdin.buffer.read().translate(TRANS).split()
    counts = collections.Counter(words)
    mc = counts.most_common(25)
    if len(mc) >= 10:
        tenth = mc[9][1]
        if mc[-1][1] == tenth and len(mc) == 25:
            top10 = heapq.nsmallest(10, counts.items(), key=lambda x: (-x[1], x[0]))
        else:
            top10 = sorted((x for x in mc if x[1] >= tenth), key=lambda x: (-x[1], x[0]))[:10]
    else:
        top10 = sorted(mc, key=lambda x: (-x[1], x[0]))
    sys.stdout.write(''.join(f"{w.decode('ascii')} {c}\n" for w, c in top10))

if __name__ == '__main__':
    main()
