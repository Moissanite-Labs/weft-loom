#!/usr/bin/env python3
"""maze.py: read a grid of '#' and '.' with S and E on stdin, print the
shortest 4-neighbour path length from S to E, or -1 if unreachable.

Speed tiers (same answer from each):
  ext - small C BFS built once as a CPython extension, cached beside this file
  ct  - the same C code loaded through ctypes (if Python.h is unavailable)
  py  - pure-Python BFS (no compiler)
Set MAZE_IMPL=ext|ct|py to force one tier.
"""
import sys, os

MOD = "_mazefast2"
CTLIB = "_mazefast2_ct.so"

C_SRC = r"""
#ifdef WITH_PY
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#endif
#include <stdint.h>
#include <stdlib.h>
/* g: rows of equal width separated by one non-open byte (stride = width+1),
   with one padding row of `stride` non-open bytes before and after.
   Open cells are '.', 'S', 'E'. Returns length, -1 unreachable, -2 = not
   handled (g untouched). */
long maze_bfs(unsigned char *g, long n, long stride, long s, long e) {
    long i, head = 0, tail = 1, d = 0;
    int32_t *q;
    const int32_t st = (int32_t)stride;
    if (stride < 1 || n >= 2147483000L || s < stride || e < stride ||
        s >= n - stride || e >= n - stride) return -2;
    if (s == e) return 0;
    q = (int32_t *)malloc(sizeof(int32_t) * (size_t)(n + 8));
    if (!q) return -2;
    for (i = 0; i < n; i++) {
        unsigned char c = g[i];
        g[i] = (unsigned char)((c == '.') | (c == 'S') | (c == 'E'));
    }
    q[0] = (int32_t)s; g[s] = 0;
    while (head < tail) {
        long end = tail;
        d++;
        for (; head < end; head++) {
            /* branchless push: always write, advance only if cell was open */
            int32_t c = q[head], nb;
            nb = c + 1;  q[tail] = nb; tail += g[nb]; g[nb] = 0;
            nb = c - 1;  q[tail] = nb; tail += g[nb]; g[nb] = 0;
            nb = c + st; q[tail] = nb; tail += g[nb]; g[nb] = 0;
            nb = c - st; q[tail] = nb; tail += g[nb]; g[nb] = 0;
        }
        if (!g[e]) { free(q); return d; }
    }
    free(q);
    return -1;
}
#ifdef WITH_PY
static PyObject *py_bfs(PyObject *self, PyObject *args) {
    Py_buffer b; Py_ssize_t stride, s, e; long r;
    if (!PyArg_ParseTuple(args, "w*nnn", &b, &stride, &s, &e)) return NULL;
    r = maze_bfs((unsigned char *)b.buf, (long)b.len, (long)stride, (long)s, (long)e);
    PyBuffer_Release(&b);
    return PyLong_FromLong(r);
}
static PyMethodDef methods[] = {{"bfs", py_bfs, METH_VARARGS, ""}, {NULL, NULL, 0, NULL}};
static struct PyModuleDef moddef = {PyModuleDef_HEAD_INIT, "_mazefast2", NULL, -1, methods};
PyMODINIT_FUNC PyInit__mazefast2(void) { return PyModule_Create(&moddef); }
#endif
"""


def _here():
    return os.path.dirname(os.path.abspath(__file__))


def _tmpdir():
    import tempfile
    uid = os.getuid() if hasattr(os, "getuid") else 0
    d = os.path.join(tempfile.gettempdir(), "mazepy-cache-%d" % uid)
    os.makedirs(d, mode=0o700, exist_ok=True)
    return d


def _load_ext(d):
    if d not in sys.path:
        sys.path.append(d)
    return __import__(MOD).bfs


def _load_ct(d):
    p = os.path.join(d, CTLIB)
    if not os.path.exists(p):
        raise OSError(p)
    import ctypes
    f = ctypes.CDLL(p).maze_bfs
    f.restype = ctypes.c_long
    f.argtypes = [ctypes.c_void_p] + [ctypes.c_long] * 4

    def bfs(g, stride, s, e):
        buf = (ctypes.c_ubyte * len(g)).from_buffer(g)
        return f(ctypes.addressof(buf), len(g), stride, s, e)
    return bfs


def _build(d, kind):
    src = os.path.join(d, "_mazefast2_%d.c" % os.getpid())
    tmp = src[:-2] + ".tmp"
    try:
        with open(src, "w") as fh:
            fh.write(C_SRC)
        import subprocess
        if kind == "ext":
            import sysconfig
            inc = sysconfig.get_paths()["include"]
            if not os.path.exists(os.path.join(inc, "Python.h")):
                return False
            out = os.path.join(d, MOD + (sysconfig.get_config_var("EXT_SUFFIX") or ".so"))
            flags = ["-DWITH_PY", "-I", inc]
            if sys.platform == "darwin":
                flags += ["-bundle", "-undefined", "dynamic_lookup"]
            else:
                flags += ["-shared"]
        else:
            out = os.path.join(d, CTLIB)
            flags = ["-shared"]
        r = subprocess.run([os.environ.get("CC", "cc"), "-O2", "-fPIC"] + flags + [src, "-o", tmp],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        if r.returncode != 0:
            return False
        os.replace(tmp, out)
        return True
    except Exception:
        return False
    finally:
        for p in (src, tmp):
            try:
                os.unlink(p)
            except OSError:
                pass


_FAST = {}


def _fast(kind):
    """Return bfs(g, stride, s, e) for this tier, building it once if needed."""
    if kind in _FAST:
        return _FAST[kind]
    loader = _load_ext if kind == "ext" else _load_ct
    f = None
    try:
        f = loader(_here())
    except Exception:
        marker = "_mazefast2.no%s.%d%d" % ((kind,) + tuple(sys.version_info[:2]))
        dirs = []
        for mk in (_here, _tmpdir):
            try:
                dirs.append(mk())
            except Exception:
                pass
        for d in dirs[1:]:
            try:
                f = loader(d)
                break
            except Exception:
                pass
        if f is None and not any(os.path.exists(os.path.join(d, marker)) for d in dirs):
            for d in dirs:
                if _build(d, kind):
                    try:
                        import importlib
                        importlib.invalidate_caches()
                        f = loader(d)
                        break
                    except Exception:
                        pass
            if f is None:  # remember the failure so later runs do not retry
                for d in dirs:
                    try:
                        open(os.path.join(d, marker), "w").close()
                        break
                    except OSError:
                        pass
    _FAST[kind] = f
    return f


def _py_bfs(g, stride, s, e):
    if s == e:
        return 0
    g[s] = 35
    frontier = [s]
    d = 0
    offs = (1, -1, stride, -stride)
    while frontier:
        d += 1
        nxt = []
        push = nxt.append
        for c in frontier:
            for o in offs:
                nb = c + o
                ch = g[nb]
                if ch == 46 or ch == 69 or ch == 83:
                    if nb == e:
                        return d
                    g[nb] = 35
                    push(nb)
        frontier = nxt
    return -1


def _prepare(data):
    """Lay the grid out as padded rows; return (g, stride, s, e) or None."""
    if b"\r" in data:
        data = data.replace(b"\r", b"")
    n = len(data)
    w = data.find(b"\n")
    st = w + 1
    uniform = False
    if w > 0 and n % st == 0:
        rows = n // st
        uniform = data.count(b"\n") == rows and data[w::st] == b"\n" * rows
    if not uniform:  # ragged rows, blank lines or no final newline
        lines = data.split(b"\n")
        while lines and not lines[-1]:
            lines.pop()
        if not lines:
            return None
        w = max(map(len, lines))
        st = w + 1
        data = b"\n".join([ln.ljust(w, b"#") for ln in lines]) + b"\n"
    s = data.find(b"S")
    e = data.find(b"E")
    if s < 0 or e < 0:
        return None
    g = bytearray(st)
    g += data
    g += bytes(st)
    return g, st, s + st, e + st


def solve(data, impl=None):
    p = _prepare(data)
    if p is None:
        return -1
    g, st, s, e = p
    if impl is None:
        impl = os.environ.get("MAZE_IMPL") or None
    if impl != "py":
        for kind in (("ext", "ct") if impl is None else (impl,)):
            f = _fast(kind)
            if f is not None:
                try:
                    r = f(g, st, s, e)
                except Exception:
                    r = -2
                if r != -2:
                    return r
    return _py_bfs(g, st, s, e)


def main():
    sys.stdout.write("%d\n" % solve(sys.stdin.buffer.read()))


if __name__ == "__main__":
    main()
