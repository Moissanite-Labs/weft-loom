import os
import sys
import time
import random
import tempfile

M = 1000000007
MAXN = 10 ** 18
HALF = 1000000008
PERIOD = 2 * HALF

orig_fd = os.dup(1)
sys.stdout.flush()


def die():
    try:
        os.dup2(orig_fd, 1)
        os.write(orig_fd, b"0\n")
    finally:
        os._exit(0)


def mul(A, B):
    a, b, c, d = A
    e, f, g, h = B
    return (
        (a * e + b * g) % M,
        (a * f + b * h) % M,
        (c * e + d * g) % M,
        (c * f + d * h) % M,
    )


def ref(n):
    R = (1, 0, 0, 1)
    Q = (1, 1, 1, 0)
    while n:
        if n & 1:
            R = mul(R, Q)
        Q = mul(Q, Q)
        n >>= 1
    return R[1]


try:
    with open("fibmod.py", "rb") as f:
        src = f.read()
    t0 = time.perf_counter()
    code = compile(src, "fibmod.py", "exec")
    compile_time = time.perf_counter() - t0
except Exception:
    die()

stdout_obj = sys.stdout
argv_obj = sys.argv


def run_capture(n):
    """Run one CLI invocation, returning exactly what it wrote to fd 1."""
    global stdout_obj, argv_obj
    old_stdout = sys.stdout
    old_argv = sys.argv
    out = b""
    sys.stdout.flush()
    saved = os.dup(1)
    with tempfile.TemporaryFile() as tmp:
        os.dup2(tmp.fileno(), 1)
        bad_exit = False
        try:
            sys.argv = ["fibmod.py", str(n)]
            sys.stdout = stdout_obj
            try:
                exec(code, {"__name__": "__main__", "__file__": "fibmod.py"})
            except SystemExit as e:
                if e.code not in (None, 0):
                    bad_exit = True
            finally:
                try:
                    sys.stdout.flush()
                except Exception:
                    pass
        finally:
            os.dup2(saved, 1)
            os.close(saved)
            sys.stdout = old_stdout
            sys.argv = old_argv
        tmp.seek(0)
        out = tmp.read()
    if bad_exit:
        return None
    return out.decode("utf-8", "strict").strip()


try:
    # Explicit contract check plus the entire small prefix via the simple recurrence.
    if run_capture(10) != "55":
        die()
    fibs = [0, 1]
    for _ in range(2, 201):
        fibs.append((fibs[-1] + fibs[-2]) % M)
    for n, want in enumerate(fibs):
        if run_capture(n) != str(want):
            die()

    # Independent matrix-power checks at boundaries, period landmarks, and random 60-bit inputs.
    rng = random.Random(0xC0FFEE)
    tests = [
        0, 1, 2, 10, 50, 201, HALF - 1, HALF, HALF + 1,
        PERIOD - 1, PERIOD, PERIOD + 1, 2 ** 60 - 1,
        MAXN - 1, MAXN, MAXN % PERIOD, MAXN % HALF,
    ]
    tests += [rng.randrange(0, MAXN + 1) for _ in range(64)]
    tests += [rng.randrange(0, PERIOD) for _ in range(16)]
    for n in tests:
        want = ref(n)
        if run_capture(n) != str(want):
            die()

    # Heavy, deterministic in-process workload: fresh globals per invocation, fd 1 to /dev/null.
    args = [str(rng.randrange(0, MAXN + 1)) for _ in range(1024)]
    args += [str(x) for x in (MAXN, MAXN - 1, HALF, PERIOD, 2 ** 60 - 1)]
    L = len(args)
    env_keys = {"__name__": "__main__", "__file__": "fibmod.py"}
    sys.stdout.flush()
    saved = os.dup(1)
    devnull = os.open(os.devnull, os.O_WRONLY)
    total = 0
    try:
        os.dup2(devnull, 1)
        # Warm-up.
        for s in args[:256]:
            sys.argv = ["fibmod.py", s]
            sys.stdout = stdout_obj
            try:
                exec(code, dict(env_keys))
            except SystemExit as e:
                if e.code not in (None, 0):
                    raise
        sys.stdout.flush()
        start = time.perf_counter()
        target = 0.65
        while True:
            for s in args:
                sys.argv = ["fibmod.py", s]
                sys.stdout = stdout_obj
                try:
                    exec(code, dict(env_keys))
                except SystemExit as e:
                    if e.code not in (None, 0):
                        raise
            total += L
            if time.perf_counter() - start >= target:
                break
        sys.stdout.flush()
        end = time.perf_counter()
    finally:
        os.dup2(saved, 1)
        os.close(saved)
        os.close(devnull)
        sys.stdout = stdout_obj
        sys.argv = argv_obj
    elapsed = end - start + compile_time
    score = total / elapsed
except Exception:
    die()

if not (score > 0):
    die()
os.dup2(orig_fd, 1)
os.write(orig_fd, ("%.6f\n" % score).encode())
os._exit(0)
