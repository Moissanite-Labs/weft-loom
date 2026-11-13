import lzma
F=[{"id":lzma.FORMAT_RAW,"filters":[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"lc":4,"lp":0,"pb":0,"dict_size":1<<22}]}][0]
def compress(b):
    return lzma.compress(b,format=F["id"],filters=F["filters"])
def decompress(b):
    return lzma.decompress(b,format=F["id"],filters=F["filters"])
