import sys, lzma, bz2
def filt(lc, lp, pb, d=8<<20):
    return [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "dict_size": d,
             "lc": lc, "lp": lp, "pb": pb, "nice_len": 273, "mf": lzma.MF_BT4}]
def main():
    m = sys.argv[1]
    data = sys.stdin.buffer.read()
    out = sys.stdout.buffer
    if m == "c":
        best = None
        for lc in (2, 3, 4):
            for pb in (0, 1, 2):
                for lp in (0,):
                    if lc + lp > 4: continue
                    try:
                        c = lzma.compress(data, lzma.FORMAT_RAW, filters=filt(lc, lp, pb))
                    except Exception:
                        continue
                    if best is None or len(c) < len(best[0]):
                        best = (c, lc | lp << 3 | pb << 5)
        out.write(bytes([best[1]]) + best[0])
    else:
        b = sys.stdin.buffer if False else None
        raw = data
        if not raw:
            return
        h = raw[0]
        out.write(lzma.decompress(raw[1:], lzma.FORMAT_RAW, filters=filt(h & 7, (h >> 3) & 3, h >> 5)))
main()
