import sys
from collections import Counter

def main():
    data = sys.stdin.buffer.read()
    tbl = bytes(c if (97 <= c <= 122 or 48 <= c <= 57) else (c + 32 if 65 <= c <= 90 else 32) for c in range(256))
    c = Counter(data.translate(tbl).split())
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    sys.stdout.write("".join(f"{w.decode()} {n}\n" for w, n in top))

if __name__ == "__main__":
    main()
