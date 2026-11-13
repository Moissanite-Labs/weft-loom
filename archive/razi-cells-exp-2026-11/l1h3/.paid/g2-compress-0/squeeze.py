import sys, lzma

# Header byte selects one of several LZMA2 literal/position parameter sets.
# Compressor tries each and keeps the smallest output; decompressor reads the header.
SETS = [
    (3, 0, 2),
    (4, 0, 0),
    (1, 0, 0),
    (2, 0, 0),
    (4, 0, 1),
]

def filters(lc, lp, pb, preset=9 | lzma.PRESET_EXTREME):
    return [{"id": lzma.FILTER_LZMA2, "preset": preset, "dict_size": 1 << 20,
             "lc": lc, "lp": lp, "pb": pb, "mf": lzma.MF_BT4, "nice_len": 273}]

def compress(data):
    best = None
    for i, (lc, lp, pb) in enumerate(SETS):
        try:
            out = lzma.compress(data, format=lzma.FORMAT_RAW, filters=filters(lc, lp, pb))
        except lzma.LZMAError:
            continue
        if best is None or len(out) < len(best[1]):
            best = (i, out)
    return bytes([best[0]]) + best[1]

def decompress(blob):
    i = blob[0]
    lc, lp, pb = SETS[i]
    return lzma.decompress(blob[1:], format=lzma.FORMAT_RAW, filters=filters(lc, lp, pb))

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    data = sys.stdin.buffer.read()
    if mode == "c":
        out = compress(data)
    elif mode == "d":
        out = decompress(data)
    else:
        sys.exit("usage: squeeze.py c|d")
    sys.stdout.buffer.write(out)

if __name__ == "__main__":
    main()
