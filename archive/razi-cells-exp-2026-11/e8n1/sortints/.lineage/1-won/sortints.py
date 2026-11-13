import sys

def main():
    data = sys.stdin.buffer.read().split()
    data.sort(key=int)
    if data:
        sys.stdout.buffer.write(b"\n".join(data) + b"\n")

if __name__ == "__main__":
    main()
