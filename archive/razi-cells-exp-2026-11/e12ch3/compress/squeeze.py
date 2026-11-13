import lzma,bz2
def _f(lc,nl,mf):
    return [{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"dict_size":1<<24,"lc":lc,"lp":0,"pb":0,"nice_len":nl,"mf":mf}]
C=[(4,273,lzma.MF_BT4),(3,273,lzma.MF_BT4),(2,273,lzma.MF_BT4),(4,273,lzma.MF_BT3)]
def compress(b):
    best=None
    for i,(lc,nl,mf) in enumerate(C):
        r=bytes([i])+lzma.compress(b,format=lzma.FORMAT_RAW,filters=_f(lc,nl,mf))
        if best is None or len(r)<len(best): best=r
    r=bytes([9])+bz2.compress(b,9)
    return r if len(r)<len(best) else best
def decompress(b):
    i=b[0]
    if i==9: return bz2.decompress(b[1:])
    lc,nl,mf=C[i]
    return lzma.decompress(b[1:],format=lzma.FORMAT_RAW,filters=_f(lc,nl,mf))
