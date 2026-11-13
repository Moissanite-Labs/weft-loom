import sys,lzma,bz2,zlib
def main():
    m=sys.argv[1];d=sys.stdin.buffer.read();o=sys.stdout.buffer
    if m=='c':
        f=[lzma.FORMAT_RAW]
        c=[b'\0'+bz2.compress(d,9),b'\1'+lzma.compress(d,format=lzma.FORMAT_RAW,filters=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"lc":4,"lp":0,"pb":0,"dict_size":1<<24}]),b'\2'+d]
        o.write(min(c,key=len))
    else:
        t=d[:1];b=d[1:]
        if t==b'\0':r=bz2.decompress(b)
        elif t==b'\1':r=lzma.decompress(b,format=lzma.FORMAT_RAW,filters=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"lc":4,"lp":0,"pb":0,"dict_size":1<<24}])
        else:r=b
        o.write(r)
main()
