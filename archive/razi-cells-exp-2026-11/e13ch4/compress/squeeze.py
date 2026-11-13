import sys,lzma,bz2,zlib
m=sys.argv[1]
d=sys.stdin.buffer.read()
o=sys.stdout.buffer
if m=='c':
    f=[lzma.LZMAFilter] if False else None
    c=[b'L'+lzma.compress(d,format=lzma.FORMAT_RAW,filters=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"lc":4,"lp":0,"pb":0,"dict_size":1<<24}]),
       b'B'+bz2.compress(d,9)]
    o.write(min(c,key=len))
else:
    t,b=d[:1],d[1:]
    if t==b'L':
        o.write(lzma.decompress(b,format=lzma.FORMAT_RAW,filters=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"lc":4,"lp":0,"pb":0,"dict_size":1<<24}]))
    else:
        o.write(bz2.decompress(b))
