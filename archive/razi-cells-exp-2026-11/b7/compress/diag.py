import gen_data, squeeze, time
d = gen_data.make_corpus(64)
print("corpus", len(d))
t0 = time.time()
for i, enc in enumerate(squeeze._ENCODERS):
    s = time.time()
    try:
        b = enc(d)
        print("%2d %-10s %8d  %.3fs" % (i, enc.__name__, len(b), time.time() - s))
    except Exception as e:
        print(i, "ERR", e)
b = squeeze.compress(d)
print("BEST", b[0], len(b), "ratio %.3f" % (len(d) / len(b)), "total %.2fs" % (time.time() - t0))
print("roundtrip", squeeze.decompress(b) == d)
