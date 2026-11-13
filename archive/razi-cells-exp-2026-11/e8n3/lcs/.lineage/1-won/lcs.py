import os
import sys
import ctypes

_lib = None
try:
    _so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lcs.so")
    _lib = ctypes.CDLL(_so_path)
    _c_lcs = _lib.lcs_ascii
    _c_lcs.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
    _c_lcs.restype = ctypes.c_int
except Exception:
    _c_lcs = None

def _py_lcs_len(a: str, b: str) -> int:
    if len(a) > len(b):
        a, b = b, a
    m = len(a)
    if m == len(b) and a == b:
        return m
    pos = {}
    for i, ch in enumerate(a):
        pos[ch] = pos.get(ch, 0) | (1 << i)
    S = (1 << m) - 1
    mask = S
    get = pos.get
    for ch in b:
        pm = get(ch, 0)
        if pm:
            u = S & pm
            S = (S + u) | (S ^ u)
    return m - (S & mask).bit_count()

def lcs_len(a: str, b: str) -> int:
    if not a or not b:
        return 0
    if a == b:
        return len(a)
    if _c_lcs is not None and a.isascii() and b.isascii():
        ba = a.encode('ascii')
        bb = b.encode('ascii')
        return _c_lcs(ba, len(ba), bb, len(bb))
    return _py_lcs_len(a, b)

def main():
    lines = sys.stdin.read().splitlines()
    if len(lines) < 2:
        a = lines[0] if len(lines) >= 1 else ""
        b = ""
    else:
        a, b = lines[0], lines[1]
    print(lcs_len(a, b))

if __name__ == '__main__':
    main()
