import os
import sys
import ctypes

DYLIB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_csvsum_c1.dylib")

C_CODE = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <pthread.h>

#define HT_SIZE 4096
#define HT_MASK 4095

typedef struct Entry {
    char *key;
    uint32_t len;
    uint32_t hash;
    int64_t val_cents;
    double val_flt;
    int use_flt;
} Entry;

typedef struct Table {
    Entry entries[HT_SIZE];
} Table;

static inline uint32_t hash_bytes(const char *p, uint32_t len) {
    uint32_t h = 2166136261u;
    for (uint32_t i = 0; i < len; i++) {
        h ^= (uint8_t)p[i];
        h *= 16777619u;
    }
    return h ? h : 1;
}

static inline void table_add(Table *t, const char *key, uint32_t len, uint32_t h, int64_t cents, double flt, int is_flt) {
    uint32_t idx = h & HT_MASK;
    while (1) {
        Entry *e = &t->entries[idx];
        if (e->hash == 0) {
            e->hash = h;
            e->len = len;
            e->key = (char *)malloc(len + 1);
            memcpy(e->key, key, len);
            e->key[len] = '\0';
            e->val_cents = cents;
            e->val_flt = flt;
            e->use_flt = is_flt;
            return;
        }
        if (e->hash == h && e->len == len && memcmp(e->key, key, len) == 0) {
            e->val_cents += cents;
            e->val_flt += flt;
            e->use_flt |= is_flt;
            return;
        }
        idx = (idx + 1) & HT_MASK;
    }
}

typedef struct WorkerArg {
    const char *start;
    const char *end;
    Table *table;
} WorkerArg;

static void *worker_fn(void *arg) {
    WorkerArg *w = (WorkerArg *)arg;
    const char *p = w->start;
    const char *end = w->end;
    Table *t = w->table;

    while (p < end) {
        while (p < end && (*p == '\r' || *p == '\n')) p++;
        if (p >= end) break;

        while (p < end && *p != ',') p++;
        if (p >= end) break;
        p++;

        const char *cat_start = p;
        uint32_t h = 2166136261u;
        while (p < end && *p != ',') {
            h ^= (uint8_t)(*p);
            h *= 16777619u;
            p++;
        }
        uint32_t cat_len = (uint32_t)(p - cat_start);
        if (h == 0) h = 1;
        if (p >= end) break;
        p++;

        int sign = 1;
        if (p < end && *p == '-') {
            sign = -1;
            p++;
        } else if (p < end && *p == '+') {
            p++;
        }

        int64_t int_part = 0;
        while (p < end && *p >= '0' && *p <= '9') {
            int_part = int_part * 10 + (*p - '0');
            p++;
        }

        int64_t frac_part = 0;
        int frac_digits = 0;
        int extra_digits = 0;
        double extra_val = 0.0;
        if (p < end && *p == '.') {
            p++;
            while (p < end && *p >= '0' && *p <= '9') {
                if (frac_digits < 2) {
                    frac_part = frac_part * 10 + (*p - '0');
                    frac_digits++;
                } else {
                    extra_digits = 1;
                    break;
                }
                p++;
            }
        }

        if (!extra_digits) {
            if (frac_digits == 1) frac_part *= 10;
            int64_t cents = sign * (int_part * 100 + frac_part);
            while (p < end && *p != '\n') p++;
            if (p < end) p++;
            table_add(t, cat_start, cat_len, h, cents, 0.0, 0);
        } else {
            while (p > cat_start && *(p - 1) != ',') p--;
            char *next_p = NULL;
            extra_val = strtod(p, &next_p);
            p = next_p;
            while (p < end && *p != '\n') p++;
            if (p < end) p++;
            table_add(t, cat_start, cat_len, h, 0, extra_val, 1);
        }
    }
    return NULL;
}

static int cmp_entry(const void *a, const void *b) {
    const Entry *ea = *(const Entry **)a;
    const Entry *eb = *(const Entry **)b;
    return strcmp(ea->key, eb->key);
}

int process_stdin(void) {
    struct stat st;
    const char *data = NULL;
    size_t size = 0;
    int is_mmap = 0;
    char *heap_buf = NULL;

    if (fstat(0, &st) == 0 && S_ISREG(st.st_mode) && st.st_size > 0) {
        size = (size_t)st.st_size;
        void *m = mmap(NULL, size, PROT_READ, MAP_PRIVATE, 0, 0);
        if (m != MAP_FAILED) {
            data = (const char *)m;
            is_mmap = 1;
        }
    }

    if (!data) {
        size_t cap = 65536;
        heap_buf = (char *)malloc(cap);
        size = 0;
        while (1) {
            if (size + 32768 > cap) {
                cap *= 2;
                heap_buf = (char *)realloc(heap_buf, cap);
            }
            ssize_t n = read(0, heap_buf + size, cap - size);
            if (n <= 0) break;
            size += (size_t)n;
        }
        data = heap_buf;
    }

    const char *p = data;
    const char *end = data + size;
    while (p < end && *p != '\n') p++;
    if (p < end) p++;

    int nthreads = (size - (size_t)(p - data) > 1000000) ? 8 : 1;
    pthread_t threads[8];
    WorkerArg args[8];
    Table *tables = (Table *)calloc((size_t)nthreads, sizeof(Table));

    size_t rem = (size_t)(end - p);
    const char *cur = p;
    for (int i = 0; i < nthreads; i++) {
        args[i].start = cur;
        if (i == nthreads - 1) {
            args[i].end = end;
        } else {
            const char *chunk_end = p + (rem * (size_t)(i + 1)) / (size_t)nthreads;
            while (chunk_end < end && *chunk_end != '\n') chunk_end++;
            if (chunk_end < end) chunk_end++;
            args[i].end = chunk_end;
            cur = chunk_end;
        }
        args[i].table = &tables[i];
        if (nthreads > 1) {
            pthread_create(&threads[i], NULL, worker_fn, &args[i]);
        } else {
            worker_fn(&args[0]);
        }
    }

    if (nthreads > 1) {
        for (int i = 0; i < nthreads; i++) {
            pthread_join(threads[i], NULL);
        }
        for (int i = 1; i < nthreads; i++) {
            for (int j = 0; j < HT_SIZE; j++) {
                Entry *e = &tables[i].entries[j];
                if (e->hash != 0) {
                    table_add(&tables[0], e->key, e->len, e->hash, e->val_cents, e->val_flt, e->use_flt);
                    free(e->key);
                }
            }
        }
    }

    Entry *list[HT_SIZE];
    int count = 0;
    for (int j = 0; j < HT_SIZE; j++) {
        if (tables[0].entries[j].hash != 0) {
            list[count++] = &tables[0].entries[j];
        }
    }

    qsort(list, (size_t)count, sizeof(Entry *), cmp_entry);

    char outbuf[65536];
    size_t outpos = 0;
    for (int i = 0; i < count; i++) {
        double total = (double)list[i]->val_cents / 100.0 + list[i]->val_flt;
        int n = snprintf(outbuf + outpos, sizeof(outbuf) - outpos, "%s,%.2f\n", list[i]->key, total);
        outpos += (size_t)n;
        if (outpos + 1024 > sizeof(outbuf)) {
            write(1, outbuf, outpos);
            outpos = 0;
        }
        free(list[i]->key);
    }
    if (outpos > 0) {
        write(1, outbuf, outpos);
    }

    free(tables);
    if (is_mmap) munmap((void *)data, size);
    if (heap_buf) free(heap_buf);
    return 0;
}
"""

def build_dylib():
    if os.path.exists(DYLIB_PATH):
        return True
    try:
        import subprocess
        c_file = DYLIB_PATH + ".c"
        tmp_dylib = DYLIB_PATH + f".tmp.{os.getpid()}"
        with open(c_file, "w") as f:
            f.write(C_CODE)
        cc = "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang"
        sdk = "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk"
        cmd = [cc, "-isysroot", sdk, "-O3", "-shared", "-fPIC", c_file, "-o", tmp_dylib]
        if not os.path.exists(cc):
            cmd = ["cc", "-O3", "-shared", "-fPIC", c_file, "-o", tmp_dylib]
        env = os.environ.copy()
        env["TMPDIR"] = os.path.dirname(DYLIB_PATH) or "."
        subprocess.run(cmd, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.replace(tmp_dylib, DYLIB_PATH)
        try:
            os.remove(c_file)
        except OSError:
            pass
        return True
    except Exception:
        return False

def fallback():
    from collections import defaultdict
    sums = defaultdict(float)
    stdin = sys.stdin.buffer
    stdin.readline()
    for line in stdin:
        if not line:
            continue
        c1 = line.find(b',')
        c2 = line.find(b',', c1 + 1)
        sums[line[c1 + 1:c2]] += float(line[c2 + 1:])
    out = [f"{cat.decode('utf-8')},{sums[cat]:.2f}\n" for cat in sorted(sums.keys())]
    sys.stdout.write("".join(out))

def main():
    if build_dylib():
        try:
            lib = ctypes.CDLL(DYLIB_PATH)
            lib.process_stdin.restype = ctypes.c_int
            lib.process_stdin()
            return
        except Exception:
            pass
    fallback()

if __name__ == '__main__':
    main()
