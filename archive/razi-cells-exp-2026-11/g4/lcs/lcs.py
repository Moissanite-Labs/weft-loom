import ctypes
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_lib = None
try:
    _lib = ctypes.CDLL(os.path.join(_HERE, "lcs_c.so"))
    _lib.lcs_len.restype = ctypes.c_long
    _lib.lcs_len.argtypes = [ctypes.c_char_p, ctypes.c_long,
                             ctypes.c_char_p, ctypes.c_long]
except Exception:
    _lib = None


def _py_lcs(a, b):
    if not a or not b:
        return 0
    masks = {}
    for j, ch in enumerate(b):
        masks[ch] = masks.get(ch, 0) | (1 << j)
    V = 0
    for ch in a:
        M = masks.get(ch, 0)
        if not M:
            continue
        x = M | V
        V = x & ~(x - ((V << 1) | 1))
    return bin(V).count("1")


def _pick(a, b):
    if len(b) > len(a):
        a, b = b, a
    return a, b


def lcs_length(a, b):
    if not isinstance(a, bytes):
        a = bytes(a)
    if not isinstance(b, bytes):
        b = bytes(b)
    n = len(a)
    m = len(b)
    if n == 0 or m == 0:
        return 0
    if _lib is not None:
        r = _lib.lcs_len(a, n, b, m)
        if r >= 0:
            return r
    return _py_lcs(a, b)


def main():
    data = sys.stdin.buffer
    a = data.readline().rstrip(b"\r\n")
    b = data.readline().rstrip(b"\r\n")
    sys.stdout.write(str(lcs_length(a, b)) + "\n")


if __name__ == "__main__":
    main()
