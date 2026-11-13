import subprocess, time, sys

def verify_and_bench():
    # Edge cases test
    edge_in = b"  100 \t -5\n0   999999999999999999999999999999 -999999999999999999999999999999 \n 42  -5 "
    edge_expected = b"-999999999999999999999999999999\n-5\n-5\n0\n42\n100\n999999999999999999999999999999\n"
    p = subprocess.run([sys.executable, "sortints.py"], input=edge_in, capture_output=True)
    if p.returncode != 0 or p.stdout != edge_expected:
        print(0)
        return

    # Empty test
    p = subprocess.run([sys.executable, "sortints.py"], input=b"   \n\t  ", capture_output=True)
    if p.returncode != 0 or p.stdout != b"":
        print(0)
        return

    # Benchmark on 1,000,000 ints (run 2 times, take best/mean, verify output)
    with open("expected.txt", "rb") as f:
        expected = f.read()

    times = []
    for i in range(2):
        with open("input.txt", "rb") as fin, open("out.txt", "wb") as fout:
            t0 = time.perf_counter()
            p = subprocess.run([sys.executable, "sortints.py"], stdin=fin, stdout=fout)
            t1 = time.perf_counter()
        if p.returncode != 0:
            print(0)
            return
        times.append(t1 - t0)

    with open("out.txt", "rb") as f:
        out = f.read()
    if out != expected:
        print(0)
        return

    avg_t = sum(times) / len(times)
    # Score: ints per second
    print(int(1000000 / avg_t))

if __name__ == "__main__":
    verify_and_bench()
