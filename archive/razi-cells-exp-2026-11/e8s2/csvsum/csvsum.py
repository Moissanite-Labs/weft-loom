import sys

def main():
    stdin = sys.stdin.buffer
    header = stdin.readline()
    sums = {}
    for line in stdin:
        # id,cat,val
        c1 = line.find(b',')
        c2 = line.find(b',', c1 + 1)
        cat = line[c1 + 1:c2]
        val = float(line[c2 + 1:])
        sums[cat] = sums.get(cat, 0.0) + val

    out = sys.stdout.buffer
    for cat in sorted(sums):
        out.write(cat + b',' + f'{sums[cat]:.2f}\n'.encode('ascii'))

if __name__ == '__main__':
    main()
