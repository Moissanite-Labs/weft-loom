import os
import sys
import subprocess

C_CODE = r"""
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <string.h>

static void radix_sort(int64_t *a, int64_t *tmp, size_t n) {
    size_t count[8][256] = {{0}};
    for (size_t i = 0; i < n; i++) {
        uint64_t u = ((uint64_t)a[i]) ^ 0x8000000000000000ULL;
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
    uint64_t *src = (uint64_t *)a;
    uint64_t *dst = (uint64_t *)tmp;
    for (int pass = 0; pass < 8; pass++) {
        size_t *c = count[pass];
        if (c[(src[0] >> (pass * 8)) & 0xFF] == n) continue;
        size_t pref[256];
        size_t sum = 0;
        for (int i = 0; i < 256; i++) {
            pref[i] = sum;
            sum += c[i];
        }
        int shift = pass * 8;
        for (size_t i = 0; i < n; i++) {
            uint64_t v = src[i];
            dst[pref[(v >> shift) & 0xFF]++] = v;
        }
        uint64_t *swap = src; src = dst; dst = swap;
    }
    if (src != (uint64_t *)a) {
        memcpy(a, src, n * sizeof(uint64_t));
    }
    for (size_t i = 0; i < n; i++) {
        a[i] = (int64_t)(((uint64_t)a[i]) ^ 0x8000000000000000ULL);
    }
}

int main(void) {
    struct stat st;
    const unsigned char *buf = NULL;
    size_t len = 0;
    int mapped = 0;
    if (fstat(0, &st) == 0 && S_ISREG(st.st_mode) && st.st_size > 0) {
        len = st.st_size;
        void *p = mmap(NULL, len, PROT_READ, MAP_PRIVATE, 0, 0);
        if (p != MAP_FAILED) {
            buf = (const unsigned char *)p;
            mapped = 1;
        }
    }
    unsigned char *dyn = NULL;
    if (!buf) {
        size_t cap = 1 << 24;
        dyn = malloc(cap);
        ssize_t r;
        while ((r = read(0, dyn + len, cap - len)) > 0) {
            len += r;
            if (len == cap) {
                cap *= 2;
                dyn = realloc(dyn, cap);
            }
        }
        buf = dyn;
    }
    size_t cap_n = (len / 2) + 16;
    int64_t *arr = malloc(cap_n * sizeof(int64_t));
    size_t n = 0;
    size_t i = 0;
    while (i < len) {
        while (i < len && buf[i] <= ' ') i++;
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
    if (mapped) munmap((void *)buf, len);
    else free(dyn);

    if (n > 1) {
        int64_t *tmp = malloc(n * sizeof(int64_t));
        radix_sort(arr, tmp, n);
        free(tmp);
    }

    char *out = malloc(n * 22 + 64);
    char *p = out;
    for (size_t j = 0; j < n; j++) {
        int64_t v = arr[j];
        uint64_t u;
        if (v < 0) {
            *p++ = '-';
            u = (uint64_t)(-v);
        } else {
            u = (uint64_t)v;
        }
        if (u == 0) {
            *p++ = '0';
        } else {
            char tmp_dig[24];
            int d = 0;
            while (u > 0) {
                tmp_dig[d++] = '0' + (u % 10);
                u /= 10;
            }
            while (d > 0) *p++ = tmp_dig[--d];
        }
        *p++ = '\n';
    }
    size_t out_len = p - out;
    size_t written = 0;
    while (written < out_len) {
        ssize_t w = write(1, out + written, out_len - written);
        if (w <= 0) break;
        written += w;
    }
    free(out);
    free(arr);
    return 0;
}
"""

def main():
    bin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sortints_c_bin1")
    if not os.path.exists(bin_path):
        c_path = bin_path + ".c"
        try:
            with open(c_path, "w") as f:
                f.write(C_CODE)
            subprocess.run(["gcc", "-O3", "-march=native", c_path, "-o", bin_path], check=True)
        except Exception:
            pass
    if os.path.exists(bin_path):
        os.execv(bin_path, [bin_path])
    data = list(map(int, sys.stdin.buffer.read().split()))
    data.sort()
    sys.stdout.write('\n'.join(map(str, data)) + '\n')

if __name__ == '__main__':
    main()
