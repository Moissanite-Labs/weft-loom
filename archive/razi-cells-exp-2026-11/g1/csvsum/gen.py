import random, sys
cats=['alpha','beta','gamma','delta','epsilon','zeta']
n=int(sys.argv[1]) if len(sys.argv)>1 else 2000000
random.seed(42)
w=sys.stdout.write
w('id,cat,val\n')
for i in range(n):
    c=random.choice(cats)
    v=random.randint(0,100000)/100.0
    w('%d,%s,%.2f\n'%(i,c,v))
