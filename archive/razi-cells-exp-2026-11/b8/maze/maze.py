import ctypes, os, subprocess, sys

_SO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_maze_c.so")
_C_SRC = r"""
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

int solve_c(const uint8_t *raw, int len) {
    if (len <= 0) return -1;
    int s_pos = -1, e_pos = -1, nl = -1;
    for (int i = 0; i < len; i++) {
        uint8_t c = raw[i];
        if (c == 'S') s_pos = i;
        else if (c == 'E') e_pos = i;
        else if (c == '\n' && nl == -1) nl = i;
    }
    if (s_pos == -1 || e_pos == -1) return -1;
    if (s_pos == e_pos) return 0;
    int stride = (nl != -1) ? (nl + 1) : (len + 1);
    int total = len + 2 * stride + 2;
    uint8_t *vis = (uint8_t *)calloc(total, 1);
    int *q = (int *)malloc((len + 1) * sizeof(int));
    int *dist = (int *)malloc((len + 1) * sizeof(int));
    if (!vis || !q || !dist) {
        free(vis); free(q); free(dist);
        return -1;
    }
    int head = 0, tail = 0;
    q[tail] = s_pos;
    dist[tail] = 0;
    tail++;
    vis[s_pos + stride] = 1;
    int ans = -1;
    int d_offs[4] = {-stride, stride, -1, 1};
    while (head < tail) {
        int u = q[head];
        int d = dist[head];
        head++;
        int nd = d + 1;
        for (int k = 0; k < 4; k++) {
            int v = u + d_offs[k];
            if ((unsigned)v < (unsigned)len && !vis[v + stride]) {
                uint8_t c = raw[v];
                if (c == '.') {
                    vis[v + stride] = 1;
                    q[tail] = v;
                    dist[tail] = nd;
                    tail++;
                } else if (v == e_pos) {
                    ans = nd;
                    goto done;
                }
            }
        }
    }
done:
    free(vis);
    free(q);
    free(dist);
    return ans;
}
"""

if not os.path.exists(_SO_PATH):
    c_path = _SO_PATH + ".c"
    with open(c_path, "w") as f:
        f.write(_C_SRC)
    subprocess.run(["gcc", "-O3", "-shared", "-fPIC", c_path, "-o", _SO_PATH], check=True)

_lib = ctypes.CDLL(_SO_PATH)
_lib.solve_c.argtypes = [ctypes.c_char_p, ctypes.c_int]
_lib.solve_c.restype = ctypes.c_int

def solve(raw: bytes) -> int:
    if not raw:
        return -1
    return _lib.solve_c(raw, len(raw))

def main():
    raw = sys.stdin.buffer.read()
    print(solve(raw))

if __name__ == '__main__':
    main()
