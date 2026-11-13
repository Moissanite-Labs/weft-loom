import bz2
def compress(b): return bz2.compress(b, 9)
def decompress(b): return bz2.decompress(b)
