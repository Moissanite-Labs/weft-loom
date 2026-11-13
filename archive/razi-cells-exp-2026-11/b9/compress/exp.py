import lzma, bz2, zlib, json, re, sys
sys.path.insert(0,'.')
from bench import corpus
parts = corpus()
tin = sum(map(len,parts))
def L(data, **kw):
    f=[dict(id=lzma.FILTER_LZMA2, preset=9|lzma.PRESET_EXTREME, **kw)]
    return len(lzma.compress(data, format=lzma.FORMAT_RAW, filters=f))
cfgs = {
 'base lc4': dict(lc=4,lp=0,pb=0),
 'lc4 nice273': dict(lc=4,lp=0,pb=0,nice_len=273,mf=lzma.MF_BT4,depth=0),
 'lc3 nice273': dict(lc=3,lp=0,pb=0,nice_len=273),
 'lc2 nice273': dict(lc=2,lp=0,pb=0,nice_len=273),
}
for k,c in cfgs.items():
    print(k, round(tin/sum(L(p,**c) for p in parts),4))
print('bz2', round(tin/sum(len(bz2.compress(p,9)) for p in parts),4))
# per-part best
print('bestmix', round(tin/sum(min(len(bz2.compress(p,9)),L(p,lc=4,lp=0,pb=0,nice_len=273)) for p in parts),4))
# json compact transform
def jt(p):
    try:
        o=json.loads(p)
        if json.dumps(o,indent=2).encode()==p: return json.dumps(o,separators=(',',':')).encode()
    except Exception: pass
    return p
print('jsoncompact+lzma', round(tin/sum(L(jt(p),lc=4,lp=0,pb=0,nice_len=273) for p in parts),4))
print('jsoncompact+bz2', round(tin/sum(len(bz2.compress(jt(p),9)) for p in parts),4))
