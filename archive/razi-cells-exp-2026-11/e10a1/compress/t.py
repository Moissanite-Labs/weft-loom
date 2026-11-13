import random, time, bench, squeeze, cand
r = random.Random(5)
bad = 0
alph = [b"a", b"b", b"A", b"B", b"ab", b"Ab", b"aB", b"the", b"The", b"THE", b" ", b" ", b" ", b"  ", b".", b". ", b"1", b"12", b"\n", b",", b"\x00", b"x9", b"-"]
for it in range(4000):
    x = b"".join(r.choice(alph) for _ in range(r.randint(1, 60)))
    if r.random() < 0.5: x = x * r.randint(1, 4)
    if cand._unwt(cand._wt(x)) != x:
        bad += 1
        if bad < 4: print("BAD", x)
    if it % 40 == 0 and cand.decompress(cand.compress(x)) != x: bad += 1; print("BADC", x)
print("fuzz bad", bad)
t0 = time.time()
tot = [0, 0]
for p in bench.corpus():
    a = squeeze.compress(p); c = cand.compress(p)
    assert cand.decompress(c) == p
    w = cand._wt(p); assert cand._unwt(w) == p
    print(len(p), "old", len(a), "new", len(c), "tag", hex(c[0]), "wt", len(w))
    tot[0] += len(a); tot[1] += len(c)
    if c[0] == 0x20:
        i = 1
        for _ in range(3):
            ln, i = cand._rvi(c, i); print("   sec", ln, "codec", c[i]); i += ln
print(tot, sum(map(len, bench.corpus())) / tot[1], "time", time.time() - t0)
