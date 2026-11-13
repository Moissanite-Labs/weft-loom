import sys
from math import isqrt

def count_primes(n: int) -> int:
    if n <= 2:
        return 0
    N = n - 1
    if N == 2:
        return 1
    if N == 3:
        return 2
    v = isqrt(N)
    s = (v + 1) // 2
    smalls = [i // 2 for i in range(v + 1)]
    smalls[0] = 0
    for i in range(1, v + 1):
        smalls[i] = (i - 1) // 2
    larges = [(N // (2 * i + 1) - 1) // 2 for i in range(s)]
    rough = [2 * i + 1 for i in range(s)]
    skip = bytearray(v + 1)

    nb_primes = 0
    for p in range(3, v + 1, 2):
        if not skip[p]:
            q = p * p
            if q * q > N:
                break
            skip[p] = 1
            for i in range(q, v + 1, 2 * p):
                skip[i] = 1
            ns = 0
            for k in range(s):
                i = rough[k]
                if skip[i]:
                    continue
                d = i * p
                larges[ns] = larges[k] - (larges[smalls[d] - nb_primes] if d <= v else smalls[N // d]) + nb_primes
                rough[ns] = i
                ns += 1
            s = ns
            i = v
            for j in range(v // p, p - 1, -1):
                c = smalls[j] - nb_primes
                e = j * p
                while i >= e:
                    smalls[i] -= c
                    i -= 1
            nb_primes += 1

    total = larges[0]
    for k in range(1, s):
        total -= smalls[N // rough[k]]
    total += (s + 2 * (nb_primes - 1)) * (s - 1) // 2

    for k in range(1, s):
        p = rough[k]
        m = N // p
        e = smalls[m // p] - nb_primes
        if e <= k:
            break
        lsum = 0
        for l in range(k + 1, e + 1):
            lsum += smalls[m // rough[l]]
        total += lsum - (e - k) * (nb_primes + k - 1)

    return total + 1

if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
