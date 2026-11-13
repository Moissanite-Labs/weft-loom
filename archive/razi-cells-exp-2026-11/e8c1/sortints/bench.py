import subprocess
import time
import sys

def main():
    with open('expected.txt', 'rb') as f:
        expected = f.read()

    t0 = time.perf_counter()
    with open('input.txt', 'rb') as fin:
        p = subprocess.run([sys.executable, 'sortints.py'], stdin=fin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t1 = time.perf_counter()

    if p.returncode != 0 or p.stdout != expected:
        print(0)
        return

    # Also quick sanity check for edge cases: arbitrary precision >64-bit, empty input, multiple whitespace
    edge_in = b"  100000000000000000000\n -100000000000000000000 \t 0  -5 5 \n"
    edge_exp = b"-100000000000000000000\n-5\n0\n5\n100000000000000000000\n"
    p2 = subprocess.run([sys.executable, 'sortints.py'], input=edge_in, stdout=subprocess.PIPE)
    if p2.returncode != 0 or p2.stdout != edge_exp:
        print(0)
        return

    elapsed = t1 - t0
    # Score = millions of ints per second
    print(f"{1.0 / elapsed:.4f}")

if __name__ == '__main__':
    main()
