import sys


def main():
    numbers = list(map(int, sys.stdin.buffer.read().split()))
    numbers.sort()
    if numbers:
        sys.stdout.write('\n'.join(map(str, numbers)) + '\n')


if __name__ == '__main__':
    main()
