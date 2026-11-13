import sys
def main():
    nums = sorted(map(int, sys.stdin.buffer.read().split()))
    sys.stdout.buffer.write(('\n'.join(map(str, nums)) + '\n').encode())
main()
