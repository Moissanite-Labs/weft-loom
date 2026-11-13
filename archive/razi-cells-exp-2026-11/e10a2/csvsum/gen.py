import random, sys
random.seed(42)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000000
cats = ['cat%02d' % i for i in range(50)]
out = ['id,cat,val\n']
r = random.random
for i in range(n):
    out.append('%d,%s,%.2f\n' % (i, cats[int(r()*50)], r()*2000 - 500))
sys.stdout.write(''.join(out))
