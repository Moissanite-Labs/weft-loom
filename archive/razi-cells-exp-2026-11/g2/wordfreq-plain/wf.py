import sys, re
from collections import Counter


def _table():
    t = bytearray(range(256))
    for b in range(65, 91):          # A-Z -> a-z
        t[b] = b + 32
    for b in range(256):
        if not (97 <= t[b] <= 122):  # anything not a-z becomes a space
            t[b] = 32
    return bytes(t)


TABLE = _table()
_FIND = re.compile(r'[a-z]+')


def main():
    data = sys.stdin.buffer.read()
    if data.isascii():
        counts = Counter(data.translate(TABLE).split())
        top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
        sys.stdout.write(''.join('%s %d\n' % (w.decode('ascii'), c) for w, c in top))
    else:
        text = data.decode('utf-8', 'replace').lower()
        counts = Counter(_FIND.findall(text))
        top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
        sys.stdout.write(''.join('%s %d\n' % (w, c) for w, c in top))


if __name__ == '__main__':
    main()
