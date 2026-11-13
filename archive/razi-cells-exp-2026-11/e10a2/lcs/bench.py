import random, subprocess, sys, time
from ref import ref
from lcs import lcs
def fail():
    print(0); sys.exit(0)
try:
    # correctness: small random cases vs reference DP
    random.seed(11)
    for t in range(400):
        k = random.choice([1, 2, 3, 4, 26])
        al = 'abcdefghijklmnopqrstuvwxyz'[:k]
        a = ''.join(random.choice(al) for _ in range(random.randint(0, 40)))
        b = ''.join(random.choice(al) for _ in range(random.randint(0, 40)))
        if lcs(a, b) != ref(a, b): fail()
    # correctness: CLI on the 3000-char case with known answer
    out = subprocess.run([sys.executable, 'lcs.py'], stdin=open('big.txt'), capture_output=True, text=True).stdout.strip()
    if out != open('big.ans').read().strip(): fail()
    out = subprocess.run([sys.executable, 'lcs.py'], input="ABCBDAB\nBDCABA\n", capture_output=True, text=True).stdout.strip()
    if out != "4": fail()
    # workload: 3000-char pairs over several alphabets
    random.seed(5)
    pairs = []
    for al in ['ACGT', 'ab', 'abcdefghijklmnopqrstuvwxyz', 'ACGT']:
        pairs.append((''.join(random.choice(al) for _ in range(3000)), ''.join(random.choice(al) for _ in range(3000))))
    best = None
    for rep in range(3):
        t = time.perf_counter()
        for _ in range(40):
            for a, b in pairs:
                lcs(a, b)
        d = time.perf_counter() - t
        best = d if best is None or d < best else best
    print(round(160 / best, 1))
except SystemExit:
    raise
except Exception:
    print(0)
