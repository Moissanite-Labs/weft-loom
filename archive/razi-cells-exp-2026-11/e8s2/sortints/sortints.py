import os
import sys
import ctypes
import subprocess

SO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_fastsort.so")

C_CODE = r"""
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>
#include <string.h>

static void radix_sort_i64(int64_t *a, size_t n) {
    if (n < 2) return;
    int64_t *tmp = (int64_t *)malloc(n * sizeof(int64_t));
    size_t count[8][256] = {0};
    for (size_t i = 0; i < n; i++) {
        uint64_t u = ((uint64_t)a[i]) ^ (1ULL << 63);
        a[i] = (int64_t)u;
        count[0][u & 0xFF]++;
        count[1][(u >> 8) & 0xFF]++;
        count[2][(u >> 16) & 0xFF]++;
        count[3][(u >> 24) & 0xFF]++;
        count[4][(u >> 32) & 0xFF]++;
        count[5][(u >> 40) & 0xFF]++;
        count[6][(u >> 48) & 0xFF]++;
        count[7][(u >> 56) & 0xFF]++;
    }
    int64_t *src = a, *dst = tmp;
    for (int pass = 0; pass < 8; pass++) {
        size_t *c = count[pass];
        if (c[(uint64_t)src[0] >> (pass * 8) & 0xFF] == n) continue;
        size_t pref[256], sum = 0;
        for (int i = 0; i < 256; i++) {
            pref[i] = sum;
            sum += c[i];
        }
        int shift = pass * 8;
        for (size_t i = 0; i < n; i++) {
            uint64_t u = (uint64_t)src[i];
            dst[pref[(u >> shift) & 0xFF]++] = (int64_t)u;
        }
        int64_t *t = src; src = dst; dst = t;
    }
    for (size_t i = 0; i < n; i++) {
        a[i] = (int64_t)(((uint64_t)src[i]) ^ (1ULL << 63));
    }
    free(tmp);
}

void sort_And_print(const char *buf, size_t len) {
    size_t cap = len / 2 + 16;
    int64_t *arr = (int64_t *)malloc(cap * sizeof(int64_t));
    size_t n = 0;
    size_t i = 0;
    while (i < len) {
        while (i < len && (unsigned char)buf[i] <= ' ') i++;
        if (i >= len) break;
        int neg = 0;
        if (buf[i] == '-') { neg = 1; i++; }
        else if (buf[i] == '+') { i++; }
        uint64_t val = 0;
        while (i < len && buf[i] >= '0' && buf[i] <= '9') {
            val = val * 10 + (buf[i] - '0');
            i++;
        }
        arr[n++] = neg ? -(int64_t)val : (int64_t)val;
    }
    radix_sort_i64(arr, n);
    char *out = (char *)malloc(n * 22 + 16);
    size_t pos = 0;
    char tmp[24];
    for (size_t j = 0; j < n; j++) {
        int64_t v = arr[j];
        uint64_t u;
        if (v < 0) {
            out[pos++] = '-';
            u = (uint64_t)(-v);
        } else {
            u = (uint64_t)v;
        }
        int k = 0;
        do {
            tmp[k++] = '0' + (u % 10);
            u /= 10;
        } while (u > 0);
        while (k > 0) out[pos++] = tmp[--k];
        out[pos++] = '\n';
    }
    size_t written = 0;
    while (written < pos) {
        ssize_t w = write(1, out + written, pos - written);
        if (w <= 0) break;
        written += w;
    }
    free(out);
    free(arr);
}
"""

def get_lib():
    if not os.path.exists(SO_PATH):
        c_path = SO_PATH + ".c"
        with open(c_path, "w") as f:
            f.write(C_CODE)
        subprocess.run(["clang", "-O3", "-shared", "-fPIC", c_path, "-o", SO_PATH], check=True)
    lib = ctypes.CDLL(SO_PATH)
    lib.sort_And_print.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
    lib.sort_And_print.restype = None
    return lib

def main():
    data = sys.stdin.buffer.read()
    if not data:
        return
    lib = get_lib()
    lib.sort_And_print(data, len(data))

if __name__ == "__main__":
    main()
