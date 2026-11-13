import sys
import math

# Dual wheel mod 6: s1[k] represents 6*k + 1, s5[k] represents 6*k + 5
# Pre-sieve with 5, 7, 11, 13 (period = 5 * 7 * 11 * 13 = 5005)
_P = 5005
_B1 = bytearray(b'\x01') * _P
_B5 = bytearray(b'\x01') * _P
for _p in (5, 7, 11, 13):
    # Find k in 0.._p-1 where (6*k + 1) % _p == 0 and (6*k + 5) % _p == 0
    for _k in range(_p):
        if (6 * _k + 1) % _p == 0:
            _B1[_k::_p] = bytes((_P - _k - 1) // _p + 1)
        if (6 * _k + 5) % _p == 0:
            _B5[_k::_p] = bytes((_P - _k - 1) // _p + 1)

def count_primes(n: int) -> int:
    if n <= 17:
        return sum(1 for p in (2, 3, 5, 7, 11, 13) if p < n)

    # Number of 6k+1 < n: 6k+1 <= n-1 => k <= (n-2)//6, so count is (n + 4) // 6
    # Number of 6k+5 < n: 6k+5 <= n-1 => k <= (n-6)//6, so count is n // 6
    n1 = (n + 4) // 6
    n5 = n // 6

    q1, r1 = divmod(n1, _P)
    s1 = _B1 * q1 + _B1[:r1]
    s1[0] = 0  # 1 is not prime

    q5, r5 = divmod(n5, _P)
    s5 = _B5 * q5 + _B5[:r5]

    limit = math.isqrt(n - 1)
    if limit >= 17:
        zeros = bytes(n1 // 17 + 2)
        max_k = limit // 6
        for k in range(2, max_k + 1):
            # Check 6k + 5 (for k=2, 17)
            if s5[k]:
                p = 6 * k + 5
                if p <= limit:
                    # p*p = 36k^2 + 60k + 25 = 6(6k^2 + 10k + 4) + 1 -> in s1
                    st1 = (p * p) // 6
                    s1[st1::p] = zeros[:(n1 - st1 - 1) // p + 1]
                    # p*(p+2) = p*(6k+7) = 6(...) + 5 -> in s5
                    st5 = (p * (p + 2)) // 6
                    if st5 < n5:
                        s5[st5::p] = zeros[:(n5 - st5 - 1) // p + 1]
            # Check 6k + 1 (skip k=2 since 13 is already pre-sieved)
            if k >= 3 and s1[k]:
                p = 6 * k + 1
                if p <= limit:
                    # p*p = 6(...) + 1 -> in s1
                    st1 = (p * p) // 6
                    s1[st1::p] = zeros[:(n1 - st1 - 1) // p + 1]
                    # p*(p+4) = 6(...) + 5 -> in s5
                    st5 = (p * (p + 4)) // 6
                    if st5 < n5:
                        s5[st5::p] = zeros[:(n5 - st5 - 1) // p + 1]

    # Add 6 for (2, 3, 5, 7, 11, 13)
    return s1.count(1) + s5.count(1) + 6

if __name__ == '__main__':
    print(count_primes(int(sys.argv[1])))
