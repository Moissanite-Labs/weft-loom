#!/usr/bin/env python3
"""Shortest path in a '#'/'.' grid with S and E, 4-neighbour moves.

Strategy: a tiny C BFS kernel is compiled once (cached next to this file) and
then exec'd, so startup is ~ms and a 2000x2000 maze is solved in well under a
second.  A pure-Python BFS fallback keeps the program correct even if no C
compiler is available (fine for small/medium grids).
"""
import os
import sys
import hashlib
import subprocess

C_SRC = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

int main(void) {
    size_t cap = 1u << 22, len = 0, r;
    char *buf = (char *)malloc(cap);
    if (!buf) return 0;
    while ((r = fread(buf + len, 1, cap - len - 1, stdin)) > 0) {
        len += r;
        if (len + 1 >= cap) {
            cap *= 2;
            char *nb = (char *)realloc(buf, cap);
            if (!nb) return 0;
            buf = nb;
        }
    }
    buf[len] = '\0';

    /* Split into non-empty lines. */
    size_t *starts = (size_t *)malloc(sizeof(size_t) * (len + 1));
    if (!starts) return 0;
    int h = 0, w = 0, first = 1;
    size_t i = 0;
    while (i < len) {
        while (i < len && (buf[i] == '\n' || buf[i] == '\r')) i++;
        if (i >= len) break;
        size_t s = i;
        while (i < len && buf[i] != '\n') i++;
        size_t e = i;
        if (e > s && buf[e - 1] == '\r') e--;
        if (first) { w = (int)(e - s); first = 0; }
        starts[h++] = s;
    }
    if (h <= 0 || w <= 0) { printf("-1\n"); return 0; }

    size_t n = (size_t)h * (size_t)w;
    int32_t *dist = (int32_t *)malloc(n * sizeof(int32_t));
    int32_t *q = (int32_t *)malloc(n * sizeof(int32_t));
    if (!dist || !q) { printf("-1\n"); return 0; }
    memset(dist, 0xFF, n * sizeof(int32_t));   /* all -1 */

    int32_t sidx = -1, eidx = -1;
    for (int rr = 0; rr < h; rr++) {
        const char *row = buf + starts[rr];
        for (int cc = 0; cc < w; cc++) {
            char ch = row[cc];
            if (ch == 'S') sidx = (int32_t)rr * w + cc;
            else if (ch == 'E') eidx = (int32_t)rr * w + cc;
        }
    }
    if (sidx < 0 || eidx < 0) { printf("-1\n"); return 0; }

    size_t head = 0, tail = 0;
    q[tail++] = sidx;
    dist[sidx] = 0;
    while (head < tail) {
        int32_t v = q[head++];
        if (v == eidx) break;
        int32_t d = dist[v] + 1;
        int rr = v / w, cc = v - rr * w;
        if (rr > 0) {
            int32_t u = v - w;
            if (dist[u] < 0 && buf[starts[rr - 1] + cc] != '#') { dist[u] = d; q[tail++] = u; }
        }
        if (rr + 1 < h) {
            int32_t u = v + w;
            if (dist[u] < 0 && buf[starts[rr + 1] + cc] != '#') { dist[u] = d; q[tail++] = u; }
        }
        if (cc > 0) {
            int32_t u = v - 1;
            if (dist[u] < 0 && buf[starts[rr] + cc - 1] != '#') { dist[u] = d; q[tail++] = u; }
        }
        if (cc + 1 < w) {
            int32_t u = v + 1;
            if (dist[u] < 0 && buf[starts[rr] + cc + 1] != '#') { dist[u] = d; q[tail++] = u; }
        }
    }
    printf("%d\n", (int)dist[eidx]);
    return 0;
}
"""


def _compiled_binary():
    here = os.path.dirname(os.path.abspath(__file__))
    tag = hashlib.sha1(C_SRC.encode()).hexdigest()[:12]
    binp = os.path.join(here, ".maze_bin_" + tag)
    if os.path.exists(binp) and os.access(binp, os.X_OK):
        return binp
    csrc = os.path.join(here, ".maze_src_" + tag + ".c")
    try:
        with open(csrc, "w") as f:
            f.write(C_SRC)
    except OSError:
        return None
    env = dict(os.environ)
    for k in ("TMPDIR", "TMP", "TEMP"):
        env[k] = here
    for cc in ("cc", "gcc", "clang"):
        try:
            res = subprocess.run([cc, "-O2", "-o", binp, csrc],
                                 env=env, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        except Exception:
            continue
        if res.returncode == 0 and os.path.exists(binp):
            return binp
    return None


def _fallback():
    from collections import deque
    data = sys.stdin.buffer.read().decode("utf-8", "replace")
    rows = [ln.rstrip("\r") for ln in data.split("\n")]
    rows = [ln for ln in rows if ln.strip()]
    if not rows:
        print(-1)
        return
    h, w = len(rows), max(len(r) for r in rows)
    start = end = None
    for r, ln in enumerate(rows):
        for c, ch in enumerate(ln):
            if ch == "S":
                start = (r, c)
            elif ch == "E":
                end = (r, c)
    if start is None or end is None:
        print(-1)
        return
    dist = {start: 0}
    dq = deque([start])
    while dq:
        r, c = dq.popleft()
        d = dist[(r, c)]
        if (r, c) == end:
            print(d)
            return
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in dist:
                ch = rows[nr][nc] if nc < len(rows[nr]) else '#'
                if ch != '#':
                    dist[(nr, nc)] = d + 1
                    dq.append((nr, nc))
    print(-1)


def main():
    binp = _compiled_binary()
    if binp:
        os.execv(binp, [binp])
    _fallback()


if __name__ == "__main__":
    main()
