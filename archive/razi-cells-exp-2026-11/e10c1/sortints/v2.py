import sys
a = sorted(map(int, sys.stdin.buffer.read().split()))
sys.stdout.buffer.write(("%d\n"*len(a) % tuple(a)).encode())
