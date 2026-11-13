import os
import ctypes

SO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_wf_fast3.dylib")

C_SRC = r"""
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <pthread.h>

#define HT_BITS 15
#define HT_SIZE (1 << HT_BITS)
#define HT_MASK (HT_SIZE - 1)
#define NTHREADS 4

typedef struct {
    uint32_t hash;
    uint32_t str_off;
    uint32_t count;
    uint32_t len;
} Entry;

typedef struct {
    Entry htab[HT_SIZE];
    char arena[2 * 1024 * 1024];
    uint32_t arena_used;
    const uint8_t *buf;
    size_t start;
    size_t end;
} Worker;

static Worker workers[NTHREADS];
static uint8_t char_map[256];

static void init_map(void) {
    for (int i = 'a'; i <= 'z'; i++) char_map[i] = (uint8_t)i;
    for (int i = 'A'; i <= 'Z'; i++) char_map[i] = (uint8_t)(i + 32);
}

static inline void insert_word(Worker *wk, const char *w, uint32_t len, uint32_t h) {
    uint32_t idx = (h ^ (h >> 15)) & HT_MASK;
    while (1) {
        Entry *e = &wk->htab[idx];
        if (e->count == 0) {
            e->hash = h;
            e->len = len;
            e->count = 1;
            e->str_off = wk->arena_used;
            memcpy(wk->arena + wk->arena_used, w, len);
            wk->arena[wk->arena_used + len] = '\0';
            wk->arena_used += len + 1;
            return;
        }
        if (e->hash == h && e->len == len && memcmp(wk->arena + e->str_off, w, len) == 0) {
            e->count++;
            return;
        }
        idx = (idx + 1) & HT_MASK;
    }
}

static void *thread_fn(void *arg) {
    Worker *wk = (Worker *)arg;
    memset(wk->htab, 0, sizeof(wk->htab));
    wk->arena_used = 1;
    char word[4096];
    uint32_t wlen = 0;
    uint32_t h = 2166136261U;
    const uint8_t *buf = wk->buf;
    size_t end = wk->end;
    for (size_t i = wk->start; i < end; i++) {
        uint8_t low = char_map[buf[i]];
        if (low) {
            if (wlen < 4095) {
                word[wlen++] = (char)low;
                h = (h ^ low) * 16777619U;
            }
        } else if (wlen > 0) {
            insert_word(wk, word, wlen, h);
            wlen = 0;
            h = 2166136261U;
        }
    }
    if (wlen > 0) {
        insert_word(wk, word, wlen, h);
    }
    return NULL;
}

static void process_all(const uint8_t *buf, size_t size) {
    if (size < 262144) {
        workers[0].buf = buf;
        workers[0].start = 0;
        workers[0].end = size;
        thread_fn(&workers[0]);
        return;
    }
    pthread_t tids[NTHREADS];
    size_t chunk = size / NTHREADS;
    size_t cur = 0;
    for (int t = 0; t < NTHREADS; t++) {
        workers[t].buf = buf;
        workers[t].start = cur;
        size_t nxt = (t == NTHREADS - 1) ? size : cur + chunk;
        while (nxt < size && char_map[buf[nxt]] != 0) nxt++;
        workers[t].end = nxt;
        cur = nxt;
        pthread_create(&tids[t], NULL, thread_fn, &workers[t]);
    }
    for (int t = 0; t < NTHREADS; t++) {
        pthread_join(tids[t], NULL);
    }
    Worker *w0 = &workers[0];
    for (int t = 1; t < NTHREADS; t++) {
        Worker *wt = &workers[t];
        for (int i = 0; i < HT_SIZE; i++) {
            Entry *e = &wt->htab[i];
            if (e->count == 0) continue;
            uint32_t h = e->hash;
            uint32_t len = e->len;
            const char *w = wt->arena + e->str_off;
            uint32_t idx = (h ^ (h >> 15)) & HT_MASK;
            while (1) {
                Entry *e0 = &w0->htab[idx];
                if (e0->count == 0) {
                    e0->hash = h;
                    e0->len = len;
                    e0->count = e->count;
                    e0->str_off = w0->arena_used;
                    memcpy(w0->arena + w0->arena_used, w, len + 1);
                    w0->arena_used += len + 1;
                    break;
                }
                if (e0->hash == h && e0->len == len && memcmp(w0->arena + e0->str_off, w, len) == 0) {
                    e0->count += e->count;
                    break;
                }
                idx = (idx + 1) & HT_MASK;
            }
        }
    }
}

int run_wf(void) {
    init_map();
    struct stat st;
    if (fstat(0, &st) == 0 && S_ISREG(st.st_mode) && st.st_size > 0) {
        void *p = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, 0, 0);
        if (p != MAP_FAILED) {
            process_all((const uint8_t *)p, st.st_size);
            munmap(p, st.st_size);
            goto done_reading;
        }
    }

    size_t cap = 1024 * 1024;
    size_t len = 0;
    uint8_t *buf = (uint8_t *)malloc(cap);
    while (1) {
        if (len == cap) {
            cap *= 2;
            buf = (uint8_t *)realloc(buf, cap);
        }
        ssize_t n = read(0, buf + len, cap - len);
        if (n <= 0) break;
        len += n;
    }
    process_all(buf, len);
    free(buf);

done_reading:;
    Worker *w0 = &workers[0];
    Entry *top[10];
    int ntop = 0;
    for (int i = 0; i < HT_SIZE; i++) {
        if (w0->htab[i].count == 0) continue;
        Entry *cur = &w0->htab[i];
        int pos = ntop;
        while (pos > 0) {
            Entry *prev = top[pos - 1];
            if (cur->count > prev->count ||
                (cur->count == prev->count && strcmp(w0->arena + cur->str_off, w0->arena + prev->str_off) < 0)) {
                pos--;
            } else {
                break;
            }
        }
        if (pos < 10) {
            int limit = ntop < 9 ? ntop : 9;
            for (int j = limit; j > pos; j--) {
                top[j] = top[j - 1];
            }
            top[pos] = cur;
            if (ntop < 10) ntop++;
        }
    }
    for (int i = 0; i < ntop; i++) {
        printf("%s %u\n", w0->arena + top[i]->str_off, top[i]->count);
    }
    fflush(stdout);
    return 0;
}
"""

if not os.path.exists(SO_PATH):
    import subprocess
    c_path = SO_PATH + ".c"
    with open(c_path, "w") as f:
        f.write(C_SRC)
    subprocess.run(["clang", "-O3", "-shared", "-fPIC", "-pthread", c_path, "-o", SO_PATH], check=True)

ctypes.CDLL(SO_PATH).run_wf()
