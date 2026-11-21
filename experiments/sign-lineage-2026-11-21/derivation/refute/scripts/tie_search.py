"""Smallest counterexample: argmax with first-index tie rule breaks the same-position null law / 1/k! bound."""
import itertools, sys
from fractions import Fraction
from math import factorial
sys.path.insert(0, '.')
from exact_refute import argmax_abs, rook_law, same, tail_low

def law_F(C, N):
    hA = len(C); law = {}
    for pi in itertools.permutations(range(N)):
        Cp = [[None]*N for _ in range(hA)]
        for i in range(hA):
            for j in range(N):
                Cp[i][pi[j]] = C[i][j]
        F = sum(1 for i in range(hA) if argmax_abs(Cp[i]) == i)
        law[F] = law.get(F, 0) + Fraction(1, factorial(N))
    return law

found = None
for N in range(2, 5):
    for hA in range(1, N+1):
        vals = [Fraction(1), Fraction(1, 2)]
        for flat in itertools.product(vals, repeat=hA*N):
            C = [list(flat[i*N:(i+1)*N]) for i in range(hA)]
            law = law_F(C, N)
            for k in range(1, hA+1):
                p = sum(w for f, w in law.items() if f >= k)
                if p > Fraction(1, factorial(k)):
                    found = (N, hA, C, k, p, law); break
            if found: break
        if found: break
    if found: break
N, hA, C, k, p, law = found
print("smallest: N", N, "hA", hA, "C", [[str(x) for x in r] for r in C], "k", k, "P(F>=k)", p, "> 1/k! =", Fraction(1, factorial(k)))
print("law", {f: str(w) for f, w in sorted(law.items())})
print("tail_low(201)", float(tail_low(201)), "tail_low(203)", float(tail_low(203)))
