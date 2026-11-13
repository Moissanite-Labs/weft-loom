import sys
d = {}
cur = []
text = sys.stdin.read().lower()
for ch in text:
    if 'a' <= ch <= 'z':
        cur.append(ch)
    elif cur:
        w = "".join(cur); d[w] = d.get(w,0)+1; cur = []
if cur:
    w = "".join(cur); d[w] = d.get(w,0)+1
for w,n in sorted(d.items(), key=lambda kv:(-kv[1],kv[0]))[:10]:
    print(w,n)
