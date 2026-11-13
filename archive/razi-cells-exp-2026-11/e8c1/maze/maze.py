import os, sys, ctypes

SO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_maze_solver_v3.so")

C_CODE = r"""
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/mman.h>

int solve_stdin(void) {
    size_t cap = 4194304 + 8192;
    size_t pad = 4096;
    unsigned char *raw = (unsigned char *)malloc(cap + 2 * pad);
    if (!raw) return -1;
    unsigned char *buf = raw + pad;
    size_t len = 0;
    while (1) {
        if (len + 65536 > cap) {
            cap *= 2;
            unsigned char *nraw = (unsigned char *)realloc(raw, cap + 2 * pad);
            if (!nraw) { free(raw); return -1; }
            raw = nraw;
            buf = raw + pad;
        }
        ssize_t r = read(0, buf + len, cap - len);
        if (r <= 0) break;
        len += r;
    }
    if (len == 0) { free(raw); return -1; }

    unsigned char *ps = (unsigned char *)memchr(buf, 'S', len);
    if (!ps) { free(raw); return -1; }
    int s = (int)(ps - buf);
    unsigned char *pe = (unsigned char *)memchr(buf, 'E', len);
    if (!pe) { free(raw); return -1; }
    int e = (int)(pe - buf);
    if (s == e) { free(raw); return 0; }

    unsigned char *pnl = (unsigned char *)memchr(buf, '\n', len);
    int stride = pnl ? (int)(pnl - buf) + 1 : (int)len + 1;

    unsigned char *grid;
    int free_grid = 0;
    if (stride <= (int)pad) {
        grid = buf - stride;
        memset(grid, '#', stride);
        memset(buf + len, '#', stride);
    } else {
        grid = (unsigned char *)malloc(len + 2 * stride);
        free_grid = 1;
        memset(grid, '#', stride);
        memcpy(grid + stride, buf, len);
        memset(grid + stride + len, '#', stride);
    }

    int start = s + stride;
    int end = e + stride;
    grid[start] = 1;
    grid[end] = 2;

    static int qs_buf[65536];
    static int qe_buf[65536];
    static int nq_buf[65536];
    int qcap = 65536;
    int *qs = qs_buf;
    int *qe = qe_buf;
    int *nq = nq_buf;
    int heap_q = 0;

    int qs_len = 1, qe_len = 1;
    qs[0] = start;
    qe[0] = end;
    int dist = 0;
    int ans = -1;

    while (qs_len > 0 && qe_len > 0) {
        dist++;
        if (qs_len <= qe_len) {
            if (qs_len * 4 >= qcap) {
                int new_cap = qcap * 4;
                if (!heap_q) {
                    int *nqs = (int *)malloc(sizeof(int) * new_cap);
                    int *nqe = (int *)malloc(sizeof(int) * new_cap);
                    int *nnq = (int *)malloc(sizeof(int) * new_cap);
                    memcpy(nqs, qs, sizeof(int) * qs_len);
                    memcpy(nqe, qe, sizeof(int) * qe_len);
                    qs = nqs; qe = nqe; nq = nnq;
                    heap_q = 1;
                } else {
                    qs = (int *)realloc(qs, sizeof(int) * new_cap);
                    qe = (int *)realloc(qe, sizeof(int) * new_cap);
                    nq = (int *)realloc(nq, sizeof(int) * new_cap);
                }
                qcap = new_cap;
            }
            int nq_len = 0;
            for (int i = 0; i < qs_len; i++) {
                int pos = qs[i];
                int p;
                unsigned char v;
                p = pos - 1; v = grid[p];
                if (v == '.') { grid[p] = 1; nq[nq_len++] = p; } else if (v == 2) { ans = dist; goto cleanup; }
                p = pos + 1; v = grid[p];
                if (v == '.') { grid[p] = 1; nq[nq_len++] = p; } else if (v == 2) { ans = dist; goto cleanup; }
                p = pos - stride; v = grid[p];
                if (v == '.') { grid[p] = 1; nq[nq_len++] = p; } else if (v == 2) { ans = dist; goto cleanup; }
                p = pos + stride; v = grid[p];
                if (v == '.') { grid[p] = 1; nq[nq_len++] = p; } else if (v == 2) { ans = dist; goto cleanup; }
            }
            int *tmp = qs; qs = nq; nq = tmp;
            qs_len = nq_len;
        } else {
            if (qe_len * 4 >= qcap) {
                int new_cap = qcap * 4;
                if (!heap_q) {
                    int *nqs = (int *)malloc(sizeof(int) * new_cap);
                    int *nqe = (int *)malloc(sizeof(int) * new_cap);
                    int *nnq = (int *)malloc(sizeof(int) * new_cap);
                    memcpy(nqs, qs, sizeof(int) * qs_len);
                    memcpy(nqe, qe, sizeof(int) * qe_len);
                    qs = nqs; qe = nqe; nq = nnq;
                    heap_q = 1;
                } else {
                    qs = (int *)realloc(qs, sizeof(int) * new_cap);
                    qe = (int *)realloc(qe, sizeof(int) * new_cap);
                    nq = (int *)realloc(nq, sizeof(int) * new_cap);
                }
                qcap = new_cap;
            }
            int nq_len = 0;
            for (int i = 0; i < qe_len; i++) {
                int pos = qe[i];
                int p;
                unsigned char v;
                p = pos - 1; v = grid[p];
                if (v == '.') { grid[p] = 2; nq[nq_len++] = p; } else if (v == 1) { ans = dist; goto cleanup; }
                p = pos + 1; v = grid[p];
                if (v == '.') { grid[p] = 2; nq[nq_len++] = p; } else if (v == 1) { ans = dist; goto cleanup; }
                p = pos - stride; v = grid[p];
                if (v == '.') { grid[p] = 2; nq[nq_len++] = p; } else if (v == 1) { ans = dist; goto cleanup; }
                p = pos + stride; v = grid[p];
                if (v == '.') { grid[p] = 2; nq[nq_len++] = p; } else if (v == 1) { ans = dist; goto cleanup; }
            }
            int *tmp = qe; qe = nq; nq = tmp;
            qe_len = nq_len;
        }
    }

cleanup:
    if (free_grid) free(grid);
    free(raw);
    if (heap_q) {
        free(qs);
        free(qe);
        free(nq);
    }
    return ans;
}
"""

if not os.path.exists(SO_PATH):
    import subprocess
    c_path = SO_PATH + ".c"
    with open(c_path, "w") as f:
        f.write(C_CODE)
    subprocess.run(["gcc", "-O3", "-march=native", "-shared", "-fPIC", c_path, "-o", SO_PATH], check=True)

lib = ctypes.CDLL(SO_PATH)
lib.solve_stdin.argtypes = []
lib.solve_stdin.restype = ctypes.c_int

if __name__ == "__main__":
    print(lib.solve_stdin())
