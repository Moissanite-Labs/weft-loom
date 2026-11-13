import sys
import lzma


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("c", "d"):
        sys.stderr.write("usage: squeeze.py c|d\n")
        sys.exit(2)
    data = sys.stdin.buffer.read()
    if sys.argv[1] == "c":
        out = lzma.compress(data, format=lzma.FORMAT_XZ, check=lzma.CHECK_CRC32,
                            preset=9 | lzma.PRESET_EXTREME)
    else:
        out = lzma.decompress(data, format=lzma.FORMAT_AUTO)
    sys.stdout.buffer.write(out)


if __name__ == "__main__":
    main()
