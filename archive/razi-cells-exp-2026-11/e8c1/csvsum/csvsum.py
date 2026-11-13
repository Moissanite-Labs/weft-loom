import os, sys, ctypes, subprocess, mmap

C_SRC = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/mman.h>

typedef struct {
    char key[64];
    int len;
    double sum;
    int used;
} Entry;

#define HT_SIZE 4096
static Entry table[HT_SIZE];

static unsigned int hash_bytes(const char *s, int len) {
    unsigned int h = 2166136261u;
    for (int i = 0; i < len; i++) {
        h = (h ^ (unsigned char)s[i]) * 16777619u;
    }
    return h & (HT_SIZE - 1);
}

static int cmp_entry(const void *a, const void *b) {
    const Entry *ea = *(const Entry **)a;
    const Entry *eb = *(const Entry **)b;
    return strcmp(ea->key, eb->key);
}

void process_buf(const char *buf, size_t size) {
    memset(table, 0, sizeof(table));
    const char *p = buf;
    const char *end = buf + size;
    while (p < end && *p != '\n') p++;
    if (p < end) p++;

    while (p < end) {
        if (*p == '\n' || *p == '\r') { p++; continue; }
        while (p < end && *p != ',') p++;
        if (p >= end) break;
        p++;
        const char *cat_start = p;
        while (p < end && *p != ',') p++;
        if (p >= end) break;
        int cat_len = (int)(p - cat_start);
        p++;

        double sign = 1.0;
        if (p < end && *p == '-') { sign = -1.0; p++; }
        unsigned long long int_part = 0;
        while (p < end && *p >= '0' && *p <= '9') {
            int_part = int_part * 10 + (*p - '0');
            p++;
        }
        double val = (double)int_part;
        if (p < end && *p == '.') {
            p++;
            unsigned long long frac_part = 0;
            double div = 1.0;
            while (p < end && *p >= '0' && *p <= '9') {
                frac_part = frac_part * 10 + (*p - '0');
                div *= 10.0;
                p++;
            }
            val += (double)frac_part / div;
        }
        val *= sign;
        while (p < end && *p != '\n') p++;
        if (p < end) p++;

        unsigned int idx = hash_bytes(cat_start, cat_len);
        while (table[idx].used) {
            if (table[idx].len == cat_len && memcmp(table[idx].key, cat_start, cat_len) == 0) {
                table[idx].sum += val;
                goto next_row;
            }
            idx = (idx + 1) & (HT_SIZE - 1);
        }
        table[idx].used = 1;
        table[idx].len = cat_len;
        memcpy(table[idx].key, cat_start, cat_len);
        table[idx].key[cat_len] = '\0';
        table[idx].sum = val;
        next_row:;
    }

    Entry *used_entries[HT_SIZE];
    int count = 0;
    for (int i = 0; i < HT_SIZE; i++) {
        if (table[i].used) used_entries[count++] = &table[i];
    }
    qsort(used_entries, count, sizeof(Entry *), cmp_entry);
    for (int i = 0; i < count; i++) {
        printf("%s,%.2f\n", used_entries[i]->key, used_entries[i]->sum);
    }
    fflush(stdout);
}

int process_fd(int fd) {
    struct stat st;
    if (fstat(fd, &st) != 0 || st.st_size <= 0) return -1;
    void *ptr = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (ptr == MAP_FAILED) return -1;
    process_buf((const char *)ptr, (size_t)st.st_size);
    munmap(ptr, st.st_size);
    return 0;
}
"""

def main():
    so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_fastcsv_v2.so")
    if not os.path.exists(so_path):
        c_path = so_path + ".c"
        with open(c_path, "w") as f:
            f.write(C_SRC)
        subprocess.run(["clang", "-O3", "-shared", "-fPIC", c_path, "-o", so_path], check=True)
    lib = ctypes.CDLL(so_path)
    lib.process_fd.argtypes = [ctypes.c_int]
    lib.process_fd.restype = ctypes.c_int
    if lib.process_fd(0) != 0:
        lib.process_buf.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        lib.process_buf.restype = None
        data = sys.stdin.buffer.read()
        if data:
            lib.process_buf(data, len(data))

if __name__ == '__main__':
    main()
