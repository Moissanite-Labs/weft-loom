import os, sys, ctypes

def fallback():
    sums = {}
    stdin = sys.stdin.buffer
    stdin.readline()
    for line in stdin:
        c1 = line.find(b',')
        if c1 < 0: continue
        c2 = line.find(b',', c1 + 1)
        cat = line[c1+1:c2]
        val = float(line[c2+1:])
        sums[cat] = sums.get(cat, 0.0) + val
    for cat in sorted(sums):
        print(f"{cat.decode()},{sums[cat]:.2f}")

def main():
    so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_csvsum.so")
    if os.path.exists(so_path):
        lib = ctypes.CDLL(so_path)
        if lib.process_stdin() == 0:
            return
    fallback()

if __name__ == '__main__':
    main()
