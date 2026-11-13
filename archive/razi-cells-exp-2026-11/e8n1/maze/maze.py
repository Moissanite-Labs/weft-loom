import sys
import os
import ctypes
from collections import deque

_lib = None
try:
    _so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_maze.so")
    if os.path.exists(_so_path):
        _lib = ctypes.CDLL(_so_path)
        _lib.solve_c.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        _lib.solve_c.restype = ctypes.c_int
except Exception:
    _lib = None


def _solve_py(data: bytes) -> int:
    lines = data.splitlines()
    if not lines:
        return -1

    H = len(lines)
    W = len(lines[0])
    stride = W + 2
    grid = bytearray(b"#" * (stride * (H + 2)))

    start = -1
    end = -1

    for r, line in enumerate(lines):
        offset = (r + 1) * stride + 1
        grid[offset : offset + W] = line
        if start == -1:
            s_idx = line.find(b"S")
            if s_idx != -1:
                start = offset + s_idx
        if end == -1:
            e_idx = line.find(b"E")
            if e_idx != -1:
                end = offset + e_idx

    if start == -1 or end == -1:
        return -1
    if start == end:
        return 0

    grid[start] = 1
    grid[end] = 2

    qS = deque([start])
    qE = deque([end])
    distS = 0
    distE = 0

    while qS and qE:
        if len(qS) <= len(qE):
            for _ in range(len(qS)):
                u = qS.popleft()
                for n in (u - 1, u + 1, u - stride, u + stride):
                    c = grid[n]
                    if c == 46:
                        grid[n] = 1
                        qS.append(n)
                    elif c == 2:
                        return distS + distE + 1
            distS += 1
        else:
            for _ in range(len(qE)):
                u = qE.popleft()
                for n in (u - 1, u + 1, u - stride, u + stride):
                    c = grid[n]
                    if c == 46:
                        grid[n] = 2
                        qE.append(n)
                    elif c == 1:
                        return distS + distE + 1
            distE += 1

    return -1


def solve():
    if hasattr(sys.stdin, "buffer"):
        data = sys.stdin.buffer.read()
    else:
        data = sys.stdin.read().encode()

    if not data:
        print(-1)
        return

    if _lib is not None and b"\r" not in data:
        res = _lib.solve_c(data, len(data))
        print(res)
        return

    print(_solve_py(data))


if __name__ == "__main__":
    solve()
