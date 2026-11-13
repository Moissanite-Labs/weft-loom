import random, json
def ref(a,b):
    n=len(b); prev=[0]*(n+1)
    for x in a:
        cur=[0]*(n+1)
        for j in range(n):
            cur[j+1]=prev[j]+1 if x==b[j] else max(prev[j+1],cur[j])
        prev=cur
    return prev[n]
random.seed(7)
cases=[]
for k in (4,26):
    alpha="abcdefghijklmnopqrstuvwxyz"[:k]
    a="".join(random.choice(alpha) for _ in range(3000))
    b="".join(random.choice(alpha) for _ in range(3000))
    cases.append([a,b,ref(a,b)])
json.dump(cases,open("bench_cases.json","w"))
print([c[2] for c in cases])
