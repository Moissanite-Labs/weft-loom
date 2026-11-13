import ctypes
import os
import re
import sys
from collections import defaultdict

def _run_c():
    dylib = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_csvsum.dylib")
    if not os.path.exists(dylib):
        c_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_csvsum.c")
        if os.path.exists(c_src):
            os.system(f"TMPDIR=. clang -O3 -shared -fPIC {c_src} -o {dylib}")
    lib = ctypes.CDLL(dylib)
    fn = None
    for name in ("run_csvsum", "csvsum", "process_stdin", "process_csv", "process", "run", "solve"):
        fn = getattr(lib, name, None)
        if fn is not None:
            break
    if fn is None:
        c_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_csvsum.c")
        with open(c_src, "r") as f:
            src = f.read()
        matches = re.findall(r"\b(?:void|int)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", src)
        for name in reversed(matches):
            if name not in ("main", "cmp_entry", "cmp", "hash_str"):
                fn = getattr(lib, name, None)
                if fn is not None:
                    break
    if fn is None:
        return False
    res = fn(0)
    try:
        lib.fflush(None)
    except Exception:
        pass
    return res == 0 or res is None

def main():
    try:
        if _run_c():
            return
    except Exception:
        pass

    data = sys.stdin.buffer.read()
    if not data:
        return
    lines = data.splitlines()
    totals = defaultdict(float)
    for line in lines[1:]:
        if not line:
            continue
        c1 = line.find(b',')
        c2 = line.find(b',', c1 + 1)
        cat = line[c1 + 1:c2]
        val = float(line[c2 + 1:])
        totals[cat] += val

    out = []
    for cat in sorted(totals):
        out.append(f"{cat.decode('ascii')},{totals[cat]:.2f}\n")
    sys.stdout.write("".join(out))

if __name__ == '__main__':
    main()
