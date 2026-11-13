import sys,lzma
m=sys.argv[1]
d=sys.stdin.buffer.read()
F=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"dict_size":1<<20,"lc":4,"lp":0,"pb":0}]
if m=='c':
    o=lzma.compress(d,format=lzma.FORMAT_RAW,filters=F)
else:
    o=lzma.decompress(d,format=lzma.FORMAT_RAW,filters=F)
sys.stdout.buffer.write(o)
