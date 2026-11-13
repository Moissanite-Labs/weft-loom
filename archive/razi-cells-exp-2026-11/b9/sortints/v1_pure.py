import sys
def main():
    data = sys.stdin.buffer.read().split()
    a = sorted(map(int, data))
    sys.stdout.buffer.write(b'\n'.join(map(str, a)).encode() if False else ('\n'.join(map(str, a)) + '\n').encode())
main()
