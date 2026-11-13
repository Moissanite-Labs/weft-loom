import sys, random
def gen(h, w, seed, dens=0.28):
    r = random.Random(seed)
    rows = []
    for y in range(h):
        rows.append(bytearray(35 if r.random() < dens else 46 for _ in range(w)))
    rows[0][0] = ord('S'); rows[h-1][w-1] = ord('E')
    return b"\n".join(bytes(x) for x in rows) + b"\n"
if __name__ == "__main__":
    h, w, seed = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    dens = float(sys.argv[4]) if len(sys.argv) > 4 else 0.28
    sys.stdout.buffer.write(gen(h, w, seed, dens))
