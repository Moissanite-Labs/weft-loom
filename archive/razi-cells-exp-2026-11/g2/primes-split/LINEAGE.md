
## split 1 (TIE: within noise)
A: Keep the current odd-only bytearray slice-assignment sieve in primes.py (0.035s for 5e6)
B: Rewrite primes.py using a numpy vectorized sieve (np.zeros bool array, slice assignment for marking) to try to beat 0.035s
medians A=28.8902 B=28.5265 over 5 runs; kept A
loser lesson: - It lost because NumPy import/allocation and temporary slicing overhead outweighed the gain; the bytearray slice-assignment sieve was already C-level and the agent botched several JSON actions.
- Keep the odd-only trick: index `i -> 2i+1`, mark via `sieve[start::step] = zeros`, then answer `1 + sum(sieve)`.
- Use NumPy only for much larger `n` or with careful preallocation/fewer temporaries.
loser body kept at .lineage/1-b/
