import sys

def main():
    data = sys.stdin.buffer.read().split()
    data.sort(key=int)
    sys.stdout.buffer.write(b'\n'.join(data))
    sys.stdout.buffer.write(b'\n')

if __name__ == '__main__':
    main()
