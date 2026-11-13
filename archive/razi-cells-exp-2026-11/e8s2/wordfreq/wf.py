import os
import sys
import mmap
import ctypes
import subprocess
from collections import Counter

SO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_wf_fast.so")

C_SRC = r"""
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

typedef struct {
    uint64_t hash;
    uint32_t offset;
    uint16_t len;
    uint32_t count;
} Entry;

#define HT_BITS 18
#define HT_SIZE (1 << HT_BITS)
#define HT_MASK (HT_SIZE - 1)

static Entry table[HT_SIZE];
static char arena[4 * 1024 * 1024];
static uint32_t arena_pos = 1;

static int cmp_entry(const void *a, const void *b) {
    const Entry *ea = *(const Entry **)a;
    const Entry *eb = *(const Entry **)b;
    if (ea->count != eb->count) return (eb->count > ea->count) ? 1 : -1;
    return strcmp(arena + ea->offset, arena + eb->offset);
}

int run_fd(int fd) {
    struct stat st;
    if (fstat(fd, &st) != 0 || st.st_size <= 0) return -1;
    size_t size = (size_t)st.st_size;
    const unsigned char *buf = (const unsigned char *)mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (buf == MAP_FAILED) return -1;

    memset(table, 0, sizeof(table));
    arena_pos = 1;

    char wbuf[256];
    size_t i = 0;
    while (i < size) {
        unsigned char c = buf[i];
        unsigned char lc = c | 32;
        if (lc >= 'a' && lc <= 'z') {
            uint64_t h = 14695981039346656037ULL;
            uint16_t wlen = 0;
            do {
                if (wlen < 255) wbuf[wlen++] = (char)lc;
                h = (h ^ lc) * 1099511628211ULL;
                i++;
                if (i >= size) break;
                c = buf[i];
                lc = c | 32;
            } while (lc >= 'a' && lc <= 'z');

            uint32_t idx = (uint32_t)h & HT_MASK;
            while (1) {
                Entry *e = &table[idx];
                if (e->offset == 0) {
                    e->hash = h;
                    e->offset = arena_pos;
                    e->len = wlen;
                    e->count = 1;
                    memcpy(arena + arena_pos, wbuf, wlen);
                    arena[arena_pos + wlen] = '\0';
                    arena_pos += wlen + 1;
                    break;
                }
                if (e->hash == h && e->len == wlen && memcmp(arena + e->offset, wbuf, wlen) == 0) {
                    e->count++;
                    break;
                }
                idx = (idx + 1) & HT_MASK;
            }
        } else {
            i++;
        }
    }
    munmap((void *)buf, size);

    Entry *top[10];
    int ntop = 0;
    for (int j = 0; j < HT_SIZE; j++) {
        if (table[j].offset == 0) continue;
        Entry *cur = &table[j];
        if (ntop < 10) {
            top[ntop++] = cur;
            for (int k = ntop - 1; k > 0 && cmp_entry(&top[k], &top[k-1]) < 0; k--) {
                Entry *tmp = top[k]; top[k] = top[k-1]; top[k-1] = tmp;
            }
        } else if (cmp_entry(&cur, &top[9]) < 0) {
            top[9] = cur;
            for (int k = 9; k > 0 && cmp_entry(&top[k], &top[k-1]) < 0; k--) {
                Entry *tmp = top[k]; top[k] = top[k-1]; top[k-1] = tmp;
            }
        }
    }
    for (int j = 0; j < ntop; j++) {
        printf("%s %u\n", arena + top[j]->offset, top[j]->count);
    }
    fflush(stdout);
    return 0;
}
"""

TABLE = bytes(
    c + 32 if 65 <= c <= 90 else (c if 97 <= c <= 122 else 32)
    for c in range(256)
)

def ensure_so():
    if os.path.exists(SO_PATH):
        return True
    try:
        p = subprocess.Popen(
            ["gcc", "-O3", "-shared", "-fPIC", "-x", "c", "-", "-o", SO_PATH],
            stdin=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        p.communicate(C_SRC.encode())
        return p.returncode == 0
    except Exception:
        return False

def main():
    if ensure_so():
        try:
            lib = ctypes.CDLL(SO_PATH)
            if lib.run_fd(sys.stdin.fileno()) == 0:
                return
        except Exception:
            pass

    counts = Counter(sys.stdin.buffer.read().translate(TABLE).split())
    if not counts:
        return
    mc = counts.most_common(20)
    tenth_count = mc[min(9, len(mc) - 1)][1]
    candidates = [(-c, w) for w, c in counts.items() if c >= tenth_count]
    candidates.sort()
    sys.stdout.write(''.join(f"{w.decode()} {-nc}\n" for nc, w in candidates[:10]))

if __name__ == '__main__':
    main()
