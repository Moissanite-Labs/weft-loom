import os
import sys

MOD = 1_000_000_007

_C_SRC = r"""
#include <stdint.h>
#define MOD 1000000007ULL

uint64_t fib(uint64_t n) {
    if (n == 0ULL) return 0ULL;
    uint64_t a = 0ULL, b = 1ULL;
    for (int i = 63 - __builtin_clzll(n); i >= 0; --i) {
        uint64_t t = (b << 1) + MOD - a; if (t >= MOD) t -= MOD;
        uint64_t c = (a * t) % MOD;
        uint64_t d = (a * a + b * b) % MOD;
        if ((n >> i) & 1ULL) { a = d; b = c + d; if (b >= MOD) b -= MOD; }
        else { a = c; b = d; }
    }
    return a;
}
"""


def _py_fib(n):
    if n == 0:
        return 0
    a, b = 0, 1
    for i in range(n.bit_length() - 1, -1, -1):
        c = (a * ((b << 1) - a)) % MOD
        d = (a * a + b * b) % MOD
        if (n >> i) & 1:
            a, b = d, (c + d) % MOD
        else:
            a, b = c, d
    return a


def _so_path():
    d = os.path.dirname(os.path.abspath(__file__))
    so = os.path.join(d, "fibmod_c.so")
    if os.path.exists(so):
        return so
    src = os.path.join(d, "fibmod_c.c")
    try:
        with open(src, "w") as f:
            f.write(_C_SRC)
        import subprocess
        for cc in ("cc", "gcc", "clang"):
            try:
                r = subprocess.run([cc, "-O3", "-shared", "-fPIC", "-o", so, src],
                                   capture_output=True)
            except OSError:
                continue
            if r.returncode == 0 and os.path.exists(so):
                return so
    except Exception:
        pass
    return so


def _load():
    so = _so_path()
    # Fast path: cffi ABI mode (cheap per-call FFI)
    try:
        import cffi
        ffi = cffi.FFI()
        ffi.cdef("unsigned long long fib(unsigned long long);")
        f = ffi.dlopen(so).fib
        if f(10) == 55 and f(0) == 0 and f(10**18) == 209783453:
            return f
    except Exception:
        pass
    # Fallback: ctypes
    try:
        import ctypes
        lib = ctypes.CDLL(so)
        fn = lib.fib
        fn.argtypes = (ctypes.c_uint64,)
        fn.restype = ctypes.c_int32
        if fn(10) == 55 and fn(0) == 0 and fn(10**18) == 209783453:
            return fn
    except Exception:
        pass
    return _py_fib


fib = _load()


def main():
    print(fib(int(sys.argv[1])))


if __name__ == "__main__":
    main()
