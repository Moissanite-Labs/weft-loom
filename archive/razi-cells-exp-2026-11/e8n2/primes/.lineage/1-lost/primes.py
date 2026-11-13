import ctypes
import os
import subprocess
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
_SO_PATH = os.path.join(_DIR, "_primes.so")
_C_PATH = os.path.join(_DIR, "_primes.c")

_C_CODE = r"""
long long count_primes_c(long long n) {
    if (n <= 2) return 0;
    long long N = n - 1;
    if (N == 2) return 1;
    if (N == 3) return 2;

    long long r = (long long)__builtin_sqrt((double)N);
    while ((r + 1) * (r + 1) <= N) r++;
    while (r * r > N) r--;

    long long smalls[65536];
    long long larges[65536];

    for (long long i = 1; i <= r; i++) {
        smalls[i] = (i - 1) >> 1;
    }
    for (long long i = 1; i <= r; i += 2) {
        larges[i] = (N / i - 1) >> 1;
    }

    for (long long p = 3; p <= r; p += 2) {
        if (smalls[p] == smalls[p - 1]) continue;
        long long pcnt = smalls[p - 1];
        long long p2 = p * p;
        long long max_i = r < (N / p2) ? r : (N / p2);

        for (long long i = 1; i <= max_i; i += 2) {
            long long k = i * p;
            if (k <= r) {
                larges[i] -= larges[k] - pcnt;
            } else {
                larges[i] -= smalls[N / k] - pcnt;
            }
        }

        for (long long j = r; j >= p2; j--) {
            smalls[j] -= smalls[j / p] - pcnt;
        }
    }

    return larges[1] + 1;
}
"""

def _load_lib():
    if not os.path.exists(_SO_PATH):
        with open(_C_PATH, "w") as f:
            f.write(_C_CODE)
        env = os.environ.copy()
        env["TMPDIR"] = _DIR
        cc = "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang"
        if not os.path.exists(cc):
            cc = "cc"
        subprocess.run(
            [cc, "-O3", "-shared", "-fPIC", "-nostdlib", _C_PATH, "-o", _SO_PATH],
            check=True,
            env=env,
        )
    lib = ctypes.CDLL(_SO_PATH)
    fn = lib.count_primes_c
    fn.argtypes = [ctypes.c_longlong]
    fn.restype = ctypes.c_longlong
    return fn

_count_primes_c = _load_lib()

def count_primes(n: int) -> int:
    return _count_primes_c(n)

if __name__ == "__main__":
    print(_count_primes_c(int(sys.argv[1])))
