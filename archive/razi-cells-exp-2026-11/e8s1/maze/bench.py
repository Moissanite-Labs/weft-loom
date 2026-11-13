import subprocess
import sys
import time

SMALL_TESTS = [
    (b"S.E\n", "2"),
    (b"S#E\n", "-1"),
    (b"S..#\n.#..\n..#E\n", "5"),
    (b"####\n#S.#\n#.#E\n####\n", "-1"),
    (b".S..\n.##.\n..E.\n", "5"),
    (b"E.S\n", "2"),
    (b"SE\n", "1"),
]

BIG_TESTS = [
    ("maze_2000_a.txt", "3998"),
    ("maze_2000_b.txt", "4006"),
    ("maze_2000_c.txt", "-1"),
    ("maze_2000_d.txt", "3998"),
]

def main():
    for inp, expected in SMALL_TESTS:
        res = subprocess.run([sys.executable, "maze.py"], input=inp, capture_output=True)
        if res.returncode != 0 or res.stdout.decode().strip() != expected:
            print(0)
            return

    big_data = []
    for fname, expected in BIG_TESTS:
        with open(fname, "rb") as f:
            big_data.append((f.read(), expected))

    t0 = time.perf_counter()
    for data, expected in big_data:
        res = subprocess.run([sys.executable, "maze.py"], input=data, capture_output=True)
        if res.returncode != 0 or res.stdout.decode().strip() != expected:
            print(0)
            return
    elapsed = time.perf_counter() - t0
    score = 100.0 / elapsed
    print(f"{score:.4f}")

if __name__ == "__main__":
    main()
