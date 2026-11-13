import sys
import lzma

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("c", "d"):
        sys.stderr.write("usage: squeeze.py c|d\n")
        sys.exit(2)
    data = sys.stdin.buffer.read()
    if sys.argv[1] == "c":
        out = lzma.compress(
            data,
            format=lzma.FORMAT_ALONE,
            preset=9 | lzma.PRESET_EXTREME,
        )
    else:
        out = lzma.decompress(data)
    sys.stdout.buffer.write(out)
    sys.stdout.buffer.flush()

if __name__ == "__main__":
    main()
