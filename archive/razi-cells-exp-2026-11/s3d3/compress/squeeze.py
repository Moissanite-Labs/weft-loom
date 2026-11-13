import sys,lzma,bz2
m=sys.argv[1];d=sys.stdin.buffer.read()
f=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"lc":4,"lp":0,"pb":0,"dict_size":1<<24}]
if m=='c':
    sys.stdout.buffer.write(lzma.compress(d,format=lzma.FORMAT_RAW,filters=f))
else:
    sys.stdout.buffer.write(lzma.decompress(d,format=lzma.FORMAT_RAW,filters=f))
