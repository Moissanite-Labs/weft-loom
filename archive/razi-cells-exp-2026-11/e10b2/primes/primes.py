import sys, os


def count_primes(n):
    """Pure-Python fallback: odds-only bytearray sieve."""
    if n <= 2:
        return 0
    size = n // 2
    sieve = bytearray([1]) * size
    i = 1
    while True:
        p = 2 * i + 1
        if p * p >= n:
            break
        if sieve[i]:
            start = (p * p) // 2
            sieve[start::p] = bytes(len(range(start, size, p)))
        i += 1
    return sieve.count(1)


def main():
    n = int(sys.argv[1])
    if n <= 2:
        print(0)
        return
    here = os.path.dirname(os.path.abspath(__file__))
    exe = os.path.join(here, "primes_c")
    src = os.path.join(here, "sieve.c")
    if not os.path.exists(exe) and os.path.exists(src):
        try:
            import subprocess
            tmp = exe + ".%d.tmp" % os.getpid()
            subprocess.run(["cc", "-O3", "-march=native", "-o", tmp, src],
                           check=True, capture_output=True)
            os.replace(tmp, exe)
        except Exception:
            pass
    if n < 2**63 and os.path.exists(exe):
        try:
            os.execv(exe, [exe, str(n)])
        except OSError:
            pass
    print(count_primes(n))


if __name__ == "__main__":
    main()
