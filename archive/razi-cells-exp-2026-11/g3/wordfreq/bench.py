import time, re
from collections import Counter
data = open('corpus.txt','rb').read()

def v1():
    t = data.decode('utf-8','replace').lower()
    return Counter(re.findall(r'[a-z]+', t))

def v2():
    return Counter(re.findall(rb'[a-z]+', data.lower()))

TBL = bytes((c+32 if 65<=c<=90 else c) if (97<=c<=122 or 65<=c<=90) else 32 for c in range(256))
def v3():
    return Counter(data.translate(TBL).split())

for f in (v1,v2,v3):
    ts=[]
    for _ in range(3):
        s=time.perf_counter(); c=f(); ts.append(time.perf_counter()-s)
    print(f.__name__, min(ts), c.most_common(3))
