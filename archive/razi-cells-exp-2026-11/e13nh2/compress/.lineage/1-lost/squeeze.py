import sys,lzma,bz2,zlib
m=sys.argv[1]
d=sys.stdin.buffer.read()
o=sys.stdout.buffer
if m=='c':
    f=[lambda x:lzma.compress(x,format=lzma.FORMAT_RAW,filters=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"lc":4,"lp":0,"pb":0,"dict_size":1<<22}]),lambda x:bz2.compress(x,9),lambda x:zlib.compress(x,9)]
    r=[bytes([i])+g(d) for i,g in enumerate(f)]
    o.write(min(r,key=len))
else:
    t=d[0];b=d[1:]
    if t==0:
        x=lzma.decompress(b,format=lzma.FORMAT_RAW,filters=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"lc":4,"lp":0,"pb":0,"dict_size":1<<22}])
    elif t==1:x=bz2.decompress(b)
    else:x=zlib.decompress(b)
    o.write(x)
