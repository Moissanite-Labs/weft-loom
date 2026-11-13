import os, ctypes

SO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_maze_v2.so")

C_CODE = r"""
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static uint8_t buf[16777216];
static int f_s1[262144], f_s2[262144];
static int f_e1[262144], f_e2[262144];

int solve_stdin(void) {
    ssize_t len = 0, n;
    while ((n = read(0, buf + len, sizeof(buf) - len)) > 0) {
        len += n;
    }
    if (len <= 0) return -1;

    uint8_t *nl = (uint8_t *)memchr(buf, '\n', len);
    int w = nl ? (int)(nl - buf) : (int)len;
    if (w > 0 && buf[w - 1] == '\r') w--;
    if (w <= 0) return -1;
    int step = nl ? (int)(nl - buf) + 1 : w + 1;

    uint8_t *sp = (uint8_t *)memchr(buf, 'S', len);
    uint8_t *ep = (uint8_t *)memchr(buf, 'E', len);
    if (!sp || !ep) return -1;
    int s_pos = (int)(sp - buf);
    int e_pos = (int)(ep - buf);
    if (s_pos == e_pos) return 0;

    int *cs = f_s1, *ns = f_s2;
    int *ce = f_e1, *ne = f_e2;
    int sc = 1, ec = 1;
    cs[0] = s_pos;
    ce[0] = e_pos;
    buf[s_pos] = 1;
    buf[e_pos] = 2;

    int dist = 0;
    int ilen = (int)len;
    while (sc > 0 && ec > 0) {
        dist++;
        if (sc <= ec) {
            int nsc = 0;
            for (int i = 0; i < sc; i++) {
                int u = cs[i];
                int v;
                v = u - 1;
                if (v >= 0) { uint8_t c = buf[v]; if (c == '.') { buf[v] = 1; ns[nsc++] = v; } else if (c == 2) return dist; }
                v = u + 1;
                if (v < ilen) { uint8_t c = buf[v]; if (c == '.') { buf[v] = 1; ns[nsc++] = v; } else if (c == 2) return dist; }
                v = u - step;
                if (v >= 0) { uint8_t c = buf[v]; if (c == '.') { buf[v] = 1; ns[nsc++] = v; } else if (c == 2) return dist; }
                v = u + step;
                if (v < ilen) { uint8_t c = buf[v]; if (c == '.') { buf[v] = 1; ns[nsc++] = v; } else if (c == 2) return dist; }
            }
            int *tmp = cs; cs = ns; ns = tmp;
            sc = nsc;
        } else {
            int nec = 0;
            for (int i = 0; i < ec; i++) {
                int u = ce[i];
                int v;
                v = u - 1;
                if (v >= 0) { uint8_t c = buf[v]; if (c == '.') { buf[v] = 2; ne[nec++] = v; } else if (c == 1) return dist; }
                v = u + 1;
                if (v < ilen) { uint8_t c = buf[v]; if (c == '.') { buf[v] = 2; ne[nec++] = v; } else if (c == 1) return dist; }
                v = u - step;
                if (v >= 0) { uint8_t c = buf[v]; if (c == '.') { buf[v] = 2; ne[nec++] = v; } else if (c == 1) return dist; }
                v = u + step;
                if (v < ilen) { uint8_t c = buf[v]; if (c == '.') { buf[v] = 2; ne[nec++] = v; } else if (c == 1) return dist; }
            }
            int *tmp = ce; ce = ne; ne = tmp;
            ec = nec;
        }
    }
    return -1;
}
"""

if not os.path.exists(SO_PATH):
    import subprocess
    c_path = SO_PATH + ".c"
    with open(c_path, "w") as f:
        f.write(C_CODE)
    subprocess.run(["gcc", "-O3", "-march=native", "-shared", "-fPIC", c_path, "-o", SO_PATH], check=True)

lib = ctypes.CDLL(SO_PATH)
print(lib.solve_stdin())
