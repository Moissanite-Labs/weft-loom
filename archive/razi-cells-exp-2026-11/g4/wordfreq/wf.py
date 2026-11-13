import os, sys

BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wfbin")
if not os.path.exists(BIN):
    SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wf.c")
    for cc in ("cc", "clang", "gcc"):
        if os.system(cc + " -O2 -o '" + BIN + "' '" + SRC + "' >/dev/null 2>&1") == 0:
            break
try:
    os.execv(BIN, ["wfbin"])
except OSError:
    pass

from collections import Counter

_t = bytearray(range(256))
for _c in range(256):
    if 65 <= _c <= 90:
        _t[_c] = _c + 32
    elif 97 <= _c <= 122:
        _t[_c] = _c
    else:
        _t[_c] = 32
TABLE = bytes(_t)

data = sys.stdin.buffer.read()
counts = Counter(data.translate(TABLE).split())
top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
out = "\n".join("%s %d" % (w.decode("ascii"), c) for w, c in top)
sys.stdout.write(out + ("\n" if out else ""))
