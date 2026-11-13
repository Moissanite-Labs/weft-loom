import sys
from collections import Counter

# non-letters -> space, uppercase -> lowercase (ASCII words [a-z]+)
_T = bytes((c if 97 <= c <= 122 else c + 32 if 65 <= c <= 90 else 32) for c in range(256))

def main():
    data = sys.stdin.buffer.read()
    c = Counter(data.translate(_T).split())
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    sys.stdout.write("".join("%s %d\n" % (w.decode(), n) for w, n in top))

main()
