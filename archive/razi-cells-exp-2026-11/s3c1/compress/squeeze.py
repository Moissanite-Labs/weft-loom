import sys
import lzma


def _opts(lc, lp, pb):
    return [{
        "id": lzma.FILTER_LZMA1,
        "preset": 9 | lzma.PRESET_EXTREME,
        "dict_size": 1 << 24,
        "lc": lc, "lp": lp, "pb": pb,
        "mode": lzma.MODE_NORMAL, "nice_len": 273,
        "mf": lzma.MF_BT4, "depth": 0,
    }]


def compress(data):
    best = None
    for lc, lp, pb in ((3, 0, 2), (4, 0, 0), (1, 0, 0), (0, 0, 0), (2, 0, 0), (3, 0, 0), (4, 0, 2)):
        try:
            out = lzma.compress(data, format=lzma.FORMAT_ALONE, filters=_opts(lc, lp, pb))
        except lzma.LZMAError:
            continue
        if best is None or len(out) < len(best):
            best = out
    return best


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("c", "d"):
        sys.stderr.write("usage: squeeze.py c|d\n")
        sys.exit(2)
    data = sys.stdin.buffer.read()
    if sys.argv[1] == "c":
        out = compress(data)
    else:
        out = lzma.decompress(data, format=lzma.FORMAT_AUTO)
    sys.stdout.buffer.write(out)
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
