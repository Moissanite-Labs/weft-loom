#!/usr/bin/env python3
import os
import sys

_TAG = "v1"

_C_SRC = r'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>

int main(void){
    size_t cap = 1u << 20, len = 0;
    char *buf = (char*)malloc(cap);
    if(!buf) return 1;
    for(;;){
        if(len == cap){
            cap <<= 1;
            char *nb = (char*)realloc(buf, cap);
            if(!nb) return 1;
            buf = nb;
        }
        ssize_t r = read(0, buf + len, cap - len);
        if(r < 0) return 1;
        if(r == 0) break;
        len += (size_t)r;
    }

    size_t W = 0;
    {
        size_t i = 0;
        while(i < len && buf[i] != '\n'){
            if(buf[i] != '\r') W++;
            i++;
        }
    }
    if(W == 0){ printf("-1\n"); return 0; }

    size_t H = 0;
    for(size_t i = 0; i < len; i++)
        if(buf[i] == '\n') H++;
    if(len > 0 && buf[len-1] != '\n') H++;
    if(H == 0){ printf("-1\n"); return 0; }

    size_t stride = W + 2;
    size_t total = (H + 2) * stride;
    char *g = (char*)malloc(total);
    if(!g) return 1;
    memset(g, '#', total);

    int32_t *dist = (int32_t*)malloc(total * sizeof(int32_t));
    if(!dist) return 1;
    memset(dist, 0xff, total * sizeof(int32_t));

    size_t start = (size_t)-1, goal = (size_t)-1;
    size_t p = 0;
    for(size_t y = 0; y < H; y++){
        size_t e = p;
        while(e < len && buf[e] != '\n') e++;
        size_t x = 0;
        for(size_t q = p; q < e && x < W; q++){
            unsigned char c = (unsigned char)buf[q];
            if(c == '\r') continue;
            size_t idx = (y + 1) * stride + (x + 1);
            if(c == 'S'){
                if(start == (size_t)-1) start = idx;
                c = '.';
            } else if(c == 'E'){
                if(goal == (size_t)-1) goal = idx;
                c = '.';
            } else if(c != '.'){
                c = '#';
            }
            g[idx] = (char)c;
            x++;
        }
        if(e < len) p = e + 1; else p = len;
    }

    free(buf);
    if(start == (size_t)-1 || goal == (size_t)-1){
        printf("-1\n");
        return 0;
    }

    int32_t *q = (int32_t*)malloc(total * sizeof(int32_t));
    if(!q) return 1;
    size_t head = 0, tail = 0;
    int ans = -1;
    dist[start] = 0;
    q[tail++] = (int32_t)start;
    int32_t sstride = (int32_t)stride;
    while(head < tail){
        int32_t cur = q[head++];
        if((size_t)cur == goal){
            ans = (int)dist[cur];
            break;
        }
        int32_t nd = dist[cur] + 1;
        int32_t n;
        n = cur - 1;
        if(g[n] == '.' && dist[n] < 0){ dist[n] = nd; q[tail++] = n; }
        n = cur + 1;
        if(g[n] == '.' && dist[n] < 0){ dist[n] = nd; q[tail++] = n; }
        n = cur - sstride;
        if(g[n] == '.' && dist[n] < 0){ dist[n] = nd; q[tail++] = n; }
        n = cur + sstride;
        if(g[n] == '.' && dist[n] < 0){ dist[n] = nd; q[tail++] = n; }
    }
    printf("%d\n", ans);
    return 0;
}
'''


def _fallback():
    from collections import deque
    data = sys.stdin.buffer.read()
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    lines = [ln[:-1] if ln.endswith(b'\r') else ln for ln in lines]
    if not lines:
        print(-1)
        return
    w = max(len(ln) for ln in lines)
    h = len(lines)
    if w == 0:
        print(-1)
        return
    grid = bytearray(b'#' * (w * h))
    start = goal = -1
    for y, ln in enumerate(lines):
        base = y * w
        for x, c in enumerate(ln):
            if c == 46 or c == 83 or c == 69:
                grid[base + x] = 46
                if c == 83 and start < 0:
                    start = base + x
                elif c == 69 and goal < 0:
                    goal = base + x
    if start < 0 or goal < 0:
        print(-1)
        return
    n = w * h
    dist = array('i', [-1]) * n
    dist[start] = 0
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            print(dist[cur])
            return
        d = dist[cur] + 1
        x = cur % w
        if x > 0:
            nb = cur - 1
            if grid[nb] == 46 and dist[nb] < 0:
                dist[nb] = d; q.append(nb)
        if x + 1 < w:
            nb = cur + 1
            if grid[nb] == 46 and dist[nb] < 0:
                dist[nb] = d; q.append(nb)
        nb = cur - w
        if nb >= 0 and grid[nb] == 46 and dist[nb] < 0:
            dist[nb] = d; q.append(nb)
        nb = cur + w
        if nb < n and grid[nb] == 46 and dist[nb] < 0:
            dist[nb] = d; q.append(nb)
    print(-1)


def main():
    d = os.path.dirname(os.path.abspath(__file__))
    binp = os.path.join(d, '.maze_bin_' + _TAG)
    if not os.path.exists(binp):
        try:
            srcp = os.path.join(d, '.maze_bin_' + _TAG + '.c')
            with open(srcp, 'w') as f:
                f.write(_C_SRC)
            import subprocess
            tmp = binp + '.%d' % os.getpid()
            cc = os.environ.get('CC', 'cc')
            r = subprocess.call([cc, '-O2', '-std=c11', '-o', tmp, srcp],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
            if r != 0:
                _fallback()
                return
            os.replace(tmp, binp)
            os.chmod(binp, 0o755)
        except Exception:
            _fallback()
            return
    try:
        os.execv(binp, [binp])
    except OSError:
        _fallback()


if __name__ == '__main__':
    from array import array
    main()
