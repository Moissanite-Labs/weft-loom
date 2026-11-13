import sys
a = list(map(int, sys.stdin.buffer.read().split()))
a.sort()
sys.stdout.write('\n'.join(map(str, a)))
sys.stdout.write('\n')
