
## split 1 (TIE: within noise)
A: Use iterative fast doubling (current fibmod.py) for F(n) mod 1e9+7, optimizing the bit loop and minimizing overhead.
B: Use 2x2 matrix exponentiation modulo 1e9+7, multiplying matrices per bit.
medians A=1.43148 B=1.44666 over 5 runs; kept A
loser lesson: It lost on constant factors: matrix exponentiation is still \(O(\log n)\) but does more modular multiplications and Python object/bookkeeping per bit than fast doubling.
Keep fast doubling: \(F(2k)=F(k)(2F(k+1)-F(k))\), \(F(2k+1)=F(k)^2+F(k+1)^2\), iterated over bits.
For negative \(n\), compute \(m=|n|\) then apply \(F(-m)=(-1)^{m+1}F(m)\).
loser body kept at .lineage/1-b/
