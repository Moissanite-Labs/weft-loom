import sys
random_seed = 1
cats = ('alpha','beta','gamma','delta','epsilon','zeta','eta','theta')
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000000
w = sys.stdout.write
w('id,cat,val\n')
buf = []
for i in range(n):
    v = (i * 2654435761) % 1000000
    buf.append('%d,%s,%d.%02d\n' % (i, cats[i % 8], v // 100, v % 100))
    if len(buf) >= 200000:
        w(''.join(buf)); buf.clear()
w(''.join(buf))
