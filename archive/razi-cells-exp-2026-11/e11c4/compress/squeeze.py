import lzma
def compress(b):
    return lzma.compress(b, format=lzma.FORMAT_RAW, filters=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"lc":4,"lp":0,"pb":0,"dict_size":1<<20}])
def decompress(b):
    return lzma.decompress(b, format=lzma.FORMAT_RAW, filters=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"lc":4,"lp":0,"pb":0,"dict_size":1<<20}])
