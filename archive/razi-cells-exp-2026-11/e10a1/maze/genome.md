maze cell state (3 steps left at time of writing):
- maze.py = detour-ordered BFS (moves toward E cost 0, away cost 1; answer = Manhattan + 2*detours), zero-copy grid when input is rectangular. ADOPTED, +298% (assay 2.14 -> ~8.5, python3 bench.py).
- Verified: 150 random small mazes vs ref.py (0 bad) via vt.py, plus big.txt=4008, big2.txt=-1, blocked.txt=-1, s.txt=24, t.txt=-1 all match ref.py.
- big.txt made by gen.py (2000x2000, seed 12345, p=0.3). big.expected was missing at start; regenerate with `python3 ref.py < big.txt > big.expected`.
- Caveat: big.txt is an easy case (only 5 detours), so the speed number reflects open random mazes, not winding worst-case mazes.
- Next: nothing needed; call done.