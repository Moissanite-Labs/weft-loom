maze.py DONE state (verified):
- maze.py reads grid from stdin, pads with '#' walls, runs BFS via ctypes on bfs.so (built from bfs.c, level-by-level BFS with int queue, marks visited by writing '#'). Falls back to pure-Python BFS if bfs.so is missing/unbuildable.
- check.py: 600 random small grids vs ref.py -> "bad 0", 134 unreachable cases covered.
- 2000x2000 files b1,b2,b3,b7 (gen.py, fixed seeds) match ref.py: 3998, -1, 3998, -1. big.txt -> -1 (matches ref).
- Assay `python3 bench.py` = 10 / total seconds over the 4 big files. Registered baseline 9.144 (pure Python). With C helper my own runs give ~46-48 (about 5x). ~0.05 s per run now, so Python startup + reading 4 MB dominates; further BFS tuning will not show above 9% noise.
Lessons: ctypes + tiny C .so is the big win for grid BFS in Python; cc prints an xcrun cache warning in this sandbox but still builds. Once per-run time is ~50 ms, the assay is startup-bound; a heavier workload would be needed to measure more gains.
Next step: call done.