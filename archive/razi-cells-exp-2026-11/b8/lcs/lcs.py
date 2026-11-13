import sys
import os
import ctypes
import subprocess
import tempfile

_C_SRC = r"""
#include <stdint.h>
#include <string.h>

int lcs_ascii(const uint8_t *a, int la, const uint8_t *b, int lb) {
    int start = 0;
    int min_len = la < lb ? la : lb;
    while (start < min_len && a[start] == b[start]) start++;
    int end_a = la, end_b = lb;
    while (start < end_a && start < end_b && a[end_a - 1] == b[end_b - 1]) {
        end_a--;
        end_b--;
    }
    int trimmed = start + (la - end_a);
    a += start;
    b += start;
    la = end_a - start;
    lb = end_b - start;
    if (la == 0 || lb == 0) return trimmed;
    if (la < lb) {
        const uint8_t *tmp = a; a = b; b = tmp;
        int t = la; la = lb; lb = t;
    }
    int W = (lb + 63) >> 6;
    uint64_t pm[256][64];
    uint8_t present[256];
    memset(present, 0, sizeof(present));
    for (int i = 0; i < lb; i++) {
        uint8_t c = b[i];
        if (!present[c]) {
            present[c] = 1;
            memset(pm[c], 0, W * sizeof(uint64_t));
        }
        pm[c][i >> 6] |= (1ULL << (i & 63));
    }
    uint64_t S[64];
    for (int w = 0; w < W; w++) S[w] = ~0ULL;
    for (int i = 0; i < la; i++) {
        uint8_t c = a[i];
        if (!present[c]) continue;
        const uint64_t *pmc = pm[c];
        uint64_t carry = 0;
        for (int w = 0; w < W; w++) {
            uint64_t sw = S[w];
            uint64_t uw = sw & pmc[w];
            unsigned __int128 sum = (unsigned __int128)sw + uw + carry;
            carry = (uint64_t)(sum >> 64);
            S[w] = (uint64_t)sum | (sw ^ uw);
        }
    }
    int rem = lb & 63;
    if (rem) {
        S[W - 1] |= (~0ULL << rem);
    }
    int zeros = 0;
    for (int w = 0; w < W; w++) {
        zeros += __builtin_popcountll(~S[w]);
    }
    return trimmed + zeros;
}
"""

def _load_c_lib():
    so_path = os.path.join(tempfile.gettempdir(), "_lcs_fast_v1.so")
    if not os.path.exists(so_path):
        try:
            c_path = os.path.join(tempfile.gettempdir(), "_lcs_fast_v1.c")
            with open(c_path, "w") as f:
                f.write(_C_SRC)
            subprocess.run(
                ["gcc", "-O3", "-march=native", "-shared", "-fPIC", c_path, "-o", so_path],
                check=True,
                capture_output=True,
            )
        except Exception:
            return None
    try:
        lib = ctypes.CDLL(so_path)
        fn = lib.lcs_ascii
        fn.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        fn.restype = ctypes.c_int
        return fn
    except Exception:
        return None

_c_lcs = _load_c_lib()

def _py_lcs(a: str, b: str) -> int:
    la, lb = len(a), len(b)
    start = 0
    min_len = la if la < lb else lb
    while start < min_len and a[start] == b[start]:
        start += 1
    end_a, end_b = la, lb
    while start < end_a and start < end_b and a[end_a - 1] == b[end_b - 1]:
        end_a -= 1
        end_b -= 1
    trimmed = start + (la - end_a)
    if start == end_a or start == end_b:
        return trimmed
    a = a[start:end_a]
    b = b[start:end_b]
    if len(a) < len(b):
        a, b = b, a
    m = len(b)
    masks = {}
    for i, ch in enumerate(b):
        masks[ch] = masks.get(ch, 0) | (1 << i)
    S = (1 << m) - 1
    get_mask = masks.get
    for ch in a:
        pm = get_mask(ch, 0)
        if pm:
            u = S & pm
            S = (S + u) | (S ^ u)
    return trimmed + m - (S & ((1 << m) - 1)).bit_count()

def lcs(a: str, b: str) -> int:
    if a == b:
        return len(a)
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0
    if _c_lcs is not None and la <= 4096 and lb <= 4096 and a.isascii() and b.isascii():
        ba = a.encode("ascii")
        bb = b.encode("ascii")
        return _c_lcs(ba, la, bb, lb)
    return _py_lcs(a, b)

def main():
    lines = sys.stdin.read().splitlines()
    if len(lines) < 2:
        a = lines[0] if lines else ""
        b = ""
    else:
        a, b = lines[0], lines[1]
    print(lcs(a, b))

if __name__ == "__main__":
    main()
