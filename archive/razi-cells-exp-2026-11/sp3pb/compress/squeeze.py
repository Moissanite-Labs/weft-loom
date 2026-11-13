import sys, lzma, bz2
def c(b):
    f=[lzma.LZMAFilter] if 0 else None
    a=lzma.compress(b,format=lzma.FORMAT_RAW,filters=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"dict_size":1<<24,"lc":4,"lp":0,"pb":0}])
    z=bz2.compress(b,9)
    return b'L'+a if len(a)<=len(z) else b'B'+z
def d(b):
    if b[:1]==b'L':
        return lzma.decompress(b[1:],format=lzma.FORMAT_RAW,filters=[{"id":lzma.FILTER_LZMA2,"preset":9,"dict_size":1<<24,"lc":4,"lp":0,"pb":0}])
    if b[:1]==b'B': return bz2.decompress(b[1:])
    return b
data=sys.stdin.buffer.read()
sys.stdout.buffer.write((c if sys.argv[1]=='c' else d)(data))
