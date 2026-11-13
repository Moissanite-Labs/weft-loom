import ctypes
import os
import sys

def _py_lcs_length(s1: str, s2: str) -> int:
    if not s1 or not s2:
        return 0
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    masks = {}
    for i, ch in enumerate(s1):
        masks[ch] = masks.get(ch, 0) | (1 << i)
    S = (1 << len(s1)) - 1
    mask_all = S
    get = masks.get
    for ch in s2:
        PM = get(ch, 0)
        u = S & PM
        S = (S + u) | (S - u)
    return len(s1) - (S & mask_all).bit_count()

_ext_lcs = None
try:
    import _lcs_ext
    _ext_lcs = _lcs_ext.lcs_length
except Exception:
    pass

_c_lcs_ascii = None
if _ext_lcs is None:
    try:
        _so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lcs.so")
        _lib = ctypes.CDLL(_so_path)
        _c_lcs_ascii = _lib.lcs_ascii
        _c_lcs_ascii.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        _c_lcs_ascii.restype = ctypes.c_int
    except Exception:
        _c_lcs_ascii = None

if _ext_lcs is not None:
    def lcs_length(s1: str, s2: str, _fast=_ext_lcs) -> int:
        res = _fast(s1, s2)
        if res >= 0:
            return res
        return _py_lcs_length(s1, s2)
else:
    def lcs_length(s1: str, s2: str, _c_func=_c_lcs_ascii) -> int:
        if not s1 or not s2:
            return 0
        if _c_func is not None and s1.isascii() and s2.isascii():
            b1 = s1.encode("ascii")
            b2 = s2.encode("ascii")
            return _c_func(b1, len(b1), b2, len(b2))
        return _py_lcs_length(s1, s2)

def main():
    lines = sys.stdin.read().splitlines()
    if len(lines) < 2:
        s1 = lines[0] if lines else ""
        s2 = ""
    else:
        s1, s2 = lines[0], lines[1]
    print(lcs_length(s1, s2))

if __name__ == "__main__":
    main()
