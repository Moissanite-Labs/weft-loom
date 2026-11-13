import ctypes
import os
import subprocess
import sys
import tempfile

_C_SRC = r"""
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

int lcs_ascii(const uint8_t * restrict a, int n, const uint8_t * restrict b, int m) {
    if (n == 0 || m == 0) return 0;
    int start = 0;
    int limit = n < m ? n : m;
    while (start < limit && a[start] == b[start]) start++;
    if (start == limit) return limit;
    int trimmed_end = 0;
    while (n > start && m > start && a[n - 1] == b[m - 1]) {
        n--;
        m--;
        trimmed_end++;
    }
    int matched = start + trimmed_end;
    a += start;
    b += start;
    n -= start;
    m -= start;
    if (n == 0 || m == 0) return matched;
    if (n < m) {
        const uint8_t *tmp = a; a = b; b = tmp;
        int t = n; n = m; m = t;
    }
    int words = (m + 63) >> 6;
    uint64_t stack_masks[256 * 48];
    uint64_t *masks = stack_masks;
    if (words > 48) {
        masks = (uint64_t *)calloc(256 * words, sizeof(uint64_t));
    } else {
        /* Only clear masks for characters actually present in a or b */
        memset(masks, 0, 256 * words * sizeof(uint64_t));
    }
    for (int j = 0; j < m; j++) {
        masks[(uint32_t)b[j] * words + (j >> 6)] |= (1ULL << (j & 63));
    }
    uint64_t stack_S[48];
    uint64_t *S = words <= 48 ? stack_S : (uint64_t *)malloc(words * sizeof(uint64_t));
    for (int w = 0; w < words; w++) S[w] = ~0ULL;
    if (m & 63) {
        S[words - 1] = (1ULL << (m & 63)) - 1ULL;
    }
    for (int i = 0; i < n; i++) {
        const uint64_t * restrict pm = masks + (uint32_t)a[i] * words;
        unsigned __int128 carry = 0;
        for (int w = 0; w < words; w++) {
            uint64_t s = S[w];
            uint64_t u = s & pm[w];
            unsigned __int128 sum = (unsigned __int128)s + (unsigned __int128)u + carry;
            carry = sum >> 64;
            S[w] = (uint64_t)sum | (s - u);
        }
    }
    if (m & 63) {
        S[words - 1] &= (1ULL << (m & 63)) - 1ULL;
    }
    int ones = 0;
    for (int w = 0; w < words; w++) {
        ones += __builtin_popcountll(S[w]);
    }
    if (words > 48) {
        free(masks);
        free(S);
    }
    return matched + (m - ones);
}
"""

_lib = None
try:
    so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lcs_fast128.so")
    if not os.path.exists(so_path):
        with tempfile.NamedTemporaryFile(suffix=".c", mode="w", delete=False) as f:
            f.write(_C_SRC)
            c_path = f.name
        try:
            subprocess.run(
                ["gcc", "-O3", "-march=native", "-shared", "-fPIC", c_path, "-o", so_path],
                check=True,
                capture_output=True,
            )
        finally:
            if os.path.exists(c_path):
                os.unlink(c_path)
    _lib = ctypes.CDLL(so_path)
    _lib.lcs_ascii.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
    _lib.lcs_ascii.restype = ctypes.c_int
except Exception:
    _lib = None


def _py_lcs(a: str, b: str) -> int:
    if not a or not b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    m = len(b)
    masks = {}
    for i, ch in enumerate(b):
        masks[ch] = masks.get(ch, 0) | (1 << i)
    S = (1 << m) - 1
    masks_get = masks.get
    for ch in a:
        pm = masks_get(ch)
        if pm:
            u = S & pm
            S = (S + u) | (S - u)
    return m - S.bit_count()


def lcs_length(a: str, b: str) -> int:
    if not a or not b:
        return 0
    if a == b:
        return len(a)
    if _lib is not None and a.isascii() and b.isascii():
        ba = a.encode("ascii")
        bb = b.encode("ascii")
        return _lib.lcs_ascii(ba, len(ba), bb, len(bb))
    return _py_lcs(a, b)


def main():
    data = sys.stdin.read().splitlines()
    a = data[0] if len(data) > 0 else ""
    b = data[1] if len(data) > 1 else ""
    print(lcs_length(a, b))


if __name__ == "__main__":
    main()
