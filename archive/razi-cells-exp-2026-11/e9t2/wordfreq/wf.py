import sys
from _collections import _count_elements

_TABLE = b' ' * 65 + b'abcdefghijklmnopqrstuvwxyz' + b' ' * 6 + b'abcdefghijklmnopqrstuvwxyz' + b' ' * 133

def main():
    counts = {}
    read = sys.stdin.buffer.read
    rem = b''
    while True:
        buf = read(524288)
        if not buf:
            if rem:
                _count_elements(counts, rem.split())
            break
        chunk = rem + buf.translate(_TABLE)
        idx = chunk.rfind(b' ')
        if idx == -1:
            rem = chunk
        else:
            _count_elements(counts, chunk[:idx].split())
            rem = chunk[idx + 1:]
    top10 = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:10]
    sys.stdout.write(''.join(f"{w.decode('ascii')} {c}\n" for w, c in top10))

if __name__ == '__main__':
    main()
