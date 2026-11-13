import sys,lzma
m=sys.argv[1]
d=sys.stdin.buffer.read()
F=dict(format=lzma.FORMAT_RAW,filters=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"dict_size":1<<24,"lc":4,"lp":0,"pb":0}])
o=lzma.compress(d,**F) if m=='c' else lzma.decompress(d,**F)
sys.stdout.buffer.write(o)
