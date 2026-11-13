import sys
from collections import Counter

def main():
    data = sys.stdin.buffer.read().lower()
    # split on anything that's not a lowercase ascii letter
    words = data.translate(_TBL).split()
    c = Counter(words)
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    out = []
    for w, n in top:
        out.append(w.decode() + ' ' + str(n))
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))

# build translation table: keep a-z, map everything else to space
_TBL = bytes((b if 97 <= b <= 122 else 32) for b in range(256))

if __name__ == '__main__':
    main()
