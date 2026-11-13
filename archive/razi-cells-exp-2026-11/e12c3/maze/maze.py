import sys
def main():
    lines = sys.stdin.read().split()
    h = len(lines); w = len(lines[0])
    s = ''.join(lines)
    W = w
    si = s.find('S'); ei = s.find('E')
    blocked = bytearray(1 if c == '#' else 0 for c in s)
    # pad via bounds checks using column tracking
    dist = [-1] * (h * w)
    dist[si] = 0
    cur = [si]; d = 0
    while cur and dist[ei] < 0:
        d += 1
        nxt = []
        for p in cur:
            c = p % W
            if p >= W:
                q = p - W
                if not blocked[q] and dist[q] < 0: dist[q] = d; nxt.append(q)
            q = p + W
            if q < h * W and not blocked[q] and dist[q] < 0: dist[q] = d; nxt.append(q)
            if c:
                q = p - 1
                if not blocked[q] and dist[q] < 0: dist[q] = d; nxt.append(q)
            if c < W - 1:
                q = p + 1
                if not blocked[q] and dist[q] < 0: dist[q] = d; nxt.append(q)
        cur = nxt
    print(dist[ei])
main()
