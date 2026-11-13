import squeeze

with open("corpus.bin", "rb") as f:
    raw = f.read()

comp = squeeze.compress(raw)
decomp = squeeze.decompress(comp)

if decomp != raw or len(comp) == 0:
    print(0)
else:
    print(f"{len(raw) / len(comp):.6f}")
