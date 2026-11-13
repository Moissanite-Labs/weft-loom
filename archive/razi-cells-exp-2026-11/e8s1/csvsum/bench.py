import subprocess, time, sys

with open("expected.txt", "rb") as f:
    expected = f.read().strip().splitlines()

def check_output(out_bytes):
    lines = out_bytes.strip().splitlines()
    if len(lines) != len(expected):
        return False
    for l1, l2 in zip(lines, expected):
        p1 = l1.split(b',')
        p2 = l2.split(b',')
        if len(p1) != 2 or p1[0] != p2[0]:
            return False
        # check formatted to 2 decimals and within 0.01 rounding tolerance
        if abs(float(p1[1]) - float(p2[1])) > 0.015:
            return False
        if b'.' not in p1[1] or len(p1[1].split(b'.')[1]) != 2:
            return False
    return True

# Also verify edge cases (arbitrary categories, scientific/integer/negative vals, piped stream)
edge_in = b"id,cat,val\n1,z_cat,10\n2,a_cat,-3.5\n3,z_cat,2.254\n4,m_cat,0\n"
edge_exp = b"a_cat,-3.50\nm_cat,0.00\nz_cat,12.25\n"
p_edge = subprocess.run([sys.executable, "csvsum.py"], input=edge_in, capture_output=True)
if p_edge.returncode != 0 or p_edge.stdout != edge_exp:
    print(0)
    sys.exit(0)

t0 = time.perf_counter()
with open("test.csv", "rb") as f:
    p = subprocess.run([sys.executable, "csvsum.py"], stdin=f, capture_output=True)
t1 = time.perf_counter()

if p.returncode != 0 or not check_output(p.stdout):
    print(0)
    sys.exit(0)

elapsed = t1 - t0
# Score is rows per second (in thousands, or millions)
score = 2000000.0 / elapsed
print(f"{score:.2f}")
