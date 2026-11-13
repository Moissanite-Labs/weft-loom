import random
random.seed(1)
cats=['c%02d'%i for i in range(50)]
out=['id,cat,val\n']
for i in range(2000000):
    out.append('%d,%s,%.2f\n'%(i,random.choice(cats),random.uniform(-1000,1000)))
open('data.csv','w').write(''.join(out))
