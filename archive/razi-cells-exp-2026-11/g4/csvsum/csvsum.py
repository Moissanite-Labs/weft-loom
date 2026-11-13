import sys, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'csvsum_c.c')
BIN = os.path.join(HERE, 'csvsum_c')


def build():
    """Return path to a working compiled helper, or None."""
    if os.path.exists(BIN) and os.access(BIN, os.X_OK):
        if not os.path.exists(SRC) or os.path.getmtime(BIN) >= os.path.getmtime(SRC):
            return BIN
    if not os.path.exists(SRC):
        return None
    for cc in ('cc', 'clang', 'gcc'):
        try:
            r = subprocess.run([cc, '-O2', '-o', BIN, SRC],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if r.returncode == 0 and os.access(BIN, os.X_OK):
                return BIN
        except Exception:
            pass
    return None


def fallback():
    data = sys.stdin.buffer.read()
    data = data[data.find(b'\n') + 1:]
    toks = data.replace(b',', b' ').split()
    sums = {}
    get = sums.get
    for c, v in zip(toks[1::3], map(float, toks[2::3])):
        sums[c] = get(c, 0.0) + v
    sys.stdout.write('\n'.join([c.decode() + ',' + format(v, '.2f')
                                for c, v in sorted(sums.items())]) + '\n')


def main():
    b = build()
    if b:
        try:
            os.execv(b, [b])
        except Exception:
            pass
    fallback()


if __name__ == '__main__':
    main()
