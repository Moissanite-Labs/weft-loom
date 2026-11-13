def ref(a,b):
    n=len(b)
    prev=[0]*(n+1)
    for x in a:
        cur=[0]
        for j in range(n):
            cur.append(prev[j]+1 if x==b[j] else max(prev[j+1],cur[j]))
        prev=cur
    return prev[n]
