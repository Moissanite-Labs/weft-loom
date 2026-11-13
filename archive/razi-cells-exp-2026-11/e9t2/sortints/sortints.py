import sys, os, ctypes, subprocess

C_CODE = r"""
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <string.h>

static void radix_sort_i64(int64_t *a, int64_t *tmp, size_t n) {
    size_t count[8][256];
    memset(count, 0, sizeof(count));
    for (size_t i = 0; i < n; i++) {
        uint64_t u = (uint64_t)a[i] ^ 0x8000000000000000ULL;
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
        if (count[pass][((uint64_t)src[0] >> (pass * 8)) & 0xFF] == n) continue;
        size_t pref[256], sum = 0;
        for (int b = 0; b < 256; b++) {
            pref[b] = sum;
            sum += count[pass][b];
        }
        int shift = pass * 8;
        for (size_t i = 0; i < n; i++) {
            uint64_t u = (uint64_t)src[i];
            dst[pref[(u >> shift) & 0xFF]++] = (int64_t)u;
        }
        int64_t *t = src; src = dst; dst = t;
    }
    for (size_t i = 0; i < n; i++) {
        a[i] = (int64_t)((uint64_t)src[i] ^ 0x8000000000000000ULL);
    }
}

int run_sort(void) {
    struct stat st;
    char *buf = NULL;
    size_t len = 0;
    int is_mmap = 0;
    if (fstat(0, &st) == 0 && st.st_size > 0 && S_ISREG(st.st_mode)) {
        len = st.st_size;
        buf = mmap(NULL, len, PROT_READ, MAP_PRIVATE, 0, 0);
        if (buf != MAP_FAILED) is_mmap = 1;
        else buf = NULL;
    }
    if (!buf) {
        size_t cap = 1 << 20;
        buf = malloc(cap);
        ssize_t r;
        while ((r = read(0, buf + len, cap - len)) > 0) {
            len += r;
            if (len == cap) { cap *= 2; buf = realloc(buf, cap); }
        }
    }
    size_t cap_n = (len / 2) + 16;
    int64_t *nums = malloc(cap_n * sizeof(int64_t));
    size_t n = 0;
    size_t i = 0;
    while (i < len) {
        while (i < len && (unsigned char)buf[i] <= ' ') i++;
        if (i >= len) break;
        int neg = 0;
        if (buf[i] == '-') { neg = 1; i++; }
        else if (buf[i] == '+') { i++; }
        uint64_t val = 0;
        while (i < len && (unsigned char)(buf[i] - '0') <= 9) {
            val = val * 10 + (buf[i] - '0');
            i++;
        }
        nums[n++] = neg ? -(int64_t)val : (int64_t)val;
    }
    if (is_mmap) munmap(buf, len);
    else free(buf);

    if (n > 1) {
        int64_t *tmp = malloc(n * sizeof(int64_t));
        radix_sort_i64(nums, tmp, n);
        free(tmp);
    }

    char *out = malloc(n * 22 + 64);
    char *p = out;
    for (size_t j = 0; j < n; j++) {
        int64_t v = nums[j];
        uint64_t u;
        if (v < 0) { *p++ = '-'; u = (uint64_t)(-v); }
        else { u = (uint64_t)v; }
        char digits[24];
        int d = 0;
        do {
            digits[d++] = '0' + (u % 10);
            u /= 10;
        } while (u > 0);
        while (d > 0) *p++ = digits[--d];
        *p++ = '\n';
    }
    size_t out_len = p - out;
    size_t off = 0;
    while (off < out_len) {
        ssize_t w = write(1, out + off, out_len - off);
        if (w <= 0) break;
        off += w;
    }
    free(out);
    free(nums);
    return 0;
}
"""

def main():
    so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_sortfast.so")
    if not os.path.exists(so_path):
        c_path = so_path + ".c"
        with open(c_path, "w") as f:
            f.write(C_CODE)
        subprocess.run(["cc", "-O3", "-shared", "-fPIC", c_path, "-o", so_path], check=True)
    lib = ctypes.CDLL(so_path)
    lib.run_sort()

if __name__ == '__main__':
    main()
