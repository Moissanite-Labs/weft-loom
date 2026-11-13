import sys
def main():
    data = sys.stdin.buffer.read().split()
    a = sorted(map(int, data))
    sys.stdout.write('\n'.join(map(str, a)))
    if a: sys.stdout.write('\n')
main()
