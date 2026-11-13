import os
import sys

def main():
    try:
        import ctypes
        so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_csvsum.so")
        lib = ctypes.CDLL(so_path)
        if lib.process_stdin() == 0:
            return
    except Exception:
        pass

    stdin = sys.stdin.buffer
    header = stdin.readline()
    if not header:
        return
    sums = {}
    float_ = float
    for line in stdin:
        try:
            _, cat, val_str = line.split(b',')
            sums[cat] += float_(val_str)
        except KeyError:
            sums[cat] = float_(val_str)
        except ValueError:
            pass

    out = sys.stdout.buffer
    out.write(b''.join(cat + b',' + f"{sums[cat]:.2f}\n".encode('ascii') for cat in sorted(sums)))

if __name__ == '__main__':
    main()
