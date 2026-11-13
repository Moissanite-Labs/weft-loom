import random, sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000000
random.seed(42)
cats = ['cat%02d' % i for i in range(50)] + ['a', 'zeta', 'Mid']
out = ['id,cat,val\n']
rc = random.choice; rr = random.random
for i in range(n):
    out.append('%d,%s,%.2f\n' % (i, rc(cats), rr() * 2000 - 500))
sys.stdout.write(''.join(out))
