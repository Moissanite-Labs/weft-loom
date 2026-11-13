import sys, re, heapq
from collections import Counter

def emit(counts):
    top = heapq.nsmallest(10, counts.items(), key=lambda kv: (-kv[1], kv[0]))
    out = []
    for w, n in top:
        if isinstance(w, bytes):
            w = w.decode('ascii')
        out.append('%s %d' % (w, n))
    if out:
        sys.stdout.write('\n'.join(out) + '\n')

def main():
    data = sys.stdin.buffer.read()
    if data.isascii():
        counts = Counter(re.findall(b'[a-z]+', data.lower()))
        emit(counts)
    else:
        text = data.decode('utf-8', errors='replace').lower()
        counts = Counter(re.findall(r'[a-z]+', text))
        emit(counts)

if __name__ == '__main__':
    main()
