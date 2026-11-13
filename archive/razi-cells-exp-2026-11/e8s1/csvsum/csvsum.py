import sys, os, subprocess, ctypes, hashlib

C_SRC = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <unistd.h>
#include <pthread.h>

#define HT_SIZE 4096
#define HT_MASK (HT_SIZE - 1)

typedef struct {
    char key[64];
    int key_len;
    double sum;
    int used;
} Entry;

typedef struct {
    const char *start;
    const char *end;
    Entry table[HT_SIZE];
} ThreadArg;

static inline uint32_t hash_bytes(const char *s, int len) {
    uint32_t h = 2166136261u;
    for (int i = 0; i < len; i++) {
        h ^= (uint8_t)s[i];
        h *= 16777619u;
    }
    return h;
}

static inline void add_entry(Entry *table, const char *key, int len, double val) {
    uint32_t idx = hash_bytes(key, len) & HT_MASK;
    while (table[idx].used) {
        if (table[idx].key_len == len && memcmp(table[idx].key, key, len) == 0) {
            table[idx].sum += val;
            return;
        }
        idx = (idx + 1) & HT_MASK;
    }
    table[idx].used = 1;
    table[idx].key_len = len;
    memcpy(table[idx].key, key, len);
    table[idx].key[len] = '\0';
    table[idx].sum = val;
}

static void *worker(void *arg) {
    ThreadArg *ta = (ThreadArg *)arg;
    memset(ta->table, 0, sizeof(ta->table));
    const char *p = ta->start;
    const char *end = ta->end;

    while (p < end) {
        // skip id until ','
        while (p < end && *p != ',') p++;
        if (p >= end) break;
        p++; // skip ','

        const char *cat_start = p;
        while (p < end && *p != ',') p++;
        int cat_len = (int)(p - cat_start);
        if (p >= end) break;
        p++; // skip ','

        // parse float
        int neg = 0;
        if (p < end && *p == '-') { neg = 1; p++; }
        else if (p < end && *p == '+') { p++; }

        uint64_t int_part = 0;
        while (p < end && *p >= '0' && *p <= '9') {
            int_part = int_part * 10 + (*p - '0');
            p++;
        }
        double val = (double)int_part;
        if (p < end && *p == '.') {
            p++;
            uint64_t frac_part = 0;
            double div = 1.0;
            while (p < end && *p >= '0' && *p <= '9') {
                frac_part = frac_part * 10 + (*p - '0');
                div *= 10.0;
                p++;
            }
            val += (double)frac_part / div;
        }
        if (neg) val = -val;
        while (p < end && *p != '\n') p++;
        if (p < end && *p == '\n') p++;

        if (cat_len > 0) {
            add_entry(ta->table, cat_start, cat_len, val);
        }
    }
    return NULL;
}

static int cmp_entry(const void *a, const void *b) {
    const Entry *ea = (const Entry *)a;
    const Entry *eb = (const Entry *)b;
    return strcmp(ea->key, eb->key);
}

int run_csvsum(void) {
    struct stat st;
    char *buf = NULL;
    size_t size = 0;
    int is_mmap = 0;

    if (fstat(0, &st) == 0 && st.st_size > 0) {
        void *m = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, 0, 0);
        if (m != MAP_FAILED) {
            buf = (char *)m;
            size = st.st_size;
            is_mmap = 1;
        }
    }
    if (!buf) {
        size_t cap = 65536;
        buf = (char *)malloc(cap);
        ssize_t n;
        while ((n = read(0, buf + size, cap - size)) > 0) {
            size += n;
            if (size == cap) {
                cap *= 2;
                buf = (char *)realloc(buf, cap);
            }
        }
    }

    const char *p = buf;
    const char *end = buf + size;
    while (p < end && *p != '\n') p++;
    if (p < end) p++;

    int nthreads = (size > 1000000) ? 8 : 1;
    pthread_t threads[8];
    ThreadArg args[8];

    size_t rem = end - p;
    size_t step = rem / nthreads;
    const char *cur = p;
    for (int i = 0; i < nthreads; i++) {
        args[i].start = cur;
        if (i == nthreads - 1) {
            args[i].end = end;
        } else {
            const char *nxt = cur + step;
            while (nxt < end && *nxt != '\n') nxt++;
            if (nxt < end) nxt++;
            args[i].end = nxt;
            cur = nxt;
        }
        if (nthreads > 1) {
            pthread_create(&threads[i], NULL, worker, &args[i]);
        } else {
            worker(&args[0]);
        }
    }

    if (nthreads > 1) {
        for (int i = 0; i < nthreads; i++) {
            pthread_join(threads[i], NULL);
        }
    }

    Entry final_table[HT_SIZE];
    memset(final_table, 0, sizeof(final_table));
    for (int i = 0; i < nthreads; i++) {
        for (int j = 0; j < HT_SIZE; j++) {
            if (args[i].table[j].used) {
                add_entry(final_table, args[i].table[j].key, args[i].table[j].key_len, args[i].table[j].sum);
            }
        }
    }

    Entry sorted[HT_SIZE];
    int count = 0;
    for (int j = 0; j < HT_SIZE; j++) {
        if (final_table[j].used) {
            sorted[count++] = final_table[j];
        }
    }
    qsort(sorted, count, sizeof(Entry), cmp_entry);

    char outbuf[65536];
    int outpos = 0;
    for (int i = 0; i < count; i++) {
        outpos += snprintf(outbuf + outpos, sizeof(outbuf) - outpos, "%s,%.2f\n", sorted[i].key, sorted[i].sum);
        if (outpos > (int)sizeof(outbuf) - 256) {
            write(1, outbuf, outpos);
            outpos = 0;
        }
    }
    if (outpos > 0) {
        write(1, outbuf, outpos);
    }

    if (is_mmap) munmap(buf, size);
    else free(buf);
    return 0;
}
"""

def main():
    tmpdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp")
    os.makedirs(tmpdir, exist_ok=True)
    h = hashlib.md5(C_SRC.encode()).hexdigest()[:12]
    so_path = os.path.join(tmpdir, f"csvsum_{h}.so")
    if not os.path.exists(so_path):
        c_path = os.path.join(tmpdir, f"csvsum_{h}.c")
        with open(c_path, "w") as f:
            f.write(C_SRC)
        env = os.environ.copy()
        env["TMPDIR"] = tmpdir
        subprocess.run(["clang", "-O3", "-shared", "-fPIC", c_path, "-o", so_path, "-lpthread"], env=env, check=True)
    lib = ctypes.CDLL(so_path)
    lib.run_csvsum()

if __name__ == '__main__':
    main()
