import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    data.sort(key=int)
    sys.stdout.buffer.write(b'\n'.join(data) + b'\n')

if __name__ == '__main__':
    main()
