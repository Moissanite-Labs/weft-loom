import subprocess
import time
import sys

def run_bench():
    with open("expected.txt", "rb") as f:
        expected = f.read()

    # Edge case check: empty input and big integers (>64 bit and leading zeros/spaces)
    edge_in = b"  100  -5\n0\t999999999999999999999999999999 -999999999999999999999999999999 42 \n"
    edge_exp = b"-999999999999999999999999999999\n-5\n0\n42\n100\n999999999999999999999999999999\n"
    p = subprocess.run([sys.executable, "sortints.py"], input=edge_in, capture_output=True)
    if p.returncode != 0 or p.stdout != edge_exp:
        print(0)
        return

    p_empty = subprocess.run([sys.executable, "sortints.py"], input=b"   \n\t  ", capture_output=True)
    if p_empty.returncode != 0 or p_empty.stdout != b"":
        print(0)
        return

    times = []
    for _ in range(3):
        with open("input.txt", "rb") as fin:
            t0 = time.perf_counter()
            p = subprocess.run([sys.executable, "sortints.py"], stdin=fin, capture_output=True)
            t1 = time.perf_counter()
        if p.returncode != 0 or p.stdout != expected:
            print(0)
            return
        times.append(t1 - t0)

    times.sort()
    median_time = times[1]
    # Score: ints per second
    print(int(1000000 / median_time))

if __name__ == "__main__":
    run_bench()
