import sys

def count_primes(n: int) -> int:
    if n <= 2:
        return 0
    n -= 1
    if n < 3:
        return 1
    r = int(n ** 0.5)
    smalls = [(i - 1) >> 1 for i in range(r + 1)]
    larges = [0 if (i & 1) == 0 else ((n // i - 1) >> 1) for i in range(r + 1)]

    for p in range(3, r + 1, 2):
        if smalls[p] > smalls[p - 1]:
            pcnt = smalls[p - 1]
            p2 = p * p
            if p2 > n:
                break
            max_i = n // p2
            if r < max_i:
                max_i = r
            mid = r // p
            if max_i < mid:
                mid = max_i
            for i in range(1, mid + 1, 2):
                larges[i] -= larges[i * p] - pcnt
            n_div_p = n // p
            for i in range(mid + 1 + (mid & 1), max_i + 1, 2):
                larges[i] -= smalls[n_div_p // i] - pcnt
            for q in range(r // p, p - 1, -1):
                d = smalls[q] - pcnt
                if d:
                    qp = q * p
                    end = qp + p
                    if end > r + 1:
                        end = r + 1
                    for i in range(qp, end):
                        smalls[i] -= d
    return larges[1] + 1

if __name__ == '__main__':
    print(count_primes(int(sys.argv[1])))
