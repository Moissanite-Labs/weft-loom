import sys
from collections import Counter

def main():
    data = sys.stdin.buffer.read()
    tbl = bytes(b if (48<=b<=57 or 97<=b<=122 or b==95) else (b+32 if 65<=b<=90 else 32) for b in range(256))
    c = Counter(data.translate(tbl).split())
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    sys.stdout.write(''.join(f'{w.decode()} {n}\n' for w, n in top))

if __name__ == '__main__':
    main()
