import sys

def main():
    data = sys.stdin.buffer.read()
    nums = list(map(int, data.split()))
    nums.sort()
    if nums:
        sys.stdout.write('\n'.join(map(str, nums)))
        sys.stdout.write('\n')

main()
