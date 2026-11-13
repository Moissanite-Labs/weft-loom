import sys
from collections import deque
for f in sys.argv[1:]:
    rows = open(f,'rb').read().split()
    n=len(rows); m=len(rows[0])
    seen=set([(0,0)]); q=deque([(0,0)])
    while q and len(seen)<200000:
        i,j=q.popleft()
        for a,b in ((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
            if 0<=a<n and 0<=b<m and rows[a][b]!=35 and (a,b) not in seen:
                seen.add((a,b)); q.append((a,b))
    print(f, n, m, 'reached from S:', len(seen), 'open frac', sum(r.count(b'.') for r in rows)/(n*m), rows[0][:1], rows[-1][-1:])
    for r in rows[:6]: print(r[:40].decode())
