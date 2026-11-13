import sys
def count_primes(n):
    if n < 3: return 0
    if n < 4: return 1
    if n < 6: return 2
    sa = (n - 2)//6 + 1
    sb = (n - 6)//6 + 1
    A = bytearray([1])*sa; B = bytearray([1])*sb
    A[0] = 0
    r = int(n**0.5)
    k = 0
    while True:
        v = 6*k+1
        if v > r: break
        if A[k]:
            p = v
            s = (p*p-1)//6
            A[s::p] = bytes(len(range(s, sa, p)))
            s = (p*(p+4)-5)//6
            B[s::p] = bytes(len(range(s, sb, p)))
        v = 6*k+5
        if v > r: break
        if B[k]:
            p = v
            s = (p*p-1)//6
            A[s::p] = bytes(len(range(s, sa, p)))
            s = (p*(p+2)-5)//6
            B[s::p] = bytes(len(range(s, sb, p)))
        k += 1
    return A.count(1) + B.count(1) + 2
print(count_primes(int(sys.argv[1])))
