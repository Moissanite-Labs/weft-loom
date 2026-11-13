import os, sys

# Words are maximal runs of ASCII letters, lowercased. Prints the 10 most
# common as 'word count', ties by word. Fast path: exec the C helper wf_c
# (built from wf.c, compiled on demand); fallback: pure Python below.
_D = os.path.dirname(os.path.abspath(__file__))
_BIN = os.path.join(_D, 'wf_c')


def _fallback():
    from collections import Counter
    t = bytearray(b' ' * 256)
    for c in range(26):
        t[65 + c] = 97 + c
        t[97 + c] = 97 + c
    data = sys.stdin.buffer.read()
    counts = Counter(data.translate(bytes(t)).split())
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    sys.stdout.write(''.join('%s %d\n' % (w.decode('ascii'), n) for w, n in top))


def main():
    try:
        os.execv(_BIN, [_BIN])
    except OSError:
        pass
    src = os.path.join(_D, 'wf.c')
    if os.path.exists(src):
        try:
            import subprocess
            subprocess.run(['cc', '-O2', '-o', _BIN, src], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            os.execv(_BIN, [_BIN])
        except Exception:
            pass
    _fallback()


if __name__ == '__main__':
    main()
