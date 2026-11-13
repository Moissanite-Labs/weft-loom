import sys, numpy as np
def main():
    a = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
    a.sort()
    a.tofile(sys.stdout.buffer, sep='\n', format='%d')
    sys.stdout.buffer.write(b"\n")
main()
