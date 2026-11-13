import os
import subprocess
import ctypes
import sys

SO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_maze_fast.so")

C_SRC = r"""
#include <stdlib.h>
#include <string.h>

int solve_maze(unsigned char *buf, int len) {
    int s_pos = -1, e_pos = -1, nl = -1;
    for (int i = 0; i < len; i++) {
        unsigned char c = buf[i];
        if (c == 'S') s_pos = i;
        else if (c == 'E') e_pos = i;
        else if (c == '\n' && nl == -1) nl = i;
    }
    if (s_pos == -1 || e_pos == -1) return -1;
    if (s_pos == e_pos) return 0;

    int stride = (nl == -1) ? (len + 1) : (nl + 1);
    int total = len + 2 * stride;
    unsigned char *grid = (unsigned char *)malloc(total);
    memset(grid, 3, stride);
    for (int i = 0; i < len; i++) {
        unsigned char c = buf[i];
        grid[stride + i] = (c == '.') ? 0 : 3;
    }
    memset(grid + stride + len, 3, stride);

    int start = s_pos + stride;
    int end = e_pos + stride;
    grid[start] = 1;
    grid[end] = 2;

    int *qs = (int *)malloc(sizeof(int) * (len + 1));
    int *qe = (int *)malloc(sizeof(int) * (len + 1));
    int hs = 0, ts = 0, he = 0, te = 0;
    qs[ts++] = start;
    qe[te++] = end;

    int ds = 0, de = 0, ans = -1;
    int dirs[4] = {-1, 1, -stride, stride};

    while (hs < ts && he < te) {
        if ((ts - hs) <= (te - he)) {
            ds++;
            int limit = ts;
            while (hs < limit) {
                int u = qs[hs++];
                for (int d = 0; d < 4; d++) {
                    int v = u + dirs[d];
                    unsigned char st = grid[v];
                    if (st == 0) {
                        grid[v] = 1;
                        qs[ts++] = v;
                    } else if (st == 2) {
                        ans = ds + de;
                        goto done;
                    }
                }
            }
        } else {
            de++;
            int limit = te;
            while (he < limit) {
                int u = qe[he++];
                for (int d = 0; d < 4; d++) {
                    int v = u + dirs[d];
                    unsigned char st = grid[v];
                    if (st == 0) {
                        grid[v] = 2;
                        qe[te++] = v;
                    } else if (st == 1) {
                        ans = ds + de;
                        goto done;
                    }
                }
            }
        }
    }
done:
    free(grid);
    free(qs);
    free(qe);
    return ans;
}
"""

def ensure_so():
    if not os.path.exists(SO_PATH):
        c_path = SO_PATH + ".c"
        with open(c_path, "w") as f:
            f.write(C_SRC)
        subprocess.run(["gcc", "-O3", "-march=native", "-shared", "-fPIC", c_path, "-o", SO_PATH], check=True)

def solve():
    ensure_so()
    lib = ctypes.CDLL(SO_PATH)
    lib.solve_maze.argtypes = [ctypes.c_char_p, ctypes.c_int]
    lib.solve_maze.restype = ctypes.c_int
    data = sys.stdin.buffer.read()
    if not data:
        print(-1)
        return
    res = lib.solve_maze(data, len(data))
    print(res)

if __name__ == '__main__':
    solve()
