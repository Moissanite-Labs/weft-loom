import sys,lzma
m=sys.argv[1];d=sys.stdin.buffer.read()
f=[dict(id=lzma.FILTER_LZMA2,preset=9|lzma.PRESET_EXTREME,lc=4,lp=0,pb=0,dict_size=1<<22)]
if m=='c':o=lzma.compress(d,format=lzma.FORMAT_RAW,filters=f)
else:o=lzma.decompress(d,format=lzma.FORMAT_RAW,filters=f)
sys.stdout.buffer.write(o)
