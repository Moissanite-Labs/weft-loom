import gen, squeeze, sys
tot = 0; out = 0
for d in gen.corpus():
    c = squeeze.compress(d)
    if not isinstance(c, bytes) or squeeze.decompress(c) != d:
        print(0); sys.exit(0)
    tot += len(d); out += len(c)
print(round(tot / out, 4))
