import random
random.seed(1)
cats=['alpha','beta','gamma','delta','epsilon','zeta','eta','theta']
w=open('data.csv','w')
w.write('id,cat,val\n')
for i in range(2000000):
    w.write('%d,%s,%.2f\n' % (i, random.choice(cats), random.uniform(0,1000)))
w.close()
