#!/usr/bin/env python3
"""Shortest path length S->E on a '#'/'.' grid (4-neighbour). Prints length or -1.

Uses a small C BFS helper (bfs.so, built from bfs.c) through ctypes when available;
falls back to an equivalent pure-Python BFS otherwise."""
import sys
import os

_cbfs = None
_tried = False


def _load():
    global _cbfs, _tried
    _tried = True
    try:
        import ctypes
        here = os.path.dirname(os.path.abspath(__file__))
        so = os.path.join(here, "bfs.so")
        src = os.path.join(here, "bfs.c")
        if not os.path.exists(so) and os.path.exists(src):
            import subprocess
            subprocess.run(["cc", "-O2", "-shared", "-fPIC", "-o", so, src],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        lib = ctypes.CDLL(so)
        f = lib.bfs
        f.restype = ctypes.c_long
        f.argtypes = [ctypes.c_void_p, ctypes.c_long, ctypes.c_long, ctypes.c_long, ctypes.c_long]
        _cbfs = (f, ctypes)
    except Exception:
        _cbfs = None


def _pybfs(g, wp, s, e):
    g[s] = 35
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            for q in (p - 1, p + 1, p - wp, p + wp):
                if g[q] != 35:
                    if q == e:
                        return d
                    g[q] = 35
                    app(q)
        frontier = nxt
    return -1


def solve(data):
    lines = data.split(b"\n")
    lines = [ln.rstrip(b"\r") for ln in lines]
    while lines and not lines[-1]:
        lines.pop()
    if not lines:
        return -1
    w = max(len(ln) for ln in lines)
    wp = w + 1  # one wall column between rows
    wall = b"#" * wp
    parts = [wall]
    for ln in lines:
        parts.append(ln.ljust(wp, b"#"))
    parts.append(wall)
    g = bytearray(b"".join(parts))
    s = g.find(b"S")
    e = g.find(b"E")
    if s < 0 or e < 0:
        return -1
    if s == e:
        return 0
    if not _tried:
        _load()
    if _cbfs is not None:
        f, ctypes = _cbfs
        n = len(g)
        buf = (ctypes.c_ubyte * n).from_buffer(g)
        r = f(ctypes.addressof(buf), n, wp, s, e)
        del buf
        if r != -2:
            return r
    return _pybfs(g, wp, s, e)


if __name__ == "__main__":
    print(solve(sys.stdin.buffer.read()))
