import re, lzma, bz2, sys
sys.argv=['x']
import importlib.util
spec=importlib.util.spec_from_file_location('b','bench.py')
src=open('bench.py').read().replace('\nmain()\n','\n')
ns={}; exec(src,ns)
inputs=ns['gen']()
F=lambda lc,lp,pb:[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"lc":lc,"lp":lp,"pb":pb,"nice_len":273,"mf":lzma.MF_BT4,"depth":0}]
def lz(d,lc=4,lp=0,pb=0): return len(lzma.compress(d,format=lzma.FORMAT_RAW,filters=F(lc,lp,pb)))
def tok(d):
    # split into words and separators, build dictionary of frequent tokens
    parts=re.findall(rb'[A-Za-z]+|[^A-Za-z]+',d)
    from collections import Counter
    c=Counter(p for p in parts if p.isalpha())
    top=[w for w,_ in c.most_common(200)]
    m={w:i for i,w in enumerate(top)}
    out=bytearray()
    for p in parts:
        if p in m:
            i=m[p]
            if i<120: out.append(0x80|i)
            else: out+=bytes([0xF8|(i>>8)&7, i&255]) if False else bytes([0xFF, i-120])
        else: out+=p
    hdr=b'\n'.join(top)
    return bytes(out), hdr
for d in inputs:
    t,h=tok(d)
    print(len(d), lz(d), bz2.compress(d,9).__len__(), 'tok', lz(t)+len(lzma.compress(h)), [lz(d,lc,0,pb) for lc,pb in ((3,0),(2,0),(1,0),(0,0),(4,1),(4,2))])
print("tok+bz2")
for d in inputs:
    t,h=tok(d)
    print(len(d), bz2.compress(d,9).__len__(), len(bz2.compress(t,9))+len(bz2.compress(h,9)), len(bz2.compress(h+b'\0'+t,9)))
