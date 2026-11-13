#!/usr/bin/env python3
"""Shortest S->E path in a '#'/'.' grid, 4-neighbour, read from stdin.

A small native BFS helper is used when available; a self-contained pure-Python
BFS is kept as an exact fallback.  Both treat S and E as open cells and pad
ragged rows with walls, so out-of-bounds steps are never possible.
"""
import ctypes
import os
import sys
from collections import deque

WALL = 35  # ord('#')
S_CH = 83  # ord('S')
E_CH = 69  # ord('E')


def solve_python(data: bytes) -> int:
    lines = data.splitlines()
    if not lines:
        return -1

    w = max(len(line) for line in lines)
    stride = w + 2

    # Padded byte grid: a wall border makes all 4 neighbour indices safe.
    grid = bytearray(b'#' * stride)
    start = -1
    goal = -1
    base = stride

    for line in lines:
        p = line.find(S_CH)
        if p >= 0 and start < 0:
            start = base + p + 1
        q = line.find(E_CH)
        if q >= 0 and goal < 0:
            goal = base + q + 1

        grid.append(WALL)
        grid.extend(line)
        missing = w - len(line)
        if missing:
            grid.extend(b'#' * missing)
        grid.append(WALL)
        base += stride

    grid.extend(b'#' * stride)

    if start < 0 or goal < 0 or grid[goal] == WALL:
        return -1
    if start == goal:
        return 0

    g = grid
    g[start] = WALL
    q = deque((start,))
    popleft = q.popleft
    extend = q.extend
    dist = 0

    # BFS by whole levels; the mutable grid doubles as the visited bitmap.
    while q:
        nxt = []
        append = nxt.append
        for _ in range(len(q)):
            i = popleft()

            j = i + 1
            if g[j] != WALL:
                if j == goal:
                    return dist + 1
                g[j] = WALL
                append(j)

            j = i - 1
            if g[j] != WALL:
                if j == goal:
                    return dist + 1
                g[j] = WALL
                append(j)

            j = i + stride
            if g[j] != WALL:
                if j == goal:
                    return dist + 1
                g[j] = WALL
                append(j)

            j = i - stride
            if g[j] != WALL:
                if j == goal:
                    return dist + 1
                g[j] = WALL
                append(j)

        extend(nxt)
        dist += 1

    return -1


def _build_so(so_path: str, c_path: str) -> bool:
    """Best-effort rebuild if the shared object is missing."""
    import subprocess

    base = os.path.dirname(so_path)
    tmp = os.path.join(base, ".tmp", "ccache")
    try:
        os.makedirs(tmp, exist_ok=True)
        env = dict(os.environ, TMPDIR=tmp)
        for cc in ("cc", "gcc", "clang"):
            try:
                p = subprocess.run(
                    [cc, "-O3", "-shared", "-fPIC", "-o", so_path, c_path],
                    env=env, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, timeout=20,
                )
                if p.returncode == 0 and os.path.isfile(so_path):
                    return True
            except (OSError, subprocess.SubprocessError):
                pass
    except OSError:
        pass
    return False


def _load_solver():
    base = os.path.dirname(os.path.abspath(__file__))
    so_path = os.path.join(base, "mazehelper.so")
    c_path = os.path.join(base, "mazehelper.c")
    if not os.path.isfile(so_path) and os.path.isfile(c_path):
        _build_so(so_path, c_path)
    try:
        lib = ctypes.CDLL(so_path)
        fn = lib.maze_solve
        fn.argtypes = (ctypes.c_char_p, ctypes.c_size_t)
        fn.restype = ctypes.c_int
        return fn
    except (OSError, AttributeError):
        return None


_C_SOLVE = _load_solver()


def solve(data: bytes) -> int:
    if _C_SOLVE is not None:
        return _C_SOLVE(data, len(data))
    return solve_python(data)


def main() -> None:
    sys.stdout.write(str(solve(sys.stdin.buffer.read())))


if __name__ == "__main__":
    main()
