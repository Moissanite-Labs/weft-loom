import sys
from collections import defaultdict

def main():
    readline = sys.stdin.buffer.readline
    header = readline()
    if not header:
        return
    sums = defaultdict(float)
    for line in sys.stdin.buffer:
        # line is b'id,cat,val\n'
        c1 = line.find(44)
        c2 = line.find(44, c1 + 1)
        cat = line[c1 + 1:c2]
        val = float(line[c2 + 1:])
        sums[cat] += val

    out = []
    for cat in sorted(sums):
        out.append(f"{cat.decode()},{sums[cat]:.2f}\n")
    sys.stdout.write("".join(out))

if __name__ == "__main__":
    main()
