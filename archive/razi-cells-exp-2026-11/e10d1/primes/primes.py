import sys

def count_primes(n):
    # mod-6 wheel sieve: two bytearrays for residues 1 and 5 (mod 6)
    if n < 3:
        return 0
    if n < 4:
        return 1
    if n < 6:
        return 2
    la = (n + 4) // 6   # k in [0, la): 6k+1 < n
    lb = n // 6         # k in [0, lb): 6k+5 < n
    a = bytearray([1]) * la
    b = bytearray([1]) * lb
    a[0] = 0  # 1 is not prime
    lim = int(n ** 0.5) + 1
    for p in range(5, lim + 1):
        r = p % 6
        if r == 1:
            if not a[p // 6]:
                continue
        elif r == 5:
            if not b[p // 6]:
                continue
        else:
            continue
        s = (p * p) // 6
        if s < la:
            a[s::p] = bytes((la - 1 - s) // p + 1)
        m = p + ((4 * p) % 6)
        s = (p * m) // 6
        if s < lb:
            b[s::p] = bytes((lb - 1 - s) // p + 1)
    return 2 + a.count(1) + b.count(1)

if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
