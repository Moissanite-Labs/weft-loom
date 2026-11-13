import sys,lzma
d=sys.stdin.buffer.read()
if sys.argv[1]=='c':
    o=lzma.compress(d,format=lzma.FORMAT_RAW,filters=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"dict_size":1<<24,"lc":4,"lp":0,"pb":0}])
else:
    o=lzma.decompress(d,format=lzma.FORMAT_RAW,filters=[{"id":lzma.FILTER_LZMA2,"dict_size":1<<24}])
sys.stdout.buffer.write(o)
