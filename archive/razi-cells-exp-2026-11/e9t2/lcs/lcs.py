import sys
import os
import ctypes
import subprocess

_c_lcs = None

C_SRC = r"""
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

int lcs_ascii(const uint8_t *a, int la, const uint8_t *b, int lb) {
    if (la == 0 || lb == 0) return 0;
    if (la > lb) {
        const uint8_t *t = a; a = b; b = t;
        int tl = la; la = lb; lb = tl;
    }
    int words = (la + 63) >> 6;
    uint64_t *masks = (uint64_t *)calloc(256 * words, sizeof(uint64_t));
    uint64_t *S = (uint64_t *)malloc(words * sizeof(uint64_t));
    if (!masks || !S) { free(masks); free(S); return -1; }

    for (int i = 0; i < la; i++) {
        masks[(int)a[i] * words + (i >> 6)] |= (1ULL << (i & 63));
    }
    for (int w = 0; w < words; w++) S[w] = ~0ULL;

    for (int j = 0; j < lb; j++) {
        const uint64_t *pm = &masks[(int)b[j] * words];
        uint64_t carry = 0;
        uint64_t borrow = 0;
        for (int w = 0; w < words; w++) {
            uint64_t s = S[w];
            uint64_t u = s & pm[w];
            // sum = s + u + carry
            uint64_t sum1 = s + u;
            uint64_t c1 = (sum1 < s);
            uint64_t sum2 = sum1 + carry;
            carry = c1 | (sum2 < sum1);
            // diff = s - u - borrow
            uint64_t diff1 = s - u;
            uint64_t b1 = (s < u);
            uint64_t diff2 = diff1 - borrow;
            borrow = b1 | (diff1 < borrow);

            S[w] = sum2 | diff2;
        }
    }
    int rem = la & 63;
    if (rem) S[words - 1] &= (1ULL << rem) - 1ULL;
    int zeros = 0;
    for (int w = 0; w < words; w++) {
        zeros += __builtin_popcountll(S[w]);
    }
    free(masks);
    free(S);
    return la - zeros;
}
"""

def _init_c():
    global _c_lcs
    so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lcs_fast.so")
    if not os.path.exists(so_path):
        c_path = so_path + ".c"
        try:
            with open(c_path, "w") as f:
                f.write(C_SRC)
            subprocess.run(
                ["cc", "-O3", "-march=native", "-shared", "-fPIC", c_path, "-o", so_path],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception:
            return
        finally:
            if os.path.exists(c_path):
                try: os.remove(c_path)
                except OSError: pass
    try:
        lib = ctypes.CDLL(so_path)
        fn = lib.lcs_ascii
        fn.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        fn.restype = ctypes.c_int
        _c_lcs = fn
    except Exception:
        _c_lcs = None

_init_c()

def _py_lcs(a: str, b: str) -> int:
    if len(a) > len(b):
        a, b = b, a
    la = len(a)
    if not la:
        return 0
    masks = {}
    get = masks.get
    bit = 1
    for ch in a:
        masks[ch] = get(ch, 0) | bit
        bit <<= 1
    S = (1 << la) - 1
    for ch in b:
        if pm := get(ch):
            u = S & pm
            S = (S + u) | (S - u)
    return la - (S & ((1 << la) - 1)).bit_count()

def lcs_length(a: str, b: str) -> int:
    if a == b:
        return len(a)
    if not a or not b:
        return 0
    if _c_lcs is not None and a.isascii() and b.isascii():
        ba = a.encode('ascii')
        bb = b.encode('ascii')
        return _c_lcs(ba, len(ba), bb, len(bb))
    return _py_lcs(a, b)

def main():
    lines = sys.stdin.read().splitlines()
    a = lines[0] if lines else ""
    b = lines[1] if len(lines) > 1 else ""
    print(lcs_length(a, b))

if __name__ == "__main__":
    main()
