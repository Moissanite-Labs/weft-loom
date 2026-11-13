import lzma, time, bench
d = bench.dataset()
base = dict(id=lzma.FILTER_LZMA1, dict_size=1<<24, mode=lzma.MODE_NORMAL,
            nice_len=273, mf=lzma.MF_BT4, depth=0)
res=[]
t0=time.time()
for lc in (0,1,2,3,4):
    for lp in (0,1,2):
        if lc+lp>4: continue
        for pb in (0,1,2):
            f=dict(base); f.update(lc=lc,lp=lp,pb=pb)
            c=lzma.compress(d, format=lzma.FORMAT_RAW, filters=[f])
            res.append((len(c),lc,lp,pb))
res.sort()
for r in res[:10]: print(r, r[0]/len(d))
print("time",round(time.time()-t0,2))
