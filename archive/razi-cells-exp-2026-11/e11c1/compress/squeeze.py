import bz2,lzma
def compress(b):
    return bz2.compress(b,9)
def decompress(b):
    return bz2.decompress(b)
