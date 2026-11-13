import os, subprocess, sys, time
from collections import Counter
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, 'corpus.txt')
EXPECTED = os.path.join(HERE, 'expected.txt')
TARGET = 20 * 1024 * 1024


def ensure_corpus():
    if os.path.exists(CORPUS) and os.path.getsize(CORPUS) >= TARGET:
        return
    with open(CORPUS, 'wb') as f:
        subprocess.run([sys.executable, os.path.join(HERE, 'gen.py')],
                       stdout=f, check=True)


def ensure_expected():
    if os.path.exists(EXPECTED):
        return open(EXPECTED, 'r').read()
    data = open(CORPUS, 'rb').read()
    low = data.decode('utf-8', 'replace').lower()
    c = Counter(p for p in re.split(r'[^a-z]+', low) if p)
    items = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    out = ''.join('%s %d\n' % (w, n) for w, n in items)
    with open(EXPECTED, 'w') as f:
        f.write(out)
    return out


def main():
    ensure_corpus()
    exp = ensure_expected()

    # correctness gate
    with open(CORPUS, 'rb') as f:
        r = subprocess.run([sys.executable, os.path.join(HERE, 'wf.py')],
                           stdin=f, capture_output=True)
    if r.returncode != 0:
        print(0.0)
        return
    got = r.stdout.decode().strip() + '\n'
    if got != exp:
        print(0.0)
        return

    best = float('inf')
    for _ in range(5):
        with open(CORPUS, 'rb') as f:
            t = time.perf_counter()
            rr = subprocess.run([sys.executable, os.path.join(HERE, 'wf.py')],
                                stdin=f, stdout=subprocess.DEVNULL)
            dt = time.perf_counter() - t
        if rr.returncode != 0:
            print(0.0)
            return
        if dt < best:
            best = dt
    print(os.path.getsize(CORPUS) / best)


main()
