import ctypes
import os
import sys

_lib = None
try:
    _so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lcs.so")
    if os.path.exists(_so_path):
        _lib = ctypes.CDLL(_so_path)
        _lib.lcs_ascii.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        _lib.lcs_ascii.restype = ctypes.c_int
except Exception:
    _lib = None


def _lcs_py(s1: str, s2: str) -> int:
    if not s1 or not s2:
        return 0
    if s1 == s2:
        return len(s1)

    n1, n2 = len(s1), len(s2)
    # Trim common prefix
    start = 0
    min_n = n1 if n1 < n2 else n2
    while start < min_n and s1[start] == s2[start]:
        start += 1

    # Trim common suffix
    end1, end2 = n1, n2
    while end1 > start and end2 > start and s1[end1 - 1] == s2[end2 - 1]:
        end1 -= 1
        end2 -= 1

    if start > 0 or end1 < n1 or end2 < n2:
        s1 = s1[start:end1]
        s2 = s2[start:end2]
        if not s1 or not s2:
            return start + (n1 - end1)

    if len(s1) > len(s2):
        s1, s2 = s2, s1

    m = len(s1)
    masks = {}
    find = s1.find
    for ch in set(s1) & set(s2):
        mask = 0
        pos = find(ch)
        while pos != -1:
            mask |= 1 << pos
            pos = find(ch, pos + 1)
        masks[ch] = mask

    S = (1 << m) - 1
    mask_all = S
    get = masks.get
    for ch in s2:
        PM = get(ch, 0)
        if PM:
            u = S & PM
            S = (S + u) | (S - u)

    return start + (n1 - end1) + (m - (S & mask_all).bit_count())


if _lib is not None:
    _c_lcs = _lib.lcs_ascii

    def lcs_length(s1: str, s2: str) -> int:
        if not s1 or not s2:
            return 0
        if s1.isascii() and s2.isascii():
            b1 = s1.encode("ascii")
            b2 = s2.encode("ascii")
            return _c_lcs(b1, len(b1), b2, len(b2))
        return _lcs_py(s1, s2)
else:
    lcs_length = _lcs_py


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
