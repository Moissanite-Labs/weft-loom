import bz2, re, math, sys, collections
sys.path.insert(0,'.')
from bench import corpus
parts=corpus()
for i,p in enumerate(parts[:3]):
    c=len(bz2.compress(p,9))
    toks=re.findall(rb"[A-Za-z']+|[^A-Za-z']+",p)
    cnt=collections.Counter(toks); n=len(toks)
    H=-sum(v/n*math.log2(v/n) for v in cnt.values())
    print(i,len(p),c,round(len(p)/c,3),'tokens',n,'uniq',len(cnt),'H0 bytes',round(n*H/8),'ratio0',round(len(p)/(n*H/8),3))
